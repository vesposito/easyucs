# coding: utf-8
# !/usr/bin/env python

""" chassis.py: Easy UCS Deployment Tool """
from easyucs import __author__, __copyright__,  __version__, __status__


import json

from easyucs.inventory.object import GenericUcsInventoryObject, UcsImcInventoryObject, UcsSystemInventoryObject
from easyucs.inventory.ucs.blade import UcsSystemBlade
from easyucs.inventory.ucs.fabric import UcsSystemFi
from easyucs.inventory.ucs.server_node import UcsImcServerNode
from easyucs.inventory.ucs.storage import UcsImcStorageEnclosure, UcsSystemStorageEnclosure, UcsImcStorageLocalDisk,\
    UcsImcSiocStorageNvmeDrive
from easyucs.inventory.ucs.port import UcsSystemIomPort, UcsSystemSiocPort
from easyucs.inventory.ucs.psu import UcsImcPsu, UcsSystemPsu
from easyucs.draw.ucs.chassis import UcsSystemDrawChassisFront, UcsSystemDrawChassisRear, UcsImcDrawChassisFront,\
    UcsImcDrawChassisRear


class UcsChassis(GenericUcsInventoryObject):
    _UCS_SDK_OBJECT_NAME = "equipmentChassis"

    def __init__(self, parent=None, equipment_chassis=None):
        GenericUcsInventoryObject.__init__(self, parent=parent, ucs_sdk_object=equipment_chassis)

        self.model = self.get_attribute(ucs_sdk_object=equipment_chassis, attribute_name="model")
        self.serial = self.get_attribute(ucs_sdk_object=equipment_chassis, attribute_name="serial")
        self.user_label = self.get_attribute(ucs_sdk_object=equipment_chassis, attribute_name="usr_lbl",
                                             attribute_secondary_name="user_label")

        self.power_supplies = self._get_power_supplies()
        self.system_io_controllers = self._get_system_io_controllers()

    def _generate_draw(self):
        pass

    def _get_model_short_name(self):
        """
        Returns Chassis short name from EasyUCS catalog files
        """
        if self.sku is not None:
            # We use the catalog file to get the chassis short name
            try:
                json_file = open("catalog/chassis/" + self.sku + ".json")
                chassis_catalog = json.load(fp=json_file)
                json_file.close()

                if "model_short_name" in chassis_catalog:
                    return chassis_catalog["model_short_name"]

            except FileNotFoundError:
                self.logger(level="error", message="Chassis catalog file " + self.sku + ".json not found")
                return None

        return None

    def _get_power_supplies(self):
        return []

    def _get_storage_enclosures(self):
        return []

    def _get_system_io_controllers(self):
        return []


class UcsIom(GenericUcsInventoryObject):
    _UCS_SDK_OBJECT_NAME = "equipmentIOCard"

    def __init__(self, parent=None, equipment_io_card=None):
        GenericUcsInventoryObject.__init__(self, parent=parent, ucs_sdk_object=equipment_io_card)

        self.chassis_id = self.get_attribute(ucs_sdk_object=equipment_io_card, attribute_name="chassis_id")
        self.id = self.get_attribute(ucs_sdk_object=equipment_io_card, attribute_name="id")
        self.model = self.get_attribute(ucs_sdk_object=equipment_io_card, attribute_name="model")
        self.revision = self.get_attribute(ucs_sdk_object=equipment_io_card, attribute_name="revision")
        self.serial = self.get_attribute(ucs_sdk_object=equipment_io_card, attribute_name="serial")
        self.vendor = self.get_attribute(ucs_sdk_object=equipment_io_card, attribute_name="vendor")

        self.ports = self._get_ports()

    def _get_ports(self):
        return []


class UcsSioc(GenericUcsInventoryObject):
    _UCS_SDK_OBJECT_NAME = "equipmentSystemIOController"

    def __init__(self, parent=None, equipment_system_io_controller=None):
        GenericUcsInventoryObject.__init__(self, parent=parent, ucs_sdk_object=equipment_system_io_controller)

        self.id = self.get_attribute(ucs_sdk_object=equipment_system_io_controller, attribute_name="id")

        self.ports = self._get_ports()

    def _get_ports(self):
        return []


