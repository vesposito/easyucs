# coding: utf-8
# !/usr/bin/env python

""" report.py: Easy UCS Deployment Tool """

import gettext
import os
import time
import uuid

from docx import Document
from docx.shared import Cm, Mm

from __init__ import __version__


class GenericReport:
    def __init__(self, device=None, inventory=None, config=None, language="en", output_format="docx",
                 page_layout="letter", directory=".", filename=None, size="full"):
        self.config = config
        self.device = device
        self.directory = directory
        self.filename = filename
        self.inventory = inventory
        self.language = language
        self.output_format = output_format
        self.page_layout = page_layout
        self.size = size
        self.timestamp = time.time()
        self.uuid = uuid.uuid4()

        self.target = device.target
        self.img_path = self.directory + "/" + device.target + "_"

        self.logger(message="Creating report for device " + self.target + " using config UUID " +
                            str(self.config.uuid) + " and inventory UUID " + str(self.inventory.uuid))
        self.logger(level="debug",
                    message="Generating report in " + self.output_format + " format with layout " +
                            self.page_layout.upper() + " in " + self.language.upper())

        self.document = None
        self.element_list = []  # list of section, front page, content table, etc.
        self.current_order_id = 0
        self.toc_order_id = 0
        self.toc = None
        if not hasattr(self, "title"):
            self.title = ""

        self.install_language()

        if self.output_format == "docx":
            # Open an empty Word as a template for some style setting
            # The template layout is letter by default
            template_ref = open("./report/template.docx", "rb")
            self.document = Document(template_ref)
            template_ref.close()

            section = self.document.sections[0]
            if self.page_layout.lower() == "a4":
                section.page_height = Mm(297)
                section.page_width = Mm(210)
                section.left_margin = Cm(2)  # Default A4 margin is Mm(25.4)
                section.right_margin = Cm(2)  # Default A4 margin is Mm(25.4)
                section.top_margin = Mm(25.4)
                section.bottom_margin = Mm(25.4)
                section.header_distance = Mm(12.7)
                section.footer_distance = Mm(12.7)

            # Setting header of report
            section.different_first_page_header_footer = True
            section.header.paragraphs[0].alignment = 1  # Centered
            section.header.paragraphs[0].text = _("Created with EasyUCS") + " " + __version__ + " - " + str(self.title)

    def install_language(self):
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

    def recursive_add_in_word_report(self, element):
        # None if add_in_word_report not found
        call = getattr(element, "add_in_word_report", None)
        if call:
            if callable(call):
                if hasattr(element, "content_list"):
                    if element.content_list:
                        element.add_in_word_report()
                elif hasattr(element, "element_list"):
                    if element.element_list:
                        element.add_in_word_report()
                else:
                    element.add_in_word_report()

        if hasattr(element, "content_list"):
            for content in element.content_list:
                self.recursive_add_in_word_report(element=content)

        if hasattr(element, "element_list"):
            for content in element.element_list:
                self.recursive_add_in_word_report(element=content)

    def save_report(self):
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)

        full_filename = self.directory + '/' + self.filename + '.' + self.output_format
        if self.output_format == "docx":
            try:
                self.document.save(full_filename)

                # Update the TOC (Windows only)
                # Not used
                # self.toc.update_toc(full_filename=full_filename)

                self.logger(message="Report generated and saved to: " + full_filename)
            except PermissionError:
                self.logger(level="error",
                            message="Report has not been created. Permission denied. Please close existing document.")

        else:
            self.logger(level="error", message="Report formats other than 'docx' are not supported")
