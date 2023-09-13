# coding: utf-8
# !/usr/bin/env python

""" policies.py: Easy UCS Deployment Tool """

from common import read_json_file
from report.content import *
from report.ucs.section import UcsReportSection
from report.ucs.table import UcsReportTable


class UcsSystemPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Policies")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            UcsSystemServerPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))


class UcsSystemServerPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Server Policies")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            UcsSystemBiosPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            UcsSystemBootPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            UcsSystemGraphicsCardPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            UcsSystemLocalDiskConfigPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            UcsSystemMaintenancePoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            UcsSystemScrubPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))
        self.content_list.append(
            UcsSystemVmediaPoliciesReportSection(order_id=self.report.get_current_order_id(), parent=self))


class UcsSystemBiosPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("BIOS Policies")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        text = _("Tokens with 'Platform-Default' values are not displayed below for easier readability.")
        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self, string=text, italicized=True))

        bios_policies_list = []
        # Searching for all BIOS Policies
        for org in self.report.config.orgs:
            self.parse_org(org, bios_policies_list, element_to_parse="bios_policies")

        if bios_policies_list:
            for bios_policy in bios_policies_list:
                self.content_list.append(
                    UcsSystemBiosPolicyReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                     bios_policy=bios_policy,
                                                     title=_("BIOS Policy ") + bios_policy.name))


class UcsSystemBiosPolicyReportSection(UcsReportSection):
    def __init__(self, order_id, parent, bios_policy, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            UcsSystemBiosPolicyReportTable(order_id=self.report.get_current_order_id(), parent=self, centered=True,
                                           bios_policy=bios_policy))


class UcsSystemBiosPolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, bios_policy, centered=False):

        rows = [[_("Description"), _("Value")],
                [_("Name"), bios_policy.name],
                [_("Description"), bios_policy.descr],
                [_("Organization"), bios_policy._parent._dn],
                [_("Policy Owner"), bios_policy.policy_owner]]

        bios_table = read_json_file(file_path="config/ucs/ucsm/bios_table.json", logger=self)
        if not bios_table:
            self.logger(level="error", message="BIOS Table not imported.")
        if bios_table:
            for attr in sorted(bios_table, key=lambda x: bios_table[x]["param_name"], reverse=False):
                if getattr(bios_policy, attr) not in ["platform-default", "Platform Default"]:
                    rows.append([bios_table[attr]["param_name"], getattr(bios_policy, attr)])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows)


class UcsSystemBootPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Boot Policies")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        boot_policies_list = []
        # Searching for all Boot Policies
        for org in self.report.config.orgs:
            self.parse_org(org, boot_policies_list, element_to_parse="boot_policies")

        if boot_policies_list:
            for boot_policy in boot_policies_list:
                self.content_list.append(
                    UcsSystemBootPolicyReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                     boot_policy=boot_policy,
                                                     title=_("Boot Policy ") + boot_policy.name))


class UcsSystemBootPolicyReportSection(UcsReportSection):
    def __init__(self, order_id, parent, boot_policy, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            UcsSystemBootPolicyReportTable(order_id=self.report.get_current_order_id(), parent=self, centered=True,
                                           boot_policy=boot_policy))

        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self, string=_("\nBoot Order: "),
                              bolded=True))

        if boot_policy.boot_order:
            self.content_list.append(
                UcsSystemBootOrderReportTable(order_id=self.report.get_current_order_id(), parent=self, centered=True,
                                              boot_policy=boot_policy))


class UcsSystemBootPolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, boot_policy, centered=False):

        rows = [[_("Description"), _("Value")],
                [_("Name"), boot_policy.name],
                [_("Description"), boot_policy.descr],
                [_("Organization"), boot_policy._parent._dn],
                [_("Reboot on Boot Order Change"), boot_policy.reboot_on_boot_order_change],
                [_("Enforce vNIC/vHBA/iSCSI Name"), boot_policy.enforce_vnic_name],
                [_("Boot Mode"), boot_policy.boot_mode],
                [_("Boot Security"), boot_policy.boot_security]]

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows)


