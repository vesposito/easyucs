# coding: utf-8
# !/usr/bin/env python

""" chassis.py: Easy UCS Deployment Tool """

import copy

from PIL import Image, ImageFont

from draw.object import GenericUcsDrawEquipment, UcsSystemDrawInfraEquipment
from draw.ucs.adaptor import UcsAdaptorDraw
from draw.ucs.blade import UcsBladeDrawFront
from draw.ucs.pcie_node import UcsPcieNodeDraw
from draw.ucs.port import UcsPortDraw
from draw.ucs.psu import UcsPsuDraw
from draw.ucs.storage import UcsStorageEnclosureDraw
from draw.wire import UcsSystemDrawWire


class UcsChassisDrawFront(GenericUcsDrawEquipment):
    def __init__(self, parent=None):
        GenericUcsDrawEquipment.__init__(self, parent=parent, orientation="front")
        if not self.picture:
            return

        self.background = self._create_background(self.canvas_width, self.canvas_height, self.canvas_color)
        self.draw = self._create_draw()

        self.paste_layer(self.picture, self.picture_offset)

        if "blades_slots" in self.json_file:
            self.blades = self.get_blades()
            self.pcie_nodes = self.get_pcie_nodes()
        if "psus_slots" in self.json_file:
            self.power_supplies = self.get_power_supplies()
        if ("blades_slots" or "psus_slots") in self.json_file:
            self.fill_blanks()

        if parent.__class__.__name__ in ["IntersightChassis"]:
            self._file_name = (self._device_target + "_" + parent._parent.name + "_chassis_" + str(self._parent.id) +
                               "_front")
        else:
            self._file_name = self._device_target + "_chassis_" + self._parent.id + "_front"

        # We drop the picture in order to save on memory
        self.picture = None

    def get_blades(self):
        blade_list = []
        for blade in self._parent.blades:
            blade_list.append(UcsBladeDrawFront(blade, self))
            # blade_list = remove_not_completed_in_list(blade_list)
        # blade_list = remove_not_supported_in_list(blade_list)
        # We only keep the blades that have been fully created -> picture
        blade_list = [blade for blade in blade_list if blade.picture_size]
        return blade_list

    def get_pcie_nodes(self):
        pcie_node_list = []
        for pcie_node in self._parent.pcie_nodes:
            pcie_node_list.append(UcsPcieNodeDraw(pcie_node, self))
            # blade_list = remove_not_completed_in_list(blade_list)
        # blade_list = remove_not_supported_in_list(blade_list)
        # We only keep the blades that have been fully created -> picture
        pcie_node_list = [pcie_node for pcie_node in pcie_node_list if pcie_node.picture_size]
        return pcie_node_list

    def get_power_supplies(self):
        psu_list = []
        for psu in self._parent.power_supplies:
            if psu.id != '0':
                psu_list.append(UcsPsuDraw(psu, self))
                # psu_list = remove_not_completed_in_list(psu_list)
            # psu_list = remove_not_supported_in_list(psu_list)
        # We only keep the PSU that have been fully created -> picture
        psu_list = [psu for psu in psu_list if psu.picture_size]
        return psu_list

    def fill_blanks(self):  # Fill blade slot
        if len(self._parent.blades) + len(self._parent.pcie_nodes) - 1 < len(self.json_file["blades_slots"]):
            used_slot = []
            potential_slot = []
            unused_slot = []
            for slot in self._parent.blades:
                if hasattr(slot, "scaled_mode"):
                    # We handle the specific case of a B460 M4 for which we also use the 2 slots above the master blade
                    if slot.scaled_mode == "scaled":
                        used_slot.append(int(slot.slot_id) - 2)
                        used_slot.append(int(slot.slot_id) - 1)
                        used_slot.append(int(slot.slot_id) + 1)
                    if slot.scaled_mode == "single":
                        used_slot.append(int(slot.slot_id) + 1)
                if getattr(slot, "sku", "") in ["UCSX-410C-M7"]:
                    # We handle the specific case of compute nodes taking 2 slots in the 9508 chassis
                    used_slot.append(int(slot.slot_id) + 1)
                used_slot.append(int(slot.slot_id))
            for slot in self._parent.pcie_nodes:
                used_slot.append(int(slot.slot_id))
            for slot in self.json_file["blades_slots"]:
                potential_slot.append(slot["id"])
            for blank_id in set(potential_slot) - set(used_slot):
                unused_slot.append(blank_id)

            for slot_id in unused_slot:
                impair_model = None
                impair_model_width = None
                if (slot_id + 1) % 2:  # condition : if even
                    for blade in self._parent.blades:
                        if int(blade.slot_id) == (slot_id - 1):
                            impair_model = blade.sku

                if impair_model:
                    for model in self.json_file["blades_models"]:
                        if model['name'] == impair_model:
                            impair_model_width = model['width']

                if impair_model_width != "full":
                    for model in self.json_file["blades_models"]:
                        if "type" in model:
                            if model["type"] == "blank":
                                blank_name = model["name"]
                                img = Image.open("catalog/blades/img/" + blank_name + ".png", 'r')
                                for slot in self.json_file["blades_slots"]:
                                    if slot["id"] == int(slot_id):
                                        coord = slot["coord"]
                                coord_offset = self.picture_offset[0] + coord[0], self.picture_offset[1] + coord[1]
                                self.paste_layer(img, coord_offset)

        if "psus_slots" in self.json_file:
            if len(self._parent.power_supplies) < len(self.json_file["psus_slots"]):  # Fill blank for rear PSU Slot
                used_slot = []
                potential_slot = []
                unused_slot = []
                for slot in self._parent.power_supplies:
                    used_slot.append(int(slot.id))
                for slot in self.json_file["psus_slots"]:
                    potential_slot.append(slot["id"])
                for blank_id in set(potential_slot) - set(used_slot):
                    unused_slot.append(blank_id)
                for slot_id in unused_slot:
                    for expansion in self.json_file["psus_models"]:
                        if "type" in expansion:
                            if expansion["type"] == "blank":
                                blank_name = expansion["name"]
                                img = Image.open("catalog/power_supplies/img/" + blank_name + ".png", 'r')
                                for slot in self.json_file["psus_slots"]:
                                    if slot["id"] == int(slot_id):
                                        coord = slot["coord"]
                                coord_offset = self.picture_offset[0] + coord[0], self.picture_offset[1] + coord[1]
                                self.paste_layer(img, coord_offset)


