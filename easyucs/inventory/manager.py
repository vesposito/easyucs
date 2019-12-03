# coding: utf-8
# !/usr/bin/env python

""" manager.py: Easy UCS Deployment Tool """
from easyucs import __author__, __copyright__,  __version__, __status__


import json
import os
import re
import uuid

from easyucs.inventory.inventory import UcsImcInventory, UcsSystemInventory, UcsCentralInventory
from easyucs.inventory.ucs.chassis import UcsImcChassis, UcsSystemChassis
from easyucs.inventory.ucs.domain import UcsCentralDomain
from easyucs.inventory.ucs.fabric import UcsSystemFex, UcsSystemFi
from easyucs.inventory.ucs.rack import UcsImcRack, UcsImcRackEnclosure, UcsSystemRack, UcsSystemRackEnclosure
from easyucs.draw.ucs.neighbor import UcsSystemDrawInfraNeighborsLan, UcsSystemDrawInfraNeighborsSan
from easyucs.draw.ucs.chassis import UcsSystemDrawInfraChassis
from easyucs.draw.ucs.rack import UcsSystemDrawInfraRack, UcsSystemDrawInfraRackEnclosure
from easyucs.draw.ucs.service_profile import UcsSystemDrawInfraServiceProfile
from easyucs import export


class GenericInventoryManager:
    def __init__(self, parent=None):
        self.inventory_class_name = None
        self.inventory_list = []
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
            header_json = {}
            header_json["metadata"] = [export.generate_json_metadata_header(file_type="inventory", inventory=inventory)]
            inventory_json = {}
            inventory_json["easyucs"] = header_json
            inventory_json["inventory"] = {}
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

            self.logger(
                message="Exporting inventory " + str(inventory.uuid) + " to file: " + directory + "/" + filename)
            if not os.path.exists(directory):
                self.logger(message="Creating directory " + directory)
                os.makedirs(directory)
            with open(directory + '/' + filename, 'w') as inventory_json_file:
                json.dump(inventory_json, inventory_json_file, indent=3)
            inventory_json_file.close()
            return True

    def import_inventory(self, import_format="json", directory=None, filename=None, inventory=None):
        """
        Imports the specified inventory in the specified import format from the specified filename
        :param import_format: The import format (e.g. "json")
        :param directory: The directory containing the import file
        :param filename: The name of the file containing the content to be imported
        :param inventory: The inventory content to be imported (if no directory/filename provided)
        :return: True if import is successful, False otherwise
        """
        if import_format not in ["json"]:
            self.logger(level="error", message="Requested inventory import format not supported!")
            return False

        # If no inventory content is provided, we need to open the file using directory and filename arguments
        if inventory is None:
            if filename is None:
                self.logger(level="error", message="Missing filename in inventory import request!")
                return False
            if directory is None:
                self.logger(level="debug",
                            message="No directory specified in inventory import request. Using local folder.")
                directory = "."

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
                complete_json = json.loads(inventory)

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

            # We make sure there is a "inventory" section in the file
            if "inventory" in complete_json:
                inventory_json = complete_json["inventory"]
            else:
                self.logger(level="error", message="No inventory section in JSON file. Could not import inventory")
                return False

            # We create a new inventory object
            inventory = self.inventory_class_name(parent=self)
            inventory.load_from = "file"

            # We set the origin of the inventory as "import"
            inventory.origin = "import"

            # We set the custom flag of the inventory
            if custom:
                inventory.custom = True

            # We fetch all options set in "easyucs" section of the file
            if "easyucs" in complete_json:
                if "options" in complete_json["easyucs"]:
                    self.logger(level="debug", message="Importing options from inventory file")
                    for option in complete_json["easyucs"]["options"]:
                        inventory.options.update(option)
                if "metadata" in complete_json["easyucs"]:
                    if "uuid" in complete_json["easyucs"]["metadata"][0]:
                        inventory.uuid = uuid.UUID(complete_json["easyucs"]["metadata"][0]["uuid"])
                    if "device_version" in complete_json["easyucs"]["metadata"][0]:
                        inventory.device_version = complete_json["easyucs"]["metadata"][0]["device_version"]
                    if "intersight_status" in complete_json["easyucs"]["metadata"][0]:
                        inventory.intersight_status = complete_json["easyucs"]["metadata"][0]["intersight_status"]

            # We start filling up the inventory
            self.logger(message="Importing inventory from " + import_format)
            result = self._fill_inventory_from_json(inventory=inventory, inventory_json=inventory_json)
            if result:
                self.logger(message="Inventory import successful. Appending inventory to the list of inventories " +
                                    "for device " + str(self.parent.uuid))
                # We add the inventory to the list of inventories
                self.inventory_list.append(inventory)
                return True
            else:
                self.logger(level="error", message="Inventory import failed!")
                return False

    def fetch_inventory(self):
        return None

    def get_latest_inventory(self):
        """
        Returns the most recent inventory from the inventory list
        :return: GenericInventory (or subclass), None if no inventory is found
        """
        if len(self.inventory_list) == 0:
            return None
        return sorted(self.inventory_list, key=lambda inventory: inventory.timestamp)[-1]

    def _fill_inventory_from_json(self, inventory=None, inventory_json=None):
        """
        Fills inventory using parsed JSON inventory file
        :param inventory: inventory to be filled
        :param inventory_json: parsed JSON content containing inventory
        :return: True if successful, False otherwise
        """
        return False
    
    def find_inventory_by_uuid(self, uuid):
        """
        Search a inventory with a specific UUID

        :param uuid:
        :return: inventory if found, None otherwise
        """

        inventory_list = [inventory for inventory in self.inventory_list if str(inventory.uuid) == str(uuid)]
        if len(inventory_list) != 1:
            self.logger(level="error", message="Failed to locate inventory with UUID " + str(uuid))
            return None
        else:
            return inventory_list[0]
    
    def remove_inventory(self, uuid):
        """
        Removes the specified inventory from the repository
        :param uuid: The UUID of the inventory to be deleted
        :return: True if delete is successful, False otherwise
        """

        # Find the inventory that needs to be removed
        inventory = self.find_inventory_by_uuid(uuid=uuid)
        if not inventory:
            return False
        else:
            inventory_to_remove = inventory

        # Remove the inventory from the list of devices
        self.inventory_list.remove(inventory_to_remove)

        # Delete the inventory in the repository
        directory = "repository/" + str(self.parent.uuid) + "/inventories/inventory-" + str(uuid) + ".json"

        if os.path.exists(directory):
            os.remove(directory)
        else:
            print("inventory not found in repository. Nothing to delete.")
            return False

        return True


