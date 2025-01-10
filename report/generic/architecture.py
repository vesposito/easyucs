# coding: utf-8
# !/usr/bin/env python

""" architecture.py: Easy UCS Deployment Tool """

import os.path

from report.content import *
from report.ucs.section import UcsReportSection
from report.ucs.table import UcsReportTable


class UcsDomainArchitectureReportSection(UcsReportSection):
    def __init__(self, order_id, parent, domain, title=""):
        if not title:
            title = "Architecture"
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        self.content_list.append(UcsDomainInfraCablingReportSection(
            self.report.get_current_order_id(), parent=self, domain=domain))
        # self.content_list.append(UcsSystemNetworkNeighborsReportSection(self.report.get_current_order_id(),
        #                                                                 parent=self))


class UcsDomainInfraCablingReportSection(UcsReportSection):
    def __init__(self, order_id, parent, domain, title=""):
        if not title:
            title = "Internal Infrastructure cabling"
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        if domain.chassis:
            if domain.fabric_interconnects[0].model not in ["UCS-FI-M-6324", "UCSX-S9108-100G"]:
                self.content_list.append(
                    UcsDomainInfraCablingAllChassisReportSection(
                        order_id=self.report.get_current_order_id(), parent=self, domain=domain))
            else:
                # Checking if we have a second chassis in UCS Mini/X-Direct, otherwise infra section is not needed
                if len(domain.chassis) > 1:
                    self.content_list.append(
                        UcsDomainInfraCablingAllChassisReportSection(
                            order_id=self.report.get_current_order_id(), parent=self, domain=domain))
        if domain.rack_units:
            self.content_list.append(
                UcsDomainInfraCablingAllRacksReportSection(
                    order_id=self.report.get_current_order_id(), parent=self, domain=domain))

        if hasattr(domain, "rack_enclosures") and domain.rack_enclosures:
            self.content_list.append(
                UcsDomainInfraCablingAllRackEnclosuresReportSection(
                    order_id=self.report.get_current_order_id(), parent=self, domain=domain))


class UcsDomainInfraCablingAllChassisReportSection(UcsReportSection):
    def __init__(self, order_id, parent, domain, title=""):
        if not title:
            title = "Chassis Internal Infrastructure cabling"
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        for chassis in domain.chassis:
            if (chassis.id == "1" and self.report.inventory.fabric_interconnects[0].model in
                    ["UCS-FI-M-6324", "UCSX-S9108-100G"]):
                # We do not create a section for chassis 1 in UCS Mini/X-Direct
                continue
            chassis_name = str(chassis.id)
            if chassis.user_label:
                chassis_name = str(chassis.id) + " - " + chassis.user_label
            self.content_list.append(
                UcsDomainInfraCablingChassisReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                          title="Chassis " + chassis_name, chassis=chassis))


class UcsDomainInfraCablingChassisReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title, chassis):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if chassis.__class__.__name__ in ["IntersightChassis"]:
            path = self.report.img_path + chassis._parent.name + "_infra_" + "chassis_" + str(chassis.id) + ".png"
        else:
            path = self.report.img_path + "infra_" + "chassis_" + str(chassis.id) + ".png"
        if os.path.exists(path):
            self.content_list.append(
                GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path,
                                   centered=True, size=18)
            )

            self.content_list.append(
                UcsDomainInfraCablingChassisConnectivityTable(order_id=self.report.get_current_order_id(), parent=self,
                                                              fis=chassis._parent.fabric_interconnects,
                                                              fexs=chassis._parent.fabric_extenders,
                                                              chassis=chassis, centered=True)
            )
        else:
            self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                       string="This device is not connected to any FI"))


