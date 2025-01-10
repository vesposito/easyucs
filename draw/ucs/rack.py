# coding: utf-8
# !/usr/bin/env python

""" rack.py: Easy UCS Deployment Tool """

import copy

from PIL import Image, ImageFont

from draw.object import GenericUcsDrawEquipment, UcsSystemDrawInfraEquipment, GenericUcsDrawObject
from draw.ucs.adaptor import UcsAdaptorDraw
from draw.ucs.cpu_module import UcsCpuModuleDraw
from draw.ucs.mgmt import UcsSystemDrawMgmtInterface
from draw.ucs.psu import UcsPsuDraw
from draw.ucs.riser import GenericUcsDrawPcieRiser
from draw.ucs.storage import UcsStorageControllerDraw, UcsStorageLocalDiskDraw
from draw.wire import UcsSystemDrawWire


class GenericDrawRackFront(GenericUcsDrawObject):
    # def __init__(self, parent=None):
    #     GenericUcsDrawEquipment.__init__(self, parent=parent, orientation="front")

    def fill_blanks(self):
        if not self.storage_controller_list:
            if "disks_slots" in self.json_file:
                # Fill blank for disks slots
                potential_slot = [*range(1, len(self.json_file["disks_slots"])+1)]
                used_slot = self.disk_slots_used
                unused_slot = []
                for blank_id in set(potential_slot) - set(used_slot):
                    unused_slot.append(blank_id)
                for slot_id in unused_slot:
                    blank_name = None
                    orientation = "horizontal"
                    disk_format = None
                    for disk_slot in self.json_file['disks_slots']:
                        if disk_slot['id'] == slot_id:
                            orientation = disk_slot['orientation']
                            disk_format = disk_slot['format']
                    for model in self.json_file["disks_models"]:
                        if "type" in model and not blank_name:
                            if model["type"] == "blank" and model["format"] == disk_format:
                                blank_name = model["name"]
                                img = Image.open("catalog/drives/img/" + blank_name + ".png", 'r')
                                if orientation == "vertical":
                                    img = GenericUcsDrawEquipment.rotate_object(picture=img)
                    if blank_name:
                        for slot in self.json_file["disks_slots"]:
                            if slot["id"] == slot_id:
                                coord = slot["coord"]
                        coord_offset = self.picture_offset[0] + coord[0], self.picture_offset[1] + coord[1]
                        self.paste_layer(img, coord_offset)

        if hasattr(self, "cpu_modules"):
            blank_name = None
            if "cpu_modules_models" in self.json_file:
                for model in self.json_file["cpu_modules_models"]:
                    if "type" in model:
                        if model["type"] == "blank":
                            blank_name = model["name"]
            if blank_name:
                if "cpu_modules_slots" in self.json_file:
                    for slot in self.json_file["cpu_modules_slots"]:
                        img = None
                        for cpu_module in self.cpu_modules:
                            if slot["id"] != cpu_module.module_id:
                                img = Image.open("catalog/cpu_modules/img/" + blank_name + ".png", 'r')
                            else:
                                img = None
                                break
                        if img:
                            coord = slot["coord"]
                            coord_offset = self.picture_offset[0] + coord[0], self.picture_offset[1] + coord[1]
                            self.paste_layer(img, coord_offset)

    def get_storage_controllers(self):
        storage_controller_list = []
        for storage_controller in self._parent.storage_controllers:
            # We skip M.2 and internal controllers on racks
            if storage_controller.type not in ["Hba", "HBA", "Raid", "RAID", "SAS", "Nvme", "NVME"]:
                continue
            storage_controller_list.append(UcsStorageControllerDraw(storage_controller, self))
        # storage_controller_list = remove_not_completed_in_list(storage_controller_list)
        return storage_controller_list

    def get_cpu_modules(self):
        cpu_module_list = []
        for cpu in self._parent.cpus:
            if int(cpu.id) % 2:  # We have one CPU Module for two CPUs
                cpu_module_list.append(UcsCpuModuleDraw(cpu, self))
        cpu_module_list = [cpu for cpu in cpu_module_list if cpu.picture_size]
        return cpu_module_list

    def get_nvme_disks(self):
        disk_list = []
        for disk in self._parent.nvme_drives:
            # Prevent potential disk with ID 0 to be used in Draw (happens sometimes with B200 M2)
            if disk.id != "0" and disk.slot_type == "sff-nvme":
                if disk.id in [str(i["id"]) for i in self.json_file["disks_slots"]]:
                    disk_list.append(UcsStorageLocalDiskDraw(parent=disk, parent_draw=self))
                    self.disk_slots_used.append(int(disk.id))
        # TODO: NVMe Disks need rework to prevent having to paste layer each time and integrate it into get_nvme_disks()
        return disk_list


class UcsRackDrawFront(GenericDrawRackFront, GenericUcsDrawEquipment):
    def __init__(self, parent=None):
        GenericUcsDrawEquipment.__init__(self, parent=parent, orientation="front")
        if not self.picture:
            return
        self.background = self._create_background(self.canvas_width, self.canvas_height, self.canvas_color)
        self.draw = self._create_draw()

        self.paste_layer(self.picture, self.picture_offset)

        self.disk_slots_used = []

        self.storage_controller_list = self.get_storage_controllers()
        if self._parent.sku in ["UCSC-C480-M5"]:
            self.cpu_modules = self.get_cpu_modules()

        self.nvme_disks = []
        if hasattr(self._parent, "nvme_drives") and "disks_slots" in self.json_file:
            self.nvme_disks = self.get_nvme_disks()
            # TODO: NVME Disks need rework to prevent having to paste layer each time and integrate it into get_nvme_disks()
            for disk in self.nvme_disks:
                self.paste_layer(disk.picture, disk.picture_offset)

        self.fill_blanks()

        if parent.__class__.__name__ in ["IntersightComputeRackUnit"]:
            if parent._parent.__class__.__name__ in ["IntersightImmDomain", "IntersightUcsmDomain"]:
                self._file_name = (self._device_target + "_" + parent._parent.name + "_rack_" +
                                   str(self._parent.id) + "_front")
            else:
                self._file_name = (self._device_target + "_rack_" + str(self._parent.name) + "_front")
        else:
            self._file_name = self._device_target + "_rack_" + str(self._parent.id) + "_front"

        # We drop the picture in order to save on memory
        self.picture = None


class UcsImcDrawRackFront(GenericDrawRackFront, GenericUcsDrawEquipment):
    def __init__(self, parent=None):
        GenericUcsDrawEquipment.__init__(self, parent=parent, orientation="front")
        if not self.picture:
            return

        self.background = self._create_background(self.canvas_width, self.canvas_height, self.canvas_color)
        self.draw = self._create_draw()

        self.paste_layer(self.picture, self.picture_offset)

        self.disk_slots_used = []

        self.storage_controller_list = self.get_storage_controllers()
        if self._parent.sku in ["UCSC-C480-M5"]:
            self.cpu_modules = self.get_cpu_modules()

        self.nvme_disks = []
        if hasattr(self._parent, "nvme_drives") and "disks_slots" in self.json_file:
            self.nvme_disks = self.get_nvme_disks()
            for disk in self.nvme_disks:
                self.paste_layer(disk.picture, disk.picture_offset)

        self.fill_blanks()

        self._file_name = self._device_target + "_rack_front"


