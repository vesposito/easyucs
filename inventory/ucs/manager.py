# coding: utf-8
# !/usr/bin/env python

""" manager.py: Easy UCS Deployment Tool """

import re

from __init__ import __version__
from draw.ucs.chassis import UcsSystemDrawInfraChassis
from draw.ucs.neighbor import UcsSystemDrawInfraNeighborsLan, UcsSystemDrawInfraNeighborsSan
from draw.ucs.rack import UcsSystemDrawInfraRack, UcsSystemDrawInfraRackEnclosure
from draw.ucs.service_profile import UcsSystemDrawInfraServiceProfile
from inventory.manager import GenericInventoryManager
from inventory.ucs.chassis import UcsImcChassis, UcsSystemChassis
from inventory.ucs.domain import UcsCentralDomain
from inventory.ucs.fabric import UcsSystemFex, UcsSystemFi
from inventory.ucs.inventory import UcsImcInventory, UcsSystemInventory, UcsCentralInventory
from inventory.ucs.rack import UcsImcRack, UcsImcRackEnclosure, UcsSystemRack, UcsSystemRackEnclosure
from inventory.ucs.device_connector import UcsSystemDeviceConnector, UcsImcDeviceConnector


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

        if self.parent.task is not None:
            self.parent.task.taskstep_manager.start_taskstep(
                name="GenerateReportDrawInventoryUcsSystem",
                description="Drawing inventory of device " + self.parent.target)

        chassis_front_draw_list = []
        chassis_rear_draw_list = []
        for chassis in inventory.chassis:
            chassis._generate_draw()
            chassis_front_draw_list.append(chassis._draw_front)
            chassis_rear_draw_list.append(chassis._draw_rear)
        # We only keep the chassis that have been fully created -> json file and picture
        chassis_front_draw_list = [chassis for chassis in chassis_front_draw_list if chassis.picture_size]
        chassis_rear_draw_list = [chassis for chassis in chassis_rear_draw_list if chassis.picture_size]

        rack_front_draw_list = []
        rack_rear_draw_list = []
        for rack in inventory.rack_units:
            rack._generate_draw()
            rack_front_draw_list.append(rack._draw_front)
            rack_rear_draw_list.append(rack._draw_rear)
        # We only keep the racks that have been fully created -> json file and picture
        rack_front_draw_list = [rack for rack in rack_front_draw_list if rack.picture_size]
        rack_rear_draw_list = [rack for rack in rack_rear_draw_list if rack.picture_size]

        rack_enclosure_front_draw_list = []
        rack_enclosure_rear_draw_list = []
        for rack_enclosure in inventory.rack_enclosures:
            rack_enclosure._generate_draw()
            rack_enclosure_front_draw_list.append(rack_enclosure._draw_front)
            rack_enclosure_rear_draw_list.append(rack_enclosure._draw_rear)
        # We only keep the racks that have been fully created -> json file and picture
        rack_enclosure_front_draw_list = [rack_enclosure for rack_enclosure in rack_enclosure_front_draw_list if
                                          rack_enclosure.picture_size]
        rack_enclosure_rear_draw_list = [rack_enclosure for rack_enclosure in rack_enclosure_rear_draw_list if
                                         rack_enclosure.picture_size]

        fi_rear_draw_list = []
        for fi in inventory.fabric_interconnects:
            fi._generate_draw()
            fi_rear_draw_list.append(fi._draw_rear)
        # We only keep the FI that have been fully created -> json file and picture
        fi_rear_draw_list = [fi for fi in fi_rear_draw_list if fi.picture_size]

        rotated_fi_draw_list = []
        is_embedded_fi = False
        for fi in fi_rear_draw_list:
            if fi._parent.sku == "UCS-FI-M-6324":
                is_embedded_fi = True
                # As we drop the picture before, we need to recreate it and drop it again
                fi._get_picture()
                rotated_fi_draw_list.append(fi.rotate_object(fi))
                fi.picture = None
            elif fi._parent.sku == "UCSX-S9108-100G":
                is_embedded_fi = True

        fex_rear_draw_list = []
        for fex in inventory.fabric_extenders:
            fex._generate_draw()
            fex_rear_draw_list.append(fex._draw_rear)
        # We only keep the FEX that have been fully created -> json file and picture
        fex_rear_draw_list = [fex for fex in fex_rear_draw_list if fex.picture_size]

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
            # if FI is embedded then the chassis 1 is a UCS Mini/X-Direct chassis, so no need to draw infra
            if not (is_embedded_fi and chassis_draw._parent.id == '1'):
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

        if self.parent.task is not None:
            self.parent.task.taskstep_manager.stop_taskstep(
                name="GenerateReportDrawInventoryUcsSystem", status="successful",
                status_message="Finished drawing inventory of device " + self.parent.target)

        return True

    def export_draw(self, uuid=None, export_format="png", directory=None, export_clear_pictures=False):
        """
        Export all the drawings generated from an inventory
        :param uuid: The UUID of the drawn inventory to be exported. If not specified, most recent will be used
        :param export_format: "png" by default, not used for now
        :param directory: directory to export the pictures to
        :param export_clear_pictures : Also export the pictures without colored ports
        :return: True if successful, False otherwise
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
                            rack_enclosure._draw_rear.clear_version.save_image(output_directory=directory,
                                                                               format=export_format)
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

        return True

    def fetch_inventory(self, force=False):
        """
        Fetches inventory from a live UCS System device
        :return: Inventory UUID if successful, None otherwise
        """
        self.logger(message="Fetching inventory from live device (can take several minutes)")
        inventory = UcsSystemInventory(parent=self)
        inventory.metadata.origin = "live"
        inventory.metadata.easyucs_version = __version__
        inventory.load_from = "live"
        inventory._fetch_sdk_objects(force=force)

        # If any of the mandatory tasksteps fails then return None
        from api.api_server import easyucs
        if easyucs and self.parent.task and \
                easyucs.task_manager.is_any_taskstep_failed(uuid=self.parent.task.metadata.uuid):
            self.logger(level="error", message="Failed to fetch one or more SDK objects. Stopping the inventory fetch.")
            return None

        self.logger(level="debug", message="Finished fetching " + self.parent.metadata.device_type_long +
                                           " SDK objects for inventory")

        # Fetch device connector info.
        # We only do this if UCSM user has admin privileges as it is required for Device Connector API
        if "admin" in self.parent.handle.priv.split(","):
            if self.parent.task is not None:
                self.parent.task.taskstep_manager.start_taskstep(
                    name="FetchInventoryUcsSystemDeviceConnector",
                    description="Fetching " + self.parent.metadata.device_type_long + " Device Connector Inventory")
            device_connector = UcsSystemDeviceConnector(parent=inventory)
            if device_connector.version:
                inventory.device_connector.append(device_connector)
                if self.parent.task is not None:
                    self.parent.task.taskstep_manager.stop_taskstep(
                        name="FetchInventoryUcsSystemDeviceConnector", status="successful",
                        status_message="Successfully fetched " + self.parent.metadata.device_type_long +
                                       " Device Connector Inventory")
            else:
                self.logger(level="warning", message="Error while fetching " + self.parent.metadata.device_type_long +
                                                     " Device Connector Inventory")
                if self.parent.task is not None:
                    self.parent.task.taskstep_manager.stop_taskstep(
                        name="FetchInventoryUcsSystemDeviceConnector", status="failed",
                        status_message="Error while fetching " + self.parent.metadata.device_type_long +
                                       " Device connector Inventory")
        else:
            self.logger(level="debug", message="Skipped fetching " + self.parent.metadata.device_type_long +
                                               " Device Connector Inventory as user " + self.parent.username +
                                               " does not have admin privileges")
            if self.parent.task is not None:
                self.parent.task.taskstep_manager.skip_taskstep(
                    name="FetchInventoryUcsSystemDeviceConnector",
                    status_message="Skipped fetching " + self.parent.metadata.device_type_long +
                                " Device Connector Inventory as user " + self.parent.username +
                                " does not have admin privileges")

        if "networkElement" in inventory.sdk_objects.keys():
            for network_element in sorted(inventory.sdk_objects["networkElement"], key=lambda fi: fi.dn):
                inventory.fabric_interconnects.append(UcsSystemFi(parent=inventory, network_element=network_element))

            # Verifying that Info Policy is enabled before trying to fetch neighbors
            self.logger(level="debug", message="Verifying that Info Policy is enabled")
            try:
                info_policy = self.parent.handle.query_dn("sys/info-policy")
                info_policy_state = info_policy.state

                if info_policy_state == "disabled":
                    self.logger(level="warning", message="Info Policy is disabled. No neighbors can be found")
                else:
                    # Fetch LAN & SAN neighbors
                    inventory.lan_neighbors = inventory._get_lan_neighbors()
                    inventory.san_neighbors = inventory._get_san_neighbors()

            except Exception as err:
                self.logger(level="warning", message="Unable to get Info Policy State: " + str(err))

        if "equipmentChassis" in inventory.sdk_objects.keys():
            for equipment_chassis in sorted(inventory.sdk_objects["equipmentChassis"],
                                            key=lambda chassis: [int(t) if t.isdigit() else t.lower() for t in
                                                                 re.split('(\d+)', chassis.id)]):
                # We filter out chassis that have "identity-unestablishable" in their presence attribute
                if hasattr(equipment_chassis, "presence") and "identity-unestablishable" in equipment_chassis.presence:
                    continue
                inventory.chassis.append(UcsSystemChassis(parent=inventory, equipment_chassis=equipment_chassis))

        if "equipmentFex" in inventory.sdk_objects.keys():
            for equipment_fex in sorted(inventory.sdk_objects["equipmentFex"],
                                        key=lambda fex: [int(t) if t.isdigit() else t.lower() for t in
                                                         re.split('(\d+)', fex.id)]):
                inventory.fabric_extenders.append(UcsSystemFex(parent=inventory, equipment_fex=equipment_fex))

        if "equipmentRackEnclosure" in inventory.sdk_objects.keys():
            for equipment_rack_enclosure in sorted(inventory.sdk_objects["equipmentRackEnclosure"],
                                                   key=lambda enclosure: [int(t) if t.isdigit() else t.lower() for t in
                                                                          re.split('(\d+)', enclosure.id)]):
                inventory.rack_enclosures.append(
                    UcsSystemRackEnclosure(parent=inventory, equipment_rack_enclosure=equipment_rack_enclosure))

        if "computeRackUnit" in inventory.sdk_objects.keys():
            for compute_rack_unit in sorted(inventory.sdk_objects["computeRackUnit"],
                                            key=lambda rack: [int(t) if t.isdigit() else t.lower() for t in
                                                              re.split('(\d+)', rack.id)]):
                # We filter out rack servers that have "identity-unestablishable" in their presence attribute
                if hasattr(compute_rack_unit, "presence") and "identity-unestablishable" in compute_rack_unit.presence:
                    continue
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

        if "device_connector" in inventory_json:
            for device_connector in inventory_json["device_connector"]:
                inventory.device_connector.append(UcsSystemDeviceConnector(parent=inventory,
                                                                           device_connector=device_connector))

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

    def fetch_inventory(self, force=False):
        self.logger(message="Fetching inventory from live device (can take several minutes)")
        inventory = UcsImcInventory(parent=self)
        inventory.metadata.origin = "live"
        inventory.metadata.easyucs_version = __version__
        inventory.load_from = "live"
        inventory._fetch_sdk_objects(force=force)

        # If any of the mandatory tasksteps fails then return None
        from api.api_server import easyucs
        if easyucs and self.parent.task and \
                easyucs.task_manager.is_any_taskstep_failed(uuid=self.parent.task.metadata.uuid):
            self.logger(level="error", message="Failed to fetch one or more SDK objects. Stopping the inventory fetch.")
            return None

        self.logger(level="debug", message="Finished fetching " + self.parent.metadata.device_type_long +
                                           " SDK objects for inventory")

        # Add device connector
        if self.parent.task is not None:
            self.parent.task.taskstep_manager.start_taskstep(
                name="FetchInventoryUcsImcDeviceConnector",
                description="Fetching " + self.parent.metadata.device_type_long + " Device Connector Inventory")
        device_connector = UcsImcDeviceConnector(parent=inventory)
        if device_connector.version:
            inventory.device_connector.append(device_connector)
            if self.parent.task is not None:
                self.parent.task.taskstep_manager.stop_taskstep(
                    name="FetchInventoryUcsImcDeviceConnector", status="successful",
                    status_message="Successfully fetched " + self.parent.metadata.device_type_long +
                                   " Device Connector Inventory")
        else:
            if self.parent.task is not None:
                self.parent.task.taskstep_manager.stop_taskstep(
                    name="FetchInventoryUcsImcDeviceConnector", status="failed",
                    status_message="Error while fetching " + self.parent.metadata.device_type_long +
                                   " Device connector Inventory")

        if "equipmentRackEnclosure" in inventory.sdk_objects and len(
                inventory.sdk_objects["equipmentRackEnclosure"]) > 0:
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

        if "device_connector" in inventory_json:
            for device_connector in inventory_json["device_connector"]:
                inventory.device_connector.append(UcsImcDeviceConnector(parent=inventory,
                                                                        device_connector=device_connector))

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

        if self.parent.task is not None:
            self.parent.task.taskstep_manager.start_taskstep(
                name="GenerateReportDrawInventoryUcsImc",
                description="Drawing inventory of device " + self.parent.target)

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

        if self.parent.task is not None:
            self.parent.task.taskstep_manager.stop_taskstep(
                name="GenerateReportDrawInventoryUcsImc", status="successful",
                status_message="Finished drawing inventory of device " + self.parent.target)

        return True

    def export_draw(self, uuid=None, export_format="png", directory=None, export_clear_pictures=False):
        """
        Export all the drawings
        :param uuid: The UUID of the drawn inventory to be exported. If not specified, most recent will be used
        :param export_format: "png" by default, not used for now
        :param directory:
        :param export_clear_pictures: not used
        :return: True if successful, False otherwise
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

        return True


