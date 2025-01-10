# coding: utf-8
# !/usr/bin/env python

""" pcie_node.py: Easy UCS Deployment Tool """

import json

from draw.object import GenericUcsDrawEquipment


class UcsPcieNodeDraw(GenericUcsDrawEquipment):
    def __init__(self, parent=None, parent_draw=None):
        self.parent_draw = parent_draw
        GenericUcsDrawEquipment.__init__(self, parent=parent, orientation="front")
        if not self.picture:
            return

        if not self.parent_draw:
            self.background = self._create_background(self.canvas_width, self.canvas_height, self.canvas_color)
            self.draw = self._create_draw()

        self.parent_draw.paste_layer(self.picture, self.picture_offset)

        # We drop the picture in order to save on memory
        self.picture = None

        # self.save_image(self._device_target + "__" + self._parent.id)

    def _get_picture_offset(self):
        if "blades_slots" in self.parent_draw.json_file:
            slots = self.parent_draw.json_file["blades_slots"]

        pcie_node_slot_id = int(self._parent.slot_id)
        for slot in slots:
            if slot["id"] == pcie_node_slot_id:
                coord = slot["coord"]
        return self.parent_draw.picture_offset[0] + coord[0], self.parent_draw.picture_offset[1] + coord[1]

    def _get_json_file(self):
        file_name = self._parent.sku
        folder_path = self._find_folder_path()

        try:
            json_file = open(folder_path + str(file_name) + ".json")
            json_string = json_file.read()
            json_file.close()
            self.json_file = json.loads(json_string)
        except FileNotFoundError:
            self.logger(level="error", message="JSON file " + folder_path + str(file_name) + ".json" + " not found")