class UcsChassisDrawRear(GenericUcsDrawEquipment):
    def __init__(self, parent=None, color_ports=True):
        GenericUcsDrawEquipment.__init__(self, parent=parent, orientation="rear")
        self.color_ports = color_ports
        if not self.picture:
            return

        self.background = self._create_background(self.canvas_width, self.canvas_height, self.canvas_color)
        self.draw = self._create_draw()

        self.paste_layer(self.picture, self.picture_offset)

        if self._parent.x_fabric_modules:
            # We have X-Fabric Modules in the chassis
            self.xfm_list = self.get_xfm_list()

        if hasattr(self._parent, "fabric_interconnects") and self._parent.fabric_interconnects:
            # We have Fabric Interconnects in the chassis (UCS Mini/X-Direct)
            self.fi_list = self.get_fi_list()
            self.fill_blanks()
            if parent.__class__.__name__ in ["IntersightChassis"]:
                self._file_name = (self._device_target + "_" + parent._parent.name + "_chassis_" +
                                   str(self._parent.id) + "_rear")
            else:
                self._file_name = self._device_target + "_chassis_" + self._parent.id + "_rear"

        elif hasattr(self._parent, "system_io_controllers") and self._parent.system_io_controllers:
            # We have SIOCs in the chassis (S3260)
            self.sioc_list = self.get_sioc_list()
            if "blades_slots_rear" in self.json_file:
                self.blades = self.get_blades()
            if "psus_slots_rear" in self.json_file:
                self.power_supplies = self.get_power_supplies()
            if "disks_slots_rear" in self.json_file:
                self.storage_enclosures = self.get_storage_enclosures()
            self.fill_blanks()
            if parent.__class__.__name__ in ["IntersightChassis"]:
                self._file_name = (self._device_target + "_" + parent._parent.name + "_chassis_" +
                                   str(self._parent.id) + "_rear")
            else:
                self._file_name = self._device_target + "_chassis_" + self._parent.id + "_rear"

        elif hasattr(self._parent, "io_modules") and self._parent.io_modules:
            # We have IOMs in the chassis (5108/9508)
            self.iom_list = self.get_iom_list()
            self.fill_blanks()
            if parent.__class__.__name__ in ["IntersightChassis"]:
                self._file_name = (self._device_target + "_" + parent._parent.name + "_chassis_" +
                                   str(self._parent.id) + "_rear")
            else:
                self._file_name = self._device_target + "_chassis_" + self._parent.id + "_rear"

        else:
            self.logger(level="error", message="No FI, SIOC or IOM in chassis " + self.chassis.id +
                                               ". Skipping chassis...")

        if not self.color_ports:
            if parent.__class__.__name__ in ["IntersightChassis"]:
                self._file_name = (self._device_target + "_" + parent._parent.name + "_chassis_" +
                                   str(self._parent.id) + "_rear_clear")
            else:
                self._file_name = self._device_target + "_chassis_" + self._parent.id + "_rear_clear"

        if self.color_ports:
            self.clear_version = UcsChassisDrawRear(parent=parent, color_ports=False)
        # We drop the picture in order to save on memory
        self.picture = None

    def get_storage_enclosures(self):
        storage_enclosure_list = []
        if hasattr(self._parent, "storage_enclosures"):
            for storage_enclosure in self._parent.storage_enclosures:
                if storage_enclosure.type == "rear-ssd":
                    storage_enclosure_list.append(UcsStorageEnclosureDraw(storage_enclosure, self))
                # storage_enclosure_list = remove_not_completed_in_list(storage_enclosure_list)
        return storage_enclosure_list
    
    def fill_blanks(self):
        # Fills unused FI, IOM or SIOC slots with blanking panels
        if hasattr(self._parent, "fabric_interconnects") and self._parent.fabric_interconnects:
            slots_list = self.json_file["io_modules_slots"]
            models_list = self.json_file["io_modules_models"]
            objects_list = self._parent.fabric_interconnects

        elif hasattr(self._parent, "system_io_controllers") and self._parent.system_io_controllers:
            slots_list = self.json_file["system_io_controllers_slots"]
            models_list = self.json_file["system_io_controllers_models"]
            objects_list = self._parent.system_io_controllers

        elif hasattr(self._parent, "io_modules") and self._parent.io_modules:
            slots_list = self.json_file["io_modules_slots"]
            models_list = self.json_file["io_modules_models"]
            objects_list = self._parent.io_modules

        if len(objects_list) < len(slots_list):
            # Load blank image from JSON file
            for expansion in models_list:
                if "type" in expansion:
                    if expansion["type"] == "blank":
                        blank_name = expansion["name"]
                        blank_img = Image.open("catalog/io_modules/img/" + blank_name + ".png", 'r')

            all_slot_ids = []
            used_slot_ids = []
            unused_slot_ids = []

            for slot in objects_list:
                if slot.id == 'A':  # for FI A in IOM Slot 1
                    used_slot_ids.append(1)
                elif slot.id == 'B':  # for FI B in IOM Slot 2
                    used_slot_ids.append(2)
                else:  # for normal use of a chassis ( != UCS Mini/X-Direct)
                    used_slot_ids.append(int(slot.id))

            for slot in slots_list:
                all_slot_ids.append(slot["id"])

            for blank_id in set(all_slot_ids) - set(used_slot_ids):
                unused_slot_ids.append(blank_id)

            for slot_id in unused_slot_ids:
                # We need to get the coordinates of the slot to place the blank
                for slot in slots_list:
                    if slot["id"] == int(slot_id):
                        coord = slot["coord"]
                # We paste the blanking panel
                coord_offset = self.picture_offset[0] + coord[0], self.picture_offset[1] + coord[1]
                self.paste_layer(blank_img, coord_offset)

        # Fills unused XFM slots with blanking panels
        if "x_fabric_modules_slots" in self.json_file:
            if len(self._parent.x_fabric_modules) < len(self.json_file["x_fabric_modules_slots"]):
                # Load blank image from JSON file
                for expansion in self.json_file["x_fabric_modules_models"]:
                    if "type" in expansion:
                        if expansion["type"] == "blank":
                            blank_name = expansion["name"]
                            blank_img = Image.open("catalog/x_fabric_modules/img/" + blank_name + ".png", 'r')

                all_slot_ids = []
                used_slot_ids = []
                unused_slot_ids = []

                for slot in self._parent.x_fabric_modules:
                    used_slot_ids.append(int(slot.id))

                for slot in self.json_file["x_fabric_modules_slots"]:
                    all_slot_ids.append(slot["id"])

                for blank_id in set(all_slot_ids) - set(used_slot_ids):
                    unused_slot_ids.append(blank_id)

                for slot_id in unused_slot_ids:
                    # We need to get the coordinates of the slot to place the blank
                    for slot in self.json_file["x_fabric_modules_slots"]:
                        if slot["id"] == int(slot_id):
                            coord = slot["coord"]
                    # We paste the blanking panel
                    coord_offset = self.picture_offset[0] + coord[0], self.picture_offset[1] + coord[1]
                    self.paste_layer(blank_img, coord_offset)

        # Fills unused PSU slots with blanking panels
        if "psus_slots_rear" in self.json_file:
            if len(self._parent.power_supplies) < len(self.json_file["psus_slots_rear"]):
                # Load blank image from JSON file
                for expansion in self.json_file["psus_models"]:
                    if "type" in expansion:
                        if expansion["type"] == "blank":
                            blank_name = expansion["name"]
                            blank_img = Image.open("catalog/power_supplies/img/" + blank_name + ".png", 'r')

                all_slot_ids = []
                used_slot_ids = []
                unused_slot_ids = []

                for slot in self._parent.power_supplies:
                    used_slot_ids.append(int(slot.id))

                for slot in self.json_file["psus_slots_rear"]:
                    all_slot_ids.append(slot["id"])

                for blank_id in set(all_slot_ids) - set(used_slot_ids):
                    unused_slot_ids.append(blank_id)

                for slot_id in unused_slot_ids:
                    # We need to get the coordinates of the slot to place the blank
                    for slot in self.json_file["psus_slots_rear"]:
                        if slot["id"] == int(slot_id):
                            coord = slot["coord"]
                    # We paste the blanking panel
                    coord_offset = self.picture_offset[0] + coord[0], self.picture_offset[1] + coord[1]
                    self.paste_layer(blank_img, coord_offset)

        # Fills unused server node slots with blanking panels
        if "blades_slots_rear" in self.json_file:
            if len(self._parent.blades) < len(self.json_file["blades_slots_rear"]):
                # Load blank image from JSON file
                for expansion in self.json_file["blades_models"]:
                    if "type" in expansion:
                        if expansion["type"] == "blank":
                            blank_name = expansion["name"]
                            blank_img = Image.open("catalog/blades/img/" + blank_name + ".png", 'r')

                all_slot_ids = []
                used_slot_ids = []
                unused_slot_ids = []

                for slot in self._parent.blades:
                    used_slot_ids.append(int(slot.slot_id))

                for slot in self.json_file["blades_slots_rear"]:
                    all_slot_ids.append(slot["id"])

                for blank_id in set(all_slot_ids) - set(used_slot_ids):
                    unused_slot_ids.append(blank_id)

                for slot_id in unused_slot_ids:
                    # We need to get the coordinates of the slot to place the blank
                    for slot in self.json_file["blades_slots_rear"]:
                        if slot["id"] == int(slot_id):
                            coord = slot["coord"]
                    # We paste the blanking panel
                    coord_offset = self.picture_offset[0] + coord[0], self.picture_offset[1] + coord[1]
                    self.paste_layer(blank_img, coord_offset)

        # Fill blank for SSD slot in UCS-S3260 chassis
        if self._parent.sku == "UCSC-C3X60" or self._parent.sku == "UCSS-S3260":
            # if len(self.blades) != 2:
            disk_list = []
            for enclosure in self.storage_enclosures:
                for disk in enclosure.disks:
                    disk_list.append(disk)
                    # disk_list = remove_not_completed_in_list(disk_list)

            used_slot = []
            potential_slot = []
            unused_slot = []

            for disk in disk_list:
                used_slot.append(int(disk.id))
            for disk in self.json_file['disks_slots_rear']:
                potential_slot.append(disk["id"])
            for blank_id in set(potential_slot) - set(used_slot):
                unused_slot.append(blank_id)
            for slot_id in unused_slot:
                blank_name = None
                orientation = "horizontal"
                disk_format = None
                for disk_slot in self.json_file['disks_slots_rear']:
                    if disk_slot['id'] == slot_id:
                        orientation = disk_slot['orientation']
                        disk_format = disk_slot['format']
                for model in self.json_file["disks_models"]:
                    if "type" in model and not blank_name:
                        if model["type"] == "blank" and model["format"] == disk_format:
                            blank_name = model["name"]
                            img = Image.open("catalog/drives/img/" + blank_name + ".png", 'r')
                            if orientation == "vertical":
                                img = GenericUcsDrawEquipment.rotate_object(picture=img)
                if blank_name:
                    for slot in self.json_file['disks_slots_rear']:
                        if slot["id"] == int(slot_id):
                            coord = slot["coord"]
                    coord_offset = self.picture_offset[0] + coord[0], \
                                   self.picture_offset[1] + coord[1]

                    self.paste_layer(img, coord_offset)

    def get_blades(self):
        blade_list = []
        for blade in self._parent.blades:
            blade_list.append(UcsBladeDrawFront(blade, self))
        # blade_list = remove_not_supported_in_list(blade_list)
        # blade_list = remove_not_completed_in_list(blade_list)
        # We only keep the blades that have been fully created -> picture
        blade_list = [blade for blade in blade_list if blade.picture_size]
        return blade_list

    def get_fi_list(self):
        from draw.ucs.fabric import UcsFiDrawRear

        fi_list = []
        if hasattr(self._parent, "fabric_interconnects"):
            for fi in self._parent.fabric_interconnects:
                fi_list.append(UcsFiDrawRear(parent=fi, parent_draw=self, color_ports=self.color_ports))
        # fi_list = remove_not_supported_in_list(fi_list)
        # fi_list = remove_not_completed_in_list(fi_list)
        # We only keep the FI that have been fully created -> picture
        fi_list = [fi for fi in fi_list if fi.picture_size]
        return fi_list

    def get_iom_list(self):
        iom_list = []
        for iom in self._parent.io_modules:
            iom_list.append(UcsIomDraw(iom, self))
        # iom_list = remove_not_supported_in_list(iom_list)
        # iom_list = remove_not_completed_in_list(iom_list)
        # We only keep the iom that have been fully created -> picture
        iom_list = [iom for iom in iom_list if iom.picture_size]
        return iom_list

    def get_power_supplies(self):
        psu_list = []
        for psu in self._parent.power_supplies:
            if psu.id != '0':  # UCS PE sometimes adds an invalid PSU with ID 0
                psu_list.append(UcsPsuDraw(psu, self))
        # psu_list = remove_not_supported_in_list(psu_list)
        # psu_list = remove_not_completed_in_list(psu_list)
        # We only keep the PSU that have been fully created -> picture
        psu_list = [psu for psu in psu_list if psu.picture_size]
        return psu_list

    def get_sioc_list(self):
        sioc_list = []
        if hasattr(self._parent, "system_io_controllers"):
            for sioc in self._parent.system_io_controllers:
                sioc_list.append(UcsSiocDraw(sioc, self, color_ports=self.color_ports))
        # sioc_list = remove_not_supported_in_list(sioc_list)
        # sioc_list = remove_not_completed_in_list(sioc_list)
        # We only keep the sioc that have been fully created -> picture
        sioc_list = [sioc for sioc in sioc_list if sioc.picture_size]
        return sioc_list

    def get_xfm_list(self):
        xfm_list = []
        for xfm in self._parent.x_fabric_modules:
            xfm_list.append(UcsXfmDraw(xfm, self))
        # xfm_list = remove_not_supported_in_list(xfm_list)
        # xfm_list = remove_not_completed_in_list(xfm_list)
        # We only keep the xfm that have been fully created -> picture
        xfm_list = [xfm for xfm in xfm_list if xfm.picture_size]
        return xfm_list


