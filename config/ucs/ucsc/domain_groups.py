# coding: utf-8
# !/usr/bin/env python

""" domain_groups.py: Easy UCS Central Domain Groups objects """
from __init__ import __author__, __copyright__, __version__, __status__

import copy
import hashlib

from config.ucs.object import GenericUcsConfigObject, UcsCentralConfigObject
from config.ucs.ucsc.orgs import UcsCentralIpPool
from config.ucs.ucsc.system import UcsCentralDateTimeMgmt, UcsCentralDns, UcsCentralLocale, UcsCentralRole, \
    UcsCentralSnmp, UcsCentralSyslog

import common

from ucscsdk.mometa.comm.CommCimxml import CommCimxml
from ucscsdk.mometa.comm.CommHttp import CommHttp
from ucscsdk.mometa.comm.CommShellSvcLimits import CommShellSvcLimits
from ucscsdk.mometa.comm.CommTelnet import CommTelnet
from ucscsdk.mometa.comm.CommWebSvcLimits import CommWebSvcLimits
from ucscsdk.mometa.compute.ComputeChassisDiscPolicy import ComputeChassisDiscPolicy
from ucscsdk.mometa.compute.ComputeGroupMembership import ComputeGroupMembership
from ucscsdk.mometa.compute.ComputePsuPolicy import ComputePsuPolicy
from ucscsdk.mometa.compute.ComputeServerDiscPolicy import ComputeServerDiscPolicy
from ucscsdk.mometa.compute.ComputeServerMgmtPolicy import ComputeServerMgmtPolicy
from ucscsdk.mometa.fabric.FabricLanCloudPolicy import FabricLanCloudPolicy
from ucscsdk.mometa.fabric.FabricNetGroup import FabricNetGroup
from ucscsdk.mometa.fabric.FabricNetGroupReq import FabricNetGroupReq
from ucscsdk.mometa.fabric.FabricPooledVlan import FabricPooledVlan
from ucscsdk.mometa.fabric.FabricVlan import FabricVlan
from ucscsdk.mometa.fabric.FabricVlanReq import FabricVlanReq
from ucscsdk.mometa.fabric.FabricVsan import FabricVsan
from ucscsdk.mometa.firmware.FirmwareAutoSyncPolicy import FirmwareAutoSyncPolicy
from ucscsdk.mometa.org.OrgDomainGroup import OrgDomainGroup
from ucscsdk.mometa.org.OrgDomainGroupPolicy import OrgDomainGroupPolicy
from ucscsdk.mometa.power.PowerMgmtPolicy import PowerMgmtPolicy
from ucscsdk.mometa.top.TopInfoSyncPolicy import TopInfoSyncPolicy

from ucscsdk.ucscexception import UcscException


