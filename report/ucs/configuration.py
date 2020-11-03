# coding: utf-8
# !/usr/bin/env python

""" configuration.py: Easy UCS Deployment Tool """

import json
import os.path
from ipaddress import IPv4Address, IPv6Address
from pathlib import Path

from PIL import Image

from report.content import *
from report.ucs.policies import UcsSystemPoliciesReportSection
from report.ucs.section import UcsReportSection
from report.ucs.table import UcsReportTable


class UcsSystemConfigurationReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Configuration")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            UcsSystemFisPortsReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            UcsSystemNetworkingReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            UcsSystemOrgsReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            UcsSystemIdentitiesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            UcsSystemPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            UcsSystemServiceProfilesAndTemplatesReportSection(order_id=self.report.get_current_order_id(), parent=self))


class UcsSystemFisPortsReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Fabric Interconnect Ports Configuration")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        for fi in self.report.inventory.fabric_interconnects:
            self.content_list.append(
                UcsSystemFiPortsReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                              title="Fabric Interconnect " + fi.id + " Ports Configuration", fi=fi))


class UcsSystemFiPortsReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title, fi):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if fi.model in ["UCS-FI-M-6324"]:
            # UCS Mini FI only has a rear picture
            path_rear = self.report.img_path + "fi_" + fi.id + "_rear.png"
            if os.path.exists(path_rear):
                # rotate and create an horizontal picture of the FI from UCS Mini
                image = Image.open(path_rear).rotate(90, expand=True)
                path_rear = self.report.img_path + "fi_" + fi.id + "_rear_horizontal.png"
                image.save(path_rear)
            self.content_list.append(
                GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path_rear,
                                   centered=True, spacing_after=2))
        else:

            path_rear = self.report.img_path + "fi_" + fi.id + "_rear.png"
            self.content_list.append(
                GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path_rear,
                                   centered=True, spacing_after=2))

        self.content_list.append(
            UcsSystemFiPortsReportTable(order_id=self.report.get_current_order_id(), parent=self, fi=fi, centered=True))


class UcsSystemFiPortsReportTable(UcsReportTable):
    def __init__(self, order_id, parent, fi, centered=False, autofit=True):
        rows = [[_("Fabric"), _("Port"), _("Port Role"), _("Speed"), _("Transceiver SKU/Type"), _("Transceiver S/N"),
                 _("Transceiver Length")]]

        for port in fi.ports:
            fi_id = fi.id
            if port.aggr_port_id:
                fi_port = port.slot_id + "/" + port.aggr_port_id + "/" + port.port_id
            else:
                fi_port = port.slot_id + "/" + port.port_id

            fi_port_role = port.role if port.role != "unknown" else _("not configured")
            fi_port_speed = port.oper_speed if port.oper_speed != "indeterminate" else ""

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

            if fi_port_role != "not configured":
                rows.append([fi_id, fi_port, fi_port_role, fi_port_speed, transceiver_type, transceiver_sn,
                             transceiver_length])

        # In case all ports are not configured, this prevents an IndexError exception
        if len(rows) == 1:
            column_number = 0
        else:
            column_number = len(rows[1])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=column_number, centered=centered, cells_list=rows, autofit=autofit,
                                font_size=8)


class UcsSystemNetworkingReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Networking")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(UcsSystemVlansReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(UcsSystemVlanGroupsReportSection(order_id=self.report.get_current_order_id(),
                                                                  parent=self))
        self.content_list.append(UcsSystemVsansReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(UcsSystemLanPortChannelsReportSection(order_id=self.report.get_current_order_id(),
                                                                       parent=self))
        self.content_list.append(UcsSystemSanPortChannelsReportSection(order_id=self.report.get_current_order_id(),
                                                                       parent=self))
        self.content_list.append(UcsSystemFcoePortChannelsReportSection(order_id=self.report.get_current_order_id(),
                                                                        parent=self))
        self.content_list.append(
            UcsSystemQosSystemClassReportSection(order_id=self.report.get_current_order_id(), parent=self))


class UcsSystemVlansReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("VLANs")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if self.report.config.vlans:
            self.content_list.append(
                GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                  string=(_("There is a total of ") + str(len(self.report.config.vlans)) + " VLANs")))
            self.content_list.append(
                UcsSystemVlansReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                          vlans=self.report.config.vlans, centered=True))


class UcsSystemVlansReportTable(UcsReportTable):
    def __init__(self, order_id, parent, vlans, centered=False):
        rows = [[_("ID"), _("VLAN Name"), _("Fabric"), _("Multicast Policy"), _("Sharing Type")]]

        vlans.sort(key=lambda x: int(x.id), reverse=False)
        for vlan in vlans:
            rows.append([vlan.id, vlan.name, vlan.fabric, vlan.multicast_policy_name, vlan.sharing_type])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows)


class UcsSystemVlanGroupsReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("VLAN Groups")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if self.report.config.vlan_groups:
            self.content_list.append(
                GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                  string=(_("There is a total of ") + str(len(self.report.config.vlan_groups)) +
                                          _(" VLAN Groups"))))
            self.content_list.append(
                UcsSystemVlanGroupsReportTable(order_id=self.report.get_current_order_id(), parent=self, centered=True,
                                               vlan_groups=self.report.config.vlan_groups))


class UcsSystemVlanGroupsReportTable(UcsReportTable):
    def __init__(self, order_id, parent, vlan_groups, centered=False):
        rows = [[_("Name"), _("VLANs"), _("Native VLAN"), _("LAN Uplink Ports"), _("LAN Port Channel"),
                 _("Org Permissions")]]

        for vlan_group in vlan_groups:
            lan_up_text = ""
            if vlan_group.lan_uplink_ports:
                for lan_up in vlan_group.lan_uplink_ports:
                    if "aggr_id" in lan_up.keys():
                        if lan_up["aggr_id"]:
                            lan_up_text += lan_up["fabric"] + "/" + lan_up["slot_id"] + "/" + lan_up["port_id"] + "/" \
                                           + lan_up["aggr_id"] + ", "
                    else:
                        lan_up_text += lan_up["fabric"] + "/" + lan_up["slot_id"] + "/" + lan_up["port_id"] + ", "

            # We remove the last ", " characters of the string
            if lan_up_text:
                lan_up_text = lan_up_text[:-2]

            lan_pc_text = ""
            if vlan_group.lan_port_channels:
                for lan_pc in vlan_group.lan_port_channels:
                    lan_pc_text += lan_pc["fabric"] + "/Po" + lan_pc["pc_id"] + ", "

            # We remove the last ", " characters of the string
            if lan_pc_text:
                lan_pc_text = lan_pc_text[:-2]

            vlans = str(vlan_group.vlans).replace("[", "").replace("'", "").replace("]", "")
            lan_up = lan_up_text
            lan_pc = lan_pc_text
            org_perm = str(vlan_group.org_permissions).replace("[", "").replace("'", "").replace("]", "")
            rows.append([vlan_group.name, vlans, vlan_group.native_vlan, lan_up, lan_pc, org_perm])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows)


class UcsSystemVsansReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("VSANs")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if self.report.config.vsans:
            self.content_list.append(
                GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                  string=(_("There is a total of ") + str(len(self.report.config.vsans)) + " VSANs")))
            self.content_list.append(
                UcsSystemVsansReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                          vsans=self.report.config.vsans, centered=True))


class UcsSystemVsansReportTable(UcsReportTable):
    def __init__(self, order_id, parent, vsans, centered=False):
        rows = [[_("ID"), _("FCoE VLAN ID"), _("VSAN Name"), _("Fabric"), _("Zoning")]]

        vsans.sort(key=lambda x: int(x.id), reverse=False)
        for vsan in vsans:
            rows.append([vsan.id, vsan.fcoe_vlan_id, vsan.name, vsan.fabric, vsan.zoning])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows)


class UcsSystemLanPortChannelsReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("LAN Port-Channels")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if self.report.config.lan_port_channels:
            self.content_list.append(
                UcsSystemLanPortChannelsReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                                    centered=True,
                                                    lan_port_channels=self.report.config.lan_port_channels))


class UcsSystemLanPortChannelsReportTable(UcsReportTable):
    def __init__(self, order_id, parent, lan_port_channels, centered=False):
        rows = [[_("ID"), _("Fabric"), _("Interfaces"), _("Name"), _("Admin Speed"), _("Flow Control Policy"),
                 _("LACP Policy")]]

        # TODO : Put in order by the PC ID (now : 119, 120, 13, 14, ...)
        for lan_port_channel in lan_port_channels:

            interfaces = ""
            for interface in lan_port_channel.interfaces:
                if "aggr_id" in interface.keys() and interface["aggr_id"]:
                    interfaces += interface["slot_id"] + "/" + interface["port_id"] + "/" + interface["aggr_id"] + ", "
                else:
                    interfaces += interface["slot_id"] + "/" + interface["port_id"] + ", "
            if interfaces:
                interfaces = interfaces[:-2]  # remove the last ", " at the end of the string

            rows.append([lan_port_channel.pc_id, lan_port_channel.fabric,
                         interfaces, lan_port_channel.name, lan_port_channel.admin_speed,
                         lan_port_channel.flow_control_policy, lan_port_channel.lacp_policy])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows)


class UcsSystemSanPortChannelsReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("SAN Port-Channels")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if self.report.config.san_port_channels:
            self.content_list.append(
                UcsSystemSanPortChannelsReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                                    centered=True,
                                                    san_port_channels=self.report.config.san_port_channels))


class UcsSystemSanPortChannelsReportTable(UcsReportTable):
    def __init__(self, order_id, parent, san_port_channels, centered=False):
        rows = [[_("ID"), _("Fabric"), _("Interfaces"), _("Name"), _("Admin Speed"), _("VSAN Fabric"), _("VSAN")]]

        # TODO : Put in order by the PC ID (now : 119, 120, 13, 14, ...)
        for san_port_channel in san_port_channels:

            interfaces = ""
            for interface in san_port_channel.interfaces:
                interfaces += interface["slot_id"] + "/" + interface["port_id"] + ", "
            if interfaces:
                interfaces = interfaces[:-2]  # remove the last ", " at the end of the string

            rows.append([san_port_channel.pc_id, san_port_channel.fabric,
                         interfaces, san_port_channel.name, san_port_channel.admin_speed,
                         san_port_channel.vsan_fabric, san_port_channel.vsan])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows)


class UcsSystemFcoePortChannelsReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("FCoE Port-Channels")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if self.report.config.fcoe_port_channels:
            self.content_list.append(
                UcsSystemFcoePortChannelsReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                                     centered=True,
                                                     fcoe_port_channels=self.report.config.fcoe_port_channels))


class UcsSystemFcoePortChannelsReportTable(UcsReportTable):
    def __init__(self, order_id, parent, fcoe_port_channels, centered=False):
        rows = [[_("ID"), _("Fabric"), _("Interfaces"), _("Name"), _("LACP Policy")]]

        # TODO : Put in order by the PC ID (now : 119, 120, 13, 14, ...)
        for fcoe_port_channel in fcoe_port_channels:

            interfaces = ""
            for interface in fcoe_port_channel.interfaces:
                if "aggr_id" in interface.keys() and interface["aggr_id"]:
                    interfaces += interface["slot_id"] + "/" + interface["port_id"] + "/" + interface["aggr_id"] + ", "
                else:
                    interfaces += interface["slot_id"] + "/" + interface["port_id"] + ", "
            if interfaces:
                interfaces = interfaces[:-2]  # remove the last ", " at the end of the string

            rows.append([fcoe_port_channel.pc_id, fcoe_port_channel.fabric,
                         interfaces, fcoe_port_channel.name, fcoe_port_channel.lacp_policy])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows)


class UcsSystemQosSystemClassReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("QoS System Class")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if self.report.config.qos_system_class:
            self.content_list.append(
                UcsSystemQosSystemClassReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                                   centered=True,
                                                   qos_system_class=self.report.config.qos_system_class))


class UcsSystemQosSystemClassReportTable(UcsReportTable):
    def __init__(self, order_id, parent, qos_system_class, centered=False):
        rows = [[_("Priority"), _("State"), _("CoS"), _("Packet Drop"), _("Weight"), _("MTU"),
                 _("Multicast Optimized")]]

        priority_order = ["platinum", "gold", "silver", "bronze", "fc", "best-effort"]
        order = {key: i for i, key in enumerate(priority_order)}

        for priority in sorted(qos_system_class, key=lambda x: order[x.priority], reverse=False):
            priority_name = \
                priority.priority.replace("-", " ").title() if priority.priority != "fc" else "Fibre Channel"
            rows.append([priority_name, priority.state, priority.cos,
                         priority.packet_drop, priority.weight, priority.mtu, priority.multicast_optimized])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows)


class UcsSystemOrgsReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Organizations")

        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        org_list = []
        # Searching for all orgs
        for org in self.report.config.orgs:
            self.parse_org(org, org_list, element_to_parse="orgs")
        if org_list:
            self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                       string=_("There is a total of ") + str(len(org_list)) +
                                                              _(" organizations (excluding 'root').")))
        if len(org_list) == 0:
            self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                       string=_("There are no organizations (other than 'root')."),
                                                       italicized=True, bolded=False))
        else:
            org_path = self.report.img_path + "orgs.png"
            self.content_list.append(
                GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=org_path,
                                   centered=True, size=18))


class UcsSystemIdentitiesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Identities")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            UcsSystemIpPoolsReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            UcsSystemUuidPoolsReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            UcsSystemMacPoolsReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            UcsSystemWwnnPoolsReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            UcsSystemWwpnPoolsReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            UcsSystemWwxnPoolsReportSection(order_id=self.report.get_current_order_id(), parent=self))


class UcsSystemIpPoolsReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("IP Pools")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        ip_pool_list = []
        # Searching for all IP Pools
        for org in self.report.config.orgs:
            self.parse_org(org, ip_pool_list, element_to_parse="ip_pools")

        if ip_pool_list:
            for ip_pool in ip_pool_list:
                self.content_list.append(
                    UcsSystemIpPoolReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                 ip_pool=ip_pool, title=_("IP Pool ") + ip_pool.name))


class UcsSystemIpPoolReportSection(UcsReportSection):
    def __init__(self, order_id, parent, ip_pool, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if ip_pool.ip_blocks:
            self.content_list.append(
                GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                  string=_("\nIPv4 Blocks :"), bolded=True))
            self.content_list.append(
                UcsSystemIpBlocksReportTable(order_id=self.report.get_current_order_id(), parent=self, centered=True,
                                             blocks_ipv4=ip_pool.ip_blocks))

        if ip_pool.ipv6_blocks:
            self.content_list.append(
                GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                  string=_("\nIPv6 Blocks :"), bolded=True)
            )
            self.content_list.append(
                UcsSystemIpv6BlocksReportTable(order_id=self.report.get_current_order_id(), parent=self, centered=True,
                                               blocks_ipv6=ip_pool.ipv6_blocks))


class UcsSystemIpBlocksReportTable(UcsReportTable):
    def __init__(self, order_id, parent, blocks_ipv4, centered=False):
        rows = [[_("From"), _("To"), _("Subnet"), _("Gateway"), _("Primary DNS"), _("Secondary DNS"), _("Size")]]

        for block_ipv4 in blocks_ipv4:
            size = int(IPv4Address(block_ipv4["to"])) - int(IPv4Address(block_ipv4["from"])) + 1
            rows.append([block_ipv4["from"], block_ipv4["to"], block_ipv4["netmask"], block_ipv4["gateway"],
                         block_ipv4["primary_dns"], block_ipv4["secondary_dns"], size])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows)


class UcsSystemIpv6BlocksReportTable(UcsReportTable):
    def __init__(self, order_id, parent, blocks_ipv6, centered=False):
        rows = [[_("From"), _("To"), _("Prefix"), _("Gateway"), _("Primary DNS"), _("Secondary DNS"), _("Size")]]

        for block_ipv6 in blocks_ipv6:
            size = int(IPv6Address(block_ipv6["to"])) - int(IPv6Address(block_ipv6["from"]))
            rows.append([block_ipv6["from"], block_ipv6["to"], block_ipv6["prefix"], block_ipv6["gateway"],
                         block_ipv6["primary_dns"], block_ipv6["secondary_dns"], size])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows)


class UcsSystemUuidPoolsReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("UUID Pools")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        uuid_pool_list = []
        # Searching for all UUID Pools
        for org in self.report.config.orgs:
            self.parse_org(org, uuid_pool_list, element_to_parse="uuid_pools")

        if uuid_pool_list:
            for uuid_pool in uuid_pool_list:
                self.content_list.append(
                    UcsSystemUuidPoolReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                   uuid_pool=uuid_pool, title=_("UUID Pool ") + uuid_pool.name))


class UcsSystemUuidPoolReportSection(UcsReportSection):
    def __init__(self, order_id, parent, uuid_pool, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self, string=_("\nPrefix : "),
                              bolded=False))
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self, string=uuid_pool.prefix,
                              bolded=True, new_paragraph=False))

        if uuid_pool.uuid_blocks:
            self.content_list.append(
                UcsSystemGenericBlocksReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                                  centered=True, blocks=uuid_pool.uuid_blocks))


class UcsSystemMacPoolsReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("MAC Pools")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        mac_pool_list = []
        # Searching for all IP Pools
        for org in self.report.config.orgs:
            self.parse_org(org, mac_pool_list, element_to_parse="mac_pools")

        if mac_pool_list:
            for mac_pool in mac_pool_list:
                self.content_list.append(
                    UcsSystemMacPoolReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                  mac_pool=mac_pool, title=_("MAC Pool ") + mac_pool.name))


class UcsSystemMacPoolReportSection(UcsReportSection):
    def __init__(self, order_id, parent, mac_pool, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if mac_pool.mac_blocks:
            self.content_list.append(
                UcsSystemGenericBlocksReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                                  centered=True, blocks=mac_pool.mac_blocks))


class UcsSystemWwnnPoolsReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("WWNN Pools")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        wwnn_pool_list = []
        # Searching for all WWNN Pools
        for org in self.report.config.orgs:
            self.parse_org(org, wwnn_pool_list, element_to_parse="wwnn_pools")

        if wwnn_pool_list:
            for wwnn_pool in wwnn_pool_list:
                self.content_list.append(
                    UcsSystemWwnnPoolReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                   wwnn_pool=wwnn_pool, title=_("WWNN Pool ") + wwnn_pool.name))


