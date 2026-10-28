# coding: utf-8
# !/usr/bin/env python

""" fabric_lan.py: Easy UCS Deployment Tool """

from common import convert_to_range, format_network_ports
from report.content import GenericReportText, GenericReportAdmonition
from report.intersight.server_policies import IntersightNetworkConnectivityPolicyReportTable, \
    IntersightNtpPolicyReportTable, IntersightSyslogPolicyReportTable
from report.ucs.section import UcsReportSection
from report.ucs.table import UcsReportTable


class IntersightPortPolicyAppliancePortChannelInterfacesReportTable(UcsReportTable):
    def __init__(self, order_id, parent, interfaces, centered=False):
        rows = [[_("Slot ID"), _("Port ID"), _("Aggr ID")]]

        interfaces.sort(key=lambda x: str(x["slot_id"]) + "/" + str(x["port_id"]), reverse=False)

        for interface in interfaces:
            rows.append([interface["slot_id"], interface["port_id"], interface["aggr_id"]])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent,
                                row_number=len(rows), column_number=len(rows[1]),
                                centered=centered, cells_list=rows)


class IntersightPortPolicyFcoeUplinkPortsReportSection(UcsReportSection):
    def __init__(self, order_id, parent, fcoe_uplink_ports, title=""):
        if not title:
            title = _("FCoE Uplink Ports")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightPortPolicyFcoeUplinkPortsReportTable(
                order_id=self.report.get_current_order_id(), parent=self,
                fcoe_uplink_ports=fcoe_uplink_ports, centered=True,
            )
        )


class IntersightPortPolicyFcoeUplinkPortsReportTable(UcsReportTable):
    def __init__(self, order_id, parent, fcoe_uplink_ports, centered=False):
        rows = [[_("Port ID"), _("Admin Speed"), _("FEC"), _("Link Control Policy")]]

        fcoe_uplink_ports.sort(key=lambda x: x["port_id"], reverse=False)

        for fcoe_uplink_port in fcoe_uplink_ports:
            if fcoe_uplink_port["aggr_id"]:
                port_id = (str(fcoe_uplink_port["slot_id"]) + "/" + str(fcoe_uplink_port["port_id"]) + "/" +
                           str(fcoe_uplink_port["aggr_id"]))
            else:
                port_id = (str(fcoe_uplink_port["slot_id"]) + "/" + str(fcoe_uplink_port["port_id"]))
            rows.append([port_id, fcoe_uplink_port["admin_speed"], fcoe_uplink_port["fec"],
                         fcoe_uplink_port["link_control_policy"]])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent,
                                row_number=len(rows), column_number=len(rows[1]),
                                centered=centered, cells_list=rows)


class IntersightPortPolicyFcoePortChannelsReportSection(UcsReportSection):
    def __init__(self, order_id, parent, fcoe_port_channels, title=""):
        if not title:
            title = _("FCoE Port Channels")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightPortPolicyFcoePortChannelsReportTable(
                order_id=self.report.get_current_order_id(), parent=self,
                fcoe_port_channels=fcoe_port_channels, centered=True,
            )
        )

        for fcoe_port_channel in fcoe_port_channels:
            if fcoe_port_channel["interfaces"]:
                self.content_list.append(
                    IntersightPortPolicyFcoePortChannelInterfacesReportSection(
                        order_id=self.report.get_current_order_id(), parent=self,
                        interfaces=fcoe_port_channel["interfaces"],
                        title="FCoE Port Channel " + str(fcoe_port_channel["pc_id"]) + " - Interfaces",
                    )
                )


class IntersightPortPolicyFcoePortChannelsReportTable(UcsReportTable):
    def __init__(self, order_id, parent, fcoe_port_channels, centered=False):
        rows = [[_("Port-Channel ID"), _("Admin Speed"), _("Link Aggregation Policy"), _("Link Control Policy")]]

        fcoe_port_channels.sort(key=lambda x: x["pc_id"], reverse=False)

        for fcoe_port_channel in fcoe_port_channels:
            rows.append([fcoe_port_channel["pc_id"], fcoe_port_channel["admin_speed"],
                         fcoe_port_channel["link_aggregation_policy"], fcoe_port_channel["link_control_policy"]])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent,
                                row_number=len(rows), column_number=len(rows[1]),
                                centered=centered, cells_list=rows)


class IntersightPortPolicyFcoePortChannelInterfacesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, interfaces, title=""):
        if not title:
            title = _("FCoE Port Channel # - Interfaces")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightPortPolicyFcoePortChannelInterfacesReportTable(
                order_id=self.report.get_current_order_id(), parent=self,
                interfaces=interfaces, centered=True,
            )
        )


class IntersightPortPolicyFcoePortChannelInterfacesReportTable(UcsReportTable):
    def __init__(self, order_id, parent, interfaces, centered=False):
        rows = [[_("Slot ID"), _("Port ID"), _("Aggr ID")]]

        interfaces.sort(key=lambda x: str(x["slot_id"]) + "/" + str(x["port_id"]), reverse=False)

        for interface in interfaces:
            rows.append([interface["slot_id"], interface["port_id"], interface["aggr_id"]])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent,
                                row_number=len(rows), column_number=len(rows[1]),
                                centered=centered, cells_list=rows)


class IntersightPortPolicyLanUplinkPortsReportSection(UcsReportSection):
    def __init__(self, order_id, parent, lan_uplink_ports, title=""):
        if not title:
            title = _("LAN Uplink Ports")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightPortPolicyLanUplinkPortsReportTable(
                order_id=self.report.get_current_order_id(), parent=self,
                lan_uplink_ports=lan_uplink_ports, centered=True,
            )
        )


class IntersightPortPolicyLanUplinkPortsReportTable(UcsReportTable):
    def __init__(self, order_id, parent, lan_uplink_ports, centered=False):
        rows = [[_("Port ID"), _("Admin Speed"), _("FEC"), _("Ethernet Network Group Policy"),
                 _("Flow Control Policy"), _("Link Control Policy"), _("MACsec Policy")]]

        lan_uplink_ports.sort(key=lambda x: x["port_id"], reverse=False)

        for lan_uplink_port in lan_uplink_ports:
            if lan_uplink_port["aggr_id"]:
                port_id = (str(lan_uplink_port["slot_id"]) + "/" + str(lan_uplink_port["port_id"]) + "/" +
                           str(lan_uplink_port["aggr_id"]))
            else:
                port_id = (str(lan_uplink_port["slot_id"]) + "/" + str(lan_uplink_port["port_id"]))
            rows.append([port_id, lan_uplink_port["admin_speed"], lan_uplink_port["fec"],
                         lan_uplink_port["ethernet_network_group_policy"], lan_uplink_port["flow_control_policy"],
                         lan_uplink_port["link_control_policy"], lan_uplink_port["macsec_policy"]])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent,
                                row_number=len(rows), column_number=len(rows[1]),
                                centered=centered, cells_list=rows)


class IntersightPortPolicyLanPortChannelsReportSection(UcsReportSection):
    def __init__(self, order_id, parent, lan_port_channels, title=""):
        if not title:
            title = _("LAN Port Channels")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightPortPolicyLanPortChannelsReportTable(
                order_id=self.report.get_current_order_id(), parent=self,
                lan_port_channels=lan_port_channels, centered=True,
            )
        )

        for lan_port_channel in lan_port_channels:
            if lan_port_channel["interfaces"]:
                self.content_list.append(
                    IntersightPortPolicyLanPortChannelInterfacesReportSection(
                        order_id=self.report.get_current_order_id(), parent=self,
                        interfaces=lan_port_channel["interfaces"],
                        title="LAN Port Channel " + str(lan_port_channel["pc_id"]) + " - Interfaces",
                    )
                )


class IntersightPortPolicyLanPortChannelsReportTable(UcsReportTable):
    def __init__(self, order_id, parent, lan_port_channels, centered=False):
        rows = [[_("Port-Channel ID"), _("Admin Speed"), _("Ethernet Network Group Policy"),
                 _("Flow Control Policy"), _("Link Aggregation Policy"), _("Link Control Policy"), _("MACsec Policy")]]

        lan_port_channels.sort(key=lambda x: x["pc_id"], reverse=False)

        for lan_port_channel in lan_port_channels:
            rows.append([lan_port_channel["pc_id"], lan_port_channel["admin_speed"],
                         lan_port_channel["ethernet_network_group_policy"], lan_port_channel["flow_control_policy"],
                         lan_port_channel["link_aggregation_policy"], lan_port_channel["link_control_policy"],
                         lan_port_channel["macsec_policy"]])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent,
                                row_number=len(rows), column_number=len(rows[1]),
                                centered=centered, cells_list=rows)


class IntersightPortPolicyLanPortChannelInterfacesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, interfaces, title=""):
        if not title:
            title = _("LAN Port Channel # - Interfaces")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightPortPolicyLanPortChannelInterfacesReportTable(
                order_id=self.report.get_current_order_id(), parent=self,
                interfaces=interfaces, centered=True,
            )
        )


class IntersightPortPolicyLanPortChannelInterfacesReportTable(UcsReportTable):
    def __init__(self, order_id, parent, interfaces, centered=False):
        rows = [[_("Slot ID"), _("Port ID"), _("Aggr ID")]]

        interfaces.sort(key=lambda x: str(x["slot_id"]) + "/" + str(x["port_id"]), reverse=False)

        for interface in interfaces:
            rows.append([interface["slot_id"], interface["port_id"], interface["aggr_id"]])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent,
                                row_number=len(rows), column_number=len(rows[1]),
                                centered=centered, cells_list=rows)


class IntersightPortPolicySanStoragePortsReportSection(UcsReportSection):
    def __init__(self, order_id, parent, san_storage_ports, title=""):
        if not title:
            title = _("SAN Storage Ports")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightPortPolicySanStoragePortsReportTable(
                order_id=self.report.get_current_order_id(), parent=self,
                san_storage_ports=san_storage_ports, centered=True,
            )
        )


