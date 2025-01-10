# coding: utf-8
# !/usr/bin/env python

""" racks.py: Easy UCS Deployment Tool """

from report.content import *
from report.generic.inventory.psu import UcsPsuReportSection
from report.generic.inventory.storage import (
    UcsNvmeDrivesReportSection,
    UcsStorageControllerReportSection
)
from report.ucs.section import UcsReportSection
from report.ucs.table import UcsReportTable


class UcsRacksInventoryReportSection(UcsReportSection):
    def __init__(self, order_id, parent, domain, title=""):
        if not title:
            title = "Rack Servers Inventory"
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        if domain.rack_units:
            descr = ""  # TODO
            self.content_list.append(
                GenericReportText(order_id=self.report.get_current_order_id(), parent=self, string=descr))
        for rack in domain.rack_units:
            if rack.id:
                rack_name = str(rack.id)
            else:
                rack_name = str(rack.name)
            if rack.user_label:
                rack_name += " - " + rack.user_label
            self.content_list.append(UcsRackReportSection(
                order_id=self.report.get_current_order_id(), parent=self, rack=rack, title="Rack " + rack_name))

        if self.report.device.metadata.device_type in ["intersight", "ucsm"]:
            if domain.rack_units:
                self.content_list.append(
                    UcsRacksSummaryReportSection(
                        order_id=self.report.get_current_order_id(), parent=self, rack_units=domain.rack_units)
                )


class UcsRackReportSection(UcsReportSection):
    def __init__(self, order_id, parent, rack, title):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        descr = ""  # TODO
        self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                   string=descr))

        path_front = self.report.img_path + "rack_" + str(rack.id) + "_front.png"
        path_rear = self.report.img_path + "rack_" + str(rack.id) + "_rear_clear.png"
        if self.report.device.metadata.device_type == "cimc":
            path_front = self.report.img_path + "rack_front.png"
            path_rear = self.report.img_path + "rack_rear.png"
        elif self.report.device.metadata.device_type == "intersight":
            if rack._parent.__class__.__name__ in ["IntersightImmDomain", "IntersightUcsmDomain"]:
                path_front = self.report.img_path + rack._parent.name + "_rack_" + str(rack.id) + "_front.png"
                path_rear = self.report.img_path + rack._parent.name + "_rack_" + str(rack.id) + "_rear_clear.png"
            else:
                path_front = self.report.img_path + "rack_" + str(rack.name) + "_front.png"
                path_rear = self.report.img_path + "rack_" + str(rack.name) + "_rear_clear.png"

        self.content_list.append(
            GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path_front,
                               centered=True, spacing_after=2))
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                              string="Front View", centered=True, italicized=True, font_size=8))

        self.content_list.append(
            GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path_rear,
                               centered=True, spacing_after=2))
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                              string="Rear View", centered=True, italicized=True, font_size=8))

        if self.report.size == "full":
            self.content_list.append(
                UcsRackReportTable(order_id=self.report.get_current_order_id(), parent=self, rack=rack, centered=True))

        if rack.power_supplies:
            self.content_list.append(UcsPsuReportSection(
                order_id=self.report.get_current_order_id(), parent=self, title="Power Supplies", device=rack))
        if rack.storage_controllers:
            for storage_controller in rack.storage_controllers:
                key = UcsReportTable.get_name_and_sku(storage_controller)
                self.content_list.append(
                    UcsStorageControllerReportSection(
                        order_id=self.report.get_current_order_id(), parent=self,
                        title="Storage Controller " + storage_controller.id + ' - ' + key, device=storage_controller))
        if rack.nvme_drives:
            self.content_list.append(
                UcsNvmeDrivesReportSection(
                    order_id=self.report.get_current_order_id(), parent=self, title="NVMe Drives", device=rack))


