# coding: utf-8
# !/usr/bin/env python

""" content_table.py: Easy UCS Deployment Tool """

from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.shared import Pt

from report.content import GenericReportContent
from reportlab.lib import colors

import textwrap
from reportlab.platypus import Paragraph, KeepTogether, Table, TableStyle, Spacer


def wrap_custom(source_text, separator_chars, width=70, keep_separators=True):
    current_length = 0
    latest_separator = -1
    current_chunk_start = 0
    output = ""
    char_index = 0
    while char_index < len(source_text):
        if source_text[char_index] == "\n":
            keep_separators = False
        if source_text[char_index] in separator_chars:
            latest_separator = char_index
        output += source_text[char_index]
        current_length += 1
        if current_length == width:
            if latest_separator >= current_chunk_start:
                # Valid earlier separator, cut there
                cutting_length = char_index - latest_separator
                if not keep_separators:
                    cutting_length += 1
                if cutting_length:
                    output = output[:-cutting_length]
                output += "\n"
                current_chunk_start = latest_separator + 1
                char_index = current_chunk_start
            else:
                # No separator found, hard cut
                output += "\n"
                current_chunk_start = char_index + 1
                latest_separator = current_chunk_start - 1
                char_index += 1
            current_length = 0
        else:
            char_index += 1
    return output