class GenericUcsInventoryManager(GenericInventoryManager):
    def __init__(self, parent=None):
        GenericInventoryManager.__init__(self, parent=parent)


class UcsSystemInventoryManager(GenericUcsInventoryManager):
    def __init__(self, parent=None):
        GenericUcsInventoryManager.__init__(self, parent=parent)
        self.inventory_class_name = UcsSystemInventory

    def draw_inventory(self, uuid=None):
        """
        Draws UCS chassis, racks, FEXs, FIs and LAN/SAN neighbors using the specified inventory
        :param uuid: The UUID of the inventory to be drawn. If not specified, the most recent inventory will be used
        :return: True if draw is successful, False otherwise
        """
        if uuid is None:
            self.logger(level="debug", message="No inventory UUID specified in inventory draw request. Using latest.")
            inventory = self.get_latest_inventory()
        else:
            # Find the inventory that needs to be exported
            inventory_list = [inventory for inventory in self.inventory_list if inventory.uuid == uuid]
            if len(inventory_list) != 1:
                self.logger(level="error", message="Failed to locate inventory with UUID " + str(uuid) + " for draw")
                return False
            else:
                inventory = inventory_list[0]

        if inventory is None:
            # We could not find any inventory
            self.logger(level="error", message="Could not find any inventory to draw!")
            return False

        chassis_front_draw_list = []
        chassis_rear_draw_list = []
        for chassis in inventory.chassis:
            chassis._generate_draw()
            chassis_front_draw_list.append(chassis._draw_front)
            chassis_rear_draw_list.append(chassis._draw_rear)
        # We only keep the chassis that have been fully created -> json file and picture
        chassis_front_draw_list = [chassis for chassis in chassis_front_draw_list if chassis.picture]
        chassis_rear_draw_list = [chassis for chassis in chassis_rear_draw_list if chassis.picture]

        rack_front_draw_list = []
        rack_rear_draw_list = []
        for rack in inventory.rack_units:
            rack._generate_draw()
            rack_front_draw_list.append(rack._draw_front)
            rack_rear_draw_list.append(rack._draw_rear)
        # We only keep the racks that have been fully created -> json file and picture
        rack_front_draw_list = [rack for rack in rack_front_draw_list if rack.picture]
        rack_rear_draw_list = [rack for rack in rack_rear_draw_list if rack.picture]

        rack_enclosure_front_draw_list = []
        rack_enclosure_rear_draw_list = []
        for rack_enclosure in inventory.rack_enclosures:
            rack_enclosure._generate_draw()
            rack_enclosure_front_draw_list.append(rack_enclosure._draw_front)
            rack_enclosure_rear_draw_list.append(rack_enclosure._draw_rear)
        # We only keep the racks that have been fully created -> json file and picture
        rack_enclosure_front_draw_list = [rack_enclosure for rack_enclosure in rack_enclosure_front_draw_list if rack_enclosure.picture]
        rack_enclosure_rear_draw_list = [rack_enclosure for rack_enclosure in rack_enclosure_rear_draw_list if rack_enclosure.picture]

        fi_rear_draw_list = []
        for fi in inventory.fabric_interconnects:
            fi._generate_draw()
            fi_rear_draw_list.append(fi._draw_rear)
        # We only keep the FI that have been fully created -> json file and picture
        fi_rear_draw_list = [fi for fi in fi_rear_draw_list if fi.picture]

        rotated_fi_draw_list = []
        for fi in fi_rear_draw_list:
            if fi._parent.sku == "UCS-FI-M-6324":
                rotated_fi_draw_list.append(fi.rotate_object(fi))

        fex_rear_draw_list = []
        for fex in inventory.fabric_extenders:
            fex._generate_draw()
            fex_rear_draw_list.append(fex._draw_rear)
        # We only keep the FEX that have been fully created -> json file and picture
        fex_rear_draw_list = [fex for fex in fex_rear_draw_list if fex.picture]

        lan_neighbor_draw_list = []
        san_neighbor_draw_list = []
        for lan_neighbor in inventory.lan_neighbors:
            lan_neighbor._generate_draw()
            lan_neighbor_draw_list.append(lan_neighbor._draw)
        for san_neighbor in inventory.san_neighbors:
            san_neighbor._generate_draw()
            san_neighbor_draw_list.append(san_neighbor._draw)
        if lan_neighbor_draw_list:
            # TODO find a better parent
            inventory._draw_infra_lan_neighbors = \
                UcsSystemDrawInfraNeighborsLan(draw_neighbor_list=lan_neighbor_draw_list,
                                               draw_fi_list=fi_rear_draw_list, parent=fi_rear_draw_list[0]._parent)
        if san_neighbor_draw_list:
            inventory._draw_infra_san_neighbors = \
                UcsSystemDrawInfraNeighborsSan(draw_neighbor_list=san_neighbor_draw_list,
                                               draw_fi_list=fi_rear_draw_list, parent=fi_rear_draw_list[0]._parent)

        # Draw infra Service Profiles
        inventory._draw_infra_chassis_service_profiles = []
        if chassis_front_draw_list or chassis_rear_draw_list:
            if fi_rear_draw_list:
                inventory._draw_infra_chassis_service_profiles.append(
                    UcsSystemDrawInfraServiceProfile(draw_chassis_front_list=chassis_front_draw_list,
                                                     draw_chassis_rear_list=chassis_rear_draw_list,
                                                     parent=fi_rear_draw_list[0]._parent))
        if inventory._draw_infra_chassis_service_profiles:
            infra = inventory._draw_infra_chassis_service_profiles[0]
            while infra.next_page_infra:
                inventory._draw_infra_chassis_service_profiles.append(infra.next_page_infra)
                infra = infra.next_page_infra

        inventory._draw_infra_rack_service_profiles = []
        if rack_front_draw_list:
            if fi_rear_draw_list:
                inventory._draw_infra_rack_service_profiles.append(
                    UcsSystemDrawInfraServiceProfile(draw_rack_list=rack_front_draw_list,
                                                     parent=fi_rear_draw_list[0]._parent))
        if inventory._draw_infra_rack_service_profiles:
            infra = inventory._draw_infra_rack_service_profiles[0]
            while infra.next_page_infra:
                inventory._draw_infra_rack_service_profiles.append(infra.next_page_infra)
                infra = infra.next_page_infra

        inventory._draw_infra_rack_enclosure_service_profiles = []
        if rack_enclosure_rear_draw_list:
            if fi_rear_draw_list:
                inventory._draw_infra_rack_enclosure_service_profiles.append(
                    UcsSystemDrawInfraServiceProfile(draw_rack_enclosure_list=rack_enclosure_rear_draw_list,
                                                     parent=fi_rear_draw_list[0]._parent))
        if inventory._draw_infra_rack_enclosure_service_profiles:
            infra = inventory._draw_infra_rack_enclosure_service_profiles[0]
            while infra.next_page_infra:
                inventory._draw_infra_rack_enclosure_service_profiles.append(infra.next_page_infra)
                infra = infra.next_page_infra

        # Draw infra of equipments
        for chassis_draw in chassis_rear_draw_list:
            # if draw_rotated_fi_list exists then the chassis 1 is a UCS Mini chassis
            if not (rotated_fi_draw_list and chassis_draw._parent.id == '1'):
                if fi_rear_draw_list:
                    infra = UcsSystemDrawInfraChassis(chassis=chassis_draw,
                                                      fi_list=fi_rear_draw_list,
                                                      fex_list=fex_rear_draw_list,
                                                      parent=fi_rear_draw_list[0]._parent)
                    if hasattr(infra, "_file_name"):
                        # If wires are present
                        chassis_draw._parent._draw_infra = infra
                    else:
                        chassis_draw._parent._draw_infra = None
                else:
                    chassis_draw._parent._draw_infra = None

        for rack_draw in rack_rear_draw_list:
            if fi_rear_draw_list:
                infra = UcsSystemDrawInfraRack(rack=rack_draw, fi_list=fi_rear_draw_list,
                                               fex_list=fex_rear_draw_list,
                                               parent=fi_rear_draw_list[0]._parent)
                if hasattr(infra, "_file_name"):
                    # If wires are present
                    rack_draw._parent._draw_infra = infra
                else:
                    rack_draw._parent._draw_infra = None
            else:
                rack_draw._parent._draw_infra = None


        for rack_enclosure_draw in rack_enclosure_rear_draw_list:
            if fi_rear_draw_list:
                infra = UcsSystemDrawInfraRackEnclosure(rack_enclosure=rack_enclosure_draw, fi_list=fi_rear_draw_list,
                                               fex_list=fex_rear_draw_list,
                                               parent=fi_rear_draw_list[0]._parent)
                if hasattr(infra, "_file_name"):
                    # If wires are present
                    rack_enclosure_draw._parent._draw_infra = infra
                else:
                    rack_enclosure_draw._parent._draw_infra = None
            else:
                rack_enclosure_draw._parent._draw_infra = None

    def export_draw(self, uuid=None, export_format="png", directory=None, export_clear_pictures=False):
        """
        Export all the drawings

        :param uuid: The UUID of the drawn inventory to be exported. If not specified, the most recent inventory will be used
        :param export_format: "png" by default, not used for now
        :param directory:
        :param export_clear_pictures : Export the pictures without colored ports
        :return:
        """

        if uuid is None:
            self.logger(level="debug",
                        message="No inventory UUID specified in inventory save draw request. Using latest.")
            inventory = self.get_latest_inventory()
        else:
            # Find the inventory that needs to be exported
            inventory_list = [inventory for inventory in self.inventory_list if inventory.uuid == uuid]
            if len(inventory_list) != 1:
                self.logger(level="error", message="Failed to locate inventory with UUID " + str(uuid) + " for draw")
                return False
            else:
                inventory = inventory_list[0]

        if inventory is None:
            self.logger(level="error", message="No available inventory for draw")
            return False

        for chassis in inventory.chassis:
            if hasattr(chassis, "_draw_front"):
                if chassis._draw_front:
                    chassis._draw_front.save_image(output_directory=directory, format=export_format)
            if hasattr(chassis, "_draw_rear"):
                if chassis._draw_rear:
                    chassis._draw_rear.save_image(output_directory=directory, format=export_format)
                    if export_clear_pictures:
                        if hasattr(chassis._draw_rear, "clear_version"):
                            chassis._draw_rear.clear_version.save_image(output_directory=directory,
                                                                        format=export_format)
            if hasattr(chassis, "_draw_infra"):
                if chassis._draw_infra:
                    chassis._draw_infra.save_image(output_directory=directory, format=export_format)

        for rack in inventory.rack_units:
            if hasattr(rack, "_draw_front"):
                if rack._draw_front:
                    rack._draw_front.save_image(output_directory=directory, format=export_format)
            if hasattr(rack, "_draw_rear"):
                if rack._draw_rear:
                    rack._draw_rear.save_image(output_directory=directory, format=export_format)
                    if export_clear_pictures:
                        if hasattr(rack._draw_rear, "clear_version"):
                            rack._draw_rear.clear_version.save_image(output_directory=directory, format=export_format)
            if hasattr(rack, "_draw_infra"):
                if rack._draw_infra:
                    rack._draw_infra.save_image(output_directory=directory, format=export_format)
                    
        for rack_enclosure in inventory.rack_enclosures:
            if hasattr(rack_enclosure, "_draw_front"):
                if rack_enclosure._draw_front:
                    rack_enclosure._draw_front.save_image(output_directory=directory, format=export_format)
            if hasattr(rack_enclosure, "_draw_rear"):
                if rack_enclosure._draw_rear:
                    rack_enclosure._draw_rear.save_image(output_directory=directory, format=export_format)
                    if export_clear_pictures:
                        if hasattr(rack_enclosure._draw_rear, "clear_version"):
                            rack_enclosure._draw_rear.clear_version.save_image(output_directory=directory, format=export_format)
            if hasattr(rack_enclosure, "_draw_infra"):
                if rack_enclosure._draw_infra:
                    rack_enclosure._draw_infra.save_image(output_directory=directory, format=export_format)

        for fi in inventory.fabric_interconnects:
            if hasattr(fi, "_draw_front"):
                if fi._draw_front:
                    fi._draw_front.save_image(output_directory=directory, format=export_format)
            if hasattr(fi, "_draw_rear"):
                if fi._draw_rear:
                    fi._draw_rear.save_image(output_directory=directory, format=export_format)
                    if export_clear_pictures:
                        if hasattr(fi._draw_rear, "clear_version"):
                            fi._draw_rear.clear_version.save_image(output_directory=directory, format=export_format)

        for fex in inventory.fabric_extenders:
            if hasattr(fex, "_draw_front"):
                if fex._draw_front:
                    fex._draw_front.save_image(output_directory=directory, format=export_format)
            if hasattr(fex, "_draw_rear"):
                if fex._draw_rear:
                    fex._draw_rear.save_image(output_directory=directory, format=export_format)
                    if export_clear_pictures:
                        if hasattr(fex._draw_rear, "clear_version"):
                            fex._draw_rear.clear_version.save_image(output_directory=directory, format=export_format)

        if inventory._draw_infra_san_neighbors:
            inventory._draw_infra_san_neighbors.save_image(output_directory=directory, format=export_format)
        if inventory._draw_infra_lan_neighbors:
            inventory._draw_infra_lan_neighbors.save_image(output_directory=directory, format=export_format)
        if inventory._draw_infra_rack_service_profiles:
            for infra in inventory._draw_infra_rack_service_profiles:
                infra.save_image(output_directory=directory, format=export_format)
        if inventory._draw_infra_chassis_service_profiles:
            for infra in inventory._draw_infra_chassis_service_profiles:
                infra.save_image(output_directory=directory, format=export_format)
        if inventory._draw_infra_rack_enclosure_service_profiles:
            for infra in inventory._draw_infra_rack_enclosure_service_profiles:
                infra.save_image(output_directory=directory, format=export_format)

    def fetch_inventory(self):
        self.logger(message="Fetching inventory from live device (can take several minutes)")
        inventory = UcsSystemInventory(parent=self)
        inventory.origin = "live"
        inventory.load_from = "live"
        inventory._fetch_sdk_objects()
        self.logger(level="debug", message="Finished fetching UCS SDK objects for inventory")

        if "networkElement" in inventory.sdk_objects.keys():
            for network_element in sorted(inventory.sdk_objects["networkElement"], key=lambda fi: fi.dn):
                inventory.fabric_interconnects.append(UcsSystemFi(parent=inventory, network_element=network_element))

            # Verifying that Info Policy is enabled before trying to fetch neighbors
            self.logger(level="debug", message="Verifying that Info Policy is enabled")
            info_policy_state = None
            try:
                info_policy = self.parent.handle.query_dn("sys/info-policy")
                info_policy_state = info_policy.state

                if info_policy_state == "disabled":
                    self.logger(level="warning", message="Info Policy is disabled. No neighbors can be found")
                else:
                    # Fetch LAN & SAN neighbors
                    inventory.lan_neighbors = inventory._get_lan_neighbors()
                    inventory.san_neighbors = inventory._get_san_neighbors()

            except Exception:
                self.logger(level="warning", message="Unable to get Info Policy State")

        if "equipmentChassis" in inventory.sdk_objects.keys():
            for equipment_chassis in sorted(inventory.sdk_objects["equipmentChassis"], key=lambda chassis: [int(t) if t.isdigit() else t.lower() for t in re.split('(\d+)', chassis.id)]):
                inventory.chassis.append(UcsSystemChassis(parent=inventory, equipment_chassis=equipment_chassis))

        if "equipmentFex" in inventory.sdk_objects.keys():
            for equipment_fex in sorted(inventory.sdk_objects["equipmentFex"], key=lambda fex: [int(t) if t.isdigit() else t.lower() for t in re.split('(\d+)', fex.id)]):
                inventory.fabric_extenders.append(UcsSystemFex(parent=inventory, equipment_fex=equipment_fex))

        if "equipmentRackEnclosure" in inventory.sdk_objects.keys():
            for equipment_rack_enclosure in sorted(inventory.sdk_objects["equipmentRackEnclosure"], key=lambda enclosure: [int(t) if t.isdigit() else t.lower() for t in re.split('(\d+)', enclosure.id)]):
                inventory.rack_enclosures.append(UcsSystemRackEnclosure(parent=inventory, equipment_rack_enclosure=equipment_rack_enclosure))

        if "computeRackUnit" in inventory.sdk_objects.keys():
            for compute_rack_unit in sorted(inventory.sdk_objects["computeRackUnit"], key=lambda rack: [int(t) if t.isdigit() else t.lower() for t in re.split('(\d+)', rack.id)]):
                # We filter out rack servers that are inside enclosures (e.g. for UCS C4200)
                if compute_rack_unit.enclosure_id in ["0", None]:
                    inventory.rack_units.append(UcsSystemRack(parent=inventory, compute_rack_unit=compute_rack_unit))

        # Removing the list of SDK objects fetched from the live UCS device
        inventory.sdk_objects = None
        self.inventory_list.append(inventory)
        self.logger(message="Finished fetching inventory with UUID " + str(inventory.uuid) + " from live device")
        return inventory.uuid

    def _fill_inventory_from_json(self, inventory=None, inventory_json=None):
        """
        Fills inventory using parsed JSON inventory file
        :param inventory: inventory to be filled
        :param inventory_json: parsed JSON content containing inventory
        :return: True if successful, False otherwise
        """
        if inventory is None or inventory_json is None:
            self.logger(level="debug", message="Missing inventory or inventory_json parameter!")
            return False

        if "fabric_interconnects" in inventory_json:
            for network_element in inventory_json["fabric_interconnects"]:
                inventory.fabric_interconnects.append(UcsSystemFi(parent=inventory, network_element=network_element))

            # Fetch LAN & SAN neighbors
            inventory.lan_neighbors = inventory._get_lan_neighbors()
            inventory.san_neighbors = inventory._get_san_neighbors()

        if "chassis" in inventory_json:
            for equipment_chassis in inventory_json["chassis"]:
                inventory.chassis.append(UcsSystemChassis(parent=inventory, equipment_chassis=equipment_chassis))

        if "fabric_extenders" in inventory_json:
            for equipment_fex in inventory_json["fabric_extenders"]:
                inventory.fabric_extenders.append(UcsSystemFex(parent=inventory, equipment_fex=equipment_fex))

        if "rack_enclosures" in inventory_json:
            for equipment_rack_enclosure in inventory_json["rack_enclosures"]:
                inventory.rack_enclosures.append(
                    UcsSystemRackEnclosure(parent=inventory, equipment_rack_enclosure=equipment_rack_enclosure))

        if "rack_units" in inventory_json:
            for compute_rack_unit in inventory_json["rack_units"]:
                inventory.rack_units.append(UcsSystemRack(parent=inventory, compute_rack_unit=compute_rack_unit))
        return True


