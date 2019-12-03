# coding: utf-8
# !/usr/bin/env python

""" storage.py: Easy UCS Deployment Tool """
from easyucs import __author__, __copyright__,  __version__, __status__


import math
import re
from easyucs.inventory.object import GenericUcsInventoryObject, UcsImcInventoryObject, UcsSystemInventoryObject


class UcsStorageController(GenericUcsInventoryObject):
    _UCS_SDK_OBJECT_NAME = "storageController"

    def __init__(self, parent=None, storage_controller=None):
        GenericUcsInventoryObject.__init__(self, parent=parent, ucs_sdk_object=storage_controller)

        self.id = self.get_attribute(ucs_sdk_object=storage_controller, attribute_name="id")
        self.model = self.get_attribute(ucs_sdk_object=storage_controller, attribute_name="model")
        self.pci_slot = self.get_attribute(ucs_sdk_object=storage_controller, attribute_name="pci_slot")
        self.raid_support = self.get_attribute(ucs_sdk_object=storage_controller, attribute_name="raid_support")
        self.serial = self.get_attribute(ucs_sdk_object=storage_controller, attribute_name="serial")
        self.type = self.get_attribute(ucs_sdk_object=storage_controller, attribute_name="type")
        self.vendor = self.get_attribute(ucs_sdk_object=storage_controller, attribute_name="vendor")

        self.disks = self._get_disks()
        self.storage_enclosures = self._get_storage_enclosures()
        self.storage_raid_batteries = self._get_storage_raid_batteries()

    def _get_disks(self):
        return []

    def _get_storage_enclosures(self):
        return []

    def _get_storage_raid_batteries(self):
        return []


class UcsSystemStorageController(UcsStorageController, UcsSystemInventoryObject):
    _UCS_SDK_CATALOG_OBJECT_NAME = "equipmentLocalDiskControllerCapProvider"
    _UCS_SDK_FIRMWARE_RUNNING_SUFFIX = "/fw-system"

    def __init__(self, parent=None, storage_controller=None):
        UcsStorageController.__init__(self, parent=parent, storage_controller=storage_controller)

        self.device_raid_support = self.get_attribute(ucs_sdk_object=storage_controller,
                                                      attribute_name="device_raid_support")
        self.revision = self.get_attribute(ucs_sdk_object=storage_controller, attribute_name="revision")

        UcsSystemInventoryObject.__init__(self, parent=parent, ucs_sdk_object=storage_controller)

        if self._inventory.load_from == "live":
            self.driver_name = None
            self.driver_version = None
        elif self._inventory.load_from == "file":
            for attribute in ["driver_name", "driver_version"]:
                setattr(self, attribute, None)
                if attribute in storage_controller:
                    setattr(self, attribute, self.get_attribute(ucs_sdk_object=storage_controller,
                                                                attribute_name=attribute))

    def _get_disks(self):
        if self._inventory.load_from == "live":
            # Fetch disks under storage controller only in case we are not in a S3260 chassis
            if self._parent.model not in ["UCSC-C3X60-SVRNB", "UCSC-C3K-M4SRB", "UCS-S3260-M5SRB"]:
                return self._inventory.get_inventory_objects_under_dn(dn=self.dn,
                                                                      object_class=UcsSystemStorageLocalDisk,
                                                                      parent=self)
            else:
                return []
        elif self._inventory.load_from == "file" and "disks" in self._ucs_sdk_object:
            return [UcsSystemStorageLocalDisk(self, storage_local_disk) for storage_local_disk in
                    self._ucs_sdk_object["disks"]]
        else:
            return []

    def _get_storage_enclosures(self):
        if self._inventory.load_from == "live":
            # Fetch storage enclosures under storage controller only in case we are not in a S3260 chassis
            if self._parent.model not in ["UCSC-C3X60-SVRNB", "UCSC-C3K-M4SRB", "UCS-S3260-M5SRB"]:
                return self._inventory.get_inventory_objects_under_dn(dn=self.dn,
                                                                      object_class=UcsSystemStorageEnclosure,
                                                                      parent=self)
            else:
                return []
        elif self._inventory.load_from == "file" and "storage_enclosures" in self._ucs_sdk_object:
            return [UcsSystemStorageEnclosure(self, storage_enclosure) for storage_enclosure in
                    self._ucs_sdk_object["storage_enclosures"]]
        else:
            return []

    def _get_storage_raid_batteries(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsSystemStorageRaidBattery,
                                                                  parent=self)
        elif self._inventory.load_from == "file" and "storage_raid_batteries" in self._ucs_sdk_object:
            return [UcsSystemStorageRaidBattery(self, storage_raid_battery) for storage_raid_battery in
                    self._ucs_sdk_object["storage_raid_batteries"]]
        else:
            return []


class UcsImcStorageController(UcsStorageController, UcsImcInventoryObject):
    _UCS_SDK_CATALOG_OBJECT_NAME = "pidCatalogPCIAdapter"
    _UCS_SDK_CATALOG_IDENTIFY_ATTRIBUTE = "slot"
    _UCS_SDK_OBJECT_IDENTIFY_ATTRIBUTE = "pci_slot"

    def __init__(self, parent=None, storage_controller=None):
        UcsStorageController.__init__(self, parent=parent, storage_controller=storage_controller)
        UcsImcInventoryObject.__init__(self, parent=parent, ucs_sdk_object=storage_controller)

    def _get_disks(self):
        if self._inventory.load_from == "live":
            # Fetch disks under storage controller only in case we are not in a S3260 chassis
            if self._parent.model not in ["UCSC-C3X60-SVRNB", "UCSC-C3K-M4SRB", "UCS-S3260-M5SRB"]:
                return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsImcStorageLocalDisk,
                                                                      parent=self)
            else:
                return []
        elif self._inventory.load_from == "file" and "disks" in self._ucs_sdk_object:
            return [UcsImcStorageLocalDisk(self, storage_local_disk) for storage_local_disk in
                    self._ucs_sdk_object["disks"]]
        else:
            return []

    def _get_storage_raid_batteries(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsImcStorageRaidBattery,
                                                                  parent=self)
        elif self._inventory.load_from == "file" and "storage_raid_batteries" in self._ucs_sdk_object:
            return [UcsImcStorageRaidBattery(self, storage_raid_battery) for storage_raid_battery in
                    self._ucs_sdk_object["storage_raid_batteries"]]
        else:
            return []


class UcsStorageEnclosure(GenericUcsInventoryObject):
    _UCS_SDK_OBJECT_NAME = "storageEnclosure"

    def __init__(self, parent=None, storage_enclosure=None):
        GenericUcsInventoryObject.__init__(self, parent=parent, ucs_sdk_object=storage_enclosure)

        self.disks = self._get_disks()

    def _get_disks(self):
        return []


class UcsSystemStorageEnclosure(UcsStorageEnclosure, UcsSystemInventoryObject):
    def __init__(self, parent=None, storage_enclosure=None):
        UcsStorageEnclosure.__init__(self, parent=parent, storage_enclosure=storage_enclosure)

        self.chassis_id = self.get_attribute(ucs_sdk_object=storage_enclosure, attribute_name="chassis_id")
        self.descr = self.get_attribute(ucs_sdk_object=storage_enclosure, attribute_name="descr")
        self.id = self.get_attribute(ucs_sdk_object=storage_enclosure, attribute_name="id")
        self.model = self.get_attribute(ucs_sdk_object=storage_enclosure, attribute_name="model")
        self.num_slots = self.get_attribute(ucs_sdk_object=storage_enclosure, attribute_name="num_slots")
        self.presence = self.get_attribute(ucs_sdk_object=storage_enclosure, attribute_name="presence")
        self.revision = self.get_attribute(ucs_sdk_object=storage_enclosure, attribute_name="revision")
        self.server_id = self.get_attribute(ucs_sdk_object=storage_enclosure, attribute_name="server_id")
        self.type = self.get_attribute(ucs_sdk_object=storage_enclosure, attribute_name="type")
        self.vendor = self.get_attribute(ucs_sdk_object=storage_enclosure, attribute_name="vendor")

        UcsSystemInventoryObject.__init__(self, parent=parent, ucs_sdk_object=storage_enclosure)

        if self._parent.model in ["UCSC-C3X60", "UCSC-C3X60-BASE", "UCSS-S3260", "UCSS-S3260-BASE"]:
            if self.descr == "Embedded Storage Enclosure":
                self.type = "top-load"
            elif self.descr == "Dedicated Rear SSD Enclosure":
                self.type = "rear-ssd"

    def _get_disks(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsSystemStorageLocalDisk,
                                                                  parent=self)
        elif self._inventory.load_from == "file" and "disks" in self._ucs_sdk_object:
            return [UcsSystemStorageLocalDisk(self, storage_local_disk) for storage_local_disk in
                    self._ucs_sdk_object["disks"]]
        else:
            return []


