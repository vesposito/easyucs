# coding: utf-8
# !/usr/bin/env python

""" wire.py: Easy UCS Deployment Tool """
from easyucs import __author__, __copyright__,  __version__, __status__

from easyucs.draw.object import GenericUcsDrawObject


class UcsSystemDrawWire(GenericUcsDrawObject):
    def __init__(self, parent_draw, points, width, extra_points=None, line_type="square", easyucs_fabric_port=None):
        # GenericUcsDrawObject.__init__(self, parent=parent_draw, orientation=None)
        self.parent_draw = parent_draw
        self.draw = parent_draw.draw
        self.point_server = points[1]
        self.point_fi = points[0]
        self.width = width
        self.line_type = line_type
        self.transport = "indeterminate"
        self.speed = "indeterminate"
        if easyucs_fabric_port:
            if hasattr(easyucs_fabric_port, "transport"):
                self.transport = easyucs_fabric_port.transport
            if hasattr(easyucs_fabric_port, "oper_speed"):
                self.speed = easyucs_fabric_port.oper_speed
            if hasattr(easyucs_fabric_port, "admin_speed"):
                self.speed = easyucs_fabric_port.admin_speed
        self.color = self.__get_wire_color()
        self.lines = []
        self.set_lines(extra_points)
        self.lines_borders = []
        self.get_borders()
        self.draw_lines()

    def draw_lines(self):
        for line in self.lines:
            self.draw.line(line, fill=self.color, width=self.width)
        for border_line in self.lines_borders:
            color = "black"
            if self.color == "black":
                color = "grey"
            self.draw.line(border_line, fill=color, width=2)

    def __get_wire_color(self):
        fc_speed = {"1gbps": self.COLOR_LINK_FC_1G,
                    "2gbps": self.COLOR_LINK_FC_2G,
                    "4gbps": self.COLOR_LINK_FC_4G,
                    "8gbps": self.COLOR_LINK_FC_8G,
                    "16gbps": self.COLOR_LINK_FC_16G,
                    "32gbps": self.COLOR_LINK_FC_32G,
                    "auto": self.COLOR_LINK_FC_AUTO,
                    "indeterminate": self.COLOR_LINK_FC_INDETERMINATE}
        ether_speed = {"1gbps": self.COLOR_LINK_ETHER_1G,
                       "10gbps": self.COLOR_LINK_ETHER_10G,
                       "20gbps": self.COLOR_LINK_ETHER_20G,
                       "25gbps": self.COLOR_LINK_ETHER_25G,
                       "40gbps": self.COLOR_LINK_ETHER_40G,
                       "100gbps": self.COLOR_LINK_ETHER_100G,
                       "auto": self.COLOR_LINK_ETHER_AUTO,
                       "indeterminate": self.COLOR_LINK_ETHER_INDETERMINATE}
        if self.speed and self.transport:
            if self.transport == "fc":
                return fc_speed[self.speed]
            elif self.transport == "ether" or self.transport == "dce":
                return ether_speed[self.speed]
            else:
                return self.COLOR_DEFAULT
        else:
            return self.COLOR_DEFAULT

    def set_lines(self, extra_points=None):
        if self.line_type == "square":
            if extra_points:
                for point in extra_points:
                    # near_point = None # 2DO Not really working as expected
                    # for i in [0,1]:
                    #     if (point[0] == self.point_fi[i]) or point[1] == self.point_fi[i]:
                    #         near_point = self.point_fi
                    #     elif (point[0] == self.point_server[i]) or point[1] == self.point_server[i]:
                    #         near_point = self.point_server
                    # if near_point:

                    # Coordinate in self.lines are always from up to bottom and left to right
                    # from server to extra1
                    if self.point_server[1] < point[1]:
                        self.lines.append((self.point_server[0], self.point_server[1], self.point_server[0],
                                           point[1] + round(self.width / 2)))
                    elif point[1] < self.point_server[1]:
                        self.lines.append((self.point_server[0], point[1] - round(self.width / 2),
                                           self.point_server[0], self.point_server[1], ))
                    # from extra1 to extra2
                    if point[0] < self.point_fi[0]:
                        self.lines.append((point[0] - round(self.width / 2), point[1],
                                           self.point_fi[0] + round(self.width / 2), point[1]))
                    elif self.point_fi[0] < point[0]:
                        self.lines.append((self.point_fi[0] - round(self.width / 2),
                                           point[1], point[0] + round(self.width / 2), point[1]))
                    # from fi to extra2
                    self.lines.append((self.point_fi[0], self.point_fi[1], self.point_fi[0],
                                       point[1] + round(self.width / 2)))

                    #
                    # else:
                    #     print("Near point not found")

            # Default usage
            else:
                self.lines.append((self.point_fi[0], self.point_fi[1], self.point_fi[0], self.point_server[1]))
                self.lines.append((self.point_fi[0], self.point_server[1], self.point_server[0], self.point_server[1]))

        if self.line_type == "straight":
            self.lines.append((self.point_fi[0], self.point_fi[1], self.point_server[0], self.point_server[1]))

    def get_borders(self):
        for line in self.lines:
            # vertical line
            if line[0] == line[2]:
                self.lines_borders.append((line[0] - round(self.width / 2), line[1], line[2] - round(self.width / 2),
                                           line[3]))
                self.lines_borders.append((line[0] + round(self.width / 2), line[1], line[2] + round(self.width / 2),
                                           line[3]))
            # horizontal line
            elif line[1] == line[3]:
                self.lines_borders.append((line[0], line[1] - round(self.width / 2), line[2],
                                           line[3] - round(self.width / 2)))
                self.lines_borders.append((line[0], line[1] + round(self.width / 2), line[2],
                                           line[3] + round(self.width / 2)))
