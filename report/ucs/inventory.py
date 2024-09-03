# coding: utf-8
# !/usr/bin/env python

""" inventory.py: Easy UCS Deployment Tool """

import json
import os.path
from pathlib import Path

from PIL import Image

from draw.object import GenericDrawObject
from report.content import *
from report.ucs.section import UcsReportSection
from report.ucs.table import UcsReportTable


class UcsSystemInventoryReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Equipment Inventory")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        descr = _("This section details the inventory: FIs, FEXs, rack Servers, chassis and their components.")
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self, string=descr))
        self.content_list.append(UcsSystemFabricInventoryReportSection(self.report.get_current_order_id(), parent=self))
        self.content_list.append(UcsChassisInventoryReportSection(self.report.get_current_order_id(), parent=self))
        self.content_list.append(UcsRacksInventoryReportSection(self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            UcsRackEnclosuresInventoryReportSection(self.report.get_current_order_id(), parent=self))
        # self.content_list.append(RecapUcsReportSection(self.report.get_current_order_id(), parent=self))


class UcsImcInventoryReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Equipment Inventory")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        descr = _("This section details the inventory.")
        self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                   string=descr))
        self.content_list.append(UcsRacksInventoryReportSection(self.report.get_current_order_id(), parent=self))
        # self.content_list.append(RecapUcsImcReportSection(self.report.get_current_order_id(), parent=self))


class UcsSystemFabricInventoryReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Fabric Inventory")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        if self.report.inventory.fabric_interconnects or self.report.inventory.fabric_extenders:
            descr = _("The Fabric inventory gives information about the ") + \
                    str(len(self.report.inventory.fabric_interconnects)) + \
                    _(" FIs, ") + str(len(self.report.inventory.fabric_extenders)) + \
                    _(" FEXs, PSUs and Expansion Modules.")
            self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                       string=descr))
        for fi in self.report.inventory.fabric_interconnects:
            self.content_list.append(UcsSystemFiReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                              title="Fabric Interconnect " + fi.id, fi=fi))

        for fex in self.report.inventory.fabric_extenders:
            self.content_list.append(UcsSystemFexReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                               title="Fabric Extender " + fex.id, fex=fex))


class UcsSystemFiReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title, fi):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        descr = _("The FI ") + fi.id + " (" + fi.model + _(") has ") + str(len(fi.expansion_modules)) + \
                _(" expansion modules and ") + str(len(fi.power_supplies)) + _(" power supplies.")
        self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                   string=descr))
        if fi.model in ["UCS-FI-M-6324", "UCSX-S9108-100G"]:
            # UCS Mini/X-Direct FI only has a rear picture
            path_rear = self.report.img_path + "fi_" + fi.id + "_rear_clear.png"
            if os.path.exists(path_rear):
                if fi.model in ["UCS-FI-M-6324"]:
                    # rotate and create a horizontal picture of the FI from UCS Mini
                    image = Image.open(path_rear).rotate(90, expand=True)
                    path_rear = self.report.img_path + "fi_" + fi.id + "_rear_clear_horizontal.png"
                    image.save(path_rear)
            self.content_list.append(
                GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path_rear,
                                   centered=True, spacing_after=2))
            self.content_list.append(
                GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                  string=(_("Rear View")), centered=True, italicized=True, font_size=8))

        else:
            path_front = self.report.img_path + "fi_" + fi.id + "_front.png"
            self.content_list.append(
                GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path_front,
                                   centered=True, spacing_after=2))
            self.content_list.append(
                GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                  string=(_("Front View")), centered=True, italicized=True, font_size=8))

            path_rear = self.report.img_path + "fi_" + fi.id + "_rear_clear.png"
            self.content_list.append(
                GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path_rear,
                                   centered=True, spacing_after=2))
            self.content_list.append(
                GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                  string=(_("Rear View")), centered=True, italicized=True, font_size=8))
        self.content_list.append(
            UcsSystemFiReportTable(order_id=self.report.get_current_order_id(), parent=self, fi=fi, centered=True))

        if fi.power_supplies:
            self.content_list.append(UcsPsuReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                         title=_("Power Supplies"), device=fi))

        if fi.expansion_modules:
            self.content_list.append(UcsSystemGemReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                               title=_("Expansion Modules"), fi=fi))

        if fi.licenses:
            self.content_list.append(UcsSystemLicensesReportSection(order_id=self.report.get_current_order_id(),
                                                                    parent=self, title=_("Port Licenses"), fi=fi))

        if fi.vlan_port_count:
            self.content_list.append(
                UcsSystemVlanPortCountReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                    title=_("VLAN Port Count"), fi=fi))


