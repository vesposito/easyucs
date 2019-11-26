# coding: utf-8
# !/usr/bin/env python

""" admin.py: Easy UCS Deployment Tool """
from easyucs import __author__, __copyright__,  __version__, __status__


import hashlib
import sys
import time
import traceback
import urllib

from easyucs.config.object import GenericUcsConfigObject, UcsImcConfigObject, UcsSystemConfigObject

from easyucs.config.ucs.lan import UcsSystemIpPool, UcsSystemMacPool, UcsSystemVnicTemplate, UcsSystemQosPolicy,\
    UcsSystemNetworkControlPolicy, UcsSystemMulticastPolicy, UcsSystemLinkProtocolPolicy,\
    UcsSystemLanConnectivityPolicy, UcsSystemLacpPolicy, UcsSystemFlowControlPolicy, UcsSystemDefaultVnicBehavior,\
    UcsSystemDynamicVnicConnectionPolicy
from easyucs.config.ucs.servers import UcsSystemUuidPool, UcsSystemServerPool, UcsSystemServerPoolPolicy,\
    UcsSystemPowerControlPolicy, UcsSystemMaintenancePolicy, UcsSystemGraphicsCardPolicy,\
    UcsSystemLocalDiskConfPolicy, UcsSystemServerPoolPolicyQualifications, UcsSystemPowerSyncPolicy,\
    UcsSystemHostFirmwarePackage, UcsSystemIpmiAccessProfile, UcsSystemKvmManagementPolicy, UcsSystemScrubPolicy,\
    UcsSystemSerialOverLanPolicy, UcsSystemBootPolicy, UcsSystemVnicVhbaPlacementPolicy, UcsSystemBiosPolicy,\
    UcsSystemIscsiAuthenticationProfile, UcsSystemVmediaPolicy, UcsSystemEthernetAdapterPolicy,\
    UcsSystemFibreChannelAdapterPolicy, UcsSystemIscsiAdapterPolicy, UcsSystemServiceProfile,\
    UcsSystemMemoryPolicy, UcsSystemThresholdPolicy, UcsSystemDiagnosticsPolicy
from easyucs.config.ucs.san import UcsSystemWwpnPool, UcsSystemWwnnPool, UcsSystemWwxnPool, UcsSystemVhbaTemplate,\
    UcsSystemSanConnectivityPolicy, UcsSystemStorageConnectionPolicy, UcsSystemDefaultVhbaBehavior, \
    UcsSystemIqnSuffixPool
from easyucs.config.ucs.storage import UcsSystemDiskGroupPolicy, UcsSystemStorageProfile
from easyucs.config.ucs.chassis import UcsSystemChassisMaintenancePolicy, UcsSystemComputeConnectionPolicy,\
    UcsSystemChassisFirmwarePackage, UcsSystemDiskZoningPolicy, UcsSystemChassisProfile, \
    UcsSystemSasExpanderConfigurationPolicy

from easyucs import common

from imcsdk.mometa.aaa.AaaUser import AaaUser as ImcAaaUser
from imcsdk.mometa.aaa.AaaUserPasswordExpiration import AaaUserPasswordExpiration as ImcAaaUserPasswordExpiration
from imcsdk.mometa.aaa.AaaUserPolicy import AaaUserPolicy as ImcAaaUserPolicy
from imcsdk.mometa.comm.CommNtpProvider import CommNtpProvider as ImcCommNtpProvider
from imcsdk.mometa.mgmt.MgmtIf import MgmtIf
from imcsdk.mometa.top.TopSystem import TopSystem as ImcTopSystem
from imcsdk.mometa.compute.ComputeRackUnit import ComputeRackUnit
from imcsdk.mometa.ip.IpBlocking import IpBlocking
from imcsdk.mometa.ip.IpFiltering import IpFiltering

from ucsmsdk.ucsexception import UcsException

from ucsmsdk.mometa.aaa.AaaLdapEp import AaaLdapEp
from ucsmsdk.mometa.aaa.AaaLdapGroup import AaaLdapGroup
from ucsmsdk.mometa.aaa.AaaLdapGroupRule import AaaLdapGroupRule
from ucsmsdk.mometa.aaa.AaaLdapProvider import AaaLdapProvider
from ucsmsdk.mometa.aaa.AaaLocale import AaaLocale
from ucsmsdk.mometa.aaa.AaaOrg import AaaOrg
from ucsmsdk.mometa.aaa.AaaPreLoginBanner import AaaPreLoginBanner
from ucsmsdk.mometa.aaa.AaaProviderGroup import AaaProviderGroup
from ucsmsdk.mometa.aaa.AaaProviderRef import AaaProviderRef
from ucsmsdk.mometa.aaa.AaaPwdProfile import AaaPwdProfile
from ucsmsdk.mometa.aaa.AaaPwdProfile import AaaPwdProfile
from ucsmsdk.mometa.aaa.AaaRadiusEp import AaaRadiusEp
from ucsmsdk.mometa.aaa.AaaRadiusProvider import AaaRadiusProvider
from ucsmsdk.mometa.aaa.AaaRole import AaaRole
from ucsmsdk.mometa.aaa.AaaSshAuth import AaaSshAuth
from ucsmsdk.mometa.aaa.AaaTacacsPlusEp import AaaTacacsPlusEp
from ucsmsdk.mometa.aaa.AaaTacacsPlusProvider import AaaTacacsPlusProvider
from ucsmsdk.mometa.aaa.AaaUser import AaaUser
from ucsmsdk.mometa.aaa.AaaUserEp import AaaUserEp
from ucsmsdk.mometa.aaa.AaaUserLocale import AaaUserLocale
from ucsmsdk.mometa.aaa.AaaUserRole import AaaUserRole
from ucsmsdk.mometa.callhome.CallhomeAnonymousReporting import CallhomeAnonymousReporting
from ucsmsdk.mometa.callhome.CallhomeDest import CallhomeDest
from ucsmsdk.mometa.callhome.CallhomeEp import CallhomeEp
from ucsmsdk.mometa.callhome.CallhomePeriodicSystemInventory import CallhomePeriodicSystemInventory
from ucsmsdk.mometa.callhome.CallhomePolicy import CallhomePolicy
from ucsmsdk.mometa.callhome.CallhomeProfile import CallhomeProfile
from ucsmsdk.mometa.callhome.CallhomeSmtp import CallhomeSmtp
from ucsmsdk.mometa.callhome.CallhomeSource import CallhomeSource
from ucsmsdk.mometa.comm.CommCimcWebService import CommCimcWebService
from ucsmsdk.mometa.comm.CommCimxml import CommCimxml
from ucsmsdk.mometa.comm.CommDateTime import CommDateTime
from ucsmsdk.mometa.comm.CommDns import CommDns
from ucsmsdk.mometa.comm.CommDnsProvider import CommDnsProvider
from ucsmsdk.mometa.comm.CommHttp import CommHttp
from ucsmsdk.mometa.comm.CommHttps import CommHttps
from ucsmsdk.mometa.comm.CommNtpProvider import CommNtpProvider
from ucsmsdk.mometa.comm.CommShellSvcLimits import CommShellSvcLimits
from ucsmsdk.mometa.comm.CommSnmp import CommSnmp
from ucsmsdk.mometa.comm.CommSnmpTrap import CommSnmpTrap
from ucsmsdk.mometa.comm.CommSnmpUser import CommSnmpUser
from ucsmsdk.mometa.comm.CommSsh import CommSsh
from ucsmsdk.mometa.comm.CommTelnet import CommTelnet
from ucsmsdk.mometa.comm.CommWebSvcLimits import CommWebSvcLimits
from ucsmsdk.mometa.compute.ComputeChassisDiscPolicy import ComputeChassisDiscPolicy
from ucsmsdk.mometa.compute.ComputeHwChangeDiscPolicy import ComputeHwChangeDiscPolicy
from ucsmsdk.mometa.compute.ComputePortDiscPolicy import ComputePortDiscPolicy
from ucsmsdk.mometa.compute.ComputePsuPolicy import ComputePsuPolicy
from ucsmsdk.mometa.compute.ComputeServerDiscPolicy import ComputeServerDiscPolicy
from ucsmsdk.mometa.compute.ComputeServerMgmtPolicy import ComputeServerMgmtPolicy
from ucsmsdk.mometa.fabric.FabricFcSan import FabricFcSan
from ucsmsdk.mometa.fabric.FabricLanCloud import FabricLanCloud
from ucsmsdk.mometa.fabric.FabricOrgVlanPolicy import FabricOrgVlanPolicy
from ucsmsdk.mometa.fabric.FabricSanCloud import FabricSanCloud
from ucsmsdk.mometa.firmware.FirmwareAck import FirmwareAck
from ucsmsdk.mometa.firmware.FirmwareAutoSyncPolicy import FirmwareAutoSyncPolicy
from ucsmsdk.mometa.mgmt.MgmtBackupExportExtPolicy import MgmtBackupExportExtPolicy
from ucsmsdk.mometa.mgmt.MgmtBackupPolicy import MgmtBackupPolicy
from ucsmsdk.mometa.mgmt.MgmtCfgExportPolicy import MgmtCfgExportPolicy
from ucsmsdk.mometa.mgmt.MgmtIPv6IfAddr import MgmtIPv6IfAddr
from ucsmsdk.mometa.mgmt.MgmtInbandProfile import MgmtInbandProfile
from ucsmsdk.mometa.network.NetworkElement import NetworkElement
from ucsmsdk.mometa.org.OrgOrg import OrgOrg
from ucsmsdk.mometa.policy.PolicyCommunication import PolicyCommunication
from ucsmsdk.mometa.policy.PolicyConfigBackup import PolicyConfigBackup
from ucsmsdk.mometa.policy.PolicyControlEp import PolicyControlEp
from ucsmsdk.mometa.policy.PolicyDateTime import PolicyDateTime
from ucsmsdk.mometa.policy.PolicyDns import PolicyDns
from ucsmsdk.mometa.policy.PolicyEquipment import PolicyEquipment
from ucsmsdk.mometa.policy.PolicyFault import PolicyFault
from ucsmsdk.mometa.policy.PolicyInfraFirmware import PolicyInfraFirmware
from ucsmsdk.mometa.policy.PolicyMEp import PolicyMEp
from ucsmsdk.mometa.policy.PolicyMonitoring import PolicyMonitoring
from ucsmsdk.mometa.policy.PolicyPortConfig import PolicyPortConfig
from ucsmsdk.mometa.policy.PolicyPowerMgmt import PolicyPowerMgmt
from ucsmsdk.mometa.policy.PolicyPsu import PolicyPsu
from ucsmsdk.mometa.policy.PolicySecurity import PolicySecurity
from ucsmsdk.mometa.power.PowerMgmtPolicy import PowerMgmtPolicy
from ucsmsdk.mometa.sysdebug.SysdebugBackupBehavior import SysdebugBackupBehavior
from ucsmsdk.mometa.sysdebug.SysdebugMEpLogPolicy import SysdebugMEpLogPolicy
from ucsmsdk.mometa.top.TopInfoPolicy import TopInfoPolicy
from ucsmsdk.mometa.top.TopSystem import TopSystem


class UcsSystemDns(UcsSystemConfigObject):
    _CONFIG_NAME = "DNS"

    def __init__(self, parent=None, json_content=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.dns = []

        if self._config.load_from == "live":
            if "commDnsProvider" in self._config.sdk_objects:
                dns_list = [dns for dns in self._config.sdk_objects["commDnsProvider"] if "sys/svc-ext/dns-svc" in
                            dns.dn]
                for dns in dns_list:
                    self.dns.append(dns.name)

        elif self._config.load_from == "file":
            # DNS is not a regular configuration object
            pass

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration")
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration" +
                                ", waiting for a commit")

        parent_mo = "sys/svc-ext/dns-svc"
        for dns in self.dns:
            mo_comm_dns_provider = CommDnsProvider(parent_mo_or_dn=parent_mo, name=dns)
            self._handle.add_mo(mo_comm_dns_provider, modify_present=True)

        if commit:
            if self.commit() != True:
                return False
        return True


class UcsSystemInformation(UcsSystemConfigObject):
    _CONFIG_NAME = "System Information"

    def __init__(self, parent=None, json_content=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.descr = None
        self.domain_name = None
        self.name = None
        self.owner = None
        self.site = None
        self.virtual_ip = None
        self.virtual_ipv6 = None

        if self._config.load_from == "live":
            # Locating SDK objects needed to initialize
            top_system = None
            comm_dns = None
            if "topSystem" in self._config.sdk_objects:
                if len(self._config.sdk_objects["topSystem"]) == 1:
                    top_system = self._config.sdk_objects["topSystem"][0]

            if "commDns" in self._config.sdk_objects:
                comm_dns_list = [comm_dns for comm_dns in self._config.sdk_objects["commDns"] if "sys/svc-ext/dns-svc"
                                 in comm_dns.dn]
                if len(comm_dns_list) == 1:
                    comm_dns = comm_dns_list[0]

            if top_system is not None:
                self.name = top_system.name
                self.virtual_ip = top_system.address
                self.virtual_ipv6 = top_system.ipv6_addr
                self.owner = top_system.owner
                self.site = top_system.site
                self.descr = top_system.descr
            if comm_dns is not None:
                self.domain_name = comm_dns.domain

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration")
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration" +
                                ", waiting for a commit")

        mo_top_system = TopSystem(name=self.name, address=self.virtual_ip, ipv6_addr=self.virtual_ipv6,
                                  owner=self.owner, site=self.site, descr=self.descr)
        mo_comm_dns = CommDns(parent_mo_or_dn="sys/svc-ext", domain=self.domain_name)
        self._handle.add_mo(mo=mo_top_system, modify_present=True)
        self._handle.add_mo(mo=mo_comm_dns, modify_present=True)

        if commit:
            if self.commit() != True:
                return False
        return True


