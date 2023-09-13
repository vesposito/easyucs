# coding: utf-8
# !/usr/bin/env python

""" export.py: Easy UCS Deployment Tool """
import hashlib

from __init__ import __version__
from config.object import GenericConfigObject
from inventory.object import GenericInventoryObject


def export_attributes_json(current_object, output_json):
    """
    Exports attributes of the given Object in JSON format in recursive fashion
    :return: nothing
    """
    try:
        if isinstance(current_object, dict):
            # We have a plain dictionary that is not an EasyUCS object
            for attribute in sorted(current_object.keys()):
                if not attribute.startswith('_') and not attribute == "dn" \
                        and current_object[attribute] is not None:
                    if isinstance(current_object[attribute], dict):
                        output_json[attribute] = {}
                        export_attributes_json(current_object[attribute], output_json[attribute])
                    elif not isinstance(current_object[attribute], list):
                        if attribute == "password":
                            # We export passwords in encrypted form if EasyUCS is run with the repository engine
                            from api.api_server import easyucs
                            if easyucs:
                                cipher_suite = easyucs.repository_manager.cipher_suite
                                encrypted_password = cipher_suite.encrypt(bytes(current_object[attribute],
                                                                                encoding='utf8'))
                                output_json["encrypted_password"] = encrypted_password.decode('utf-8')
                            else:
                                output_json[attribute] = current_object[attribute]
                        else:
                            output_json[attribute] = current_object[attribute]
                    else:
                        if len(current_object[attribute]) == 0:
                            continue
                        output_json[attribute] = []
                        element_count = 0
                        for element in current_object[attribute]:
                            if not isinstance(element, (str, float, int)):
                                output_json[attribute].append({})
                                export_attributes_json(element, output_json[attribute][element_count])
                            else:
                                output_json[attribute].append(element)
                            element_count += 1
        else:
            # We have an EasyUCS object
            for attribute in sorted(vars(current_object)):
                if not attribute.startswith('_') and not attribute == "dn" \
                        and getattr(current_object, attribute) is not None:
                    if isinstance(getattr(current_object, attribute), dict):
                        # Attribute of EasyUCS object is a dictionary
                        output_json[attribute] = {}
                        export_attributes_json(getattr(current_object, attribute), output_json[attribute])
                    elif any(isinstance(getattr(current_object, attribute), x) for x in [GenericConfigObject,
                                                                                         GenericInventoryObject]):
                        # Attribute of EasyUCS object is an EasyUCS object
                        output_json[attribute] = {}
                        export_attributes_json(getattr(current_object, attribute), output_json[attribute])
                    elif not isinstance(getattr(current_object, attribute), list):
                        # Attribute of EasyUCS object is a regular value
                        if attribute == "password":
                            # We export passwords in encrypted form if EasyUCS is run with the repository engine
                            from api.api_server import easyucs
                            if easyucs:
                                cipher_suite = easyucs.repository_manager.cipher_suite
                                encrypted_password = cipher_suite.encrypt(bytes(getattr(current_object, attribute),
                                                                                encoding='utf8')).decode('utf-8')
                                output_json["encrypted_password"] = encrypted_password
                            else:
                                output_json[attribute] = getattr(current_object, attribute)
                        else:
                            output_json[attribute] = getattr(current_object, attribute)
                    else:
                        # Attribute of EasyUCS object is a list
                        if len(getattr(current_object, attribute)) == 0:
                            continue
                        output_json[attribute] = []
                        element_count = 0
                        for element in getattr(current_object, attribute):
                            if not isinstance(element, (str, float, int)):
                                output_json[attribute].append({})
                                export_attributes_json(element, output_json[attribute][element_count])
                            else:
                                output_json[attribute].append(element)
                            element_count += 1

    except TypeError as err:
        print("Error while trying to export " + str(current_object) + ": " + str(err))


