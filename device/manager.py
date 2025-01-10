# coding: utf-8
# !/usr/bin/env python

""" manager.py: Easy UCS Deployment Tool """

import json
import os

import common
import export
from __init__ import __version__, EASYUCS_ROOT
from device.imm_domain.device import ImmDomainDevice, ImmDomainFiDevice
from device.intersight.device import IntersightDevice
from device.ucs.device import UcsSystem, UcsImc, UcsCentral
from repository.metadata import DeviceMetadata


class DeviceManager:
    REPOSITORY_FOLDER_NAME = "repository"

    def __init__(self, parent=None):
        self.device_list = []
        self.parent = parent

        self._parent_having_logger = self._find_logger()

    def logger(self, level='info', message="No message"):
        if not self._parent_having_logger:
            self._parent_having_logger = self._find_logger()

        if self._parent_having_logger:
            self._parent_having_logger.logger(level=level, message=message)

    def _find_logger(self):
        # Method to find the object having a logger - it can be high up in the hierarchy of objects
        current_object = self
        while hasattr(current_object, 'parent') and not hasattr(current_object, '_logger_handle'):
            current_object = current_object.parent

        if hasattr(current_object, '_logger_handle'):
            return current_object
        else:
            print("WARNING: No logger found in Device Manager")
            return None

    def add_device(self, metadata=None, device_type=None, uuid=None, target=None, username=None, password=None,
                   key_id=None, private_key_path=None, sub_device_uuids=None, standalone=False, parent_device_uuid=None,
                   is_hidden=False, is_system=False, system_usage=None, logger_handle_log_level=None, 
                   bypass_connection_checks=False, bypass_version_checks=False, use_proxy=False, user_label=None):
        """
        Adds a device to the list of devices
        :param metadata: The metadata object of to the device to be added (if no device details provided)
        :param device_type: The type of device to be added (e.g. "ucsm")
        :param uuid: The UUID of the device to be added
        :param target: The IP address/hostname of the device
        :param username: The username/login of the device
        :param password: The password of the device
        :param key_id: The key ID of the device (for Intersight devices)
        :param private_key_path: The private key path of the device (for Intersight devices)
        :param sub_device_uuids: The uuid's of the sub devices (for IMM domain devices)
        :param standalone: Indicates if the IMM domain device is standalone. Currently, this parameter is not relevant,
        as the IMM domain cannot be built using a single FI. However, it is included for potential future changes.
        :param parent_device_uuid: The UUID of the parent device
        :param is_hidden: Whether the device should be set to hidden
        :param is_system: Whether the device is a system device
        :param system_usage: If device is a system device, indicates the usage for this system device (e.g. "catalog")
        :param use_proxy: Whether the device should use the proxy
        :param logger_handle_log_level: The log level of the device to be added (e.g. "info", "debug", ...)
        :param bypass_connection_checks: Whether the device needs to bypass the connection check or not
        :param bypass_version_checks: Whether the device needs to bypass the version check or not
        :param user_label: The user defined label about the device.
        :return: UUID of device if add is successful, False otherwise
        """
        if isinstance(metadata, DeviceMetadata):
            device_type = metadata.device_type
            uuid = metadata.uuid
            target = metadata.target
            username = metadata.username
            password = metadata.password
            key_id = metadata.key_id
            private_key_path = metadata.private_key_path
            sub_device_uuids = metadata.sub_device_uuids
            if sub_device_uuids and len(sub_device_uuids) > 1:
                standalone = False
            parent_device_uuid = metadata.parent_device_uuid
            is_hidden = metadata.is_hidden
            is_system = metadata.is_system
            system_usage = metadata.system_usage
            use_proxy = metadata.use_proxy
            bypass_connection_checks = metadata.bypass_connection_checks
            bypass_version_checks = metadata.bypass_version_checks
            user_label = metadata.user_label

        if device_type is None:
            self.logger(level="error", message="Missing device_type in device add request!")
            return False

        if device_type not in ["cimc", "imm_domain", "intersight", "ucsc", "ucsm"]:
            self.logger(level="error", message="Device type not recognized. Could not add device")
            return False

        if not is_system:
            if device_type in ["intersight"]:
                if key_id is None or private_key_path is None:
                    self.logger(level="error", message="Missing key_id or private_key_path in device add request!")
                    return False
            else:
                if target is None or username is None or password is None:
                    self.logger(level="error", message="Missing target, username or password in device add request!")
                    return False

        if logger_handle_log_level is None:
            logger_handle_log_level = self.parent.logger_handle_log_level

        proxy = None
        proxy_username = None
        proxy_password = None
        if use_proxy:
            proxy, proxy_username, proxy_password = common.get_proxy_url(logger=self)
            if not proxy:
                self.logger(level="error", message="Failed to get proxy URL in proxy_settings.json! Proceeding to add "
                                                   "device without using proxy")

        certificate_path = os.path.join(EASYUCS_ROOT, "data", "keys", "ca_certs", "ca_cert.pem")
        ca_cert_file = None
        if os.path.exists(certificate_path):
            ca_cert_file = certificate_path

        if device_type == "cimc":
            device = UcsImc(parent=self, uuid=uuid, target=target, user=username, password=password,
                            is_hidden=is_hidden, is_system=is_system, system_usage=system_usage,
                            logger_handle_log_level=logger_handle_log_level,
                            bypass_connection_checks=bypass_connection_checks,
                            bypass_version_checks=bypass_version_checks, user_label=user_label)
        elif device_type == "imm_domain":
            device = ImmDomainDevice(parent=self, uuid=uuid, target=target, username=username, password=password,
                                     sub_device_uuids=sub_device_uuids, standalone=standalone, is_hidden=is_hidden,
                                     is_system=is_system, system_usage=system_usage,
                                     logger_handle_log_level=logger_handle_log_level, user_label=user_label)
            if sub_device_uuids:
                sub_devices = []
                # Add references to the sub devices in parent device and vice versa.
                # NOTE: We are not doing this to add sub devices to memory (device_list), we had to add them to memory
                # because we want to create relationship between parent and sub devices. Eg: In this case we want
                # ImmDomain device to have 'sub_devices', 'fi_a' and 'fi_b' containing its sub devices.
                # NOTE: When a ImmDomain device is created for the first time, these relationships are created
                # in the __init__ of the ImmDomain device. So, in this case those sub devices won't be added
                # to the device_list.
                for sub_device_uuid in sub_device_uuids:
                    if not self.find_device_by_uuid(uuid=sub_device_uuid):
                        sub_device_metadata = self.parent.repository_manager.get_metadata(object_type="device",
                                                                                          uuid=sub_device_uuid)
                        if sub_device_metadata:
                            self.add_device(device_type="imm_domain_fi", metadata=sub_device_metadata[0])

                    sub_device = self.find_device_by_uuid(uuid=sub_device_uuid)
                    if isinstance(sub_device, ImmDomainFiDevice):
                        sub_devices.append(sub_device)
                    elif not sub_device:
                        self.logger(level="error",
                                    message=f"Sub device UUID {sub_device_uuid} of IMM Domain device with UUID "
                                            f"{device.metadata.uuid} is not an IMM Domain FI device.")
                        return False
                    else:
                        self.logger(level="error",
                                    message=f"Sub device UUID of IMM Domain device with UUID {device.metadata.uuid} "
                                            f"is not an IMM Domain FI device.")
                        return False
                device.sub_devices = sub_devices
                device.fi_a = sub_devices[0]
                device.fi_a.parent_device = device
                if len(sub_devices) > 1:
                    device.fi_b = sub_devices[1]
                    device.fi_b.parent_device = device
        elif device_type == "imm_domain_fi":
            device = ImmDomainFiDevice(parent=self, uuid=uuid, username=username, password=password,
                                       parent_device_uuid=parent_device_uuid, is_hidden=is_hidden, is_system=is_system,
                                       system_usage=system_usage, logger_handle_log_level=logger_handle_log_level,
                                       user_label=user_label)
        elif device_type == "intersight":
            if target:
                device = IntersightDevice(parent=self, uuid=uuid, target=target, key_id=key_id,
                                          private_key_path=private_key_path, is_hidden=is_hidden, is_system=is_system,
                                          system_usage=system_usage, proxy=proxy, proxy_user=proxy_username,
                                          proxy_password=proxy_password,
                                          logger_handle_log_level=logger_handle_log_level,
                                          bypass_connection_checks=bypass_connection_checks,
                                          bypass_version_checks=bypass_version_checks,
                                          user_label=user_label)
            else:
                device = IntersightDevice(parent=self, uuid=uuid, key_id=key_id, private_key_path=private_key_path,
                                          is_hidden=is_hidden, is_system=is_system, system_usage=system_usage,
                                          proxy=proxy, proxy_user=proxy_username, proxy_password=proxy_password,
                                          logger_handle_log_level=logger_handle_log_level,
                                          bypass_connection_checks=bypass_connection_checks,
                                          bypass_version_checks=bypass_version_checks,
                                          user_label=user_label)
        elif device_type == "ucsc":
            device = UcsCentral(parent=self, uuid=uuid, target=target, user=username, password=password,
                                is_hidden=is_hidden, is_system=is_system, system_usage=system_usage,
                                logger_handle_log_level=logger_handle_log_level,
                                bypass_connection_checks=bypass_connection_checks,
                                bypass_version_checks=bypass_version_checks, user_label=user_label)
        elif device_type == "ucsm":
            device = UcsSystem(parent=self, uuid=uuid, target=target, user=username, password=password,
                               is_hidden=is_hidden, is_system=is_system, system_usage=system_usage,
                               logger_handle_log_level=logger_handle_log_level,
                               bypass_connection_checks=bypass_connection_checks,
                               bypass_version_checks=bypass_version_checks, user_label=user_label)
        else:
            self.logger(level="error", message="Device type not recognized. Could not add device")
            return False

        if isinstance(metadata, DeviceMetadata):
            # We use the provided metadata as the newly added device metadata.
            device.metadata = metadata
        else:
            device.metadata.use_proxy = use_proxy
            device.metadata.easyucs_version = __version__
            device.load_from = "add"
        self.logger(level="debug", message="Adding device of type '" + device_type + "' with UUID " + str(device.uuid) +
                                           " to the list of devices")
        for loaded_device in self.device_list:
            if str(device.uuid) == str(loaded_device.uuid):
                self.logger(level="error", message="Device of type " + device_type + "' with UUID " + str(device.uuid) +
                                                   " already loaded")
                return device.uuid

        self.device_list.append(device)
        return device.uuid

    def clear_device_list(self):
        """
        Removes all the devices from the device list
        :return: True
        """
        self.device_list.clear()
        return True

    def export_device(self, uuid=None, export_format="json", directory=None, filename=None):
        """
        Exports the specified device in the specified export format to the repository
        :param uuid: The UUID of the device to be saved
        :param export_format: The export format (e.g. "json")
        :param directory: The directory containing the export file
        :param filename: The name of the file containing the exported content
        :return: True if export is successful, False otherwise
        """
        if export_format not in ["json"]:
            return False
        if filename is None:
            self.logger(level="error", message="Missing filename in device export request!")
            return False
        if not directory:
            self.logger(level="debug",
                        message="No directory specified in device export request. Using local folder.")
            directory = "."

        if uuid is None:
            self.logger(level="debug", message="No device UUID specified in device export request. Using latest.")
            device = self.get_latest_device()
        else:
            # Find the device that needs to be exported
            device = self.find_device_by_uuid(uuid=uuid)
            if not device:
                self.logger(level="error", message="Failed to locate device with UUID " + str(uuid) + " for export")
                return False

        if device is None:
            # We could not find any device
            self.logger(level="error", message="Could not find any device to export!")
            return False

        self.logger(level="debug", message="Using device " + str(device.uuid) + " for export")

        if export_format == "json":
            header_json = {"metadata": [export.generate_json_metadata_header(file_type="device", device=device)]}
            device_json = {"easyucs": header_json, "device": {}}

            device_json["device"]["target"] = device.target

            if device.metadata.device_type in ["intersight"]:
                device_json["device"]["key_id"] = device.key_id
                device_json["device"]["private_key_path"] = device.private_key_path
            else:
                device_json["device"]["username"] = device.username
                device_json["device"]["password"] = device.password

            # Calculate hash of entire JSON file and adding it to header before exporting
            device_json = export.insert_json_metadata_hash(json_content=device_json)
            if not device_json:
                self.logger(level="error", message="Unable to calculate MD5 hash of device file!")
                return False

            # Saving md5 hash to the InventoryMetadata object
            device.metadata.hash = device_json["easyucs"]["metadata"][0]["hash"]

            self.logger(message="Exporting device " + str(device.uuid) + " to file: " + directory + "/" + filename)
            if not os.path.exists(directory):
                self.logger(message="Creating directory " + directory)
                os.makedirs(directory)
            with open(directory + '/' + filename, 'w') as device_json_file:
                json.dump(device_json, device_json_file, indent=3)
            device_json_file.close()
            return True

    def find_device_by_uuid(self, uuid=None):
        """
        Finds a device from the device list given a specific UUID
        :param uuid: UUID of the device to find
        :return: device if found, None otherwise
        """
        if uuid is None:
            self.logger(level="error", message="No device UUID specified in find device request.")
            return None

        device_list = [device for device in self.device_list if str(device.uuid) == str(uuid)]
        if len(device_list) != 1:
            self.logger(level="debug", message="Failed to locate device with UUID " + str(uuid) +
                                               " - Found " + str(len(device_list)) + " devices")
            return None
        else:
            return device_list[0]

    def get_latest_device(self):
        """
        Returns the most recent device from the device list
        :return: GenericDevice (or subclass), None if no device is found
        """
        if len(self.device_list) == 0:
            return None
        # return sorted(self.device_list, key=lambda device: device.metadata.timestamp)[-1]
        return self.device_list[-1]

    def import_device(self, import_format="json", directory=None, filename=None, device=None, metadata=None,
                      force_custom=None):
        """
        Imports the specified device in the specified import format from the specified filename to device_list
        :param import_format: The import format (e.g. "json")
        :param directory: The directory containing the import file
        :param filename: The name of the file containing the content to be imported
        :param device: The device content to be imported (if no directory/filename provided)
        :param metadata: The metadata object of to the device to be imported (if no device or dir/file provided)
        :param force_custom: If set, then overwrite the value of 'is_custom' flag with whatever is set here. Has to
        be used in situations where a custom device (device which is edited), needs to pretend as a non-custom
        device (non-edited device).
        :return: Device object if import is successful, False otherwise
        """
        if import_format not in ["json"]:
            self.logger(level="error", message="Requested device import format not supported!")
            return False

        # If no device content is provided, we need to open the file using directory and filename arguments
        if device is None:
            if metadata is None:
                if filename is None:
                    self.logger(level="error", message="Missing filename in device import request!")
                    return False
                if directory is None:
                    self.logger(level="debug",
                                message="No directory specified in device import request. Using local folder.")
                    directory = "."
            else:
                if metadata.file_path is None:
                    self.logger(level="error", message="Missing metadata file path in device import request!")
                    return False
                else:
                    directory = os.path.dirname(metadata.file_path)
                    filename = os.path.basename(metadata.file_path)

            # Making sure device file exists
            if not os.path.exists(directory + '/' + filename):
                self.logger(level="error",
                            message="Requested device file: " + directory + "/" + filename + " does not exist!")
                return False

            if import_format == "json":
                self.logger(level="debug", message="Requested device import format is JSON")
                with open(directory + '/' + filename, 'r') as device_json_file:
                    try:
                        complete_json = json.load(device_json_file)
                    except json.decoder.JSONDecodeError as err:
                        self.logger(level="error",
                                    message="Invalid device JSON file " + directory + "/" + filename + ": " + str(err))
                        return False
                device_json_file.close()

        else:
            if import_format == "json":
                self.logger(level="debug", message="Requested device import format is JSON")
                if isinstance(device, str):
                    complete_json = json.loads(device)
                elif isinstance(device, dict):
                    complete_json = device
                else:
                    self.logger(level="error", message="Unable to import device")
                    return False

        if import_format in ["json"]:
            # We verify that the JSON content is valid
            if not self._validate_device_from_json(device_json=complete_json):
                self.logger(message="Can't import invalid device JSON file")
                return False
            else:
                self.logger(message="Successfully validated device JSON file")

            # We verify the hash of the file to check if it has been modified
            custom = False
            if not export.verify_json_metadata_hash(json_content=complete_json):
                self.logger(message="Hash of the imported file does not verify. Device will be marked as custom")
                custom = True

            # We calculate md5 hash of entire imported JSON file and add it to header
            complete_json = export.insert_json_metadata_hash(json_content=complete_json)
            if not complete_json:
                self.logger(level="debug", message="Unable to calculate MD5 hash of imported device file!")
                return False

            # We now compare the hash of the file to the hash of the metadata object if we have it
            if not custom and metadata is not None:
                if "metadata" in complete_json["easyucs"]:
                    if "hash" in complete_json["easyucs"]["metadata"][0]:
                        if metadata.hash is not None:
                            if metadata.hash != complete_json["easyucs"]["metadata"][0]["hash"]:
                                self.logger(level="debug", message="Hash of the imported file does not match " +
                                                                   "metadata hash. Device will be marked as custom")
                                custom = True

            # We make sure there is a "device" section in the file
            if "device" in complete_json:
                device_json = complete_json["device"]
            else:
                self.logger(level="error", message="No device section in JSON file. Could not import device")
                return False

            # We fetch the device type
            if "device_type" not in complete_json["easyucs"]["metadata"][0]:
                self.logger(level="error", message="Device type not specified in JSON file. Could not import device")
                return False

            device_type = complete_json["easyucs"]["metadata"][0]["device_type"]
            if device_type not in ["cimc", "intersight", "ucsc", "ucsm"]:
                self.logger(level="error", message="Device type not recognized. Could not import device")
                return False

            # We create a new device object
            try:
                if device_type == "cimc":
                    device = UcsImc(target=device_json["target"], user=device_json["username"],
                                    password=device_json["password"])
                elif device_type == "intersight":
                    device = IntersightDevice(target=device_json["target"], key_id=device_json["key_id"],
                                              private_key_path=device_json["private_key_path"])
                elif device_type == "ucsc":
                    device = UcsCentral(target=device_json["target"], user=device_json["username"],
                                        password=device_json["password"])
                elif device_type == "ucsm":
                    device = UcsSystem(target=device_json["target"], user=device_json["username"],
                                       password=device_json["password"])
                else:
                    return False

                device.load_from = "file"
                device.metadata.easyucs_version = __version__

                # We save md5 hash to the DeviceMetadata object
                device.metadata.hash = complete_json["easyucs"]["metadata"][0]["hash"]

                # We set the origin of the device as "file"
                device.metadata.origin = "file"

                # We set the custom flag of the device
                if custom:
                    device.metadata.is_custom = True

                    # Override the 'is_custom' flag of the device if it's a custom file (edited by user) and the user
                    # explicitly sets it to pretend to be non-custom (not edited by user).
                    if force_custom is not None:
                        device.metadata.is_custom = force_custom

                # We use the provided metadata for the new device object if the hash of the file is valid
                if not custom and metadata is not None:
                    self.logger(level="debug", message="Using provided metadata for device import")
                    device.metadata = metadata
                    device.metadata.parent = device
                    device.uuid = metadata.uuid

                self.logger(message="Device import successful. Appending device to the list of devices")
                # We add the device to the list of devices
                self.device_list.append(device)
                return device

            except Exception:
                self.logger(level="error", message="Device import failed!")
                return False

    def remove_device(self, uuid=None):
        """
        Removes the specified device from the device list
        :param uuid: The UUID of the device to be deleted
        :return: True if delete is successful, False otherwise
        """
        if uuid is None:
            self.logger(level="error", message="No device UUID specified in remove device request.")
            return False

        # Find the device that needs to be removed
        device = self.find_device_by_uuid(uuid=uuid)
        if not device:
            return False
        else:
            device_to_remove = device

        # If device has sub-devices, they should be removed as well
        if device_to_remove.sub_devices:
            for sub_device in device_to_remove.sub_devices:
                if sub_device in self.device_list:
                    self.device_list.remove(sub_device)

        # Remove the device from the list of devices
        self.device_list.remove(device_to_remove)

        return True

    def _validate_device_from_json(self, device_json=None):
        # TODO: Verify that the JSON content is valid using jsonschema
        return True
