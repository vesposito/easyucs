# coding: utf-8
# !/usr/bin/env python

""" report.py: Easy UCS Deployment Tool """
from __init__ import __author__, __copyright__,  __version__, __status__


import time, datetime, os, sys, gettext, uuid
from docx import Document
from docx.shared import Cm, RGBColor
from report.section import *


class GenericReport:
    def __init__(self, device, inventory, config, language, output_format, page_layout, directory, filename):
        self.uuid = uuid.uuid4()
        self.language = language
        self.output_format = output_format
        self.page_layout = page_layout
        self.directory = directory
        self.filename = filename
        self.timestamp = time.time()

        self.img_path = self.directory + "/" + device.target + "_"

        self.device = device
        self.inventory = inventory
        self.config = config

        self.logger(message="Creating report")

        self.element_list = [] # list of Section, front page, content table, etc.
        self.current_order_id = 0

        self.title = self.device.device_type

        if self.output_format == "docx":
            self.document = Document()
        self.install_language()

    def install_language(self):
        # Command to create the pot
        # py C:\Users\mabuelgh\AppData\Local\Programs\Python\Python35\Tools\i18n\pygettext.py -d report .\report.py .\element.py .\subelement.py .\section.py

        if self.language == "en":
            en = gettext.NullTranslations()
            en.install()
        elif self.language == "fr":
            fr = gettext.translation('report', localedir='./locales', languages=['fr'])
            fr.install()

    def get_current_order_id(self):
        self.current_order_id += 1
        return self.current_order_id - 1

    def logger(self, level='info', message="No message"):
        if self.device:
            self.device.logger(level=level, message=message)


class UcsGenericReport(GenericReport):
    def __init__(self, device, inventory, config, language, output_format, page_layout, directory, filename):
        GenericReport.__init__(self,device=device, inventory=inventory, config=config, language=language, output_format=output_format, page_layout=page_layout,
                               directory=directory, filename=filename)


class UcsSystemReport(UcsGenericReport):
    def __init__(self, device, inventory, config, language, output_format, page_layout, directory, filename):
        UcsGenericReport.__init__(self, device=device, inventory=inventory, config=config, language=language,
                                  output_format=output_format, page_layout=page_layout,
                                  directory=directory, filename=filename)

        self.element_list.append(
            ReportFrontPage(order_id=self.get_current_order_id(),parent=self,title=_("EasyUcs Report"),
                            description=_("Created with EasyUcs") + " - " + time.strftime("%d %B %Y"),
                            authors=__author__))

        # We determine the order id of the ReportTableOfContents at the begining (second element to be added but
        # created at the end for obvious reason)
        table_content_order_id = self.get_current_order_id()

        self.element_list.append(
            ClusterOverviewUcsReportSection(order_id=self.get_current_order_id(), parent=self))
        self.element_list.append(
            ArchitectureUcsReportSection(order_id=self.get_current_order_id(), parent=self))
        self.element_list.append(
            EquipmentInventoryUcsReportSection(order_id=self.get_current_order_id(), parent=self))
        self.element_list.append(
            LogicalConfigurationUcsReportSection(order_id=self.get_current_order_id(), parent=self))

        # Always last to append
        self.element_list.append(
            ReportTableOfContents(order_id=table_content_order_id, parent=self, section_list=self.element_list))

        # We sort the element list in order to put the table of content at the begining
        self.element_list = sorted(self.element_list, key=lambda element: element.order_id)

        self.logger(level="debug", message="All report elements added to the list")

        if self.output_format == "docx":
            self.logger(message="Generating " + self.output_format + " report")
            #self.document.sections[0].footer.text = "Created with EasyUcs"
            self.recursive_add_in_word_report(element=self)
            try:
                self.document.save(self.directory + '/' + filename + '.docx')
                self.logger(message="Report generated and saved :" + self.directory + '/' + filename + '.docx')
            except PermissionError:
                self.logger(level="error",message="Report has not been created. Permission denied. Please close Word.")


    def recursive_add_in_word_report(self, element):
        # None if add_in_word_report not found
        call = getattr(element, "add_in_word_report", None)
        if call:
            if callable(call):
                element.add_in_word_report()

        if hasattr(element, "content_list"):
            for content in element.content_list:
                self.recursive_add_in_word_report(element=content)

        if hasattr(element, "element_list"):
            for content in element.element_list:
                self.recursive_add_in_word_report(element=content)


class UcsImcReport(UcsGenericReport):
    def __init__(self, device, inventory, config, language, output_format, page_layout, directory, filename):
        UcsGenericReport.__init__(self, device=device, inventory=inventory, config=config, language=language, output_format=output_format, page_layout=page_layout,
                                  directory=directory, filename=filename)
