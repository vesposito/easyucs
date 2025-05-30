# coding: utf-8
# !/usr/bin/env python

""" adaptor.py: Easy UCS Deployment Tool """

from PIL import Image

from draw.object import GenericUcsDrawEquipment
from draw.ucs.port import UcsPortDraw


class UcsAdaptorDraw(GenericUcsDrawEquipment):
    def __init__(self, parent=None, parent_draw=None):
        self.picture = None
        self.parent_draw = parent_draw
        self.width = None
        self.orientation = None

        if not parent.sku:
            parent_draw.logger(level="error", message="No SKU found, this adaptor will not be created")
            return None

        GenericUcsDrawEquipment.__init__(self, parent=parent)
        if not self.picture:
            return

        self.ports = []

        self.parent_draw.paste_layer(self.picture, self.picture_offset)
        if "UcsImc" not in parent.__class__.__name__:
            if self.parent_draw.color_ports:
                if self._parent.sku not in ["UCSC-PCIE-C25Q-04"]:  #TODO Workaround until fixed on inventory as the port of the PCIe card are not correct and appears as active even when should not
                    self.draw_ports()
                elif "Rack" in self._parent._parent.__class__.__name__:  #TODO Workaround until above problem fixed
                    self.draw_ports()
                # self.draw_ports()

        # We drop the picture in order to save on memory
        self.picture = None

    def _get_picture(self):
        if self._parent.pci_slot:
            if "SIOC" in self._parent.pci_slot:
                self.width = self.parent_draw.json_file["pcie_slots"][0]["width"]
                if "orientation" in self.parent_draw.json_file["pcie_slots"][0]:
                    self.orientation = self.parent_draw.json_file["pcie_slots"][0]["orientation"]
            elif self._parent.pci_slot not in ["MLOM", "OCP"]:  # not MLOM or OCP
                if self.parent_draw.json_file.get("pcie_slots"):
                    for slot in self.parent_draw.json_file["pcie_slots"]:
                        if slot["id"] == int(self._parent.pci_slot):
                            if "width" in slot:
                                self.width = slot['width']
                            if "orientation" in slot:
                                self.orientation = slot['orientation']

        if self.json_file:
            if self.width == "half":
                file_name = self.json_file.get("rear_file_name_half")
            else:
                file_name = self.json_file.get("rear_file_name")

            try:
                self.picture = Image.open("catalog/adaptors/img/" + str(file_name), 'r')
                self.picture_size = tuple(self.picture.size)
            except FileNotFoundError:
                self.logger(level="error",
                            message="Image file " "catalog/adaptors/img/" + str(file_name) + " not found")
                return False

            if self.picture and self.orientation:
                if self.orientation == "reverse":
                    self.picture = self.rotate_object(picture=self.picture)
                    self.picture = self.rotate_object(picture=self.picture)
                if self.orientation == "vertical":
                    self.picture = self.rotate_object(picture=self.picture)
                    self.picture = self.rotate_object(picture=self.picture)
                    self.picture = self.rotate_object(picture=self.picture)
                self.picture_size = tuple(self.picture.size)
        else:
            return False

    def _get_picture_offset(self):
        coord = None
        if self._parent.pci_slot:
            if self._parent.pci_slot == "MLOM":  # for MLOM Slot
                coord = self.parent_draw.json_file["mlom_slots"][0]["coord"]
            elif self._parent.pci_slot == "OCP":  # for OCP Slot
                coord = self.parent_draw.json_file["ocp_slots"][0]["coord"]
            elif "SIOC" in self._parent.pci_slot:  # for PCIe slot in UCS-S3260-PCISIOC
                coord = self.parent_draw.json_file["pcie_slots"][0]["coord"]
            else:  # for PCIe Slot
                if self.parent_draw.json_file.get("pcie_slots"):
                    for slot in self.parent_draw.json_file["pcie_slots"]:
                        if slot["id"] == int(self._parent.pci_slot):
                            coord = slot["coord"]
        if coord:
            return self.parent_draw.picture_offset[0] + coord[0], self.parent_draw.picture_offset[1] + coord[1]
        return False

    def draw_ports(self):
        for port in self._parent.ports:
            port_color = self.COLOR_LAN_UPLINK_PORTS
            port_id = port.port_id
            rectangle_width = self.WIDTH_PORT_RECTANGLE_DEFAULT

            if self.width == "half":
                rear_ports = self.json_file["rear_ports_half"]
            else:
                rear_ports = self.json_file["rear_ports"]

            if port.aggr_port_id:  # for aggr ports
                port_info = dict(rear_ports["x/" + port.aggr_port_id])
            else:
                port_info = rear_ports["x/" + port_id]

            if port.aggr_port_id:
                rectangle_width = self.WIDTH_PORT_RECTANGLE_BREAKOUT

                aggr_width = round(port_info['port_size'][0] / 4)
                port_info['port_size'] = aggr_width - 2, port_info['port_size'][1]
                port_info['port_coord'] = port_info['port_coord'][0] + (int(port_id) - 1) * aggr_width, \
                                          port_info['port_coord'][1]

            port_size_x = port_info['port_size'][0]
            port_size_y = port_info['port_size'][1]
            coord_x = port_info['port_coord'][0]
            coord_y = port_info['port_coord'][1]

            if self.orientation == "reverse":
                coord_x = self.picture_size[0] - coord_x - port_size_x
                coord_y = self.picture_size[1] - coord_y - port_size_y
            if self.orientation == "vertical":
                coord_x = self.picture_size[0] - coord_y - port_size_y
                coord_y = port_info['port_coord'][0]
                port_size_x = port_info['port_size'][1]
                port_size_y = port_info['port_size'][0]

            peer = None
            if port.peer:
                peer = port.peer

            self.ports.append(
                UcsPortDraw(id=port_id, color=port_color, size=(port_size_x, port_size_y),
                            coord=(self.picture_offset[0] + coord_x, self.picture_offset[1] + coord_y),
                            parent_draw=self, port=port, peer=peer))

            self.draw_rectangle(draw=self.parent_draw.draw,
                                coordinates=((self.picture_offset[0] + coord_x, self.picture_offset[1] + coord_y),
                                             (self.picture_offset[0] + coord_x + port_size_x, self.picture_offset[1] +
                                              coord_y + port_size_y)), color=port_color, width=rectangle_width)
