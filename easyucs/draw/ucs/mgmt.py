# coding: utf-8
# !/usr/bin/env python

""" mgmt.py: Easy UCS Deployment Tool """
from easyucs import __author__, __copyright__,  __version__, __status__


class UcsSystemDrawMgmtInterface:
    def __init__(self, parent, parent_draw):
        self._parent = parent
        self.parent_draw = parent_draw

        self.peer = self._parent.peer

        self.id = self._parent.id

        self.coord = self.get_coord()
        self.size = self.get_size()

    def get_coord(self):
        return self.parent_draw.json_file["lom_ports"][self.id]['port_coord'][0] + self.parent_draw.picture_offset[0],\
            self.parent_draw.json_file["lom_ports"][self.id]['port_coord'][1] + self.parent_draw.picture_offset[1]

    def get_size(self):
        return self.parent_draw.json_file["lom_ports"][self.id]['port_size']