class UcsImcStorageEnclosure(UcsStorageEnclosure, UcsImcInventoryObject):
    def __init__(self, parent=None, storage_enclosure=None):
        UcsStorageEnclosure.__init__(self, parent=parent, storage_enclosure=storage_enclosure)

        self.descr = self.get_attribute(ucs_sdk_object=storage_enclosure, attribute_name="description",
                                        attribute_secondary_name="descr")

        UcsImcInventoryObject.__init__(self, parent=parent, ucs_sdk_object=storage_enclosure)

        if self._inventory.load_from == "live":
            # Clean up and set attributes of Embbedded Storage Enclosure for S3260
            if self._parent.model in ["UCSC-C3X60", "UCSC-C3X60-BASE", "UCSS-S3260", "UCSS-S3260-BASE"]:
                if self.descr == "Chassis scope dynamic storage management":
                    self.descr = "Embedded Storage Enclosure"
                    self.type = "top-load"
                    self.num_slots = "56"
        elif self._inventory.load_from == "file":
            for attribute in ["type", "num_slots"]:
                setattr(self, attribute, None)
                if attribute in storage_enclosure:
                    setattr(self, attribute, self.get_attribute(ucs_sdk_object=storage_enclosure,
                                                                attribute_name=attribute))
            pass

    def _get_disks(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsImcStorageEnclosureDisk,
                                                                  parent=self)
        elif self._inventory.load_from == "file" and "disks" in self._ucs_sdk_object:
            return [UcsImcStorageLocalDisk(self, storage_local_disk) for storage_local_disk in
                    self._ucs_sdk_object["disks"]]
        else:
            return []


class UcsStorageEnclosureDisk(GenericUcsInventoryObject):
    _UCS_SDK_OBJECT_NAME = "storageEnclosureDisk"

    def __init__(self, parent=None, storage_enclosure_disk=None):
        GenericUcsInventoryObject.__init__(self, parent=parent, ucs_sdk_object=storage_enclosure_disk)

        self.serial = self.get_attribute(ucs_sdk_object=storage_enclosure_disk, attribute_name="serial")
        self.vendor = self.get_attribute(ucs_sdk_object=storage_enclosure_disk, attribute_name="vendor")


class UcsImcStorageEnclosureDisk(UcsStorageEnclosureDisk, UcsImcInventoryObject):
    def __init__(self, parent=None, storage_enclosure_disk=None):
        UcsStorageEnclosureDisk.__init__(self, parent=parent, storage_enclosure_disk=storage_enclosure_disk)

        self.block_size = self.get_attribute(ucs_sdk_object=storage_enclosure_disk, attribute_name="blocksize",
                                             attribute_type="int")
        self.firmware_version = self.get_attribute(ucs_sdk_object=storage_enclosure_disk, attribute_name="revision",
                                                   attribute_secondary_name="firmware_version")
        self.id = self.get_attribute(ucs_sdk_object=storage_enclosure_disk, attribute_name="slot",
                                     attribute_secondary_name="id")
        self.model = self.get_attribute(ucs_sdk_object=storage_enclosure_disk, attribute_name="product_id",
                                        attribute_secondary_name="model")
        self.number_of_blocks = self.get_attribute(ucs_sdk_object=storage_enclosure_disk, attribute_name="blockcount",
                                                   attribute_secondary_name="number_of_blocks", attribute_type="int")
        self.size = self.get_attribute(ucs_sdk_object=storage_enclosure_disk, attribute_name="size")

        UcsImcInventoryObject.__init__(self, parent=parent, ucs_sdk_object=storage_enclosure_disk)

        if self._inventory.load_from == "live":
            # We try to find the matching storageLocalDisk to get more details
            storage_local_disk = self._find_corresponding_storage_local_disk()
            if storage_local_disk:
                # We create a UcsImcStorageLocalDisk object out of the storageLocalDisk so that we get all the details
                ucs_imc_storage_local_disk = UcsImcStorageLocalDisk(parent=self, storage_local_disk=storage_local_disk)

                self.bootable = ucs_imc_storage_local_disk.bootable
                self.connection_protocol = ucs_imc_storage_local_disk.connection_protocol
                self.drive_state = ucs_imc_storage_local_disk.drive_state
                self.drive_type = ucs_imc_storage_local_disk.drive_type
                self.link_speed = ucs_imc_storage_local_disk.link_speed
                self.rotational_speed_marketing = ucs_imc_storage_local_disk.rotational_speed_marketing
                self.self_encrypting_drive = ucs_imc_storage_local_disk.self_encrypting_drive
                self.size = ucs_imc_storage_local_disk.size
                self.size_marketing = ucs_imc_storage_local_disk.size_marketing
                self.size_raw = ucs_imc_storage_local_disk.size_raw
                self.sku = ucs_imc_storage_local_disk.sku
            else:
                self.bootable = None
                self.connection_protocol = None
                self.drive_state = None
                self.drive_type = None
                self.link_speed = None
                self.rotational_speed_marketing = None
                self.self_encrypting_drive = None
                self.size_marketing = None
                self.size_raw = None

                # We first clean up the "size" attribute
                if "TB" in self.size:
                    self.size = int(float(self.size.split(" ")[0]) * 1048576)
                elif "GB" in self.size:
                    self.size = int(float(self.size.split(" ")[0]) * 1024)
                else:
                    self.logger(level="debug",
                                message="Not sure about the size attribute of disk " + self.id + ": " + self.size)
                    self.size = int(float(self.size.split(" ")[0]))

                # We calculate the "size_marketing" attribute
                if self.block_size is not None and self.number_of_blocks is not None:
                    self.size_marketing = int((self.block_size * self.number_of_blocks) / 1000000000)
                    # Properly format size_marketing so that it fits the display on disk drives for the pictures
                    if self.size_marketing < 1000:
                        self.size_marketing = str(int(self.size_marketing)) + "GB"
                    elif self.size_marketing >= 1000:
                        if (self.size_marketing / 1000).is_integer():
                            self.size_marketing = str(int(self.size_marketing / 1000)) + "TB"
                        else:
                            if str(round(self.size_marketing / 1000, ndigits=1))[-2:] == ".0":
                                self.size_marketing = str(int(self.size_marketing / 1000)) + "TB"
                            else:
                                self.size_marketing = str(round(self.size_marketing / 1000, ndigits=1)) + "TB"

        elif self._inventory.load_from == "file":
            for attribute in ["bootable", "connection_protocol", "drive_state", "drive_type", "link_speed",
                              "number_of_blocks", "rotational_speed_marketing", "self_encrypting_drive",
                              "size_marketing", "size_raw"]:
                setattr(self, attribute, None)
                if attribute in storage_enclosure_disk:
                    setattr(self, attribute, self.get_attribute(ucs_sdk_object=storage_enclosure_disk,
                                                                attribute_name=attribute))

    def _find_corresponding_storage_local_disk(self):
        if "storageLocalDisk" not in self._inventory.sdk_objects.keys():
            return False

        # We check if we already have fetched the list of storageLocalDisk objects
        if self._inventory.sdk_objects["storageLocalDisk"] is not None:

            # We need to find the matching storageLocalDisk object
            storage_local_disk_list = [storage_local_disk for storage_local_disk in
                                       self._inventory.sdk_objects["storageLocalDisk"] if
                                       self.id == storage_local_disk.id and
                                       self.serial == storage_local_disk.drive_serial_number]
            if (len(storage_local_disk_list)) != 1:
                self.logger(level="debug",
                            message="Could not find the corresponding storageLocalDisk for object with DN " +
                                    self.dn + " of model \"" + self.model + "\" with ID " + self.id)
                self.logger(level="info", message="Details of disk with id " + self.id +
                                                  " are not available. Has disk been assigned to a server node?")
                return False
            else:
                return storage_local_disk_list[0]

        return False