class UcsSystemManagementInterface(UcsSystemConfigObject):
    _CONFIG_NAME = "Management Interface"

    def __init__(self, parent=None, json_content=None, network_element=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.fabric = None
        self.gateway = None
        self.gateway_v6 = None
        self.ip = None
        self.ipv6 = None
        self.netmask = None
        self.prefix = None

        if self._config.load_from == "live":
            # Locating SDK objects needed to initialize

            if network_element is not None:
                self.fabric = network_element.id
                self.ip = network_element.oob_if_ip
                self.netmask = network_element.oob_if_mask
                self.gateway = network_element.oob_if_gw

            if "mgmtIPv6IfAddr" in self._config.sdk_objects:
                for mgmt_ipv6_ifaddr in self._config.sdk_objects["mgmtIPv6IfAddr"]:
                    if "sys/switch-" + self.fabric + "/" in mgmt_ipv6_ifaddr.dn:
                        self.ipv6 = mgmt_ipv6_ifaddr.addr
                        self.prefix = mgmt_ipv6_ifaddr.prefix
                        self.gateway_v6 = mgmt_ipv6_ifaddr.def_gw

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration for fabric " + self.fabric)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration for fabric" +
                                self.fabric + ", waiting for a commit")
        # TODO : Add check if IP mgmt int is different from the one configured and reset the handle if this is the case
        # Checking if the IPv4 and/or IPv6 parameters are given
        if self.ip and self.netmask and self.gateway:
            mo_network_element = NetworkElement(parent_mo_or_dn="sys", id=self.fabric.upper(), oob_if_ip=self.ip,
                                                oob_if_gw=self.gateway, oob_if_mask=self.netmask)
            self._handle.add_mo(mo=mo_network_element, modify_present=True)
            self.logger(level="debug", message="IPv4 parameters for " + self._CONFIG_NAME + " " + self.fabric + " set")

        if self.ipv6 and self.prefix and self.gateway_v6:
            mo_mgmt_ipv6_if_addr = MgmtIPv6IfAddr(parent_mo_or_dn="sys/switch-" + self.fabric + "/ifConfig-ipv6",
                                                  addr=self.ipv6, def_gw=self.gateway_v6, prefix=self.prefix)
            self._handle.add_mo(mo=mo_mgmt_ipv6_if_addr, modify_present=True)
            self.logger(level="debug", message="IPv6 parameters for " + self._CONFIG_NAME + " " + self.fabric + " set")

        if commit:
            if self.commit() != True:
                return False
        return True


class UcsSystemOrg(UcsSystemConfigObject):
    _CONFIG_NAME = "Organization"
    _UCS_SDK_OBJECT_NAME = "orgOrg"

    def __init__(self, parent=None, json_content=None, org_org=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.descr = None
        self.name = None

        if self._config.load_from == "live":
            if org_org is not None:
                self._dn = org_org.dn
                self.name = org_org.name
                self.descr = org_org.descr

        elif self._config.load_from == "file":
            if json_content is not None:
                if self.get_attributes_from_json(json_content=json_content):
                    if hasattr(self._parent, '_dn'):
                        self._dn = self._parent._dn + "/org-" + str(self.name)
                    else:
                        self._dn = "org-" + str(self.name)
                else:
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.orgs = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemOrg, name_to_fetch="orgs")
        self.ip_pools = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemIpPool, name_to_fetch="ip_pools")
        self.mac_pools = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemMacPool,
                                      name_to_fetch="mac_pools")
        self.uuid_pools = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemUuidPool,
                                      name_to_fetch="uuid_pools")
        self.wwnn_pools = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemWwnnPool,
                                      name_to_fetch="wwnn_pools")
        self.wwpn_pools = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemWwpnPool,
                                      name_to_fetch="wwpn_pools")
        self.wwxn_pools = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemWwxnPool,
                                      name_to_fetch="wwxn_pools")
        self.iqn_suffix_pools = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemIqnSuffixPool,
                                      name_to_fetch="iqn_suffix_pools")
        self.server_pools = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemServerPool,
                                      name_to_fetch="server_pools")
        self.server_pool_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemServerPoolPolicy,
                                      name_to_fetch="server_pool_policies")
        self.vnic_templates = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemVnicTemplate,
                                      name_to_fetch="vnic_templates")
        self.vhba_templates = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemVhbaTemplate,
                                      name_to_fetch="vhba_templates")
        self.power_control_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemPowerControlPolicy,
                                      name_to_fetch="power_control_policies")
        self.qos_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemQosPolicy,
                                      name_to_fetch="qos_policies")
        self.dynamic_vnic_connection_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemDynamicVnicConnectionPolicy,
                                      name_to_fetch="dynamic_vnic_connection_policies")
        self.maintenance_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemMaintenancePolicy,
                                      name_to_fetch="maintenance_policies")
        self.graphics_card_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemGraphicsCardPolicy,
                                      name_to_fetch="graphics_card_policies")
        self.local_disk_config_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemLocalDiskConfPolicy,
                                      name_to_fetch="local_disk_config_policies")
        self.server_pool_policy_qualifications = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemServerPoolPolicyQualifications,
                                      name_to_fetch="server_pool_policy_qualifications")
        self.power_sync_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemPowerSyncPolicy,
                                      name_to_fetch="power_sync_policies")
        self.host_firmware_packages = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemHostFirmwarePackage,
                                      name_to_fetch="host_firmware_packages")
        self.ipmi_access_profiles = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemIpmiAccessProfile,
                                      name_to_fetch="ipmi_access_profiles")
        self.kvm_management_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemKvmManagementPolicy,
                                      name_to_fetch="kvm_management_policies")
        self.scrub_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemScrubPolicy,
                                      name_to_fetch="scrub_policies")
        self.serial_over_lan_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemSerialOverLanPolicy,
                                      name_to_fetch="serial_over_lan_policies")
        self.boot_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemBootPolicy,
                                      name_to_fetch="boot_policies")
        self.vnic_vhba_placement_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemVnicVhbaPlacementPolicy,
                                      name_to_fetch="vnic_vhba_placement_policies")
        self.bios_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemBiosPolicy,
                                      name_to_fetch="bios_policies")
        self.network_control_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemNetworkControlPolicy,
                                      name_to_fetch="network_control_policies")
        self.default_vnic_behavior = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemDefaultVnicBehavior,
                                      name_to_fetch="default_vnic_behavior")
        self.default_vhba_behavior = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemDefaultVhbaBehavior,
                                      name_to_fetch="default_vhba_behavior")
        self.flow_control_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemFlowControlPolicy,
                                      name_to_fetch="flow_control_policies", restrict_to_root=True)
        self.lacp_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemLacpPolicy,
                                      name_to_fetch="lacp_policies", restrict_to_root=True)
        self.iscsi_authentication_profiles = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemIscsiAuthenticationProfile,
                                      name_to_fetch="iscsi_authentication_profiles")
        self.vmedia_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemVmediaPolicy,
                                      name_to_fetch="vmedia_policies")
        self.multicast_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemMulticastPolicy,
                                      name_to_fetch="multicast_policies", restrict_to_root=True)
        self.disk_group_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemDiskGroupPolicy,
                                      name_to_fetch="disk_group_policies")
        self.storage_profiles = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemStorageProfile,
                                      name_to_fetch="storage_profiles")
        self.chassis_maintenance_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemChassisMaintenancePolicy,
                                      name_to_fetch="chassis_maintenance_policies")
        self.compute_connection_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemComputeConnectionPolicy,
                                      name_to_fetch="compute_connection_policies")
        self.chassis_firmware_packages = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemChassisFirmwarePackage,
                                      name_to_fetch="chassis_firmware_packages")
        self.disk_zoning_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemDiskZoningPolicy,
                                      name_to_fetch="disk_zoning_policies")
        self.link_protocol_policy = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemLinkProtocolPolicy,
                                      name_to_fetch="link_protocol_policy", restrict_to_root=True)
        self.ethernet_adapter_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemEthernetAdapterPolicy,
                                      name_to_fetch="ethernet_adapter_policies")
        self.fibre_channel_adapter_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemFibreChannelAdapterPolicy,
                                      name_to_fetch="fibre_channel_adapter_policies")
        self.iscsi_adapter_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemIscsiAdapterPolicy,
                                      name_to_fetch="iscsi_adapter_policies")
        self.lan_connectivity_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemLanConnectivityPolicy,
                                      name_to_fetch="lan_connectivity_policies")
        self.san_connectivity_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemSanConnectivityPolicy,
                                      name_to_fetch="san_connectivity_policies")
        self.storage_connection_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemStorageConnectionPolicy,
                                      name_to_fetch="storage_connection_policies")
        self.sas_expander_configuration_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemSasExpanderConfigurationPolicy,
                                      name_to_fetch="sas_expander_configuration_policies")
        self.chassis_profiles = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemChassisProfile,
                                      name_to_fetch="chassis_profiles")
        self.service_profiles = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemServiceProfile,
                                      name_to_fetch="service_profiles")
        self.memory_policy = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemMemoryPolicy,
                                      name_to_fetch="memory_policy")
        self.threshold_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemThresholdPolicy,
                                      name_to_fetch="threshold_policies")
        self.diagnostics_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsSystemDiagnosticsPolicy,
                                      name_to_fetch="diagnostics_policies")

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

        mo_org_org = OrgOrg(parent_mo_or_dn=parent_mo, name=self.name, descr=self.descr)

        self._handle.add_mo(mo=mo_org_org, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False

        # We push all subconfig elements, in a specific optimized order to reduce number of reboots
        # TODO: Verify order
        objects_to_push_in_order = ['server_pool_policy_qualifications', 'server_pools', 'server_pool_policies',
                                    'ip_pools', 'mac_pools', 'uuid_pools', 'wwpn_pools', 'wwnn_pools', 'wwxn_pools',
                                    'bios_policies', 'boot_policies', 'orgs', 'iqn_suffix_pools',
                                    'vmedia_policies', 'qos_policies', 'dynamic_vnic_connection_policies',
                                    'ethernet_adapter_policies', 'fibre_channel_adapter_policies',
                                    'diagnostics_policies', 'iscsi_adapter_policies', 'ipmi_access_profiles',
                                    'power_control_policies', 'serial_over_lan_policies', 'power_sync_policies',
                                    'vnic_vhba_placement_policies', 'lan_connectivity_policies',
                                    'san_connectivity_policies', 'storage_connection_policies',
                                    'local_disk_config_policies', 'host_firmware_packages', 'maintenance_policies',
                                    'network_control_policies', 'multicast_policies', 'lacp_policies',
                                    'link_protocol_policy', 'default_vnic_behavior', 'flow_control_policies',
                                    'scrub_policies', 'vnic_templates', 'default_vhba_behavior', 'vhba_templates',
                                    'chassis_firmware_packages', 'chassis_maintenance_policies',
                                    'compute_connection_policies', 'disk_zoning_policies',
                                    'sas_expander_configuration_policies', 'disk_group_policies', 'storage_profiles',
                                    'graphics_card_policies', 'kvm_management_policies', 'memory_policy',
                                    'threshold_policies', 'iscsi_authentication_profiles']

        for config_object in objects_to_push_in_order:
            if getattr(self, config_object) is not None:
                if getattr(self, config_object).__class__.__name__ == "list":
                    for subobject in getattr(self, config_object):
                        subobject.push_object()

        # HANDLING OF CHASSIS PROFILES & TEMPLATES
        # We first need to identify all Chassis Profile Templates and push them, and then push the Chassis Profiles
        # so that instantiation can find the required Template
        chassis_profile_templates = []
        chassis_profiles = []
        if self.chassis_profiles:
            for chassis_profile in self.chassis_profiles:
                if chassis_profile.type in ["initial-template", "updating-template"]:
                    chassis_profile_templates.append(chassis_profile)
                else:
                    chassis_profiles.append(chassis_profile)

        for chassis_profile_template in chassis_profile_templates:
            chassis_profile_template.push_object()

        for chassis_profile in chassis_profiles:
            if all(getattr(chassis_profile, attr) for attr in ["chassis_profile_template", "name"]):
                chassis_profile.instantiate_profile()
            else:
                chassis_profile.push_object()

        # HANDLING OF SERVICE PROFILES & TEMPLATES
        # We first need to identify all Service Profile Templates and push them, and then push the Service Profiles
        # so that instantiation can find the required Template
        service_profile_templates = []
        service_profiles = []
        if self.service_profiles:
            for service_profile in self.service_profiles:
                if service_profile.type in ["initial-template", "updating-template"]:
                    service_profile_templates.append(service_profile)
                else:
                    service_profiles.append(service_profile)

        for service_profile_template in service_profile_templates:
            service_profile_template.push_object()

        for service_profile in service_profiles:
            if all(getattr(service_profile, attr) for attr in ["service_profile_template", "name"]):
                service_profile.instantiate_profile()
            else:
                service_profile.push_object()

        return True

    def _get_generic_element(self, json_content, object_class, name_to_fetch, restrict_to_root=False):
        if self._config.load_from == "live":
            if restrict_to_root and self.name != "root":
                return []
            list_of_obj = self._config.get_config_objects_under_dn(dn=self._dn, object_class=object_class, parent=self)
            return list_of_obj
        elif self._config.load_from == "file" and json_content is not None:
            if name_to_fetch in json_content:
                return [object_class(self, generic, None) for generic in json_content[name_to_fetch]]
        else:
            return []


class UcsSystemTimezoneMgmt(UcsSystemConfigObject):
    _CONFIG_NAME = "Timezone Management"

    def __init__(self, parent=None, json_content=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.ntp = []
        self.zone = None

        if self._config.load_from == "live":
            if "commDateTime" in self._config.sdk_objects:
                comm_date_time_list = [comm_date_time for comm_date_time in self._config.sdk_objects["commDateTime"]
                                       if "sys/svc-ext/datetime-svc" in comm_date_time.dn]
                if len(comm_date_time_list) == 1:
                    comm_date_time = comm_date_time_list[0]
                    self.zone = comm_date_time.timezone

            if "commNtpProvider" in self._config.sdk_objects:
                ntp_provider_list = [ntp_provider for ntp_provider in self._config.sdk_objects["commNtpProvider"]
                                     if "sys/svc-ext/datetime-svc" in ntp_provider.dn]
                for ntp_provider in ntp_provider_list:
                    self.ntp.append(ntp_provider.name)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration")
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration" +
                                ", waiting for a commit")
        parent_mo = "sys/svc-ext"

        mo_comm_date_time = CommDateTime(parent_mo_or_dn=parent_mo, timezone=self.zone)
        for ntp in self.ntp:
            CommNtpProvider(parent_mo_or_dn=mo_comm_date_time, name=ntp)

        self._handle.add_mo(mo=mo_comm_date_time, modify_present=True)
        if commit:
            if self.commit() != True:
                return False
        return True


class UcsSystemLocale(UcsSystemConfigObject):
    _CONFIG_NAME = "Locale"

    def __init__(self, parent=None, json_content=None, aaa_locale=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.name = None
        self.descr = None
        self.organizations = []

        if self._config.load_from == "live":
            self.name = aaa_locale.name
            self.descr = aaa_locale.descr

            if "aaaOrg" in self._config.sdk_objects:
                for organization in self._config.sdk_objects["aaaOrg"]:
                    if "sys/user-ext/locale-" + self.name + "/org-" in organization.dn:
                        self.organizations.append(organization.org_dn)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration" +
                                ", waiting for a commit")

        parent_mo = "sys/user-ext"
        mo_locale = AaaLocale(parent_mo_or_dn=parent_mo, name=self.name, descr=self.descr)
        if self.organizations:
            for organization in self.organizations:
                complete_org_path = ""
                for part in organization.split("/"):
                    if "org-" not in part:
                        complete_org_path += "org-"
                    complete_org_path += part + "/"
                complete_org_path = complete_org_path[:-1]  # Remove the trailing "/"
                if not complete_org_path.startswith("org-root"):
                    complete_org_path = "org-root/" + complete_org_path

                # We use a MD5 hashing function for the name of the AaaOrg object, since UCSM automatically generates
                # a numerical ID when doing the action from the GUI.
                AaaOrg(parent_mo_or_dn=mo_locale, name=hashlib.md5(complete_org_path.encode()).hexdigest()[:16],
                       descr="", org_dn=complete_org_path)
        self._handle.add_mo(mo_locale, modify_present=True)

        if commit:
            if self.commit() != True:
                return False
        return True


class UcsSystemRole(UcsSystemConfigObject):
    _CONFIG_NAME = "Role"

    def __init__(self, parent=None, json_content=None, aaa_role=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.name = None
        self.privileges = []

        if self._config.load_from == "live":

            if aaa_role is not None:
                self.name = aaa_role.name
                role_privilege = aaa_role.priv
                if role_privilege:
                    privilege_list = role_privilege.split(',')
                    for priv in privilege_list:
                        self.privileges.append(priv)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + ": " + str(self.name))
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + str(self.name) +
                                ", waiting for a commit")

        parent_mo = "sys/user-ext"
        privileges = None
        if self.privileges:
            privileges = ",".join(self.privileges)
        mo_role = AaaRole(parent_mo_or_dn=parent_mo, name=self.name, descr="", priv=privileges)
        self._handle.add_mo(mo_role, modify_present=True)

        if commit:
            if self.commit() != True:
                return False
        return True


