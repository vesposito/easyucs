# coding: utf-8
# !/usr/bin/env python

""" chassis.py: Easy UCS Deployment Tool """

from report.content import *
from report.generic.inventory.psu import UcsPsuReportSection
from report.generic.inventory.storage import (
    UcsDiskReportTable,
    UcsNvmeDrivesReportSection,
    UcsStorageControllerReportSection
)
from report.ucs.section import UcsReportSection
from report.ucs.table import UcsReportTable


class UcsChassisInventoryReportSection(UcsReportSection):
    def __init__(self, order_id, parent, domain, title=""):
        if not title:
            title = "Chassis Inventory"
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if domain.chassis:
            descr = ""  # TODO
            self.content_list.append(
                GenericReportText(order_id=self.report.get_current_order_id(), parent=self, string=descr)
            )
        blade_list = []
        for chassis in domain.chassis:
            chassis_name = str(chassis.id)
            if chassis.user_label:
                chassis_name = str(chassis.id) + " - " + chassis.user_label
            self.content_list.append(UcsChassisReportSection(
                order_id=self.report.get_current_order_id(), parent=self, chassis=chassis,
                title="Chassis " + chassis_name)
            )
            if chassis.blades:
                blade_list += chassis.blades
            if chassis.pcie_nodes:
                blade_list += chassis.pcie_nodes

        if blade_list:
            self.content_list.append(UcsBladesSummaryReportSection(
                order_id=self.report.get_current_order_id(), parent=self, blades=blade_list)
            )


class UcsChassisReportSection(UcsReportSection):
    def __init__(self, order_id, parent, chassis, title):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        descr = ""  # TODO
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self, string=descr))

        if chassis.__class__.__name__ in ["IntersightChassis"]:
            path_front = self.report.img_path + chassis._parent.name + "_chassis_" + str(chassis.id) + "_front.png"
        else:
            path_front = self.report.img_path + "chassis_" + str(chassis.id) + "_front.png"
        self.content_list.append(
            GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path_front,
                               centered=True, spacing_after=2))
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                              string="Front View", centered=True, italicized=True, font_size=8))

        if chassis.__class__.__name__ in ["IntersightChassis"]:
            path_rear = self.report.img_path + chassis._parent.name + "_chassis_" + str(chassis.id) + "_rear_clear.png"
        else:
            path_rear = self.report.img_path + "chassis_" + str(chassis.id) + "_rear_clear.png"
        self.content_list.append(
            GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path_rear,
                               centered=True, spacing_after=2))
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                              string="Rear View", centered=True, italicized=True, font_size=8))
        self.content_list.append(
            UcsChassisReportTable(order_id=self.report.get_current_order_id(), parent=self, chassis=chassis,
                                  centered=True))

        if chassis.io_modules:
            self.content_list.append(UcsIomReportSection(
                order_id=self.report.get_current_order_id(), parent=self, chassis=chassis, title="IO Modules"))
        if chassis.power_supplies:
            self.content_list.append(UcsPsuReportSection(
                order_id=self.report.get_current_order_id(), parent=self, device=chassis, title="Power Supplies"))

        if hasattr(chassis, "storage_enclosures") and chassis.storage_enclosures:
            self.content_list.append(UcsStorageEnclosuresReportSection(
                order_id=self.report.get_current_order_id(), parent=self, chassis=chassis, title="Storage Enclosures"))

        if chassis.blades:
            self.content_list.append(
                UcsBladesReportSection(
                    order_id=self.report.get_current_order_id(), parent=self, chassis=chassis, title="Blade Servers"))