class UcsStorageFlexFlashController(GenericUcsInventoryObject):
    _UCS_SDK_OBJECT_NAME = "storageFlexFlashController"

    def __init__(self, parent=None, storage_flexflash_controller=None):
        GenericUcsInventoryObject.__init__(self, parent=parent, ucs_sdk_object=storage_flexflash_controller)

        self.id = self.get_attribute(ucs_sdk_object=storage_flexflash_controller, attribute_name="id")
        self.vendor = self.get_attribute(ucs_sdk_object=storage_flexflash_controller, attribute_name="vendor")

        self.flexflash_cards = self._get_flexflash_cards()

    def _get_flexflash_cards(self):
        return []


class UcsSystemStorageFlexFlashController(UcsStorageFlexFlashController, UcsSystemInventoryObject):
    _UCS_SDK_FIRMWARE_RUNNING_SUFFIX = "/fw-system"

    def __init__(self, parent=None, storage_flexflash_controller=None):
        UcsStorageFlexFlashController.__init__(self, parent=parent,
                                               storage_flexflash_controller=storage_flexflash_controller)

        self.configured_mode = self.get_attribute(ucs_sdk_object=storage_flexflash_controller,
                                                  attribute_name="configured_mode")
        self.firmware_version = self.get_attribute(ucs_sdk_object=storage_flexflash_controller,
                                                   attribute_name="firmware_version")
        self.model = self.get_attribute(ucs_sdk_object=storage_flexflash_controller, attribute_name="model")
        self.operating_mode = self.get_attribute(ucs_sdk_object=storage_flexflash_controller,
                                                 attribute_name="operating_mode")
        self.physical_drive_count = self.get_attribute(ucs_sdk_object=storage_flexflash_controller,
                                                       attribute_name="physical_drive_count", attribute_type="int")
        self.revision = self.get_attribute(ucs_sdk_object=storage_flexflash_controller, attribute_name="revision")
        self.serial = self.get_attribute(ucs_sdk_object=storage_flexflash_controller, attribute_name="serial")
        self.virtual_drive_count = self.get_attribute(ucs_sdk_object=storage_flexflash_controller,
                                                      attribute_name="virtual_drive_count", attribute_type="int")

        UcsSystemInventoryObject.__init__(self, parent=parent, ucs_sdk_object=storage_flexflash_controller)

    def _get_flexflash_cards(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn,
                                                                  object_class=UcsSystemStorageFlexFlashCard,
                                                                  parent=self)
        elif self._inventory.load_from == "file" and "flexflash_cards" in self._ucs_sdk_object:
            return [UcsSystemStorageFlexFlashCard(self, storage_flexflash_card) for storage_flexflash_card in
                    self._ucs_sdk_object["flexflash_cards"]]
        else:
            return []


class UcsImcStorageFlexFlashController(UcsStorageFlexFlashController, UcsImcInventoryObject):
    def __init__(self, parent=None, storage_flexflash_controller=None):
        UcsStorageFlexFlashController.__init__(self, parent=parent,
                                               storage_flexflash_controller=storage_flexflash_controller)

        self.firmware_version = self.get_attribute(ucs_sdk_object=storage_flexflash_controller,
                                                   attribute_name="fw_version",
                                                   attribute_secondary_name="firmware_version")

        UcsImcInventoryObject.__init__(self, parent=parent, ucs_sdk_object=storage_flexflash_controller)

        if self._inventory.load_from == "live":
            self.configured_mode = None
            self.operating_mode = None
            self.physical_drive_count = None
            self.virtual_drive_count = None
            self._find_flexflash_controller_specs()
        elif self._inventory.load_from == "file":
            for attribute in ["configured_mode", "operating_mode", "physical_drive_count", "virtual_drive_count"]:
                setattr(self, attribute, None)
                if attribute in storage_flexflash_controller:
                    setattr(self, attribute, self.get_attribute(ucs_sdk_object=storage_flexflash_controller,
                                                                attribute_name=attribute))

    def _get_flexflash_cards(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsImcStorageFlexFlashCard,
                                                                  parent=self)
        elif self._inventory.load_from == "file" and "flexflash_cards" in self._ucs_sdk_object:
            return [UcsImcStorageFlexFlashCard(self, storage_flexflash_card) for storage_flexflash_card in
                    self._ucs_sdk_object["flexflash_cards"]]
        else:
            return []

    def _find_flexflash_controller_specs(self):
        if "storageFlexFlashControllerProps" not in self._inventory.sdk_objects.keys():
            return False

        # We check if we already have fetched the list of storageFlexFlashControllerProps objects
        if self._inventory.sdk_objects["storageFlexFlashControllerProps"] is not None:

            # We need to find the matching storageFlexFlashControllerProps object
            storage_flexflash_controller_props_list = [storage_flexflash_controller_props for
                                                       storage_flexflash_controller_props in
                                                       self._inventory.sdk_objects["storageFlexFlashControllerProps"] if
                                                       self.dn + "/" in storage_flexflash_controller_props.dn]
            if (len(storage_flexflash_controller_props_list)) != 1:
                self.logger(level="warning",
                            message="Could not find the appropriate FlexFlash controller details for object with DN " +
                                    self.dn + " of model \"" + self.model + "\" with ID " + self.id)
                return False
            else:
                self.configured_mode = storage_flexflash_controller_props_list[0].configured_mode
                self.operating_mode = storage_flexflash_controller_props_list[0].operating_mode
                self.physical_drive_count = int(storage_flexflash_controller_props_list[0].physical_drive_count)
                self.virtual_drive_count = int(storage_flexflash_controller_props_list[0].virtual_drive_count)
                return True

        return False


class UcsStorageFlexFlashCard(GenericUcsInventoryObject):
    def __init__(self, parent=None, storage_flexflash_card=None):
        GenericUcsInventoryObject.__init__(self, parent=parent, ucs_sdk_object=storage_flexflash_card)

        self.block_size = self.get_attribute(ucs_sdk_object=storage_flexflash_card, attribute_name="block_size")
        self.card_type = self.get_attribute(ucs_sdk_object=storage_flexflash_card, attribute_name="card_type")
        self.card_mode = self.get_attribute(ucs_sdk_object=storage_flexflash_card, attribute_name="card_mode")
        self.drives_enabled = self.get_attribute(ucs_sdk_object=storage_flexflash_card, attribute_name="drives_enabled")
        self.partition_count = self.get_attribute(ucs_sdk_object=storage_flexflash_card,
                                                  attribute_name="partition_count")
        self.slot_number = self.get_attribute(ucs_sdk_object=storage_flexflash_card, attribute_name="slot_number")


class UcsSystemStorageFlexFlashCard(UcsStorageFlexFlashCard, UcsSystemInventoryObject):
    _UCS_SDK_OBJECT_NAME = "storageFlexFlashCard"

    def __init__(self, parent=None, storage_flexflash_card=None):
        UcsStorageFlexFlashCard.__init__(self, parent=parent,
                                         storage_flexflash_card=storage_flexflash_card)

        self.capacity = self.get_attribute(ucs_sdk_object=storage_flexflash_card, attribute_name="size",
                                           attribute_secondary_name="capacity", attribute_type="int")
        self.card_state = self.get_attribute(ucs_sdk_object=storage_flexflash_card, attribute_name="card_state")
        self.card_health = self.get_attribute(ucs_sdk_object=storage_flexflash_card, attribute_name="card_health")
        self.model = self.get_attribute(ucs_sdk_object=storage_flexflash_card, attribute_name="model")
        self.revision = self.get_attribute(ucs_sdk_object=storage_flexflash_card, attribute_name="revision")
        self.serial = self.get_attribute(ucs_sdk_object=storage_flexflash_card, attribute_name="serial")
        self.sync_mode = self.get_attribute(ucs_sdk_object=storage_flexflash_card, attribute_name="card_sync",
                                            attribute_secondary_name="sync_mode")
        self.write_enabled = self.get_attribute(ucs_sdk_object=storage_flexflash_card, attribute_name="write_enable",
                                                attribute_secondary_name="write_enabled")

        UcsSystemInventoryObject.__init__(self, parent=parent, ucs_sdk_object=storage_flexflash_card)

        if self._inventory.load_from == "live":
            self.block_size = int(self.block_size)
            self.capacity_marketing = str(int(2 ** math.ceil(math.log2(self.capacity)) / 1024)) + "GB"

        elif self._inventory.load_from == "file":
            self.capacity_marketing = self.get_attribute(ucs_sdk_object=storage_flexflash_card,
                                                         attribute_name="capacity_marketing")


