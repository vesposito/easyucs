# coding: utf-8
# !/usr/bin/env python

""" cpu_module.py: Easy UCS Deployment Tool """
from easyucs import __author__, __copyright__,  __version__, __status__


from easyucs.draw.object import GenericUcsDrawEquipment
from PIL import Image, ImageDraw, ImageTk, ImageFont
from easyucs.draw.ucs.port import UcsSystemDrawPort


class UcsSystemDrawCpuModule(GenericUcsDrawEquipment):
    def __init__(self, parent=None, parent_draw=None):
        self.parent_draw = parent_draw
        self.module_id = int(parent.id) // 2 + int(parent.id) % 2
        GenericUcsDrawEquipment.__init__(self, parent=parent)
        if not self.picture:
            return
        if not self.parent_draw:
            self.background = self._create_background(self.canvas_width, self.canvas_height, self.canvas_color)
            self.draw = self._create_draw()

        self.parent_draw.paste_layer(self.picture, self.picture_offset)

    def _get_picture(self):
        folder_path = self._find_folder_path()
        if folder_path is None:
            return False

        # TODO: Check if viable in long term
        file_name = "UCSC-C480-CM"

        try:
            self.picture = Image.open(folder_path + "img/" + file_name + ".png", 'r')
        except FileNotFoundError:
            self.logger(level="error", message="Image file " + folder_path + "img/" + file_name + " not found")
            return False
        return True

    def _get_picture_offset(self):
        if "cpu_modules_slots" in self.parent_draw.json_file:
            for cpu_module in self.parent_draw.json_file["cpu_modules_slots"]:
                if cpu_module["id"] == self.module_id:
                    coord = cpu_module["coord"]
        return self.parent_draw.picture_offset[0] + coord[0], self.parent_draw.picture_offset[1] + coord[1]

    def _get_json_file(self):
        pass