class UcsSystemFiReportTable(UcsReportTable):
    def __init__(self, order_id, parent, fi, centered=False):
        rows = [[_("Description"), _("Value")], [_("Fabric"), fi.id], [_("SKU"), fi.sku], [_("Model"), fi.name],
                [_("Serial Number"), fi.serial], [_("Firmware"), fi.firmware_package_version]]

        # We have to get the JSON file of the device to get information about the ports
        # We use a DrawingObject because they already have a method to get the JSON file efficiently
        draw = GenericDrawObject(parent=fi)
        draw._get_json_file()
        rear_ports = None
        if draw.json_file:
            if "rear_ports" in draw.json_file:
                rear_ports = draw.json_file['rear_ports']
        if rear_ports:
            port_dict = {}
            for port in rear_ports.items():
                if port[1]['port_type'] in port_dict:
                    port_dict[port[1]['port_type']] += 1
                else:
                    port_dict.update({port[1]['port_type']: 1})
            port_info = "\n".join([(str(i[1]) + "x " + str(i[0]).upper()) for i in port_dict.items()])
            rows.append([_("Ports"), port_info])

        if fi.power_supplies:
            psu_dict = {}
            for psu in fi.power_supplies:
                key = self.get_name_and_sku(psu)
                if key in psu_dict:
                    psu_dict[key] += 1
                else:
                    psu_dict.update({key: 1})
            psu_models = "\n".join([(str(i[1]) + "x " + str(i[0])) for i in psu_dict.items()])
            rows.append([_("Power Supplies"), psu_models])

        if fi.expansion_modules:
            expansion_dict = {}
            for expansion in fi.expansion_modules:
                key = self.get_name_and_sku(expansion)
                if key in expansion_dict:
                    expansion_dict[key] += 1
                else:
                    expansion_dict.update({key: 1})
            gem_models = "\n".join([(str(i[1]) + "x " + str(i[0])) for i in expansion_dict.items()])
            rows.append([_("Expansion Modules"), gem_models])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows)


class UcsSystemGemReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title, fi):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if self.report.size == "full":
            self.content_list.append(
                UcsSystemGemReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                        gem=fi.expansion_modules, centered=True))


class UcsSystemGemReportTable(UcsReportTable):
    def __init__(self, order_id, parent, gem, centered=False):
        rows = [[_("ID"), _("SKU"), _("Model"), _("Serial Number")]]

        for expansion_module in gem:
            rows.append([expansion_module.id, expansion_module.sku, expansion_module.name, expansion_module.serial])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows)


class UcsSystemLicensesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title, fi):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if self.report.size == "full":
            self.content_list.append(
                UcsSystemLicensesReportTable(order_id=self.report.get_current_order_id(), parent=self, fi=fi,
                                             centered=True))


class UcsSystemLicensesReportTable(UcsReportTable):
    def __init__(self, order_id, parent, fi, centered=False):
        rows = [[_("SKU"), _("Total"), _("Default"), _("Used"), _("Available"), _("Status"),
                 _("Grace Period Used (days)")]]

        for lic in fi.licenses:
            rows.append([lic["sku"], lic["quantity"], lic["quantity_default"], lic["quantity_used"],
                         lic["quantity_available"], lic["status"], lic["grace_period_used_days"]])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows)


class UcsSystemVlanPortCountReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title, fi):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if self.report.size == "full":
            self.content_list.append(
                UcsSystemVlanPortCountReportTable(order_id=self.report.get_current_order_id(), parent=self, fi=fi,
                                                  centered=True))


class UcsSystemVlanPortCountReportTable(UcsReportTable):
    def __init__(self, order_id, parent, fi, centered=False):
        rows = [[_("Actual Limit"), _("VLAN Compression State"), _("Max Limit"), _("Total VLAN Port Count"),
                 _("Access VLAN Port Count"), _("Border VLAN Port Count"), _("Usage (%)")]]

        port_count = fi.vlan_port_count
        rows.append([port_count["limit"], port_count["vlan_compression_state"], port_count["limit_with_compression"],
                     port_count["total_vlan_port_count"], port_count["access_vlan_port_count"],
                     port_count["border_vlan_port_count"], port_count["usage_percent"]])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows)


class UcsSystemFexReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title, fex):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        descr = _("The FEX ") + fex.id + " (" + fex.model + _(") has ") + str(len(fex.power_supplies)) + \
                _(" power supplies.")
        self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                   string=descr))

        path_front = self.report.img_path + "fex_" + fex.id + "_front.png"
        self.content_list.append(
            GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path_front,
                               centered=True, spacing_after=2))
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                              string=(_("Front View")), centered=True, italicized=True, font_size=8))

        path_rear = self.report.img_path + "fex_" + fex.id + "_rear_clear.png"
        self.content_list.append(
            GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path_rear,
                               centered=True, spacing_after=2))
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                              string=(_("Rear View")), centered=True, italicized=True, font_size=8))
        self.content_list.append(
            UcsSystemFexReportTable(order_id=self.report.get_current_order_id(), parent=self, fex=fex, centered=True))

        if fex.power_supplies:
            self.content_list.append(UcsPsuReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                         title=_("Power Supplies"), device=fex))


class UcsSystemFexReportTable(UcsReportTable):
    def __init__(self, order_id, parent, fex, centered=False):
        rows = [[_("Description"), _("Value")], [_("FEX"), fex.id], [_("Fabric"), fex.switch_id], [_("SKU"), fex.sku],
                [_("Model"), fex.name], [_("Serial Number"), fex.serial]]

        # We have to get the JSON file of the device to get information about the ports
        # We use a DrawingObject because they already have a method to get the JSON file efficiently
        draw = GenericDrawObject(parent=fex)
        draw._get_json_file()
        rear_ports = None
        if draw.json_file:
            if "rear_ports" in draw.json_file:
                rear_ports = draw.json_file['rear_ports']
        if rear_ports:
            port_dict = {}
            for port in rear_ports.items():
                if port[1]['port_type'] in port_dict:
                    port_dict[port[1]['port_type']] += 1
                else:
                    port_dict.update({port[1]['port_type']: 1})
            port_info = "\n".join([(str(i[1]) + "x " + str(i[0]).upper()) for i in port_dict.items()])
            rows.append([_("Ports"), port_info])

        if fex.power_supplies:
            psu_dict = {}
            for psu in fex.power_supplies:
                key = self.get_name_and_sku(psu)
                if key in psu_dict:
                    psu_dict[key] += 1
                else:
                    psu_dict.update({key: 1})
            psu_models = "\n".join([(str(i[1]) + "x " + str(i[0])) for i in psu_dict.items()])
            rows.append([_("Power Supplies"), psu_models])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows)


class UcsChassisInventoryReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Chassis Inventory")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if self.report.inventory.chassis:
            descr = ""  # TODO
            self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                       string=descr))
        blade_list = []
        for chassis in self.report.inventory.chassis:
            chassis_name = chassis.id
            if chassis.user_label:
                chassis_name = chassis.id + " - " + chassis.user_label
            self.content_list.append(UcsChassisReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                             title=_("Chassis ") + chassis_name, chassis=chassis))
            if chassis.blades:
                blade_list = blade_list + chassis.blades

        if blade_list:
            self.content_list.append(
                UcsBladesSummaryReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                              title=_("Blade Servers Summary"), blades=blade_list))


class UcsChassisReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title, chassis):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        descr = ""  # TODO
        self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                   string=descr))

        path_front = self.report.img_path + "chassis_" + chassis.id + "_front.png"
        self.content_list.append(
            GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path_front,
                               centered=True, spacing_after=2))
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                              string=(_("Front View")), centered=True, italicized=True, font_size=8))

        path_rear = self.report.img_path + "chassis_" + chassis.id + "_rear_clear.png"
        self.content_list.append(
            GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path_rear,
                               centered=True, spacing_after=2))
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                              string=(_("Rear View")), centered=True, italicized=True, font_size=8))
        self.content_list.append(
            UcsChassisReportTable(order_id=self.report.get_current_order_id(), parent=self, chassis=chassis,
                                  centered=True))

        if chassis.io_modules:
            self.content_list.append(UcsSystemIomReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                               title=_("IO Modules"), chassis=chassis))
        if chassis.power_supplies:
            self.content_list.append(UcsPsuReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                         title=_("Power Supplies"), device=chassis))

        if chassis.storage_enclosures:
            self.content_list.append(UcsStorageEnclosuresReportSection(order_id=self.report.get_current_order_id(),
                                                                       parent=self, title=_("Storage Enclosures"),
                                                                       chassis=chassis))

        if chassis.blades:
            self.content_list.append(
                UcsBladesReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                       title=_("Blade Servers"), chassis=chassis))


class UcsChassisReportTable(UcsReportTable):
    def __init__(self, order_id, parent, chassis, centered=False):
        rows = [[_("Description"), _("Value")], [_("Chassis ID"), chassis.id], [_("SKU"), chassis.sku],
                [_("Model"), chassis.name], [_("Serial Number"), chassis.serial],
                [_("Slots Used/Total"), str(chassis.slots_populated) + "/" + str(chassis.slots_max)],
                [_("Slots Free (full-size)"), chassis.slots_free_full],
                [_("Slots Free (half-size)"), chassis.slots_free_half]]

        if chassis.io_modules:
            io_dict = {}
            for io_module in chassis.io_modules:
                key = self.get_name_and_sku(io_module)
                if key in io_dict:
                    io_dict[key] += 1
                else:
                    io_dict.update({key: 1})
            io_modules_models = "\n".join([(str(i[1]) + "x " + str(i[0])) for i in io_dict.items()])
            rows.append([_("IO Modules"), io_modules_models])

        if chassis.system_io_controllers:
            sioc_dict = {}
            for sioc_controller in chassis.system_io_controllers:
                key = self.get_name_and_sku(sioc_controller)
                if key in sioc_dict:
                    sioc_dict[key] += 1
                else:
                    sioc_dict.update({key: 1})
            sioc_models = "\n".join([(str(i[1]) + "x " + str(i[0])) for i in sioc_dict.items()])
            rows.append([_("SIOCs"), sioc_models])

        if chassis.power_supplies:
            psu_dict = {}
            for psu in chassis.power_supplies:
                key = self.get_name_and_sku(psu)
                if key in psu_dict:
                    psu_dict[key] += 1
                else:
                    psu_dict.update({key: 1})
            psu_models = "\n".join([(str(i[1]) + "x " + str(i[0])) for i in psu_dict.items()])
            rows.append([_("Power Supplies"), psu_models])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows)


class UcsSystemIomReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title, chassis):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if self.report.size == "full":
            self.content_list.append(
                UcsSystemIomReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                        iom=chassis.io_modules, centered=True))


class UcsSystemIomReportTable(UcsReportTable):
    def __init__(self, order_id, parent, iom, centered=False):
        rows = [[_("ID"), _("SKU"), _("Model"), _("Serial Number"), _("Firmware"), _("Fabric ports used")]]

        for iom_unit in iom:
            rows.append([iom_unit.id, iom_unit.sku, iom_unit.name, iom_unit.serial, iom_unit.firmware_package_version,
                         len(iom_unit.ports)])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows)


class UcsStorageEnclosuresReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title, chassis):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if self.report.size == "full":
            for storage_enclosure in chassis.storage_enclosures:
                storage_enclosure_name = storage_enclosure.descr + " (" + storage_enclosure.num_slots + " slots)"
                self.content_list.append(
                    UcsStorageEnclosureReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                     title=storage_enclosure_name, storage_enclosure=storage_enclosure))


class UcsStorageEnclosureReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title, storage_enclosure):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if self.report.size == "full":
            if storage_enclosure.disks:
                self.content_list.append(
                    UcsDiskReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                       disks=storage_enclosure.disks, centered=True))


class UcsBladesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title, chassis):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if self.report.size == "full":
            self.content_list.append(
                UcsBladesSummaryReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                            blades=chassis.blades, centered=True))

            for blade in chassis.blades:
                blade_name = blade.id + " details"
                if blade.user_label:
                    blade_name = blade.id + " details - " + blade.user_label
                self.content_list.append(UcsBladeReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                               title=_("Blade Server ") + blade_name,
                                                               blade=blade))


class UcsBladesSummaryReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title, blades):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            UcsBladesSummaryReportTable(order_id=self.report.get_current_order_id(), parent=self, blades=blades,
                                        centered=True))


class UcsBladesSummaryReportTable(UcsReportTable):
    def __init__(self, order_id, parent, blades, centered=False):
        rows = [[_("ID"), _("Model"), _("Serial Number"), _("RAM"), _("CPUs"), _("Cores"), _("Adapters"), _("GPUs"),
                 _("Drives"), _("SD Cards")]]

        for blade in blades:
            cores = ""
            if blade.cpus:
                if blade.cpus[0].cores:
                    cores = int(blade.cpus[0].cores)
                    if len(blade.cpus) > 1:
                        cores = int(blade.cpus[0].cores) * len(blade.cpus)

            adaptor_sum = 0
            adaptor_models = ""  # If all adaptors have the same model, we write it down
            if blade.adaptors:
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
            if blade.nvme_drives:
                drives += len(blade.nvme_drives)
                if type(drives_capacity) == str:
                    drives_capacity = blade.nvme_drives[0].size_marketing
                if drives_capacity:
                    for disk in blade.nvme_drives:
                        if disk.size_marketing != drives_capacity:
                            drives_capacity = None
            if drives_capacity and drives:
                drives = str(drives) + "x " + drives_capacity

            sd_cards = 0
            sd_cards_capacity = ""   # If all SD cards have the same capacity, we write it down
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

            if blade.cpus:
                if blade.cpus[0].model_short_name:
                    rows.append([blade.id, blade.short_name, blade.serial, blade.memory_total_marketing,
                                 str(len(blade.cpus)) + "x " + blade.cpus[0].model_short_name, cores, adaptor_sum,
                                 len(blade.gpus), drives, sd_cards])
                else:
                    rows.append([blade.id, blade.short_name, blade.serial, blade.memory_total_marketing,
                                 str(len(blade.cpus)), cores, adaptor_sum, len(blade.gpus), drives, sd_cards])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows, font_size=9)


class UcsBladeReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title, blade):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if self.report.size == "full":
            self.content_list.append(
                UcsBladeReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                    blade=blade, centered=True))

            if blade.storage_controllers:
                for storage_controller in blade.storage_controllers:
                    key = UcsReportTable.get_name_and_sku(storage_controller)
                    self.content_list.append(
                        UcsStorageControllerReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                          title=_("Storage Controller ") + storage_controller.id +
                                                                ' - ' + key, device=storage_controller))

            if blade.nvme_drives:
                self.content_list.append(
                    UcsNvmeDrivesReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                               title=_("NVMe Drives"), device=blade))


class UcsBladeReportTable(UcsReportTable):
    def __init__(self, order_id, parent, blade, centered=False):
        rows = [[_("Description"), _("Value")], [_("Blade ID"), blade.id], [_("SKU"), blade.sku],
                [_("Model"), blade.name], [_("Serial Number"), blade.serial],
                [_("Firmware Package"), blade.firmware_package_version]]

        memory_info = ""
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
            rows.append([_("Memory"), str(blade.memory_total_marketing) + "\n" + memory_info])

        if blade.adaptors:
            adaptor_dict = {}
            for adaptor in blade.adaptors:
                key = self.get_name_and_sku(adaptor)
                if key in adaptor_dict:
                    adaptor_dict[key] += 1
                else:
                    adaptor_dict.update({key: 1})
            adaptor_models = "\n".join([(str(i[1]) + "x " + str(i[0])) for i in adaptor_dict.items()])
            rows.append([_("Adaptors"), adaptor_models])

        cpu_model = ""
        cores = 0
        if blade.cpus:
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

        rows.append([_("CPUs"), cpu_model])
        rows.append([_("Cores"), cores])

        gpu_models = ""
        if blade.gpus:
            gpu_dict = {}
            for gpu in blade.gpus:
                key = self.get_name_and_sku(gpu)
                if key in gpu_dict:
                    gpu_dict[key] += 1
                else:
                    gpu_dict.update({key: 1})
            gpu_models = "\n".join([(str(i[1]) + "x " + str(i[0])) for i in gpu_dict.items()])
            rows.append([_("GPUs"), gpu_models])

        storage = ""
        drives = ""
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
        rows.append([_("Storage Controllers"), storage])
        rows.append([_("Drives"), drives])

        flash_cards = ""
        if blade.storage_flexflash_controllers:
            flash_dict = {}
            for controller in blade.storage_flexflash_controllers:
                for card in controller.flexflash_cards:
                    if card.capacity_marketing in flash_dict:
                        flash_dict[card.capacity_marketing] += 1
                    else:
                        flash_dict.update({card.capacity_marketing: 1})
            flash_cards = "\n".join([(str(i[1]) + "x " + str(i[0])) for i in flash_dict.items()])
        rows.append([_("FlexFlash SD Cards"), flash_cards])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows)


class UcsRacksInventoryReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Rack Servers Inventory")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        if self.report.inventory.rack_units:
            descr = ""  # TODO
            self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                       string=descr))
        for rack in self.report.inventory.rack_units:
            rack_name = rack.id
            if rack.user_label:
                rack_name = rack.id + " - " + rack.user_label
            self.content_list.append(UcsRackReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                          title=_("Rack ") + rack_name, rack=rack))

        if self.report.device.metadata.device_type == "ucsm":
            if self.report.inventory.rack_units:
                self.content_list.append(
                    UcsRacksSummaryReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                 title=_("Rack Servers Summary"),
                                                 rack_units=self.report.inventory.rack_units))


class UcsRackReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title, rack):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        descr = ""  # TODO
        self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                   string=descr))

        path_front = self.report.img_path + "rack_" + rack.id + "_front.png"
        path_rear = self.report.img_path + "rack_" + rack.id + "_rear_clear.png"
        if self.report.device.metadata.device_type == "cimc":
            path_front = self.report.img_path + "rack_front.png"
            path_rear = self.report.img_path + "rack_rear.png"

        self.content_list.append(
            GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path_front,
                               centered=True, spacing_after=2))
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                              string=(_("Front View")), centered=True, italicized=True, font_size=8))

        self.content_list.append(
            GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path_rear,
                               centered=True, spacing_after=2))
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                              string=(_("Rear View")), centered=True, italicized=True, font_size=8))

        if self.report.size == "full":
            self.content_list.append(
                UcsRackReportTable(order_id=self.report.get_current_order_id(), parent=self, rack=rack, centered=True))

        if rack.power_supplies:
            self.content_list.append(UcsPsuReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                         title=_("Power Supplies"), device=rack))
        if rack.storage_controllers:
            for storage_controller in rack.storage_controllers:
                key = UcsReportTable.get_name_and_sku(storage_controller)
                self.content_list.append(
                    UcsStorageControllerReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                      title=_("Storage Controller ") + storage_controller.id + ' - ' +
                                                            key, device=storage_controller))
        if rack.nvme_drives:
            self.content_list.append(
                UcsNvmeDrivesReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                           title=_("NVMe Drives"), device=rack))


class UcsRackReportTable(UcsReportTable):
    def __init__(self, order_id, parent, rack, centered=False):
        rows = [[_("Description"), _("Value")], [_("Rack ID"), rack.id], [_("SKU"), rack.sku], [_("Model"), rack.name],
                [_("Serial Number"), rack.serial]]

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
        rows.append([_("Memory"), str(rack.memory_total_marketing) + "\n" + memory_info])

        if rack.adaptors:
            adaptor_dict = {}
            for adaptor in rack.adaptors:
                key = self.get_name_and_sku(adaptor)
                if key in adaptor_dict:
                    adaptor_dict[key] += 1
                else:
                    adaptor_dict.update({key: 1})
            adaptor_models = "\n".join([(str(i[1]) + "x " + str(i[0])) for i in adaptor_dict.items()])
            rows.append([_("Adaptors"), adaptor_models])

        cpu_model = ""
        cores = 0
        if rack.cpus:
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

        rows.append([_("CPUs"), cpu_model])
        rows.append([_("Cores"), cores])

        gpu_models = ""
        if rack.gpus:
            gpu_dict = {}
            for gpu in rack.gpus:
                key = self.get_name_and_sku(gpu)
                if key in gpu_dict:
                    gpu_dict[key] += 1
                else:
                    gpu_dict.update({key: 1})
            gpu_models = "\n".join([(str(i[1]) + "x " + str(i[0])) for i in gpu_dict.items()])
            rows.append([_("GPUs"), gpu_models])

        storage = ""
        drives = ""
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
        rows.append([_("Storage Controllers"), storage])
        rows.append([_("Drives"), drives])

        flash_cards = ""
        if rack.storage_flexflash_controllers:
            flash_dict = {}
            for controller in rack.storage_flexflash_controllers:
                for card in controller.flexflash_cards:
                    if card.capacity_marketing in flash_dict:
                        flash_dict[card.capacity_marketing] += 1
                    else:
                        flash_dict.update({card.capacity_marketing: 1})
            flash_cards = "\n".join([(str(i[1]) + "x " + str(i[0])) for i in flash_dict.items()])
        rows.append([_("FlexFlash SD Cards"), flash_cards])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows)


class UcsRacksSummaryReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title, rack_units):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            UcsRacksSummaryReportTable(order_id=self.report.get_current_order_id(), parent=self, rack_units=rack_units,
                                       centered=True))