class UcsSystemPreLoginBanner(UcsSystemConfigObject):
    _CONFIG_NAME = "Pre-Login Banner"

    def __init__(self, parent=None, json_content=None):
        UcsSystemConfigObject.__init__(self, parent=parent)

        self.message = ""

        if self._config.load_from == "live":
            # Locating SDK objects needed to initialize
            if "aaaPreLoginBanner" in self._config.sdk_objects:
                if self._config.sdk_objects["aaaPreLoginBanner"]:
                    self.message = self._config.sdk_objects["aaaPreLoginBanner"][0].message

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration" +
                                ", waiting for a commit")

        parent_mo = "sys/user-ext"
        mo_aaa_pre_login_banner = AaaPreLoginBanner(parent_mo_or_dn=parent_mo, message=self.message)

        self._handle.add_mo(mo=mo_aaa_pre_login_banner, modify_present=True)
        if commit:
            if self.commit() != True:
                return False
        return True


class UcsSystemLocalUsersProperties(UcsSystemConfigObject):
    _CONFIG_NAME = "Local Users Properties"

    def __init__(self, parent=None, json_content=None):
        UcsSystemConfigObject.__init__(self, parent=parent)

        self.password_strength_check = None
        self.change_interval = None
        self.no_change_interval = None
        self.change_during_interval = None
        self.change_count = None
        self.history_count = None

        if self._config.load_from == "live":
            # Locating SDK objects needed to initialize
            if "aaaUserEp" in self._config.sdk_objects:
                aaa_user_ep = [user_ep for user_ep in self._config.sdk_objects["aaaUserEp"]]
                if len(aaa_user_ep):
                    self.password_strength_check = aaa_user_ep[0].pwd_strength_check
                    if "aaaPwdProfile" in self._config.sdk_objects:
                        aaa_pwd_profile = [pwd_profile for pwd_profile in self._config.sdk_objects["aaaPwdProfile"]]
                        if len(aaa_pwd_profile):
                            self.change_interval = aaa_pwd_profile[0].change_interval
                            self.no_change_interval = aaa_pwd_profile[0].no_change_interval
                            self.change_during_interval = aaa_pwd_profile[0].change_during_interval
                            self.change_count = aaa_pwd_profile[0].change_count
                            self.history_count = aaa_pwd_profile[0].history_count

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration" +
                                ", waiting for a commit")

        mo_aaa_user_ep = AaaUserEp(parent_mo_or_dn="sys", pwd_strength_check=self.password_strength_check)
        AaaPwdProfile(parent_mo_or_dn=mo_aaa_user_ep, no_change_interval=self.no_change_interval,
                      change_interval=self.change_interval,
                      history_count=self.history_count, change_count=self.change_count,
                      change_during_interval=self.change_during_interval)

        self._handle.add_mo(mo=mo_aaa_user_ep, modify_present=True)
        if commit:
            if self.commit() != True:
                return False
        return True


class UcsSystemLocalUser(UcsSystemConfigObject):
    _CONFIG_NAME = "Local User"

    def __init__(self, parent=None, json_content=None, aaa_user=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.id = None
        self.first_name = None
        self.last_name = None
        self.email = None
        self.phone = None
        self.password = None
        self.account_status = None
        self.ssh_key = None
        self.expiration = None
        self.roles = []
        self.locales = []

        if self._config.load_from == "live":
            # Locating SDK objects needed to initialize

            if aaa_user is not None:
                self.account_status = aaa_user.account_status
                self.email = aaa_user.email
                self.first_name = aaa_user.first_name
                self.id = aaa_user.name
                self.last_name = aaa_user.last_name
                self.phone = aaa_user.phone
                self.password = aaa_user.pwd

                self.logger(level="warning", message="Password of " + self._CONFIG_NAME + " " + self.id +
                            " can't be exported")

                self.expiration = aaa_user.expiration
                if self.expiration == "never":
                    self.expiration = None

                if "aaaSshAuth" in self._config.sdk_objects:
                    ssh_key = [ssh_key.data for ssh_key in self._config.sdk_objects["aaaSshAuth"]
                               if "user-" + self.id + "/" in ssh_key.dn]
                    if ssh_key:
                        self.ssh_key = ssh_key[0]

                if "aaaUserLocale" in self._config.sdk_objects:
                    locale_list = [locale for locale in self._config.sdk_objects["aaaUserLocale"]
                                   if "user-" + self.id + "/" in locale.dn]
                    for locale in locale_list:
                        self.locales.append(locale.name)

                if "aaaUserRole" in self._config.sdk_objects:
                    role_list = [role for role in self._config.sdk_objects["aaaUserRole"]
                                 if "user-" + self.id + "/" in role.dn]
                    for role in role_list:
                        self.roles.append(role.name)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + self.id)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + self.id +
                                ", waiting for a commit")

        parent_mo = "sys/user-ext"
        expires = "no"
        if self.expiration:
            expires = "yes"
        mo_user = AaaUser(parent_mo_or_dn=parent_mo, name=self.id, first_name=self.first_name, last_name=self.last_name,
                          email=self.email, phone=self.phone, pwd=self.password, account_status=self.account_status,
                          expires=expires, expiration=self.expiration)
        for locale in self.locales:
            AaaUserLocale(parent_mo_or_dn=mo_user, name=locale)
        for role in self.roles:
            AaaUserRole(parent_mo_or_dn=mo_user, name=role)

        if self.ssh_key:
            AaaSshAuth(parent_mo_or_dn=mo_user, data=self.ssh_key, str_type="key")
        self._handle.add_mo(mo_user, modify_present=True)

        if commit:
            committed = self.commit(show=False)
            if committed != True:
                # We handle this specific error
                if hasattr(committed, "error_descr"):
                    if committed.error_descr == \
                            "Password history check: user should not use the previously used password.":
                        self.logger(level="warning", message="The password history of " + self.id + " will be deleted")
                        # We add again this user but with the clear pwd history value at "yes"
                        mo_aaa_user = AaaUser(parent_mo_or_dn=parent_mo, name=self.id, first_name=self.first_name,
                                              last_name=self.last_name, email=self.email, phone=self.phone,
                                              pwd=self.password, account_status=self.account_status, expires=expires,
                                              expiration=self.expiration, clear_pwd_history="yes")
                        self._handle.add_mo(mo_aaa_user, modify_present=True)
                        if self.commit() != True:
                            return False
                    else:
                        # The print value of commit is True so we need to log the error if it is not the expected error
                        self.logger(level="error",
                                    message="Error in configuring " + self._CONFIG_NAME + ": " + committed.error_descr)
                return False
            self.logger(message="Successfully configured " + self._CONFIG_NAME + " configuration: " + self.id)
        return True