class UcsIomDraw(GenericUcsDrawEquipment):
    def __init__(self, parent=None, parent_draw=None):
        self.parent_draw = parent_draw
        GenericUcsDrawEquipment.__init__(self, parent=parent)
        if not self.picture:
            return

        self.ports = []
        self.parent_draw.paste_layer(self.picture, self.picture_offset)

        if self.parent_draw.color_ports:
            self.draw_ports()

        # We drop the picture in order to save on memory
        self.picture = None

        # TODO : Should not work on UCS-S3260-PCISIOC

    def _get_picture_offset(self):
        for slot in self.parent_draw.json_file["io_modules_slots"]:
            if slot["id"] == int(self._parent.id):
                coord = slot["coord"]
        return self.parent_draw.picture_offset[0] + coord[0], self.parent_draw.picture_offset[1] + coord[1]

    def draw_ports(self):
        for port in self._parent.ports:
            if port.role != "unknown":
                port_color = None
                port_id = str(port.port_id)
                port_info = self.json_file["rear_ports"]["x/" + port_id]

                if (port.role == "network" and port.type == "lan") or port.role in ["Uplink", "Uplink PC Member"]:
                    port_color = self.COLOR_LAN_UPLINK_PORTS
                if (port.role == "network" and port.type == "san") or \
                        port.role in ["FcUplink", "FcUplink PC Member"]:
                    port_color = self.COLOR_SAN_UPLINK_PORTS
                if port.role in ["storage", "FcStorage"]:
                    port_color = self.COLOR_SAN_STORAGE_PORTS
                if port.role in ["fcoe-uplink", "FcoeUplink"]:
                    port_color = self.COLOR_FCOE_UPLINK_PORTS
                if port.role == "fcoe-storage":
                    port_color = self.COLOR_FCOE_STORAGE_PORTS
                if port.role in ["nas-storage", "Appliance"]:
                    port_color = self.COLOR_APPLIANCE_STORAGE_PORTS
                if port.role in ["server", "Server"]:
                    port_color = self.COLOR_SERVER_PORTS
                if port.role == "fcoe-nas-storage":
                    port_color = self.COLOR_UNIFIED_STORAGE_PORTS
                if port.role == "network-fcoe-uplink":
                    port_color = self.COLOR_UNIFIED_UPLINK_PORTS
                if port.role == "monitor" and port.type == "san":
                    port_color = self.COLOR_SAN_MONITOR_PORTS
                elif port.role == "monitor":
                    port_color = self.COLOR_LAN_MONITOR_PORTS

                port_size_x = port_info['port_size'][0]
                port_size_y = port_info['port_size'][1]
                coord_x = port_info['port_coord'][0]
                coord_y = port_info['port_coord'][1]

                peer = None
                if port.peer:
                    peer = port.peer
                self.ports.append(
                    UcsPortDraw(port_id, port_color, (port_size_x, port_size_y),
                                (self.picture_offset[0] + coord_x, self.picture_offset[1] + coord_y), self, port,
                                peer=peer))
                self.draw_rectangle(self.parent_draw.draw,
                                    ((self.picture_offset[0] + coord_x, self.picture_offset[1] + coord_y),
                                     (self.picture_offset[0] + coord_x + port_size_x,
                                      self.picture_offset[1] + coord_y + port_size_y)), color=port_color, width=10)


