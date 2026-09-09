import base64
import copy
import csv
import ctypes
import datetime
import gc
import json
import os
import re
import shutil
import signal
import sys
import tarfile
import threading
import time
import uuid
from functools import wraps
from io import StringIO
from typing import Any
from urllib.parse import urlparse

from OpenSSL import crypto
from cryptography import x509
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.x509.oid import NameOID
from flask import Flask, Response, request, send_file, after_this_request
from flask_cors import CORS
from packaging.version import Version
from werkzeug.exceptions import BadRequest
from werkzeug.utils import secure_filename

from __init__ import EASYUCS_ROOT, __version__
from common import (decrypt, encrypt, extract, get_certificate_details, get_disk_space_usage, guess_image_metadata,
                    read_json_file, validate_json)
from device.device import GenericDevice

app = Flask(__name__)
cors = CORS(app)
# easyucs is a runtime-injected singleton (set by start()), so its concrete type is not known at
# import time. Annotating it as Any avoids hundreds of false-positive reportOptionalMemberAccess
# warnings from static analysis while still being accurate (the engine object is duck-typed and may
# be any of the entry-point Easyucs classes).
easyucs: Any = None
logContent = ""
displayLogsBool = False
_shutdown_in_progress = False

timeout_values = {
    "add_device": 360,
    "calculate_checksums": 300,
    "change_mode": 3600,
    "claim_to_intersight": 600,
    "clear_config": 3600,
    "clear_sel_logs": 300,
    "create_vmedia_policy": 300,
    "deploy_domain_profile": 3600,
    "download_file": 7200,
    "fetch_backup": 600,
    "fetch_cache": 1200,
    "fetch_config": 3600,
    "fetch_config_inventory": 7200,
    "fetch_inventory": 3600,
    "fetch_os_firmware_data": 1800,
    "generate_report": 600,
    "import_tech_support": 7200,
    "initial_setup": 3000,
    "push_config": 10800,
    "regenerate_certificate": 300,
    "reset": 720,
    "reset_device_connector": 300,
    "sync_to_software_repository": 600,
    "test_connection": 300
}


def timeout_wrapper(action_func):
    @wraps(action_func)
    def decorated(timeout=900, **kwargs):
        obj = kwargs.get("device", easyucs.repository_manager.repo)
        action_type = kwargs.get("action_type", None)
        object_type = kwargs.get("object_type", None)
        task_uuid = kwargs.get("task_uuid", None)

        if obj is None:
            easyucs.logger(level="error", message="No device/repo provided")
            sys.exit()

        if task_uuid is None:
            easyucs.logger(level="error", message="No task UUID provided")
            sys.exit()

        obj.task = easyucs.task_manager.find_task_by_uuid(uuid=task_uuid)
        if obj.task is None:
            easyucs.logger(level="error", message="Could not find task UUID")
            sys.exit()

        # We start the timer
        start_timer = time.time()

        # We start the task
        easyucs.task_manager.start_task(uuid=task_uuid)

        # We perform the main action on a separate thread
        # daemon=True so that a long-running action thread does not block interpreter shutdown
        # (e.g. on CTRL+C). Its lifecycle is explicitly managed below (waited on / terminated).
        action_thread = threading.Thread(target=action_func, kwargs=kwargs,
                                         name=str(action_type) + "_" + str(object_type) + "_" + str(task_uuid),
                                         daemon=True)
        action_thread.start()

        easyucs.logger(
            message=f"Waiting up to {str(timeout)} seconds for the {str(action_type)} {str(object_type)} "
                    f"operation to be performed on the "
                    f"{obj.metadata.device_type_long + ' device' if isinstance(obj, GenericDevice) else 'repo file'}"
        )
        thread_cancelled = False
        i = 0
        # We wait for the thread to end or to be cancelled by user
        while (time.time() - start_timer) < timeout:
            time_left = int(timeout - (time.time() - start_timer))
            if not action_thread.is_alive():
                easyucs.logger(level="debug",
                               message="Thread for the " + str(action_type) + " " + str(object_type) +
                                       " operation is finished")
                break
            if obj.task.cancel:
                thread_cancelled = True
                break
            if i % 60 == 0:
                easyucs.logger(level="debug",
                               message="Waiting up to " + str(time_left) + " seconds for the " + str(action_type) +
                                       " " + str(object_type) + " operation on thread '" +
                                       str(action_thread.name) + "' to finish...")
            time.sleep(1)
            i += 1

        if thread_cancelled:
            easyucs.logger(level="debug",
                           message="Received signal to cancel the task. Killing thread " + str(action_thread.name)
                                   + "...")
            terminate_thread(action_thread)

            # We stop the task
            easyucs.task_manager.stop_task(uuid=task_uuid, status="failed", status_message="Task cancelled by user")

        elif action_thread.is_alive():
            easyucs.logger(level="debug",
                           message="Timeout exceeded. Killing thread " + str(action_thread.name) + "...")
            terminate_thread(action_thread)

            # We stop the task
            easyucs.task_manager.stop_task(uuid=task_uuid, status="failed",
                                           status_message="Timeout of " + str(timeout) + " seconds exceeded")
        else:
            # We stop the task
            easyucs.task_manager.stop_task(uuid=task_uuid)

        # We release 1 token to the available tokens
        easyucs.task_manager.available_tokens.put(1)
        easyucs.logger(level="debug",
                       message="Released 1 token. " + str(easyucs.task_manager.available_tokens.qsize()) +
                               " token(s) left")

        # We reset the task attribute on the device/repo
        obj.task = None

        # If the device/repo has any queued tasks, move the oldest one to the system's (task manager's) task queue.
        #
        # Additional handling is required for devices that share the same endpoint ID
        # (e.g., registered using different API keys but ultimately pointing to the same backend system).
        # In such cases, queued tasks across all devices with the same endpoint must be considered.
        # Example scenario:
        # Devices A and B sharing same endpoint ID. A task is currently running on device A.
        # If a new task is initiated on device B during that time, it will be queued under device B.
        # Once the task on device A completes:
        #   1. We first check if device A has any queued tasks to schedule.
        #   2. If not, we then look for queued tasks on other devices (like B) sharing the same endpoint ID.

        if not obj.queued_tasks.empty():
            if not easyucs.task_manager.add_to_pending_tasks(obj.queued_tasks.get()):
                # Should not happen theoretically
                easyucs.logger(level="error",
                               message="Error while scheduling the device's/repo's queued task. System's task queue "
                                       "might be full")
        else:
            secondary_obj = None
            # Find all devices sharing the same endpoint ID (may have different API credentials).
            # Skip if device_endpoint_id is None (e.g. devices imported from a tech-support bundle
            # without a live connection, which never run _set_device_endpoint_id).
            devices_with_same_endpoint = []
            if obj.metadata.device_endpoint_id is not None and obj.parent is not None:
                devices_with_same_endpoint = obj.parent.find_devices_by_endpoint_id(
                    endpoint_id=obj.metadata.device_endpoint_id
                )
            # Look for another device (sharing same endpoint ID) that has queued tasks
            if devices_with_same_endpoint and len(devices_with_same_endpoint) > 1:
                for device in devices_with_same_endpoint:
                    if hasattr(device, "queued_tasks") and not device.queued_tasks.empty():
                        secondary_obj = device
                        break
            # Move the next queued task from the device (sharing same endpoint ID) to pending tasks
            if secondary_obj:
                if not easyucs.task_manager.add_to_pending_tasks(secondary_obj.queued_tasks.get()):
                    easyucs.logger(level="error",
                                   message="Error while scheduling queued task from device "
                                           "sharing the same endpoint ID. System's task queue might be full")

        sys.exit()

    return decorated


def fetch_config_inventory(device: Any = None, force=False):
    """
    Performs config and inventory fetch sequentially
    :param device: The device for which the fetch is to be performed
    :param force: Force the config & inventory fetch to continue even if facing errors
    :return: True if both config and inventory are fetched successfully else False
    """
    if device is None:
        easyucs.logger(level="error", message="No device provided")
        sys.exit()

    config_uuid = device.config_manager.fetch_config(force=force)
    inventory_uuid = device.inventory_manager.fetch_inventory(force=force)
    if config_uuid and inventory_uuid:
        return True
    return False


def fetch_config_inventory_from_xml(device: Any = None, xml_file_path=None, force=False, tech_support_timestamp=None,
                                    tech_support_filename=None):
    """
    Performs config and inventory fetch from a MIT XML file (extracted from a tech-support bundle)
    :param device: The UcsSystem device for which the fetch is to be performed
    :param xml_file_path: Absolute path to the mit.xml file to parse
    :param force: Force the fetch to continue even if facing errors
    :param tech_support_timestamp: datetime of when the tech-support bundle was taken (from topSystem.currentTime)
    :param tech_support_filename: Original filename of the uploaded tech-support bundle
    :return: True if both config and inventory are fetched successfully else False
    """
    if device is None:
        easyucs.logger(level="error", message="No device provided")
        sys.exit()
    if not xml_file_path:
        easyucs.logger(level="error", message="No xml_file_path provided")
        sys.exit()

    config_uuid = device.config_manager.fetch_config(force=force, xml_file_path=xml_file_path,
                                                     tech_support_timestamp=tech_support_timestamp,
                                                     tech_support_filename=tech_support_filename)
    inventory_uuid = device.inventory_manager.fetch_inventory(force=force, xml_file_path=xml_file_path,
                                                              tech_support_timestamp=tech_support_timestamp,
                                                              tech_support_filename=tech_support_filename)
    if config_uuid and inventory_uuid:
        return True
    return False


def get_object_from_db(object_type=None, uuid=None, device_uuid=None, task_uuid=None, filter=None,
                       order_by=None, page_number=0, page_size=None, repo_file_path=None):
    """
    Gets all objects' metadata from the Database
    :param object_type: Type of object to get metadata of (backup/config/device/inventory/report/task/taskstep)
    :param uuid: Only get metadata that matches the specified UUID
    :param device_uuid: Filter results to only include entries for a given device UUID
    :param task_uuid: Filter results to only include entries for a given task UUID
    :param filter: Optional array of attributes to filter in the get operation
    :param order_by: Order of returned objects (Tuple with object attribute and order [desc, asc])
    :param page_size: Number of returned objects
    :param page_number: Page number of returned objects
    :param repo_file_path: Relative Path to the file in repo
    :return: Dictionary with the list of objects' metadata if successful, None otherwise
    """

    if object_type not in ["backup", "config", "device", "inventory", "repofile", "report", "task", "taskstep"]:
        easyucs.logger(level="error", message="Invalid object type provided")
        return None

    if uuid and device_uuid:
        easyucs.logger(level="error", message="Both uuid and device uuid are provided")
        return None

    if uuid and task_uuid:
        easyucs.logger(level="error", message="Both uuid and task uuid are provided")
        return None

    if device_uuid and task_uuid:
        easyucs.logger(level="error", message="Both device uuid and task uuid are provided")
        return None

    if filter and len(filter) != 3:
        easyucs.logger(level="error", message="Filter length is not equal to 3")
        return None

    if filter:
        if filter[0] in ["is_system", "is_hidden"]:
            if filter[2].lower() == "true":
                filter[2] = True
            elif filter[2].lower() == "false":
                filter[2] = False
        filter = (filter[0], filter[1], filter[2])

    if order_by is None:
        order_by = ("timestamp", "desc")
    object_metadata_list = []

    # If we get a single object we put the name to singular, otherwise to plural
    if uuid or repo_file_path:
        dict_name = object_type
    else:
        if object_type == "inventory":
            dict_name = "inventories"
        elif object_type == "taskstep":
            dict_name = "steps"
        else:
            dict_name = object_type + "s"

    for object_metadata in easyucs.repository_manager.get_metadata(
            object_type=object_type, uuid=uuid, device_uuid=device_uuid, task_uuid=task_uuid, filter=filter,
            order_by=order_by, limit=page_size, page=page_number, repo_file_path=repo_file_path
    ):
        obj = {}

        if hasattr(object_metadata, 'device_uuid') and getattr(object_metadata, 'device_uuid'):
            obj["device_uuid"] = str(object_metadata.device_uuid)
        if hasattr(object_metadata, 'uuid'):
            obj["uuid"] = str(object_metadata.uuid)
        if hasattr(object_metadata, 'timestamp'):
            obj["timestamp"] = object_metadata.timestamp.isoformat()[:-3] + 'Z'

        # If we are not dealing with a task, these attributes are common to all the other objects
        if object_type not in ["task", "taskstep", "repofile"]:
            for attribute in ["device_version", "easyucs_version", "is_hidden", "is_system", "name", "origin",
                              "system_usage"]:
                if getattr(object_metadata, attribute) not in [None, ""]:
                    obj[attribute] = getattr(object_metadata, attribute)

        if object_type == "backup":
            for attribute in ["backup_type"]:
                if getattr(object_metadata, attribute) not in [None, ""]:
                    obj[attribute] = getattr(object_metadata, attribute)

        elif object_type == "config":
            for attribute in ["category", "is_custom", "revision", "subcategory", "url"]:
                if getattr(object_metadata, attribute) not in [None, ""]:
                    obj[attribute] = getattr(object_metadata, attribute)

        elif object_type == "device":
            for attribute in ["bypass_connection_checks", "bypass_version_checks", "device_connector_claim_status",
                              "device_connector_ownership_name", "device_connector_ownership_user",
                              "device_endpoint_id", "device_name", "device_type", "device_type_long", "is_reachable",
                              "key_id", "sub_device_uuids", "target", "timestamp_last_connected", "username",
                              "use_proxy", "user_label"]:
                if getattr(object_metadata, attribute) not in [None, ""]:
                    if "timestamp" in attribute:
                        obj[attribute] = getattr(object_metadata, attribute).isoformat()[:-3] + 'Z'
                    else:
                        obj[attribute] = getattr(object_metadata, attribute)

            for attribute in ["intersight_device_uuid", "parent_device_uuid"]:
                if getattr(object_metadata, attribute) not in [None, ""]:
                    obj[attribute] = str(getattr(object_metadata, attribute))

        elif object_type == "inventory":
            for attribute in ["is_custom"]:
                if getattr(object_metadata, attribute) not in [None, ""]:
                    obj[attribute] = getattr(object_metadata, attribute)

        elif object_type == "repofile":
            for attribute in ["file_path", "md5", "sha1", "sha256", "timestamp"]:
                if getattr(object_metadata, attribute) not in [None, ""]:
                    if "timestamp" in attribute:
                        obj[attribute] = getattr(object_metadata, attribute).isoformat()[:-3] + 'Z'
                    else:
                        obj[attribute] = getattr(object_metadata, attribute)

        elif object_type == "report":
            for attribute in ["language", "output_format", "page_layout", "report_type", "size"]:
                if getattr(object_metadata, attribute) not in [None, ""]:
                    obj[attribute] = getattr(object_metadata, attribute)

        elif object_type == "task":
            for attribute in ["config_uuid", "description", "device_endpoint_id", "device_name", "easyucs_version",
                              "inventory_uuid", "name", "progress", "repo_file_path", "repo_file_uuid", "report_uuid",
                              "status", "status_message", "target_device_uuid", "timestamp_start", "timestamp_stop"]:
                if getattr(object_metadata, attribute) not in [None, ""]:
                    if "timestamp" in attribute:
                        obj[attribute] = getattr(object_metadata, attribute).isoformat()[:-3] + 'Z'
                    elif "uuid" in attribute:
                        obj[attribute] = str(getattr(object_metadata, attribute))
                    else:
                        obj[attribute] = getattr(object_metadata, attribute)

        elif object_type == "taskstep":
            for attribute in ["description", "name", "optional", "order", "status", "status_message", "timestamp_start",
                              "timestamp_stop", "weight"]:
                if getattr(object_metadata, attribute) not in [None, ""]:
                    if "timestamp" in attribute:
                        obj[attribute] = getattr(object_metadata, attribute).isoformat()[:-3] + 'Z'
                    else:
                        obj[attribute] = getattr(object_metadata, attribute)

        else:
            return None

        object_metadata_list.append(obj)

    # If we take a single object, we do not return a list but the object directly
    if uuid or repo_file_path:
        if len(object_metadata_list) == 1:
            object_dict = {dict_name: object_metadata_list[0]}
        else:
            easyucs.logger(level="error", message=f"Could not find {object_type} with "
                                                  f"{'uuid ' + str(uuid) if uuid else 'file path ' + str(repo_file_path)}")
            return None
    else:
        object_dict = {dict_name: object_metadata_list}
    return object_dict


def load_object(object_type=None, object_uuid=None, device: Any = None):
    """
    Loads an object in the corresponding object list in memory
    :param object_type: Type of object to be loaded (config/device/inventory)
    :param object_uuid: The UUID of the object to be loaded
    :param device: The device to which the object belongs (optional)
    :return: Object loaded in memory if successful, None otherwise
    """

    if object_type not in ["config", "device", "inventory", "report"]:
        easyucs.logger(level="error", message="Invalid object type provided")
        return None

    if not object_uuid:
        easyucs.logger(level="error", message="Missing UUID of object")
        return None

    if object_type == "device":
        manager_target = getattr(easyucs, object_type + "_manager")
    else:
        if not device:
            easyucs.logger(level="error", message="Missing device for which object must be loaded")
            return None
        manager_target = getattr(device, object_type + "_manager")

    obj = getattr(manager_target, "find_" + object_type + "_by_uuid")(uuid=object_uuid)

    if not obj:
        # Object may not have been loaded into object list yet. Trying to load it using its metadata (DB)
        easyucs.logger(level="debug",
                       message="Trying to load " + object_type + " with UUID " + object_uuid + " from the DB")
        obj_metadata_list = easyucs.repository_manager.get_metadata(object_type=object_type, uuid=object_uuid)
        if len(obj_metadata_list) == 1:
            if object_type == "device":
                result = getattr(manager_target, "add_" + object_type)(metadata=obj_metadata_list[0])
            else:
                result = getattr(manager_target, "import_" + object_type)(metadata=obj_metadata_list[0])

            if result:
                obj = getattr(manager_target, "find_" + object_type + "_by_uuid")(uuid=object_uuid)
            else:
                easyucs.logger(level="error", message="Could not perform add/import action",
                               set_api_error_message=False)
                return None

        else:
            easyucs.logger(level="error", message="Could not find " + object_type + " with UUID " + object_uuid + ": " +
                                                  str(len(obj_metadata_list)) + " objects found")
            return None

    return obj


@timeout_wrapper
def perform_action(device: Any = None, action_type="", object_type="", task_uuid=None, action_kwargs=None):
    """
    Performs an action with an object type on a given device
    :param device: The device for which the action is to be performed
    :param action_type: The action to be performed (fetch/push/generate)
    :param object_type: The type of object to be used for this action (backup/config/inventory/report/config_inventory)
    :param task_uuid: The UUID of the associated task for this action
    :param action_kwargs: A dictionary of keyword args to pass to the action to be performed
    :return: True if successful, False otherwise
    """
    if object_type not in ["repo"] and not device:
        easyucs.logger(level="error", message="No device provided")
        sys.exit()

    if action_type not in ["add_device", "calculate_checksums", "change_mode", "claim_to_intersight", "clear_config",
                           "clear_sel_logs", "create_vmedia_policy", "deploy_domain_profile", "download_file", "fetch",
                           "fetch_os_firmware_data", "initial_setup", "generate", "push", "regenerate_certificate",
                           "reset", "reset_device_connector", "sync_to_software_repository", "test_connection"]:
        easyucs.logger(level="error", message="Invalid action type provided")
        sys.exit()

    if object_type not in ["backup", "cache", "config", "config_inventory", "config_inventory_from_xml", "device",
                            "inventory", "repo", "report"]:
        easyucs.logger(level="error", message="Invalid object type provided")
        sys.exit()

    if not task_uuid:
        easyucs.logger(level="error", message="No task_uuid provided")
        sys.exit()

    if action_kwargs is None:
        action_kwargs = {}

    # In case this is a clear, fetch or push operation, we first need to connect to the device
    # (XML-based imports read from a local file and must not attempt a live connection)
    if object_type != "config_inventory_from_xml" and \
            action_type in ["add_device", "change_mode", "clear_config", "clear_sel_logs", "create_vmedia_policy",
                            "deploy_domain_profile", "fetch", "fetch_os_firmware_data", "push",
                            "regenerate_certificate", "reset", "reset_device_connector",
                            "sync_to_software_repository", "test_connection"]:
        if not device.connect(bypass_version_checks=device.metadata.bypass_version_checks):
            easyucs.logger(level="error",
                           message="Failed to connect to " + device.metadata.device_type_long + " device",
                           set_api_error_message=False)
            status_message = easyucs.api_error_message
            if not status_message:
                status_message = "Failed to connect to " + device.metadata.device_type_long + " device"
            easyucs.task_manager.stop_task(uuid=task_uuid, status="failed", status_message=status_message[:255])
            if action_type == "add_device":
                easyucs.device_manager.remove_device(uuid=str(device.metadata.device_uuid))

        # We save device metadata in case they have changed (version, name, is_reachable and timestamp_last_connected)
        if action_type == "add_device":
            if device.metadata.is_reachable:
                easyucs.repository_manager.save_to_repository(object=device)
        else:
            easyucs.repository_manager.save_to_repository(object=device)

        if not device.metadata.is_reachable:
            sys.exit()
    elif object_type == "config_inventory_from_xml":
        # No live connection is made - skip the Connect task step so the task sequence advances correctly
        if device.task is not None:
            device.task.taskstep_manager.skip_taskstep(
                name="ConnectUcsSystemDevice",
                status_message="Skipped - reading config and inventory from local XML file")

    # In case this is a "generate report" operation, we first need to draw the inventory/config plots & save images
    elif action_type in ["generate"]:
        if not device.inventory_manager.draw_inventory(uuid=action_kwargs["inventory"].uuid):
            message_str = "Impossible to draw the inventory with UUID " + str(action_kwargs["inventory"].uuid) + \
                          " of " + device.metadata.device_type_long + " device"
            easyucs.logger(level="error", message=message_str)
            easyucs.task_manager.stop_task(uuid=task_uuid, status="failed", status_message=message_str)
            sys.exit()

        if not easyucs.repository_manager.save_images_to_repository(inventory=action_kwargs["inventory"]):
            message_str = "Impossible to save the images to the repository for inventory with UUID " + \
                          str(action_kwargs["inventory"].uuid) + " of " + device.metadata.device_type_long + " device"
            easyucs.logger(level="error", message=message_str)
            easyucs.task_manager.stop_task(uuid=task_uuid, status="failed", status_message=message_str)
            sys.exit()

        if device.metadata.device_type in ["ucsm"]:
            if not device.config_manager.generate_config_plots(config=action_kwargs["config"]):
                message_str = "Impossible to draw the plots for config with UUID " + \
                              str(action_kwargs["config"].uuid) + " of " + device.metadata.device_type_long + " device"
                easyucs.logger(level="error", message=message_str)
                easyucs.task_manager.stop_task(uuid=task_uuid, status="failed", status_message=message_str)
                sys.exit()

            if not easyucs.repository_manager.save_images_to_repository(config=action_kwargs["config"]):
                message_str = "Impossible to save the plot images to the repository for config with UUID " + \
                              str(action_kwargs["config"].uuid) + " of " + device.metadata.device_type_long + " device"
                easyucs.logger(level="error", message=message_str)
                easyucs.task_manager.stop_task(uuid=task_uuid, status="failed", status_message=message_str)
                sys.exit()

        # We set the directory for the pictures to be the device metadata image_path folder
        action_kwargs["directory"] = device.metadata.images_path

    # In case this is a claim to intersight operation, we first need to connect to both devices
    elif action_type in ["claim_to_intersight"]:

        if not device.connect(bypass_version_checks=device.metadata.bypass_version_checks):
            easyucs.logger(level="error",
                           message="Failed to connect to " + device.metadata.device_type_long + " device")
            status_message = easyucs.api_error_message
            if not status_message:
                status_message = "Failed to connect to " + device.metadata.device_type_long + " device"
            easyucs.task_manager.stop_task(uuid=task_uuid, status="failed", status_message=status_message[:255])
            sys.exit()

        # Since we were able to connect, we save the device metadata in case they have changed (version & name)
        easyucs.repository_manager.save_metadata(metadata=device.metadata)

        intersight_device = action_kwargs["intersight_device"]
        # We need to add this task step to the UCS device as the 'connect()' function will only add it to
        # the Intersight device by default
        device.task.taskstep_manager.start_taskstep(
            name="ConnectIntersightDevice",
            description="Connecting to " + intersight_device.metadata.device_type_long + " device")
        if not intersight_device.connect(bypass_version_checks=device.metadata.bypass_version_checks):
            easyucs.logger(level="error",
                           message="Failed to connect to " + intersight_device.metadata.device_type_long +
                                   " device")
            status_message = easyucs.api_error_message
            if not status_message:
                status_message = "Failed to connect to " + intersight_device.metadata.device_type_long + " device"
            device.task.taskstep_manager.stop_taskstep(name="ConnectIntersightDevice", status="failed",
                                                       status_message=status_message[:255])
            easyucs.task_manager.stop_task(uuid=task_uuid, status="failed", status_message=status_message)
            sys.exit()

        # We were able to connect, we save the Intersight device metadata in case they have changed (version & name)
        easyucs.repository_manager.save_metadata(metadata=intersight_device.metadata)
        if device.task is not None:
            device.task.taskstep_manager.stop_taskstep(
                name="ConnectIntersightDevice", status="successful",
                status_message="Successfully connected to " + intersight_device.metadata.device_type_long + " device " +
                               str(intersight_device.name))

    # In case this is a change mode operation, we need to retrieve the new imm_domain_device after switching the device
    # from UCS Manager mode to Intersight mode.
    if action_type in ["change_mode"]:

        imm_domain_device = device.change_mode(
            clear_sel_logs=action_kwargs.get("clear_sel_logs"),
            decommission_blade_servers=action_kwargs.get("decommission_blade_servers"),
            decommission_chassis=action_kwargs.get("decommission_chassis"),
            decommission_rack_servers=action_kwargs.get("decommission_rack_servers"),
            erase_flexflash=action_kwargs.get("erase_flexflash"),
            erase_virtual_drives=action_kwargs.get("erase_virtual_drives"),
            reset_device_connector=action_kwargs.get("reset_device_connector"),
            unregister_from_central=action_kwargs.get("unregister_from_central")
        )
        if not imm_domain_device:
            message_str = "Impossible to convert the " + device.metadata.device_type_long + " device with UUID " + \
                          str(device.uuid) + " to Intersight using change-mode operation."
            easyucs.logger(level="error", message=message_str)
            easyucs.task_manager.stop_task(uuid=task_uuid, status="failed", status_message=message_str)

            sys.exit()

        # Save the imm domain device in case its attributes have changed (credentials, version, name, is_reachable,
        # and timestamp_last_connected). We use save_to_repository instead of save_metadata because
        # some devices may have sub_devices, which will also be saved when calling save_to_repository().
        easyucs.repository_manager.save_to_repository(object=imm_domain_device)

    manager_target = None
    file_uuid = None
    file_path = None
    if object_type in ["device"] and action_type in ["claim_to_intersight", "clear_config", "clear_sel_logs",
                                                     "deploy_domain_profile", "fetch_os_firmware_data",
                                                     "initial_setup", "regenerate_certificate", "reset",
                                                     "reset_device_connector"]:
        # The operation to perform is a direct call to the function at the device level
        action_target = getattr(device, action_type)

    elif object_type in ["device"] and action_type in ["create_vmedia_policy", "sync_to_software_repository"]:
        # Removing some arguments which are not needed for those actions.
        if "file_uuid" in action_kwargs:
            file_uuid = action_kwargs.pop("file_uuid")

        # The operation to perform is a direct call to the function at the device level
        action_target = getattr(device, action_type)
    elif object_type == "config_inventory":
        action_target = fetch_config_inventory
        if action_kwargs:
            action_kwargs["device"] = device
        else:
            action_kwargs = {
                "device": device
            }
    elif object_type == "config_inventory_from_xml":
        action_target = fetch_config_inventory_from_xml
        if action_kwargs:
            action_kwargs["device"] = device
        else:
            action_kwargs = {
                "device": device
            }
    elif object_type in ["repo"] and action_type in ["calculate_checksums"]:
        action_target = easyucs.repository_manager.repo.calculate_checksums
    elif object_type in ["repo"] and action_type in ["download_file"]:
        action_target = easyucs.repository_manager.repo.download_file
    elif object_type in ["cache"] and action_type in ["fetch_os_firmware_data"]:
        action_target = device.cache_manager.cache.fetch_os_firmware_data
    elif object_type in ["cache"] and action_type in ["fetch"]:
        action_target = device.cache_manager.fetch_cache
    else:
        manager_target = getattr(device, object_type + "_manager", None)
        action_target = getattr(manager_target, action_type + "_" + object_type, None)

    response = None
    if action_target:
        response = action_target(**action_kwargs)

    # In case this is a claim, a clear, a fetch or a push operation, we now need to disconnect from the device
    # (XML-based imports never connected, so skip the Disconnect task step instead)
    if object_type == "config_inventory_from_xml":
        if device.task is not None:
            device.task.taskstep_manager.skip_taskstep(
                name="DisconnectUcsSystemDevice",
                status_message="Skipped - no connection was made (reading from local XML file)")
    elif action_type in ["add_device", "claim_to_intersight", "clear_config", "clear_sel_logs",
                         "deploy_domain_profile", "fetch", "fetch_os_firmware_data", "push",
                         "regenerate_certificate", "reset_device_connector", "sync_to_software_repository",
                         "test_connection"]:
        device.disconnect()

    if action_type in ["reset"]:
        # If erase configuration is successful then we skip the disconnect step otherwise we perform a disconnect.
        if response:
            taskstep_name = ""
            if device.metadata.device_type == "cimc":
                taskstep_name = "DisconnectUcsImcDevice"
            elif device.metadata.device_type == "imm_domain":
                taskstep_name = "DisconnectUcsImcDevice"
            elif device.metadata.device_type == "ucsm":
                taskstep_name = "DisconnectUcsSystemDevice"

            if taskstep_name:
                device.task.taskstep_manager.skip_taskstep(
                    name=taskstep_name,
                    status_message=f"Skipping the disconnect to {device.metadata.device_type_long} device "
                                   f"{device.metadata.device_type_long} since the reset operation was successful"
                )
        else:
            device.disconnect()

    # In case this is a claim to Intersight operation, we now need to disconnect from the Intersight device
    if action_type in ["claim_to_intersight"]:
        intersight_device = action_kwargs["intersight_device"]
        # We need to add this taskstep to the UCS device as the disconnect() function will only add it to
        # the Intersight device by default
        device.task.taskstep_manager.skip_taskstep(
            name="DisconnectIntersightDevice",
            status_message="Disconnecting from " + intersight_device.metadata.device_type_long + " device " +
                           str(intersight_device.name))
        intersight_device.disconnect()

    # In case this is a clear_config operation, we now need to generate the delete summary report
    delete_summary = False
    if action_type in ["clear_config"]:
        delete_summary = device.report_manager.generate_report(output_formats=["json"],
                                                               report_type="delete_summary")
    # In case this is a push operation, we now need to generate the push summary report
    push_summary = False
    if action_type in ["push"] and device.report_manager:
        config = device.config_manager.find_config_by_uuid(uuid=action_kwargs["uuid"])
        push_summary = device.report_manager.generate_report(config=config, output_formats=["json"],
                                                             report_type="push_summary")

    if action_type in ["deploy_domain_profile"]:
        if not response:
            status_message = easyucs.api_error_message
            if not status_message:
                status_message = "Failed to Deploy Domain Profile. Check logs for more details.."
            easyucs.task_manager.stop_task(uuid=task_uuid, status="failed", status_message=status_message[:255])

    if action_type in ["create_vmedia_policy"]:
        if not response:
            status_message = easyucs.api_error_message
            if not status_message:
                status_message = "Failed to create vMedia Policy. Check logs"
            easyucs.task_manager.stop_task(uuid=task_uuid, status="failed", status_message=status_message[:255])

    if action_type in ["fetch_os_firmware_data"]:
        if not response:
            status_message = easyucs.api_error_message
            if not status_message:
                status_message = "Failed to fetch OS and Firmware data objects. Check logs"
            easyucs.task_manager.stop_task(uuid=task_uuid, status="failed", status_message=status_message[:255])

    if action_type in ["sync_to_software_repository"]:
        if response:
            # We add some arguments back to the action kwargs. These arguments are needed to create db object.
            if file_uuid:
                action_kwargs["file_uuid"] = file_uuid
            if file_path:
                action_kwargs["file_path"] = file_path
        else:
            status_message = easyucs.api_error_message
            if not status_message:
                status_message = "Failed to create Software repository Link. Check logs"
            easyucs.task_manager.stop_task(uuid=task_uuid, status="failed", status_message=status_message[:255])

    # We save the object(s) when we get successful response from action_target and none of the tasksteps have failed.
    if response and not easyucs.task_manager.is_any_taskstep_failed(uuid=task_uuid):
        if action_type in ["fetch", "generate"]:
            # We save the newly added object to the repository
            if object_type in ["config_inventory", "config_inventory_from_xml"]:
                # Saving config in repository
                obj = getattr(device.config_manager, "get_latest_config")()
                if obj is not None:
                    easyucs.repository_manager.save_to_repository(object=obj)
                # Saving inventory in repository
                obj = getattr(device.inventory_manager, "get_latest_inventory")()
                if obj is not None:
                    easyucs.repository_manager.save_to_repository(object=obj)
                # Clean up the temporary MIT XML file used for tech-support import
                if object_type == "config_inventory_from_xml" and action_kwargs.get("xml_file_path"):
                    tmp_dir = os.path.dirname(action_kwargs["xml_file_path"])
                    if tmp_dir and os.path.isdir(tmp_dir):
                        shutil.rmtree(tmp_dir, ignore_errors=True)
            elif object_type in ["report"]:
                # Determining the number of reports that have been generated
                number_of_reports = 1
                if "output_formats" in action_kwargs:
                    number_of_reports = len(list(set(action_kwargs["output_formats"])))
                if device.report_manager.report_list:
                    for report in [device.report_manager.report_list[-x] for x in range(1, number_of_reports + 1)]:
                        if not easyucs.repository_manager.save_to_repository(object=report):
                            message_str = "Failed to save report with UUID " + str(report.uuid) + \
                                          " to repository"
                            easyucs.logger(level="error", message=message_str)
                            easyucs.task_manager.stop_task(uuid=task_uuid, status="failed",
                                                           status_message=message_str)
                            sys.exit()
                    # Null the report's references to inventory/config before popping it so that
                    # removing the report from the list drops all remaining strong references.
                    for report in [device.report_manager.report_list[-x] for x in range(1, number_of_reports + 1)]:
                        report.inventory = None
                        report.config = None
                        report.device = None
                        report.element_list = []
                        report.document = None
                    # Free report objects from memory now that they are saved to disk.
                    for _ in range(number_of_reports):
                        if device.report_manager.report_list:
                            device.report_manager.report_list.pop()
                # Unload the inventory and config that were loaded for this report. They are already
                # persisted to disk and keeping them in memory causes large accumulation when generating
                # reports for multiple devices sequentially.
                inventory_to_free = action_kwargs.get("inventory")
                if inventory_to_free is not None:
                    action_kwargs["inventory"] = None
                    try:
                        device.inventory_manager.inventory_list.remove(inventory_to_free)
                    except ValueError:
                        pass
                config_to_free = action_kwargs.get("config")
                if config_to_free is not None:
                    action_kwargs["config"] = None
                    try:
                        device.config_manager.config_list.remove(config_to_free)
                    except ValueError:
                        pass
                # Force a GC cycle to collect any remaining reference cycles, then
                # return freed heap pages to the OS. Without the trim, Python's allocator
                # keeps the virtual memory pages in its own free list and RSS stays high
                # even though all objects have been released. ctypes.CDLL(None) resolves
                # symbols from the current process (glibc on Linux); on other platforms
                # malloc_trim won't be found and the except clause swallows it silently.
                gc.collect()
                try:
                    ctypes.CDLL(None).malloc_trim(0)
                except Exception:
                    pass
            elif object_type in ["cache"]:
                easyucs.repository_manager._save_file(object=response)
            else:
                obj = getattr(manager_target, "get_latest_" + object_type)()
                if obj is not None:
                    easyucs.repository_manager.save_to_repository(object=obj)

        elif action_type in ["clear_config"] and delete_summary:
            # Determining the number of reports that have been generated
            number_of_reports = 1
            if "output_formats" in action_kwargs:
                number_of_reports = len(list(set(action_kwargs["output_formats"])))
            if device.report_manager.report_list:
                for report in [device.report_manager.report_list[-x] for x in range(1, number_of_reports + 1)]:
                    easyucs.repository_manager.save_to_repository(object=report)
            # Save metadata associated with the device to the repository
            # This is done to ensure that updated list of organizations (orgs left after deletion)
            # are reflected in the device table.
            easyucs.repository_manager.save_metadata(metadata=device.metadata)

        elif action_type in ["push"] and push_summary:
            # Determining the number of reports that have been generated
            number_of_reports = 1
            if "output_formats" in action_kwargs:
                number_of_reports = len(list(set(action_kwargs["output_formats"])))
            if device.report_manager.report_list:
                for report in [device.report_manager.report_list[-x] for x in range(1, number_of_reports + 1)]:
                    easyucs.repository_manager.save_to_repository(object=report)

        elif action_type in ["initial_setup"]:
            # Save the device in case its attributes have changed (credentials, version, name, is_reachable,
            # and timestamp_last_connected). We use save_to_repository instead of save_metadata because
            # some devices may have sub_devices, which will also be saved when calling save_to_repository().
            easyucs.repository_manager.save_to_repository(object=device)

        elif action_type in ["fetch_os_firmware_data"]:
            # We save the OS and Firmware data to the cache
            device.cache_manager.save_to_cache(cache_key="os_firmware")

        elif action_type in ["sync_to_software_repository"]:
            # We save software repository link details to reposynctodevice table

            sync_metadata = easyucs.repository_manager.repo.create_reposynctodevice_metadata(
                device=device, **action_kwargs
            )
            easyucs.repository_manager.save_metadata(sync_metadata)

    sys.exit()