class GenericDrawRackRear(GenericUcsDrawObject):
    # def __init__(self, parent=None):
    #     GenericUcsDrawObject.__init__(self, parent=parent, orientation="rear")

    def get_storage_controllers(self):
        storage_controller_list = []
        for storage_controller in self._parent.storage_controllers:
            if storage_controller.type in ["Hba", "HBA", "Raid", "RAID", "SAS", "Nvme", "NVME"]:
                storage_controller_list.append(UcsStorageControllerDraw(storage_controller, self))
        # storage_controller_list = remove_not_completed_in_list(storage_controller_list)
        return storage_controller_list

    def get_psu_list(self):
        psu_list = []
        for psu in self._parent.power_supplies:
            if psu.id != '0':  # UCS PE sometimes adds an invalid PSU with ID 0
                psu_list.append(UcsPsuDraw(psu, self))
        # psu_list = remove_not_supported_in_list(psu_list)
        # psu_list = remove_not_completed_in_list(psu_list)
        # We only keep the PSU that have been fully created -> picture
        psu_list = [psu for psu in psu_list if psu.picture_size]
        return psu_list

    def get_mgmt_if_list(self):
        mgmt_if_list = []
        if "lom_ports" in self.json_file:
            if hasattr(self._parent, "mgmt_interfaces"):
                for mgmt_if in self._parent.mgmt_interfaces:
                    if mgmt_if.id is not None:
                        mgmt_if_list.append(UcsSystemDrawMgmtInterface(mgmt_if, self))
            # mgmt_if_list = remove_not_completed_in_list(mgmt_if_list)
        return mgmt_if_list

    def get_pcie_riser_list(self, infra=False):
        pcie_riser_list = []
        self._parent_pcie_risers = None
        if hasattr(self._parent, "pcie_risers") and self._parent.pcie_risers:
            self._parent_pcie_risers = self._parent.pcie_risers

        # If no PCIe Riser detected
        elif self._parent.model == "UCSC-C240-M5SD":
            # Since we don't have any object that gives us which PCIe risers are available, we have to force a default
            # We do this for C240 M5SD, since it is mandatory for the draw operation
            self._parent_pcie_risers = [{"id": "1", "sku": "UCSC-RIS-1-240M5"},
                                        {"id": "2", "sku": "UCSC-RIS-2B-240M5"}]

        elif self._parent.model in ["UCSC-C240-M6S", "UCSC-C240-M6SX", "UCSC-C240-M6N", "UCSC-C240-M6SN",
                                    "UCSC-C240-M6L", "UCSC-C245-M6SX"]:
            # Since we don't have any object that gives us which PCIe risers are available, we have to force a default
            # We do this for C240/C245 M6, since it is mandatory for the draw operation
            self._parent_pcie_risers = [{"id": "1", "sku": "UCSC-RIS1A-240M6"},
                                        {"id": "2", "sku": "UCSC-RIS2A-240M6"},
                                        {"id": "3", "sku": "UCSC-RIS3A-240M6"}]

        elif self._parent.model in ["UCSC-C220-M6S", "UCSC-C220-M6N", "UCSC-C225-M6S", "UCSC-C225-M6N"]:
            # Since we don't have any object that gives us which PCIe risers are available, we have to force a default
            # We do this for C220/C225 M6, since it is mandatory for the draw operation
            self._parent_pcie_risers = [{"id": "1", "sku": "UCSC-R2R3-C220M6"}]

        elif self._parent.model in ["UCSC-C220-M7S", "UCSC-C220-M7N"]:
            # Since we don't have any object that gives us which PCIe risers are available, we have to force a default
            # We do this for C220 M7, since it is mandatory for the draw operation
            self._parent_pcie_risers = [{"id": "1", "sku": "UCSC-RIS1A-22XM7"},
                                        {"id": "2", "sku": "UCSC-RIS2A-22XM7"},
                                        {"id": "3", "sku": "UCSC-RIS3A-22XM7"}]

        elif self._parent.model in ["UCSC-C240-M7SX", "UCSC-C240-M7SN", "UCSC-C245-M8SX"]:
            # Since we don't have any object that gives us which PCIe risers are available, we have to force a default
            # We do this for C240 M7/C245 M8, since it is mandatory for the draw operation
            self._parent_pcie_risers = [{"id": "1", "sku": "UCSC-RIS1A-240-D"},
                                        {"id": "2", "sku": "UCSC-RIS2A-240-D"},
                                        {"id": "3", "sku": "UCSC-RIS3A-240-D"}]

        elif self._parent.model in ["UCSC-C225-M8S", "UCSC-C225-M8N"]:
            # Since we don't have any object that gives us which PCIe risers are available, we have to force a default
            # We do this for C225 M8, since it is mandatory for the draw operation
            self._parent_pcie_risers = [{"id": "1", "sku": "UCSC-RIS1A-225M8"},
                                        {"id": "2", "sku": "UCSC-RIS2A-225M8"},
                                        {"id": "3", "sku": "UCSC-RIS3A-225M8"}]

        else:
            return pcie_riser_list

        for pcie_riser in self._parent_pcie_risers:
            # if hasattr(pcie_riser, "sku"):
            #     if pcie_riser.sku not in ["None"]:
            #         pcie_riser_list.append(
            #             GenericUcsDrawPcieRiser(parent=pcie_riser, parent_draw=self, infra=infra))
            if pcie_riser["sku"] not in ["None"]:
                pcie_riser_list.append(
                    GenericUcsDrawPcieRiser(parent=pcie_riser, parent_draw=self, infra=infra))

        # We only keep the Riser that have been fully created -> picture
        pcie_riser_list = [riser for riser in pcie_riser_list if riser.picture_size]

        return pcie_riser_list

    def get_adaptor_list(self):
        adaptor_list = []
        for adaptor in self._parent.adaptors:
            if adaptor.pci_slot not in ["L", "N/A"]:
                adaptor_list.append(UcsAdaptorDraw(parent=adaptor, parent_draw=self))
        # adaptor_list = remove_not_supported_in_list(adaptor_list)
        # adaptor_list = remove_not_completed_in_list(adaptor_list)
        # We only keep the adaptor that have been fully created -> picture
        adaptor_list = [adaptor for adaptor in adaptor_list if adaptor.picture_size]
        return [e for e in adaptor_list if hasattr(e, "_parent")]

    def get_nvme_disks(self):
        disk_list = []
        for disk in self._parent.nvme_drives:
            # Prevent potential disk with ID 0 to be used in Draw (happens sometimes with B200 M2)
            if disk.id != "0" and disk.slot_type == "sff-nvme":
                if disk.id in [str(i["id"]) for i in self.json_file["disks_slots_rear"]]:
                    disk_list.append(UcsStorageLocalDiskDraw(parent=disk, parent_draw=self))
                    self.disk_slots_used.append(int(disk.id))
        return disk_list

    def fill_blanks(self):
        len_mlom = 0
        if "mlom_slots" in self.json_file:
            len_mlom = len(self.json_file["mlom_slots"])
        if len(self.adaptor_list) < (len(self.json_file["pcie_slots"]) + len_mlom):
            mlom_used_slot = []
            mlom_potential_slot = []
            mlom_unused_slot = []

            pcie_used_slot = []
            pcie_potential_slot = []
            pcie_potential_slot_info = []
            pcie_unused_slot = []

            for slot in self._parent.adaptors:
                if slot.pci_slot == "MLOM" and len_mlom:
                    if hasattr(slot, "id"):
                        if slot.id == "MLOM":
                            mlom_used_slot.append(1)
                        elif slot.id.isdigit():
                            mlom_used_slot.append(int(slot.id))
                        else:
                            mlom_used_slot.append(1)
                    else:
                        mlom_used_slot.append(1)
                elif slot.pci_slot and slot.pci_slot.isdigit():
                    pcie_used_slot.append(int(slot.pci_slot))

            for slot in self.json_file["pcie_slots"]:
                # slot = id, width
                pcie_potential_slot.append(slot["id"])
                width = "full"
                orientation = "horizontal"
                if "width" in slot:
                    width = slot["width"]
                if "orientation" in slot:
                    orientation = slot["orientation"]
                pcie_potential_slot_info.append((slot["id"], width, orientation))

            if len_mlom:
                for slot in self.json_file["mlom_slots"]:
                    mlom_potential_slot.append(slot["id"])

            for blank_id in set(pcie_potential_slot) - set(pcie_used_slot):
                pcie_unused_slot.append(blank_id)

            if len_mlom:
                for blank_id in set(mlom_potential_slot) - set(mlom_used_slot):
                    mlom_unused_slot.append(blank_id)

            for slot_id in pcie_unused_slot:
                for triple in pcie_potential_slot_info:  # Search for width of the slot
                    if triple[0] == slot_id:
                        width = triple[1]
                        orientation = triple[2]
                for expansion in self.json_file["pcie_models"]:
                    if "type" in expansion:
                        if expansion["type"] == "blank" and expansion['width'] == width:
                            blank_name = expansion["name"]
                            img = Image.open("catalog/adaptors/img/" + blank_name + ".png", 'r')
                            if orientation == "reverse":
                                img = self.rotate_object(picture=img)
                                img = self.rotate_object(picture=img)
                            elif orientation == "vertical":
                                img = self.rotate_object(picture=img)
                                img = self.rotate_object(picture=img)
                                img = self.rotate_object(picture=img)
                            for slot in self.json_file["pcie_slots"]:
                                if slot["id"] == int(slot_id):
                                    coord = slot["coord"]
                            coord_offset = self.picture_offset[0] + coord[0], self.picture_offset[1] + coord[1]
                            self.paste_layer(img, coord_offset)

            if len_mlom:  # if MLOM slot present
                for slot_id in mlom_unused_slot:
                    for expansion in self.json_file["mlom_models"]:
                        if "type" in expansion:
                            if expansion["type"] == "blank":
                                blank_name = expansion["name"]
                                img = Image.open("catalog/adaptors/img/" + blank_name + ".png", 'r')
                                for slot in self.json_file["mlom_slots"]:
                                    if slot["id"] == int(slot_id):
                                        coord = slot["coord"]
                                coord_offset = self.picture_offset[0] + coord[0], self.picture_offset[1] + coord[1]
                                self.paste_layer(img, coord_offset)

        if "psus_slots_rear" in self.json_file:
            # Fill blank for rear PSU Slot
            if len(self._parent.power_supplies)-1 < len(self.json_file["psus_slots_rear"]):
                used_slot = []
                potential_slot = []
                unused_slot = []
                for slot in self._parent.power_supplies:
                    used_slot.append(int(slot.id))
                for slot in self.json_file["psus_slots_rear"]:
                    potential_slot.append(slot["id"])
                for blank_id in set(potential_slot) - set(used_slot):
                    unused_slot.append(blank_id)
                for slot_id in unused_slot:
                    for expansion in self.json_file["psus_models"]:
                        if "type" in expansion:
                            if expansion["type"] == "blank":
                                blank_name = expansion["name"]
                                img = Image.open("catalog/power_supplies/img/" + blank_name + ".png", 'r')
                                for slot in self.json_file["psus_slots_rear"]:
                                    if slot["id"] == int(slot_id):
                                        coord = slot["coord"]
                                coord_offset = self.picture_offset[0] + coord[0], self.picture_offset[1] + coord[1]
                                self.paste_layer(img, coord_offset)

        if "pcie_riser_slots" in self.json_file:
            # Fill blank for PCIe Riser slot (we put the default ones when None could be detected)
            if len(self._parent_pcie_risers)-1 < len(self.json_file["pcie_riser_slots"]):
                used_slot = []
                potential_slot = []
                unused_slot = []
                for slot in self._parent_pcie_risers:
                    used_slot.append(int(slot["id"]))
                for slot in self.json_file["pcie_riser_slots"]:
                    potential_slot.append(slot["id"])
                a = list(set(potential_slot) - set(used_slot))
                for blank_id in set(potential_slot) - set(used_slot):
                    unused_slot.append(blank_id)
                for slot_id in unused_slot:
                    for expansion in self.json_file["pcie_riser_models"]:
                        if "type" in expansion:
                            if expansion["type"] == "blank":
                                # Some riser need a specific blank panel due to form factor
                                if "riser_ids" in expansion:
                                    found = False
                                    for riser_id in expansion["riser_ids"]:
                                        if riser_id == slot_id:
                                            found = True
                                    if not found:
                                        continue
                                blank_name = expansion["name"]
                                img = Image.open("catalog/pcie_risers/img/" + blank_name + ".png", 'r')
                                for slot in self.json_file["pcie_riser_slots"]:
                                    if slot["id"] == int(slot_id):
                                        coord = slot["coord"]
                                coord_offset = self.picture_offset[0] + coord[0], self.picture_offset[1] + coord[1]
                                self.paste_layer(img, coord_offset)

        if not self.storage_controller_list:
            if "disks_slots_rear" in self.json_file:
                # Fill blank for disks slots
                if len(self.disk_slots_used) < len(self.json_file["disks_slots_rear"]):
                    used_slot = []
                    potential_slot = []
                    unused_slot = []
                    for disk_used in self.disk_slots_used:
                        used_slot.append(disk_used)
                    for disk in self.json_file["disks_slots_rear"]:
                        potential_slot.append(disk["id"])
                    for blank_id in set(potential_slot) - set(used_slot):
                        unused_slot.append(blank_id)
                    for slot_id in unused_slot:
                        blank_name = None
                        orientation = "horizontal"
                        disk_format = None
                        for disk_slot in self.json_file['disks_slots_rear']:
                            if disk_slot['id'] == slot_id:
                                orientation = disk_slot['orientation']
                                disk_format = disk_slot['format']
                        for model in self.json_file["disks_models"]:
                            if "type" in model and not blank_name:
                                if model["type"] == "blank" and model["format"] == disk_format:
                                    blank_name = model["name"]
                                    img = Image.open("catalog/drives/img/" + blank_name + ".png", 'r')
                                    if orientation == "vertical":
                                        img = GenericUcsDrawEquipment.rotate_object(picture=img)

                        if blank_name:
                            for slot in self.json_file["disks_slots_rear"]:
                                if slot["id"] == int(slot_id):
                                    coord = slot["coord"]
                            coord_offset = self.picture_offset[0] + coord[0], self.picture_offset[1] + coord[1]
                            self.paste_layer(img, coord_offset)


class UcsRackDrawRear(GenericDrawRackRear, GenericUcsDrawEquipment):
    def __init__(self, parent=None, color_ports=True):
        GenericUcsDrawEquipment.__init__(self, parent=parent, orientation="rear")
        self.color_ports = color_ports
        if not self.picture:
            return
        self.background = self._create_background(self.canvas_width, self.canvas_height, self.canvas_color)
        self.draw = self._create_draw()

        self.paste_layer(self.picture, self.picture_offset)

        self.disk_slots_used = []

        self.pcie_riser_list = self.get_pcie_riser_list()
        self.adaptor_list = self.get_adaptor_list()
        self.psu_list = self.get_psu_list()
        self.mgmt_if_list = self.get_mgmt_if_list()

        self.storage_controller_list = self.get_storage_controllers()

        self.nvme_disks = []
        if hasattr(self._parent, "nvme_drives") and "disks_slots_rear" in self.json_file:
            self.nvme_disks = self.get_nvme_disks()
            for disk in self.nvme_disks:
                self.paste_layer(disk.picture, disk.picture_offset)

        self.fill_blanks()

        if parent.__class__.__name__ in ["IntersightComputeRackUnit"]:
            if parent._parent.__class__.__name__ in ["IntersightImmDomain", "IntersightUcsmDomain"]:
                self._file_name = (self._device_target + "_" + parent._parent.name + "_rack_" +
                                   str(self._parent.id) + "_rear")
            else:
                self._file_name = self._device_target + "_rack_" + str(self._parent.name) + "_rear"
        else:
            self._file_name = self._device_target + "_rack_" + str(self._parent.id) + "_rear"

        if not self.color_ports:
            if parent.__class__.__name__ in ["IntersightComputeRackUnit"]:
                if parent._parent.__class__.__name__ in ["IntersightImmDomain", "IntersightUcsmDomain"]:
                    self._file_name = (self._device_target + "_" + parent._parent.name + "_rack_" +
                                       str(self._parent.id) + "_rear_clear")
                else:
                    self._file_name = self._device_target + "_rack_" + str(self._parent.name) + "_rear_clear"
            else:
                self._file_name = self._device_target + "_rack_" + str(self._parent.id) + "_rear_clear"

        if self.color_ports:
            self.clear_version = UcsRackDrawRear(parent=parent, color_ports=False)

        # We drop the picture in order to save on memory
        self.picture = None


class UcsImcDrawRackRear(GenericDrawRackRear, GenericUcsDrawEquipment):
    def __init__(self, parent=None):
        GenericUcsDrawEquipment.__init__(self, parent=parent, orientation="rear")
        if not self.picture:
            return

        self.background = self._create_background(self.canvas_width, self.canvas_height, self.canvas_color)
        self.draw = self._create_draw()

        self.paste_layer(self.picture, self.picture_offset)

        self.disk_slots_used = []

        self.pcie_riser_list = self.get_pcie_riser_list()
        self.adaptor_list = self.get_adaptor_list()
        self.psu_list = self.get_psu_list()
        # self.mgmt_if_list = self.get_mgmt_if_list()

        self.storage_controller_list = self.get_storage_controllers()

        self.nvme_disks = []
        if hasattr(self._parent, "nvme_drives") and "disks_slots_rear" in self.json_file:
            self.nvme_disks = self.get_nvme_disks()
            for disk in self.nvme_disks:
                self.paste_layer(disk.picture, disk.picture_offset)

        self.fill_blanks()
        self._file_name = self._device_target + "_rack_rear"