class UcsImcStorageFlexFlashCard(UcsStorageFlexFlashCard, UcsImcInventoryObject):
    _UCS_SDK_OBJECT_NAME = "storageFlexFlashPhysicalDrive"

    def __init__(self, parent=None, storage_flexflash_card=None):
        UcsStorageFlexFlashCard.__init__(self, parent=parent,
                                         storage_flexflash_card=storage_flexflash_card)

        self.capacity = self.get_attribute(ucs_sdk_object=storage_flexflash_card, attribute_name="capacity")
        self.card_state = self.get_attribute(ucs_sdk_object=storage_flexflash_card, attribute_name="card_status",
                                             attribute_secondary_name="card_state")
        self.card_health = self.get_attribute(ucs_sdk_object=storage_flexflash_card, attribute_name="health",
                                              attribute_secondary_name="card_health")
        self.model = self.get_attribute(ucs_sdk_object=storage_flexflash_card, attribute_name="product_name",
                                        attribute_secondary_name="model")
        self.revision = self.get_attribute(ucs_sdk_object=storage_flexflash_card, attribute_name="product_revision",
                                           attribute_secondary_name="revision")
        self.serial = self.get_attribute(ucs_sdk_object=storage_flexflash_card, attribute_name="serial_number",
                                         attribute_secondary_name="serial")
        self.sync_mode = self.get_attribute(ucs_sdk_object=storage_flexflash_card, attribute_name="sync_mode")
        self.write_enabled = self.get_attribute(ucs_sdk_object=storage_flexflash_card, attribute_name="write_enabled")

        UcsImcInventoryObject.__init__(self, parent=parent, ucs_sdk_object=storage_flexflash_card)

        if self._inventory.load_from == "live":
            if " MB" in self.capacity:
                self.capacity = int(self.capacity.split(" ")[0])
                self.capacity_marketing = str(int(2 ** math.ceil(math.log2(self.capacity)) / 1024)) + "GB"
            if " bytes" in self.block_size:
                self.block_size = int(self.block_size.split(" ")[0])

        elif self._inventory.load_from == "file":
            self.capacity_marketing = self.get_attribute(ucs_sdk_object=storage_flexflash_card,
                                                         attribute_name="capacity_marketing")


class UcsStorageLocalDisk(GenericUcsInventoryObject):
    _UCS_SDK_OBJECT_NAME = "storageLocalDisk"

    def __init__(self, parent=None, storage_local_disk=None):
        GenericUcsInventoryObject.__init__(self, parent=parent, ucs_sdk_object=storage_local_disk)

        self.id = self.get_attribute(ucs_sdk_object=storage_local_disk, attribute_name="id")
        self.link_speed = self.get_attribute(ucs_sdk_object=storage_local_disk, attribute_name="link_speed")
        self.vendor = self.get_attribute(ucs_sdk_object=storage_local_disk, attribute_name="vendor")