class UcsRacksSummaryReportTable(UcsReportTable):
    def __init__(self, order_id, parent, rack_units, centered=False):
        rows = [[_("ID"), _("Model"), _("Serial Number"), _("RAM"), _("CPUs"), _("Cores"), _("Adapters"), _("GPUs"),
                 _("Drives"), _("SD Cards")]]

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
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Rack Enclosures Inventory")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        if self.report.inventory.rack_enclosures:
            descr = ""  # TODO
            self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                       string=descr))
        server_node_list = []
        for rack_enclosure in self.report.inventory.rack_enclosures:
            rack_enclosure_name = rack_enclosure.id
            self.content_list.append(
                UcsRackEnclosureReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                              title=_("Rack Enclosure ") + rack_enclosure_name,
                                              rack_enclosure=rack_enclosure))
            if rack_enclosure.server_nodes:
                server_node_list = server_node_list + rack_enclosure.server_nodes

        if server_node_list:
            self.content_list.append(
                UcsServerNodesSummaryReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                   title=_("Server Nodes Servers Summary"),
                                                   server_nodes=server_node_list))


class UcsRackEnclosureReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title, rack_enclosure):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        descr = ""  # TODO
        self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                   string=descr))

        path_front = self.report.img_path + "rack_enclosure_" + rack_enclosure.id + "_front.png"
        self.content_list.append(
            GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path_front,
                               centered=True, spacing_after=2))
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                              string=(_("Front View")), centered=True, italicized=True, font_size=8))

        path_rear = self.report.img_path + "rack_enclosure_" + rack_enclosure.id + "_rear_clear.png"
        self.content_list.append(
            GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path_rear,
                               centered=True, spacing_after=2))
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                              string=(_("Rear View")), centered=True, italicized=True, font_size=8))
        self.content_list.append(
            UcsRackEnclosureReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                        rack_enclosure=rack_enclosure, centered=True))

        if rack_enclosure.power_supplies:
            self.content_list.append(UcsPsuReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                         title=_("Power Supplies"), device=rack_enclosure))

        if rack_enclosure.server_nodes:
            self.content_list.append(UcsServerNodesReportSection(order_id=self.report.get_current_order_id(),
                                                                 parent=self, title=_("Server Nodes"),
                                                                 rack_enclosure=rack_enclosure))


class UcsRackEnclosureReportTable(UcsReportTable):
    def __init__(self, order_id, parent, rack_enclosure, centered=False):
        rows = [[_("Description"), _("Value")], [_("Rack Enclosure ID"), rack_enclosure.id],
                [_("SKU"), rack_enclosure.sku], [_("Model"), rack_enclosure.name],
                [_("Serial Number"), rack_enclosure.serial]]
        # rows.append([_("Slots Used/Total"), str(rack_enclosure.slots_populated) + "/" + str(rack_enclosure.slots_max)])
        # rows.append([_("Slots Free (full-size)"), rack_enclosure.slots_free_full])
        # rows.append([_("Slots Free (half-size)"), rack_enclosure.slots_free_half])

        if rack_enclosure.power_supplies:
            psu_dict = {}
            for psu in rack_enclosure.power_supplies:
                key = self.get_name_and_sku(psu)
                if key in psu_dict:
                    psu_dict[key] += 1
                else:
                    psu_dict.update({key: 1})
            psu_models = "\n".join([(str(i[1]) + "x " + str(i[0])) for i in psu_dict.items()])
            rows.append([_("Power Supplies"), psu_models])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows)


class UcsServerNodesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title, rack_enclosure):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if self.report.size == "full":
            self.content_list.append(
                UcsServerNodesSummaryReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                                 server_nodes=rack_enclosure.server_nodes, centered=True))

            for server_node in rack_enclosure.server_nodes:
                server_node_name = server_node.id + " details"
                if server_node.user_label:
                    server_node_name = server_node.id + " details - " + server_node.user_label
                self.content_list.append(UcsServerNodeReportSection(order_id=self.report.get_current_order_id(),
                                                                    parent=self,
                                                                    title=_("Server Node ") + server_node_name,
                                                                    server_node=server_node))


class UcsServerNodeReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title, server_node):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if self.report.size == "full":
            self.content_list.append(
                UcsServerNodeReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                         server_node=server_node, centered=True))

            if server_node.storage_controllers:
                for storage_controller in server_node.storage_controllers:
                    key = UcsReportTable.get_name_and_sku(storage_controller)
                    self.content_list.append(
                        UcsStorageControllerReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                          title=_("Storage Controller ") + storage_controller.id +
                                                                ' - ' + key, device=storage_controller))

            if server_node.nvme_drives:
                self.content_list.append(
                    UcsNvmeDrivesReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                               title=_("NVMe Drives"), device=server_node))


