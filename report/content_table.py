# coding: utf-8
# !/usr/bin/env python

""" content_table.py: Easy UCS Deployment Tool """

from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.shared import Pt

from report.content import GenericReportContent


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
            self.logger(level="warning",
                        message="Cells in the table are not the same size as the number of columns or rows")
            return False

        self.clean_empty()

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

        # Ajust list of index column to delete because we delete column one by one. So if I need to delete the
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
        for row_index in range(len(self.cells_list)):
            if row_index != 0:
                empty = True
                for column_in_row in self.cells_list[row_index]:
                    if isinstance(column_in_row, type(None)):
                        # Avoid issue with None value that is misinterpret by Word. We change None to empty string
                        self.cells_list[row_index][self.cells_list[row_index].index(column_in_row)] = ""
                    if not empty:
                        continue
                    if column_in_row == self.cells_list[row_index][0]:
                        continue
                    if column_in_row or column_in_row == 0:
                        empty = False
                if empty:
                    rows_to_delete.append(row_index)
        # Ajust list of index row to delete because we delete row one by one. So if I need to delete the
        # 2 and 3 row, once the 2nd row is deleted the 3rd row is now the 2nd
        for i in range(len(rows_to_delete)):
            rows_to_delete[i] = rows_to_delete[i] - i

        for row_to_delete in rows_to_delete:
            self.cells_list.pop(row_to_delete)

        self.row_number = len(self.cells_list)
        self.column_number = len(self.cells_list[0])

    def add_in_word_report(self):
        # self.logger(level="debug", message="Adding " + self.__class__.__name__ + " in word")
        table = self.report.document.add_table(rows=self.row_number, cols=self.column_number,
                                               style=self.style)
        table.alignment = int(bool(self.centered))

        for i in range(len(self.cells_list)):
            row = self.cells_list[i]
            row = list(filter(None.__ne__, row))  # Remove None values
            row_cells = table.rows[i].cells
            for j in range(0, len(row)):
                row_cells[j].text = str(row[j])
                row_cells[j].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                if self.autofit:
                    # For more info : https://github.com/python-openxml/python-docx/issues/209
                    row_cells[j]._tc.tcPr.tcW.type = 'auto'

        # Change to keep the table on one page 1/2 - Put all the value at False (default values)
        table.style.paragraph_format.keep_together = False
        table.style.paragraph_format.keep_with_next = False

        # Change the font size
        for row in table.rows:
            for cell in row.cells:
                paragraphs = cell.paragraphs
                for paragraph in paragraphs:
                    for run in paragraph.runs:
                        run.font.size = Pt(self.font_size)

        # Change to keep the table on one page 2/2
        # Put the entire table at "keep together" and then put all the rows, except the last one, at "keep with next"
        # Tips found here : https://wordribbon.tips.net/T012975_Keeping_Tables_on_One_Page
        table.style.paragraph_format.keep_together = True
        for row in table.rows[:-1]:
            for cell in row.cells:
                paragraphs = cell.paragraphs
                for paragraph in paragraphs:
                    paragraph.paragraph_format.keep_with_next = True

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