class UcsSystemStorageLocalDisk(UcsStorageLocalDisk, UcsSystemInventoryObject):
    _UCS_SDK_CATALOG_OBJECT_NAME = "equipmentLocalDiskCapProvider"
    _UCS_SDK_FIRMWARE_RUNNING_SUFFIX = "/fw-system"

    def __init__(self, parent=None, storage_local_disk=None):
        UcsStorageLocalDisk.__init__(self, parent=parent, storage_local_disk=storage_local_disk)

        self.block_size = self.get_attribute(ucs_sdk_object=storage_local_disk, attribute_name="block_size",
                                             attribute_type="int")
        self.block_size_catalog = None
        self.block_size_physical = None
        if self._inventory.load_from == "live":
            if storage_local_disk.physical_block_size is not None:
                if storage_local_disk.physical_block_size != "unknown":
                    self.block_size_physical = int(storage_local_disk.physical_block_size)
                else:
                    self.block_size_physical = 0
        elif self._inventory.load_from == "file":
            self.block_size_physical = self.get_attribute(ucs_sdk_object=storage_local_disk,
                                                          attribute_name="block_size_physical", attribute_type="int")
        self.bootable = self.get_attribute(ucs_sdk_object=storage_local_disk, attribute_name="bootable")
        self.cache_size = None
        self.capacity_catalog = None
        self.connection_protocol = self.get_attribute(ucs_sdk_object=storage_local_disk,
                                                      attribute_name="connection_protocol")
        self.drive_state = self.get_attribute(ucs_sdk_object=storage_local_disk, attribute_name="disk_state",
                                              attribute_secondary_name="drive_state")
        self.drive_type = self.get_attribute(ucs_sdk_object=storage_local_disk, attribute_name="device_type",
                                             attribute_secondary_name="drive_type")
        self.firmware_version = self.get_attribute(ucs_sdk_object=storage_local_disk, attribute_name="device_version",
                                                   attribute_secondary_name="firmware_version")
        self.locator_led_status = None
        self.model = self.get_attribute(ucs_sdk_object=storage_local_disk, attribute_name="model")
        self.number_of_blocks = self.get_attribute(ucs_sdk_object=storage_local_disk, attribute_name="number_of_blocks",
                                                   attribute_type="int")
        self.number_of_blocks_catalog = None
        self.operability = self.get_attribute(ucs_sdk_object=storage_local_disk, attribute_name="operability")
        self.rotational_speed = None
        self.rotational_speed_marketing = None
        self.self_encrypting_drive = None
        self.serial = self.get_attribute(ucs_sdk_object=storage_local_disk, attribute_name="serial")
        self.size = self.get_attribute(ucs_sdk_object=storage_local_disk, attribute_name="size", attribute_type="int")
        self.size_marketing = None
        self.size_raw = self.get_attribute(ucs_sdk_object=storage_local_disk, attribute_name="raw_size",
                                           attribute_secondary_name="size_raw", attribute_type="int")
        self.revision = self.get_attribute(ucs_sdk_object=storage_local_disk, attribute_name="revision")

        if self.link_speed == "1-5-gbps":
            self.link_speed = float(1.5)
        elif self.link_speed == "3-gbps":
            self.link_speed = float(3)
        elif self.link_speed == "6-gbps":
            self.link_speed = float(6)
        elif self.link_speed == "12-gbps":
            self.link_speed = float(12)

        UcsSystemInventoryObject.__init__(self, parent=parent, ucs_sdk_object=storage_local_disk)

        if self._inventory.load_from == "live":
            self.locator_led_status = self._determine_locator_led_status()
            self.size_marketing = None
            self.rotational_speed_marketing = None

            if self._find_drive_specs_from_catalog():
                self.size_marketing = int((self.block_size_catalog * self.number_of_blocks_catalog) / 1000000000)
                if self.size_marketing == 0:
                    # We are facing an improperly referenced drive in the catalog (e.g. Micron_P400e)
                    # Trying to set the size without using the catalog information
                    if self.block_size is not None and self.number_of_blocks is not None:
                        self.size_marketing = int((self.block_size * self.number_of_blocks) / 1000000000)
            else:
                if self.block_size is not None and self.number_of_blocks is not None:
                    self.size_marketing = int((self.block_size * self.number_of_blocks) / 1000000000)

            # Properly format size_marketing so that it fits the display on disk drives for the pictures
            if self.size_marketing is not None:
                if self.size_marketing < 1000:
                    self.size_marketing = str(int(self.size_marketing)) + "GB"
                elif self.size_marketing >= 1000:
                    if (self.size_marketing / 1000).is_integer():
                        self.size_marketing = str(int(self.size_marketing / 1000)) + "TB"
                    else:
                        if str(round(self.size_marketing / 1000, ndigits=1))[-2:] == ".0":
                            self.size_marketing = str(int(self.size_marketing / 1000)) + "TB"
                        else:
                            self.size_marketing = str(round(self.size_marketing / 1000, ndigits=1)) + "TB"

            # Manual adjustment for wrong round up of some drives
            if self.size_marketing == "147GB":
                self.size_marketing = "146GB"
            elif self.size_marketing == "98GB":
                self.size_marketing = "100GB"
            elif self.size_marketing == "118GB":
                self.size_marketing = "120GB"
            elif self.size_marketing == "998GB":
                self.size_marketing = "1TB"

            if self.rotational_speed is not None:
                self.rotational_speed_marketing = self.rotational_speed

                # Properly format rotational_speed_marketing so that it fits the display on disk drives for the pictures
                if self.rotational_speed_marketing == 15000:
                    self.rotational_speed_marketing = "15K"
                elif self.rotational_speed_marketing == 10000:
                    self.rotational_speed_marketing = "10K"
                elif self.rotational_speed_marketing == 7200:
                    self.rotational_speed_marketing = "7.2K"
                elif self.rotational_speed_marketing == 5400:
                    self.rotational_speed_marketing = "5.4K"
                elif self.rotational_speed_marketing == 0:
                    self.rotational_speed_marketing = None
                # Handle catalog issues
                elif self.rotational_speed_marketing in [10, 10025, 10520]:
                    self.rotational_speed_marketing = "10K"
                elif self.rotational_speed_marketing == 7202:
                    self.rotational_speed_marketing = "7.2K"

            # Manual adjustments for catalog SKU with double values like "UCS-SD100G0KA2-G/UCS-SD100G0KA2-S"
            if self.sku == "UCS-SD100G0KA2-G/UCS-SD100G0KA2-S":
                # Determining if parent server is a B230 M2 blade
                if hasattr(self._parent._parent, "model"):
                    if self._parent._parent.model == "B230-BASE-M2":
                        self.sku = "UCS-SD100G0KA2-S"
                    else:
                        self.sku = "UCS-SD100G0KA2-G"

            elif self.sku == "UCS-SD400G0KA2-G/UCS-SD400G0KA2-S":
                # Determining if parent server is a B230 M2 blade
                if hasattr(self._parent._parent, "model"):
                    if self._parent._parent.model == "B230-BASE-M2":
                        self.sku = "UCS-SD400G0KA2-S"
                    else:
                        self.sku = "UCS-SD400G0KA2-G"

            elif self.sku == "UCS-SSD100GI1F105 / UCS-SD100G0KA2-E":
                # Determining if parent server is a B230 M2 blade
                if hasattr(self._parent._parent, "model"):
                    if self._parent._parent.model == "B230-BASE-M2":
                        self.sku = "UCS-SSD100GI1F105"
                    else:
                        self.sku = "UCS-SD100G0KA2-E"

            elif self.sku == "UCS-SD200G0KA2-T / UCS-SD200G0KA2-E":
                # Determining if parent server is a B230 M2 blade
                if hasattr(self._parent._parent, "model"):
                    if self._parent._parent.model == "B230-BASE-M2":
                        self.sku = "UCS-SD200G0KA2-T"
                    else:
                        self.sku = "UCS-SD200G0KA2-E"

            elif self.sku == "UCS-SD300G0KA2-T / UCS-SD300G0KA2-E":
                # Determining if parent server is a B230 M2 blade
                if hasattr(self._parent._parent, "model"):
                    if self._parent._parent.model == "B230-BASE-M2":
                        self.sku = "UCS-SD300G0KA2-T"
                    else:
                        self.sku = "UCS-SD300G0KA2-E"

        elif self._inventory.load_from == "file":
            for attribute in ["block_size_catalog", "cache_size", "capacity_catalog", "locator_led_status",
                              "number_of_blocks_catalog", "rotational_speed", "rotational_speed_marketing",
                              "self_encrypting_drive", "size_marketing"]:
                setattr(self, attribute, None)
                if attribute in storage_local_disk:
                    setattr(self, attribute, self.get_attribute(ucs_sdk_object=storage_local_disk,
                                                                attribute_name=attribute))

    def _find_drive_specs_from_catalog(self):
        if "equipmentLocalDiskDef" not in self._inventory.sdk_objects.keys():
            return False

        # We check if we already have fetched the list of equipmentLocalDiskDef catalog objects and the CapProvider
        if self._inventory.sdk_objects["equipmentLocalDiskDef"] is not None and self._cap_provider is not None:

            # We have the corresponding CapProvider object - We need to find the matching equipmentLocalDiskDef object
            equipment_local_disk_def_list = [equipment_local_disk_def for equipment_local_disk_def in
                                             self._inventory.sdk_objects["equipmentLocalDiskDef"] if
                                             self._cap_provider.dn in equipment_local_disk_def.dn]
            if (len(equipment_local_disk_def_list)) != 1:
                self.logger(level="warning",
                            message="Could not find the appropriate catalog detail for object with DN " + self.dn +
                                    " of model \"" + self.model + "\" with ID " + self.id)
                return False
            else:
                self.cache_size = equipment_local_disk_def_list[0].cache_size
                self.block_size_catalog = int(equipment_local_disk_def_list[0].block_size)
                if equipment_local_disk_def_list[0].capacity:
                    self.capacity_catalog = equipment_local_disk_def_list[0].capacity
                self.number_of_blocks_catalog = int(equipment_local_disk_def_list[0].number_of_blocks)
                self.rotational_speed = int(float(equipment_local_disk_def_list[0].rotational_speed))
                self.self_encrypting_drive = equipment_local_disk_def_list[0].self_encrypting_drive
                return True

        return False