class UcsSystemChassis(UcsChassis, UcsSystemInventoryObject):
    _UCS_SDK_CATALOG_OBJECT_NAME = "equipmentChassisCapProvider"

    def __init__(self, parent=None, equipment_chassis=None):
        UcsChassis.__init__(self, parent=parent, equipment_chassis=equipment_chassis)

        self.id = self.get_attribute(ucs_sdk_object=equipment_chassis, attribute_name="id")
        self.revision = self.get_attribute(ucs_sdk_object=equipment_chassis, attribute_name="revision")
        self.vendor = self.get_attribute(ucs_sdk_object=equipment_chassis, attribute_name="vendor")

        UcsSystemInventoryObject.__init__(self, parent=parent, ucs_sdk_object=equipment_chassis)

        self.blades = self._get_blades()
        self.fabric_interconnects = self._get_fabric_interconnects()
        self.io_modules = self._get_io_modules()
        self.storage_enclosures = self._get_storage_enclosures()
        self.slots_max = self._get_chassis_slots_max()
        self.slots_populated = self._calculate_chassis_slots_populated()
        self.slots_free_half = self._calculate_chassis_slots_free_half()
        self.slots_free_full = self._calculate_chassis_slots_free_full()
        self.locator_led_status = None
        self.short_name = None

        if self._inventory.load_from == "live":
            self.locator_led_status = self._determine_locator_led_status()
            self.short_name = self._get_model_short_name()
        elif self._inventory.load_from == "file":
            for attribute in ["locator_led_status", "short_name"]:
                setattr(self, attribute, None)
                if attribute in equipment_chassis:
                    setattr(self, attribute, self.get_attribute(ucs_sdk_object=equipment_chassis,
                                                                attribute_name=attribute))

    def _calculate_chassis_slots_free_full(self):
        if self.slots_max is None:
            return None

        slots_used = []
        for blade in self.blades:
            if not hasattr(blade, "slot_id"):
                return None
            slots_used.append(int(blade.slot_id))

            # We handle the specific case of a B460 M4 for which we also use the 2 slots above the master blade
            if hasattr(blade, "scaled_mode"):
                if blade.scaled_mode == "scaled":
                    slots_used.extend([int(blade.slot_id) - 1, int(blade.slot_id) - 2])

        slots_free_full = [slot_even for slot_even in range(1, self.slots_max + 1, 2) if slot_even not in slots_used
                           and slot_even + 1 not in slots_used]
        return len(slots_free_full)

    def _calculate_chassis_slots_free_half(self):
        if self.slots_max is None or self.slots_populated is None:
            return None
        return self.slots_max - self.slots_populated

    def _calculate_chassis_slots_populated(self):
        if not hasattr(self, "sku"):
            return None
        if self.sku is None:
            return None

        # We use the catalog file to get the blades widths
        try:
            json_file = open("catalog/chassis/" + self.sku + ".json")
            chassis_catalog = json.load(fp=json_file)
            json_file.close()
        except FileNotFoundError:
            self.logger(level="error", message="Chassis catalog file " + self.sku + ".json not found")
            return None

        if "blades_models" not in chassis_catalog:
            self.logger(level="warning",
                        message="Chassis catalog file " + self.sku +
                                ".json has no section \"blades_models\". Could not calculate populated slots.")
            return None

        slots_populated = 0
        for blade in self.blades:
            if not hasattr(blade, "sku"):
                return None
            for blade_model in chassis_catalog["blades_models"]:
                if "name" not in blade_model or "width" not in blade_model:
                    self.logger(level="warning",
                                message="Chassis catalog file " + self.sku + ".json section \"blades_models\"" +
                                        " is incomplete. Could not calculate populated slots.")
                    return None
                if blade_model["name"] == blade.sku:
                    # We handle the specific case of a B460 M4
                    if hasattr(blade, "scaled_mode"):
                        if blade.scaled_mode == "scaled":
                            slots_populated += 4
                            continue
                    if blade_model["width"] == "half":
                        slots_populated += 1
                    elif blade_model["width"] == "full":
                        slots_populated += 2
                    else:
                        self.logger(level="warning",
                                    message="Chassis catalog file " + self.sku + ".json section \"blades_models\"" +
                                            " is incorrect. Could not calculate populated slots.")
                        return None
        return slots_populated

    def _generate_draw(self):
        self._draw_front = UcsSystemDrawChassisFront(parent=self)
        self._draw_rear = UcsSystemDrawChassisRear(parent=self)
        self._draw_infra = None

    def _get_blades(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsSystemBlade, parent=self)
        elif self._inventory.load_from == "file" and "blades" in self._ucs_sdk_object:
            return [UcsSystemBlade(self, blade) for blade in self._ucs_sdk_object["blades"]]
        else:
            return []

    def _get_chassis_slots_max(self):
        if not hasattr(self, "sku"):
            return None
        if self.sku is None:
            return None

        # We use the catalog file to get the number of slots in the chassis
        try:
            json_file = open("catalog/chassis/" + self.sku + ".json")
            chassis_catalog = json.load(fp=json_file)
            json_file.close()
        except FileNotFoundError:
            self.logger(level="error", message="Chassis catalog file " + self.sku + ".json not found")
            return None

        if "blades_slots" in chassis_catalog:
            return len(chassis_catalog["blades_slots"])
        elif "blades_slots_rear" in chassis_catalog:
            return len(chassis_catalog["blades_slots_rear"])
        return None

    def _get_fabric_interconnects(self):
        if self._inventory.load_from == "live":
            equipment_switch_io_card_list = []
            ucs_system_fi_list = []
            if "equipmentSwitchIOCard" in self._inventory.sdk_objects.keys():
                if self._inventory.sdk_objects["equipmentSwitchIOCard"] is not None:
                    # We filter out SDK objects that are not under this Dn
                    for sdk_object in self._inventory.sdk_objects["equipmentSwitchIOCard"]:
                        if self.dn + "/" in sdk_object.dn:
                            equipment_switch_io_card_list.append(sdk_object)

                    # We create a list of UcsSystemFi objects from the equipmentSwitchIOCard objects list
                    for equipment_switch_io_card in equipment_switch_io_card_list:
                        # We need to get the networkElement object corresponding to the equipmentSwitchIOCard
                        list_fi = [network_element for network_element in self._inventory.sdk_objects["networkElement"]
                                   if equipment_switch_io_card.serial == network_element.serial]
                        if len(list_fi) == 1:
                            ucs_system_fi_list.append(UcsSystemFi(parent=self, network_element=list_fi[0]))

            return ucs_system_fi_list
        elif self._inventory.load_from == "file" and "fabric_interconnects" in self._ucs_sdk_object:
            return [UcsSystemFi(self, fi) for fi in self._ucs_sdk_object["fabric_interconnects"]]
        else:
            return []

    def _get_io_modules(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsSystemIom, parent=self)
        elif self._inventory.load_from == "file" and "io_modules" in self._ucs_sdk_object:
            return [UcsSystemIom(self, iom) for iom in self._ucs_sdk_object["io_modules"]]
        else:
            return []

    def _get_power_supplies(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsSystemPsu, parent=self)
        elif self._inventory.load_from == "file" and "power_supplies" in self._ucs_sdk_object:
            return [UcsSystemPsu(self, psu) for psu in self._ucs_sdk_object["power_supplies"]]
        else:
            return []

    def _get_storage_enclosures(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsSystemStorageEnclosure,
                                                                  parent=self)
        elif self._inventory.load_from == "file" and "storage_enclosures" in self._ucs_sdk_object:
            return [UcsSystemStorageEnclosure(self, storage_enclosure) for storage_enclosure in
                    self._ucs_sdk_object["storage_enclosures"]]
        else:
            return []

    def _get_system_io_controllers(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsSystemSioc, parent=self)
        elif self._inventory.load_from == "file" and "system_io_controllers" in self._ucs_sdk_object:
            return [UcsSystemSioc(self, sioc) for sioc in self._ucs_sdk_object["system_io_controllers"]]
        else:
            return []


