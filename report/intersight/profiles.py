
from report.content import GenericReportText
from report.ucs.section import UcsReportSection
from report.ucs.table import UcsReportTable


class IntersightProfilesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Profiles")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightUcsDomainProfilesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightUcsDomainProfileTemplatesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightUcsChassisProfilesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightChassisProfileTemplatesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightUcsServerProfilesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightUcsServerProfileTemplatesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightUnifiedEdgeProfilesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            IntersightUnifiedEdgeProfileTemplatesReportSection(order_id=self.report.get_current_order_id(), parent=self))


class IntersightUcsServerProfilesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("UCS Server Profiles")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        config = self.report.config
        server_profiles = []
        for org in config.orgs:
            self.parse_org(org, server_profiles, element_to_parse="ucs_server_profiles")

        if server_profiles:
            for profile in server_profiles:
                self.content_list.append(
                    IntersightUcsServerProfileReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        profile=profile,
                        title="UCS Server Profile " + profile.name,
                    )
                )
        else:
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=_("No UCS Server Profiles found."),
                    italicized=True,
                )
            )


class IntersightUcsServerProfileReportSection(UcsReportSection):
    def __init__(self, order_id, parent, profile, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        self.content_list.append(
            IntersightUcsServerProfileReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                profile=profile,
                centered=True,
            )
        )


class IntersightUcsServerProfileReportTable(UcsReportTable):
    def __init__(self, order_id, parent, profile, centered=False):
        rows = [
            [_("Description"), _("Value")],
            [_("Name"), profile.name],
            [_("Target Platform"), profile.target_platform],
            [_("UCS Server Profile Template"), getattr(profile, "ucs_server_profile_template", None) or _("N/A")],
            [_("UUID Pool"), profile.uuid_pool],
            [_("UUID Allocation Type"), getattr(profile, "uuid_allocation_type", None) or _("N/A")],
            [_("Adapter Configuration Policy"), profile.adapter_configuration_policy],
            [_("BIOS Policy"), profile.bios_policy],
            [_("Boot Policy"), profile.boot_policy],
            [_("Drive Security Policy"), profile.drive_security_policy],
            [_("Firmware Policy"), getattr(profile, "firmware_policy", None) or _("N/A")],
            [_("IMC Access Policy"), profile.imc_access_policy],
            [_("IPMI over LAN Policy"), profile.ipmi_over_lan_policy],
            [_("LAN Connectivity Policy"), profile.lan_connectivity_policy],
            [_("Local User Policy"), profile.local_user_policy],
            [_("Network Connectivity Policy"), profile.network_connectivity_policy],
            [_("NTP Policy"), profile.ntp_policy],
            [_("Power Policy"), profile.power_policy],
            [_("SAN Connectivity Policy"), profile.san_connectivity_policy],
            [_("SD Card Policy"), profile.sd_card_policy],
            [_("Serial over LAN Policy"), profile.serial_over_lan_policy],
            [_("SNMP Policy"), profile.snmp_policy],
            [_("Storage Policy"), profile.storage_policy],
            [_("Syslog Policy"), profile.syslog_policy],
            [_("Thermal Policy"), profile.thermal_policy],
            [_("Virtual KVM Policy"), profile.virtual_kvm_policy],
            [_("Virtual Media Policy"), profile.virtual_media_policy],
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


class IntersightUcsServerProfileTemplatesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("UCS Server Profile Templates")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        config = self.report.config
        templates = []
        for org in config.orgs:
            self.parse_org(org, templates, element_to_parse="ucs_server_profile_templates")

        if templates:
            for template in templates:
                self.content_list.append(
                    IntersightUcsServerProfileTemplateReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        template=template,
                        title="UCS Server Profile Template " + template.name,
                    )
                )
        else:
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=_("No UCS Server Profile Templates found."),
                    italicized=True,
                )
            )


class IntersightUcsServerProfileTemplateReportSection(UcsReportSection):
    def __init__(self, order_id, parent, template, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        self.content_list.append(
            IntersightUcsServerProfileTemplateReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                template=template,
                centered=True,
            )
        )


