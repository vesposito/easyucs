# coding: utf-8
# !/usr/bin/env python

""" object.py: Easy UCS Deployment Tool """
from easyucs import __author__, __copyright__,  __version__, __status__

import json
import os

from PIL import Image, ImageDraw, ImageFont


class GenericDrawObject:
    COLOR_DEFAULT = "black"

    def __init__(self, parent=None, orientation="rear"):
        self._parent = parent
        self._parent_having_logger = self._find_logger()

        self._orientation = orientation

        self._inventory = self.__find_inventory()
        self._device_target = self._inventory.parent.parent.target
        self._output_directory = "temp"

        self.picture = None
        self.json_file = None

        self.canvas_color = (255, 255, 255, 255)  # white

    @staticmethod
    def rotate_object(obj=None, picture=None):
        # Rotate objects
        if obj.__class__.__name__ == "UcsSystemDrawFiRear":
            obj.picture = obj.picture.rotate(90, expand=1)
            obj.json_file['rear_file_size'] = obj.json_file['rear_file_size'][1], obj.json_file['rear_file_size'][0]
            for port in obj.json_file['rear_ports']:
                obj.json_file['rear_ports'][port]['port_coord'] = obj.json_file['rear_ports'][port]['port_coord'][1], \
                                                                  obj.json_file['rear_file_size'][1] - \
                                                                  obj.json_file['rear_ports'][port]['port_coord'][0] - \
                                                                  obj.json_file['rear_ports'][port]['port_size'][0]
                obj.json_file['rear_ports'][port]['port_size'] = obj.json_file['rear_ports'][port]['port_size'][1], \
                                                                 obj.json_file['rear_ports'][port]['port_size'][0]
            return obj

        if picture and not obj:
            picture = picture.rotate(90, expand=1)
            return picture
        else:
            obj.picture = obj.picture.rotate(90, expand=1)
            return obj

    def logger(self, level='info', message="No message"):
        if not self._parent_having_logger:
            self._parent_having_logger = self._find_logger()

        if self._parent_having_logger:
            self._parent_having_logger.logger(level=level, message=message)

    def _find_logger(self):
        # Method to find the object having a logger - it can be high up in the hierarchy of objects
        current_object = self
        while hasattr(current_object, '_parent') and not hasattr(current_object, '_logger_handle'):
            current_object = current_object._parent

        while hasattr(current_object, 'parent') and not hasattr(current_object, '_logger_handle'):
            current_object = current_object.parent

        if hasattr(current_object, '_logger_handle'):
            return current_object
        else:
            print("WARNING: No logger found in inventory object")
            return None

    def _find_folder_path(self):
        if self._parent.__class__.__name__ == "UcsSystemFi" or self._parent.__class__.__name__ == "UcsSystemGem":
            folder_path = "catalog/fabric_interconnects/"
        elif "Adapter" in self._parent.__class__.__name__ or "Adaptor" in self._parent.__class__.__name__:
            folder_path = "catalog/adaptors/"
        elif "Chassis" in self._parent.__class__.__name__:
            folder_path = "catalog/chassis/"
        elif self._parent.__class__.__name__ in ["UcsSystemBlade", "UcsImcServerNode"]:
            folder_path = "catalog/blades/"
        elif self._parent.__class__.__name__ == "UcsSystemPsu":
            folder_path = "catalog/power_supplies/"
        elif self._parent.__class__.__name__ == "UcsSystemStorageLocalDisk":
            folder_path = "catalog/drives/"
        elif "Iom" in self._parent.__class__.__name__ or "Sioc" in self._parent.__class__.__name__:
            folder_path = "catalog/io_modules/"
        elif "Rack" in self._parent.__class__.__name__:
            if self._parent.model == "UCSC-C125":
                folder_path = "catalog/server_nodes/"
            else:
                folder_path = "catalog/racks/"
        elif self._parent.__class__.__name__ == "UcsSystemFex":
            folder_path = "catalog/fabric_extenders/"
        elif "Cpu" in self.__class__.__name__:
            folder_path = "catalog/cpu_modules/"
        else:
            self.logger(level="error", message="Could not find catalog folder path for " +
                                               self._parent.__class__.__name__ + " objects")
            return None

        return folder_path

    def _get_picture(self):
        folder_path = self._find_folder_path()
        if folder_path is None:
            return False

        if self.json_file:
            if self._orientation + "_file_name" in self.json_file:
                file_name = self.json_file[self._orientation + "_file_name"]
            else:
                self.logger(level="error", message="Could not find key \"" + self._orientation +
                                                   "_file_name\" in JSON file " + self._parent.sku + ".json")
                return False
        else:
            return False
        try:
            self.picture = Image.open(folder_path + "img/" + file_name, 'r')
        except FileNotFoundError:
            self.logger(level="error", message="Image file " + folder_path + "img/" + file_name + " not found")
            return False
        return True

    def _get_json_file(self):
        file_name = str(self._parent.sku)
        folder_path = self._find_folder_path()

        try:
            json_file = open(folder_path + str(file_name) + ".json")
            json_string = json_file.read()
            json_file.close()
            self.json_file = json.loads(json_string)
        except FileNotFoundError:
            self.logger(level="error", message="JSON file " + folder_path + file_name + ".json" + " not found")

    def _get_picture_offset(self):
        img_w, img_h = self.picture.size
        # 0 is an arbitrary value
        return 0, self.canvas_height - img_h

    def _create_background(self, width=None, height=None, color=None):
        if not width:
            width = self.canvas_width
        if not height:
            height = self.canvas_height
        if not color:
            color = self.canvas_color
        return Image.new('RGBA', (width, height), color)

    def _create_draw(self):
        return ImageDraw.Draw(self.background)

    def paste_layer(self, layer, layer_offset):
        self.background.paste(layer, layer_offset, mask=layer)

    def save_image(self, file_name=None, output_directory=None, format="png"):
        if not hasattr(self, "_file_name"):
            # If the object has not the _file_name attribute then the object has not been created correctly
            self.logger(level="warning",
                        message="Couldn't create picture of " + self.__class__.__name__ + " with ID " + self._parent.id)
            return False
        if not file_name:
            file_name = self._file_name
        if not output_directory:
            output_directory = self._output_directory + "/" + self._device_target

        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        self.background.save(output_directory + '/' + file_name + "." + format)
        self.logger(message="Image " + output_directory + '/' + file_name + "." + format + " saved")

    @staticmethod
    def draw_rectangle(draw, coordinates, color, width=1, fill=None):
        for i in range(width):
            rect_start = (coordinates[0][0] + i, coordinates[0][1] + i)
            rect_end = (coordinates[1][0] - i, coordinates[1][1] - i)
            draw.rectangle((rect_start, rect_end), outline=color, fill=fill)

    def __str__(self):
        return self.__class__.__name__ + "\n" +\
               str({key: value for key, value in vars(self).items() if not key.startswith('_')})

    def __find_inventory(self):
        # Method to find the Inventory object - it can be high up in the hierarchy of objects
        current_object = self
        while hasattr(current_object, '_parent') and not hasattr(current_object, 'timestamp'):
            current_object = current_object._parent
        if hasattr(current_object, 'timestamp'):
            return current_object
        else:
            return None