class UcsRackReportTable(UcsReportTable):
    def __init__(self, order_id, parent, rack, centered=False):
        firmware_version = "N/A"
        if parent.report.device.metadata.device_type == "intersight":
            firmware_version = rack.firmware_version
        elif parent.report.device.metadata.device_type in ["ucsc", "ucsm"]:
            firmware_version = rack.firmware_package_version
        rows = [
            ["Description", "Value"],
            ["Rack ID", rack.id],
            ["SKU", rack.sku],
            ["Model", rack.name],
            ["Serial Number", rack.serial],
            ["Firmware", firmware_version]
        ]

        memory_info = ""
        if rack.memory_arrays:
            memory_dict = {}
            for array in rack.memory_arrays:
                for unit in array.memory_units:
                    if not unit.capacity:
                        continue
                    if unit.sku:
                        if unit.clock and unit.type:
                            key = str(int(unit.capacity / 1024)) + 'GB ' + str(unit.type) + ' ' + str(unit.clock) + \
                                  'MHz (' + unit.sku + ')'
                        elif unit.clock:
                            key = str(int(unit.capacity / 1024)) + 'GB ' + str(unit.clock) + 'MHz (' + unit.sku + ')'
                        else:
                            key = str(int(unit.capacity / 1024)) + 'GB ' + str(unit.type) + ' (' + unit.sku + ')'
                    else:
                        if unit.clock and unit.type:
                            key = str(int(unit.capacity / 1024)) + 'GB ' + str(unit.type) + ' ' + str(unit.clock) + \
                                  'MHz'
                        elif unit.clock:
                            key = str(int(unit.capacity / 1024)) + 'GB ' + str(unit.clock) + 'MHz'
                        else:
                            key = str(int(unit.capacity / 1024)) + 'GB' + str(unit.type)
                    if key in memory_dict:
                        memory_dict[key] += 1
                    else:
                        memory_dict.update({key: 1})
            memory_info = "\n".join([(str(i[1]) + "x " + str(i[0])) for i in memory_dict.items()])
        rows.append(["Memory", str(rack.memory_total_marketing) + "\n" + memory_info])

        if rack.adaptors:
            adaptor_dict = {}
            for adaptor in rack.adaptors:
                key = self.get_name_and_sku(adaptor)
                if key in adaptor_dict:
                    adaptor_dict[key] += 1
                else:
                    adaptor_dict.update({key: 1})
            adaptor_models = "\n".join([(str(i[1]) + "x " + str(i[0])) for i in adaptor_dict.items()])
            rows.append(["Adaptors", adaptor_models])

        if rack.cpus:
            cores = 0
            cpu_dict = {}

            for cpu in rack.cpus:
                key = self.get_name_and_sku(cpu)
                if key in cpu_dict:
                    cpu_dict[key] += 1
                else:
                    cpu_dict.update({key: 1})
                if cpu.cores:
                    cores += int(cpu.cores)

            if cores:
                if rack.cpus[0].speed:
                    speed = round(rack.cpus[0].speed / 1000, 2)
                    cores = str(cores) + " @ " + str(speed) + "GHz"

            cpu_model = "\n".join([(str(i[1]) + "x " + str(i[0])) for i in cpu_dict.items()])
            rows.append(["CPUs", cpu_model])
            rows.append(["Cores", cores])

        if rack.gpus:
            gpu_dict = {}
            for gpu in rack.gpus:
                key = self.get_name_and_sku(gpu)
                if key in gpu_dict:
                    gpu_dict[key] += 1
                else:
                    gpu_dict.update({key: 1})
            gpu_models = "\n".join([(str(i[1]) + "x " + str(i[0])) for i in gpu_dict.items()])
            rows.append(["GPUs", gpu_models])

        if rack.storage_controllers:
            storage_dict = {}
            drives_dict = {}
            for controller in rack.storage_controllers:
                key = self.get_name_and_sku(controller)
                if key in storage_dict:
                    storage_dict[key] += 1
                else:
                    storage_dict.update({key: 1})

                for drive in controller.disks:
                    key_drive = self.get_name_and_sku(drive)
                    if key_drive in drives_dict:
                        drives_dict[key_drive] += 1
                    else:
                        drives_dict.update({key_drive: 1})

            for drive in rack.nvme_drives:
                key_drive = self.get_name_and_sku(drive)
                if key_drive in drives_dict:
                    drives_dict[key_drive] += 1
                else:
                    drives_dict.update({key_drive: 1})

            storage = "\n".join([(str(i[1]) + "x " + str(i[0])) for i in storage_dict.items()])
            drives = "\n".join([(str(i[1]) + "x " + str(i[0])) for i in drives_dict.items()])
            rows.append(["Storage Controllers", storage])
            rows.append(["Drives", drives])

        if hasattr(rack, "storage_flexflash_controllers") and rack.storage_flexflash_controllers:
            flash_dict = {}
            for controller in rack.storage_flexflash_controllers:
                for card in controller.flexflash_cards:
                    if card.capacity_marketing in flash_dict:
                        flash_dict[card.capacity_marketing] += 1
                    else:
                        flash_dict.update({card.capacity_marketing: 1})
            flash_cards = "\n".join([(str(i[1]) + "x " + str(i[0])) for i in flash_dict.items()])
            rows.append(["FlexFlash SD Cards", flash_cards])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows)


