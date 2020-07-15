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