class UcsCentralInventoryManager(GenericUcsInventoryManager):
    def __init__(self, parent=None):
        GenericUcsInventoryManager.__init__(self, parent=parent)
        self.inventory_class_name = UcsCentralInventory

    def fetch_inventory(self, force=False):
        self.logger(message="Fetching inventory from live device (can take several minutes)")
        inventory = UcsCentralInventory(parent=self)
        inventory.metadata.origin = "live"
        inventory.metadata.easyucs_version = __version__
        inventory.load_from = "live"
        inventory._fetch_sdk_objects(force=force)

        # If any of the mandatory tasksteps fails then return None
        from api.api_server import easyucs
        if easyucs and self.parent.task and \
                easyucs.task_manager.is_any_taskstep_failed(uuid=self.parent.task.metadata.uuid):
            self.logger(level="error", message="Failed to fetch one or more SDK objects. Stopping the inventory fetch.")
            return None

        self.logger(level="debug", message="Finished fetching " + self.parent.metadata.device_type_long +
                                           " SDK objects for inventory")

        if "computeSystem" in inventory.sdk_objects.keys():
            for compute_system in sorted(inventory.sdk_objects["computeSystem"],
                                         key=lambda domain: [int(t) if t.isdigit() else t.lower() for t in
                                                             re.split('(\d+)', domain.id)]):
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
