# coding: utf-8
# !/usr/bin/env python

""" architecture.py: Easy UCS Deployment Tool """

from report.content import *
from report.generic.architecture import UcsDomainInfraCablingReportSection
from report.ucs.section import UcsReportSection
from report.ucs.table import UcsReportTable


class UcsSystemArchitectureReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = "Architecture"
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        self.content_list.append(UcsDomainInfraCablingReportSection(self.report.get_current_order_id(), parent=self,
                                                                    domain=self.report.inventory))
        self.content_list.append(UcsSystemNetworkNeighborsReportSection(self.report.get_current_order_id(),
                                                                        parent=self))


class UcsSystemNetworkNeighborsReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = "Network Neighbors"
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        if self.report.inventory.lan_neighbors:
            self.content_list.append(
                UcsSystemLanNeighborsReportSection(order_id=self.report.get_current_order_id(), parent=self))
        if self.report.inventory.san_neighbors:
            self.content_list.append(
                UcsSystemSanNeighborsReportSection(order_id=self.report.get_current_order_id(), parent=self))


class UcsSystemLanNeighborsReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = "LAN Neighbors"
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        lan_neighbors_path = self.report.img_path + "infra_lan_neighbors.png"
        self.content_list.append(GenericReportImage(order_id=self.report.get_current_order_id(), parent=self,
                                                    path=lan_neighbors_path, centered=True, size=18))

        self.content_list.append(
            UcsSystemLanNeighborsConnectivityTable(order_id=self.report.get_current_order_id(), parent=self,
                                                   fis=self.report.inventory.fabric_interconnects, centered=False)
        )


class UcsSystemLanNeighborsConnectivityTable(UcsReportTable):
    def __init__(self, order_id, parent, fis, centered=False, autofit=True):
        rows = [["Fabric", "Fabric Port", "Remote Name", "Remote Interface", "Remote Model", "Remote S/N",
                 "Transceiver SKU/Type", "Transceiver S/N", "Transceiver Length"]]

        for fi in fis:
            for port in fi.ports:
                if port.type == "lan":
                    if hasattr(port, 'neighbor_entries'):
                        if port.neighbor_entries:
                            for neighbor_entry in port.neighbor_entries:
                                fi_id = fi.id
                                if port.aggr_port_id:
                                    fi_port = port.slot_id + "/" + port.aggr_port_id + "/" + port.port_id
                                else:
                                    fi_port = port.slot_id + "/" + port.port_id

                                remote_name = ""
                                if hasattr(neighbor_entry, "lldp_system_name"):
                                    if neighbor_entry.lldp_system_name:
                                        remote_name = neighbor_entry.lldp_system_name
                                if hasattr(neighbor_entry, "cdp_system_name") and not remote_name:
                                    if neighbor_entry.cdp_system_name:
                                        remote_name = neighbor_entry.cdp_system_name

                                remote_interface = ""
                                if hasattr(neighbor_entry, "cdp_remote_interface"):
                                    if neighbor_entry.cdp_remote_interface:
                                        remote_interface = neighbor_entry.cdp_remote_interface
                                if hasattr(neighbor_entry, "lldp_remote_interface") and not remote_interface:
                                    if neighbor_entry.lldp_remote_interface:
                                        remote_interface = neighbor_entry.lldp_remote_interface

                                remote_device_model = neighbor_entry.model
                                remote_sn = neighbor_entry.serial

                                if len(port.transceivers) == 1:
                                    if port.transceivers[0].sku:
                                        transceiver_type = port.transceivers[0].sku
                                    else:
                                        transceiver_type = port.transceivers[0].type
                                    transceiver_sn = port.transceivers[0].serial
                                    transceiver_length = port.transceivers[0].length
                                else:
                                    transceiver_type = ""
                                    transceiver_sn = ""
                                    transceiver_length = ""
                                rows.append([fi_id, fi_port, remote_name, remote_interface,
                                             remote_device_model, remote_sn, transceiver_type, transceiver_sn,
                                             transceiver_length])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows, autofit=autofit,
                                font_size=8)


class UcsSystemSanNeighborsReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = "SAN Neighbors"
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        san_neighbors_path = self.report.img_path + "infra_san_neighbors.png"
        self.content_list.append(
            GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=san_neighbors_path,
                               centered=True, size=18))

        self.content_list.append(
            UcsSystemSanNeighborsConnectivityTable(order_id=self.report.get_current_order_id(), parent=self,
                                                   fis=self.report.inventory.fabric_interconnects, centered=False)
        )


class UcsSystemSanNeighborsConnectivityTable(UcsReportTable):
    def __init__(self, order_id, parent, fis, centered=False, autofit=True):
        rows = [["Fabric", "Fabric Port", "Remote Mgmt IP", "Remote WWNN", "Remote WWPN",
                 "Transceiver SKU/Type", "Transceiver S/N", "Transceiver Length"]]

        for fi in fis:
            for port in fi.ports:
                if port.type == "san":
                    if hasattr(port, 'neighbor_entries'):
                        if port.neighbor_entries:
                            for neighbor_entry in port.neighbor_entries:
                                fi_id = fi.id
                                if port.aggr_port_id:
                                    fi_port = port.slot_id + "/" + port.aggr_port_id + "/" + port.port_id
                                else:
                                    fi_port = port.slot_id + "/" + port.port_id

                                fabric_mgmt_addr = neighbor_entry.fabric_mgmt_addr \
                                    if neighbor_entry.fabric_mgmt_addr != "null" else None
                                fabric_nwwn = neighbor_entry.fabric_nwwn
                                fabric_pwwn = neighbor_entry.fabric_pwwn

                                if len(port.transceivers) == 1:
                                    if port.transceivers[0].sku:
                                        transceiver_type = port.transceivers[0].sku
                                    else:
                                        transceiver_type = port.transceivers[0].type
                                    transceiver_sn = port.transceivers[0].serial
                                    transceiver_length = port.transceivers[0].length
                                else:
                                    transceiver_type = ""
                                    transceiver_sn = ""
                                    transceiver_length = ""
                                rows.append([fi_id, fi_port, fabric_mgmt_addr, fabric_nwwn, fabric_pwwn,
                                             transceiver_type, transceiver_sn, transceiver_length])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows, autofit=autofit,
                                font_size=8)
