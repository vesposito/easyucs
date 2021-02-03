# coding: utf-8
# !/usr/bin/env python

""" riser.py: Easy UCS Deployment Tool """
from __init__ import __author__, __copyright__,  __version__, __status__


from draw.object import GenericUcsDrawEquipment
from PIL import Image, ImageDraw, ImageFont
from draw.ucs.port import UcsSystemDrawPort


class GenericUcsDrawPcieRiser():
    def __init__(self, parent=None, parent_draw=None, infra=False):
        self._parent = parent
        self.parent_draw = parent_draw
        self._get_json_file()
        self._get_picture()
        self.picture_offset = self._get_picture_offset()
        # We add element brought from the PCIe Riser to the json file copy of the rack
        if not infra:
            self.add_info_to_parent()

        if not self.picture:
            return

        self.parent_draw.paste_layer(self.picture, self.picture_offset)

        # self.save_image(self._device_target + "__" + self._parent.id)

        # We drop the picture in order to save on memory
        self.picture = None

    def add_info_to_parent(self):
        if "pcie_slots" in self.json_file:
            pcie_slots = self.json_file["pcie_slots"].copy()

            for slot in pcie_slots:
                # Ajust coord with offset
                slot['coord'] = [self.picture_offset[0] + slot['coord'][0], self.picture_offset[1] + slot['coord'][1]]

            if "pcie_slots" in self.parent_draw.json_file:
                self.parent_draw.json_file["pcie_slots"] = self.parent_draw.json_file["pcie_slots"] + pcie_slots
            else:
                self.parent_draw.json_file["pcie_slots"] = pcie_slots

        if "disks_slots" in self.json_file:
            disks_slots = self.json_file["disks_slots"].copy()

            for slot in disks_slots:
                # Ajust coord with offset
                slot['coord'] = [self.picture_offset[0] + slot['coord'][0], self.picture_offset[1] + slot['coord'][1]]

            if "disks_slots_rear" in self.parent_draw.json_file:
                self.parent_draw.json_file["disks_slots_rear"] = \
                    self.parent_draw.json_file["disks_slots_rear"] + disks_slots
            else:
                self.parent_draw.json_file["disks_slots_rear"] = disks_slots

            # if "disks_slots" in self.parent_draw.json_file:
            #     self.parent_draw.json_file["disks_slots"] = \
            #         self.parent_draw.json_file["disks_slots"] + disks_slots
            # else:
            #     self.parent_draw.json_file["disks_slots"] = disks_slots


    def _get_picture(self):
        if 'sku' in self._parent:
            file_name = self._parent['sku']
        else:
            for model in self.parent_draw.json_file["pcie_riser_models"]:
                if "type" in model:
                    if model["type"] == "blank":
                        file_name = model["name"]
        try:
            if file_name:
                self.picture = Image.open("catalog/pcie_risers/img/" + str(file_name) + ".png", 'r')
                self.picture_size = tuple(self.picture.size)
            else:
                return False
        except FileNotFoundError:
            self.logger(level="error",
                        message="Image file " "catalog/pcie_risers/img/" + str(file_name) + ".png not found")
            return False

    def _get_picture_offset(self):
        slots = self.parent_draw.json_file["pcie_riser_slots"]

        for slot in slots:
            if slot["id"] == int(self._parent['id']):
                coord = slot["coord"]
        return self.parent_draw.picture_offset[0] + coord[0], self.parent_draw.picture_offset[1] + coord[1]

    def _get_json_file(self):
        import json
        file_name = str(self._parent['sku'])
        folder_path = "catalog/pcie_risers/"

        try:
            json_file = open(folder_path + str(file_name) + ".json")
            json_string = json_file.read()
            json_file.close()
            self.json_file = json.loads(json_string)
        except FileNotFoundError:
            self.parent_draw.logger(level="error", message="JSON file " + folder_path + file_name + ".json" + " not found")