class UcsImcChassis(UcsChassis, UcsImcInventoryObject):
    def __init__(self, parent=None, equipment_chassis=None):
        UcsChassis.__init__(self, parent=parent, equipment_chassis=equipment_chassis)
        UcsImcInventoryObject.__init__(self, parent=parent, ucs_sdk_object=equipment_chassis)

        self.name = self.get_attribute(ucs_sdk_object=equipment_chassis, attribute_name="name")

        # Since we don't have a catalog item for finding the SKU, we set it manually here
        self.sku = self.model
        if self.sku == "UCSS-S3260-BASE":
            self.sku = "UCSS-S3260"

        self.locator_led_status = None
        self.short_name = None

        self.server_nodes = self._get_server_nodes()
        self.storage_enclosures = self._get_storage_enclosures()
        self.slots_max = self._get_chassis_slots_max()
        self.slots_populated = self._calculate_chassis_slots_populated()
        self.slots_free_half = self._calculate_chassis_slots_free_half()
        self.slots_free_full = self._calculate_chassis_slots_free_full()

        if self._inventory.load_from == "live":
            self.locator_led_status = self._determine_locator_led_status()
            self.short_name = self._get_model_short_name()
        elif self._inventory.load_from == "file":
            for attribute in ["locator_led_status", "short_name"]:
                setattr(self, attribute, None)
                if attribute in equipment_chassis:
                    setattr(self, attribute, self.get_attribute(ucs_sdk_object=equipment_chassis,
                                                                attribute_name=attribute))

    def _calculate_chassis_slots_free_full(self):
        if self.slots_max is None:
            return None

        slots_used = []
        for server_node in self.server_nodes:
            if not hasattr(server_node, "id"):
                return None
            slots_used.append(int(server_node.id))

        slots_free_full = [slot_even for slot_even in range(1, self.slots_max + 1, 2) if slot_even not in slots_used
                           and slot_even + 1 not in slots_used]
        return len(slots_free_full)

    def _calculate_chassis_slots_free_half(self):
        if self.slots_max is None or self.slots_populated is None:
            return None
        return self.slots_max - self.slots_populated

    def _calculate_chassis_slots_populated(self):
        if not hasattr(self, "sku"):
            return None
        if self.sku is None:
            return None

        # We use the catalog file to get the blades widths
        try:
            json_file = open("catalog/chassis/" + self.sku + ".json")
            chassis_catalog = json.load(fp=json_file)
            json_file.close()
        except FileNotFoundError:
            self.logger(level="error", message="Chassis catalog file " + self.sku + ".json not found")
            return None

        if "blades_models" not in chassis_catalog:
            self.logger(level="warning",
                        message="Chassis catalog file " + self.sku +
                                ".json has no section \"blades_models\". Could not calculate populated slots.")
            return None

        slots_populated = 0
        for server_node in self.server_nodes:
            if not hasattr(server_node, "sku"):
                return None
            for blade_model in chassis_catalog["blades_models"]:
                if "name" not in blade_model or "width" not in blade_model:
                    self.logger(level="warning",
                                message="Chassis catalog file " + self.sku + ".json section \"blades_models\"" +
                                        " is incomplete. Could not calculate populated slots.")
                    return None
                if blade_model["name"] == server_node.sku:
                    if blade_model["width"] == "half":
                        slots_populated += 1
                    elif blade_model["width"] == "full":
                        slots_populated += 2
                    else:
                        self.logger(level="warning",
                                    message="Chassis catalog file " + self.sku + ".json section \"blades_models\"" +
                                            " is incorrect. Could not calculate populated slots.")
                        return None
        return slots_populated

    def _generate_draw(self):
        self._draw_front = UcsImcDrawChassisFront(parent=self)
        self._draw_rear = UcsImcDrawChassisRear(parent=self)

    def _get_chassis_slots_max(self):
        if not hasattr(self, "sku"):
            return None
        if self.sku is None:
            return None

        # We use the catalog file to get the number of slots in the chassis
        try:
            json_file = open("catalog/chassis/" + self.sku + ".json")
            chassis_catalog = json.load(fp=json_file)
            json_file.close()
        except FileNotFoundError:
            self.logger(level="error", message="Chassis catalog file " + self.sku + ".json not found")
            return None

        if "blades_slots" in chassis_catalog:
            return len(chassis_catalog["blades_slots"])
        elif "blades_slots_rear" in chassis_catalog:
            return len(chassis_catalog["blades_slots_rear"])
        return None

    def _get_power_supplies(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsImcPsu, parent=self)
        elif self._inventory.load_from == "file" and "power_supplies" in self._ucs_sdk_object:
            return [UcsImcPsu(self, psu) for psu in self._ucs_sdk_object["power_supplies"]]
        else:
            return []

    def _get_server_nodes(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsImcServerNode,
                                                                  parent=self)
        elif self._inventory.load_from == "file" and "server_nodes" in self._ucs_sdk_object:
            return [UcsImcServerNode(self, server_node) for server_node in self._ucs_sdk_object["server_nodes"]]
        else:
            return []

    def _get_storage_enclosures(self):
        if self._inventory.load_from == "live":
            if self.sku in ["UCSC-C3X60", "UCSC-C3X60-BASE", "UCSS-S3260", "UCSS-S3260-BASE"]:
                # Create Storage Enclosures for rear SSD drives - they do not appear on IMC MIT
                rear_ssd_storage_enclosure_1 = UcsImcStorageEnclosure(parent=self, storage_enclosure=None)
                rear_ssd_storage_enclosure_1.descr = "Dedicated Rear SSD Enclosure"
                rear_ssd_storage_enclosure_1.type = "rear-ssd"
                rear_ssd_storage_enclosure_1.num_slots = "2"
                rear_ssd_storage_enclosure_1.disks = []

                # We find out if there are boot drives that belong to this Storage Enclosure, and we add them to it
                if "storageLocalDisk" in self._inventory.sdk_objects.keys():
                    # We check if we already have fetched the list of storageLocalDisk objects
                    if self._inventory.sdk_objects["storageLocalDisk"] is not None:

                        # We need to find the matching storageLocalDisk object(s)
                        storage_local_disk_list = [storage_local_disk for storage_local_disk in
                                                   self._inventory.sdk_objects["storageLocalDisk"] if
                                                   storage_local_disk.id in ["201", "202"]]
                        if (len(storage_local_disk_list)) in [1, 2]:
                            for boot_drive in storage_local_disk_list:
                                rear_ssd_storage_enclosure_1.disks.append(
                                    UcsImcStorageLocalDisk(parent=rear_ssd_storage_enclosure_1,
                                                           storage_local_disk=boot_drive))
                        else:
                            self.logger(level="debug",
                                        message="Could not find corresponding boot drive(s) for rear SSD storage enclosure 1")

                if len(self.server_nodes) == 2:
                    rear_ssd_storage_enclosure_2 = UcsImcStorageEnclosure(parent=self, storage_enclosure=None)
                    rear_ssd_storage_enclosure_2.descr = "Dedicated Rear SSD Enclosure"
                    rear_ssd_storage_enclosure_2.type = "rear-ssd"
                    rear_ssd_storage_enclosure_2.num_slots = "2"
                    rear_ssd_storage_enclosure_2.disks = []

                    # We find out if there are boot drives that belong to this Storage Enclosure, and we add them to it
                    if "storageLocalDisk" in self._inventory.sdk_objects.keys():
                        # We check if we already have fetched the list of storageLocalDisk objects
                        if self._inventory.sdk_objects["storageLocalDisk"] is not None:

                            # We need to find the matching storageLocalDisk object(s)
                            storage_local_disk_list = [storage_local_disk for storage_local_disk in
                                                       self._inventory.sdk_objects["storageLocalDisk"] if
                                                       storage_local_disk.id in ["203", "204"]]
                            if (len(storage_local_disk_list)) in [1, 2]:
                                for boot_drive in storage_local_disk_list:
                                    rear_ssd_storage_enclosure_2.disks.append(
                                        UcsImcStorageLocalDisk(parent=rear_ssd_storage_enclosure_2,
                                                               storage_local_disk=boot_drive))
                            else:
                                self.logger(level="debug",
                                            message="Could not find corresponding boot drive(s) for rear SSD storage enclosure 2")

                    return self._inventory.get_inventory_objects_under_dn(dn=self.dn,
                                                                          object_class=UcsImcStorageEnclosure,
                                                                          parent=self) + [rear_ssd_storage_enclosure_1,
                                                                                          rear_ssd_storage_enclosure_2]

                else:
                    return self._inventory.get_inventory_objects_under_dn(dn=self.dn,
                                                                          object_class=UcsImcStorageEnclosure,
                                                                          parent=self) + [rear_ssd_storage_enclosure_1]
            else:
                return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsImcStorageEnclosure,
                                                                      parent=self)
        elif self._inventory.load_from == "file" and "storage_enclosures" in self._ucs_sdk_object:
            return [UcsImcStorageEnclosure(self, storage_enclosure) for storage_enclosure in
                    self._ucs_sdk_object["storage_enclosures"]]
        else:
            return []

    def _get_system_io_controllers(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsImcSioc, parent=self)
        elif self._inventory.load_from == "file" and "system_io_controllers" in self._ucs_sdk_object:
            return [UcsImcSioc(self, sioc) for sioc in self._ucs_sdk_object["system_io_controllers"]]
        else:
            return []


