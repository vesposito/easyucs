# coding: utf-8
# !/usr/bin/env python

""" architecture.py: Easy UCS Deployment Tool """

from report.generic.architecture import UcsDomainInfraCablingReportSection
from report.ucs.section import UcsReportSection


class IntersightArchitectureReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = "Architecture"
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        self.content_list.append(UcsDomainInfraCablingReportSection(self.report.get_current_order_id(), parent=self))
        # self.content_list.append(UcsSystemNetworkNeighborsReportSection(self.report.get_current_order_id(),
        #                                                                 parent=self))
