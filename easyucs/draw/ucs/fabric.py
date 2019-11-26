# coding: utf-8
# !/usr/bin/env python

""" fabric.py: Easy UCS Deployment Tool """
from easyucs import __author__, __copyright__,  __version__, __status__


from easyucs.draw.object import GenericUcsDrawEquipment
from easyucs.draw.ucs.port import UcsSystemDrawPort
from easyucs.draw.ucs.psu import GenericUcsDrawPsu
from PIL import Image, ImageDraw, ImageTk, ImageFont


class UcsSystemDrawFiRear(GenericUcsDrawEquipment):
    def __init__(self, parent=None, parent_draw=None, color_ports=True):
        self.parent_draw = parent_draw
        self.color_ports = color_ports
        GenericUcsDrawEquipment.__init__(self, parent=parent)
        if not self.picture:
            return

        if not self.parent_draw:
            self.background = self._create_background(self.canvas_width, self.canvas_height, self.canvas_color)
            self.draw = self._create_draw()
        else:
            self.background = self.parent_draw.background
            self.draw = self.parent_draw.draw

        self.paste_layer(self.picture, self.picture_offset)

        self.legend_items = []
        self.ports = []
        if color_ports:
            self.draw_ports()
        self.expansion_modules = self.get_expansion_modules()
        self.fill_blanks()

        self._file_name = None
        if not self.parent_draw:
            self._file_name = self._device_target + "_fi_" + self._parent.id + "_rear"
            if not self.color_ports:
                self._file_name = self._device_target + "_fi_" + self._parent.id + "_rear_clear"

        if color_ports:
            self.clear_version = UcsSystemDrawFiRear(parent=parent, parent_draw=parent_draw, color_ports=False)

    def _get_picture_offset(self):
        img_w, img_h = self.picture.size

        if self.parent_draw:
            if "io_modules_slots" in self.parent_draw.json_file:
                for slot in self.parent_draw.json_file["io_modules_slots"]:
                    if self._parent.id == "A":
                        if slot["id"] == 1:
                            fi_offset_from_chassis = slot["coord"]
                    else:
                        if slot["id"] == 2:
                            fi_offset_from_chassis = slot["coord"]

            UCS_MINI_PICTURE_OFFSET = 8  # We offset the picture because of the levers with transparent background
            return self.parent_draw.picture_offset[0] + fi_offset_from_chassis[0], \
                   self.parent_draw.picture_offset[1] + fi_offset_from_chassis[1] - UCS_MINI_PICTURE_OFFSET

        # 0 is an arbitrary value
        return 0, self.canvas_height - img_h

    def get_expansion_modules(self):
        gem_list = []
        for gem in self._parent.expansion_modules:
            gem_list.append(UcsSystemDrawGem(parent=gem, parent_draw=self))
        # gem_list = remove_not_completed_in_list(gem_list)
        # We only keep the gem that have been fully created -> picture
        gem_list = [gem for gem in gem_list if gem.picture]
        return gem_list

    def draw_ports(self, call_from_infra=None):
        # Draws color-coded rectangles on top of FI base ports
        for port in self._parent.ports:
            if port.slot_id == "1":
                if port.role != "unknown":
                    port_color = self.COLOR_DEFAULT
                    port_id = port.port_id
                    rectangle_width = self.WIDTH_PORT_RECTANGLE_DEFAULT

                    if port.aggr_port_id:  # for breakout ports
                        # We create a copy of the "rear_ports" section of the JSON file to modify it on the fly
                        port_info = dict(self.json_file["rear_ports"][port.aggr_port_id])
                        rectangle_width = self.WIDTH_PORT_RECTANGLE_BREAKOUT
                        if self._parent.sku == "UCS-FI-M-6324" and not call_from_infra:
                            # We are drawing ports for UCS Mini in chassis view.
                            # Since the FI is vertical, we need to break the port vertically
                            aggr_height = round(port_info['port_size'][1] / 4)
                            port_info['port_size'] = port_info['port_size'][0],\
                                                     aggr_height - self.WIDTH_PORT_SEPARATOR_BREAKOUT
                            port_info['port_coord'] = port_info['port_coord'][0], port_info['port_coord'][1] + \
                                                      (int(port_id) - 1) * aggr_height

                        else:
                            # We are drawing ports for a Fabric Interconnect in horizontal view
                            aggr_width = round(port_info['port_size'][0] / 4)
                            port_info['port_size'] = aggr_width - self.WIDTH_PORT_SEPARATOR_BREAKOUT, \
                                                     port_info['port_size'][1]
                            port_info['port_coord'] = port_info['port_coord'][0] + (int(port_id) - 1) * aggr_width, \
                                                      port_info['port_coord'][1]

                    else:
                        port_info = self.json_file["rear_ports"][port_id]

                    if port.role == "network" and port.type == "lan":
                        port_color = self.COLOR_LAN_UPLINK_PORTS
                    if port.role == "network" and port.type == "san":
                        port_color = self.COLOR_SAN_UPLINK_PORTS
                    if port.role == "storage":
                        port_color = self.COLOR_SAN_STORAGE_PORTS
                    if port.role == "fcoe-uplink":
                        port_color = self.COLOR_FCOE_UPLINK_PORTS
                    if port.role == "fcoe-storage":
                        port_color = self.COLOR_FCOE_STORAGE_PORTS
                    if port.role == "nas-storage":
                        port_color = self.COLOR_APPLIANCE_STORAGE_PORTS
                    if port.role == "server":
                        port_color = self.COLOR_SERVER_PORTS
                    if port.role == "fcoe-nas-storage":
                        port_color = self.COLOR_UNIFIED_STORAGE_PORTS
                    if port.role == "network-fcoe-uplink":
                        port_color = self.COLOR_UNIFIED_UPLINK_PORTS
                    if port.role == "monitor" and port.type == "san":
                        port_color = self.COLOR_SAN_MONITOR_PORTS
                    elif port.role == "monitor":
                        port_color = self.COLOR_LAN_MONITOR_PORTS

                    # We add the color of the port type to the list of legend items
                    if port_color not in self.legend_items:
                        self.legend_items.append(port_color)

                    port_size_x = port_info['port_size'][0]
                    port_size_y = port_info['port_size'][1]
                    coord_x = port_info['port_coord'][0]
                    coord_y = port_info['port_coord'][1]

                    self.ports.append(UcsSystemDrawPort(id=port_id, color=port_color, size=(port_size_x, port_size_y),
                                                        coord=(self.picture_offset[0] + coord_x,
                                                               self.picture_offset[1] + coord_y), parent_draw=self,
                                                        port=port))
                    # self.port_list = remove_not_completed_in_list(self.port_list)

                    self.draw_rectangle(draw=self.draw,
                                        coordinates=((self.picture_offset[0] + coord_x,
                                                      self.picture_offset[1] + coord_y),
                                                     (self.picture_offset[0] + coord_x + port_size_x,
                                                      self.picture_offset[1] + coord_y + port_size_y)),
                                        color=port_color,
                                        width=rectangle_width)

    def fill_blanks(self):
        # Fills unused GEM slots with blanking panels
        if len(self._parent.expansion_modules) < len(self.json_file["expansion_modules_slots"]):
            # Load blank image from JSON file
            for expansion in self.json_file["expansion_modules_models"]:
                if "type" in expansion:
                    if expansion["type"] == "blank":
                        blank_name = expansion["name"]
                        blank_img = Image.open("catalog/fabric_interconnects/img/" + blank_name + ".png", 'r')

            all_slot_ids = []
            used_slot_ids = []
            unused_slot_ids = []

            for slot in self._parent.expansion_modules:
                used_slot_ids.append(int(slot.id))
            for slot in self.json_file["expansion_modules_slots"]:
                all_slot_ids.append(slot["id"])
            for blank_id in set(all_slot_ids) - set(used_slot_ids):
                unused_slot_ids.append(blank_id)

            for slot_id in unused_slot_ids:
                # We need to get the coordinates of the slot to place the blank
                for slot in self.json_file["expansion_modules_slots"]:
                    if slot["id"] == int(slot_id):
                        coord = slot["coord"]
                # We paste the blanking panel
                coord_offset = self.picture_offset[0] + coord[0], self.picture_offset[1] + coord[1]
                self.paste_layer(blank_img, coord_offset)