class UcsSystemIom(UcsIom, UcsSystemInventoryObject):
    _UCS_SDK_CATALOG_OBJECT_NAME = "equipmentIOCardCapProvider"
    _UCS_SDK_FIRMWARE_RUNNING_SUFFIX = "/mgmt/fw-system"

    def __init__(self, parent=None, equipment_io_card=None):
        UcsIom.__init__(self, parent=parent, equipment_io_card=equipment_io_card)
        UcsSystemInventoryObject.__init__(self, parent=parent, ucs_sdk_object=equipment_io_card)

    def _get_ports(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsSystemIomPort,
                                                                  parent=self)
        elif self._inventory.load_from == "file" and "ports" in self._ucs_sdk_object:
            return [UcsSystemIomPort(self, port) for port in self._ucs_sdk_object["ports"]]
        else:
            return []


class UcsSystemSioc(UcsSioc, UcsSystemInventoryObject):
    _UCS_SDK_CATALOG_OBJECT_NAME = "adaptorFruCapProvider"
    _UCS_SDK_FIRMWARE_RUNNING_SUFFIX = "/shared-io-module/mgmt/fw-system"

    def __init__(self, parent=None, equipment_system_io_controller=None):
        UcsSioc.__init__(self, parent=parent, equipment_system_io_controller=equipment_system_io_controller)

        self.chassis_id = self.get_attribute(ucs_sdk_object=equipment_system_io_controller, attribute_name="chassis_id")
        self.model = self.get_attribute(ucs_sdk_object=equipment_system_io_controller, attribute_name="model")
        self.revision = self.get_attribute(ucs_sdk_object=equipment_system_io_controller, attribute_name="revision")
        self.serial = self.get_attribute(ucs_sdk_object=equipment_system_io_controller, attribute_name="serial")
        self.vendor = self.get_attribute(ucs_sdk_object=equipment_system_io_controller, attribute_name="vendor")

        UcsSystemInventoryObject.__init__(self, parent=parent, ucs_sdk_object=equipment_system_io_controller)

    def _get_ports(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsSystemSiocPort,
                                                                  parent=self)
        elif self._inventory.load_from == "file" and "ports" in self._ucs_sdk_object:
            return [UcsSystemSiocPort(self, port) for port in self._ucs_sdk_object["ports"]]
        else:
            return []


