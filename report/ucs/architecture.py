# coding: utf-8
# !/usr/bin/env python

""" architecture.py: Easy UCS Deployment Tool """

import os.path

from report.content import *
from report.ucs.section import UcsReportSection
from report.ucs.table import UcsReportTable


class UcsSystemArchitectureReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Architecture")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        self.content_list.append(UcsSystemInfraCablingReportSection(self.report.get_current_order_id(), parent=self))
        self.content_list.append(UcsSystemNetworkNeighborsReportSection(self.report.get_current_order_id(),
                                                                        parent=self))


class UcsSystemInfraCablingReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Internal Infrastructure cabling")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        if self.report.inventory.chassis:
            if self.report.inventory.fabric_interconnects[0].model not in ["UCS-FI-M-6324", "UCSX-S9108-100G"]:
                self.content_list.append(
                    UcsSystemInfraCablingAllChassisReportSection(order_id=self.report.get_current_order_id(),
                                                                 parent=self))
            else:
                # Checking if we have a second chassis in UCS Mini/X-Direct, otherwise infra section is not needed
                if len(self.report.inventory.chassis) > 1:
                    self.content_list.append(
                        UcsSystemInfraCablingAllChassisReportSection(order_id=self.report.get_current_order_id(),
                                                                     parent=self))
        if self.report.inventory.rack_units:
            self.content_list.append(
                UcsSystemInfraCablingAllRacksReportSection(order_id=self.report.get_current_order_id(), parent=self))

        if self.report.inventory.rack_enclosures:
            self.content_list.append(
                UcsSystemInfraCablingAllRackEnclosuresReportSection(order_id=self.report.get_current_order_id(),
                                                                    parent=self))


class UcsSystemInfraCablingAllChassisReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Chassis Internal Infrastructure cabling")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        for chassis in self.report.inventory.chassis:
            if (chassis.id == "1" and self.report.inventory.fabric_interconnects[0].model in
                    ["UCS-FI-M-6324", "UCSX-S9108-100G"]):
                # We do not create a section for chassis 1 in UCS Mini/X-Direct
                continue
            chassis_name = chassis.id
            if chassis.user_label:
                chassis_name = chassis.id + " - " + chassis.user_label
            self.content_list.append(
                UcsSystemInfraCablingChassisReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                          title=_("Chassis ") + chassis_name, chassis=chassis))


class UcsSystemInfraCablingChassisReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title, chassis):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        path = self.report.img_path + "infra_" + "chassis_" + chassis.id + ".png"
        if os.path.exists(path):
            self.content_list.append(
                GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path,
                                   centered=True, size=18)
            )

            self.content_list.append(
                UcsSystemInfraCablingChassisConnectivityTable(order_id=self.report.get_current_order_id(), parent=self,
                                                              fis=self.report.inventory.fabric_interconnects,
                                                              fexs=self.report.inventory.fabric_extenders,
                                                              chassis=chassis, centered=True)
            )
        else:
            self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                       string=_("This device is not connected to any FI")))