class UcsRacksSummaryReportSection(UcsReportSection):
    def __init__(self, order_id, parent, rack_units, title=""):
        if not title:
            title = "Rack Servers Summary"
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            UcsRacksSummaryReportTable(order_id=self.report.get_current_order_id(), parent=self, rack_units=rack_units,
                                       centered=True))


class UcsRacksSummaryReportTable(UcsReportTable):
    def __init__(self, order_id, parent, rack_units, centered=False):
        rows = [["ID", "Model", "Serial Number", "RAM", "CPUs", "Cores", "Adapters", "GPUs", "Drives", "SD Cards"]]

        for rack in rack_units:
            cores = ""
            if rack.cpus:
                if rack.cpus[0].cores:
                    cores = int(rack.cpus[0].cores)
                    if len(rack.cpus) > 1:
                        cores = int(rack.cpus[0].cores) * len(rack.cpus)

            adaptor_sum = 0
            adaptor_models = ""  # If all drives have the same capacity, we write it down
            if rack.adaptors:
                adaptor_sum = len(rack.adaptors)
                if type(adaptor_models) == str:
                    adaptor_models = rack.adaptors[0].short_name
                if adaptor_models:
                    for adaptor in rack.adaptors:
                        if adaptor.short_name != adaptor_models:
                            adaptor_models = None
            if adaptor_models and adaptor_sum:
                adaptor_sum = str(adaptor_sum) + "x " + adaptor_models

            drives = 0
            drives_capacity = ""  # If all drives have the same capacity, we write it down
            for storage_controller in rack.storage_controllers:
                if storage_controller.disks:
                    drives += len(storage_controller.disks)
                    if type(drives_capacity) == str:
                        if not drives_capacity:
                            drives_capacity = storage_controller.disks[0].size_marketing
                    if drives_capacity:
                        for disk in storage_controller.disks:
                            if disk.size_marketing != drives_capacity:
                                drives_capacity = None
            if rack.nvme_drives:
                drives += len(rack.nvme_drives)
                if type(drives_capacity) == str:
                    drives_capacity = rack.nvme_drives[0].size_marketing
                if drives_capacity:
                    for disk in rack.nvme_drives:
                        if disk.size_marketing != drives_capacity:
                            drives_capacity = None
            if drives_capacity and drives:
                drives = str(drives) + "x " + str(drives_capacity)

            sd_cards = 0
            sd_cards_capacity = ""   # If all drives have the same capacity, we write it down
            if hasattr(rack, "storage_flexflash_controller"):
                for storage_flexflash_controller in rack.storage_flexflash_controllers:
                    if storage_flexflash_controller.flexflash_cards:
                        sd_cards += len(storage_flexflash_controller.flexflash_cards)
                        if type(sd_cards_capacity) == str:
                            sd_cards_capacity = storage_flexflash_controller.flexflash_cards[0].capacity_marketing
                        if sd_cards_capacity:
                            for sd_card in storage_flexflash_controller.flexflash_cards:
                                if sd_card.capacity_marketing != sd_cards_capacity:
                                    sd_cards_capacity = None
                    if sd_cards_capacity and sd_cards:
                        sd_cards = str(sd_cards) + "x " + sd_cards_capacity

            if rack.cpus:
                if rack.cpus[0].model_short_name:
                    rows.append([rack.id, rack.short_name, rack.serial, rack.memory_total_marketing,
                                 str(len(rack.cpus)) + "x " + rack.cpus[0].model_short_name, cores, adaptor_sum,
                                 len(rack.gpus), drives, sd_cards])
                else:
                    rows.append([rack.id, rack.short_name, rack.serial, rack.memory_total_marketing,
                                 str(len(rack.cpus)), cores, adaptor_sum, len(rack.gpus), drives, sd_cards])

        # In case there are no racks, this prevents an IndexError exception
        if len(rows) == 1:
            column_number = 0
        else:
            column_number = len(rows[1])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=column_number, centered=centered, cells_list=rows, font_size=9)