def response_handle(response=None, code: int | None = 400, mimetype="application/json"):
    """
    Function to create response objects based on the "response" and "response code".
    :param response: (str, dict, list) Response to be sent
    :param code: Response Code
    :param mimetype: Mimetype of the response being sent
    :return: Response object.
    """
    # Some callers pass an HTTPException.code (typed int | None); fall back to 500 when it is None,
    # since a missing code in an error path indicates an unexpected server-side condition.
    if code is None:
        code = 500
    response_code_mapping = {
        200: "OK",
        400: "Invalid Request",
        404: "Resource Not Found",
        500: "Internal Server Error"
    }
    if response is not None:
        if response.__class__.__name__ == "str":
            dict_response = {"message": response}
        elif response.__class__.__name__ in ["dict", "list"]:
            dict_response = response
        else:
            dict_response = {"message": str(response)}
    else:
        dict_response = {"message": response_code_mapping.get(code, "Unexpected Error Code")}

    json_response = json.dumps(dict_response, indent=4)
    final_response = Response(response=json_response, status=code, mimetype=mimetype)
    return final_response


def terminate_task_scheduler(sig, frame):
    # Guard against re-entrancy: pressing CTRL+C several times must not run this handler again.
    # Re-entering previously raised SystemExit from inside _thread._shutdown() while it was joining
    # threads, producing the confusing "Exception ignored while joining a thread" traceback.
    global _shutdown_in_progress
    if _shutdown_in_progress:
        return
    _shutdown_in_progress = True

    # Restore the default SIGINT handler so that, should anything below block, a subsequent CTRL+C
    # performs the OS default (immediate terminate) instead of re-entering this handler.
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    easyucs.logger(level="info", message="Received interrupt signal - Stopping task scheduler thread '" +
                                         str(easyucs.task_manager.scheduler_thread.name) + "'")

    # Stop the scheduler thread gracefully. It is blocked on a blocking pending_tasks.get(), so simply
    # setting the stop flag is not enough: we also inject the "__stop_scheduler__" sentinel to wake it
    # up so the while-loop in task_scheduler() can observe the flag and exit cleanly.
    # NOTE: the previous implementation used PyThreadState_SetAsyncExc(SystemExit) here, which does NOT
    # work for a thread blocked inside queue.get() - an async exception is only delivered when the target
    # thread next executes Python bytecode, never while it is parked in a C-level blocking call. As a
    # result the scheduler never stopped and the process hung until CTRL+C was pressed again.
    try:
        easyucs.task_manager._stop_scheduler = True
        easyucs.task_manager.pending_tasks.put({"task_uuid": "__stop_scheduler__"})
        easyucs.task_manager.scheduler_thread.join(timeout=5)
    except Exception:
        pass

    sys.exit(0)


# Register the SIGINT handler so a CTRL+C on the dev server stops the scheduler and exits cleanly.
# Under embedded WSGI servers (e.g. mod_wsgi/Apache) the module may be imported outside the main
# thread, where signal.signal() raises ValueError. In that case the host server owns process/signal
# handling anyway, so we simply skip registration instead of breaking the import.
try:
    signal.signal(signal.SIGINT, terminate_task_scheduler)
except ValueError:
    pass


def terminate_thread(thread):
    """
    Terminates a Python thread from another thread
    :param thread: a threading.Thread instance
    :return: True if successfully terminated the thread, False otherwise
    """
    # https://stackoverflow.com/questions/52631315/python-properly-kill-exit-futures-thread
    if not thread.is_alive():
        return

    exc = ctypes.py_object(SystemExit)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread.ident), exc)
    if res == 0:
        easyucs.logger(level="error", message=f"Unable to terminate the thread {thread.name}. " +
                                              f"Non existent thread id")
        return False
    elif res > 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(thread.ident, None)
        easyucs.logger(level="error", message=f"Unable to terminate the thread {thread.name}. " +
                                              f"PyThreadState_SetAsyncExc failed")
        return False
    return True


@app.route("/")
def hello():
    return "EasyUCS API"


@app.route("/backups", methods=['GET'])
# @cross_origin()
def backups():
    if request.method == 'GET':
        try:
            filter_attribute = request.args.get("filter_attribute", None)
            filter_type = request.args.get("filter_type", None)
            filter_value = request.args.get("filter_value", None)

            if filter_attribute is None or filter_type is None or filter_value is None:
                filter = None
            else:
                filter = [filter_attribute, filter_type, filter_value]

            order_by_attribute = request.args.get("order_by_attribute", None)
            order_by_direction = request.args.get("order_by_direction", None)

            if order_by_attribute is None or order_by_direction is None:
                order_by = None
            else:
                order_by = (order_by_attribute, order_by_direction)

            page_size = request.args.get("page_size", None)
            page_number = int(request.args.get("page_number", 0))

            backup_dict = get_object_from_db(object_type="backup", filter=filter, page_size=page_size,
                                             page_number=page_number, order_by=order_by)

            if backup_dict:
                response = response_handle(backup_dict, 200)
            else:
                response = response_handle(code=500,
                                           response="Unexpected error while fetching data from DB. Please check logs.")

        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/configs", methods=['GET'])
# @cross_origin()
def configs():
    if request.method == 'GET':
        try:
            filter_attribute = request.args.get("filter_attribute", None)
            filter_type = request.args.get("filter_type", None)
            filter_value = request.args.get("filter_value", None)

            if filter_attribute is None or filter_type is None or filter_value is None:
                filter = None
            else:
                filter = [filter_attribute, filter_type, filter_value]

            order_by_attribute = request.args.get("order_by_attribute", None)
            order_by_direction = request.args.get("order_by_direction", None)

            if order_by_attribute is None or order_by_direction is None:
                order_by = None
            else:
                order_by = (order_by_attribute, order_by_direction)

            page_size = request.args.get("page_size", None)
            page_number = int(request.args.get("page_number", 0))

            config_dict = get_object_from_db(object_type="config", filter=filter, page_size=page_size,
                                             page_number=page_number, order_by=order_by)

            if config_dict:
                response = response_handle(config_dict, 200)
            else:
                response = response_handle(code=500,
                                           response="Unexpected error while fetching data from DB. Please check logs.")

        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices", methods=['GET', 'POST'])
# @cross_origin()
def devices():
    if request.method == 'GET':
        try:
            filter_attribute = request.args.get("filter_attribute", None)
            filter_type = request.args.get("filter_type", None)
            filter_value = request.args.get("filter_value", None)
            device_type = request.args.get("device_type", None)

            if filter_attribute is None or filter_type is None or filter_value is None:
                if device_type:
                    if device_type not in ["cimc", "imm_domain", "intersight", "ucsc", "ucsm"]:
                        response = response_handle(code=400, response="Invalid device type")
                        return response
                    filter = ["device_type", "==", device_type]
                else:
                    filter = None
            else:
                filter = [filter_attribute, filter_type, filter_value]

            order_by_attribute = request.args.get("order_by_attribute", None)
            order_by_direction = request.args.get("order_by_direction", None)

            if order_by_attribute is None or order_by_direction is None:
                order_by = None
            else:
                order_by = (order_by_attribute, order_by_direction)

            page_size = request.args.get("page_size", None)
            page_number = int(request.args.get("page_number", 0))

            device_dict = get_object_from_db(object_type="device", filter=filter, page_size=page_size,
                                             page_number=page_number, order_by=order_by)

            if device_dict:
                response = response_handle(device_dict, 200)
            else:
                response = response_handle(code=500,
                                           response="Unexpected error while fetching data from DB. Please check logs.")

        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    elif request.method == 'POST':
        try:
            payload = request.json

            # Check if payload valid
            if not validate_json(json_data=payload, schema_path="api/specs/device_post.json", logger=easyucs):
                response = response_handle(code=400, response="Invalid payload")
                return response

            # Since this is a new device, we generate a new UUID (useful in case of private key to store)
            new_device_uuid = uuid.uuid4()

            # We first need to take care of the private key if there is one given. We need to store it in the repository
            private_key_path = None
            if "private_key" in payload:
                private_key = payload["private_key"].replace('\r', '')
                private_key_path = easyucs.repository_manager.save_key_to_repository(private_key=private_key,
                                                                                     device_uuid=new_device_uuid)

                @after_this_request
                def cleanup(response):
                    """
                    Function to delete the private key file at the end of this request if the requests fails
                    """
                    if response.status_code not in [200]:
                        if private_key_path and os.path.exists(private_key_path):
                            os.remove(private_key_path)
                    return response
            user_label = None
            if "user_label" in payload:
                user_label = payload["user_label"]
            device_type = None
            if "device_type" in payload:
                device_type = payload["device_type"]
            key_id = None
            if "key_id" in payload:
                key_id = payload["key_id"]
            password = None
            if "password" in payload:
                password = payload["password"]
            target = None
            if "target" in payload:
                target = payload["target"]
            username = None
            if "username" in payload:
                username = payload["username"]
            use_proxy = False
            if "use_proxy" in payload:
                use_proxy = payload["use_proxy"]
            bypass_version_checks = False
            if "bypass_version_checks" in payload:
                bypass_version_checks = payload["bypass_version_checks"]
            bypass_connection_checks = False
            if "bypass_connection_checks" in payload:
                bypass_connection_checks = payload["bypass_connection_checks"]

            if use_proxy:
                if device_type != "intersight":
                    response = response_handle(response=f"Use Proxy is only applicable for Intersight devices",
                                               code=400)
                    return response

                proxy_details = read_json_file(file_path=os.path.join(EASYUCS_ROOT, "proxy_settings.json"),
                                               logger=easyucs) or {}
                if not proxy_details.get("proxy_url", ""):
                    response = response_handle(response=f"Please set 'Proxy URL' in Proxy Settings and try again",
                                               code=400)
                    return response

            if easyucs.device_manager.add_device(device_type=device_type, uuid=new_device_uuid, target=target,
                                                 username=username, password=password, key_id=key_id,
                                                 private_key_path=private_key_path, use_proxy=use_proxy,
                                                 user_label=user_label, bypass_version_checks=bypass_version_checks,
                                                 bypass_connection_checks=bypass_connection_checks):
                device = easyucs.device_manager.get_latest_device()

                if not bypass_connection_checks:
                    # Raise an error when device is not connectable
                    if not device.connect(bypass_version_checks=device.metadata.bypass_version_checks):
                        response_message = easyucs.api_error_message
                        if not response_message:
                            response_message = "Failed to connect to " + device.metadata.device_type_long + " device"
                        response = response_handle(response=response_message, code=400)
                        easyucs.device_manager.remove_device(uuid=new_device_uuid)
                        return response

                easyucs.repository_manager.save_to_repository(object=device)
                device_metadata = {"device_uuid": str(device.uuid),
                                   "timestamp": device.metadata.timestamp.isoformat()[:-3] + 'Z'}
                for attribute in ["bypass_connection_checks", "bypass_version_checks", "device_name",
                                  "device_type", "device_type_long", "device_version", "easyucs_version", "is_hidden",
                                  "is_system", "key_id", "system_usage", "target", "username", "user_label"]:
                    if getattr(device.metadata, attribute) not in [None, ""]:
                        device_metadata[attribute] = getattr(device.metadata, attribute)
                device_dict = {"device": device_metadata}
                response = response_handle(device_dict, 200)
            else:
                response = response_handle(code=400)
        except BadRequest as err:
            response = response_handle(code=err.code, response=str(err.description))
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response


@app.route("/devices/actions/import_tech_support", methods=['POST'])
def devices_actions_import_tech_support():
    """Accepts a tech-support bundle archive, auto-detects the device type from its contents,
    creates or reuses the matching device, and triggers an async XML-based config & inventory fetch.

    Currently supported device types: UCS System (UCSM).
    Other device types will be rejected with HTTP 400 until support is added.
    """

    # Maximum accepted upload size (bytes). Adjust here if a larger limit is ever needed.
    TECH_SUPPORT_MAX_SIZE_BYTES = 2 * 1024 * 1024 * 1024  # 2 GB

    # ── Device-type detection table ───────────────────────────────────────────────
    # Each entry maps a set of inner archive basenames (used for detection) to the
    # parameters needed to extract mit.xml and schedule the fetch task.
    #
    # Keys:
    #   inner_archive_names : set of filenames to look for inside the outer bundle
    #   device_type         : EasyUCS device type string (e.g. "ucsm")
    #   task_name           : task_library.json key for the fetch task
    #   supported           : False until the code path is actually implemented
    #
    # To add a new device type in the future, add a new entry here and implement
    # the corresponding _import_<device_type>_tech_support() helper below.
    TECH_SUPPORT_DETECTION_TABLE = [
        {
            "inner_archive_names": {"UCSM_A_TechSupport.tar.gz", "UCSM_B_TechSupport.tar.gz"},
            "device_type": "ucsm",
            "task_name": "FetchConfigInventoryUcsSystem",
            "supported": True,
        }
    ]

    if request.method != 'POST':
        return response_handle(code=500, response="Invalid HTTP method")

    try:
        if "tech_support_file" not in request.files:
            return response_handle(code=400, response="Missing 'tech_support_file' in request")

        uploaded_file = request.files["tech_support_file"]
        if not uploaded_file.filename:
            return response_handle(code=400, response="Invalid filename")

        # secure_filename() is used both for safe on-disk storage and for the
        # sanitized display name persisted in config/inventory metadata.
        # Retaining the raw user-supplied name is avoided to prevent stored XSS
        # if any downstream UI/API consumer renders the metadata field without escaping.
        filename = secure_filename(uploaded_file.filename)
        if not filename:
            return response_handle(code=400, response="Invalid filename")

        # Validate extension
        is_tar = filename.endswith(".tar") or filename.endswith(".tar.gz") or filename.endswith(".tgz")
        is_xml = filename.endswith(".xml")
        is_xml_gz = filename.endswith(".xml.gz") or (
            filename.endswith(".gz") and not filename.endswith(".tar.gz"))
        if not (is_tar or is_xml or is_xml_gz):
            return response_handle(code=400,
                                   response="Invalid file type. Expected .tar, .tar.gz, .tgz, .xml or .xml.gz")

        # Check file size via Content-Length header (early rejection before saving)
        content_length = request.content_length
        if content_length is not None and content_length > TECH_SUPPORT_MAX_SIZE_BYTES:
            return response_handle(code=400, response="File exceeds maximum allowed size of 2 GB")

        # Save the bundle to a unique subdirectory under the repository tmp folder
        upload_id = str(uuid.uuid4())
        tmp_dir = os.path.abspath(os.path.join(
            EASYUCS_ROOT,
            easyucs.repository_manager.REPOSITORY_FOLDER_NAME,
            easyucs.repository_manager.REPOSITORY_TMP_FOLDER_NAME,
            upload_id))
        os.makedirs(tmp_dir, exist_ok=True)

        @after_this_request
        def cleanup_on_error(response):
            """Remove the temp directory if the request does not end with a successful 200."""
            if response.status_code != 200:
                shutil.rmtree(tmp_dir, ignore_errors=True)
            return response

        outer_bundle_path = os.path.join(tmp_dir, filename)
        uploaded_file.save(outer_bundle_path)

        # Double-check size after save (in case Content-Length was absent)
        if os.path.getsize(outer_bundle_path) > TECH_SUPPORT_MAX_SIZE_BYTES:
            return response_handle(code=400, response="File exceeds maximum allowed size of 2 GB")

        if is_xml or is_xml_gz:
            # ── Direct XML upload: mit.xml or mit.xml.gz is always UCSM ─────────────
            ucsm_entry = next(
                (e for e in TECH_SUPPORT_DETECTION_TABLE if e["device_type"] == "ucsm"), None)
            if ucsm_entry is None or not ucsm_entry["supported"]:
                return response_handle(code=400, response="UCSM tech-support import is not supported")

            if is_xml_gz:
                import gzip as _gzip
                mit_xml_path = os.path.join(tmp_dir, "mit.xml")
                try:
                    with _gzip.open(outer_bundle_path) as gz_f:
                        with open(mit_xml_path, "wb") as xml_f:
                            xml_f.write(gz_f.read())
                except Exception as err:
                    return response_handle(code=400, response="Could not decompress file: " + str(err))
                os.remove(outer_bundle_path)
            else:
                mit_xml_path = outer_bundle_path

            return _import_ucsm_tech_support(
                outer_bundle_path=None,
                tmp_dir=tmp_dir,
                detected_entry=ucsm_entry,
                mit_xml_path=mit_xml_path,
                sanitized_filename=filename
            )

        # ── Step 1: Open the outer tar and auto-detect the device type ───────────────
        if not tarfile.is_tarfile(outer_bundle_path):
            return response_handle(code=400, response="Uploaded file is not a valid tar archive")

        with tarfile.open(outer_bundle_path) as outer_tar:
            outer_member_names = {os.path.basename(m.name) for m in outer_tar.getmembers() if m.isfile()}

        detected_entry = None
        for entry in TECH_SUPPORT_DETECTION_TABLE:
            if outer_member_names & entry["inner_archive_names"]:
                detected_entry = entry
                break

        if detected_entry is None:
            known_signatures = ", ".join(
                name
                for entry in TECH_SUPPORT_DETECTION_TABLE
                for name in sorted(entry["inner_archive_names"])
            )
            return response_handle(
                code=400,
                response="Could not identify the device type from the tech-support bundle. "
                         "No recognised inner archive found (expected one of: " + known_signatures + ")"
            )

        if not detected_entry["supported"]:
            return response_handle(
                code=400,
                response="Tech-support bundles for device type '" + detected_entry["device_type"] +
                         "' are not yet supported"
            )

        # Dispatch to the device-type-specific import handler
        return _import_ucsm_tech_support(
            outer_bundle_path=outer_bundle_path,
            tmp_dir=tmp_dir,
            detected_entry=detected_entry,
            sanitized_filename=filename
        )

    except BadRequest as err:
        return response_handle(code=err.code, response=str(err.description))
    except Exception as err:
        return response_handle(code=500, response=str(err))