class UcsSystemInfraCablingChassisConnectivityTable(UcsReportTable):
    def __init__(self, order_id, parent, fis, fexs, chassis, centered=False, autofit=True):
        ext_port_type = "SIOC" if chassis.model in ["UCSC-C3X60", "UCSS-S3260"] else "IOM"
        rows = [[_("Fabric"), _("Fabric Port"), _("FEX ID"), _("FEX Fabric Port"), _("FEX Host Port"), ext_port_type,
                 ext_port_type + _(" Port"), _("Transceiver SKU/Type"), _("Transceiver S/N"), _("Transceiver Length")]]

        for fi in fis:
            for port in fi.ports:
                if hasattr(port, 'peer'):
                    if port.peer:
                        fi_id = fi.id
                        if port.aggr_port_id:
                            fi_port = port.slot_id + "/" + port.aggr_port_id + "/" + port.port_id
                        else:
                            fi_port = port.slot_id + "/" + port.port_id

                        if "chassis" in port.peer.keys():
                            if str(port.peer['chassis']) == chassis.id:
                                iom = port.peer['slot']
                                iom_port = port.peer['port']
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
                                rows.append([fi_id, fi_port, "", "", "", iom, iom_port,
                                             transceiver_type, transceiver_sn,
                                             transceiver_length])

                        if "fex" in port.peer.keys():
                            for fex in fexs:
                                # We need to find the FEX and the associated peer port
                                if fex.id == str(port.peer['fex']):
                                    fex_fabric_port = str(port.peer['slot']) + "/" + str(port.peer['port'])
                                    for fex_host_port in fex.host_ports:
                                        if fex_host_port.peer:
                                            if "chassis" in fex_host_port.peer.keys():
                                                if str(fex_host_port.peer['chassis']) == chassis.id:
                                                    fex_id = fex.id
                                                    if fex_host_port.aggr_port_id:
                                                        fex_port = fex_host_port.slot_id + "/" + \
                                                                   fex_host_port.aggr_port_id + "/" + \
                                                                   fex_host_port.port_id
                                                    else:
                                                        fex_port = fex_host_port.slot_id + "/" + fex_host_port.port_id
                                                    adaptor = fex_host_port.peer['slot']
                                                    adaptor_port = fex_host_port.peer['port']
                                                    if len(fex_host_port.transceivers) == 1:
                                                        if fex_host_port.transceivers[0].sku:
                                                            transceiver_type = fex_host_port.transceivers[0].sku
                                                        else:
                                                            transceiver_type = fex_host_port.transceivers[0].type
                                                        transceiver_sn = fex_host_port.transceivers[0].serial
                                                        transceiver_length = fex_host_port.transceivers[0].length
                                                    else:
                                                        transceiver_type = ""
                                                        transceiver_sn = ""
                                                        transceiver_length = ""
                                                    rows.append(
                                                        [fi_id, fi_port, fex_id, fex_fabric_port, fex_port,
                                                         adaptor, adaptor_port, transceiver_type,
                                                         transceiver_sn,
                                                         transceiver_length])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows, autofit=autofit)


class UcsSystemInfraCablingAllRacksReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Rack Servers Internal Infrastructure cabling")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        for rack in self.report.inventory.rack_units:
            rack_name = rack.id
            if rack.user_label:
                rack_name = rack.id + " - " + rack.user_label
            self.content_list.append(
                UcsSystemInfraCablingRackReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                       title=_("Rack ") + rack_name, rack=rack))


class UcsSystemInfraCablingRackReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title, rack):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        path = self.report.img_path + "infra_" + "rack_" + rack.id + ".png"
        if os.path.exists(path):
            self.content_list.append(
                GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path,
                                   centered=True, size=18))

            self.content_list.append(
                UcsSystemInfraCablingRackConnectivityTable(order_id=self.report.get_current_order_id(), parent=self,
                                                           fis=self.report.inventory.fabric_interconnects,
                                                           fexs=self.report.inventory.fabric_extenders, rack=rack,
                                                           centered=True)
            )
        else:
            self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                       string=_("This device is not connected to any FI or FEX")))