class IntersightPortPolicySanStoragePortsReportTable(UcsReportTable):
    def __init__(self, order_id, parent, san_storage_ports, centered=False):
        rows = [[_("Port ID"), _("Admin Speed"), _("VSAN ID")]]

        san_storage_ports.sort(key=lambda x: x["port_id"], reverse=False)

        for san_storage_port in san_storage_ports:
            port_id = (str(san_storage_port["slot_id"]) + "/" + str(san_storage_port["port_id"]))
            rows.append([port_id, san_storage_port["admin_speed"], san_storage_port["vsan_id"]])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent,
                                row_number=len(rows), column_number=len(rows[1]),
                                centered=centered, cells_list=rows)


class IntersightPortPolicySanUplinkPortsReportSection(UcsReportSection):
    def __init__(self, order_id, parent, san_uplink_ports, title=""):
        if not title:
            title = _("SAN Uplink Ports")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightPortPolicySanUplinkPortsReportTable(
                order_id=self.report.get_current_order_id(), parent=self,
                san_uplink_ports=san_uplink_ports, centered=True,
            )
        )


class IntersightPortPolicySanUplinkPortsReportTable(UcsReportTable):
    def __init__(self, order_id, parent, san_uplink_ports, centered=False):
        rows = [[_("Port ID"), _("Admin Speed"), _("VSAN ID"), _("Fill Pattern")]]

        san_uplink_ports.sort(key=lambda x: x["port_id"], reverse=False)

        for san_uplink_port in san_uplink_ports:
            port_id = (str(san_uplink_port["slot_id"]) + "/" + str(san_uplink_port["port_id"]))
            rows.append([port_id, san_uplink_port["admin_speed"], san_uplink_port["vsan_id"],
                         san_uplink_port["fill_pattern"]])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent,
                                row_number=len(rows), column_number=len(rows[1]),
                                centered=centered, cells_list=rows)


class IntersightPortPolicySanPortChannelsReportSection(UcsReportSection):
    def __init__(self, order_id, parent, san_port_channels, title=""):
        if not title:
            title = _("SAN Port Channels")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightPortPolicySanPortChannelsReportTable(
                order_id=self.report.get_current_order_id(), parent=self,
                san_port_channels=san_port_channels, centered=True,
            )
        )

        for san_port_channel in san_port_channels:
            if san_port_channel["interfaces"]:
                self.content_list.append(
                    IntersightPortPolicySanPortChannelInterfacesReportSection(
                        order_id=self.report.get_current_order_id(), parent=self,
                        interfaces=san_port_channel["interfaces"],
                        title="SAN Port Channel " + str(san_port_channel["pc_id"]) + " - Interfaces",
                    )
                )


class IntersightPortPolicySanPortChannelsReportTable(UcsReportTable):
    def __init__(self, order_id, parent, san_port_channels, centered=False):
        rows = [[_("Port-Channel ID"), _("Admin Speed"), _("VSAN ID"), _("Fill Pattern")]]

        san_port_channels.sort(key=lambda x: x["pc_id"], reverse=False)

        for san_port_channel in san_port_channels:
            rows.append([san_port_channel["pc_id"], san_port_channel["admin_speed"],
                         san_port_channel["vsan_id"], san_port_channel["fill_pattern"]])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent,
                                row_number=len(rows), column_number=len(rows[1]),
                                centered=centered, cells_list=rows)


class IntersightPortPolicySanPortChannelInterfacesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, interfaces, title=""):
        if not title:
            title = _("SAN Port Channel # - Interfaces")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightPortPolicySanPortChannelInterfacesReportTable(
                order_id=self.report.get_current_order_id(), parent=self,
                interfaces=interfaces, centered=True,
            )
        )


class IntersightPortPolicySanPortChannelInterfacesReportTable(UcsReportTable):
    def __init__(self, order_id, parent, interfaces, centered=False):
        rows = [[_("Slot ID"), _("Port ID")]]

        interfaces.sort(key=lambda x: str(x["slot_id"]) + "/" + str(x["port_id"]), reverse=False)

        for interface in interfaces:
            rows.append([interface["slot_id"], interface["port_id"]])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent,
                                row_number=len(rows), column_number=len(rows[1]),
                                centered=centered, cells_list=rows)


class IntersightPortPolicyServerPortsReportSection(UcsReportSection):
    def __init__(self, order_id, parent, server_ports, title=""):
        if not title:
            title = _("Server Ports")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightPortPolicyServerPortsReportTable(
                order_id=self.report.get_current_order_id(), parent=self,
                server_ports=server_ports, centered=True,
            )
        )


class IntersightPortPolicyServerPortsReportTable(UcsReportTable):
    def __init__(self, order_id, parent, server_ports, centered=False):
        connected_devices_present = False
        for server_port in server_ports:
            if server_port["connected_device_type"] or server_port["connected_device_id"]:
                connected_devices_present = True
                break

        if not connected_devices_present:
            rows = [[_("Slot ID"), _("Port ID Range"), _("Aggr ID Range")]]
            formatted_server_ports = []
            for formatted_port in format_network_ports(server_ports, logger=parent.report):
                ids = formatted_port.split("/")
                if len(ids) == 3:
                    formatted_server_ports.append(ids)
                elif len(ids) == 2:
                    formatted_server_ports.append([ids[0], ids[1], None])
                elif len(ids) == 1:
                    formatted_server_ports.append([ids[0], None, None])
            rows.extend(formatted_server_ports)
        else:
            rows = [[_("Slot ID"), _("Port ID"), _("Aggr ID"), _("Connected Device Type"), _("Connected Device ID")]]
            for port in sorted(server_ports, key=lambda x: x["port_id"]):
                rows.append([port["slot_id"], port["port_id"], port["aggr_id"], port["connected_device_type"],
                             str(port["connected_device_id"]) if port["connected_device_id"] is not None else None])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent,
                                row_number=len(rows), column_number=len(rows[1]),
                                centered=centered, cells_list=rows)


class IntersightVlanPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("VLAN Policies")

        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config
        descr = _("The following VLAN Policies define VLAN configurations for Fabric Interconnects.")
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self, string=descr))

        vlan_policies_list = []
        for org in config.orgs:
            self.parse_org(org, vlan_policies_list, element_to_parse="vlan_policies")

        if vlan_policies_list:
            for vlan_policy in vlan_policies_list:
                self.content_list.append(
                    IntersightVlanPolicyReportSection(
                        self.report.get_current_order_id(), parent=self,
                        vlan_policy=vlan_policy, name=vlan_policy.name))
        else:
            self.content_list.append(
                GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                  string=_("No VLAN Policies found."), italicized=True))


class IntersightVlanPolicyReportSection(UcsReportSection):
    def __init__(self, order_id, parent, vlan_policy, name="", title=""):
        if not title:
            title = _("VLAN Policy " + str(name))
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightVlanPolicyReportTable(
                order_id=self.report.get_current_order_id(), parent=self,
                vlan_policy=vlan_policy, centered=True))

        if vlan_policy.vlans:
            fabric = "_a"
            if vlan_policy.name.endswith("-A"):
                fabric = "_a"
            elif vlan_policy.name.endswith("-B"):
                fabric = "_b"

            duplicate_vlans = {}
            appliance_vlans = []
            descr = _("\nThe following table lists the VLANs that are part of VLAN Policy " + str(name) + ":")
            self.content_list.append(
                GenericReportText(order_id=self.report.get_current_order_id(), parent=self, string=descr))
            self.content_list.append(
                IntersightVlanPolicyVlansReportTable(
                    order_id=self.report.get_current_order_id(), parent=self,
                    vlan_policy=vlan_policy, duplicate_vlans=duplicate_vlans,
                    appliance_vlans=appliance_vlans, centered=True))


class IntersightVlanPolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, vlan_policy, centered=False):
        vlans = vlan_policy.vlans if vlan_policy.vlans else []
        rows = [
            [_("Description"), _("Value")],
            [_("Name"), vlan_policy.name],
            [_("Description"), vlan_policy.descr],
            [_("Target Platform"), vlan_policy.target_platform],
            [_("Number of VLANs"), str(len(vlans))],
        ]
        UcsReportTable.__init__(self, order_id=order_id, parent=parent,
                                row_number=len(rows), column_number=len(rows[0]),
                                centered=centered, cells_list=rows)


class IntersightVlanPolicyVlansReportTable(UcsReportTable):
    def __init__(self, order_id, parent, vlan_policy, duplicate_vlans, appliance_vlans, centered=False):
        rows = [[_("ID"), _("VLAN Name"), _("Native VLAN"), _("Multicast Policy"), _("Allow on all Uplinks"),
                 _("Sharing Type"), _("Primary VLAN ID"), _("Removed Duplicates"), _("Appliance VLAN")]]

        vlans = vlan_policy.vlans
        vlans.sort(key=lambda x: x["id"], reverse=False)
        fabric = ""
        if duplicate_vlans:
            if vlan_policy.name.endswith("-A"):
                fabric = "A"
            elif vlan_policy.name.endswith("-B"):
                fabric = "B"

        for vlan in vlans:
            removed_duplicates = ""
            if duplicate_vlans and vlan["id"] in duplicate_vlans:
                if duplicate_vlans[vlan["id"]]["fabric"] in ["dual", fabric]:
                    removed_duplicates = ", ".join(duplicate_vlans[vlan["id"]]["duplicate_names"])
            rows.append([
                vlan["id"], vlan["name"],
                vlan["native_vlan"] if vlan["native_vlan"] else None,
                vlan["multicast_policy"], vlan["auto_allow_on_uplinks"],
                vlan["sharing_type"], vlan["primary_vlan_id"],
                removed_duplicates,
                "Yes" if str(vlan["id"]) in appliance_vlans else "No",
            ])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent,
                                row_number=len(rows), column_number=len(rows[1]),
                                centered=centered, cells_list=rows)


class IntersightVsanPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("VSAN Policies")

        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config
        descr = _("The following VSAN Policies define VSAN configurations for Fabric Interconnects.")
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self, string=descr))

        vsan_policies_list = []
        for org in config.orgs:
            self.parse_org(org, vsan_policies_list, element_to_parse="vsan_policies")

        if vsan_policies_list:
            for vsan_policy in vsan_policies_list:
                self.content_list.append(
                    IntersightVsanPolicyReportSection(
                        self.report.get_current_order_id(), parent=self,
                        vsan_policy=vsan_policy, name=vsan_policy.name))
        else:
            self.content_list.append(
                GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                  string=_("No VSAN Policies found."), italicized=True))


class IntersightVsanPolicyReportSection(UcsReportSection):
    def __init__(self, order_id, parent, vsan_policy, name="", title=""):
        if not title:
            title = _("VSAN Policy " + str(name))
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightVsanPolicyReportTable(
                order_id=self.report.get_current_order_id(), parent=self,
                vsan_policy=vsan_policy, centered=True))

        if vsan_policy.vsans:
            fabric = "_a"
            if vsan_policy.name.endswith("-A"):
                fabric = "_a"
            elif vsan_policy.name.endswith("-B"):
                fabric = "_b"

            duplicate_vsans = {}
            descr = _("\nThe following table lists the VSANs that are part of VSAN Policy " + str(name) + ":")
            self.content_list.append(
                GenericReportText(order_id=self.report.get_current_order_id(), parent=self, string=descr))
            self.content_list.append(
                IntersightVsanPolicyVsansReportTable(
                    order_id=self.report.get_current_order_id(), parent=self,
                    vsan_policy=vsan_policy, duplicate_vsans=duplicate_vsans, centered=True))


class IntersightVsanPolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, vsan_policy, centered=False):
        vsans = vsan_policy.vsans if vsan_policy.vsans else []
        rows = [
            [_("Description"), _("Value")],
            [_("Name"), vsan_policy.name],
            [_("Description"), vsan_policy.descr],
            [_("FC Uplink Trunking"), vsan_policy.uplink_trunking],
            [_("Number of VSANs"), str(len(vsans))],
        ]
        UcsReportTable.__init__(self, order_id=order_id, parent=parent,
                                row_number=len(rows), column_number=len(rows[0]),
                                centered=centered, cells_list=rows)


class IntersightVsanPolicyVsansReportTable(UcsReportTable):
    def __init__(self, order_id, parent, vsan_policy, duplicate_vsans, centered=False):
        rows = [[_("ID"), _("VSAN Name"), _("FCoE VLAN ID"), _("Scope"), _("Removed Duplicates")]]

        vsans = vsan_policy.vsans
        vsans.sort(key=lambda x: x["id"], reverse=False)
        fabric = ""
        if duplicate_vsans:
            if vsan_policy.name.endswith("-A"):
                fabric = "A"
            elif vsan_policy.name.endswith("-B"):
                fabric = "B"

        for vsan in vsans:
            removed_duplicates = ""
            if duplicate_vsans and vsan["id"] in duplicate_vsans:
                if duplicate_vsans[vsan["id"]]["fabric"] in ["dual", fabric]:
                    removed_duplicates = ", ".join(duplicate_vsans[vsan["id"]]["duplicate_names"])
            rows.append([vsan["id"], vsan["name"], vsan["fcoe_vlan_id"],
                         vsan.get("scope"), removed_duplicates])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent,
                                row_number=len(rows), column_number=len(rows[1]),
                                centered=centered, cells_list=rows)


class IntersightMulticastPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Multicast Policies")

        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config
        default_multicast_policy_name = ""

        descr = _("The following Multicast Policies define multicast configurations for Fabric Interconnects.")
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self, string=descr))

        multicast_policies_list = []
        for org in config.orgs:
            self.parse_org(org, multicast_policies_list, element_to_parse="multicast_policies")

        if multicast_policies_list:
            for multicast_policy in multicast_policies_list:
                policy_name = multicast_policy.name + " (default)" \
                    if multicast_policy.name == default_multicast_policy_name else multicast_policy.name
                self.content_list.append(
                    IntersightMulticastPolicyReportSection(
                        self.report.get_current_order_id(), parent=self,
                        multicast_policy=multicast_policy, name=policy_name))
        else:
            self.content_list.append(
                GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                  string=_("No Multicast Policies found."), italicized=True))


class IntersightMulticastPolicyReportSection(UcsReportSection):
    def __init__(self, order_id, parent, multicast_policy, name="", title=""):
        if not title:
            title = _("Multicast Policy " + str(name))
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightMulticastPolicyReportTable(
                order_id=self.report.get_current_order_id(), parent=self,
                multicast_policy=multicast_policy, name=name, centered=True,
            )
        )


class IntersightMulticastPolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, multicast_policy, name="", centered=False):
        rows = [
            [_("Description"), _("Value")],
            [_("Name"), name],
            [_("Description"), multicast_policy.descr],
            [_("IGMP Snooping State"), multicast_policy.igmp_snooping_state],
            [_("IGMP Snooping Querier State"), multicast_policy.igmp_snooping_querier_state],
            [_("Querier IP Address"), multicast_policy.querier_ip_address],
            [_("Peer Querier IP Address"), multicast_policy.querier_ip_address_peer],
            [_("IGMP Source IP Proxy State"), multicast_policy.source_ip_proxy_state],
        ]
        UcsReportTable.__init__(self, order_id=order_id, parent=parent,
                                row_number=len(rows), column_number=len(rows[0]),
                                centered=centered, cells_list=rows)


class IntersightNetworkConnectivityPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Network Connectivity Policies")

        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config
        descr = _("The following Network Connectivity Policies define DNS configurations for Fabric Interconnects.")
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self, string=descr))

        network_connectivity_policies_list = []
        for org in config.orgs:
            self.parse_org(org, network_connectivity_policies_list,
                           element_to_parse="network_connectivity_policies")

        if network_connectivity_policies_list:
            for netconfig_policy in network_connectivity_policies_list:
                self.content_list.append(
                    IntersightNetworkConnectivityPolicyReportTable(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        netconfig_policy=netconfig_policy,
                        centered=True,
                    )
                )
                self.content_list.append(
                    GenericReportText(order_id=self.report.get_current_order_id(), parent=self, string="")
                )
        else:
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(), parent=self,
                    string=_("No Network Connectivity Policies found."), italicized=True,
                )
            )


class IntersightNtpPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("NTP Policies")

        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config
        descr = _("The following NTP Policies define NTP configurations for Fabric Interconnects.")
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self, string=descr))

        ntp_policies_list = []
        for org in config.orgs:
            self.parse_org(org, ntp_policies_list, element_to_parse="ntp_policies")

        if ntp_policies_list:
            for ntp_policy in ntp_policies_list:
                self.content_list.append(
                    IntersightNtpPolicyReportTable(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        ntp_policy=ntp_policy,
                        centered=True,
                    )
                )
        else:
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(), parent=self,
                    string=_("No NTP Policies found."), italicized=True,
                )
            )


class IntersightSyslogPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Syslog Policies")

        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config
        descr = _("The following Syslog Policies define Syslog configurations for Fabric Interconnects.")
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self, string=descr))

        syslog_policies_list = []
        for org in config.orgs:
            self.parse_org(org, syslog_policies_list, element_to_parse="syslog_policies")

        if syslog_policies_list:
            for syslog_policy in syslog_policies_list:
                self.content_list.append(
                    IntersightSyslogPolicyReportTable(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        syslog_policy=syslog_policy,
                        centered=True,
                    )
                )
        else:
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(), parent=self,
                    string=_("No Syslog Policies found."), italicized=True,
                )
            )


class IntersightSnmpPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("SNMP Policies")

        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config
        descr = _("The following SNMP Policies define SNMP configurations for Fabric Interconnects.")
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self, string=descr))

        snmp_policies_list = []
        for org in config.orgs:
            self.parse_org(org, snmp_policies_list, element_to_parse="snmp_policies")

        if snmp_policies_list:
            for snmp_policy in snmp_policies_list:
                self.content_list.append(
                    IntersightSnmpPolicyReportTable(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        snmp_policy=snmp_policy,
                        centered=True,
                    )
                )

                if snmp_policy.trap_destinations:
                    for trap_destination in snmp_policy.trap_destinations:
                        self.content_list.append(
                            IntersightSnmpPolicyTrapDestReportSection(
                                self.report.get_current_order_id(), parent=self,
                                trap_destination=trap_destination,
                                name=trap_destination["destination_address"],
                            )
                        )

                if snmp_policy.users:
                    for user in snmp_policy.users:
                        self.content_list.append(
                            IntersightSnmpPolicyUserReportSection(
                                self.report.get_current_order_id(), parent=self,
                                user=user, name=user["name"],
                            )
                        )
        else:
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(), parent=self,
                    string=_("No SNMP Policies found."), italicized=True,
                )
            )


class IntersightSnmpPolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, snmp_policy, centered=False):
        rows = [
            [_("Description"), _("Value")],
            [_("Name"), snmp_policy.name],
            [_("Enabled"), snmp_policy.enabled],
            [_("Access Community String"), snmp_policy.access_community_string],
            [_("Community Access"), snmp_policy.community_access],
            [_("Engine Input ID"), snmp_policy.engine_input_id],
            [_("Port"), snmp_policy.port],
            [_("System Contact"), snmp_policy.system_contact],
            [_("System Location"), snmp_policy.system_location],
            [_("Trap Community String"), snmp_policy.trap_community_string],
        ]

        UcsReportTable.__init__(self, order_id=order_id, parent=parent,
                                row_number=len(rows), column_number=len(rows[0]),
                                centered=centered, cells_list=rows)