class UcsSystemGlobalPolicies(UcsSystemConfigObject):
    _CONFIG_NAME = "Global Policies"

    def __init__(self, parent=None, json_content=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.chassis_discovery_policy = []
        self.rack_server_discovery_policy = []
        self.rack_management_connection_policy = None
        self.power_policy = None
        self.mac_address_table_aging = None
        self.vlan_port_count_optimization = None
        self.org_permissions = None
        self.inband_profile_vlan_group = None
        self.inband_profile_network = None
        self.inband_profile_ip_pool_name = None
        self.global_power_allocation_policy = None
        self.firmware_auto_sync_server_policy = None
        self.global_power_profiling_policy = None
        self.info_policy = None
        self.hardware_change_discovery_policy = None
        self.fabric_a_fc_uplink_trunking = None
        self.fabric_b_fc_uplink_trunking = None

        if self._config.load_from == "live":
            # Locating SDK objects needed to initialize
            if "computeChassisDiscPolicy" in self._config.sdk_objects:
                self.chassis_discovery_policy = [{}]
                chassis_discovery_policy = self._config.sdk_objects["computeChassisDiscPolicy"][0]
                self.chassis_discovery_policy[0].update({"action_link": chassis_discovery_policy.action})
                if "-link" in self.chassis_discovery_policy[0]["action_link"]:
                    self.chassis_discovery_policy[0]["action_link"] = \
                        self.chassis_discovery_policy[0]["action_link"].split('-')[0]
                self.chassis_discovery_policy[0].update(
                    {"link_grouping_preference": chassis_discovery_policy.link_aggregation_pref})
                self.chassis_discovery_policy[0].update(
                    {"multicast_hardware_hash": chassis_discovery_policy.multicast_hw_hash})
                self.chassis_discovery_policy[0].update(
                    {"backplane_speed_preference": chassis_discovery_policy.backplane_speed_pref})

            if "computeServerDiscPolicy" in self._config.sdk_objects:
                self.rack_server_discovery_policy = [{}]
                rack_server_discovery_policy = self._config.sdk_objects["computeServerDiscPolicy"][0]
                self.rack_server_discovery_policy[0].update({"action": rack_server_discovery_policy.action})
                self.rack_server_discovery_policy[0].update(
                    {"scrub_policy": rack_server_discovery_policy.scrub_policy_name})

            if "computeServerMgmtPolicy" in self._config.sdk_objects:
                self.rack_management_connection_policy = self._config.sdk_objects["computeServerMgmtPolicy"][0].action

            if "computePsuPolicy" in self._config.sdk_objects:
                self.power_policy = self._config.sdk_objects["computePsuPolicy"][0].redundancy

            if "fabricLanCloud" in self._config.sdk_objects:
                self.mac_address_table_aging = self._config.sdk_objects["fabricLanCloud"][0].mac_aging
                self.vlan_port_count_optimization = self._config.sdk_objects["fabricLanCloud"][0].vlan_compression

            if "fabricOrgVlanPolicy" in self._config.sdk_objects:
                self.org_permissions = self._config.sdk_objects["fabricOrgVlanPolicy"][0].admin_state

            if "mgmtInbandProfile" in self._config.sdk_objects:
                self.inband_profile_vlan_group = self._config.sdk_objects["mgmtInbandProfile"][0].name
                self.inband_profile_network = self._config.sdk_objects["mgmtInbandProfile"][0].default_vlan_name
                self.inband_profile_ip_pool_name = self._config.sdk_objects["mgmtInbandProfile"][0].pool_name

            if "powerMgmtPolicy" in self._config.sdk_objects:
                self.global_power_allocation_policy = self._config.sdk_objects["powerMgmtPolicy"][0].style
                self.global_power_profiling_policy = self._config.sdk_objects["powerMgmtPolicy"][0].profiling

            if "firmwareAutoSyncPolicy" in self._config.sdk_objects:
                self.firmware_auto_sync_server_policy = self._config.sdk_objects["firmwareAutoSyncPolicy"][0].sync_state

            if "topInfoPolicy" in self._config.sdk_objects:
                self.info_policy = self._config.sdk_objects["topInfoPolicy"][0].state

            if "computeHwChangeDiscPolicy" in self._config.sdk_objects:
                self.hardware_change_discovery_policy = self._config.sdk_objects["computeHwChangeDiscPolicy"][0].action

            if "fabricFcSan" in self._config.sdk_objects:
                    for fi in self._config.sdk_objects["fabricFcSan"]:
                        if fi.id == "A":
                            self.fabric_a_fc_uplink_trunking = fi.uplink_trunking
                        elif fi.id == "B":
                            self.fabric_b_fc_uplink_trunking = fi.uplink_trunking

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration" +
                                ", waiting for a commit")

        parent_mo_root = "org-root"
        parent_mo_sys = "sys"
        parent_mo_fabric = "fabric"
        parent_mo_lan = "fabric/lan"
        parent_mo_san = "fabric/san"

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

            mo_compute_chassis_disc_policy = ComputeChassisDiscPolicy(parent_mo_or_dn=parent_mo_root,
                                                                      link_aggregation_pref=link_grouping_preference,
                                                                      action=action,
                                                                      multicast_hw_hash=multicast_hardware_hash,
                                                                      backplane_speed_pref=backplane_speed_pref)
            self._handle.add_mo(mo_compute_chassis_disc_policy, modify_present=True)
            if commit:
                if self.commit(detail="Chassis Discovery Policy") != True:
                    return False

        if self.rack_server_discovery_policy:
            action = None
            if "action" in self.rack_server_discovery_policy[0]:
                action = self.rack_server_discovery_policy[0]["action"]
            scrub_policy = None
            if "scrub_policy" in self.rack_server_discovery_policy[0]:
                scrub_policy = self.rack_server_discovery_policy[0]["scrub_policy"]

            mo_compute_server_disc_policy = ComputeServerDiscPolicy(parent_mo_or_dn=parent_mo_root, action=action,
                                                                    scrub_policy_name=scrub_policy)
            self._handle.add_mo(mo_compute_server_disc_policy, modify_present=True)
            if commit:
                if self.commit(detail="Rack Server Discovery Policy") != True:
                    return False

        if self.rack_management_connection_policy:
            mo_compute_server_mgmt_policy = ComputeServerMgmtPolicy(parent_mo_or_dn=parent_mo_root,
                                                                    action=self.rack_management_connection_policy)
            self._handle.add_mo(mo_compute_server_mgmt_policy, modify_present=True)
            if commit:
                if self.commit(detail="Rack Management Connection Policy") != True:
                    return False

        if self.power_policy:
            mo_compute_psu_policy = ComputePsuPolicy(parent_mo_or_dn=parent_mo_root, redundancy=self.power_policy)
            self._handle.add_mo(mo_compute_psu_policy, modify_present=True)
            if commit:
                if self.commit("Power Policy") != True:
                    return False

        if self.mac_address_table_aging:
            mo_fabric_lan_cloud = FabricLanCloud(parent_mo_or_dn=parent_mo_fabric,
                                                 mac_aging=self.mac_address_table_aging)
            self._handle.add_mo(mo_fabric_lan_cloud, modify_present=True)
            if commit:
                if self.commit("MAC Address Table Aging") != True:
                    return False

        if self.vlan_port_count_optimization:
            mo_fabric_lan_cloud = FabricLanCloud(parent_mo_or_dn=parent_mo_fabric,
                                                 vlan_compression=self.vlan_port_count_optimization)
            self._handle.add_mo(mo_fabric_lan_cloud, modify_present=True)
            if commit:
                if self.commit("VLAN Port Count Optimization") != True:
                    return False

        if self.org_permissions:
            mo_fabric_org_vlan_policy = FabricOrgVlanPolicy(parent_mo_or_dn=parent_mo_root,
                                                            admin_state=self.org_permissions)
            self._handle.add_mo(mo_fabric_org_vlan_policy, modify_present=True)
            if commit:
                if self.commit("Org Permissions") != True:
                    return False

        if self.inband_profile_network or self.inband_profile_vlan_group or self.inband_profile_ip_pool_name:
            mo_mgmt_inband_profile = MgmtInbandProfile(parent_mo_or_dn=parent_mo_lan,
                                                       default_vlan_name=self.inband_profile_network,
                                                       name=self.inband_profile_vlan_group,
                                                       pool_name=self.inband_profile_ip_pool_name
                                                       )
            self._handle.add_mo(mo_mgmt_inband_profile, modify_present=True)
            if commit:
                if self.commit("Inband Profile") != True:
                    return False

        if self.global_power_allocation_policy:
            if self.global_power_allocation_policy == "Policy Driven Chassis Group Cap":
                self.global_power_allocation_policy = "intelligent-policy-driven"
            elif self.global_power_allocation_policy == "Manual Blade Level Cap":
                self.global_power_allocation_policy = "manual-per-blade"
            mo_power_mgmt_policy = PowerMgmtPolicy(parent_mo_or_dn=parent_mo_root,
                                                   style=self.global_power_allocation_policy)
            self._handle.add_mo(mo_power_mgmt_policy, modify_present=True)
            if commit:
                if self.commit("Global Power Allocation Policy") != True:
                    return False

        if self.firmware_auto_sync_server_policy:
            if self.firmware_auto_sync_server_policy == "user-acknowledge":
                self.firmware_auto_sync_server_policy = "User Acknowledge"
            elif self.firmware_auto_sync_server_policy == "no-actions":
                self.firmware_auto_sync_server_policy = "No Actions"
            mo_firmware_auto_sync_policy = FirmwareAutoSyncPolicy(parent_mo_or_dn=parent_mo_root,
                                                                  sync_state=self.firmware_auto_sync_server_policy)
            self._handle.add_mo(mo_firmware_auto_sync_policy, modify_present=True)
            if commit:
                if self.commit("Firmware Auto Sync Server Policy") != True:
                    return False

        if self.global_power_profiling_policy:
            mo_power_mgmt_policy = PowerMgmtPolicy(parent_mo_or_dn=parent_mo_root,
                                                   profiling=self.global_power_profiling_policy)
            self._handle.add_mo(mo_power_mgmt_policy, modify_present=True)
            if commit:
                if self.commit("Global Power Profiling Policy") != True:
                    return False

        if self.info_policy:
            mo_top_info_policy = TopInfoPolicy(parent_mo_or_dn=parent_mo_sys, state=self.info_policy)
            self._handle.add_mo(mo_top_info_policy, modify_present=True)
            if commit:
                if self.commit("Info Policy") != True:
                    return False

        if self.hardware_change_discovery_policy:
            mo_compute_hw_change_disc_policy = ComputeHwChangeDiscPolicy(parent_mo_or_dn=parent_mo_root,
                                                                         action=self.hardware_change_discovery_policy)
            self._handle.add_mo(mo_compute_hw_change_disc_policy, modify_present=True)

            if commit:
                if self.commit("Hardware Change Discovery Policy") != True:
                    return False
        if self.fabric_a_fc_uplink_trunking or self.fabric_b_fc_uplink_trunking:
            if self.fabric_a_fc_uplink_trunking:
                mo_fabric_a_fc_san = FabricFcSan(parent_mo_or_dn=parent_mo_san, id="A",
                                                 uplink_trunking=self.fabric_a_fc_uplink_trunking)
                self._handle.add_mo(mo_fabric_a_fc_san, modify_present=True)

            if self.fabric_b_fc_uplink_trunking:
                mo_fabric_b_fc_san = FabricFcSan(parent_mo_or_dn=parent_mo_san, id="B",
                                                 uplink_trunking=self.fabric_b_fc_uplink_trunking)
                self._handle.add_mo(mo_fabric_b_fc_san, modify_present=True)

            if self.fabric_a_fc_uplink_trunking or self.fabric_b_fc_uplink_trunking:
                if commit:
                    if self.commit("FC Uplink Trunking") != True:
                        return False

        return True