class UcsSystemInfraCablingRackConnectivityTable(UcsReportTable):
    def __init__(self, order_id, parent, fis, fexs, rack, centered=False, autofit=True):
        rows = [[_("Fabric"), _("Fabric Port"), _("FEX ID"), _("FEX Fabric Port"), _("FEX Host Port"), _("Adaptor ID"),
                 _("Adaptor Port"), _("Transceiver SKU/Type"), _("Transceiver S/N"), _("Transceiver Length")]]

        for fi in fis:
            for port in fi.ports:
                if hasattr(port, 'peer'):
                    if port.peer:
                        fi_id = fi.id
                        if port.aggr_port_id:
                            fi_port = port.slot_id + "/" + port.aggr_port_id + "/" + port.port_id
                        else:
                            fi_port = port.slot_id + "/" + port.port_id

                        if "rack" in port.peer.keys():
                            if str(port.peer['rack']) == rack.id:
                                adaptor = port.peer['slot']
                                adaptor_port = port.peer['port']
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
                                rows.append(
                                    [fi_id, fi_port, "", "", "",
                                     adaptor, adaptor_port, transceiver_type,
                                     transceiver_sn,
                                     transceiver_length])

                        if "fex" in port.peer.keys():
                            for fex in fexs:
                                # We need to find the FEX and the associated peer port
                                if fex.id == str(port.peer['fex']):
                                    fex_fabric_port = str(port.peer['slot']) + "/" + str(port.peer['port'])
                                    for fex_host_port in fex.host_ports:
                                        if fex_host_port.peer:
                                            if "rack" in fex_host_port.peer.keys():
                                                if str(fex_host_port.peer['rack']) == rack.id:
                                                    fex_id = fex.id
                                                    if fex_host_port.aggr_port_id:
                                                        fex_port = fex_host_port.slot_id + "/" + \
                                                                   fex_host_port.aggr_port_id + "/" + \
                                                                   fex_host_port.port_id
                                                    else:
                                                        fex_port = fex_host_port.slot_id + "/" + fex_host_port.port_id
                                                    adaptor = fex_host_port.peer['slot']
                                                    adaptor_port = fex_host_port.peer['port']
                                                    if len(fex_host_port.transceivers) == 1:
                                                        if fex_host_port.transceivers[0].sku:
                                                            transceiver_type = fex_host_port.transceivers[0].sku
                                                        else:
                                                            transceiver_type = fex_host_port.transceivers[0].type
                                                        transceiver_sn = fex_host_port.transceivers[0].serial
                                                        transceiver_length = fex_host_port.transceivers[0].length
                                                    else:
                                                        transceiver_type = ""
                                                        transceiver_sn = ""
                                                        transceiver_length = ""
                                                    rows.append(
                                                        [fi_id, fi_port, fex_id, fex_fabric_port, fex_port,
                                                         adaptor, adaptor_port, transceiver_type,
                                                         transceiver_sn,
                                                         transceiver_length])

        # In case all racks are not connected, this prevents an IndexError exception
        if len(rows) == 1:
            column_number = 0
        else:
            column_number = len(rows[1])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=column_number, centered=centered, cells_list=rows, autofit=autofit)


class UcsSystemInfraCablingAllRackEnclosuresReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Rack Enclosures Internal Infrastructure cabling")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        for rack_enclosure in self.report.inventory.rack_enclosures:
            rack_enclosure_name = rack_enclosure.id
            self.content_list.append(
                UcsSystemInfraCablingRackEnclosureReportSection(order_id=self.report.get_current_order_id(),
                                                                parent=self,
                                                                title=_("Rack Enclosure ") + rack_enclosure_name,
                                                                rack_enclosure=rack_enclosure))


class UcsSystemInfraCablingRackEnclosureReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title, rack_enclosure):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        path = self.report.img_path + "infra_" + "rack_enclosure_" + rack_enclosure.id + ".png"
        if os.path.exists(path):
            self.content_list.append(
                GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path,
                                   centered=True, size=18))

            self.content_list.append(
                UcsSystemInfraCablingRackEnclosureConnectivityTable(order_id=self.report.get_current_order_id(),
                                                                    parent=self,
                                                                    fis=self.report.inventory.fabric_interconnects,
                                                                    fexs=self.report.inventory.fabric_extenders,
                                                                    rack_enclosure=rack_enclosure, centered=True)
            )
        else:
            self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                       string=_("This device is not connected to any FI or FEX")))


