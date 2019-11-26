# coding: utf-8
# !/usr/bin/env python

""" manager.py: Easy UCS Deployment Tool """
from easyucs import __author__, __copyright__,  __version__, __status__


import json
import os
import shutil
import uuid

from easyucs.device.device import GenericDevice, UcsSystem, UcsImc, UcsCentral

from easyucs import export


class DeviceManager:
    REPOSITORY_FOLDER_NAME = "repository"

    def __init__(self):
        self.device_list = []

    def add_device(self, device_type=None, target=None, username=None, password=None):
        """
        Adds a device to the list of devices
        :param device_type: The type of device to be added (e.g. "ucsm")
        :param target: The IP address/hostname of the device
        :param username: The username/login of the device
        :param password: The password of the device
        :return: True if add is successful, False otherwise
        """
        if device_type is None:
            # TODO: Change to make it optional
            print("Missing device_type in device add request!")
            return False

        if target is None or username is None or password is None:
            print("Missing target, username or password in device add request!")
            return False

        if device_type not in ["ucsm", "cimc"]:
            print("Device type not recognized. Could not import device")
            return False

        # We create a new device object
        device = GenericDevice(target=target, user=username, password=password)

        if device_type == "ucsm":
            device = UcsSystem(target=target, user=username, password=password)
        elif device_type == "cimc":
            device = UcsImc(target=target, user=username, password=password)
        elif device_type == "ucsc":
            device = UcsCentral(target=target, user=username, password=password)

        device.load_from = "add"

        self.device_list.append(device)
        return True

    def load_device(self, import_format="json", directory=None, filename=None):
        """
        Loads the specified device in the specified import format from the specified filename to the list of devices
        :param import_format: The import format (e.g. "json")
        :param directory: The directory containing the import file
        :param filename: The name of the file containing the content to be imported
        :return: True if load is successful, False otherwise
        """
        if import_format not in ["json"]:
            print("Requested device import format not supported!")
            return False
        if filename is None:
            print("Missing filename in device import request!")
            return False
        if directory is None:
            print("No directory specified in device import request. Using local folder.")
            directory = "."

        if import_format == "json":
            try:
                with open(directory + '/' + filename, 'r') as config_json_file:
                    complete_json = json.load(config_json_file)
                config_json_file.close()
            except FileNotFoundError as err:
                print("File not found: " + str(err))
                return False

            # We verify that the JSON content is valid
            device_valid = self._validate_device_from_json(device_json=complete_json)
            if device_valid:
                print("Successfully validated device JSON file: " + directory + "/" + filename)

            # We verify the hash of the file to check if it has been modified
            custom = False
            if not export.verify_json_metadata_hash(json_content=complete_json):
                print("Hash of the imported file does not verify. Device will be marked as custom")
                custom = True

            # We make sure there is a "device" section in the file
            if "device" in complete_json:
                device_json = complete_json["device"]
            else:
                print("No device section in JSON file. Could not import device")
                return False

            # We fetch the device type
            if "device_type" not in complete_json["easyucs"]["metadata"][0]:
                print("Device type not specified in JSON file. Could not import device")
                return False

            device_type = complete_json["easyucs"]["metadata"][0]["device_type"]
            if device_type not in ["ucsm", "cimc"]:
                print("Device type not recognized. Could not import device")
                return False

            # We fetch the device UUID
            if "device_uuid" not in complete_json["easyucs"]["metadata"][0]:
                print("Device UUID not specified in JSON file. Could not import device")
                return False

            device_uuid = uuid.UUID(complete_json["easyucs"]["metadata"][0]["device_uuid"])

            # We first need to make sure that the device has not already been loaded
            device_list = [device for device in self.device_list if device.uuid == device_uuid]
            if len(device_list) >= 1:
                print("Device with UUID " + str(device_uuid) + " is already loaded!")
                return False

            # We create a new device object
            try:
                if device_type == "ucsm":
                    device = UcsSystem(target=device_json["target"], user=device_json["username"],
                                       password=device_json["password"])
                elif device_type == "cimc":
                    device = UcsImc(target=device_json["target"], user=device_json["username"],
                                    password=device_json["password"])
                elif device_type == "ucsc":
                    device = UcsCentral(target=device_json["target"], user=device_json["username"],
                                        password=device_json["password"])
                else:
                    return False

                device.load_from = "file"

                # We set the UUID of the device from the JSON file
                device.uuid = device_uuid

                # We set the custom flag of the device
                if custom:
                    device.custom = True

                print("Device import successful. Appending device to the list of devices")
                # We add the device to the list of devices
                self.device_list.append(device)
                return True

            except Exception:
                print("Device import failed!")
                return False

    def remove_device(self, uuid):
        """
        Removes the specified device from the repository
        :param uuid: The UUID of the device to be deleted
        :return: True if delete is successful, False otherwise
        """

        # Find the device that needs to be removed
        device = self.find_device_by_uuid(device_uuid=uuid)
        if not device:
            return False
        else:
            device_to_remove = device

        # Remove the device from the list of devices
        self.device_list.remove(device_to_remove)

        # Delete the directory for the device in the repository
        directory = self.REPOSITORY_FOLDER_NAME + "/" + str(uuid)

        if os.path.exists(directory):
            shutil.rmtree(directory)
        else:
            print("Device not found in repository. Nothing to delete.")
            return False

        return True

    def save_device(self, uuid=None, export_format="json"):
        """
        Saves the specified device in the specified export format to the repository
        :param uuid: The UUID of the device to be saved
        :param export_format: The export format (e.g. "json")
        :return: True if save is successful, False otherwise
        """
        if export_format not in ["json"]:
            return False
        if uuid is None:
            return False

        # Find the device that needs to be exported
        device = self.find_device_by_uuid(device_uuid=uuid)
        if not device:
            print("Failed to locate device with UUID " + str(uuid) + " for export")
            return False

        directory = self.REPOSITORY_FOLDER_NAME + "/" + str(uuid)
        filename = "device-" + str(uuid) + "." + export_format

        # Creating folder for device
        if not os.path.exists(directory):
            os.makedirs(directory)

        if export_format == "json":
            header_json = {}
            header_json["metadata"] = [export.generate_json_metadata_header(file_type="device", device=device)]
            device_json = {}
            device_json["easyucs"] = header_json
            device_json["device"] = {}

            device_json["device"]["target"] = device.target
            device_json["device"]["username"] = device.username
            device_json["device"]["password"] = device.password

            # Calculate hash of entire JSON file and adding it to header before exporting
            device_json = export.insert_json_metadata_hash(json_content=device_json)

            print("Exporting device " + str(device.uuid) + " to file: " + directory + "/" + filename)
            with open(directory + '/' + filename, 'w') as device_json_file:
                json.dump(device_json, device_json_file, indent=3)
            device_json_file.close()
            return True

    def save_device_configs(self, device_uuid=None, export_format="json"):
        """
        Saves all configs of a given device in the specified export format to the repository
        :param device_uuid: The UUID of the device containing the configs to be saved
        :param export_format: The export format (e.g. "json")
        :return: True if save is successful, False otherwise
        """
        if export_format not in ["json"]:
            return False
        if device_uuid is None:
            return False

        # Find the device that needs to be exported
        device_list = [device for device in self.device_list if device.uuid == device_uuid]
        if len(device_list) != 1:
            print("Failed to locate device with UUID " + str(device_uuid) + " for export")
            return False
        else:
            device = device_list[0]

        directory = self.REPOSITORY_FOLDER_NAME + "/" + str(device_uuid) + "/configs"

        # Creating folder for configs
        if not os.path.exists(directory):
            os.makedirs(directory)

        for config in device.config_manager.config_list:
            filename = "config-" + str(config.uuid) + ".json"
            device.config_manager.export_config(directory=directory, filename=filename)

        return True

    def scan_repository(self):
        """
        Scans the repository for devices, configs and inventories and loads them
        :return: True if successful, False otherwise
        """
        directory = self.REPOSITORY_FOLDER_NAME

        # We make sure the repository folder exists - otherwise we create it
        if not os.path.exists(directory):
            os.makedirs(directory)

        folder_list = [name for name in os.listdir(directory) if os.path.isdir(directory + "/" + name)]

        if len(folder_list) == 0:
            print("Nothing in the repository!")

        for folder in folder_list:
            if os.path.exists(directory + "/" + folder + "/device-" + folder + ".json"):
                # We first need to make sure that the device has not already been loaded
                device_list = [device for device in self.device_list if device.uuid == uuid.UUID(folder)]
                if len(device_list) >= 1:
                    print("Device with UUID " + folder + " is already loaded!")
                    continue
                if not self.load_device(import_format="json", directory=directory + "/" + folder,
                                        filename="device-" + folder + ".json"):
                    print("Failed to load device with UUID " + folder)
                    continue

                # We fetch the corresponding device
                device_list = [device for device in self.device_list if device.uuid == uuid.UUID(folder)]
                if len(device_list) != 1:
                    print("Failed to locate device with UUID " + folder)
                    continue
                else:
                    device = device_list[0]

                # We now need to load configs and inventories for that device
                configs_folder = directory + "/" + folder + "/configs"
                if os.path.exists(configs_folder):
                    config_file_list = [name for name in os.listdir(configs_folder) if
                                        os.path.isfile(configs_folder + "/" + name) and
                                        os.path.splitext(configs_folder + "/" + name)[1] == ".json"]
                    for config_file in config_file_list:
                        config_file_uuid = os.path.splitext(config_file)[0][7:]
                        # We first need to make sure that the config has not already been loaded
                        config_list = [config for config in device.config_manager.config_list
                                       if config.uuid == uuid.UUID(config_file_uuid)]
                        if len(config_list) >= 1:
                            print("Config with UUID " + config_file_uuid + " is already loaded!")
                            continue
                        print("Importing config with UUID " + config_file_uuid)
                        device.config_manager.import_config(import_format="json", directory=configs_folder,
                                                            filename=config_file)
                        # Keep the uuid of the config file because the import from file creates a new config
                        # with a new uuid
                        device.config_manager.config_list[-1].uuid = uuid.UUID(config_file_uuid)

                inventories_folder = directory + "/" + folder + "/inventories"
                if os.path.exists(inventories_folder):
                    inventory_file_list = [name for name in os.listdir(inventories_folder) if
                                           os.path.isfile(inventories_folder + "/" + name) and
                                           os.path.splitext(inventories_folder + "/" + name)[1] == ".json"]
                    for inventory_file in inventory_file_list:
                        inventory_file_uuid = os.path.splitext(inventory_file)[0][7:]
                        # We first need to make sure that the inventory has not already been loaded
                        inventory_list = [inventory for inventory in device.inventory_manager.inventory_list
                                          if inventory.uuid == uuid.UUID(inventory_file_uuid)]
                        if len(inventory_list) >= 1:
                            print("Inventory with UUID " + inventory_file_uuid + " is already loaded!")
                            continue
                        print("Importing inventory with UUID " + inventory_file_uuid)
                        device.inventory_manager.import_inventory(import_format="json", directory=inventories_folder,
                                                                  filename=inventory_file)

            else:
                print("Folder " + folder + " does not contain a device .json file!")

        return True

    def _validate_device_from_json(self, device_json=None):
        # TODO: Verify that the JSON content is valid using jsonschema
        return True

    def find_device_by_uuid(self, device_uuid):
        """
        Finds a device given a specific UUID

        :param device_uuid: UUID of the device to find
        :return: device if found, None otherwise
        """
        device_list = [device for device in self.device_list if str(device.uuid) == str(device_uuid)]
        if len(device_list) != 1:
            print("Failed to locate device with UUID " + str(device_uuid))
            return None
        else:
            return device_list[0]