class UcsSiocDraw(GenericUcsDrawEquipment):
    def __init__(self, parent=None, parent_draw=None, color_ports=None):
        self.parent_draw = parent_draw
        self.color_ports = color_ports
        GenericUcsDrawEquipment.__init__(self, parent=parent)
        if not self.picture:
            return

        # We do this to be able to support adding a modular adaptor for UCS-S3260-PCISIOC
        #self.background = self._create_background(self.canvas_width, self.canvas_height, self.canvas_color)
        #self.draw = self._create_draw()
        self.draw = self.parent_draw.draw
        self.background = self.parent_draw.background

        self.adaptor_list = None
        self.ports = []
        self.parent_draw.paste_layer(self.picture, self.picture_offset)

        if self._parent.sku in ["UCS-S3260-PCISIOC"]:
            self.adaptor_list = self.get_adaptor_list()

        if hasattr(self.parent_draw, "color_ports"):
            if self.parent_draw.color_ports:
                self.draw_ports()

        # We drop the picture in order to save on memory
        self.picture = None

    def _get_picture_offset(self):
        for slot in self.parent_draw.json_file["system_io_controllers_slots"]:
            if slot["id"] == int(self._parent.id):
                coord = slot["coord"]
        return self.parent_draw.picture_offset[0] + coord[0], self.parent_draw.picture_offset[1] + coord[1]
    
    def draw_ports(self):
        # Fix for when S3260 chassis is properly discovered and has a PCI SIOC but there is no server inserted.
        # In that case there won't be any info in the inventory about the VIC model
        if self._parent.sku in ["UCS-S3260-PCISIOC"]:
            if not self.adaptor_list:
                return None

        for port in self._parent.ports:
            if port.role != "unknown":
                port_color = None
                port_id = port.port_id
                rectangle_width = self.WIDTH_PORT_RECTANGLE_DEFAULT

                if self._parent.sku in ["UCS-S3260-PCISIOC"]:
                    if self.adaptor_list[0]._parent.sku in ["UCSC-PCIE-C100-04"]:
                        if port_id == "3": #TODO Workaround until fixed on inventory, not the right port id in the ports of the SIOC
                            port_id = "2"

                    if self.adaptor_list[0]._parent.sku in ["UCSC-PCIE-C25Q-04"]:
                        port.is_breakout = False #TODO Workaround until fixed on inventory, appears as breakout in the ports of the SIOC even when not breakout

                    else:  ## TODO add more PCIe exception
                        continue

                    port_info = self.adaptor_list[0].json_file["rear_ports_half"]["x/" + port_id]
                    port_info["port_coord"] = port_info["port_coord"][0] + self.json_file["pcie_slots"][0]["coord"][0], \
                                              port_info["port_coord"][1] + self.json_file["pcie_slots"][0]["coord"][1]

                elif port.is_breakout:  # for aggr ports
                    if port_id in ["1", "2", "3", "4"]:
                        port_info = dict(self.json_file["rear_ports"]["1"])
                    if port_id in ["5", "6", "7", "8"]:
                        port_info = dict(self.json_file["rear_ports"]["5"])

                    rectangle_width = self.WIDTH_PORT_RECTANGLE_BREAKOUT
                    aggr_width = round(port_info['port_size'][0] / 4)
                    port_info['port_size'] = aggr_width - 2, port_info['port_size'][1]
                    port_info['port_coord'] = port_info['port_coord'][0] + (int(port_id)-1) % 4 * aggr_width, \
                                              port_info['port_coord'][1]
                else:
                    port_info = self.json_file["rear_ports"][port_id]

                if (port.role == "network" and port.type == "lan") or port.role in ["Uplink", "Uplink PC Member"]:
                    port_color = self.COLOR_LAN_UPLINK_PORTS
                if (port.role == "network" and port.type == "san") or \
                        port.role in ["FcUplink", "FcUplink PC Member"]:
                    port_color = self.COLOR_SAN_UPLINK_PORTS
                if port.role in ["storage", "FcStorage"]:
                    port_color = self.COLOR_SAN_STORAGE_PORTS
                if port.role in ["fcoe-uplink", "FcoeUplink"]:
                    port_color = self.COLOR_FCOE_UPLINK_PORTS
                if port.role == "fcoe-storage":
                    port_color = self.COLOR_FCOE_STORAGE_PORTS
                if port.role in ["nas-storage", "Appliance"]:
                    port_color = self.COLOR_APPLIANCE_STORAGE_PORTS
                if port.role in ["server", "Server"]:
                    port_color = self.COLOR_SERVER_PORTS
                if port.role == "fcoe-nas-storage":
                    port_color = self.COLOR_UNIFIED_STORAGE_PORTS
                if port.role == "network-fcoe-uplink":
                    port_color = self.COLOR_UNIFIED_UPLINK_PORTS
                if port.role == "monitor" and port.type == "san":
                    port_color = self.COLOR_SAN_MONITOR_PORTS
                elif port.role == "monitor":
                    port_color = self.COLOR_LAN_MONITOR_PORTS

                port_size_x = port_info['port_size'][0]
                port_size_y = port_info['port_size'][1]
                coord_x = port_info['port_coord'][0]
                coord_y = port_info['port_coord'][1]

                peer = None
                if port.peer:
                    peer = port.peer
                self.ports.append(
                    UcsPortDraw(port_id, port_color, (port_size_x, port_size_y),
                                (self.picture_offset[0] + coord_x, self.picture_offset[1] + coord_y), self, port,
                                peer=peer))
                self.draw_rectangle(self.parent_draw.draw,
                                    ((self.picture_offset[0] + coord_x, self.picture_offset[1] + coord_y),
                                     (self.picture_offset[0] + coord_x + port_size_x,
                                      self.picture_offset[1] + coord_y + port_size_y)), color=port_color,
                                    width=rectangle_width)

    def get_adaptor_list(self):
        adaptor_list = []
        if hasattr(self._parent, "_parent"):
            if hasattr(self._parent._parent, "server_nodes"):
                for server_node in self._parent._parent.server_nodes:
                    for adaptor in server_node.adaptors:
                        if hasattr(adaptor, "id"):
                            if adaptor.id is not None:
                                if "SIOC" in adaptor.id:
                                    if adaptor.id[-1] == self._parent.id:
                                        adaptor_list.append(UcsAdaptorDraw(parent=adaptor, parent_draw=self))
            elif hasattr(self._parent._parent, "blades"):
                for blade in self._parent._parent.blades:
                    for adaptor in blade.adaptors:
                        # For IMC SIOCs
                        if hasattr(adaptor, "id"):
                            if adaptor.id is not None:
                                if "SIOC" in adaptor.id:
                                    # Adaptor ID appears as "SIOCx" ex. SIOC1
                                    if adaptor.id[-1] == self._parent.id:
                                        adaptor_list.append(UcsAdaptorDraw(parent=adaptor, parent_draw=self))
                        # For UCSM SIOCs
                        if hasattr(adaptor, "pci_slot"):
                            if adaptor.pci_slot is not None:
                                if "SIOC" in adaptor.pci_slot:
                                    # PCI Slot appears as "SIOCx" ex. SIOC1
                                    if adaptor.pci_slot[-1] == self._parent.id:
                                        adaptor_list.append(UcsAdaptorDraw(parent=adaptor, parent_draw=self))

        adaptor_list = [adaptor for adaptor in adaptor_list if adaptor.picture_size]
        return [e for e in adaptor_list if hasattr(e, "_parent")]


class UcsXfmDraw(GenericUcsDrawEquipment):
    def __init__(self, parent=None, parent_draw=None):
        self.parent_draw = parent_draw
        GenericUcsDrawEquipment.__init__(self, parent=parent)
        if not self.picture:
            return

        self.ports = []
        self.parent_draw.paste_layer(self.picture, self.picture_offset)

        # We drop the picture in order to save on memory
        self.picture = None

    def _get_picture_offset(self):
        for slot in self.parent_draw.json_file["x_fabric_modules_slots"]:
            if slot["id"] == int(self._parent.id):
                coord = slot["coord"]
        return self.parent_draw.picture_offset[0] + coord[0], self.parent_draw.picture_offset[1] + coord[1]


