# coding: utf-8
# !/usr/bin/env python

""" section.py: Easy UCS Deployment Tool """

from report.section import GenericReportSection


class UcsReportSection(GenericReportSection):
    # A section has a list of img, string and table (all called content) (content can even be other sections)
    def __init__(self, order_id, parent, title):
        GenericReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

    def parse_org(self, org, element_list, element_to_parse):
        if eval("org." + element_to_parse) is not None:
            for element in eval("org." + element_to_parse):
                element_list.append(element)
        if hasattr(org, "orgs"):
            if org.orgs is not None:
                for suborg in org.orgs:
                    self.parse_org(suborg, element_list, element_to_parse)
