# coding: utf-8
# !/usr/bin/env python

""" content_table.py: Easy UCS Deployment Tool """
from __init__ import __author__, __copyright__,  __version__, __status__


from docx.shared import Cm, Pt
from report.content import GenericReportContent
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.table import WD_ROW_HEIGHT_RULE
import os.path


class GenericReportTable(GenericReportContent):
    def __init__(self, order_id, parent, row_number, column_number, centered=False, cells_list=[],
                 style="Light Grid Accent 1", autofit=False, font_size=10):
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
        self.row_number = row_number
        self.column_number = column_number
        self.cells_list = cells_list
        self.style = style
        self.autofit = autofit
        self.font_size = font_size

        if len(self.cells_list) == self.row_number:
            self.cells_type = "row"
        elif len(self.cells_list) == self.column_number:
            self.cells_type = "column"
            self.__format_column_to_row()
        else:
            self.logger(level="warning",
                        message="Cells in the table are not the same size as the number of column or row")
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
                    # We skip the firt row because it can't be empty in a "row" cells_type table
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
        table.autofit = self.autofit
        table.style.font.size = Pt(self.font_size)
        # table.style.paragraph_format.widow_control = True
        # table.style.paragraph_format.keep_together = True
        # table.style.paragraph_format.keep_with_next = True

        for i in range(len(self.cells_list)):
            row = self.cells_list[i]
            row_cells = table.rows[i].cells
            for j in range(0, len(row)):
                row_cells[j].text = str(row[j])
                row_cells[j].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                if self.autofit:
                    row_cells[j].width = WD_ROW_HEIGHT_RULE.AUTO

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


class FiUcsReportTable(GenericReportTable):
    def __init__(self, order_id, parent, fi, centered=False):
        rows = [[_("Description"),_("Value")]]
        rows.append([_("FI"), fi.id])
        rows.append([_("SKU / Model"), fi.sku])
        rows.append([_("Serial Number"), fi.serial])
        rows.append([_("Firmware Package Version"), fi.firmware_package_version])

        GenericReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                    column_number=len(rows[1]), centered=centered, cells_list=rows)


class FexUcsReportTable(GenericReportTable):
    def __init__(self, order_id, parent, fex, centered=False):
        rows = [[_("Description"),_("Value")]]
        rows.append([_("FEX"), fex.id])
        rows.append([_("SKU / Model"), fex.sku])
        rows.append([_("Serial Number"), fex.serial])

        GenericReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                    column_number=len(rows[1]), centered=centered, cells_list=rows)


class RackUcsReportTable(GenericReportTable):
    def __init__(self, order_id, parent, rack, centered=False):
        rows = [[_("Description"),_("Value")]]
        rows.append([_("Rack Id"), rack.id])
        rows.append([_("SKU / Model"), rack.sku])
        rows.append([_("Serial Number"), rack.serial])
        rows.append([_("Total Memory"), rack.memory_total])
        rows.append([_("Adaptors"), len(rack.adaptors)])
        if rack.cpus:
            cpu_model = rack.cpus[0].model
            cores = rack.cpus[0].cores
            if len(rack.cpus) > 1:
                cpu_model = str(len(rack.cpus)) + "x " + rack.cpus[0].model
                cores = int(rack.cpus[0].cores) * len(rack.cpus)
            rows.append([_("CPU(s) Model"), cpu_model])
            rows.append([_("CPU(s) Cores"), cores])
        rows.append([_("GPU(s)"), len(rack.gpus)])
        if rack.gpus:
            gpu_models = rack.gpus[0].model
            for gpu in rack.gpus:
                if gpu_models != gpu.model:
                    # We avoid the first model with this condition
                    gpu_models = gpu_models + " / " + gpu.model
            rows.append([_("GPU(s)  Model"), gpu_models])

        GenericReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                    column_number=len(rows[1]), centered=centered, cells_list=rows)


class ChassisUcsReportTable(GenericReportTable):
    def __init__(self, order_id, parent, chassis, centered=False):
        rows = [[_("Description"),_("Value")]]
        rows.append([_("Chassis Id"), chassis.id])
        rows.append([_("SKU / Model"), chassis.name])
        rows.append([_("Serial Number"), chassis.serial])
        rows.append([_("Populated slots"), str(chassis.slots_populated) + "/" + str(chassis.slots_max)])
        rows.append([_("Free full size slots"), chassis.slots_free_full])
        if len(chassis.io_modules):
            rows.append([_("IO Modules"), len(chassis.io_modules)])
        if len(chassis.system_io_controllers):
            rows.append([_("SIOCs"), len(chassis.system_io_controllers)])

        GenericReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                    column_number=len(rows[1]), centered=centered, cells_list=rows)