class UcsRackEnclosuresInventoryReportSection(UcsReportSection):
    def __init__(self, order_id, parent, domain, title=""):
        if not title:
            title = "Rack Enclosures Inventory"
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        if domain.rack_enclosures:
            descr = ""  # TODO
            self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                       string=descr))
        server_node_list = []
        for rack_enclosure in domain.rack_enclosures:
            rack_enclosure_name = str(rack_enclosure.id)
            self.content_list.append(
                UcsRackEnclosureReportSection(
                    order_id=self.report.get_current_order_id(), parent=self, rack_enclosure=rack_enclosure,
                    title="Rack Enclosure " + rack_enclosure_name)
            )
            if rack_enclosure.server_nodes:
                server_node_list = server_node_list + rack_enclosure.server_nodes

        if server_node_list:
            self.content_list.append(
                UcsServerNodesSummaryReportSection(
                    order_id=self.report.get_current_order_id(), parent=self, server_nodes=server_node_list,
                    title="Server Nodes Servers Summary")
            )


class UcsRackEnclosureReportSection(UcsReportSection):
    def __init__(self, order_id, parent, rack_enclosure, title):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        descr = ""  # TODO
        self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                   string=descr))

        path_front = self.report.img_path + "rack_enclosure_" + str(rack_enclosure.id) + "_front.png"
        self.content_list.append(
            GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path_front,
                               centered=True, spacing_after=2))
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                              string="Front View", centered=True, italicized=True, font_size=8))

        path_rear = self.report.img_path + "rack_enclosure_" + str(rack_enclosure.id) + "_rear_clear.png"
        self.content_list.append(
            GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path_rear,
                               centered=True, spacing_after=2))
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                              string="Rear View", centered=True, italicized=True, font_size=8))
        self.content_list.append(
            UcsRackEnclosureReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                        rack_enclosure=rack_enclosure, centered=True))

        if rack_enclosure.power_supplies:
            self.content_list.append(UcsPsuReportSection(
                order_id=self.report.get_current_order_id(), parent=self, title="Power Supplies",
                device=rack_enclosure)
            )

        if rack_enclosure.server_nodes:
            self.content_list.append(UcsServerNodesReportSection(
                order_id=self.report.get_current_order_id(), parent=self, rack_enclosure=rack_enclosure,
                title="Server Nodes")
            )


class UcsRackEnclosureReportTable(UcsReportTable):
    def __init__(self, order_id, parent, rack_enclosure, centered=False):
        rows = [
            ["Description", "Value"],
            ["Rack Enclosure ID", rack_enclosure.id],
            ["SKU", rack_enclosure.sku],
            ["Model", rack_enclosure.name],
            ["Serial Number", rack_enclosure.serial]
        ]

        if rack_enclosure.power_supplies:
            psu_dict = {}
            for psu in rack_enclosure.power_supplies:
                key = self.get_name_and_sku(psu)
                if key in psu_dict:
                    psu_dict[key] += 1
                else:
                    psu_dict.update({key: 1})
            psu_models = "\n".join([(str(i[1]) + "x " + str(i[0])) for i in psu_dict.items()])
            rows.append(["Power Supplies", psu_models])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows)


class UcsServerNodesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, rack_enclosure, title):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if self.report.size == "full":
            self.content_list.append(
                UcsServerNodesSummaryReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                                 server_nodes=rack_enclosure.server_nodes, centered=True))

            for server_node in rack_enclosure.server_nodes:
                server_node_name = server_node.id + " details"
                if server_node.user_label:
                    server_node_name = server_node.id + " details - " + server_node.user_label
                self.content_list.append(UcsServerNodeReportSection(
                    order_id=self.report.get_current_order_id(), parent=self, server_node=server_node,
                    title="Server Node " + server_node_name)
                )


class UcsServerNodeReportSection(UcsReportSection):
    def __init__(self, order_id, parent, server_node, title):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if self.report.size == "full":
            self.content_list.append(
                UcsServerNodeReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                         server_node=server_node, centered=True))

            if server_node.storage_controllers:
                for storage_controller in server_node.storage_controllers:
                    key = UcsReportTable.get_name_and_sku(storage_controller)
                    self.content_list.append(
                        UcsStorageControllerReportSection(
                            order_id=self.report.get_current_order_id(), parent=self,
                            title="Storage Controller " + storage_controller.id + ' - ' + key,
                            device=storage_controller)
                    )

            if server_node.nvme_drives:
                self.content_list.append(
                    UcsNvmeDrivesReportSection(
                        order_id=self.report.get_current_order_id(), parent=self, title="NVMe Drives",
                        device=server_node)
                )


