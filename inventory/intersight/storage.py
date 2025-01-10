# coding: utf-8
# !/usr/bin/env python

""" storage.py: Easy UCS Deployment Tool """
from inventory.generic.storage import GenericStorageController, GenericStorageRaidBattery, GenericStorageLocalDisk
from inventory.intersight.object import IntersightInventoryObject


class IntersightStorageController(GenericStorageController, IntersightInventoryObject):
    def __init__(self, parent=None, storage_controller=None):
        GenericStorageController.__init__(self, parent=parent)
        IntersightInventoryObject.__init__(self, parent=parent, sdk_object=storage_controller)

        self.id = self.get_attribute(attribute_name="controller_id", attribute_secondary_name="id")
        self.model = self.get_attribute(attribute_name="model")
        self.pci_slot = self.get_attribute(attribute_name="pci_slot")
        self.raid_support = self.get_attribute(attribute_name="raid_support")
        self.revision = self.get_attribute(attribute_name="revision")
        self.serial = self.get_attribute(attribute_name="serial")
        self.type = self.get_attribute(attribute_name="type")
        self.vendor = self.get_attribute(attribute_name="vendor")

        self.disks = self._get_disks()
        self.storage_raid_batteries = self._get_storage_raid_batteries()

        if self._inventory.load_from == "live":
            self.sku = self.model
            self.firmware_version = self._determine_firmware_version(filter_attr="dn", filter_value="-system")

            if not self.type:
                # Fix for case where controller type is not set in the backend
                if self.pci_slot == "SLOT-HBA":
                    self.type = "HBA"
                elif self.model == "Cisco 12G SAS Modular Raid Controller":
                    self.type = "RAID"

        elif self._inventory.load_from == "file":
            for attribute in ["firmware_version", "sku"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

    def _get_disks(self):
        if self._inventory.load_from == "live":
            return self.get_inventory_objects_from_ref(
                ref=self._object.physical_disks, object_class=IntersightStorageLocalDisk, parent=self)
        elif self._inventory.load_from == "file" and "disks" in self._object:
            return [IntersightStorageLocalDisk(self, disk) for disk in self._object["disks"]]
        else:
            return []

    def _get_storage_raid_batteries(self):
        if self._inventory.load_from == "live":
            return self.get_inventory_objects_from_ref(
                ref=self._object.backup_battery_unit, object_class=IntersightStorageRaidBattery, parent=self)
        elif self._inventory.load_from == "file" and "storage_raid_batteries" in self._object:
            return [IntersightStorageRaidBattery(self, battery) for battery in self._object["storage_raid_batteries"]]
        else:
            return []


class IntersightStorageControllerNvmeDrive(GenericStorageLocalDisk, IntersightInventoryObject):
    def __init__(self, parent=None, storage_local_disk=None):
        GenericStorageLocalDisk.__init__(self, parent=parent)
        IntersightInventoryObject.__init__(self, parent=parent, sdk_object=storage_local_disk)

        self.block_size = self.get_attribute(attribute_name="block_size", attribute_type="int")
        self.block_size_physical = self.get_attribute(attribute_name="physical_block_size",
                                                      attribute_secondary_name="block_size_physical",
                                                      attribute_type="int")
        self.bootable = self.get_attribute(attribute_name="bootable")
        self.connection_protocol = self.get_attribute(attribute_name="protocol",
                                                      attribute_secondary_name="connection_protocol")
        self.drive_state = self.get_attribute(attribute_name="drive_state")
        self.drive_type = self.get_attribute(attribute_name="type", attribute_secondary_name="drive_type")
        self.id = self.get_attribute(attribute_name="disk_id", attribute_secondary_name="id")
        self.firmware_version = self.get_attribute(attribute_name="drive_firmware",
                                                   attribute_secondary_name="firmware_version")
        self.life_left_in_percent = self.get_attribute(attribute_name="percent_life_left",
                                                       attribute_secondary_name="life_left_in_percent",
                                                       attribute_type="int")
        self.link_speed = self.get_attribute(attribute_name="link_speed")
        self.model = self.get_attribute(attribute_name="model")
        self.name = self.get_attribute(attribute_name="name")
        self.number_of_blocks = self.get_attribute(attribute_name="num_blocks",
                                                   attribute_secondary_name="number_of_blocks", attribute_type="int")
        self.operability = self.get_attribute(attribute_name="operability")
        self.part_number = self.get_attribute(attribute_name="part_number")
        self.pci_slot = None
        self.power_cycle_count = self.get_attribute(attribute_name="power_cycle_count", attribute_type="int")
        self.power_on_hours = self.get_attribute(attribute_name="power_on_hours", attribute_type="int")
        self.revision = self.get_attribute(attribute_name="revision")
        self.self_encrypting_drive = self.get_attribute(attribute_name="fde_capable",
                                                        attribute_secondary_name="self_encrypting_drive")
        self.serial = self.get_attribute(attribute_name="serial")
        self.size = self.get_attribute(attribute_name="size", attribute_type="int")
        self.size_raw = self.get_attribute(attribute_name="raw_size", attribute_secondary_name="size_raw",
                                           attribute_type="int")
        self.sku = self.get_attribute(attribute_name="pid", attribute_secondary_name="sku")
        self.slot_type = None
        self.vendor = self.get_attribute(attribute_name="vendor")
        self.wear_status_in_days = self.get_attribute(attribute_name="wear_status_in_days", attribute_type="int")

        if self._inventory.load_from == "live":
            self.firmware_version = self._determine_firmware_version()
            self.locator_led_status = self._determine_locator_led_status()
            self._format_link_speed()

            if self.model == self.sku:
                if " - " in self._object.name:
                    # Model info is same as SKU. Real model info is stored in "Name" field, alongside description.
                    self.model = self._object.name.split(" - ")[0]
                    self.name = self._object.description
                elif not self._object.name and self._object.description:
                    # Name field is empty. Using description field for Name contents
                    self.name = self._object.description

            # We need to find the "storage.Controller" object that corresponds to this NVMe drive for additional info
            storage_controller = self.get_inventory_objects_from_ref(ref=self._object.storage_controller)
            if len(storage_controller) == 1:
                self.pci_slot = storage_controller[0].pci_slot

            self._determine_nvme_slot_type()
            self._determine_size_and_rpm(self.name)
            if not self.size_marketing:
                if self.block_size not in [None, 0] and self.number_of_blocks not in [None, 0]:
                    self.size_marketing = int((self.block_size * self.number_of_blocks) / 1000000000)
                elif self.size:
                    self.size_marketing = int(self.size / 1000)

                self._format_size_marketing()

        elif self._inventory.load_from == "file":
            for attribute in ["firmware_version", "locator_led_status", "pci_slot", "size_marketing", "slot_type"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))


