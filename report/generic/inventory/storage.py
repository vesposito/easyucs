# coding: utf-8
# !/usr/bin/env python

""" storage.py: Easy UCS Deployment Tool """

from report.ucs.section import UcsReportSection
from report.ucs.table import UcsReportTable


class UcsDiskReportTable(UcsReportTable):
    def __init__(self, order_id, parent, disks, centered=False):
        rows = [["ID", "PCIe Slot", "SKU", "Drive Type", "Connection Protocol", "Size", "Block Size", "RPM"]]

        for disk in disks:
            connection_protocol = None
            if hasattr(disk, "link_speed"):
                if disk.link_speed not in ["unknown", "NA", None]:
                    connection_protocol = str(disk.connection_protocol) + ' (' + str(disk.link_speed) + 'Gbps)'
                else:
                    connection_protocol = str(disk.connection_protocol)
            rpm = None
            if hasattr(disk, "rotational_speed_marketing"):
                rpm = disk.rotational_speed_marketing if disk.rotational_speed_marketing != 0 else None
            block_size = None
            if hasattr(disk, "block_size"):
                block_size = disk.block_size
            pcie_slot = None
            if hasattr(disk, "slot_type") and hasattr(disk, "pci_slot"):
                if disk.slot_type == "pcie-nvme":
                    pcie_slot = disk.pci_slot
            rows.append([disk.id, pcie_slot, disk.sku, disk.drive_type, connection_protocol, disk.size_marketing,
                         block_size, rpm])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows)


class UcsStorageControllerReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title, device):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if self.report.size == "full":
            if device.disks:
                self.content_list.append(
                    UcsDiskReportTable(order_id=self.report.get_current_order_id(), parent=self, disks=device.disks,
                                       centered=True))


class UcsNvmeDrivesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title, device):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if self.report.size == "full":
            if device.nvme_drives:
                self.content_list.append(
                    UcsDiskReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                       disks=device.nvme_drives, centered=True))