class UcsServerNodeReportTable(UcsReportTable):
    def __init__(self, order_id, parent, server_node, centered=False):
        firmware_version = "N/A"
        if parent.report.device.metadata.device_type == "intersight":
            firmware_version = server_node.firmware_version
        elif parent.report.device.metadata.device_type in ["ucsc", "ucsm"]:
            firmware_version = server_node.firmware_package_version
        rows = [
            ["Description", "Value"],
            ["Server Node ID", server_node.id],
            ["SKU", server_node.sku],
            ["Model", server_node.name],
            ["Serial Number", server_node.serial],
            ["Firmware", firmware_version]
        ]

        if server_node.memory_arrays:
            memory_dict = {}
            for array in server_node.memory_arrays:
                for unit in array.memory_units:
                    if not unit.capacity:
                        continue
                    if unit.sku:
                        if unit.clock:
                            key = str(int(unit.capacity / 1024)) + 'GB ' + str(unit.type) + ' ' + str(
                                unit.clock) + 'MHz (' + unit.sku + ')'
                        else:
                            key = str(int(unit.capacity / 1024)) + 'GB ' + str(unit.type) + ' (' + unit.sku + ')'
                    else:
                        if unit.clock:
                            key = str(int(unit.capacity / 1024)) + 'GB ' + str(unit.type) + ' ' + str(
                                unit.clock) + 'MHz'
                        else:
                            key = str(int(unit.capacity / 1024)) + 'GB' + str(unit.type)
                    if key in memory_dict:
                        memory_dict[key] += 1
                    else:
                        memory_dict.update({key: 1})
            memory_info = "\n".join([(str(i[1]) + "x " + str(i[0])) for i in memory_dict.items()])
            rows.append(["Memory", str(server_node.memory_total_marketing) + "\n" + memory_info])

        if server_node.adaptors:
            adaptor_dict = {}
            for adaptor in server_node.adaptors:
                key = self.get_name_and_sku(adaptor)
                if key in adaptor_dict:
                    adaptor_dict[key] += 1
                else:
                    adaptor_dict.update({key: 1})
            adaptor_models = "\n".join([(str(i[1]) + "x " + str(i[0])) for i in adaptor_dict.items()])
            rows.append(["Adaptors", adaptor_models])

        if server_node.cpus:
            cores = 0
            cpu_dict = {}

            for cpu in server_node.cpus:
                key = self.get_name_and_sku(cpu)
                if key in cpu_dict:
                    cpu_dict[key] += 1
                else:
                    cpu_dict.update({key: 1})
                if cpu.cores:
                    cores += int(cpu.cores)

            if cores:
                if server_node.cpus[0].speed:
                    speed = round(server_node.cpus[0].speed / 1000, 2)
                    cores = str(cores) + " @ " + str(speed) + "GHz"

            cpu_model = "\n".join([(str(i[1]) + "x " + str(i[0])) for i in cpu_dict.items()])
            rows.append(["CPUs", cpu_model])
            rows.append(["Cores", cores])

        if server_node.gpus:
            gpu_dict = {}
            for gpu in server_node.gpus:
                key = self.get_name_and_sku(gpu)
                if key in gpu_dict:
                    gpu_dict[key] += 1
                else:
                    gpu_dict.update({key: 1})
            gpu_models = "\n".join([(str(i[1]) + "x " + str(i[0])) for i in gpu_dict.items()])
            rows.append(["GPUs", gpu_models])

        if server_node.storage_controllers:
            storage_dict = {}
            drives_dict = {}
            for controller in server_node.storage_controllers:
                key = self.get_name_and_sku(controller)
                if key in storage_dict:
                    storage_dict[key] += 1
                else:
                    storage_dict.update({key: 1})

                for drive in controller.disks:
                    key_drive = self.get_name_and_sku(drive)
                    if key_drive in drives_dict:
                        drives_dict[key_drive] += 1
                    else:
                        drives_dict.update({key_drive: 1})

            for drive in server_node.nvme_drives:
                key_drive = self.get_name_and_sku(drive)
                if key_drive in drives_dict:
                    drives_dict[key_drive] += 1
                else:
                    drives_dict.update({key_drive: 1})

            storage = "\n".join([(str(i[1]) + "x " + str(i[0])) for i in storage_dict.items()])
            drives = "\n".join([(str(i[1]) + "x " + str(i[0])) for i in drives_dict.items()])
            rows.append(["Storage Controllers", storage])
            rows.append(["Drives", drives])

        if hasattr(server_node, "storage_flexflash_controllers") and server_node.storage_flexflash_controllers:
            flash_dict = {}
            for controller in server_node.storage_flexflash_controllers:
                for card in controller.flexflash_cards:
                    if card.capacity_marketing in flash_dict:
                        flash_dict[card.capacity_marketing] += 1
                    else:
                        flash_dict.update({card.capacity_marketing: 1})
            flash_cards = "\n".join([(str(i[1]) + "x " + str(i[0])) for i in flash_dict.items()])
            rows.append(["FlexFlash SD Cards", flash_cards])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows)


