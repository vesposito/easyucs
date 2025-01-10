# coding: utf-8
# !/usr/bin/env python

""" report.py: Easy UCS Deployment Tool """

from __init__ import __author__, __version__
from report.content import *
from report.intersight.config import IntersightConfigReportSection
from report.intersight.inventory import IntersightInventoryReportSection
from report.report import GenericReport


class IntersightReport(GenericReport):
    def __init__(self, parent, device, inventory, config, language, output_format, page_layout, directory, size):
        GenericReport.__init__(self, parent=parent, device=device, inventory=inventory, config=config,
                               language=language, output_format=output_format, page_layout=page_layout,
                               directory=directory, size=size, report_type="classic")

        self.title = "Intersight"
        if config.account_details:
            if getattr(config.account_details[0], "account_name", None):
                self.title = config.account_details[0].account_name

        # We add the Front Page of the report, which is identical for all UCS devices
        self.element_list.append(
            ReportFrontPage(order_id=self.get_current_order_id(), parent=self, title=self.title,
                            description="Created with EasyUCS" + " " + __version__ + " - " +
                                        self.metadata.timestamp.strftime("%d %B %Y"), authors=__author__))

        # We determine the order id of the TOC at the beginning (second element to be added, but it needs to be
        # created at the end for obvious reasons)
        self.toc_order_id = self.get_current_order_id()

        self.element_list.append(
            IntersightInventoryReportSection(order_id=self.get_current_order_id(), parent=self))
        self.element_list.append(
            IntersightConfigReportSection(order_id=self.get_current_order_id(), parent=self))

        # Always last to append
        self.element_list.append(
            ReportTableOfContents(order_id=self.toc_order_id, parent=self, section_list=self.element_list))
        self.toc = self.element_list[-1]

        # We sort the element list in order to put the table of content at the beginning
        self.element_list = sorted(self.element_list, key=lambda element: element.order_id)

        self.logger(level="debug", message="All report elements added to the list")

        self.logger(message="Generating " + self.metadata.output_format + " report (can take several minutes)")
        if self.metadata.output_format == "docx":
            self.recursive_add_in_word_report(element=self)
        elif self.metadata.output_format == "json":
            self.recursive_add_in_json_report(element=self, document_json=self.document["report"])
        elif self.metadata.output_format == "pdf":
            self.recursive_add_in_pdf_report(element=self)
            self._reset_pdf_sequence()
        else:
            self.logger(level="error",
                        message=f"Invalid output format. '{self.metadata.output_format}' format not supported")
