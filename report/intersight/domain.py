# coding: utf-8
# !/usr/bin/env python

""" inventory.py: Easy UCS Deployment Tool """

from report.content import *
from report.generic.architecture import UcsDomainArchitectureReportSection
from report.generic.inventory.chassis import UcsChassisInventoryReportSection
from report.generic.inventory.fabric import UcsFabricInventoryReportSection
from report.generic.inventory.racks import UcsRacksInventoryReportSection
from report.ucs.section import UcsReportSection


class IntersightImmDomainReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title, domain):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        descr = ""  # TODO
        self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                   string=descr))

        self.content_list.append(
            UcsDomainArchitectureReportSection(order_id=self.report.get_current_order_id(), parent=self, domain=domain))
        if domain.fabric_interconnects:
            self.content_list.append(UcsFabricInventoryReportSection(
                order_id=self.report.get_current_order_id(), parent=self, domain=domain))
        if domain.chassis:
            self.content_list.append(UcsChassisInventoryReportSection(
                order_id=self.report.get_current_order_id(), parent=self, domain=domain))
        if domain.rack_units:
            self.content_list.append(UcsRacksInventoryReportSection(
                order_id=self.report.get_current_order_id(), parent=self, domain=domain))


class IntersightUcsmDomainReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title, domain):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        descr = ""  # TODO
        self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                   string=descr))

        if domain.fabric_interconnects:
            self.content_list.append(UcsFabricInventoryReportSection(
                order_id=self.report.get_current_order_id(), parent=self, domain=domain))
        if domain.chassis:
            self.content_list.append(UcsChassisInventoryReportSection(
                order_id=self.report.get_current_order_id(), parent=self, domain=domain))
        if domain.rack_units:
            self.content_list.append(UcsRacksInventoryReportSection(
                order_id=self.report.get_current_order_id(), parent=self, domain=domain))
