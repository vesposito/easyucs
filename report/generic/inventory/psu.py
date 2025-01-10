# coding: utf-8
# !/usr/bin/env python

""" psu.py: Easy UCS Deployment Tool """

from report.ucs.section import UcsReportSection
from report.ucs.table import UcsReportTable


class UcsPsuReportSection(UcsReportSection):
    def __init__(self, order_id, parent, device, title):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if self.report.size == "full":
            self.content_list.append(
                UcsPsuReportTable(
                    order_id=self.report.get_current_order_id(), parent=self, psu=device.power_supplies, centered=True)
            )


class UcsPsuReportTable(UcsReportTable):
    def __init__(self, order_id, parent, psu, centered=False):
        rows = [["ID", "SKU", "Model", "Serial Number"]]

        for power_supply in psu:
            if hasattr(power_supply, 'name'):  # IMC doesn't have .name
                name = power_supply.name
            else:
                name = power_supply.model

            rows.append([power_supply.id, power_supply.sku, name, power_supply.serial])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows)