def _import_ucsm_tech_support(outer_bundle_path, tmp_dir, detected_entry, mit_xml_path=None,
                              sanitized_filename=None):
    """
    Handles the UCSM-specific part of a tech-support import after the device type
    has been detected by devices_actions_import_tech_support().

    When called from a tar bundle upload, extracts mit.xml from the largest UCSM_A/B
    inner archive. When called from a direct .xml or .xml.gz upload, mit_xml_path
    is already set and the extraction steps are skipped.

    :param outer_bundle_path: Full path to the already-saved outer tarball, or None
                              for direct XML uploads.
    :param tmp_dir: Temporary directory owning the upload; cleaned up on failure.
    :param detected_entry: Entry from TECH_SUPPORT_DETECTION_TABLE for 'ucsm'.
    :param mit_xml_path: Pre-extracted path to mit.xml. If provided, tar extraction
                         is skipped entirely.
    :param sanitized_filename: Sanitized filename (via secure_filename) of the uploaded
                               tech-support bundle, stored in config/inventory metadata
                               as tech_support_filename. The raw user-supplied name is
                               not persisted to avoid stored XSS.
    :return: Flask response object.
    """
    if mit_xml_path is None:
        # ── Steps 1-2: Extract mit.xml from the outer tar bundle ─────────────────
        with tarfile.open(outer_bundle_path) as outer_tar:
            inner_candidates = [
                m for m in outer_tar.getmembers()
                if os.path.basename(m.name) in detected_entry["inner_archive_names"]
                and m.isfile()
            ]

        # Prefer the larger archive (usually contains the active FI)
        inner_candidates.sort(key=lambda m: m.size, reverse=True)

        for inner_member in inner_candidates:
            inner_tar_path = os.path.join(tmp_dir, os.path.basename(inner_member.name))
            with tarfile.open(outer_bundle_path) as outer_tar:
                inner_file_obj = outer_tar.extractfile(inner_member)
                if inner_file_obj is None:
                    continue
                with open(inner_tar_path, "wb") as f:
                    f.write(inner_file_obj.read())

            if not tarfile.is_tarfile(inner_tar_path):
                os.remove(inner_tar_path)
                continue

            mit_gz_member = None
            with tarfile.open(inner_tar_path) as inner_tar:
                for m in inner_tar.getmembers():
                    if os.path.basename(m.name) == "mit.xml.gz" and m.isfile():
                        mit_gz_member = m
                        break

            if mit_gz_member is None:
                os.remove(inner_tar_path)
                continue

            import gzip as _gzip
            mit_xml_path = os.path.join(tmp_dir, "mit.xml")
            with tarfile.open(inner_tar_path) as inner_tar:
                gz_obj = inner_tar.extractfile(mit_gz_member)
                if gz_obj is not None:
                    with _gzip.open(gz_obj) as gz_f:
                        with open(mit_xml_path, "wb") as xml_f:
                            xml_f.write(gz_f.read())

            os.remove(inner_tar_path)
            break  # Successfully extracted mit.xml

        os.remove(outer_bundle_path)

        if not mit_xml_path or not os.path.isfile(mit_xml_path):
            return response_handle(code=400,
                                   response="Could not find or extract mit.xml from the tech-support bundle")

    # ── Step 3: Read topSystem to get device name, management IP and firmware version ──
    import xml.etree.ElementTree as _ET
    top_system_name = None
    top_system_address = None
    top_system_version = None
    top_system_current_time = None
    try:
        for _event, _elem in _ET.iterparse(mit_xml_path, events=("end",)):
            if _elem.tag == "topSystem":
                top_system_name = _elem.get("name")
                top_system_address = _elem.get("address")
                top_system_current_time = _elem.get("currentTime")
            elif _elem.tag == "firmwareRunning" and "sys/mgmt/fw-system" in _elem.get("dn", ""):
                top_system_version = _elem.get("version")
            elif (_elem.tag == "versionApplication" and
                  _elem.get("dn", "") == "sys/version/application" and
                  not top_system_version):
                # Fallback: versionApplication is always present, even on older UCSM
                # releases where firmwareRunning at sys/mgmt/fw-system may be absent.
                top_system_version = _elem.get("version")
            _elem.clear()
            # Break only after topSystem has been seen (address is set) and version is found,
            # so non-standard XML element ordering cannot skip topSystem processing.
            if top_system_address and top_system_version is not None:
                break
    except Exception as err:
        return response_handle(code=400, response="Failed to parse mit.xml: " + str(err))

    # Parse currentTime into a datetime object (format: YYYY-MM-DDTHH:MM:SS[.mmm])
    tech_support_timestamp = None
    if top_system_current_time:
        for _fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
            try:
                tech_support_timestamp = datetime.datetime.strptime(top_system_current_time, _fmt)
                break
            except ValueError:
                pass
        if tech_support_timestamp is None:
            easyucs.logger(level="warning",
                           message="Could not parse topSystem currentTime '" + top_system_current_time +
                                   "'; config and inventory timestamps will be set to import time")

    if not top_system_address:
        return response_handle(code=400, response="Could not find topSystem address in mit.xml")

    # ── Step 4: Find or create the UcsSystem device ───────────────────────────────
    existing_device = None
    device_metadata_list = easyucs.repository_manager.get_metadata(
        object_type="device",
        filter=("device_type", "==", detected_entry["device_type"])
    )
    for dm in device_metadata_list:
        if dm.target == top_system_address and dm.device_name == top_system_name:
            existing_device = load_object(object_type="device", object_uuid=str(dm.uuid))
            break

    if existing_device:
        device = existing_device
        easyucs.logger(
            message="Reusing existing UcsSystem device with UUID " + str(device.uuid) +
                    " for tech-support import (target=" + top_system_address +
                    ", name=" + str(top_system_name) + ")")
    else:
        new_device_uuid = uuid.uuid4()
        if not easyucs.device_manager.add_device(
            device_type=detected_entry["device_type"],
            uuid=new_device_uuid,
            target=top_system_address,
            username="admin",
            password="",
            bypass_connection_checks=True,
            bypass_version_checks=True
        ):
            return response_handle(code=500,
                                   response="Failed to create UcsSystem device for target " + top_system_address)
        device = easyucs.device_manager.get_latest_device()
        device.name = top_system_name
        device.metadata.device_name = top_system_name
        if top_system_version:
            device.metadata.device_version = top_system_version
        easyucs.repository_manager.save_to_repository(object=device)
        easyucs.logger(
            message="Created new UcsSystem device with UUID " + str(device.uuid) +
                    " for tech-support import (target=" + top_system_address +
                    ", name=" + str(top_system_name) + ")")

    # ── Step 5: Schedule the async fetch task ─────────────────────────────────────
    task_uuid = easyucs.task_manager.add_task(
        name=detected_entry["task_name"],
        device_name=str(device.name),
        device_uuid=str(device.uuid)
    )
    pending_task = {
        "task_uuid": task_uuid,
        "action_type": "fetch",
        "object_type": "config_inventory_from_xml",
        "timeout": timeout_values["import_tech_support"],
        "action_kwargs": {
            "xml_file_path": mit_xml_path,
            "force": False,
            "tech_support_timestamp": tech_support_timestamp,
            "tech_support_filename": sanitized_filename
        }
    }
    if not easyucs.task_manager.add_to_pending_tasks(pending_task):
        return response_handle(
            response="Error while scheduling the task. Task Queue might be Full. Try again after some time.",
            code=400
        )

    return response_handle(
        response={"task": str(task_uuid), "device_uuid": str(device.uuid)},
        code=200
    )


@app.route("/devices/actions/add", methods=['POST'])
# Method to add multiple devices from CSV file
def devices_actions_add():
    if request.method == 'POST':
        try:
            if "devices_file" not in request.files:
                response = response_handle(code=400, response="Invalid payload")
                return response

            file = request.files['devices_file']

            # Validating the type of file
            file_type = (file.filename or "").split(".")
            if len(file_type) <= 1 or file_type[1] != "csv":
                response = response_handle(code=400, response="Invalid file type")
                return response

            # Mapping the contents of csv with column headers as key
            device_data = list(csv.DictReader(StringIO(file.read().decode("utf-8-sig"))))
            if not device_data:
                response = response_handle(code=400,
                                           response="Relevant device credentials not found in the uploaded CSV")
                return response

            # Removing duplicate values
            device_data_list = []
            for data in device_data:
                if data not in device_data_list:
                    device_data_list.append(data)

            # Expected headers of the CSV file
            headers = ['Device Type', 'Target', 'Username', 'Password']
            # Validating the headers of CSV file
            csv_headers = list(device_data[0].keys())
            if csv_headers != headers:
                response = response_handle(
                    code=400,
                    response="The column headings of uploaded CSV file are invalid"
                )
                return response

            # Regular expression for validating IPv4/FQDN
            ipv4_fqdn_pattern = (r'^((?:(25[0-5]|(?:2[0-4]|1[0-9]|[1-9]|)[0-9])(\.(?!$)|)){4}$)|'
                                 r'(?=^.{4,253}$)(^((?!-)[a-zA-Z0-9-]{0,62}[a-zA-Z0-9]\.)+[a-zA-Z]{2,63})$')

            # Validating the contents of the CSV file
            for row in device_data_list:
                if row["Device Type"] not in ["ucsm", "ucsc", "cimc", "imm_domain"]:
                    response = response_handle(
                        code=400,
                        response="The device type in CSV file should be ucsm/ucsc/cimc/imm_domain"
                    )
                    return response

                if not re.match(ipv4_fqdn_pattern, row["Target"]):
                    response = response_handle(
                        code=400,
                        response=f"The target {row['Target']} provided is not a valid IP or FQDN"
                    )
                    return response

                if not row["Username"] or not row["Password"]:
                    response = response_handle(
                        code=400,
                        response="Username and Password fields cannot be empty"
                    )
                    return response

            # Get devices from DB
            device_dict = get_object_from_db(object_type="device")
            db_devices = []
            if device_dict:
                for device in device_dict["devices"]:
                    if "username" in device and device["device_type"] != "intersight":
                        db_devices.append(device["target"] + device["username"])

            # Adding the device if not present in the DB
            device_list = []
            @after_this_request
            def cleanup(response):
                if response.status_code != 200:
                    for device in device_list:
                        easyucs.device_manager.remove_device(uuid=str(device.metadata.device_uuid))
                return response

            for row in device_data_list:
                unique_id = row["Target"] + row["Username"]
                if unique_id not in db_devices:
                    if easyucs.device_manager.add_device(device_type=row["Device Type"], target=row["Target"],
                                                         username=row["Username"], password=row["Password"]):
                        device_list.append(easyucs.device_manager.get_latest_device())
                    else:
                        response = response_handle(code=400, response=f"Failed to add device: {row['Target']}.")
                        return response
                else:
                    easyucs.logger(level="debug", message="Target device " + row['Target'] + " was already added.")

            if not device_list:
                response = response_handle(code=400, response=f"No new device(s) found in CSV (some devices "
                                                              f"might already be present in the database.)")
                return response

            task_uuid_list = []
            for device in device_list:
                task_uuid = None
                if device.metadata.device_type == "cimc":
                    task_uuid = easyucs.task_manager.add_task(name="TestConnectionUcsImc",
                                                              device_name=str(device.metadata.name),
                                                              device_uuid=str(device.metadata.device_uuid))
                elif device.metadata.device_type == "imm_domain":
                    task_uuid = easyucs.task_manager.add_task(name="TestConnectionImmDomain",
                                                              device_name=str(device.metadata.name),
                                                              device_uuid=str(device.metadata.device_uuid))
                elif device.metadata.device_type == "ucsc":
                    task_uuid = easyucs.task_manager.add_task(name="TestConnectionUcsCentral",
                                                              device_name=str(device.metadata.name),
                                                              device_uuid=str(device.metadata.device_uuid))
                elif device.metadata.device_type == "ucsm":
                    task_uuid = easyucs.task_manager.add_task(name="TestConnectionUcsSystem",
                                                              device_name=str(device.metadata.name),
                                                              device_uuid=str(device.metadata.device_uuid))

                pending_task = {
                    "task_uuid": task_uuid,
                    "action_type": "add_device",
                    "object_type": "device",
                    "timeout": timeout_values["add_device"]
                }
                if not easyucs.task_manager.add_to_pending_tasks(pending_task):
                    easyucs.logger(level="error",
                                   message=f"Error while scheduling the task for {device.metadata.target}. "
                                           f"Task Queue might be Full. Try again after some time.", code=400)

                task_uuid_list.append(str(task_uuid))

            response = response_handle(response={"tasks": task_uuid_list}, code=200)
            return response

        except BadRequest as err:
            response = response_handle(code=err.code, response=str(err.description))
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/actions/claim_to_intersight", methods=['POST'])
# @cross_origin()
def devices_actions_claim_to_intersight():
    if request.method == 'POST':
        try:
            payload = request.json

            # Check if payload valid
            if not validate_json(json_data=payload, schema_path="api/specs/devices_actions_claim_to_intersight.json",
                                 logger=easyucs):
                response = response_handle(code=400, response="Invalid payload")
                return response

            device_uuid_list = payload.get("device_uuids", [])
            intersight_device_uuid = payload.get("intersight_device_uuid", None)

            device_list = []

            for device_uuid in device_uuid_list:
                device = load_object(object_type="device", object_uuid=device_uuid)
                if device:
                    device_list.append(device)
                else:
                    response = response_handle(response="Device with UUID " + device_uuid + " not found", code=404)
                    return response

            intersight_device = load_object(object_type="device", object_uuid=intersight_device_uuid)
            if not intersight_device:
                response = response_handle(response="Intersight device with UUID " + intersight_device_uuid +
                                                    " not found", code=404)
                return response

            action_kwargs = {
                "access_mode": payload.get("access_mode"),
                "intersight_device": intersight_device,
                "proxy_details": payload.get("proxy_details")
            }

            try:
                # We loop through the devices and create a task for each
                task_uuid_list = []
                for device in device_list:
                    if device.metadata.device_type in ["cimc"]:
                        task_uuid = easyucs.task_manager.add_task(name="ClaimToIntersightUcsImc",
                                                                  device_name=str(device.name),
                                                                  device_uuid=str(device.uuid),
                                                                  target_device_uuid=str(intersight_device.uuid))
                    elif device.metadata.device_type in ["imm_domain"]:
                        task_uuid = easyucs.task_manager.add_task(name="ClaimToIntersightImmDomain",
                                                                  device_name=str(device.name),
                                                                  device_uuid=str(device.uuid),
                                                                  target_device_uuid=str(intersight_device.uuid))
                    elif device.metadata.device_type in ["ucsm"]:
                        task_uuid = easyucs.task_manager.add_task(name="ClaimToIntersightUcsSystem",
                                                                  device_name=str(device.name),
                                                                  device_uuid=str(device.uuid),
                                                                  target_device_uuid=str(intersight_device.uuid))
                    else:
                        response = response_handle(response="Unsupported device type (" + device.metadata.device_type +
                                                            ") for device with UUID " + str(device.uuid), code=500)
                        return response
                    task_uuid_list.append(str(task_uuid))

                # We schedule the claim to Intersight actions through the scheduler
                for task_uuid in task_uuid_list:
                    pending_task = {
                        "task_uuid": task_uuid,
                        "action_type": "claim_to_intersight",
                        "object_type": "device",
                        "timeout": timeout_values["claim_to_intersight"],
                        "action_kwargs": action_kwargs
                    }
                    if not easyucs.task_manager.add_to_pending_tasks(pending_task):
                        response = response_handle(response="Error while scheduling the task. Task Queue might be Full."
                                                            " Try again after some time.", code=400)
                        return response

            except Exception as err:
                response = response_handle(response="Error while claiming device to Intersight: " + str(err), code=500)
                return response

            response = response_handle(response={"tasks": task_uuid_list}, code=200)

        except BadRequest as err:
            response = response_handle(code=err.code, response=str(err.description))
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/actions/create_from_files", methods=['POST'])
def devices_actions_create_from_files():
    if request.method == 'POST':
        try:
            payload = request.form

            # Validate form fields against JSON schema
            if payload and not validate_json(json_data=payload,
                                             schema_path="api/specs/devices_actions_create_from_files_post.json",
                                             logger=easyucs):
                response = response_handle(code=400, response="Invalid payload")
                return response

            supported_device_types = ["ucsm", "ucsc", "cimc", "intersight"]
            device_type = payload.get("device_type") if payload else None

            # Read the config file (always required)
            if "config_file" not in request.files:
                response = response_handle(code=400, response="config_file is required")
                return response

            # Read the config file and extract its EasyUCS metadata header
            try:
                json_config = request.files["config_file"].read().decode("utf-8")
                config_json = json.loads(json_config)
            except Exception as err:
                response = response_handle(code=400,
                                           response="Error reading config_file: " + str(err))
                return response

            try:
                config_header = config_json["easyucs"]["metadata"][0]
            except (KeyError, IndexError, TypeError):
                response = response_handle(
                    code=400,
                    response="config_file is missing the EasyUCS metadata header (easyucs.metadata)")
                return response

            # config_file must be an EasyUCS config export
            if config_header.get("file_type") != "config":
                response = response_handle(
                    code=400,
                    response="Uploaded config_file is not an EasyUCS config export "
                             "(file_type must be 'config')")
                return response

            # Read the inventory file (optional)
            json_inventory = None
            inventory_header = None
            inventory_file = request.files.get("inventory_file")
            if inventory_file and inventory_file.filename:
                try:
                    json_inventory = inventory_file.read().decode("utf-8")
                    inventory_json = json.loads(json_inventory)
                except Exception as err:
                    response = response_handle(code=400,
                                               response="Error reading inventory_file: " + str(err))
                    return response

                try:
                    inventory_header = inventory_json["easyucs"]["metadata"][0]
                except (KeyError, IndexError, TypeError):
                    response = response_handle(
                        code=400,
                        response="inventory_file is missing the EasyUCS metadata header "
                                 "(easyucs.metadata)")
                    return response

                if inventory_header.get("file_type") != "inventory":
                    response = response_handle(
                        code=400,
                        response="Uploaded inventory_file is not an EasyUCS inventory export "
                                 "(file_type must be 'inventory')")
                    return response

            # If device_type was not supplied, auto-detect it from the uploaded files
            if not device_type:
                config_device_type = config_header.get("device_type")
                inventory_device_type = inventory_header.get("device_type") if inventory_header else None

                if config_device_type and inventory_device_type:
                    if config_device_type != inventory_device_type:
                        response = response_handle(
                            code=400,
                            response="Conflicting device_type in provided files: config_file has '" +
                                     config_device_type + "' and inventory_file has '" +
                                     inventory_device_type +
                                     "'. Please specify device_type explicitly.")
                        return response
                    device_type = config_device_type
                elif config_device_type:
                    device_type = config_device_type
                elif inventory_device_type:
                    device_type = inventory_device_type
                else:
                    response = response_handle(
                        code=400,
                        response="device_type could not be determined from the provided files. "
                                 "Please specify device_type explicitly. Must be one of: " +
                                 ", ".join(supported_device_types))
                    return response

            # Validate the resolved device_type
            if device_type not in supported_device_types:
                response = response_handle(
                    code=400,
                    response="device_type must be one of: " + ", ".join(supported_device_types))
                return response

            # Cross-validate config_file device_type against the resolved device_type
            config_device_type = config_header.get("device_type")
            if config_device_type and config_device_type != device_type:
                response = response_handle(
                    code=400,
                    response="config_file device_type ('" + str(config_device_type) +
                             "') does not match the requested device_type '" + device_type +
                             "'. Please upload a " + device_type + " config file.")
                return response

            # device_name is read from the config metadata header
            device_name = config_header.get("device_name")
            if not device_name:
                response = response_handle(code=400,
                                           response="Missing device_name in config_file metadata")
                return response

            # Cross-validate inventory_file device_type and device_name
            if inventory_header:
                inventory_device_type = inventory_header.get("device_type")
                if inventory_device_type and inventory_device_type != device_type:
                    response = response_handle(
                        code=400,
                        response="inventory_file device_type ('" + str(inventory_device_type) +
                                 "') does not match the requested device_type '" + device_type +
                                 "'. Please upload a " + device_type + " inventory file.")
                    return response

                inventory_device_name = inventory_header.get("device_name")
                if inventory_device_name and inventory_device_name != device_name:
                    response = response_handle(
                        code=400,
                        response="device_name mismatch between config_file ('" + str(device_name) +
                                 "') and inventory_file ('" + str(inventory_device_name) + "')")
                    return response

            target = "www.intersight.com" if device_type == "intersight" else "0.0.0.0"

            new_device_uuid = None
            device = None
            for existing_metadata in easyucs.repository_manager.get_metadata(object_type="device"):
                if (existing_metadata.device_type == device_type and
                        existing_metadata.target == target and
                        existing_metadata.device_name == device_name):
                    easyucs.logger(
                        level="info",
                        message=f"{device_type} device '{device_name}' already exists "
                                f"(UUID {existing_metadata.uuid}), reusing it"
                    )
                    device = load_object(object_type="device", object_uuid=str(existing_metadata.uuid))
                    if not device:
                        response = response_handle(code=500,
                                                   response="Found existing device but could not load it")
                        return response
                    break

            # Create a new device if no existing match was found
            if not device:
                new_device_uuid = uuid.uuid4()
                # UCSM / UCS Central / CIMC: placeholder credentials the user can update later.
                # Intersight: username/password left as None (no key required for a device).
                username = "admin" if device_type in ["ucsm", "ucsc", "cimc"] else None
                password = ""     if device_type in ["ucsm", "ucsc", "cimc"] else None

                # Create the device record without any live connection
                if not easyucs.device_manager.add_device(
                    device_type=device_type,
                    uuid=new_device_uuid,
                    target=target,
                    username=username,
                    password=password,
                    key_id=None,
                    private_key_path=None,
                    bypass_connection_checks=True,
                    bypass_version_checks=True
                ):
                    response = response_handle(code=500,
                                               response="Failed to create " + device_type + " device")
                    return response

                device = easyucs.device_manager.get_latest_device()
                device.name = device_name
                device.metadata.device_name = device_name
                easyucs.repository_manager.save_to_repository(object=device)
                easyucs.logger(
                    message="Created " + device_type + " device '" + device_name +
                            "' with UUID " + str(device.uuid) + " (target=" + target + ")"
                )

            # Build device portion of the response
            device_metadata = {
                "device_uuid": str(device.uuid),
                "timestamp": device.metadata.timestamp.isoformat()[:-3] + 'Z'
            }
            for attribute in ["bypass_connection_checks", "bypass_version_checks", "device_name",
                              "device_type", "device_type_long", "device_version", "easyucs_version",
                              "imm_migration_version", "is_hidden", "target", "user_label"]:
                if getattr(device.metadata, attribute) not in [None, ""]:
                    device_metadata[attribute] = getattr(device.metadata, attribute)

            # Import config file (mandatory — json_config was already read & validated above)
            config = device.config_manager.import_config(
                import_format="json", config=json_config, force_custom=False
            )
            if not config:
                if new_device_uuid:
                    easyucs.device_manager.remove_device(uuid=new_device_uuid)
                response_message = easyucs.api_error_message
                if not response_message:
                    response_message = "Failed to import config_file into the device"
                response = response_handle(code=500, response=response_message)
                return response

            easyucs.repository_manager.save_to_repository(object=config)

            # Import inventory file (optional — json_inventory was already read & validated above)
            if json_inventory is not None:
                inventory = device.inventory_manager.import_inventory(
                    import_format="json", inventory=json_inventory, force_custom=False
                )
                if not inventory:
                    if new_device_uuid:
                        easyucs.device_manager.remove_device(uuid=new_device_uuid)
                    response = response_handle(code=500,
                                               response="Failed to import inventory_file into the device")
                    return response

                easyucs.repository_manager.save_to_repository(object=inventory)

            response = response_handle({"device": device_metadata}, 200)

        except BadRequest as err:
            response = response_handle(code=err.code, response=str(err.description))
        except Exception as err:
            easyucs.logger(level="exception", message="Unexpected error while creating device")
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/actions/delete", methods=['POST'])
# @cross_origin()
def devices_actions_delete():
    if request.method == 'POST':
        try:
            payload = request.json

            # Check if payload valid
            if not validate_json(json_data=payload, schema_path="api/specs/devices_actions_delete.json",
                                 logger=easyucs):
                response = response_handle(code=400, response="Invalid payload")
                return response

            device_uuid_list = payload["device_uuids"]

            devices_metadata_list = []

            for device_uuid in device_uuid_list:
                device_metadata_list = easyucs.repository_manager.get_metadata(object_type="device", uuid=device_uuid)
                if len(device_metadata_list) == 1:
                    devices_metadata_list.append(device_metadata_list[0])
                else:
                    response = response_handle(response="Device with UUID " + device_uuid + " not found", code=404)
                    return response

            if easyucs.repository_manager.delete_bulk_from_repository(metadata_list=devices_metadata_list,
                                                                      delete_keys=True):
                response = response_handle(code=200)
            else:
                response = response_handle(code=500, response="Could not delete devices from repository")

        except BadRequest as err:
            response = response_handle(code=err.code, response=str(err.description))
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/actions/reset_device_connector", methods=['POST'])
# @cross_origin()
def devices_actions_reset_device_connector():
    if request.method == 'POST':
        try:
            payload = request.json

            # Check if payload valid
            if not validate_json(json_data=payload, schema_path="api/specs/devices_actions_reset_device_connector.json",
                                 logger=easyucs):
                response = response_handle(code=400, response="Invalid payload")
                return response

            device_uuid_list = payload.get("device_uuids", [])

            device_list = []

            for device_uuid in device_uuid_list:
                device = load_object(object_type="device", object_uuid=device_uuid)
                if device:
                    device_list.append(device)
                else:
                    response = response_handle(response="Device with UUID " + device_uuid + " not found", code=404)
                    return response

            try:
                # We loop through the devices and create a task for each
                task_uuid_list = []
                for device in device_list:
                    if device.metadata.device_type in ["cimc"]:
                        task_uuid = easyucs.task_manager.add_task(name="ResetDeviceConnectorUcsImc",
                                                                  device_name=str(device.name),
                                                                  device_uuid=str(device.uuid))
                    elif device.metadata.device_type in ["imm_domain"]:
                        task_uuid = easyucs.task_manager.add_task(name="ResetDeviceConnectorImmDomain",
                                                                  device_name=str(device.name),
                                                                  device_uuid=str(device.uuid))
                    elif device.metadata.device_type in ["ucsm"]:
                        task_uuid = easyucs.task_manager.add_task(name="ResetDeviceConnectorUcsSystem",
                                                                  device_name=str(device.name),
                                                                  device_uuid=str(device.uuid))
                    else:
                        response = response_handle(response="Unsupported device type (" + device.metadata.device_type +
                                                            ") for device with UUID " + str(device.uuid), code=500)
                        return response
                    task_uuid_list.append(str(task_uuid))

                # We schedule the Reset Device Connector actions through the scheduler
                for task_uuid in task_uuid_list:
                    pending_task = {
                        "task_uuid": task_uuid,
                        "action_type": "reset_device_connector",
                        "object_type": "device",
                        "timeout": timeout_values["reset_device_connector"]
                    }
                    if not easyucs.task_manager.add_to_pending_tasks(pending_task):
                        response = response_handle(response="Error while scheduling the task. Task Queue might be Full."
                                                            " Try again after some time.", code=400)
                        return response

            except Exception as err:
                response = response_handle(response="Error while resetting Device Connector: " + str(err), code=500)
                return response

            response = response_handle(response={"tasks": task_uuid_list}, code=200)

        except BadRequest as err:
            response = response_handle(code=err.code, response=str(err.description))
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/types", methods=['GET'])
# @cross_origin()
def devices_types():
    if request.method == 'GET':
        try:
            # Ordered by display_name
            actions = {
                "imm_domain": {
                    "display_name": "IMM Domain",
                    "available_actions": ["claim_to_intersight", "reset",
                                          "reset_device_connector", "test_connection"]
                },
                "intersight": {
                    "display_name": "Intersight",
                    "available_actions": ["clear_config", "test_connection"]
                },
                "cimc": {
                    "display_name": "UCS IMC",
                    "available_actions": ["claim_to_intersight", "clear_sel_logs", "clear_user_sessions",
                                          "erase_all_virtual_drives", "erase_all_flexflash", "regenerate_certificate",
                                          "reset", "reset_device_connector", "set_all_drives_status",
                                          "test_connection"]
                },
                "ucsc": {
                    "display_name": "UCS Central",
                    "available_actions": ["clear_user_sessions", "test_connection"]
                },
                "ucsm": {
                    "display_name": "UCS System",
                    "available_actions": ["claim_to_intersight", "clear_sel_logs", "clear_user_sessions",
                                          "erase_all_virtual_drives", "erase_all_flexflash",
                                          "regenerate_certificate", "reset", "reset_device_connector",
                                          "test_connection"]
                }
            }

            actions_dict = {"types": actions}

            response = response_handle(actions_dict, 200)

        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/<device_uuid>", methods=['GET', 'DELETE', 'PUT'])