class UcsCentralDomainGroup(UcsCentralConfigObject):
    _CONFIG_NAME = "Domain Group"
    _UCS_SDK_OBJECT_NAME = "orgDomainGroup"

    def __init__(self, parent=None, json_content=None, org_domain_group=None):
        UcsCentralConfigObject.__init__(self, parent=parent)
        self.descr = None
        self.domains = []
        self.name = None
        self.qualification_policies = []

        if self._config.load_from == "live":
            if org_domain_group is not None:
                self._dn = org_domain_group.dn
                self.name = org_domain_group.name
                self.descr = org_domain_group.descr

                if "orgDomainGroupPolicy" in self._config.sdk_objects:
                    for org_domain_group_policy in self._config.sdk_objects["orgDomainGroupPolicy"]:
                        if self._dn in org_domain_group_policy.group_dn:
                            self.qualification_policies.append(org_domain_group_policy.qualifier)

                if "computeGroupMembership" in self._config.sdk_objects:
                    for compute_group_membership in self._config.sdk_objects["computeGroupMembership"]:
                        if self._dn in compute_group_membership.group_dn:
                            self.domains.append(compute_group_membership.ip)

        elif self._config.load_from == "file":
            if json_content is not None:
                if self.get_attributes_from_json(json_content=json_content):
                    if hasattr(self._parent, '_dn'):
                        self._dn = self._parent._dn + "/domaingroup-" + str(self.name)
                    else:
                        self._dn = "domaingroup-" + str(self.name)
                else:
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.date_time = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralDateTimeMgmt,
                                      name_to_fetch="date_time")
        self.dns = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralDns,
                                      name_to_fetch="dns")
        self.remote_access = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralDomainGroupRemoteAccess,
                                      name_to_fetch="remote_access")
        self.equipment_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralDomainGroupEquipmentPolicies,
                                      name_to_fetch="equipment_policies")
        self.syslog = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralSyslog,
                                      name_to_fetch="syslog")
        self.snmp = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralSnmp,
                                      name_to_fetch="snmp")
        self.locales = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralLocale,
                                      name_to_fetch="locales")
        self.roles = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralRole,
                                      name_to_fetch="roles")
        self.domain_groups = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralDomainGroup,
                                      name_to_fetch="domain_groups")
        self.vlans = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralVlan,
                                      name_to_fetch="vlans")
        self.appliance_vlans = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralApplianceVlan,
                                      name_to_fetch="appliance_vlans")
        self.vlan_groups = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralVlanGroup,
                                      name_to_fetch="vlan_groups")
        self.ip_pools = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralIpPool,
                                      name_to_fetch="ip_pools")
        self.vsans = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralVsan,
                                      name_to_fetch="vsans")

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + str(self.name))
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + str(self.name) +
                                ", waiting for a commit")

        parent_mo = ""
        if hasattr(self._parent, '_dn'):
            parent_mo = self._parent._dn

        mo_org_domain_group = OrgDomainGroup(parent_mo_or_dn=parent_mo, name=self.name, descr=self.descr)
        self._handle.add_mo(mo=mo_org_domain_group, modify_present=True)

        if self.qualification_policies:
            for qual_policy in self.qualification_policies:
                # We use a MD5 hashing function for the name of the OrgDomainGroupPolicy object,
                # since Central automatically generates a numerical ID when doing the action from the GUI.
                mo_org_domain_group_policy = \
                    OrgDomainGroupPolicy(parent_mo_or_dn="org-root",
                                         name="easyucs-" + hashlib.md5(self._dn.encode()).hexdigest()[:8],
                                         descr="Domain Group policy is created by EasyUCS",
                                         qualifier=qual_policy, group_dn=self._dn)
                self._handle.add_mo(mo=mo_org_domain_group_policy, modify_present=True)

        if commit:
            if self.commit(detail=self.name) != True:
                return False

        if self.domains:
            for domain in self.domains:
                compute_group_membership = self._device.query(mode="classid", target="computeGroupMembership",
                                                              filter_str="(ip,'" + domain + "',type='eq')")
                if len(compute_group_membership) == 1:
                    if compute_group_membership[0].oper_group_dn:
                        if compute_group_membership[0].oper_group_dn != self._dn:
                            self.logger(level="warning",
                                        message="Domain " + domain + " is currently assigned to " +
                                                compute_group_membership[0].oper_group_dn +
                                                ". Changing assignment to " + self._dn)
                    compute_group_membership[0].group_dn = self._dn
                    self._handle.set_mo(mo=compute_group_membership[0])
                else:
                    self.logger(level="warning",
                                message="Unable to find domain " + domain + " to assign to Domain Group " + self.name)

            if commit:
                if self.commit(detail=self.name + " - Domains") != True:
                    return False

        # We push all subconfig elements, in a specific optimized order
        objects_to_push_in_order = ['date_time', 'dns', 'remote_access', 'equipment_policies', 'snmp', 'syslog',
                                    'locales', 'roles', 'vlan_groups', 'ip_pools', 'vsans', 'domain_groups']

        # The VLANs and Appliance VLANs are not pushed with the rest
        vlan_list = None
        if self.vlans and self.appliance_vlans:
            vlan_list = self.vlans + self.appliance_vlans
        elif self.vlans:
            vlan_list = self.vlans
        elif self.appliance_vlans:
            vlan_list = self.appliance_vlans

        if vlan_list:
            for vlan in vlan_list:
                # Handling range of VLAN
                if vlan.prefix:
                    start = int(vlan.id_from)
                    stop = int(vlan.id_to)
                    for i in range(start, stop + 1):
                        vlan_temp = copy.deepcopy(vlan)
                        vlan_temp.id = str(i)
                        vlan_temp.name = vlan_temp.prefix + vlan_temp.id
                        vlan_temp.push_object()
                else:
                    vlan.push_object()

        for config_object in objects_to_push_in_order:
            if getattr(self, config_object) is not None:
                if getattr(self, config_object).__class__.__name__ == "list":
                    for subobject in getattr(self, config_object):
                        subobject.push_object()

        return True

    def _get_generic_element(self, json_content, object_class, name_to_fetch):
        if self._config.load_from == "live":
            list_of_obj = self._config.get_config_objects_under_dn(dn=self._dn, object_class=object_class, parent=self)
            return list_of_obj
        elif self._config.load_from == "file" and json_content is not None:
            if name_to_fetch in json_content:
                return [object_class(self, generic, None) for generic in json_content[name_to_fetch]]
        else:
            return []


