# coding: utf-8
# !/usr/bin/env python

""" manager.py: Easy UCS Deployment Tool """

import json
import os

import export
from __init__ import __version__


class GenericInventoryManager:
    def __init__(self, parent=None):
        self.inventory_class_name = None
        self.inventory_list = []
        self.parent = parent

        self._parent_having_logger = self._find_logger()

    def clear_inventory_list(self):
        """
        Removes all the inventories from the inventory list
        :return: True
        """
        self.inventory_list.clear()
        return True

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
            print("WARNING: No logger found in Inventory Manager")
            return None

    def draw_inventory(self, uuid=None):
        pass

    def export_draw(self, uuid=None, export_format="png", directory=None, export_clear_pictures=False):
        pass

    def export_inventory(self, uuid=None, export_format="json", directory=None, filename=None):
        """
        Exports the specified inventory in the specified export format to the specified filename
        :param uuid: The UUID of the inventory to be exported. If not specified, the most recent inventory will be used
        :param export_format: The export format (e.g. "json")
        :param directory: The directory containing the export file
        :param filename: The name of the file containing the exported content
        :return: True if export is successful, False otherwise
        """
        if export_format not in ["json"]:
            self.logger(level="error", message="Requested inventory export format not supported!")
            return False
        if filename is None:
            self.logger(level="error", message="Missing filename in inventory export request!")
            return False
        if not directory:
            self.logger(level="debug",
                        message="No directory specified in inventory export request. Using local folder.")
            directory = "."

        if uuid is None:
            self.logger(level="debug", message="No inventory UUID specified in inventory export request. Using latest.")
            inventory = self.get_latest_inventory()
        else:
            # Find the inventory that needs to be exported
            inventory_list = [inventory for inventory in self.inventory_list if inventory.uuid == uuid]
            if len(inventory_list) != 1:
                self.logger(level="error", message="Failed to locate inventory with UUID " + str(uuid) + " for export")
                return False
            else:
                inventory = inventory_list[0]

        if inventory is None:
            # We could not find any inventory
            self.logger(level="error", message="Could not find any inventory to export!")
            return False
        if inventory.export_list is None or len(inventory.export_list) == 0:
            # Nothing to export
            self.logger(level="error", message="Nothing to export on the selected inventory!")
            return False

        self.logger(level="debug", message="Using inventory " + str(inventory.uuid) + " for export")

        if export_format == "json":
            self.logger(level="debug", message="Requested inventory export format is JSON")
            header_json = {
                "metadata": [export.generate_json_metadata_header(file_type="inventory", inventory=inventory)]}
            inventory_json = {"easyucs": header_json, "inventory": {}}
            for export_attribute in inventory.export_list:
                # We check if the attribute to be exported is an empty list, in which case, we don't export it
                if isinstance(getattr(inventory, export_attribute), list):
                    if len(getattr(inventory, export_attribute)) == 0:
                        continue
                inventory_json["inventory"][export_attribute] = []
                if isinstance(getattr(inventory, export_attribute), list):
                    count = 0
                    for inventory_object in getattr(inventory, export_attribute):
                        inventory_json["inventory"][export_attribute].append({})
                        export.export_attributes_json(inventory_object,
                                                      inventory_json["inventory"][export_attribute][count])
                        count += 1
                else:
                    inventory_object = getattr(inventory, export_attribute)
                    inventory_json["inventory"][export_attribute].append({})
                    export.export_attributes_json(inventory_object, inventory_json["inventory"][export_attribute][0])

            # Calculate md5 hash of entire JSON file and adding it to header before exporting
            inventory_json = export.insert_json_metadata_hash(json_content=inventory_json)
            if not inventory_json:
                self.logger(level="error", message="Unable to calculate MD5 hash of inventory file!")
                return False

            # Saving md5 hash to the InventoryMetadata object
            inventory.metadata.hash = inventory_json["easyucs"]["metadata"][0]["hash"]

            self.logger(
                message="Exporting inventory " + str(inventory.uuid) + " to file: " + directory + "/" + filename)
            if not os.path.exists(directory):
                self.logger(message="Creating directory " + directory)
                os.makedirs(directory)
            with open(directory + '/' + filename, 'w') as inventory_json_file:
                json.dump(inventory_json, inventory_json_file, indent=3)
            inventory_json_file.close()
            return True

    def import_inventory(self, import_format="json", directory=None, filename=None, inventory=None, metadata=None):
        """
        Imports the specified inventory in the specified import format from the specified filename to inventory_list
        :param import_format: The import format (e.g. "json")
        :param directory: The directory containing the import file
        :param filename: The name of the file containing the content to be imported
        :param inventory: The inventory content to be imported (if no directory/filename provided)
        :param metadata: The metadata object of to the inventory to be imported (if no inventory or dir/file provided)
        :return: Inventory object if import is successful, False otherwise
        """
        if import_format not in ["json"]:
            self.logger(level="error", message="Requested inventory import format not supported!")
            return False

        # If no inventory content is provided, we need to open the file using directory and filename arguments
        if inventory is None:
            if metadata is None:
                if filename is None:
                    self.logger(level="error", message="Missing filename in inventory import request!")
                    return False
                if directory is None:
                    self.logger(level="debug",
                                message="No directory specified in inventory import request. Using local folder.")
                    directory = "."
            else:
                if metadata.file_path is None:
                    self.logger(level="error", message="Missing metadata file path in inventory import request!")
                    return False
                else:
                    directory = os.path.dirname(metadata.file_path)
                    filename = os.path.basename(metadata.file_path)

            # Making sure inventory file exists
            if not os.path.exists(directory + '/' + filename):
                self.logger(level="error",
                            message="Requested inventory file: " + directory + "/" + filename + " does not exist!")
                return False

            if import_format == "json":
                self.logger(level="debug", message="Requested inventory import format is JSON")
                with open(directory + '/' + filename, 'r') as inventory_json_file:
                    try:
                        complete_json = json.load(inventory_json_file)
                    except json.decoder.JSONDecodeError as err:
                        self.logger(level="error", message="Invalid inventory JSON file " + directory + "/" +
                                                           filename + ": " + str(err))
                        return False
                inventory_json_file.close()

        else:
            if import_format == "json":
                self.logger(level="debug", message="Requested inventory import format is JSON")
                try:
                    complete_json = json.loads(inventory)
                except json.decoder.JSONDecodeError as err:
                    self.logger(level="error", message="Error while importing inventory: " + str(err))
                    return False

        if import_format in ["json"]:
            # # We verify that the JSON content is valid
            # inventory_valid = self._validate_inventory_from_json(inventory_json=complete_json)
            # if inventory_valid:
            #     self.logger(message="Successfully validated inventory JSON file")

            # We verify the hash of the file to check if it has been modified
            custom = False
            if not export.verify_json_metadata_hash(json_content=complete_json):
                self.logger(message="Hash of the imported file does not verify. inventory will be marked as custom")
                custom = True

            # We calculate md5 hash of entire imported JSON file and add it to header
            complete_json = export.insert_json_metadata_hash(json_content=complete_json)
            if not complete_json:
                self.logger(level="debug", message="Unable to calculate MD5 hash of imported inventory file!")
                return False

            # We now compare the hash of the file to the hash of the metadata object if we have it
            if not custom and metadata is not None:
                if "metadata" in complete_json["easyucs"]:
                    if "hash" in complete_json["easyucs"]["metadata"][0]:
                        if metadata.hash is not None:
                            if metadata.hash != complete_json["easyucs"]["metadata"][0]["hash"]:
                                self.logger(level="debug", message="Hash of the imported file does not match " +
                                                                   "metadata hash. Inventory will be marked as custom")
                                custom = True

            # We make sure there is an "inventory" section in the file
            if "inventory" in complete_json:
                inventory_json = complete_json["inventory"]
            else:
                self.logger(level="error", message="No inventory section in JSON file. Could not import inventory")
                return False

            # We create a new inventory object
            inventory = self.inventory_class_name(parent=self)

            # We use the provided metadata for the new inventory object if the hash of the file is valid
            if not custom and metadata is not None:
                self.logger(level="debug", message="Using provided metadata for inventory import")
                inventory.metadata = metadata
                inventory.metadata.parent = inventory
                inventory.uuid = metadata.uuid

            inventory.load_from = "file"
            inventory.metadata.easyucs_version = __version__

            # We save md5 hash to the InventoryMetadata object
            inventory.metadata.hash = complete_json["easyucs"]["metadata"][0]["hash"]

            # We set the origin of the inventory as "file"
            inventory.metadata.origin = "file"

            # We set the custom flag of the inventory
            if custom:
                inventory.custom = True

            # We fetch all options set in "easyucs" section of the file
            if "easyucs" in complete_json:
                if "options" in complete_json["easyucs"]:
                    self.logger(level="debug", message="Importing options from inventory file")
                    for option in complete_json["easyucs"]["options"]:
                        inventory.options.update(option)
                if (custom or metadata is None) and "metadata" in complete_json["easyucs"]:
                    # We use some values from the file (but not all - e.g. we do not trust UUID)
                    if "intersight_status" in complete_json["easyucs"]["metadata"][0]:
                        inventory.intersight_status = complete_json["easyucs"]["metadata"][0]["intersight_status"]

                    if "device_name" in complete_json["easyucs"]["metadata"][0]:
                        inventory.metadata.device_name = complete_json["easyucs"]["metadata"][0]["device_name"]
                    if "device_version" in complete_json["easyucs"]["metadata"][0]:
                        inventory.metadata.device_version = complete_json["easyucs"]["metadata"][0]["device_version"]

            # We start filling up the inventory
            self.logger(message="Importing inventory from " + import_format)
            result = self._fill_inventory_from_json(inventory=inventory, inventory_json=inventory_json)
            if result:
                self.logger(message="Inventory import successful. Appending inventory " + str(inventory.uuid) +
                                    " to the list of inventories for device " + str(self.parent.uuid))
                # We add the inventory to the list of inventories
                self.inventory_list.append(inventory)
                return inventory
            else:
                self.logger(level="error", message="Inventory import failed!")
                return False

    def fetch_inventory(self, force=False):
        return None

    def get_latest_inventory(self):
        """
        Returns the most recent inventory from the inventory list
        :return: GenericInventory (or subclass), None if no inventory is found
        """
        if len(self.inventory_list) == 0:
            return None
        # return sorted(self.inventory_list, key=lambda inventory: inventory.metadata.timestamp)[-1]
        return self.inventory_list[-1]

    def _fill_inventory_from_json(self, inventory=None, inventory_json=None):
        """
        Fills inventory using parsed JSON inventory file
        :param inventory: inventory to be filled
        :param inventory_json: parsed JSON content containing inventory
        :return: True if successful, False otherwise
        """
        return False
    
    def find_inventory_by_uuid(self, uuid=None):
        """
        Finds an inventory from the inventory list given a specific UUID
        :param uuid: UUID of the inventory to find
        :return: inventory if found, None otherwise
        """
        if uuid is None:
            self.logger(level="error", message="No inventory UUID specified in find inventory request.")
            return None

        inventory_list = [inventory for inventory in self.inventory_list if str(inventory.uuid) == str(uuid)]
        if len(inventory_list) != 1:
            self.logger(level="debug", message="Failed to locate inventory with UUID " + str(uuid))
            return None
        else:
            return inventory_list[0]
    
    def remove_inventory(self, uuid=None):
        """
        Removes the specified inventory from the inventory list
        :param uuid: The UUID of the inventory to be deleted
        :return: True if delete is successful, False otherwise
        """
        if uuid is None:
            self.logger(level="error", message="No inventory UUID specified in remove inventory request.")
            return False

        # Find the inventory that needs to be removed
        inventory = self.find_inventory_by_uuid(uuid=uuid)
        if not inventory:
            return False
        else:
            inventory_to_remove = inventory

        # Remove the inventory from the list of inventories
        self.inventory_list.remove(inventory_to_remove)

        # Delete the inventory in the repository
        # directory = "repository/" + str(self.parent.uuid) + "/inventories/inventory-" + str(uuid) + ".json"
        #
        # if os.path.exists(directory):
        #     os.remove(directory)
        # else:
        #     print("inventory not found in repository. Nothing to delete.")
        #     return False

        return True