# @cross_origin()
def device_uuid(device_uuid):
    if request.method == 'GET':
        try:
            filter_attribute = request.args.get("filter_attribute", None)
            filter_type = request.args.get("filter_type", None)
            filter_value = request.args.get("filter_value", None)

            if filter_attribute is None or filter_type is None or filter_value is None:
                filter = None
            else:
                filter = [filter_attribute, filter_type, filter_value]

            order_by_attribute = request.args.get("order_by_attribute", None)
            order_by_direction = request.args.get("order_by_direction", None)

            if order_by_attribute is None or order_by_direction is None:
                order_by = None
            else:
                order_by = (order_by_attribute, order_by_direction)

            page_size = request.args.get("page_size", None)
            page_number = int(request.args.get("page_number", 0))

            device_dict = get_object_from_db(object_type="device", uuid=device_uuid, filter=filter, page_size=page_size,
                                             page_number=page_number, order_by=order_by)

            if device_dict:
                response = response_handle(device_dict, 200)
            else:
                response = response_handle(code=400, response=f"Could not find device with UUID {device_uuid}")

        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    elif request.method == 'DELETE':
        try:
            device_metadata_list = easyucs.repository_manager.get_metadata(object_type="device", uuid=device_uuid)
            if len(device_metadata_list) == 1:
                if easyucs.repository_manager.delete_from_repository(metadata=device_metadata_list[0],
                                                                     delete_keys=True):
                    response = response_handle(code=200)
                else:
                    response = response_handle(code=500, response="Could not delete device from repository")
            else:
                response = response_handle(response="Device with UUID " + device_uuid + " not found", code=404)
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    elif request.method == 'PUT':
        try:
            device_metadata_list = easyucs.repository_manager.get_metadata(object_type="device", uuid=device_uuid)
            if len(device_metadata_list) == 1:
                payload = request.json
                # Check if payload valid
                if not validate_json(json_data=payload, schema_path="api/specs/device_put.json", logger=easyucs):
                    response = response_handle(code=400, response="Invalid payload")
                    return response

                updating_fields = ["target", "bypass_connection_checks", "bypass_version_checks", "user_label"]
                if device_metadata_list[0].device_type == "intersight":
                    updating_fields.extend(["key_id", "use_proxy"])
                else:
                    updating_fields.extend(["username", "password"])

                if payload.get("use_proxy", False):
                    if device_metadata_list[0].device_type != "intersight":
                        response = response_handle(response=f"Use Proxy is only applicable for Intersight devices",
                                                   code=400)
                        return response

                    proxy_details = read_json_file(file_path=os.path.join(EASYUCS_ROOT, "proxy_settings.json"),
                                                   logger=easyucs) or {}
                    if not proxy_details.get("proxy_url", ""):
                        response = response_handle(response=f"Please set 'Proxy URL' in Proxy Settings and try again",
                                                   code=400)
                        return response

                for attribute in updating_fields:
                    if attribute in payload:
                        setattr(device_metadata_list[0], attribute, payload[attribute])
                        if device_metadata_list[0].parent is not None:
                            # We also change the attributes in the object if it is linked to the metadata
                            setattr(device_metadata_list[0].parent, attribute, payload[attribute])

                # In case the private key has been changed, we need to save it to the repository again
                if device_metadata_list[0].device_type == "intersight" and "private_key" in payload:
                    private_key = payload["private_key"].replace('\r', '')
                    easyucs.repository_manager.save_key_to_repository(private_key=private_key,
                                                                      device_uuid=device_metadata_list[0].uuid)

                # Need to call add_device to make sure that handle is updated with the latest credentials
                device = easyucs.device_manager.find_device_by_uuid(uuid=device_uuid)
                if device:
                    easyucs.device_manager.remove_device(uuid=device_uuid)
                    easyucs.device_manager.add_device(metadata=device_metadata_list[0])
                else:
                    easyucs.device_manager.add_device(metadata=device_metadata_list[0])

                device = easyucs.device_manager.get_latest_device()

                if not payload.get("bypass_connection_checks", False):
                    # Raise an error when device is not connectable
                    if not device.connect(bypass_version_checks=device.metadata.bypass_version_checks):
                        response_message = easyucs.api_error_message
                        if not response_message:
                            response_message = "Failed to connect to " + device.metadata.device_type_long + " device"
                        response = response_handle(response=response_message, code=400)
                        easyucs.device_manager.remove_device(uuid=device_uuid)
                        return response

                easyucs.repository_manager.save_metadata(metadata=device_metadata_list[0])

                device_metadata = {"device_uuid": str(device_metadata_list[0].uuid),
                                   "timestamp": device_metadata_list[0].timestamp.isoformat()[:-3] + 'Z'}
                for attribute in ["bypass_connection_checks", "bypass_version_checks", "device_name",
                                  "device_type", "device_type_long", "device_version", "easyucs_version", "is_hidden",
                                  "is_system", "key_id", "system_usage", "target", "username", "user_label"]:
                    if getattr(device_metadata_list[0], attribute) not in [None, ""]:
                        device_metadata[attribute] = getattr(device_metadata_list[0], attribute)
                device_dict = {"device": device_metadata}
                response = response_handle(device_dict, 200)
                return response
            else:
                response = response_handle(response="Device with UUID " + device_uuid + " not found", code=404)
        except BadRequest as err:
            response = response_handle(code=err.code, response=str(err.description))
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/<device_uuid>/actions", methods=['GET'])
# @cross_origin()
def device_uuid_actions(device_uuid):
    if request.method == 'GET':
        try:
            device_metadata_list = easyucs.repository_manager.get_metadata(object_type="device", uuid=device_uuid)
            if len(device_metadata_list) == 1:
                device_type = device_metadata_list[0].device_type

                actions = None
                if device_type in ["cimc"]:
                    actions = ["claim_to_intersight", "clear_sel_logs", "clear_user_sessions",
                               "erase_all_virtual_drives", "erase_all_flexflash", "regenerate_certificate", "reset",
                               "reset_device_connector", "set_all_drives_status", "test_connection"]
                elif device_type in ["imm_domain"]:
                    actions = ["claim_to_intersight", "reset", "reset_device_connector", "test_connection"]
                elif device_type in ["intersight"]:
                    actions = ["clear_config", "test_connection"]
                elif device_type in ["ucsc"]:
                    actions = ["clear_user_sessions", "test_connection"]
                elif device_type in ["ucsm"]:
                    actions = ["claim_to_intersight", "clear_sel_logs", "clear_user_sessions",
                               "erase_all_virtual_drives", "erase_all_flexflash",
                               "regenerate_certificate", "reset", "reset_device_connector", "test_connection"]

                actions_dict = {"actions": actions}

                response = response_handle(actions_dict, 200)
            else:
                response = response_handle(response="Device with UUID " + device_uuid + " not found", code=404)
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/<device_uuid>/actions/change_mode", methods=['POST'])
# @cross_origin()
def device_uuid_actions_change_mode(device_uuid):
    if request.method == 'POST':
        try:
            payload = request.json

            # Check if payload valid
            if not validate_json(json_data=payload, schema_path="api/specs/device_change_mode_post.json", logger=easyucs):
                response = response_handle(response="Invalid Payload", code=400)
                return response

            device = load_object(object_type="device", object_uuid=device_uuid)
            if device:
                if device.task is not None:
                    response = response_handle(response="Device already has a task running: " + str(device.task.uuid),
                                               code=500)
                    return response

                if payload.get("password") == device.password:
                    if device.metadata.device_type != "ucsm":
                        response = response_handle(
                            response="Change mode operation is only supported for UCS Manager devices", code=400)
                        return response

                    task_uuid = easyucs.task_manager.add_task(name="ChangeModeToIntersightUcsSystem",
                                                              device_name=str(device.name),
                                                              device_uuid=str(device.uuid))
                    action_kwargs = {
                        "clear_sel_logs": payload.get("clear_sel_logs", False),
                        "decommission_blade_servers": payload.get("decommission_blade_servers", False),
                        "decommission_chassis": payload.get("decommission_chassis", True),
                        "decommission_rack_servers": payload.get("decommission_rack_servers", True),
                        "erase_flexflash": payload.get("erase_flexflash", False),
                        "erase_virtual_drives": payload.get("erase_virtual_drives", False),
                        "reset_device_connector": payload.get("reset_device_connector", True),
                        "unregister_from_central": payload.get("unregister_from_central", False)
                    }

                    pending_task = {
                        "task_uuid": task_uuid,
                        "action_type": "change_mode",
                        "object_type": "device",
                        "timeout": timeout_values["change_mode"],
                        "action_kwargs": action_kwargs
                    }

                    if not easyucs.task_manager.add_to_pending_tasks(pending_task):
                        response = response_handle(response="Error while scheduling the task. Task Queue might be Full."
                                                            " Try again after some time.", code=400)
                        return response
                    response = response_handle(response={"task": str(task_uuid)}, code=200)

                else:
                    response = response_handle(response="Admin password mismatch", code=400)
            else:
                response = response_handle(response="Device not found with UUID: " + device_uuid, code=404)
        except BadRequest as err:
            response = response_handle(code=err.code, response=str(err.description))
        except Exception as err:
            easyucs.logger(level="error", message="Unexpected error while changing the mode of the device!")
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/<device_uuid>/actions/claim_to_intersight", methods=['POST'])
# @cross_origin()
def device_uuid_actions_claim_to_intersight(device_uuid):
    if request.method == 'POST':
        try:
            payload = request.json

            # Check if payload valid
            if payload:
                if not validate_json(json_data=payload, schema_path="api/specs/device_claim_to_intersight_post.json",
                                     logger=easyucs):
                    response = response_handle(code=400, response="Invalid payload")
                    return response

            intersight_device_uuid = payload.get("intersight_device_uuid", None)

            device = load_object(object_type="device", object_uuid=device_uuid)
            if device:
                # We need to find & potentially load the intersight device
                intersight_device = load_object(object_type="device", object_uuid=intersight_device_uuid)

                if not intersight_device:
                    response = response_handle(response="Could not find Intersight device with UUID: " +
                                                        str(intersight_device_uuid), code=404)
                    return response

                action_kwargs = {
                    "access_mode": payload.get("access_mode"),
                    "intersight_device": intersight_device,
                    "proxy_details": payload.get("proxy_details")
                }

                try:
                    # We create a new task
                    if device.metadata.device_type in ["cimc"]:
                        task_uuid = easyucs.task_manager.add_task(name="ClaimToIntersightUcsImc",
                                                                  device_name=str(device.name),
                                                                  device_uuid=str(device.uuid),
                                                                  target_device_uuid=str(intersight_device.uuid))
                    elif device.metadata.device_type in ["imm_domain"]:
                        task_uuid = easyucs.task_manager.add_task(name="ClaimToIntersightImmDomain",
                                                                  device_name=str(device.name),
                                                                  device_uuid=str(device.uuid),
                                                                  target_device_uuid=str(intersight_device.uuid))
                    elif device.metadata.device_type in ["ucsm"]:
                        task_uuid = easyucs.task_manager.add_task(name="ClaimToIntersightUcsSystem",
                                                                  device_name=str(device.name),
                                                                  device_uuid=str(device.uuid),
                                                                  target_device_uuid=str(intersight_device.uuid))
                    else:
                        response = response_handle(response="Unsupported device type", code=500)
                        return response

                    # We schedule the claim to Intersight action through the scheduler
                    pending_task = {
                        "task_uuid": task_uuid,
                        "action_type": "claim_to_intersight",
                        "object_type": "device",
                        "timeout": timeout_values["claim_to_intersight"],
                        "action_kwargs": action_kwargs
                    }
                    if not easyucs.task_manager.add_to_pending_tasks(pending_task):
                        response = response_handle(response="Error while scheduling the task. Task Queue might be Full."
                                                            " Try again after some time.", code=400)
                        return response

                except Exception as err:
                    response = response_handle(response="Error while claiming devices to Intersight: " + str(err),
                                               code=500)
                    return response

                response = response_handle(response={"task": str(task_uuid)}, code=200)
            else:
                response = response_handle(response="Device not found with UUID: " + device_uuid, code=404)
        except BadRequest as err:
            response = response_handle(code=err.code, response=str(err.description))
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/<device_uuid>/actions/clear_config", methods=['POST'])
# @cross_origin()
def device_uuid_actions_clear_config(device_uuid):
    if request.method == 'POST':
        try:
            payload = request.json

            # Check if payload valid
            if payload:
                if not validate_json(json_data=payload, schema_path="api/specs/clear_config_post.json", logger=easyucs):
                    response = response_handle(code=400, response="Invalid payload")
                    return response

            device = load_object(object_type="device", object_uuid=device_uuid)
            if device:
                orgs = payload.get("orgs")
                if orgs:
                    validation_result = device.validate_orgs_for_clear_config(orgs=orgs)
                    if not validation_result:
                        response_message = easyucs.api_error_message
                        return response_handle(response=response_message, code=400)

                action_kwargs = {
                    "orgs": orgs,
                    "delete_equipment_tags_and_labels": payload.get("delete_equipment_tags_and_labels", False),
                    "delete_path_tags": payload.get("delete_path_tags", False),
                    "delete_settings": payload.get("delete_settings", False),
                    "force": payload.get("force", False)
                }

                try:
                    # We create a new task
                    if device.metadata.device_type in ["intersight"]:
                        task_uuid = easyucs.task_manager.add_task(name="ClearConfigIntersight",
                                                                  device_name=str(device.name),
                                                                  device_uuid=str(device.uuid))
                    else:
                        response = response_handle(response="Unsupported device type", code=500)
                        return response

                    # Resetting the delete_summary dictionary. This is done to avoid having legacy data when
                    # deleting multiple times.
                    device.delete_summary_manager._init_delete_summary()

                    # We schedule the clear config action through the scheduler
                    pending_task = {
                        "task_uuid": task_uuid,
                        "action_type": "clear_config",
                        "object_type": "device",
                        "timeout": timeout_values["clear_config"],
                        "action_kwargs": action_kwargs
                    }
                    if not easyucs.task_manager.add_to_pending_tasks(pending_task):
                        response = response_handle(response="Error while scheduling the task. Task Queue might be Full."
                                                            " Try again after some time.", code=400)
                        return response
                except Exception as err:
                    response = response_handle(response="Error while performing clear config: " + str(err),
                                               code=500)
                    return response
                response = response_handle(response={"task": str(task_uuid)}, code=200)

            else:
                response = response_handle(response="Device not found with UUID: " + device_uuid, code=404)

        except BadRequest as err:
            response = response_handle(code=err.code, response=str(err.description))
        except Exception as err:
            response = response_handle(response="Error while performing clear config: " + str(err), code=500)
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/<device_uuid>/actions/clear_sel_logs", methods=['POST'])
# @cross_origin()
def device_uuid_actions_clear_sel_logs(device_uuid):
    if request.method == 'POST':
        try:
            device = load_object(object_type="device", object_uuid=device_uuid)
            if device:
                try:
                    # We create a new task
                    if device.metadata.device_type in ["cimc"]:
                        task_uuid = easyucs.task_manager.add_task(name="ClearSelLogsUcsImc",
                                                                  device_name=str(device.name),
                                                                  device_uuid=str(device.uuid))
                    elif device.metadata.device_type in ["ucsm"]:
                        task_uuid = easyucs.task_manager.add_task(name="ClearSelLogsUcsSystem",
                                                                  device_name=str(device.name),
                                                                  device_uuid=str(device.uuid))
                    else:
                        response = response_handle(response="Unsupported device type", code=500)
                        return response
                    # We schedule the clear SEL logs action through the scheduler
                    pending_task = {
                        "task_uuid": task_uuid,
                        "action_type": "clear_sel_logs",
                        "object_type": "device",
                        "timeout": timeout_values["clear_sel_logs"]
                    }
                    if not easyucs.task_manager.add_to_pending_tasks(pending_task):
                        response = response_handle(response="Error while scheduling the task. Task Queue might be Full."
                                                            " Try again after some time.", code=400)
                        return response
                except Exception as err:
                    response = response_handle(response="Error while performing clear SEL logs: " + str(err),
                                               code=500)
                    return response
                response = response_handle(response={"task": str(task_uuid)}, code=200)

            else:
                response = response_handle(response="Device not found with UUID: " + device_uuid, code=404)

        except BadRequest as err:
            response = response_handle(code=err.code, response=str(err.description))
        except Exception as err:
            response = response_handle(response="Error while performing clear SEL logs: " + str(err), code=500)
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/<device_uuid>/actions/deploy_domain_profile", methods=['POST'])
# @cross_origin()
def device_uuid_actions_deploy_domain_profile(device_uuid):
    if request.method == 'POST':
        try:
            payload = request.json
            # Check if payload valid
            if payload:
                if not validate_json(json_data=payload,
                                     schema_path="api/specs/device_actions_deploy_domain_profile.json",
                                     logger=easyucs):
                    response = response_handle(code=400, response="Invalid payload")
                    return response
            device = load_object(object_type="device", object_uuid=device_uuid)
            if not device:
                response = response_handle(response="Device not found with UUID: " + device_uuid, code=404)
                return response

            action_kwargs = {
                "domain_profile_name": payload.get("domain_profile_name", None),
                "imm_domain_name": payload.get("imm_domain_name", None),
                "org_name": payload.get("org_name", None)
            }

            try:
                # We create a new task
                if device.metadata.device_type in ["intersight"]:
                    task_uuid = easyucs.task_manager.add_task(
                        name="DeployDomainProfileIntersight", device_name=str(device.name),
                        device_uuid=str(device.uuid)
                    )
                else:
                    response = response_handle(response="Unsupported device type", code=500)
                    return response

                # We schedule the  action through the scheduler
                pending_task = {
                    "task_uuid": task_uuid,
                    "action_type": "deploy_domain_profile",
                    "object_type": "device",
                    "timeout": timeout_values["deploy_domain_profile"],
                    "action_kwargs": action_kwargs
                }
                if not easyucs.task_manager.add_to_pending_tasks(pending_task):
                    response = response_handle(response="Error while scheduling the task. Task Queue might be Full."
                                                        " Try again after some time.", code=400)
                    return response

            except Exception as err:
                response = response_handle(response="Error while performing assign and deployment of domain profiles. " +
                                                    str(err), code=500)
                return response

            response = response_handle(response={"task": str(task_uuid)}, code=200)
        except BadRequest as err:
            response = response_handle(code=err.code, response=str(err.description))
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/<device_uuid>/actions/fetch_config_and_inventory", methods=['POST'])
# @cross_origin()
def device_uuid_actions_fetch_config_and_inventory(device_uuid):
    if request.method == 'POST':
        try:
            payload = request.json

            # Check if payload valid
            if payload:
                if not validate_json(json_data=payload, schema_path="api/specs/fetch.json",
                                     logger=easyucs):
                    response = response_handle(code=400, response="Invalid payload")
                    return response

            force = payload.get("force", False) if payload else False

            device = load_object(object_type="device", object_uuid=device_uuid)
            if device:
                try:
                    # We create a new task
                    if device.metadata.device_type in ["ucsm"]:
                        task_uuid = easyucs.task_manager.add_task(name="FetchConfigInventoryUcsSystem",
                                                                  device_name=str(device.name),
                                                                  device_uuid=str(device.uuid))
                    elif device.metadata.device_type in ["ucsc"]:
                        task_uuid = easyucs.task_manager.add_task(name="FetchConfigInventoryUcsCentral",
                                                                  device_name=str(device.name),
                                                                  device_uuid=str(device.uuid))
                    else:
                        response = response_handle(response="Unsupported device type", code=500)
                        return response

                    # We schedule the fetch config & inventory action through the scheduler
                    pending_task = {
                        "task_uuid": task_uuid,
                        "action_type": "fetch",
                        "object_type": "config_inventory",
                        "timeout": timeout_values["fetch_config_inventory"],
                        "action_kwargs": {"force": force}
                    }
                    if not easyucs.task_manager.add_to_pending_tasks(pending_task):
                        response = response_handle(response="Error while scheduling the task. Task Queue might be Full."
                                                            " Try again after some time.", code=400)
                        return response

                except Exception as err:
                    response = response_handle(response="Error while fetching config and inventory: " + str(err),
                                               code=500)
                    return response

                response = response_handle(response={"task": str(task_uuid)}, code=200)
            else:
                response = response_handle(response="Device not found with UUID: " + device_uuid, code=404)
        except BadRequest as err:
            response = response_handle(code=err.code, response=str(err.description))
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/<device_uuid>/latest_config_and_inventory", methods=['GET'])
# @cross_origin()
def device_uuid_latest_config_and_inventory(device_uuid):
    if request.method == 'GET':
        try:
            page_size = request.args.get("page_size", None)
            page_number = int(request.args.get("page_number", 0))
            config_metadata_list = []
            configs_metadata = easyucs.repository_manager.get_metadata(object_type="config", device_uuid=device_uuid,
                                                                       limit=page_size, page=page_number)
            if len(configs_metadata) > 0:
                for config_metadata in configs_metadata:
                    # We return the first live fetched config, a tech-support imported config, or an uploaded non-edited config
                    if config_metadata.origin in ("live", "import") or \
                            (config_metadata.origin == "file" and not config_metadata.is_custom):
                        config = {"device_uuid": str(config_metadata.device_uuid),
                                  "timestamp": config_metadata.timestamp.isoformat()[:-3] + 'Z',
                                  "uuid": str(config_metadata.uuid)}
                        for attribute in ["category", "device_version", "easyucs_version",
                                          "is_custom", "name", "origin", "revision", "subcategory", "url"]:
                            if getattr(config_metadata, attribute) not in [None, ""]:
                                config[attribute] = getattr(config_metadata, attribute)
                        for attribute in ["source_config_uuid", "source_device_uuid", "source_inventory_uuid"]:
                            if getattr(config_metadata, attribute) not in [None, ""]:
                                config[attribute] = str(getattr(config_metadata, attribute))
                        config_metadata_list.append(config)
                        break

            inventory_metadata_list = []
            inventories_metadata = easyucs.repository_manager.get_metadata(object_type="inventory",
                                                                           device_uuid=device_uuid, limit=page_size,
                                                                           page=page_number)
            if len(inventories_metadata) > 0:
                for inventory_metadata in inventories_metadata:
                    # We return the first live fetched inventory, a tech-support imported inventory, or an uploaded non-edited inventory
                    if inventory_metadata.origin in ("live", "import") or \
                            (inventory_metadata.origin == "file" and not inventory_metadata.is_custom):
                        inventory = {"device_uuid": str(inventory_metadata.device_uuid),
                                     "timestamp": inventory_metadata.timestamp.isoformat()[:-3] + 'Z',
                                     "uuid": str(inventory_metadata.uuid)}
                        for attribute in ["device_version", "easyucs_version",
                                          "is_custom", "name", "origin"]:
                            if getattr(inventory_metadata, attribute) not in [None, ""]:
                                inventory[attribute] = getattr(inventory_metadata, attribute)
                        inventory_metadata_list.append(inventory)
                        break

            latest_config_and_inventory = {"config": config_metadata_list,
                                           "inventory": inventory_metadata_list}

            response = response_handle(latest_config_and_inventory, 200)
        except Exception as err:
            easyucs.logger(level="exception", message="Unexpected error while fetching latest config and inventory!")
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/<device_uuid>/actions/initial_setup", methods=['POST'])
# @cross_origin()
def device_uuid_actions_initial_setup(device_uuid):
    if request.method == 'POST':
        try:
            payload = request.json
            # Check if payload valid
            if payload:
                if not validate_json(json_data=payload, schema_path="api/specs/device_initial_setup_post.json",
                                     logger=easyucs):
                    response = response_handle(code=400, response="Invalid payload")
                    return response
            else:
                response = response_handle(code=400, response="Missing payload")
                return response

            device = load_object(object_type="device", object_uuid=device_uuid)
            if device:
                config_uuid = payload.get("config_uuid")
                config = load_object(object_type="config", object_uuid=config_uuid, device=device)
                target_admin_password = getattr(getattr(device, "metadata", None), "password", None)

                if not target_admin_password:
                    response = response_handle(code=400, response="Failed to fetch device password")
                    return response

                if config:
                    if device.metadata.device_type == "cimc":
                        task_uuid = easyucs.task_manager.add_task(name="InitialSetupUcsImc",
                                                                  device_name=str(device.name),
                                                                  device_uuid=str(device.uuid))
                    elif device.metadata.device_type == "imm_domain":
                        task_uuid = easyucs.task_manager.add_task(name="InitialSetupImmDomain",
                                                                  device_name=str(device.name),
                                                                  device_uuid=str(device.uuid))
                    elif device.metadata.device_type == "ucsm":
                        task_uuid = easyucs.task_manager.add_task(name="InitialSetupUcsSystem",
                                                                  device_name=str(device.name),
                                                                  device_uuid=str(device.uuid))
                    else:
                        response = response_handle(code=400, response=f"Initial setup is not supported for "
                                                                      f"{device.metadata.device_type_long} device")
                        return response

                    action_kwargs = {
                        "config": config,
                        "target_admin_password": target_admin_password
                    }
                    if device.metadata.device_type == "cimc":
                        action_kwargs["imc_ip"] = payload.get("imc_ip")
                    else:
                        action_kwargs["fi_ip_list"] = payload.get("fi_ip_list")

                    pending_task = {
                        "task_uuid": task_uuid,
                        "action_type": "initial_setup",
                        "object_type": "device",
                        "timeout": timeout_values["initial_setup"],
                        "action_kwargs": action_kwargs
                    }

                    if not easyucs.task_manager.add_to_pending_tasks(pending_task):
                        response = response_handle(code=400, response="Error while scheduling the task. Task Queue might be Full."
                                                   " Try again after some time.")
                    else:
                        response = response_handle(code=200, response={"task": str(task_uuid)})
                else:
                    response = response_handle(code=400, response=f"Failed to load config with UUID {config_uuid}")
            else:
                response = response_handle(code=404, response=f"Device not found with UUID: {device_uuid}")
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/<device_uuid>/actions/regenerate_certificate", methods=['POST'])
# @cross_origin()
def device_uuid_actions_regenerate_certificate(device_uuid):
    if request.method == 'POST':
        try:
            device = load_object(object_type="device", object_uuid=device_uuid)
            if device:
                if device.task is not None:
                    response = response_handle(response="Device already has a task running: " + str(device.task.uuid),
                                               code=500)
                    return response

                # Regenerating the certificate of the device
                if device.metadata.device_type == "ucsm":
                    task_uuid = easyucs.task_manager.add_task(name="RegenerateCertificateUcsSystem",
                                                              device_name=str(device.name),
                                                              device_uuid=str(device.uuid))
                elif device.metadata.device_type == "cimc":
                    task_uuid = easyucs.task_manager.add_task(name="RegenerateCertificateUcsImc",
                                                              device_name=str(device.name),
                                                              device_uuid=str(device.uuid))
                else:
                    response = response_handle(response="Regenerating Certificate on " + device.metadata.device_type +
                                               " device is not supported", code=400)
                    return response

                pending_task = {
                    "task_uuid": task_uuid,
                    "action_type": "regenerate_certificate",
                    "object_type": "device",
                    "timeout": timeout_values["regenerate_certificate"]
                }
                if not easyucs.task_manager.add_to_pending_tasks(pending_task):
                    response = response_handle(response="Error while scheduling the task. Task Queue might be Full."
                                                        " Try again after some time.", code=400)
                    return response
                response = response_handle(response={"task": str(task_uuid)}, code=200)

            else:
                response = response_handle(response="Device not found with UUID: " + device_uuid, code=404)
        except Exception:
            response = response_handle(code=500)
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/<device_uuid>/actions/reset", methods=['POST'])
# @cross_origin()
def device_uuid_actions_reset(device_uuid):
    if request.method == 'POST':
        try:
            payload = request.json

            # Check if payload valid
            if not validate_json(json_data=payload, schema_path="api/specs/device_reset_post.json", logger=easyucs):
                response = response_handle(response="Invalid Payload", code=400)
                return response

            device = load_object(object_type="device", object_uuid=device_uuid)
            if device:
                if device.task is not None:
                    response = response_handle(response="Device already has a task running: " + str(device.task.uuid),
                                               code=500)
                    return response

                # Resetting the device
                if payload.get("password") == device.password:
                    if device.metadata.device_type == "ucsm":
                        task_uuid = easyucs.task_manager.add_task(name="ResetDeviceUcsSystem",
                                                                  device_name=str(device.name),
                                                                  device_uuid=str(device.uuid))
                        action_kwargs = {
                            "clear_sel_logs": payload.get("clear_sel_logs", False),
                            "decommission_blade_servers":  payload.get("decommission_blade_servers", False),
                            "decommission_chassis":  payload.get("decommission_chassis", True),
                            "decommission_rack_servers":  payload.get("decommission_rack_servers", True),
                            "erase_flexflash": payload.get("erase_flexflash", False),
                            "erase_virtual_drives": payload.get("erase_virtual_drives", False),
                            "reset_device_connector": payload.get("reset_device_connector", True),
                            "unregister_from_central":  payload.get("unregister_from_central", False)
                        }
                    elif device.metadata.device_type == "cimc":
                        task_uuid = easyucs.task_manager.add_task(name="ResetDeviceUcsImc",
                                                                  device_name=str(device.name),
                                                                  device_uuid=str(device.uuid))
                        action_kwargs = {
                            "reset_device_connector": payload.get("reset_device_connector", False)
                        }
                    elif device.metadata.device_type == "imm_domain":
                        task_uuid = easyucs.task_manager.add_task(name="ResetDeviceImmDomain",
                                                                  device_name=str(device.name),
                                                                  device_uuid=str(device.uuid))
                        action_kwargs = {
                            "reset_device_connector": payload.get("reset_device_connector", False)
                        }
                    else:
                        response = response_handle(response="Resetting " + device.metadata.device_type +
                                                   " device is not supported", code=400)
                        return response

                    pending_task = {
                        "task_uuid": task_uuid,
                        "action_type": "reset",
                        "object_type": "device",
                        "timeout": timeout_values["reset"],
                        "action_kwargs": action_kwargs
                    }
                    if not easyucs.task_manager.add_to_pending_tasks(pending_task):
                        response = response_handle(response="Error while scheduling the task. Task Queue might be Full."
                                                            " Try again after some time.", code=400)
                        return response
                    response = response_handle(response={"task": str(task_uuid)}, code=200)

                else:
                    response = response_handle(response="Admin password mismatch", code=400)
            else:
                response = response_handle(response="Device not found with UUID: " + device_uuid, code=404)
        except Exception:
            response = response_handle(code=500)
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/<device_uuid>/actions/reset_device_connector", methods=['POST'])
# @cross_origin()
def device_uuid_actions_reset_device_connector(device_uuid):
    if request.method == 'POST':
        try:
            device = load_object(object_type="device", object_uuid=device_uuid)
            if device:
                try:
                    # We create a new task
                    if device.metadata.device_type in ["cimc"]:
                        task_uuid = easyucs.task_manager.add_task(name="ResetDeviceConnectorUcsImc",
                                                                  device_name=str(device.name),
                                                                  device_uuid=str(device.uuid))
                    elif device.metadata.device_type in ["imm_domain"]:
                        task_uuid = easyucs.task_manager.add_task(name="ResetDeviceConnectorImmDomain",
                                                                  device_name=str(device.name),
                                                                  device_uuid=str(device.uuid))
                    elif device.metadata.device_type in ["ucsm"]:
                        task_uuid = easyucs.task_manager.add_task(name="ResetDeviceConnectorUcsSystem",
                                                                  device_name=str(device.name),
                                                                  device_uuid=str(device.uuid))
                    else:
                        response = response_handle(response="Unsupported device type", code=500)
                        return response
                    # We schedule the Reset Device Connector action through the scheduler
                    pending_task = {
                        "task_uuid": task_uuid,
                        "action_type": "reset_device_connector",
                        "object_type": "device",
                        "timeout": timeout_values["reset_device_connector"]
                    }
                    if not easyucs.task_manager.add_to_pending_tasks(pending_task):
                        response = response_handle(response="Error while scheduling the task. Task Queue might be Full."
                                                            " Try again after some time.", code=400)
                        return response
                except Exception as err:
                    response = response_handle(response="Error while performing Reset Device Connector: " +
                                                        str(err), code=500)
                    return response
                response = response_handle(response={"task": str(task_uuid)}, code=200)

            else:
                response = response_handle(response="Device not found with UUID: " + device_uuid, code=404)

        except BadRequest as err:
            response = response_handle(code=err.code, response=str(err.description))
        except Exception as err:
            response = response_handle(response="Error while performing Reset Device Connector: " + str(err),
                                       code=500)
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/<device_uuid>/actions/test_connection", methods=['POST'])
# @cross_origin()
def device_uuid_actions_test_connection(device_uuid):
    if request.method == 'POST':
        try:
            device = load_object(object_type="device", object_uuid=device_uuid)
            if device:
                if device.task is not None:
                    response = response_handle(response="Device already has a task running: " + str(device.task.uuid),
                                               code=500)
                    return response
                try:
                    # We create a new task
                    if device.metadata.device_type in ["cimc"]:
                        task_uuid = easyucs.task_manager.add_task(name="TestConnectionUcsImc",
                                                                  device_name=str(device.name),
                                                                  device_uuid=str(device.uuid))
                    elif device.metadata.device_type in ["imm_domain"]:
                        task_uuid = easyucs.task_manager.add_task(name="TestConnectionImmDomain",
                                                                  device_name=str(device.name),
                                                                  device_uuid=str(device.uuid))
                    elif device.metadata.device_type in ["intersight"]:
                        task_uuid = easyucs.task_manager.add_task(name="TestConnectionIntersight",
                                                                  device_name=str(device.name),
                                                                  device_uuid=str(device.uuid))
                    elif device.metadata.device_type in ["ucsc"]:
                        task_uuid = easyucs.task_manager.add_task(name="TestConnectionUcsCentral",
                                                                  device_name=str(device.name),
                                                                  device_uuid=str(device.uuid))
                    elif device.metadata.device_type in ["ucsm"]:
                        task_uuid = easyucs.task_manager.add_task(name="TestConnectionUcsSystem",
                                                                  device_name=str(device.name),
                                                                  device_uuid=str(device.uuid))
                    else:
                        response = response_handle(response="Unsupported device type", code=500)
                        return response

                    # We schedule the test connection action through the scheduler
                    pending_task = {
                        "task_uuid": task_uuid,
                        "action_type": "test_connection",
                        "object_type": "device",
                        "timeout": timeout_values["test_connection"]
                    }
                    if not easyucs.task_manager.add_to_pending_tasks(pending_task):
                        response = response_handle(response="Error while scheduling the task. Task Queue might be Full."
                                                            " Try again after some time.", code=400)
                        return response

                except Exception as err:
                    response = response_handle(response="Error testing the device connection: " + str(err),
                                               code=500)
                    return response

                response = response_handle(response={"task": str(task_uuid)}, code=200)
            else:
                response = response_handle(response="Device not found with UUID: " + device_uuid, code=404)
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/<device_uuid>/backups", methods=['GET'])
# @cross_origin()
def device_uuid_backups(device_uuid):
    if request.method == 'GET':
        try:
            filter_attribute = request.args.get("filter_attribute", None)
            filter_type = request.args.get("filter_type", None)
            filter_value = request.args.get("filter_value", None)

            if filter_attribute is None or filter_type is None or filter_value is None:
                filter = None
            else:
                filter = [filter_attribute, filter_type, filter_value]

            order_by_attribute = request.args.get("order_by_attribute", None)
            order_by_direction = request.args.get("order_by_direction", None)

            if order_by_attribute is None or order_by_direction is None:
                order_by = None
            else:
                order_by = (order_by_attribute, order_by_direction)

            page_size = request.args.get("page_size", None)
            page_number = int(request.args.get("page_number", 0))

            backup_dict = get_object_from_db(object_type="backup", device_uuid=device_uuid, filter=filter,
                                             page_size=page_size, page_number=page_number, order_by=order_by)

            if backup_dict:
                response = response_handle(backup_dict, 200)
            else:
                response = response_handle(code=500,
                                           response="Unexpected error while fetching data from DB. Please check logs.")

        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/<device_uuid>/backups/actions", methods=['GET'])