class UcsSystemWwnnPoolReportSection(UcsReportSection):
    def __init__(self, order_id, parent, wwnn_pool, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if wwnn_pool.wwnn_blocks:
            self.content_list.append(
                UcsSystemGenericBlocksReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                                  centered=True, blocks=wwnn_pool.wwnn_blocks))


class UcsSystemWwpnPoolsReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("WWPN Pools")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        wwpn_pool_list = []
        # Searching for all WWPN Pools
        for org in self.report.config.orgs:
            self.parse_org(org, wwpn_pool_list, element_to_parse="wwpn_pools")

        if wwpn_pool_list:
            for wwpn_pool in wwpn_pool_list:
                self.content_list.append(
                    UcsSystemWwpnPoolReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                   wwpn_pool=wwpn_pool, title=_("WWPN Pool ") + wwpn_pool.name))


class UcsSystemWwpnPoolReportSection(UcsReportSection):
    def __init__(self, order_id, parent, wwpn_pool, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if wwpn_pool.wwpn_blocks:
            self.content_list.append(
                UcsSystemGenericBlocksReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                                  centered=True, blocks=wwpn_pool.wwpn_blocks))


class UcsSystemWwxnPoolsReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("WWxN Pools")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        wwxn_pool_list = []
        # Searching for all WWxN Pools
        for org in self.report.config.orgs:
            self.parse_org(org, wwxn_pool_list, element_to_parse="wwxn_pools")

        if wwxn_pool_list:
            for wwxn_pool in wwxn_pool_list:
                self.content_list.append(
                    UcsSystemWwxnPoolReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                   wwxn_pool=wwxn_pool, title=_("WWxN Pool ") + wwxn_pool.name))


class UcsSystemWwxnPoolReportSection(UcsReportSection):
    def __init__(self, order_id, parent, wwxn_pool, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                              string=_("\nMax ports per Node: "), bolded=False))
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                              string=wwxn_pool.max_ports_per_node, bolded=True, new_paragraph=False))

        if wwxn_pool.wwxn_blocks:
            self.content_list.append(
                UcsSystemGenericBlocksReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                                  centered=True, blocks=wwxn_pool.wwxn_blocks))


class UcsSystemGenericBlocksReportTable(UcsReportTable):
    # Used for WWNN, WWPN, WWXN, UUID and MAC Blocks
    def __init__(self, order_id, parent, blocks, centered=False):
        rows = [[_("From"), _("To"), _("Size")]]

        for block in blocks:
            size = int(block["to"].replace("-", "").replace(":", ""), 16) - int(block["from"].replace(
                "-", "").replace(":", ""), 16) + 1
            rows.append([block["from"], block["to"], size])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows)


class UcsSystemServiceProfilesAndTemplatesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Service Profiles & Templates")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            UcsSystemServiceProfileTemplatesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            UcsSystemServiceProfilesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            UcsSystemServiceProfilesAllocationReportSection(order_id=self.report.get_current_order_id(), parent=self))


class UcsSystemServiceProfileTemplatesReportSection(UcsReportSection):
    def parse_org(self, org, service_profile_temp_list, service_profile_child_list,
                  element_to_parse="service_profiles"):
        if org.service_profiles is not None:
            for service_profile in org.service_profiles:
                if not service_profile.service_profile_template:
                    if service_profile.type in ["updating-template", "initial-template"]:
                        service_profile_temp_list.append(service_profile)
                else:
                    service_profile_child_list.append(service_profile)

        if hasattr(org, "orgs"):
            if org.orgs is not None:
                for suborg in org.orgs:
                    self.parse_org(suborg, service_profile_temp_list, service_profile_child_list)

    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Service Profiles Templates")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        service_profile_temp_list = []
        service_profile_child_list = []
        # Searching for all updating template Service Profile
        for org in self.report.config.orgs:
            self.parse_org(org, service_profile_temp_list, service_profile_child_list)

        for sp_temp in service_profile_temp_list:
            # Get the SP spawned from the template
            children = ""
            for child in service_profile_child_list:
                if child.service_profile_template == sp_temp.name:
                    if not children:
                        children = child.name
                    else:
                        children = children + ", " + child.name
            sp_temp.children = children

            self.content_list.append(
                UcsSystemServiceProfileReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                     service_profile=sp_temp,
                                                     title=_("Service Profile Template ") + sp_temp.name))
            delattr(sp_temp, "children")