class IntersightSnmpPolicyTrapDestReportSection(UcsReportSection):
    def __init__(self, order_id, parent, trap_destination, name="", title=""):
        if not title:
            title = _("Trap Destination " + str(name))
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightSnmpPolicyTrapDestReportTable(
                order_id=self.report.get_current_order_id(), parent=self,
                trap_destination=trap_destination, name=name, centered=True,
            )
        )


class IntersightSnmpPolicyTrapDestReportTable(UcsReportTable):
    def __init__(self, order_id, parent, trap_destination, name="", centered=False):
        rows = [
            [_("Description"), _("Value")],
            [_("Destination Address"), name],
            [_("Enabled"), trap_destination["enabled"]],
            [_("Port"), trap_destination["port"]],
            [_("Trap Type"), trap_destination["trap_type"]],
            [_("Community"), trap_destination["community"]],
            [_("User"), trap_destination["user"]],
            [_("Version"), trap_destination["version"]],
        ]

        UcsReportTable.__init__(self, order_id=order_id, parent=parent,
                                row_number=len(rows), column_number=len(rows[0]),
                                centered=centered, cells_list=rows)


class IntersightSnmpPolicyUserReportSection(UcsReportSection):
    def __init__(self, order_id, parent, user, name="", title=""):
        if not title:
            title = _("User " + str(name))
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightSnmpPolicyUserReportTable(
                order_id=self.report.get_current_order_id(), parent=self,
                user=user, name=name, centered=True,
            )
        )


class IntersightSnmpPolicyUserReportTable(UcsReportTable):
    def __init__(self, order_id, parent, user, name="", centered=False):
        rows = [
            [_("Description"), _("Value")],
            [_("Name"), name],
            [_("Auth Type"), user["auth_type"]],
            [_("Auth Password"), user["auth_password"]],
            [_("Privacy Type"), user["privacy_type"]],
            [_("Privacy Password"), user["privacy_password"]],
            [_("Security Level"), user["security_level"]],
        ]

        UcsReportTable.__init__(self, order_id=order_id, parent=parent,
                                row_number=len(rows), column_number=len(rows[0]),
                                centered=centered, cells_list=rows)

class IntersightPortPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Port Policies")

        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config
        descr = _("The following Port Policies define port configurations for Fabric Interconnects.")
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self, string=descr))

        port_policies_list = []
        for org in config.orgs:
            self.parse_org(org, port_policies_list, element_to_parse="port_policies")

        if port_policies_list:
            for port_policy in port_policies_list:
                fabric = None
                self.content_list.append(
                    IntersightPortPolicyReportSection(
                        self.report.get_current_order_id(),
                        parent=self,
                        port_policy=port_policy,
                        fabric=fabric,
                        name=port_policy.name,
                    )
                )
        else:
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(), parent=self,
                    string=_("No Port Policies found."), italicized=True,
                )
            )


class IntersightPortPolicyReportSection(UcsReportSection):
    def __init__(self, order_id, parent, port_policy, fabric=None, name="", title=""):
        if not title:
            title = _("Port Policy " + str(name))
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if port_policy.san_unified_ports:
            self.content_list.append(
                IntersightPortPolicySanUnifiedPortsReportSection(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    san_unified_ports=port_policy.san_unified_ports,
                )
            )

        if port_policy.appliance_ports:
            self.content_list.append(
                IntersightPortPolicyAppliancePortsReportSection(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    appliance_ports=port_policy.appliance_ports,
                )
            )

        if port_policy.appliance_port_channels:
            self.content_list.append(
                IntersightPortPolicyAppliancePortChannelsReportSection(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    appliance_port_channels=port_policy.appliance_port_channels,
                )
            )

        if port_policy.fcoe_uplink_ports:
            self.content_list.append(
                IntersightPortPolicyFcoeUplinkPortsReportSection(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    fcoe_uplink_ports=port_policy.fcoe_uplink_ports,
                )
            )

        if port_policy.fcoe_port_channels:
            self.content_list.append(
                IntersightPortPolicyFcoePortChannelsReportSection(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    fcoe_port_channels=port_policy.fcoe_port_channels,
                )
            )

        if port_policy.lan_uplink_ports:
            self.content_list.append(
                IntersightPortPolicyLanUplinkPortsReportSection(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    lan_uplink_ports=port_policy.lan_uplink_ports,
                )
            )

        if port_policy.lan_port_channels:
            self.content_list.append(
                IntersightPortPolicyLanPortChannelsReportSection(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    lan_port_channels=port_policy.lan_port_channels,
                )
            )

        if port_policy.san_storage_ports:
            self.content_list.append(
                IntersightPortPolicySanStoragePortsReportSection(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    san_storage_ports=port_policy.san_storage_ports,
                )
            )

        if port_policy.san_uplink_ports:
            self.content_list.append(
                IntersightPortPolicySanUplinkPortsReportSection(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    san_uplink_ports=port_policy.san_uplink_ports,
                )
            )

        if port_policy.san_port_channels:
            self.content_list.append(
                IntersightPortPolicySanPortChannelsReportSection(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    san_port_channels=port_policy.san_port_channels,
                )
            )

        if port_policy.server_ports:
            self.content_list.append(
                IntersightPortPolicyServerPortsReportSection(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    server_ports=port_policy.server_ports,
                )
            )


class IntersightPortPolicySanUnifiedPortsReportSection(UcsReportSection):
    def __init__(self, order_id, parent, san_unified_ports, title=""):
        if not title:
            title = _("SAN Unified Ports")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightPortPolicySanUnifiedPortsReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                san_unified_ports=san_unified_ports,
                centered=True,
            )
        )


class IntersightPortPolicySanUnifiedPortsReportTable(UcsReportTable):
    def __init__(self, order_id, parent, san_unified_ports, centered=False):
        rows = [["", _("Port ID Start"), _("Port ID End")]]

        port_id_start = (str(san_unified_ports["slot_id"]) + "/" + str(san_unified_ports["port_id_start"]))
        port_id_end = (str(san_unified_ports["slot_id"]) + "/" + str(san_unified_ports["port_id_end"]))
        rows.append([_("Range"), port_id_start, port_id_end])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent,
                                row_number=len(rows), column_number=len(rows[1]),
                                centered=centered, cells_list=rows)


class IntersightPortPolicyAppliancePortsReportSection(UcsReportSection):
    def __init__(self, order_id, parent, appliance_ports, title=""):
        if not title:
            title = _("Appliance Ports")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightPortPolicyAppliancePortsReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                appliance_ports=appliance_ports,
                centered=True,
            )
        )


class IntersightPortPolicyAppliancePortsReportTable(UcsReportTable):
    def __init__(self, order_id, parent, appliance_ports, centered=False):
        rows = [[_("Port ID"), _("Admin Speed"), _("FEC"), _("Mode"), _("Priority"),
                 _("Ethernet Network Group Policy"), _("Ethernet Network Control Policy")]]

        appliance_ports.sort(key=lambda x: x["port_id"], reverse=False)

        for appliance_port in appliance_ports:
            if appliance_port["aggr_id"]:
                port_id = (str(appliance_port["slot_id"]) + "/" + str(appliance_port["port_id"]) + "/" +
                           str(appliance_port["aggr_id"]))
            else:
                port_id = (str(appliance_port["slot_id"]) + "/" + str(appliance_port["port_id"]))
            rows.append([
                port_id,
                appliance_port["admin_speed"],
                appliance_port["fec"],
                appliance_port["mode"],
                appliance_port["priority"],
                appliance_port["ethernet_network_group_policy"],
                appliance_port["ethernet_network_control_policy"],
            ])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent,
                                row_number=len(rows), column_number=len(rows[1]),
                                centered=centered, cells_list=rows)


class IntersightPortPolicyAppliancePortChannelsReportSection(UcsReportSection):
    def __init__(self, order_id, parent, appliance_port_channels, title=""):
        if not title:
            title = _("Appliance Port Channels")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightPortPolicyAppliancePortChannelsReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                appliance_port_channels=appliance_port_channels,
                centered=True,
            )
        )

        for appliance_port_channel in appliance_port_channels:
            if appliance_port_channel["interfaces"]:
                self.content_list.append(
                    IntersightPortPolicyAppliancePortChannelInterfacesReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        interfaces=appliance_port_channel["interfaces"],
                        title="Appliance Port Channel " + str(appliance_port_channel["pc_id"]) + " - Interfaces",
                    )
                )


class IntersightPortPolicyAppliancePortChannelsReportTable(UcsReportTable):
    def __init__(self, order_id, parent, appliance_port_channels, centered=False):
        rows = [[_("Port-Channel ID"), _("Admin Speed"), _("Mode"), _("Priority"),
                 _("Ethernet Network Group Policy"), _("Ethernet Network Control Policy")]]

        appliance_port_channels.sort(key=lambda x: x["pc_id"], reverse=False)

        for appliance_port_channel in appliance_port_channels:
            rows.append([
                appliance_port_channel["pc_id"],
                appliance_port_channel["admin_speed"],
                appliance_port_channel["mode"],
                appliance_port_channel["priority"],
                appliance_port_channel["ethernet_network_group_policy"],
                appliance_port_channel["ethernet_network_control_policy"],
            ])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent,
                                row_number=len(rows), column_number=len(rows[1]),
                                centered=centered, cells_list=rows)


class IntersightPortPolicyAppliancePortChannelInterfacesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, interfaces, title=""):
        if not title:
            title = _("Appliance Port Channel # - Interfaces")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightPortPolicyAppliancePortChannelInterfacesReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                interfaces=interfaces,
                centered=True,
            )
        )


class IntersightLdapPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("LDAP Policies")

        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config
        descr = _("The following LDAP Policies define LDAP authentication configurations for Fabric Interconnects.")
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self, string=descr))

        ldap_policies_list = []
        for org in config.orgs:
            self.parse_org(org, ldap_policies_list, element_to_parse="ldap_policies")

        if ldap_policies_list:
            for ldap_policy in ldap_policies_list:
                self.content_list.append(
                    IntersightLdapPolicyReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        ldap_policy=ldap_policy,
                        name=ldap_policy.name,
                    )
                )
        else:
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=_("No LDAP Policies found."),
                    italicized=True,
                )
            )