# @cross_origin()
def device_uuid_backups_actions(device_uuid):
    if request.method == 'GET':
        try:
            device_metadata_list = easyucs.repository_manager.get_metadata(object_type="device", uuid=device_uuid)
            if len(device_metadata_list) == 1:
                device_type = device_metadata_list[0].device_type

                actions = None
                if device_type in ["cimc", "ucsc", "ucsm"]:
                    actions = ["fetch"]

                actions_dict = {"actions": actions}

                response = response_handle(actions_dict, 200)
            else:
                response = response_handle(response="Device with UUID " + device_uuid + " not found", code=404)
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/<device_uuid>/backups/actions/delete", methods=['POST'])
# @cross_origin()
def device_uuid_backups_actions_delete(device_uuid):
    if request.method == 'POST':
        try:
            payload = request.json

            # Check if payload valid
            if not validate_json(json_data=payload, schema_path="api/specs/backup_delete.json", logger=easyucs):
                response = response_handle(code=400, response="Invalid payload")
                return response

            backup_uuid_list = []
            if "backup_uuids" in payload:
                backup_uuid_list = payload["backup_uuids"]

            backups_metadata_list = []

            for backup_uuid in backup_uuid_list:
                backup_metadata_list = easyucs.repository_manager.get_metadata(object_type="backup", uuid=backup_uuid)
                if len(backup_metadata_list) == 1:
                    backups_metadata_list.append(backup_metadata_list[0])
                else:
                    response = response_handle(response="Backup with UUID " + backup_uuid + " not found", code=404)
                    return response

            if easyucs.repository_manager.delete_bulk_from_repository(metadata_list=backups_metadata_list):
                response = response_handle(code=200)
            else:
                response = response_handle(code=500, response="Could not delete backups from repository")

        except BadRequest as err:
            response = response_handle(code=err.code, response=str(err.description))
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/<device_uuid>/backups/actions/fetch", methods=['POST'])
# @cross_origin()
def device_uuid_backups_actions_fetch(device_uuid):
    if request.method == 'POST':
        try:
            action_kwargs = {
                "use_repository": True,
                "timeout": timeout_values["fetch_backup"] - 60
            }

            payload = request.json
            # Check if payload valid
            if payload:
                if not validate_json(json_data=payload, schema_path="api/specs/backup_fetch_post.json", logger=easyucs):
                    response = response_handle(code=400, response="Invalid payload")
                    return response
                if "backup_type" in payload:
                    action_kwargs["backup_type"] = payload["backup_type"]

            device = load_object(object_type="device", object_uuid=device_uuid)
            if device:
                try:
                    # We create a new task
                    if device.metadata.device_type in ["cimc"]:
                        task_uuid = easyucs.task_manager.add_task(name="FetchBackupUcsImc",
                                                                  device_name=str(device.name),
                                                                  device_uuid=str(device.uuid))
                    elif device.metadata.device_type in ["ucsc"]:
                        task_uuid = easyucs.task_manager.add_task(name="FetchBackupUcsCentral",
                                                                  device_name=str(device.name),
                                                                  device_uuid=str(device.uuid))
                    elif device.metadata.device_type in ["ucsm"]:
                        task_uuid = easyucs.task_manager.add_task(name="FetchBackupUcsSystem",
                                                                  device_name=str(device.name),
                                                                  device_uuid=str(device.uuid))
                    else:
                        response = response_handle(response="Unsupported device type", code=500)
                        return response

                    # We schedule the fetch backup action through the scheduler
                    pending_task = {
                        "task_uuid": task_uuid,
                        "action_type": "fetch",
                        "object_type": "backup",
                        "timeout": timeout_values["fetch_backup"],
                        "action_kwargs": action_kwargs
                    }
                    if not easyucs.task_manager.add_to_pending_tasks(pending_task):
                        response = response_handle(response="Error while scheduling the task. Task Queue might be Full."
                                                            " Try again after some time.", code=400)
                        return response

                except Exception as err:
                    response = response_handle(response="Error while fetching backup: " + str(err), code=500)
                    return response

                response = response_handle(response={"task": str(task_uuid)}, code=200)
            else:
                response = response_handle(response="Device not found with UUID: " + device_uuid, code=404)
        except BadRequest as err:
            response = response_handle(code=err.code, response=str(err.description))
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/<device_uuid>/backups/<backup_uuid>", methods=['GET', 'DELETE'])
# @cross_origin()
def device_uuid_backup_uuid(device_uuid, backup_uuid):
    if request.method == 'GET':
        try:
            filter_attribute = request.args.get("filter_attribute", None)
            filter_type = request.args.get("filter_type", None)
            filter_value = request.args.get("filter_value", None)

            if filter_attribute is None or filter_type is None or filter_value is None:
                filter = None
            else:
                filter = [filter_attribute, filter_type, filter_value]

            order_by_attribute = request.args.get("order_by_attribute", None)
            order_by_direction = request.args.get("order_by_direction", None)

            if order_by_attribute is None or order_by_direction is None:
                order_by = None
            else:
                order_by = (order_by_attribute, order_by_direction)

            page_size = request.args.get("page_size", None)
            page_number = int(request.args.get("page_number", 0))

            backup_dict = get_object_from_db(object_type="backup", uuid=backup_uuid, filter=filter, page_size=page_size,
                                             page_number=page_number, order_by=order_by)

            if backup_dict:
                response = response_handle(backup_dict, 200)
            else:
                response = response_handle(code=500, response=f"Could not find backup with UUID {backup_uuid}")

        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    elif request.method == 'DELETE':
        try:
            backup_metadata_list = easyucs.repository_manager.get_metadata(object_type="backup", uuid=backup_uuid)
            if len(backup_metadata_list) == 1:
                if easyucs.repository_manager.delete_from_repository(metadata=backup_metadata_list[0]):
                    response = response_handle(code=200)
                else:
                    response = response_handle(code=500, response="Could not delete backup from repository")
            else:
                response = response_handle(response="Backup with UUID " + backup_uuid + " not found", code=404)
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/<device_uuid>/backups/<backup_uuid>/actions", methods=['GET'])
# @cross_origin()
def device_uuid_backup_uuid_actions(device_uuid, backup_uuid):
    if request.method == 'GET':
        try:
            device_metadata_list = easyucs.repository_manager.get_metadata(object_type="device", uuid=device_uuid)
            if len(device_metadata_list) == 1:
                device_type = device_metadata_list[0].device_type

                backup_metadata_list = easyucs.repository_manager.get_metadata(object_type="backup", uuid=backup_uuid)
                if len(backup_metadata_list) == 1:

                    actions = None
                    if device_type in ["cimc", "ucsc", "ucsm"]:
                        actions = ["download"]

                    actions_dict = {"actions": actions}

                    response = response_handle(actions_dict, 200)

                else:
                    response = response_handle(response="Backup with UUID " + backup_uuid + " not found",
                                               code=404)
            else:
                response = response_handle(response="Device with UUID " + device_uuid + " not found", code=404)
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/<device_uuid>/backups/<backup_uuid>/actions/download", methods=['GET'])
# @cross_origin()
def device_uuid_backup_uuid_actions_download(device_uuid, backup_uuid):
    if request.method == 'GET':
        try:
            # Trying to find device using its metadata (DB)
            easyucs.logger(level="debug", message="Trying to find device with UUID " + device_uuid + " from the DB")
            device_metadata_list = easyucs.repository_manager.get_metadata(object_type="device", uuid=device_uuid)
            if len(device_metadata_list) != 1:
                response = response_handle(response="Device not found with UUID: " + device_uuid, code=404)
                return response

            # Trying to find backup using its metadata (DB)
            easyucs.logger(level="debug",
                           message="Trying to find backup with UUID " + backup_uuid + " from the DB")
            backup_metadata_list = easyucs.repository_manager.get_metadata(object_type="backup", uuid=backup_uuid)
            if len(backup_metadata_list) == 1:
                file_path = os.path.abspath(os.path.join(EASYUCS_ROOT, backup_metadata_list[0].file_path))
                response = send_file(file_path, as_attachment=True,
                                     download_name="backup_" + backup_uuid +
                                                   backup_metadata_list[0].backup_file_extension)
            else:
                response = response_handle(response="Backup not found with UUID: " + backup_uuid, code=404)

        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/<device_uuid>/cache", methods=['GET'])
def device_uuid_cache(device_uuid):
    if request.method == 'GET':
        try:
            device = load_object(object_type="device", object_uuid=device_uuid)
            if device:
                operating_system = request.args.get("os", None, type=lambda v: v.lower() == 'true' if v else None)
                firmware = request.args.get("firmware", None, type=lambda v: v.lower() == 'true' if v else None)
                orgs = request.args.get("orgs", None, type=lambda v: v.lower() == 'true' if v else None)
                server_details = request.args.get("server_details", None,
                                                  type=lambda v: v.lower() == 'true' if v else None)

                cache_details = read_json_file(
                    file_path=os.path.join(EASYUCS_ROOT, f"data/files/devices/{device_uuid}/cache/cache.json"),
                    logger=easyucs)

                if not cache_details:
                    response = response_handle(response="Failed to read cached data from device",
                                               code=500)
                    return response

                fields = {
                    "os": operating_system,
                    "firmware": firmware,
                    "orgs": orgs,
                    "server_details": server_details
                }

                for field, value in fields.items():
                    if value is None:
                        # Skip if no preference is set; include field in response only if present in the cache.
                        continue
                    elif value is True:
                        # Ensure requested field exists in the cache; return error if missing.
                        if field in ["os", "firmware"]:
                            if not cache_details.get("os_firmware", {}).get(field):
                                response = response_handle(response="OS and Firmware cached data not found", code=404)
                                return response
                        elif field in ["server_details"]:
                            if not cache_details.get("servers"):
                                response = response_handle(response="Server details cached data not found", code=404)
                                return response
                        else:
                            if not cache_details.get(field):
                                response = response_handle(response=f"{field} data not found", code=404)
                                return response
                    elif value is False:
                        # Remove field from the response if explicitly not needed.
                        if field in ["os", "firmware"]:
                            if cache_details.get("os_firmware", {}).get(field):
                                del cache_details["os_firmware"][field]
                        elif field in ["server_details"]:
                            if cache_details.get("servers"):
                                del cache_details["servers"]
                        else:
                            if cache_details.get(field):
                                del cache_details[field]

                response = response_handle(response=cache_details, code=200)
            else:
                response = response_handle(response="Device not found with UUID: " + device_uuid, code=404)
        except Exception as err:
            easyucs.logger(level="error", message="Unexpected error while getting the cache!")
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/<device_uuid>/cache/actions/fetch", methods=['POST'])
def device_uuid_cache_actions_fetch(device_uuid):
    if request.method == 'POST':
        try:
            device = load_object(object_type="device", object_uuid=device_uuid)
            if device:
                try:
                    # We create a new task
                    if device.metadata.device_type in ["intersight"]:
                        task_uuid = easyucs.task_manager.add_task(name="FetchCacheIntersight",
                                                                  device_name=str(device.name),
                                                                  device_uuid=str(device.uuid))
                    elif device.metadata.device_type in ["ucsc"]:
                        task_uuid = easyucs.task_manager.add_task(name="FetchCacheUcsCentral",
                                                                  device_name=str(device.name),
                                                                  device_uuid=str(device.uuid))
                    elif device.metadata.device_type in ["ucsm"]:
                        task_uuid = easyucs.task_manager.add_task(name="FetchCacheUcsSystem",
                                                                  device_name=str(device.name),
                                                                  device_uuid=str(device.uuid))
                    else:
                        response = response_handle(response="Unsupported device type", code=500)
                        return response

                    # We schedule the fetch cache action through the scheduler
                    pending_task = {
                        "task_uuid": task_uuid,
                        "action_type": "fetch",
                        "object_type": "cache",
                        "timeout": timeout_values["fetch_cache"]
                    }

                    if not easyucs.task_manager.add_to_pending_tasks(pending_task):
                        response = response_handle(response="Error while scheduling the task. Task Queue might be Full."
                                                            " Try again after some time.", code=400)
                        return response

                except Exception as err:
                    response = response_handle(response="Error while fetching cache: " + str(err), code=500)
                    return response

                response = response_handle(response={"task": str(task_uuid)}, code=200)
            else:
                response = response_handle(response="Device not found with UUID: " + device_uuid, code=404)
        except BadRequest as err:
            response = response_handle(code=err.code, response=str(err.description))
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/<device_uuid>/cache/actions/fetch_os_firmware_data", methods=['POST'])
# @cross_origin()
def device_uuid_cache_actions_fetch_os_firmware_data(device_uuid):
    if request.method == 'POST':
        try:
            device = load_object(object_type="device", object_uuid=device_uuid)
            if device:
                if device.task is not None:
                    response = response_handle(response="Device already has a task running: " + str(device.task.uuid),
                                               code=500)
                    return response
                try:
                    # We create a new task
                    if device.metadata.device_type in ["intersight"]:
                        task_uuid = easyucs.task_manager.add_task(name="FetchOSFirmwareDataIntersight",
                                                                  device_name=str(device.name),
                                                                  device_uuid=str(device.uuid))
                    else:
                        response = response_handle(response="Unsupported device type", code=500)
                        return response

                    # We schedule the test connection action through the scheduler
                    pending_task = {
                        "task_uuid": task_uuid,
                        "action_type": "fetch_os_firmware_data",
                        "object_type": "cache",
                        "timeout": timeout_values["fetch_os_firmware_data"]
                    }
                    if not easyucs.task_manager.add_to_pending_tasks(pending_task):
                        response = response_handle(response="Error while scheduling the task. Task Queue might be Full."
                                                            " Try again after some time.", code=400)
                        return response

                except Exception as err:
                    response = response_handle(response="Error testing the device connection: " + str(err),
                                               code=500)
                    return response

                response = response_handle(response={"task": str(task_uuid)}, code=200)
            else:
                response = response_handle(response="Device not found with UUID: " + device_uuid, code=404)
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/<device_uuid>/cache/orgs", methods=['GET'])
def device_uuid_cache_orgs(device_uuid):
    if request.method == "GET":
        try:
            device = load_object(object_type="device", object_uuid=device_uuid)
            if not device:
                return response_handle(response="Device not found with UUID: " + device_uuid, code=404)

            if device.metadata.device_type not in ["intersight", "ucsm", "ucsc"]:
                return response_handle(response="Invalid device type", code=400)

            cached_orgs = device.cache_manager.cache.get_orgs()
            if device.metadata.device_type == "intersight":
                if cached_orgs.get("orgs", None):
                    response = response_handle(response={"orgs": cached_orgs["orgs"]}, code=200)
                else:
                    easyucs.logger(level="info", message="No cached orgs were found.")
                    response = response_handle(response={"orgs": {}}, code=200)

            else:  # ucsm / ucsc (only remaining valid device types after the check above)
                if not cached_orgs or not cached_orgs.get("orgs"):
                    easyucs.logger(level="info", message="No cached orgs were found. Showing default root org.")
                    response = response_handle(response=cached_orgs, code=200)
                else:
                    response = response_handle(response=cached_orgs, code=200)
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/<device_uuid>/configs", methods=['GET', 'POST'])
# @cross_origin()
def device_uuid_configs(device_uuid):
    if request.method == 'GET':
        try:
            filter_attribute = request.args.get("filter_attribute", None)
            filter_type = request.args.get("filter_type", None)
            filter_value = request.args.get("filter_value", None)

            if filter_attribute is None or filter_type is None or filter_value is None:
                filter = None
            else:
                filter = [filter_attribute, filter_type, filter_value]

            order_by_attribute = request.args.get("order_by_attribute", None)
            order_by_direction = request.args.get("order_by_direction", None)

            if order_by_attribute is None or order_by_direction is None:
                order_by = None
            else:
                order_by = (order_by_attribute, order_by_direction)

            page_size = request.args.get("page_size", None)
            page_number = int(request.args.get("page_number", 0))

            config_dict = get_object_from_db(object_type="config", device_uuid=device_uuid, filter=filter,
                                             page_size=page_size, page_number=page_number, order_by=order_by)

            if config_dict:
                response = response_handle(config_dict, 200)
            else:
                response = response_handle(code=500,
                                           response="Unexpected error while fetching data from DB. Please check logs.")
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    elif request.method == 'POST':
        try:
            if request.form:
                if not validate_json(json_data=request.form, schema_path="api/specs/config_post.json",
                                     logger=easyucs):
                    response = response_handle(code=400, response="Invalid payload")
                    return response

            device = load_object(object_type="device", object_uuid=device_uuid)
            if device:
                if device.task is not None:
                    response = response_handle(response="Device already has a task running: " + str(device.task.uuid),
                                               code=400)
                    return response

                try:
                    file = request.files['config_file']
                    json_file = file.read().decode("utf-8")
                except Exception as err:  # FIXME: Handle various exception cases - should only support JSON files
                    response = response_handle(response="Error while reading config file: " + str(err), code=500)
                    return response

                # If force_custom is not sent then its value must be None. If it's sent from the API then it should be
                # converted to boolean before passing it as an argument.
                force_custom = request.form.get('force_custom')
                if force_custom:
                    force_custom = force_custom == "true"

                config = device.config_manager.import_config(import_format="json", config=json_file,
                                                             force_custom=force_custom)
                if config:
                    # Save the imported config
                    easyucs.repository_manager.save_to_repository(object=config)

                    config_metadata = {"device_uuid": str(config.metadata.device_uuid),
                                       "timestamp": config.metadata.timestamp.isoformat()[:-3] + 'Z',
                                       "uuid": str(config.metadata.uuid)}
                    for attribute in ["category", "device_version", "easyucs_version", "is_custom", "is_hidden",
                                      "is_system", "name", "origin", "revision", "subcategory", "system_usage", "url"]:
                        if getattr(config.metadata, attribute) not in [None, ""]:
                            config_metadata[attribute] = getattr(config.metadata, attribute)

                    for attribute in ["source_config_uuid", "source_device_uuid", "source_inventory_uuid"]:
                        if getattr(config.metadata, attribute) not in [None, ""]:
                            config_metadata[attribute] = str(getattr(config.metadata, attribute))

                    config_dict = {"config": config_metadata}
                    response = response_handle(config_dict, 200)
                else:
                    response_message = easyucs.api_error_message
                    if not response_message:
                        response_message = "Impossible to import the file as a config"
                    response = response_handle(response=response_message, code=500)
            else:
                response = response_handle(response="Device not found with UUID: " + device_uuid, code=404)
        except BadRequest as err:
            response = response_handle(code=err.code, response=str(err.description))
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/<device_uuid>/configs/actions", methods=['GET'])
# @cross_origin()
def device_uuid_configs_actions(device_uuid):
    if request.method == 'GET':
        try:
            device_metadata_list = easyucs.repository_manager.get_metadata(object_type="device", uuid=device_uuid)
            if len(device_metadata_list) == 1:
                device_type = device_metadata_list[0].device_type

                actions = None
                if device_type in ["cimc", "imm_domain", "intersight", "ucsc", "ucsm"]:
                    actions = ["fetch"]

                actions_dict = {"actions": actions}

                response = response_handle(actions_dict, 200)
            else:
                response = response_handle(response="Device with UUID " + device_uuid + " not found", code=404)
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/<device_uuid>/configs/actions/delete", methods=['POST'])
# @cross_origin()
def device_uuid_configs_actions_delete(device_uuid):
    if request.method == 'POST':
        try:
            payload = request.json

            # Check if payload valid
            if not validate_json(json_data=payload, schema_path="api/specs/config_delete.json", logger=easyucs):
                response = response_handle(code=400, response="Invalid payload")
                return response

            config_uuid_list = []
            if "config_uuids" in payload:
                config_uuid_list = payload["config_uuids"]

            configs_uuid_list = []

            for config_uuid in config_uuid_list:
                config_metadata_list = easyucs.repository_manager.get_metadata(object_type="config", uuid=config_uuid)
                if len(config_metadata_list) == 1:
                    configs_uuid_list.append(config_metadata_list[0])
                else:
                    response = response_handle(response="Config with UUID " + config_uuid + " not found", code=404)
                    return response

            if easyucs.repository_manager.delete_bulk_from_repository(metadata_list=configs_uuid_list):
                response = response_handle(code=200)
            else:
                response = response_handle(code=500, response="Could not delete configs from repository")

        except BadRequest as err:
            response = response_handle(code=err.code, response=str(err.description))
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/<device_uuid>/configs/actions/fetch", methods=['POST'])
# @cross_origin()
def device_uuid_configs_actions_fetch(device_uuid):
    if request.method == 'POST':
        try:
            payload = request.json

            # Check if payload valid
            if payload:
                if not validate_json(json_data=payload, schema_path="api/specs/fetch.json",
                                     logger=easyucs):
                    response = response_handle(code=400, response="Invalid payload")
                    return response

            force = payload.get("force", False) if payload else False

            device = load_object(object_type="device", object_uuid=device_uuid)
            if device:
                try:
                    # We create a new task
                    if device.metadata.device_type in ["cimc"]:
                        task_uuid = easyucs.task_manager.add_task(name="FetchConfigUcsImc",
                                                                  device_name=str(device.name),
                                                                  device_uuid=str(device.uuid))
                    elif device.metadata.device_type in ["imm_domain"]:
                        task_uuid = easyucs.task_manager.add_task(name="FetchConfigImmDomain",
                                                                  device_name=str(device.name),
                                                                  device_uuid=str(device.uuid))
                    elif device.metadata.device_type in ["intersight"]:
                        task_uuid = easyucs.task_manager.add_task(name="FetchConfigIntersight",
                                                                  device_name=str(device.name),
                                                                  device_uuid=str(device.uuid))
                    elif device.metadata.device_type in ["ucsc"]:
                        task_uuid = easyucs.task_manager.add_task(name="FetchConfigUcsCentral",
                                                                  device_name=str(device.name),
                                                                  device_uuid=str(device.uuid))
                    elif device.metadata.device_type in ["ucsm"]:
                        task_uuid = easyucs.task_manager.add_task(name="FetchConfigUcsSystem",
                                                                  device_name=str(device.name),
                                                                  device_uuid=str(device.uuid))
                    else:
                        response = response_handle(response="Unsupported device type", code=500)
                        return response

                    # We schedule the fetch config action through the scheduler
                    pending_task = {
                        "task_uuid": task_uuid,
                        "action_type": "fetch",
                        "object_type": "config",
                        "timeout": timeout_values["fetch_config"],
                        "action_kwargs": {"force": force}
                    }
                    if not easyucs.task_manager.add_to_pending_tasks(pending_task):
                        response = response_handle(response="Error while scheduling the task. Task Queue might be Full."
                                                            " Try again after some time.", code=400)
                        return response

                except Exception as err:
                    response = response_handle(response="Error while fetching config: " + str(err), code=500)
                    return response

                response = response_handle(response={"task": str(task_uuid)}, code=200)
            else:
                response = response_handle(response="Device not found with UUID: " + device_uuid, code=404)
        except BadRequest as err:
            response = response_handle(code=err.code, response=str(err.description))
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/<device_uuid>/configs/<config_uuid>", methods=['GET', 'DELETE'])
# @cross_origin()
def device_uuid_config_uuid(device_uuid, config_uuid):
    if request.method == 'GET':
        try:
            filter_attribute = request.args.get("filter_attribute", None)
            filter_type = request.args.get("filter_type", None)
            filter_value = request.args.get("filter_value", None)

            if filter_attribute is None or filter_type is None or filter_value is None:
                filter = None
            else:
                filter = [filter_attribute, filter_type, filter_value]

            order_by_attribute = request.args.get("order_by_attribute", None)
            order_by_direction = request.args.get("order_by_direction", None)

            if order_by_attribute is None or order_by_direction is None:
                order_by = None
            else:
                order_by = (order_by_attribute, order_by_direction)

            page_size = request.args.get("page_size", None)
            page_number = int(request.args.get("page_number", 0))

            config_dict = get_object_from_db(object_type="config", uuid=config_uuid, filter=filter,
                                             page_size=page_size, page_number=page_number, order_by=order_by)

            if config_dict:
                response = response_handle(config_dict, 200)
            else:
                response = response_handle(code=500, response=f"Could not find config with UUID {config_uuid}")

        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    elif request.method == 'DELETE':
        try:
            config_metadata_list = easyucs.repository_manager.get_metadata(object_type="config", uuid=config_uuid)
            if len(config_metadata_list) == 1:
                if easyucs.repository_manager.delete_from_repository(metadata=config_metadata_list[0]):
                    response = response_handle(code=200)
                else:
                    response = response_handle(code=500, response="Could not delete config from repository")
            else:
                response = response_handle(response="Config with UUID " + config_uuid + " not found", code=404)
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/<device_uuid>/configs/<config_uuid>/actions", methods=['GET'])
# @cross_origin()
def device_uuid_config_uuid_actions(device_uuid, config_uuid):
    if request.method == 'GET':
        try:
            device_metadata_list = easyucs.repository_manager.get_metadata(object_type="device", uuid=device_uuid)
            if len(device_metadata_list) == 1:
                device_type = device_metadata_list[0].device_type

                config_metadata_list = easyucs.repository_manager.get_metadata(object_type="config", uuid=config_uuid)
                if len(config_metadata_list) == 1:

                    actions = None
                    if device_type in ["cimc", "imm_domain", "intersight", "ucsc", "ucsm"]:
                        actions = ["download", "push"]

                    actions_dict = {"actions": actions}

                    response = response_handle(actions_dict, 200)

                else:
                    response = response_handle(response="Config with UUID " + config_uuid + " not found", code=404)
            else:
                response = response_handle(response="Device with UUID " + device_uuid + " not found", code=404)
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/<device_uuid>/configs/<config_uuid>/actions/download", methods=['GET'])
# @cross_origin()
def device_uuid_config_uuid_actions_download(device_uuid, config_uuid):
    if request.method == 'GET':
        try:
            # Trying to find device using its metadata (DB)
            easyucs.logger(level="debug", message="Trying to find device with UUID " + device_uuid + " from the DB")
            device_metadata_list = easyucs.repository_manager.get_metadata(object_type="device", uuid=device_uuid)
            if len(device_metadata_list) != 1:
                response = response_handle(response="Device not found with UUID: " + device_uuid, code=404)
                return response

            # Trying to find config using its metadata (DB)
            easyucs.logger(level="debug", message="Trying to find config with UUID " + config_uuid + " from the DB")
            config_metadata_list = easyucs.repository_manager.get_metadata(object_type="config", uuid=config_uuid)
            if len(config_metadata_list) == 1:
                file_path = os.path.abspath(os.path.join(EASYUCS_ROOT, config_metadata_list[0].file_path))
                response = send_file(file_path, as_attachment=True, download_name="config_" + config_uuid + ".json")
            else:
                response = response_handle(response="Config not found with UUID: " + config_uuid, code=404)

        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/<device_uuid>/configs/<config_uuid>/actions/push", methods=['POST'])
