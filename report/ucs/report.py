# coding: utf-8
# !/usr/bin/env python

""" report.py: Easy UCS Deployment Tool """

import time

from __init__ import __author__, __version__
from report.content import *
from report.report import GenericReport
from report.ucs.architecture import UcsSystemArchitectureReportSection
from report.ucs.configuration import UcsSystemConfigurationReportSection
from report.ucs.inventory import UcsSystemInventoryReportSection, UcsImcInventoryReportSection
from report.ucs.overview import UcsImcOverviewReportSection, UcsSystemOverviewReportSection


class UcsGenericReport(GenericReport):
    def __init__(self, device, inventory, config, language, output_format, page_layout, directory, filename, size):
        GenericReport.__init__(self, device=device, inventory=inventory, config=config, language=language,
                               output_format=output_format, page_layout=page_layout, directory=directory,
                               filename=filename, size=size)

        # We add the Front Page of the report, which is identical for all UCS devices
        self.element_list.append(
            ReportFrontPage(order_id=self.get_current_order_id(), parent=self, title=self.title,
                            description=_("Created with EasyUCS") + " " + __version__ + " - " +
                                        time.strftime("%d %B %Y"), authors=__author__))

        # We determine the order id of the TOC at the beginning (second element to be added but it needs to be
        # created at the end for obvious reasons)
        self.toc_order_id = self.get_current_order_id()


class UcsSystemReport(UcsGenericReport):
    def __init__(self, device, inventory, config, language, output_format, page_layout, directory, filename, size):
        self.title = config.system[0].name

        UcsGenericReport.__init__(self, device=device, inventory=inventory, config=config, language=language,
                                  output_format=output_format, page_layout=page_layout,
                                  directory=directory, filename=filename, size=size)

        self.element_list.append(
            UcsSystemOverviewReportSection(order_id=self.get_current_order_id(), parent=self))
        self.element_list.append(
            UcsSystemArchitectureReportSection(order_id=self.get_current_order_id(), parent=self))
        self.element_list.append(
            UcsSystemInventoryReportSection(order_id=self.get_current_order_id(), parent=self))
        self.element_list.append(
            UcsSystemConfigurationReportSection(order_id=self.get_current_order_id(), parent=self))

        # Always last to append
        self.element_list.append(
            ReportTableOfContents(order_id=self.toc_order_id, parent=self, section_list=self.element_list))
        self.toc = self.element_list[-1]

        # We sort the element list in order to put the table of content at the beginning
        self.element_list = sorted(self.element_list, key=lambda element: element.order_id)

        self.logger(level="debug", message="All report elements added to the list")

        if self.output_format == "docx":
            self.logger(message="Generating " + self.output_format + " report")
            self.recursive_add_in_word_report(element=self)

        self.save_report()


class UcsImcReport(UcsGenericReport):
    def __init__(self, device, inventory, config, language, output_format, page_layout, directory, filename, size):
        self.title = config.admin_networking[0].management_hostname

        UcsGenericReport.__init__(self, device=device, inventory=inventory, config=config, language=language,
                                  output_format=output_format, page_layout=page_layout,
                                  directory=directory, filename=filename, size=size)

        self.element_list.append(
            UcsImcOverviewReportSection(order_id=self.get_current_order_id(), parent=self))
        self.element_list.append(
            UcsImcInventoryReportSection(order_id=self.get_current_order_id(), parent=self))

        # Always last to append
        self.element_list.append(
            ReportTableOfContents(order_id=self.toc_order_id, parent=self, section_list=self.element_list))
        self.toc = self.element_list[-1]

        # We sort the element list in order to put the table of content at the beginning
        self.element_list = sorted(self.element_list, key=lambda element: element.order_id)

        self.logger(level="debug", message="All report elements added to the list")

        if self.output_format == "docx":
            self.logger(message="Generating " + self.output_format + " report")
            self.recursive_add_in_word_report(element=self)

        self.save_report()