def generate_json_metadata_header(file_type=None, inventory=None, config=None, device=None, report=None,
                                  name=None, category=None, subcategory=None, url=None, revision=None):
    """
    Generates an easyucs metadata JSON header for an export file
    :param file_type: Export file type (e.g. "inventory", "config", "device")
    :param inventory: If the export file type is "inventory", this must contain the inventory to be exported
    :param config: If the export file type is "config", this must contain the config to be exported
    :param device: If the export file type is "device", this must contain the device to be exported
    :param report: If the export file type is "report", this must contain the report to be exported
    :param name: Name of the export file
    :param category: Category of the export file (used to categorize config files)
    :param subcategory: Subcategory of the export file (used to categorize config files)
    :param url: Associated URL if applicable
    :param revision: Revision of the file if applicable
    :return: The metadata JSON header if successful, None otherwise
    """
    if file_type is None:
        return None
    if inventory is None and config is None and device is None and report is None:
        return None
    if file_type == "inventory" and inventory is None:
        return None
    if file_type == "config" and config is None:
        return None
    if file_type == "device" and device is None:
        return None
    if file_type == "report" and report is None:
        return None

    json_metadata_header = {
        "easyucs_version": __version__,
        "file_type": file_type
    }

    if file_type == "inventory":
        json_metadata_header["uuid"] = str(inventory.uuid)

        if inventory.metadata.device_name is not None:
            json_metadata_header["device_name"] = inventory.metadata.device_name
        if inventory.device.metadata.device_type is not None:
            json_metadata_header["device_type"] = inventory.device.metadata.device_type
        if inventory.metadata.device_uuid is not None:
            json_metadata_header["device_uuid"] = str(inventory.metadata.device_uuid)
        if inventory.metadata.device_version is not None:
            json_metadata_header["device_version"] = inventory.metadata.device_version
        if inventory.metadata.origin is not None:
            json_metadata_header["origin"] = inventory.metadata.origin
        if inventory.metadata.timestamp is not None:
            json_metadata_header["timestamp"] = inventory.metadata.timestamp.strftime("%a, %d %b %Y %H:%M:%S")
            # json_metadata_header["timestamp"] = time.strftime("%a, %d %b %Y %H:%M:%S", inventory.metadata.timestamp)

        if hasattr(inventory.parent.parent, "intersight_status"):
            json_metadata_header["intersight_status"] = inventory.parent.parent.intersight_status
    elif file_type == "config":
        json_metadata_header["uuid"] = str(config.uuid)

        if config.metadata.category is not None:
            json_metadata_header["category"] = config.metadata.category
        if config.metadata.device_name is not None:
            json_metadata_header["device_name"] = config.metadata.device_name
        if config.device.metadata.device_type is not None:
            json_metadata_header["device_type"] = config.device.metadata.device_type
        if config.metadata.device_uuid is not None:
            json_metadata_header["device_uuid"] = str(config.metadata.device_uuid)
        if config.metadata.device_version is not None:
            json_metadata_header["device_version"] = config.metadata.device_version
        if config.metadata.name is not None:
            json_metadata_header["name"] = config.metadata.name
        if config.metadata.origin is not None:
            json_metadata_header["origin"] = config.metadata.origin
        if config.metadata.revision is not None:
            json_metadata_header["revision"] = config.metadata.revision
        if config.metadata.subcategory is not None:
            json_metadata_header["subcategory"] = config.metadata.subcategory
        if config.metadata.timestamp is not None:
            json_metadata_header["timestamp"] = config.metadata.timestamp.strftime("%a, %d %b %Y %H:%M:%S")
            # json_metadata_header["timestamp"] = time.strftime("%a, %d %b %Y %H:%M:%S", config.metadata.timestamp)
        if config.metadata.url is not None:
            json_metadata_header["url"] = config.metadata.url

        if hasattr(config.parent.parent, "intersight_status"):
            json_metadata_header["intersight_status"] = config.parent.parent.intersight_status
    elif file_type == "device":
        json_metadata_header["device_uuid"] = str(device.uuid)

        if device.metadata.device_name is not None:
            json_metadata_header["device_name"] = device.metadata.device_name
        if device.metadata.device_type is not None:
            json_metadata_header["device_type"] = device.metadata.device_type
        if device.metadata.device_version is not None:
            json_metadata_header["device_version"] = device.metadata.device_version

        if hasattr(device, "intersight_status"):
            json_metadata_header["intersight_status"] = device.intersight_status
    elif file_type == "report":
        json_metadata_header["uuid"] = str(report.uuid)

        if report.metadata.report_type is not None:
            json_metadata_header["report_type"] = report.metadata.report_type
        if report.metadata.device_name is not None:
            json_metadata_header["device_name"] = report.metadata.device_name
        if report.device.metadata.device_type is not None:
            json_metadata_header["device_type"] = report.device.metadata.device_type
        if report.metadata.device_uuid is not None:
            json_metadata_header["device_uuid"] = str(report.metadata.device_uuid)
        if report.metadata.device_version is not None:
            json_metadata_header["device_version"] = report.metadata.device_version
        if report.config is not None:
            json_metadata_header["config_uuid"] = str(report.config.uuid)
        if report.inventory is not None:
            json_metadata_header["inventory_uuid"] = str(report.inventory.uuid)
        if report.metadata.timestamp is not None:
            json_metadata_header["timestamp"] = report.metadata.timestamp.strftime("%a, %d %b %Y %H:%M:%S")

    return json_metadata_header


def insert_json_metadata_hash(json_content=None):
    """
    Inserts a SHA-256 hash of the supplied JSON file in the metadata header
    :param json_content: JSON file to be hashed
    :return: JSON content with inserted SHA-256 hash if successful, None otherwise
    """
    if json_content is None:
        return None

    if "easyucs" not in json_content:
        return None

    if "metadata" not in json_content["easyucs"]:
        return None

    json_content["easyucs"]["metadata"][0]["hash"] = hashlib.sha256(str(json_content).encode()).hexdigest()
    return json_content


def verify_json_metadata_hash(json_content=None):
    """
    Verifies the SHA-256 hash in the metadata header of the supplied JSON file
    :param json_content: JSON file containing the hash header
    :return: True if hash is verified, False otherwise
    """
    if json_content is None:
        return False

    if "easyucs" not in json_content:
        return False

    if "metadata" not in json_content["easyucs"]:
        return False

    if "hash" not in json_content["easyucs"]["metadata"][0]:
        return False

    file_hash = json_content["easyucs"]["metadata"][0]["hash"]
    json_content["easyucs"]["metadata"][0].pop("hash")

    calculated_hash = hashlib.sha256(str(json_content).encode()).hexdigest()

    if file_hash == calculated_hash:
        return True
    return False
