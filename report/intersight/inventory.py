# coding: utf-8
# !/usr/bin/env python

""" inventory.py: Easy UCS Deployment Tool """

from report.content import *
from report.generic.inventory.racks import UcsRacksInventoryReportSection
from report.intersight.domain import IntersightImmDomainReportSection, IntersightUcsmDomainReportSection
from report.ucs.section import UcsReportSection


class IntersightInventoryReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = "Equipment Inventory"
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        descr = ("This section details the inventory of this UCS domain: " +
                 "FIs, FEXs, rack servers, chassis and their components.")
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self, string=descr))

        for imm_domain in self.report.inventory.imm_domains:
            domain_name = imm_domain.name
            self.content_list.append(
                IntersightImmDomainReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                 title="IMM Domain " + domain_name, domain=imm_domain))

        for ucsm_domain in self.report.inventory.ucsm_domains:
            domain_name = ucsm_domain.name
            self.content_list.append(
                IntersightUcsmDomainReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                  title="UCSM Domain " + domain_name, domain=ucsm_domain))

        if self.report.inventory.rack_units:
            self.content_list.append(
                UcsRacksInventoryReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                               domain=self.report.inventory))