class UcsCentralDomainGroupEquipmentPolicies(UcsCentralConfigObject):
    _CONFIG_NAME = "Domain Group Equipment Policies"
    _UCS_SDK_OBJECTS_NAMES = ["computeChassisDiscPolicy", "computePsuPolicy", "computeServerDiscPolicy",
                              "computeServerMgmtPolicy", "fabricLanCloudPolicy", "firmwareAutoSyncPolicy",
                              "powerMgmtPolicy", "topInfoSyncPolicy"]

    def __init__(self, parent=None, json_content=None, sdk_object=None):
        UcsCentralConfigObject.__init__(self, parent=parent)
        self.rack_management_connection_policy = None
        self.mac_address_table_aging = None
        self.vlan_port_count_optimization = None
        self.firmware_auto_sync_server_policy = None
        self.info_policy = None
        self.chassis_discovery_policy = []
        self.power_redundancy_policy = None
        self.power_allocation_method = None
        self.power_profiling_policy = None
        self.rack_server_discovery_policy = []

        if self._config.load_from == "live":
            if "computeServerMgmtPolicy" in self._config.sdk_objects:
                compute_server_mgmt_policy_list = \
                    [compute_server_mgmt_policy for compute_server_mgmt_policy in
                     self._config.sdk_objects["computeServerMgmtPolicy"] if self._parent._dn + "/server-mgmt-policy"
                     in compute_server_mgmt_policy.dn]
                if len(compute_server_mgmt_policy_list) == 1:
                    compute_server_mgmt_policy = compute_server_mgmt_policy_list[0]
                    self.rack_management_connection_policy = compute_server_mgmt_policy.action

            if "fabricLanCloudPolicy" in self._config.sdk_objects:
                fabric_lan_cloud_policy_list = \
                    [fabric_lan_cloud_policy for fabric_lan_cloud_policy in
                     self._config.sdk_objects["fabricLanCloudPolicy"] if self._parent._dn + "/lan-policy"
                     in fabric_lan_cloud_policy.dn]
                if len(fabric_lan_cloud_policy_list) == 1:
                    fabric_lan_cloud_policy = fabric_lan_cloud_policy_list[0]
                    self.mac_address_table_aging = fabric_lan_cloud_policy.mac_aging
                    self.vlan_port_count_optimization = fabric_lan_cloud_policy.vlan_compression

            if "firmwareAutoSyncPolicy" in self._config.sdk_objects:
                firmware_auto_sync_policy_list = \
                    [firmware_auto_sync_policy for firmware_auto_sync_policy in
                     self._config.sdk_objects["firmwareAutoSyncPolicy"] if self._parent._dn + "/fw-auto-sync"
                     in firmware_auto_sync_policy.dn]
                if len(firmware_auto_sync_policy_list) == 1:
                    firmware_auto_sync_policy = firmware_auto_sync_policy_list[0]
                    self.firmware_auto_sync_server_policy = firmware_auto_sync_policy.sync_state

            if "topInfoSyncPolicy" in self._config.sdk_objects:
                top_info_sync_policy_list = \
                    [top_info_sync_policy for top_info_sync_policy in self._config.sdk_objects["topInfoSyncPolicy"]
                     if self._parent._dn + "/info-sync-policy" in top_info_sync_policy.dn]
                if len(top_info_sync_policy_list) == 1:
                    top_info_sync_policy = top_info_sync_policy_list[0]
                    self.info_policy = top_info_sync_policy.state

            if "computeChassisDiscPolicy" in self._config.sdk_objects:
                compute_chassis_disc_policy_list = \
                    [compute_chassis_disc_policy for compute_chassis_disc_policy in
                     self._config.sdk_objects["computeChassisDiscPolicy"] if self._parent._dn + "/chassis-discovery"
                     in compute_chassis_disc_policy.dn]
                if len(compute_chassis_disc_policy_list) == 1:
                    compute_chassis_disc_policy = compute_chassis_disc_policy_list[0]
                    self.chassis_discovery_policy = [{}]
                    self.chassis_discovery_policy[0].update({"action_link": compute_chassis_disc_policy.action})
                    if "-link" in self.chassis_discovery_policy[0]["action_link"]:
                        self.chassis_discovery_policy[0]["action_link"] = \
                            self.chassis_discovery_policy[0]["action_link"].split('-')[0]
                    self.chassis_discovery_policy[0].update(
                        {"link_grouping_preference": compute_chassis_disc_policy.link_aggregation_pref})
                    self.chassis_discovery_policy[0].update(
                        {"multicast_hardware_hash": compute_chassis_disc_policy.multicast_hw_hash})
                    self.chassis_discovery_policy[0].update(
                        {"backplane_speed_preference": compute_chassis_disc_policy.backplane_speed_pref})

            if "computePsuPolicy" in self._config.sdk_objects:
                compute_psu_policy_list = \
                    [compute_psu_policy for compute_psu_policy in self._config.sdk_objects["computePsuPolicy"]
                     if self._parent._dn + "/psu-policy" in compute_psu_policy.dn]
                if len(compute_psu_policy_list) == 1:
                    compute_psu_policy = compute_psu_policy_list[0]
                    self.power_redundancy_policy = compute_psu_policy.redundancy

            if "powerMgmtPolicy" in self._config.sdk_objects:
                power_mgmt_policy_list = \
                    [power_mgmt_policy for power_mgmt_policy in self._config.sdk_objects["powerMgmtPolicy"]
                     if self._parent._dn + "/pwr-mgmt-policy" in power_mgmt_policy.dn]
                if len(power_mgmt_policy_list) == 1:
                    power_mgmt_policy = power_mgmt_policy_list[0]
                    self.power_allocation_method = power_mgmt_policy.style
                    # Not in UCS Central GUI but present in MIT and ucscsdk
                    self.power_profiling_policy = power_mgmt_policy.profiling

            if "computeServerDiscPolicy" in self._config.sdk_objects:
                compute_server_disc_policy_list = \
                    [compute_server_disc_policy for compute_server_disc_policy in
                     self._config.sdk_objects["computeServerDiscPolicy"] if self._parent._dn + "/server-discovery"
                     in compute_server_disc_policy.dn]
                if len(compute_server_disc_policy_list) == 1:
                    compute_server_disc_policy = compute_server_disc_policy_list[0]
                    self.rack_server_discovery_policy = [{}]
                    self.rack_server_discovery_policy[0].update({"action": compute_server_disc_policy.action})
                    self.rack_server_discovery_policy[0].update(
                        {"scrub_policy": compute_server_disc_policy.scrub_policy_name})

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

                for element in self.chassis_discovery_policy:
                    for value in ["action_link", "link_grouping_preference", "multicast_hardware_hash",
                                  "backplane_speed_preference"]:
                        if value not in element:
                            element[value] = None

                for element in self.rack_server_discovery_policy:
                    for value in ["action", "scrub_policy"]:
                        if value not in element:
                            element[value] = None

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration, waiting for a commit")

        if hasattr(self._parent, '_dn'):
            parent_mo = self._parent._dn
        else:
            self.logger(level="error",
                        message="Impossible to find the parent dn of " + self._CONFIG_NAME)
            return False

        if self.rack_management_connection_policy:
            mo_compute_server_mgmt_policy = ComputeServerMgmtPolicy(parent_mo_or_dn=parent_mo,
                                                                    action=self.rack_management_connection_policy)
            self._handle.add_mo(mo_compute_server_mgmt_policy, modify_present=True)
            if commit:
                if self.commit(detail="Rack Management Connection Policy") != True:
                    return False

        if self.mac_address_table_aging:
            if ":" in self.mac_address_table_aging:
                # Converting 00:00:00:00 to integer format to avoid ucscsdk issue
                mac_address_table_aging = None
                mac_aging = self.mac_address_table_aging.split(":")
                if len(mac_aging) == 4:
                    mac_address_table_aging = str(int(mac_aging[0]) * 86400 + int(mac_aging[1]) * 3600 +
                                                  int(mac_aging[2]) * 60 + int(mac_aging[3]))
                elif len(mac_aging) == 3:
                    mac_address_table_aging = str(int(mac_aging[0]) * 3600 + int(mac_aging[1]) * 60 + int(mac_aging[2]))
                elif len(mac_aging) == 2:
                    mac_address_table_aging = str(int(mac_aging[0]) * 60 + int(mac_aging[1]))
            else:
                mac_address_table_aging = self.mac_address_table_aging
            mo_fabric_lan_cloud_policy = FabricLanCloudPolicy(parent_mo_or_dn=parent_mo,
                                                              mac_aging=mac_address_table_aging)
            self._handle.add_mo(mo_fabric_lan_cloud_policy, modify_present=True)
            if commit:
                if self.commit("MAC Address Table Aging") != True:
                    return False

        if self.vlan_port_count_optimization:
            mo_fabric_lan_cloud_policy = FabricLanCloudPolicy(parent_mo_or_dn=parent_mo,
                                                              vlan_compression=self.vlan_port_count_optimization)
            self._handle.add_mo(mo_fabric_lan_cloud_policy, modify_present=True)
            if commit:
                if self.commit("VLAN Port Count Optimization") != True:
                    return False

        if self.firmware_auto_sync_server_policy:
            if self.firmware_auto_sync_server_policy == "user-acknowledge":
                self.firmware_auto_sync_server_policy = "User Acknowledge"
            elif self.firmware_auto_sync_server_policy == "no-actions":
                self.firmware_auto_sync_server_policy = "No Actions"
            mo_firmware_auto_sync_policy = FirmwareAutoSyncPolicy(parent_mo_or_dn=parent_mo,
                                                                  sync_state=self.firmware_auto_sync_server_policy)
            self._handle.add_mo(mo_firmware_auto_sync_policy, modify_present=True)
            if commit:
                if self.commit("Firmware Auto Sync Server Policy") != True:
                    return False

        if self.info_policy:
            mo_top_info_sync_policy = TopInfoSyncPolicy(parent_mo_or_dn=parent_mo, state=self.info_policy)
            self._handle.add_mo(mo_top_info_sync_policy, modify_present=True)
            if commit:
                if self.commit("Info Policy") != True:
                    return False

        if self.chassis_discovery_policy:
            action = self.chassis_discovery_policy[0]["action_link"]
            if action == "max":
                action = "platform-max"
            elif len(action) == 1:
                action = action + "-link"

            link_grouping_preference = None
            if "link_grouping_preference" in self.chassis_discovery_policy[0]:
                link_grouping_preference = self.chassis_discovery_policy[0]["link_grouping_preference"]

            multicast_hardware_hash = None
            if "multicast_hardware_hash" in self.chassis_discovery_policy[0]:
                multicast_hardware_hash = self.chassis_discovery_policy[0]["multicast_hardware_hash"]

            backplane_speed_pref = None
            if "backplane_speed_preference" in self.chassis_discovery_policy[0]:
                backplane_speed_pref = self.chassis_discovery_policy[0]["backplane_speed_preference"]

            mo_compute_chassis_disc_policy = ComputeChassisDiscPolicy(parent_mo_or_dn=parent_mo,
                                                                      link_aggregation_pref=link_grouping_preference,
                                                                      action=action,
                                                                      multicast_hw_hash=multicast_hardware_hash,
                                                                      backplane_speed_pref=backplane_speed_pref)
            self._handle.add_mo(mo_compute_chassis_disc_policy, modify_present=True)
            if commit:
                if self.commit(detail="Chassis Discovery Policy") != True:
                    return False

        if self.power_redundancy_policy:
            mo_compute_psu_policy = ComputePsuPolicy(parent_mo_or_dn=parent_mo, redundancy=self.power_redundancy_policy)
            self._handle.add_mo(mo_compute_psu_policy, modify_present=True)
            if commit:
                if self.commit("Power Redundancy Policy") != True:
                    return False

        if self.power_allocation_method:
            if self.power_allocation_method == "Policy Driven Chassis Group Cap":
                self.power_allocation_method = "intelligent-policy-driven"
            elif self.power_allocation_method == "Manual Blade Level Cap":
                self.power_allocation_method = "manual-per-blade"
            mo_power_mgmt_policy = PowerMgmtPolicy(parent_mo_or_dn=parent_mo, style=self.power_allocation_method)
            self._handle.add_mo(mo_power_mgmt_policy, modify_present=True)
            if commit:
                if self.commit("Power Allocation Method Policy") != True:
                    return False

        if self.power_profiling_policy:
            mo_power_mgmt_policy = PowerMgmtPolicy(parent_mo_or_dn=parent_mo, profiling=self.power_profiling_policy)
            self._handle.add_mo(mo_power_mgmt_policy, modify_present=True)
            if commit:
                if self.commit("Power Profiling Policy") != True:
                    return False

        if self.rack_server_discovery_policy:
            action = None
            if "action" in self.rack_server_discovery_policy[0]:
                action = self.rack_server_discovery_policy[0]["action"]
            scrub_policy = None
            if "scrub_policy" in self.rack_server_discovery_policy[0]:
                scrub_policy = self.rack_server_discovery_policy[0]["scrub_policy"]

            mo_compute_server_disc_policy = ComputeServerDiscPolicy(parent_mo_or_dn=parent_mo, action=action,
                                                                    scrub_policy_name=scrub_policy)
            self._handle.add_mo(mo_compute_server_disc_policy, modify_present=True)
            if commit:
                if self.commit(detail="Rack Server Discovery Policy") != True:
                    return False

        return True