class UcsDomainInfraCablingChassisConnectivityTable(UcsReportTable):
    def __init__(self, order_id, parent, fis, fexs, chassis, centered=False, autofit=True):
        ext_port_type = "SIOC" if chassis.model in ["UCSC-C3X60", "UCSS-S3260"] else "IOM"
        rows = [["Fabric", "Fabric Port", "FEX ID", "FEX Fabric Port", "FEX Host Port", ext_port_type,
                 ext_port_type + " Port", "Transceiver SKU/Type", "Transceiver S/N", "Transceiver Length"]]

        for fi in fis:
            for port in fi.ports:
                if hasattr(port, 'peer'):
                    if port.peer:
                        fi_id = fi.id
                        if port.aggr_port_id:
                            fi_port = str(port.slot_id) + "/" + str(port.aggr_port_id) + "/" + str(port.port_id)
                        else:
                            fi_port = str(port.slot_id) + "/" + str(port.port_id)

                        if "chassis" in port.peer.keys():
                            if str(port.peer['chassis']) == str(chassis.id):
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
                                if str(fex.id) == str(port.peer['fex']):
                                    fex_fabric_port = str(port.peer['slot']) + "/" + str(port.peer['port'])
                                    for fex_host_port in fex.host_ports:
                                        if fex_host_port.peer:
                                            if "chassis" in fex_host_port.peer.keys():
                                                if str(fex_host_port.peer['chassis']) == str(chassis.id):
                                                    fex_id = str(fex.id)
                                                    if fex_host_port.aggr_port_id:
                                                        fex_port = str(fex_host_port.slot_id) + "/" + \
                                                                   str(fex_host_port.aggr_port_id) + "/" + \
                                                                   str(fex_host_port.port_id)
                                                    else:
                                                        fex_port = (str(fex_host_port.slot_id) + "/" +
                                                                    str(fex_host_port.port_id))
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


class UcsDomainInfraCablingAllRacksReportSection(UcsReportSection):
    def __init__(self, order_id, parent, domain, title=""):
        if not title:
            title = "Rack Servers Internal Infrastructure cabling"
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        for rack in domain.rack_units:
            rack_name = str(rack.id)
            if rack.user_label:
                rack_name = str(rack.id) + " - " + rack.user_label
            self.content_list.append(
                UcsDomainInfraCablingRackReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                       title="Rack " + rack_name, rack=rack))


class UcsDomainInfraCablingRackReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title, rack):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if rack.__class__.__name__ in ["IntersightComputeRackUnit"]:
            path = self.report.img_path + rack._parent.name + "_infra_" + "rack_" + str(rack.id) + ".png"
        else:
            path = self.report.img_path + "infra_" + "rack_" + str(rack.id) + ".png"
        if os.path.exists(path):
            self.content_list.append(
                GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path,
                                   centered=True, size=18))

            self.content_list.append(
                UcsDomainInfraCablingRackConnectivityTable(order_id=self.report.get_current_order_id(), parent=self,
                                                           fis=rack._parent.fabric_interconnects,
                                                           fexs=rack._parent.fabric_extenders, rack=rack,
                                                           centered=True)
            )
        else:
            self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                       string="This device is not connected to any FI or FEX"))


class UcsDomainInfraCablingRackConnectivityTable(UcsReportTable):
    def __init__(self, order_id, parent, fis, fexs, rack, centered=False, autofit=True):
        rows = [["Fabric", "Fabric Port", "FEX ID", "FEX Fabric Port", "FEX Host Port", "Adaptor ID",
                 "Adaptor Port", "Transceiver SKU/Type", "Transceiver S/N", "Transceiver Length"]]

        for fi in fis:
            for port in fi.ports:
                if hasattr(port, 'peer'):
                    if port.peer:
                        fi_id = fi.id
                        if port.aggr_port_id:
                            fi_port = str(port.slot_id) + "/" + str(port.aggr_port_id) + "/" + str(port.port_id)
                        else:
                            fi_port = str(port.slot_id) + "/" + str(port.port_id)

                        if "rack" in port.peer.keys():
                            if str(port.peer['rack']) == str(rack.id):
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
                                if str(fex.id) == str(port.peer['fex']):
                                    fex_fabric_port = str(port.peer['slot']) + "/" + str(port.peer['port'])
                                    for fex_host_port in fex.host_ports:
                                        if fex_host_port.peer:
                                            if "rack" in fex_host_port.peer.keys():
                                                if str(fex_host_port.peer['rack']) == str(rack.id):
                                                    fex_id = str(fex.id)
                                                    if fex_host_port.aggr_port_id:
                                                        fex_port = str(fex_host_port.slot_id) + "/" + \
                                                                   str(fex_host_port.aggr_port_id) + "/" + \
                                                                   str(fex_host_port.port_id)
                                                    else:
                                                        fex_port = (str(fex_host_port.slot_id) + "/" +
                                                                    str(fex_host_port.port_id))
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


