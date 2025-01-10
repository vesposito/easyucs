# coding: utf-8
# !/usr/bin/env python

""" neighbor.py: Easy UCS Deployment Tool """

import copy

from PIL import Image, ImageFont

from draw.object import GenericUcsDrawObject
from draw.wire import UcsSystemDrawWire


class UcsSystemDrawNeighbor:
    def __init__(self, parent, parent_draw):
        self._parent = parent
        self.parent_draw = parent_draw
        self.picture = self._get_picture()
        self.picture_size = tuple(self.picture.size)
        self.picture_offset = self._get_picture_offset()

    def _get_picture(self):
        file_name = "generic"
        if self._parent.device_type != "unknown":
            file_name = self._parent.device_type
        return Image.open("catalog/misc/icons/" + file_name + ".png", 'r')

    def _get_picture_offset(self):
        return 0, 0


class UcsSystemDrawInfraNeighbors(GenericUcsDrawObject):
    def __init__(self, draw_neighbor_list, draw_fi_list, parent=None):
        SPACING_H = 800
        SPACING_W = 200

        self.neighbors = draw_neighbor_list
        self.fi_a = self._get_fi(draw_fi_list, "A")
        self.fi_b = self._get_fi(draw_fi_list, "B")
        self.canvas_color = (255, 255, 255, 255)  # white
        # spacing between equipments, H for height, W for width
        # 70 px is the space for text
        self.canvas_height = 70 + self._max_height_neighbor() + self.fi_a.picture_size[1] + SPACING_H
        self.canvas_width = (max((self._max_width_neighbor() + SPACING_W) * len(self.neighbors),
                                 (self.fi_a.picture_size[0] * 2 + SPACING_W)))

        self.background = self._create_background(self.canvas_width, self.canvas_height, self.canvas_color)
        self.draw = self._create_draw()

        self.neighbors_dict = self.sort_neighbors()

        self.fi_a.picture_offset = self._get_picture_offset("fi_a")
        if self.fi_b:
            self.fi_b.picture_offset = self._get_picture_offset("fi_b")

        # As we drop the picture before, we need to recreate it and drop it again after pasting the layer
        self.fi_a._get_picture()
        if self.fi_a._parent.sku == "UCS-FI-M-6324":
            # We only need to rotate the picture as the other parameters are already rotated (json_file, picture_size)
            self.fi_a.picture = self.fi_a.rotate_object(picture=self.fi_a.picture)
        self.paste_layer(self.fi_a.picture, self.fi_a.picture_offset)
        self.fi_a.picture = None

        if self.fi_b:
            self.fi_b._get_picture()
            if self.fi_b._parent.sku == "UCS-FI-M-6324":
                self.fi_b.picture = self.fi_b.rotate_object(picture=self.fi_b.picture)
            self.paste_layer(self.fi_b.picture, self.fi_b.picture_offset)
            self.fi_b.picture = None

        for key, neighbor in self.neighbors_dict.items():
            neighbor.picture_offset = self._get_picture_offset("neighbor", key, neighbor)

        self.fi_a.draw = self.draw
        self.fi_a.background = self.background
        self.fi_a.ports = []
        self.fi_a.draw_ports(call_from_infra=True)
        self.fi_a.expansion_modules = self.fi_a.get_expansion_modules()
        self.fi_a.fill_blanks()

        if self.fi_b:
            self.fi_b.draw = self.draw
            self.fi_b.background = self.background
            self.fi_b.ports = []
            self.fi_b.draw_ports(call_from_infra=True)
            self.fi_b.expansion_modules = self.fi_b.get_expansion_modules()
            self.fi_b.fill_blanks()

        self.wires = []
        self.set_wire()

        for key, neighbor in self.neighbors_dict.items():
            # As we drop the picture before, we need to recreate it and drop it again after pasting the layer
            neighbor._get_picture()
            self.paste_layer(neighbor.picture, neighbor.picture_offset)
            neighbor.picture = None

        self.port_color_list = self.fi_a.legend_items
        if self.fi_b:
            self.port_color_list = self.fi_b.legend_items + self.port_color_list
        self.port_color_list = set(self.port_color_list)  # Delete duplication

        # For the legend of wires
        self.wire_color_list = []
        for wire in self.wires:
            self.wire_color_list.append(wire.color)
        self.wire_color_list = set(self.wire_color_list)  # Delete duplication

        self.draw_port_wire_legend(self, self.port_color_list, self.wire_color_list)

        self.draw_neighbors_info()

        GenericUcsDrawObject.__init__(self, parent=parent)

    def draw_neighbors_info(self):
        pass

    def _get_fi(self, fi_list, id):
        fabric = None
        for fi in fi_list:
            if fi._parent.id == id:
                fabric = fi
            if fi._parent.id == id:
                fabric = fi
        # return a copy of the fabric
        return copy.copy(fabric)

    def _get_picture_offset(self, type, order=None, neighbor=None):
        SPACING_W = 200
        if type == "neighbor" and order is not None:
            # 70 px is the space for text
            return order * round(self.canvas_width / len(self.neighbors)) + round(
                self.canvas_width / len(self.neighbors) / 2) - round(neighbor.picture_size[0] / 2), \
                   70 + self._max_height_neighbor() - neighbor.picture_size[1]
        if type == "fi_a":
            return round(self.canvas_width / 2) - self.fi_a.picture_size[0] - round(SPACING_W / 2),\
                   self.canvas_height - self.fi_a.picture_size[1]
        if type == "fi_b":
            return round(self.canvas_width / 2) + SPACING_W - round(SPACING_W / 2),\
                   self.canvas_height - self.fi_b.picture_size[1]

    def _max_height_neighbor(self):
        max = 0
        for neighbor in self.neighbors:
            if neighbor.picture_size[1] > max:
                max = neighbor.picture_size[1]
        return max

    def _max_width_neighbor(self):
        max = 0
        for neighbor in self.neighbors:
            if neighbor.picture_size[0] > max:
                max = neighbor.picture_size[0]
        return max

    def set_wire(self):
        for key, neighbor in self.neighbors_dict.items():
            for peer_port in neighbor._parent.peer_ports:
                # 70 px from the bottom of the device
                point_neighbor = neighbor.picture_offset[0] + round(neighbor.picture_size[0] / 2), \
                                 neighbor.picture_offset[1] + neighbor.picture_size[1] - 70
                for draw_fi_port in self.fi_a.ports:
                    if draw_fi_port.port == peer_port:
                        point_fi = draw_fi_port.coord[0] + round(draw_fi_port.size[0] / 2), \
                                   draw_fi_port.coord[1] + round(draw_fi_port.size[1] / 2)
                        self.wires.append(UcsSystemDrawWire(parent_draw=self, points=(point_neighbor, point_fi),
                                                            width=self.WIDTH_PORT_RECTANGLE_DEFAULT,
                                                            line_type="straight",
                                                            easyucs_fabric_port=draw_fi_port.port))
                        # self.wires = remove_not_completed_in_list(self.wires)
                if self.fi_b:
                    for draw_fi_port in self.fi_b.ports:
                        if draw_fi_port.port == peer_port:
                            point_fi = draw_fi_port.coord[0] + round(draw_fi_port.size[0] / 2), \
                                       draw_fi_port.coord[1] + round(draw_fi_port.size[1] / 2)
                            self.wires.append(UcsSystemDrawWire(parent_draw=self, points=(point_neighbor, point_fi),
                                                                width=self.WIDTH_PORT_RECTANGLE_DEFAULT,
                                                                line_type="straight",
                                                                easyucs_fabric_port=draw_fi_port.port))
                            # self.wires = remove_not_completed_in_list(self.wires)

    def sort_neighbors(self):
        pass