class GenericReportTable(GenericReportContent):
    def __init__(self, order_id, parent, row_number, column_number, centered=False, cells_list=[],
                 style="Light Grid Accent 1", autofit=True, font_size=10):
        """
        :param order_id:
        :param parent:
        :param row_number:
        :param column_number:
        :param centered:
        :param cells_list: example : list = [[1,2,3],[2,3,4]]
        :param style:
        :param autofit:
        :param font_size:
        """

        GenericReportContent.__init__(self, order_id=order_id, parent=parent, centered=centered)
        self.autofit = autofit
        self.cells_list = cells_list
        self.column_number = column_number
        self.font_size = font_size
        self.row_number = row_number
        self.style = style

        if len(self.cells_list) == self.row_number:
            self.cells_type = "row"
        elif len(self.cells_list) == self.column_number:
            self.cells_type = "column"
            self.__format_column_to_row()
        else:
            err_message = "Cells in the table are not the same size as the number of columns or rows"
            self.logger(level="warning", message=err_message)
            raise ValueError(err_message)

        self.clean_empty()

        self.table_style = TableStyle([("BOX", (0, 0), (-1, -1), 0.10, "#4983c6"),
                                       ("GRID", (0, 0), (-1, -1), 0.10, "#4983c6"),
                                       ("FONTSIZE", (0, 0), (-1, -1), 8),
                                       ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold")])

    def clean_empty(self):
        # Column
        columns_to_delete = []
        for column_index in range(len(self.cells_list[0])):
            empty = True
            for row in self.cells_list:
                if not empty:
                    continue
                if row == self.cells_list[0]:
                    # We skip the first row because it can't be empty in a "row" cells_type table
                    continue
                if row[column_index] or row[column_index] == 0:
                    empty = False
            if empty:
                columns_to_delete.append(column_index)

        # Adjust list of index column to delete because we delete column one by one. So if I need to delete the
        # 2 and 3 column, once the 2nd column is deleted the 3rd column is now the 2nd
        for i in range(len(columns_to_delete)):
            columns_to_delete[i] = columns_to_delete[i] - i

        for column_to_delete in columns_to_delete:
            for row in self.cells_list:
                row.pop(column_to_delete)

        self.row_number = len(self.cells_list)
        self.column_number = len(self.cells_list[0])

        # Rows
        rows_to_delete = []
        if self.column_number > 1:
            for row_index in range(len(self.cells_list)):
                if row_index != 0:
                    empty = True
                    for column_in_row in self.cells_list[row_index]:
                        if isinstance(column_in_row, type(None)):
                            # Avoid issue with None value that is misinterpreted by Word. We change None to empty string
                            self.cells_list[row_index][self.cells_list[row_index].index(column_in_row)] = ""
                        if not empty:
                            continue
                        if column_in_row == self.cells_list[row_index][0]:
                            continue
                        if column_in_row or column_in_row == 0:
                            empty = False
                    if empty:
                        rows_to_delete.append(row_index)
        # Adjust list of index row to delete because we delete row one by one. So if I need to delete the
        # 2 and 3 row, once the 2nd row is deleted the 3rd row is now the 2nd
        for i in range(len(rows_to_delete)):
            rows_to_delete[i] = rows_to_delete[i] - i

        for row_to_delete in rows_to_delete:
            self.cells_list.pop(row_to_delete)

        self.row_number = len(self.cells_list)
        self.column_number = len(self.cells_list[0])

    def add_in_word_report(self):
        # TO-DO: To make incompatible hardware more visible in the report similar to PDF REPORT,
        # self.logger(level="debug", message="Adding " + self.__class__.__name__ + " in word")
        table = self.report.document.add_table(rows=self.row_number, cols=self.column_number,
                                               style=self.style)
        table.alignment = int(bool(self.centered))

        # Change to keep the table on one page 1/2 - Put all the value at True (default values)
        table.style.paragraph_format.keep_together = True
        table.style.paragraph_format.keep_with_next = True

        for i in range(len(self.cells_list)):
            row = self.cells_list[i]
            row = list(filter(None.__ne__, row))  # Remove None values
            # Replace True with unicode check mark and False with unicode cross mark
            # row = ["\U00002705" if e is True else "\U0000274C" if e is False else e for e in row]
            row_cells = table.rows[i].cells
            for j in range(0, len(row)):
                if row[j] is True:
                    row[j] = "Yes"
                elif row[j] is False:
                    row[j] = "No"
                row_cells[j].text = str(row[j])
                row_cells[j].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                if self.autofit:
                    # For more info : https://github.com/python-openxml/python-docx/issues/209
                    row_cells[j]._tc.tcPr.tcW.type = 'auto'

                paragraphs = row_cells[j].paragraphs
                for paragraph in paragraphs:
                    # Change to keep the table on one page 2/2
                    # We have put the entire table at "Keep lines together" and "Keep with Next" in the template.docx.
                    # And then we unset the last row's "Keep with Next". To summarize we have all rows, except the
                    # last row at "Keep with Next"
                    # Tips found here : https://wordribbon.tips.net/T012975_Keeping_Tables_on_One_Page
                    if i == len(table.rows) - 1:
                        paragraph.paragraph_format.keep_with_next = False
                    # Change the font size only when self.font_size is not 10 cause the default font size is
                    # kept at 10 in the template.docx file
                    if self.font_size != 10:
                        for run in paragraph.runs:
                            run.font.size = Pt(self.font_size)

    def add_in_json_report(self, content):
        content["Table"] = True
        content["CellsList"] = {
            "Headers": self.cells_list[0],
            "Rows": [[cell if not isinstance(cell, bool) else ("Yes" if cell else "No") for cell in row] for row in
                     self.cells_list[1:]]
        }

        # Check if the headers contain "Compatible HW?" and "Compatible FW?"
        headers = content["CellsList"]["Headers"]
        rows = content["CellsList"]["Rows"]

        compatible_hw_index = -1
        compatible_fw_index = -1

        # Find the index of "Compatible HW?" and "Compatible FW?" headers if present
        if "Compatible HW?" in headers:
            compatible_hw_index = headers.index("Compatible HW?")
        if "Compatible FW?" in headers:
            compatible_fw_index = headers.index("Compatible FW?")

        # Check if either of the headers is present
        if compatible_hw_index != -1 or compatible_fw_index != -1:
            # If at least one of the headers is present, check for incompatibility
            incompatible_hardware = any(
                row[compatible_hw_index] == "No" for row in rows) if compatible_hw_index != -1 else False
            incompatible_firmware = any(
                row[compatible_fw_index] == "No" for row in rows) if compatible_fw_index != -1 else False

            content["IncompatibleHardware"] = incompatible_hardware
            content["IncompatibleFirmware"] = incompatible_firmware

    def add_in_pdf_report(self):
        if self.font_size > 8 or not self.font_size:
            self.font_size = 8
        self.report.pdf_element_list.append(Spacer(1, 10))
        table = []
        for i in range(len(self.cells_list)):
            column = []
            for j in range(len(self.cells_list[i])):
                if self.cells_list[i][j] is True:
                    self.cells_list[i][j] = "Yes"
                elif self.cells_list[i][j] is False:
                    self.cells_list[i][j] = "No"
                if chr(9989) in str(self.cells_list[i][j]):
                    self.cells_list[i][j] = self.cells_list[i][j].replace(chr(9989), "✓")
                # Wrapping the text inside the table cell so that it wouldn't bleed out of the page
                wrap_delimiter = [" ", "_", "-", "/", ":", "\n", "*"]
                if len(self.cells_list[i]) == 2:
                    word_len = 65 + abs(self.font_size - 8) * 4
                    if len(str(self.cells_list[i][j])) >= word_len:
                        p = self.cells_list[i][j]
                        self.cells_list[i][j] = wrap_custom(str(p), wrap_delimiter, word_len, True)
                elif len(self.cells_list[i]) == 3:
                    word_len = 45 + abs(self.font_size - 8) * 4
                    if len(str(self.cells_list[i][j])) >= word_len:
                        p = self.cells_list[i][j]
                        self.cells_list[i][j] = wrap_custom(str(p), wrap_delimiter, word_len, True)
                elif len(self.cells_list[i]) == 4:
                    word_len = 24 + abs(self.font_size - 8) * 4
                    if len(str(self.cells_list[i][j])) >= word_len:
                        p = self.cells_list[i][j]
                        self.cells_list[i][j] = wrap_custom(str(p), wrap_delimiter, word_len, True)
                elif len(self.cells_list[i]) == 5:
                    word_len = 22 + abs(self.font_size - 8) * 3
                    if len(str(self.cells_list[i][j])) >= word_len:
                        p = self.cells_list[i][j]
                        self.cells_list[i][j] = wrap_custom(str(p), wrap_delimiter, word_len, True)
                elif len(self.cells_list[i]) == 6:
                    word_len = 21 + abs(self.font_size - 8) * 3
                    if len(str(self.cells_list[i][j])) >= word_len:
                        p = self.cells_list[i][j]
                        self.cells_list[i][j] = wrap_custom(str(p), wrap_delimiter, word_len, True)
                elif len(self.cells_list[i]) == 7:
                    word_len = 18 + abs(self.font_size - 8) * 3
                    if len(str(self.cells_list[i][j])) >= word_len:
                        p = self.cells_list[i][j]
                        self.cells_list[i][j] = wrap_custom(str(p), wrap_delimiter, word_len, True)
                elif len(self.cells_list[i]) == 8:
                    word_len = 15 + abs(self.font_size - 8) * 3
                    if len(str(self.cells_list[i][j])) >= word_len:
                        p = self.cells_list[i][j]
                        self.cells_list[i][j] = wrap_custom(str(p), wrap_delimiter, word_len, True)
                elif len(self.cells_list[i]) == 9:
                    word_len = 12 + abs(self.font_size - 8) * 3
                    if len(str(self.cells_list[i][j])) >= word_len:
                        p = self.cells_list[i][j]
                        self.cells_list[i][j] = wrap_custom(str(p), wrap_delimiter, word_len, True)
                elif len(self.cells_list[i]) == 10:
                    word_len = 10 + abs(self.font_size - 8) * 3
                    if len(str(self.cells_list[i][j])) >= word_len:
                        p = self.cells_list[i][j]
                        self.cells_list[i][j] = wrap_custom(str(p), wrap_delimiter, word_len, True)
                elif len(self.cells_list[i]) >= 11:
                    word_len = 10 + abs(self.font_size - 8) * 1
                    if len(str(self.cells_list[i][j])) >= word_len:
                        p = self.cells_list[i][j]
                        self.cells_list[i][j] = wrap_custom(str(p), wrap_delimiter, word_len, True)
                # Truncating larger cells
                if self.cells_list[0][j] == "Description" and len(str(self.cells_list[i][j])) >= 156:
                    p = self.cells_list[i][j]
                    self.cells_list[i][j] = textwrap.shorten(p, width=10, placeholder='...')
                elif len(str(self.cells_list[i][j])) >= 1000:
                    # FIXME: This is a temporary fix, ideally if length of characters is too long in a cell, then
                    #  split the cells into multiple cells.
                    self.cells_list[i][j] = self.cells_list[i][j][:1000] + " ..."
                column.append(str(self.cells_list[i][j]))
            table.append(column)

        try:
            tables = Table(table, spaceAfter=0, repeatRows=1)
            tables.setStyle(self.table_style)
            column_len = len(table)
            if self.font_size:
                tables.setStyle(TableStyle([("FONTSIZE", (0, 0), (-1, -1), self.font_size)]))
            for each in range(column_len):
                if each % 2 == 0:
                    bg_color = "#dbe5f1"
                else:
                    bg_color = "#ffffff"
                tables.setStyle(TableStyle([("BACKGROUND", (0, each), (-1, each), bg_color)]))

            # Checking if the table has "Compatible HW?" / "Compatible FW?" columns
            if "Compatible HW?" in self.cells_list[0] or "Compatible FW?" in self.cells_list[0]:
                for i in range(len(self.cells_list)):
                    for j in range(len(self.cells_list[i])):
                        # Check if the value is No for Compatible HW or Compatible FW
                        if self.cells_list[0][j] == "Compatible HW?" and self.cells_list[i][j] == "No":
                            tables.setStyle(TableStyle([('BACKGROUND', (j, i), (j, i), colors.red)]))
                        elif self.cells_list[0][j] == "Compatible FW?" and self.cells_list[i][j] == "No":
                            tables.setStyle(TableStyle([('BACKGROUND', (j, i), (j, i), colors.yellow)]))

            self.report.pdf_element_list.append(KeepTogether(tables))
        except ValueError as err:
            self.logger(
                level="debug",
                message=f"Error while adding table of type {self.__class__.__name__} to the PDF report: {str(err)}"
            )

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