class UcsDomainInfraCablingAllRackEnclosuresReportSection(UcsReportSection):
    def __init__(self, order_id, parent, domain, title=""):
        if not title:
            title = "Rack Enclosures Internal Infrastructure cabling"
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        for rack_enclosure in domain.rack_enclosures:
            rack_enclosure_name = str(rack_enclosure.id)
            self.content_list.append(
                UcsDomainInfraCablingRackEnclosureReportSection(
                    order_id=self.report.get_current_order_id(), parent=self,
                    title="Rack Enclosure " + rack_enclosure_name, rack_enclosure=rack_enclosure)
            )


class UcsDomainInfraCablingRackEnclosureReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title, rack_enclosure):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        path = self.report.img_path + "infra_" + "rack_enclosure_" + str(rack_enclosure.id) + ".png"
        if os.path.exists(path):
            self.content_list.append(
                GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path,
                                   centered=True, size=18))

            self.content_list.append(
                UcsDomainInfraCablingRackEnclosureConnectivityTable(
                    order_id=self.report.get_current_order_id(), parent=self,
                    fis=rack_enclosure._parent.fabric_interconnects, fexs=rack_enclosure._parent.fabric_extenders,
                    rack_enclosure=rack_enclosure, centered=True
                )
            )
        else:
            self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                       string="This device is not connected to any FI or FEX"))


class UcsDomainInfraCablingRackEnclosureConnectivityTable(UcsReportTable):
    def __init__(self, order_id, parent, fis, fexs, rack_enclosure, centered=False, autofit=True):
        rows = [["Fabric", "Fabric Port", "FEX ID", "FEX Fabric Port", "FEX Host Port", "Server ID",
                 "Server Node Slot", "Adaptor ID", "Adaptor Port", "Transceiver SKU/Type",
                 "Transceiver S/N", "Transceiver Length"]]

        for fi in fis:
            for port in fi.ports:
                if hasattr(port, 'peer'):
                    if port.peer:
                        fi_id = fi.id
                        if port.aggr_port_id:
                            fi_port = str(port.slot_id) + "/" + str(port.aggr_port_id) + "/" + str(port.port_id)
                        else:
                            fi_port = str(port.slot_id) + "/" + str(port.port_id)

                        if "rack" in port.peer.keys():
                            for server_node in rack_enclosure.server_nodes:
                                if str(port.peer['rack']) == str(server_node.id):
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
                                        [fi_id, fi_port, "", "", "", str(server_node.id), server_node.slot_id,
                                         adaptor, adaptor_port, transceiver_type, transceiver_sn, transceiver_length])

                        if "fex" in port.peer.keys():
                            for fex in fexs:
                                # We need to find the FEX and the associated peer port
                                if str(fex.id) == str(port.peer['fex']):
                                    fex_fabric_port = str(port.peer['slot']) + "/" + str(port.peer['port'])
                                    for fex_host_port in fex.host_ports:
                                        if fex_host_port.peer:
                                            if "rack" in fex_host_port.peer.keys():
                                                for server_node in rack_enclosure.server_nodes:
                                                    if str(fex_host_port.peer['rack']) == str(server_node.id):
                                                        fex_id = str(fex.id)
                                                        if fex_host_port.aggr_port_id:
                                                            fex_port = str(fex_host_port.slot_id) + "/" + \
                                                                       str(fex_host_port.aggr_port_id) + "/" + \
                                                                       str(fex_host_port.port_id)
                                                        else:
                                                            fex_port = str(fex_host_port.slot_id) + "/" + \
                                                                       str(fex_host_port.port_id)
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
                                                             str(server_node.id), server_node.slot_id, adaptor, adaptor_port,
                                                             transceiver_type, transceiver_sn, transceiver_length])

        # In case all racks are not connected, this prevents an IndexError exception
        if len(rows) == 1:
            column_number = 0
        else:
            column_number = len(rows[1])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=column_number, centered=centered, cells_list=rows, autofit=autofit)