class UcsImcStorageLocalDisk(UcsStorageLocalDisk, UcsImcInventoryObject):
    _UCS_SDK_CATALOG_OBJECT_NAME = "pidCatalogHdd"
    _UCS_SDK_CATALOG_IDENTIFY_ATTRIBUTE = "disk"
    _UCS_SDK_OBJECT_IDENTIFY_ATTRIBUTE = "id"

    def __init__(self, parent=None, storage_local_disk=None):
        UcsStorageLocalDisk.__init__(self, parent=parent, storage_local_disk=storage_local_disk)

        self.connection_protocol = self.get_attribute(ucs_sdk_object=storage_local_disk,
                                                      attribute_name="interface_type",
                                                      attribute_secondary_name="connection_protocol")
        self.drive_state = self.get_attribute(ucs_sdk_object=storage_local_disk, attribute_name="drive_state")
        self.drive_type = self.get_attribute(ucs_sdk_object=storage_local_disk, attribute_name="media_type",
                                             attribute_secondary_name="drive_type")
        self.firmware_version = self.get_attribute(ucs_sdk_object=storage_local_disk, attribute_name="drive_firmware",
                                                   attribute_secondary_name="firmware_version")
        self.locator_led_status = self.get_attribute(ucs_sdk_object=storage_local_disk,
                                                     attribute_name="locator_led_status")
        self.model = self.get_attribute(ucs_sdk_object=storage_local_disk, attribute_name="product_id",
                                        attribute_secondary_name="model")
        self.self_encrypting_drive = self.get_attribute(ucs_sdk_object=storage_local_disk, attribute_name="fde_capable",
                                                        attribute_secondary_name="self_encrypting_drive")
        self.serial = self.get_attribute(ucs_sdk_object=storage_local_disk, attribute_name="drive_serial_number",
                                         attribute_secondary_name="serial")
        if self._inventory.load_from == "live":
            self.size = int(storage_local_disk.coerced_size.split(" ")[0])
            if self.link_speed == "unknown":
                self.link_speed = None
            else:
                self.link_speed = float(self.link_speed.split(" ")[0])
        elif self._inventory.load_from == "file":
            self.size = self.get_attribute(ucs_sdk_object=storage_local_disk, attribute_name="size",
                                           attribute_type="int")
            self.link_speed = self.get_attribute(ucs_sdk_object=storage_local_disk, attribute_name="link_speed",
                                                 attribute_type="float")

        UcsImcInventoryObject.__init__(self, parent=parent, ucs_sdk_object=storage_local_disk)

        if self._inventory.load_from == "live":
            self._find_drive_specs()

            # We check if we already have fetched the PID Catalog object
            description = ""
            if self._pid_catalog is not None:
                description = self._pid_catalog.description

            self.rotational_speed_marketing = None
            regex = r"(\d+\.?\dK) RPM"
            res = re.search(regex, description)
            if res is not None:
                self.rotational_speed_marketing = res.group(1)

            self.size_marketing = None
            regex = r"(\d+\.?\d?) ?[GT]B"
            res = re.search(regex, description)
            if res is not None:
                self.size_marketing = res.group(0).replace(" ", "")
            else:
                if self.block_size is not None and self.number_of_blocks is not None:
                    self.size_marketing = int((self.block_size * self.number_of_blocks) / 1000000000)
                    # Properly format size_marketing so that it fits the display on disk drives for the pictures
                    if self.size_marketing < 1000:
                        self.size_marketing = str(int(self.size_marketing)) + "GB"
                    elif self.size_marketing >= 1000:
                        if (self.size_marketing / 1000).is_integer():
                            self.size_marketing = str(int(self.size_marketing / 1000)) + "TB"
                        else:
                            if str(round(self.size_marketing / 1000, ndigits=1))[-2:] == ".0":
                                self.size_marketing = str(int(self.size_marketing / 1000)) + "TB"
                            else:
                                self.size_marketing = str(round(self.size_marketing / 1000, ndigits=1)) + "TB"

            # Fix for unknown SKU & drive size with SSD drive Micron_P400e-MTFDDAK400MAR
            if self.sku is None:
                if self.model == "Micron_P400e-MTFDDAK400MAR":
                    self.sku = "UCS-SD400G0KA2-G"
                    if self._pid_catalog.description == "UNKNOWN":
                        self.size_marketing = "400G"

            # Manual adjustment for wrong round up of some drives
            if self.size_marketing == "147GB":
                self.size_marketing = "146GB"
            elif self.size_marketing == "98GB":
                self.size_marketing = "100GB"
            elif self.size_marketing == "118GB":
                self.size_marketing = "120GB"
            elif self.size_marketing == "998GB":
                self.size_marketing = "1TB"

        elif self._inventory.load_from == "file":
            for attribute in ["block_size", "bootable", "number_of_blocks", "rotational_speed_marketing",
                              "size_marketing", "size_raw"]:
                setattr(self, attribute, None)
                if attribute in storage_local_disk:
                    setattr(self, attribute, self.get_attribute(ucs_sdk_object=storage_local_disk,
                                                                attribute_name=attribute))

    def _find_drive_specs(self):
        if "storageLocalDiskProps" not in self._inventory.sdk_objects.keys():
            return False

        # We check if we already have fetched the list of storageLocalDiskProps objects
        if self._inventory.sdk_objects["storageLocalDiskProps"] is not None:

            # We need to find the matching storageLocalDiskProps object
            storage_local_disk_props_list = [storage_local_disk_props for storage_local_disk_props in
                                             self._inventory.sdk_objects["storageLocalDiskProps"] if
                                             self.dn + "/" in storage_local_disk_props.dn]
            if (len(storage_local_disk_props_list)) != 1:
                self.logger(level="warning",
                            message="Could not find the appropriate drive details for object with DN " + self.dn +
                                    " of model \"" + self.model + "\" with ID " + self.id)
                return False
            else:
                self.block_size = int(storage_local_disk_props_list[0].block_size)
                self.bootable = storage_local_disk_props_list[0].boot_drive
                self.number_of_blocks = int(storage_local_disk_props_list[0].block_count)
                self.size_raw = int(storage_local_disk_props_list[0].raw_size.split(" ")[0])
                return True

        return False


class UcsStorageNvmeDrive(GenericUcsInventoryObject):
    def __init__(self, parent=None, ucs_sdk_object=None):
        GenericUcsInventoryObject.__init__(self, parent=parent, ucs_sdk_object=ucs_sdk_object)


class UcsSystemStorageControllerNvmeDrive(UcsStorageNvmeDrive, UcsSystemInventoryObject):
    _UCS_SDK_OBJECT_NAME = "storageController"
    _UCS_SDK_CATALOG_OBJECT_NAME = "equipmentLocalDiskControllerCapProvider"
    _UCS_SDK_FIRMWARE_RUNNING_SUFFIX = "/fw-system"

    def __init__(self, parent=None, storage_controller=None):
        UcsStorageNvmeDrive.__init__(self, parent=parent, ucs_sdk_object=storage_controller)

        self.id = self.get_attribute(ucs_sdk_object=storage_controller, attribute_name="id")
        self.model = self.get_attribute(ucs_sdk_object=storage_controller, attribute_name="model")
        self.pci_slot = self.get_attribute(ucs_sdk_object=storage_controller, attribute_name="pci_slot")
        self.revision = self.get_attribute(ucs_sdk_object=storage_controller, attribute_name="revision")
        self.serial = self.get_attribute(ucs_sdk_object=storage_controller, attribute_name="serial")
        # self.temperature = self.get_attribute(ucs_sdk_object=storage_controller,
        #                                       attribute_name="controller_chip_temp_celsius",
        #                                       attribute_secondary_name="temperature")
        self.vendor = self.get_attribute(ucs_sdk_object=storage_controller, attribute_name="vendor")

        UcsSystemInventoryObject.__init__(self, parent=parent, ucs_sdk_object=storage_controller)

        if self._inventory.load_from == "live":
            self.block_size = None
            self.block_size_catalog = None
            self.block_size_physical = None
            self.bootable = None
            self.cache_size = None
            self.capacity_catalog = None
            self.connection_protocol = None
            self.drive_state = None
            self.drive_type = None
            self.firmware_version = None
            self.life_left_in_days = None
            self.link_speed = None
            self.locator_led_status = None
            self.number_of_blocks = None
            self.number_of_blocks_catalog = None
            self.operability = None
            self.rotational_speed = None
            self.rotational_speed_marketing = None
            self.self_encrypting_drive = None
            self.size = None
            self.size_marketing = None
            self.size_raw = None
            self.slot_type = None
            self.temperature = None
            if self.pci_slot:
                if any(x in self.pci_slot for x in ["FRONT", "REAR"]):
                    self.slot_type = "sff-nvme"
                else:
                    self.slot_type = "pcie-nvme"

            disks = self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsSystemStorageLocalDisk,
                                                                   parent=self)
            if len(disks) == 1:
                self.block_size = disks[0].block_size
                self.block_size_catalog = disks[0].block_size_catalog
                self.block_size_physical = disks[0].block_size_physical
                self.bootable = disks[0].bootable
                self.cache_size = disks[0].cache_size
                self.capacity_catalog = disks[0].capacity_catalog
                self.connection_protocol = disks[0].connection_protocol
                self.drive_state = disks[0].drive_state
                self.drive_type = disks[0].drive_type
                self.firmware_version = disks[0].firmware_version
                self.link_speed = disks[0].link_speed
                self.locator_led_status = disks[0].locator_led_status
                self.number_of_blocks = disks[0].number_of_blocks
                self.number_of_blocks_catalog = disks[0].number_of_blocks_catalog
                self.operability = disks[0].operability
                self.rotational_speed = disks[0].rotational_speed
                self.rotational_speed_marketing = disks[0].rotational_speed_marketing
                self.self_encrypting_drive = disks[0].self_encrypting_drive
                self.size = disks[0].size
                self.size_marketing = disks[0].size_marketing
                self.size_raw = disks[0].size_raw

            nvme_stats = self._find_corresponding_storage_nvme_stats()
            if nvme_stats:
                self.temperature = nvme_stats.temperature
                self.life_left_in_days = nvme_stats.life_left_in_days

                if self.temperature is not None:
                    if " degrees C" in self.temperature:
                        self.temperature = float(self.temperature.split(" degrees C")[0])
                    else:
                        self.temperature = float(self.temperature)

                if self.life_left_in_days is not None:
                    self.life_left_in_days = int(self.life_left_in_days)

        elif self._inventory.load_from == "file":
            for attribute in ["block_size", "block_size_catalog", "block_size_physical", "bootable", "cache_size",
                              "capacity_catalog", "connection_protocol", "drive_state", "drive_type",
                              "firmware_version", "life_left_in_days", "link_speed", "locator_led_status",
                              "number_of_blocks", "number_of_blocks_catalog", "operability", "rotational_speed",
                              "rotational_speed_marketing", "self_encrypting_drive", "size", "size_marketing",
                              "size_raw", "slot_type", "temperature"]:
                setattr(self, attribute, None)
                if attribute in storage_controller:
                    setattr(self, attribute, self.get_attribute(ucs_sdk_object=storage_controller,
                                                                attribute_name=attribute))

    def _find_corresponding_storage_nvme_stats(self):
        if "storageNvmeStats" not in self._inventory.sdk_objects.keys():
            return False

        # We check if we already have fetched the list of storageNvmeStats objects
        if self._inventory.sdk_objects["storageNvmeStats"] is not None:

            # We need to find the matching storageNvmeStats object
            storage_nvme_stats_list = [storage_nvme_stats for storage_nvme_stats in
                                       self._inventory.sdk_objects["storageNvmeStats"] if
                                       self.dn + "/nvme-stats" == storage_nvme_stats.dn]
            if (len(storage_nvme_stats_list)) != 1:
                self.logger(level="debug",
                            message="Could not find the corresponding storageNvmeStats for object with DN " +
                                    self.dn + " of model \"" + self.model + "\" with ID " + self.id)
                self.logger(level="info", message="NVMe stats of disk with id " + self.id + " for server " +
                                                  self._parent.id + " are not available.")
                return False
            else:
                return storage_nvme_stats_list[0]

        return False