class UcsSystemInfraCablingRackEnclosureConnectivityTable(UcsReportTable):
    def __init__(self, order_id, parent, fis, fexs, rack_enclosure, centered=False, autofit=True):
        rows = [[_("Fabric"), _("Fabric Port"), _("FEX ID"), _("FEX Fabric Port"), _("FEX Host Port"), _("Server ID"),
                 _("Server Node Slot"), _("Adaptor ID"), _("Adaptor Port"), _("Transceiver SKU/Type"),
                 _("Transceiver S/N"), _("Transceiver Length")]]

        for fi in fis:
            for port in fi.ports:
                if hasattr(port, 'peer'):
                    if port.peer:
                        fi_id = fi.id
                        if port.aggr_port_id:
                            fi_port = port.slot_id + "/" + port.aggr_port_id + "/" + port.port_id
                        else:
                            fi_port = port.slot_id + "/" + port.port_id

                        if "rack" in port.peer.keys():
                            for server_node in rack_enclosure.server_nodes:
                                if str(port.peer['rack']) == server_node.id:
                                    adaptor = port.peer['slot']
                                    adaptor_port = port.peer['port']
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
                                    rows.append(
                                        [fi_id, fi_port, "", "", "", server_node.id, server_node.slot_id,
                                         adaptor, adaptor_port, transceiver_type, transceiver_sn, transceiver_length])

                        if "fex" in port.peer.keys():
                            for fex in fexs:
                                # We need to find the FEX and the associated peer port
                                if fex.id == str(port.peer['fex']):
                                    fex_fabric_port = str(port.peer['slot']) + "/" + str(port.peer['port'])
                                    for fex_host_port in fex.host_ports:
                                        if fex_host_port.peer:
                                            if "rack" in fex_host_port.peer.keys():
                                                for server_node in rack_enclosure.server_nodes:
                                                    if str(fex_host_port.peer['rack']) == server_node.id:
                                                        fex_id = fex.id
                                                        if fex_host_port.aggr_port_id:
                                                            fex_port = fex_host_port.slot_id + "/" + \
                                                                       fex_host_port.aggr_port_id + "/" + \
                                                                       fex_host_port.port_id
                                                        else:
                                                            fex_port = fex_host_port.slot_id + "/" + \
                                                                       fex_host_port.port_id
                                                        adaptor = fex_host_port.peer['slot']
                                                        adaptor_port = fex_host_port.peer['port']
                                                        if len(fex_host_port.transceivers) == 1:
                                                            if fex_host_port.transceivers[0].sku:
                                                                transceiver_type = fex_host_port.transceivers[0].sku
                                                            else:
                                                                transceiver_type = fex_host_port.transceivers[0].type
                                                            transceiver_sn = fex_host_port.transceivers[0].serial
                                                            transceiver_length = fex_host_port.transceivers[0].length
                                                        else:
                                                            transceiver_type = ""
                                                            transceiver_sn = ""
                                                            transceiver_length = ""
                                                        rows.append(
                                                            [fi_id, fi_port, fex_id, fex_fabric_port, fex_port,
                                                             server_node.id, server_node.slot_id, adaptor, adaptor_port,
                                                             transceiver_type, transceiver_sn, transceiver_length])

        # In case all racks are not connected, this prevents an IndexError exception
        if len(rows) == 1:
            column_number = 0
        else:
            column_number = len(rows[1])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=column_number, centered=centered, cells_list=rows, autofit=autofit)


class UcsSystemNetworkNeighborsReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Network Neighbors")
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
            title = _("LAN Neighbors")
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
        rows = [[_("Fabric"), _("Fabric Port"), _("Remote Name"), _("Remote Interface"), _("Remote Model"),
                 _("Remote S/N"), _("Transceiver SKU/Type"), _("Transceiver S/N"), _("Transceiver Length")]]

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
            title = _("SAN Neighbors")
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
        rows = [[_("Fabric"), _("Fabric Port"), _("Remote Mgmt IP"), _("Remote WWNN"), _("Remote WWPN"),
                 _("Transceiver SKU/Type"), _("Transceiver S/N"), _("Transceiver Length")]]

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