class BladeUcsReportTable(GenericReportTable):
    def __init__(self, order_id, parent, blade, centered=False):
        rows = [[_("Description"),_("Value")]]
        rows.append([_("Blade Id"), blade.id])
        rows.append([_("SKU / Model"), blade.sku])
        rows.append([_("Serial Number"), blade.serial])
        rows.append([_("Total Memory"), blade.memory_total])
        rows.append([_("Adaptors"), len(blade.adaptors)])
        if blade.cpus:
            cpu_model = blade.cpus[0].model
            cores = blade.cpus[0].cores
            if len(blade.cpus) > 1:
                cpu_model = str(len(blade.cpus)) + "x " + str(blade.cpus[0].model)
                if blade.cpus[0].cores:
                    cores = int(blade.cpus[0].cores) * len(blade.cpus)
                else:
                    cores = "N/A"
            rows.append([_("CPU(s) Model"), cpu_model])
            rows.append([_("CPU(s) Cores"), cores])
        rows.append([_("GPU(s)"), len(blade.gpus)])
        if blade.gpus:
            gpu_models = blade.gpus[0].model
            for gpu in blade.gpus:
                if gpu_models != gpu.model:
                    # We avoid the first model with this condition
                    gpu_models = gpu_models + " / " + gpu.model
            rows.append([_("GPU(s)  Model"), gpu_models])

        GenericReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                    column_number=len(rows[1]), centered=centered, cells_list=rows)


class VlanUcsReportTable(GenericReportTable):
    def __init__(self, order_id, parent, vlans, centered=False):
        rows = [[_("VLAN ID"), _("VLAN Name")]]

        vlans.sort(key=lambda x: int(x.id), reverse=False)
        for vlan in vlans:
            rows.append([vlan.id, vlan.name])

        GenericReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                    column_number=len(rows[1]), centered=centered, cells_list=rows)


class VlanGroupUcsReportTable(GenericReportTable):
    def __init__(self, order_id, parent, vlan_groups, centered=False):
        rows = [[_("Name"),_("VLANs"), _("Native VLAN"), _("LAN Uplink Ports"), _("LAN Port Channel"),
                 _("Org Permissions")]]

        for vlan_group in vlan_groups:
            vlans = str(vlan_group.vlans).replace("[", "").replace("'", "").replace("]", "")
            lan_up = str(vlan_group.lan_uplink_ports).replace("[", "").replace("'", "").replace("]", "")
            lan_pc = str(vlan_group.lan_port_channels).replace("[", "").replace("'", "").replace("]", "")
            org_perm = str(vlan_group.org_permissions).replace("[", "").replace("'", "").replace("]", "")
            rows.append([vlan_group.name, vlans, vlan_group.native_vlan, lan_up, lan_pc, org_perm])

        GenericReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                    column_number=len(rows[1]), centered=centered, cells_list=rows)


class VsanUcsReportTable(GenericReportTable):
    def __init__(self, order_id, parent, vsans, centered=False):
        rows = [[_("VSAN ID"), _("FCoE VLAN ID"),_("VSAN Name"), _("Fabric"), _("Zoning")]]

        for vsan in vsans:
            rows.append([vsan.id, vsan.fcoe_vlan_id, vsan.name, vsan.fabric, vsan.zoning])

        GenericReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                    column_number=len(rows[1]), centered=centered, cells_list=rows)


class IomSectionInfoUcsReportTable(GenericReportTable):
    def __init__(self, order_id, parent, iom, centered=False):
        rows = [[_("IO Module Id"),_("SKU / Model"), _("Serial Number"), _("Firmware Package Version"),
                 _("Number of ports used")]]

        for iom_unit in iom:
            rows.append([iom_unit.id, iom_unit.sku, iom_unit.serial, iom_unit.firmware_package_version,
                         len(iom_unit.ports)])

        GenericReportTable.__init__(self,order_id=order_id, parent=parent, row_number=len(rows),
                                    column_number=len(rows[1]), centered=centered, cells_list=rows)


class PsuSectionInfoUcsReportTable(GenericReportTable):
    def __init__(self, order_id, parent, psu, centered=False):
        rows = [[_("PSU Id"),_("SKU / Model"), _("Serial Number"), _("Info")]]

        for power_supply in psu:
            rows.append([power_supply.id, power_supply.sku, power_supply.serial, power_supply.name])

        GenericReportTable.__init__(self,order_id=order_id, parent=parent, row_number=len(rows),
                                    column_number=len(rows[1]), centered=centered, cells_list=rows)


class GemSectionInfoUcsReportTable(GenericReportTable):
    def __init__(self, order_id, parent, gem, centered=False):
        rows = [[_("GEM Id"),_("SKU / Model"), _("Serial Number"), _("Info")]]

        for expansion_module in gem:
            rows.append([expansion_module.id, expansion_module.sku, expansion_module.serial, expansion_module.name])

        GenericReportTable.__init__(self,order_id=order_id, parent=parent, row_number=len(rows),
                                    column_number=len(rows[1]), centered=centered, cells_list=rows)