class IntersightUcsServerProfileTemplateReportTable(UcsReportTable):
    def __init__(self, order_id, parent, template, centered=False):
        rows = [
            [_("Description"), _("Value")],
            [_("Name"), template.name],
            [_("Target Platform"), template.target_platform],
            [_("UUID Pool"), template.uuid_pool],
            [_("Adapter Configuration Policy"), template.adapter_configuration_policy],
            [_("BIOS Policy"), template.bios_policy],
            [_("Boot Policy"), template.boot_policy],
            [_("Drive Security Policy"), template.drive_security_policy],
            [_("Firmware Policy"), getattr(template, "firmware_policy", None) or _("N/A")],
            [_("IMC Access Policy"), template.imc_access_policy],
            [_("IPMI over LAN Policy"), template.ipmi_over_lan_policy],
            [_("LAN Connectivity Policy"), template.lan_connectivity_policy],
            [_("Local User Policy"), template.local_user_policy],
            [_("Network Connectivity Policy"), template.network_connectivity_policy],
            [_("NTP Policy"), template.ntp_policy],
            [_("Power Policy"), template.power_policy],
            [_("SAN Connectivity Policy"), template.san_connectivity_policy],
            [_("SD Card Policy"), template.sd_card_policy],
            [_("Serial over LAN Policy"), template.serial_over_lan_policy],
            [_("SNMP Policy"), template.snmp_policy],
            [_("Storage Policy"), template.storage_policy],
            [_("Syslog Policy"), template.syslog_policy],
            [_("Thermal Policy"), template.thermal_policy],
            [_("Virtual KVM Policy"), template.virtual_kvm_policy],
            [_("Virtual Media Policy"), template.virtual_media_policy],
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


class IntersightUnifiedEdgeProfilesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Unified Edge Profiles")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        config = self.report.config
        unified_edge_profiles = []
        for org in config.orgs:
            self.parse_org(org, unified_edge_profiles, element_to_parse="unified_edge_profiles")

        if unified_edge_profiles:
            for profile in unified_edge_profiles:
                self.content_list.append(
                    IntersightUnifiedEdgeProfileReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        profile=profile,
                        title="Unified Edge Profile " + profile.name,
                    )
                )
        else:
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=_("No Unified Edge Profiles found."),
                    italicized=True,
                )
            )


class IntersightUnifiedEdgeProfileReportSection(UcsReportSection):
    def __init__(self, order_id, parent, profile, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        self.content_list.append(
            IntersightUnifiedEdgeProfileReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                profile=profile,
                centered=True,
            )
        )


class IntersightUnifiedEdgeProfileReportTable(UcsReportTable):
    def __init__(self, order_id, parent, profile, centered=False):
        rows = [
            [_("Description"), _("Value")],
            [_("Name"), profile.name],
            [_("Unified Edge Profile Template"), getattr(profile, "unified_edge_profile_template", None) or _("N/A")],
            [_("Local User Policy"), profile.local_user_policy],
            [_("Network Connectivity Policy"), profile.network_connectivity_policy],
            [_("NTP Policy"), profile.ntp_policy],
            [_("Port Policy - ECMC A"), (profile.port_policies or {}).get("ecmc_a")],
            [_("Port Policy - ECMC B"), (profile.port_policies or {}).get("ecmc_b")],
            [_("Power Policy"), profile.power_policy],
            [_("Switch Control Policy"), profile.switch_control_policy],
            [_("Syslog Policy"), profile.syslog_policy],
            [_("System QoS Policy"), profile.system_qos_policy],
            [_("Thermal Policy"), profile.thermal_policy],
            [_("VLAN Policy - ECMC A"), (profile.vlan_policies or {}).get("ecmc_a")],
            [_("VLAN Policy - ECMC B"), (profile.vlan_policies or {}).get("ecmc_b")],
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


class IntersightUnifiedEdgeProfileTemplatesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Unified Edge Profile Templates")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        config = self.report.config
        templates = []
        for org in config.orgs:
            self.parse_org(org, templates, element_to_parse="unified_edge_profile_templates")

        if templates:
            for template in templates:
                self.content_list.append(
                    IntersightUnifiedEdgeProfileTemplateReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        template=template,
                        title="Unified Edge Profile Template " + template.name,
                    )
                )
        else:
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=_("No Unified Edge Profile Templates found."),
                    italicized=True,
                )
            )


class IntersightUnifiedEdgeProfileTemplateReportSection(UcsReportSection):
    def __init__(self, order_id, parent, template, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        self.content_list.append(
            IntersightUnifiedEdgeProfileTemplateReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                template=template,
                centered=True,
            )
        )


