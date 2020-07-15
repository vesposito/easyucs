# coding: utf-8
# !/usr/bin/env python

""" section.py: Easy UCS Deployment Tool """

from report.content import *


class GenericReportSection(GenericReportElement):
    # A section has a list of img, string and table (all called content) (content can even be other sections)
    def __init__(self, order_id, parent, title):
        GenericReportElement.__init__(self, order_id=order_id, parent=parent)
        self.content_list = []
        self.title = title
        self.indent = self.__find_indent()  # Heading 1 for example

    def add_in_word_report(self):
        # self.logger(level="debug", message="Adding " + self.__class__.__name__ + " in word")
        self.report.document.add_heading(text=self.title, level=self.indent)

    def __find_indent(self):
        indent = 1
        current_object = self.parent
        while hasattr(current_object, 'parent') and not hasattr(current_object, 'timestamp'):
            current_object = current_object.parent
            indent += 1
        if hasattr(current_object, 'timestamp'):
            return indent
        else:
            return None
