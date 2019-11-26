# coding: utf-8
# !/usr/bin/env python

""" chassis.py: Easy UCS Deployment Tool """
from easyucs import __author__, __copyright__,  __version__, __status__


from easyucs.draw.object import GenericUcsDrawEquipment
from PIL import Image, ImageDraw, ImageTk, ImageFont


class GenericUcsDrawStorageEnclosure:
    def __init__(self, parent=None, parent_draw=None):
        self.parent_draw = parent_draw
        self._parent = parent

        self.disks = self._get_disks()

        self.draw_disks()

    def _get_disks(self):
        disk_list = []
        for disk in self._parent.disks:
            disk_list.append(UcsSystemDrawStorageLocalDisk(parent=disk, parent_draw=self))
        # disk_list = remove_not_completed_in_list(disk_list)
        return disk_list

    def draw_disks(self):
        for disk in self.disks:
            if self.parent_draw.__class__.__name__ == "GenericUcsDrawBlade":
                self.parent_draw.parent_draw.paste_layer(disk.picture, disk.picture_offset)
            elif self.parent_draw.__class__.__name__ in ["UcsImcDrawChassisRear", "UcsSystemDrawChassisRear"]:
                self.parent_draw.paste_layer(disk.picture, disk.picture_offset)
            # else:
            #     self.parent_draw.paste_layer(disk.picture, disk.picture_offset)


class UcsSystemDrawStorageController:
    def __init__(self, parent=None, parent_draw=None):
        self.parent_draw = parent_draw
        self._parent = parent

        self.disks = self._get_disks()
        self.draw_disks()
        self.fill_blanks()

    def _get_disks(self):
        disk_list = []
        for disk in self._parent.disks:
            # We handle the rear slot disks present on C240 M5 models
            if "M5" in self.parent_draw._parent.sku:
                if "Front" in self.parent_draw.__class__.__name__:
                    if int(disk.id) not in [int(disk['id']) for disk in self.parent_draw.json_file["disks_slots"]]:
                        continue
                if "Rear" in self.parent_draw.__class__.__name__ and "disks_slots_rear" in self.parent_draw.json_file:
                    if int(disk.id) not in [int(disk['id']) for disk in self.parent_draw.json_file["disks_slots_rear"]]:
                        continue

            # We handle the internal slot disks present on C480 M5 models
            if ("DrawRackFront" in self.parent_draw.__class__.__name__) \
                    and (self.parent_draw._parent.sku == "UCSC-C480-M5"):
                if int(disk.id) > 24:
                    continue

            # Prevent potential disk with ID 0 to be used in Draw (happens sometimes with B200 M2)
            if disk.id != "0":
                disk_list.append(UcsSystemDrawStorageLocalDisk(parent=disk, parent_draw=self))
                self.parent_draw.disk_slots_used.append(int(disk.id))
        # disk_list = remove_not_completed_in_list(disk_list)
        return disk_list

    def draw_disks(self):
        for disk in self.disks:
            if disk.picture is not None:
                if self.parent_draw.__class__.__name__ == "GenericUcsDrawBlade":
                    self.parent_draw.parent_draw.paste_layer(disk.picture, disk.picture_offset)
                else:
                    self.parent_draw.paste_layer(disk.picture, disk.picture_offset)

    def fill_blanks(self):
        if "disks_slots" in self.parent_draw.json_file:
            # For rack front or blade only
            if "Front" in self.parent_draw.__class__.__name__ or "Blade" in self.parent_draw.__class__.__name__:
                if len(self.disks) < len(self.parent_draw.json_file["disks_slots"]):  # Fill blank for disks slots
                    used_slot = []
                    potential_slot = []
                    unused_slot = []
                    for disk in self.disks:
                        used_slot.append(int(disk._parent.id))
                    # We add to the list of used slots, the slot of potential other Storage Controllers
                    used_slot = list(set(used_slot + self.parent_draw.disk_slots_used))

                    for disk in self.parent_draw.json_file["disks_slots"]:
                        potential_slot.append(disk["id"])
                    for blank_id in set(potential_slot) - set(used_slot):
                        unused_slot.append(blank_id)
                    for slot_id in unused_slot:
                        blank_name = None
                        orientation = "horizontal"
                        disk_format = None
                        for disk_slot in self.parent_draw.json_file['disks_slots']:
                            if disk_slot['id'] == slot_id:
                                orientation = disk_slot['orientation']
                                disk_format = disk_slot['format']
                        for model in self.parent_draw.json_file["disks_models"]:
                            if "type" in model and not blank_name:
                                if model["type"] == "blank" and model["format"] == disk_format:
                                    blank_name = model["name"]
                                    img = Image.open("catalog/drives/img/" + blank_name + ".png", 'r')
                                    if orientation == "vertical":
                                        img = GenericUcsDrawEquipment.rotate_object(picture=img)

                        if blank_name:
                            for slot in self.parent_draw.json_file["disks_slots"]:
                                if slot["id"] == int(slot_id):
                                    coord = slot["coord"]
                            coord_offset = self.parent_draw.picture_offset[0] + coord[0],\
                                           self.parent_draw.picture_offset[1] + coord[1]
                            if self.parent_draw.__class__.__name__ == "GenericUcsDrawBlade":
                                self.parent_draw.parent_draw.paste_layer(img, coord_offset)
                            else:
                                self.parent_draw.paste_layer(img, coord_offset)

        if "disks_slots_rear" in self.parent_draw.json_file:
            # For rack rear only
            if "Rear" in self.parent_draw.__class__.__name__:
                if len(self.disks) < len(self.parent_draw.json_file["disks_slots_rear"]):  # Fill blank for disks slots
                    used_slot = []
                    potential_slot = []
                    unused_slot = []
                    for disk in self.disks:
                        disk_id = int(disk._parent.id)
                        used_slot.append(disk_id)

                    for disk in self.parent_draw.json_file["disks_slots_rear"]:
                        potential_slot.append(disk["id"])
                    for blank_id in set(potential_slot) - set(used_slot):
                        unused_slot.append(blank_id)
                    for slot_id in unused_slot:
                        blank_name = None
                        orientation = "horizontal"
                        disk_format = None
                        for disk_slot in self.parent_draw.json_file['disks_slots_rear']:
                            if disk_slot['id'] == slot_id:
                                orientation = disk_slot['orientation']
                                disk_format = disk_slot['format']
                        for model in self.parent_draw.json_file["disks_models"]:
                            if "type" in model and not blank_name:
                                if model["type"] == "blank" and model["format"] == disk_format:
                                    blank_name = model["name"]
                                    img = Image.open("catalog/drives/img/" + blank_name + ".png", 'r')
                                    if orientation == "vertical":
                                        img = GenericUcsDrawEquipment.rotate_object(picture=img)

                        if blank_name:
                            for slot in self.parent_draw.json_file["disks_slots_rear"]:
                                if slot["id"] == int(slot_id):
                                    coord = slot["coord"]
                            coord_offset = self.parent_draw.picture_offset[0] + coord[0],\
                                           self.parent_draw.picture_offset[1] + coord[1]
                            self.parent_draw.paste_layer(img, coord_offset)