class IntersightUnifiedEdgeProfileTemplateReportTable(UcsReportTable):
    def __init__(self, order_id, parent, template, centered=False):
        rows = [
            [_("Description"), _("Value")],
            [_("Name"), template.name],
            [_("Local User Policy"), template.local_user_policy],
            [_("Network Connectivity Policy"), template.network_connectivity_policy],
            [_("NTP Policy"), template.ntp_policy],
            [_("Port Policy - ECMC A"), (template.port_policies or {}).get("ecmc_a")],
            [_("Port Policy - ECMC B"), (template.port_policies or {}).get("ecmc_b")],
            [_("Power Policy"), template.power_policy],
            [_("Switch Control Policy"), template.switch_control_policy],
            [_("Syslog Policy"), template.syslog_policy],
            [_("System QoS Policy"), template.system_qos_policy],
            [_("Thermal Policy"), template.thermal_policy],
            [_("VLAN Policy - ECMC A"), (template.vlan_policies or {}).get("ecmc_a")],
            [_("VLAN Policy - ECMC B"), (template.vlan_policies or {}).get("ecmc_b")],
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


class IntersightUcsDomainProfilesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("UCS Domain Profile")

        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config
        ucs_domain_profiles_list = []
        # Searching for all UCS Domain Profiles
        for org in config.orgs:
            self.parse_org(org, ucs_domain_profiles_list, element_to_parse="ucs_domain_profiles")

        if ucs_domain_profiles_list:
            for ucs_domain_profile in ucs_domain_profiles_list:
                self.content_list.append(
                    IntersightUcsDomainProfileReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        ucs_domain_profile=ucs_domain_profile,
                        title="UCS Domain Profile " + ucs_domain_profile.name,
                    )
                )
        else:
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=_("No UCS Domain Profiles found."),
                    italicized=True,
                )
            )


class IntersightUcsDomainProfileReportSection(UcsReportSection):
    def __init__(self, order_id, parent, ucs_domain_profile, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        self.content_list.append(
            IntersightUcsDomainProfileReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                ucs_domain_profile=ucs_domain_profile,
                centered=True,
            )
        )


class IntersightUcsDomainProfileReportTable(UcsReportTable):
    def __init__(self, order_id, parent, ucs_domain_profile, centered=False):
        rows = [
            [_("Description"), _("Value")],
            [_("Name"), ucs_domain_profile.name],
            [_("AuditD Policy"), ucs_domain_profile.auditd_policy],
            [_("LDAP Policy"), ucs_domain_profile.ldap_policy],
            [_("Network Connectivity Policy"), ucs_domain_profile.network_connectivity_policy],
            [_("NTP Policy"), ucs_domain_profile.ntp_policy],
            [_("Switch Control Policy"), ucs_domain_profile.switch_control_policy],
            [_("SNMP Policy"), ucs_domain_profile.snmp_policy],
            [_("Syslog Policy"), ucs_domain_profile.syslog_policy],
            [_("System QoS Policy"), ucs_domain_profile.system_qos_policy],
            [_("Port Policy - Fabric A"), (ucs_domain_profile.port_policies or {}).get("fabric_a")],
            [_("Port Policy - Fabric B"), (ucs_domain_profile.port_policies or {}).get("fabric_b")],
            [_("VLAN Policy - Fabric A"), (ucs_domain_profile.vlan_policies or {}).get("fabric_a")],
            [_("VLAN Policy - Fabric B"), (ucs_domain_profile.vlan_policies or {}).get("fabric_b")],
            [_("VSAN Policy - Fabric A"), (ucs_domain_profile.vsan_policies or {}).get("fabric_a")],
            [_("VSAN Policy - Fabric B"), (ucs_domain_profile.vsan_policies or {}).get("fabric_b")],
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


class IntersightChassisProfileTemplatesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("UCS Chassis Profile Template")

        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config
        chassis_profile_templates_list = []
        # Searching for all UCS Chassis Profile Templates
        for org in config.orgs:
            self.parse_org(org, chassis_profile_templates_list,
                           element_to_parse="ucs_chassis_profile_templates")

        if chassis_profile_templates_list:
            for ucs_chassis_profile_template in chassis_profile_templates_list:
                self.content_list.append(
                    IntersightChassisProfileTemplateReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        ucs_chassis_profile_template=ucs_chassis_profile_template,
                        title="UCS Chassis Profile Template " + ucs_chassis_profile_template.name,
                    )
                )
        else:
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=_("No UCS Chassis Profile Templates found."),
                    italicized=True,
                )
            )


class IntersightChassisProfileTemplateReportSection(UcsReportSection):
    def __init__(self, order_id, parent, ucs_chassis_profile_template, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        self.content_list.append(
            IntersightChassisProfileTemplateReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                ucs_chassis_profile_template=ucs_chassis_profile_template,
                centered=True,
            )
        )