class UcsChassisDrawInfra(UcsSystemDrawInfraEquipment):
    def __init__(self, chassis, fi_list, fex_list=None, parent=None):

        UcsSystemDrawInfraEquipment.__init__(self, parent=parent)
        # Create a copy of the DrawChassis
        if 'Rear' in chassis.__class__.__name__:
            self.chassis = UcsChassisDrawRear(parent=chassis._parent)
        else:
            self.chassis = UcsChassisDrawFront(parent=chassis._parent)
        self.fi_a = self._get_fi(fi_list, "A")
        self.fi_b = self._get_fi(fi_list, "B")

        self.fex_presence = None
        if fex_list:
            self.fex_presence = self._get_fex_infra_presence()
            if self.fex_presence:
                self.fex_list = self._get_fex(fex_list)
                self.fex_a = self.fex_list[0]
                self.fex_b = self.fex_list[1]
                # Should implement self.valid_fex and check if FEX are usable as in the UcsSystemDraw InfraRack object
                # Even if chassis can't be connected through FEX as of now

        # Canvas settings
        if self.fex_presence:
            # self.canvas_width = self.fi_a.picture_size[0] * 2 + self.chassis.picture_size[0] + self.fex_a.picture_size[0] * 2 + 200  # arbitrary
            self.canvas_width = self.chassis.picture_size[0] + self.fex_a.picture_size[0] * 2 + 100  # arbitrary
            self.canvas_height = self.fi_a.picture_size[1] + self.chassis.picture_size[1] + \
                                 self.fex_a.picture_size[1] + 400  # arbitrary
        else:
            self.canvas_width = self.fi_a.picture_size[0] * 2 + self.chassis.picture_size[0] + 100  # arbitrary
            self.canvas_height = self.fi_a.picture_size[1] + self.chassis.picture_size[1] + 100  # arbitrary

        self.chassis_offset = self._get_picture_offset("chassis")
        self.fi_a_offset = self._get_picture_offset("fi_a")
        if self.fi_b:
            self.fi_b_offset = self._get_picture_offset("fi_b")
        if self.fex_presence:
            self.fex_a_offset = self._get_picture_offset("fex_a")
            self.fex_b_offset = self._get_picture_offset("fex_b")

        self.background = self._create_background(self.canvas_width, self.canvas_height, self.canvas_color)
        self.draw = self._create_draw()

        # Paste layers
        # As we drop the picture before, we need to recreate it and drop it again after pasting the layer
        self.chassis._get_picture()
        self.paste_layer(self.chassis.picture, self.chassis_offset)
        self.chassis.picture = None

        self.fi_a._get_picture()
        if self.fi_a._parent.sku == "UCS-FI-M-6324":
            # We only need to rotate the picture as the other parameters are already rotated (json_file, picture_size)
            self.fi_a.picture = self.fi_a.rotate_object(picture=self.fi_a.picture)
        self.paste_layer(self.fi_a.picture, self.fi_a_offset)
        self.fi_a.picture = None

        if self.fi_b:
            self.fi_b._get_picture()
            if self.fi_b._parent.sku == "UCS-FI-M-6324":
                self.fi_b.picture = self.fi_b.rotate_object(picture=self.fi_b.picture)
            self.paste_layer(self.fi_b.picture, self.fi_b_offset)
            self.fi_b.picture = None
        if self.fex_presence:
            self.fex_a._get_picture()
            self.paste_layer(self.fex_a.picture, self.fex_a_offset)
            self.fex_a.picture = None
            self.fex_b._get_picture()
            self.paste_layer(self.fex_b.picture, self.fex_b_offset)
            self.fex_b.picture = None

        # Draw ports and expansion
        self.fi_a.draw = self.draw
        self.fi_a.background = self.background
        self.fi_a.picture_offset = self.fi_a_offset
        self.fi_a.ports = []
        self.fi_a.draw_ports(True)
        self.fi_a.gem_list = self.fi_a.get_expansion_modules()
        self.fi_a.fill_blanks()

        if self.fi_b:  # if FI B is present
            self.fi_b.draw = self.draw
            self.fi_b.background = self.background
            self.fi_b.picture_offset = self.fi_b_offset
            self.fi_b.ports = []
            self.fi_b.draw_ports(True)
            self.fi_b.gem_list = self.fi_b.get_expansion_modules()
            self.fi_b.fill_blanks()

        self.chassis.draw = self.draw
        self.chassis.background = self.background
        self.chassis.picture_offset = self.chassis_offset
        self.chassis.iom_list = self.chassis.get_iom_list()
        self.chassis.sioc_list = self.chassis.get_sioc_list()
        self.chassis.storage_enclosures = self.chassis.get_storage_enclosures()
        self.chassis.fi_list = self.chassis.get_fi_list()
        # if chassis.fi_list:
        #     self.chassis.fi_list = self.chassis.draw_fi()
        #     self.chassis.draw_fi_ports()
        self.chassis.xfm_list = self.chassis.get_xfm_list()

        if self.fex_presence:
            self.fex_a.draw = self.draw
            self.fex_a.background = self.background
            self.fex_a.picture_offset = self.fex_a_offset
            self.fex_a.fabric_ports = []
            self.fex_a.host_ports = []
            self.fex_a.draw_ports()

            self.fex_b.draw = self.draw
            self.fex_b.background = self.background
            self.fex_b.picture_offset = self.fex_b_offset
            self.fex_b.fabric_ports = []
            self.fex_b.host_ports = []
            self.fex_b.draw_ports()

        if "blades_slots_rear" in self.chassis.json_file:
            self.chassis.blade_list = self.chassis.get_blades()
        if "psus_slots_rear" in self.chassis.json_file:
            self.chassis.psu_list = self.chassis.get_power_supplies()
        self.chassis.fill_blanks()

        self.wires = []
        self.set_wire()

        # For the legend of ports
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
        self.draw_chassis_info()

        # if there is no wire at all, there is no need to save the picture
        if self.wires:
            if parent.__class__.__name__ in ["IntersightFi"]:
                self._file_name = (self._device_target + "_" + parent._parent.name + "_infra_chassis_" +
                                   str(self.chassis._parent.id))
            else:
                self._file_name = self._device_target + "_infra_chassis_" + str(self.chassis._parent.id)
        else:
            self.logger(level="warning", message="Infra of chassis #" + str(self.chassis._parent.id) +
                                                 " not saved because no connection between the FI and the chassis")

        # We drop the picture in order to save on memory
        self.picture = None

    def _get_fex_infra_presence(self):
        # Used to know if a FEX need to be used for this infra
        if hasattr(self.chassis, 'iom_list'):  # if the chassis has IOM
            io_list = self.chassis.iom_list
        elif hasattr(self.chassis, 'sioc_list'):  # if the chassis has SIOC
            io_list = self.chassis.sioc_list

        for io in io_list:
            for port in io.ports:
                # Search for peer information
                if hasattr(port, 'peer'):
                    if "fex" in port.peer:
                        return True
        return False

    def _get_fex(self, list):
        fex_id_list = []
        for mgmt_if in self.chassis._parent.mgmt_if_list:
            fex_id_list.append(mgmt_if.peer["fex"])
        fex_list = []
        for id in fex_id_list:
            for fex in list:
                if fex._parent.id == id:
                    fex_list.append(copy.copy(fex))
        if len(fex_list) > 2:
            self.logger(level="error", message="more than two FEX for one equipment")
        fex_list.sort(key=lambda fex: fex._parent.switch_id)
        return fex_list

    def _get_fi(self, fi_list, id):
        fabric = None
        for fi in fi_list:
            if fi._parent.id == id:
                fabric = fi
            if fi._parent.id == id:
                fabric = fi
        return copy.copy(fabric)

    def _get_picture_offset(self, type):
        if type == "chassis":
            return round(self.canvas_width / 2 - self.chassis.picture_size[0] / 2), \
                   self.canvas_height - self.chassis.picture_size[1]

        if type == "fi_a":
            return 0, 0

        if type == "fi_b":
            return self.canvas_width - self.fi_b.picture_size[0], 0

        if type == "fex_a":
            # return self.fi_a.picture_size[0] + 50, self.fi_a.picture_size[1] + 100
            return 0, self.fi_a.picture_size[1] + 400

        if type == "fex_b":
            # return self.canvas_width - self.fex_b.picture_size[0] - self.fi_a.picture_size[0] - 50, self.fi_a.picture_size[1] + 100
            return self.canvas_width - self.fex_b.picture_size[0], self.fi_a.picture_size[1] + 400

    def draw_chassis_info(self):
        fill_color = "black"
        font_size = 60
        font_title = ImageFont.truetype('arial.ttf', font_size)

        if self.chassis._parent.user_label:
            msg = "Chassis #" + str(self.chassis._parent.id) + " - " + self.chassis._parent.user_label
        else:
            msg = "Chassis #" + str(self.chassis._parent.id)
        w = self.draw.textlength(msg, font=font_title)
        # 16 px space between text and equipment
        self.draw.text((round(self.canvas_width/2 - w / 2), self.chassis_offset[1] - (font_size + 16)), msg,
                       fill=fill_color, font=font_title)

    def set_wire(self):
        # Bottom to top
        io_list = []
        if self.chassis.iom_list:  # if the chassis has IOM
            io_list = self.chassis.iom_list
        elif self.chassis.sioc_list:  # if the chassis has SIOC
            io_list = self.chassis.sioc_list

        for io in io_list:
            for io_port in io.ports:
                # Search for peer information
                if hasattr(io_port, 'peer'):
                    peer = io_port.peer
                    peer_fex = None
                    peer_fi = None
                    if "fex" in peer:
                        peer_fex = peer["fex"]
                        if self.fex_a._parent.id is peer_fex:
                            fex = self.fex_a
                            fabric = "a"
                        elif self.fex_b._parent.id is peer_fex:
                            fex = self.fex_b
                            fabric = "b"
                    elif "switch" in peer:
                        peer_fi = peer["switch"]
                        if peer_fi == "A":  # if FI A
                            fi = self.fi_a
                            fabric = "a"
                        if peer_fi == "B":  # if FI B
                            fi = self.fi_b
                            fabric = "b"
                    peer_slot_id = peer["slot"]
                    peer_port_id = peer["port"]
                    if "aggr_port" in peer:
                        peer_aggr_id = peer["aggr_port"]
                    else:
                        peer_aggr_id = None

                    wire_width = self.WIDTH_WIRE  # Set the default wire width

                    point_breakout = None

                    io_detail = io._parent
                    # if self.chassis.iom_list:
                    #     io_detail = io._parent
                    # elif self.chassis.sioc_list:
                    #     io_detail = io._parent

                    # if io_detail.sku == "UCSC-C3260-SIOC":  # Exception for UCSC-C3260-SIOC
                    #     wire_width = 7
                    #     port_position = int(io_port.id)
                    #     if port_position > 4:  # for port between 5 and 8
                    #         port_position = port_position - 4
                    #     point_chassis = io_port.coord[0] + round(io_port.size[0] / 2), io_port.coord[1] + round(
                    #         io_port.size[1] / 4) * port_position
                    # else:  # For most chassis
                    #     point_chassis = io_port.coord[0] + round(io_port.size[0] / 2), io_port.coord[1] + round(io_port.size[1] / 2)
                    if not io_port._parent.is_breakout:
                        point_chassis = io_port.coord[0] + round(io_port.size[0] / 2),\
                                        io_port.coord[1] + round(io_port.size[1] / 2)
                    else:
                        wire_width = self.WIDTH_WIRE_BREAKOUT
                        point_breakout = io_port.coord[0] + round(io_port.size[0] / 2),\
                                         io_port.coord[1] + round(io_port.size[1] / 2)

                        if fabric == "a":
                            if int(io_detail.id) == 1:
                                point_chassis = io_port.coord[0] - (int(io_port.id)-1) % 4 * io_port.size[0] \
                                                + io_port.size[0]*2, io_port.coord[1] + io_port.size[1] + \
                                                self.WIRE_DISTANCE_SHORT
                            if int(io_detail.id) == 2:
                                point_chassis = io_port.coord[0] - (int(io_port.id)-1) % 4 * io_port.size[0] \
                                                + io_port.size[0]*2, io_port.coord[1] + io_port.size[1] + \
                                                self.WIRE_DISTANCE_LONG
                        elif fabric == "b":
                            if int(io_detail.id) == 1:
                                point_chassis = io_port.coord[0] - (int(io_port.id)-1) % 4 * io_port.size[0] \
                                                + io_port.size[0]*2, io_port.coord[1] - self.WIRE_DISTANCE_LONG
                            if int(io_detail.id) == 2:
                                point_chassis = io_port.coord[0] - (int(io_port.id)-1) % 4 * io_port.size[0] \
                                                + io_port.size[0]*2, io_port.coord[1] - self.WIRE_DISTANCE_SHORT

                    if peer_fi:
                        # Find and calculate coordinates of the peer point on the FI
                        point_fi = None
                        if peer_slot_id == 1:
                            for port in fi.ports:
                                if peer_aggr_id:
                                    if int(port.id) == peer_port_id:
                                        if port.aggr_id:
                                            wire_width = 5
                                            if int(port.aggr_id) == peer_aggr_id:
                                                # Even / odd
                                                point_fi = port.coord[0] + round(port.size[0] / 3) + (
                                                    peer_aggr_id + 1) % 2 * round(
                                                    port.size[0] / 3) - ((peer_aggr_id + 1) % 2), port.coord[1] + round(
                                                    port.size[1] / 2)
                                                peer_port = port
                                else:
                                    if (int(port.id) == peer_port_id) and port.aggr_id is None:
                                        # Even / odd
                                        point_fi = port.coord[0] + round(port.size[0] / 3) + (
                                                    peer_port_id + 1) % 2 * round(port.size[0] / 3), port.coord[
                                                       1] + round(port.size[1] / 2)
                                        peer_port = port

                        else:
                            for gem in fi.gem_list:
                                if int(gem._parent.id) == peer_slot_id:
                                    for port in gem.ports:
                                        if peer_aggr_id:
                                            if int(port.id) == peer_port_id:
                                                if port.aggr_id:
                                                    wire_width = 5
                                                    if int(port.aggr_id) == peer_aggr_id:
                                                        # Even / odd
                                                        point_fi = port.coord[0] + round(port.size[0] / 3) + (
                                                                    peer_aggr_id + 1) % 2 * round(port.size[0] / 3) - (
                                                                               (peer_aggr_id + 1) % 2), port.coord[
                                                                       1] + round(port.size[1] / 2)
                                                        peer_port = port
                                        else:
                                            if (int(port.id) == peer_port_id) and port.aggr_id is None:
                                                # Even / odd
                                                point_fi = port.coord[0] + round(port.size[0] / 3) + (
                                                            peer_port_id + 1) % 2 * round(port.size[0] / 3), port.coord[
                                                               1] + round(port.size[1] / 2)
                                                peer_port = port

                        self.logger(level="debug", message="Setting wire for chassis " + str(self.chassis._parent.id) +
                                                           ", width : " + str(wire_width))
                        if point_fi:
                            # if io_detail.sku == "UCSC-C3260-SIOC":  # Exception for S3260
                            #     if int(io_detail.id) == 1:  # if SIOC's id is 1 then the wires will go up
                            #         step = - 40
                            #     if int(io_detail.id) == 2:  # if SIOC's id is 2 then the wires will go down
                            #         step = 40
                            #     target = point_chassis[0], point_chassis[1] + step + round(
                            #         step / 1) * port_position  # port_position is initialised before
                            if point_breakout:
                                self.wires.append(
                                    UcsSystemDrawWire(self, (point_chassis, point_breakout), wire_width,
                                                      easyucs_fabric_port=peer_port._parent, line_type="straight"))
                                self.wires.append(UcsSystemDrawWire(self, (point_fi, point_chassis), wire_width,
                                                                    easyucs_fabric_port=peer_port._parent))
                                # self.wires = remove_not_completed_in_list(self.wires)

                                fill_color = "black"
                                font_size = 40
                                font_title = ImageFont.truetype('arial.ttf', font_size)
                                self.draw.text((point_fi[0] - 30, point_chassis[1] - 45), io_port.id, fill=fill_color,
                                               font=font_title)

                            else:
                                # draw_wire(self.draw, point_fi, point_chassis, wire_color, wire_width)
                                # self.wires.append(EasyUcsDrawWire(self.draw, (point_fi, point_chassis), wire_width,
                                #                                   easyucs_fi_port=port.port))

                                # Check if a card of a quad port on a SIOC
                                inline_sioc_ports = False
                                if len(io.ports) > 2:
                                    y_coord = io.ports[0].coord[1]
                                    inline_sioc_ports = True
                                    for port in io.ports:
                                        if port.coord[1] == y_coord and inline_sioc_ports == True:
                                            inline_sioc_ports = True
                                        else:
                                            inline_sioc_ports = False

                                # When a card is a quad port we had to create 8 different "step"
                                if "-C25Q-04" in io_port._parent._parent.sku or inline_sioc_ports:
                                    wire_width = self.WIDTH_WIRE_BREAKOUT
                                    if fabric == "a":
                                        if int(io._parent.id) % 2:
                                            if int(io_port.id) % 2:
                                                step = self.WIRE_DISTANCE_SHORT + round(io_port.size[1] / 2)
                                            else:
                                                step = self.WIRE_DISTANCE_LONG + round(io_port.size[1] / 4)
                                        else:
                                            if int(io_port.id) % 2:
                                                step = self.WIRE_DISTANCE_SHORT + round(io_port.size[1] / 4)
                                            else:
                                                step = self.WIRE_DISTANCE_LONG + round(io_port.size[1] / 2)
                                    if fabric == "b":
                                        if int(io._parent.id) % 2:
                                            if int(io_port.id) % 2:
                                                step = - self.WIRE_DISTANCE_LONG - round(io_port.size[1] / 4)
                                            else:
                                                step = - self.WIRE_DISTANCE_SHORT - round(io_port.size[1] / 2)
                                        else:
                                            if int(io_port.id) % 2:
                                                step = - self.WIRE_DISTANCE_LONG - round(io_port.size[1] / 2)
                                            else:
                                                step = - self.WIRE_DISTANCE_SHORT - round(io_port.size[1] / 4)
                                # for all the non quad port cards
                                else:
                                    if fabric == "a":
                                        if int(io_detail.id) % 2:
                                            # if (int(adapt_port.port.port_id) % 2) :
                                            step = self.WIRE_DISTANCE_SHORT + round(io_port.size[1] / 2)
                                        else:
                                            step = self.WIRE_DISTANCE_LONG + round(io_port.size[1] / 2)
                                    if fabric == "b":
                                        if int(io_detail.id) % 2:
                                            step = - self.WIRE_DISTANCE_LONG - round(io_port.size[1] / 2)
                                        else:
                                            step = - self.WIRE_DISTANCE_SHORT - round(io_port.size[1] / 2)
                                target = point_chassis[0], point_chassis[1] + step
                                self.wires.append(UcsSystemDrawWire(self, (point_fi, point_chassis), wire_width,
                                                                    extra_points=[target],
                                                                    easyucs_fabric_port=peer_port._parent))
                                # self.wires = remove_not_completed_in_list(self.wires)
                        else:
                            self.logger(level="error", message="Peer not found")

                    if peer_fex:
                        # Find and calculate coordinates of the peer point on the FEX
                        point_fex = None
                        for port in fex.host_ports:
                            if (int(port.id) == peer_port_id) and port.aggr_id is None:
                                # Even / odd
                                point_fex = port.coord[0] + round(port.size[0] / 3) + (peer_port_id + 1) % 2 * round(
                                    port.size[0] / 3), port.coord[1] + round(port.size[1] / 2)
                                peer_port = port

                        self.logger(level="debug", message="Setting wire for chassis " + self.chassis._parent.id +
                                                           ", width : " + str(wire_width),)
                        if point_fex:
                            # draw_wire(self.draw, point_fex, point_chassis, wire_color, wire_width)
                            if point_breakout:
                                self.wires.append(
                                    UcsSystemDrawWire(self, (point_chassis, point_breakout), wire_width,
                                                      easyucs_fabric_port=peer_port._parent, line_type="straight"))
                                self.wires.append(UcsSystemDrawWire(self, (point_fex, point_chassis), wire_width,
                                                                    easyucs_fabric_port=peer_port._parent))
                                # self.wires = remove_not_completed_in_list(self.wires)

                                fill_color = "black"
                                font_size = 40
                                font_title = ImageFont.truetype('arial.ttf', font_size)
                                self.draw.text((point_fex[0] - 30, point_chassis[1] - 45), io_port.id, fill=fill_color,
                                               font=font_title)
                            else:
                                # self.wires.append(EasyUcsDrawWire(self.draw, (point_fex, point_chassis), wire_width,
                                #                              easyucs_fi_port=port.port))
                                if fabric == "a":
                                    if int(io_detail.id) % 2:
                                        # if (int(adapt_port.port.port_id) % 2) :
                                        step = self.WIRE_DISTANCE_SHORT + round(io_port.size[1] / 2)
                                    else:
                                        step = self.WIRE_DISTANCE_LONG + round(io_port.size[1] / 2)
                                if fabric == "b":
                                    if int(io_detail.id) % 2:
                                        step = - self.WIRE_DISTANCE_LONG - round(io_port.size[1] / 2)
                                    else:
                                        step = - self.WIRE_DISTANCE_SHORT - round(io_port.size[1] / 2)
                                target = point_chassis[0], point_chassis[1] + step
                                self.wires.append(UcsSystemDrawWire(self, (point_fex, point_chassis), wire_width,
                                                                    extra_points=[target],
                                                                    easyucs_fabric_port=peer_port._parent))
                                # self.wires = remove_not_completed_in_list(self.wires)
                        else:
                            self.logger(level="error", message="Peer not found1")

        # Handling wire from FEX to FI
        if self.fex_presence:
            for fex in (self.fex_a, self.fex_b):
                for fex_port in fex.fabric_ports:
                    # Search for peer information
                    if hasattr(port, 'peer'):
                        peer = fex_port.peer
                    else:
                        peer = fex_port._parent.peer
                    peer_fi = None
                    if "switch" in peer:
                        peer_fi = peer["switch"]
                        if peer_fi == "A":  # if FI A
                            fi = self.fi_a
                        if peer_fi == "B":  # if FI B
                            fi = self.fi_b
                    peer_slot_id = peer["slot"]
                    peer_port_id = peer["port"]
                    if "aggr_port" in peer:
                        peer_aggr_id = peer["aggr_port"]
                    else:
                        peer_aggr_id = None
                    #  int(not(0)) = 1, impair port are placed at a third of the port size, pair at two third
                    point_fex = fex_port.coord[0] + (1 + int(not (int(fex_port.id) % 2))) * round(fex_port.size[0] / 3), \
                                fex_port.coord[1] + fex_port.size[1] / 2

                    wire_width = 15  # Set the default wire width

                    if peer_fi:
                        # Find and calculate coordinates of the peer point on the FI
                        point_fi = None
                        if peer_slot_id == 1:
                            for port in fi.ports:
                                if peer_aggr_id:
                                    if int(port.id) == peer_port_id:
                                        if port.aggr_id:
                                            wire_width = 5
                                            if int(port.aggr_id) == peer_aggr_id:
                                                # Even / odd
                                                point_fi = port.coord[0] + round(port.size[0] / 3) + (
                                                    peer_aggr_id + 1) % 2 * round(
                                                    port.size[0] / 3) - ((peer_aggr_id + 1) % 2), port.coord[1] + round(
                                                    port.size[1] / 2)
                                                peer_port = port
                                else:
                                    if (int(port.id) == peer_port_id) and port.aggr_id is None:
                                        # Even / odd
                                        point_fi = port.coord[0] + round(port.size[0] / 3) + (
                                                    peer_port_id + 1) % 2 * round(port.size[0] / 3), port.coord[
                                                       1] + round(port.size[1] / 2)
                                        peer_port = port

                        else:
                            for gem in fi.expansion_modules:
                                if int(gem._parent.id) == peer_slot_id:
                                    for port in gem.ports:
                                        if peer_aggr_id:
                                            if int(port.id) == peer_port_id:
                                                if port.aggr_id:
                                                    wire_width = 5
                                                    if int(port.aggr_id) == peer_aggr_id:
                                                        # Even / odd
                                                        point_fi = port.coord[0] + round(port.size[0] / 3) + (
                                                            peer_aggr_id + 1) % 2 * round(
                                                            port.size[0] / 3) - ((peer_aggr_id + 1) % 2), port.coord[
                                                                       1] + round(
                                                            port.size[1] / 2)
                                                        peer_port = port
                                        else:
                                            if (int(port.id) == peer_port_id) and port.aggr_id is None:
                                                # Even / odd
                                                point_fi = port.coord[0] + round(port.size[0] / 3) + (
                                                    peer_port_id + 1) % 2 * round(
                                                    port.size[0] / 3), port.coord[1] + round(
                                                    port.size[1] / 2)
                                                peer_port = port

                        self.logger(level="debug", message="Setting wire for FEX " + fex._parent.id + ", width : " +
                                                           str(wire_width))
                        if point_fi:
                            # draw_wire(self.draw, point_fi, point_fex, wire_color, wire_width)
                            # 8 is the number max of fex port wired to a FI, 400 is the space between a fex and a FI
                            target = point_fex[0], fex.picture_offset[1] - int(fex_port.id) * round(400 / 8) + \
                                     round(400 / 8 / 2)
                            self.wires.append(UcsSystemDrawWire(self, (point_fi, point_fex), wire_width,
                                                                easyucs_fabric_port=peer_port._parent,
                                                                extra_points=[target]))
                            # self.wires = remove_not_completed_in_list(self.wires)
                        else:
                            self.logger(level="error", message="Peer not found2")


