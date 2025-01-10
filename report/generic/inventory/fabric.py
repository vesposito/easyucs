# coding: utf-8
# !/usr/bin/env python

""" fabric.py: Easy UCS Deployment Tool """

import os.path

from draw.object import GenericDrawObject
from report.content import *
from report.generic.inventory.psu import UcsPsuReportSection
from report.ucs.section import UcsReportSection
from report.ucs.table import UcsReportTable


class UcsFabricInventoryReportSection(UcsReportSection):
    def __init__(self, order_id, parent, domain, title=""):
        if not title:
            title = "Fabric Inventory"
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        if domain.fabric_interconnects or domain.fabric_extenders:
            descr = "The Fabric inventory gives information about the " + str(len(domain.fabric_interconnects)) + \
                    " FIs, " + str(len(domain.fabric_extenders)) + " FEXs, PSUs and Expansion Modules."
            self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                       string=descr))
        for fi in domain.fabric_interconnects:
            self.content_list.append(UcsFiReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                        fi=fi, title="Fabric Interconnect " + str(fi.id)))

        for fex in domain.fabric_extenders:
            self.content_list.append(UcsFexReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                         fex=fex, title="Fabric Extender " + str(fex.id)))


class UcsFiReportSection(UcsReportSection):
    def __init__(self, order_id, parent, fi, title):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        descr = "The FI " + fi.id + " (" + fi.model + ") has " + str(len(fi.expansion_modules)) + \
                " expansion modules and " + str(len(fi.power_supplies)) + " power supplies."
        self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                   string=descr))
        if fi.model in ["UCS-FI-M-6324", "UCSX-S9108-100G"]:
            # UCS Mini/X-Direct FI only has a rear picture
            if fi.__class__.__name__ in ["IntersightFi"]:
                path_rear = self.report.img_path + fi._parent.name + "_fi_" + fi.id + "_rear_clear.png"
            else:
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
                                  string="Rear View", centered=True, italicized=True, font_size=8))

        else:
            if fi.__class__.__name__ in ["IntersightFi"]:
                path_front = self.report.img_path + fi._parent.name + "_fi_" + fi.id + "_front.png"
            else:
                path_front = self.report.img_path + "fi_" + fi.id + "_front.png"
            self.content_list.append(
                GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path_front,
                                   centered=True, spacing_after=2))
            self.content_list.append(
                GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                  string="Front View", centered=True, italicized=True, font_size=8))

            if fi.__class__.__name__ in ["IntersightFi"]:
                path_rear = self.report.img_path + fi._parent.name + "_fi_" + fi.id + "_rear_clear.png"
            else:
                path_rear = self.report.img_path + "fi_" + fi.id + "_rear_clear.png"
            self.content_list.append(
                GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path_rear,
                                   centered=True, spacing_after=2))
            self.content_list.append(
                GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                  string="Rear View", centered=True, italicized=True, font_size=8))
        self.content_list.append(
            UcsFiReportTable(order_id=self.report.get_current_order_id(), parent=self, fi=fi, centered=True))

        if fi.power_supplies:
            self.content_list.append(UcsPsuReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                         title="Power Supplies", device=fi))

        if fi.expansion_modules:
            self.content_list.append(UcsGemReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                         title="Expansion Modules", fi=fi))

        if hasattr(fi, "licenses") and fi.licenses:
            self.content_list.append(UcsSystemLicensesReportSection(order_id=self.report.get_current_order_id(),
                                                                    parent=self, title="Port Licenses", fi=fi))

        if hasattr(fi, "vlan_port_count") and fi.vlan_port_count:
            self.content_list.append(
                UcsSystemVlanPortCountReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                    title="VLAN Port Count", fi=fi))


class UcsFiReportTable(UcsReportTable):
    def __init__(self, order_id, parent, fi, centered=False):
        firmware_version = "N/A"
        if parent.report.device.metadata.device_type == "intersight":
            firmware_version = fi.firmware_version
        elif parent.report.device.metadata.device_type in ["ucsc", "ucsm"]:
            firmware_version = fi.firmware_package_version
        rows = [
            ["Description", "Value"],
            ["Fabric", fi.id],
            ["SKU", fi.sku],
            ["Model", fi.name],
            ["Serial Number", fi.serial],
            ["Firmware", firmware_version]
        ]

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
            rows.append(["Ports", port_info])

        if fi.power_supplies:
            psu_dict = {}
            for psu in fi.power_supplies:
                key = self.get_name_and_sku(psu)
                if key in psu_dict:
                    psu_dict[key] += 1
                else:
                    psu_dict.update({key: 1})
            psu_models = "\n".join([(str(i[1]) + "x " + str(i[0])) for i in psu_dict.items()])
            rows.append(["Power Supplies", psu_models])

        if fi.expansion_modules:
            expansion_dict = {}
            for expansion in fi.expansion_modules:
                key = self.get_name_and_sku(expansion)
                if key in expansion_dict:
                    expansion_dict[key] += 1
                else:
                    expansion_dict.update({key: 1})
            gem_models = "\n".join([(str(i[1]) + "x " + str(i[0])) for i in expansion_dict.items()])
            rows.append(["Expansion Modules", gem_models])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows)