class UcsSystemDrawFiFront(GenericUcsDrawEquipment):
    def __init__(self, parent=None):
        GenericUcsDrawEquipment.__init__(self, parent=parent, orientation="front")
        if not self.picture:
            return

        self.background = self._create_background(self.canvas_width, self.canvas_height, self.canvas_color)
        self.draw = self._create_draw()

        self.paste_layer(self.picture, self.picture_offset)

        if "psus_slots" in self.json_file:
            self.power_supplies = self.get_power_supplies()

        self._file_name = self._device_target + "_fi_" + self._parent.id + "_front"

    def get_power_supplies(self):
        psu_list = []
        for psu in self._parent.power_supplies:
            if psu.id != '0':
                psu_list.append(GenericUcsDrawPsu(psu, self))
        return psu_list


class UcsSystemDrawGem(GenericUcsDrawEquipment):
    def __init__(self, parent=None, parent_draw=None):
        self.parent_draw = parent_draw
        GenericUcsDrawEquipment.__init__(self, parent=parent)
        if not self.picture:
            return

        self.ports = []
        self.parent_draw.paste_layer(self.picture, self.picture_offset)

        if self.parent_draw.color_ports:
            self.draw_ports()

    def _get_picture_offset(self):
        for slot in self.parent_draw.json_file["expansion_modules_slots"]:
            if slot["id"] == int(self._parent.id):
                coord = slot["coord"]
        return self.parent_draw.picture_offset[0] + coord[0], self.parent_draw.picture_offset[1] + coord[1]

    def draw_ports(self):
        # Draws color-coded rectangles on top of FEX ports
        for port in self._parent.ports:
            if port.role != "unknown":
                port_color = self.COLOR_DEFAULT
                port_id = port.port_id
                rectangle_width = self.WIDTH_PORT_RECTANGLE_DEFAULT

                if port.aggr_port_id:  # for breakout ports
                    # We create a copy of the "rear_ports" section of the JSON file to modify it on the fly
                    port_info = dict(self.json_file["rear_ports"][port.aggr_port_id])
                    rectangle_width = self.WIDTH_PORT_RECTANGLE_BREAKOUT

                    # We are drawing ports for a GEM in horizontal view
                    aggr_width = round(port_info['port_size'][0] / 4)
                    port_info['port_size'] = aggr_width - self.WIDTH_PORT_SEPARATOR_BREAKOUT, port_info['port_size'][1]
                    port_info['port_coord'] = port_info['port_coord'][0] + (int(port_id) - 1) * aggr_width,\
                                              port_info['port_coord'][1]

                else:
                    # Handling special case of N10-E0440 GEM which has Ethernet and FC ports with the same port_id
                    if self._parent.sku == "N10-E0440":
                        if port.transport == "ether":
                            port_info = self.json_file["rear_ports"][port_id]
                        elif port.transport == "fc":
                            port_info = self.json_file["rear_ports"]["fc" + port_id]
                    else:
                        port_info = self.json_file["rear_ports"][port_id]

                if port.role == "network" and port.type == "lan":
                    port_color = self.COLOR_LAN_UPLINK_PORTS
                if port.role == "network" and port.type == "san":
                    port_color = self.COLOR_SAN_UPLINK_PORTS
                if port.role == "storage":
                    port_color = self.COLOR_SAN_STORAGE_PORTS
                if port.role == "fcoe-uplink":
                    port_color = self.COLOR_FCOE_UPLINK_PORTS
                if port.role == "fcoe-storage":
                    port_color = self.COLOR_FCOE_STORAGE_PORTS
                if port.role == "nas-storage":
                    port_color = self.COLOR_APPLIANCE_STORAGE_PORTS
                if port.role == "server":
                    port_color = self.COLOR_SERVER_PORTS
                if port.role == "fcoe-nas-storage":
                    port_color = self.COLOR_UNIFIED_STORAGE_PORTS
                if port.role == "network-fcoe-uplink":
                    port_color = self.COLOR_UNIFIED_UPLINK_PORTS
                if port.role == "monitor" and port.type == "san":
                    port_color = self.COLOR_SAN_MONITOR_PORTS
                elif port.role == "monitor":
                    port_color = self.COLOR_LAN_MONITOR_PORTS

                # We add the color of the port type to the list of legend items
                if port_color not in self.parent_draw.legend_items:
                    self.parent_draw.legend_items.append(port_color)

                port_size_x = port_info['port_size'][0]
                port_size_y = port_info['port_size'][1]
                coord_x = port_info['port_coord'][0]
                coord_y = port_info['port_coord'][1]

                self.ports.append(UcsSystemDrawPort(id=port_id, color=port_color, size=(port_size_x, port_size_y),
                                                    coord=(self.picture_offset[0] + coord_x,
                                                           self.picture_offset[1] + coord_y), parent_draw=self,
                                                    port=port))
                # self.ports = remove_not_completed_in_list(self.port_list)

                self.draw_rectangle(draw=self.parent_draw.draw,
                                    coordinates=((self.picture_offset[0] + coord_x, self.picture_offset[1] + coord_y),
                                                 (self.picture_offset[0] + coord_x + port_size_x,
                                                  self.picture_offset[1] + coord_y + port_size_y)), color=port_color,
                                    width=rectangle_width)