class UcsImcStorageControllerNvmeDrive(UcsStorageNvmeDrive, UcsImcInventoryObject):
    _UCS_SDK_OBJECT_NAME = "storageControllerNVMe"
    _UCS_SDK_CATALOG_OBJECT_NAME = "pidCatalogPCIAdapter"
    _UCS_SDK_CATALOG_IDENTIFY_ATTRIBUTE = "slot"
    _UCS_SDK_OBJECT_IDENTIFY_ATTRIBUTE = "id"

    def __init__(self, parent=None, storage_controller_nvme=None):
        UcsStorageNvmeDrive.__init__(self, parent=parent, ucs_sdk_object=storage_controller_nvme)

        self.health = self.get_attribute(ucs_sdk_object=storage_controller_nvme, attribute_name="health")
        self.id = self.get_attribute(ucs_sdk_object=storage_controller_nvme, attribute_name="id")
        self.model = self.get_attribute(ucs_sdk_object=storage_controller_nvme, attribute_name="model")
        self.serial = self.get_attribute(ucs_sdk_object=storage_controller_nvme, attribute_name="serial")
        self.temperature = self.get_attribute(ucs_sdk_object=storage_controller_nvme,
                                              attribute_name="controller_chip_temp_celsius",
                                              attribute_secondary_name="temperature")
        self.vendor = self.get_attribute(ucs_sdk_object=storage_controller_nvme, attribute_name="vendor")

        UcsImcInventoryObject.__init__(self, parent=parent, ucs_sdk_object=storage_controller_nvme)

        if self._inventory.load_from == "live":
            self.connection_protocol = "NVME"
            self.drive_type = "SSD"

            self.slot_type = None
            if "FrontPCIe" in self.id:
                self.slot_type = "sff-nvme"
                regex = r"\d+"
                res = re.search(regex, self.id)
                if res is not None:
                    self.id = str(res.group(0))
            elif self.model is not None:
                if "HHHL" in self.model:
                    self.slot_type = "pcie-nvme"
                    if "SLOT-" in self.id:
                        regex = r"\d+"
                        res = re.search(regex, self.id)
                        if res is not None:
                            self.id = str(res.group(0))

            if self.temperature is None:
                self.temperature = self.get_attribute(ucs_sdk_object=storage_controller_nvme,
                                                      attribute_name="temperature")
            if self.temperature is not None:
                if " degrees C" in self.temperature:
                    self.temperature = float(self.temperature.split(" degrees C")[0])
                else:
                    self.temperature = float(self.temperature)

            # Trying to determine drive size
            self.size_marketing = None
            self.size = None
            if self.model is not None:
                regex = r"(\d+\.?\d?) ?[GT]B"
                res = re.search(regex, self.model)
                if res is not None:
                    size_marketing = res.group(0).replace(" ", "")
                    if "GB" in size_marketing:
                        self.size = int(res.group(1)) * 1000
                        if self.size < 1000000:
                            self.size_marketing = str(int(self.size / 1000)) + "GB"
                        else:
                            self.size_marketing = str(float(self.size / 1000000)) + "TB"
                    elif "TB" in size_marketing:
                        self.size = float(res.group(1)) * 1000000
                        if str(round(self.size / 1000000, ndigits=1))[-2:] == ".0":
                            self.size_marketing = str(int(self.size / 1000000)) + "TB"
                        else:
                            self.size_marketing = str(round(self.size / 1000000, ndigits=1)) + "TB"

        elif self._inventory.load_from == "file":
            for attribute in ["connection_protocol", "drive_type", "size", "size_marketing", "slot_type"]:
                setattr(self, attribute, None)
                if attribute in storage_controller_nvme:
                    setattr(self, attribute, self.get_attribute(ucs_sdk_object=storage_controller_nvme,
                                                                attribute_name=attribute))


class UcsImcStorageNvmeDrive(UcsStorageNvmeDrive, UcsImcInventoryObject):
    _UCS_SDK_OBJECT_NAME = "storageNVMePhysicalDrive"
    _UCS_SDK_CATALOG_OBJECT_NAME = "pidCatalogPCIAdapter"
    _UCS_SDK_CATALOG_IDENTIFY_ATTRIBUTE = "slot"
    _UCS_SDK_OBJECT_IDENTIFY_ATTRIBUTE = "id"

    def __init__(self, parent=None, storage_nvme_physical_drive=None):
        UcsStorageNvmeDrive.__init__(self, parent=parent, ucs_sdk_object=storage_nvme_physical_drive)

        self.health = self.get_attribute(ucs_sdk_object=storage_nvme_physical_drive, attribute_name="pd_status",
                                         attribute_secondary_name="health")
        self.firmware_version = self.get_attribute(ucs_sdk_object=storage_nvme_physical_drive,
                                                   attribute_name="firmware_version")
        self.id = self.get_attribute(ucs_sdk_object=storage_nvme_physical_drive, attribute_name="id")
        self.model = self.get_attribute(ucs_sdk_object=storage_nvme_physical_drive, attribute_name="product_name",
                                        attribute_secondary_name="model")
        self.serial = self.get_attribute(ucs_sdk_object=storage_nvme_physical_drive, attribute_name="serial")
        self.temperature = self.get_attribute(ucs_sdk_object=storage_nvme_physical_drive,
                                              attribute_name="pd_chip_temp_celsius",
                                              attribute_secondary_name="temperature")
        self.vendor = self.get_attribute(ucs_sdk_object=storage_nvme_physical_drive, attribute_name="vendor")

        UcsImcInventoryObject.__init__(self, parent=parent, ucs_sdk_object=storage_nvme_physical_drive)

        if self._inventory.load_from == "live":
            self.connection_protocol = "NVME"
            self.drive_type = "SSD"

            self.slot_type = None
            if "FRONT-NVME-" in self.id:
                self.slot_type = "sff-nvme"
                regex = r"\d+"
                res = re.search(regex, self.id)
                if res is not None:
                    self.id = str(res.group(0))
            elif self.model is not None:
                if "HHHL" in self.model:
                    self.slot_type = "pcie-nvme"

            if self.temperature is None:
                self.temperature = self.get_attribute(ucs_sdk_object=storage_nvme_physical_drive,
                                                      attribute_name="temperature")
            if self.temperature is not None:
                if " degrees C" in self.temperature:
                    self.temperature = float(self.temperature.split(" degrees C")[0])
                else:
                    self.temperature = float(self.temperature)

            # Trying to determine drive size
            self.size_marketing = None
            self.size = None
            if self.model is not None:
                regex = r"(\d+\.?\d?) ?[GT]B"
                res = re.search(regex, self.model)
                if res is not None:
                    size_marketing = res.group(0).replace(" ", "")
                    if "GB" in size_marketing:
                        self.size = int(res.group(1)) * 1000
                        if self.size < 1000000:
                            self.size_marketing = str(int(self.size / 1000)) + "GB"
                        else:
                            self.size_marketing = str(float(self.size / 1000000)) + "TB"
                    elif "TB" in size_marketing:
                        self.size = float(res.group(1)) * 1000000
                        if str(round(self.size / 1000000, ndigits=1))[-2:] == ".0":
                            self.size_marketing = str(int(self.size / 1000000)) + "TB"
                        else:
                            self.size_marketing = str(round(self.size / 1000000, ndigits=1)) + "TB"

        elif self._inventory.load_from == "file":
            for attribute in ["connection_protocol", "drive_type", "size", "size_marketing", "slot_type"]:
                setattr(self, attribute, None)
                if attribute in storage_nvme_physical_drive:
                    setattr(self, attribute, self.get_attribute(ucs_sdk_object=storage_nvme_physical_drive,
                                                                attribute_name=attribute))


