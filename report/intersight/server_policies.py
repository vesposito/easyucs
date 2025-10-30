# coding: utf-8
# !/usr/bin/env python

""" policies.py: Easy UCS Deployment Tool """

from common import convert_to_range, read_json_file
from report.content import *
from report.ucs.section import UcsReportSection
from report.ucs.table import UcsReportTable


class IntersightOrganizationsReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title="Organizations"):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        descr = "There is a total of " + str(len(self.report.config.orgs)) + " organizations."
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self, string=descr))

        self.content_list.append(
            IntersightOrganizationsReportTable(
                self.report.get_current_order_id(), parent=self, orgs=self.report.config.orgs))


class IntersightOrganizationsReportTable(UcsReportTable):
    def __init__(self, order_id, parent, orgs, centered=True):
        rows = [["Org Name", "Description", "Shared With Orgs", "Resource Groups"]]

        for org in orgs:
            shared_orgs = None
            if org.shared_with_orgs:
                shared_orgs = ",".join(org.shared_with_orgs)
            resource_groups = None
            if org.resource_groups:
                resource_groups = ",".join(org.resource_groups)
            rows.append([org.name, org.descr, shared_orgs, resource_groups])

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[0]),
            centered=centered,
            cells_list=rows,
        )


class IntersightBiosPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title="BIOS Policies"):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config

        text = "Tokens with 'Platform-Default' values are not displayed below for easier readability."
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self, string=text, italicized=True))

        bios_policies_list = []
        # Searching for all BIOS Policies
        for org in config.orgs:
            self.parse_org(org, bios_policies_list, element_to_parse="bios_policies")

        if bios_policies_list:
            for bios_policy in bios_policies_list:
                self.content_list.append(
                    IntersightBiosPolicyReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        bios_policy=bios_policy,
                        title="BIOS Policy " + bios_policy.name,
                    )
                )
        else:
            text = "No BIOS Policies found."
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=text,
                    italicized=True,
                )
            )


class IntersightBiosPolicyReportSection(UcsReportSection):
    def __init__(self, order_id, parent, bios_policy, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightBiosPolicyReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                centered=True,
                bios_policy=bios_policy,
            )
        )


class IntersightBiosPolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, bios_policy, centered=False):
        rows = [
            ["Description", "Value"],
            ["Name", bios_policy.name],
            ["Description", bios_policy.descr],
            ["Organization", bios_policy._parent.name],
        ]

        bios_table = read_json_file(file_path="config/intersight/bios_table.json", logger=self)
        if not bios_table:
            self.logger(level="error", message="Intersight BIOS Table not imported.")
        if bios_table:
            for attr in sorted(bios_table, key=lambda x: bios_table.keys(), reverse=False):
                if getattr(bios_policy, attr) not in ["platform-default", "Platform Default"]:
                    rows.append([attr, getattr(bios_policy, attr)])

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightBootPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title="Boot Policies"):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config

        boot_policies_list = []
        # Searching for all Boot Policies
        for org in config.orgs:
            self.parse_org(org, boot_policies_list, element_to_parse="boot_policies")

        if boot_policies_list:
            for boot_policy in boot_policies_list:
                self.content_list.append(
                    IntersightBootPolicyReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        boot_policy=boot_policy,
                        title="Boot Policy " + boot_policy.name,
                    )
                )
        else:
            text = "No Boot Policies found."
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=text,
                    italicized=True,
                )
            )


class IntersightBootPolicyReportSection(UcsReportSection):
    def __init__(self, order_id, parent, boot_policy, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightBootPolicyReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                centered=True,
                boot_policy=boot_policy,
            )
        )

        self.content_list.append(
            GenericReportText(
                order_id=self.report.get_current_order_id(),
                parent=self,
                string="\nBoot Devices: ",
                bolded=True,
            )
        )

        if boot_policy.boot_devices:
            self.content_list.append(
                IntersightBootDevicesReportTable(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    centered=True,
                    boot_policy=boot_policy,
                )
            )


class IntersightBootPolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, boot_policy, centered=False):

        rows = [
            ["Description", "Value"],
            ["Name", boot_policy.name],
            ["Description", boot_policy.descr],
            ["Organization", boot_policy._parent.name],
            ["Boot Mode", boot_policy.boot_mode],
            ["Enable Secure Boot", boot_policy.enable_secure_boot],
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightBootDevicesReportTable(UcsReportTable):
    def __init__(self, order_id, parent, boot_policy, centered=False):

        rows = [["Order", "Device Type", "Device Name", "Enabled", "Interface Name", "Interface Source", "IP Type",
                 "LUN", "MAC Address", "Port", "Slot", "Subtype", "Target WWPN", "Boot Loader Name",
                 "Boot Loader Path", "Boot Loader Description"]]

        order = 0
        for boot_item in boot_policy.boot_devices:
            order += 1
            rows.append(
                [
                    order,
                    boot_item["device_type"],
                    boot_item["device_name"],
                    boot_item["enabled"],
                    boot_item["interface_name"],
                    boot_item["interface_source"],
                    boot_item["ip_type"],
                    boot_item["lun"],
                    boot_item["mac_address"],
                    boot_item["port"],
                    boot_item["slot"],
                    boot_item["subtype"],
                    boot_item["target_wwpn"],
                    boot_item["bootloader_name"],
                    boot_item["bootloader_path"],
                    boot_item["bootloader_description"],
                ]
            )

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
            font_size=8,
        )


class IntersightDriveSecurityPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title="Drive Security Policies"):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config

        drive_security_policies_list = []
        # Searching for all Drive Security Policies
        for org in config.orgs:
            self.parse_org(org, drive_security_policies_list, element_to_parse="drive_security_policies")

        if drive_security_policies_list:
            for drive_security_policy in drive_security_policies_list:
                self.content_list.append(
                    IntersightDriveSecurityPolicyReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        drive_security_policy=drive_security_policy,
                        title="Drive Security Policy " + drive_security_policy.name,
                    )
                )
        else:
            text = "No Drive Security Policies found."
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=text,
                    italicized=True,
                )
            )


class IntersightDriveSecurityPolicyReportSection(UcsReportSection):
    def __init__(self, order_id, parent, drive_security_policy, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightDriveSecurityPolicyReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                centered=True,
                drive_security_policy=drive_security_policy,
            )
        )

        if hasattr(drive_security_policy, "primary_kmip_server") and drive_security_policy.primary_kmip_server:
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string="\nPrimary KMIP Server Details: ",
                    bolded=True,
                )
            )

            self.content_list.append(
                IntersightDriveSecurityPolicyKmipServerReportTable(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    centered=True,
                    kmip_server=drive_security_policy.primary_kmip_server,
                )
            )

        if hasattr(drive_security_policy, "secondary_kmip_server") and drive_security_policy.secondary_kmip_server:
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string="\nSecondary KMIP Server Details: ",
                    bolded=True,
                )
            )

            self.content_list.append(
                IntersightDriveSecurityPolicyKmipServerReportTable(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    centered=True,
                    kmip_server=drive_security_policy.secondary_kmip_server,
                )
            )


class IntersightDriveSecurityPolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, drive_security_policy, centered=False):

        rows = [
            ["Description", "Value"],
            ["Name", drive_security_policy.name],
            ["Description", drive_security_policy.descr],
            ["Organization", drive_security_policy._parent.name],
            ["Server Certificate", drive_security_policy.server_public_root_ca_certificate]
        ]

        if hasattr(drive_security_policy, "authentication_credentials") and drive_security_policy.authentication_credentials:
            rows.append(["Username", drive_security_policy.authentication_credentials.get("username", None)])

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightDriveSecurityPolicyKmipServerReportTable(UcsReportTable):
    def __init__(self, order_id, parent, kmip_server, centered=False):

        rows = [
            ["Description", "Value"],
            ["IP Address", kmip_server["ip_address"]],
            ["Port", kmip_server["port"]],
        ]
        if parent.report.device.metadata.device_type in ["ucsc"]:
            rows.append(["Timeout", kmip_server["timeout"]],)

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightEthAdapterPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title="Ethernet Adapter Policies"):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config

        eth_adapter_policies_list = []
        # Searching for all Ethernet Adapter Policies
        for org in config.orgs:
            self.parse_org(org, eth_adapter_policies_list, element_to_parse="ethernet_adapter_policies")

        if eth_adapter_policies_list:
            for eth_adapter_policy in eth_adapter_policies_list:
                self.content_list.append(
                    IntersightEthAdapterPolicyReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        eth_adapter_policy=eth_adapter_policy,
                        title="Ethernet Adapter Policy " + eth_adapter_policy.name,
                    )
                )
        else:
            text = "No Ethernet Adapter Policies found."
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=text,
                    italicized=True,
                )
            )


class IntersightEthAdapterPolicyReportSection(UcsReportSection):
    def __init__(self, order_id, parent, eth_adapter_policy, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightEthAdapterPolicyReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                centered=True,
                eth_adapter_policy=eth_adapter_policy,
            )
        )

        if eth_adapter_policy.roce_settings:
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string="\nRDMA over Converged Ethernet Settings: ",
                    bolded=True,
                )
            )

            self.content_list.append(
                IntersightEthAdapterPolicyRoceReportTable(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    centered=True,
                    eth_adapter_policy=eth_adapter_policy,
                )
            )

        if eth_adapter_policy.interrupt_settings:
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string="\nInterrupt Settings: ",
                    bolded=True,
                )
            )

            self.content_list.append(
                IntersightEthAdapterPolicyInterruptReportTable(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    centered=True,
                    eth_adapter_policy=eth_adapter_policy,
                )
            )

        if eth_adapter_policy.tcp_offload_settings:
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string="\nTCP Offload Settings: ",
                    bolded=True,
                )
            )

            self.content_list.append(
                IntersightEthAdapterPolicyTcpOffloadReportTable(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    centered=True,
                    eth_adapter_policy=eth_adapter_policy,
                )
            )

        if eth_adapter_policy.rss_settings:
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string="\nReceive Side Scaling Settings: ",
                    bolded=True,
                )
            )

            self.content_list.append(
                IntersightEthAdapterPolicyRssReportTable(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    centered=True,
                    eth_adapter_policy=eth_adapter_policy,
                )
            )


class IntersightEthAdapterPolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, eth_adapter_policy, centered=False):

        rows = [
            ["Description", "Value"],
            ["Name", eth_adapter_policy.name],
            ["Description", eth_adapter_policy.descr],
            ["Organization", eth_adapter_policy._parent.name],
            ["Enable VXLAN Offload", eth_adapter_policy.enable_vxlan_offload],
            ["Enable NVGRE Offload", eth_adapter_policy.enable_nvgre_offload],
            ["Enable EtherChannel Pinning", eth_adapter_policy.enable_etherchannel_pinning],
            [
                "Enable Accelerated Receive Flow Steering",
                eth_adapter_policy.enable_accelerated_receive_flow_steering,
            ],
            ["Enable Advanced Filter", eth_adapter_policy.enable_advanced_filter],
            ["Enable Geneve Offload", eth_adapter_policy.enable_geneve_offload],
            ["Enable Interrupt Scaling", eth_adapter_policy.enable_interrupt_scaling],
            ["Receive Queue Count", eth_adapter_policy.receive_queue_count],
            ["Receive Ring Size", eth_adapter_policy.receive_ring_size],
            ["Transmit Queue Count", eth_adapter_policy.transmit_queue_count],
            ["Transmit Ring Size", eth_adapter_policy.transmit_ring_size],
            ["Completion Queue Count", eth_adapter_policy.completion_queue_count],
            ["Completion Ring Size", eth_adapter_policy.completion_ring_size],
            ["Uplink Failback Timeout (seconds)", eth_adapter_policy.uplink_failback_timeout],
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightEthAdapterPolicyRoceReportTable(UcsReportTable):
    def __init__(self, order_id, parent, eth_adapter_policy, centered=False):

        rows = [
            ["Description", "Value"],
            [
                "Enable RDMA over Converged Ethernet",
                eth_adapter_policy.roce_settings["enable_rdma_over_converged_ethernet"],
            ],
            ["Queue Pairs", eth_adapter_policy.roce_settings["queue_pairs"]],
            ["Memory Regions", eth_adapter_policy.roce_settings["memory_regions"]],
            ["Resource Groups", eth_adapter_policy.roce_settings["resource_groups"]],
            ["Version", eth_adapter_policy.roce_settings["version"]],
            ["Class of Service", eth_adapter_policy.roce_settings["class_of_service"]],
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightEthAdapterPolicyInterruptReportTable(UcsReportTable):
    def __init__(self, order_id, parent, eth_adapter_policy, centered=False):

        rows = [
            ["Description", "Value"],
            ["Number of Interrupts", eth_adapter_policy.interrupt_settings["interrupts"]],
            ["Interrupt Mode", eth_adapter_policy.interrupt_settings["interrupt_mode"]],
            ["Interrupt Timer (µs)", eth_adapter_policy.interrupt_settings["interrupt_timer"]],
            ["Interrupt Coalescing Type", eth_adapter_policy.interrupt_settings["interrupt_coalescing_type"]],
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightEthAdapterPolicyTcpOffloadReportTable(UcsReportTable):
    def __init__(self, order_id, parent, eth_adapter_policy, centered=False):

        rows = [
            ["Description", "Value"],
            ["Enable Tx Checksum Offload", eth_adapter_policy.tcp_offload_settings["enable_tx_checksum_offload"]],
            ["Enable Rx Checksum Offload", eth_adapter_policy.tcp_offload_settings["enable_rx_checksum_offload"]],
            ["Enable Large Send Offload", eth_adapter_policy.tcp_offload_settings["enable_large_send_offload"]],
            ["Enable Large Receive Offload", eth_adapter_policy.tcp_offload_settings["enable_large_receive_offload"]],
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightEthAdapterPolicyRssReportTable(UcsReportTable):
    def __init__(self, order_id, parent, eth_adapter_policy, centered=False):

        rows = [
            ["Description", "Value"],
            ["Enable Receive Side Scaling", eth_adapter_policy.rss_settings["enable_receive_side_scaling"]],
            ["Enable IPv4 Hash", eth_adapter_policy.rss_settings["enable_ipv4_hash"]],
            ["Enable IPv6 Hash", eth_adapter_policy.rss_settings["enable_ipv6_hash"]],
            ["Enable IPv6 Extensions Hash", eth_adapter_policy.rss_settings["enable_ipv6_extensions_hash"]],
            ["Enable TCP and IPv4 Hash", eth_adapter_policy.rss_settings["enable_tcp_and_ipv4_hash"]],
            ["Enable TCP and IPv6 Hash", eth_adapter_policy.rss_settings["enable_tcp_and_ipv6_hash"]],
            [
                "Enable TCP and IPv6 Extensions Hash",
                eth_adapter_policy.rss_settings["enable_tcp_and_ipv6_extensions_hash"],
            ],
            ["Enable UDP and IPv4 Hash", eth_adapter_policy.rss_settings["enable_udp_and_ipv4_hash"]],
            ["Enable UDP and IPv6 Hash", eth_adapter_policy.rss_settings["enable_udp_and_ipv6_hash"]],
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightEthNetworkControlPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title="Ethernet Network Control Policies"):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config

        default_ethernet_network_control_policy_name = ""

        ethernet_network_control_policies_list = []
        # Searching for all Ethernet Network Control Policies
        for org in config.orgs:
            self.parse_org(
                org,
                ethernet_network_control_policies_list,
                element_to_parse="ethernet_network_control_policies",
            )

        if ethernet_network_control_policies_list:
            for ethernet_network_control_policy in ethernet_network_control_policies_list:
                # Validating if the Policy belongs to Server vNIC or Appliance Port
                if "_appliance" not in ethernet_network_control_policy.name:
                    if ethernet_network_control_policy.name == default_ethernet_network_control_policy_name:
                        ethernet_network_control_policy_name = ethernet_network_control_policy.name + " (default)"
                    else:
                        ethernet_network_control_policy_name = ethernet_network_control_policy.name
                    self.content_list.append(
                        IntersightEthNetworkControlPolicyReportSection(
                            order_id=self.report.get_current_order_id(),
                            parent=self,
                            ethernet_network_control_policy=ethernet_network_control_policy,
                            name=ethernet_network_control_policy_name,
                            title="Ethernet Network Control Policy " + ethernet_network_control_policy.name,
                        )
                    )
        else:
            text = "No Ethernet Network Control Policies found."
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=text,
                    italicized=True,
                )
            )


class IntersightEthNetworkControlPolicyReportSection(UcsReportSection):
    def __init__(self, order_id, parent, ethernet_network_control_policy, name="", title=""):
        if not title:
            title = "Ethernet Network Control Policy " + str(name)
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightEthNetworkControlPolicyReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                ethernet_network_control_policy=ethernet_network_control_policy,
                name=name,
                centered=True,
            )
        )


class IntersightEthNetworkControlPolicyReportTable(UcsReportTable):
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
            ["Description", "Value"],
            ["Name", name],
            ["Description", ethernet_network_control_policy.descr],
            ["Organization", ethernet_network_control_policy._parent.name],
            ["Enable CDP", ethernet_network_control_policy.cdp_enable],
            ["MAC Register Mode", mac_register_mode],
            ["Action on Uplink Fail", action_on_uplink_fail],
            ["MAC Security - MAC Forging", mac_security_forge],
            ["LLDP Transmit", ethernet_network_control_policy.lldp_transmit_enable],
            ["LLDP Receive", ethernet_network_control_policy.lldp_receive_enable],
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


class IntersightEthNetworkGroupPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title="Ethernet Network Group Policies"):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config

        eth_network_group_policies_list = []
        # Searching for all Ethernet Network Group Policies
        for org in config.orgs:
            self.parse_org(org, eth_network_group_policies_list, element_to_parse="ethernet_network_group_policies")

        if eth_network_group_policies_list:
            for ethernet_network_group_policy in eth_network_group_policies_list:
                self.content_list.append(
                    IntersightEthNetworkGroupPolicyReportSection(
                        self.report.get_current_order_id(),
                        parent=self,
                        ethernet_network_group_policy=ethernet_network_group_policy,
                        name=ethernet_network_group_policy.name,
                    )
                )


class IntersightEthNetworkGroupPolicyReportSection(UcsReportSection):
    def __init__(self, order_id, parent, ethernet_network_group_policy, name="", title=""):
        if not title:
            title = "Ethernet Network Group Policy " + str(name)
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightEthNetworkGroupPolicyReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                ethernet_network_group_policy=ethernet_network_group_policy,
                name=name,
                centered=True,
            )
        )


class IntersightEthNetworkGroupPolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, ethernet_network_group_policy, name="", centered=False):
        rows = [
            ["Description", "Value"],
            ["Name", name],
            ["Description", ethernet_network_group_policy.descr],
            ["Organization", ethernet_network_group_policy._parent.name],
            ["Allowed VLAN IDs", convert_to_range(ethernet_network_group_policy.allowed_vlans)],
            ["Native VLAN ID", ethernet_network_group_policy.native_vlan],
            ["QinQ VLAN ID", ethernet_network_group_policy.q_in_q_vlan],
            ["Enable QinQ Tunneling", ethernet_network_group_policy.enable_q_in_q_tunneling],
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


class IntersightEthQosPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title="Ethernet QoS Policies"):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config

        eth_qos_policies_list = []
        # Searching for all Ethernet QoS Policies
        for org in config.orgs:
            self.parse_org(org, eth_qos_policies_list, element_to_parse="ethernet_qos_policies")

        if eth_qos_policies_list:
            for eth_qos_policy in eth_qos_policies_list:
                self.content_list.append(
                    IntersightEthQosPolicyReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        eth_qos_policy=eth_qos_policy,
                        title="Ethernet QoS Policy " + eth_qos_policy.name,
                    )
                )
        else:
            text = "No Ethernet QoS Policies found."
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=text,
                    italicized=True,
                )
            )


class IntersightEthQosPolicyReportSection(UcsReportSection):
    def __init__(self, order_id, parent, eth_qos_policy, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightEthQosPolicyReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                centered=True,
                eth_qos_policy=eth_qos_policy,
            )
        )


class IntersightEthQosPolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, eth_qos_policy, centered=False):

        rows = [
            ["Description", "Value"],
            ["Name", eth_qos_policy.name],
            ["Description", eth_qos_policy.descr],
            ["Organization", eth_qos_policy._parent.name],
            ["MTU (Bytes)", eth_qos_policy.mtu],
            ["Rate Limit (Mbps)", eth_qos_policy.rate_limit],
            ["Burst", eth_qos_policy.burst],
            ["Priority", eth_qos_policy.priority],
            ["Enable Trust Host CoS", eth_qos_policy.enable_trust_host_cos],
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightFcAdapterPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title="Fibre Channel Adapter Policies"):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config

        fc_adapter_policies_list = []
        # Searching for all Fibre Channel Adapter Policies
        for org in config.orgs:
            self.parse_org(org, fc_adapter_policies_list, element_to_parse="fibre_channel_adapter_policies")

        if fc_adapter_policies_list:
            for fc_adapter_policy in fc_adapter_policies_list:
                self.content_list.append(
                    IntersightFcAdapterPolicyReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        fc_adapter_policy=fc_adapter_policy,
                        title="Fibre Channel Adapter Policy " + fc_adapter_policy.name,
                    )
                )
        else:
            text = "No Fibre Channel Adapter Policies found."
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=text,
                    italicized=True,
                )
            )


class IntersightFcAdapterPolicyReportSection(UcsReportSection):
    def __init__(self, order_id, parent, fc_adapter_policy, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightFcAdapterPolicyReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                centered=True,
                fc_adapter_policy=fc_adapter_policy,
            )
        )

        if fc_adapter_policy.error_recovery_settings:
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string="\nError Recovery Settings: ",
                    bolded=True,
                )
            )

            self.content_list.append(
                IntersightFcAdapterPolicyErrRecoveryReportTable(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    centered=True,
                    fc_adapter_policy=fc_adapter_policy,
                )
            )

        if fc_adapter_policy.interrupt_settings:
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string="\nInterrupt Settings: ",
                    bolded=True,
                )
            )

            self.content_list.append(
                IntersightFcAdapterPolicyInterruptReportTable(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    centered=True,
                    fc_adapter_policy=fc_adapter_policy,
                )
            )


class IntersightFcAdapterPolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, fc_adapter_policy, centered=False):

        rows = [
            ["Description", "Value"],
            ["Name", fc_adapter_policy.name],
            ["Description", fc_adapter_policy.descr],
            ["Organization", fc_adapter_policy._parent.name],
            ["Error Detection Timeout", fc_adapter_policy.error_detection_timeout],
            ["Resource Allocation Timeout", fc_adapter_policy.resource_allocation_timeout],
            ["Flogi Retries", fc_adapter_policy.flogi_retries],
            ["Flogi Timeout (ms)", fc_adapter_policy.flogi_timeout],
            ["Plogi Retries", fc_adapter_policy.plogi_retries],
            ["Plogi Timeout (ms)", fc_adapter_policy.plogi_timeout],
            ["I/O Throttle Count", fc_adapter_policy.io_throttle_count],
            ["Maximum LUNs per Target", fc_adapter_policy.max_luns_per_target],
            ["LUN Queue Depth", fc_adapter_policy.lun_queue_depth],
            ["Receive Ring Size", fc_adapter_policy.receive_ring_size],
            ["Transmit Ring Size", fc_adapter_policy.transmit_ring_size],
            ["SCSI I/O Queues", fc_adapter_policy.scsi_io_queue_count],
            ["SCSI I/O Ring Size", fc_adapter_policy.scsi_io_ring_size],
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightFcAdapterPolicyErrRecoveryReportTable(UcsReportTable):
    def __init__(self, order_id, parent, fc_adapter_policy, centered=False):

        rows = [
            ["Description", "Value"],
            ["Enable FCP Error Recovery", fc_adapter_policy.error_recovery_settings["enable_fcp_error_recovery"]],
            ["Port Down Timeout (ms)", fc_adapter_policy.error_recovery_settings["port_down_timeout"]],
            ["Link Down Timeout (ms)", fc_adapter_policy.error_recovery_settings["link_down_timeout"]],
            ["I/O Retry Timeout (s)", fc_adapter_policy.error_recovery_settings["io_retry_timeout"]],
            ["Port Down I/O Retry (ms)", fc_adapter_policy.error_recovery_settings["port_down_io_retry"]],
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightFcAdapterPolicyInterruptReportTable(UcsReportTable):
    def __init__(self, order_id, parent, fc_adapter_policy, centered=False):

        rows = [
            ["Description", "Value"],
            ["Interrupt Mode", fc_adapter_policy.interrupt_settings["interrupt_mode"]],
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightFcNetworkPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title="Fibre Channel Network Policies"):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config

        fc_network_policies_list = []
        # Searching for all Fibre Channel Network Policies
        for org in config.orgs:
            self.parse_org(org, fc_network_policies_list, element_to_parse="fibre_channel_network_policies")

        if fc_network_policies_list:
            for fc_network_policy in fc_network_policies_list:
                self.content_list.append(
                    IntersightFcNetworkPolicyReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        fc_network_policy=fc_network_policy,
                        title="Fibre Channel Network Policy " + fc_network_policy.name,
                    )
                )
        else:
            text = "No Fibre Channel Network Policies found."
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=text,
                    italicized=True,
                )
            )