class UcsSystemDrawStorageLocalDisk(GenericUcsDrawEquipment):
    def __init__(self, parent=None, parent_draw=None):
        self.parent_draw = parent_draw
        self._parent = parent

        self.id = int(self._parent.id)

        if hasattr(self._parent, 'sku'):
            self.sku = self._parent.sku
        else:
            self.sku = None

        if self._parent.connection_protocol == "NVME":
            self.device_type = self._parent.connection_protocol + " " + self._parent.drive_type
        elif self._parent.rotational_speed_marketing:
            self.device_type = str(self._parent.rotational_speed_marketing) + " " + self._parent.connection_protocol
        else:
            self.device_type = self._parent.drive_type + " " + self._parent.connection_protocol
        self.disk_size = self._parent.size_marketing

        self.disk_info = self._get_disk_info()
        if self.disk_info is not None:
            self.size = self.disk_info["size"]
            self.orientation = self.disk_info["orientation"]
            self.format = self.disk_info["format"]

            # Special case for M5 NVMe disks
            if self._parent.connection_protocol == "NVME" and self.format == "sff_m5":
                self.format = self.format + "_nvme"

            GenericUcsDrawEquipment.__init__(self, parent=parent)

            self.background = self._create_background(self.canvas_width, self.canvas_height, self.canvas_color)
            self.draw = self._create_draw()

            self.paste_layer(self.picture, (0, 0))

            self.draw_disk_information()

        else:
            self.size = None
            self.orientation = None
            self.format = None
            self.background = None
            self.draw = None
            self.picture = None
            self.picture_offset = None

        # self.save_image(self._device_target + "__" + self._parent.id)

    def _get_json_file(self):
        pass

    def _get_picture(self):
        try:
            self.picture = Image.open("catalog/drives/img/" + self.format + ".png", 'r')
        except FileNotFoundError:
            self.logger(level="error", message="Image file " + "catalog/drives/img/" + self.format + " not found")

    def _get_picture_offset(self):
        if hasattr(self.parent_draw, "parent_draw"):
            if self.parent_draw.parent_draw.__class__.__name__ == "GenericUcsDrawBlade":
                if isinstance(self.parent_draw, GenericUcsDrawStorageEnclosure):
                    if (self.parent_draw.parent_draw._parent.sku == "UCSC-C3X60-SVRNB")\
                            or (self.parent_draw.parent_draw._parent.sku == "UCSC-C3K-M4SRB"):
                        return self.parent_draw.parent_draw.parent_draw.picture_offset[0] + self.disk_info["coord"][0],\
                               self.parent_draw.parent_draw.parent_draw.picture_offset[1] + self.disk_info["coord"][1]
            # For NVMe Disk on a blade
            elif self.parent_draw.__class__.__name__ == "GenericUcsDrawBlade":
                return self.parent_draw.picture_offset[0] + self.disk_info["coord"][0], \
                       self.parent_draw.picture_offset[1] + self.disk_info["coord"][1]

            return self.parent_draw.parent_draw.picture_offset[0] + self.disk_info["coord"][0], \
                   self.parent_draw.parent_draw.picture_offset[1] + self.disk_info["coord"][1]
        else:
            return self.parent_draw.picture_offset[0] + self.disk_info["coord"][0], \
                   self.parent_draw.picture_offset[1] + self.disk_info["coord"][1]

    def _get_disk_info(self):
        if hasattr(self.parent_draw, "parent_draw"):
            if "DrawRackRear" in self.parent_draw.parent_draw.__class__.__name__:
                if any(x in self.parent_draw.parent_draw._parent.sku
                       for x in ["UCSC-C240-M5", "HX240C-M5", "HXAF240C-M5"]):
                    for disk in self.parent_draw.parent_draw.json_file["disks_slots_rear"]:
                        if self.id == disk['id']:
                            return disk
                    if self.parent_draw.parent_draw._parent.sku == "UCSC-C240-M5S":
                        # It happens that the rear disk port ID of UCSC-C240-M5S are 11 / 12 instead of 9 / 10
                        if self.id > 10:
                            self.id = self.id - 2
                            return self._get_disk_info()

            elif "DrawChassisRear" in self.parent_draw.parent_draw.__class__.__name__:
                if self.parent_draw.parent_draw._parent.sku in ["UCSS-S3260", "UCSC-C3X60"]:
                    if self.id > 200:
                        self.id = self.id - 200
                    for disk in self.parent_draw.parent_draw.json_file["disks_slots_rear"]:
                        if self.id == disk['id']:
                            return disk

            elif "disks_slots" in self.parent_draw.parent_draw.json_file:
                for disk in self.parent_draw.parent_draw.json_file["disks_slots"]:
                    if self.id == disk['id']:
                        return disk

            elif "disks_slots" in self.parent_draw.json_file:
                for disk in self.parent_draw.json_file["disks_slots"]:
                    if self.id == disk['id']:
                        return disk

            if self._parent._parent._parent.__class__.__name__ in ["UcsSystemChassis", "UcsImcChassis"]:
                self.parent_draw.parent_draw.logger(level="error",
                                                    message="Disk with id " + str(self.id) + " of blade server " +
                                                            self._parent._parent.id +
                                                            ", no match found in the json file")
                return None
            else:
                self.parent_draw.parent_draw.logger(level="error",
                                                    message="Disk with id " + str(self.id) + " of rack server " +
                                                            self._parent._parent.id +
                                                            ", no match found in the json file")
                return None

        # For NVME disks (no storage controller as parent)
        elif hasattr(self, "parent_draw"):
            if "DrawRackRear" in self.parent_draw.__class__.__name__:
                if any(x in self.parent_draw._parent.sku
                       for x in ["UCSC-C240-M5", "HX240C-M5", "HXAF240C-M5"]):
                    for disk in self.parent_draw.json_file["disks_slots_rear"]:
                        if self.id == disk['id']:
                            return disk
                    if self.parent_draw._parent.sku == "UCSC-C240-M5S":
                        # It happens that the rear disk port ID of UCSC-C240-M5S are 11 / 12 instead of 9 / 10
                        if self.id > 10:
                            self.id = self.id - 2
                            return self._get_disk_info()

            elif "disks_slots" in self.parent_draw.json_file:
                for disk in self.parent_draw.json_file["disks_slots"]:
                    if self.id == disk['id']:
                        return disk

        else:
            if "DrawRackRear" in self.parent_draw.__class__.__name__:
                for disk in self.parent_draw.json_file["disks_slots"]:
                    if self.id == disk['id']:
                        return disk
            elif "DrawRackFront" in self.parent_draw.__class__.__name__:
                for disk in self.parent_draw.json_file["disks_slots"]:
                    if self.id == disk['id']:
                        return disk
            self.parent_draw.logger(level="error", message="Disk with id " + str(self.id) + " of rack server " +
                                                           self._parent.id + ", no match found in the json file")
            return None

    def draw_disk_information(self):
        # We first make sure that we have no variable set to "None"
        warning = False
        fill_color_sku_warning = "red"
        if self.sku is None:
            if self._parent._parent._parent.__class__.__name__ == "UcsSystemBlade":
                self.logger(level="warning", message="Disk with id " + str(self.id) + " in chassis/blade " +
                                                     self._parent._parent._parent.id +
                                                     " has an unknown SKU!")
            elif self._parent._parent._parent.__class__.__name__ in ["UcsSystemChassis", "UcsImcChassis"]:
                self.logger(level="warning",
                            message="Disk with id " + str(self.id) + " in the chassis has an unknown SKU!")
            elif self._parent._parent.__class__.__name__ in ["UcsImcRack"]:
                self.logger(level="warning", message="Disk with id " + str(self.id) + " in rack " +
                                                     self._parent._parent.id +
                                                     " has an unknown SKU!")
            else:
                self.logger(level="warning", message="Disk with id " + str(self.id) + " in rack " +
                                                     self._parent._parent._parent.id +
                                                     " has an unknown SKU!")
            warning = True
            if self._parent.vendor and self._parent.model:
                self.sku = self._parent.vendor + " " + self._parent.model
            else:
                self.sku = "UNKNOWN"

        if self.device_type is None:
            self.logger(level="warning", message="Disk with id " + str(self.id) + " of server " + self._parent.id +
                                                 " has an unknown device type!")
            warning = True
            self.device_type = ""

        if self.disk_size is None:
            self.logger(level="warning", message="Disk with id " + str(self.id) + " of server " + self._parent.id +
                                                 " has an unknown size!")
            warning = True
            self.disk_size = ""

        if self.format == "sff":
            fill_color = "black"
            if warning:
                fill_color = fill_color_sku_warning
            font_size = 16
            font = ImageFont.truetype('arial.ttf', font_size)
            start_coord = (38, 8)
            self.draw.text((start_coord[0], start_coord[1] + 0 * font_size), self.sku, fill=fill_color, font=font)
            self.draw.text((start_coord[0], start_coord[1] + 1 * font_size), self.device_type, fill=fill_color,
                           font=font)
            self.draw.text((start_coord[0], start_coord[1] + 2 * font_size), self.disk_size, fill=fill_color, font=font)

        elif self.format == "sff_7mm":
            center_square = [[190, 0], [237, 39]]
            fill_color = "black"
            if warning:
                fill_color = fill_color_sku_warning
            font_size = 11
            font = ImageFont.truetype('arial.ttf', font_size)

            text_left = self.sku
            w, h = self.draw.textsize(text_left, font=font)
            self.draw.text(
                (center_square[0][0] - 20 - w, round((center_square[1][1] - center_square[0][1]) / 2 - h / 2)),
                text_left, fill=fill_color, font=font)

            text_right = self.disk_size + " " + self.device_type
            w, h = self.draw.textsize(text_right, font=font)
            self.draw.text(
                (center_square[1][0] + 20, round((center_square[1][1] - center_square[0][1]) / 2 - h / 2)),
                text_right, fill=fill_color, font=font)

        elif self.format == "lff":
            fill_color = "white"
            if warning:
                fill_color = fill_color_sku_warning
            font_size = 16
            font = ImageFont.truetype('arial.ttf', font_size)

            start_frame_coord = (136, 124)
            end_frame_coord = (379, 148)
            self.draw.rectangle((start_frame_coord, end_frame_coord), fill=(127, 127, 127))
            frame_dim = end_frame_coord[0] - start_frame_coord[0], end_frame_coord[1] - start_frame_coord[1]

            text = self.sku + " / " + self.disk_size
            w, h = self.draw.textsize(text, font=font)
            self.draw.text((round(frame_dim[0]/2 + start_frame_coord[0] - w/2),
                            round(frame_dim[1]/2 + start_frame_coord[1] - h/2)), text,
                           fill=fill_color, font=font)

        elif self.format == "lff_m5":
            self.picture = self.rotate_object(picture=self.picture)

            # Special usage because we write on the disk after a rotation
            self.background = self._create_background(self.canvas_height, self.canvas_width, self.canvas_color)
            self.draw = self._create_draw()
            self.paste_layer(self.picture, (0, 0))

            start_frame_coord = (25, 509)
            end_frame_coord = (127, 574)
            frame_dim = end_frame_coord[0] - start_frame_coord[0], end_frame_coord[1] - start_frame_coord[1]

            fill_color = "black"
            if warning:
                fill_color = fill_color_sku_warning
            font_size_1 = 14
            font_size_2 = 13
            font_size_3 = 11

            font_1 = ImageFont.truetype('arial.ttf', font_size_1)
            font_2 = ImageFont.truetype('arial.ttf', font_size_2)
            font_3 = ImageFont.truetype('arial_bold.ttf', font_size_3)

            text_1 = self.disk_size
            w_1, h_1 = self.draw.textsize(text_1, font=font_1)
            text_2 = ''.join(self.sku.split('-')[1:])
            w_2, h_2 = self.draw.textsize(text_2, font=font_2)
            text_3 = self._parent.connection_protocol + ' ' + self._parent.drive_type
            w_3, h_3 = self.draw.textsize(text_3, font=font_3)

            self.draw.text((round(frame_dim[0] / 2 + start_frame_coord[0] - w_1 / 2), 518), text_1,
                           fill=fill_color, font=font_1)

            self.draw.text((round(frame_dim[0] / 2 + start_frame_coord[0] - w_2 / 2),
                            round(frame_dim[1] / 2 + start_frame_coord[1] - h_2 / 2)), text_2,
                           fill=fill_color, font=font_2)

            self.draw.text((round(frame_dim[0] / 2 + start_frame_coord[0] - w_3 / 2), 558), text_3,
                           fill=fill_color, font=font_3)

            # Special usage because we write on the disk after a rotation
            self.picture = self.background

            self.picture = self.rotate_object(picture=self.picture)
            self.picture = self.rotate_object(picture=self.picture)
            self.picture = self.rotate_object(picture=self.picture)

            # Special usage because we write on the disk after a rotation
            self.background = self._create_background(self.canvas_width, self.canvas_height, self.canvas_color)
            self.draw = self._create_draw()
            self.paste_layer(self.picture, (0, 0))

        elif self.format in ["sff_m5", "sff_m5_nvme"]:
            self.picture = self.rotate_object(picture=self.picture)

            # Special usage because we write on the disk after a rotation
            self.background = self._create_background(self.canvas_height, self.canvas_width, self.canvas_color)
            self.draw = self._create_draw()
            self.paste_layer(self.picture, (0, 0))

            start_frame_coord = (18, 371)
            end_frame_coord = (80, 417)
            frame_dim = end_frame_coord[0] - start_frame_coord[0], end_frame_coord[1] - start_frame_coord[1]

            fill_color = "black"

            if warning:
                fill_color = fill_color_sku_warning
            font_size_1 = 14
            font_size_2 = 8
            font_size_3 = 11

            font_1 = ImageFont.truetype('arial.ttf', font_size_1)
            font_2 = ImageFont.truetype('arial.ttf', font_size_2)
            font_3 = ImageFont.truetype('arial_bold.ttf', font_size_3)

            text_1 = self.disk_size
            w_1, h_1 = self.draw.textsize(text_1, font=font_1)
            text_2 = ''.join(self.sku.split('-')[1:])
            w_2, h_2 = self.draw.textsize(text_2, font=font_2)
            text_3 = self._parent.connection_protocol + ' ' + self._parent.drive_type
            w_3, h_3 = self.draw.textsize(text_3, font=font_3)

            self.draw.text((round(frame_dim[0] / 2 + start_frame_coord[0] - w_1 / 2), 372), text_1,
                           fill=fill_color, font=font_1)

            self.draw.text((round(frame_dim[0] / 2 + start_frame_coord[0] - w_2 / 2), 390), text_2,
                           fill=fill_color, font=font_2)

            if self.format == "sff_m5_nvme":
                fill_color = "white"

            self.draw.text((round(frame_dim[0] / 2 + start_frame_coord[0] - w_3 / 2), 403), text_3,
                           fill=fill_color, font=font_3)

            # Special usage because we write on the disk after a rotation
            self.picture = self.background

            self.picture = self.rotate_object(picture=self.picture)
            self.picture = self.rotate_object(picture=self.picture)
            self.picture = self.rotate_object(picture=self.picture)

            # Special usage because we write on the disk after a rotation
            self.background = self._create_background(self.canvas_width, self.canvas_height, self.canvas_color)
            self.draw = self._create_draw()
            self.paste_layer(self.picture, (0, 0))

        self.picture = self.background

        if self.orientation == "vertical":
            self.rotate_object(self)
