# coding: utf-8
# !/usr/bin/env python

""" table.py: Easy UCS Deployment Tool """

from report.content_table import GenericReportTable


class UcsReportTable(GenericReportTable):
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

        GenericReportTable.__init__(self, order_id=order_id, parent=parent, row_number=row_number,
                                    column_number=column_number, centered=centered, cells_list=cells_list, style=style,
                                    autofit=autofit, font_size=font_size)

    @staticmethod
    def get_name_and_sku(inventory_object):
        """
        Generate proper name depending on available attributes
        :param inventory_object:
        :return: key
        """
        key = ""

        if hasattr(inventory_object, "name"):
            if inventory_object.name:
                key = inventory_object.name
                if inventory_object.sku:
                    key = inventory_object.name + ' (' + inventory_object.sku + ')'
                elif inventory_object.model and inventory_object.model != inventory_object.name:
                    key = inventory_object.name + ' (' + inventory_object.model + ')'
        if not key:
            if inventory_object.sku:
                key = inventory_object.sku
            elif inventory_object.model:
                key = inventory_object.model

        return key