class UcsSystemBootOrderReportTable(UcsReportTable):
    def __init__(self, order_id, parent, boot_policy, centered=False):

        rows = [[_("Order"), _("Device Type"), _("vNIC/vHBA Name"), _("vNIC/vHBA Type"), _("IP Address Type"),
                 _("LUN"), _("Target WWPN"), _("Type"), _("Slot Number"), _("Boot Loader Name"),
                 _("Boot Loader Path"), _("Boot Loader Description")]]

        for boot_item in sorted(boot_policy.boot_order, key=lambda x: x["order"], reverse=False):
            if "vnic" in boot_item:
                if boot_item["vnics"]:
                    for vnic in boot_item["vnics"]:
                        rows.append([boot_item["order"], boot_item["device_type"], vnic["name"], vnic["type"],
                                     vnic["ip_address_type"], None, None, None, None, None, None, None])
                    continue
            if "iscsi_vnics" in boot_item:
                if boot_item["iscsi_vnics"]:
                    for iscsi_vnic in boot_item["iscsi_vnics"]:
                        rows.append([boot_item["order"], boot_item["device_type"], iscsi_vnic["name"],
                                     iscsi_vnic["type"], None, None, None, None, None, iscsi_vnic["boot_loader_name"],
                                     iscsi_vnic["boot_loader_path"], iscsi_vnic["boot_loader_description"]])
                    continue
            if "vhbas" in boot_item:
                if boot_item["vhbas"]:
                    for vhba in boot_item["vhbas"]:
                        if "targets" in vhba:
                            if vhba["targets"]:
                                for target in vhba["targets"]:
                                    rows.append(
                                        [boot_item["order"], boot_item["device_type"], vhba["name"], vhba["type"], None,
                                         target["lun"], target["wwpn"], target["type"], None,
                                         target["boot_loader_name"], target["boot_loader_path"],
                                         target["boot_loader_description"]])
                            else:
                                rows.append([boot_item["order"], boot_item["device_type"], vhba["name"], vhba["type"],
                                             None, None, None, None, None, None, None, None])
                    continue
            if "embedded_local_disks" in boot_item:
                if boot_item["embedded_local_disks"]:
                    for embedded_local_disk in boot_item["embedded_local_disks"]:
                        rows.append([boot_item["order"], boot_item["device_type"], None, None, None, None, None,
                                     embedded_local_disk["type"], embedded_local_disk["slot_number"],
                                     embedded_local_disk["boot_loader_name"], embedded_local_disk["boot_loader_path"],
                                     embedded_local_disk["boot_loader_description"]])
                    continue
            if "local_luns" in boot_item:
                if boot_item["local_luns"]:
                    for local_lun in boot_item["local_luns"]:
                        rows.append([boot_item["order"], boot_item["device_type"], None, None, None, local_lun["name"],
                                     None, local_lun["type"], None, local_lun["boot_loader_name"],
                                     local_lun["boot_loader_path"], local_lun["boot_loader_description"]])
                    continue
            if "local_jbods" in boot_item:
                if boot_item["local_jbods"]:
                    for local_jbod in boot_item["local_jbods"]:
                        rows.append([boot_item["order"], boot_item["device_type"], None, None, None, None, None, None,
                                     local_jbod["slot_number"], None, None, None])
                    continue
            if "embedded_local_luns" in boot_item:
                if boot_item["embedded_local_luns"]:
                    for embedded_local_lun in boot_item["embedded_local_luns"]:
                        rows.append([boot_item["order"], boot_item["device_type"], None, None, None, None, None, None,
                                     None, embedded_local_lun["boot_loader_name"],
                                     embedded_local_lun["boot_loader_path"],
                                     embedded_local_lun["boot_loader_description"]])
                    continue
            rows.append([boot_item["order"], boot_item["device_type"], None, None, None, None, None, None, None, None,
                         None, None])

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows, font_size=8)


class UcsSystemGraphicsCardPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Graphics Card Policies")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        graphics_card_policies_list = []
        # Searching for all Graphics Card Policies
        for org in self.report.config.orgs:
            self.parse_org(org, graphics_card_policies_list, element_to_parse="graphics_card_policies")

        if graphics_card_policies_list:
            for graphics_card_policy in graphics_card_policies_list:
                self.content_list.append(
                    UcsSystemGraphicsCardPolicyReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                             graphics_card_policy=graphics_card_policy,
                                                             title=_("Graphics Card Policy ") +
                                                                   graphics_card_policy.name))


class UcsSystemGraphicsCardPolicyReportSection(UcsReportSection):
    def __init__(self, order_id, parent, graphics_card_policy, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            UcsSystemGraphicsCardPolicyReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                                   centered=True, graphics_card_policy=graphics_card_policy))


class UcsSystemGraphicsCardPolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, graphics_card_policy, centered=False):

        rows = [[_("Description"), _("Value")],
                [_("Name"), graphics_card_policy.name],
                [_("Description"), graphics_card_policy.descr],
                [_("Organization"), graphics_card_policy._parent._dn],
                [_("Policy Owner"), graphics_card_policy.policy_owner],
                [_("Graphics Card Mode"), graphics_card_policy.graphics_card_mode]]

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows)


class UcsSystemLocalDiskConfigPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Local Disk Configuration Policies")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        local_disk_config_policies = []
        # Searching for all Local Disk Config Policies
        for org in self.report.config.orgs:
            self.parse_org(org, local_disk_config_policies, element_to_parse="local_disk_config_policies")

        if local_disk_config_policies:
            for local_disk_config_policy in local_disk_config_policies:
                self.content_list.append(
                    UcsSystemLocalDiskConfigPolicyReportSection(order_id=self.report.get_current_order_id(),
                                                                parent=self,
                                                                local_disk_config_policy=local_disk_config_policy,
                                                                title=_("Local Disk Config Policy ") +
                                                                      local_disk_config_policy.name))


class UcsSystemLocalDiskConfigPolicyReportSection(UcsReportSection):
    def __init__(self, order_id, parent, local_disk_config_policy, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            UcsSystemLocalDiskConfigPolicyReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                                      centered=True, local_disk_config_policy=local_disk_config_policy))


class UcsSystemLocalDiskConfigPolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, local_disk_config_policy, centered=False):

        mode = local_disk_config_policy.mode
        if mode == "raid-striped":
            mode += " (RAID 0)"
        elif mode == "raid-mirrored":
            mode += " (RAID 1)"
        elif mode == "raid-striped-parity":
            mode += " (RAID 5)"
        elif mode == "raid-striped-dual-parity":
            mode += " (RAID 6)"
        elif mode == "raid-mirrored-striped":
            mode += " (RAID 10)"
        elif mode == "raid-striped-parity-striped":
            mode += " (RAID 50)"
        elif mode == "raid-striped-dual-parity-striped":
            mode += " (RAID 60)"

        rows = [[_("Description"), _("Value")],
                [_("Name"), local_disk_config_policy.name],
                [_("Description"), local_disk_config_policy.descr],
                [_("Organization"), local_disk_config_policy._parent._dn],
                [_("Policy Owner"), local_disk_config_policy.policy_owner],
                [_("Mode"), mode],
                [_("Protect Configuration"), local_disk_config_policy.protect_configuration],
                [_("FlexFlash State"), local_disk_config_policy.flexflash_state],
                [_("FlexFlash RAID Reporting State"), local_disk_config_policy.flexflash_raid_reporting_state],
                [_("FlexFlash Removable State"), local_disk_config_policy.flexflash_removable_state]]

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows)


class UcsSystemMaintenancePoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Maintenance Policies")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        maintenance_policies_list = []
        # Searching for all Maintenance Policies
        for org in self.report.config.orgs:
            self.parse_org(org, maintenance_policies_list, element_to_parse="maintenance_policies")

        if maintenance_policies_list:
            for maintenance_policy in maintenance_policies_list:
                self.content_list.append(
                    UcsSystemMaintenancePolicyReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                            maintenance_policy=maintenance_policy,
                                                            title=_("Maintenance Policy ") + maintenance_policy.name))


class UcsSystemMaintenancePolicyReportSection(UcsReportSection):
    def __init__(self, order_id, parent, maintenance_policy, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            UcsSystemMaintenancePolicyReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                                  centered=True, maintenance_policy=maintenance_policy))


class UcsSystemMaintenancePolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, maintenance_policy, centered=False):

        soft_shutdown_timer = maintenance_policy.soft_shutdown_timer
        if soft_shutdown_timer not in [None, "never"]:
            soft_shutdown_timer += " seconds"

        rows = [[_("Description"), _("Value")],
                [_("Name"), maintenance_policy.name],
                [_("Description"), maintenance_policy.descr],
                [_("Organization"), maintenance_policy._parent._dn],
                [_("Policy Owner"), maintenance_policy.policy_owner],
                [_("Reboot Policy"), maintenance_policy.reboot_policy],
                [_("Soft Shutdown Timer"), soft_shutdown_timer],
                [_("Storage Config. Deployment Policy"), maintenance_policy.storage_config_deployment_policy],
                [_("On Next Boot"), maintenance_policy.on_next_boot],
                [_("Schedule"), maintenance_policy.schedule]]

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows)


class UcsSystemScrubPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("Scrub Policies")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        scrub_policies_list = []
        # Searching for all Scrub Policies
        for org in self.report.config.orgs:
            self.parse_org(org, scrub_policies_list, element_to_parse="scrub_policies")

        if scrub_policies_list:
            for scrub_policy in scrub_policies_list:
                self.content_list.append(
                    UcsSystemScrubPolicyReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                      scrub_policy=scrub_policy,
                                                      title=_("Scrub Policy ") + scrub_policy.name))


class UcsSystemScrubPolicyReportSection(UcsReportSection):
    def __init__(self, order_id, parent, scrub_policy, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            UcsSystemScrubPolicyReportTable(order_id=self.report.get_current_order_id(), parent=self, centered=True,
                                            scrub_policy=scrub_policy))


class UcsSystemScrubPolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, scrub_policy, centered=False):

        rows = [[_("Description"), _("Value")],
                [_("Name"), scrub_policy.name],
                [_("Description"), scrub_policy.descr],
                [_("Organization"), scrub_policy._parent._dn],
                [_("Policy Owner"), scrub_policy.policy_owner],
                [_("Disk Scrub"), scrub_policy.disk_scrub],
                [_("FlexFlash Scrub"), scrub_policy.flexflash_scrub],
                [_("BIOS Settings Scrub"), scrub_policy.bios_settings_scrub],
                [_("Persistent Memory Scrub"), scrub_policy.persistent_memory_scrub]]

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows)


class UcsSystemVmediaPoliciesReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title=""):
        if not title:
            title = _("vMedia Policies")
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        vmedia_policies_list = []
        # Searching for all vMedia Policies
        for org in self.report.config.orgs:
            self.parse_org(org, vmedia_policies_list, element_to_parse="vmedia_policies")

        if vmedia_policies_list:
            for vmedia_policy in vmedia_policies_list:
                self.content_list.append(
                    UcsSystemVmediaPolicyReportSection(order_id=self.report.get_current_order_id(), parent=self,
                                                       vmedia_policy=vmedia_policy,
                                                       title=_("vMedia Policy ") + vmedia_policy.name))


class UcsSystemVmediaPolicyReportSection(UcsReportSection):
    def __init__(self, order_id, parent, vmedia_policy, title=""):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            UcsSystemVmediaPolicyReportTable(order_id=self.report.get_current_order_id(), parent=self, centered=True,
                                             vmedia_policy=vmedia_policy))

        self.content_list.append(
            GenericReportText(order_id=self.report.get_current_order_id(), parent=self, string=_("\nvMedia Mounts: "),
                              bolded=True))

        for vmedia_mount in sorted(vmedia_policy.vmedia_mounts, key=lambda x: x["name"], reverse=False):
            self.content_list.append(
                UcsSystemVmediaMountReportTable(order_id=self.report.get_current_order_id(), parent=self,
                                                centered=True, vmedia_mount=vmedia_mount))


class UcsSystemVmediaPolicyReportTable(UcsReportTable):
    def __init__(self, order_id, parent, vmedia_policy, centered=False):

        rows = [[_("Description"), _("Value")],
                [_("Name"), vmedia_policy.name],
                [_("Description"), vmedia_policy.descr],
                [_("Organization"), vmedia_policy._parent._dn],
                [_("Policy Owner"), vmedia_policy.policy_owner],
                [_("Retry on Mount Fail"), vmedia_policy.retry_on_mount_fail]]

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows)


class UcsSystemVmediaMountReportTable(UcsReportTable):
    def __init__(self, order_id, parent, vmedia_mount, centered=False):

        rows = [[_("Description"), _("Value")],
                [_("Name"), vmedia_mount["name"]],
                [_("Description"), vmedia_mount["descr"]],
                [_("Device Type"), vmedia_mount["device_type"]],
                [_("Protocol"), vmedia_mount["protocol"]],
                [_("Authentication Protocol"), vmedia_mount["authentication_protocol"]],
                [_("Hostname"), vmedia_mount["hostname"]],
                [_("Image Name Variable"), vmedia_mount["image_name_variable"]],
                [_("Remote File"), vmedia_mount["remote_file"]],
                [_("Remote Path"), vmedia_mount["remote_path"]],
                [_("Username"), vmedia_mount["username"]],
                [_("Password"), vmedia_mount["password"]],
                [_("Remap on Eject"), vmedia_mount["remap_on_eject"]],
                [_("Writable"), vmedia_mount["writable"]]]

        UcsReportTable.__init__(self, order_id=order_id, parent=parent, row_number=len(rows),
                                column_number=len(rows[1]), centered=centered, cells_list=rows)