class IntersightChassisProfileTemplateReportTable(UcsReportTable):
    def __init__(self, order_id, parent, ucs_chassis_profile_template, centered=False):
        rows = [
            [_("Description"), _("Value")],
            [_("Name"), ucs_chassis_profile_template.name],
            [_("Power Policy"), ucs_chassis_profile_template.power_policy],
            [_("Thermal Policy"), ucs_chassis_profile_template.thermal_policy],
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


class IntersightUcsDomainProfileTemplatesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("UCS Domain Profile Templates")

        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config
        ucs_domain_profile_templates_list = []
        # Searching for all UCS Domain Profile Templates
        for org in config.orgs:
            self.parse_org(org, ucs_domain_profile_templates_list,
                           element_to_parse="ucs_domain_profile_templates")

        if ucs_domain_profile_templates_list:
            for ucs_domain_profile_template in ucs_domain_profile_templates_list:
                self.content_list.append(
                    IntersightUcsDomainProfileTemplateReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        ucs_domain_profile_template=ucs_domain_profile_template,
                        title="UCS Domain Profile Template " + ucs_domain_profile_template.name,
                    )
                )
        else:
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=_("No UCS Domain Profile Templates found."),
                    italicized=True,
                )
            )


class IntersightUcsDomainProfileTemplateReportSection(UcsReportSection):
    def __init__(self, order_id, parent, ucs_domain_profile_template, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        self.content_list.append(
            IntersightUcsDomainProfileTemplateReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                ucs_domain_profile_template=ucs_domain_profile_template,
                centered=True,
            )
        )


class IntersightUcsDomainProfileTemplateReportTable(UcsReportTable):
    def __init__(self, order_id, parent, ucs_domain_profile_template, centered=False):
        rows = [
            [_("Description"), _("Value")],
            [_("Name"), ucs_domain_profile_template.name],
            [_("AuditD Policy"), ucs_domain_profile_template.auditd_policy],
            [_("LDAP Policy"), ucs_domain_profile_template.ldap_policy],
            [_("Netflow Configuration Policy"), ucs_domain_profile_template.netflow_configuration_policy],
            [_("Network Connectivity Policy"), ucs_domain_profile_template.network_connectivity_policy],
            [_("NTP Policy"), ucs_domain_profile_template.ntp_policy],
            [_("Switch Control Policy"), ucs_domain_profile_template.switch_control_policy],
            [_("SNMP Policy"), ucs_domain_profile_template.snmp_policy],
            [_("Syslog Policy"), ucs_domain_profile_template.syslog_policy],
            [_("System QoS Policy"), ucs_domain_profile_template.system_qos_policy],
            [_("Port Policy - Fabric A"), (ucs_domain_profile_template.port_policies or {}).get("fabric_a")],
            [_("Port Policy - Fabric B"), (ucs_domain_profile_template.port_policies or {}).get("fabric_b")],
            [_("VLAN Policy - Fabric A"), (ucs_domain_profile_template.vlan_policies or {}).get("fabric_a")],
            [_("VLAN Policy - Fabric B"), (ucs_domain_profile_template.vlan_policies or {}).get("fabric_b")],
            [_("VSAN Policy - Fabric A"), (ucs_domain_profile_template.vsan_policies or {}).get("fabric_a")],
            [_("VSAN Policy - Fabric B"), (ucs_domain_profile_template.vsan_policies or {}).get("fabric_b")],
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


class IntersightUcsChassisProfilesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("UCS Chassis Profiles")

        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config
        ucs_chassis_profiles_list = []
        # Searching for all UCS Chassis Profiles
        for org in config.orgs:
            self.parse_org(org, ucs_chassis_profiles_list, element_to_parse="ucs_chassis_profiles")

        if ucs_chassis_profiles_list:
            for ucs_chassis_profile in ucs_chassis_profiles_list:
                self.content_list.append(
                    IntersightUcsChassisProfileReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        ucs_chassis_profile=ucs_chassis_profile,
                        title="UCS Chassis Profile " + ucs_chassis_profile.name,
                    )
                )
        else:
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=_("No UCS Chassis Profiles found."),
                    italicized=True,
                )
            )


class IntersightUcsChassisProfileReportSection(UcsReportSection):
    def __init__(self, order_id, parent, ucs_chassis_profile, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        self.content_list.append(
            IntersightUcsChassisProfileReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                ucs_chassis_profile=ucs_chassis_profile,
                centered=True,
            )
        )


class IntersightUcsChassisProfileReportTable(UcsReportTable):
    def __init__(self, order_id, parent, ucs_chassis_profile, centered=False):
        rows = [
            [_("Description"), _("Value")],
            [_("Name"), ucs_chassis_profile.name],
            [_("UCS Chassis Profile Template"),
             getattr(ucs_chassis_profile, "ucs_chassis_profile_template", None) or _("N/A")],
            [_("IMC Access Policy"), ucs_chassis_profile.imc_access_policy],
            [_("Power Policy"), ucs_chassis_profile.power_policy],
            [_("SNMP Policy"), ucs_chassis_profile.snmp_policy],
            [_("Thermal Policy"), ucs_chassis_profile.thermal_policy],
            [_("Pre-assigned Chassis Serial Number"), ucs_chassis_profile.chassis_pre_assign_by_serial],
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