class UcsSystemCommunicationServices(UcsSystemConfigObject):
    _CONFIG_NAME = "Communication Services"

    def __init__(self, parent=None, json_content=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.web_session_limits = []
        self.shell_session_limits = []
        self.cimc_web_service = None
        self.http_service = []
        self.telnet_service = None
        self.https_service = []
        self.cim_xml_service = None
        self.snmp_service = []
        self.ssh_service = None

        if self._config.load_from == "live":
            # Locating SDK objects needed to initialize
            if "commWebSvcLimits" in self._config.sdk_objects:
                self.web_session_limits = [{}]
                web_session_limits = self._config.sdk_objects["commWebSvcLimits"][0]
                self.web_session_limits[0].update({"maximum_sessions_per_user": web_session_limits.sessions_per_user})
                self.web_session_limits[0].update({"maximum_sessions": web_session_limits.total_sessions})
                self.web_session_limits[0].update({"maximum_event_interval": web_session_limits.max_event_interval})

            if "commShellSvcLimits" in self._config.sdk_objects:
                self.shell_session_limits = [{}]
                shell_session_limits = self._config.sdk_objects["commShellSvcLimits"][0]
                self.shell_session_limits[0].update(
                    {"maximum_sessions_per_user": shell_session_limits.sessions_per_user})
                self.shell_session_limits[0].update({"maximum_sessions": shell_session_limits.total_sessions})

            if "commCimcWebService" in self._config.sdk_objects:
                self.cimc_web_service = self._config.sdk_objects["commCimcWebService"][0].admin_state

            if "commHttp" in self._config.sdk_objects:
                self.http_service = [{}]
                http_service = self._config.sdk_objects["commHttp"][0]
                self.http_service[0].update({"state": http_service.admin_state})
                self.http_service[0].update({"timeout": http_service.request_timeout})
                self.http_service[0].update({"redirect_to_https": http_service.redirect_state})
                self.http_service[0].update({"port": http_service.port})

            if "commTelnet" in self._config.sdk_objects:
                self.telnet_service = self._config.sdk_objects["commTelnet"][0].admin_state

            if "commHttps" in self._config.sdk_objects:
                self.https_service = [{}]
                https_service = self._config.sdk_objects["commHttps"][0]
                self.https_service[0].update({"state": https_service.admin_state})
                self.https_service[0].update({"port": https_service.port})
                self.https_service[0].update({"keyring": https_service.key_ring})
                self.https_service[0].update({"cipher_mode": https_service.cipher_suite_mode})
                self.https_service[0].update({"custom_cipher_suite": https_service.cipher_suite})
                self.https_service[0].update({"allowed_ssl_protocols": https_service.allowed_ssl_protocols})

                if self.https_service[0]["allowed_ssl_protocols"] == "default":
                    # "default" in the UCSM GUI is "all" in the SDK
                    self.https_service[0]["allowed_ssl_protocols"] = "all"
                elif self.https_service[0]["allowed_ssl_protocols"] == "tlsv1.2":
                    self.https_service[0]["allowed_ssl_protocols"] = "tlsv1_2"

            if "commCimxml" in self._config.sdk_objects:
                self.cim_xml_service = self._config.sdk_objects["commCimxml"][0].admin_state

            if "commSnmp" in self._config.sdk_objects:
                self.snmp_service = [{}]
                snmp_service = self._config.sdk_objects["commSnmp"][0]
                self.snmp_service[0].update({"state": snmp_service.admin_state})
                self.snmp_service[0].update({"community": snmp_service.community})
                self.snmp_service[0].update({"contact": snmp_service.sys_contact})
                self.snmp_service[0].update({"location": snmp_service.sys_location})
                if "commSnmpTrap" in self._config.sdk_objects:
                    self.snmp_service[0].update({"snmp_traps": []})
                    traps = self.snmp_service[0]["snmp_traps"]
                    for snmp_trap in self._config.sdk_objects["commSnmpTrap"]:
                        trap = {}
                        trap.update({"hostname": snmp_trap.hostname})
                        trap.update({"community": snmp_trap.community})
                        trap.update({"port": snmp_trap.port})
                        trap.update({"version": snmp_trap.version})
                        trap.update({"notification_type": snmp_trap.notification_type})
                        trap.update({"v3privilege": snmp_trap.v3_privilege})
                        traps.append(trap)
                if "commSnmpUser" in self._config.sdk_objects:
                    self.snmp_service[0].update({"snmp_users": []})
                    users = self.snmp_service[0]["snmp_users"]
                    for snmp_user in self._config.sdk_objects["commSnmpUser"]:
                        user = {}
                        user.update({"name": snmp_user.name})
                        user.update({"descr": snmp_user.descr})
                        user.update({"privacy_password": snmp_user.privpwd})
                        user.update({"password": snmp_user.pwd})
                        user.update({"auth_type": snmp_user.auth})
                        user.update({"use_aes": snmp_user.use_aes})
                        users.append(user)

            if "commSsh" in self._config.sdk_objects:
                self.ssh_service = self._config.sdk_objects["commSsh"][0].admin_state

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)
                for element in self.web_session_limits:
                    for value in ["maximum_sessions_per_user", "maximum_sessions", "maximum_event_interval"]:
                        if value not in element:
                            element[value] = None
                for element in self.shell_session_limits:
                    for value in ["maximum_sessions_per_user", "maximum_sessions"]:
                        if value not in element:
                            element[value] = None
                for element in self.http_service:
                    for value in ["state", "timeout", "redirect_to_https", "port"]:
                        if value not in element:
                            element[value] = None
                for element in self.https_service:
                    for value in ["state", "port", "keyring", "cipher_mode", "custom_cipher_suite",
                                  "allowed_ssl_protocols"]:
                        if value not in element:
                            element[value] = None
                for element in self.snmp_service:
                    for value in ["state", "community", "contact", "location", "snmp_traps", "snmp_users"]:
                        if value not in element:
                            element[value] = None
                    if element["snmp_traps"]:
                        for subelement in element["snmp_traps"]:
                            for subvalue in ["hostname", "community", "port", "version", "notification_type",
                                             "v3privilege"]:
                                if subvalue not in subelement:
                                    subelement[subvalue] = None
                    if element["snmp_users"]:
                        for subelement in element["snmp_users"]:
                            for subvalue in ["name", "descr", "privacy_password", "password", "auth_type", "use_aes"]:
                                if subvalue not in subelement:
                                    subelement[subvalue] = None

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration" +
                                ", waiting for a commit")

        parent_mo_svc_ext = "sys/svc-ext"

        if self.web_session_limits:
            mo_comm_web_svc_limits = \
                CommWebSvcLimits(parent_mo_or_dn=parent_mo_svc_ext,
                                 sessions_per_user=self.web_session_limits[0]["maximum_sessions_per_user"],
                                 total_sessions=self.web_session_limits[0]["maximum_sessions"],
                                 max_event_interval=self.web_session_limits[0]["maximum_event_interval"])
            self._handle.add_mo(mo_comm_web_svc_limits, modify_present=True)
            if commit:
                if self.commit("Web Session Limits") != True:
                    return False

        if self.shell_session_limits:
            mo_comm_shell_svc_limits = \
                CommShellSvcLimits(parent_mo_or_dn=parent_mo_svc_ext,
                                   sessions_per_user=self.shell_session_limits[0]["maximum_sessions_per_user"],
                                   total_sessions=self.shell_session_limits[0]["maximum_sessions"])
            self._handle.add_mo(mo_comm_shell_svc_limits, modify_present=True)
            if commit:
                if self.commit("Shell Session Limits") != True:
                    return False

        if self.cimc_web_service:
            mo_comm_cimc_web_service = CommCimcWebService(parent_mo_or_dn=parent_mo_svc_ext,
                                                          admin_state=self.cimc_web_service)
            self._handle.add_mo(mo_comm_cimc_web_service, modify_present=True)
            if commit:
                if self.commit("CIMC Web Service") != True:
                    return False

        if self.http_service:
            mo_comm_http = CommHttp(parent_mo_or_dn=parent_mo_svc_ext,
                                    admin_state=self.http_service[0]["state"],
                                    port=self.http_service[0]["port"],
                                    redirect_state=self.http_service[0]["redirect_to_https"],
                                    request_timeout=self.http_service[0]["timeout"])
            self._handle.add_mo(mo_comm_http, modify_present=True)
            if commit:
                if self.commit("HTTP Service") != True:
                    return False

        if self.telnet_service:
            mo_comm_telnet = CommTelnet(parent_mo_or_dn=parent_mo_svc_ext, admin_state=self.telnet_service)
            self._handle.add_mo(mo_comm_telnet, modify_present=True)
            if commit:
                if self.commit("Telnet Service") != True:
                    return False

        if self.https_service:
            mo_comm_https = CommHttps(parent_mo_or_dn=parent_mo_svc_ext, admin_state=self.https_service[0]["state"],
                                      port=self.https_service[0]["port"],
                                      cipher_suite_mode=self.https_service[0]["cipher_mode"],
                                      cipher_suite=self.https_service[0]["custom_cipher_suite"],
                                      key_ring=self.https_service[0]["keyring"],
                                      allowed_ssl_protocols=self.https_service[0]["allowed_ssl_protocols"])
            self._handle.add_mo(mo_comm_https, modify_present=True)
            if commit:
                if self.commit("HTTPS Service") != True:
                    return False

        if self.cim_xml_service:
            mo_comm_cimxml = CommCimxml(parent_mo_or_dn=parent_mo_svc_ext, admin_state=self.cim_xml_service)
            self._handle.add_mo(mo_comm_cimxml, modify_present=True)
            if commit:
                if self.commit("CIM XML Service") != True:
                    return False

        if self.snmp_service:
            mo_comm_snmp = CommSnmp(parent_mo_or_dn=parent_mo_svc_ext, admin_state=self.snmp_service[0]["state"],
                                    community=self.snmp_service[0]["community"],
                                    sys_contact=self.snmp_service[0]["contact"],
                                    sys_location=self.snmp_service[0]["location"])

            if self.snmp_service[0]["snmp_users"]:
                for user in self.snmp_service[0]["snmp_users"]:
                    CommSnmpUser(parent_mo_or_dn=mo_comm_snmp, name=user["name"], descr=user["descr"],
                                 pwd=user["password"], privpwd=user["privacy_password"], auth=user["auth_type"],
                                 use_aes=user["use_aes"])
            if self.snmp_service[0]["snmp_traps"]:
                for trap in self.snmp_service[0]["snmp_traps"]:
                    CommSnmpTrap(parent_mo_or_dn=mo_comm_snmp, hostname=trap["hostname"], community=trap["community"],
                                 port=trap["port"], version=trap["version"],
                                 notification_type=trap["notification_type"], v3_privilege=trap["v3privilege"])

            self._handle.add_mo(mo_comm_snmp, modify_present=True)
            if commit:
                if self.commit("SNMP Service") != True:
                    return False

        if self.ssh_service:
            mo_comm_ssh = CommSsh(parent_mo_or_dn=parent_mo_svc_ext, admin_state=self.ssh_service)
            self._handle.add_mo(mo_comm_ssh, modify_present=True)
            if commit:
                if self.commit("SSH Service") != True:
                    return False

        return True


class UcsSystemBackupExportPolicy(UcsSystemConfigObject):
    _CONFIG_NAME = "Backup Export Policy"

    def __init__(self, parent=None, json_content=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.full_state = []
        self.all_configuration = []
        self.reminder = []

        if self._config.load_from == "live":
            # Locating SDK objects needed to initialize
            if "mgmtBackupPolicy" in self._config.sdk_objects:
                self.full_state = [{}]
                full_state = self._config.sdk_objects["mgmtBackupPolicy"][0]
                self.full_state[0].update({"hostname": full_state.host})
                self.full_state[0].update({"protocol": full_state.proto})
                self.full_state[0].update({"user": full_state.user})
                self.full_state[0].update({"password": full_state.pwd})
                self.full_state[0].update({"remote_file": full_state.remote_file})
                self.full_state[0].update({"admin_state": full_state.admin_state})
                self.full_state[0].update({"schedule": full_state.schedule})
                self.full_state[0].update({"descr": full_state.descr})

            if "mgmtCfgExportPolicy" in self._config.sdk_objects:
                self.all_configuration = [{}]
                all_configuration = self._config.sdk_objects["mgmtCfgExportPolicy"][0]
                self.all_configuration[0].update({"hostname": all_configuration.host})
                self.all_configuration[0].update({"protocol": all_configuration.proto})
                self.all_configuration[0].update({"user": all_configuration.user})
                self.all_configuration[0].update({"password": all_configuration.pwd})
                self.all_configuration[0].update({"remote_file": all_configuration.remote_file})
                self.all_configuration[0].update({"admin_state": all_configuration.admin_state})
                self.all_configuration[0].update({"schedule": all_configuration.schedule})
                self.all_configuration[0].update({"descr": all_configuration.descr})

            if "mgmtBackupExportExtPolicy" in self._config.sdk_objects:
                self.reminder = [{}]
                reminder = self._config.sdk_objects["mgmtBackupExportExtPolicy"][0]
                self.reminder[0].update({"admin_state": reminder.admin_state})
                self.reminder[0].update({"remind_me_after": reminder.frequency})

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)
                for element in self.full_state:
                    for value in ["hostname", "protocol", "user", "password", "remote_file", "admin_state",
                                  "schedule", "descr"]:
                        if value not in element:
                            element[value] = None
                for element in self.all_configuration:
                    for value in ["hostname", "protocol", "user", "password", "remote_file", "admin_state",
                                  "schedule", "descr"]:
                        if value not in element:
                            element[value] = None
                for element in self.reminder:
                    for value in ["admin_state", "remind_me_after"]:
                        if value not in element:
                            element[value] = None

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration" +
                                ", waiting for a commit")

        parent_mo = "org-root"

        if self.full_state:
            schedule = self.full_state[0]["schedule"]
            if self.full_state[0]["schedule"] == "daily":
                schedule = "1day"
            if self.full_state[0]["schedule"] == "weekly":
                schedule = "1week"
            if self.full_state[0]["schedule"] in ["bi-weekly", "bi_weekly", "bi weekly"]:
                schedule = "2week"

            mo_mgmt_backup_policy = MgmtBackupPolicy(parent_mo_or_dn=parent_mo, descr=self.full_state[0]["descr"],
                                                     proto=self.full_state[0]["protocol"],
                                                     admin_state=self.full_state[0]["admin_state"],
                                                     pwd=self.full_state[0]["password"],
                                                     user=self.full_state[0]["user"],
                                                     host=self.full_state[0]["hostname"],
                                                     remote_file=self.full_state[0]["remote_file"],
                                                     schedule=schedule, name="default")
            self._handle.add_mo(mo_mgmt_backup_policy, modify_present=True)
            if commit:
                if self.commit(detail="Full state") != True:
                    return False

        if self.all_configuration:
            schedule = self.all_configuration[0]["schedule"]
            if self.all_configuration[0]["schedule"] == "daily":
                schedule = "1day"
            if self.all_configuration[0]["schedule"] == "weekly":
                schedule = "1week"
            if self.all_configuration[0]["schedule"] in ["bi-weekly", "bi_weekly", "bi weekly"]:
                schedule = "2week"

            mo_mgmt_cfg_export_policy = MgmtCfgExportPolicy(parent_mo_or_dn=parent_mo,
                                                            descr=self.all_configuration[0]["descr"],
                                                            proto=self.all_configuration[0]["protocol"],
                                                            admin_state=self.all_configuration[0]["admin_state"],
                                                            pwd=self.all_configuration[0]["password"],
                                                            user=self.all_configuration[0]["user"],
                                                            host=self.all_configuration[0]["hostname"],
                                                            remote_file=self.all_configuration[0]["remote_file"],
                                                            schedule=schedule, name="default")
            self._handle.add_mo(mo_mgmt_cfg_export_policy, modify_present=True)
            if commit:
                if self.commit(detail="All configuration") != True:
                    return False

        if self.reminder:
            mo_mgmt_backup_export_ext_policy = MgmtBackupExportExtPolicy(parent_mo_or_dn=parent_mo,
                                                                         frequency=self.reminder[0]["remind_me_after"],
                                                                         admin_state=self.reminder[0]["admin_state"])
            self._handle.add_mo(mo_mgmt_backup_export_ext_policy, modify_present=True)
            if commit:
                if self.commit(detail="Reminder") != True:
                    return False

        return True