class UcsRackDrawInfra(UcsSystemDrawInfraEquipment):
    def __init__(self, rack, fi_list, fex_list=None, parent=None):

        UcsSystemDrawInfraEquipment.__init__(self, parent=parent)
        # Create a copy of the DrawRack
        if 'Rear' in rack.__class__.__name__:
            self.rack = UcsRackDrawRear(parent=rack._parent)
        else:
            self.rack = UcsRackDrawFront(parent=rack._parent)

        self.fi_a = self._get_fi(fi_list, "A")
        self.fi_b = self._get_fi(fi_list, "B")

        self.fex_presence = None
        if fex_list:
            self.fex_presence = self._get_fex_infra_presence()
            if self.fex_presence:
                self.fex_list = self._get_fex(fex_list)
                self.fex_a = self.fex_list[0]
                self.fex_b = self.fex_list[1]
                if self.fex_a:
                    self.valid_fex = self.fex_a
                elif self.fex_b:
                    self.valid_fex = self.fex_b
                else:
                    self.logger(level="warning", message="Infra of rack #" + str(self.rack._parent.id) +
                                                         " not saved because FEX presence confirmed "
                                                         "but could not be found")
                    return None

        # Canvas settings
        if self.fex_presence:
            # self.canvas_width = self.fi_a.picture_size[0] * 2 + self.rack.picture_size[0] + self.fex_a.picture_size[0] * 2 + 200  # arbitrary
            self.canvas_width = self.rack.picture_size[0] + self.valid_fex.picture_size[0] * 2 + 100  # arbitrary
            self.canvas_height = self.fi_a.picture_size[1] + self.rack.picture_size[1] + \
                                 self.valid_fex.picture_size[1] + 400  # arbitrary
        else:
            self.canvas_width = self.fi_a.picture_size[0] * 2 + self.rack.picture_size[0] + 100  # arbitrary
            self.canvas_height = self.fi_a.picture_size[1] + self.rack.picture_size[1] + 100  # arbitrary
        self.canvas_color = (255, 255, 255, 255)  # white

        self.rack_offset = self._get_picture_offset("rack")
        self.fi_a_offset = self._get_picture_offset("fi_a")
        if self.fi_b:
            self.fi_b_offset = self._get_picture_offset("fi_b")
        if self.fex_presence:
            if self.fex_a:
                self.fex_a_offset = self._get_picture_offset("fex_a")
            if self.fex_b:
                self.fex_b_offset = self._get_picture_offset("fex_b")

        self.background = self._create_background(self.canvas_width, self.canvas_height, self.canvas_color)
        self.draw = self._create_draw()

        # Paste layers
        # As we drop the picture before, we need to recreate it and drop it again after pasting the layer
        self.rack._get_picture()
        self.paste_layer(self.rack.picture, self.rack_offset)
        self.rack.picture = None

        self.fi_a._get_picture()
        if self.fi_a._parent.sku == "UCS-FI-M-6324":
            # We only need to rotate the picture as the other parameters are already rotated (json_file, picture_size)
            self.fi_a.picture = self.fi_a.rotate_object(picture=self.fi_a.picture)
        self.paste_layer(self.fi_a.picture, self.fi_a_offset)
        self.fi_a.picture = None

        if self.fi_b:
            self.fi_b._get_picture()
            if self.fi_b._parent.sku == "UCS-FI-M-6324":
                self.fi_b.picture = self.fi_b.rotate_object(picture=self.fi_b.picture)
            self.paste_layer(self.fi_b.picture, self.fi_b_offset)
            self.fi_b.picture = None
        if self.fex_presence:
            if self.fex_a:
                self.fex_a._get_picture()
                self.paste_layer(self.fex_a.picture, self.fex_a_offset)
                self.fex_a.picture = None
            if self.fex_b:
                self.fex_b._get_picture()
                self.paste_layer(self.fex_b.picture, self.fex_b_offset)
                self.fex_b.picture = None

        # Draw ports and expansion
        self.fi_a.draw = self.draw
        self.fi_a.background = self.background
        self.fi_a.picture_offset = self.fi_a_offset
        self.fi_a.ports = []
        self.fi_a.draw_ports(True)
        self.fi_a.gem_list = self.fi_a.get_expansion_modules()
        self.fi_a.fill_blanks()

        if self.fi_b:  # if FI B is present
            self.fi_b.draw = self.draw
            self.fi_b.background = self.background
            self.fi_b.picture_offset = self.fi_b_offset
            self.fi_b.ports = []
            self.fi_b.draw_ports(True)
            self.fi_b.gem_list = self.fi_b.get_expansion_modules()
            self.fi_b.fill_blanks()

        if self.fex_presence:
            if self.fex_a:
                self.fex_a.draw = self.draw
                self.fex_a.background = self.background
                self.fex_a.picture_offset = self.fex_a_offset
                self.fex_a.fabric_port_list = []
                self.fex_a.host_port_list = []
                self.fex_a.draw_ports()
            if self.fex_b:
                self.fex_b.draw = self.draw
                self.fex_b.background = self.background
                self.fex_b.picture_offset = self.fex_b_offset
                self.fex_b.fabric_port_list = []
                self.fex_b.host_port_list = []
                self.fex_b.draw_ports()

        self.rack.draw = self.draw
        self.rack.background = self.background
        self.rack.picture_offset = self.rack_offset
        self.rack.pcie_riser_list = self.rack.get_pcie_riser_list(infra=True)
        self.rack.adaptor_list = self.rack.get_adaptor_list()
        self.rack.psu_list = self.rack.get_psu_list()
        self.rack.mgmt_if_list = self.rack.get_mgmt_if_list()
        self.rack.storage_controller_list = self.rack.get_storage_controllers()
        if hasattr(self.rack._parent, "nvme_drives") and "disks_slots_rear" in self.rack.json_file:
            self.rack.disk_slots_used = []
            self.rack.nvme_disks = self.rack.get_nvme_disks()
            for disk in self.rack.nvme_disks:
                self.rack.paste_layer(disk.picture, disk.picture_offset)
        self.rack.fill_blanks()

        self.wires = []
        self.set_wire()

        # For the legend of ports
        self.port_color_list = self.fi_a.legend_items
        if self.fi_b:
            self.port_color_list = self.fi_b.legend_items + self.port_color_list
        self.port_color_list = set(self.port_color_list)  # Delete duplication

        # For the legend of wires
        self.wire_color_list = []
        for wire in self.wires:
            self.wire_color_list.append(wire.color)
        self.wire_color_list = set(self.wire_color_list)

        self.draw_port_wire_legend(self, self.port_color_list, self.wire_color_list)
        self.draw_rack_info()

        # if there is no wire at all, there is no need to save the picture
        if self.wires:
            if parent.__class__.__name__ in ["IntersightFi"]:
                self._file_name = (self._device_target + "_" + parent._parent.name + "_infra_rack_" +
                                   str(self.rack._parent.id))
            else:
                self._file_name = self._device_target + "_infra_rack_" + str(self.rack._parent.id)
        else:
            self.logger(level="warning", message="Infra of rack #" + str(self.rack._parent.id) +
                                                 " not saved because no connection between the FI and the rack")

        # We drop the picture in order to save on memory
        self.picture = None

    def _get_fex_infra_presence(self):
        # Used to know if a FEX needs to be used for this infra - for connecting network adapters
        for adaptor in self.rack.adaptor_list:
            for adapt_port in adaptor.ports:
                # Search for peer information
                if hasattr(adapt_port, "peer"):
                    if "fex" in adapt_port.peer:
                        return True
        # Used to know if a FEX needs to be used for this infra - for connecting rack servers LOM management ports
        if hasattr(self.rack._parent, "mgmt_interfaces"):
            for mgmt_if in self.rack._parent.mgmt_interfaces:
                if hasattr(mgmt_if, "peer"):
                    if mgmt_if.peer:
                        if "fex" in mgmt_if.peer:
                            return True
        return False

    def _get_fex(self, list):
        fex_id_list = []
        if hasattr(self.rack._parent, "mgmt_interfaces"):
            for mgmt_if in self.rack._parent.mgmt_interfaces:
                if hasattr(mgmt_if, "peer"):
                    if mgmt_if.peer:
                        if "fex" in mgmt_if.peer.keys():
                            fex_id_list.append(str(mgmt_if.peer["fex"]))

        # Handle case where adaptor is connected to FEX, but management interface is not
        if not fex_id_list:
            for adaptor in self.rack._parent.adaptors:
                for adapt_port in adaptor.ports:
                    if hasattr(adapt_port, "peer"):
                        if adapt_port.peer:
                            if "fex" in adapt_port.peer.keys():
                                fex_id_list.append(str(adapt_port.peer["fex"]))

        fex_list = [None, None]
        for id in fex_id_list:
            for fex in list:
                if str(fex._parent.id) == id:
                    if fex._parent.switch_id == 'A':
                        fex_list[0] = copy.copy(fex)
                    elif fex._parent.switch_id == 'B':
                        fex_list[1] = copy.copy(fex)
        return fex_list

    def _get_fi(self, fi_list, id):
        fabric = None
        for fi in fi_list:
            if fi._parent.id == id:
                fabric = fi
            if fi._parent.id == id:
                fabric = fi
        return copy.copy(fabric)

    def _get_picture_offset(self, type):
        if type == "rack":
            return round(self.canvas_width / 2 - self.rack.picture_size[0] / 2), self.canvas_height - \
                       self.rack.picture_size[1]

        if type == "fi_a":
            return 0, 0

        if type == "fi_b":
            return self.canvas_width - self.fi_b.picture_size[0], 0

        if type == "fex_a":
            # return self.fi_a.picture_size[0] + 50, self.fi_a.picture_size[1] + 100
            return 0, self.fi_a.picture_size[1] + 400

        if type == "fex_b":
            # return self.canvas_width - self.fex_b.picture_size[0] - self.fi_a.picture_size[0] - 50, self.fi_a.picture_size[1] + 100
            return self.canvas_width - self.fex_b.picture_size[0], self.fi_a.picture_size[1] + 400

    def draw_rack_info(self):
        fill_color = "black"
        font_size = 60
        font_title = ImageFont.truetype('arial.ttf', font_size)
        if self.rack._parent.user_label:
            msg = "Rack #" + str(self.rack._parent.id) + " - " + self.rack._parent.user_label
        else:
            msg = "Rack #" + str(self.rack._parent.id)
        w = self.draw.textlength(msg, font=font_title)
        # 16 px space between text and equipment
        self.draw.text((round(self.canvas_width / 2 - w / 2), self.rack_offset[1] - (font_size + 16)), msg,
                       fill=fill_color, font=font_title)
        if self.fex_presence:
            if self.fex_a:
                msg = "Fex #" + str(self.fex_a._parent.id)
                w = self.draw.textlength(msg, font=font_title)
                # 16 px space between text and equipment
                self.draw.text((self.fex_a.picture_size[0] - w, self.fex_a_offset[1] - (font_size + 16)), msg,
                               fill=fill_color, font=font_title)
            if self.fex_b:
                msg = "Fex #" + str(self.fex_b._parent.id)
                w = self.draw.textlength(msg, font=font_title)
                # 16 px space between text and equipment
                self.draw.text((self.canvas_width - self.fex_b.picture_size[0],
                                self.fex_b_offset[1] - (font_size + 16)), msg, fill=fill_color, font=font_title)

    def set_wire(self):
        # Handling wire from server to FI or FEX
        for adaptor in self.rack.adaptor_list:
            for adapt_port in getattr(adaptor, "ports", []):
                # Search for peer information
                if hasattr(adapt_port, "peer"):
                    peer = adapt_port.peer
                    peer_fex = None
                    peer_fi = None
                    if "fex" in peer:
                        peer_fex = peer["fex"]
                        if hasattr(self, "fex_a"):
                            if self.fex_a:
                                if str(self.fex_a._parent.id) == str(peer_fex):
                                    fex = self.fex_a
                                    fabric = "a"
                        if hasattr(self, "fex_b"):
                            if self.fex_b:
                                if str(self.fex_b._parent.id) == str(peer_fex):
                                    fex = self.fex_b
                                    fabric = "b"
                        if not hasattr(self, "fex_a") and not hasattr(self, "fex_b"):
                            return None
                    elif "switch" in peer:
                        peer_fi = peer["switch"]
                        if peer_fi == "A":  # if FI A
                            fi = self.fi_a
                            fabric = "a"
                        if peer_fi == "B":  # if FI B
                            fi = self.fi_b
                            fabric = "b"
                    peer_slot_id = peer["slot"]
                    peer_port_id = peer["port"]
                    if "aggr_port" in peer:
                        peer_aggr_id = peer["aggr_port"]
                    else:
                        peer_aggr_id = None

                    wire_width = self.WIDTH_WIRE  # Set the default wire width

                    point_breakout = None
                    if not adapt_port._parent.is_breakout:
                        point_rack = adapt_port.coord[0] + round(adapt_port.size[0] / 2), adapt_port.coord[
                            1] + round(adapt_port.size[1] / 2)
                    else:
                        wire_width = self.WIDTH_WIRE_BREAKOUT
                        point_breakout = adapt_port.coord[0] + round(adapt_port.size[0] / 2), \
                                         adapt_port.coord[1] + round(adapt_port.size[1] / 2)

                        if fabric == "a":
                            if int(adaptor._parent.id) == 1:
                                point_rack = adapt_port.coord[0] - (int(adapt_port.id) - 1) % 4 * adapt_port.size[0] + \
                                                adapt_port.size[0] * 2, \
                                                adapt_port.coord[1] + adapt_port.size[1] + self.WIRE_DISTANCE_SHORT
                            if int(adaptor._parent.id) == 2:
                                point_rack = adapt_port.coord[0] - (int(adapt_port.id) - 1) % 4 * adapt_port.size[0] + \
                                                adapt_port.size[0] * 2, \
                                                adapt_port.coord[1] + adapt_port.size[1] + self.WIRE_DISTANCE_LONG
                        elif fabric == "b":
                            if int(adaptor._parent.id) == 1:
                                point_rack = adapt_port.coord[0] - (int(adapt_port.id) - 1) % 4 * adapt_port.size[0] + \
                                                adapt_port.size[0] * 2, \
                                                adapt_port.coord[1] - self.WIRE_DISTANCE_LONG
                            if int(adaptor._parent.id) == 2:
                                point_rack = adapt_port.coord[0] - (int(adapt_port.id) - 1) % 4 * adapt_port.size[0] + \
                                                adapt_port.size[0] * 2, \
                                                adapt_port.coord[1] - self.WIRE_DISTANCE_SHORT

                    # Find and calculate coordinates of the peer point on the FI
                    if peer_fi:
                        point_fi = None
                        if peer_slot_id == 1:
                            for port in fi.ports:
                                if peer_aggr_id:
                                    if int(port.id) == peer_port_id:
                                        if port.aggr_id:
                                            wire_width = self.WIDTH_WIRE_BREAKOUT
                                            if int(port.aggr_id) == peer_aggr_id:
                                                # Even / odd
                                                point_fi = port.coord[0] + round(port.size[0] / 3) + (
                                                    peer_aggr_id + 1) % 2 * round(
                                                    port.size[0] / 3) - ((peer_aggr_id + 1) % 2), port.coord[1] + round(
                                                    port.size[1] / 2)
                                                peer_port = port
                                else:
                                    if (int(port.id) == peer_port_id) and port.aggr_id is None:
                                        # Even / odd
                                        point_fi = port.coord[0] + round(port.size[0] / 3) + (
                                                    peer_port_id + 1) % 2 * round(port.size[0] / 3), port.coord[
                                                       1] + round(port.size[1] / 2)
                                        peer_port = port

                        else:
                            for gem in fi.gem_list:
                                if int(gem._parent.id) == peer_slot_id:
                                    for port in gem.ports:
                                        if peer_aggr_id:
                                            if int(port.id) == peer_port_id:
                                                if port.aggr_id:
                                                    wire_width = 5
                                                    if int(port.aggr_id) == peer_aggr_id:
                                                        # Even / odd
                                                        point_fi = port.coord[0] + round(port.size[0] / 3) + (
                                                                    peer_aggr_id + 1) % 2 * round(port.size[0] / 3) - (
                                                                               (peer_aggr_id + 1) % 2), port.coord[
                                                                       1] + round(port.size[1] / 2)
                                                        peer_port = port
                                        else:
                                            if (int(port.id) == peer_port_id) and port.aggr_id is None:
                                                # Even / odd
                                                point_fi = port.coord[0] + round(port.size[0] / 3) + (
                                                            peer_port_id + 1) % 2 * round(port.size[0] / 3), port.coord[
                                                               1] + round(port.size[1] / 2)
                                                peer_port = port

                        self.logger(level="debug", message="Setting wire for rack " + str(self.rack._parent.id) +
                                                           ", width : " + str(wire_width))
                        if point_fi:
                            # draw_wire(self.draw, point_fi, point_rack, wire_color, wire_width)
                            if point_breakout:
                                self.wires.append(
                                    UcsSystemDrawWire(self, (point_rack, point_breakout), wire_width,
                                                      easyucs_fabric_port=peer_port._parent, line_type="straight"))
                                self.wires.append(UcsSystemDrawWire(self, (point_fi, point_rack), wire_width,
                                                                    easyucs_fabric_port=peer_port._parent))
                                # self.wires = remove_not_completed_in_list(self.wires)

                                fill_color = "black"
                                font_size = 40
                                font_title = ImageFont.truetype('arial.ttf', font_size)
                                self.draw.text((point_fi[0] - 30, point_rack[1] - 45), adapt_port.id, fill=fill_color,
                                               font=font_title)

                            else:
                                # draw_wire(self.draw, point_fi, point_chassis, wire_color, wire_width)
                                # self.wires.append(UcsSystemDrawWire(self, (point_fi, point_rack), wire_width,
                                #                                  easyucs_fi_port=port._parent))
                                # When a card is a quad port
                                if "-C25Q-04" in adapt_port._parent._parent.sku:
                                    wire_width = self.WIDTH_WIRE_BREAKOUT
                                    if fabric == "a":
                                        if adaptor._parent.id.isdigit() and int(adaptor._parent.id) % 2:
                                            if int(adapt_port.id) % 2:
                                                step = self.WIRE_DISTANCE_SHORT + round(adapt_port.size[1] / 2)
                                            else:
                                                step = self.WIRE_DISTANCE_LONG + round(adapt_port.size[1] / 2)
                                        else:
                                            if int(adapt_port.id) % 2:
                                                step = self.WIRE_DISTANCE_SHORT + round(adapt_port.size[1] / 2)
                                            else:
                                                step = self.WIRE_DISTANCE_LONG + round(adapt_port.size[1] / 2)
                                    if fabric == "b":
                                        if adaptor._parent.id.isdigit() and int(adaptor._parent.id) % 2:
                                            if int(adapt_port.id) % 2:
                                                step = - self.WIRE_DISTANCE_LONG - round(adapt_port.size[1] / 2)
                                            else:
                                                step = - self.WIRE_DISTANCE_SHORT - round(adapt_port.size[1] / 2)
                                        else:
                                            if int(adapt_port.id) % 2:
                                                step = - self.WIRE_DISTANCE_LONG - round(adapt_port.size[1] / 2)
                                            else:
                                                step = - self.WIRE_DISTANCE_SHORT - round(adapt_port.size[1] / 2)
                                # for all the non quad port cards
                                else:
                                    if fabric == "a":
                                        if adaptor._parent.id.isdigit() and int(adaptor._parent.id) % 2:
                                        # if (int(adapt_port._parent.port_id) % 2):
                                            step = self.WIRE_DISTANCE_SHORT + round(adapt_port.size[1]/2)
                                        else:
                                            step = self.WIRE_DISTANCE_LONG + round(adapt_port.size[1]/2)
                                    if fabric == "b":
                                        if adaptor._parent.id.isdigit() and int(adaptor._parent.id) % 2:
                                            step = - self.WIRE_DISTANCE_LONG - round(adapt_port.size[1]/2)
                                        else:
                                            step = - self.WIRE_DISTANCE_SHORT - round(adapt_port.size[1]/2)
                                target = point_rack[0], point_rack[1] + step
                                self.wires.append(UcsSystemDrawWire(self, (point_fi, point_rack), wire_width,
                                                                    extra_points=[target],
                                                                    easyucs_fabric_port=peer_port._parent))
                                # self.wires = remove_not_completed_in_list(self.wires)
                        else:
                            self.logger(level="error", message="Peer not found")

                    if peer_fex:
                        # Find and calculate coordinates of the peer point on the FEX
                        point_fex = None
                        for port in fex.host_port_list:
                            if (int(port.id) == peer_port_id) and port.aggr_id is None:
                                # Even / odd
                                point_fex = port.coord[0] + round(port.size[0] / 3) + (
                                    peer_port_id + 1) % 2 * round(
                                    port.size[0] / 3), port.coord[1] + round(
                                    port.size[1] / 2)
                                peer_port = port

                        self.logger(level="debug", message="Setting wire for rack " + str(self.rack._parent.id) +
                                                           ", width : " + str(wire_width))
                        if point_fex:
                            # draw_wire(self.draw, point_fex, point_rack, wire_color, wire_width)
                            if point_breakout:
                                self.wires.append(
                                    UcsSystemDrawWire(self, (point_rack, point_breakout), wire_width,
                                                      easyucs_fabric_port=peer_port._parent, line_type="straight"))
                                self.wires.append(UcsSystemDrawWire(self, (point_fex, point_rack), wire_width,
                                                                    easyucs_fabric_port=peer_port._parent))
                                # self.wires = remove_not_completed_in_list(self.wires)

                                fill_color = "black"
                                font_size = 40
                                font_title = ImageFont.truetype('arial.ttf', font_size)
                                self.draw.text((point_fex[0] - 30, point_rack[1] - 45), adapt_port.id, fill=fill_color,
                                               font=font_title)

                            else:
                                # draw_wire(self.draw, point_fi, point_chassis, wire_color, wire_width)
                                # self.wires.append(UcsSystemDrawWire(self, (point_fi, point_rack), wire_width,
                                #                                  easyucs_fi_port=port._parent))
                                # When a card is a quad port
                                if "-C25Q-04" in adapt_port._parent._parent.sku:
                                    wire_width = self.WIDTH_WIRE_BREAKOUT
                                    if fabric == "a":
                                        if adaptor._parent.id.isdigit() and int(adaptor._parent.id) % 2:
                                            if int(adapt_port.id) % 2:
                                                step = self.WIRE_DISTANCE_SHORT + round(adapt_port.size[1] / 2)
                                            else:
                                                step = self.WIRE_DISTANCE_LONG + round(adapt_port.size[1] / 2)
                                        else:
                                            if int(adapt_port.id) % 2:
                                                step = self.WIRE_DISTANCE_SHORT + round(adapt_port.size[1] / 2)
                                            else:
                                                step = self.WIRE_DISTANCE_LONG + round(adapt_port.size[1] / 2)
                                    if fabric == "b":
                                        if adaptor._parent.id.isdigit() and int(adaptor._parent.id) % 2:
                                            if int(adapt_port.id) % 2:
                                                step = - self.WIRE_DISTANCE_LONG - round(adapt_port.size[1] / 2)
                                            else:
                                                step = - self.WIRE_DISTANCE_SHORT - round(adapt_port.size[1] / 2)
                                        else:
                                            if int(adapt_port.id) % 2:
                                                step = - self.WIRE_DISTANCE_LONG - round(adapt_port.size[1] / 2)
                                            else:
                                                step = - self.WIRE_DISTANCE_SHORT - round(adapt_port.size[1] / 2)
                                # for all the non quad port cards
                                else:
                                    if fabric == "a":
                                        if adaptor._parent.id.isdigit() and int(adaptor._parent.id) % 2:
                                        # if (int(adapt_port._parent.port_id) % 2):
                                            step = self.WIRE_DISTANCE_SHORT + round(adapt_port.size[1]/2)
                                        else:
                                            step = self.WIRE_DISTANCE_LONG + round(adapt_port.size[1]/2)
                                    if fabric == "b":
                                        if adaptor._parent.id.isdigit() and int(adaptor._parent.id) % 2:
                                            step = - self.WIRE_DISTANCE_LONG - round(adapt_port.size[1]/2)
                                        else:
                                            step = - self.WIRE_DISTANCE_SHORT - round(adapt_port.size[1]/2)

                                target = point_rack[0], point_rack[1] + step
                                self.wires.append(UcsSystemDrawWire(self, (point_fex, point_rack), wire_width,
                                                                    extra_points=[target],
                                                                    easyucs_fabric_port=peer_port._parent))
                                # self.wires = remove_not_completed_in_list(self.wires)
                        else:
                            self.logger(level="error", message="Peer not found")

        # Handling wire from FEX to FI
        if self.fex_presence:
            if self.fex_a and self.fex_b:
                fex_list = [self.fex_a, self.fex_b]
            elif self.fex_a:
                fex_list = [self.fex_a]
            elif self.fex_b:
                fex_list = [self.fex_b]
            else:
                fex_list = []
            for fex in fex_list:
                for fex_port in fex.fabric_port_list:
                    # Search for peer information
                    if hasattr(port, 'peer'):
                        peer = fex_port.peer
                    else:
                        peer = fex_port._parent.peer
                    peer_fi = None
                    if "switch" in peer:
                        peer_fi = peer["switch"]
                        if peer_fi == "A":  # if FI A
                            fi = self.fi_a
                        if peer_fi == "B":  # if FI B
                            fi = self.fi_b
                    peer_slot_id = peer["slot"]
                    peer_port_id = peer["port"]
                    if "aggr_port" in peer:
                        peer_aggr_id = peer["aggr_port"]
                    else:
                        peer_aggr_id = None
                    #  int(not(0)) = 1, impair port are placed at a third of the port size, pair at two third
                    point_fex = fex_port.coord[0] + (1 + int(not (int(fex_port.id) % 2))) * round(
                        fex_port.size[0] / 3), fex_port.coord[1] + fex_port.size[1] / 2

                    wire_width = self.WIDTH_WIRE  # Set the default wire width

                    if peer_fi:
                        # Find and calculate coordinates of the peer point on the FI
                        point_fi = None
                        if peer_slot_id == 1:
                            for port in fi.ports:
                                if peer_aggr_id:
                                    if int(port.id) == peer_port_id:
                                        if port.aggr_id:
                                            wire_width = 5
                                            if int(port.aggr_id) == peer_aggr_id:
                                                # Even / odd
                                                point_fi = port.coord[0] + round(port.size[0] / 3) + (
                                                    peer_aggr_id + 1) % 2 * round(
                                                    port.size[0] / 3) - ((peer_aggr_id + 1) % 2), \
                                                           port.coord[1] + round(
                                                               port.size[1] / 2)
                                                peer_port = port
                                else:
                                    if (int(port.id) == peer_port_id) and port.aggr_id is None:
                                        # Even / odd
                                        point_fi = port.coord[0] + round(port.size[0] / 3) + (
                                            peer_port_id + 1) % 2 * round(
                                            port.size[0] / 3), port.coord[1] + round(
                                            port.size[1] / 2)
                                        peer_port = port

                        else:
                            for gem in fi.gem_list:
                                if int(gem._parent.id) == peer_slot_id:
                                    for port in gem.ports:
                                        if peer_aggr_id:
                                            if int(port.id) == peer_port_id:
                                                if port.aggr_id:
                                                    wire_width = 5
                                                    if int(port.aggr_id) == peer_aggr_id:
                                                        # Even / odd
                                                        point_fi = port.coord[0] + round(
                                                            port.size[0] / 3) + (
                                                                       peer_aggr_id + 1) % 2 * round(
                                                            port.size[0] / 3) - ((peer_aggr_id + 1) % 2), \
                                                                   port.coord[
                                                                       1] + round(
                                                                       port.size[1] / 2)
                                                        peer_port = port
                                        else:
                                            if (int(port.id) == peer_port_id) and port.aggr_id is None:
                                                # Even / odd
                                                point_fi = port.coord[0] + round(port.size[0] / 3) + (
                                                    peer_port_id + 1) % 2 * round(
                                                    port.size[0] / 3), port.coord[1] + round(
                                                    port.size[1] / 2)
                                                peer_port = port

                        self.logger(level="debug", message="Setting wire for FEX " + str(fex._parent.id) +
                                                           ", width : " + str(wire_width))
                        if point_fi:
                            # draw_wire(self.draw, point_fi, point_fex, wire_color, wire_width)
                            target = point_fex[0], fex.picture_offset[1] - int(fex_port.id) * round(
                                400 / 8) + round(400 / 8 / 2)
                            self.wires.append(UcsSystemDrawWire(self, (point_fi, point_fex), wire_width,
                                                                easyucs_fabric_port=peer_port._parent,
                                                                extra_points=[target]))
                            # self.wires = remove_not_completed_in_list(self.wires)
                        else:
                            self.logger(level="error", message="Peer not found")

        # Handling wires from mgmt interface to FEX
        if self.fex_presence:
            # Determine if the rack connection to FEX is dual wire mode (shared-lom) or single wire (sideband)
            if hasattr(self.rack._parent, "mgmt_connection_type") and \
                    self.rack._parent.mgmt_connection_type == "shared-lom":
                for mgmt_port in self.rack.mgmt_if_list:
                    peer_port_id = mgmt_port.peer['port']

                    point_rack = mgmt_port.coord[0] + round(mgmt_port.size[0] / 2), mgmt_port.coord[
                        1] + round(mgmt_port.size[1] / 2)

                    wire_width = self.WIDTH_WIRE

                    if str(mgmt_port.peer['fex']) == '1':
                        fex = self.fex_a
                        fabric = "a"
                    else:
                        fex = self.fex_b
                        fabric = "b"
                    # Find and calculate coordinates of the peer point on the FEX
                    point_fex = None
                    for port in fex.host_port_list:
                        if int(port.id) == peer_port_id:
                            # Even / odd
                            point_fex = port.coord[0] + round(port.size[0] / 3) + (
                                peer_port_id + 1) % 2 * round(
                                port.size[0] / 3), port.coord[1] + round(
                                port.size[1] / 2)
                            peer_port = port

                    if point_fex:
                        # draw_wire(self.draw, point_fi, point_chassis, wire_color, wire_width)
                        # self.wires.append(UcsSystemDrawWire(self, (point_fi, point_rack), wire_width,
                        #                                  easyucs_fi_port=port._parent))
                        if fabric == "a":
                            if int(mgmt_port.id) % 2:
                            # if (int(mgmt_port._parent.port_id) % 2) :
                                step = self.WIRE_DISTANCE_LONG + round(mgmt_port.size[1] / 2)
                            else:
                                step = self.WIRE_DISTANCE_SHORT + round(mgmt_port.size[1] / 2)
                        if fabric == "b":
                            if int(mgmt_port.id) % 2:
                                step = - self.WIRE_DISTANCE_SHORT - round(mgmt_port.size[1] / 2)
                            else:
                                step = - self.WIRE_DISTANCE_LONG - round(mgmt_port.size[1] / 2)
                        target = point_rack[0], point_rack[1] + step
                        self.wires.append(UcsSystemDrawWire(self, (point_fex, point_rack), wire_width,
                                                            extra_points=[target],
                                                            easyucs_fabric_port=peer_port._parent))
                        # self.wires = remove_not_completed_in_list(self.wires)
                    else:
                        self.logger(level="error", message="Peer not found")


