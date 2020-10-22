# coding: utf-8
# !/usr/bin/env python

""" overview.py: Easy UCS Deployment Tool """

from report.content import *
from report.ucs.section import UcsReportSection
from report.ucs.table import UcsReportTable


class UcsSystemOverviewReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("UCS System Overview")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            UcsSystemClusterInfoReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                            config=self.report.config, device=self.report.device, centered=True))

        if self.report.inventory.device_connector:
            self.content_list.append(
                UcsIntersightReportSection(order_id=self.report.get_current_order_id(), parent=self))

        self.content_list.append(
            UcsSystemCommServicesReportSection(order_id=self.report.get_current_order_id(), parent=self))


class UcsSystemClusterInfoReportTable(UcsReportTable):
    def __init__(self, order_id, parent, config, device, centered=False):
        config_system = config.system[0]
        config_mng_int = config.management_interfaces[0]

        rows = [[_("Description"), _("Value")], [_("System Name"), config_system.name],
                [_("Version"), config.device_version], [_("Cluster IP Address"), config_system.virtual_ip],
                [_("Netmask"), config_mng_int.netmask], [_("Gateway"), config_mng_int.gateway]]
        # Cluster info
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
            rows.append([_("Link to UCS Central"), _("Registered to ") + config.ucs_central[0].ip_address])
        else:
            rows.append([_("Link to UCS Central"), "off"])
        rows.append([_("Intersight Claim Status"), config.intersight_status])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[0]), centered=centered, cells_list=rows)


class UcsSystemCommServicesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Communication Services")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            UcsSystemCommServicesReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                             config=self.report.config, device=self.report.device, centered=True))


class UcsSystemCommServicesReportTable(UcsReportTable):
    def __init__(self, order_id, parent, config, device, centered=False):
        communication_services = config.communication_services[0]

        rows = [[_("Service"), _("State")], [_("HTTP"), communication_services.http_service[0]["state"]],
                [_("Redirect to HTTPS"), communication_services.http_service[0]["redirect_to_https"]],
                [_("HTTPS"), communication_services.https_service[0]["state"]],
                [_("SNMP"), communication_services.snmp_service[0]["state"]],
                [_("CIMC"), communication_services.cimc_web_service], [_("SSH"), communication_services.ssh_service],
                [_("Telnet"), communication_services.telnet_service]]
        # Cluster info

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[0]), centered=centered, cells_list=rows, autofit=True)


class UcsIntersightReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Intersight Device Connector")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            UcsIntersightReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                     inventory=self.report.inventory, device=self.report.device, centered=True))


class UcsIntersightReportTable(UcsReportTable):
    def __init__(self, order_id, parent, inventory, device, centered=False):
        device_connector = inventory.device_connector[0]

        rows = [[_("Description"), _("Value")], [_("Claim Status"), device_connector.ownership],
                [_("Intersight URL"), device_connector.intersight_url],
                [_("Account Name"), device_connector.ownership_name],
                [_("Claimed By"), device_connector.ownership_user],
                [_("Device ID"), device_connector.device_id], [_("Device Connector Version"), device_connector.version]]

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[0]), centered=centered, cells_list=rows)


class UcsImcOverviewReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("UCS IMC Overview")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            UcsImcInfoReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                  config=self.report.config, device=self.report.device, centered=True))

        if self.report.inventory.device_connector:
            self.content_list.append(
                UcsIntersightReportSection(order_id=self.report.get_current_order_id(), parent=self))


class UcsImcInfoReportTable(UcsReportTable):
    def __init__(self, order_id, parent, config, device, centered=False):
        config_admin_networking = config.admin_networking[0]

        rows = [[_("Description"), _("Value")], [_("System Name"), config_admin_networking.management_hostname],
                [_("Version"), config.device_version],
                [_("IP Address"), config_admin_networking.management_ipv4_address],
                [_("Netmask"), config_admin_networking.management_subnet_mask],
                [_("Gateway"), config_admin_networking.gateway_ipv4],
                [_("NIC Mode"), config_admin_networking.nic_mode]]
        # Server info
        if config.server_properties:
            rows.append([_("Asset Tag"), config.server_properties[0].asset_tag])
        rows.append([_("Intersight Claim Status"), config.intersight_status])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[0]), centered=centered, cells_list=rows)
