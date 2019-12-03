# coding: utf-8
# !/usr/bin/env python

""" chassis.py: Easy UCS Deployment Tool """
from easyucs import __author__, __copyright__,  __version__, __status__


from easyucs.draw.object import GenericUcsDrawEquipment
from PIL import Image, ImageDraw, ImageTk, ImageFont


class GenericUcsDrawPsu(GenericUcsDrawEquipment):
    def __init__(self, parent=None, parent_draw=None):
        self.parent_draw = parent_draw
        GenericUcsDrawEquipment.__init__(self, parent=parent)
        if not self.picture:
            return

        if not self.parent_draw:
            self.background = self._create_background(self.canvas_width, self.canvas_height, self.canvas_color)
            self.draw = self._create_draw()

        self.parent_draw.paste_layer(self.picture, self.picture_offset)

        # self.save_image(self._device_target + "__" + self._parent.id)

    def _get_picture(self):
        if hasattr(self._parent, 'sku'):
            file_name = self._parent.sku
        else:
            # When a PSU is missing, the PSU is still an "equipmentPsu" but without model name /!\ Not used anymore
            for model in self.parent_draw.json_file["psus_models"]:
                if "type" in model:
                    if model["type"] == "blank":
                        file_name = model["name"]
        try:
            if file_name:
                self.picture = Image.open("catalog/power_supplies/img/" + str(file_name) + ".png", 'r')
            else:
                return False
        except FileNotFoundError:
            self.logger(level="error",
                        message="Image file " "catalog/power_supplies/img/" + str(file_name) + " not found")
            return False

    def _get_json_file(self):
        pass

    def _get_picture_offset(self):
        if "psus_slots" in self.parent_draw.json_file:
            slots = self.parent_draw.json_file["psus_slots"]
        if "psus_slots_rear" in self.parent_draw.json_file:
            slots = self.parent_draw.json_file["psus_slots_rear"]

        for slot in slots:
            if slot["id"] == int(self._parent.id):
                coord = slot["coord"]
        return self.parent_draw.picture_offset[0] + coord[0], self.parent_draw.picture_offset[1] + coord[1]