class UcsSystemSelPolicy(UcsSystemConfigObject):
    _CONFIG_NAME = "SEL Policy"

    def __init__(self, parent=None, json_content=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.description = None
        self.action = []
        self.protocol = None
        self.hostname = None
        self.remote_path = None
        self.backup_interval = None
        self.format = None
        self.clear_on_backup = None
        self.user = None
        self.password = None

        if self._config.load_from == "live":
            # Locating SDK objects needed to initialize
            if "sysdebugMEpLogPolicy" in self._config.sdk_objects:
                self.description = self._config.sdk_objects["sysdebugMEpLogPolicy"][0].descr
            if "sysdebugBackupBehavior" in self._config.sdk_objects:
                self.action = [action for action in
                               self._config.sdk_objects["sysdebugBackupBehavior"][0].action.split(',') if action != ""]
                self.protocol = self._config.sdk_objects["sysdebugBackupBehavior"][0].proto
                self.hostname = self._config.sdk_objects["sysdebugBackupBehavior"][0].hostname
                self.remote_path = self._config.sdk_objects["sysdebugBackupBehavior"][0].remote_path
                self.backup_interval = self._config.sdk_objects["sysdebugBackupBehavior"][0].interval
                self.format = self._config.sdk_objects["sysdebugBackupBehavior"][0].format
                self.clear_on_backup = self._config.sdk_objects["sysdebugBackupBehavior"][0].clear_on_backup
                self.user = self._config.sdk_objects["sysdebugBackupBehavior"][0].user
                self.password = self._config.sdk_objects["sysdebugBackupBehavior"][0].pwd

                self.logger(level="warning", message="Password of " + self._CONFIG_NAME + " " + self.hostname +
                                                     " can't be exported")

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration" +
                                ", waiting for a commit")

        parent_mo = "org-root"

        mo_sysdebug_mpe_log_policy = SysdebugMEpLogPolicy(parent_mo_or_dn=parent_mo, descr=self.description, type="SEL")
        SysdebugBackupBehavior(parent_mo_or_dn=mo_sysdebug_mpe_log_policy, action=','.join(self.action),
                               clear_on_backup=self.clear_on_backup,
                               format=self.format,
                               hostname=self.hostname, interval=self.backup_interval, proto=self.protocol,
                               remote_path=self.remote_path,
                               user=self.user, pwd=self.password)
        self._handle.add_mo(mo_sysdebug_mpe_log_policy, modify_present=True)

        if commit:
            if self.commit() != True:
                return False
        return True


class UcsSystemUcsCentral(UcsSystemConfigObject):
    _CONFIG_NAME = "UCS Central"

    def __init__(self, parent=None, json_content=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.ip_address = None
        self.shared_secret = None
        self.cleanup_mode = None
        self.suspend_state = None
        self.ack_state = None
        self.policy_resolution_control = []

        if self._config.load_from == "live":
            # Locating SDK objects needed to initialize
            if "policyControlEp" in self._config.sdk_objects:
                self.ip_address = self._config.sdk_objects["policyControlEp"][0].svc_reg_name
                self.shared_secret = self._config.sdk_objects["policyControlEp"][0].secret
                self.cleanup_mode = self._config.sdk_objects["policyControlEp"][0].cleanup_mode
                self.suspend_state = self._config.sdk_objects["policyControlEp"][0].suspend_state
                self.ack_state = self._config.sdk_objects["policyControlEp"][0].ack_state

                self.logger(level="warning", message="Password of " + self._CONFIG_NAME + " can't be exported")

                if 'policyCommunication'or 'policyConfigBackup' or 'policyDateTime' or 'policyDns' or 'policyEquipment'\
                        or 'policyFault' or 'policyInfraFirmware' or 'policyMEp' or 'policyMonitoring'\
                        or 'policyPortConfig' or 'policyPowerMgmt' or 'policyPsu'\
                        or 'policySecurity' in self._config.sdk_objects:
                    self.policy_resolution_control = [{}]

                if "policyInfraFirmware" in self._config.sdk_objects:
                    policy_infra_firmware = self._config.sdk_objects["policyInfraFirmware"][0].source
                    if policy_infra_firmware == "policy":
                        policy_infra_firmware = "global"
                    self.policy_resolution_control[0].update({"infrastructure_catalog_firmware": policy_infra_firmware})

                if "policyDateTime" in self._config.sdk_objects:
                    timezone_management = self._config.sdk_objects["policyDateTime"][0].source
                    if timezone_management == "policy":
                        timezone_management = "global"
                    self.policy_resolution_control[0].update({"timezone_management": timezone_management})

                if "policyCommunication" in self._config.sdk_objects:
                    policy_communication = self._config.sdk_objects["policyCommunication"][0].source
                    if policy_communication == "policy":
                        policy_communication = "global"
                    self.policy_resolution_control[0].update({"communication_services": policy_communication})

                if "policyFault" in self._config.sdk_objects:
                    policy_fault = self._config.sdk_objects["policyFault"][0].source
                    if policy_fault == "policy":
                        policy_fault = "global"
                    self.policy_resolution_control[0].update({"global_fault_policy": policy_fault})

                if "policySecurity" in self._config.sdk_objects:
                    policy_security = self._config.sdk_objects["policySecurity"][0].source
                    if policy_security == "policy":
                        policy_security = "global"
                    self.policy_resolution_control[0].update({"user_management": policy_security})

                if "policyDns" in self._config.sdk_objects:
                    policy_dns = self._config.sdk_objects["policyDns"][0].source
                    if policy_dns == "policy":
                        policy_dns = "global"
                    self.policy_resolution_control[0].update({"dns_management": policy_dns})

                if "policyConfigBackup" in self._config.sdk_objects:
                    policy_config_backup = self._config.sdk_objects["policyConfigBackup"][0].source
                    if policy_config_backup == "policy":
                        policy_config_backup = "global"
                    self.policy_resolution_control[0].update({"backup_export_policies": policy_config_backup})

                if "policyMonitoring" in self._config.sdk_objects:
                    policy_monitoring = self._config.sdk_objects["policyMonitoring"][0].source
                    if policy_monitoring == "policy":
                        policy_monitoring = "global"
                    self.policy_resolution_control[0].update({"monitoring": policy_monitoring})

                if "policyMEp" in self._config.sdk_objects:
                    policy_mep = self._config.sdk_objects["policyMEp"][0].source
                    if policy_mep == "policy":
                        policy_mep = "global"
                    self.policy_resolution_control[0].update({"sel_policy": policy_mep})

                if "policyPowerMgmt" in self._config.sdk_objects:
                    policy_power_mgmt = self._config.sdk_objects["policyPowerMgmt"][0].source
                    if policy_power_mgmt == "policy":
                        policy_power_mgmt = "global"
                    self.policy_resolution_control[0].update({"power_allocation_policy": policy_power_mgmt})

                if "policyPsu" in self._config.sdk_objects:
                    policy_psu = self._config.sdk_objects["policyPsu"][0].source
                    if policy_psu == "policy":
                        policy_psu = "global"
                    self.policy_resolution_control[0].update({"power_policy": policy_psu})

                if "policyEquipment" in self._config.sdk_objects:
                    policy_equipment = self._config.sdk_objects["policyEquipment"][0].source
                    if policy_equipment == "policy":
                        policy_equipment = "global"
                    self.policy_resolution_control[0].update({"equipment_policy": policy_equipment})

                if "policyPortConfig" in self._config.sdk_objects:
                    policy_port_config = self._config.sdk_objects["policyPortConfig"][0].source
                    if policy_port_config == "policy":
                        policy_port_config = "global"
                    self.policy_resolution_control[0].update({"port_configuration": policy_port_config})

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()
        # We need an exception to clean_object() for shared _secret because it is a mandatory value
        if not self.shared_secret:
            self.shared_secret = ""

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration" +
                                ", waiting for a commit")
        parent_mo = "sys"
        mo_policy_control_ep = PolicyControlEp(parent_mo_or_dn=parent_mo, type="policy", secret=self.shared_secret,
                                               suspend_state=self.suspend_state, ack_state=self.ack_state,
                                               svc_reg_name=self.ip_address, cleanup_mode=self.cleanup_mode)
        if self.policy_resolution_control:
            if "infrastructure_catalog_firmware" in self.policy_resolution_control[0]:
                source = self.policy_resolution_control[0]["infrastructure_catalog_firmware"]
                if source == "global":
                    source = "policy"
                PolicyInfraFirmware(parent_mo_or_dn=mo_policy_control_ep, source=source)

            if 'timezone_management' in self.policy_resolution_control[0]:
                source = self.policy_resolution_control[0]['timezone_management']
                if source == "global":
                    source = "policy"
                PolicyDateTime(parent_mo_or_dn=mo_policy_control_ep, source=source)

            if 'communication_services' in self.policy_resolution_control[0]:
                source = self.policy_resolution_control[0]['communication_services']
                if source == "global":
                    source = "policy"
                PolicyCommunication(parent_mo_or_dn=mo_policy_control_ep, source=source)

            if 'global_fault_policy' in self.policy_resolution_control[0]:
                source = self.policy_resolution_control[0]['global_fault_policy']
                if source == "global":
                    source = "policy"
                PolicyFault(parent_mo_or_dn=mo_policy_control_ep, source=source)

            if 'user_management' in self.policy_resolution_control[0]:
                source = self.policy_resolution_control[0]['user_management']
                if source == "global":
                    source = "policy"
                PolicySecurity(parent_mo_or_dn=mo_policy_control_ep, source=source)

            if 'dns_management' in self.policy_resolution_control[0]:
                source = self.policy_resolution_control[0]['dns_management']
                if source == "global":
                    source = "policy"
                PolicyDns(parent_mo_or_dn=mo_policy_control_ep, source=source)

            if 'backup_export_policies' in self.policy_resolution_control[0]:
                source = self.policy_resolution_control[0]['backup_export_policies']
                if source == "global":
                    source = "policy"
                PolicyConfigBackup(parent_mo_or_dn=mo_policy_control_ep, source=source)

            if 'monitoring' in self.policy_resolution_control[0]:
                source = self.policy_resolution_control[0]['monitoring']
                if source == "global":
                    source = "policy"
                PolicyMonitoring(parent_mo_or_dn=mo_policy_control_ep, source=source)

            if 'sel_policy' in self.policy_resolution_control[0]:
                source = self.policy_resolution_control[0]['sel_policy']
                if source == "global":
                    source = "policy"
                PolicyMEp(parent_mo_or_dn=mo_policy_control_ep, source=source)

            if 'power_allocation_policy' in self.policy_resolution_control[0]:
                source = self.policy_resolution_control[0]['power_allocation_policy']
                if source == "global":
                    source = "policy"
                PolicyPowerMgmt(parent_mo_or_dn=mo_policy_control_ep, source=source)

            if 'power_policy' in self.policy_resolution_control[0]:
                source = self.policy_resolution_control[0]['power_policy']
                if source == "global":
                    source = "policy"
                PolicyPsu(parent_mo_or_dn=mo_policy_control_ep, source=source)

            if 'equipment_policy' in self.policy_resolution_control[0]:
                source = self.policy_resolution_control[0]['equipment_policy']
                if source == "global":
                    source = "policy"
                PolicyEquipment(parent_mo_or_dn=mo_policy_control_ep, source=source)

            if 'port_configuration' in self.policy_resolution_control[0]:
                source = self.policy_resolution_control[0]['port_configuration']
                if source == "global":
                    source = "policy"
                PolicyPortConfig(parent_mo_or_dn=mo_policy_control_ep, source=source)

        self._handle.add_mo(mo_policy_control_ep, modify_present=True)
        if commit:
            if self.commit() != True:
                return False
        return True