class GenericDrawRackEnclosureFront(GenericUcsDrawEquipment):
    def __init__(self, parent=None, orientation="front"):
        GenericUcsDrawEquipment.__init__(self, parent=parent, orientation=orientation)
        if not self.picture:
            return
        self.background = self._create_background(self.canvas_width, self.canvas_height, self.canvas_color)
        self.draw = self._create_draw()

        self.paste_layer(self.picture, self.picture_offset)

        self.disk_slots_used = []

        self.server_nodes_list = self.get_server_nodes()

        self.fill_blanks()

    def fill_blanks(self):
        # Fill blank for disks slots
        potential_slot = [*range(1, len(self.json_file["disks_slots"]) + 1)]
        used_slot = self.disk_slots_used
        unused_slot = []
        for blank_id in set(potential_slot) - set(used_slot):
            unused_slot.append(blank_id)
        for slot_id in unused_slot:
            blank_name = None
            orientation = "horizontal"
            disk_format = None
            coord = [0,0]
            for disk_slot in self.json_file['disks_slots']:
                if disk_slot['id'] == slot_id:
                    orientation = disk_slot['orientation']
                    disk_format = disk_slot['format']
                    coord = disk_slot["coord"]
            for model in self.json_file["disks_models"]:
                if "type" in model and not blank_name:
                    if model["type"] == "blank" and model["format"] == disk_format:
                        blank_name = model["name"]
                        img = Image.open("catalog/drives/img/" + blank_name + ".png", 'r')
                        if orientation == "vertical":
                            img = GenericUcsDrawEquipment.rotate_object(picture=img)
            if blank_name:
                coord_offset = self.picture_offset[0] + coord[0], self.picture_offset[1] + coord[1]
                self.paste_layer(img, coord_offset)

    def get_server_nodes(self):
        server_node_list = []
        for server_node in self._parent.server_nodes:
            server_node_list.append(UcsSystemDrawServerNodeFront(server_node, self))
        # server_node_list = remove_not_completed_in_list(server_node_list)
        return server_node_list