class IntersightFcNetworkPolicyReportSection(UcsReportSection):
    def __init__(self, order_id, parent, fc_network_policy, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightFcNetworkPolicyReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                centered=True,
                fc_network_policy=fc_network_policy,
            )
        )


class IntersightFcNetworkPolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, fc_network_policy, centered=False):

        rows = [
            ["Description", "Value"],
            ["Name", fc_network_policy.name],
            ["Description", fc_network_policy.descr],
            ["Organization", fc_network_policy._parent.name],
            ["Default VLAN", fc_network_policy.default_vlan],
            ["VSAN ID", fc_network_policy.vsan_id],
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightFcQosPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title="Fibre Channel QoS Policies"):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config

        fc_qos_policies_list = []
        # Searching for all Fibre Channel QoS Policies
        for org in config.orgs:
            self.parse_org(org, fc_qos_policies_list, element_to_parse="fibre_channel_qos_policies")

        if fc_qos_policies_list:
            for fc_qos_policy in fc_qos_policies_list:
                self.content_list.append(
                    IntersightFcQosPolicyReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        fc_qos_policy=fc_qos_policy,
                        title="Fibre Channel QoS Policy " + fc_qos_policy.name,
                    )
                )
        else:
            text = "No Fibre Channel QoS Policies found."
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=text,
                    italicized=True,
                )
            )


class IntersightFcQosPolicyReportSection(UcsReportSection):
    def __init__(self, order_id, parent, fc_qos_policy, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightFcQosPolicyReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                centered=True,
                fc_qos_policy=fc_qos_policy,
            )
        )


class IntersightFcQosPolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, fc_qos_policy, centered=False):

        rows = [
            ["Description", "Value"],
            ["Name", fc_qos_policy.name],
            ["Description", fc_qos_policy.descr],
            ["Organization", fc_qos_policy._parent.name],
            ["Rate Limit (Mbps)", fc_qos_policy.rate_limit],
            ["Maximum Data Field Size (Bytes)", fc_qos_policy.max_data_field_size],
            ["Burst", fc_qos_policy.burst],
            ["Priority", "Fc"],
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightFcZonePoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title="FC Zone Policies"):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config

        fc_zone_policies_list = []
        # Searching for all FC Zone Policies
        for org in config.orgs:
            self.parse_org(org, fc_zone_policies_list, element_to_parse="fc_zone_policies")

        if fc_zone_policies_list:
            for fc_zone_policy in fc_zone_policies_list:
                self.content_list.append(
                    IntersightFcZonePolicyReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        fc_zone_policy=fc_zone_policy,
                        title="FC Zone Policy " + fc_zone_policy.name,
                    )
                )
        else:
            text = "No FC Zone Policies found."
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=text,
                    italicized=True,
                )
            )


class IntersightFcZonePolicyReportSection(UcsReportSection):
    def __init__(self, order_id, parent, fc_zone_policy, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightFcZonePolicyReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                centered=True,
                fc_zone_policy=fc_zone_policy,
            )
        )

        if hasattr(fc_zone_policy, "fc_zone_targets") and fc_zone_policy.fc_zone_targets:
            for fc_zone_target in fc_zone_policy.fc_zone_targets:
                self.content_list.append(
                    GenericReportText(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        string="\nFC Zone Target Details: " + str(fc_zone_target["name"]),
                        bolded=True,
                    )
                )

                self.content_list.append(
                    IntersightFcZonePolicyTargetsReportTable(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        centered=True,
                        fc_zone_target=fc_zone_target,
                    )
                )


class IntersightFcZonePolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, fc_zone_policy, centered=False):

        rows = [
            ["Description", "Value"],
            ["Name", fc_zone_policy.name],
            ["Description", fc_zone_policy.descr],
            ["Organization", fc_zone_policy._parent.name],
            ["FC Target Zoning Type", fc_zone_policy.fc_target_zoning_type],
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightFcZonePolicyTargetsReportTable(UcsReportTable):
    def __init__(self, order_id, parent, fc_zone_target, centered=False):

        rows = [["Description", "Value"]]

        if fc_zone_target.get("name"):
            rows.append(["Name", fc_zone_target["name"]])
        if fc_zone_target.get("switch_id"):
            rows.append(["Switch ID", fc_zone_target["switch_id"]])
        if fc_zone_target.get("vsan_id"):
            rows.append(["VSAN ID", fc_zone_target["vsan_id"]])
        if fc_zone_target.get("wwpn"):
            rows.append(["WWPN", fc_zone_target["wwpn"]])

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightImcAccessPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title="IMC Access Policies"):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config

        imc_access_policies_list = []
        # Searching for all IMC Access Policies
        for org in config.orgs:
            self.parse_org(org, imc_access_policies_list, element_to_parse="imc_access_policies")

        if imc_access_policies_list:
            for imc_access_policy in imc_access_policies_list:
                self.content_list.append(
                    IntersightImcAccessPolicyReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        imc_access_policy=imc_access_policy,
                        title="IMC Access Policy " + imc_access_policy.name,
                    )
                )
        else:
            text = "No IMC Access Policies found."
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=text,
                    italicized=True,
                )
            )


class IntersightImcAccessPolicyReportSection(UcsReportSection):
    def __init__(self, order_id, parent, imc_access_policy, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightImcAccessPolicyReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                centered=True,
                imc_access_policy=imc_access_policy,
            )
        )


class IntersightImcAccessPolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, imc_access_policy, centered=False):

        rows = [
            ["Description", "Value"],
            ["Name", imc_access_policy.name],
            ["Description", imc_access_policy.descr],
            ["Organization", imc_access_policy._parent.name],
            ["Inband Configuration", imc_access_policy.inband_configuration],
            ["Inband IP Pool", imc_access_policy.inband_ip_pool],
            ["Inband VLAN ID", imc_access_policy.inband_vlan_id],
            ["Enable IPv4 Address Configuration", imc_access_policy.ipv4_address_configuration],
            ["Enable IPv6 Address Configuration", imc_access_policy.ipv6_address_configuration],
            ["Out of Band Configuration", imc_access_policy.out_of_band_configuration],
            ["Out of Band IP Pool", imc_access_policy.out_of_band_ip_pool]
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightIpmiOverLanPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title="IPMI over LAN Policies"):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config

        ipmi_over_lan_policies_list = []
        # Searching for all IPMI Over LAN Policies
        for org in config.orgs:
            self.parse_org(org, ipmi_over_lan_policies_list, element_to_parse="ipmi_over_lan_policies")

        if ipmi_over_lan_policies_list:
            for ipmi_over_lan_policy in ipmi_over_lan_policies_list:
                self.content_list.append(
                    IntersightIpmiOverLanPolicyReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        ipmi_over_lan_policy=ipmi_over_lan_policy,
                        title="IPMI Over LAN Policy " + ipmi_over_lan_policy.name,
                    )
                )
        else:
            text = "No IPMI Over LAN Policies found."
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=text,
                    italicized=True,
                )
            )


class IntersightIpmiOverLanPolicyReportSection(UcsReportSection):
    def __init__(self, order_id, parent, ipmi_over_lan_policy, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightIpmiOverLanPolicyReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                centered=True,
                ipmi_over_lan_policy=ipmi_over_lan_policy,
            )
        )


class IntersightIpmiOverLanPolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, ipmi_over_lan_policy, centered=False):

        rows = [
            ["Description", "Value"],
            ["Name", ipmi_over_lan_policy.name],
            ["Description", ipmi_over_lan_policy.descr],
            ["Organization", ipmi_over_lan_policy._parent.name],
            ["Enable IPMI Over LAN Policy", ipmi_over_lan_policy.enabled],
            ["Privilege Level", ipmi_over_lan_policy.privilege_level],
            ["Encryption Key", ipmi_over_lan_policy.encryption_key],
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightIscsiAdapterPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title="iSCSI Adapter Policies"):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config

        iscsi_adapter_policies_list = []
        # Searching for all iSCSI Adapter Policies
        for org in config.orgs:
            self.parse_org(org, iscsi_adapter_policies_list, element_to_parse="iscsi_adapter_policies")

        if iscsi_adapter_policies_list:
            for iscsi_adapter_policy in iscsi_adapter_policies_list:
                self.content_list.append(
                    IntersightIscsiAdapterPolicyReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        iscsi_adapter_policy=iscsi_adapter_policy,
                        title="iSCSI Adapter Policy " + iscsi_adapter_policy.name,
                    )
                )
        else:
            text = "No iSCSI Adapter Policies found."
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=text,
                    italicized=True,
                )
            )


class IntersightIscsiAdapterPolicyReportSection(UcsReportSection):
    def __init__(self, order_id, parent, iscsi_adapter_policy, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightIscsiAdapterPolicyReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                centered=True,
                iscsi_adapter_policy=iscsi_adapter_policy,
            )
        )


class IntersightIscsiAdapterPolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, iscsi_adapter_policy, centered=False):

        rows = [
            ["Description", "Value"],
            ["Name", iscsi_adapter_policy.name],
            ["Description", iscsi_adapter_policy.descr],
            ["Organization", iscsi_adapter_policy._parent.name],
            ["TCP Connection Timeout", iscsi_adapter_policy.tcp_connection_timeout],
            ["DHCP Timeout", iscsi_adapter_policy.dhcp_timeout],
            ["LUN Busy Retry Count", iscsi_adapter_policy.lun_busy_retry_count],
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightIscsiBootPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title="iSCSI Boot Policies"):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config

        iscsi_boot_policies_list = []
        # Searching for all iSCSI Boot Policies
        for org in config.orgs:
            self.parse_org(org, iscsi_boot_policies_list, element_to_parse="iscsi_boot_policies")

        if iscsi_boot_policies_list:
            for iscsi_boot_policy in iscsi_boot_policies_list:
                self.content_list.append(
                    IntersightIscsiBootPolicyReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        iscsi_boot_policy=iscsi_boot_policy,
                        title="iSCSI Boot Policy " + iscsi_boot_policy.name,
                    )
                )
        else:
            text = "No iSCSI Boot Policies found."
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=text,
                    italicized=True,
                )
            )


class IntersightIscsiBootPolicyReportSection(UcsReportSection):
    def __init__(self, order_id, parent, iscsi_boot_policy, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightIscsiBootPolicyReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                centered=True,
                iscsi_boot_policy=iscsi_boot_policy,
            )
        )

        if hasattr(iscsi_boot_policy, "chap") and iscsi_boot_policy.chap:
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string="\nCHAP Authentication Details: ",
                    bolded=True,
                )
            )

            self.content_list.append(
                IntersightIscsiBootPolicyChapReportTable(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    centered=True,
                    iscsi_boot_policy=iscsi_boot_policy,
                )
            )

        if hasattr(iscsi_boot_policy, "mutual_chap") and iscsi_boot_policy.mutual_chap:
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string="\nMutual CHAP Authentication Details: ",
                    bolded=True,
                )
            )

            self.content_list.append(
                IntersightIscsiBootPolicyMutualChapReportTable(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    centered=True,
                    iscsi_boot_policy=iscsi_boot_policy,
                )
            )


class IntersightIscsiBootPolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, iscsi_boot_policy, centered=False):

        rows = [
            ["Description", "Value"],
            ["Name", iscsi_boot_policy.name],
            ["Description", iscsi_boot_policy.descr],
            ["Organization", iscsi_boot_policy._parent.name],
            ["Target Source Type", iscsi_boot_policy.target_source_type],
        ]

        if hasattr(iscsi_boot_policy, "dhcp_vendor_id_iqn"):
            rows.append(["DHCP Vendor ID/IQN", iscsi_boot_policy.dhcp_vendor_id_iqn])
        if hasattr(iscsi_boot_policy, "iscsi_adapter_policy"):
            rows.append(["iSCSI Adapter Policy", iscsi_boot_policy.iscsi_adapter_policy])
        if hasattr(iscsi_boot_policy, "primary_target_policy"):
            rows.append(["Primary Target Policy", iscsi_boot_policy.primary_target_policy])
        if hasattr(iscsi_boot_policy, "secondary_target_policy"):
            rows.append(["Secondary Target Policy", iscsi_boot_policy.secondary_target_policy])
        if hasattr(iscsi_boot_policy, "initiator_ip_source"):
            rows.append(["Initiator IP Source", iscsi_boot_policy.initiator_ip_source])
        if hasattr(iscsi_boot_policy, "ip_pool"):
            rows.append(["IP Pool", iscsi_boot_policy.ip_pool])
        if hasattr(iscsi_boot_policy, "ipv4_address") and getattr(iscsi_boot_policy, "ipv4_address", None):
            rows.append(["IPv4 Address", iscsi_boot_policy.ipv4_address])
            if (
                getattr(iscsi_boot_policy, "initiator_static_ip_v4_config", None)
                and iscsi_boot_policy.initiator_static_ip_v4_config.get("default_gateway")
            ):
                rows.append(["Default Gateway", iscsi_boot_policy.initiator_static_ip_v4_config["default_gateway"]])
            if (
                getattr(iscsi_boot_policy, "initiator_static_ip_v4_config", None)
                and iscsi_boot_policy.initiator_static_ip_v4_config.get("subnet_mask")
            ):
                rows.append(["Subnet Mask", iscsi_boot_policy.initiator_static_ip_v4_config["subnet_mask"]])
            if (
                getattr(iscsi_boot_policy, "initiator_static_ip_v4_config", None)
                and iscsi_boot_policy.initiator_static_ip_v4_config.get("primary_dns")
            ):
                rows.append(["Primary DNS", iscsi_boot_policy.initiator_static_ip_v4_config["primary_dns"]])
            if (
                getattr(iscsi_boot_policy, "initiator_static_ip_v4_config", None)
                and iscsi_boot_policy.initiator_static_ip_v4_config.get("secondary_dns")
            ):
                rows.append(["Secondary DNS", iscsi_boot_policy.initiator_static_ip_v4_config["secondary_dns"]])
        elif hasattr(iscsi_boot_policy, "ipv6_address") and getattr(iscsi_boot_policy, "ipv6_address", None):
            rows.append(["IPv6 Address", iscsi_boot_policy.ipv6_address])
            if (
                getattr(iscsi_boot_policy, "initiator_static_ip_v6_config", None)
                and iscsi_boot_policy.initiator_static_ip_v6_config.get("default_gateway")
            ):
                rows.append(["Default Gateway", iscsi_boot_policy.initiator_static_ip_v6_config["default_gateway"]])
            if (
                getattr(iscsi_boot_policy, "initiator_static_ip_v6_config", None)
                and iscsi_boot_policy.initiator_static_ip_v6_config.get("prefix")
            ):
                rows.append(["Prefix", iscsi_boot_policy.initiator_static_ip_v6_config["prefix"]])
            if (
                getattr(iscsi_boot_policy, "initiator_static_ip_v6_config", None)
                and iscsi_boot_policy.initiator_static_ip_v6_config.get("primary_dns")
            ):
                rows.append(["Primary DNS", iscsi_boot_policy.initiator_static_ip_v6_config["primary_dns"]])
            if (
                getattr(iscsi_boot_policy, "initiator_static_ip_v6_config", None)
                and iscsi_boot_policy.initiator_static_ip_v6_config.get("secondary_dns")
            ):
                rows.append(["Secondary DNS", iscsi_boot_policy.initiator_static_ip_v6_config["secondary_dns"]])

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightIscsiBootPolicyChapReportTable(UcsReportTable):
    def __init__(self, order_id, parent, iscsi_boot_policy, centered=False):

        rows = [
            ["Description", "Value"],
            ["User Name", iscsi_boot_policy.chap["user_id"]]
        ]
        if iscsi_boot_policy.chap.get("password"):
            rows.append(["Password", "<<Set>>"])

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightIscsiBootPolicyMutualChapReportTable(UcsReportTable):
    def __init__(self, order_id, parent, iscsi_boot_policy, centered=False):

        rows = [
            ["Description", "Value"],
            ["User Name", iscsi_boot_policy.mutual_chap["user_id"]]
        ]
        if iscsi_boot_policy.mutual_chap.get("password"):
            rows.append(["Password", "<<Set>>"])

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightIscsiStaticTargetPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title="iSCSI Static Target Policies"):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config

        iscsi_static_target_policies_list = []
        # Searching for all iSCSI Static Target Policies
        for org in config.orgs:
            self.parse_org(org, iscsi_static_target_policies_list, element_to_parse="iscsi_static_target_policies")

        if iscsi_static_target_policies_list:
            for iscsi_static_target_policy in iscsi_static_target_policies_list:
                self.content_list.append(
                    IntersightIscsiStaticTargetPolicyReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        iscsi_static_target_policy=iscsi_static_target_policy,
                        title="iSCSI Static Target Policy " + iscsi_static_target_policy.name,
                    )
                )
        else:
            text = "No iSCSI Static Target Policies found."
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=text,
                    italicized=True,
                )
            )


class IntersightIscsiStaticTargetPolicyReportSection(UcsReportSection):
    def __init__(self, order_id, parent, iscsi_static_target_policy, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightIscsiStaticTargetPolicyReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                centered=True,
                iscsi_static_target_policy=iscsi_static_target_policy,
            )
        )


class IntersightIscsiStaticTargetPolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, iscsi_static_target_policy, centered=False):

        rows = [
            ["Description", "Value"],
            ["Name", iscsi_static_target_policy.name],
            ["Description", iscsi_static_target_policy.descr],
            ["Organization", iscsi_static_target_policy._parent.name],
            ["Target Name", iscsi_static_target_policy.target_name],
            ["Port", iscsi_static_target_policy.port],
            ["Lun ID", iscsi_static_target_policy.lun["lun_id"]],
        ]
        if hasattr(iscsi_static_target_policy, "ipv4_address") and getattr(iscsi_static_target_policy, "ipv4_address", None):
            rows.append(["IPv4 Address", iscsi_static_target_policy.ipv4_address])
        elif hasattr(iscsi_static_target_policy, "ipv6_address") and getattr(iscsi_static_target_policy, "ipv6_address", None):
            rows.append(["IPv6 Address", iscsi_static_target_policy.ipv6_address])

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightLanConnectivityPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title="LAN Connectivity Policies"):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config

        lan_connectivity_policies_list = []
        # Searching for all LAN Connectivity Policies
        for org in config.orgs:
            self.parse_org(org, lan_connectivity_policies_list, element_to_parse="lan_connectivity_policies")

        if lan_connectivity_policies_list:
            for lan_connectivity_policy in lan_connectivity_policies_list:
                self.content_list.append(
                    IntersightLanConnectivityPolicyReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        lan_connectivity_policy=lan_connectivity_policy,
                        title="LAN Connectivity Policy " + lan_connectivity_policy.name,
                    )
                )
        else:
            text = "No LAN Connectivity Policies found."
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=text,
                    italicized=True,
                )
            )


class IntersightLanConnectivityPolicyReportSection(UcsReportSection):
    def __init__(self, order_id, parent, lan_connectivity_policy, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightLanConnectivityPolicyReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                centered=True,
                lan_connectivity_policy=lan_connectivity_policy,
            )
        )

        if hasattr(lan_connectivity_policy, "vnics") and lan_connectivity_policy.vnics:
            # Sorting the vNICs based on Slot ID and PCI Order
            lan_connectivity_policy.vnics = sorted(
                lan_connectivity_policy.vnics, key=lambda vif: (vif.get("slot_id") if vif.get("slot_id") else "",
                                                                vif.get("pci_order")))
            for vnic in lan_connectivity_policy.vnics:
                self.content_list.append(
                    GenericReportText(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        string="\nvNIC Details: " + str(vnic["name"]),
                        bolded=True,
                    )
                )

                self.content_list.append(
                    IntersightLanConnectivityPolicyVnicsReportTable(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        centered=True,
                        vnic=vnic,
                    )
                )

                if vnic.get("usnic_settings"):
                    self.content_list.append(
                        GenericReportText(
                            order_id=self.report.get_current_order_id(),
                            parent=self,
                            string="\nusNIC Settings",
                            bolded=True,
                        )
                    )
                    self.content_list.append(
                        IntersightLanConnectivityPolicyVnicUsnicReportTable(
                            order_id=self.report.get_current_order_id(),
                            parent=self,
                            centered=True,
                            vnic=vnic,
                        )
                    )

                if vnic.get("vmq_settings"):
                    self.content_list.append(
                        GenericReportText(
                            order_id=self.report.get_current_order_id(),
                            parent=self,
                            string="\nVMQ Settings",
                            bolded=True,
                        )
                    )
                    self.content_list.append(
                        IntersightLanConnectivityPolicyVnicVmqReportTable(
                            order_id=self.report.get_current_order_id(),
                            parent=self,
                            centered=True,
                            vnic=vnic,
                        )
                    )

                if vnic.get("sriov_settings"):
                    self.content_list.append(
                        GenericReportText(
                            order_id=self.report.get_current_order_id(),
                            parent=self,
                            string="\nSRIOV Settings",
                            bolded=True,
                        )
                    )
                    self.content_list.append(
                        IntersightLanConnectivityPolicyVnicSriovReportTable(
                            order_id=self.report.get_current_order_id(),
                            parent=self,
                            centered=True,
                            vnic=vnic,
                        )
                    )


class IntersightLanConnectivityPolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, lan_connectivity_policy, centered=False):

        rows = [
            ["Description", "Value"],
            ["Name", lan_connectivity_policy.name],
            ["Description", lan_connectivity_policy.descr],
            ["Organization", lan_connectivity_policy._parent.name],
            ["Target Platform", lan_connectivity_policy.target_platform],
            ["Enable Azure Stack Host QoS", lan_connectivity_policy.enable_azure_stack_host_qos],
            ["IQN Allocation Type", lan_connectivity_policy.iqn_allocation_type],
            ["IQN Identifier", lan_connectivity_policy.iqn_identifier],
            ["IQN Pool", lan_connectivity_policy.iqn_pool],
            ["vNIC Placement Model", lan_connectivity_policy.vnic_placement_mode]
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightLanConnectivityPolicyVnicsReportTable(UcsReportTable):
    def __init__(self, order_id, parent, vnic, centered=False):

        rows = [["Description", "Value"]]

        if vnic.get("name"):
            rows.append(["Name", vnic["name"]])
        if vnic.get("cdn_source"):
            rows.append(["CDN Source", vnic["cdn_source"]])
        if vnic.get("cdn_value"):
            rows.append(["CDN Value", vnic["cdn_value"]])
        if vnic.get("enable_failover"):
            rows.append(["Enable Failover", vnic["enable_failover"]])
        if vnic.get("ethernet_adapter_policy"):
            rows.append(["Ethernet Adapter Policy", vnic["ethernet_adapter_policy"]])
        if vnic.get("ethernet_network_control_policy"):
            rows.append(["Ethernet Network Control Policy", vnic["ethernet_network_control_policy"]])
        if vnic.get("ethernet_network_group_policies"):
            rows.append(["Ethernet Network Group Policies", ', '.join(vnic["ethernet_network_group_policies"])])
        elif vnic.get("ethernet_network_group_policy"):  # Deprecated
            rows.append(["Ethernet Network Group Policy", vnic["ethernet_network_group_policy"]])
        if vnic.get("ethernet_qos_policy"):
            rows.append(["Ethernet QoS Policy", vnic["ethernet_qos_policy"]])
        if vnic.get("iscsi_boot_policy"):
            rows.append(["iSCSI Boot Policy", vnic["iscsi_boot_policy"]])
        if vnic.get("mac_address_allocation_type"):
            rows.append(["MAC Address Allocation Type", vnic["mac_address_allocation_type"]])
        if vnic.get("mac_address_pool"):
            rows.append(["MAC Address Pool", vnic["mac_address_pool"]])
        if vnic.get("mac_address_static"):
            rows.append(["Static MAC Address", vnic["mac_address_static"]])
        if vnic.get("switch_id"):
            rows.append(["Switch ID", vnic["switch_id"]])
        if vnic.get("vnic_template"):
            rows.append(["vNIC Template", vnic["vnic_template"]])
        if vnic.get("automatic_pci_link_assignment"):
            rows.append(["Automatic PCI Link Assignment", vnic["automatic_pci_link_assignment"]])
        else:
            if vnic.get("pci_link_assignment_mode"):
                rows.append(["PCI Link Assignment Mode", vnic["pci_link_assignment_mode"]])
            if vnic.get("pci_link") is not None:
                rows.append(["PCI Link", vnic["pci_link"]])
        if vnic.get("automatic_slot_id_assignment"):
            rows.append(["Automatic Slot ID Assignment", vnic["automatic_slot_id_assignment"]])
        elif vnic.get("slot_id"):
            rows.append(["Slot ID", vnic["slot_id"]])
        if vnic.get("pci_order") is not None:
            rows.append(["PCI Order", vnic["pci_order"]])

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightLanConnectivityPolicyVnicUsnicReportTable(UcsReportTable):
    def __init__(self, order_id, parent, vnic, centered=False):

        rows = [["Description", "Value"]]

        if vnic["usnic_settings"].get("number_of_usnics"):
            rows.append(["Number of usNICs", vnic["usnic_settings"]["number_of_usnics"]])
        if vnic["usnic_settings"].get("usnic_adapter_policy"):
            rows.append(["usNIC Adapter Policy", vnic["usnic_settings"]["usnic_adapter_policy"]])

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightLanConnectivityPolicyVnicVmqReportTable(UcsReportTable):
    def __init__(self, order_id, parent, vnic, centered=False):

        rows = [["Description", "Value"]]

        if vnic["vmq_settings"].get("enable_virtual_machine_multi_queue"):
            rows.append(["Enable Virtual Machine Multi Queue",
                        vnic["vmq_settings"]["enable_virtual_machine_multi_queue"]])
        if vnic["vmq_settings"].get("number_of_interrupts"):
            rows.append(["Number of Interrupts", vnic["vmq_settings"]["number_of_interrupts"]])
        if vnic["vmq_settings"].get("number_of_sub_vnics"):
            rows.append(["Number of Sub vNICs", vnic["vmq_settings"]["number_of_sub_vnics"]])
        if vnic["vmq_settings"].get("number_of_virtual_machine_queues"):
            rows.append(["Number of Virtual Machine Multi Queues",
                        vnic["vmq_settings"]["number_of_virtual_machine_queues"]])
        if vnic["vmq_settings"].get("vmmq_adapter_policy"):
            rows.append(["VMMQ Adapter Policy", vnic["vmq_settings"]["vmmq_adapter_policy"]])

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightLanConnectivityPolicyVnicSriovReportTable(UcsReportTable):
    def __init__(self, order_id, parent, vnic, centered=False):

        rows = [["Description", "Value"]]

        if vnic["sriov_settings"].get("number_of_vfs"):
            rows.append(["Number of VFs", vnic["sriov_settings"]["number_of_vfs"]])
        if vnic["sriov_settings"].get("receive_queue_count_per_vf"):
            rows.append(["Receive Queue Count per VF", vnic["sriov_settings"]["receive_queue_count_per_vf"]])
        if vnic["sriov_settings"].get("transmit_queue_count_per_vf"):
            rows.append(["Transmit Queue Count per VF", vnic["sriov_settings"]["transmit_queue_count_per_vf"]])
        if vnic["sriov_settings"].get("completion_queue_count_per_vf"):
            rows.append(["Completion Queue Count per VF", vnic["sriov_settings"]["completion_queue_count_per_vf"]])
        if vnic["sriov_settings"].get("interrupt_count_per_vf"):
            rows.append(["Interrupt Count per VF", vnic["sriov_settings"]["interrupt_count_per_vf"]])

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightLocalUserPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title="Local User Policies"):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config

        local_user_policies_list = []
        # Searching for all Local User Policies
        for org in config.orgs:
            self.parse_org(org, local_user_policies_list, element_to_parse="local_user_policies")

        if local_user_policies_list:
            for local_user_policy in local_user_policies_list:
                self.content_list.append(
                    IntersightLocalUserPolicyReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        local_user_policy=local_user_policy,
                        title="Local User Policy " + local_user_policy.name,
                    )
                )
        else:
            text = "No Local User Policies found."
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=text,
                    italicized=True,
                )
            )