class UcsImcInventoryManager(GenericUcsInventoryManager):
    def __init__(self, parent=None):
        GenericUcsInventoryManager.__init__(self, parent=parent)
        self.inventory_class_name = UcsImcInventory

    def fetch_inventory(self):
        self.logger(message="Fetching inventory from live device (can take several minutes)")
        inventory = UcsImcInventory(parent=self)
        inventory.origin = "live"
        inventory.load_from = "live"
        inventory._fetch_sdk_objects()
        self.logger(level="debug", message="Finished fetching UCS SDK objects for inventory")

        if "equipmentRackEnclosure" in inventory.sdk_objects and len(inventory.sdk_objects["equipmentRackEnclosure"]) > 0:
            # Server is a server node inside a rack enclosure
            inventory.rack_enclosures.append(
                UcsImcRackEnclosure(parent=inventory,
                                    equipment_rack_enclosure=inventory.sdk_objects["equipmentRackEnclosure"][0]))

        elif "equipmentChassis" in inventory.sdk_objects:
            # Server is a chassis like S3260
            inventory.chassis.append(UcsImcChassis(parent=inventory,
                                                   equipment_chassis=inventory.sdk_objects["equipmentChassis"][0]))

        elif "computeRackUnit" in inventory.sdk_objects:
            # Server is a standalone rack server
            inventory.rack_units.append(UcsImcRack(parent=inventory,
                                                   compute_rack_unit=inventory.sdk_objects["computeRackUnit"][0]))

        # Removing the list of SDK objects fetched from the live UCS device
        inventory.sdk_objects = None
        self.inventory_list.append(inventory)
        self.logger(message="Finished fetching inventory with UUID " + str(inventory.uuid) + " from live device")
        return inventory.uuid

    def _fill_inventory_from_json(self, inventory=None, inventory_json=None):
        """
        Fills inventory using parsed JSON inventory file
        :param inventory: inventory to be filled
        :param inventory_json: parsed JSON content containing inventory
        :return: True if successful, False otherwise
        """
        if inventory is None or inventory_json is None:
            self.logger(level="debug", message="Missing inventory or inventory_json parameter!")
            return False

        if "rack_enclosures" in inventory_json:
            for equipment_rack_enclosure in inventory_json["rack_enclosures"]:
                inventory.rack_enclosures.append(UcsImcRackEnclosure(parent=inventory,
                                                                     equipment_rack_enclosure=equipment_rack_enclosure))

        if "chassis" in inventory_json:
            for chassis in inventory_json["chassis"]:
                inventory.chassis.append(UcsImcChassis(parent=inventory, equipment_chassis=chassis))

        if "rack_units" in inventory_json:
            for compute_rack_unit in inventory_json["rack_units"]:
                inventory.rack_units.append(UcsImcRack(parent=inventory, compute_rack_unit=compute_rack_unit))

        return True

    def draw_inventory(self, uuid=None):
        """
        Draws UCS chassis, racks, FEXs, FIs and LAN/SAN neighbors using the specified inventory
        :param uuid: The UUID of the inventory to be drawn. If not specified, the most recent inventory will be used
        :return: True if draw is successful, False otherwise
        """
        if uuid is None:
            self.logger(level="debug", message="No inventory UUID specified in inventory draw request. Using latest.")
            inventory = self.get_latest_inventory()
        else:
            # Find the inventory that needs to be exported
            inventory_list = [inventory for inventory in self.inventory_list if inventory.uuid == uuid]
            if len(inventory_list) != 1:
                self.logger(level="error", message="Failed to locate inventory with UUID " + str(uuid) + " for draw")
                return False
            else:
                inventory = inventory_list[0]

        if inventory is None:
            return False

        # rack_front_draw_list = []
        # rack_rear_draw_list = []
        for rack in inventory.rack_units:
            rack._generate_draw()
            # rack_front_draw_list.append(rack._draw_front)
            # rack_rear_draw_list.append(rack._draw_rear)

        for rack in inventory.rack_enclosures:
            rack._generate_draw()

        for chassis in inventory.chassis:
            chassis._generate_draw()

    def export_draw(self, uuid=None, export_format="png", directory=None, export_clear_pictures=False):
        """
        Export all the drawings

        :param uuid: The UUID of the drawn inventory to be exported. If not specified, the most recent inventory will be used
        :param export_format: "png" by default, not used for now
        :param directory:
        :param export_clear_pictures: not used
        :return:
        """

        if uuid is None:
            self.logger(level="debug",
                        message="No inventory UUID specified in inventory save draw request. Using latest.")
            inventory = self.get_latest_inventory()
        else:
            # Find the inventory that needs to be exported
            inventory_list = [inventory for inventory in self.inventory_list if inventory.uuid == uuid]
            if len(inventory_list) != 1:
                self.logger(level="error", message="Failed to locate inventory with UUID " + str(uuid) + " for draw")
                return False
            else:
                inventory = inventory_list[0]

        if inventory is None:
            return False

        for chassis in inventory.chassis:
            if hasattr(chassis, "_draw_front"):
                if chassis._draw_front:
                    chassis._draw_front.save_image(output_directory=directory, format=export_format)
            if hasattr(chassis, "_draw_rear"):
                if chassis._draw_rear:
                    chassis._draw_rear.save_image(output_directory=directory, format=export_format)

        for rack in inventory.rack_units:
            if hasattr(rack, "_draw_front"):
                if rack._draw_front:
                    rack._draw_front.save_image(output_directory=directory, format=export_format)
            if hasattr(rack, "_draw_rear"):
                if rack._draw_rear:
                    rack._draw_rear.save_image(output_directory=directory, format=export_format)

        for rack_enclosure in inventory.rack_enclosures:
            if hasattr(rack_enclosure, "_draw_front"):
                if rack_enclosure._draw_front:
                    rack_enclosure._draw_front.save_image(output_directory=directory, format=export_format)
            if hasattr(rack_enclosure, "_draw_rear"):
                if rack_enclosure._draw_rear:
                    rack_enclosure._draw_rear.save_image(output_directory=directory, format=export_format)