class UcsSystemDrawRackEnclosureFront(GenericDrawRackEnclosureFront):
    def __init__(self, parent=None):
        GenericDrawRackEnclosureFront.__init__(self, parent=parent, orientation="front")
        if not self.picture:
            return

        self._file_name = self._device_target + "_rack_enclosure_" + self._parent.id + "_front"


class UcsImcDrawRackEnclosureFront(GenericDrawRackEnclosureFront):
    def __init__(self, parent=None):
        GenericDrawRackEnclosureFront.__init__(self, parent=parent)
        if not self.picture:
            return

        self._file_name = self._device_target + "_rack_enclosure_front"
        self.paste_cover()

    def paste_cover(self):
        # WORK ONLY FOR C4200
        if self.server_nodes_list:
            slot_id = self.server_nodes_list[0]._parent.slot_id

            img = Image.open("catalog/misc/C4200_covers/C4200_front_cover_" + slot_id + ".png", 'r')
            self.paste_layer(img, (self.picture_offset[0], self.picture_offset[1]))


class GenericDrawRackEnclosureRear(GenericUcsDrawEquipment):
    def __init__(self, parent=None, color_ports=True, orientation="rear"):
        self.color_ports = color_ports
        GenericUcsDrawEquipment.__init__(self, parent=parent, orientation=orientation)
        if not self.picture:
            return
        self.background = self._create_background(self.canvas_width, self.canvas_height, self.canvas_color)
        self.draw = self._create_draw()

        self.paste_layer(self.picture, self.picture_offset)

        self.disk_slots_used = []

        self.server_nodes_list = self.get_server_nodes()
        self.psu_list = self.get_psu_list()

        self.fill_blanks()

    def get_server_nodes(self):
        server_node_list = []
        for server_node in self._parent.server_nodes:
            server_node_list.append(UcsSystemDrawServerNodeRear(server_node, self, color_ports=self.color_ports))
        # server_node_list = remove_not_completed_in_list(server_node_list)
        return server_node_list

    def get_psu_list(self):
        psu_list = []
        for psu in self._parent.power_supplies:
            if psu.id != '0':  # UCS PE sometimes adds an invalid PSU with ID 0
                psu_list.append(UcsPsuDraw(psu, self))
        # psu_list = remove_not_supported_in_list(psu_list)
        # psu_list = remove_not_completed_in_list(psu_list)
        # We only keep the PSU that have been fully created -> picture
        psu_list = [psu for psu in psu_list if psu.picture_size]
        return psu_list

    def fill_blanks(self):
        if "psus_slots_rear" in self.json_file:
            # Fill blank for rear PSU Slot
            if len(self._parent.power_supplies)-1 < len(self.json_file["psus_slots_rear"]):
                used_slot = []
                potential_slot = []
                unused_slot = []
                for slot in self._parent.power_supplies:
                    used_slot.append(int(slot.id))
                for slot in self.json_file["psus_slots_rear"]:
                    potential_slot.append(slot["id"])
                for blank_id in set(potential_slot) - set(used_slot):
                    unused_slot.append(blank_id)
                for slot_id in unused_slot:
                    for expansion in self.json_file["psus_models"]:
                        if "type" in expansion:
                            if expansion["type"] == "blank":
                                blank_name = expansion["name"]
                                img = Image.open("catalog/power_supplies/img/" + blank_name + ".png", 'r')
                                for slot in self.json_file["psus_slots_rear"]:
                                    if slot["id"] == int(slot_id):
                                        coord = slot["coord"]
                                coord_offset = self.picture_offset[0] + coord[0], self.picture_offset[1] + coord[1]
                                self.paste_layer(img, coord_offset)

        if "server_node_slots" in self.json_file:
            # Fill blank for rear PSU Slot
            if len(self._parent.server_nodes)-1 < len(self.json_file["server_node_slots"]):
                used_slot = []
                potential_slot = []
                unused_slot = []
                for slot in self._parent.server_nodes:
                    used_slot.append(int(slot.slot_id))
                for slot in self.json_file["server_node_slots"]:
                    potential_slot.append(slot["id"])
                for blank_id in set(potential_slot) - set(used_slot):
                    unused_slot.append(blank_id)
                for slot_id in unused_slot:
                    for expansion in self.json_file["server_node_models"]:
                        if "type" in expansion:
                            if expansion["type"] == "blank":
                                blank_name = expansion["name"]
                                img = Image.open("catalog/server_nodes/img/" + blank_name + ".png", 'r')
                                for slot in self.json_file["server_node_slots"]:
                                    if slot["id"] == int(slot_id):
                                        coord = slot["coord"]
                                coord_offset = self.picture_offset[0] + coord[0], self.picture_offset[1] + coord[1]
                                self.paste_layer(img, coord_offset)

        # TODO for Server Node


class UcsSystemDrawRackEnclosureRear(GenericDrawRackEnclosureRear):
    def __init__(self, parent=None, color_ports=True):
        self.color_ports = color_ports
        GenericDrawRackEnclosureRear.__init__(self, parent=parent, orientation="rear", color_ports=self.color_ports)
        if not self.picture:
            return

        self._file_name = self._device_target + "_rack_enclosure_" + self._parent.id + "_rear"

        if not self.color_ports:
            self._file_name = self._device_target + "_rack_enclosure_" + self._parent.id + "_rear_clear"

        if self.color_ports:
            self.clear_version = UcsSystemDrawRackEnclosureRear(parent=parent, color_ports=False)