class UcsChassisReportTable(UcsReportTable):
    def __init__(self, order_id, parent, chassis, centered=False):
        rows = [
            ["Description", "Value"],
            ["Chassis ID", chassis.id],
            ["SKU", chassis.sku],
            ["Model", chassis.name],
            ["Serial Number", chassis.serial],
            ["Slots Used/Total", str(chassis.slots_populated) + "/" + str(chassis.slots_max)],
            ["Slots Free (full-size)", chassis.slots_free_full],
            ["Slots Free (half-size)", chassis.slots_free_half]
        ]

        if chassis.io_modules:
            io_dict = {}
            for io_module in chassis.io_modules:
                key = self.get_name_and_sku(io_module)
                if key in io_dict:
                    io_dict[key] += 1
                else:
                    io_dict.update({key: 1})
            io_modules_models = "\n".join([(str(i[1]) + "x " + str(i[0])) for i in io_dict.items()])
            rows.append(["IO Modules", io_modules_models])

        if hasattr(chassis, "system_io_controllers") and chassis.system_io_controllers:
            sioc_dict = {}
            for sioc_controller in chassis.system_io_controllers:
                key = self.get_name_and_sku(sioc_controller)
                if key in sioc_dict:
                    sioc_dict[key] += 1
                else:
                    sioc_dict.update({key: 1})
            sioc_models = "\n".join([(str(i[1]) + "x " + str(i[0])) for i in sioc_dict.items()])
            rows.append(["SIOCs", sioc_models])

        if chassis.power_supplies:
            psu_dict = {}
            for psu in chassis.power_supplies:
                key = self.get_name_and_sku(psu)
                if key in psu_dict:
                    psu_dict[key] += 1
                else:
                    psu_dict.update({key: 1})
            psu_models = "\n".join([(str(i[1]) + "x " + str(i[0])) for i in psu_dict.items()])
            rows.append(["Power Supplies", psu_models])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows)


class UcsIomReportSection(UcsReportSection):
    def __init__(self, order_id, parent, chassis, title):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if self.report.size == "full":
            self.content_list.append(
                UcsIomReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                  iom=chassis.io_modules, centered=True))


class UcsIomReportTable(UcsReportTable):
    def __init__(self, order_id, parent, iom, centered=False):
        rows = [["ID", "SKU", "Model", "Serial Number", "Firmware", "Fabric ports used"]]

        for iom_unit in iom:
            firmware_version = "N/A"
            if parent.report.device.metadata.device_type == "intersight":
                firmware_version = iom_unit.firmware_version
            elif parent.report.device.metadata.device_type in ["ucsc", "ucsm"]:
                firmware_version = iom_unit.firmware_package_version
            rows.append([iom_unit.id, iom_unit.sku, iom_unit.name, iom_unit.serial, firmware_version,
                         len(iom_unit.ports)])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows)


class UcsStorageEnclosuresReportSection(UcsReportSection):
    def __init__(self, order_id, parent, chassis, title):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if self.report.size == "full":
            for storage_enclosure in chassis.storage_enclosures:
                storage_enclosure_name = storage_enclosure.descr + " (" + storage_enclosure.num_slots + " slots)"
                self.content_list.append(
                    UcsStorageEnclosureReportSection(
                        order_id=self.report.get_current_order_id(), parent=self, storage_enclosure=storage_enclosure,
                        title=storage_enclosure_name)
                )


class UcsStorageEnclosureReportSection(UcsReportSection):
    def __init__(self, order_id, parent, storage_enclosure, title):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if self.report.size == "full":
            if storage_enclosure.disks:
                self.content_list.append(
                    UcsDiskReportTable(
                        order_id=self.report.get_current_order_id(), parent=self, disks=storage_enclosure.disks,
                        centered=True)
                )


class UcsBladesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, chassis, title):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if self.report.size == "full":
            self.content_list.append(
                UcsBladesSummaryReportTable(
                    order_id=self.report.get_current_order_id(), parent=self,
                    blades=chassis.blades + chassis.pcie_nodes, centered=True))

            for blade in chassis.blades:
                blade_name = blade.id + " details"
                if blade.user_label:
                    blade_name = blade.id + " details - " + blade.user_label
                self.content_list.append(UcsBladeReportSection(
                    order_id=self.report.get_current_order_id(), parent=self, blade=blade,
                    title="Blade Server " + blade_name)
                )

            for pcie_node in chassis.pcie_nodes:
                pcie_node_name = pcie_node.id + " details"
                self.content_list.append(UcsPcieNodeReportSection(
                    order_id=self.report.get_current_order_id(), parent=self, pcie_node=pcie_node,
                    title="PCIe Node " + pcie_node_name)
                )


class UcsBladesSummaryReportSection(UcsReportSection):
    def __init__(self, order_id, parent, blades, title=""):
        if not title:
            title = "Blade Servers Summary"
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            UcsBladesSummaryReportTable(order_id=self.report.get_current_order_id(), parent=self, blades=blades,
                                        centered=True))