class UcsServerNodesSummaryReportSection(UcsReportSection):
    def __init__(self, order_id, parent, server_nodes, title):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            UcsServerNodesSummaryReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                             server_nodes=server_nodes, centered=True))


class UcsServerNodesSummaryReportTable(UcsReportTable):
    def __init__(self, order_id, parent, server_nodes, centered=False):
        rows = [["ID", "Model", "Serial Number", "RAM", "CPUs", "Cores", "Adapters", "GPUs", "Drives", "SD Cards"]]

        for server_node in server_nodes:
            cores = ""
            if server_node.cpus:
                if server_node.cpus[0].cores:
                    cores = int(server_node.cpus[0].cores)
                    if len(server_node.cpus) > 1:
                        cores = int(server_node.cpus[0].cores) * len(server_node.cpus)

            adaptor_sum = 0
            adaptor_models = ""  # If all drives have the same capacity, we write it down
            if server_node.adaptors:
                adaptor_sum = len(server_node.adaptors)
                if type(adaptor_models) == str:
                    adaptor_models = server_node.adaptors[0].short_name
                if adaptor_models:
                    for adaptor in server_node.adaptors:
                        if adaptor.short_name != adaptor_models:
                            adaptor_models = None
            if adaptor_models and adaptor_sum:
                adaptor_sum = str(adaptor_sum) + "x " + adaptor_models

            drives = 0
            drives_capacity = ""  # If all drives have the same capacity, we write it down
            for storage_controller in server_node.storage_controllers:
                if storage_controller.disks:
                    drives += len(storage_controller.disks)
                    if type(drives_capacity) == str:
                        if not drives_capacity:
                            drives_capacity = storage_controller.disks[0].size_marketing
                    if drives_capacity:
                        for disk in storage_controller.disks:
                            if disk.size_marketing != drives_capacity:
                                drives_capacity = None
            if server_node.nvme_drives:
                drives += len(server_node.nvme_drives)
                if type(drives_capacity) == str:
                    drives_capacity = server_node.nvme_drives[0].size_marketing
                if drives_capacity:
                    for disk in server_node.nvme_drives:
                        if disk.size_marketing != drives_capacity:
                            drives_capacity = None
            if drives_capacity and drives:
                drives = str(drives) + "x " + drives_capacity

            sd_cards = 0
            sd_cards_capacity = ""   # If all drives have the same capacity, we write it down
            for storage_flexflash_controller in server_node.storage_flexflash_controllers:
                if storage_flexflash_controller.flexflash_cards:
                    sd_cards += len(storage_flexflash_controller.flexflash_cards)
                    if type(sd_cards_capacity) == str:
                        sd_cards_capacity = storage_flexflash_controller.flexflash_cards[0].capacity_marketing
                    if sd_cards_capacity:
                        for sd_card in storage_flexflash_controller.flexflash_cards:
                            if sd_card.capacity_marketing != sd_cards_capacity:
                                sd_cards_capacity = None
                if sd_cards_capacity and sd_cards:
                    sd_cards = str(sd_cards) + "x " + sd_cards_capacity

            if server_node.cpus:
                if server_node.cpus[0].model_short_name:
                    rows.append([server_node.id, server_node.short_name, server_node.serial,
                                 server_node.memory_total_marketing,
                                 str(len(server_node.cpus)) + "x " + server_node.cpus[0].model_short_name, cores,
                                 adaptor_sum, len(server_node.gpus), drives, sd_cards])
                else:
                    rows.append([server_node.id, server_node.short_name, server_node.serial,
                                 server_node.memory_total_marketing, str(len(server_node.cpus)), cores, adaptor_sum,
                                 len(server_node.gpus), drives, sd_cards])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows, font_size=9)