class UcsCentralDomainGroupRemoteAccess(UcsCentralConfigObject):
    _CONFIG_NAME = "Domain Group Remote Access"
    _UCS_SDK_OBJECTS_NAMES = ["commHttp", "commTelnet", "commCimxml", "commWebSvcLimits", "commShellSvcLimits"]

    def __init__(self, parent=None, json_content=None, sdk_object=None):
        UcsCentralConfigObject.__init__(self, parent=parent)
        self.http = []
        self.telnet = None
        self.cim_xml = None
        self.web_sessions = []
        self.shell_sessions = []

        if self._config.load_from == "live":
            if "commHttp" in self._config.sdk_objects:
                comm_http_list = [comm_http for comm_http in self._config.sdk_objects["commHttp"]
                                  if self._parent._dn + "/http-svc" in comm_http.dn]
                if len(comm_http_list) == 1:
                    comm_http = comm_http_list[0]
                    self.http = [{}]
                    self.http[0].update({"state": comm_http.admin_state})

                    # redirectState attribute is returning values of 0 and 1 in ucscsdk instead of enabled/disabled
                    if comm_http.redirect_state in ["0", "disabled"]:
                        self.http[0].update({"https_redirect": "disabled"})
                    elif comm_http.redirect_state in ["1", "enabled"]:
                        self.http[0].update({"https_redirect": "enabled"})

            if "commTelnet" in self._config.sdk_objects:
                comm_telnet_list = [comm_telnet for comm_telnet in self._config.sdk_objects["commTelnet"]
                                    if self._parent._dn + "/telnet-svc" in comm_telnet.dn]
                if len(comm_telnet_list) == 1:
                    comm_telnet = comm_telnet_list[0]
                    self.telnet = comm_telnet.admin_state

            if "commCimxml" in self._config.sdk_objects:
                comm_cimxml_list = [comm_cimxml for comm_cimxml in self._config.sdk_objects["commCimxml"]
                                    if self._parent._dn + "/cimxml-svc" in comm_cimxml.dn]
                if len(comm_cimxml_list) == 1:
                    comm_cimxml = comm_cimxml_list[0]
                    self.cim_xml = comm_cimxml.admin_state

            if "commWebSvcLimits" in self._config.sdk_objects:
                comm_websvclimits_list = [comm_websvclimits for comm_websvclimits in
                                          self._config.sdk_objects["commWebSvcLimits"] if self._parent._dn +
                                          "/web-svc-limits" in comm_websvclimits.dn]
                if len(comm_websvclimits_list) == 1:
                    comm_websvclimits = comm_websvclimits_list[0]
                    self.web_sessions = [{}]
                    self.web_sessions[0].update({"maximum_sessions_per_user": comm_websvclimits.sessions_per_user})
                    self.web_sessions[0].update({"maximum_sessions": comm_websvclimits.total_sessions})

            if "commShellSvcLimits" in self._config.sdk_objects:
                comm_shellsvclimits_list = [comm_shellsvclimits for comm_shellsvclimits in
                                            self._config.sdk_objects["commShellSvcLimits"] if self._parent._dn +
                                            "/shell-svc-limits" in comm_shellsvclimits.dn]
                if len(comm_shellsvclimits_list) == 1:
                    comm_shellsvclimits = comm_shellsvclimits_list[0]
                    self.shell_sessions = [{}]
                    self.shell_sessions[0].update({"maximum_sessions_per_user": comm_shellsvclimits.sessions_per_user})
                    self.shell_sessions[0].update({"maximum_sessions": comm_shellsvclimits.total_sessions})

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

                for element in self.http:
                    for value in ["state", "https_redirect"]:
                        if value not in element:
                            element[value] = None

                for element in self.web_sessions:
                    for value in ["maximum_sessions", "maximum_sessions_per_user"]:
                        if value not in element:
                            element[value] = None

                for element in self.shell_sessions:
                    for value in ["maximum_sessions", "maximum_sessions_per_user"]:
                        if value not in element:
                            element[value] = None

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration, waiting for a commit")

        if hasattr(self._parent, '_dn'):
            parent_mo = self._parent._dn
        else:
            self.logger(level="error",
                        message="Impossible to find the parent dn of " + self._CONFIG_NAME)
            return False

        if self.http:
            mo_comm_http = CommHttp(parent_mo_or_dn=parent_mo, admin_state=self.http[0]["state"],
                                    redirect_state=self.http[0]["https_redirect"])
            self._handle.add_mo(mo_comm_http, modify_present=True)
            if commit:
                if self.commit("HTTP") != True:
                    return False

        if self.telnet:
            mo_comm_telnet = CommTelnet(parent_mo_or_dn=parent_mo, admin_state=self.telnet)
            self._handle.add_mo(mo_comm_telnet, modify_present=True)
            if commit:
                if self.commit("Telnet") != True:
                    return False

        if self.cim_xml:
            mo_comm_cimxml = CommCimxml(parent_mo_or_dn=parent_mo, admin_state=self.cim_xml)
            self._handle.add_mo(mo_comm_cimxml, modify_present=True)
            if commit:
                if self.commit("CIM XML") != True:
                    return False

        if self.web_sessions:
            mo_comm_web_svc_limits = \
                CommWebSvcLimits(parent_mo_or_dn=parent_mo,
                                 sessions_per_user=self.web_sessions[0]["maximum_sessions_per_user"],
                                 total_sessions=self.web_sessions[0]["maximum_sessions"])
            self._handle.add_mo(mo_comm_web_svc_limits, modify_present=True)
            if commit:
                if self.commit("Web Sessions") != True:
                    return False

        if self.shell_sessions:
            mo_comm_shell_svc_limits = \
                CommShellSvcLimits(parent_mo_or_dn=parent_mo,
                                   sessions_per_user=self.shell_sessions[0]["maximum_sessions_per_user"],
                                   total_sessions=self.shell_sessions[0]["maximum_sessions"])
            self._handle.add_mo(mo_comm_shell_svc_limits, modify_present=True)
            if commit:
                if self.commit("Shell Sessions") != True:
                    return False

        return True