# @cross_origin()
def device_uuid_config_uuid_actions_push(device_uuid, config_uuid):
    if request.method == 'POST':
        try:
            action_kwargs = {
                "uuid": config_uuid,
                "bypass_version_checks": True
            }

            payload = request.json
            # Check if payload valid
            if payload:
                if not validate_json(json_data=payload, schema_path="api/specs/config_push_post.json", logger=easyucs):
                    response = response_handle(code=400, response="Invalid payload")
                    return response
                if "fi_ip_list" in payload:
                    action_kwargs["fi_ip_list"] = payload["fi_ip_list"]
                if "reset" in payload:
                    action_kwargs["reset"] = payload["reset"]
                action_kwargs["force"] = payload.get("force", False)
                action_kwargs["push_equipment"] = payload.get("push_equipment", False)

            device = load_object(object_type="device", object_uuid=device_uuid)
            if device:
                # We first need to find & potentially load the config
                config = None
                if config_uuid:
                    config = load_object(object_type="config", object_uuid=config_uuid, device=device)
                    if not config:
                        response_message = easyucs.api_error_message
                        if not response_message:
                            response_message = "Failed to load config with UUID " + str(config_uuid)
                        response = response_handle(response=response_message, code=400)
                        return response
                    # Resetting the push summary and commit statuses in config objects.
                    # Skip the reset when doing an equipment-only push so that the previous
                    # "Push config to Intersight" results (org/policy/profile statuses) are
                    # preserved. Without this guard, navigating back to the push-config summary
                    # after a push-equipment run would show "Nothing to commit" for all orgs/
                    # policies because their commit_status arrays were cleared.
                    if not action_kwargs.get("push_equipment", False):
                        config.push_summary_manager.reset_push_summary()

                if not config:
                    response = response_handle(response="No config UUID provided", code=400)
                    return response

                try:
                    # We create a new task
                    if device.metadata.device_type in ["cimc"]:
                        task_uuid = easyucs.task_manager.add_task(
                            name="PushConfigUcsImc", device_name=str(device.name), device_uuid=str(device.uuid),
                            config_uuid=str(config.uuid)
                        )
                    elif device.metadata.device_type in ["intersight"]:
                        task_uuid = easyucs.task_manager.add_task(
                            name="PushConfigIntersight", device_name=str(device.name), device_uuid=str(device.uuid),
                            config_uuid=str(config.uuid)
                        )
                    elif device.metadata.device_type in ["ucsc"]:
                        task_uuid = easyucs.task_manager.add_task(
                            name="PushConfigUcsCentral", device_name=str(device.name), device_uuid=str(device.uuid),
                            config_uuid=str(config.uuid)
                        )
                    elif device.metadata.device_type in ["ucsm"]:
                        task_uuid = easyucs.task_manager.add_task(
                            name="PushConfigUcsSystem", device_name=str(device.name), device_uuid=str(device.uuid),
                            config_uuid=str(config.uuid)
                        )
                    else:
                        response = response_handle(response="Unsupported device type", code=500)
                        return response

                    # We schedule the push config action through the scheduler
                    pending_task = {
                        "task_uuid": task_uuid,
                        "action_type": "push",
                        "object_type": "config",
                        "timeout": timeout_values["push_config"],
                        "action_kwargs": action_kwargs
                    }
                    if not easyucs.task_manager.add_to_pending_tasks(pending_task):
                        response = response_handle(response="Error while scheduling the task. Task Queue might be Full."
                                                            " Try again after some time.", code=400)
                        return response

                except Exception as err:
                    response = response_handle(response="Error while pushing config: " + str(err), code=500)
                    return response

                response = response_handle(response={"task": str(task_uuid)}, code=200)
            else:
                response = response_handle(response="Device not found with UUID: " + device_uuid, code=404)
        except BadRequest as err:
            response = response_handle(code=err.code, response=str(err.description))
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/<device_uuid>/configs/<config_uuid>/profiles", methods=['GET'])
def device_uuid_config_uuid_profiles(device_uuid, config_uuid):
    if request.method == "GET":
        try:
            device = load_object(object_type="device", object_uuid=device_uuid)
            if device:
                config = load_object(object_type="config", object_uuid=config_uuid, device=device)
                if not config:
                    response_message = easyucs.api_error_message
                    if not response_message:
                        response_message = "Failed to load config with UUID " + str(config_uuid)
                    response = response_handle(response=response_message, code=400)
                    return response

                service_profiles = device.config_manager.get_profiles(config=config)
                if service_profiles:
                    response = response_handle(response=service_profiles, code=200)
                else:
                    response = response_handle(response=[], code=200)
            else:
                response = response_handle(response="Device not found with UUID: " + device_uuid, code=404)
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/<device_uuid>/configs/<config_uuid>/orgs", methods=["GET"])
def device_uuid_config_uuid_orgs(device_uuid, config_uuid):
    try:
        # Load the device object using its UUID
        device = load_object(object_type="device", object_uuid=device_uuid)
        if not device:
            # If device is not found, return 404 response
            return response_handle(response=f"Device not found with UUID: {device_uuid}", code=404)

        if device.metadata.device_type not in ["intersight", "ucsm", "ucsc"]:
            return response_handle(response="Invalid device type", code=400)

        config = load_object(object_type="config", object_uuid=config_uuid, device=device)
        if not config:
            # If config is not found or there was an error loading it, return error response
            msg = easyucs.api_error_message or f"Failed to load config with UUID {config_uuid}"
            return response_handle(response=msg, code=400)

        orgs_data = {}
        if device.metadata.device_type == "intersight":
            # Iterate over all organizations in the config
            for org in config.orgs:
                org_name = org.name
                # Check if the org is shared (i.e., has shared_with_orgs list)
                is_shared = bool(getattr(org, "shared_with_orgs", None))

                # Check if the org has any profiles (server/domain/chassis/unified_edge and their templates)
                has_profiles = any([
                    getattr(org, "ucs_server_profiles", []),
                    getattr(org, "ucs_server_profile_templates", []),
                    getattr(org, "ucs_domain_profiles", []),
                    getattr(org, "ucs_domain_profile_templates", []),
                    getattr(org, "ucs_chassis_profiles", []),
                    getattr(org, "ucs_chassis_profile_templates", []),
                    getattr(org, "unified_edge_profiles", []),
                    getattr(org, "unified_edge_profile_templates", []),
                ])

                # Populate the org data dictionary with relevant information
                orgs_data[org_name] = {
                    "description": getattr(org, "descr", "") or "",
                    "is_shared": is_shared,
                    "resource_groups": getattr(org, "resource_groups", []),
                    "shared_with_orgs": getattr(org, "shared_with_orgs", []),
                    "has_profiles": has_profiles
                }

            return response_handle(response={"orgs": orgs_data}, code=200)

        elif device.metadata.device_type in ["ucsm", "ucsc"]:
            # Recursive function to walk through org hierarchy
            def traverse_orgs(org, parent_path=""):
                org_name = org.name
                # Construct the full org path based on current and parent names
                org_path = f"{parent_path}/{org_name}".strip("/")

                # Check if this org contains any profiles
                has_profiles = any([
                    getattr(org, "service_profiles", []),
                    getattr(org, "chassis_profiles", [])
                ])
                # Populate org data into the final result dictionary
                orgs_data[org_path] = {
                    "org_name": org_name,
                    "org_path": org_path,
                    "description": getattr(org, "descr", "") or "",
                    "has_profiles": has_profiles
                }

                # Recurse into sub_orgs
                for sub_org in getattr(org, "orgs", []) or []:
                    traverse_orgs(sub_org, parent_path=org_path)

            # Start traversing from each top-level org in the config
            for root_org in config.orgs:
                traverse_orgs(root_org)

        return response_handle(response={"orgs": orgs_data}, code=200)

    except Exception as err:
        return response_handle(code=500, response=str(err))


@app.route("/devices/<device_uuid>/inventories", methods=['GET', 'POST'])
# @cross_origin()
def device_uuid_inventories(device_uuid):
    if request.method == 'GET':
        try:
            filter_attribute = request.args.get("filter_attribute", None)
            filter_type = request.args.get("filter_type", None)
            filter_value = request.args.get("filter_value", None)

            if filter_attribute is None or filter_type is None or filter_value is None:
                filter = None
            else:
                filter = [filter_attribute, filter_type, filter_value]

            order_by_attribute = request.args.get("order_by_attribute", None)
            order_by_direction = request.args.get("order_by_direction", None)

            if order_by_attribute is None or order_by_direction is None:
                order_by = None
            else:
                order_by = (order_by_attribute, order_by_direction)

            page_size = request.args.get("page_size", None)
            page_number = int(request.args.get("page_number", 0))

            inventory_dict = get_object_from_db(object_type="inventory", device_uuid=device_uuid, filter=filter,
                                                page_size=page_size, page_number=page_number, order_by=order_by)

            if inventory_dict:
                response = response_handle(inventory_dict, 200)
            else:
                response = response_handle(code=500,
                                           response="Unexpected error while fetching data from DB. Please check logs.")

        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    elif request.method == 'POST':
        try:
            if request.form:
                if not validate_json(json_data=request.form, schema_path="api/specs/inventory_post.json",
                                     logger=easyucs):
                    response = response_handle(code=400, response="Invalid payload")
                    return response

            device = load_object(object_type="device", object_uuid=device_uuid)
            if device:
                if device.task is not None:
                    response = response_handle(response="Device already has a task running: " + str(device.task.uuid),
                                               code=400)
                    return response
                
                try:
                    file = request.files['inventory_file']
                    json_file = file.read().decode("utf-8")
                except Exception as err:  # FIXME: Handle various exception cases - should only support JSON files
                    response = response_handle(response="Error while reading inventory file: " + str(err), code=500)
                    return response

                # If force_custom is not sent then its value must be None. If it's sent from the API then it should be
                # converted to boolean before passing it as an argument.
                force_custom = request.form.get('force_custom')
                if force_custom:
                    force_custom = force_custom == "true"

                inventory = device.inventory_manager.import_inventory(import_format="json", inventory=json_file,
                                                                      force_custom=force_custom)
                if inventory:
                    # Save the imported inventory
                    easyucs.repository_manager.save_to_repository(object=inventory)

                    inventory_metadata = {"device_uuid": str(inventory.metadata.device_uuid),
                                          "timestamp": inventory.metadata.timestamp.isoformat()[:-3] + 'Z',
                                          "uuid": str(inventory.metadata.uuid)}
                    for attribute in ["device_version", "easyucs_version", "is_custom", "is_hidden", "is_system",
                                      "name", "origin", "system_usage"]:
                        if getattr(inventory.metadata, attribute) not in [None, ""]:
                            inventory_metadata[attribute] = getattr(inventory.metadata, attribute)

                    inventory_dict = {"inventory": inventory_metadata}
                    response = response_handle(inventory_dict, 200)
                else:
                    response = response_handle(response="Impossible to import the file as an inventory", code=500)
            else:
                response = response_handle(response="Device not found with UUID: " + device_uuid, code=404)
        except BadRequest as err:
            response = response_handle(code=err.code, response=str(err.description))
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/<device_uuid>/inventories/actions", methods=['GET'])
# @cross_origin()
def device_uuid_inventories_actions(device_uuid):
    if request.method == 'GET':
        try:
            device_metadata_list = easyucs.repository_manager.get_metadata(object_type="device", uuid=device_uuid)
            if len(device_metadata_list) == 1:
                device_type = device_metadata_list[0].device_type

                actions = None
                if device_type in ["cimc", "imm_domain", "intersight", "ucsc", "ucsm"]:
                    actions = ["fetch"]

                actions_dict = {"actions": actions}

                response = response_handle(actions_dict, 200)
            else:
                response = response_handle(response="Device with UUID " + device_uuid + " not found", code=404)
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/<device_uuid>/inventories/actions/delete", methods=['POST'])
# @cross_origin()
def device_uuid_inventories_actions_delete(device_uuid):
    if request.method == 'POST':
        try:
            payload = request.json

            # Check if payload valid
            if not validate_json(json_data=payload, schema_path="api/specs/inventory_delete.json", logger=easyucs):
                response = response_handle(code=400, response="Invalid payload")
                return response

            inventory_uuid_list = []
            if "inventory_uuids" in payload:
                inventory_uuid_list = payload["inventory_uuids"]

            inventories_uuid_list = []

            for inventory_uuid in inventory_uuid_list:
                inventory_metadata_list = easyucs.repository_manager.get_metadata(object_type="inventory",
                                                                                  uuid=inventory_uuid)
                if len(inventory_metadata_list) == 1:
                    inventories_uuid_list.append(inventory_metadata_list[0])
                else:
                    response = response_handle(response="Inventory with UUID " + inventory_uuid + " not found",
                                               code=404)
                    return response

            if easyucs.repository_manager.delete_bulk_from_repository(metadata_list=inventories_uuid_list):
                response = response_handle(code=200)
            else:
                response = response_handle(code=500, response="Could not delete inventories from repository")

        except BadRequest as err:
            response = response_handle(code=err.code, response=str(err.description))
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/<device_uuid>/inventories/actions/fetch", methods=['POST'])
# @cross_origin()
def device_uuid_inventories_actions_fetch(device_uuid):
    if request.method == 'POST':
        try:
            payload = request.json

            # Check if payload valid
            if payload:
                if not validate_json(json_data=payload, schema_path="api/specs/fetch.json",
                                     logger=easyucs):
                    response = response_handle(code=400, response="Invalid payload")
                    return response

            force = payload.get("force", False) if payload else False

            device = load_object(object_type="device", object_uuid=device_uuid)
            if device:
                try:
                    # We create a new task
                    if device.metadata.device_type in ["cimc"]:
                        task_uuid = easyucs.task_manager.add_task(name="FetchInventoryUcsImc",
                                                                  device_name=str(device.name),
                                                                  device_uuid=str(device.uuid))
                    elif device.metadata.device_type in ["imm_domain"]:
                        task_uuid = easyucs.task_manager.add_task(name="FetchInventoryImmDomain",
                                                                  device_name=str(device.name),
                                                                  device_uuid=str(device.uuid))
                    elif device.metadata.device_type in ["intersight"]:
                        task_uuid = easyucs.task_manager.add_task(name="FetchInventoryIntersight",
                                                                  device_name=str(device.name),
                                                                  device_uuid=str(device.uuid))
                    elif device.metadata.device_type in ["ucsc"]:
                        task_uuid = easyucs.task_manager.add_task(name="FetchInventoryUcsCentral",
                                                                  device_name=str(device.name),
                                                                  device_uuid=str(device.uuid))
                    elif device.metadata.device_type in ["ucsm"]:
                        task_uuid = easyucs.task_manager.add_task(name="FetchInventoryUcsSystem",
                                                                  device_name=str(device.name),
                                                                  device_uuid=str(device.uuid))
                    else:
                        response = response_handle(response="Unsupported device type", code=500)
                        return response

                    # We schedule the fetch inventory action through the scheduler
                    pending_task = {
                        "task_uuid": task_uuid,
                        "action_type": "fetch",
                        "object_type": "inventory",
                        "timeout": timeout_values["fetch_inventory"],
                        "action_kwargs": {"force": force}
                    }
                    if not easyucs.task_manager.add_to_pending_tasks(pending_task):
                        response = response_handle(response="Error while scheduling the task. Task Queue might be Full."
                                                            " Try again after some time.", code=400)
                        return response

                except Exception as err:
                    response = response_handle(response="Error while fetching inventory: " + str(err), code=500)
                    return response

                response = response_handle(response={"task": str(task_uuid)}, code=200)
            else:
                response = response_handle(response="Device not found with UUID: " + device_uuid, code=404)
        except BadRequest as err:
            response = response_handle(code=err.code, response=str(err.description))
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/<device_uuid>/inventories/<inventory_uuid>", methods=['GET', 'DELETE'])
# @cross_origin()
def device_uuid_inventory_uuid(device_uuid, inventory_uuid):
    if request.method == 'GET':
        try:
            filter_attribute = request.args.get("filter_attribute", None)
            filter_type = request.args.get("filter_type", None)
            filter_value = request.args.get("filter_value", None)

            if filter_attribute is None or filter_type is None or filter_value is None:
                filter = None
            else:
                filter = [filter_attribute, filter_type, filter_value]

            page_size = request.args.get("page_size", None)
            page_number = int(request.args.get("page_number", 0))

            order_by_attribute = request.args.get("order_by_attribute", None)
            order_by_direction = request.args.get("order_by_direction", None)

            if order_by_attribute is None or order_by_direction is None:
                order_by = None
            else:
                order_by = (order_by_attribute, order_by_direction)

            inventory_dict = get_object_from_db(object_type="inventory", uuid=inventory_uuid, filter=filter,
                                                page_size=page_size, page_number=page_number, order_by=order_by)

            if inventory_dict:
                response = response_handle(inventory_dict, 200)
            else:
                response = response_handle(code=500, response=f"Could not find inventory with UUID {inventory_uuid}")

        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    elif request.method == 'DELETE':
        try:
            inventory_metadata_list = easyucs.repository_manager.get_metadata(object_type="inventory",
                                                                              uuid=inventory_uuid)
            if len(inventory_metadata_list) == 1:
                if easyucs.repository_manager.delete_from_repository(metadata=inventory_metadata_list[0]):
                    response = response_handle(code=200)
                else:
                    response = response_handle(code=500, response="Could not delete inventory from repository")
            else:
                response = response_handle(response="Inventory with UUID " + inventory_uuid + " not found", code=404)
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/<device_uuid>/inventories/<inventory_uuid>/actions", methods=['GET'])
# @cross_origin()
def device_uuid_inventory_uuid_actions(device_uuid, inventory_uuid):
    if request.method == 'GET':
        try:
            device_metadata_list = easyucs.repository_manager.get_metadata(object_type="device", uuid=device_uuid)
            if len(device_metadata_list) == 1:
                device_type = device_metadata_list[0].device_type

                inventory_metadata_list = easyucs.repository_manager.get_metadata(object_type="inventory",
                                                                                  uuid=inventory_uuid)
                if len(inventory_metadata_list) == 1:

                    actions = None
                    if device_type in ["cimc", "imm_domain", "intersight", "ucsc", "ucsm"]:
                        actions = ["download"]

                    actions_dict = {"actions": actions}

                    response = response_handle(actions_dict, 200)

                else:
                    response = response_handle(response="Inventory with UUID " + inventory_uuid + " not found",
                                               code=404)
            else:
                response = response_handle(response="Device with UUID " + device_uuid + " not found", code=404)
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/<device_uuid>/inventories/<inventory_uuid>/actions/download", methods=['GET'])
# @cross_origin()
def device_uuid_inventory_uuid_actions_download(device_uuid, inventory_uuid):
    if request.method == 'GET':
        try:
            # Trying to find device using its metadata (DB)
            easyucs.logger(level="debug", message="Trying to find device with UUID " + device_uuid + " from the DB")
            device_metadata_list = easyucs.repository_manager.get_metadata(object_type="device", uuid=device_uuid)
            if len(device_metadata_list) != 1:
                response = response_handle(response="Device not found with UUID: " + device_uuid, code=404)
                return response

            # Trying to find inventory using its metadata (DB)
            easyucs.logger(level="debug",
                           message="Trying to find inventory with UUID " + inventory_uuid + " from the DB")
            inventory_metadata_list = easyucs.repository_manager.get_metadata(object_type="inventory",
                                                                              uuid=inventory_uuid)
            if len(inventory_metadata_list) == 1:
                file_path = os.path.abspath(os.path.join(EASYUCS_ROOT, inventory_metadata_list[0].file_path))
                response = send_file(file_path, as_attachment=True,
                                     download_name="inventory_" + inventory_uuid + ".json")
            else:
                response = response_handle(response="Inventory not found with UUID: " + inventory_uuid, code=404)

        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/<device_uuid>/inventories/<inventory_uuid>/fabric_interconnects", methods=['GET'])
def device_uuid_inventory_uuid_fabric_interconnects(device_uuid, inventory_uuid):
    if request.method == 'GET':
        try:
            # Retrieve inventory metadata
            inventory_metadata_list = easyucs.repository_manager.get_metadata(object_type="inventory", uuid=inventory_uuid)
            if len(inventory_metadata_list) != 1:
                return response_handle(response=f"Inventory with UUID {inventory_uuid} not found", code=404)

            # Load the inventory file
            file_path = os.path.abspath(os.path.join(EASYUCS_ROOT, inventory_metadata_list[0].file_path))
            with open(file_path, "r") as file:
                inventory_data = json.load(file)
            # Extract relevant FI information
            fi_info = []
            if "inventory" in inventory_data:
                fabric_interconnects = inventory_data["inventory"].get("fabric_interconnects", [])
                # Extract only the first-level fields
                fi_info = [
                    {key: fi[key] for key in fi if not isinstance(fi[key], (dict, list))}
                    for fi in fabric_interconnects
                ]
            if not fi_info:
                return response_handle(response="No Fabric Interconnects information found in inventory", code=404)
            # Return the extracted FI information
            return response_handle(fi_info, 200)

        except Exception as err:
            return response_handle(code=500, response=str(err))

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/<device_uuid>/logs", methods=['GET'])
def device_uuid_logs(device_uuid):
    if request.method == 'GET':
        try:
            device = load_object(object_type="device", object_uuid=device_uuid)
            if device:
                try:
                    device_logs = device.get_logs()
                    if not device_logs:
                        logs_dict = {"logs": None}
                    else:
                        logs_dict = {"logs": device_logs}
                    response = response_handle(logs_dict, 200)

                except Exception as err:
                    response = response_handle(response="Error while getting device logs: " + str(err), code=500)
                    return response
            else:
                response = response_handle(response="Device with UUID " + device_uuid + " not found", code=404)
                return response

        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/<device_uuid>/reports", methods=['GET'])
# @cross_origin()
def device_uuid_reports(device_uuid):
    if request.method == 'GET':
        try:
            filter_attribute = request.args.get("filter_attribute", None)
            filter_type = request.args.get("filter_type", None)
            filter_value = request.args.get("filter_value", None)

            if filter_attribute is None or filter_type is None or filter_value is None:
                filter = None
            else:
                filter = [filter_attribute, filter_type, filter_value]

            order_by_attribute = request.args.get("order_by_attribute", None)
            order_by_direction = request.args.get("order_by_direction", None)

            if order_by_attribute is None or order_by_direction is None:
                order_by = None
            else:
                order_by = (order_by_attribute, order_by_direction)

            page_size = request.args.get("page_size", None)
            page_number = int(request.args.get("page_number", 0))

            report_dict = get_object_from_db(object_type="report", device_uuid=device_uuid, filter=filter,
                                             page_size=page_size, page_number=page_number, order_by=order_by)

            if report_dict:
                response = response_handle(report_dict, 200)
            else:
                response = response_handle(code=500,
                                           response="Unexpected error while fetching data from DB. Please check logs.")

        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/<device_uuid>/reports/actions", methods=['GET'])
