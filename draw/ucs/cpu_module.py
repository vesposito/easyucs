# coding: utf-8
# !/usr/bin/env python

""" cpu_module.py: Easy UCS Deployment Tool """

from PIL import Image

from draw.object import GenericUcsDrawEquipment


class UcsCpuModuleDraw(GenericUcsDrawEquipment):
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

        # We drop the picture in order to save on memory
        self.picture = None

    def _get_picture(self):
        folder_path = self._find_folder_path()
        if folder_path is None:
            return False

        # TODO: Check if viable in long term
        file_name = "UCSC-C480-CM"

        try:
            self.picture = Image.open(folder_path + "img/" + file_name + ".png", 'r')
            self.picture_size = tuple(self.picture.size)
        except FileNotFoundError:
            self.logger(level="error", message="Image file " + folder_path + "img/" + file_name + ".png not found")
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