class UcsSystemServiceProfilesReportSection(UcsReportSection):
    def parse_org(self, org, service_profile_list, element_to_parse="service_profiles"):
        if org.service_profiles is not None:
            for service_profile in org.service_profiles:
                if not service_profile.service_profile_template:
                    if service_profile.type not in ["updating-template", "initial-template"]:
                        service_profile_list.append(service_profile)
        if hasattr(org, "orgs"):
            if org.orgs is not None:
                for suborg in org.orgs:
                    self.parse_org(suborg, service_profile_list)

    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Service Profiles")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        service_profile_list = []
        # Searching for all updating template Service Profile
        for org in self.report.config.orgs:
            self.parse_org(org, service_profile_list)

        for sp in service_profile_list:
            self.content_list.append(
                UcsSystemServiceProfileReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                     service_profile=sp, title=_("Service Profile ") + sp.name))


class UcsSystemServiceProfileReportSection(UcsReportSection):
    def __init__(self, order_id, parent, service_profile, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if "template" in service_profile.type:
            service_profile_path = self.report.img_path + service_profile._parent._dn.replace(
                "/", "_") + "_Service_Profile_Template_" + "_".join(service_profile.name.split(" ")) + '.png'
        else:
            service_profile_path = self.report.img_path + service_profile._parent._dn.replace(
                "/", "_") + "_Service_Profile_" + "_".join(service_profile.name.split(" ")) + '.png'
        self.content_list.append(
            GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=service_profile_path,
                               centered=True, size=18))

        self.content_list.append(
            UcsSystemServiceProfileReportTable(order_id=self.report.get_current_order_id(), parent=self, centered=True,
                                               service_profile=service_profile))


class UcsSystemServiceProfileReportTable(UcsReportTable):
    def __init__(self, order_id, parent, service_profile, centered=False):
        rows = [[_("Description"), _("Value")], [_("Name"), service_profile.name], [_("Type"), service_profile.type],
                [_("Organization"), service_profile._parent._dn], [_("BIOS Policy"), service_profile.bios_policy],
                [_("Boot Policy"), service_profile.boot_policy],
                [_("Maintenance Policy"), service_profile.maintenance_policy],
                [_("Local Disk Configuration Policy"), service_profile.local_disk_configuration_policy],
                [_("Dynamic vNIC Connection Policy"), service_profile.dynamic_vnic_connection_policy],
                [_("LAN Connectivity Policy"), service_profile.lan_connectivity_policy],
                [_("SAN Connectivity Policy"), service_profile.san_connectivity_policy],
                [_("Placement Policy"), service_profile.placement_policy],
                [_("vMedia Policy"), service_profile.vmedia_policy],
                [_("Serial Over LAN Policy"), service_profile.serial_over_lan_policy],
                [_("Threshold Policy"), service_profile.threshold_policy],
                [_("Power Control Policy"), service_profile.power_control_policy],
                [_("Scrub Policy"), service_profile.scrub_policy],
                [_("KVM Management Policy"), service_profile.kvm_management_policy],
                [_("Graphics Card Policy"), service_profile.graphics_card_policy],
                [_("Power Sync Policy"), service_profile.power_sync_policy],
                [_("Storage Profile"), service_profile.storage_profile],
                [_("IPMI Access Profile"), service_profile.ipmi_access_profile],
                [_("UUID Pool"), service_profile.uuid_pool], [_("WWNN Pool"), service_profile.wwnn_pool],
                [_("Server Pool"), service_profile.server_pool],
                [_("Host Firmware Package"), service_profile.host_firmware_package]]
        if hasattr(service_profile, "children"):
            rows.append([_("Instantiated Service Profiles"), service_profile.children.replace(", ", "\n")])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows)


class UcsSystemServiceProfilesAllocationReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Service Profiles associations")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if self.report.inventory.chassis:
            self.content_list.append(
                UcsSystemServiceProfilesAllocationChassisReportSection(order_id=self.report.get_current_order_id(),
                                                                       parent=self))

        if self.report.inventory.rack_units:
            self.content_list.append(
                UcsSystemServiceProfilesAllocationRacksReportSection(order_id=self.report.get_current_order_id(),
                                                                     parent=self))

        if self.report.inventory.rack_enclosures:
            self.content_list.append(
                UcsSystemServiceProfilesAllocationRackEnclosuresReportSection(
                    order_id=self.report.get_current_order_id(), parent=self))


class UcsSystemServiceProfilesAllocationChassisReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Blade Servers associations")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        i = 1
        path = self.report.img_path + "infra_service_profile_" + "chassis_" + str(i) + ".png"
        while os.path.exists(path):
            self.content_list.append(
                GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path, centered=True,
                                   size=18))
            i += 1
            path = self.report.img_path + "infra_service_profile_" + "chassis_" + str(i) + ".png"

        flag = False
        for chassis in self.report.inventory.chassis:
            for blade in chassis.blades:
                if blade.service_profile_name:
                    flag = True
        if flag:
            self.content_list.append(
                UcsSystemServiceProfilesAllocationChassisReportTable(order_id=self.report.get_current_order_id(),
                                                                     parent=self, centered=True,
                                                                     chassis=self.report.inventory.chassis))