class UcsSystemDrawInfraNeighborsLan(UcsSystemDrawInfraNeighbors):
    def __init__(self, draw_neighbor_list, draw_fi_list, parent=None):
        UcsSystemDrawInfraNeighbors.__init__(self, draw_neighbor_list=draw_neighbor_list, draw_fi_list=draw_fi_list,
                                             parent=parent)
        self._file_name = self._device_target + "_infra_lan_neighbors"

    def draw_neighbors_info(self):
        fill_color = self.COLOR_DEFAULT
        font_size = 60
        font_title = ImageFont.truetype('arial.ttf', font_size)
        for key, neighbor in self.neighbors_dict.items():
            msg = neighbor._parent.system_name
            w = self.draw.textlength(msg, font=font_title)
            # 70 px is the space for text, 16 px space between text and equipment
            self.draw.text((neighbor.picture_offset[0] + neighbor.picture_size[0] / 2 - w/2,
                            neighbor.picture_offset[1] - (font_size + 16)), msg, fill=fill_color, font=font_title)

    def sort_neighbors(self):
        # Determining the number of groups in the list of LAN neighbors
        lan_neighbors_group_count = 0
        lan_neighbors_group_list = []
        for neighbor in self.neighbors:
            if neighbor._parent.group_number not in lan_neighbors_group_list \
                    and neighbor._parent.group_number is not None:
                lan_neighbors_group_list.append(neighbor._parent.group_number)
                lan_neighbors_group_count += 1

        # Creating a list of LAN neighbors sorted by group member and by system name
        lan_neighbors_sorted_list = sorted([neighbor for neighbor in self.neighbors if neighbor._parent.group_number is
                                            None], key=lambda neighbor: neighbor._parent.system_name)
        for group in range(0, lan_neighbors_group_count):
            lan_neighbors_sorted_list += sorted([neighbor for neighbor in self.neighbors if
                                                 neighbor._parent.group_number == group],
                                                key=lambda neighbor: neighbor._parent.system_name)
        neighbors_dict = dict()
        for i in range(0, len(self.neighbors)):
            # Sorting LAN neighbors with group members
            neighbors_dict.update({i: lan_neighbors_sorted_list[i]})

        return neighbors_dict


class UcsSystemDrawInfraNeighborsSan(UcsSystemDrawInfraNeighbors):
    def __init__(self, draw_neighbor_list, draw_fi_list, parent=None):
        UcsSystemDrawInfraNeighbors.__init__(self, draw_neighbor_list=draw_neighbor_list, draw_fi_list=draw_fi_list,
                                             parent=parent)
        self._file_name = self._device_target + "_infra_san_neighbors"

    def draw_neighbors_info(self):
        fill_color = self.COLOR_DEFAULT
        font_size = 60
        font_title = ImageFont.truetype('arial.ttf', font_size)
        for key, neighbor in self.neighbors_dict.items():
            msg = neighbor._parent.fabric_nwwn
            w = self.draw.textlength(msg, font=font_title)
            # 70 px is the space for text, 16 px space between text and equipment
            self.draw.text((neighbor.picture_offset[0] + neighbor.picture_size[0] / 2 - w / 2,
                            neighbor.picture_offset[1] - (font_size + 16)),
                           msg, fill=fill_color, font=font_title)

    def sort_neighbors(self):
        neighbors_dict = dict()
        for i in range(0, len(self.neighbors)):
            # Sorting LAN neighbors with group members
            neighbors_dict.update({i: self.neighbors[i]})
        return neighbors_dict
