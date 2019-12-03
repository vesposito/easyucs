# coding: utf-8
# !/usr/bin/env python

""" blade.py: Easy UCS Deployment Tool """
from easyucs import __author__, __copyright__,  __version__, __status__


from easyucs.draw.object import GenericUcsDrawEquipment
from easyucs.draw.ucs.storage import UcsSystemDrawStorageController, UcsSystemDrawStorageLocalDisk

from PIL import Image, ImageDraw, ImageTk, ImageFont
import json


class GenericUcsDrawBlade(GenericUcsDrawEquipment):
    def __init__(self, parent=None, parent_draw=None):
        self.parent_draw = parent_draw
        GenericUcsDrawEquipment.__init__(self, parent=parent, orientation="front")
        if not self.picture:
            return

        self.disk_slots_used = []

        if not self.parent_draw:
            self.background = self._create_background(self.canvas_width, self.canvas_height, self.canvas_color)
            self.draw = self._create_draw()

        self.parent_draw.paste_layer(self.picture, self.picture_offset)

        self.storage_controllers = self._get_storage_controllers()

        self.nvme_disks = []
        if hasattr(self._parent, "nvme_drives") and "disks_slots" in self.json_file:
            self.nvme_disks = self._get_nvme_disks()
            for disk in self.nvme_disks:
                self.parent_draw.paste_layer(disk.picture, disk.picture_offset)

        self.fill_blanks()

        # self.save_image(self._device_target + "__" + self._parent.id)

    def _get_picture_offset(self):
        if "blades_slots" in self.parent_draw.json_file:
            slots = self.parent_draw.json_file["blades_slots"]
        if "blades_slots_rear" in self.parent_draw.json_file:
            slots = self.parent_draw.json_file["blades_slots_rear"]

        blade_slot_id = int(self._parent.slot_id)
        if hasattr(self._parent, "scaled_mode"):
            if self._parent.scaled_mode == "scaled":
                blade_slot_id = blade_slot_id - 2
        for slot in slots:
            if slot["id"] == blade_slot_id:
                coord = slot["coord"]
        return self.parent_draw.picture_offset[0] + coord[0], self.parent_draw.picture_offset[1] + coord[1]

    def _get_json_file(self):
        file_name = self._parent.sku
        if hasattr(self._parent, "sku_scaled"):
            if self._parent.sku_scaled:
                file_name = self._parent.sku_scaled
        folder_path = self._find_folder_path()

        try:
            json_file = open(folder_path + str(file_name) + ".json")
            json_string = json_file.read()
            json_file.close()
            self.json_file = json.loads(json_string)
        except FileNotFoundError:
            self.logger(level="error", message="JSON file " + folder_path + str(file_name) + ".json" + " not found")

    def _get_storage_controllers(self):
        storage_controller_list = []
        # TODO : Check if this condition still needs to be here
        if (self._parent.sku != "UCSC-C3X60-SVRNB") and (self._parent.sku != "UCSC-C3K-M4SRB"):
            for storage_controller in self._parent.storage_controllers:
                # We skip M.2 controllers on M5 blades
                if ("M5" in self._parent.sku) and (storage_controller.type not in ["SAS", "NVME"]):
                    continue
                storage_controller_list.append(UcsSystemDrawStorageController(storage_controller, self))
                # storage_controller_list = remove_not_completed_in_list(storage_controller_list)
        return storage_controller_list

    def _get_nvme_disks(self):
        disk_list = []
        for disk in self._parent.nvme_drives:
            # Prevent potential disk with ID 0 to be used in Draw (happens sometimes with B200 M2)
            if disk.id != "0" and disk.slot_type == "sff-nvme":
                if disk.id in [str(i["id"]) for i in self.json_file["disks_slots"]]:
                    disk_list.append(UcsSystemDrawStorageLocalDisk(parent=disk, parent_draw=self))
                    self.disk_slots_used.append(int(disk.id))
        return disk_list

    def fill_blanks(self):
        if not self.storage_controllers:
            if "disks_slots" in self.json_file:
                # Fill blank for disks slots
                disks_slots = [*range(1, len(self.json_file["disks_slots"])+1)]
                disks_slots = set(disks_slots) - set(self.disk_slots_used)
                for slot_id in disks_slots:
                    blank_name = None
                    orientation = "horizontal"
                    disk_format = None
                    for disk_slot in self.json_file["disks_slots"]:
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
                        self.parent_draw.paste_layer(img, coord_offset)