class UcsServerNodeReportTable(UcsReportTable):
    def __init__(self, order_id, parent, server_node, centered=False):
        rows = [[_("Description"), _("Value")], [_("Server Node ID"), server_node.id], [_("SKU"), server_node.sku],
                [_("Model"), server_node.name], [_("Serial Number"), server_node.serial],
                [_("Firmware Package"), server_node.firmware_package_version]]

        memory_info = ""
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
            rows.append([_("Memory"), str(server_node.memory_total_marketing) + "\n" + memory_info])

        if server_node.adaptors:
            adaptor_dict = {}
            for adaptor in server_node.adaptors:
                key = self.get_name_and_sku(adaptor)
                if key in adaptor_dict:
                    adaptor_dict[key] += 1
                else:
                    adaptor_dict.update({key: 1})
            adaptor_models = "\n".join([(str(i[1]) + "x " + str(i[0])) for i in adaptor_dict.items()])
            rows.append([_("Adaptors"), adaptor_models])

        cpu_model = ""
        cores = 0
        if server_node.cpus:
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

        rows.append([_("CPUs"), cpu_model])
        rows.append([_("Cores"), cores])

        gpu_models = ""
        if server_node.gpus:
            gpu_dict = {}
            for gpu in server_node.gpus:
                key = self.get_name_and_sku(gpu)
                if key in gpu_dict:
                    gpu_dict[key] += 1
                else:
                    gpu_dict.update({key: 1})
            gpu_models = "\n".join([(str(i[1]) + "x " + str(i[0])) for i in gpu_dict.items()])
            rows.append([_("GPUs"), gpu_models])

        storage = ""
        drives = ""
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
        rows.append([_("Storage Controllers"), storage])
        rows.append([_("Drives"), drives])

        flash_cards = ""
        if server_node.storage_flexflash_controllers:
            flash_dict = {}
            for controller in server_node.storage_flexflash_controllers:
                for card in controller.flexflash_cards:
                    if card.capacity_marketing in flash_dict:
                        flash_dict[card.capacity_marketing] += 1
                    else:
                        flash_dict.update({card.capacity_marketing: 1})
            flash_cards = "\n".join([(str(i[1]) + "x " + str(i[0])) for i in flash_dict.items()])
        rows.append([_("FlexFlash SD Cards"), flash_cards])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows)


class UcsServerNodesSummaryReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title, server_nodes):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            UcsServerNodesSummaryReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                             server_nodes=server_nodes, centered=True))


class UcsServerNodesSummaryReportTable(UcsReportTable):
    def __init__(self, order_id, parent, server_nodes, centered=False):
        rows = [[_("ID"), _("Model"), _("Serial Number"), _("RAM"), _("CPUs"), _("Cores"), _("Adapters"), _("GPUs"),
                 _("Drives"), _("SD Cards")]]

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


class UcsPsuReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title, device):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if self.report.size == "full":
            self.content_list.append(
                UcsPsuReportTable(order_id=self.report.get_current_order_id(), parent=self, psu=device.power_supplies,
                                  centered=True))


class UcsPsuReportTable(UcsReportTable):
    def __init__(self, order_id, parent, psu, centered=False):
        rows = [[_("ID"), _("SKU"), _("Model"), _("Serial Number")]]

        for power_supply in psu:
            if hasattr(power_supply, 'name'):  # IMC doesn't have .name
                name = power_supply.name
            else:
                name = power_supply.model

            rows.append([power_supply.id, power_supply.sku, name, power_supply.serial])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows)


class UcsDiskReportTable(UcsReportTable):
    def __init__(self, order_id, parent, disks, centered=False):
        rows = [[_("ID"), _("PCIe Slot"), _("SKU"), _("Drive Type"), _("Connection Protocol"), _("Size"),
                 _("Block Size"), _("RPM")]]

        for disk in disks:
            connection_protocol = None
            if hasattr(disk, "link_speed"):
                if disk.link_speed not in ["unknown", "NA", None]:
                    connection_protocol = disk.connection_protocol + ' (' + str(disk.link_speed) + 'Gbps)'
                else:
                    connection_protocol = disk.connection_protocol
            rpm = None
            if hasattr(disk, "rotational_speed_marketing"):
                rpm = disk.rotational_speed_marketing if disk.rotational_speed_marketing != 0 else None
            block_size = None
            if hasattr(disk, "block_size"):
                block_size = disk.block_size
            pcie_slot = None
            if hasattr(disk, "slot_type") and hasattr(disk, "pci_slot"):
                if disk.slot_type == "pcie-nvme":
                    pcie_slot = disk.pci_slot
            rows.append([disk.id, pcie_slot, disk.sku, disk.drive_type, connection_protocol, disk.size_marketing,
                         block_size, rpm])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows)


class UcsStorageControllerReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title, device):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if self.report.size == "full":
            if device.disks:
                self.content_list.append(
                    UcsDiskReportTable(order_id=self.report.get_current_order_id(), parent=self, disks=device.disks,
                                       centered=True))


class UcsNvmeDrivesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title, device):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if self.report.size == "full":
            if device.nvme_drives:
                self.content_list.append(
                    UcsDiskReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                       disks=device.nvme_drives, centered=True))


class RecapUcsReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Detailed Specifications")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        # FI
        if self.report.inventory.fabric_interconnects or self.report.inventory.fabric_extenders:
            fabric_model_list = []
            for fabric in self.report.inventory.fabric_interconnects:
                key = fabric.sku
                if key not in fabric_model_list:
                    fabric_model_list.append(key)

            if fabric_model_list:
                self.content_list.append(ReportInventoryRecap(order_id=self.report.get_current_order_id(), parent=self,
                                                              type="FI", recap=fabric_model_list,
                                                              title=_("Fabric Interconnect Details")))

        # FEX
        if self.report.inventory.fabric_extenders:
            fabric_model_list = []
            for fabric in self.report.inventory.fabric_extenders:
                key = fabric.sku
                if key not in fabric_model_list:
                    fabric_model_list.append(key)

            if fabric_model_list:
                self.content_list.append(ReportInventoryRecap(order_id=self.report.get_current_order_id(), parent=self,
                                                              type="FEX", recap=fabric_model_list,
                                                              title=_("FEX Details")))

        # Chassis / Blades
        if self.report.inventory.chassis:
            chassis_model_list = []
            blade_model_list = []
            for chassis in self.report.inventory.chassis:
                if chassis.blades:
                    for blade in chassis.blades:
                        if blade.sku_scaled:
                            key = blade.sku_scaled
                        else:
                            key = blade.sku
                        if key not in blade_model_list:
                            blade_model_list.append(key)
                key = chassis.sku
                if key not in chassis_model_list:
                    chassis_model_list.append(key)
            if chassis_model_list:
                self.content_list.append(ReportInventoryRecap(order_id=self.report.get_current_order_id(), parent=self,
                                                              type="Chassis", recap=chassis_model_list,
                                                              title=_("Chassis Details")))
            if blade_model_list:
                self.content_list.append(ReportInventoryRecap(order_id=self.report.get_current_order_id(), parent=self,
                                                              type="Blades", recap=blade_model_list,
                                                              title=_("Blades Details")))

        # Racks
        if self.report.inventory.rack_units:
            rack_model_list = []
            for rack in self.report.inventory.rack_units:
                key = rack.sku
                if key not in rack_model_list:
                    rack_model_list.append(key)

            if rack_model_list:
                self.content_list.append(ReportInventoryRecap(order_id=self.report.get_current_order_id(), parent=self,
                                                              type="Rack", recap=rack_model_list,
                                                              title=_("Racks Details")))


class RecapUcsImcReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Detailed Specifications")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        # Racks
        if self.report.inventory.rack_units:
            rack_model_list = []
            for rack in self.report.inventory.rack_units:
                key = rack.sku
                if key not in rack_model_list:
                    rack_model_list.append(key)

            if rack_model_list:
                self.content_list.append(ReportInventoryRecap(order_id=self.report.get_current_order_id(), parent=self,
                                                              type="Rack", recap=rack_model_list,
                                                              title=_("Racks Details")))


class ReportInventoryRecap(UcsReportSection):
    def __init__(self, order_id, parent, title, recap, type):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        self.rows = []

        self.title = title
        self.recap = recap
        self.parent = parent

        for sku in recap:
            json_file = self._get_json_file(sku)
            name = type + " " + sku
            if json_file:
                spec_sheet_url = "Not Found"
                descr = "Not defined"
                dimensions = ""
                weight = ""
                if "spec_sheet_url" in json_file:
                    spec_sheet_url = json_file['spec_sheet_url']
                if "specs" in json_file:
                    specs = json_file["specs"]
                    if "descr" in specs:
                        descr = specs['descr']
                    if 'dimensions' in specs:
                        dimensions = specs['dimensions']
                    if 'weight' in specs:
                        weight = specs['weight']
                if "model_short_name" in json_file:
                    name = type + " " + json_file["model_short_name"] + ' (' + sku + ')'

                self.rows.append([name, descr, spec_sheet_url, dimensions, weight])

        if self.rows:
            for row in self.rows:
                self.content_list.append(ReportInventoryDeviceRecap(order_id=self.report.get_current_order_id(),
                                                                    parent=self, row=row))

    def _get_json_file(self, sku):
        file_name = str(sku) + ".json"
        folder_path = self._find_folder_path(file_name=file_name)
        try:
            json_file = open(folder_path / str(file_name))
            json_string = json_file.read()
            json_file.close()
            return json.loads(json_string)
        except FileNotFoundError:
            self.logger(level="error", message="JSON file " + folder_path + file_name + " not found")

        return False

    def _find_folder_path(self, file_name):
        for directory, sub_dirs, files in os.walk("catalog"):
            for file in files:
                if file == file_name:
                    return Path(directory)
        self.logger(level="error", message="Could not find catalog folder path for " + file_name)
        return Path('')


class ReportInventoryDeviceRecap(UcsReportSection):
    def __init__(self, order_id, parent, row, title=""):
        if not title:
            title = row[0]
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.title = title

        self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                   string=_("Description: "), italicized=True, bolded=True))
        self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                   string=row[1], new_paragraph=False))

        self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                   string=_("SpecSheet: "), italicized=True, bolded=True))
        self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                   string=_("specsheet"), hyper_link=row[2], new_paragraph=False,
                                                   color="blue",
                                                   underlined=True))
        # Dimensions
        if row[3]:
            self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                       string=_("Dimensions: \n"), italicized=True, bolded=True))
            dim = ""
            for key, value in row[3].items():
                if type(value) is dict:
                    data = key.title() + " (H x W x D): "
                    for subkey, subvalue in value.items():
                        data = data + str(subvalue) + " x "
                    data = data[:-2]  # remove the last " x "
                    dim = dim + "    " + data + "\n"
                else:
                    data = key.title().replace('_', ' ') + ": " + str(value)
                    dim = dim + "    " + data + "\n"
            dim = dim[:-1]  # remove the last "\n"
            self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                       string=dim, new_paragraph=False))

            # Weight
            if row[4]:
                self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                           string=_("Weight: \n"), italicized=True, bolded=True))
                weight = ""
                for key, value in row[4].items():
                    data = key.title().replace('_', ' ') + ": " + str(value)
                    weight = weight + "    " + data + "\n"
                weight = weight[:-1]  # remove the last "\n"
                self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                           string=weight, new_paragraph=False))