class UcsImcDrawRackEnclosureRear(GenericDrawRackEnclosureRear):
    def __init__(self, parent=None, color_ports=True):
        self.color_ports = color_ports
        GenericDrawRackEnclosureRear.__init__(self, parent=parent, orientation="rear", color_ports=self.color_ports)
        if not self.picture:
            return

        self._file_name = self._device_target + "_rack_enclosure_rear"
        self.paste_cover()

    def paste_cover(self):
        # WORK ONLY FOR C4200
        if self.server_nodes_list:
            slot_id = self.server_nodes_list[0]._parent.slot_id

            img = Image.open("catalog/misc/C4200_covers/C4200_rear_cover_" + slot_id + ".png", 'r')
            self.paste_layer(img, (self.picture_offset[0], self.picture_offset[1]))


class UcsSystemDrawServerNodeFront(GenericUcsDrawEquipment):
    def __init__(self, parent=None, parent_draw=None):
        # GenericUcsDrawEquipment.__init__(self, parent=parent, orientation="front")
        self.parent_draw = parent_draw
        self._parent = parent
        self._parent_having_logger = self._find_logger()
        self._get_json_file()

        self.disk_slots_used = []

        # We use the parent draw here
        self.picture = self.parent_draw.picture
        self.picture_offset = self.parent_draw.picture_offset
        self.background = self.parent_draw.background
        self.draw = self.parent_draw.draw

        self.json_file["disks_slots"] = self.add_disks_slots_to_json_file()
        self.json_file["disks_models"] = self.parent_draw.json_file["disks_models"]

        # self.parent_draw.paste_layer(self.picture, self.picture_offset)

        self.storage_controllers = self._get_storage_controllers()

        self.parent_draw.disk_slots_used = self.parent_draw.disk_slots_used + [i + (6 * (int(self._parent.slot_id) - 1)) for i in self.disk_slots_used]
        # self.fill_blanks()

    def add_disks_slots_to_json_file(self):
        parent_disks_slots = copy.deepcopy(self.parent_draw.json_file["disks_slots"])
        first = 6 * (int(self._parent.slot_id) - 1)
        last = first + 6
        disks_slots = parent_disks_slots[first: last]
        for i in range(1, 7):
            disks_slots[i-1]["id"] = i
        return disks_slots

    def _get_storage_controllers(self):
        storage_controller_list = []
        # TODO : Check if this condition still needs to be here
        if (self._parent.sku != "UCSC-C3X60-SVRNB") and (self._parent.sku != "UCSC-C3K-M4SRB"):
            for storage_controller in self._parent.storage_controllers:
                # We skip M.2 controllers on M5 server nodes
                if any(x in self._parent.sku for x in ["M5", "C125"]) and \
                        (storage_controller.type not in ["Hba", "HBA", "Raid", "RAID", "SAS", "Nvme", "NVME"]):
                    continue
                storage_controller_list.append(UcsStorageControllerDraw(storage_controller, self))
                # storage_controller_list = remove_not_completed_in_list(storage_controller_list)
        return storage_controller_list


class UcsSystemDrawServerNodeRear(GenericUcsDrawEquipment):
    def __init__(self, parent=None, parent_draw=None, color_ports=True):
        self.parent_draw = parent_draw
        self.color_ports = color_ports
        GenericUcsDrawEquipment.__init__(self, parent=parent, orientation="rear")
        if not self.picture:
            return

        # self.disk_slots_used = []

        if not self.parent_draw:
            self.background = self._create_background(self.canvas_width, self.canvas_height, self.canvas_color)
            self.draw = self._create_draw()

        self.parent_draw.paste_layer(self.picture, self.picture_offset)

        # We use the parent draw here for an easier pasting of the layer in the adaptor code
        self.draw = self.parent_draw.draw
        self.background = self.parent_draw.background
        self.adaptor_list = self.get_adaptor_list()

        self.fill_blanks()

    def fill_blanks(self):
        len_ocp = 0
        if "ocp_slots" in self.json_file:
            len_ocp = len(self.json_file["ocp_slots"])
        if len(self.adaptor_list) < (len(self.json_file["pcie_slots"]) + len_ocp):
            ocp_used_slot = []
            ocp_potential_slot = []
            ocp_unused_slot = []

            pcie_used_slot = []
            pcie_potential_slot = []
            pcie_potential_slot_info = []
            pcie_unused_slot = []

            for slot in self._parent.adaptors:
                if slot.pci_slot == "OCP" and len_ocp:
                    ocp_used_slot.append(1)
                elif slot.pci_slot.isdigit():
                    pcie_used_slot.append(int(slot.pci_slot))

            for slot in self.json_file["pcie_slots"]:
                # slot = id, width
                pcie_potential_slot.append(slot["id"])
                width = "full"
                orientation = "horizontal"
                if "width" in slot:
                    width = slot["width"]
                if "orientation" in slot:
                    orientation = slot["orientation"]
                pcie_potential_slot_info.append((slot["id"], width, orientation))

            if len_ocp:
                for slot in self.json_file["ocp_slots"]:
                    ocp_potential_slot.append(slot["id"])

            for blank_id in set(pcie_potential_slot) - set(pcie_used_slot):
                pcie_unused_slot.append(blank_id)

            if len_ocp:
                for blank_id in set(ocp_potential_slot) - set(ocp_used_slot):
                    ocp_unused_slot.append(blank_id)

            for slot_id in pcie_unused_slot:
                for triple in pcie_potential_slot_info:  # Search for width of the slot
                    if triple[0] == slot_id:
                        width = triple[1]
                        orientation = triple[2]
                for expansion in self.json_file["pcie_models"]:
                    if "type" in expansion:
                        if expansion["type"] == "blank" and expansion['width'] == width:
                            blank_name = expansion["name"]
                            img = Image.open("catalog/adaptors/img/" + blank_name + ".png", 'r')
                            if orientation == "reverse":
                                img = self.rotate_object(picture=img)
                                img = self.rotate_object(picture=img)
                            elif orientation == "vertical":
                                img = self.rotate_object(picture=img)
                                img = self.rotate_object(picture=img)
                                img = self.rotate_object(picture=img)
                            for slot in self.json_file["pcie_slots"]:
                                if slot["id"] == int(slot_id):
                                    coord = slot["coord"]
                            coord_offset = self.picture_offset[0] + coord[0], self.picture_offset[1] + coord[1]
                            self.paste_layer(img, coord_offset)

            if len_ocp:  # if OCP slot present
                for slot_id in ocp_unused_slot:
                    for expansion in self.json_file["ocp_models"]:
                        if "type" in expansion:
                            if expansion["type"] == "blank":
                                blank_name = expansion["name"]
                                img = Image.open("catalog/adaptors/img/" + blank_name + ".png", 'r')
                                for slot in self.json_file["ocp_slots"]:
                                    if slot["id"] == int(slot_id):
                                        coord = slot["coord"]
                                coord_offset = self.picture_offset[0] + coord[0], self.picture_offset[1] + coord[1]
                                self.paste_layer(img, coord_offset)

    def get_adaptor_list(self):
        adaptor_list = []
        for adaptor in self._parent.adaptors:
            if adaptor.pci_slot not in ["L", "N/A"]:
                adaptor_list.append(UcsAdaptorDraw(parent=adaptor, parent_draw=self))
        # adaptor_list = remove_not_supported_in_list(adaptor_list)
        # adaptor_list = remove_not_completed_in_list(adaptor_list)
        # We only keep the adaptor that have been fully created -> picture
        adaptor_list = [adaptor for adaptor in adaptor_list if adaptor.picture_size]
        return [e for e in adaptor_list if hasattr(e, "_parent")]

    def _get_picture_offset(self):
        if "server_node_slots" in self.parent_draw.json_file:
            slots = self.parent_draw.json_file["server_node_slots"]

        server_slot_id = int(self._parent.slot_id)
        for slot in slots:
            if slot["id"] == server_slot_id:
                coord = slot["coord"]
        return self.parent_draw.picture_offset[0] + coord[0], self.parent_draw.picture_offset[1] + coord[1]