class UcsSystemSwitchingMode(UcsSystemConfigObject):
    _CONFIG_NAME = "Switching Mode"

    def __init__(self, parent=None, json_content=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.ethernet_mode = None
        self.fc_mode = None

        if self._config.load_from == "live":
            # Locating SDK objects needed to initialize
            if "fabricLanCloud" in self._config.sdk_objects:
                self.ethernet_mode = self._config.sdk_objects["fabricLanCloud"][0].mode
            if "fabricSanCloud" in self._config.sdk_objects:
                self.fc_mode = self._config.sdk_objects["fabricSanCloud"][0].mode

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration" +
                                ", waiting for a commit")

        if not self._parent.check_if_switching_mode_config_requires_reboot():
            self.logger(message="Switching Modes already configured. Skipping")
            return True

        parent_mo = "fabric"
        mo_san = FabricSanCloud(parent_mo_or_dn=parent_mo, mode=self.fc_mode)
        mo_lan = FabricLanCloud(parent_mo_or_dn=parent_mo, mode=self.ethernet_mode)

        self._handle.add_mo(mo=mo_lan, modify_present=True)
        self._handle.add_mo(mo=mo_san, modify_present=True)

        if commit:
            if self.commit() != True:
                return False

            # Handling the reboot
            if self._device.sys_mode == "cluster":
                fabric_lan_cloud_mo = self._device.query(mode="dn", target="fabric/lan")
                fabric_san_cloud_mo = self._device.query(mode="dn", target="fabric/san")

                mo_list = [fabric_lan_cloud_mo, fabric_san_cloud_mo]
                for mo in mo_list:
                    if mo.fsm_progr != "100":
                        if mo.fsm_status != "SwitchModeWaitForUserAck":
                            self.logger(message="Please wait up to 720 seconds while the secondary " +
                                                "Fabric Interconnect is rebooting")
                            if not self._device.wait_for_fsm_status(ucs_sdk_object_dn=mo.dn,
                                                                    status="SwitchModeWaitForUserAck", timeout=720):
                                self.logger(level="error",
                                            message="Timeout exceeded while waiting for FSM state of switching mode " +
                                                    "to reach UserAck state")
                                return False
                            break

                # Sending the user-ack
                self.logger(message="Secondary Fabric Interconnect is back, sending user-acknowledgement")
                mo_ack = FirmwareAck(parent_mo_or_dn="sys/fw-system", admin_state="trigger-immediate")
                self._handle.add_mo(mo=mo_ack, modify_present=True)
                if self.commit(detail="User-acknowledgement") != True:
                    return False

                # Handling reboot of primary FI
                self.logger(message="Caution: The system will reboot in a few seconds!")
                self.logger(message="Waiting up to 720 seconds for the primary FI to come back")
                time.sleep(240)
                if not common.check_web_page(device=self._device, url="https://" + self._device.target,
                                             str_match="Cisco", timeout=480):
                    self.logger(level="error", message="Impossible to reconnect to UCS system")
                    return False

                # Need to reconnect
                if not self._device.connect():
                    self.logger(level="error", message="Impossible to reconnect to UCS system")
                    return False
                self.logger(message="Reconnected to UCS system: " + self._device.name + " running version: "
                            + self._device.version.version)

                # Check the FSM State after reboot of primary FI
                self.logger(message="Waiting up to 120 seconds for the FSM state of LAN switching mode to reach 100%")
                if not self._device.wait_for_fsm_complete(ucs_sdk_object_class="fabricLanCloud", timeout=120):
                    self.logger(level="error", message="Timeout exceeded while waiting for FSM state of LAN switching" +
                                " mode to reach 100%")
                    return False
                self.logger(message="Waiting up to 120 seconds for the FSM state of SAN switching mode to reach 100%")
                if not self._device.wait_for_fsm_complete(ucs_sdk_object_class="fabricSanCloud", timeout=120):
                    self.logger(level="error", message="Timeout exceeded while waiting for FSM state of SAN switching" +
                                " mode to reach 100%")
                    return False

                return True

            elif self._device.sys_mode == "stand-alone":

                fabric_lan_cloud_mo = self._device.query(mode="dn", target="fabric/lan")
                fabric_san_cloud_mo = self._device.query(mode="dn", target="fabric/san")

                mo_list = [fabric_lan_cloud_mo, fabric_san_cloud_mo]
                for mo in mo_list:
                    if mo.fsm_progr != "100":
                        if mo.fsm_status != "SwitchModeWaitForUserAck":
                            self.logger(message="Please wait for Switching Mode to be processed before reboot")
                            if not self._device.wait_for_fsm_status(ucs_sdk_object_dn=mo.dn,
                                                                    status="SwitchModeWaitForUserAck", timeout=300):
                                self.logger(level="error",
                                            message="Timeout exceeded while waiting for FSM state of switching mode " +
                                                    "to reach UserAck state")
                                return False
                            break

                # Sending the user-ack
                self.logger(message="Sending user-acknowledgement")
                mo_ack = FirmwareAck(parent_mo_or_dn="sys/fw-system", admin_state="trigger-immediate")
                self._handle.add_mo(mo=mo_ack, modify_present=True)
                if self.commit(detail="User-acknowledgement") != True:
                    return False

                # Handling reboot of the FI
                self.logger(message="Caution: The system will reboot in a few seconds!")
                self.logger(message="Waiting up to 720 seconds for the FI to come back")
                time.sleep(240)
                if not common.check_web_page(device=self._device, url="https://" + self._device.target,
                                             str_match="Cisco", timeout=480):
                    self.logger(level="error", message="Impossible to reconnect to UCS system")
                    return False

                # Need to reconnect
                if not self._device.connect():
                    self.logger(level="error", message="Impossible to reconnect to UCS system")
                    return False
                self.logger(message="Reconnected to UCS system: " + self._device.name + " running version: "
                                    + self._device.version.version)

                # Check the FSM State after reboot of FI
                self.logger(
                    message="Waiting up to 120 seconds for the FSM state of LAN switching mode to reach 100%")
                if not self._device.wait_for_fsm_complete(ucs_sdk_object_class="fabricLanCloud",
                                                          timeout=120):
                    self.logger(level="error",
                                message="Timeout exceeded while waiting for FSM state of LAN switching" +
                                        " mode to reach 100%")
                    return False
                self.logger(
                    message="Waiting up to 120 seconds for the FSM state of SAN switching mode to reach 100%")
                if not self._device.wait_for_fsm_complete(ucs_sdk_object_class="fabricSanCloud",
                                                          timeout=120):
                    self.logger(level="error",
                                message="Timeout exceeded while waiting for FSM state of SAN switching" +
                                        " mode to reach 100%")
                    return False

                return True


class UcsSystemRadius(UcsSystemConfigObject):
    _CONFIG_NAME = "RADIUS"

    def __init__(self, parent=None, json_content=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.timeout = None
        self.retries = None
        self.providers = []
        self.provider_groups = []

        if self._config.load_from == "live":
            # Locating SDK objects needed to initialize
            if "aaaRadiusEp" in self._config.sdk_objects:
                self.timeout = self._config.sdk_objects["aaaRadiusEp"][0].timeout
                self.retries = self._config.sdk_objects["aaaRadiusEp"][0].retries

            if "aaaRadiusProvider" in self._config.sdk_objects:
                for radius_provider in self._config.sdk_objects["aaaRadiusProvider"]:
                    provider = {}
                    provider.update({"hostname": radius_provider.name})
                    provider.update({"timeout": radius_provider.timeout})
                    provider.update({"port": radius_provider.auth_port})
                    provider.update({"key": radius_provider.key})
                    provider.update({"order": radius_provider.order})
                    provider.update({"retries": radius_provider.retries})
                    self.providers.append(provider)

            if "aaaProviderGroup" in self._config.sdk_objects:
                for aaa_provider_group in [aaa_provider_group for aaa_provider_group in
                                           self._config.sdk_objects["aaaProviderGroup"]
                                           if "sys/radius-ext/" in aaa_provider_group.dn]:
                    provider_group = {}
                    provider_group.update({"name": aaa_provider_group.name})

                    provider_ref = []
                    if "aaaProviderRef" in self._config.sdk_objects:
                        for aaa_provider_ref in [aaa_provider_ref for aaa_provider_ref in
                                                 self._config.sdk_objects["aaaProviderRef"]
                                                 if "sys/radius-ext/" in aaa_provider_ref.dn]:
                            provider_ref.append(aaa_provider_ref.name)
                    provider_group["included_providers"] = provider_ref
                    self.provider_groups.append(provider_group)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)
                for element in self.providers:
                    for value in ["hostname", "timeout", "port", "key", "order", "retries"]:
                        if value not in element:
                            element[value] = None
                for element in self.provider_groups:
                    for value in ["name", "included_providers"]:
                        if value not in element:
                            element[value] = None

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration" +
                                ", waiting for a commit")

        mo_sys = "sys"
        mo_aaa_radius_ep = AaaRadiusEp(parent_mo_or_dn=mo_sys, timeout=self.timeout, retries=self.retries)
        if self.providers:
            for provider in self.providers:
                AaaRadiusProvider(parent_mo_or_dn=mo_aaa_radius_ep, timeout=provider["timeout"],
                                  name=provider["hostname"], key=provider["key"], auth_port=provider["port"],
                                  order=provider["order"], retries=provider["retries"])
        if self.provider_groups:
            for group in self.provider_groups:
                mo_aaa_provider_group = AaaProviderGroup(parent_mo_or_dn=mo_aaa_radius_ep, name=group["name"])
                if "included_providers" in group:
                    for provider in group["included_providers"]:
                        AaaProviderRef(parent_mo_or_dn=mo_aaa_provider_group, name=provider)

        self._handle.add_mo(mo_aaa_radius_ep, modify_present=True)
        if commit:
            if self.commit() != True:
                return False
        return True


class UcsSystemTacacs(UcsSystemConfigObject):
    _CONFIG_NAME = "TACACS"

    def __init__(self, parent=None, json_content=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.timeout = None
        self.providers = []
        self.provider_groups = []

        if self._config.load_from == "live":
            # Locating SDK objects needed to initialize
            if "aaaTacacsPlusEp" in self._config.sdk_objects:
                self.timeout = self._config.sdk_objects["aaaTacacsPlusEp"][0].timeout

            if "aaaTacacsPlusProvider" in self._config.sdk_objects:
                for tacacs_provider in self._config.sdk_objects["aaaTacacsPlusProvider"]:
                    provider = {}
                    provider.update({"hostname": tacacs_provider.name})
                    provider.update({"timeout": tacacs_provider.timeout})
                    provider.update({"port": tacacs_provider.port})
                    provider.update({"key": tacacs_provider.key})
                    provider.update({"order": tacacs_provider.order})
                    self.providers.append(provider)

            if "aaaProviderGroup" in self._config.sdk_objects:
                for aaa_provider_group in [aaa_provider_group for aaa_provider_group in
                                           self._config.sdk_objects["aaaProviderGroup"]
                                           if "sys/tacacs-ext/" in aaa_provider_group.dn]:
                    provider_group = {}
                    provider_group.update({"name": aaa_provider_group.name})

                    provider_ref = []
                    if "aaaProviderRef" in self._config.sdk_objects:
                        for aaa_provider_ref in [aaa_provider_ref for aaa_provider_ref in
                                                 self._config.sdk_objects["aaaProviderRef"]
                                                 if "sys/tacacs-ext/" in aaa_provider_ref.dn]:
                            provider_ref.append(aaa_provider_ref.name)
                    provider_group["included_providers"] = provider_ref
                    self.provider_groups.append(provider_group)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)
                for element in self.providers:
                    for value in ["hostname", "timeout", "port", "key", "order"]:
                        if value not in element:
                            element[value] = None
                for element in self.provider_groups:
                    for value in ["name", "included_providers"]:
                        if value not in element:
                            element[value] = None

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration" +
                                ", waiting for a commit")

        mo_sys = "sys"
        mo_aaa_tacacs_ep = AaaTacacsPlusEp(parent_mo_or_dn=mo_sys, timeout=self.timeout)
        if self.providers:
            for provider in self.providers:
                AaaTacacsPlusProvider(parent_mo_or_dn=mo_aaa_tacacs_ep, timeout=provider["timeout"],
                                      name=provider["hostname"], key=provider["key"], port=provider["port"],
                                      order=provider["order"])
        if self.provider_groups:
            for group in self.provider_groups:
                mo_aaa_provider_group = AaaProviderGroup(parent_mo_or_dn=mo_aaa_tacacs_ep, name=group["name"])
                if "included_providers" in group:
                    for provider in group["included_providers"]:
                        AaaProviderRef(parent_mo_or_dn=mo_aaa_provider_group, name=provider)

        self._handle.add_mo(mo_aaa_tacacs_ep, modify_present=True)

        if commit:
            if self.commit() != True:
                return False
        return True