class UcsCentralVlan(UcsCentralConfigObject):
    _CONFIG_NAME = "VLAN"
    _UCS_SDK_OBJECT_NAME = "fabricVlan"

    def __init__(self, parent=None, json_content=None, fabric_vlan=None):
        UcsCentralConfigObject.__init__(self, parent=parent)
        self.id = None
        self.name = None
        self.sharing_type = None
        self.org_permissions = []
        self.multicast_policy_name = None
        self.primary_vlan_name = None

        # Range purpose
        self.id_from = None
        self.id_to = None
        self.prefix = None

        if self._config.load_from == "live":
            if fabric_vlan is not None:
                self.id = fabric_vlan.id
                self.name = fabric_vlan.name

                if fabric_vlan.mcast_policy_name != "":
                    self.multicast_policy_name = fabric_vlan.mcast_policy_name
                if fabric_vlan.sharing != "none":
                    self.sharing_type = fabric_vlan.sharing
                    if self.sharing_type in ["community", "isolated"]:
                        self.primary_vlan_name = fabric_vlan.pub_nw_name

                if "fabricVlanReq" in self._config.sdk_objects:
                    for vlan_req in self._config.sdk_objects["fabricVlanReq"]:
                        if vlan_req.name == self.name:
                            org_dn = vlan_req.dn.split("/vlan-req-")[0]
                            self.org_permissions.append(org_dn)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + self.name +
                                ' (' + self.id + ')')
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + self.name +
                                ' (' + self.id + ')' + ", waiting for a commit")

        if hasattr(self._parent, '_dn'):
            parent_mo = self._parent._dn
        else:
            self.logger(level="error",
                        message="Impossible to find the parent dn of " + self._CONFIG_NAME + " : " + str(self.name))
            return False

        mo_fabric_vlan = FabricVlan(parent_mo_or_dn=parent_mo + "/fabric/lan", sharing=self.sharing_type,
                                    name=self.name, id=self.id, mcast_policy_name=self.multicast_policy_name,
                                    pub_nw_name=self.primary_vlan_name)
        self._handle.add_mo(mo=mo_fabric_vlan, modify_present=True)

        if self.org_permissions:
            for organization in self.org_permissions:
                complete_org_path = ""
                for part in organization.split("/"):
                    if "org-" not in part:
                        complete_org_path += "org-"
                    complete_org_path += part + "/"
                complete_org_path = complete_org_path[:-1]  # Remove the trailing "/"
                if not complete_org_path.startswith("org-root"):
                    complete_org_path = "org-root/" + complete_org_path

                mo_fabric_vlan_req = FabricVlanReq(parent_mo_or_dn=complete_org_path, name=self.name)
                self._handle.add_mo(mo=mo_fabric_vlan_req, modify_present=True)

        if commit:
            if self.commit(detail=self.name + " (" + self.id + ")") != True:
                return False

        return True


