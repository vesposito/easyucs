# coding: utf-8
# !/usr/bin/env python

""" service_profile.py: Easy UCS Deployment Tool """

import math

from PIL import Image, ImageDraw, ImageFont

from draw.object import UcsSystemDrawInfraEquipment
from draw.ucs.chassis import UcsChassisDrawRear, UcsChassisDrawFront
from draw.ucs.rack import UcsRackDrawRear, UcsRackDrawFront, UcsSystemDrawRackEnclosureRear


class UcsSystemDrawInfraServiceProfile(UcsSystemDrawInfraEquipment):
    def __init__(self, parent=None, draw_chassis_list=[], draw_chassis_front_list=[], draw_chassis_rear_list=[],
                 draw_rack_list=[], draw_rack_enclosure_list=[], page=1):
        UcsSystemDrawInfraEquipment.__init__(self, parent=parent)
        self._parent = parent

        self.next_page_infra = None

        if draw_chassis_list:
            self.chassis_list = draw_chassis_list
        elif draw_chassis_front_list or draw_chassis_rear_list:
            self.chassis_list = self._parse_chassis(draw_chassis_front_list, draw_chassis_rear_list)
        else:
            self.chassis_list = []
        self.rack_list = draw_rack_list
        self.rack_enclosure_list = draw_rack_enclosure_list

        if self.rack_list:
            self.duplicate_rack_list()
        if self.rack_enclosure_list:
            self.duplicate_rack_enclosure_list()
        if self.chassis_list:
            self.duplicate_chassis_list()
        
        self.page = page
        # max 3 equipments in a row
        self.max_in_a_row = 3

        self.max_chassis_per_page = 6
        self.max_rack_per_page = 12
        self.max_rack_enclosure_per_page = 12

        # Adapt max_in_a_row value
        if self.chassis_list:
            if len(self.chassis_list) < self.max_in_a_row:
                self.max_in_a_row = len(self.chassis_list)

            if len(self.chassis_list) < self.max_chassis_per_page:
                self.number_of_row = math.ceil(len(self.chassis_list) / self.max_in_a_row)
            else:
                self.number_of_row = math.ceil(self.max_chassis_per_page/self.max_in_a_row)

        elif self.rack_list:
            if len(self.rack_list) < self.max_in_a_row:
                self.max_in_a_row = len(self.rack_list)

            if len(self.rack_list) < self.max_rack_per_page:
                self.number_of_row = math.ceil(len(self.rack_list) / self.max_in_a_row)
            else:
                self.number_of_row = math.ceil(self.max_rack_per_page/self.max_in_a_row)

        elif self.rack_enclosure_list:
            if len(self.rack_enclosure_list) < self.max_in_a_row:
                self.max_in_a_row = len(self.rack_enclosure_list)

            if len(self.rack_enclosure_list) < self.max_rack_per_page:
                self.number_of_row = math.ceil(len(self.rack_enclosure_list) / self.max_in_a_row)
            else:
                self.number_of_row = math.ceil(self.max_rack_per_page/self.max_in_a_row)

        self.horiz_space = 100
        self.verti_space = 150
        self.canvas_width = self.max_in_a_row * (self._max_width() + self.horiz_space)
        self.canvas_height = (self._max_height() + self.verti_space) * self.number_of_row
        self.canvas_color = (255, 255, 255, 255)  # white

        self.background = self._create_background(self.canvas_width, self.canvas_height, self.canvas_color)
        self.draw = self._create_draw()

        self.color_list_per_sp_template = self._inventory._draw_color_list_per_sp_template
        self.sp_template_used = []

        self.equipments_dict = self.sort_equipments()

        self.font_size_name = self._max_length_sp_name()
        self.font_size_org = round(self.font_size_name / 2)

        for order, equipment in self.equipments_dict.items():
            equipment.picture_offset = self._get_picture_offset(order, equipment)
            equipment.draw = self.draw
            equipment.background = self.background
            # As we drop the picture before, we need to recreate it and drop it again after pasting the layer
            equipment._get_picture()
            self.paste_layer(equipment.picture, equipment.picture_offset)
            equipment.picture = None

            if "Chassis" in equipment.__class__.__name__:
                equip_type = "chassis"
                if "blades_slots" in equipment.json_file:
                    equipment.blade_list = equipment.get_blades()
                if "blades_slots_rear" in equipment.json_file:
                    equipment.sioc_list = equipment.get_sioc_list()
                    if "blades_slots_rear" in equipment.json_file:
                        equipment.blade_list = equipment.get_blades()
                    if "psus_slots_rear" in equipment.json_file:
                        equipment.psu_list = equipment.get_power_supplies()
                # We have to check differently as there is no difference in compute slots or pcie slots on the json file
                if hasattr(equipment, "pcie_nodes") and equipment.pcie_nodes:
                    equipment.pcie_nodes = equipment.get_pcie_nodes()
                if "psus_slots" in equipment.json_file:
                    equipment.psu_list = equipment.get_power_supplies()
                if "disks_slots_rear" in equipment.json_file:
                    equipment.storage_enclosures = equipment.get_storage_enclosures()
                if "blades_slots" or "psus_slots" or "blades_slots_rear" in equipment.json_file:
                    equipment.fill_blanks()
            elif "Enclosure" in equipment.__class__.__name__:
                equip_type = "rack_enclosure"
                equipment.server_nodes_list = equipment.get_server_nodes()
                equipment.psu_list = equipment.get_psu_list()
                equipment.fill_blanks()
            elif "Rack" in equipment.__class__.__name__:
                equip_type = "rack"
                equipment.storage_controller_list = equipment.get_storage_controllers()
                if equipment._parent.sku in ["UCSC-C480-M5"]:
                    equipment.cpu_modules = equipment.get_cpu_modules()
                equipment.nvme_list = equipment.get_nvme_disks()
                for disk in equipment.nvme_list:
                    self.paste_layer(disk.picture, disk.picture_offset)
                equipment.fill_blanks()
            # Draw text related to equipment drawn above
            self.draw_equipment_service_profile_info(equip_type, equipment)

        self.parse_template_list()
        self.draw_service_profile_template_legend(self, self.color_list_per_sp_template_used)

        if self.rack_list:
            type = "rack"
        elif self.chassis_list:
            type = "chassis"
        elif self.rack_enclosure_list:
            type = "rack_enclosure"
        self._file_name = self._device_target + "_infra_service_profile_" + type + '_' + str(self.page)

        # We drop the picture in order to save on memory
        self.picture = None

    def _get_picture_offset(self, order, equipment):
        # trunc will be 0 for all equipment on line 1, 1 for all equip on line 2, ....
        trunc = int(order / self.max_in_a_row)
        # X coordinate
        if order >= self.max_in_a_row:
            # We only want 0, 1 or 2 as a value
            order_in_list = order - self.max_in_a_row * int(order / self.max_in_a_row)
        else:
            order_in_list = order
        x = order_in_list * round(self.canvas_width / self.max_in_a_row)

        # Y coordinate
        # truncation of the order by the max in a row
        # y = trunc * round(self.canvas_height / self.number_of_row)
        y = trunc * round(self.canvas_height / self.number_of_row) + \
            round(self.canvas_height / self.number_of_row / 2) - round(equipment.picture_size[1] / 2)

        return x, y

    def _max_height(self):
        max = 0
        if self.chassis_list:
            for chassis in self.chassis_list:
                if chassis.picture_size[1] > max:
                    max = chassis.picture_size[1]
        elif self.rack_list:
            for rack in self.rack_list:
                if rack.picture_size[1] > max:
                    max = rack.picture_size[1]
        elif self.rack_enclosure_list:
            for rack in self.rack_enclosure_list:
                if rack.picture_size[1] > max:
                    max = rack.picture_size[1]
        return max

    def _max_width(self):
        max = 0
        if self.chassis_list:
            for chassis in self.chassis_list:
                if chassis.picture_size[0] > max:
                    max = chassis.picture_size[0]
        elif self.rack_list:
            for rack in self.rack_list:
                if rack.picture_size[0] > max:
                    max = rack.picture_size[0]
        elif self.rack_enclosure_list:
            for rack in self.rack_enclosure_list:
                if rack.picture_size[0] > max:
                    max = rack.picture_size[0]
        return max

    def _max_length_sp_name(self):
        max_name = ""
        min_length_equipment = 3000
        font_size_name = 120
        if self.equipments_dict:
            for order, equipment in self.equipments_dict.items():
                if "Chassis" in equipment.__class__.__name__:
                    for blade in equipment.blades:
                        if blade._parent.service_profile_name:
                            name = blade._parent.service_profile_name
                            if len(name) > len(max_name):
                                max_name = name
                            length = blade.picture_size[0]
                            # Exception for X-Series as it's drawn vertically
                            if "x_fabric_modules_slots" in equipment.json_file:
                                length = blade.picture_size[1]
                            if length < min_length_equipment:
                                min_length_equipment = length
                elif "Enclosure" in equipment.__class__.__name__:
                    for server_node in equipment.server_nodes_list:
                        if server_node._parent.service_profile_name:
                            name = server_node._parent.service_profile_name
                            if len(name) > len(max_name):
                                max_name = name
                            length = server_node.picture_size[0]
                            if length < min_length_equipment:
                                min_length_equipment = length
                else:
                    if equipment._parent.service_profile_name:
                        name = equipment._parent.service_profile_name
                        if len(name) > len(max_name):
                            max_name = name
                        length = equipment.picture_size[0]
                        if length < min_length_equipment:
                            min_length_equipment = length

        font = ImageFont.truetype('arial.ttf', font_size_name)
        while self.draw.textlength(max_name, font=font) > min_length_equipment:
            font_size_name -= 5
            font = ImageFont.truetype('arial.ttf', font_size_name)

        return font_size_name

    def _parse_chassis(self, chassis_front, chassis_rear):
        chassis_list = []
        for chassis in chassis_front:
            if "blades_slots" in chassis.json_file:
                chassis_list.append(chassis)
        for chassis in chassis_rear:
            if "blades_slots_rear" in chassis.json_file:
                chassis_list.append(chassis)

        chassis_list.sort(key=lambda chassis: chassis._parent.id)
        return chassis_list
    
    def duplicate_chassis_list(self):
        new_list = []
        for chassis in self.chassis_list:
            if 'Rear' in chassis.__class__.__name__:
                new_chassis = UcsChassisDrawRear(parent=chassis._parent)
            else:
                new_chassis = UcsChassisDrawFront(parent=chassis._parent)
            new_list.append(new_chassis)
            # Sort the chassis by id
        self.chassis_list = sorted(new_list, key=lambda x: int(x._parent.id))
    
    def duplicate_rack_list(self):
        new_list = []
        for rack in self.rack_list:
            if 'Rear' in rack.__class__.__name__:
                new_rack = UcsRackDrawRear(parent=rack._parent)
            else:
                new_rack = UcsRackDrawFront(parent=rack._parent)
            new_list.append(new_rack)
        # Sort the racks by id
        self.rack_list = sorted(new_list, key=lambda x: int(x._parent.id))

    def duplicate_rack_enclosure_list(self):
        new_list = []
        for rack_enclosure in self.rack_enclosure_list:
            new_rack = UcsSystemDrawRackEnclosureRear(parent=rack_enclosure._parent)
            new_list.append(new_rack)
        # Sort the racks by id
        self.rack_enclosure_list = sorted(new_list, key=lambda x: int(x._parent.id))

    def parse_template_list(self):
        parsed_list = []
        for template_used in list(set(self.sp_template_used)):
            for template in self.color_list_per_sp_template:
                if template_used == template["template_org"] + template["template_name"]:
                    parsed_list.append(template)
        self.color_list_per_sp_template_used = parsed_list

    def determine_color_service_profile(self, sp_template_name, sp_template_org):
        for dict in self.color_list_per_sp_template:
            template = dict["template_org"] + dict["template_name"]
            color = dict["color"]
            if not template:
                dict["template_org"] = sp_template_org
                dict["template_name"] = sp_template_name
                return color
            if template == sp_template_org + sp_template_name:
                return color
        self.logger(level="error", message="Too much Service Profile templates: "
                                           + str(len(self.color_list_per_sp_template)) + " is the maximum number")
        return 'grey'

    def draw_equipment_service_profile_info(self, type, equipment):
        fill_color = self.COLOR_DEFAULT
        font_name = ImageFont.truetype('arial.ttf', self.font_size_name)
        font_org = ImageFont.truetype('arial.ttf', self.font_size_org)
        if type == "rack":
            cover_color = "grey"

            service_profile_org = equipment._parent.service_profile_org
            service_profile_name = equipment._parent.service_profile_name
            sp_template_name = equipment._parent.service_profile_template_name
            sp_template_org = equipment._parent.service_profile_template_org
            if sp_template_name:
                self.sp_template_used.append(sp_template_org + sp_template_name)
                cover_color = self.determine_color_service_profile(sp_template_name, sp_template_org)
            cover = self.generate_cover(cover_color, equipment.picture_size)
            self.paste_layer(cover, equipment.picture_offset)

            if service_profile_name:
                left, top, right, bottom = self.draw.textbbox((0, 0), service_profile_name, font=font_name)
                l_org, t_org, r_org, b_org = self.draw.textbbox((0, 0), service_profile_org, font=font_org)

                # Draw service profile name info
                self.draw.text(
                    (equipment.picture_offset[0] + equipment.picture_size[0] / 2,
                     equipment.picture_offset[1] + equipment.picture_size[1] / 2),
                    service_profile_name, fill=fill_color, font=font_name, align="center",
                    anchor="mm")

                # Draw service profile org info
                self.draw.text(
                    (equipment.picture_offset[0] + equipment.picture_size[0] / 2 - (r_org - l_org) / 2,
                     equipment.picture_offset[1] + (t_org - b_org) / 8 + 15),
                    service_profile_org, fill=fill_color, font=font_org)

            if equipment._parent.user_label:
                rack_info = "Rack #" + equipment._parent.id + " - " + equipment._parent.user_label
            else:
                rack_info = "Rack #" + equipment._parent.id

            left, top, right, bottom = self.draw.textbbox((0, 0), rack_info, font=font_org)

            # Draw rack info
            self.draw.text(
                (equipment.picture_offset[0] + equipment.picture_size[0] / 2 - (right - left) / 2,
                 equipment.picture_offset[1] - bottom - 5),
                rack_info, fill=fill_color, font=font_org)

        elif type == "rack_enclosure":
            if "server_node_slots" in equipment.json_file:
                for server_node in equipment.server_nodes_list:
                    cover_color = "grey"

                    service_profile_org = server_node._parent.service_profile_org
                    service_profile_name = server_node._parent.service_profile_name
                    sp_template_name = server_node._parent.service_profile_template_name
                    sp_template_org = server_node._parent.service_profile_template_org
                    if sp_template_name:
                        self.sp_template_used.append(sp_template_org + sp_template_name)
                        cover_color = self.determine_color_service_profile(sp_template_name, sp_template_org)
                    cover = self.generate_cover(cover_color, server_node.picture_size)
                    self.paste_layer(cover, server_node.picture_offset)

                    if service_profile_name:
                        left, top, right, bottom = self.draw.textbbox((0, 0), service_profile_name, font=font_name)
                        l_org, t_org, r_org, b_org = self.draw.textbbox((0, 0), service_profile_org, font=font_org)

                        # Draw service profile name info
                        self.draw.text((server_node.picture_offset[0] + server_node.picture_size[0] / 2,
                                        server_node.picture_offset[1] + server_node.picture_size[1] / 2),
                                       service_profile_name, fill=fill_color, font=font_name, align="center",
                                       anchor="mm")

                        # Draw service profile org info
                        self.draw.text((server_node.picture_offset[0] + server_node.picture_size[0] / 2 - (
                                r_org - l_org) / 2,
                                        server_node.picture_offset[1] + (t_org - b_org) / 8 + 15),
                                       service_profile_org, fill=fill_color, font=font_org)

                    # if equipment._parent.user_label:
                    #     chassis_info = "Chassis #" + equipment._parent.id + " - " + equipment._parent.user_label
                    # else:
                    #     chassis_info = "Chassis #" + equipment._parent.id
                    # w, h = self.draw.textsize(chassis_info, font=font_org)
                    # self.draw.text((equipment.picture_offset[0] + equipment.picture_size[0]/2 - w/2,
                    #                 equipment.picture_offset[1] - h - 5), chassis_info,
                    #                fill=fill_color, font=font_org)

        else:
            if "blades_slots" or "blade_slots_rear" in equipment.json_file:
                equipment.blade_list = equipment.get_blades()
                for blade in equipment.blade_list:
                    cover_color = "grey"

                    service_profile_org = blade._parent.service_profile_org
                    service_profile_name = blade._parent.service_profile_name
                    sp_template_name = blade._parent.service_profile_template_name
                    sp_template_org = blade._parent.service_profile_template_org
                    if sp_template_name:
                        self.sp_template_used.append(sp_template_org + sp_template_name)
                        cover_color = self.determine_color_service_profile(sp_template_name, sp_template_org)
                    cover = self.generate_cover(cover_color, blade.picture_size)
                    self.paste_layer(cover, blade.picture_offset)

                    # Draw service profile info
                    if service_profile_name:
                        left, top, right, bottom = self.draw.textbbox((0, 0), service_profile_name, font=font_name)
                        l_org, t_org, r_org, b_org = self.draw.textbbox((0, 0), service_profile_org, font=font_org)
                        # Exception for X-Series to draw text vertically / draw.text cannot rotate text
                        if "x_fabric_modules_slots" in equipment.json_file:
                            # Draw service profile name info
                            self.rotate_text(font=font_name, text=service_profile_name,
                                             x=(blade.picture_offset[0] + blade.picture_size[0] / 2),
                                             y=(blade.picture_offset[1] + blade.picture_size[1] / 2),
                                             fill=fill_color, angle=90)

                            # Draw service profile org info
                            # Align center:
                            # y = (blade.picture_offset[1] + blade.picture_size[1] / 2 - (b_org - t_org) / 2)
                            # Align top:
                            # y = (blade.picture_offset[1] + r_org - b_org)
                            self.rotate_text(font=font_org, text=service_profile_org,
                                             # x=(blade.picture_offset[0] + blade.picture_size[0] - b_org), # Angle 270
                                             x=(blade.picture_offset[0] + b_org /2),
                                             y=(blade.picture_offset[1] + blade.picture_size[1] / 2),
                                             fill=fill_color, angle=90)
                        else:
                            # Draw service profile name info
                            self.draw.text(
                                (blade.picture_offset[0] + blade.picture_size[0] / 2,
                                 blade.picture_offset[1] + blade.picture_size[1] / 2),
                                service_profile_name, fill=fill_color, font=font_name, align="center", anchor="mm")

                            # Draw service profile org info
                            self.draw.text(
                                (blade.picture_offset[0] + blade.picture_size[0] / 2 - (r_org - l_org) / 2,
                                 blade.picture_offset[1] + (t_org - b_org) / 8 + 15),
                                service_profile_org, fill=fill_color, font=font_org)

                    # Draw equipment info
                    if equipment._parent.user_label:
                        chassis_info = "Chassis #" + equipment._parent.id + " - " + equipment._parent.user_label
                    else:
                        chassis_info = "Chassis #" + equipment._parent.id

                    left, top, right, bottom = self.draw.textbbox((0, 0), chassis_info, font=font_org)
                    self.draw.text((equipment.picture_offset[0] + equipment.picture_size[0] / 2 - (right - left) / 2,
                                    equipment.picture_offset[1] - bottom - 5), chassis_info, fill=fill_color,
                                   font=font_org)

    def generate_cover(self, color, size):
        img = Image.new('RGBA', size, color)
        img.putalpha(240)
        draw = ImageDraw.Draw(img)
        return img

    def sort_equipments(self):
        equipments_dict = dict()
        i = 0
        if self.rack_list:
            for i in range(0, len(self.rack_list)):
                if i == self.max_rack_per_page:
                    self.next_page_infra = \
                        UcsSystemDrawInfraServiceProfile(draw_rack_list=self.rack_list[i:len(self.rack_list)],
                                                         page=self.page + 1, parent=self._parent)
                if i < self.max_rack_per_page:
                    equipments_dict.update({i: self.rack_list[i]})
        if self.chassis_list:
            if self.rack_list:
                for j in range(i, len(self.chassis_list) + len(self.rack_list)):
                    equipments_dict.update({i: self.chassis_list[i]})
            else:
                for j in range(0, len(self.chassis_list)):
                    if j == self.max_chassis_per_page:
                        self.next_page_infra = UcsSystemDrawInfraServiceProfile(
                            draw_chassis_list=self.chassis_list[j:len(self.chassis_list)], page=self.page + 1,
                            parent=self._parent)
                    if j < self.max_chassis_per_page:
                        equipments_dict.update({j: self.chassis_list[j]})
        if self.rack_enclosure_list:
            for i in range(0, len(self.rack_enclosure_list)):
                if i == self.max_rack_enclosure_per_page:
                    self.next_page_infra = \
                        UcsSystemDrawInfraServiceProfile(draw_rack_enclosure_list=self.rack_enclosure_list[i:len(self.rack_enclosure_list)],
                                                         page=self.page + 1, parent=self._parent)
                if i < self.max_rack_enclosure_per_page:
                    equipments_dict.update({i: self.rack_enclosure_list[i]})

        return equipments_dict