# @cross_origin()
def device_uuid_reports_actions(device_uuid):
    if request.method == 'GET':
        try:
            device_metadata_list = easyucs.repository_manager.get_metadata(object_type="device", uuid=device_uuid)
            if len(device_metadata_list) == 1:
                device_type = device_metadata_list[0].device_type

                actions = None
                if device_type in ["cimc", "ucsm"]:
                    actions = ["generate"]

                actions_dict = {"actions": actions}

                response = response_handle(actions_dict, 200)
            else:
                response = response_handle(response="Device with UUID " + device_uuid + " not found", code=404)
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/<device_uuid>/reports/actions/delete", methods=['POST'])
# @cross_origin()
def device_uuid_reports_actions_delete(device_uuid):
    if request.method == 'POST':
        try:
            payload = request.json

            # Check if payload valid
            if not validate_json(json_data=payload, schema_path="api/specs/report_delete.json", logger=easyucs):
                response = response_handle(code=400, response="Invalid payload")
                return response

            report_uuid_list = []
            if "report_uuids" in payload:
                report_uuid_list = payload["report_uuids"]

            reports_uuid_list = []

            for report_uuid in report_uuid_list:
                report_metadata_list = easyucs.repository_manager.get_metadata(object_type="report", uuid=report_uuid)
                if len(report_metadata_list) == 1:
                    reports_uuid_list.append(report_metadata_list[0])
                else:
                    response = response_handle(response="Report with UUID " + report_uuid + " not found", code=404)
                    return response

            if easyucs.repository_manager.delete_bulk_from_repository(metadata_list=reports_uuid_list):
                response = response_handle(code=200)
            else:
                response = response_handle(code=500, response="Could not delete reports from repository")

        except BadRequest as err:
            response = response_handle(code=err.code, response=str(err.description))
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/<device_uuid>/reports/actions/generate", methods=['POST'])
# @cross_origin()
def device_uuid_reports_actions_generate(device_uuid):
    if request.method == 'POST':
        try:
            payload = request.json

            # Check if payload valid
            if not validate_json(json_data=payload, schema_path="api/specs/report_generate_post.json", logger=easyucs):
                response = response_handle(code=400, response="Invalid payload")
                return response

            config_uuid = payload.get("config_uuid", None)
            inventory_uuid = payload.get("inventory_uuid", None)

            action_kwargs = {}
            if "language" in payload:
                action_kwargs["language"] = payload["language"]
            if "output_formats" in payload:
                action_kwargs["output_formats"] = payload["output_formats"]
            if "page_layout" in payload:
                action_kwargs["page_layout"] = payload["page_layout"]
            if "size" in payload:
                action_kwargs["size"] = payload["size"]

            device = load_object(object_type="device", object_uuid=device_uuid)
            if device:
                # We first need to find & potentially load the config & inventory
                config = load_object(object_type="config", object_uuid=config_uuid, device=device)
                if config:
                    action_kwargs["config"] = config
                else:
                    response_message = easyucs.api_error_message
                    if not response_message:
                        response_message = "Failed to load config with UUID " + str(config_uuid)
                    response = response_handle(response=response_message, code=400)
                    return response

                inventory = load_object(object_type="inventory", object_uuid=inventory_uuid, device=device)
                if inventory:
                    action_kwargs["inventory"] = inventory
                else:
                    response = response_handle(response="Inventory not found with UUID: " + str(inventory_uuid),
                                               code=404)
                    return response

                try:
                    # We create a new task
                    if device.metadata.device_type in ["cimc"]:
                        task_uuid = easyucs.task_manager.add_task(
                            name="GenerateReportUcsImc", device_name=str(device.name), device_uuid=str(device.uuid),
                            config_uuid=str(config.uuid), inventory_uuid=str(inventory.uuid)
                        )
                    elif device.metadata.device_type in ["ucsm"]:
                        task_uuid = easyucs.task_manager.add_task(
                            name="GenerateReportUcsSystem", device_name=str(device.name), device_uuid=str(device.uuid),
                            config_uuid=str(config.uuid), inventory_uuid=str(inventory.uuid)
                        )
                    elif device.metadata.device_type in ["intersight"]:
                        task_uuid = easyucs.task_manager.add_task(
                            name="GenerateReportIntersight", device_name=str(device.name), device_uuid=str(device.uuid),
                            config_uuid=str(config.uuid), inventory_uuid=str(inventory.uuid)
                        )
                    else:
                        response = response_handle(response="Unsupported device type", code=500)
                        return response

                    # We schedule the "generate report" action through the scheduler
                    pending_task = {
                        "task_uuid": task_uuid,
                        "action_type": "generate",
                        "object_type": "report",
                        "timeout": timeout_values["generate_report"],
                        "action_kwargs": action_kwargs
                    }
                    if not easyucs.task_manager.add_to_pending_tasks(pending_task):
                        response = response_handle(response="Error while scheduling the task. Task Queue might be Full."
                                                            " Try again after some time.", code=400)
                        return response

                except Exception as err:
                    response = response_handle(response="Error while generating report: " + str(err), code=500)
                    return response

                response = response_handle(response={"task": str(task_uuid)}, code=200)
            else:
                response = response_handle(response="Device not found with UUID: " + device_uuid, code=404)
        except BadRequest as err:
            response = response_handle(code=err.code, response=str(err.description))
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/<device_uuid>/reports/<report_uuid>", methods=['GET', 'DELETE'])
# @cross_origin()
def device_uuid_report_uuid(device_uuid, report_uuid):
    if request.method == 'GET':
        try:
            filter_attribute = request.args.get("filter_attribute", None)
            filter_type = request.args.get("filter_type", None)
            filter_value = request.args.get("filter_value", None)

            if filter_attribute is None or filter_type is None or filter_value is None:
                filter = None
            else:
                filter = [filter_attribute, filter_type, filter_value]

            order_by_attribute = request.args.get("order_by_attribute", None)
            order_by_direction = request.args.get("order_by_direction", None)

            if order_by_attribute is None or order_by_direction is None:
                order_by = None
            else:
                order_by = (order_by_attribute, order_by_direction)

            page_size = request.args.get("page_size", None)
            page_number = int(request.args.get("page_number", 0))

            report_dict = get_object_from_db(object_type="report", uuid=report_uuid, filter=filter,
                                             page_size=page_size, page_number=page_number, order_by=order_by)

            if report_dict:
                response = response_handle(report_dict, 200)
            else:
                response = response_handle(code=500, response=f"Could not find report with UUID {report_uuid}")
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    elif request.method == 'DELETE':
        try:
            report_metadata_list = easyucs.repository_manager.get_metadata(object_type="report", uuid=report_uuid)
            if len(report_metadata_list) == 1:
                if easyucs.repository_manager.delete_from_repository(metadata=report_metadata_list[0]):
                    response = response_handle(code=200)
                else:
                    response = response_handle(code=500, response="Could not delete report from repository")
            else:
                response = response_handle(response="Report with UUID " + report_uuid + " not found", code=404)
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/<device_uuid>/reports/<report_uuid>/actions", methods=['GET'])
# @cross_origin()
def device_uuid_report_uuid_actions(device_uuid, report_uuid):
    if request.method == 'GET':
        try:
            device_metadata_list = easyucs.repository_manager.get_metadata(object_type="device", uuid=device_uuid)
            if len(device_metadata_list) == 1:
                device_type = device_metadata_list[0].device_type

                report_metadata_list = easyucs.repository_manager.get_metadata(object_type="report", uuid=report_uuid)
                if len(report_metadata_list) == 1:

                    actions = None
                    if device_type in ["cimc", "ucsm"]:
                        actions = ["download"]

                    actions_dict = {"actions": actions}

                    response = response_handle(actions_dict, 200)

                else:
                    response = response_handle(response="Report with UUID " + report_uuid + " not found", code=404)
            else:
                response = response_handle(response="Device with UUID " + device_uuid + " not found", code=404)
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/devices/<device_uuid>/reports/<report_uuid>/actions/download", methods=['GET'])
# @cross_origin()
def device_uuid_report_uuid_actions_download(device_uuid, report_uuid):
    if request.method == 'GET':
        try:
            # Trying to find device using its metadata (DB)
            easyucs.logger(level="debug", message="Trying to find device with UUID " + device_uuid + " from the DB")
            device_metadata_list = easyucs.repository_manager.get_metadata(object_type="device", uuid=device_uuid)
            if len(device_metadata_list) != 1:
                response = response_handle(response="Device not found with UUID: " + device_uuid, code=404)
                return response

            # Trying to find report using its metadata (DB)
            easyucs.logger(level="debug",
                           message="Trying to find report with UUID " + report_uuid + " from the DB")
            report_metadata_list = easyucs.repository_manager.get_metadata(object_type="report", uuid=report_uuid)
            if len(report_metadata_list) == 1:
                file_path = os.path.abspath(os.path.join(EASYUCS_ROOT, report_metadata_list[0].file_path))
                response = send_file(file_path, as_attachment=True,
                                     download_name=os.path.basename(report_metadata_list[0].file_path))
            else:
                response = response_handle(response="Report not found with UUID: " + report_uuid, code=404)

        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/inventories", methods=['GET'])
# @cross_origin()
def inventories():
    if request.method == 'GET':
        try:
            filter_attribute = request.args.get("filter_attribute", None)
            filter_type = request.args.get("filter_type", None)
            filter_value = request.args.get("filter_value", None)

            if filter_attribute is None or filter_type is None or filter_value is None:
                filter = None
            else:
                filter = [filter_attribute, filter_type, filter_value]

            order_by_attribute = request.args.get("order_by_attribute", None)
            order_by_direction = request.args.get("order_by_direction", None)

            if order_by_attribute is None or order_by_direction is None:
                order_by = None
            else:
                order_by = (order_by_attribute, order_by_direction)

            page_size = request.args.get("page_size", None)
            page_number = int(request.args.get("page_number", 0))

            inventory_dict = get_object_from_db(object_type="inventory", filter=filter, page_size=page_size,
                                                page_number=page_number, order_by=order_by)

            if inventory_dict:
                response = response_handle(inventory_dict, 200)
            else:
                response = response_handle(code=500,
                                           response="Unexpected error while fetching data from DB. Please check logs.")
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/logs/session", methods=['GET', 'POST'])
def logs():
    global logContent
    global displayLogsBool
    if request.method == 'GET':
        try:
            logs_dict = {"logs": logContent,
                         "displayLogsBool": displayLogsBool
                         }
            response = response_handle(logs_dict, 200)
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    elif request.method == 'POST':
        try:
            payload = request.json
            if not payload:
                return response_handle(code=400, response="Invalid payload")

            if not ("logs" in payload or "displayLogsBool" in payload):
                return response_handle(code=500, response="Impossible to save logs: wrong payload provided")

            if "logs" in payload:
                logs = payload["logs"]
                if not isinstance(logs, str):
                    return response_handle(code=500, response="Impossible to save logs string: not a string")
                logContent = logs

            if "displayLogsBool" in payload:
                logsBool = payload["displayLogsBool"]
                if not isinstance(logsBool, bool):
                    return response_handle(code=500, response="Impossible to save display log bool: not a boolean")
                displayLogsBool = logsBool

            response = response_handle(code=200)
        except BadRequest as err:
            response = response_handle(code=err.code, response=str(err.description))
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/reports", methods=['GET'])
# @cross_origin()
def reports():
    if request.method == 'GET':
        try:
            filter_attribute = request.args.get("filter_attribute", None)
            filter_type = request.args.get("filter_type", None)
            filter_value = request.args.get("filter_value", None)

            if filter_attribute is None or filter_type is None or filter_value is None:
                filter = None
            else:
                filter = [filter_attribute, filter_type, filter_value]

            order_by_attribute = request.args.get("order_by_attribute", None)
            order_by_direction = request.args.get("order_by_direction", None)

            if order_by_attribute is None or order_by_direction is None:
                order_by = None
            else:
                order_by = (order_by_attribute, order_by_direction)

            page_size = request.args.get("page_size", None)
            page_number = int(request.args.get("page_number", 0))

            report_dict = get_object_from_db(object_type="report", filter=filter, page_size=page_size,
                                             page_number=page_number, order_by=order_by)

            if report_dict:
                response = response_handle(report_dict, 200)
            else:
                response = response_handle(code=500,
                                           response="Unexpected error while fetching data from DB. Please check logs.")
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/tasks", methods=['GET'])
# @cross_origin()
def tasks():
    if request.method == 'GET':
        try:
            filter_attribute = request.args.get("filter_attribute", None)
            filter_type = request.args.get("filter_type", None)
            filter_value = request.args.get("filter_value", None)

            if filter_attribute is None or filter_type is None or filter_value is None:
                filter = None
            else:
                filter = [filter_attribute, filter_type, filter_value]

            order_by_attribute = request.args.get("order_by_attribute", None)
            order_by_direction = request.args.get("order_by_direction", None)

            if order_by_attribute is None or order_by_direction is None:
                order_by = None
            else:
                order_by = (order_by_attribute, order_by_direction)

            page_size = request.args.get("page_size", None)
            page_number = int(request.args.get("page_number", 0))

            task_dict = get_object_from_db(object_type="task", filter=filter, page_size=page_size,
                                           page_number=page_number, order_by=order_by)

            if task_dict:
                response = response_handle(task_dict, 200)
            else:
                response = response_handle(code=500,
                                           response="Unexpected error while fetching data from DB. Please check logs.")
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/tasks/<task_uuid>", methods=['GET'])
# @cross_origin()
def task_uuid(task_uuid):
    if request.method == 'GET':
        try:
            filter_attribute = request.args.get("filter_attribute", None)
            filter_type = request.args.get("filter_type", None)
            filter_value = request.args.get("filter_value", None)

            if filter_attribute is None or filter_type is None or filter_value is None:
                filter = None
            else:
                filter = [filter_attribute, filter_type, filter_value]

            order_by_attribute = request.args.get("order_by_attribute", None)
            order_by_direction = request.args.get("order_by_direction", None)

            if order_by_attribute is None or order_by_direction is None:
                order_by = None
            else:
                order_by = (order_by_attribute, order_by_direction)

            page_size = request.args.get("page_size", None)
            page_number = int(request.args.get("page_number", 0))

            task_dict = get_object_from_db(object_type="task", uuid=task_uuid, filter=filter, page_size=page_size,
                                           page_number=page_number, order_by=order_by)
            steps_dict = get_object_from_db(object_type="taskstep", task_uuid=task_uuid, order_by=("order", "desc"))

            if task_dict:
                if steps_dict and steps_dict.get("steps", None):
                    task_dict["task"]["steps"] = steps_dict["steps"]
                    response = response_handle(task_dict, 200)
                else:
                    response = response_handle(code=500,
                                               response=f"Error collecting task steps for task UUID {task_uuid}")
            else:
                response = response_handle(code=500,
                                           response=f"Could not find task with UUID {task_uuid}")
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/tasks/<task_uuid>/actions", methods=['GET'])
# @cross_origin()
def task_uuid_actions(task_uuid):
    if request.method == 'GET':
        try:
            actions = ["cancel"]
            actions_dict = {"actions": actions}
            response = response_handle(actions_dict, 200)
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/tasks/<task_uuid>/actions/cancel", methods=['POST'])
# @cross_origin()
def task_uuid_actions_cancel(task_uuid):
    if request.method == 'POST':
        try:
            task = easyucs.task_manager.find_task_by_uuid(uuid=task_uuid)
            if task:
                if task.metadata.status in ["in_progress"]:
                    task.cancel = True
                    retries = 0
                    while task.metadata.status not in ["failed", "successful"] and retries < 3:
                        time.sleep(1)
                        retries += 1
                    if retries >= 3 and task.metadata.status not in ["failed", "successful"]:
                        response = response_handle(response="Failed to cancel the task.", code=500)
                    else:
                        response = response_handle(code=200)
                elif task.metadata.status in ["pending"]:
                    easyucs.task_manager.stop_task(uuid=task_uuid, status="failed",
                                                   status_message="Task cancelled by user")
                    response = response_handle(code=200)
                else:
                    response = response_handle(
                        response="Task with UUID " + task_uuid + " is not pending or in progress", code=400)
            else:
                response = response_handle(response="Task with UUID " + task_uuid + " not found", code=404)
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/easyucs/settings", methods=['GET', 'PUT'])
# @cross_origin()
def easyucs_settings():
    if request.method == 'GET':
        try:
            settings = copy.deepcopy(easyucs.repository_manager.settings)
            settings_dict = {"settings": settings}
            response = response_handle(response=settings_dict, code=200)
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    elif request.method == 'PUT':
        try:
            payload = request.json
            if not validate_json(json_data=payload, schema_path="api/specs/easyucs_settings_put.json", logger=easyucs):
                response = response_handle(code=400, response="Invalid payload")
                return response

            settings = copy.deepcopy(easyucs.repository_manager.settings)
            for key in payload:
                if isinstance(payload[key], dict):
                    for field in payload[key]:
                            settings[key][field] = payload[key][field]
                else:
                    settings[key] = payload[key]

            # Updating the settings.json file
            with open("settings.json", "w") as settings_file:
                json.dump(settings, settings_file, indent=3)

            # Saving the updated settings.json in repository_manager.settings object
            easyucs.repository_manager._init_settings()

            # Returning the settings as response
            settings = copy.deepcopy(easyucs.repository_manager.settings)
            settings_dict = {"settings": settings}
            response = response_handle(response=settings_dict, code=200)
        except BadRequest as err:
            response = response_handle(code=err.code, response=str(err.description))
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/easyucs/backup/actions/download", methods=['POST'])
# @cross_origin()
def easyucs_backup_actions_download():
    if request.method == 'POST':
        try:
            payload = request.json
            if not validate_json(json_data=payload, schema_path="api/specs/easyucs_backup_download_post.json",
                                 logger=easyucs):
                response = response_handle(code=400, response="Invalid payload")
                return response

            if easyucs.task_manager.is_any_task_in_progress():
                response = response_handle(code=400, response="Some tasks are in-progress/pending. Please cancel or "
                                                              "wait for them to end.")
                return response

            output_files = [
                {
                    "file_path": os.path.join(EASYUCS_ROOT, 'data', 'files'),
                    "file_name": "devices"
                },
                {
                    "file_path": os.path.join(EASYUCS_ROOT, 'data', 'keys'),
                    "file_name": "keys"
                },
                {
                    "file_path": os.path.join(EASYUCS_ROOT, 'settings.json'),
                    "file_name": "settings.json"
                },
                {
                    "file_path": os.path.join(EASYUCS_ROOT, 'proxy_settings.json'),
                    "file_name": "proxy_settings.json"
                },
                # The backup file is always added as the last item in the list to ensure it can be deleted at the end,
                # after the response is streamed.
                {
                    "file_path": easyucs.repository_manager.create_db_backup(decrypt_passwords=True),
                    "file_name": easyucs.repository_manager.REPOSITORY_DB_BACKUP_NAME
                }
            ]

            # We get an encryption key of length 4-32 character as an input. If the length is less than 32 characters,
            # then we append the string with multiple "\0" to make it 32 char long. Then we encode the key using
            # urlsafe base64 alphabets to make it Fernet compatible.
            key = base64.urlsafe_b64encode(payload["encryption_key"].encode("utf-8").ljust(32, b"\0"))

            # Create a Fernet object with the key
            fernet = Fernet(key)

            tar_file_name = "backup.tar.gz"
            bin_file_name = "backup.bin"

            def stream_file():
                """
                Function to send backup.bin file as a stream of response. After sending the files, we delete the files.
                """
                # Iterate over the files/folder which needs to be archived. And them to the tar file.
                tar_file_path = os.path.join(EASYUCS_ROOT, easyucs.repository_manager.REPOSITORY_FOLDER_NAME,
                                             easyucs.repository_manager.REPOSITORY_TMP_FOLDER_NAME, tar_file_name)
                easyucs.logger(level="debug", message=f"Creating the {tar_file_name} file for backing up everything")
                with tarfile.open(tar_file_path, "w|gz") as tar:
                    for each_file in output_files:
                        if os.path.exists(each_file["file_path"]):
                            tar.add(each_file["file_path"],
                                    arcname=os.path.relpath(path=each_file["file_path"], start=EASYUCS_ROOT))

                # Reading and encrypting the tar data and creating a ".bin" file out of it
                bin_file_path = os.path.join(EASYUCS_ROOT, easyucs.repository_manager.REPOSITORY_FOLDER_NAME,
                                             easyucs.repository_manager.REPOSITORY_TMP_FOLDER_NAME, bin_file_name)
                easyucs.logger(level="debug", message=f"Encrypting the {tar_file_name} file to {bin_file_name} file")
                with open(tar_file_path, "rb") as f_read, open(bin_file_path, "wb") as f_write:
                    binary_tar_data = f_read.read()
                    encrypted_data = encrypt(data=binary_tar_data, fernet=fernet, logger=easyucs)
                    if not encrypted_data:
                        error_message = easyucs.api_error_message
                        if not error_message:
                            error_message = "Failed to encrypt the backup tar.gz file. Check logs."
                        return response_handle(code=500, response=error_message)
                    f_write.write(encrypted_data)

                with open(bin_file_path, "rb") as f_read:
                    yield from f_read

                # We delete the saved backup file at the end after the response is streamed
                easyucs.logger(level="debug", message=f"Removing the files: {tar_file_path}, {bin_file_path} and "
                                                      f"{output_files[-1]['file_path']}")
                os.remove(tar_file_path)
                os.remove(bin_file_path)
                os.remove(output_files[-1]["file_path"])

            response = Response(stream_file(), mimetype="application/octet-stream")
            response.headers["Content-Disposition"] = "attachment; filename=%s" % bin_file_name
        except BadRequest as err:
            response = response_handle(code=err.code, response=str(err.description))
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/easyucs/backup/actions/restore", methods=['POST'])
# @cross_origin()
def easyucs_backup_actions_restore():
    if request.method == 'POST':
        try:
            # We validate the form data using schema "easyucs_backup_download_post.json", because "request.form"
            # only contains attribute "encryption_key". So, we reuse the schema "easyucs_backup_download_post.json".
            if not validate_json(json_data=request.form, schema_path="api/specs/easyucs_backup_download_post.json",
                                 logger=easyucs):
                response = response_handle(code=400, response="Invalid payload")
                return response

            # Making sure that no tasks are in progress
            if easyucs.task_manager.is_any_task_in_progress():
                response = response_handle(code=400, response="Some tasks are in-progress/pending. Please cancel or "
                                                              "wait for them to end.")
                return response

            # We get an encryption key of length 4-32 character as an input. If the length is less than 32 characters,
            # then we append the string with multiple "\0" to make it 32 char long. Then we encode the key using
            # urlsafe base64 alphabets to make it Fernet compatible.
            key = base64.urlsafe_b64encode(request.form["encryption_key"].encode("utf-8").ljust(32, b"\0"))

            # Create a Fernet object with the key
            fernet = Fernet(key)

            # Object to store the backup file content
            bin_file = request.files['backup_file']

            # Decrypt the data using Fernet
            decrypted_data = decrypt(data=bin_file.read(), fernet=fernet, logger=easyucs)
            if not decrypted_data:
                error_message = easyucs.api_error_message
                if not error_message:
                    error_message = "Failed to decrypt the backup bin file. Check logs."
                return response_handle(code=500, response=error_message)

            db_backup_file_path = os.path.join(EASYUCS_ROOT, easyucs.repository_manager.REPOSITORY_FOLDER_NAME,
                                               easyucs.repository_manager.REPOSITORY_DB_FOLDER_NAME,
                                               easyucs.repository_manager.REPOSITORY_DB_BACKUP_NAME)

            tar_file_path = os.path.join(EASYUCS_ROOT, easyucs.repository_manager.REPOSITORY_FOLDER_NAME,
                                         easyucs.repository_manager.REPOSITORY_TMP_FOLDER_NAME,
                                         secure_filename("backup.tar.gz"))

            # Saving the backup file on disk.
            with open(tar_file_path, "wb") as tar_file:
                tar_file.write(decrypted_data)

            @after_this_request
            def cleanup(response):
                """
                Function to delete the saved files at the end of this request - whether it's successful or not
                """
                os.remove(tar_file_path)
                if os.path.exists(db_backup_file_path):
                    os.remove(db_backup_file_path)
                return response

            # If the backup is not a tar file then return error
            if not tarfile.is_tarfile(tar_file_path):
                response = response_handle(code=400, response="Invalid backup file. Please provide a valid backup file")
                return response

            # Steps for the restore:
            # 1. Extract the DB Backup file. Validate whether its compatible with current version.
            # 2. Delete the repository data (DB records and files).
            # 3. Extract rest of the files.
            # 4. Restore the key and settings file.
            # 5. Restore the DB Data.

            # Extract DB Backup file, to validate the backup file
            if not extract(tar_file=tar_file_path, logger=easyucs,
                           file_name=easyucs.repository_manager.REPOSITORY_DB_BACKUP_NAME):
                error_message = easyucs.api_error_message
                if not error_message:
                    error_message = "Failed to extract and decrypt the backup file. Check logs."
                return response_handle(code=400, response=error_message)

            # Read the contents of DB backup file and validate whether it could be applied to the current version
            with open(db_backup_file_path) as f:
                backup_data = json.load(f)
            backup_easyucs_version = backup_data["metadata"]["easyucs_version"]
            backup_easyucs_timestamp = backup_data["metadata"]["timestamp"]

            if Version(backup_easyucs_version) > Version(__version__):
                error_message = f"Cannot restore from higher EasyUCS version {backup_easyucs_version}"
                easyucs.logger(level="error", message=error_message)
                return response_handle(code=400, response=error_message)

            # Deleting the existing data from the DB
            easyucs.repository_manager.clear_db()

            # Deleting the existing files
            easyucs.repository_manager.clear_files()

            # Emptying the device_list and task list
            easyucs.device_manager.clear_device_list()
            easyucs.task_manager.clear_task_list()

            # Extract all the files from the tar
            if not extract(tar_file=tar_file_path, logger=easyucs):
                error_message = easyucs.api_error_message
                if not error_message:
                    error_message = "Failed to extract and decrypt the backup file. Check logs."
                return response_handle(code=400, response=error_message)

            # Processes restored files after a restore operation to handle specific upgrade scenarios
            if not easyucs.repository_manager.process_restored_files(backup_easyucs_version=backup_easyucs_version):
                return response_handle(code=400, response="Failed to process restored files Check logs.")

            # Restoring the key and settings from the backed up files
            if not easyucs.repository_manager.restore_key_and_settings_backup(
                    backup_version=backup_easyucs_version):
                return response_handle(code=400, response="Failed to restore Key and Settings. Check logs.")

            restore_repo = request.args.get("restore_repo", False, type=lambda v: v.lower() == 'true')

            # Restore all the data from the DB backup
            easyucs.logger(level="info", message=f"Restoring DB from EasyUCS {backup_easyucs_version}, backed "
                                                 f"up on {backup_easyucs_timestamp}")
            if not easyucs.repository_manager.restore_db_backup(db_backup_data=backup_data, restore_repo=restore_repo):
                error_message = easyucs.api_error_message
                if not error_message:
                    error_message = "Failed to restore DB data. Check logs."
                return response_handle(code=400, response=error_message)

            response = response_handle(code=200)
        except BadRequest as err:
            response = response_handle(code=err.code, response=str(err.description))
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/easyucs/certificates/trusted", methods=['GET', 'POST'])
# @cross_origin()
def easyucs_certificates_trusted():
    if request.method == 'GET':
        # This API end point retrieves information about all trusted certificates.
        try:
            certificate_list = get_certificate_details(logger=easyucs)

            response = response_handle(code=200, response={"certificates": certificate_list})

        except BadRequest as err:
            response = response_handle(code=err.code, response=str(err.description))
        except Exception as err:
            easyucs.logger(level="exception", message="Unexpected error while Displaying Certificate info")
            response = response_handle(code=500, response=str(err))
        return response

    elif request.method == 'POST':
        # This API end point uploads a new certificate file to the trusted store.
        try:
            if 'certificate' not in request.files:
                response = response_handle(code=400, response=f"No certificate file provided")
                return response

            certificate_file = request.files['certificate']
            if not (certificate_file.filename or "").endswith(('.cer', '.crt', '.pem', '.der')):
                response = response_handle(code=400, response="Invalid file format.")
                return response

            cert_data = certificate_file.read()
            if not cert_data:
                response = response_handle(code=400, response="The uploaded certificate file is empty. Please upload "
                                                              "a valid file.")
                return response
            # Validate certificate
            try:
                if cert_data.startswith(b'-----BEGIN CERTIFICATE-----'):
                    cert = x509.load_pem_x509_certificate(cert_data, default_backend())
                else:
                    cert = x509.load_der_x509_certificate(cert_data, default_backend())
                # Check whether uploaded certificate is a duplicate by comparing its 'issuer_name' and 'serial_number',
                # which uniquely identify the certificate, with those of existing certificates.
                issuer_name = cert.issuer.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
                serial_number = cert.serial_number
                for cert_detail in get_certificate_details(logger=easyucs):
                    if cert_detail["issued_by"] == issuer_name and cert_detail["serial_number"] == serial_number:
                        easyucs.logger(level="error", message=f"Cannot upload duplicate certificate")
                        response = response_handle(code=400, response="Cannot import certificate as it is already "
                                                                      "present in the trust store.")
                        return response

            except Exception as err:
                easyucs.logger(level="error", message=f"Failed to load certificate: {str(err)}")
                response = response_handle(code=400, response="Failed to load certificate:")
                return response

            certificate_dir_path = os.path.join(EASYUCS_ROOT, "data", "keys", "ca_certs")

            if not os.path.exists(certificate_dir_path):
                os.makedirs(certificate_dir_path)
            # Save the uploaded CA certificate with a generated UUID.
            filename = str(uuid.uuid4()) + ".pem"
            uploaded_file_path = os.path.join(certificate_dir_path, filename)
            certificate_file.save(uploaded_file_path)

            with open(uploaded_file_path, 'wb') as file:
                if cert_data.startswith(b'-----BEGIN CERTIFICATE-----'):
                    file.write(cert_data)
                # Convert a DER certificate file to PEM format
                else:
                    # Load the DER-encoded certificate
                    cert = crypto.load_certificate(crypto.FILETYPE_ASN1, cert_data)
                    # Write the PEM-encoded certificate
                    file.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))

            @after_this_request
            def cleanup(response):
                """
                Function to delete the certificate file at the end of this request if the requests fails
                """
                if response.status_code not in [200]:
                    if uploaded_file_path and os.path.exists(uploaded_file_path):
                        os.remove(uploaded_file_path)
                return response

            # Initialize the 'ca_cert.pem' file
            easyucs.repository_manager._init_ca_cert()

            # Update SSL CA certificate configuration for all devices
            for device_metadata in easyucs.repository_manager.get_metadata(object_type="device"):
                device = easyucs.device_manager.find_device_by_uuid(uuid=device_metadata.uuid)
                if device:
                    easyucs.device_manager.remove_device(uuid=device.uuid)
                    easyucs.device_manager.add_device(metadata=device_metadata)

            response = response_handle(code=200, response="Certificate uploaded successfully.")
            return response

        except BadRequest as err:
            response = response_handle(code=err.code, response=str(err.description))
        except Exception as err:
            easyucs.logger(level="exception", message="Unexpected error while uploading the root ca certificate!")
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/easyucs/certificates/trusted/<ca_cert_uuid>", methods=['DELETE'])
# @cross_origin()
def easyucs_certificates_trusted_ca_cert_uuid(ca_cert_uuid):
    if request.method == 'DELETE':
        try:
            trusted_ca_store = os.path.join(EASYUCS_ROOT, "data", "keys", "ca_certs")

            file_path = os.path.join(trusted_ca_store, ca_cert_uuid + ".pem")
            if os.path.exists(file_path):
                os.remove(file_path)

                # Remove ca_cert.pem if no CA certificates found in trusted store
                files_and_directories = os.listdir(trusted_ca_store)
                if len(files_and_directories) == 1 and "ca_cert.pem" in files_and_directories:
                    os.remove(os.path.join(trusted_ca_store, "ca_cert.pem"))

                # Update ca_cert.pem file by removing deleted file contents
                easyucs.repository_manager._init_ca_cert()

                # Remove deleted certificate file from SSL CA certificate configuration for all devices
                for device_metadata in easyucs.repository_manager.get_metadata(object_type="device"):
                    device = easyucs.device_manager.find_device_by_uuid(uuid=device_metadata.uuid)
                    if device:
                        easyucs.device_manager.remove_device(uuid=device.uuid)
                        easyucs.device_manager.add_device(metadata=device_metadata)

                response = response_handle(code=200, response="Certificate deleted successfully")
            else:
                response = response_handle(code=404, response="Certificate not found")
        except Exception as err:
            easyucs.logger(level="exception", message="Unexpected error while deleting certificate")
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route("/easyucs/proxy", methods=['GET', 'PUT'])
def easyucs_proxy():
    if request.method == "GET":
        try:
            proxy_details = read_json_file(file_path=os.path.join(EASYUCS_ROOT, "proxy_settings.json"),
                                           logger=easyucs) or {}
            for option in ['proxy_password']:
                proxy_details[option + '_set'] = True if proxy_details.get('encrypted_' + option) else False
            for option in ['encrypted_proxy_password']:
                if option in proxy_details:
                    del proxy_details[option]
            response = response_handle(proxy_details, code=200)
        except Exception as err:
            easyucs.logger(level="exception", message="Unexpected error while fetching the proxy details!")
            response = response_handle(code=500, response=str(err))
        return response

    elif request.method == "PUT":
        try:
            payload = request.json

            if not validate_json(json_data=payload, schema_path="api/specs/easyucs_proxy_put.json", logger=easyucs):
                response = response_handle(code=400, response="Invalid payload")
                return response

            for device in easyucs.device_manager.device_list:
                if device.task:
                    response = response_handle(code=400, response="Cannot change the proxy setting when a device task"
                                                                  " is in progress")
                    return response

            if not payload.get("proxy_url", ""):
                for device_metadata in easyucs.repository_manager.get_metadata(object_type="device"):
                    if device_metadata.use_proxy:
                        response = response_handle(code=400,
                                                   response="Cannot unset the proxy settings when some device(s) have"
                                                            " 'Use Proxy' enabled")
                        return response

            proxy_details = {
                "proxy_url": payload.get("proxy_url", ""),
                "proxy_port": payload.get("proxy_port", None),
                "proxy_authentication": payload.get("proxy_authentication", False),
                "proxy_username": payload.get("proxy_username", "")
            }
            cipher_suite = easyucs.repository_manager.cipher_suite
            if payload.get("proxy_password"):
                encrypted_password = cipher_suite.encrypt(bytes(payload.get("proxy_password"), encoding='utf8')) \
                    .decode('utf-8')
                proxy_details['encrypted_proxy_password'] = encrypted_password

            easyucs.logger(level="debug", message="Updating proxy details file 'proxy_settings.json'")
            with open(os.path.join(EASYUCS_ROOT, "proxy_settings.json"), 'w') as proxy_file:
                json.dump(proxy_details, proxy_file, indent=4)

            easyucs.logger(level="debug", message="Reloading all the devices in memory to make sure that the " +
                                                  "proxy is being set")
            for device_metadata in easyucs.repository_manager.get_metadata(object_type="device"):
                device = easyucs.device_manager.find_device_by_uuid(uuid=device_metadata.uuid)
                if device:
                    easyucs.device_manager.remove_device(uuid=device.uuid)
                    easyucs.device_manager.add_device(metadata=device_metadata)

            for option in ['proxy_password']:
                proxy_details[option + '_set'] = True if proxy_details.get('encrypted_' + option) else False
            for option in ['encrypted_proxy_password']:
                if option in proxy_details:
                    del proxy_details[option]

            response = response_handle(proxy_details, code=200)

        except BadRequest as err:
            response = response_handle(code=err.code, response=str(err.description))
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route('/repo/actions/checksum/<path:file_path>', methods=['POST'])
def repo_actions_checksum(file_path=None):
    file_hosting_path = absolute_file_path = os.path.abspath(os.path.join(
        EASYUCS_ROOT, easyucs.repository_manager.REPOSITORY_FOLDER_NAME,
        easyucs.repository_manager.SOFTWARE_REPOSITORY_FOLDER_NAME))
    if file_path:
        absolute_file_path = os.path.abspath(os.path.join(file_hosting_path, file_path))

    if os.path.commonpath([file_hosting_path]) != os.path.commonpath([file_hosting_path,
                                                                      absolute_file_path]):
        easyucs.logger(level="warning",
                       message=f"User is trying to access restricted path {absolute_file_path}")
        return response_handle(code=400, response=f"Please provide a valid file path")

    if not os.path.exists(absolute_file_path):
        response = response_handle(f"File {file_path} not found", 404)
        return response

    if request.method == 'POST':
        try:
            if not os.path.exists(absolute_file_path):
                response = response_handle("File not found", 404)
                return response

            if not os.path.isfile(absolute_file_path):
                response = response_handle("Not a file", 400)
                return response

            file_metadata = easyucs.repository_manager.get_metadata(object_type="repofile",
                                                                    repo_file_path=os.path.relpath(absolute_file_path,
                                                                                                   start=EASYUCS_ROOT))
            if len(file_metadata) == 1:
                file_metadata = file_metadata[0]
            elif len(file_metadata) < 1:
                # If the record do not exist then we create one.
                file_metadata = easyucs.repository_manager.repo.create_repofile_metadata(
                    file_path=os.path.relpath(absolute_file_path, start=EASYUCS_ROOT))
                easyucs.repository_manager.save_metadata(metadata=file_metadata)
            else:
                response = response_handle(response="More than 1 record found with same name.", code=500)
                return response

            # We create a new task
            task_uuid = easyucs.task_manager.add_task(name="CalculateChecksumsRepoFile",
                                                      repo_file_path=file_metadata.file_path,
                                                      repo_file_uuid=file_metadata.uuid)

            action_kwargs = {
                "file_path": absolute_file_path,
                "algorithms": ["MD5", "SHA1", "SHA256"]
            }

            # We schedule the calculate checksums action through the scheduler
            pending_task = {
                "task_uuid": task_uuid,
                "action_type": "calculate_checksums",
                "object_type": "repo",
                "timeout": timeout_values["calculate_checksums"],
                "action_kwargs": action_kwargs
            }
            if not easyucs.task_manager.add_to_pending_tasks(pending_task):
                response = response_handle(response="Error while scheduling the task. Task Queue might be Full."
                                                    " Try again after some time.", code=400)
                return response

            response = response_handle(response={"task": str(task_uuid)}, code=200)

        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route('/repo/actions/create_vmedia_policy', methods=['POST'])