class UcsCentralApplianceVlan(UcsCentralConfigObject):
    _CONFIG_NAME = "Appliance VLAN"
    _UCS_SDK_OBJECT_NAME = "fabricVlan"

    def __init__(self, parent=None, json_content=None, fabric_vlan=None):
        UcsCentralConfigObject.__init__(self, parent=parent)
        self.id = None
        self.name = None
        self.sharing_type = None
        self.org_permissions = []
        self.multicast_policy_name = None
        self.primary_vlan_name = None

        # Range purpose
        self.id_from = None
        self.id_to = None
        self.prefix = None

        if self._config.load_from == "live":
            if fabric_vlan is not None:
                self.id = fabric_vlan.id
                self.name = fabric_vlan.name

                if fabric_vlan.mcast_policy_name != "":
                    self.multicast_policy_name = fabric_vlan.mcast_policy_name
                if fabric_vlan.sharing != "none":
                    self.sharing_type = fabric_vlan.sharing
                    if self.sharing_type in ["community", "isolated"]:
                        self.primary_vlan_name = fabric_vlan.pub_nw_name

                if "fabricVlanReq" in self._config.sdk_objects:
                    for vlan_req in self._config.sdk_objects["fabricVlanReq"]:
                        if vlan_req.name == self.name:
                            org_dn = vlan_req.dn.split("/vlan-req-")[0]
                            self.org_permissions.append(org_dn)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + self.name +
                                ' (' + self.id + ')')
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + self.name +
                                ' (' + self.id + ')' + ", waiting for a commit")

        if hasattr(self._parent, '_dn'):
            parent_mo = self._parent._dn
        else:
            self.logger(level="error",
                        message="Impossible to find the parent dn of " + self._CONFIG_NAME + " : " + str(self.name))
            return False

        mo_fabric_vlan = FabricVlan(parent_mo_or_dn=parent_mo + "/fabric/eth-estc", sharing=self.sharing_type,
                                    name=self.name, id=self.id, mcast_policy_name=self.multicast_policy_name,
                                    pub_nw_name=self.primary_vlan_name)
        self._handle.add_mo(mo=mo_fabric_vlan, modify_present=True)

        if self.org_permissions:
            for organization in self.org_permissions:
                complete_org_path = ""
                for part in organization.split("/"):
                    if "org-" not in part:
                        complete_org_path += "org-"
                    complete_org_path += part + "/"
                complete_org_path = complete_org_path[:-1]  # Remove the trailing "/"
                if not complete_org_path.startswith("org-root"):
                    complete_org_path = "org-root/" + complete_org_path

                mo_fabric_vlan_req = FabricVlanReq(parent_mo_or_dn=complete_org_path, name=self.name)
                self._handle.add_mo(mo=mo_fabric_vlan_req, modify_present=True)

        if commit:
            if self.commit(detail=self.name + " (" + self.id + ")") != True:
                return False

        return True