class IntersightLdapPolicyReportSection(UcsReportSection):
    def __init__(self, order_id, parent, ldap_policy, name="", title=""):
        if not title:
            title = _("LDAP Policy " + str(name))
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightLdapPolicyReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                ldap_policy=ldap_policy,
                name=name,
                centered=True,
            )
        )
        if ldap_policy.base_properties:
            self.content_list.append(
                IntersightLdapPolicyBasePropertiesReportSection(
                    self.report.get_current_order_id(),
                    parent=self,
                    base_properties=ldap_policy.base_properties,
                    name=name,
                )
            )
        if ldap_policy.dns_parameters:
            self.content_list.append(
                IntersightLdapPolicyDnsReportSection(
                    self.report.get_current_order_id(),
                    parent=self,
                    dns_parameters=ldap_policy.dns_parameters,
                    name=name,
                )
            )
        if ldap_policy.providers:
            for provider in ldap_policy.providers:
                self.content_list.append(
                    IntersightLdapPolicyProviderReportSection(
                        self.report.get_current_order_id(),
                        parent=self,
                        provider=provider,
                        name=name,
                    )
                )
        if ldap_policy.groups:
            for group in ldap_policy.groups:
                self.content_list.append(
                    IntersightLdapPolicyGroupReportSection(
                        self.report.get_current_order_id(),
                        parent=self,
                        group=group,
                        name=name,
                    )
                )


class IntersightLdapPolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, ldap_policy, name="", centered=False):
        rows = [
            [_("Description"), _("Value")],
            [_("Name"), name],
            [_("Description"), ldap_policy.descr],
            [_("Enable LDAP"), ldap_policy.enable_ldap],
            [_("Enable DNS"), ldap_policy.enable_dns],
            [_("User Search Precedence"), ldap_policy.user_search_precedence],
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[0]),
            centered=centered,
            cells_list=rows,
        )


class IntersightLdapPolicyBasePropertiesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, base_properties, name="", title=""):
        if not title:
            title = _("LDAP Policy '" + str(name) + "' Base Properties")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightLdapPolicyBasePropertiesReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                base_properties=base_properties,
                centered=True,
            )
        )


class IntersightLdapPolicyBasePropertiesReportTable(UcsReportTable):
    def __init__(self, order_id, parent, base_properties, centered=False):
        rows = [
            [_("Description"), _("Value")],
            [_("Base DN"), base_properties.get("base_dn")],
            [_("Domain"), base_properties.get("domain")],
            [_("Timeout"), base_properties.get("timeout")],
            [_("Enable Encryption"), base_properties.get("enable_encryption")],
            [_("Bind Method"), base_properties.get("bind_method")],
            [_("Bind DN"), base_properties.get("bind_dn")],
            [_("Bind Password"), base_properties.get("bind_password")],
            [_("Filter"), base_properties.get("filter")],
            [_("Group Attribute"), base_properties.get("group_attribute")],
            [_("Attribute"), base_properties.get("attribute")],
            [_("Enable Group Authorization"), base_properties.get("enable_group_authorization")],
            [_("Enable Nested Group Search"), base_properties.get("enable_nested_group_search")],
            [_("Nested Group Search Depth"), base_properties.get("nested_group_search_depth")],
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[0]),
            centered=centered,
            cells_list=rows,
        )


class IntersightLdapPolicyDnsReportSection(UcsReportSection):
    def __init__(self, order_id, parent, dns_parameters, name="", title=""):
        if not title:
            title = _("LDAP Policy '" + str(name) + "' DNS Parameters")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightLdapPolicyDnsReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                dns_parameters=dns_parameters,
                centered=True,
            )
        )


class IntersightLdapPolicyDnsReportTable(UcsReportTable):
    def __init__(self, order_id, parent, dns_parameters, centered=False):
        rows = [
            [_("Description"), _("Value")],
            [_("Source"), dns_parameters.get("source")],
            [_("Search Domain"), dns_parameters.get("search_domain")],
            [_("Search Forest"), dns_parameters.get("search_forest")],
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[0]),
            centered=centered,
            cells_list=rows,
        )


class IntersightLdapPolicyProviderReportSection(UcsReportSection):
    def __init__(self, order_id, parent, provider, name="", title=""):
        if not title:
            title = _("LDAP Policy '" + str(name) + "' Provider")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightLdapPolicyProviderReportTable(
                self.report.get_current_order_id(),
                parent=self,
                provider=provider,
            )
        )


class IntersightLdapPolicyProviderReportTable(UcsReportTable):
    def __init__(self, order_id, parent, provider, centered=False):
        rows = [
            [_("Description"), _("Value")],
            [_("LDAP Server"), provider.get("ldap_server")],
            [_("LDAP Server Port"), provider.get("ldap_server_port")],
            [_("Vendor"), provider.get("vendor")],
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[0]),
            centered=centered,
            cells_list=rows,
        )


class IntersightLdapPolicyGroupReportSection(UcsReportSection):
    def __init__(self, order_id, parent, group, name="", title=""):
        if not title:
            title = _("LDAP Policy '" + str(name) + "' Group")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightLdapPolicyGroupReportTable(
                self.report.get_current_order_id(),
                parent=self,
                group=group,
            )
        )


class IntersightLdapPolicyGroupReportTable(UcsReportTable):
    def __init__(self, order_id, parent, group, centered=False):
        rows = [
            [_("Description"), _("Value")],
            [_("Name"), group.get("name")],
            [_("Domain"), group.get("domain")],
            [_("Group DN"), group.get("group_dn")],
            [_("Role"), group.get("role")],
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[0]),
            centered=centered,
            cells_list=rows,
        )


class IntersightSystemQosPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("System QoS Policies")

        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config
        descr = _("The following System QoS Policies define QoS configurations for Fabric Interconnects.")
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self, string=descr))

        system_qos_policies_list = []
        for org in config.orgs:
            self.parse_org(org, system_qos_policies_list, element_to_parse="system_qos_policies")

        if system_qos_policies_list:
            for system_qos_policy in system_qos_policies_list:
                self.content_list.append(
                    IntersightSystemQosPolicyReportTable(
                        order_id=self.report.get_current_order_id(), parent=self,
                        system_qos_policy=system_qos_policy, centered=True,
                    )
                )
                if hasattr(system_qos_policy, 'watchdog_enabled') and system_qos_policy.watchdog_enabled is not None:
                    self.content_list.append(
                        IntersightSystemQosPolicyWatchdogReportSection(
                            order_id=self.report.get_current_order_id(), parent=self,
                            system_qos_policy=system_qos_policy,
                        )
                    )
        else:
            self.content_list.append(
                GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                  string=_("No System QoS Policies found."), italicized=True))


class IntersightSystemQosPolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, system_qos_policy, centered=False):
        if system_qos_policy.classes:
            rows = [[_("Priority"), _("State"), _("CoS"), _("Packet Drop"), _("Weight"), _("MTU"),
                     _("Multicast Optimized")]]
            priority_order = ["Platinum", "Gold", "Silver", "Bronze", "FC", "Best Effort"]
            order = {key: i for i, key in enumerate(priority_order)}
            for priority in sorted(system_qos_policy.classes, key=lambda x: order[x["priority"]]):
                rows.append([priority["priority"], priority["state"], priority["cos"],
                             priority["packet_drop"], priority["weight"], priority["mtu"],
                             priority["multicast_optimized"]])
            UcsReportTable.__init__(self, order_id=order_id, parent=parent,
                                    row_number=len(rows), column_number=len(rows[1]),
                                    centered=centered, cells_list=rows)


class IntersightSystemQosPolicyWatchdogReportSection(UcsReportSection):
    def __init__(self, order_id, parent, system_qos_policy, title=""):
        if not title:
            title = _("PFC Watchdog")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        self.content_list.append(
            IntersightSystemQosPolicyWatchdogReportTable(
                order_id=self.report.get_current_order_id(), parent=self,
                system_qos_policy=system_qos_policy, centered=True))


class IntersightSystemQosPolicyWatchdogReportTable(UcsReportTable):
    def __init__(self, order_id, parent, system_qos_policy, centered=False):
        rows = [[_("Description"), _("Value")],
                [_("Watchdog Enabled"), system_qos_policy.watchdog_enabled]]
        if system_qos_policy.pfc_watchdog_configuration:
            rows.append([_("Watchdog Interval (ms)"),
                         system_qos_policy.pfc_watchdog_configuration.get("watchdog_interval")])
            rows.append([_("Shutdown Multiplier"),
                         system_qos_policy.pfc_watchdog_configuration.get("shutdown_multiplier")])
        UcsReportTable.__init__(self, order_id=order_id, parent=parent,
                                row_number=len(rows), column_number=len(rows[0]),
                                centered=centered, cells_list=rows)


class IntersightSwitchControlPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Switch Control Policies")

        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config
        descr = _("The following Switch Control Policies define switch control configurations for Fabric Interconnects.")
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self, string=descr))

        switch_control_policies_list = []
        for org in config.orgs:
            self.parse_org(org, switch_control_policies_list, element_to_parse="switch_control_policies")

        if switch_control_policies_list:
            for switch_control_policy in switch_control_policies_list:
                self.content_list.append(
                    IntersightSwitchControlPolicyReportTable(
                        order_id=self.report.get_current_order_id(), parent=self,
                        switch_control_policy=switch_control_policy, centered=True))
        else:
            self.content_list.append(
                GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                  string=_("No Switch Control Policies found."), italicized=True))


class IntersightSwitchControlPolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, switch_control_policy, centered=False):
        rows = [
            [_("Description"), _("Value")],
            [_("Name"), switch_control_policy.name],
            [_("Target Platform"), switch_control_policy.target_platform],
            [_("Fabric Port-Channel vHBA Reset"), switch_control_policy.fabric_port_channel_vhba_reset],
            [_("VLAN Port Count Optimization"), switch_control_policy.vlan_port_count_optimization],
            [_("Reserved VLAN Start ID"), switch_control_policy.reserved_vlan_start_id],
            [_("MAC Address Table Aging"), switch_control_policy.mac_address_table_aging],
            [_("MAC Aging Time"), switch_control_policy.mac_aging_time],
        ]
        if switch_control_policy.switching_mode:
            rows.append([_("Ethernet Switch Mode"), switch_control_policy.switching_mode["ethernet"]])
            rows.append([_("FC Switch Mode"), switch_control_policy.switching_mode["fc"]])
        if switch_control_policy.link_control_global_settings:
            rows.append([_("Message Interval"),
                         switch_control_policy.link_control_global_settings["message_interval"]])
            rows.append([_("Recovery Action"),
                         switch_control_policy.link_control_global_settings["recovery_action"]])
        UcsReportTable.__init__(self, order_id=order_id, parent=parent,
                                row_number=len(rows), column_number=len(rows[0]),
                                centered=centered, cells_list=rows)


class IntersightThermalPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Thermal Policies")

        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config
        descr = _("The following Thermal Policies define fan control configurations for Fabric Interconnects.")
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self, string=descr))

        thermal_policies_list = []
        for org in config.orgs:
            self.parse_org(org, thermal_policies_list, element_to_parse="thermal_policies")

        if thermal_policies_list:
            for thermal_policy in thermal_policies_list:
                self.content_list.append(
                    IntersightThermalPolicyReportTable(
                        order_id=self.report.get_current_order_id(), parent=self,
                        thermal_policy=thermal_policy, centered=True))
        else:
            self.content_list.append(
                GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                  string=_("No Thermal Policies found."), italicized=True))


class IntersightThermalPolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, thermal_policy, centered=False):
        rows = [
            [_("Description"), _("Value")],
            [_("Name"), thermal_policy.name],
            [_("Description"), thermal_policy.descr],
            [_("Fan Control Mode"), thermal_policy.fan_control_mode],
        ]
        UcsReportTable.__init__(self, order_id=order_id, parent=parent,
                                row_number=len(rows), column_number=len(rows[0]),
                                centered=centered, cells_list=rows)


class IntersightPowerPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Power Policies")

        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config
        descr = _("The following Power Policies define power management configurations for Fabric Interconnects.")
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self, string=descr))

        power_policies_list = []
        for org in config.orgs:
            self.parse_org(org, power_policies_list, element_to_parse="power_policies")

        if power_policies_list:
            for power_policy in power_policies_list:
                self.content_list.append(
                    IntersightPowerPolicyReportTable(
                        order_id=self.report.get_current_order_id(), parent=self,
                        power_policy=power_policy, centered=True))
        else:
            self.content_list.append(
                GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                  string=_("No Power Policies found."), italicized=True))


class IntersightPowerPolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, power_policy, centered=False):
        rows = [
            [_("Description"), _("Value")],
            [_("Name"), power_policy.name],
            [_("Description"), power_policy.descr],
            [_("Power Redundancy"), power_policy.power_redundancy],
            [_("Power Save Mode"), power_policy.power_save_mode],
        ]
        UcsReportTable.__init__(self, order_id=order_id, parent=parent,
                                row_number=len(rows), column_number=len(rows[0]),
                                centered=centered, cells_list=rows)


class IntersightPowerGroupsReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Power Groups")

        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config
        descr = _("The following Power Groups define power budget configurations for devices in the domain.")
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self, string=descr))

        power_groups_list = config.power_groups

        if power_groups_list:
            for power_group in power_groups_list:
                self.content_list.append(
                    IntersightPowerGroupReportSection(
                        self.report.get_current_order_id(),
                        parent=self,
                        power_group=power_group,
                        name=power_group.name,
                    )
                )
        else:
            self.content_list.append(
                GenericReportText(order_id=self.report.get_current_order_id(), parent=self,
                                  string=_("No Power Groups found."), italicized=True))


class IntersightPowerGroupReportSection(UcsReportSection):
    def __init__(self, order_id, parent, power_group, name="", title=""):
        if not title:
            title = _("Power Group " + str(name))
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightPowerGroupReportTable(
                order_id=self.report.get_current_order_id(), parent=self,
                power_group=power_group, name=name, centered=True))


class IntersightPowerGroupReportTable(UcsReportTable):
    def __init__(self, order_id, parent, power_group, name="", centered=False):
        rows = [
            [_("Description"), _("Value")],
            [_("Name"), name],
            [_("Description"), power_group.descr],
            [_("Power Budget (W)"), power_group.power_group_budget],
            [_("Admin State"), power_group.admin_state],
        ]

        # Add member devices if present
        if power_group.power_group_devices:
            for chassis in power_group.power_group_devices.get("chassis", []):
                rows.append([_("Chassis"), chassis.get("serial") or _("N/A")])
            for fi in power_group.power_group_devices.get("fabric_interconnects", []):
                rows.append([_(f"FI-{fi.get('switch_id')}"), fi.get("serial") or _("N/A")])
            for fex in power_group.power_group_devices.get("fabric_extenders", []):
                rows.append([_("Fabric Extender"), fex.get("serial") or _("N/A")])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent,
                                row_number=len(rows), column_number=len(rows[0]),
                                centered=centered, cells_list=rows)


class IntersightEthernetNetworkControlPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Ethernet Network Control Policies")

        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config
        default_policy_name = ""

        descr = _("The following Ethernet Network Control Policies define network control configurations for Fabric Interconnects.")
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self, string=descr))

        ethernet_network_control_policies_list = []
        for org in config.orgs:
            self.parse_org(org, ethernet_network_control_policies_list,
                           element_to_parse="ethernet_network_control_policies")

        found = False
        for ethernet_network_control_policy in ethernet_network_control_policies_list:
            if "_appliance" in ethernet_network_control_policy.name:
                found = True
                if ethernet_network_control_policy.name == default_policy_name:
                    policy_name = ethernet_network_control_policy.name + " (default)"
                else:
                    policy_name = ethernet_network_control_policy.name
                self.content_list.append(
                    IntersightEthernetNetworkControlPolicyReportSection(
                        self.report.get_current_order_id(),
                        parent=self,
                        ethernet_network_control_policy=ethernet_network_control_policy,
                        name=policy_name,
                    )
                )

        if not found:
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=_("No Appliance Ethernet Network Control Policies found."),
                    italicized=True,
                )
            )


class IntersightEthernetNetworkControlPolicyReportSection(UcsReportSection):
    def __init__(self, order_id, parent, ethernet_network_control_policy, name="", title=""):
        if not title:
            title = _("Ethernet Network Control Policy " + str(name))
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightEthernetNetworkControlPolicyReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                ethernet_network_control_policy=ethernet_network_control_policy,
                name=name,
                centered=True,
            )
        )


class IntersightEthernetNetworkControlPolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, ethernet_network_control_policy, name="", centered=False):
        mac_register_mode = None
        action_on_uplink_fail = None
        mac_security_forge = None
        if ethernet_network_control_policy.mac_register_mode == "nativeVlanOnly":
            mac_register_mode = "Only Native VLAN"
        elif ethernet_network_control_policy.mac_register_mode == "allVlans":
            mac_register_mode = "All Host VLANs"
        if ethernet_network_control_policy.action_on_uplink_fail == "warning":
            action_on_uplink_fail = "Warning"
        elif ethernet_network_control_policy.action_on_uplink_fail == "linkDown":
            action_on_uplink_fail = "Link Down"
        if ethernet_network_control_policy.mac_security_forge == "deny":
            mac_security_forge = "Deny"
        elif ethernet_network_control_policy.mac_security_forge == "allow":
            mac_security_forge = "Allow"

        rows = [
            [_("Description"), _("Value")],
            [_("Name"), name],
            [_("Description"), ethernet_network_control_policy.descr],
            [_("Enable CDP"), ethernet_network_control_policy.cdp_enable],
            [_("MAC Register Mode"), mac_register_mode],
            [_("Action on Uplink Fail"), action_on_uplink_fail],
            [_("MAC Security - MAC Forging"), mac_security_forge],
            [_("LLDP Transmit"), ethernet_network_control_policy.lldp_transmit_enable],
            [_("LLDP Receive"), ethernet_network_control_policy.lldp_receive_enable],
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[0]),
            centered=centered,
            cells_list=rows,
        )


class IntersightEthernetNetworkGroupPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Ethernet Network Group Policies")

        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config
        descr = _("The following Ethernet Network Group Policies define VLAN group configurations for Fabric Interconnects.")
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self, string=descr))

        ethernet_network_group_policies_list = []
        for org in config.orgs:
            self.parse_org(org, ethernet_network_group_policies_list,
                           element_to_parse="ethernet_network_group_policies")

        if ethernet_network_group_policies_list:
            for ethernet_network_group_policy in ethernet_network_group_policies_list:
                self.content_list.append(
                    IntersightEthernetNetworkGroupPolicyReportSection(
                        self.report.get_current_order_id(),
                        parent=self,
                        ethernet_network_group_policy=ethernet_network_group_policy,
                        name=ethernet_network_group_policy.name,
                    )
                )
        else:
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=_("No Ethernet Network Group Policies found."),
                    italicized=True,
                )
            )


class IntersightEthernetNetworkGroupPolicyReportSection(UcsReportSection):
    def __init__(self, order_id, parent, ethernet_network_group_policy, name="", title=""):
        if not title:
            title = _("Ethernet Network Group Policy " + str(name))
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightEthernetNetworkGroupPolicyReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                ethernet_network_group_policy=ethernet_network_group_policy,
                name=name,
                centered=True,
            )
        )


class IntersightEthernetNetworkGroupPolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, ethernet_network_group_policy, name="", centered=False):
        rows = [
            [_("Description"), _("Value")],
            [_("Name"), name],
            [_("Description"), ethernet_network_group_policy.descr],
            [_("Organization"), ethernet_network_group_policy._parent.name],
            [_("Allowed VLAN IDs"), convert_to_range(ethernet_network_group_policy.allowed_vlans)],
            [_("Native VLAN ID"), ethernet_network_group_policy.native_vlan],
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[0]),
            centered=centered,
            cells_list=rows,
        )


class IntersightFlowControlPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Flow Control Policies")

        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config
        descr = _("The following Flow Control Policies define PFC configurations for Fabric Interconnects.")
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self, string=descr))

        flow_control_policies_list = []
        for org in config.orgs:
            self.parse_org(org, flow_control_policies_list, element_to_parse="flow_control_policies")

        if flow_control_policies_list:
            for flow_control_policy in flow_control_policies_list:
                self.content_list.append(
                    IntersightFlowControlPolicyReportSection(
                        self.report.get_current_order_id(),
                        parent=self,
                        flow_control_policy=flow_control_policy,
                        name=flow_control_policy.name,
                    )
                )
        else:
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=_("No Flow Control Policies found."),
                    italicized=True,
                )
            )


class IntersightFlowControlPolicyReportSection(UcsReportSection):
    def __init__(self, order_id, parent, flow_control_policy, name="", title=""):
        if not title:
            title = _("Flow Control Policy " + str(name))
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightFlowControlPolicyReportTable(
                order_id=self.report.get_current_order_id(), parent=self,
                flow_control_policy=flow_control_policy, name=name, centered=True,
            )
        )


class IntersightFlowControlPolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, flow_control_policy, name="", centered=False):
        rows = [
            [_("Description"), _("Value")],
            [_("Name"), name],
            [_("Description"), flow_control_policy.descr],
            [_("Priority"), flow_control_policy.priority],
            [_("Receive"), flow_control_policy.receive],
            [_("Send"), flow_control_policy.send],
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[0]),
            centered=centered,
            cells_list=rows,
        )


class IntersightLinkAggregationPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Link Aggregation Policies")

        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config
        descr = _("The following Link Aggregation Policies define LACP configurations for Fabric Interconnects.")
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self, string=descr))

        link_aggregation_policies_list = []
        for org in config.orgs:
            self.parse_org(org, link_aggregation_policies_list, element_to_parse="link_aggregation_policies")

        if link_aggregation_policies_list:
            for link_aggregation_policy in link_aggregation_policies_list:
                self.content_list.append(
                    IntersightLinkAggregationPolicyReportSection(
                        self.report.get_current_order_id(),
                        parent=self,
                        link_aggregation_policy=link_aggregation_policy,
                        name=link_aggregation_policy.name,
                    )
                )
        else:
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=_("No Link Aggregation Policies found."),
                    italicized=True,
                )
            )


class IntersightLinkAggregationPolicyReportSection(UcsReportSection):
    def __init__(self, order_id, parent, link_aggregation_policy, name="", title=""):
        if not title:
            title = _("Link Aggregation Policy " + str(name))
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightLinkAggregationPolicyReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                link_aggregation_policy=link_aggregation_policy,
                name=name,
                centered=True,
            )
        )


class IntersightLinkAggregationPolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, link_aggregation_policy, name="", centered=False):
        rows = [
            [_("Description"), _("Value")],
            [_("Name"), name],
            [_("Description"), link_aggregation_policy.descr],
            [_("Suspend Individual"), link_aggregation_policy.suspend_individual],
            [_("LACP Rate"), link_aggregation_policy.lacp_rate],
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[0]),
            centered=centered,
            cells_list=rows,
        )


class IntersightLinkControlPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Link Control Policies")

        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config
        descr = _("The following Link Control Policies define UDLD configurations for Fabric Interconnects.")
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self, string=descr))

        link_control_policies_list = []
        for org in config.orgs:
            self.parse_org(org, link_control_policies_list, element_to_parse="link_control_policies")

        if link_control_policies_list:
            for link_control_policy in link_control_policies_list:
                self.content_list.append(
                    IntersightLinkControlPolicyReportSection(
                        self.report.get_current_order_id(),
                        parent=self,
                        link_control_policy=link_control_policy,
                        name=link_control_policy.name,
                    )
                )
        else:
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=_("No Link Control Policies found."),
                    italicized=True,
                )
            )


class IntersightLinkControlPolicyReportSection(UcsReportSection):
    def __init__(self, order_id, parent, link_control_policy, name="", title=""):
        if not title:
            title = _("Link Control Policy " + str(name))
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightLinkControlPolicyReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                link_control_policy=link_control_policy,
                name=name,
                centered=True,
            )
        )


class IntersightLinkControlPolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, link_control_policy, name="", centered=False):
        rows = [
            [_("Description"), _("Value")],
            [_("Name"), name],
            [_("Description"), link_control_policy.descr],
            [_("Admin State"), link_control_policy.admin_state],
            [_("Mode"), link_control_policy.mode],
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[0]),
            centered=centered,
            cells_list=rows,
        )


class IntersightMacsecPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("MACsec Policies")

        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config
        descr = _("The following MACsec Policies define MACsec configurations for Fabric Interconnects.")
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self, string=descr))

        macsec_policies_list = []
        for org in config.orgs:
            self.parse_org(org, macsec_policies_list, element_to_parse="macsec_policies")

        if macsec_policies_list:
            for macsec_policy in macsec_policies_list:
                self.content_list.append(
                    IntersightMacsecPolicyReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        macsec_policy=macsec_policy,
                        name=macsec_policy.name,
                    )
                )
        else:
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=_("No MACsec Policies found."),
                    italicized=True,
                )
            )


class IntersightMacsecPolicyReportSection(UcsReportSection):
    def __init__(self, order_id, parent, macsec_policy, name="", title=""):
        if not title:
            title = _("MACsec Policy " + str(name))
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightMacsecPolicyReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                macsec_policy=macsec_policy,
                name=name,
                centered=True,
            )
        )
        if macsec_policy.eapol_configurations:
            self.content_list.append(
                IntersightMacsecPolicyEapolReportSection(
                    self.report.get_current_order_id(),
                    parent=self,
                    eapol_configuration=macsec_policy.eapol_configurations,
                    name=name,
                )
            )
        if macsec_policy.primary_keychain:
            self.content_list.append(
                IntersightMacsecPolicyKeyChainReportSection(
                    self.report.get_current_order_id(),
                    parent=self,
                    keychain=macsec_policy.primary_keychain,
                    keychain_type="Primary",
                    keychain_name=macsec_policy.primary_keychain["keychain_name"],
                    name=name,
                )
            )
        if macsec_policy.fallback_keychain:
            self.content_list.append(
                IntersightMacsecPolicyKeyChainReportSection(
                    self.report.get_current_order_id(),
                    parent=self,
                    keychain=macsec_policy.fallback_keychain,
                    keychain_type="Fallback",
                    keychain_name=macsec_policy.fallback_keychain["keychain_name"],
                    name=name,
                )
            )


class IntersightMacsecPolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, macsec_policy, name="", centered=False):
        rows = [
            [_("Description"), _("Value")],
            [_("Name"), name],
            [_("Description"), macsec_policy.descr],
            [_("Cipher Suite"), macsec_policy.cipher_suite],
            [_("Confidentiality Offset"), macsec_policy.confidentiality_offset],
            [_("Include ICV Indicator"), macsec_policy.include_icv_indicator],
            [_("Key Server Priority"), macsec_policy.key_server_priority],
            [_("Replay Window Size"), macsec_policy.replay_window_size],
            [_("SAK Expiry Time"), macsec_policy.sak_expiry_time],
            [_("Security Policy"), macsec_policy.security_policy],
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[0]),
            centered=centered,
            cells_list=rows,
        )


class IntersightMacsecPolicyEapolReportSection(UcsReportSection):
    def __init__(self, order_id, parent, eapol_configuration, name="", title=""):
        if not title:
            title = _("MACsec Policy '" + str(name) + "' EAPOL Configurations")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightMacsecPolicyEapolReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                eapol_configuration=eapol_configuration,
                centered=True,
            )
        )


class IntersightMacsecPolicyEapolReportTable(UcsReportTable):
    def __init__(self, order_id, parent, eapol_configuration, centered=False):
        rows = [
            [_("Description"), _("Value")],
            [_("Ether Type"), eapol_configuration.get("ether_type")],
            [_("MAC Address"), eapol_configuration.get("mac_address")],
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[0]),
            centered=centered,
            cells_list=rows,
        )


class IntersightMacsecPolicyKeyChainReportSection(UcsReportSection):
    def __init__(self, order_id, parent, keychain, keychain_name, keychain_type, name="", title=""):
        if not title:
            title = _("MACsec Policy " + keychain_type + " Keychain '" + keychain_name + "' Keys")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if keychain.get("keys"):
            for key in keychain["keys"]:
                self.content_list.append(
                    IntersightMacsecPolicyKeyReportTable(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        macsec_key=key,
                        centered=True,
                    )
                )
                if key.get("lifetime"):
                    self.content_list.append(
                        IntersightMacsecPolicyKeyLifetimeReportSection(
                            self.report.get_current_order_id(),
                            parent=self,
                            lifetime=key["lifetime"],
                            key_id=key["id"],
                        )
                    )


class IntersightMacsecPolicyKeyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, macsec_key, centered=False):
        rows = [
            [_("Description"), _("Value")],
            [_("Id"), macsec_key.get("id")],
            [_("Cryptographic Algorithm"), macsec_key.get("cryptographic_algorithm")],
            [_("Key Type"), macsec_key.get("key_type")],
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[0]),
            centered=centered,
            cells_list=rows,
        )