class BladesSectionInfoUcsReportTable(GenericReportTable):
    def __init__(self, order_id, parent, blades, centered=False):
        rows = [[_("Blade Id"),_("SKU / Model"), _("Serial Number"), _("Firmware Package Version")]]

        for blade in blades:
            rows.append([blade.slot_id, blade.sku, blade.serial, blade.firmware_package_version])

        GenericReportTable.__init__(self,order_id=order_id, parent=parent, row_number=len(rows),
                                    column_number=len(rows[1]), centered=centered, cells_list=rows)


class UcsReportRackConnectivityTable(GenericReportTable):
    def __init__(self, order_id, parent, fis, fexs, rack, centered=False, autofit=True):
        rows = [
            [_("FI"), _("FI Port"), _("FEX"), _("FEX Fabric Port"), _("FEX Host Port"),
             _("Adaptor ID"), _("Adaptor Port"), _("Transceiver SKU/Type"),
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
                                    fex_fabric_port = port.peer['slot'] + port.peer['port']
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
                                                        fex_port = port.slot_id + "/" + port.port_id
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

        GenericReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                        column_number=len(rows[1]), centered=centered, cells_list=rows, autofit=autofit)



class UcsReportChassisConnectivityTable(GenericReportTable):
    def __init__(self, order_id, parent, fis, fexs, chassis, centered=False, autofit=True):
        rows = [[_("FI"), _("FI Port"), _("FEX"), _("FEX Fabric Port"), _("FEX Host Port"),_("IOM/SIOC"),
                 _("IOM/SIOC Port"), _("Transceiver SKU/Type"), _("Transceiver S/N"),
                 _("Transceiver Length")]]

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
                                    fex_fabric_port = port.peer['slot'] + port.peer['port']
                                    for fex_host_port in fex.host_ports:
                                        if fex_host_port.peer:
                                            if "chassis" in fex_host_port.peer.keys():
                                                if str(fex_host_port.peer['rack']) == chassis.id:
                                                    fex_id = fex.id
                                                    if fex_host_port.aggr_port_id:
                                                        fex_port = fex_host_port.slot_id + "/" + \
                                                                   fex_host_port.aggr_port_id + "/" + \
                                                                   fex_host_port.port_id
                                                    else:
                                                        fex_port = port.slot_id + "/" + port.port_id
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

        GenericReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                    column_number=len(rows[1]), centered=centered, cells_list=rows, autofit=autofit)



class UcsReportLanNeighborsConnectivityTable(GenericReportTable):
    def __init__(self, order_id, parent, fis, centered=False, autofit=True):
        rows = [[_("FI"), _("FI Port"), _("Remote Name"), _("Remote Interface"),
                 _("Remote Model"), _("Remote S/N"), _("Transceiver SKU/Type"), _("Transceiver S/N"),
                 _("Transceiver Length")]]

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

                                if neighbor_entry.lldp_system_name:
                                    remote_name = neighbor_entry.cdp_system_name
                                elif neighbor_entry.cdp_system_name:
                                    remote_name = neighbor_entry.cdp_system_name
                                else:
                                    remote_name = ""

                                if neighbor_entry.cdp_remote_interface:
                                    remote_interface = neighbor_entry.cdp_remote_interface
                                elif neighbor_entry.lldp_remote_interface:
                                    remote_interface = neighbor_entry.lldp_remote_interface
                                else:
                                    remote_interface = ""

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

            GenericReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                        column_number=len(rows[1]), centered=centered, cells_list=rows, autofit=autofit)