class UcsSystemServiceProfilesAllocationChassisReportTable(UcsReportTable):
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

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows)


class UcsSystemServiceProfilesAllocationRacksReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Rack Servers associations")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        i = 1
        path = self.report.img_path + "infra_service_profile_" + "rack_" + str(i) + ".png"
        while os.path.exists(path):
            self.content_list.append(
                GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path, centered=True,
                                   size=18))
            i += 1
            path = self.report.img_path + "infra_service_profile_" + "rack_" + str(i) + ".png"

        flag = False
        for rack in self.report.inventory.rack_units:
            if rack.service_profile_name:
                flag = True
        if flag:
            self.content_list.append(
                UcsSystemServiceProfilesAllocationRacksReportTable(order_id=self.report.get_current_order_id(),
                                                                   parent=self, centered=True,
                                                                   rack_units=self.report.inventory.rack_units))


class UcsSystemServiceProfilesAllocationRacksReportTable(UcsReportTable):
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

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[0]), centered=centered, cells_list=rows)


class UcsSystemServiceProfilesAllocationRackEnclosuresReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Rack Enclosures Servers associations")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        i = 1
        path = self.report.img_path + "infra_service_profile_" + "rack_enclosure_" + str(i) + ".png"
        while os.path.exists(path):
            self.content_list.append(
                GenericReportImage(order_id=self.report.get_current_order_id(), parent=self, path=path, centered=True,
                                   size=18))
            i += 1
            path = self.report.img_path + "infra_service_profile_" + "rack_enclosure_" + str(i) + ".png"

        flag = False
        for rack_enclosure in self.report.inventory.rack_enclosures:
            for server_node in rack_enclosure.server_nodes:
                if server_node.service_profile_name:
                    flag = True
        if flag:
            self.content_list.append(
                UcsSystemServiceProfilesAllocationRackEnclosuresReportTable(
                    order_id=self.report.get_current_order_id(), parent=self, centered=True,
                    rack_enclosures=self.report.inventory.rack_enclosures))


class UcsSystemServiceProfilesAllocationRackEnclosuresReportTable(UcsReportTable):
    def __init__(self, order_id, parent, rack_enclosures, centered=False):

        rows = [[_("Rack Enclosure ID"), _("Rack ID"), _("Service Profile"), _("Service Profile Org"),
                 _("Service Profile Template"), _("Service Profile Template Org")]]
        # Rack Enclosures Service Profile info
        for rack_enclosure in rack_enclosures:
            for server_node in rack_enclosure.server_nodes:
                rack_enclosure_id = rack_enclosure.id
                rack_id = server_node.id
                ls_name = server_node.service_profile_name
                ls_org = server_node.service_profile_org
                ls_template = None
                ls_template_org = None

                if server_node.service_profile_template_name:
                    ls_template = server_node.service_profile_template_name
                    ls_template_org = server_node.service_profile_template_org
                rows.append([rack_enclosure_id, rack_id, ls_name, ls_org, ls_template, ls_template_org])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[0]), centered=centered, cells_list=rows)


class RecapUcsReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Detailed Specifications")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        # FI
        if self.report.inventory.fabric_interconnects or self.report.inventory.fabric_extenders:
            fabric_model_list = []
            for fabric in self.report.inventory.fabric_interconnects:
                key = fabric.sku
                if key not in fabric_model_list:
                    fabric_model_list.append(key)

            if fabric_model_list:
                self.content_list.append(ReportInventoryRecap(order_id=self.report.get_current_order_id(), parent=self,
                                                              type="FI", recap=fabric_model_list,
                                                              title=_("Fabric Interconnect Details")))

        # FEX
        if self.report.inventory.fabric_extenders:
            fabric_model_list = []
            for fabric in self.report.inventory.fabric_extenders:
                key = fabric.sku
                if key not in fabric_model_list:
                    fabric_model_list.append(key)

            if fabric_model_list:
                self.content_list.append(ReportInventoryRecap(order_id=self.report.get_current_order_id(), parent=self,
                                                              type="FEX", recap=fabric_model_list,
                                                              title=_("FEX Details")))

        # Chassis / Blades
        if self.report.inventory.chassis:
            chassis_model_list = []
            blade_model_list = []
            for chassis in self.report.inventory.chassis:
                if chassis.blades:
                    for blade in chassis.blades:
                        if blade.sku_scaled:
                            key = blade.sku_scaled
                        else:
                            key = blade.sku
                        if key not in blade_model_list:
                            blade_model_list.append(key)
                key = chassis.sku
                if key not in chassis_model_list:
                    chassis_model_list.append(key)
            if chassis_model_list:
                self.content_list.append(ReportInventoryRecap(order_id=self.report.get_current_order_id(), parent=self,
                                                              type="Chassis", recap=chassis_model_list,
                                                              title=_("Chassis Details")))
            if blade_model_list:
                self.content_list.append(ReportInventoryRecap(order_id=self.report.get_current_order_id(), parent=self,
                                                              type="Blades", recap=blade_model_list,
                                                              title=_("Blades Details")))

        # Racks
        if self.report.inventory.rack_units:
            rack_model_list = []
            for rack in self.report.inventory.rack_units:
                key = rack.sku
                if key not in rack_model_list:
                    rack_model_list.append(key)

            if rack_model_list:
                self.content_list.append(ReportInventoryRecap(order_id=self.report.get_current_order_id(), parent=self,
                                                              type="Rack", recap=rack_model_list,
                                                              title=_("Racks Details")))


class RecapUcsImcReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Detailed Specifications")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        # Racks
        if self.report.inventory.rack_units:
            rack_model_list = []
            for rack in self.report.inventory.rack_units:
                key = rack.sku
                if key not in rack_model_list:
                    rack_model_list.append(key)

            if rack_model_list:
                self.content_list.append(ReportInventoryRecap(order_id=self.report.get_current_order_id(), parent=self,
                                                              type="Rack", recap=rack_model_list,
                                                              title=_("Racks Details")))


class ReportInventoryRecap(UcsReportSection):
    def __init__(self, order_id, parent, title, recap, type):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        self.rows = []

        self.title = title
        self.recap = recap
        self.parent = parent

        for sku in recap:
            json_file = self._get_json_file(sku)
            name = type + " " + sku
            if json_file:
                spec_sheet_url = "Not Found"
                descr = "Not defined"
                dimensions = ""
                weight = ""
                if "spec_sheet_url" in json_file:
                    spec_sheet_url = json_file['spec_sheet_url']
                if "specs" in json_file:
                    specs = json_file["specs"]
                    if "descr" in specs:
                        descr = specs['descr']
                    if 'dimensions' in specs:
                        dimensions = specs['dimensions']
                    if 'weight' in specs:
                        weight = specs['weight']
                if "model_short_name" in json_file:
                    name = type + " " + json_file["model_short_name"] + ' (' + sku + ')'

                self.rows.append([name, descr, spec_sheet_url, dimensions, weight])

        if self.rows:
            for row in self.rows:
                self.content_list.append(ReportInventoryDeviceRecap(order_id=self.report.get_current_order_id(),
                                                                    parent=self, row=row))

    def _get_json_file(self, sku):
        file_name = str(sku) + ".json"
        folder_path = self._find_folder_path(file_name=file_name)
        try:
            json_file = open(folder_path / str(file_name))
            json_string = json_file.read()
            json_file.close()
            return json.loads(json_string)
        except FileNotFoundError:
            self.logger(level="error", message="JSON file " + folder_path + file_name + " not found")

        return False

    def _find_folder_path(self, file_name):
        for directory, sub_dirs, files in os.walk("catalog"):
            for file in files:
                if file == file_name:
                    return Path(directory)
        self.logger(level="error", message="Could not find catalog folder path for " + file_name)
        return Path('')


class ReportInventoryDeviceRecap(UcsReportSection):
    def __init__(self, order_id, parent, row, title=""):
        if not title:
            title = row[0]
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.title = title

        self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                   string=_("Description: "), italicized=True, bolded=True))
        self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                   string=row[1], new_paragraph=False))

        self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                   string=_("SpecSheet: "), italicized=True, bolded=True))
        self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                   string=_("specsheet"), hyper_link=row[2], new_paragraph=False,
                                                   color="blue",
                                                   underlined=True))
        # Dimensions
        if row[3]:
            self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                       string=_("Dimensions: \n"), italicized=True, bolded=True))
            dim = ""
            for key, value in row[3].items():
                if type(value) is dict:
                    data = key.title() + " (H x W x D): "
                    for subkey, subvalue in value.items():
                        data = data + str(subvalue) + " x "
                    data = data[:-2]  # remove the last " x "
                    dim = dim + "    " + data + "\n"
                else:
                    data = key.title().replace('_', ' ') + ": " + str(value)
                    dim = dim + "    " + data + "\n"
            dim = dim[:-1]  # remove the last "\n"
            self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                       string=dim, new_paragraph=False))

            # Weight
            if row[4]:
                self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                           string=_("Weight: \n"), italicized=True, bolded=True))
                weight = ""
                for key, value in row[4].items():
                    data = key.title().replace('_', ' ') + ": " + str(value)
                    weight = weight + "    " + data + "\n"
                weight = weight[:-1]  # remove the last "\n"
                self.content_list.append(GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                                           string=weight, new_paragraph=False))