class UcsCentralInventoryManager(GenericUcsInventoryManager):
    def __init__(self, parent=None):
        GenericUcsInventoryManager.__init__(self, parent=parent)
        self.inventory_class_name = UcsCentralInventory

    def fetch_inventory(self):
        self.logger(message="Fetching inventory from live device (can take several minutes)")
        inventory = UcsCentralInventory(parent=self)
        inventory.origin = "live"
        inventory.load_from = "live"
        inventory._fetch_sdk_objects()
        self.logger(level="debug", message="Finished fetching UCS SDK objects for inventory")

        if "computeSystem" in inventory.sdk_objects.keys():
            for compute_system in sorted(inventory.sdk_objects["computeSystem"], key=lambda domain: [int(t) if t.isdigit() else t.lower() for t in re.split('(\d+)', domain.id)]):
                inventory.domains.append(UcsCentralDomain(parent=inventory, compute_system=compute_system))

        # Removing the list of SDK objects fetched from the live UCS device
        inventory.sdk_objects = None
        self.inventory_list.append(inventory)
        self.logger(message="Finished fetching inventory with UUID " + str(inventory.uuid) + " from live device")
        return inventory.uuid

    def _fill_inventory_from_json(self, inventory=None, inventory_json=None):
        """
        Fills inventory using parsed JSON inventory file
        :param inventory: inventory to be filled
        :param inventory_json: parsed JSON content containing inventory
        :return: True if successful, False otherwise
        """
        if inventory is None or inventory_json is None:
            self.logger(level="debug", message="Missing inventory or inventory_json parameter!")
            return False

        if "domains" in inventory_json:
            for compute_system in inventory_json["domains"]:
                inventory.domains.append(UcsCentralDomain(parent=inventory, compute_system=compute_system))

        return True