class UcsImcDrawChassisFront(GenericUcsDrawEquipment):
    def __init__(self, parent=None):
        GenericUcsDrawEquipment.__init__(self, parent=parent, orientation="front")
        if not self.picture:
            return

        self.background = self._create_background(self.canvas_width, self.canvas_height, self.canvas_color)
        self.draw = self._create_draw()

        self.paste_layer(self.picture, self.picture_offset)

        if "blades_slots" in self.json_file:
            self.server_nodes = self.get_server_nodes()
        if "psus_slots" in self.json_file:
            self.power_supplies = self.get_power_supplies()
        if ("blades_slots" or "psus_slots") in self.json_file:
            self.fill_blanks()

        self._file_name = self._device_target + "_chassis_front"

    def get_server_nodes(self):
        server_nodes_list = []
        for server_node in self._parent.server_nodes:
            server_nodes_list.append(UcsBladeDrawFront(server_node, self))
            # blade_list = remove_not_completed_in_list(blade_list)
        # blade_list = remove_not_supported_in_list(blade_list)
        # We only keep the blades that have been fully created -> picture
        server_nodes = [server_node for server_node in server_nodes_list if server_node.picture_size]
        return server_nodes

    def get_power_supplies(self):
        psu_list = []
        for psu in self._parent.power_supplies:
            if psu.id != '0':
                psu_list.append(UcsPsuDraw(psu, self))
                # psu_list = remove_not_completed_in_list(psu_list)
            # psu_list = remove_not_supported_in_list(psu_list)
        # We only keep the PSU that have been fully created -> picture
        psu_list = [psu for psu in psu_list if psu.picture_size]
        return psu_list

    def fill_blanks(self):  # Fill blade slot
        if len(self._parent.server_nodes)-1 < len(self.json_file["blades_slots"]):
            used_slot = []
            potential_slot = []
            unused_slot = []
            for slot in self._parent.server_nodes:
                if hasattr(slot, "scaled_mode"):
                    if slot.scaled_mode == "scaled":
                        used_slot.append(int(slot.slot_id) - 2)
                        used_slot.append(int(slot.slot_id) - 1)
                        used_slot.append(int(slot.slot_id) + 1)
                    if slot.scaled_mode == "single":
                        used_slot.append(int(slot.slot_id) + 1)
                # We handle the specific case of a B460 M4 for which we also use the 2 slots above the master blade
                used_slot.append(int(slot.slot_id))
            for slot in self.json_file["blades_slots"]:
                potential_slot.append(slot["id"])
            for blank_id in set(potential_slot) - set(used_slot):
                unused_slot.append(blank_id)

            for slot_id in unused_slot:
                impair_model = None
                impair_model_width = None
                if (slot_id + 1) % 2:  # condition : if even
                    for server_node in self._parent.server_nodes:
                        if int(server_node.slot_id) == (slot_id - 1):
                            impair_model = server_node.sku

                if impair_model:
                    for model in self.json_file["blades_models"]:
                        if model['name'] == impair_model:
                            impair_model_width = model['width']

                if impair_model_width != "full":
                    for model in self.json_file["blades_models"]:
                        if "type" in model:
                            if model["type"] == "blank":
                                blank_name = model["name"]
                                img = Image.open("catalog/blades/img/" + blank_name + ".png", 'r')
                                for slot in self.json_file["blades_slots"]:
                                    if slot["id"] == int(slot_id):
                                        coord = slot["coord"]
                                coord_offset = self.picture_offset[0] + coord[0], self.picture_offset[1] + coord[1]
                                self.paste_layer(img, coord_offset)

        if "psus_slots" in self.json_file:
            if len(self._parent.power_supplies) < len(self.json_file["psus_slots"]):  # Fill blank for rear PSU Slot
                used_slot = []
                potential_slot = []
                unused_slot = []
                for slot in self._parent.power_supplies:
                    used_slot.append(int(slot.id))
                for slot in self.json_file["psus_slots"]:
                    potential_slot.append(slot["id"])
                for blank_id in set(potential_slot) - set(used_slot):
                    unused_slot.append(blank_id)
                for slot_id in unused_slot:
                    for expansion in self.json_file["psus_models"]:
                        if "type" in expansion:
                            if expansion["type"] == "blank":
                                blank_name = expansion["name"]
                                img = Image.open("catalog/power_supplies/img/" + blank_name + ".png", 'r')
                                for slot in self.json_file["psus_slots"]:
                                    if slot["id"] == int(slot_id):
                                        coord = slot["coord"]
                                coord_offset = self.picture_offset[0] + coord[0], self.picture_offset[1] + coord[1]
                                self.paste_layer(img, coord_offset)