class UcsImcSioc(UcsSioc, UcsImcInventoryObject):
    def __init__(self, parent=None, equipment_system_io_controller=None):
        UcsSioc.__init__(self, parent=parent, equipment_system_io_controller=equipment_system_io_controller)
        UcsImcInventoryObject.__init__(self, parent=parent, ucs_sdk_object=equipment_system_io_controller)

        self.sku = self.get_attribute(ucs_sdk_object=equipment_system_io_controller, attribute_name="pid",
                                      attribute_secondary_name="sku")

        self.nvme_drives = self._get_nvme_drives()

        if self._inventory.load_from == "live":
            self.firmware_version = None
            self.model = None
            self.serial = None
            self.vendor = None
            self._get_details()

            if self.sku is None and self.model not in ["NA", "N/A"]:
                self.sku = self.model

        elif self._inventory.load_from == "file":
            for attribute in ["firmware_version", "model", "serial", "vendor"]:
                setattr(self, attribute, None)
                if attribute in equipment_system_io_controller:
                    setattr(self, attribute, self.get_attribute(ucs_sdk_object=equipment_system_io_controller,
                                                                attribute_name=attribute))

    def _get_details(self):
        if self._inventory.load_from == "live":
            equipment_shared_io_module_list = []
            mgmt_controller_list = []
            pci_equip_slot_list = []

            # We use the mgmtController object to get more details
            if "mgmtController" in self._inventory.sdk_objects.keys():
                if self._inventory.sdk_objects["mgmtController"] is not None:
                    # We filter out SDK objects that are not under this Dn
                    for sdk_object in self._inventory.sdk_objects["mgmtController"]:
                        if self.dn + "/" in sdk_object.dn:
                            mgmt_controller_list.append(sdk_object)

                    if len(mgmt_controller_list) != 1:
                        self.logger(level="debug",
                                    message="Could not find unique mgmtController for SIOC " + self.id)
                    else:
                        self.model = mgmt_controller_list[0].model
                        self.serial = mgmt_controller_list[0].serial
                        self.vendor = mgmt_controller_list[0].vendor

            # In case SIOC is a UCSC-C3260-SIOC we can use the equipmentSharedIOModule object to get more details
            if "equipmentSharedIOModule" in self._inventory.sdk_objects.keys():
                if self._inventory.sdk_objects["equipmentSharedIOModule"] is not None:
                    # We filter out SDK objects that are not under this Dn
                    for sdk_object in self._inventory.sdk_objects["equipmentSharedIOModule"]:
                        if self.dn + "/" in sdk_object.dn:
                            equipment_shared_io_module_list.append(sdk_object)

                    if len(equipment_shared_io_module_list) != 1:
                        self.logger(level="debug",
                                    message="Could not find unique equipmentSharedIOModule for SIOC " + self.id)
                    else:
                        self.firmware_version = equipment_shared_io_module_list[0].current_firmware_version
                        self.model = equipment_shared_io_module_list[0].product_id
                        self.serial = equipment_shared_io_module_list[0].serial_number
                        self.vendor = equipment_shared_io_module_list[0].vendor

            # In case we still don't have the model information, we use pciEquipSlot object to get more details
            if self.model in ["NA", "N/A"]:
                if "pciEquipSlot" in self._inventory.sdk_objects.keys():
                    if self._inventory.sdk_objects["pciEquipSlot"] is not None:
                        # We filter out SDK objects that are not under this Dn
                        for sdk_object in self._inventory.sdk_objects["pciEquipSlot"]:
                            if "SIOC" in sdk_object.model and self.id == sdk_object.id:
                                pci_equip_slot_list.append(sdk_object)

                        if len(pci_equip_slot_list) != 1:
                            self.logger(level="debug",
                                        message="Could not find unique pciEquipSlot for SIOC " + self.id)
                        else:
                            self.model = pci_equip_slot_list[0].model

    def _get_nvme_drives(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsImcSiocStorageNvmeDrive,
                                                                  parent=self)
        elif self._inventory.load_from == "file" and "nvme_drives" in self._ucs_sdk_object:
            return [UcsImcSiocStorageNvmeDrive(self, nvme_drive) for nvme_drive in self._ucs_sdk_object["nvme_drives"]]
        else:
            return []