class UcsBladesSummaryReportTable(UcsReportTable):
    def __init__(self, order_id, parent, blades, centered=False):
        rows = [["ID", "Model", "Serial Number", "RAM", "CPUs", "Cores", "Adapters", "GPUs", "Drives", "SD Cards"]]

        for blade in blades:
            cores = ""
            if hasattr(blade, "cpus") and blade.cpus:
                if blade.cpus[0].cores:
                    cores = int(blade.cpus[0].cores)
                    if len(blade.cpus) > 1:
                        cores = int(blade.cpus[0].cores) * len(blade.cpus)

            adaptor_sum = 0
            adaptor_models = ""  # If all adaptors have the same model, we write it down
            if hasattr(blade, "adaptors") and blade.adaptors:
                adaptor_sum = len(blade.adaptors)
                if type(adaptor_models) == str:
                    adaptor_models = blade.adaptors[0].short_name
                if adaptor_models:
                    # We treat VIC + Port Expander in a specific fashion to display "1x VIC 1340+PE"
                    if adaptor_sum == 2 and blade.adaptors[1].sku == "UCSB-MLOM-PT-01":
                        adaptor_sum = 1
                        adaptor_models = adaptor_models + "+PE"
                    else:
                        for adaptor in blade.adaptors:
                            if adaptor.short_name != adaptor_models:
                                adaptor_models = None
            if adaptor_models and adaptor_sum:
                adaptor_sum = str(adaptor_sum) + "x " + adaptor_models

            drives = 0
            drives_capacity = ""  # If all drives have the same capacity, we write it down
            if hasattr(blade, "storage_controllers"):
                for storage_controller in blade.storage_controllers:
                    if storage_controller.disks:
                        drives += len(storage_controller.disks)
                        if type(drives_capacity) == str:
                            if not drives_capacity:
                                drives_capacity = storage_controller.disks[0].size_marketing
                        if drives_capacity:
                            for disk in storage_controller.disks:
                                if disk.size_marketing != drives_capacity:
                                    drives_capacity = None
            if hasattr(blade, "nvme_drives") and blade.nvme_drives:
                drives += len(blade.nvme_drives)
                if type(drives_capacity) == str and not drives_capacity:
                    drives_capacity = blade.nvme_drives[0].size_marketing
                if drives_capacity:
                    for disk in blade.nvme_drives:
                        if disk.size_marketing != drives_capacity:
                            drives_capacity = None
            if drives_capacity and drives:
                drives = str(drives) + "x " + drives_capacity

            sd_cards = 0
            sd_cards_capacity = ""   # If all SD cards have the same capacity, we write it down
            if hasattr(blade, "storage_flexflash_controllers"):
                for storage_flexflash_controller in blade.storage_flexflash_controllers:
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

            if hasattr(blade, "cpus") and blade.cpus:
                if blade.cpus[0].model_short_name:
                    rows.append([blade.id, blade.short_name, blade.serial, blade.memory_total_marketing,
                                 str(len(blade.cpus)) + "x " + blade.cpus[0].model_short_name, cores, adaptor_sum,
                                 len(blade.gpus), drives, sd_cards])
                else:
                    rows.append([blade.id, blade.short_name, blade.serial, blade.memory_total_marketing,
                                 str(len(blade.cpus)), cores, adaptor_sum, len(blade.gpus), drives, sd_cards])
            elif "PcieNode" in blade.__class__.__name__:
                # PCIe Node
                rows.append([blade.id, blade.short_name, blade.serial, None, None, None, None, len(blade.gpus), None, None])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows, font_size=9)


class UcsBladeReportSection(UcsReportSection):
    def __init__(self, order_id, parent, blade, title):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if self.report.size == "full":
            self.content_list.append(
                UcsBladeReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                    blade=blade, centered=True))

            if blade.storage_controllers:
                for storage_controller in blade.storage_controllers:
                    key = UcsReportTable.get_name_and_sku(storage_controller)
                    self.content_list.append(
                        UcsStorageControllerReportSection(
                            order_id=self.report.get_current_order_id(), parent=self,
                            title="Storage Controller " + storage_controller.id + ' - ' + key,
                            device=storage_controller)
                    )

            if blade.nvme_drives:
                self.content_list.append(
                    UcsNvmeDrivesReportSection(
                        order_id=self.report.get_current_order_id(), parent=self, title="NVMe Drives", device=blade))