class IntersightLocalUserPolicyReportSection(UcsReportSection):
    def __init__(self, order_id, parent, local_user_policy, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightLocalUserPolicyReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                centered=True,
                local_user_policy=local_user_policy
            )
        )

        if local_user_policy.local_users:
            for user in local_user_policy.local_users:
                self.content_list.append(
                    IntersightLocalUserPolicyUserReportSection(
                        self.report.get_current_order_id(),
                        parent=self,
                        user=user,
                        name=user["username"],
                    )
                )


class IntersightLocalUserPolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, local_user_policy, centered=False):

        rows = [
            ["Description", "Value"],
            ["Name", local_user_policy.name],
            ["Description", local_user_policy.descr],
            ["Organization", local_user_policy._parent.name],
            ["Always Send User Password", local_user_policy.always_send_user_password],
            ["Enable Password Expiry", local_user_policy.enable_password_expiry],
            ["Enforce Strong Password", local_user_policy.enforce_strong_password],
            ["Grace Period", local_user_policy.grace_period],
            ["Notification Period", local_user_policy.notification_period],
            ["Password Expiry Duration", local_user_policy.password_expiry_duration],
            ["Password History", local_user_policy.password_history],
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightLocalUserPolicyUserReportSection(UcsReportSection):
    def __init__(self, order_id, parent, user, name="", title=""):
        if not title:
            title = "Local User " + str(name)
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightLocalUserPolicyUserReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                user=user,
                name=name,
                centered=True,
            )
        )


class IntersightLocalUserPolicyUserReportTable(UcsReportTable):
    def __init__(self, order_id, parent, user, name="", centered=False):
        rows = [
            ["Username", name],
            ["Enable", user["enable"]],
            ["Role", user["role"]],
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


class IntersightMemoryPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title="Memory Policies"):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config

        memory_policies_list = []
        # Searching for all Memory Policies
        for org in config.orgs:
            self.parse_org(org, memory_policies_list, element_to_parse="memory_policies")

        if memory_policies_list:
            for memory_policy in memory_policies_list:
                self.content_list.append(
                    IntersightMemoryPolicyReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        memory_policy=memory_policy,
                        title="Memory Policy " + memory_policy.name,
                    )
                )
        else:
            text = "No Memory Policies found."
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=text,
                    italicized=True,
                )
            )


class IntersightMemoryPolicyReportSection(UcsReportSection):
    def __init__(self, order_id, parent, memory_policy, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightMemoryPolicyReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                centered=True,
                memory_policy=memory_policy
            )
        )


class IntersightMemoryPolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, memory_policy, centered=False):
        rows = [
            ["Description", "Value"],
            ["Name", memory_policy.name],
            ["Description", memory_policy.descr],
            ["Organization", memory_policy._parent.name],
            ["Enable DIMM Blocklisting", memory_policy.enable_dimm_blocklisting]
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


class IntersightNetworkConnectivityPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title="Network Connectivity Policies"):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config

        network_connectivity_policies_list = []
        # Searching for all Network Connectivity Policies
        for org in config.orgs:
            self.parse_org(org, network_connectivity_policies_list, element_to_parse="network_connectivity_policies")

        if network_connectivity_policies_list:
            for netconfig_policy in network_connectivity_policies_list:
                self.content_list.append(
                    IntersightNetworkConnectivityPolicyReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        netconfig_policy=netconfig_policy,
                        title="Network Connectivity Policy " + netconfig_policy.name,
                    )
                )
        else:
            text = "No Network Connectivity Policies found."
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=text,
                    italicized=True,
                )
            )


class IntersightNetworkConnectivityPolicyReportSection(UcsReportSection):
    def __init__(self, order_id, parent, netconfig_policy, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightNetworkConnectivityPolicyReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                centered=True,
                netconfig_policy=netconfig_policy,
            )
        )


class IntersightNetworkConnectivityPolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, netconfig_policy, centered=False):
        rows = [
            ["Description", "Value"],
            ["Name", netconfig_policy.name],
            ["Description", netconfig_policy.descr],
            ["Organization", netconfig_policy._parent.name],
            ["Obtain IPv4 DNS from DHCP", netconfig_policy.obtain_ipv4_dns_from_dhcp],
            ["Enable IPv6", netconfig_policy.enable_ipv6],
            ["Obtain IPv6 DNS from DHCP", netconfig_policy.obtain_ipv6_dns_from_dhcp],
            ["Enable Dynamic DNS", netconfig_policy.enable_dynamic_dns],
            ["Preferred IPv4 DNS server", netconfig_policy.preferred_ipv4_dns_server],
            ["Alternate IPv4 DNS server", netconfig_policy.alternate_ipv4_dns_server],
            ["Preferred IPv6 DNS server", netconfig_policy.preferred_ipv6_dns_server],
            ["Alternate IPv6 DNS server", netconfig_policy.alternate_ipv6_dns_server],
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


class IntersightNtpPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title="NTP Policies"):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config

        ntp_policies_list = []
        # Searching for all NTP Policies
        for org in config.orgs:
            self.parse_org(org, ntp_policies_list, element_to_parse="ntp_policies")

        if ntp_policies_list:
            for ntp_policy in ntp_policies_list:
                self.content_list.append(
                    IntersightNtpPolicyReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        ntp_policy=ntp_policy,
                        title="NTP Policy " + ntp_policy.name,
                    )
                )
        else:
            text = "No NTP Policies found."
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=text,
                    italicized=True,
                )
            )


class IntersightNtpPolicyReportSection(UcsReportSection):
    def __init__(self, order_id, parent, ntp_policy, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightNtpPolicyReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                centered=True,
                ntp_policy=ntp_policy,
            )
        )


class IntersightNtpPolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, ntp_policy, centered=False):
        if ntp_policy.ntp_servers:
            ntp_servers = ", ".join(ntp_policy.ntp_servers)
        else:
            ntp_servers = None

        rows = [
            ["Description", "Value"],
            ["Name", ntp_policy.name],
            ["Description", ntp_policy.descr],
            ["Organization", ntp_policy._parent.name],
            ["Enabled", ntp_policy.enabled],
            ["NTP Servers", ntp_servers],
            ["Timezone", ntp_policy.timezone],
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


class IntersightPowerPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title="Power Policies"):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config

        power_policies_list = []
        # Searching for all Power Policies
        for org in config.orgs:
            self.parse_org(org, power_policies_list, element_to_parse="power_policies")

        if power_policies_list:
            for power_policy in power_policies_list:
                self.content_list.append(
                    IntersightPowerPolicyReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        power_policy=power_policy,
                        title="Power Policy " + power_policy.name,
                    )
                )
        else:
            text = "No Power Policies found."
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=text,
                    italicized=True,
                )
            )


class IntersightPowerPolicyReportSection(UcsReportSection):
    def __init__(self, order_id, parent, power_policy, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightPowerPolicyReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                centered=True,
                power_policy=power_policy,
            )
        )


class IntersightPowerPolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, power_policy, centered=False):
        rows = [
            ["Description", "Value"],
            ["Name", power_policy.name],
            ["Description", power_policy.descr],
            ["Organization", power_policy._parent.name],
            ["Power Profiling", power_policy.power_profiling],
            ["Power Priority", power_policy.power_priority],
            ["Power Restore", power_policy.power_restore],
            ["Processor Package Power Limit", power_policy.processor_package_power_limit]
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightSanConnectivityPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title="SAN Connectivity Policies"):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config

        san_connectivity_policies_list = []
        # Searching for all SAN Connectivity Policies
        for org in config.orgs:
            self.parse_org(org, san_connectivity_policies_list, element_to_parse="san_connectivity_policies")

        if san_connectivity_policies_list:
            for san_connectivity_policy in san_connectivity_policies_list:
                self.content_list.append(
                    IntersightSanConnectivityPolicyReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        san_connectivity_policy=san_connectivity_policy,
                        title="SAN Connectivity Policy " + san_connectivity_policy.name,
                    )
                )
        else:
            text = "No SAN Connectivity Policies found."
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=text,
                    italicized=True,
                )
            )


class IntersightSanConnectivityPolicyReportSection(UcsReportSection):
    def __init__(self, order_id, parent, san_connectivity_policy, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightSanConnectivityPolicyReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                centered=True,
                san_connectivity_policy=san_connectivity_policy,
            )
        )

        if hasattr(san_connectivity_policy, "vhbas") and san_connectivity_policy.vhbas:
            # Sorting the vHBAs based on Slot ID and PCI Order
            san_connectivity_policy.vhbas = sorted(
                san_connectivity_policy.vhbas, key=lambda vif: (vif.get("slot_id"), vif.get("pci_order")))
            for vhba in san_connectivity_policy.vhbas:
                self.content_list.append(
                    GenericReportText(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        string="\nvHBA Details: " + str(vhba["name"]),
                        bolded=True,
                    )
                )

                self.content_list.append(
                    IntersightSanConnectivityPolicyVhbasReportTable(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        centered=True,
                        vhba=vhba,
                    )
                )


class IntersightSanConnectivityPolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, san_connectivity_policy, centered=False):

        rows = [
            ["Description", "Value"],
            ["Name", san_connectivity_policy.name],
            ["Description", san_connectivity_policy.descr],
            ["Organization", san_connectivity_policy._parent.name],
            ["Target Platform", san_connectivity_policy.target_platform],
            ["vHBA Placement Model", san_connectivity_policy.vhba_placement_mode],
            ["WWNN Allocation Type", san_connectivity_policy.wwnn_allocation_type],
            ["Static WWNN", san_connectivity_policy.wwnn_static],
            ["WWNN Pool", san_connectivity_policy.wwnn_pool]
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightSanConnectivityPolicyVhbasReportTable(UcsReportTable):
    def __init__(self, order_id, parent, vhba, centered=False):

        rows = [["Description", "Value"]]

        if vhba.get("name"):
            rows.append(["Name", vhba["name"]])
        if vhba.get("fc_zone_policies"):
            rows.append(["FC Zone Policies", ', '.join(vhba["fc_zone_policies"])])
        if vhba.get("fibre_channel_adapter_policy"):
            rows.append(["Fibre Channel Adapter Policy", vhba["fibre_channel_adapter_policy"]])
        if vhba.get("fibre_channel_network_policy"):
            rows.append(["Fibre Channel Network Policy", vhba["fibre_channel_network_policy"]])
        if vhba.get("fibre_channel_qos_policy"):
            rows.append(["Fibre Channel QoS Policy", vhba["fibre_channel_qos_policy"]])
        if vhba.get("persistent_lun_bindings"):
            rows.append(["Persistent LUN Bindings", vhba["persistent_lun_bindings"]])
        if vhba.get("switch_id"):
            rows.append(["Switch ID", vhba["switch_id"]])
        if vhba.get("vhba_template"):
            rows.append(["vHBA Template", vhba["vhba_template"]])
        if vhba.get("automatic_pci_link_assignment"):
            rows.append(["Automatic PCI Link Assignment", vhba["automatic_pci_link_assignment"]])
        else:
            if vhba.get("pci_link_assignment_mode"):
                rows.append(["PCI Link Assignment Mode", vhba["pci_link_assignment_mode"]])
            if vhba.get("pci_link") is not None:
                rows.append(["PCI Link", vhba["pci_link"]])
        if vhba.get("automatic_slot_id_assignment"):
            rows.append(["Automatic Slot ID Assignment", vhba["automatic_slot_id_assignment"]])
        elif vhba.get("slot_id"):
            rows.append(["Slot ID", vhba["slot_id"]])
        if vhba.get("pci_order") is not None:
            rows.append(["PCI Order", vhba["pci_order"]])
        if vhba.get("vhba_type"):
            rows.append(["vHBA Type", vhba["vhba_type"]])
        if vhba.get("wwpn_allocation_type"):
            rows.append(["WWPN Allocation Type", vhba["wwpn_allocation_type"]])
        if vhba.get("wwpn_pool"):
            rows.append(["WWPN Pool", vhba["wwpn_pool"]])
        if vhba.get("wwpn_static"):
            rows.append(["WWPN Static", vhba["wwpn_static"]])

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightScrubPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title="Scrub Policies"):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config

        scrub_policies_list = []

        for org in config.orgs:
            self.parse_org(org, scrub_policies_list, element_to_parse="scrub_policies")

        if scrub_policies_list:
            for scrub_policy in scrub_policies_list:
                self.content_list.append(
                    IntersightScrubPolicyReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        scrub_policy=scrub_policy,
                        title="Scrub Policy " + scrub_policy.name,
                    )
                )
        else:
            text = "No Scrub Policies found."
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=text,
                    italicized=True,
                )
            )


class IntersightScrubPolicyReportSection(UcsReportSection):
    def __init__(self, order_id, parent, scrub_policy, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightScrubPolicyReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                centered=True,
                scrub_policy=scrub_policy,
            )
        )


class IntersightScrubPolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, scrub_policy, centered=False):

        rows = [
            ["Description", "Value"],
            ["Name", scrub_policy.name],
            ["Description", scrub_policy.descr],
            ["Disk Scrub", scrub_policy.disk ],
            ["BIOS Settings Scrub", scrub_policy.bios]
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


class IntersightSdCardPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title="SD Card Policies"):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config

        sd_card_policies_list = []
        # Searching for all SD Card Policies
        for org in config.orgs:
            self.parse_org(org, sd_card_policies_list, element_to_parse="sd_card_policies")

        if sd_card_policies_list:
            for sdcard_policy in sd_card_policies_list:
                self.content_list.append(
                    IntersightSdCardPolicyReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        sdcard_policy=sdcard_policy,
                        title="SD Card Policy " + sdcard_policy.name,
                    )
                )
        else:
            text = "No SD Card Policies found."
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=text,
                    italicized=True,
                )
            )


class IntersightSdCardPolicyReportSection(UcsReportSection):
    def __init__(self, order_id, parent, sdcard_policy, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightSdCardPolicyReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                centered=True,
                sdcard_policy=sdcard_policy,
            )
        )


class IntersightSdCardPolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, sdcard_policy, centered=False):

        rows = [
            ["Description", "Value"],
            ["Name", sdcard_policy.name],
            ["Description", sdcard_policy.descr],
            ["Organization", sdcard_policy._parent.name],
        ]

        if hasattr(sdcard_policy, "partitions") and sdcard_policy.partitions:
            for partition in sdcard_policy.partitions:
                rows.append(["SD Card Mode", partition["type"]])
                if partition.get("virtual_drives"):
                    for virtual_drive in partition["virtual_drives"]:
                        rows.append(["Enable Virtual Drive", virtual_drive["enable"]])
                        rows.append(["Virtual Drive Name", virtual_drive["name"]])
                        rows.append(["Virtual Drive Type", virtual_drive["object_type"]])

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightServerPoolQualificationPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title="Server Pool Qualification Policies"):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config

        server_pool_qualification_policies_list = []
        # Searching for all Server Pool Qualification Policies
        for org in config.orgs:
            self.parse_org(org, server_pool_qualification_policies_list,
                           element_to_parse="server_pool_qualification_policies")

        if server_pool_qualification_policies_list:
            for server_pool_qualification_policy in server_pool_qualification_policies_list:
                self.content_list.append(
                    IntersightServerPoolQualificationPolicyReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        server_pool_qualification_policy=server_pool_qualification_policy,
                        title="Server Pool Qualification Policy " + server_pool_qualification_policy.name,
                    )
                )
        else:
            text = "No Server Pool Qualification Policies found."
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=text,
                    italicized=True,
                )
            )


class IntersightServerPoolQualificationPolicyReportSection(UcsReportSection):
    def __init__(self, order_id, parent, server_pool_qualification_policy, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightServerPoolQualificationPolicyReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                centered=True,
                server_pool_qualification_policy=server_pool_qualification_policy,
            )
        )

        if server_pool_qualification_policy.domain_qualifiers:
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string="\nDomain Qualifiers:",
                    bolded=True,
                )
            )

            self.content_list.append(
                IntersightServerPoolQualificationPolicyDomainQualifiersReportTable(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    centered=True,
                    domain_qualifiers=server_pool_qualification_policy.domain_qualifiers,
                )
            )

        if server_pool_qualification_policy.hardware_qualifiers:
            if server_pool_qualification_policy.hardware_qualifiers.get("memory_qualifier"):
                memory_qualifier = server_pool_qualification_policy.hardware_qualifiers["memory_qualifier"]
                self.content_list.append(
                    GenericReportText(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        string="\nHardware Qualifiers: Memory Qualifier",
                        bolded=True,
                    )
                )
                self.content_list.append(
                    IntersightServerPoolQualificationPolicyMemoryQualifierReportTable(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        centered=True,
                        memory_qualifier=memory_qualifier,
                    )
                )
            if server_pool_qualification_policy.hardware_qualifiers.get("gpu_qualifier"):
                gpu_qualifier = server_pool_qualification_policy.hardware_qualifiers["gpu_qualifier"]
                self.content_list.append(
                    GenericReportText(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        string="\nHardware Qualifiers: GPU Qualifier",
                        bolded=True,
                    )
                )
                self.content_list.append(
                    IntersightServerPoolQualificationPolicyGpuQualifierReportTable(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        centered=True,
                        gpu_qualifier=gpu_qualifier,
                    )
                )
            if server_pool_qualification_policy.hardware_qualifiers.get("cpu_qualifier"):
                cpu_qualifier = server_pool_qualification_policy.hardware_qualifiers["cpu_qualifier"]
                self.content_list.append(
                    GenericReportText(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        string="\nHardware Qualifiers: CPU Qualifier",
                        bolded=True,
                    )
                )
                self.content_list.append(
                    IntersightServerPoolQualificationPolicyCpuQualifierReportTable(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        centered=True,
                        cpu_qualifier=cpu_qualifier,
                    )
                )
            if server_pool_qualification_policy.hardware_qualifiers.get("network_adapter_qualifier"):
                network_adapter_qualifier = (
                    server_pool_qualification_policy.hardware_qualifiers["network_adapter_qualifier"])
                self.content_list.append(
                    GenericReportText(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        string="\nHardware Qualifiers: Network Adapter Qualifier",
                        bolded=True,
                    )
                )
                self.content_list.append(
                    IntersightServerPoolQualificationPolicyNetworkAdapterQualifierReportTable(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        centered=True,
                        network_adapter_qualifier=network_adapter_qualifier,
                    )
                )

        if server_pool_qualification_policy.tag_qualifiers:
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string="\nTag Qualifiers:",
                    bolded=True,
                )
            )

            self.content_list.append(
                IntersightServerPoolQualificationPolicyTagQualifiersReportTable(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    centered=True,
                    tag_qualifiers=server_pool_qualification_policy.tag_qualifiers,
                )
            )

        if server_pool_qualification_policy.server_qualifiers:

            if server_pool_qualification_policy.server_qualifiers.get("rack_server_qualifier"):
                rack_server_qualifier = server_pool_qualification_policy.server_qualifiers["rack_server_qualifier"]
                self.content_list.append(
                    GenericReportText(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        string="\nRack Server Qualifier:",
                        bolded=True,
                    )
                )
                self.content_list.append(
                    IntersightServerPoolQualificationPolicyRackServerQualifierReportTable(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        centered=True,
                        rack_server_qualifier=rack_server_qualifier,
                    )
                )
                if rack_server_qualifier.get("rack_ids"):
                    self.content_list.append(
                        GenericReportText(
                            order_id=self.report.get_current_order_id(),
                            parent=self,
                            string="\nRack Server Qualifier: Rack IDs",
                            bolded=True,
                        )
                    )

                    for rack_id in rack_server_qualifier["rack_ids"]:
                        self.content_list.append(
                            IntersightServerPoolQualificationPolicyRackServerQualifierRackIDsReportTable(
                                order_id=self.report.get_current_order_id(),
                                parent=self,
                                centered=True,
                                rack_ids=rack_id,
                            )
                        )

            if server_pool_qualification_policy.server_qualifiers.get("blade_server_qualifier"):
                blade_server_qualifier = server_pool_qualification_policy.server_qualifiers["blade_server_qualifier"]
                self.content_list.append(
                    GenericReportText(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        string="\nBlade Server Qualifier:",
                        bolded=True,
                    )
                )

                self.content_list.append(
                    IntersightServerPoolQualificationPolicyBladeServerQualifierReportTable(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        centered=True,
                        blade_server_qualifier=blade_server_qualifier,
                    )
                )
                if blade_server_qualifier.get("chassis_slot_ids"):
                    self.content_list.append(
                        GenericReportText(
                            order_id=self.report.get_current_order_id(),
                            parent=self,
                            string="\nBlade Server Qualifier: Chassis and Slot IDs",
                            bolded=True,
                        )
                    )
                    for chassis_slot_id in blade_server_qualifier["chassis_slot_ids"]:
                        if chassis_slot_id.get("chassis_ids"):
                            self.content_list.append(
                                IntersightServerPoolQualificationPolicyBladeServerQualifierChassisIDsReportTable(
                                    order_id=self.report.get_current_order_id(),
                                    parent=self,
                                    centered=True,
                                    chassis_ids=chassis_slot_id["chassis_ids"]
                                )
                            )
                        if chassis_slot_id.get("slot_ids"):
                            for slot_id in chassis_slot_id["slot_ids"]:
                                self.content_list.append(
                                    IntersightServerPoolQualificationPolicyBladeServerQualifierSlotIDsReportTable(
                                        order_id=self.report.get_current_order_id(),
                                        parent=self,
                                        centered=True,
                                        slot_id=slot_id,
                                    )
                                )


class IntersightServerPoolQualificationPolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, server_pool_qualification_policy, centered=False):

        rows = [
            ["Description", "Value"],
            ["Name", server_pool_qualification_policy.name],
            ["Description", server_pool_qualification_policy.descr],
            ["Organization", server_pool_qualification_policy._parent.name]
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightServerPoolQualificationPolicyDomainQualifiersReportTable(UcsReportTable):
    def __init__(self, order_id, parent, domain_qualifiers, centered=False):

        rows = [
            ["Description", "Value"],
            ["Domain Names", domain_qualifiers.get("domain_names")],
            ["Fabric Interconnect PIDs", domain_qualifiers.get("fabric_interconnect_pids")]

        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightServerPoolQualificationPolicyRackServerQualifierReportTable(UcsReportTable):
    def __init__(self, order_id, parent, rack_server_qualifier, centered=False):

        rows = [
            ["Description", "Value"],
            ["Asset Tags", rack_server_qualifier.get("asset_tags")],
            ["Rack PIDs", rack_server_qualifier.get("rack_pids")],
            ["User Labels", rack_server_qualifier.get("user_labels")]
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightServerPoolQualificationPolicyRackServerQualifierRackIDsReportTable(UcsReportTable):
    def __init__(self, order_id, parent, rack_ids, centered=False):

        rows = [
            ["Description", "Value"],
            ["Rack ID From", rack_ids.get("rack_id_from")],
            ["Rack ID To", rack_ids.get("rack_id_to")]
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightServerPoolQualificationPolicyBladeServerQualifierReportTable(UcsReportTable):
    def __init__(self, order_id, parent, blade_server_qualifier, centered=False):

        rows = [
            ["Description", "Value"],
            ["Asset Tags", blade_server_qualifier.get("asset_tags")],
            ["Blade PIDs", blade_server_qualifier.get("rack_pids")],
            ["Chassis PIDs", blade_server_qualifier.get("chassis_pids")],
            ["User Labels", blade_server_qualifier.get("user_labels")]
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightServerPoolQualificationPolicyBladeServerQualifierChassisIDsReportTable(UcsReportTable):
    def __init__(self, order_id, parent, chassis_ids, centered=False):

        rows = [
            ["Description", "Value"],
            ["Chassis ID From", chassis_ids.get("chassis_id_from")],
            ["Chassis ID To", chassis_ids.get("chassis_id_to")]
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightServerPoolQualificationPolicyBladeServerQualifierSlotIDsReportTable(UcsReportTable):
    def __init__(self, order_id, parent, slot_id, centered=False):

        rows = [
            ["Description", "Value"],
            ["Slot ID From", slot_id.get("slot_id_from")],
            ["Slot ID To", slot_id.get("slot_id_to")]
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightServerPoolQualificationPolicyTagQualifiersReportTable(UcsReportTable):
    def __init__(self, order_id, parent, tag_qualifiers, centered=False):

        rows = [
            ["Description", "Value"],
            ["Chassis Tags", tag_qualifiers.get("chassis_tags")],
            ["Domain Profile Tags", tag_qualifiers.get("domain_profile_tags")],
            ["Server Tags", tag_qualifiers.get("server_tags")]
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightServerPoolQualificationPolicyMemoryQualifierReportTable(UcsReportTable):
    def __init__(self, order_id, parent, memory_qualifier, centered=False):

        rows = [
            ["Description", "Value"],
            ["Capacity Minimum", memory_qualifier.get("capacity_minimum")],
            ["Capacity Maximum", memory_qualifier.get("capacity_maximum")],
            ["Number of Units Minimum", memory_qualifier.get("number_of_units_minimum")],
            ["Number of Units Maximum", memory_qualifier.get("number_of_units_maximum")]
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightServerPoolQualificationPolicyGpuQualifierReportTable(UcsReportTable):
    def __init__(self, order_id, parent, gpu_qualifier, centered=False):

        rows = [
            ["Description", "Value"],
            ["GPU PIDs", gpu_qualifier.get("gpu_pids")],
            ["GPU Evaluation Type", gpu_qualifier.get("gpu_evaluation_type")],
            ["Number of GPUs Minimum", gpu_qualifier.get("number_of_gpus_minimum")],
            ["Number of Gpus Maximum", gpu_qualifier.get("number_of_gpus_maximum")],
            ["Vendor", gpu_qualifier.get("vendor")]
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightServerPoolQualificationPolicyCpuQualifierReportTable(UcsReportTable):
    def __init__(self, order_id, parent, cpu_qualifier, centered=False):

        rows = [
            ["Description", "Value"],
            ["CPU PIDs", cpu_qualifier.get("cpu_pids")],
            ["Number of Cores Minimum", cpu_qualifier.get("number_of_cores_minimum")],
            ["Number of Cores Maximum", cpu_qualifier.get("number_of_cores_maximum")],
            ["Speed Minimum", cpu_qualifier.get("speed_minimum")],
            ["Speed Maximum", cpu_qualifier.get("speed_maximum")],
            ["Vendor", cpu_qualifier.get("vendor")]
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightServerPoolQualificationPolicyNetworkAdapterQualifierReportTable(UcsReportTable):
    def __init__(self, order_id, parent, network_adapter_qualifier, centered=False):

        rows = [
            ["Description", "Value"],
            ["Number of Network Adapters Minimum", network_adapter_qualifier.get("number_of_network_adapters_minimum")],
            ["Number of Network Adapters Maximum", network_adapter_qualifier.get("number_of_network_adapters_maximum")]
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightSerialOverLanPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title="Serial over LAN Policies"):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config

        serial_over_lan_policies_list = []
        # Searching for all Serial Over LAN Policies
        for org in config.orgs:
            self.parse_org(org, serial_over_lan_policies_list, element_to_parse="serial_over_lan_policies")

        if serial_over_lan_policies_list:
            for sol_policy in serial_over_lan_policies_list:
                self.content_list.append(
                    IntersightSerialOverLanPolicyReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        sol_policy=sol_policy,
                        title="Serial Over LAN Policy " + sol_policy.name,
                    )
                )
        else:
            text = "No Serial Over LAN Policies found."
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=text,
                    italicized=True,
                )
            )


class IntersightSerialOverLanPolicyReportSection(UcsReportSection):
    def __init__(self, order_id, parent, sol_policy, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightSerialOverLanPolicyReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                centered=True,
                sol_policy=sol_policy,
            )
        )


class IntersightSerialOverLanPolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, sol_policy, centered=False):

        rows = [
            ["Description", "Value"],
            ["Name", sol_policy.name],
            ["Description", sol_policy.descr],
            ["Organization", sol_policy._parent.name],
            ["Enable Serial Over LAN", sol_policy.enabled],
            ["COM Port", sol_policy.com_port],
            ["Baud Rate", sol_policy.baud_rate],
            ["SSH Port", sol_policy.ssh_port],
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightStoragePoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title="Storage Policies"):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config

        storage_policies_list = []
        # Searching for all Storage Policies
        for org in config.orgs:
            self.parse_org(org, storage_policies_list, element_to_parse="storage_policies")

        if storage_policies_list:
            for storage_policy in storage_policies_list:
                self.content_list.append(
                    IntersightStoragePolicyReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        storage_policy=storage_policy,
                        title="Storage Policy " + storage_policy.name,
                    )
                )
        else:
            text = "No Storage Policies found."
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=text,
                    italicized=True,
                )
            )


class IntersightStoragePolicyReportSection(UcsReportSection):
    def __init__(self, order_id, parent, storage_policy, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightStoragePolicyReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                centered=True,
                storage_policy=storage_policy,
            )
        )

        if hasattr(storage_policy, "m2_configuration") and storage_policy.m2_configuration:
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string="\nM.2 Configuration Details",
                    bolded=True,
                )
            )

            self.content_list.append(
                IntersightStoragePolicyM2ConfigReportTable(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    centered=True,
                    m2_config=storage_policy.m2_configuration,
                )
            )

        if hasattr(storage_policy, "drive_group") and storage_policy.drive_group:
            for drive_group in storage_policy.drive_group:
                self.content_list.append(
                    GenericReportText(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        string="\nDrive Group Details: " + str(drive_group["drive_group_name"]),
                        bolded=True,
                    )
                )

                self.content_list.append(
                    IntersightStoragePolicyDriveGroupReportTable(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        centered=True,
                        drive_group=drive_group,
                    )
                )

                if drive_group.get("virtual_drives"):
                    for virtual_drive in drive_group["virtual_drives"]:
                        self.content_list.append(
                            GenericReportText(
                                order_id=self.report.get_current_order_id(),
                                parent=self,
                                string="\nVirtual Drive Details: " + str(virtual_drive["vd_name"]),
                                bolded=True,
                            )
                        )

                        self.content_list.append(
                            IntersightStoragePolicyVirtualDriveReportTable(
                                order_id=self.report.get_current_order_id(),
                                parent=self,
                                centered=True,
                                virtual_drive=virtual_drive,
                            )
                        )

        if (
            hasattr(storage_policy, "single_drive_raid_configuration")
            and storage_policy.single_drive_raid_configuration
        ):
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string="\nSingle Drive RAID Configuration Details",
                    bolded=True,
                )
            )

            self.content_list.append(
                IntersightStoragePolicySingleDriveReportTable(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    centered=True,
                    single_drive=storage_policy.single_drive_raid_configuration,
                )
            )

        if hasattr(storage_policy, "hybrid_slot_configuration") and storage_policy.hybrid_slot_configuration:
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string="\nHybrid Slot Configuration Details",
                    bolded=True,
                )
            )

            self.content_list.append(
                IntersightStoragePolicyHybridSlotConfigReportTable(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    centered=True,
                    hybrid_slot_config=storage_policy.hybrid_slot_configuration,
                )
            )


class IntersightStoragePolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, storage_policy, centered=False):

        rows = [
            ["Description", "Value"],
            ["Name", storage_policy.name],
            ["Description", storage_policy.descr],
            ["Organization", storage_policy._parent.name],
            ["Use JBOD drives for VD Creation", storage_policy.use_jbod_for_vd_creation],
            ["Unused Disks State", storage_policy.unused_disks_state],
            ["Default Drive State", storage_policy.default_drive_state],
            ["Secure JBOD Disk Slots", storage_policy.secure_jbod_disk_slots],
            ["Global Hot Spares", storage_policy.global_hot_spares],
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightStoragePolicyM2ConfigReportTable(UcsReportTable):
    def __init__(self, order_id, parent, m2_config, centered=False):

        rows = [
            ["Description", "Value"],
            ["Enable", m2_config.get("enable")],
            ["Virtual Drive Name", m2_config.get("name")],
            ["Controller Slot", m2_config.get("controller_slot")]
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightStoragePolicyDriveGroupReportTable(UcsReportTable):
    def __init__(self, order_id, parent, drive_group, centered=False):

        rows = [
            ["Description", "Value"],
            ["Drive Group Name", drive_group.get("drive_group_name")],
            ["RAID Level", drive_group.get("raid_level")],
            ["Secure Drive Group", drive_group.get("secure_drive_group")]
        ]

        if drive_group.get("manual_drive_selection"):
            rows.append(["Drive Group Type", "Manual"])
            rows.append(["Dedicated Hot Spares", drive_group["manual_drive_selection"]["dedicated_hot_spares"]])
            for drive_array_span in drive_group["manual_drive_selection"]["drive_array_spans"]:
                rows.append(["Disks Slot Range", str(drive_array_span["slots"])])

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightStoragePolicyVirtualDriveReportTable(UcsReportTable):
    def __init__(self, order_id, parent, virtual_drive, centered=False):

        rows = [
            ["Description", "Value"],
            ["Virtual Drive Name", virtual_drive.get("vd_name")],
            ["Size (MiB)", virtual_drive.get("size")],
            ["Expand to available", virtual_drive.get("expand_to_available")],
            ["Set as Boot Drive", virtual_drive.get("boot_drive")],
            ["Strip Size", virtual_drive.get("strip_size")],
            ["Access Policy", virtual_drive.get("access_policy")],
            ["Read Policy", virtual_drive.get("read_policy")],
            ["Write Policy", virtual_drive.get("write_policy")],
            ["Disk Cache", virtual_drive.get("disk_cache")]
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightStoragePolicySingleDriveReportTable(UcsReportTable):
    def __init__(self, order_id, parent, single_drive, centered=False):

        rows = [
            ["Description", "Value"],
            ["Enable", single_drive.get("enable")],
            ["Drive Slots", single_drive.get("drive_slots")],
            ["Strip Size", single_drive.get("strip_size")],
            ["Access Policy", single_drive.get("access_policy")],
            ["Read Policy", single_drive.get("read_policy")],
            ["Write Policy", single_drive.get("write_policy")],
            ["Disk Cache", single_drive.get("disk_cache")]
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightStoragePolicyHybridSlotConfigReportTable(UcsReportTable):
    def __init__(self, order_id, parent, hybrid_slot_config, centered=False):

        rows = [
            ["Description", "Value"],
            ["Controller Attached NVMe Slots", hybrid_slot_config.get("controller_attached_nvme_slots")],
            ["Direct Attached NVMe Slots", hybrid_slot_config.get("direct_attached_nvme_slots")]
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightSyslogPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title="Syslog Policies"):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config

        syslog_policies_list = []
        # Searching for all Syslog Policies
        for org in config.orgs:
            self.parse_org(org, syslog_policies_list, element_to_parse="syslog_policies")

        if syslog_policies_list:
            for syslog_policy in syslog_policies_list:
                self.content_list.append(
                    IntersightSyslogPolicyReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        syslog_policy=syslog_policy,
                        title="Syslog Policy " + syslog_policy.name,
                    )
                )
        else:
            text = "No Syslog Policies found."
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=text,
                    italicized=True,
                )
            )


class IntersightSyslogPolicyReportSection(UcsReportSection):
    def __init__(self, order_id, parent, syslog_policy, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightSyslogPolicyReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                centered=True,
                syslog_policy=syslog_policy,
            )
        )


class IntersightSyslogPolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, syslog_policy, centered=False):
        rows = [
            ["Description", "Value"],
            ["Name", syslog_policy.name],
            ["Description", syslog_policy.descr],
            ["Organization", syslog_policy._parent.name]
        ]

        if syslog_policy.local_logging:
            if "file" in syslog_policy.local_logging:
                if "min_severity" in syslog_policy.local_logging["file"]:
                    rows.append(
                        ["Local Logging - File - Min Severity", syslog_policy.local_logging["file"]["min_severity"]]
                    )

        if syslog_policy.remote_logging:
            if syslog_policy.remote_logging.get("server1"):
                rows.append(
                    ["Remote Logging - Server1 - Enabled", syslog_policy.remote_logging["server1"]["enable"]]
                )
                rows.append(
                    ["Remote Logging - Server1 - Hostname", syslog_policy.remote_logging["server1"]["hostname"]]
                )
                rows.append(
                    ["Remote Logging - Server1 - Min Severity",
                     syslog_policy.remote_logging["server1"]["min_severity"]]
                )

        if syslog_policy.remote_logging:
            if syslog_policy.remote_logging.get("server2"):
                rows.append(
                    ["Remote Logging - Server2 - Enabled", syslog_policy.remote_logging["server2"]["enable"]]
                )
                rows.append(
                    ["Remote Logging - Server2 - Hostname", syslog_policy.remote_logging["server2"]["hostname"]]
                )
                rows.append(
                    ["Remote Logging - Server2 - Min Severity",
                     syslog_policy.remote_logging["server2"]["min_severity"]]
                )

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[0]),
            centered=centered,
            cells_list=rows,
        )


class IntersightThermalPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title="Thermal Policies"):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config

        thermal_policies_list = []
        # Searching for all Thermal Policies
        for org in config.orgs:
            self.parse_org(org, thermal_policies_list, element_to_parse="thermal_policies")

        if thermal_policies_list:
            for thermal_policy in thermal_policies_list:
                self.content_list.append(
                    IntersightThermalPolicyReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        thermal_policy=thermal_policy,
                        title="Thermal Policy " + thermal_policy.name,
                    )
                )
        else:
            text = "No Thermal Policies found."
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=text,
                    italicized=True,
                )
            )


class IntersightThermalPolicyReportSection(UcsReportSection):
    def __init__(self, order_id, parent, thermal_policy, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightThermalPolicyReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                centered=True,
                thermal_policy=thermal_policy,
            )
        )


class IntersightThermalPolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, thermal_policy, centered=False):
        rows = [
            ["Description", "Value"],
            ["Name", thermal_policy.name],
            ["Description", thermal_policy.descr],
            ["Organization", thermal_policy._parent.name],
            ["Fan Control Mode", thermal_policy.fan_control_mode],
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightVirtualKvmPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title="Virtual KVM Policies"):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config

        virtual_kvm_policies_list = []
        # Searching for all Virtual KVM Policies
        for org in config.orgs:
            self.parse_org(org, virtual_kvm_policies_list, element_to_parse="virtual_kvm_policies")

        if virtual_kvm_policies_list:
            for kvm_policy in virtual_kvm_policies_list:
                self.content_list.append(
                    IntersightVirtualKvmPolicyReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        kvm_policy=kvm_policy,
                        title="Virtual KVM Policy " + kvm_policy.name,
                    )
                )
        else:
            text = "No Virtual KVM Policies found."
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=text,
                    italicized=True,
                )
            )


class IntersightVirtualKvmPolicyReportSection(UcsReportSection):
    def __init__(self, order_id, parent, kvm_policy, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightVirtualKvmPolicyReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                centered=True,
                kvm_policy=kvm_policy,
            )
        )


class IntersightVirtualKvmPolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, kvm_policy, centered=False):

        rows = [
            ["Description", "Value"],
            ["Name", kvm_policy.name],
            ["Description", kvm_policy.descr],
            ["Organization", kvm_policy._parent.name],
            ["Enable Virtual KVM", kvm_policy.enable_virtual_kvm],
            ["Max Sessions", kvm_policy.max_sessions],
            ["Remote Port", kvm_policy.remote_port],
            ["Enable Video Encryption", kvm_policy.enable_video_encryption],
            ["Enable Local Server Video", kvm_policy.enable_local_server_video],
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightVirtualMediaPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title="Virtual Media Policies"):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config

        virtual_media_policies_list = []
        # Searching for all Virtual Media Policies
        for org in config.orgs:
            self.parse_org(org, virtual_media_policies_list, element_to_parse="virtual_media_policies")

        if virtual_media_policies_list:
            for vmedia_policy in virtual_media_policies_list:
                self.content_list.append(
                    IntersightVirtualMediaPolicyReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        vmedia_policy=vmedia_policy,
                        title="Virtual Media Policy " + vmedia_policy.name,
                    )
                )
        else:
            text = "No Virtual Media Policies found."
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=text,
                    italicized=True,
                )
            )


class IntersightVirtualMediaPolicyReportSection(UcsReportSection):
    def __init__(self, order_id, parent, vmedia_policy, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightVirtualMediaPolicyReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                centered=True,
                vmedia_policy=vmedia_policy,
            )
        )

        if hasattr(vmedia_policy, "vmedia_mounts") and vmedia_policy.vmedia_mounts:
            for vmedia_mount in vmedia_policy.vmedia_mounts:
                self.content_list.append(
                    GenericReportText(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        string="\nvMedia Mount Details: " + str(vmedia_mount["name"]),
                        bolded=True,
                    )
                )

                self.content_list.append(
                    IntersightVirtualMediaPolicyMountsReportTable(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        centered=True,
                        vmedia_mount=vmedia_mount,
                    )
                )


class IntersightVirtualMediaPolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, vmedia_policy, centered=False):

        rows = [
            ["Description", "Value"],
            ["Name", vmedia_policy.name],
            ["Description", vmedia_policy.descr],
            ["Organization", vmedia_policy._parent.name],
            ["Enable Virtual Media", vmedia_policy.enable_virtual_media],
            ["Enable Virtual Media Encryption", vmedia_policy.enable_virtual_media_encryption],
            ["Enable Low Power USB", vmedia_policy.enable_low_power_usb],
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightVirtualMediaPolicyMountsReportTable(UcsReportTable):
    def __init__(self, order_id, parent, vmedia_mount, centered=False):

        rows = [["Description", "Value"]]

        if vmedia_mount.get("device_type"):
            rows.append(["Virtual Media Type", vmedia_mount["device_type"]])
        if vmedia_mount.get("protocol"):
            rows.append(["Protocol", vmedia_mount["protocol"]])
        if vmedia_mount.get("name"):
            rows.append(["Name", vmedia_mount["name"]])
        if vmedia_mount.get("file_location"):
            rows.append(["File Location", vmedia_mount["file_location"]])
        if vmedia_mount.get("mount_options"):
            rows.append(["Mount Options", vmedia_mount["mount_options"]])
        if vmedia_mount.get("username"):
            rows.append(["User Name", vmedia_mount["username"]])
        if vmedia_mount.get("password"):
            rows.append(["Password", "<<Set>>"])
        if vmedia_mount.get("authentication_protocol"):
            rows.append(["Authentication Protocol", vmedia_mount["authentication_protocol"]])
        if vmedia_mount.get("hostname"):
            rows.append(["Host Name", vmedia_mount["hostname"]])
        if vmedia_mount.get("remote_path"):
            rows.append(["Remote Path", vmedia_mount["remote_path"]])
        if vmedia_mount.get("remote_file"):
            rows.append(["Remote File", vmedia_mount["remote_file"]])

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightVhbaTemplatesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title="vHBA Templates"):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config

        vhba_templates = []
        # Searching for all vHBA Templates
        for org in config.orgs:
            self.parse_org(org, vhba_templates, element_to_parse="vhba_templates")

        if vhba_templates:
            for vhba_template in vhba_templates:
                self.content_list.append(
                    IntersightVhbaTemplateReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        vhba_template=vhba_template,
                        title="vHBA Template " + vhba_template.name,
                    )
                )
        else:
            text = "No vHBA Templates found. "
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=text,
                    italicized=True,
                )
            )


class IntersightVhbaTemplateReportSection(UcsReportSection):
    def __init__(self, order_id, parent, vhba_template, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightVhbaTemplateReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                centered=True,
                vhba_template=vhba_template,
            )
        )


class IntersightVhbaTemplateReportTable(UcsReportTable):
    def __init__(self, order_id, parent, vhba_template, centered=False):
        rows = [
            ["Description", "Value"],
            ["Name", vhba_template.name],
            ["Description", vhba_template.descr],
            ["Organization", vhba_template._parent.name],
            ["Enable Override", vhba_template.enable_override],
            ["FC Zone Policies", vhba_template.fc_zone_policies],
            ["Fibre Channel Adapter Policy", vhba_template.fibre_channel_adapter_policy],
            ["Fibre Channel Network Policy", vhba_template.fibre_channel_network_policy],
            ["Fibre Channel QoS Policy", vhba_template.fibre_channel_qos_policy],
            ["Persistent LUN Bindings", vhba_template.persistent_lun_bindings],
            ["Pin Group Name", vhba_template.pin_group_name],
            ["Switch ID", vhba_template.switch_id],
            ["vHBA Type", vhba_template.vhba_type],
            ["WWPN Pool", vhba_template.wwpn_pool]
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )
        

class IntersightVnicTemplatesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title="vNIC Templates"):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config

        vnic_templates = []
        # Searching for all vNIC Templates
        for org in config.orgs:
            self.parse_org(org, vnic_templates, element_to_parse="vnic_templates")

        if vnic_templates:
            for vnic_template in vnic_templates:
                self.content_list.append(
                    IntersightVnicTemplateReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        vnic_template=vnic_template,
                        title="vNIC Template " + vnic_template.name,
                    )
                )
        else:
            text = "No vNIC Templates found. "
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=text,
                    italicized=True,
                )
            )


class IntersightVnicTemplateReportSection(UcsReportSection):
    def __init__(self, order_id, parent, vnic_template, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightVnicTemplateReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                centered=True,
                vnic_template=vnic_template,
            )
        )

        if vnic_template.usnic_settings:
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string="\nusNIC Settings",
                    bolded=True,
                )
            )
            self.content_list.append(
                IntersightLanConnectivityPolicyVnicUsnicReportTable(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    centered=True,
                    vnic=vnic_template,
                )
            )

        if vnic_template.vmq_settings:
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string="\nVMQ Settings",
                    bolded=True,
                )
            )
            self.content_list.append(
                IntersightLanConnectivityPolicyVnicVmqReportTable(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    centered=True,
                    vnic=vnic_template,
                )
            )

        if vnic_template.sriov_settings:
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string="\nSRIOV Settings",
                    bolded=True,
                )
            )
            self.content_list.append(
                IntersightLanConnectivityPolicyVnicSriovReportTable(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    centered=True,
                    vnic=vnic_template,
                )
            )


class IntersightVnicTemplateReportTable(UcsReportTable):
    def __init__(self, order_id, parent, vnic_template, centered=False):

        rows = [
            ["Description", "Value"],
            ["Name", vnic_template.name],
            ["Description", vnic_template.descr],
            ["Organization", vnic_template._parent.name],
            ["CDN Source", vnic_template.cdn_source],
            ["CDN Value", vnic_template.cdn_value],
            ["Enable Failover", vnic_template.enable_failover],
            ["Enable Override", vnic_template.enable_override],
            ["Ethernet Adapter Policy", vnic_template.ethernet_adapter_policy],
            ["Ethernet Network Control Policy", vnic_template.ethernet_network_control_policy],
            ["Ethernet Network Group Policy", vnic_template.ethernet_network_group_policy],
            ["Ethernet QoS Policy", vnic_template.ethernet_qos_policy],
            ["iSCSI Boot Policy", vnic_template.iscsi_boot_policy],
            ["MAC Address Pool", vnic_template.mac_address_pool],
            ["Pin Group Name", vnic_template.pin_group_name],
            ["Switch ID", vnic_template.switch_id]

        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )