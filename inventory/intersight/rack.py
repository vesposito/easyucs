# coding: utf-8
# !/usr/bin/env python

""" rack.py: Easy UCS Deployment Tool """

from inventory.generic.rack import GenericRack
from inventory.intersight.adaptor import IntersightAdaptor
from inventory.intersight.cpu import IntersightCpu
from inventory.intersight.gpu import IntersightGpu
from inventory.intersight.memory import IntersightMemoryArray
from inventory.intersight.object import IntersightInventoryObject
from inventory.intersight.psu import IntersightPsu
from inventory.intersight.storage import IntersightStorageController, IntersightStorageControllerNvmeDrive
from inventory.intersight.tpm import IntersightTpm


class IntersightComputeRackUnit(GenericRack, IntersightInventoryObject):
    def __init__(self, parent=None, compute_rack_unit=None):
        GenericRack.__init__(self, parent=parent)
        IntersightInventoryObject.__init__(self, parent=parent, sdk_object=compute_rack_unit)

        self.cpus = []
        self.id = self.get_attribute(attribute_name="server_id", attribute_secondary_name="id")
        self.gpus = []
        self.management_mode = self.get_attribute(attribute_name="management_mode")
        self.memory_arrays = []
        self.memory_available = self.get_attribute(attribute_name="available_memory",
                                                   attribute_secondary_name="memory_available")
        self.memory_total = self.get_attribute(attribute_name="total_memory",
                                               attribute_secondary_name="memory_total")
        self.model = self.get_attribute(attribute_name="model")
        self.name = self.get_attribute(attribute_name="name")
        self.nvme_drives = []
        self.revision = self.get_attribute(attribute_name="revision")
        self.serial = self.get_attribute(attribute_name="serial")
        self.storage_controllers = []
        self.tpms = []
        self.user_label = self.get_attribute(attribute_name="user_label")
        self.vendor = self.get_attribute(attribute_name="vendor")

        # Adding a human-readable attribute for memory capacity
        self._get_memory_total_marketing()

        self.adaptors = self._get_adaptors()
        self.power_supplies = self._get_power_supplies()

        if self._inventory.load_from == "live":
            if self._parent.__class__.__name__ not in ["IntersightImmDomain", "IntersightUcsmDomain"]:
                # We use the server name as the ID for Intersight Standalone Mode
                self.id = self.name

            self.sku = self.model
            self.locator_led_status = self._determine_locator_led_status()
            self.short_name = self._get_model_short_name()
            #self.name = self._get_compute_rack_unit_name()

            # Available Memory is stored in GB, whereas Total Memory is stored in MB. Converting Available Memory to MB
            if self.memory_available:
                self.memory_available = int(self.memory_available) * 1024

            # We need to find the "compute.Board" object that belongs to this rack server to inventory subcomponents
            compute_board = self.get_inventory_objects_from_ref(ref=self._object.board)
            if len(compute_board) == 1:
                self.cpus = self.get_inventory_objects_from_ref(
                    ref=compute_board[0].processors, object_class=IntersightCpu, parent=self)
                self.gpus = self.get_inventory_objects_from_ref(
                    ref=compute_board[0].graphics_cards, object_class=IntersightGpu, parent=self)
                self.memory_arrays = self.get_inventory_objects_from_ref(
                    ref=compute_board[0].memory_arrays, object_class=IntersightMemoryArray, parent=self)
                self.storage_controllers = self.get_inventory_objects_from_ref(
                    ref=compute_board[0].storage_controllers, object_class=IntersightStorageController, parent=self)
                self.tpms = self.get_inventory_objects_from_ref(
                    ref=compute_board[0].equipment_tpms, object_class=IntersightTpm, parent=self)
                self.nvme_drives = []
                storage_controllers = self.get_inventory_objects_from_ref(
                    ref=compute_board[0].storage_controllers)
                for storage_controller in storage_controllers:
                    if getattr(storage_controller, "type", None) in ["Nvme", "NVME"] and \
                            getattr(storage_controller, "physical_disks", []):
                        self.nvme_drives.extend(self.get_inventory_objects_from_ref(
                            ref=storage_controller.physical_disks, object_class=IntersightStorageControllerNvmeDrive,
                            parent=self))
            else:
                self.logger(level="debug",
                            message="Unable to find unique compute.Board object for rack unit with ID " + str(self.id))

            # We need to find the "management.Controller" object that belongs to this rack to inventory subcomponents
            management_controller = self.get_inventory_objects_from_ref(ref=self._object.bmc)
            if len(management_controller) == 1:
                self.firmware_version = self._determine_firmware_version(
                    source_obj=management_controller[0], filter_attr="dn", filter_value="-system")
            else:
                self.logger(level="debug",
                            message="Unable to find unique management.Controller object for rack unit with ID " +
                                    str(self.id))

        elif self._inventory.load_from == "file":
            if "cpus" in self._object:
                for cpu in self._object["cpus"]:
                    self.cpus.append(IntersightCpu(parent=self, processor_unit=cpu))
            if "gpus" in self._object:
                for gpu in self._object["gpus"]:
                    self.gpus.append(IntersightGpu(parent=self, graphics_card=gpu))
            if "nvme_drives" in self._object:
                for nvme_drive in self._object["nvme_drives"]:
                    self.nvme_drives.append(IntersightStorageControllerNvmeDrive(parent=self, storage_local_disk=nvme_drive))
            if "memory_arrays" in self._object:
                for memory_array in self._object["memory_arrays"]:
                    self.memory_arrays.append(IntersightMemoryArray(parent=self, memory_array=memory_array))
            if "storage_controllers" in self._object:
                for storage_controller in self._object["storage_controllers"]:
                    self.storage_controllers.append(IntersightStorageController(
                        parent=self, storage_controller=storage_controller))
            if "tpms" in self._object:
                for tpm in self._object["tpms"]:
                    self.tpms.append(IntersightTpm(parent=self, equipment_tpm=tpm))
            for attribute in ["firmware_version", "locator_led_status", "memory_total_marketing", "name",
                              "short_name", "sku"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

    def _get_adaptors(self):
        if self._inventory.load_from == "live":
            return self.get_inventory_objects_from_ref(ref=self._object.adapters, object_class=IntersightAdaptor,
                                                       parent=self)
        elif self._inventory.load_from == "file" and "adaptors" in self._object:
            return [IntersightAdaptor(self, adapter) for adapter in self._object["adaptors"]]
        else:
            return []

    def _get_power_supplies(self):
        if self._inventory.load_from == "live":
            return self.get_inventory_objects_from_ref(ref=self._object.psus, object_class=IntersightPsu, parent=self)
        elif self._inventory.load_from == "file" and "power_supplies" in self._object:
            return [IntersightPsu(self, psu) for psu in self._object["power_supplies"]]
        else:
            return []