class UcsImcDrawChassisRear(GenericUcsDrawEquipment):
    def __init__(self, parent=None):
        GenericUcsDrawEquipment.__init__(self, parent=parent, orientation="rear")
        if not self.picture:
            return

        self.background = self._create_background(self.canvas_width, self.canvas_height, self.canvas_color)
        self.draw = self._create_draw()

        self.paste_layer(self.picture, self.picture_offset)

        if self._parent.system_io_controllers:
            # We have SIOCs in the chassis (S3260)
            self.sioc_list = self.get_sioc_list()
            if "blades_slots_rear" in self.json_file:
                self.server_nodes = self.get_server_nodes()
            if "psus_slots_rear" in self.json_file:
                self.power_supplies = self.get_power_supplies()
            if "disks_slots_rear" in self.json_file:
                self.storage_enclosures = self.get_storage_enclosures()
            self.fill_blanks()
            self._file_name = self._device_target + "_chassis_rear"

        else:
            self.logger(level="error", message="No SIOC in chassis. Skipping chassis")

    def fill_blanks(self):
        # Fills unused SIOC slots with blanking panels
        if self._parent.system_io_controllers:
            slots_list = self.json_file["system_io_controllers_slots"]
            models_list = self.json_file["system_io_controllers_models"]
            objects_list = self._parent.system_io_controllers

        if len(objects_list) < len(slots_list):
            # Load blank image from JSON file
            for expansion in models_list:
                if "type" in expansion:
                    if expansion["type"] == "blank":
                        blank_name = expansion["name"]
                        blank_img = Image.open("catalog/io_modules/img/" + blank_name + ".png", 'r')

            all_slot_ids = []
            used_slot_ids = []
            unused_slot_ids = []

            for slot in objects_list:
                if slot.id == 'A':  # for FI A in IOM Slot 1
                    used_slot_ids.append(1)
                elif slot.id == 'B':  # for FI B in IOM Slot 2
                    used_slot_ids.append(2)
                else:  # for normal use of a chassis ( != UCS Mini/X-Direct)
                    used_slot_ids.append(int(slot.id))

            for slot in slots_list:
                all_slot_ids.append(slot["id"])

            for blank_id in set(all_slot_ids) - set(used_slot_ids):
                unused_slot_ids.append(blank_id)

            for slot_id in unused_slot_ids:
                # We need to get the coordinates of the slot to place the blank
                for slot in slots_list:
                    if slot["id"] == int(slot_id):
                        coord = slot["coord"]
                # We paste the blanking panel
                coord_offset = self.picture_offset[0] + coord[0], self.picture_offset[1] + coord[1]
                self.paste_layer(blank_img, coord_offset)

        # Fills unused PSU slots with blanking panels
        if "psus_slots_rear" in self.json_file:
            if len(self._parent.power_supplies) < len(self.json_file["psus_slots_rear"]):
                # Load blank image from JSON file
                for expansion in self.json_file["psus_models"]:
                    if "type" in expansion:
                        if expansion["type"] == "blank":
                            blank_name = expansion["name"]
                            blank_img = Image.open("catalog/power_supplies/img/" + blank_name + ".png", 'r')

                all_slot_ids = []
                used_slot_ids = []
                unused_slot_ids = []

                for slot in self._parent.power_supplies:
                    used_slot_ids.append(int(slot.id))

                for slot in self.json_file["psus_slots_rear"]:
                    all_slot_ids.append(slot["id"])

                for blank_id in set(all_slot_ids) - set(used_slot_ids):
                    unused_slot_ids.append(blank_id)

                for slot_id in unused_slot_ids:
                    # We need to get the coordinates of the slot to place the blank
                    for slot in self.json_file["psus_slots_rear"]:
                        if slot["id"] == int(slot_id):
                            coord = slot["coord"]
                    # We paste the blanking panel
                    coord_offset = self.picture_offset[0] + coord[0], self.picture_offset[1] + coord[1]
                    self.paste_layer(blank_img, coord_offset)

        # Fills unused server node slots with blanking panels
        if "blades_slots_rear" in self.json_file:
            if len(self._parent.server_nodes) < len(self.json_file["blades_slots_rear"]):
                # Load blank image from JSON file
                for expansion in self.json_file["blades_models"]:
                    if "type" in expansion:
                        if expansion["type"] == "blank":
                            blank_name = expansion["name"]
                            blank_img = Image.open("catalog/blades/img/" + blank_name + ".png", 'r')

                all_slot_ids = []
                used_slot_ids = []
                unused_slot_ids = []

                for slot in self._parent.server_nodes:
                    used_slot_ids.append(int(slot.slot_id))

                for slot in self.json_file["blades_slots_rear"]:
                    all_slot_ids.append(slot["id"])

                for blank_id in set(all_slot_ids) - set(used_slot_ids):
                    unused_slot_ids.append(blank_id)

                for slot_id in unused_slot_ids:
                    # We need to get the coordinates of the slot to place the blank
                    for slot in self.json_file["blades_slots_rear"]:
                        if slot["id"] == int(slot_id):
                            coord = slot["coord"]
                    # We paste the blanking panel
                    coord_offset = self.picture_offset[0] + coord[0], self.picture_offset[1] + coord[1]
                    self.paste_layer(blank_img, coord_offset)

        # Fill blank for SSD slot in UCSS chassis
        if self._parent.sku == "UCSC-C3X60" or self._parent.sku == "UCSS-S3260":
            disk_list = []
            for enclosure in self.storage_enclosures:
                for disk in enclosure.disks:
                    disk_list.append(disk)
                    # disk_list = remove_not_completed_in_list(disk_list)

            used_slot = []
            potential_slot = []
            unused_slot = []

            for disk in disk_list:
                used_slot.append(int(disk.id))
            for disk in self.json_file['disks_slots_rear']:
                potential_slot.append(disk["id"])
            for blank_id in set(potential_slot) - set(used_slot):
                unused_slot.append(blank_id)
            for slot_id in unused_slot:
                blank_name = None
                orientation = "horizontal"
                disk_format = None
                for disk_slot in self.json_file["disks_slots_rear"]:
                    if disk_slot['id'] == slot_id:
                        orientation = disk_slot['orientation']
                        disk_format = disk_slot['format']
                for model in self.json_file["disks_models"]:
                    if "type" in model and not blank_name:
                        if model["type"] == "blank" and model["format"] == disk_format:
                            blank_name = model["name"]
                            img = Image.open("catalog/drives/img/" + blank_name + ".png", 'r')
                            if orientation == "vertical":
                                img = GenericUcsDrawEquipment.rotate_object(picture=img)
                if blank_name:
                    for slot in self.json_file['disks_slots_rear']:
                        if slot["id"] == int(slot_id):
                            coord = slot["coord"]
                    coord_offset = self.picture_offset[0] + coord[0], \
                                   self.picture_offset[1] + coord[1]

                    self.paste_layer(img, coord_offset)

    def get_storage_enclosures(self):
        storage_enclosure_list = []
        for storage_enclosure in self._parent.storage_enclosures:
            if storage_enclosure.type == "rear-ssd":
                storage_enclosure_list.append(UcsStorageEnclosureDraw(storage_enclosure, self))
            # storage_enclosure_list = remove_not_completed_in_list(storage_enclosure_list)
        return storage_enclosure_list

    def get_server_nodes(self):
        server_nodes_list = []
        for server_node in self._parent.server_nodes:
            server_nodes_list.append(UcsBladeDrawFront(server_node, self))
        # blade_list = remove_not_supported_in_list(blade_list)
        # blade_list = remove_not_completed_in_list(blade_list)
        # We only keep the blades that have been fully created -> picture
        server_nodes = [server_node for server_node in server_nodes_list if server_node.picture_size]
        return server_nodes

    def get_power_supplies(self):
        psu_list = []
        for psu in self._parent.power_supplies:
            if psu.id != '0':  # UCS PE sometimes adds an invalid PSU with ID 0
                psu_list.append(UcsPsuDraw(psu, self))
        # psu_list = remove_not_supported_in_list(psu_list)
        # psu_list = remove_not_completed_in_list(psu_list)
        # We only keep the PSU that have been fully created -> picture
        psu_list = [psu for psu in psu_list if psu.picture_size]
        return psu_list

    def get_sioc_list(self):
        sioc_list = []
        for sioc in self._parent.system_io_controllers:
            sioc_list.append(UcsSiocDraw(sioc, self))
        # sioc_list = remove_not_supported_in_list(sioc_list)
        # sioc_list = remove_not_completed_in_list(sioc_list)
        # We only keep the sioc that have been fully created -> picture
        sioc_list = [sioc for sioc in sioc_list if sioc.picture_size]
        return sioc_list