class GenericUcsDrawObject(GenericDrawObject):
    WIDTH_PORT_RECTANGLE_DEFAULT = 10
    WIDTH_PORT_RECTANGLE_BREAKOUT = 7
    WIDTH_PORT_SEPARATOR_BREAKOUT = 3

    # List of supported colors : https://en.wikipedia.org/wiki/X11_color_names#Color_name_chart
    COLOR_LAN_UPLINK_PORTS = "dodgerblue"
    COLOR_SERVER_PORTS = "greenyellow"
    COLOR_SAN_UPLINK_PORTS = "green"
    COLOR_SAN_STORAGE_PORTS = "lightblue"
    COLOR_FCOE_UPLINK_PORTS = "yellow"
    COLOR_FCOE_STORAGE_PORTS = "orange"
    COLOR_APPLIANCE_STORAGE_PORTS = "grey"
    COLOR_UNIFIED_UPLINK_PORTS = "brown"
    COLOR_UNIFIED_STORAGE_PORTS = "violet"
    COLOR_LAN_MONITOR_PORTS = "antiquewhite"
    COLOR_SAN_MONITOR_PORTS = "burlywood"

    COLOR_LINK_FC_16G = "goldenrod"
    COLOR_LINK_FC_1G = "pink"
    COLOR_LINK_FC_2G = "red"
    COLOR_LINK_FC_4G = "brown"
    COLOR_LINK_FC_8G = "grey"
    COLOR_LINK_FC_32G = "tomato"
    COLOR_LINK_FC_AUTO = "lavender"
    COLOR_LINK_FC_INDETERMINATE = "blue"

    COLOR_LINK_ETHER_10G = "violet"
    COLOR_LINK_ETHER_1G = "khaki"
    COLOR_LINK_ETHER_20G = "green"
    COLOR_LINK_ETHER_25G = "slateblue"
    COLOR_LINK_ETHER_40G = "crimson"
    COLOR_LINK_ETHER_100G = "salmon"
    COLOR_LINK_ETHER_AUTO = "olive"
    COLOR_LINK_ETHER_INDETERMINATE = "limegreen"

    WIRE_DISTANCE_LONG = 26
    WIRE_DISTANCE_SHORT = 6
    WIDTH_WIRE_BREAKOUT = 7
    WIDTH_WIRE = 14

    def draw_port_wire_legend(self, infra, port_color_list=[], wire_color_list=[]):

        # Collection of colors
        port_color_collection = [{"color": self.COLOR_LAN_UPLINK_PORTS, "name": "LAN UPLINK PORTS"},
                                 {"color": self.COLOR_SERVER_PORTS, "name": "SERVER PORTS"},
                                 {"color": self.COLOR_SAN_UPLINK_PORTS, "name": "SAN UPLINK PORTS"},
                                 {"color": self.COLOR_SAN_STORAGE_PORTS, "name": "SAN STORAGE PORTS"},
                                 {"color": self.COLOR_FCOE_UPLINK_PORTS, "name": "FCOE UPLINK PORTS"},
                                 {"color": self.COLOR_FCOE_STORAGE_PORTS, "name": "FCOE STORAGE PORTS"},
                                 {"color": self.COLOR_APPLIANCE_STORAGE_PORTS, "name": "APPLIANCE STORAGE PORTS"},
                                 {"color": self.COLOR_UNIFIED_UPLINK_PORTS, "name": "UNIFIED UPLINK PORTS"},
                                 {"color": self.COLOR_UNIFIED_STORAGE_PORTS, "name": "UNIFIED STORAGE PORTS"},
                                 {"color": self.COLOR_LAN_MONITOR_PORTS, "name": "LAN MONITOR PORTS"},
                                 {"color": self.COLOR_SAN_MONITOR_PORTS, "name": "SAN MONITOR PORTS"}]

        wire_color_collection = [{"color": self.COLOR_LINK_FC_32G, "name": "LINK FC 32G"},
                                 {"color": self.COLOR_LINK_FC_16G, "name": "LINK FC 16G"},
                                 {"color": self.COLOR_LINK_FC_1G, "name": "LINK FC 1G"},
                                 {"color": self.COLOR_LINK_FC_2G, "name": "LINK FC 2G"},
                                 {"color": self.COLOR_LINK_FC_4G, "name": "LINK FC 4G"},
                                 {"color": self.COLOR_LINK_FC_8G, "name": "LINK FC 8G"},
                                 {"color": self.COLOR_LINK_FC_AUTO, "name": "LINK FC AUTO"},
                                 {"color": self.COLOR_LINK_FC_INDETERMINATE, "name": "LINK FC INDETERMINATE"},
                                 {"color": self.COLOR_LINK_ETHER_10G, "name": "LINK ETHER 10G"},
                                 {"color": self.COLOR_LINK_ETHER_1G, "name": "LINK ETHER 1G"},
                                 {"color": self.COLOR_LINK_ETHER_20G, "name": "LINK ETHER 20G"},
                                 {"color": self.COLOR_LINK_ETHER_25G, "name": "LINK ETHER 25G"},
                                 {"color": self.COLOR_LINK_ETHER_40G, "name": "LINK ETHER 40G"},
                                 {"color": self.COLOR_LINK_ETHER_100G, "name": "LINK ETHER 100G"},
                                 {"color": self.COLOR_LINK_ETHER_AUTO, "name": "LINK ETHER AUTO"},
                                 {"color": self.COLOR_LINK_ETHER_INDETERMINATE, "name": "LINK ETHER INDETERMINATE"}]

        canvas_width = infra.background.size[0]
        canvas_height = infra.background.size[1]

        fill_color = "black"
        font_size = 40
        font_size_title = 60
        font_title = ImageFont.truetype('arial.ttf', font_size_title)
        font = ImageFont.truetype('arial.ttf', font_size)

        height_betw_title_line = 100
        height_betw_line = 80
        align_left = 40
        space_rect_txt = 100

        # Search height of the legend
        height_betw_server_legend = 30
        legend_height = (len(wire_color_list) + len(port_color_list)) * height_betw_line + height_betw_title_line

        # New canvas dimensions
        new_background = Image.new('RGBA', (canvas_width, canvas_height + legend_height + height_betw_server_legend),
                                   'white')
        new_background.paste(infra.background, mask=infra.background)
        new_draw = ImageDraw.Draw(new_background)
        infra.background = new_background
        infra.draw = new_draw

        # Drawing the legend
        height_start = infra.background.size[1] - legend_height
        height_line = height_start + height_betw_title_line

        infra.draw.text((align_left, height_start), "Legend", fill=fill_color, font=font_title)

        # Determine the longest text
        max_len_txt = 0

        if port_color_list:
            for color in port_color_collection:
                for p_type in port_color_list:
                    if p_type == color["color"]:
                        infra.draw.text((align_left + space_rect_txt, height_line), color["name"], fill=fill_color,
                                        font=font)
                        self.draw_rectangle(infra.draw,
                                            ((align_left, height_line - 3), (align_left + 80, height_line + 52)),
                                            color["color"], width=10)

                        height_line = height_line + height_betw_line

                        if len(color["name"]) > max_len_txt:
                            max_len_txt = len(color["name"])
        else:
            for color in port_color_collection:
                infra.draw.text((align_left + space_rect_txt, height_line), color["name"], fill=fill_color, font=font)
                self.draw_rectangle(infra.draw, ((align_left, height_line - 3), (align_left + 80, height_line + 52)),
                                    color["color"], width=10)
                height_line = height_line + height_betw_line

                if len(color["name"]) > max_len_txt:
                    max_len_txt = len(color["name"])

        if wire_color_list:
            for color in wire_color_collection:
                for p_type in wire_color_list:
                    if p_type == color["color"]:
                        infra.draw.text((align_left + space_rect_txt, height_line), color["name"], fill=fill_color,
                                        font=font)
                        infra.draw.line(((align_left, height_line + 28), (align_left + 80, height_line + 28)),
                                        color["color"], width=10)
                        height_line = height_line + height_betw_line

                        if len(color["name"]) > max_len_txt:
                            max_len_txt = len(color["name"])
        else:
            for color in wire_color_collection:
                infra.draw.text((align_left + space_rect_txt, height_line), color["name"], fill=fill_color, font=font)
                infra.draw.line(((align_left, height_line + 28), (align_left + 80, height_line + 28)), color["color"],
                                width=10)
                height_line = height_line + height_betw_line

                if len(color["name"]) > max_len_txt:
                    max_len_txt = len(color["name"])

        # Draw frame around legend
        max_txt = 'X' * max_len_txt
        w, h = infra.draw.textsize(max_txt, font=font)
        frame_w = w + align_left + space_rect_txt
        frame_wire_width = 5
        infra.draw.line(((0, canvas_height + round(height_betw_server_legend / 2)),
                         (frame_w, canvas_height + round(height_betw_server_legend / 2))), fill='black',
                        width=frame_wire_width)
        # infra.draw.line(((0, height_start+round(height_betw_server_legend)),
        # (frame_w,  height_start+round(height_betw_server_legend))), fill='black', width=frame_wire_width)
        infra.draw.line(((frame_w, canvas_height + round(height_betw_server_legend / 2)),
                         (frame_w, infra.background.size[1])), fill='black', width=frame_wire_width)
        # frame_wire_width * 2 : in order to see the wire like if they were not cropped outside the canvas
        infra.draw.line(((0, infra.background.size[1]),
                         (frame_w, infra.background.size[1])), fill='black', width=frame_wire_width * 2)
        infra.draw.line(((0, canvas_height + round(height_betw_server_legend / 2)),
                         (0, infra.background.size[1])), fill='black', width=frame_wire_width * 2)

    def draw_service_profile_template_legend(self, infra, sp_template_list):
        if sp_template_list:
            canvas_width = infra.background.size[0]
            canvas_height = infra.background.size[1]

            fill_color = "black"
            font_size = 40
            font_size_title = 60
            font_title = ImageFont.truetype('arial.ttf', font_size_title)
            font = ImageFont.truetype('arial.ttf', font_size)

            height_betw_title_line = 100
            height_betw_line = 80
            align_left = 40
            space_rect_txt = 100

            # Change the name of the template for a better understanding
            template_list = []
            if sp_template_list:
                for template in sp_template_list:
                    if template["template_name"]:
                        template_name = template["template_name"] + ' (' + template["template_org"] + ')'
                        list = {"color": template["color"], "template_name": template_name,
                                "template_org": template["template_org"]}
                        template_list.append(list)

            # Search height of the legend
            height_betw_server_legend = 30
            legend_height = len(template_list) * height_betw_line + height_betw_title_line

            # New canvas dimensions
            new_background = Image.new('RGBA',
                                       (canvas_width, canvas_height + legend_height + height_betw_server_legend),
                                       'white')
            new_background.paste(infra.background, mask=infra.background)
            new_draw = ImageDraw.Draw(new_background)
            infra.background = new_background
            infra.draw = new_draw

            # Drawing the legend
            height_start = infra.background.size[1] - legend_height
            height_line = height_start + height_betw_title_line

            infra.draw.text((align_left, height_start), "Legend", fill=fill_color, font=font_title)

            # Determine the longest text
            max_len_txt = 0

            if template_list:
                for template in template_list:
                    if template["template_name"]:
                        infra.draw.text((align_left + space_rect_txt, height_line), template["template_name"],
                                        fill=fill_color, font=font)
                        self.draw_rectangle(infra.draw,
                                            ((align_left, height_line - 3), (align_left + 80, height_line + 52)),
                                            template["color"], width=10, fill=template["color"])
                        height_line = height_line + height_betw_line

                        if len(template["template_name"]) > max_len_txt:
                            max_len_txt = len(template["template_name"])

            # Draw frame around legend
            max_txt = 'X' * max_len_txt
            w, h = infra.draw.textsize(max_txt, font=font)
            frame_w = w + align_left + space_rect_txt
            frame_wire_width = 5
            infra.draw.line(((0, canvas_height + round(height_betw_server_legend / 2)),
                             (frame_w, canvas_height + round(height_betw_server_legend / 2))), fill='black',
                            width=frame_wire_width)
            # infra.draw.line(((0, height_start+round(height_betw_server_legend)),
            # (frame_w,  height_start+round(height_betw_server_legend))), fill='black', width=frame_wire_width)
            infra.draw.line(((frame_w, canvas_height + round(height_betw_server_legend / 2)),
                             (frame_w, infra.background.size[1])), fill='black', width=frame_wire_width)
            # frame_wire_width * 2 : in order to see the wire like if they were not cropped outside the canvas
            infra.draw.line(((0, infra.background.size[1]),
                             (frame_w, infra.background.size[1])), fill='black', width=frame_wire_width * 2)
            infra.draw.line(((0, canvas_height + round(height_betw_server_legend / 2)),
                             (0, infra.background.size[1])), fill='black', width=frame_wire_width * 2)

    def __init__(self, parent=None, orientation="rear"):
        GenericDrawObject.__init__(self, parent=parent, orientation=orientation)


class GenericUcsDrawEquipment(GenericUcsDrawObject):
    def __init__(self, parent=None, orientation="rear"):
        GenericUcsDrawObject.__init__(self, parent=parent, orientation=orientation)

        self._get_json_file()
        self._get_picture()
        if self.picture:
            self.canvas_width = self.picture.size[0]
            self.canvas_height = self.picture.size[1]
            self.picture_offset = self._get_picture_offset()
        else:
            self.canvas_width = 0
            self.canvas_height = 0
            self.picture_offset = 0


class UcsSystemDrawInfraEquipment(GenericUcsDrawObject):
    def __init__(self, parent=None):
        GenericUcsDrawObject.__init__(self, parent=parent)