class IntersightStorageLocalDisk(GenericStorageLocalDisk, IntersightInventoryObject):
    def __init__(self, parent=None, storage_local_disk=None):
        GenericStorageLocalDisk.__init__(self, parent=parent)
        IntersightInventoryObject.__init__(self, parent=parent, sdk_object=storage_local_disk)

        self.block_size = self.get_attribute(attribute_name="block_size", attribute_type="int")
        self.block_size_physical = self.get_attribute(attribute_name="physical_block_size",
                                                      attribute_secondary_name="block_size_physical",
                                                      attribute_type="int")
        self.bootable = self.get_attribute(attribute_name="bootable")
        self.connection_protocol = self.get_attribute(attribute_name="protocol",
                                                      attribute_secondary_name="connection_protocol")
        self.drive_state = self.get_attribute(attribute_name="drive_state")
        self.drive_type = self.get_attribute(attribute_name="type", attribute_secondary_name="drive_type")
        self.id = self.get_attribute(attribute_name="disk_id", attribute_secondary_name="id")
        self.firmware_version = self.get_attribute(attribute_name="drive_firmware",
                                                   attribute_secondary_name="firmware_version")
        self.life_left_in_percent = self.get_attribute(attribute_name="percent_life_left",
                                                       attribute_secondary_name="life_left_in_percent",
                                                       attribute_type="int")
        self.link_speed = self.get_attribute(attribute_name="link_speed")
        self.model = self.get_attribute(attribute_name="model")
        self.name = self.get_attribute(attribute_name="name")
        self.number_of_blocks = self.get_attribute(attribute_name="num_blocks",
                                                   attribute_secondary_name="number_of_blocks", attribute_type="int")
        self.operability = self.get_attribute(attribute_name="operability")
        self.part_number = self.get_attribute(attribute_name="part_number")
        self.power_cycle_count = self.get_attribute(attribute_name="power_cycle_count", attribute_type="int")
        self.power_on_hours = self.get_attribute(attribute_name="power_on_hours", attribute_type="int")
        self.revision = self.get_attribute(attribute_name="revision")
        self.self_encrypting_drive = self.get_attribute(attribute_name="fde_capable",
                                                        attribute_secondary_name="self_encrypting_drive")
        self.serial = self.get_attribute(attribute_name="serial")
        self.size = self.get_attribute(attribute_name="size", attribute_type="int")
        self.size_raw = self.get_attribute(attribute_name="raw_size", attribute_secondary_name="size_raw",
                                           attribute_type="int")
        self.sku = self.get_attribute(attribute_name="pid", attribute_secondary_name="sku")
        self.vendor = self.get_attribute(attribute_name="vendor")
        self.wear_status_in_days = self.get_attribute(attribute_name="wear_status_in_days", attribute_type="int")

        if self._inventory.load_from == "live":
            self.firmware_version = self._determine_firmware_version()
            self.locator_led_status = self._determine_locator_led_status()
            self._format_link_speed()

            if self.model == self.sku:
                if " - " in self._object.name:
                    # Model info is same as SKU. Real model info is stored in "Name" field, alongside description.
                    self.model = self._object.name.split(" - ")[0]
                    self.name = self._object.description
                elif not self._object.name and self._object.description:
                    # Name field is empty. Using description field for Name contents
                    self.name = self._object.description
                elif not self.name:
                    # We store the model info as the name if it is empty
                    self.name = self.model

                if self.sku and not any(
                        self.sku.startswith(x) for x in ["A03-", "N20-", "R200-", "R2XX-", "UCS-", "UCSX-"]):
                    # SKU is not a correct UCS SKU
                    self.sku = None

            self._determine_size_and_rpm(self.name)
            if not self.size_marketing:
                if self.block_size not in [None, 0] and self.number_of_blocks not in [None, 0]:
                    self.size_marketing = int((self.block_size * self.number_of_blocks) / 1000000000)

                    self._format_size_marketing()

        elif self._inventory.load_from == "file":
            for attribute in ["firmware_version", "locator_led_status", "size_marketing"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))


class IntersightStorageRaidBattery(GenericStorageRaidBattery, IntersightInventoryObject):
    def __init__(self, parent=None, storage_battery_backup_unit=None):
        GenericStorageRaidBattery.__init__(self, parent=parent)
        IntersightInventoryObject.__init__(self, parent=parent, sdk_object=storage_battery_backup_unit)

        self.battery_status = self.get_attribute(attribute_name="status", attribute_secondary_name="battery_status")
        self.battery_type = self.get_attribute(attribute_name="type", attribute_secondary_name="battery_type")
        self.capacity_percentage = self.get_attribute(attribute_name="capacitance_in_percent",
                                                      attribute_secondary_name="capacity_percentage")
        self.model = self.get_attribute(attribute_name="model")
        self.name = self.get_attribute(attribute_name="device_name", attribute_secondary_name="name")
        self.revision = self.get_attribute(attribute_name="revision")
        self.serial = self.get_attribute(attribute_name="serial")
        self.temperature = self.get_attribute(attribute_name="temperature_in_cel",
                                              attribute_secondary_name="temperature")
        self.vendor = self.get_attribute(attribute_name="vendor")