class UcsSystemDrawInfraRackEnclosure(UcsSystemDrawInfraEquipment):
    def __init__(self, rack_enclosure, fi_list, fex_list=None, parent=None):

        UcsSystemDrawInfraEquipment.__init__(self, parent=parent)
        # Create a copy of the DrawRack
        if 'Rear' in rack_enclosure.__class__.__name__:
            self.rack_enclosure = UcsSystemDrawRackEnclosureRear(parent=rack_enclosure._parent)
        else:
            self.rack_enclosure = UcsSystemDrawRackEnclosureFront(parent=rack_enclosure._parent)

        self.fi_a = self._get_fi(fi_list, "A")
        self.fi_b = self._get_fi(fi_list, "B")

        self.fex_presence = None
        if fex_list:
            self.fex_presence = self._get_fex_infra_presence()
            if self.fex_presence:
                self.fex_list = self._get_fex(fex_list)
                self.fex_a = self.fex_list[0]
                self.fex_b = self.fex_list[1]
                if self.fex_a:
                    self.valid_fex = self.fex_a
                elif self.fex_b:
                    self.valid_fex = self.fex_b
                else:
                    self.logger(level="warning", message="Infra of rack enclosure #" + self.rack_enclosure._parent.id +
                                                         " not saved because FEX presence confirmed "
                                                         "but could not be found")
                    return None

        # Canvas settings
        if self.fex_presence:
            # self.canvas_width = self.fi_a.picture_size[0] * 2 + self.rack.picture_size[0] + self.fex_a.picture_size[0] * 2 + 200  # arbitrary
            self.canvas_width = self.rack_enclosure.picture_size[0] + self.valid_fex.picture_size[0] * 2 + 100  # arbitrary
            self.canvas_height = self.fi_a.picture_size[1] + self.rack_enclosure.picture_size[1] + \
                                 self.valid_fex.picture_size[1] + 400  # arbitrary
        else:
            self.canvas_width = self.fi_a.picture_size[0] * 2 + self.rack_enclosure.picture_size[0] + 100  # arbitrary
            self.canvas_height = self.fi_a.picture_size[1] + self.rack_enclosure.picture_size[1] + 100  # arbitrary
        self.canvas_color = (255, 255, 255, 255)  # white

        self.rack_offset = self._get_picture_offset("rack")
        self.fi_a_offset = self._get_picture_offset("fi_a")
        if self.fi_b:
            self.fi_b_offset = self._get_picture_offset("fi_b")
        if self.fex_presence:
            if self.fex_a:
                self.fex_a_offset = self._get_picture_offset("fex_a")
            if self.fex_b:
                self.fex_b_offset = self._get_picture_offset("fex_b")

        self.background = self._create_background(self.canvas_width, self.canvas_height, self.canvas_color)
        self.draw = self._create_draw()

        # Paste layers
        # As we drop the picture before, we need to recreate it and drop it again after pasting the layer
        self.rack_enclosure._get_picture()
        self.paste_layer(self.rack_enclosure.picture, self.rack_offset)
        self.rack_enclosure.picture = None

        self.fi_a._get_picture()
        self.paste_layer(self.fi_a.picture, self.fi_a_offset)
        self.fi_a.picture = None

        if self.fi_b:
            self.fi_b._get_picture()
            self.paste_layer(self.fi_b.picture, self.fi_b_offset)
            self.fi_b.picture = None
        if self.fex_presence:
            if self.fex_a:
                self.fex_a._get_picture()
                self.paste_layer(self.fex_a.picture, self.fex_a_offset)
                self.fex_a.picture = None
            if self.fex_b:
                self.fex_b._get_picture()
                self.paste_layer(self.fex_b.picture, self.fex_b_offset)
                self.fex_b.picture = None

        # Draw ports and expansion
        self.fi_a.draw = self.draw
        self.fi_a.background = self.background
        self.fi_a.picture_offset = self.fi_a_offset
        self.fi_a.ports = []
        self.fi_a.draw_ports(True)
        self.fi_a.gem_list = self.fi_a.get_expansion_modules()
        self.fi_a.fill_blanks()

        if self.fi_b:  # if FI B is present
            self.fi_b.draw = self.draw
            self.fi_b.background = self.background
            self.fi_b.picture_offset = self.fi_b_offset
            self.fi_b.ports = []
            self.fi_b.draw_ports(True)
            self.fi_b.gem_list = self.fi_b.get_expansion_modules()
            self.fi_b.fill_blanks()

        if self.fex_presence:
            if self.fex_a:
                self.fex_a.draw = self.draw
                self.fex_a.background = self.background
                self.fex_a.picture_offset = self.fex_a_offset
                self.fex_a.fabric_port_list = []
                self.fex_a.host_port_list = []
                self.fex_a.draw_ports()
            if self.fex_b:
                self.fex_b.draw = self.draw
                self.fex_b.background = self.background
                self.fex_b.picture_offset = self.fex_b_offset
                self.fex_b.fabric_port_list = []
                self.fex_b.host_port_list = []
                self.fex_b.draw_ports()

        self.rack_enclosure.draw = self.draw
        self.rack_enclosure.background = self.background
        self.rack_enclosure.picture_offset = self.rack_offset
        self.rack_enclosure.psu_list = self.rack_enclosure.get_psu_list()
        self.server_nodes_list = self.rack_enclosure.get_server_nodes()
        self.rack_enclosure.fill_blanks()

        self.wires = []
        self.set_wire()

        # For the legend of ports
        self.port_color_list = self.fi_a.legend_items
        if self.fi_b:
            self.port_color_list = self.fi_b.legend_items + self.port_color_list
        self.port_color_list = set(self.port_color_list)  # Delete duplication

        # For the legend of wires
        self.wire_color_list = []
        for wire in self.wires:
            self.wire_color_list.append(wire.color)
        self.wire_color_list = set(self.wire_color_list)

        self.draw_port_wire_legend(self, self.port_color_list, self.wire_color_list)
        # self.draw_rack_info()

        # if there is no wire at all, there is no need to save the picture
        if self.wires:
            self._file_name = self._device_target + "_infra_rack_enclosure_" + self.rack_enclosure._parent.id
        else:
            self.logger(level="warning", message="Infra of rack enclosure #" + self.rack_enclosure._parent.id +
                                                 " not saved because no connection between the FI and the rack")

        # We drop the picture in order to save on memory
        self.picture = None

    def _get_fex_infra_presence(self):
        # Used to know if a FEX need to be used for this infra
        for server_node in self.rack_enclosure.server_nodes_list:
            for adaptor in server_node.adaptor_list:
                for adapt_port in adaptor.ports:
                    # Search for peer information
                    if hasattr(adapt_port, "peer"):
                        if adapt_port.peer:
                            if "fex" in adapt_port.peer:
                                return True
            for mgmt_if in server_node._parent.mgmt_interfaces:
                if hasattr(mgmt_if, "peer"):
                    if mgmt_if.peer:
                        if "fex" in mgmt_if.peer:
                            return True
        return False

    def _get_fex(self, list):
        fex_id_list = []
        for server_node in self.rack_enclosure.server_nodes_list:
            for mgmt_if in server_node._parent.mgmt_interfaces:
                if hasattr(mgmt_if, "peer"):
                    if mgmt_if.peer:
                        if "fex" in mgmt_if.peer:
                            fex_id_list.append(str(mgmt_if.peer["fex"]))
        fex_list = [None, None]
        for id in fex_id_list:
            for fex in list:
                if fex._parent.id == id:
                    if fex._parent.switch_id == 'A':
                        fex_list[0] = copy.copy(fex)
                    elif fex._parent.switch_id == 'B':
                        fex_list[1] = copy.copy(fex)
        return fex_list

    def _get_fi(self, fi_list, id):
        fabric = None
        for fi in fi_list:
            if fi._parent.id == id:
                fabric = fi
            if fi._parent.id == id:
                fabric = fi
        return copy.copy(fabric)

    def _get_picture_offset(self, type):
        if type == "rack":
            return round(self.canvas_width / 2 - self.rack_enclosure.picture_size[0] / 2), self.canvas_height - \
                   self.rack_enclosure.picture_size[1]

        if type == "fi_a":
            return 0, 0

        if type == "fi_b":
            return self.canvas_width - self.fi_b.picture_size[0], 0

        if type == "fex_a":
            # return self.fi_a.picture_size[0] + 50, self.fi_a.picture_size[1] + 100
            return 0, self.fi_a.picture_size[1] + 400

        if type == "fex_b":
            # return self.canvas_width - self.fex_b.picture_size[0] - self.fi_a.picture_size[0] - 50, self.fi_a.picture_size[1] + 100
            return self.canvas_width - self.fex_b.picture_size[0], self.fi_a.picture_size[1] + 400

    def draw_rack_info(self):
        fill_color = "black"
        font_size = 60
        font_title = ImageFont.truetype('arial.ttf', font_size)

        if self.rack_enclosure._parent.user_label:
            msg = "Rack #" + self.rack_enclosure._parent.id + " - " + self.rack_enclosure._parent.user_label
        else:
            msg = "Rack #" + self.rack_enclosure._parent.id

        w = self.draw.textlength(msg, font=font_title)
        # 16 px space between text and equipment
        self.draw.text((round(self.canvas_width / 2 - w / 2), self.rack_offset[1] - (font_size + 16)), msg,
                       fill=fill_color, font=font_title)

        if self.fex_presence:
            if self.fex_a:
                msg = "Fex #" + self.fex_a._parent.id
                w = self.draw.textlength(msg, font=font_title)
                # 16 px space between text and equipment
                self.draw.text((self.fex_a.picture_size[0] - w, self.fex_a_offset[1] - (font_size + 16)), msg,
                               fill=fill_color, font=font_title)

            if self.fex_b:
                msg = "Fex #" + self.fex_b._parent.id
                w = self.draw.textlength(msg, font=font_title)
                # 16 px space between text and equipment
                self.draw.text((self.canvas_width - self.fex_b.picture_size[0],
                                self.fex_b_offset[1] - (font_size + 16)), msg, fill=fill_color, font=font_title)

    def set_wire(self):
        # Handling wire from server to FI or FEX
        for server_node in self.rack_enclosure.server_nodes_list:
            for adaptor in server_node.adaptor_list:
                for adapt_port in adaptor.ports:
                    # Search for peer information
                    if hasattr(adapt_port, "peer"):
                        peer = adapt_port.peer
                        peer_fex = None
                        peer_fi = None
                        if "fex" in peer:
                            peer_fex = peer["fex"]
                            if hasattr(self, "fex_a"):
                                if self.fex_a:
                                    if self.fex_a._parent.id == str(peer_fex):
                                        fex = self.fex_a
                                        fabric = "a"
                            if hasattr(self, "fex_b"):
                                if self.fex_b:
                                    if self.fex_b._parent.id == str(peer_fex):
                                        fex = self.fex_b
                                        fabric = "b"
                            if not hasattr(self, "fex_a") and not hasattr(self, "fex_b"):
                                return None
                        elif "switch" in peer:
                            peer_fi = peer["switch"]
                            if peer_fi == "A":  # if FI A
                                fi = self.fi_a
                                fabric = "a"
                            if peer_fi == "B":  # if FI B
                                fi = self.fi_b
                                fabric = "b"
                        peer_slot_id = peer["slot"]
                        peer_port_id = peer["port"]
                        if "aggr_port" in peer:
                            peer_aggr_id = peer["aggr_port"]
                        else:
                            peer_aggr_id = None

                        wire_width = self.WIDTH_WIRE  # Set the default wire width

                        point_breakout = None
                        adapt_port.coord = adapt_port.coord[0] + self.rack_offset[0], \
                                           adapt_port.coord[1] + self.rack_offset[1]
                        if not adapt_port._parent.is_breakout:
                            point_rack = adapt_port.coord[0] + round(adapt_port.size[0] / 2), \
                                         adapt_port.coord[1] + round(adapt_port.size[1] / 2)
                        else:
                            wire_width = self.WIDTH_WIRE_BREAKOUT
                            point_breakout = adapt_port.coord[0] + round(adapt_port.size[0] / 2), \
                                             adapt_port.coord[1] + round(adapt_port.size[1] / 2)

                            if fabric == "a":
                                if int(adaptor._parent.id) == 1:
                                    point_rack = adapt_port.coord[0] - (int(adapt_port.id) - 1) % 4 * adapt_port.size[0] + \
                                                 adapt_port.size[0] * 2, \
                                                 adapt_port.coord[1] + adapt_port.size[1] + self.WIRE_DISTANCE_SHORT
                                if int(adaptor._parent.id) == 2:
                                    point_rack = adapt_port.coord[0] - (int(adapt_port.id) - 1) % 4 * adapt_port.size[0] + \
                                                 adapt_port.size[0] * 2, \
                                                 adapt_port.coord[1] + adapt_port.size[1] + self.WIRE_DISTANCE_LONG
                            elif fabric == "b":
                                if int(adaptor._parent.id) == 1:
                                    point_rack = adapt_port.coord[0] - (int(adapt_port.id) - 1) % 4 * adapt_port.size[0] + \
                                                 adapt_port.size[0] * 2, \
                                                 adapt_port.coord[1] - self.WIRE_DISTANCE_LONG
                                if int(adaptor._parent.id) == 2:
                                    point_rack = adapt_port.coord[0] - (int(adapt_port.id) - 1) % 4 * adapt_port.size[0] + \
                                                 adapt_port.size[0] * 2, \
                                                 adapt_port.coord[1] - self.WIRE_DISTANCE_SHORT

                        # Find and calculate coordinates of the peer point on the FI
                        if peer_fi:
                            point_fi = None
                            if peer_slot_id == 1:
                                for port in fi.ports:
                                    if peer_aggr_id:
                                        if int(port.id) == peer_port_id:
                                            if port.aggr_id:
                                                wire_width = self.WIDTH_WIRE_BREAKOUT
                                                if int(port.aggr_id) == peer_aggr_id:
                                                    # Even / odd
                                                    point_fi = port.coord[0] + round(port.size[0] / 3) + (
                                                        peer_aggr_id + 1) % 2 * round(
                                                        port.size[0] / 3) - ((peer_aggr_id + 1) % 2), port.coord[1] + round(
                                                        port.size[1] / 2)
                                                    peer_port = port
                                    else:
                                        if (int(port.id) == peer_port_id) and port.aggr_id is None:
                                            # Even / odd
                                            point_fi = port.coord[0] + round(port.size[0] / 3) + (
                                                        peer_port_id + 1) % 2 * round(port.size[0] / 3), port.coord[
                                                           1] + round(port.size[1] / 2)
                                            peer_port = port

                            else:
                                for gem in fi.gem_list:
                                    if int(gem._parent.id) == peer_slot_id:
                                        for port in gem.ports:
                                            if peer_aggr_id:
                                                if int(port.id) == peer_port_id:
                                                    if port.aggr_id:
                                                        wire_width = 5
                                                        if int(port.aggr_id) == peer_aggr_id:
                                                            # Even / odd
                                                            point_fi = port.coord[0] + round(port.size[0] / 3) + (
                                                                        peer_aggr_id + 1) % 2 * round(port.size[0] / 3) - (
                                                                                   (peer_aggr_id + 1) % 2), port.coord[
                                                                           1] + round(port.size[1] / 2)
                                                            peer_port = port
                                            else:
                                                if (int(port.id) == peer_port_id) and port.aggr_id is None:
                                                    # Even / odd
                                                    point_fi = port.coord[0] + round(port.size[0] / 3) + (
                                                                peer_port_id + 1) % 2 * round(port.size[0] / 3), port.coord[
                                                                   1] + round(port.size[1] / 2)
                                                    peer_port = port

                            self.logger(level="debug", message="Setting wire for rack " + self.rack_enclosure._parent.id +
                                                               ", width : " + str(wire_width))
                            if point_fi:
                                # draw_wire(self.draw, point_fi, point_rack, wire_color, wire_width)
                                if point_breakout:
                                    self.wires.append(
                                        UcsSystemDrawWire(self, (point_rack, point_breakout), wire_width,
                                                          easyucs_fabric_port=peer_port._parent, line_type="straight"))
                                    self.wires.append(UcsSystemDrawWire(self, (point_fi, point_rack), wire_width,
                                                                        easyucs_fabric_port=peer_port._parent))
                                    # self.wires = remove_not_completed_in_list(self.wires)

                                    fill_color = "black"
                                    font_size = 40
                                    font_title = ImageFont.truetype('arial.ttf', font_size)
                                    self.draw.text((point_fi[0] - 30, point_rack[1] - 45), adapt_port.id, fill=fill_color,
                                                   font=font_title)

                                else:
                                    # draw_wire(self.draw, point_fi, point_chassis, wire_color, wire_width)
                                    # self.wires.append(UcsSystemDrawWire(self, (point_fi, point_rack), wire_width,
                                    #                                  easyucs_fi_port=port._parent))
                                    # When a card is a quad port
                                    if "-C25Q-04" in adapt_port._parent._parent.sku:
                                        wire_width = self.WIDTH_WIRE_BREAKOUT
                                        if fabric == "a":
                                            if int(adaptor._parent.id) % 2:
                                                if int(adapt_port.id) % 2:
                                                    step = self.WIRE_DISTANCE_SHORT + round(adapt_port.size[1]/2)
                                                else:
                                                    step = self.WIRE_DISTANCE_LONG + round(adapt_port.size[1] / 2)
                                            else:
                                                if int(adapt_port.id) % 2:
                                                    step = self.WIRE_DISTANCE_SHORT + round(adapt_port.size[1]/2)
                                                else:
                                                    step = self.WIRE_DISTANCE_LONG + round(adapt_port.size[1] / 2)
                                        if fabric == "b":
                                            if int(adaptor._parent.id) % 2:
                                                if int(adapt_port.id) % 2:
                                                    step = - self.WIRE_DISTANCE_LONG - round(adapt_port.size[1]/2)
                                                else:
                                                    step = - self.WIRE_DISTANCE_SHORT - round(adapt_port.size[1] / 2)
                                            else:
                                                if int(adapt_port.id) % 2:
                                                    step = - self.WIRE_DISTANCE_LONG - round(adapt_port.size[1]/2)
                                                else:
                                                    step = - self.WIRE_DISTANCE_SHORT - round(adapt_port.size[1] / 2)
                                    # for all the non quad port cards
                                    else:
                                        if fabric == "a":
                                            if int(adaptor._parent.id) % 2:
                                            # if (int(adapt_port._parent.port_id) % 2):
                                                step = self.WIRE_DISTANCE_SHORT + round(adapt_port.size[1]/2)
                                            else:
                                                step = self.WIRE_DISTANCE_LONG + round(adapt_port.size[1]/2)
                                        if fabric == "b":
                                            if int(adaptor._parent.id) % 2:
                                                step = - self.WIRE_DISTANCE_LONG - round(adapt_port.size[1]/2)
                                            else:
                                                step = - self.WIRE_DISTANCE_SHORT - round(adapt_port.size[1]/2)
                                    target = point_rack[0], point_rack[1] + step
                                    self.wires.append(UcsSystemDrawWire(self, (point_fi, point_rack), wire_width,
                                                                        extra_points=[target],
                                                                        easyucs_fabric_port=peer_port._parent))
                                    # self.wires = remove_not_completed_in_list(self.wires)
                            else:
                                self.logger(level="error", message="Peer not found")

                        if peer_fex:
                            # Find and calculate coordinates of the peer point on the FEX
                            point_fex = None
                            for port in fex.host_port_list:
                                if (int(port.id) == peer_port_id) and port.aggr_id is None:
                                    # Even / odd
                                    point_fex = port.coord[0] + round(port.size[0] / 3) + (
                                        peer_port_id + 1) % 2 * round(
                                        port.size[0] / 3), port.coord[1] + round(
                                        port.size[1] / 2)
                                    peer_port = port

                            self.logger(level="debug", message="Setting wire for rack " + self.rack_enclosure._parent.id +
                                                               ", width : " + str(wire_width))
                            if point_fex:
                                # draw_wire(self.draw, point_fex, point_rack, wire_color, wire_width)
                                if point_breakout:
                                    self.wires.append(
                                        UcsSystemDrawWire(self, (point_rack, point_breakout), wire_width,
                                                          easyucs_fabric_port=peer_port._parent, line_type="straight"))
                                    self.wires.append(UcsSystemDrawWire(self, (point_fex, point_rack), wire_width,
                                                                        easyucs_fabric_port=peer_port._parent))
                                    # self.wires = remove_not_completed_in_list(self.wires)

                                    fill_color = "black"
                                    font_size = 40
                                    font_title = ImageFont.truetype('arial.ttf', font_size)
                                    self.draw.text((point_fex[0] - 30, point_rack[1] - 45), adapt_port.id, fill=fill_color,
                                                   font=font_title)

                                else:
                                    # draw_wire(self.draw, point_fi, point_chassis, wire_color, wire_width)
                                    # self.wires.append(UcsSystemDrawWire(self, (point_fi, point_rack), wire_width,
                                    #                                  easyucs_fi_port=port._parent))
                                    # When a card is a quad port
                                    if "-C25Q-04" in adapt_port._parent._parent.sku:
                                        wire_width = self.WIDTH_WIRE_BREAKOUT
                                        if fabric == "a":
                                            if int(adaptor._parent.id) % 2:
                                                if int(adapt_port.id) % 2:
                                                    step = self.WIRE_DISTANCE_SHORT + round(adapt_port.size[1] / 2)
                                                else:
                                                    step = self.WIRE_DISTANCE_LONG + round(adapt_port.size[1] / 2)
                                            else:
                                                if int(adapt_port.id) % 2:
                                                    step = self.WIRE_DISTANCE_SHORT + round(adapt_port.size[1] / 2)
                                                else:
                                                    step = self.WIRE_DISTANCE_LONG + round(adapt_port.size[1] / 2)
                                        if fabric == "b":
                                            if int(adaptor._parent.id) % 2:
                                                if int(adapt_port.id) % 2:
                                                    step = - self.WIRE_DISTANCE_LONG - round(adapt_port.size[1] / 2)
                                                else:
                                                    step = - self.WIRE_DISTANCE_SHORT - round(adapt_port.size[1] / 2)
                                            else:
                                                if int(adapt_port.id) % 2:
                                                    step = - self.WIRE_DISTANCE_LONG - round(adapt_port.size[1] / 2)
                                                else:
                                                    step = - self.WIRE_DISTANCE_SHORT - round(adapt_port.size[1] / 2)
                                    # for all the non quad port cards
                                    else:
                                        if fabric == "a":
                                            if int(adaptor._parent.id) % 2:
                                            # if (int(adapt_port._parent.port_id) % 2):
                                                step = self.WIRE_DISTANCE_SHORT + round(adapt_port.size[1]/2)
                                            else:
                                                step = self.WIRE_DISTANCE_LONG + round(adapt_port.size[1]/2)
                                        if fabric == "b":
                                            if int(adaptor._parent.id) % 2:
                                                step = - self.WIRE_DISTANCE_LONG - round(adapt_port.size[1]/2)
                                            else:
                                                step = - self.WIRE_DISTANCE_SHORT - round(adapt_port.size[1]/2)

                                    target = point_rack[0], point_rack[1] + step
                                    self.wires.append(UcsSystemDrawWire(self, (point_fex, point_rack), wire_width,
                                                                        extra_points=[target],
                                                                        easyucs_fabric_port=peer_port._parent))
                                    # self.wires = remove_not_completed_in_list(self.wires)
                            else:
                                self.logger(level="error", message="Peer not found")

        # Handling wire from FEX to FI
        if self.fex_presence:
            if self.fex_a and self.fex_b:
                fex_list = [self.fex_a, self.fex_b]
            elif self.fex_a:
                fex_list = [self.fex_a]
            elif self.fex_b:
                fex_list = [self.fex_b]
            else:
                fex_list = []
            for fex in fex_list:
                for fex_port in fex.fabric_port_list:
                    # Search for peer information
                    if hasattr(fex_port, 'peer'):
                        peer = fex_port.peer
                    else:
                        peer = fex_port._parent.peer
                    peer_fi = None
                    if "switch" in peer:
                        peer_fi = peer["switch"]
                        if peer_fi == "A":  # if FI A
                            fi = self.fi_a
                        if peer_fi == "B":  # if FI B
                            fi = self.fi_b
                    peer_slot_id = peer["slot"]
                    peer_port_id = peer["port"]
                    if "aggr_port" in peer:
                        peer_aggr_id = peer["aggr_port"]
                    else:
                        peer_aggr_id = None
                    #  int(not(0)) = 1, impair port are placed at a third of the port size, pair at two third
                    point_fex = fex_port.coord[0] + (1 + int(not (int(fex_port.id) % 2))) * round(
                        fex_port.size[0] / 3), fex_port.coord[1] + fex_port.size[1] / 2

                    wire_width = self.WIDTH_WIRE  # Set the default wire width

                    if peer_fi:
                        # Find and calculate coordinates of the peer point on the FI
                        point_fi = None
                        if peer_slot_id == 1:
                            for port in fi.ports:
                                if peer_aggr_id:
                                    if int(port.id) == peer_port_id:
                                        if port.aggr_id:
                                            wire_width = 5
                                            if int(port.aggr_id) == peer_aggr_id:
                                                # Even / odd
                                                point_fi = port.coord[0] + round(port.size[0] / 3) + (
                                                    peer_aggr_id + 1) % 2 * round(
                                                    port.size[0] / 3) - ((peer_aggr_id + 1) % 2), \
                                                           port.coord[1] + round(
                                                               port.size[1] / 2)
                                                peer_port = port
                                else:
                                    if (int(port.id) == peer_port_id) and port.aggr_id is None:
                                        # Even / odd
                                        point_fi = port.coord[0] + round(port.size[0] / 3) + (
                                            peer_port_id + 1) % 2 * round(
                                            port.size[0] / 3), port.coord[1] + round(
                                            port.size[1] / 2)
                                        peer_port = port

                        else:
                            for gem in fi.gem_list:
                                if int(gem._parent.id) == peer_slot_id:
                                    for port in gem.ports:
                                        if peer_aggr_id:
                                            if int(port.id) == peer_port_id:
                                                if port.aggr_id:
                                                    wire_width = 5
                                                    if int(port.aggr_id) == peer_aggr_id:
                                                        # Even / odd
                                                        point_fi = port.coord[0] + round(
                                                            port.size[0] / 3) + (
                                                                       peer_aggr_id + 1) % 2 * round(
                                                            port.size[0] / 3) - ((peer_aggr_id + 1) % 2), \
                                                                   port.coord[
                                                                       1] + round(
                                                                       port.size[1] / 2)
                                                        peer_port = port
                                        else:
                                            if (int(port.id) == peer_port_id) and port.aggr_id is None:
                                                # Even / odd
                                                point_fi = port.coord[0] + round(port.size[0] / 3) + (
                                                    peer_port_id + 1) % 2 * round(
                                                    port.size[0] / 3), port.coord[1] + round(
                                                    port.size[1] / 2)
                                                peer_port = port

                        self.logger(level="debug", message="Setting wire for FEX " + fex._parent.id +
                                                           ", width : " + str(wire_width))
                        if point_fi:
                            # draw_wire(self.draw, point_fi, point_fex, wire_color, wire_width)
                            target = point_fex[0], fex.picture_offset[1] - int(fex_port.id) * round(
                                400 / 8) + round(400 / 8 / 2)
                            self.wires.append(UcsSystemDrawWire(self, (point_fi, point_fex), wire_width,
                                                                easyucs_fabric_port=peer_port._parent,
                                                                extra_points=[target]))
                            # self.wires = remove_not_completed_in_list(self.wires)
                        else:
                            self.logger(level="error", message="Peer not found")

        # Handling wires from mgmt interface to FEX
        if self.fex_presence:
            # Determine if the rack connection to FEX is dual wire mode (shared-lom) or single wire (sideband)
            for server_node in self.rack_enclosure.server_nodes_list:
                if server_node._parent.mgmt_connection_type == "shared-lom":
                    if hasattr(server_node, "mgmt_if_list"):
                        for mgmt_port in server_node.mgmt_if_list:
                            peer_port_id = mgmt_port.peer['port']

                            point_rack = mgmt_port.coord[0] + round(mgmt_port.size[0] / 2), mgmt_port.coord[
                                1] + round(mgmt_port.size[1] / 2)

                            wire_width = self.WIDTH_WIRE

                            if str(mgmt_port.peer['fex']) == '1':
                                fex = self.fex_a
                                fabric = "a"
                            else:
                                fex = self.fex_b
                                fabric = "b"
                            # Find and calculate coordinates of the peer point on the FEX
                            point_fex = None
                            for port in fex.host_port_list:
                                if int(port.id) == peer_port_id:
                                    # Even / odd
                                    point_fex = port.coord[0] + round(port.size[0] / 3) + (
                                        peer_port_id + 1) % 2 * round(
                                        port.size[0] / 3), port.coord[1] + round(
                                        port.size[1] / 2)
                                    peer_port = port

                            if point_fex:
                                # draw_wire(self.draw, point_fi, point_chassis, wire_color, wire_width)
                                # self.wires.append(UcsSystemDrawWire(self, (point_fi, point_rack), wire_width,
                                #                                  easyucs_fi_port=port._parent))
                                if fabric == "a":
                                    if int(mgmt_port.id) % 2:
                                    # if (int(mgmt_port._parent.port_id) % 2) :
                                        step = self.WIRE_DISTANCE_LONG + round(mgmt_port.size[1] / 2)
                                    else:
                                        step = self.WIRE_DISTANCE_SHORT + round(mgmt_port.size[1] / 2)
                                if fabric == "b":
                                    if int(mgmt_port.id) % 2:
                                        step = - self.WIRE_DISTANCE_SHORT - round(mgmt_port.size[1] / 2)
                                    else:
                                        step = - self.WIRE_DISTANCE_LONG - round(mgmt_port.size[1] / 2)
                                target = point_rack[0], point_rack[1] + step
                                self.wires.append(UcsSystemDrawWire(self, (point_fex, point_rack), wire_width,
                                                                    extra_points=[target],
                                                                    easyucs_fabric_port=peer_port._parent))
                                # self.wires = remove_not_completed_in_list(self.wires)
                            else:
                                self.logger(level="error", message="Peer not found")