class UcsSystemLdap(UcsSystemConfigObject):
    _CONFIG_NAME = "LDAP"

    def __init__(self, parent=None, json_content=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.timeout = None
        self.attribute = None
        self.filter = None
        self.base_dn = None
        self.providers = []
        self.provider_groups = []
        self.group_maps = []

        if self._config.load_from == "live":
            # Locating SDK objects needed to initialize
            if "aaaLdapEp" in self._config.sdk_objects:
                self.timeout = self._config.sdk_objects["aaaLdapEp"][0].timeout
                self.base_dn = self._config.sdk_objects["aaaLdapEp"][0].basedn
                self.filter = self._config.sdk_objects["aaaLdapEp"][0].filter
                self.attribute = self._config.sdk_objects["aaaLdapEp"][0].attribute

            if "aaaProviderGroup" in self._config.sdk_objects:
                for aaa_provider_group in [aaa_provider_group for aaa_provider_group in
                                           self._config.sdk_objects["aaaProviderGroup"]
                                           if "sys/ldap-ext/" in aaa_provider_group.dn]:
                    provider_group = {}
                    provider_group.update({"name": aaa_provider_group.name})

                    provider_ref = []
                    if "aaaProviderRef" in self._config.sdk_objects:
                        for aaa_provider_ref in [aaa_provider_ref for aaa_provider_ref in
                                                 self._config.sdk_objects["aaaProviderRef"]
                                                 if "sys/ldap-ext/" in aaa_provider_ref.dn]:
                            provider_ref.append(aaa_provider_ref.name)
                    provider_group["included_providers"] = provider_ref
                    self.provider_groups.append(provider_group)

            if "aaaLdapProvider" in self._config.sdk_objects:
                for ldap_group in self._config.sdk_objects["aaaLdapProvider"]:
                    provider = {}
                    provider.update({"bind_dn": ldap_group.rootdn})
                    provider.update({"vendor": ldap_group.vendor})
                    provider.update({"password": ldap_group.key})
                    provider.update({"port": ldap_group.port})
                    provider.update({"attribute": ldap_group.attribute})
                    provider.update({"timeout": ldap_group.timeout})
                    provider.update({"hostname": ldap_group.name})
                    provider.update({"base_dn": ldap_group.basedn})
                    provider.update({"ssl": ldap_group.enable_ssl})
                    provider.update({"filter": ldap_group.filter})
                    provider.update({"order": ldap_group.order})
                    if "aaaLdapGroupRule" in self._config.sdk_objects:
                        for group_rule in [group_rule for group_rule in self._config.sdk_objects["aaaLdapGroupRule"]
                                           if "sys/ldap-ext/provider-" + ldap_group.name in group_rule.dn]:
                            provider.update({"target_attribute": group_rule.target_attr})
                            provider.update({"use_primary_group": group_rule.use_primary_group})
                            provider.update({"group_authorization": group_rule.authorization})
                            provider.update({"group_recursion": group_rule.traversal})
                    self.providers.append(provider)

            if "aaaLdapGroup" in self._config.sdk_objects:
                for ldap_group in self._config.sdk_objects["aaaLdapGroup"]:
                    group_map = {}
                    group_map.update({"group_dn": ldap_group.name})
                    if "aaaUserRole" in self._config.sdk_objects:
                        group_map["roles"] = []
                        for role in [role for role in self._config.sdk_objects["aaaUserRole"]
                                     if "sys/ldap-ext/ldapgroup-" + ldap_group.name in role.dn]:
                            group_map["roles"].append(role.name)

                    if "aaaUserLocale" in self._config.sdk_objects:
                        group_map["locales"] = []
                        for role in [role for role in self._config.sdk_objects["aaaUserLocale"]
                                     if "sys/ldap-ext/ldapgroup-" + ldap_group.name in role.dn]:
                            group_map["locales"].append(role.name)

                    self.group_maps.append(group_map)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)
                for element in self.providers:
                    for value in ["bind_dn", "vendor", "password", "port", "attribute", "timeout", "hostname",
                                  "base_dn", "ssl", "filter", "order", "group_authorization", "group_recursion",
                                  "target_attribute", "use_primary_group"]:
                        if value not in element:
                            element[value] = None
                for element in self.provider_groups:
                    for value in ["name", "included_providers"]:
                        if value not in element:
                            element[value] = None
                for element in self.group_maps:
                    for value in ["group_dn", "roles", "locales"]:
                        if value not in element:
                            element[value] = None

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration" +
                                ", waiting for a commit")

        mo_sys = "sys"
        mo_aaa_ldap_ep = AaaLdapEp(parent_mo_or_dn=mo_sys, timeout=self.timeout)
        if self.providers:
            for provider in self.providers:
                mo_ldap_provider = AaaLdapProvider(parent_mo_or_dn=mo_aaa_ldap_ep, rootdn=provider["bind_dn"],
                                                   vendor=provider["vendor"], key=provider["password"],
                                                   port=provider["port"], attribute=provider["attribute"],
                                                   timeout=provider["timeout"], name=provider["hostname"],
                                                   basedn=provider["base_dn"], enable_ssl=provider["ssl"],
                                                   order=provider["order"], filter=provider["filter"])
                AaaLdapGroupRule(parent_mo_or_dn=mo_ldap_provider, target_attr=provider["target_attribute"],
                                 use_primary_group=provider["use_primary_group"],
                                 authorization=provider["group_authorization"], traversal=provider["group_recursion"])
        if self.provider_groups:
            for group in self.provider_groups:
                mo_aaa_provider_group = AaaProviderGroup(parent_mo_or_dn=mo_aaa_ldap_ep, name=group["name"])
                if "included_providers" in group:
                    for provider in group["included_providers"]:
                        AaaProviderRef(parent_mo_or_dn=mo_aaa_provider_group, name=provider)

        if self.group_maps:
            for group_map in self.group_maps:
                mo_ldap_group = AaaLdapGroup(parent_mo_or_dn=mo_aaa_ldap_ep, name=group_map["group_dn"])
                if 'roles' in group_map:
                    for role in group_map['roles']:
                        AaaUserRole(parent_mo_or_dn=mo_ldap_group, name=role, descr="")
                if 'locales' in group_map:
                    for locale in group_map['locales']:
                        AaaUserLocale(parent_mo_or_dn=mo_ldap_group, name=locale, descr="")

        self._handle.add_mo(mo_aaa_ldap_ep, modify_present=True)

        if commit:
            if self.commit() != True:
                return False
        return True


class UcsSystemCallHome(UcsSystemConfigObject):
    _CONFIG_NAME = "Call Home"

    def __init__(self, parent=None, json_content=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.mute_at_start = None
        self.anonymous_reporting = None
        self.smtp_host = None
        self.smtp_port = None
        self.system_inventory = None
        self.system_inventory_send_now = None
        self.system_inventory_send_interval = None
        self.system_inventory_hour = None
        self.system_inventory_minute = None
        self.admin_state = None
        self.throttling = None
        self.contact = None
        self.phone = None
        self.email = None
        self.address = None
        self.customer_id = None
        self.contract_id = None
        self.site_id = None
        self.email_from = None
        self.email_reply_to = None
        self.switch_priority = None
        self.profiles = []
        self.policies = []

        if self._config.load_from == "live":
            # Locating SDK objects needed to initialize
            if "callhomeAnonymousReporting" in self._config.sdk_objects:
                if self._config.sdk_objects["callhomeAnonymousReporting"]:
                    self.mute_at_start = self._config.sdk_objects["callhomeAnonymousReporting"][0].user_acknowledged
                    self.anonymous_reporting = self._config.sdk_objects["callhomeAnonymousReporting"][0].admin_state

            if "callhomeSmtp" in self._config.sdk_objects:
                if self._config.sdk_objects["callhomeSmtp"]:
                    self.smtp_port = self._config.sdk_objects["callhomeSmtp"][0].port
                    self.smtp_host = self._config.sdk_objects["callhomeSmtp"][0].host

            if "callhomeEp" in self._config.sdk_objects:
                if self._config.sdk_objects["callhomeEp"]:
                    self.admin_state = self._config.sdk_objects["callhomeEp"][0].admin_state
                    self.throttling = self._config.sdk_objects["callhomeEp"][0].alert_throttling_admin_state

            if "callhomeSource" in self._config.sdk_objects:
                if self._config.sdk_objects["callhomeSource"]:
                    self.contact = self._config.sdk_objects["callhomeSource"][0].contact
                    self.phone = self._config.sdk_objects["callhomeSource"][0].phone
                    self.email = self._config.sdk_objects["callhomeSource"][0].email
                    self.address = self._config.sdk_objects["callhomeSource"][0].addr
                    self.contract_id = self._config.sdk_objects["callhomeSource"][0].contract
                    self.customer_id = self._config.sdk_objects["callhomeSource"][0].customer
                    self.site_id = self._config.sdk_objects["callhomeSource"][0].site
                    self.email_reply_to = self._config.sdk_objects["callhomeSource"][0].reply_to
                    self.email_from = self._config.sdk_objects["callhomeSource"][0].r_from
                    self.switch_priority = self._config.sdk_objects["callhomeSource"][0].urgency

            if "callhomePeriodicSystemInventory" in self._config.sdk_objects:
                if self._config.sdk_objects["callhomePeriodicSystemInventory"]:
                    self.system_inventory = self._config.sdk_objects["callhomePeriodicSystemInventory"][0].admin_state
                    self.system_inventory_send_interval = \
                        self._config.sdk_objects["callhomePeriodicSystemInventory"][0].interval_days
                    self.system_inventory_send_now = \
                        self._config.sdk_objects["callhomePeriodicSystemInventory"][0].send_now
                    self.system_inventory_hour = \
                        self._config.sdk_objects["callhomePeriodicSystemInventory"][0].time_of_day_hour
                    self.system_inventory_minute = \
                        self._config.sdk_objects["callhomePeriodicSystemInventory"][0].time_of_day_minute

            if "callhomePolicy" in self._config.sdk_objects:
                for callhome_policy in self._config.sdk_objects["callhomePolicy"]:
                    policy = {}
                    policy.update({"state": callhome_policy.admin_state})
                    policy.update({"cause": callhome_policy.cause})
                    self.policies.append(policy)

            if "callhomeProfile" in self._config.sdk_objects:
                for callhome_profile in self._config.sdk_objects["callhomeProfile"]:
                    profile = {}
                    profile.update({"profile_name": callhome_profile.name})
                    profile.update({"profile_level": callhome_profile.level})
                    profile.update({"profile_format": callhome_profile.format})
                    profile.update({"profile_max_size": callhome_profile.max_size})
                    profile.update({"profile_alert_groups": callhome_profile.alert_groups.split(',')})
                    profile.update({"profile_emails": []})
                    if "callhomeDest" in self._config.sdk_objects:
                        for callhome_dest in self._config.sdk_objects["callhomeDest"]:
                            profile["profile_emails"].append(callhome_dest.email)
                    self.profiles.append(profile)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)
                for element in self.profiles:
                    for value in ["profile_name", "profile_level", "profile_format", "profile_max_size",
                                  "profile_alert_groups", "profile_emails"]:
                        if value not in element:
                            element[value] = None
                for element in self.policies:
                    for value in ["state", "cause"]:
                        if value not in element:
                            element[value] = None

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration" +
                                ", waiting for a commit")

        mo_callhome = "call-home"

        mo_callhome_anonymous_reporting = CallhomeAnonymousReporting(parent_mo_or_dn=mo_callhome,
                                                                     user_acknowledged=self.mute_at_start,
                                                                     admin_state=self.anonymous_reporting)
        self._handle.add_mo(mo_callhome_anonymous_reporting, modify_present=True)
        mo_callhome_smtp = CallhomeSmtp(parent_mo_or_dn=mo_callhome, port=self.smtp_port, host=self.smtp_host)
        self._handle.add_mo(mo_callhome_smtp, modify_present=True)
        mo_callhome_ep = CallhomeEp(admin_state=self.admin_state, alert_throttling_admin_state=self.throttling)
        CallhomeSource(parent_mo_or_dn=mo_callhome_ep, contact=self.contact, phone=self.phone, email=self.email,
                       addr=self.address, contract=self.contract_id, customer=self.customer_id, site=self.site_id,
                       reply_to=self.email_reply_to, r_from=self.email_from, urgency=self.switch_priority)
        self._handle.add_mo(mo_callhome_ep, modify_present=True)

        # Fix to workaround system_inventory_send_interval default value of 0
        system_inventory_send_interval = None
        if self.system_inventory_send_interval != "0":
            system_inventory_send_interval = self.system_inventory_send_interval

        mo_callhome_inventory = CallhomePeriodicSystemInventory(parent_mo_or_dn=mo_callhome,
                                                                admin_state=self.system_inventory,
                                                                interval_days=system_inventory_send_interval,
                                                                send_now=self.system_inventory_send_now,
                                                                time_of_day_hour=self.system_inventory_hour,
                                                                time_of_day_minute=self.system_inventory_minute)
        self._handle.add_mo(mo_callhome_inventory, modify_present=True)

        if self.policies:
            for policy in self.policies:
                mo_callhome_policy = CallhomePolicy(parent_mo_or_dn=mo_callhome, cause=policy['cause'],
                                                    admin_state=policy['state'])
                self._handle.add_mo(mo_callhome_policy, modify_present=True)

        if self.profiles:
            for profile in self.profiles:
                mo_callhome_profile = CallhomeProfile(parent_mo_or_dn=mo_callhome, format=profile["profile_format"],
                                                      level=profile["profile_level"],
                                                      max_size=profile["profile_max_size"],
                                                      alert_groups=','.join(profile["profile_alert_groups"]),
                                                      name=profile["profile_name"])

                if "profile_emails" in profile:
                    if profile["profile_emails"]:
                        for email in profile["profile_emails"]:
                            CallhomeDest(parent_mo_or_dn=mo_callhome_profile, email=email)
                self._handle.add_mo(mo_callhome_profile, modify_present=True)
        self._handle.add_mo(mo_callhome_anonymous_reporting, modify_present=True)

        if commit:
            if self.commit() != True:
                return False
        return True


class UcsSystemPortAutoDiscoveryPolicy(UcsSystemConfigObject):
    _CONFIG_NAME = "Port Auto Discovery Policy"

    def __init__(self, parent=None, json_content=None):
        UcsSystemConfigObject.__init__(self, parent=parent)

        self.auto_configure_server_ports = None

        if self._config.load_from == "live":
            # Locating SDK objects needed to initialize
            if "computePortDiscPolicy" in self._config.sdk_objects:
                discovery_policy = [policy for policy in self._config.sdk_objects["computePortDiscPolicy"]]
                if len(discovery_policy):
                    self.auto_configure_server_ports = discovery_policy[0].eth_svr_auto_discovery

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration" +
                                ", waiting for a commit")

        mo_org_root = "org-root"
        mo_compute_port_disc_policy = ComputePortDiscPolicy(parent_mo_or_dn=mo_org_root,
                                                            eth_svr_auto_discovery=self.auto_configure_server_ports)
        self._handle.add_mo(mo=mo_compute_port_disc_policy, modify_present=True)
        if commit:
            if self.commit() != True:
                return False
        return True