class UcsBladeReportTable(UcsReportTable):
    def __init__(self, order_id, parent, blade, centered=False):
        firmware_version = "N/A"
        if parent.report.device.metadata.device_type == "intersight":
            firmware_version = blade.firmware_version
        elif parent.report.device.metadata.device_type in ["ucsc", "ucsm"]:
            firmware_version = blade.firmware_package_version
        rows = [
            ["Description", "Value"],
            ["Blade ID", blade.id],
            ["SKU", blade.sku],
            ["Model", blade.name],
            ["Serial Number", blade.serial],
            ["Firmware", firmware_version]
        ]

        if blade.memory_arrays:
            memory_dict = {}
            for array in blade.memory_arrays:
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
            rows.append(["Memory", str(blade.memory_total_marketing) + "\n" + memory_info])

        if blade.adaptors:
            adaptor_dict = {}
            for adaptor in blade.adaptors:
                key = self.get_name_and_sku(adaptor)
                if key in adaptor_dict:
                    adaptor_dict[key] += 1
                else:
                    adaptor_dict.update({key: 1})
            adaptor_models = "\n".join([(str(i[1]) + "x " + str(i[0])) for i in adaptor_dict.items()])
            rows.append(["Adaptors", adaptor_models])

        if blade.cpus:
            cores = 0
            cpu_dict = {}

            for cpu in blade.cpus:
                key = self.get_name_and_sku(cpu)
                if key in cpu_dict:
                    cpu_dict[key] += 1
                else:
                    cpu_dict.update({key: 1})
                if cpu.cores:
                    cores += int(cpu.cores)

            if cores:
                if blade.cpus[0].speed:
                    speed = round(blade.cpus[0].speed / 1000, 2)
                    cores = str(cores) + " @ " + str(speed) + "GHz"

            cpu_model = "\n".join([(str(i[1]) + "x " + str(i[0])) for i in cpu_dict.items()])
            rows.append(["CPUs", cpu_model])
            rows.append(["Cores", cores])

        if blade.gpus:
            gpu_dict = {}
            for gpu in blade.gpus:
                key = self.get_name_and_sku(gpu)
                if key in gpu_dict:
                    gpu_dict[key] += 1
                else:
                    gpu_dict.update({key: 1})
            gpu_models = "\n".join([(str(i[1]) + "x " + str(i[0])) for i in gpu_dict.items()])
            rows.append(["GPUs", gpu_models])

        if blade.storage_controllers:
            storage_dict = {}
            drives_dict = {}
            for controller in blade.storage_controllers:
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

            for drive in blade.nvme_drives:
                key_drive = self.get_name_and_sku(drive)
                if key_drive in drives_dict:
                    drives_dict[key_drive] += 1
                else:
                    drives_dict.update({key_drive: 1})

            storage = "\n".join([(str(i[1]) + "x " + str(i[0])) for i in storage_dict.items()])
            drives = "\n".join([(str(i[1]) + "x " + str(i[0])) for i in drives_dict.items()])
            rows.append(["Storage Controllers", storage])
            rows.append(["Drives", drives])

        if hasattr(blade, "storage_flexflash_controllers") and blade.storage_flexflash_controllers:
            flash_dict = {}
            for controller in blade.storage_flexflash_controllers:
                for card in controller.flexflash_cards:
                    if card.capacity_marketing in flash_dict:
                        flash_dict[card.capacity_marketing] += 1
                    else:
                        flash_dict.update({card.capacity_marketing: 1})
            flash_cards = "\n".join([(str(i[1]) + "x " + str(i[0])) for i in flash_dict.items()])
            rows.append(["FlexFlash SD Cards", flash_cards])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows)


class UcsPcieNodeReportSection(UcsReportSection):
    def __init__(self, order_id, parent, pcie_node, title):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if self.report.size == "full":
            self.content_list.append(
                UcsPcieNodeReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                       pcie_node=pcie_node, centered=True))


class UcsPcieNodeReportTable(UcsReportTable):
    def __init__(self, order_id, parent, pcie_node, centered=False):
        rows = [
            ["Description", "Value"],
            ["PCIe Node ID", pcie_node.id],
            ["SKU", pcie_node.sku],
            ["Serial Number", pcie_node.serial]
        ]

        if pcie_node.gpus:
            gpu_dict = {}
            for gpu in pcie_node.gpus:
                key = self.get_name_and_sku(gpu)
                if key in gpu_dict:
                    gpu_dict[key] += 1
                else:
                    gpu_dict.update({key: 1})
            gpu_models = "\n".join([(str(i[1]) + "x " + str(i[0])) for i in gpu_dict.items()])
            rows.append(["GPUs", gpu_models])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows)