class UcsCentralVlanGroup(UcsCentralConfigObject):
    _CONFIG_NAME = "VLAN Group"
    _UCS_SDK_OBJECT_NAME = "fabricNetGroup"

    def __init__(self, parent=None, json_content=None, fabric_net_group=None):
        UcsCentralConfigObject.__init__(self, parent=parent)
        self.name = None
        self.vlans = []
        self.native_vlan = None
        self.org_permissions = []

        if self._config.load_from == "live":
            if fabric_net_group is not None:
                self.name = fabric_net_group.name
                self.native_vlan = fabric_net_group.native_net

                if "fabricPooledVlan" in self._config.sdk_objects:
                    vlans = [vlan for vlan in self._config.sdk_objects["fabricPooledVlan"]
                             if "fabric/lan/net-group-" + self.name in vlan.dn]
                    if vlans:
                        for vlan in vlans:
                            if vlan.name != self.native_vlan:
                                self.vlans.append(vlan.name)

                if "fabricNetGroupReq" in self._config.sdk_objects:
                    for ng_req in self._config.sdk_objects["fabricNetGroupReq"]:
                        if ng_req.name == self.name:
                            org_dn = ng_req.dn.split("/ngreq-")[0]
                            self.org_permissions.append(org_dn)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + str(self.name))
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + str(self.name) +
                                ", waiting for a commit")

        if hasattr(self._parent, '_dn'):
            parent_mo = self._parent._dn
        else:
            self.logger(level="error",
                        message="Impossible to find the parent dn of " + self._CONFIG_NAME + " : " + str(self.name))
            return False
        mo_fabric_net_group = FabricNetGroup(parent_mo_or_dn=parent_mo + "/fabric/lan",
                                             native_net=self.native_vlan,
                                             name=self.name)
        self._handle.add_mo(mo=mo_fabric_net_group, modify_present=True)

        if commit:
            if self.commit(detail=self.name) != True:
                return False

        if self.vlans:
            for vlan in self.vlans:
                FabricPooledVlan(parent_mo_or_dn=mo_fabric_net_group, name=vlan)
                self._handle.add_mo(mo=mo_fabric_net_group, modify_present=True)

                if commit:
                    self.commit(detail="vlan: " + vlan)

        if self.native_vlan:
            FabricPooledVlan(parent_mo_or_dn=mo_fabric_net_group, name=self.native_vlan)
            self._handle.add_mo(mo=mo_fabric_net_group, modify_present=True)

            if commit:
                self.commit(detail="native_vlan: " + self.native_vlan)

        if self.org_permissions:
            for organization in self.org_permissions:
                complete_org_path = ""
                for part in organization.split("/"):
                    if "org-" not in part:
                        complete_org_path += "org-"
                    complete_org_path += part + "/"
                complete_org_path = complete_org_path[:-1]  # Remove the trailing "/"
                if not complete_org_path.startswith("org-root"):
                    complete_org_path = "org-root/" + complete_org_path

                mo_fabric_ng_req = FabricNetGroupReq(parent_mo_or_dn=complete_org_path, name=self.name)
                self._handle.add_mo(mo=mo_fabric_ng_req, modify_present=True)

                if commit:
                    self.commit(detail="Org permission: " + organization)

        return True