class UcsReportSanNeighborsConnectivityTable(GenericReportTable):
    def __init__(self, order_id, parent, fis, centered=False, autofit=True):
        rows = [[_("FI"), _("FI Port"), _("Remote IP"), _("Remote WWNN"), _("Remote WWPN"),
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

                                fabric_mgmt_addr = neighbor_entry.fabric_mgmt_addr
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

        GenericReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                    column_number=len(rows[1]), centered=centered, cells_list=rows, autofit=autofit)


class ClusterInfoUcsReportTable(GenericReportTable):
    def __init__(self, order_id, parent, config, device, centered=False):
        config_system = config.system[0]
        config_mng_int = config.management_interfaces[0]

        rows = [[_("Description"),_("Value")]]
        # Cluster info
        rows.append([_("System Name"), config_system.name])
        rows.append([_("Admin password"), device.password])
        rows.append([_("Cluster IP Address"),config_system.virtual_ip])
        rows.append([_("Netmask"), config_mng_int.netmask])
        rows.append([_("Gateway"), config_mng_int.gateway])
        if config_system.virtual_ipv6 and config_system.virtual_ipv6 not in ["::"]:
            rows.append([_("Cluster IP V6 Address"), config_system.virtual_ipv6])
        if config_mng_int.gateway_v6 and config_mng_int.gateway_v6 not in ["::"]:
            rows.append([_("Gateway V6"), config_mng_int.gateway_v6])
        # FI A (& B) info
        if config.management_interfaces:
            for interface in config.management_interfaces:
                if interface.fabric == "A":
                    if interface.ipv6 not in ["", "::"]:
                        rows.append([_("FI A - IPv6 Address"), interface.ipv6])
                    rows.append([_("FI A - IP Address"), interface.ip])

                if interface.fabric == "B":
                    if interface.ipv6 not in ["", "::"]:
                        rows.append([_("FI B - IPv6 Address"), interface.ipv6])
                    rows.append([_("FI B - IP Address"), interface.ip])
        # General cluster info
        if config_system.descr:
            rows.append([_("Description"), config_system.descr])
        if config_system.site:
            rows.append([_("Site"), config_system.site])
        if config_system.owner:
            rows.append([_("Owner"), config_system.owner])
        if config_system.domain_name:
            rows.append([_("Domain Name"), config_system.domain_name])
        # Timezone and DNS info
        if config.timezone_mgmt:
            if config.timezone_mgmt[0].zone:
                rows.append([_("Time Zone"), config.timezone_mgmt[0].zone])
            if config.timezone_mgmt[0].ntp:
                rows.append([_("NTP"),
                             str(config.timezone_mgmt[0].ntp).replace("'", "").replace("[", "").replace("]", "")])
        if config.dns:
            rows.append([_("DNS"), str(config.dns).replace("'", "").replace("[", "").replace("]", "")])
        if config.call_home:
            rows.append([_("Call Home"), config.call_home[0].admin_state])
        if config.ucs_central:
            rows.append([_("Link to UCS Central"), _("Connected to ") + config.ucs_central[0].ip_address])
        else:
            rows.append([_("Link to UCS Central"), "off"])

        GenericReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                    column_number=len(rows[0]), centered=centered, cells_list=rows)


class CommServicesInfoUcsReportTable(GenericReportTable):
    def __init__(self, order_id, parent, config, device, centered=False):
        communication_services = config.communication_services[0]

        rows = [[_("Service"),_("State")]]
        # Cluster info
        rows.append([_("HTTP"), communication_services.http_service[0]["state"]])
        rows.append([_("Redirect to HTTPS"), communication_services.http_service[0]["redirect_to_https"]])
        rows.append([_("HTTPS"), communication_services.https_service[0]["state"]])
        rows.append([_("SNMP"), communication_services.snmp_service[0]["state"]])
        rows.append([_("CIMC"), communication_services.cimc_web_service])
        rows.append([_("SSH"), communication_services.ssh_service])
        rows.append([_("Telnet"), communication_services.telnet_service])

        GenericReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                    column_number=len(rows[0]), centered=centered, cells_list=rows)


class ServiceProfilesRacksUcsReportTable(GenericReportTable):
    def __init__(self, order_id, parent, rack_units, centered=False):

        rows = [[_("Rack ID"), _("Service Profile"), _("Service Profile Org"), _("Service Profile Template"),
                 _("Service Profile Template Org")]]
        # Rack Service Profile info
        for rack in rack_units:
            rack_id = rack.id
            ls_name = rack.service_profile_name
            ls_org = rack.service_profile_org
            ls_template = None
            ls_template_org = None

            if rack.service_profile_template_name:
                ls_template = rack.service_profile_template_name
                ls_template_org = rack.service_profile_template_org
            rows.append([rack_id, ls_name, ls_org, ls_template, ls_template_org])

        GenericReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                    column_number=len(rows[0]), centered=centered, cells_list=rows)


class ServiceProfilesChassisUcsReportTable(GenericReportTable):
    def __init__(self, order_id, parent, chassis, centered=False):

        rows = [[_("Chassis ID"), _("Blade ID"), _("Service Profile"), _("Service Profile Org"),
                 _("Service Profile Template"), _("Service Profile Template Org")]]
        # Blade Service Profile info
        for chassis_unit in chassis:
            for blade in chassis_unit.blades:
                chassis_id = chassis_unit.id
                blade_id = blade.slot_id
                ls_name = blade.service_profile_name
                ls_org = blade.service_profile_org
                ls_template = None
                ls_template_org = None

                if blade.service_profile_template_name:
                    ls_template = blade.service_profile_template_name
                    ls_template_org = blade.service_profile_template_org
                rows.append([chassis_id, blade_id, ls_name, ls_org, ls_template, ls_template_org])

        GenericReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                    column_number=len(rows[1]), centered=centered, cells_list=rows)