# coding: utf-8
# !/usr/bin/env python

""" inventory.py: Easy UCS Deployment Tool """

import json
import os.path
from pathlib import Path

from report.content import *
from report.generic.inventory.chassis import UcsChassisInventoryReportSection
from report.generic.inventory.fabric import UcsFabricInventoryReportSection
from report.generic.inventory.racks import UcsRackEnclosuresInventoryReportSection, UcsRacksInventoryReportSection
from report.ucs.section import UcsReportSection


class UcsSystemInventoryReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = "Equipment Inventory"
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        descr = ("This section details the inventory of this UCS domain: " +
                 "FIs, FEXs, rack servers, chassis and their components.")
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self, string=descr))
        self.content_list.append(UcsFabricInventoryReportSection(
            self.report.get_current_order_id(), parent=self, domain=self.report.inventory))
        self.content_list.append(UcsChassisInventoryReportSection(
            self.report.get_current_order_id(), parent=self, domain=self.report.inventory))
        self.content_list.append(UcsRacksInventoryReportSection(
            self.report.get_current_order_id(), parent=self, domain=self.report.inventory))
        self.content_list.append(UcsRackEnclosuresInventoryReportSection(
            self.report.get_current_order_id(), parent=self, domain=self.report.inventory))
        # self.content_list.append(RecapUcsReportSection(self.report.get_current_order_id(), parent=self))


class UcsImcInventoryReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = "Equipment Inventory"
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        descr = "This section details the inventory."
        self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                   string=descr))
        self.content_list.append(UcsRacksInventoryReportSection(
            self.report.get_current_order_id(), parent=self, domain=self.report.inventory))
        # self.content_list.append(RecapUcsImcReportSection(self.report.get_current_order_id(), parent=self))


class RecapUcsReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = "Detailed Specifications"
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
                                                              title="Fabric Interconnect Details"))

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
                                                              title="FEX Details"))

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
                                                              title="Chassis Details"))
            if blade_model_list:
                self.content_list.append(ReportInventoryRecap(order_id=self.report.get_current_order_id(), parent=self,
                                                              type="Blades", recap=blade_model_list,
                                                              title="Blades Details"))

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
                                                              title="Racks Details"))


class RecapUcsImcReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = "Detailed Specifications"
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
                                                              title="Racks Details"))


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
                                                   string="Description: ", italicized=True, bolded=True))
        self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                   string=row[1], new_paragraph=False))

        self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                   string="SpecSheet: ", italicized=True, bolded=True))
        self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                   string="specsheet", hyper_link=row[2], new_paragraph=False,
                                                   color="blue",
                                                   underlined=True))
        # Dimensions
        if row[3]:
            self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                       string="Dimensions: \n", italicized=True, bolded=True))
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
                                                           string="Weight: \n", italicized=True, bolded=True))
                weight = ""
                for key, value in row[4].items():
                    data = key.title().replace('_', ' ') + ": " + str(value)
                    weight = weight + "    " + data + "\n"
                weight = weight[:-1]  # remove the last "\n"
                self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                           string=weight, new_paragraph=False))