class UcsGemReportSection(UcsReportSection):
    def __init__(self, order_id, parent, fi, title):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if self.report.size == "full":
            self.content_list.append(
                UcsGemReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                  gem=fi.expansion_modules, centered=True))


class UcsGemReportTable(UcsReportTable):
    def __init__(self, order_id, parent, gem, centered=False):
        rows = [["ID", "SKU", "Model", "Serial Number"]]

        for expansion_module in gem:
            rows.append([expansion_module.id, expansion_module.sku, expansion_module.name, expansion_module.serial])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows)


class UcsSystemLicensesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, fi, title):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if self.report.size == "full":
            self.content_list.append(
                UcsSystemLicensesReportTable(order_id=self.report.get_current_order_id(), parent=self, fi=fi,
                                             centered=True))


class UcsSystemLicensesReportTable(UcsReportTable):
    def __init__(self, order_id, parent, fi, centered=False):
        rows = [["SKU", "Total", "Default", "Used", "Available", "Status", "Grace Period Used (days)"]]

        for lic in fi.licenses:
            rows.append([lic["sku"], lic["quantity"], lic["quantity_default"], lic["quantity_used"],
                         lic["quantity_available"], lic["status"], lic["grace_period_used_days"]])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows)


class UcsSystemVlanPortCountReportSection(UcsReportSection):
    def __init__(self, order_id, parent, fi, title):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if self.report.size == "full":
            self.content_list.append(
                UcsSystemVlanPortCountReportTable(order_id=self.report.get_current_order_id(), parent=self, fi=fi,
                                                  centered=True))


class UcsSystemVlanPortCountReportTable(UcsReportTable):
    def __init__(self, order_id, parent, fi, centered=False):
        rows = [["Actual Limit", "VLAN Compression State", "Max Limit", "Total VLAN Port Count",
                 "Access VLAN Port Count", "Border VLAN Port Count", "Usage (%)"]]

        port_count = fi.vlan_port_count
        rows.append([port_count["limit"], port_count["vlan_compression_state"], port_count["limit_with_compression"],
                     port_count["total_vlan_port_count"], port_count["access_vlan_port_count"],
                     port_count["border_vlan_port_count"], port_count["usage_percent"]])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows)


class UcsFexReportSection(UcsReportSection):
    def __init__(self, order_id, parent, fex, title):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        descr = ("The FEX " + str(fex.id) + " (" + fex.model + ") has " + str(len(fex.power_supplies)) +
                 " power supplies.")
        self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                   string=descr))

        if fex.__class__.__name__ in ["IntersightFex"]:
            path_front = self.report.img_path + fex._parent.name + "_fex_" + str(fex.id) + "_front.png"
        else:
            path_front = self.report.img_path + "fex_" + str(fex.id) + "_front.png"
        self.content_list.append(
            GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path_front,
                               centered=True, spacing_after=2))
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                              string="Front View", centered=True, italicized=True, font_size=8))

        if fex.__class__.__name__ in ["IntersightFex"]:
            path_rear = self.report.img_path + fex._parent.name + "_fex_" + str(fex.id) + "_rear_clear.png"
        else:
            path_rear = self.report.img_path + "fex_" + str(fex.id) + "_rear_clear.png"
        self.content_list.append(
            GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path_rear,
                               centered=True, spacing_after=2))
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                              string="Rear View", centered=True, italicized=True, font_size=8))
        self.content_list.append(
            UcsFexReportTable(order_id=self.report.get_current_order_id(), parent=self, fex=fex, centered=True))

        if fex.power_supplies:
            self.content_list.append(UcsPsuReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                         title="Power Supplies", device=fex))


class UcsFexReportTable(UcsReportTable):
    def __init__(self, order_id, parent, fex, centered=False):
        rows = [
            ["Description", "Value"],
            ["FEX", fex.id],
            ["Fabric", fex.switch_id],
            ["SKU", fex.sku],
            ["Model", fex.name],
            ["Serial Number", fex.serial]
        ]

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
            rows.append(["Ports", port_info])

        if fex.power_supplies:
            psu_dict = {}
            for psu in fex.power_supplies:
                key = self.get_name_and_sku(psu)
                if key in psu_dict:
                    psu_dict[key] += 1
                else:
                    psu_dict.update({key: 1})
            psu_models = "\n".join([(str(i[1]) + "x " + str(i[0])) for i in psu_dict.items()])
            rows.append(["Power Supplies", psu_models])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows)