class UcsSystemDrawFexRear(GenericUcsDrawEquipment):
    def __init__(self, parent=None, color_ports=True):
        GenericUcsDrawEquipment.__init__(self, parent=parent)
        self.color_ports = color_ports
        if not self.picture:
            return

        self.background = self._create_background(self.canvas_width, self.canvas_height, self.canvas_color)
        self.draw = self._create_draw()

        self.paste_layer(self.picture, self.picture_offset)

        self.fabric_port_list = []
        self.host_port_list = []

        if color_ports:
            self.draw_ports()

        self._file_name = self._device_target + "_fex_" + self._parent.id + "_rear"
        if not self.color_ports:
            self._file_name = self._device_target + "_fex_" + self._parent.id + "_rear_clear"

        if color_ports:
            self.clear_version = UcsSystemDrawFexRear(parent=parent, color_ports=False)

    def draw_ports(self):
        # Draws color-coded rectangles on top of base ports
        for port in self._parent.host_ports:
            if port.oper_state != "indeterminate":
                port_color = self.COLOR_SERVER_PORTS
            else:
                port_color = self.COLOR_DEFAULT
            port_id = port.port_id
            rectangle_width = self.WIDTH_PORT_RECTANGLE_DEFAULT

            port_info = self.json_file["rear_ports"][port_id]

            port_size_x = port_info['port_size'][0]
            port_size_y = port_info['port_size'][1]
            coord_x = port_info['port_coord'][0]
            coord_y = port_info['port_coord'][1]

            self.host_port_list.append(UcsSystemDrawPort(id=port_id, color=port_color, size=(port_size_x, port_size_y),
                                                         coord=(self.picture_offset[0] + coord_x,
                                                                self.picture_offset[1] + coord_y), parent_draw=self,
                                                         port=port))
            # self.host_port_list = remove_not_completed_in_list(self.host_port_list)

            if "down" not in port.oper_state and "sfp-not-present" not in port.oper_state:
                self.draw_rectangle(draw=self.draw,
                                    coordinates=((self.picture_offset[0] + coord_x, self.picture_offset[1] + coord_y),
                                                 (self.picture_offset[0] + coord_x + port_size_x,
                                                  self.picture_offset[1] + coord_y + port_size_y)), color=port_color,
                                    width=rectangle_width)

        for port in self._parent.fabric_ports:
            # TODO find a way to avoid unused port
            if port.oper_state != "indeterminate":
                port_color = self.COLOR_LAN_UPLINK_PORTS
            else:
                port_color = self.COLOR_DEFAULT
            port_id = port.port_id
            rectangle_width = self.WIDTH_PORT_RECTANGLE_DEFAULT

            if ("1/" + port_id) in self.json_file["rear_ports"]:  # Temporary fix for UCS PE's bugs
                port_info = self.json_file["rear_ports"]["1/" + port_id]
            else:
                continue

            port_size_x = port_info['port_size'][0]
            port_size_y = port_info['port_size'][1]
            coord_x = port_info['port_coord'][0]
            coord_y = port_info['port_coord'][1]

            self.fabric_port_list.append(UcsSystemDrawPort(id=port_id, color=port_color,
                                                           size=(port_size_x, port_size_y),
                                                           coord=(self.picture_offset[0] + coord_x,
                                                                  self.picture_offset[1] + coord_y),
                                                           parent_draw=self, port=port))
            # self.fabric_port_list = remove_not_completed_in_list(self.host_port_list)

            self.draw_rectangle(draw=self.draw,
                                coordinates=((self.picture_offset[0] + coord_x, self.picture_offset[1] + coord_y),
                                             (self.picture_offset[0] + coord_x + port_size_x,
                                              self.picture_offset[1] + coord_y + port_size_y)),
                                color=port_color,
                                width=rectangle_width)


class UcsSystemDrawFexFront(GenericUcsDrawEquipment):
    def __init__(self, parent=None):
        GenericUcsDrawEquipment.__init__(self, parent=parent, orientation="front")
        if not self.picture:
            return

        self.background = self._create_background(self.canvas_width, self.canvas_height, self.canvas_color)
        self.draw = self._create_draw()

        self.paste_layer(self.picture, self.picture_offset)

        if "psus_slots" in self.json_file:
            self.power_supplies = self.get_power_supplies()

        self._file_name = self._device_target + "_fex_" + self._parent.id + "_front"

    def get_power_supplies(self):
        psu_list = []
        for psu in self._parent.power_supplies:
            if psu.id != '0':
                psu_list.append(GenericUcsDrawPsu(psu, self))
        return psu_list