def repo_actions_create_vmedia_policy():
    if request.method == 'POST':
        try:
            payload = request.json
            if not payload:
                return response_handle(code=400, response="Invalid payload")

            if not validate_json(json_data=payload, schema_path="api/specs/repo_actions_vmedia_post.json",
                                 logger=easyucs):
                return response_handle(code=400, response="Invalid payload")

            device_uuid = payload.get("device_uuid", None)

            device = load_object(object_type="device", object_uuid=device_uuid)

            if not device:
                return response_handle(response="Device not found with UUID: " + device_uuid, code=404)

            if device.task is not None:
                return response_handle(
                    response="Device already has a task running: " + str(device.task.uuid), code=500)

            action_kwargs = {
                "name": payload.get("name"),
                "device_name": device.name,
                "org_name": payload.get("org_name"),
                "enable_virtual_media": payload.get("enable_virtual_media"),
                "enable_virtual_encryption": payload.get("enable_virtual_encryption"),
                "enable_low_power_usb": payload.get("enable_low_power_usb")
            }
            if "description" in payload:
                action_kwargs["description"] = payload["description"]
            if "tags" in payload:
                action_kwargs["tags"] = payload["tags"]
            if "vmedia_mount" in payload:
                action_kwargs["vmedia_mount"] = payload["vmedia_mount"]

            # We create a new task
            if device.metadata.device_type in ["intersight"]:
                task_uuid = easyucs.task_manager.add_task(name="CreateVmediaPolicyIntersight",
                                                          device_name=str(device.name),
                                                          device_uuid=str(device.uuid))
            else:
                return response_handle(response="Unsupported device type", code=500)

            # We schedule the test connection action through the scheduler
            pending_task = {
                "task_uuid": task_uuid,
                "action_type": "create_vmedia_policy",
                "object_type": "device",
                "timeout": timeout_values["create_vmedia_policy"],
                "action_kwargs": action_kwargs
            }
            if not easyucs.task_manager.add_to_pending_tasks(pending_task):
                return response_handle(response="Error while scheduling the task. Task Queue might be Full."
                                                " Try again after some time.", code=400)

            response = response_handle(response={"task": str(task_uuid)}, code=200)

        except BadRequest as err:
            response = response_handle(code=err.code, response=str(err.description))
        except Exception as err:
            easyucs.logger(level="exception", message="Unexpected error while Creating vMedia Policy")
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route('/repo/actions/guess', methods=['POST'])
def repo_actions_guess():
    if request.method == 'POST':
        try:
            payload = request.json
            if not validate_json(json_data=payload, schema_path="api/specs/repo_guess_post.json",
                                 logger=easyucs):
                response = response_handle(code=400, response="Invalid payload")
                return response

            device_uuid = payload.get("device_uuid", None)
            image_name = payload.get("image_name", None)

            device = None
            if device_uuid:
                device = load_object(object_type="device", object_uuid=device_uuid)

            guessed_data = guess_image_metadata(image_name=image_name, device=device)

            response = response_handle(code=200, response=guessed_data)
        except BadRequest as err:
            response = response_handle(code=err.code, response=str(err.description))
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route('/repo/actions/sync_to_software_repository', methods=['POST'])
def repo_actions_sync_to_software_repository():
    if request.method == 'POST':
        try:
            payload = request.json
            if payload:
                if not validate_json(json_data=payload,
                                     schema_path="api/specs/repo_sync_to_software_repository_post.json",
                                     logger=easyucs):
                    response = response_handle(code=400, response="Invalid payload")
                    return response

            # We create the file download link if its not present in payload
            file_download_link = payload.get("file_download_link")
            if "file_download_link" not in payload:
                file_download_link = easyucs.repository_manager.repo.create_repofile_download_link(
                    host_url=request.host_url,
                    file_path=payload.get("file_path")
                )

            device_uuid = payload.get("device_uuid", None)

            device = load_object(object_type="device", object_uuid=device_uuid)

            if device:
                if device.task is not None:
                    response = response_handle(response="Device already has a task running: " + str(device.task.uuid),
                                               code=500)
                    return response

                action_kwargs = {
                    "file_download_link": file_download_link,
                    "image_type": payload["image_type"],
                    "name": payload["name"],
                    "org_name": payload["org_name"],
                    "version": payload["version"]
                }
                if "description" in payload:
                    action_kwargs["description"] = payload["description"]
                if "file_path" in payload:
                    path_prefix = os.path.join(easyucs.repository_manager.REPOSITORY_FOLDER_NAME,
                                               easyucs.repository_manager.SOFTWARE_REPOSITORY_FOLDER_NAME)
                    if not payload["file_path"].startswith(path_prefix):
                        action_kwargs["file_path"] = os.path.join(path_prefix, payload["file_path"])
                    else:
                        action_kwargs["file_path"] = payload["file_path"]
                if "file_uuid" in payload:
                    action_kwargs["file_uuid"] = payload["file_uuid"]
                if "firmware_image_type" in payload:
                    action_kwargs["firmware_image_type"] = payload["firmware_image_type"]
                if "supported_models" in payload:
                    action_kwargs["supported_models"] = payload["supported_models"]
                if "tags" in payload:
                    action_kwargs["tags"] = payload["tags"]
                if "vendor" in payload:
                    action_kwargs["vendor"] = payload["vendor"]

                # We create a new task
                if device.metadata.device_type in ["intersight"]:
                    task_uuid = easyucs.task_manager.add_task(name="SyncToIntersightSoftwareRepository",
                                                              device_name=str(device.name),
                                                              device_uuid=str(device.uuid),
                                                              repo_file_uuid=action_kwargs.get("file_uuid"),
                                                              repo_file_path=action_kwargs.get("file_path"))
                else:
                    response = response_handle(response="Unsupported device type", code=500)
                    return response

                # We schedule the test connection action through the scheduler
                pending_task = {
                    "task_uuid": task_uuid,
                    "action_type": "sync_to_software_repository",
                    "object_type": "device",
                    "timeout": timeout_values["sync_to_software_repository"],
                    "action_kwargs": action_kwargs
                }
                if not easyucs.task_manager.add_to_pending_tasks(pending_task):
                    response = response_handle(response="Error while scheduling the task. Task Queue might be Full."
                                                        " Try again after some time.", code=400)
                    return response

                response = response_handle(response={"task": str(task_uuid)}, code=200)
            else:
                response = response_handle(response="Device not found with UUID: " + device_uuid, code=404)
        except BadRequest as err:
            response = response_handle(code=err.code, response=str(err.description))
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route('/repo/actions/upload/', methods=['POST'])
@app.route('/repo/actions/upload/<path:file_path>', methods=['POST'])
def repo_actions_upload(file_path=None):
    file_hosting_path = absolute_file_path = os.path.abspath(os.path.join(
        EASYUCS_ROOT, easyucs.repository_manager.REPOSITORY_FOLDER_NAME,
        easyucs.repository_manager.SOFTWARE_REPOSITORY_FOLDER_NAME))
    if file_path:
        absolute_file_path = os.path.abspath(os.path.join(file_hosting_path, file_path))

    if os.path.commonpath([file_hosting_path]) != os.path.commonpath([file_hosting_path,
                                                                      absolute_file_path]):
        easyucs.logger(level="warning",
                       message=f"User is trying to access restricted path {absolute_file_path}")
        return response_handle(code=400, response=f"Please provide a valid file path")

    if not os.path.exists(absolute_file_path):
        response = response_handle(f"File {file_path} not found", 404)
        return response

    if request.method == 'POST':
        try:
            if not os.path.isdir(absolute_file_path):
                response = response_handle(f"File {file_path} is not a directory", 400)
                return response

            tmp_path = os.path.abspath(os.path.join(
                EASYUCS_ROOT, easyucs.repository_manager.REPOSITORY_FOLDER_NAME,
                easyucs.repository_manager.REPOSITORY_TMP_FOLDER_NAME))

            file = request.files["file"]
            file_uuid = request.form["uuid"]

            original_filename = file.filename
            if not original_filename:
                response = response_handle("No file provided", 400)
                return response

            # Generate a unique filename to avoid overwriting using 8 chars of uuid before filename.
            filename = f"{file_uuid[:8]}_{secure_filename(original_filename)}"

            tmp_file_path = os.path.join(tmp_path, filename)
            dest_file_path = os.path.join(absolute_file_path, original_filename)

            if os.path.exists(dest_file_path):
                response = response_handle("File with same name already exists", 400)
                return response

            use_chunks = request.args.get("use_chunks", True, type=lambda v: v.lower() == 'true')

            if use_chunks:
                cancel_upload = request.args.get("cancel", False, type=lambda v: v.lower() == 'true')

                # If upload is cancelled we remove the temporary file and return status code 200
                if cancel_upload:
                    if os.path.exists(tmp_file_path):
                        os.remove(tmp_file_path)
                    response = response_handle("Upload cancelled", 200)
                    return response

                current_chunk = int(request.form["chunk_index"])

                try:
                    with open(tmp_file_path, "ab") as f:
                        f.seek(int(request.form["chunk_byte_offset"]))
                        f.write(file.stream.read())
                except OSError:
                    # In case of error, delete the temporary file
                    if os.path.exists(tmp_file_path):
                        os.remove(tmp_file_path)
                    response = response_handle("Error appending to the existing file", 500)
                    return response

                total_chunks = int(request.form["total_chunk_count"])

                if current_chunk + 1 == total_chunks:
                    # This was the last chunk, the file should be complete and the size we expect
                    if os.path.getsize(tmp_file_path) != int(request.form["total_file_size"]):
                        # In case of error, delete the temporary file
                        if os.path.exists(tmp_file_path):
                            os.remove(tmp_file_path)
                        response = response_handle("File does not match the original size", 500)
                        return response

                    # After all the chunks are saved to tmp folder, we move the file to its designated position.
                    shutil.move(tmp_file_path, dest_file_path)
            else:
                file.save(dest_file_path)

            response = response_handle(code=200)
        except BadRequest as err:
            response = response_handle(code=err.code, response=str(err.description))
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route('/repo/actions/url/download/', methods=['POST'])
@app.route('/repo/actions/url/download/<path:file_path>', methods=['POST'])
def repo_actions_url_download(file_path=None):
    file_hosting_path = absolute_file_path = os.path.abspath(os.path.join(
        EASYUCS_ROOT, easyucs.repository_manager.REPOSITORY_FOLDER_NAME,
        easyucs.repository_manager.SOFTWARE_REPOSITORY_FOLDER_NAME))
    if file_path:
        absolute_file_path = os.path.abspath(os.path.join(file_hosting_path, file_path))

    if os.path.commonpath([file_hosting_path]) != os.path.commonpath([file_hosting_path,
                                                                      absolute_file_path]):
        easyucs.logger(level="warning",
                       message=f"User is trying to access restricted path {absolute_file_path}")
        return response_handle(code=400, response=f"Please provide a valid file path")

    if not os.path.exists(absolute_file_path):
        response = response_handle(f"File {file_path} not found", 404)
        return response

    if request.method == 'POST':
        try:
            if not os.path.isdir(absolute_file_path):
                response = response_handle(f"'{file_path}' is not a directory", 400)
                return response

            payload = request.json
            # Check if payload valid
            if payload:
                if not validate_json(json_data=payload, schema_path="api/specs/repo_actions_url_download_post.json",
                                     logger=easyucs):
                    response = response_handle(code=400, response="Invalid payload")
                    return response
            else:
                response = response_handle(code=400, response="Missing payload")
                return response

            download_url = payload.get("url")
            # Parse the URL to check if it contains a valid path segment which contains filename.
            parsed_url = urlparse(download_url)
            # If the URL does not contain a valid path segment,
            # return a response indicating the issue.
            if not parsed_url.path or parsed_url.path == "/":
                response = response_handle("Invalid URL: The URL does not contain a valid file path.", 400)
                return response
            # If 'file_name' is not provided in the payload and the last segment of the URL is empty,
            # second last segment of the URL is used as the filename.
            file_name = payload.get("file_name", download_url.split('/')[-1])
            if not file_name:
                file_name = download_url.split('/')[-2]
            verify_ssl = payload.get("verify_ssl", True)

            use_proxy = payload.get("use_proxy", False)
            if use_proxy:
                proxy_details = read_json_file(file_path=os.path.join(EASYUCS_ROOT, "proxy_settings.json"),
                                               logger=easyucs) or {}
                if not proxy_details.get("proxy_url", ""):
                    response = response_handle(response=f"Please set 'Proxy URL' in Proxy Settings and try again",
                                               code=400)
                    return response

            if os.path.exists(os.path.join(absolute_file_path, file_name)):
                response = response_handle("File with same name already exists", 400)
                return response

            # We create a new task
            task_uuid = easyucs.task_manager.add_task(name="DownloadFileFromUrl")

            action_kwargs = {
                "url": download_url,
                "path": absolute_file_path,
                "file_name": file_name,
                "verify_ssl": verify_ssl,
                "use_proxy": use_proxy
            }

            # We schedule the calculate checksums action through the scheduler
            pending_task = {
                "task_uuid": task_uuid,
                "action_type": "download_file",
                "object_type": "repo",
                "timeout": timeout_values["download_file"],
                "action_kwargs": action_kwargs
            }
            if not easyucs.task_manager.add_to_pending_tasks(pending_task):
                response = response_handle(response="Error while scheduling the task. Task Queue might be Full."
                                                    " Try again after some time.", code=400)
                return response

            response = response_handle(response={"task": str(task_uuid)}, code=200)

        except BadRequest as err:
            response = response_handle(code=err.code, response=str(err.description))
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


@app.route('/repo/files/', methods=['GET', 'POST'])
@app.route('/repo/files/<path:file_path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def repo_files(file_path=None):
    file_hosting_path = absolute_file_path = os.path.abspath(os.path.join(
        EASYUCS_ROOT, easyucs.repository_manager.REPOSITORY_FOLDER_NAME,
        easyucs.repository_manager.SOFTWARE_REPOSITORY_FOLDER_NAME))

    if file_path:
        absolute_file_path = os.path.abspath(os.path.join(file_hosting_path, file_path))

    if os.path.commonpath([file_hosting_path]) != os.path.commonpath([file_hosting_path,
                                                                      absolute_file_path]):
        easyucs.logger(level="warning",
                       message=f"User is trying to access restricted path {absolute_file_path}")
        return response_handle(code=400, response=f"Please provide a valid file path")

    if not os.path.exists(absolute_file_path):
        response = response_handle(f"File {file_path} not found", 404)
        return response

    if request.method == 'GET':
        # This API endpoint behaves differently based on the 'file_path' value:
        # If file_path=None or file_path=Directory: GET list of content and its details inside a directory
        # If file_path=File: Get the details of the file
        try:
            if os.path.isdir(absolute_file_path):
                total, used, available = get_disk_space_usage(file_hosting_path)
                summarize = request.args.get("summarize", False, type=lambda v: v.lower() == 'true')

                if not summarize:
                    recursive = request.args.get("recursive", False, type=lambda v: v.lower() == 'true')

                    def travel_folder(folder_path, result):
                        file_list = sorted(os.listdir(folder_path))
                        if file_list:
                            for file_name in file_list:
                                sub_file_path = os.path.join(folder_path, file_name)
                                file_info = {
                                    "name": file_name,
                                    "timestamp_last_modified": datetime.datetime.fromtimestamp(
                                        os.path.getmtime(sub_file_path)).isoformat()[:-3] + 'Z',
                                    "is_directory": os.path.isdir(sub_file_path)
                                }
                                if not file_info["is_directory"]:
                                    file_info = easyucs.repository_manager.repo.get_repofile(
                                        absolute_file_path=sub_file_path)
                                else:
                                    if recursive:
                                        file_info["sub_files"] = []
                                        travel_folder(sub_file_path, file_info["sub_files"])
                                result.append(file_info)

                    result = []
                    travel_folder(absolute_file_path, result)
                    result = {
                        "repofiles": result,
                        "disk_utilization": {
                            "total": total,
                            "used": used,
                            "available": available
                        }
                    }
                else:
                    result = {
                        "repofile": {
                            "name": os.path.basename(absolute_file_path),
                            "timestamp_last_modified": datetime.datetime.fromtimestamp(
                                os.path.getmtime(absolute_file_path)).isoformat()[:-3] + 'Z',
                            "is_directory": True
                        },
                        "disk_utilization": {
                            "total": total,
                            "used": used,
                            "available": available
                        }
                    }
                response = response_handle(result, 200)
            elif os.path.isfile(absolute_file_path):

                file_info = easyucs.repository_manager.repo.get_repofile(absolute_file_path=absolute_file_path,
                                                                         synced_data=True)
                file_info = {
                    "repofile": file_info
                }

                response = response_handle(file_info, 200)
            else:
                response = response_handle(code=500, response="Path is neither file nor folder")
        except Exception as err:
            response = response_handle(code=500, response=str(err))
        return response

    elif request.method == 'POST':
        # This API endpoint creates folders
        try:
            payload = request.json
            if not validate_json(json_data=payload, schema_path="api/specs/repo_files_post.json",
                                 logger=easyucs):
                response = response_handle(code=400, response="Invalid payload")
                return response

            folder_name = payload.get("folder_name")

            if not os.path.isdir(absolute_file_path):
                response = response_handle(code=400, response=f"Path {absolute_file_path} is not a directory")
                return response

            folder_path = os.path.join(absolute_file_path, folder_name)

            if os.path.exists(folder_path):
                response = response_handle(code=400, response=f"Folder {folder_path} already exists")
                return response

            os.makedirs(folder_path)
            response = response_handle(code=200)
        except BadRequest as err:
            easyucs.logger(level="error", message=str(err))
            response = response_handle(code=err.code, response=str(err.description))
        except Exception as err:
            easyucs.logger(level="error", message=str(err))
            response = response_handle(code=500, response=str(err))
        return response

    elif request.method == 'PUT':
        # This API endpoint moves/renames the file path
        try:
            payload = request.json
            if not validate_json(json_data=payload, schema_path="api/specs/repo_files_put.json",
                                 logger=easyucs):
                response = response_handle(code=400, response="Invalid payload")
                return response

            if not file_path:
                response = response_handle("Rename failed as no directory path mentioned", code=400)
                return response

            target_path = payload.get("target_path")
            absolute_target_path = os.path.join(file_hosting_path, target_path)

            if os.path.commonpath([file_hosting_path]) != os.path.commonpath([file_hosting_path,
                                                                              absolute_target_path]):
                easyucs.logger(level="warning",
                               message=f"User is trying to access restricted path {absolute_target_path}")
                return response_handle(code=400, response=f"Please provide a valid file path")

            if os.path.exists(absolute_target_path):
                response = response_handle(f"File/Folder {absolute_target_path} already exists", code=400)
                return response

            if not os.path.exists(os.path.dirname(absolute_target_path)):
                response = response_handle(f"Directory {os.path.dirname(target_path)} does not exists",
                                           code=400)
                return response

            shutil.move(absolute_file_path, absolute_target_path)
            response = response_handle(code=200)

        except BadRequest as err:
            easyucs.logger(level="error", message=str(err))
            response = response_handle(code=err.code, response=str(err.description))
        except Exception as err:
            easyucs.logger(level="error", message=str(err))
            response = response_handle(code=500, response=str(err))
        return response

    elif request.method == 'DELETE':
        # This API endpoint deletes the file path
        try:
            if os.path.isfile(absolute_file_path):
                # If it's a file we delete it directly
                os.remove(absolute_file_path)
                response = response_handle(code=200)
            elif os.path.isdir(absolute_file_path):
                # If it's a directory then we perform deletion based on whether there is content inside it or not.
                if not os.listdir(absolute_file_path):
                    # If directory is empty then we remove the directory
                    os.rmdir(absolute_file_path)
                    response = response_handle(code=200)
                else:
                    # If directory have some content then we make sure to delete sub files/folders before deleting the
                    # directory.
                    # Here topdown=False is used when calling os.walk() to ensure that the files and subdirectories
                    # within the directory are deleted first before attempting to delete the parent directory.
                    for root, dirs, files in os.walk(absolute_file_path, topdown=False):
                        for file in files:
                            os.remove(os.path.join(root, file))
                        for directory in dirs:
                            os.rmdir(os.path.join(root, directory))
                    os.rmdir(absolute_file_path)
                    response_message = "Deleted directory " + os.path.basename(absolute_file_path)
                    response = response_handle(response_message, 200)
            else:
                response = response_handle(code=500, response="Path is neither file nor folder")
        except Exception as err:
            easyucs.logger(level="error", message=str(err))
            response = response_handle(code=500, response=str(err))
        return response

    else:
        return response_handle(code=500, response="Invalid HTTP method")


def start(easyucs_object=None):
    global easyucs
    easyucs = easyucs_object
    # app.run(threaded=True)