class UcsCentralVsan(UcsCentralConfigObject):
    _CONFIG_NAME = "VSAN"
    _UCS_SDK_OBJECT_NAME = "fabricVsan"

    def __init__(self, parent=None, json_content=None, fabric_vsan=None):
        UcsCentralConfigObject.__init__(self, parent=parent)
        self.fabric = None
        self.fcoe_vlan_id = None
        self.id = None
        self.name = None
        self.zoning = None

        if self._config.load_from == "live":
            if fabric_vsan is not None:
                self.fcoe_vlan_id = fabric_vsan.fcoe_vlan
                self.id = fabric_vsan.id
                self.name = fabric_vsan.name
                self.zoning = fabric_vsan.zoning_state

                if fabric_vsan.switch_id not in ["NONE", "dual"]:
                    self.fabric = fabric_vsan.switch_id
                else:
                    self.fabric = "dual"

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + self.name + ' (' + self.id + ')')
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + self.name +
                                ' (' + self.id + ')' + ", waiting for a commit")

        if hasattr(self._parent, '_dn'):
            parent_mo = self._parent._dn
        else:
            self.logger(level="error",
                        message="Impossible to find the parent dn of " + self._CONFIG_NAME + " : " + str(self.name))
            return False

        dn_subpath = "/fabric/san"
        if self.fabric is not None and self.fabric not in ["NONE", "dual"]:
            dn_subpath = "/fabric/san/" + self.fabric

        mo_fabric_vsan = FabricVsan(parent_mo_or_dn=parent_mo + dn_subpath, name=self.name, id=self.id,
                                    zoning_state=self.zoning, fcoe_vlan=self.fcoe_vlan_id)

        self._handle.add_mo(mo=mo_fabric_vsan, modify_present=True)
        if commit:
            if self.commit(detail=self.name + " (" + self.id + ")") != True:
                return False
        return True