class IntersightMacsecPolicyKeyLifetimeReportSection(UcsReportSection):
    def __init__(self, order_id, parent, lifetime, key_id="", title=""):
        if not title:
            title = _("MACsec Key '" + key_id + "' Lifetime")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightMacsecPolicyKeyLifetimeReportTable(
                self.report.get_current_order_id(),
                parent=self,
                lifetime=lifetime,
            )
        )


class IntersightMacsecPolicyKeyLifetimeReportTable(UcsReportTable):
    def __init__(self, order_id, parent, lifetime, centered=False):
        rows = [
            [_("Description"), _("Value")],
            [_("Start Time"), lifetime.get("start_time")],
            [_("Always Active"), lifetime.get("always_active")],
            [_("Timezone"), lifetime.get("timezone")],
            [_("Infinite Lifetime"), lifetime.get("infinite_lifetime")],
            [_("End Time"), lifetime.get("end_time")],
            [_("Duration"), lifetime.get("duration")],
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[0]),
            centered=centered,
            cells_list=rows,
        )


class IntersightNetflowConfigurationPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("NetFlow Configuration Policies")

        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config
        descr = _("The following NetFlow Configuration Policies define NetFlow configurations for Fabric Interconnects.")
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self, string=descr))

        netflow_policies_list = []
        for org in config.orgs:
            self.parse_org(org, netflow_policies_list, element_to_parse="netflow_configuration_policies")

        if netflow_policies_list:
            for netflow_policy in netflow_policies_list:
                self.content_list.append(
                    IntersightNetflowConfigurationPolicyReportSection(
                        self.report.get_current_order_id(),
                        parent=self,
                        netflow_policy=netflow_policy,
                        name=netflow_policy.name,
                    )
                )
        else:
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=_("No NetFlow Configuration Policies found."),
                    italicized=True,
                )
            )


class IntersightNetflowConfigurationPolicyReportSection(UcsReportSection):
    def __init__(self, order_id, parent, netflow_policy, name="", title=""):
        if not title:
            title = _("NetFlow Configuration Policy " + str(name))
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        if netflow_policy.flow_definitions:
            self.content_list.append(
                IntersightNetflowFlowDefinitionsReportSection(
                    self.report.get_current_order_id(), parent=self,
                    flow_definitions=netflow_policy.flow_definitions, name=name,
                )
            )
        if netflow_policy.flow_exporters:
            self.content_list.append(
                IntersightNetflowFlowExportersReportSection(
                    self.report.get_current_order_id(), parent=self,
                    flow_exporters=netflow_policy.flow_exporters, name=name,
                )
            )
        if netflow_policy.flow_monitors:
            self.content_list.append(
                IntersightNetflowFlowMonitorsReportSection(
                    self.report.get_current_order_id(), parent=self,
                    flow_monitors=netflow_policy.flow_monitors, name=name,
                )
            )


class IntersightNetflowFlowDefinitionsReportSection(UcsReportSection):
    def __init__(self, order_id, parent, flow_definitions, name="", title=""):
        if not title:
            title = _("NetFlow Policy '" + str(name) + "' Flow Definitions")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        for flow_def in flow_definitions:
            self.content_list.append(
                IntersightNetflowFlowDefinitionReportTable(
                    order_id=self.report.get_current_order_id(), parent=self,
                    flow_def=flow_def, centered=True,
                )
            )


class IntersightNetflowFlowDefinitionReportTable(UcsReportTable):
    def __init__(self, order_id, parent, flow_def, centered=False):
        keys_str = ", ".join(flow_def.get("keys", [])) if flow_def.get("keys") else None
        non_keys_str = ", ".join(flow_def.get("non_keys", [])) if flow_def.get("non_keys") else None

        rows = [
            [_("Description"), _("Value")],
            [_("Name"), flow_def.get("name")],
            [_("Record Type"), flow_def.get("record_type")],
            [_("Keys"), keys_str],
            [_("Non-Keys"), non_keys_str],
        ]

        UcsReportTable.__init__(self, order_id=order_id, parent=parent,
                                row_number=len(rows), column_number=len(rows[0]),
                                centered=centered, cells_list=rows)


class IntersightNetflowFlowExportersReportSection(UcsReportSection):
    def __init__(self, order_id, parent, flow_exporters, name="", title=""):
        if not title:
            title = _("NetFlow Policy '" + str(name) + "' Flow Exporters")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        for exporter in flow_exporters:
            self.content_list.append(
                IntersightNetflowFlowExporterReportTable(
                    order_id=self.report.get_current_order_id(), parent=self,
                    exporter=exporter, centered=True,
                )
            )


class IntersightNetflowFlowExporterReportTable(UcsReportTable):
    def __init__(self, order_id, parent, exporter, centered=False):
        fc = exporter.get("flow_collector") or {}
        timeouts = exporter.get("timeouts") or {}
        ei = exporter.get("exporter_interfaces") or {}

        rows = [
            [_("Description"), _("Value")],
            [_("Name"), exporter.get("name")],
            [_("Destination IP Address"), fc.get("destination_ip_address")],
            [_("UDP Port"), str(fc.get("udp_port")) if fc.get("udp_port") is not None else None],
            [_("Gateway IP Address"), fc.get("gateway_ip_address")],
            [_("DSCP"), str(fc.get("dscp")) if fc.get("dscp") is not None else None],
            [_("Template Data Timeout"), str(timeouts.get("template_data_timeout")) if timeouts.get("template_data_timeout") is not None else None],
            [_("Option Exporter Stats Timeout"), str(timeouts.get("option_exporter_stats_timeout")) if timeouts.get("option_exporter_stats_timeout") is not None else None],
            [_("Option Interface Table Timeout"), str(timeouts.get("option_interface_table_timeout")) if timeouts.get("option_interface_table_timeout") is not None else None],
            [_("VLAN ID"), str(ei.get("vlan_id")) if ei.get("vlan_id") is not None else None],
            [_("Switch A Source IP"), ei.get("switch_a_ip")],
            [_("Switch A Subnet Mask"), ei.get("switch_a_subnet_mask")],
            [_("Switch B Source IP"), ei.get("switch_b_ip")],
            [_("Switch B Subnet Mask"), ei.get("switch_b_subnet_mask")],
        ]

        UcsReportTable.__init__(self, order_id=order_id, parent=parent,
                                row_number=len(rows), column_number=len(rows[0]),
                                centered=centered, cells_list=rows)


class IntersightNetflowFlowMonitorsReportSection(UcsReportSection):
    def __init__(self, order_id, parent, flow_monitors, name="", title=""):
        if not title:
            title = _("NetFlow Policy '" + str(name) + "' Flow Monitors")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        for monitor in flow_monitors:
            self.content_list.append(
                IntersightNetflowFlowMonitorReportTable(
                    order_id=self.report.get_current_order_id(), parent=self,
                    monitor=monitor, centered=True,
                )
            )


class IntersightNetflowFlowMonitorReportTable(UcsReportTable):
    def __init__(self, order_id, parent, monitor, centered=False):
        exporters_str = ", ".join(monitor.get("flow_exporters", [])) if monitor.get("flow_exporters") else None

        rows = [
            [_("Description"), _("Value")],
            [_("Name"), monitor.get("name")],
            [_("Flow Record"), monitor.get("flow_record")],
            [_("Flow Exporters"), exporters_str],
        ]

        UcsReportTable.__init__(self, order_id=order_id, parent=parent,
                                row_number=len(rows), column_number=len(rows[0]),
                                centered=centered, cells_list=rows)


class IntersightAuditdPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("AuditD Policy")

        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config
        descr = _("The following AuditD Policies define AuditD configurations for Fabric Interconnects.")
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self, string=descr))

        auditd_policies_list = []
        for org in config.orgs:
            self.parse_org(org, auditd_policies_list, element_to_parse="auditd_policies")

        if auditd_policies_list:
            for auditd_policy in auditd_policies_list:
                self.content_list.append(
                    IntersightAuditdPolicyReportSection(
                        self.report.get_current_order_id(), parent=self,
                        auditd_policy=auditd_policy, name=auditd_policy.name,
                    )
                )
        else:
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(), parent=self,
                    string=_("No AuditD Policies found."), italicized=True,
                )
            )


class IntersightAuditdPolicyReportSection(UcsReportSection):
    def __init__(self, order_id, parent, auditd_policy, name="", title=""):
        if not title:
            title = _("AuditD Policy " + str(name))
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightAuditdPolicyReportTable(
                order_id=self.report.get_current_order_id(), parent=self,
                auditd_policy=auditd_policy, name=name, centered=True,
            )
        )


class IntersightAuditdPolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, auditd_policy, name="", centered=False):
        log_monitor = auditd_policy.log_monitor or {}
        enabled_log_monitor = [
            (' '.join(field.split('_'))).title()
            for field in log_monitor
            if log_monitor[field] == "yes"
        ]
        str_log_monitor = ", ".join(enabled_log_monitor)
        rows = [
            [_("Description"), _("Value")],
            [_("Name"), name],
            [_("Description"), auditd_policy.descr],
            [_("Admin State"), auditd_policy.admin_state],
            [_("Minimum Severity to Report"), auditd_policy.minimum_severity_to_report],
            [_("Log Monitor"), str_log_monitor]
        ]

        UcsReportTable.__init__(self, order_id=order_id, parent=parent,
                                row_number=len(rows), column_number=len(rows[0]),
                                centered=centered, cells_list=rows)


class IntersightFabricPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Fabric Policies")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightAuditdPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightEthernetNetworkControlPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightEthernetNetworkGroupPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightFlowControlPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightLdapPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightLinkAggregationPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightLinkControlPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightMacsecPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightMulticastPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightNetflowConfigurationPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightNetworkConnectivityPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightNtpPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightPortPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightPowerGroupsReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightPowerPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightSnmpPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightSwitchControlPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightSyslogPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightSystemQosPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightThermalPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightVlanPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightVsanPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