class UcsImcSiocStorageNvmeDrive(UcsStorageNvmeDrive, UcsImcInventoryObject):
    _UCS_SDK_OBJECT_NAME = "ioControllerNVMePhysicalDrive"

    #TODO: Get the corresponding pidCatalog item to fetch SKU

    def __init__(self, parent=None, io_controller_nvme_physical_drive=None):
        UcsStorageNvmeDrive.__init__(self, parent=parent, ucs_sdk_object=io_controller_nvme_physical_drive)

        self.health = self.get_attribute(ucs_sdk_object=io_controller_nvme_physical_drive, attribute_name="pd_status",
                                         attribute_secondary_name="health")
        self.firmware_version = self.get_attribute(ucs_sdk_object=io_controller_nvme_physical_drive,
                                                   attribute_name="firmware_version")
        self.id = self.get_attribute(ucs_sdk_object=io_controller_nvme_physical_drive, attribute_name="id")
        self.model = self.get_attribute(ucs_sdk_object=io_controller_nvme_physical_drive, attribute_name="model")
        self.serial = self.get_attribute(ucs_sdk_object=io_controller_nvme_physical_drive, attribute_name="serial")
        self.temperature = self.get_attribute(ucs_sdk_object=io_controller_nvme_physical_drive,
                                              attribute_name="pd_chip_temp_celsius",
                                              attribute_secondary_name="temperature")
        self.vendor = self.get_attribute(ucs_sdk_object=io_controller_nvme_physical_drive, attribute_name="vendor")

        UcsImcInventoryObject.__init__(self, parent=parent, ucs_sdk_object=io_controller_nvme_physical_drive)

        if self._inventory.load_from == "live":
            self.connection_protocol = "NVME"
            self.drive_type = "SSD"

            self.slot_type = None
            if "SIOCNVMe" in self.id:
                self.slot_type = "sioc-nvme"
                regex = r"\d+"
                res = re.search(regex, self.id)
                if res is not None:
                    self.id = str(res.group(0))

            if self.temperature is not None:
                if " degrees C" in self.temperature:
                    self.temperature = float(self.temperature.split(" degrees C")[0])
                else:
                    self.temperature = float(self.temperature)

            # Trying to determine drive size
            self.size_marketing = None
            self.size = None
            if self.model is not None:
                regex = r"(\d+\.?\d?) ?[GT]B"
                res = re.search(regex, self.model)
                if res is not None:
                    size_marketing = res.group(0).replace(" ", "")
                    if "GB" in size_marketing:
                        self.size = int(res.group(1)) * 1000
                        if self.size < 1000000:
                            self.size_marketing = str(int(self.size / 1000)) + "GB"
                        else:
                            self.size_marketing = str(float(self.size / 1000000)) + "TB"
                    elif "TB" in size_marketing:
                        self.size = float(res.group(1)) * 1000000
                        if str(round(self.size / 1000000, ndigits=1))[-2:] == ".0":
                            self.size_marketing = str(int(self.size / 1000000)) + "TB"
                        else:
                            self.size_marketing = str(round(self.size / 1000000, ndigits=1)) + "TB"

        elif self._inventory.load_from == "file":
            for attribute in ["connection_protocol", "drive_type", "size", "size_marketing", "slot_type"]:
                setattr(self, attribute, None)
                if attribute in io_controller_nvme_physical_drive:
                    setattr(self, attribute, self.get_attribute(ucs_sdk_object=io_controller_nvme_physical_drive,
                                                                attribute_name=attribute))


class UcsStorageRaidBattery(GenericUcsInventoryObject):
    _UCS_SDK_OBJECT_NAME = "storageRaidBattery"

    def __init__(self, parent=None, storage_raid_battery=None):
        GenericUcsInventoryObject.__init__(self, parent=parent, ucs_sdk_object=storage_raid_battery)

        self.battery_type = self.get_attribute(ucs_sdk_object=storage_raid_battery, attribute_name="battery_type")


class UcsSystemStorageRaidBattery(UcsStorageRaidBattery, UcsSystemInventoryObject):
    def __init__(self, parent=None, storage_raid_battery=None):
        UcsStorageRaidBattery.__init__(self, parent=parent, storage_raid_battery=storage_raid_battery)

        self.battery_status = self.get_attribute(ucs_sdk_object=storage_raid_battery, attribute_name="bbu_status",
                                                 attribute_secondary_name="battery_status")
        self.capacity_percentage = self.get_attribute(ucs_sdk_object=storage_raid_battery,
                                                      attribute_name="capacity_percentage")
        self.id = self.get_attribute(ucs_sdk_object=storage_raid_battery, attribute_name="id")
        self.model = self.get_attribute(ucs_sdk_object=storage_raid_battery, attribute_name="model")
        self.revision = self.get_attribute(ucs_sdk_object=storage_raid_battery, attribute_name="revision")
        self.serial = self.get_attribute(ucs_sdk_object=storage_raid_battery, attribute_name="serial")
        self.temperature = self.get_attribute(ucs_sdk_object=storage_raid_battery, attribute_name="temperature",
                                              attribute_type="float")
        self.vendor = self.get_attribute(ucs_sdk_object=storage_raid_battery, attribute_name="vendor")

        UcsSystemInventoryObject.__init__(self, parent=parent, ucs_sdk_object=storage_raid_battery)


class UcsImcStorageRaidBattery(UcsStorageRaidBattery, UcsImcInventoryObject):
    def __init__(self, parent=None, storage_raid_battery=None):
        UcsStorageRaidBattery.__init__(self, parent=parent, storage_raid_battery=storage_raid_battery)

        self.battery_status = self.get_attribute(ucs_sdk_object=storage_raid_battery, attribute_name="battery_status")
        self.serial = self.get_attribute(ucs_sdk_object=storage_raid_battery, attribute_name="serial_number",
                                         attribute_secondary_name="serial")
        self.vendor = self.get_attribute(ucs_sdk_object=storage_raid_battery, attribute_name="manufacturer",
                                         attribute_secondary_name="vendor")

        UcsImcInventoryObject.__init__(self, parent=parent, ucs_sdk_object=storage_raid_battery)

        if self._inventory.load_from == "live":
            regex = r"\d+"
            res = re.search(regex, str(storage_raid_battery.temperature))
            if res is not None:
                self.temperature = float(res.group(0))
        elif self._inventory.load_from == "file":
            self.temperature = self.get_attribute(ucs_sdk_object=storage_raid_battery, attribute_name="temperature",
                                                  attribute_type="float")
