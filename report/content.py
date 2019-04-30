# coding: utf-8
# !/usr/bin/env python

""" content.py: Easy UCS Deployment Tool """
from __init__ import __author__, __copyright__,  __version__, __status__


from docx.shared import Cm, Pt
import os.path


class GenericReportElement():
    def __init__(self, order_id, parent):
        self.order_id = order_id
        self.parent = parent

        self.report = self.__find_report()

    def __find_report(self):
        current_object = self.parent
        while hasattr(current_object, 'parent') and not hasattr(current_object, 'timestamp'):
            current_object = current_object.parent
        if hasattr(current_object, 'timestamp'):
            return current_object
        else:
            return None

    def logger(self, level='info', message="No message"):
        if not self.report:
            self.report = self._find_report()

        if self.report:
            self.report.logger(level=level, message=message)


class GenericReportContent(GenericReportElement):
    def __init__(self, order_id, parent, centered=False):
        GenericReportElement.__init__(self, order_id=order_id, parent=parent)
        self.centered = centered  # True or False


class GenericReportHeading(GenericReportContent):
    def __init__(self, order_id, parent, string, heading_size=0):
        GenericReportContent.__init__(self, order_id=order_id, parent=parent)
        self.string = string
        self.heading_size = heading_size

    def add_in_word_report(self):
        #self.logger(level="debug", message="Adding " + self.__class__.__name__ + " in word")
        self.report.document.add_heading(text=self.string, level=self.heading_size)


class GenericReportText(GenericReportContent):
    def __init__(self, order_id, parent, string, centered=False, italicized=False, bolded=False,
                 font="Calibri", font_size=11, color="black",):
        GenericReportContent.__init__(self, order_id=order_id, parent=parent, centered=centered)
        self.string = string
        self.italicized = italicized
        self.bolded = bolded
        self.font = font
        self.font_size = font_size
        self.color = color

    def add_in_word_report(self):
        #self.logger(level="debug", message="Adding " + self.__class__.__name__ + " in word")
        self.paragraph = self.report.document.add_paragraph()
        self.paragraph.alignment = int(bool(self.centered))
        string = self.paragraph.add_run(self.string)
        string.italic = self.italicized
        string.bold = self.bolded
        string.font.size = Pt(self.font_size)
        string.font.name = self.font


class GenericReportImage(GenericReportContent):
    def __init__(self, order_id, parent, path, centered=False, size=15):
        GenericReportContent.__init__(self, order_id=order_id, parent=parent, centered=centered)
        self.path = path
        self.size = size

        if not os.path.exists(self.path):
            self.logger(level="warning", message="Image : " + self.path + " not found")
            return

    def add_in_word_report(self):
        #self.logger(level="debug", message="Adding " + self.__class__.__name__ + " in word")
        self.paragraph = self.report.document.add_paragraph()
        self.paragraph.alignment = int(bool(self.centered))
        self.paragraph.add_run().add_picture(self.path, width=Cm(self.size))


class GenericReportTable(GenericReportContent):
    def __init__(self, order_id, parent, row_number, column_number, centered=False, cells_list=[],
                 style="Light Grid Accent 1"):
        """
        :param order_id:
        :param parent:
        :param row_number:
        :param column_number:
        :param centered:
        :param cells_list: example : list = [[1,2,3],[2,3,4]]
        """

        GenericReportContent.__init__(self, order_id=order_id, parent=parent, centered=centered)
        self.row_number = row_number
        self.column_number = column_number
        self.cells_list = cells_list
        self.style = style

        if len(self.cells_list) == self.row_number:
            self.cells_type = "row"
        elif len(self.cells_list) == self.column_number:
            self.cells_type = "column"
            self.__format_column_to_row()
        else:
            self.logger(level="warning",
                        message="Cells in the table are not the same size as the number of column or row")
            return False

    def add_in_word_report(self):
        #self.logger(level="debug", message="Adding " + self.__class__.__name__ + " in word")
        table = self.report.document.add_table(rows=self.row_number, cols=self.column_number,
                                               style=self.style)
        table.alignment = int(bool(self.centered))
        for i in range(len(self.cells_list)):
            row = self.cells_list[i]
            row_cells = table.rows[i].cells
            for j in range(0, len(row)):
                row_cells[j].text = str(row[j])

    def __format_column_to_row(self):
        column_cells_list = self.cells_list
        row_cells_list = []
        for i in range(0, self.row_number):
            row_cells_list.append([])

        for i in range(0, len(column_cells_list)):
            for j in range(0, self.row_number):
                row_cells_list[j].append(column_cells_list[i][j])

        self.cells_list = row_cells_list
        self.cells_type = "row"


class ReportTableOfContents(GenericReportElement):
    def __init__(self, order_id, parent, section_list):
        GenericReportElement.__init__(self, order_id=order_id, parent=parent)
        self.section_list = []
        self.generate_list(list=section_list)
        self.title = "Table of Contents"

    def add_in_word_report(self):
        #self.logger(level="debug", message="Adding " + self.__class__.__name__ + " in word")
        self.report.document.add_heading(text=self.title, level=1)
        self.report.document.add_paragraph()
        for element in self.section_list:
            self.paragraph = self.report.document.add_paragraph()
            self.paragraph.add_run((element))
        self.report.document.add_page_break()

    def generate_list(self, list, indent=0):
        # Generate the list of content
        spacing = "    "
        for element in list:
            if hasattr(element, "title"):
                title = element.title
                if indent:
                    for i in range(0, indent):
                        title = spacing + title
                self.section_list.append(title)
            if hasattr(element, "content_list"):
                self.generate_list(list=element.content_list, indent=indent + 1)


class ReportFrontPage(GenericReportElement):
    def __init__(self, order_id, parent, title, description="", authors=""):
        GenericReportElement.__init__(self, order_id=order_id, parent=parent)
        self.title = title
        self.description = description
        self.authors = authors

    def add_in_word_report(self):
        #self.logger(level="debug", message="Adding " + self.__class__.__name__ + " in word")
        page_breaks = 26
        count_break = 0
        # Add line breaks
        for i in range(0, int(page_breaks/2) - 4):
            self.report.document.add_paragraph()
            count_break += 1

        self.paragraph = self.report.document.add_paragraph()
        self.paragraph.alignment = int(bool(True))
        title = self.paragraph.add_run((self.title))
        title.bold = True
        title.font.size = Pt(28)
        count_break += 1

        self.paragraph = self.report.document.add_paragraph()
        self.paragraph.alignment = int(bool(True))
        description = self.paragraph.add_run((self.description))
        description.italic = True
        self.paragraph = self.report.document.add_paragraph()
        count_break += 2

        # Add line breaks, we adjust to write 2 lines before the end of the page
        for i in range(count_break, page_breaks -3):
            self.paragraph = self.report.document.add_paragraph()
            count_break += 1
        # alignment = 2 to align right
        self.paragraph.alignment = 2
        author = self.paragraph.add_run((self.authors))

        #self.report.document.add_page_break()
        # Add the first header
        self.paragraph = self.report.document.add_paragraph()
        self.report.document.add_heading(self.report.title, 0)
