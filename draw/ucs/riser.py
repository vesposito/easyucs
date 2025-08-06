# coding: utf-8
# !/usr/bin/env python

""" riser.py: Easy UCS Deployment Tool """

from PIL import Image

from draw.object import GenericUcsDrawObject


class GenericUcsDrawFrontMezz(GenericUcsDrawObject):
    def __init__(self, parent=None, parent_draw=None, infra=False):
        self._parent = parent
        self.parent_draw = parent_draw
        self._get_json_file()
        self._get_picture()

        if not self.picture:
            return

        self.disk_slots_used = []

        if not self.parent_draw:
            self.background = self._create_background(self.canvas_width, self.canvas_height, self.canvas_color)
            self.draw = self._create_draw()

        self.picture_offset = self._get_picture_offset()
        if self.picture_offset:
            # We add element brought from the Front Mezz to the json file copy of the blade
            if not infra:
                self.add_info_to_parent()

            self.parent_draw.parent_draw.paste_layer(self.picture, self.picture_offset)

        # self.save_image(self._device_target + "__" + self._parent.id)

        # We drop the picture in order to save on memory
        self.picture = None

    def add_info_to_parent(self):
        if "disks_slots" in self.json_file:
            disks_slots = self.json_file["disks_slots"].copy()

            # for slot in disks_slots:
            #     # Adjust coord with offset
            #     slot['coord'] = [self.picture_offset[0] + slot['coord'][0], self.picture_offset[1] + slot['coord'][1]]

            # Add the slots in the riser to the list of slots front on the parent json file
            if "disks_slots" in self.parent_draw.json_file:
                self.parent_draw.json_file["disks_slots"] = \
                    self.parent_draw.json_file["disks_slots"] + disks_slots
            else:
                self.parent_draw.json_file["disks_slots"] = disks_slots

            # Also add the disks models to the parent json file (useful for blank)
            if "disks_models" in self.json_file:
                disks_models = self.json_file["disks_models"].copy()
                if "disks_models" in self.parent_draw.json_file:
                    self.parent_draw.json_file["disks_models"] += disks_models
                else:
                    self.parent_draw.json_file["disks_models"] = disks_models

    def _get_picture(self):
        file_name = None
        if self.json_file:
            file_name = self.json_file.get("front_file_name")
            if file_name.endswith(".png"):
                file_name = file_name[:-4]
        elif 'sku' in self._parent:
            file_name = self._parent['sku']
        else:
            for model in self.parent_draw.json_file["front_mezzanine_models"]:
                if "type" in model:
                    if model["type"] == "blank":
                        file_name = model["name"]

        try:
            if file_name:
                self.picture = Image.open("catalog/front_mezzanines/img/" + str(file_name) + ".png", 'r')
                self.picture_size = tuple(self.picture.size)
            else:
                return False
        except FileNotFoundError:
            # self.logger(level="error",
            #             message="Image file " "catalog/front_mezzanine/img/" + str(file_name) + ".png not found")
            self.picture = None
            self.picture_size = None
            return False

    def _get_picture_offset(self):
        slots = []
        if "front_mezzanine_slots" in self.parent_draw.json_file:
            slots = self.parent_draw.json_file["front_mezzanine_slots"]

        if slots:
            coord = slots[0]["coord"]
            return self.parent_draw.picture_offset[0] + coord[0], self.parent_draw.picture_offset[1] + coord[1]

        return False

    def _get_json_file(self):
        import json
        file_name = str(self._parent['sku'])
        folder_path = "catalog/front_mezzanines/"

        try:
            json_file = open(folder_path + str(file_name) + ".json")
            json_string = json_file.read()
            json_file.close()
            self.json_file = json.loads(json_string)
        except FileNotFoundError:
            self.parent_draw.logger(level="error",
                                    message="JSON file " + folder_path + file_name + ".json" + " not found")


class GenericUcsDrawPcieRiser:
    def __init__(self, parent=None, parent_draw=None, infra=False):
        self._parent = parent
        self.parent_draw = parent_draw
        self._get_json_file()
        self._get_picture()

        if not self.picture:
            return

        self.picture_offset = self._get_picture_offset()
        if self.picture_offset:
            # We add element brought from the PCIe Riser to the json file copy of the rack
            if not infra:
                self.add_info_to_parent()

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

            # Add the slots in the riser to the list of port rear on the parent json file
            if "disks_slots_rear" in self.parent_draw.json_file:
                self.parent_draw.json_file["disks_slots_rear"] = \
                    self.parent_draw.json_file["disks_slots_rear"] + disks_slots
            else:
                self.parent_draw.json_file["disks_slots_rear"] = disks_slots

            # Might use in the future if a riser goes in front of a device
            # if "disks_slots" in self.parent_draw.json_file:
            #     self.parent_draw.json_file["disks_slots"] = \
            #         self.parent_draw.json_file["disks_slots"] + disks_slots
            # else:
            #     self.parent_draw.json_file["disks_slots"] = disks_slots

    def _get_picture(self):
        file_name = None
        if self.json_file:
            file_name = self.json_file.get("rear_file_name")
            if file_name.endswith(".png"):
                file_name = file_name[:-4]
        elif 'sku' in self._parent:
            file_name = self._parent['sku']
        else:
            for model in self.parent_draw.json_file["pcie_riser_models"]:
                if "type" in model:
                    if model["type"] == "blank":
                        file_name = model["name"]

        # Handle SKUs with multiple values like "UCSC-PCI-1-C240M5/UCSC-RIS-1-240M5" - Arbitrarily using the last one
        if "/" in file_name:
            file_name = file_name.split("/")[-1]

        try:
            if file_name:
                self.picture = Image.open("catalog/pcie_risers/img/" + str(file_name) + ".png", 'r')
                self.picture_size = tuple(self.picture.size)
            else:
                return False
        except FileNotFoundError:
            # self.logger(level="error",
            #             message="Image file " "catalog/pcie_risers/img/" + str(file_name) + ".png not found")
            self.picture = None
            self.picture_size = None
            return False

    def _get_picture_offset(self):
        slots = []
        if "pcie_riser_slots" in self.parent_draw.json_file:
            slots = self.parent_draw.json_file["pcie_riser_slots"]

        if slots:
            for slot in slots:
                if slot["id"] == int(self._parent['id']):
                    coord = slot["coord"]
            return self.parent_draw.picture_offset[0] + coord[0], self.parent_draw.picture_offset[1] + coord[1]

        return False

    def _get_json_file(self):
        import json
        file_name = str(self._parent['sku'])
        folder_path = "catalog/pcie_risers/"

        # Handle SKUs with multiple values like "UCSC-PCI-1-C240M5/UCSC-RIS-1-240M5" - Arbitrarily using the last one
        if "/" in file_name:
            file_name = file_name.split("/")[-1]

        try:
            json_file = open(folder_path + str(file_name) + ".json")
            json_string = json_file.read()
            json_file.close()
            self.json_file = json.loads(json_string)
        except FileNotFoundError:
            self.parent_draw.logger(level="error",
                                    message="JSON file " + folder_path + file_name + ".json" + " not found")
