# coding: utf-8
# !/usr/bin/env python

""" admin.py: Easy UCS Deployment Tool """
from easyucs import __author__, __copyright__,  __version__, __status__


import sys
import time
import traceback
import urllib

from easyucs.config.object import GenericUcsConfigObject, UcsImcConfigObject, UcsSystemConfigObject

from easyucs import common

from imcsdk.mometa.aaa.AaaLdap import AaaLdap
from imcsdk.mometa.aaa.AaaLdapRoleGroup import AaaLdapRoleGroup
from imcsdk.mometa.aaa.AaaUser import AaaUser as ImcAaaUser
from imcsdk.mometa.aaa.AaaUserPasswordExpiration import AaaUserPasswordExpiration as ImcAaaUserPasswordExpiration
from imcsdk.mometa.aaa.AaaUserPolicy import AaaUserPolicy as ImcAaaUserPolicy
from imcsdk.mometa.adaptor.AdaptorEthCompQueueProfile import AdaptorEthCompQueueProfile
from imcsdk.mometa.adaptor.AdaptorEthGenProfile import AdaptorEthGenProfile
from imcsdk.mometa.adaptor.AdaptorEthInterruptProfile import AdaptorEthInterruptProfile
from imcsdk.mometa.adaptor.AdaptorEthOffloadProfile import AdaptorEthOffloadProfile
from imcsdk.mometa.adaptor.AdaptorEthRecvQueueProfile import AdaptorEthRecvQueueProfile
from imcsdk.mometa.adaptor.AdaptorEthUSNICProfile import AdaptorEthUSNICProfile
from imcsdk.mometa.adaptor.AdaptorEthWorkQueueProfile import AdaptorEthWorkQueueProfile
from imcsdk.mometa.adaptor.AdaptorExtIpV6RssHashProfile import AdaptorExtIpV6RssHashProfile
from imcsdk.mometa.adaptor.AdaptorFcBootTable import AdaptorFcBootTable
from imcsdk.mometa.adaptor.AdaptorFcCdbWorkQueueProfile import AdaptorFcCdbWorkQueueProfile
from imcsdk.mometa.adaptor.AdaptorFcErrorRecoveryProfile import AdaptorFcErrorRecoveryProfile
from imcsdk.mometa.adaptor.AdaptorFcGenProfile import AdaptorFcGenProfile
from imcsdk.mometa.adaptor.AdaptorFcInterruptProfile import AdaptorFcInterruptProfile
from imcsdk.mometa.adaptor.AdaptorFcPortFLogiProfile import AdaptorFcPortFLogiProfile
from imcsdk.mometa.adaptor.AdaptorFcPortPLogiProfile import AdaptorFcPortPLogiProfile
from imcsdk.mometa.adaptor.AdaptorFcPortProfile import AdaptorFcPortProfile
from imcsdk.mometa.adaptor.AdaptorFcRecvQueueProfile import AdaptorFcRecvQueueProfile
from imcsdk.mometa.adaptor.AdaptorFcWorkQueueProfile import AdaptorFcWorkQueueProfile
from imcsdk.mometa.adaptor.AdaptorGenProfile import AdaptorGenProfile
from imcsdk.mometa.adaptor.AdaptorHostEthIf import AdaptorHostEthIf
from imcsdk.mometa.adaptor.AdaptorHostFcIf import AdaptorHostFcIf
from imcsdk.mometa.adaptor.AdaptorIpV4RssHashProfile import AdaptorIpV4RssHashProfile
from imcsdk.mometa.adaptor.AdaptorIpV6RssHashProfile import AdaptorIpV6RssHashProfile
from imcsdk.mometa.adaptor.AdaptorRssProfile import AdaptorRssProfile
from imcsdk.mometa.adaptor.AdaptorUnit import AdaptorUnit
from imcsdk.mometa.advanced.AdvancedPowerProfile import AdvancedPowerProfile
from imcsdk.mometa.bios.BiosSettings import BiosSettings
from imcsdk.mometa.bios.BiosUnit import BiosUnit
from imcsdk.mometa.bios.BiosVfAdjacentCacheLinePrefetch import BiosVfAdjacentCacheLinePrefetch
from imcsdk.mometa.bios.BiosVfAltitude import BiosVfAltitude
from imcsdk.mometa.bios.BiosVfAutonumousCstateEnable import BiosVfAutonumousCstateEnable
from imcsdk.mometa.bios.BiosVfBootPerformanceMode import BiosVfBootPerformanceMode
from imcsdk.mometa.bios.BiosVfCDNEnable import BiosVfCDNEnable
from imcsdk.mometa.bios.BiosVfCPUEnergyPerformance import BiosVfCPUEnergyPerformance
from imcsdk.mometa.bios.BiosVfCPUPerformance import BiosVfCPUPerformance
from imcsdk.mometa.bios.BiosVfCPUPowerManagement import BiosVfCPUPowerManagement
from imcsdk.mometa.bios.BiosVfCmciEnable import BiosVfCmciEnable
from imcsdk.mometa.bios.BiosVfConsoleRedirection import BiosVfConsoleRedirection
from imcsdk.mometa.bios.BiosVfCoreMultiProcessing import BiosVfCoreMultiProcessing
from imcsdk.mometa.bios.BiosVfDCUPrefetch import BiosVfDCUPrefetch
from imcsdk.mometa.bios.BiosVfDemandScrub import BiosVfDemandScrub
from imcsdk.mometa.bios.BiosVfDirectCacheAccess import BiosVfDirectCacheAccess
from imcsdk.mometa.bios.BiosVfEnhancedIntelSpeedStepTech import BiosVfEnhancedIntelSpeedStepTech
from imcsdk.mometa.bios.BiosVfExecuteDisableBit import BiosVfExecuteDisableBit
from imcsdk.mometa.bios.BiosVfExtendedAPIC import BiosVfExtendedAPIC
from imcsdk.mometa.bios.BiosVfFRB2Enable import BiosVfFRB2Enable
from imcsdk.mometa.bios.BiosVfHWPMEnable import BiosVfHWPMEnable
from imcsdk.mometa.bios.BiosVfHardwarePrefetch import BiosVfHardwarePrefetch
from imcsdk.mometa.bios.BiosVfIntelHyperThreadingTech import BiosVfIntelHyperThreadingTech
from imcsdk.mometa.bios.BiosVfIntelTurboBoostTech import BiosVfIntelTurboBoostTech
from imcsdk.mometa.bios.BiosVfIntelVTForDirectedIO import BiosVfIntelVTForDirectedIO
from imcsdk.mometa.bios.BiosVfIntelVirtualizationTechnology import BiosVfIntelVirtualizationTechnology
from imcsdk.mometa.bios.BiosVfLOMPortOptionROM import BiosVfLOMPortOptionROM
from imcsdk.mometa.bios.BiosVfLegacyUSBSupport import BiosVfLegacyUSBSupport
from imcsdk.mometa.bios.BiosVfMemoryInterleave import BiosVfMemoryInterleave
from imcsdk.mometa.bios.BiosVfMemoryMappedIOAbove4GB import BiosVfMemoryMappedIOAbove4GB
from imcsdk.mometa.bios.BiosVfNUMAOptimized import BiosVfNUMAOptimized
from imcsdk.mometa.bios.BiosVfOSBootWatchdogTimer import BiosVfOSBootWatchdogTimer
from imcsdk.mometa.bios.BiosVfOSBootWatchdogTimerPolicy import BiosVfOSBootWatchdogTimerPolicy
from imcsdk.mometa.bios.BiosVfOSBootWatchdogTimerTimeout import BiosVfOSBootWatchdogTimerTimeout
from imcsdk.mometa.bios.BiosVfOutOfBandMgmtPort import BiosVfOutOfBandMgmtPort
from imcsdk.mometa.bios.BiosVfPCIOptionROMs import BiosVfPCIOptionROMs
from imcsdk.mometa.bios.BiosVfPCISlotOptionROMEnable import BiosVfPCISlotOptionROMEnable
from imcsdk.mometa.bios.BiosVfPCIeSSDHotPlugSupport import BiosVfPCIeSSDHotPlugSupport
from imcsdk.mometa.bios.BiosVfPStateCoordType import BiosVfPStateCoordType
from imcsdk.mometa.bios.BiosVfPackageCStateLimit import BiosVfPackageCStateLimit
from imcsdk.mometa.bios.BiosVfPatrolScrub import BiosVfPatrolScrub
from imcsdk.mometa.bios.BiosVfPchUsb30Mode import BiosVfPchUsb30Mode
from imcsdk.mometa.bios.BiosVfPciRomClp import BiosVfPciRomClp
from imcsdk.mometa.bios.BiosVfPowerOnPasswordSupport import BiosVfPowerOnPasswordSupport
from imcsdk.mometa.bios.BiosVfProcessorC1E import BiosVfProcessorC1E
from imcsdk.mometa.bios.BiosVfProcessorC3Report import BiosVfProcessorC3Report
from imcsdk.mometa.bios.BiosVfProcessorC6Report import BiosVfProcessorC6Report
from imcsdk.mometa.bios.BiosVfPwrPerfTuning import BiosVfPwrPerfTuning
from imcsdk.mometa.bios.BiosVfQPIConfig import BiosVfQPIConfig
from imcsdk.mometa.bios.BiosVfQpiSnoopMode import BiosVfQpiSnoopMode
from imcsdk.mometa.bios.BiosVfResumeOnACPowerLoss import BiosVfResumeOnACPowerLoss
from imcsdk.mometa.bios.BiosVfSataModeSelect import BiosVfSataModeSelect
from imcsdk.mometa.bios.BiosVfSelectMemoryRASConfiguration import BiosVfSelectMemoryRASConfiguration
from imcsdk.mometa.bios.BiosVfSrIov import BiosVfSrIov
from imcsdk.mometa.bios.BiosVfTPMSupport import BiosVfTPMSupport
from imcsdk.mometa.bios.BiosVfUSBEmulation import BiosVfUSBEmulation
from imcsdk.mometa.bios.BiosVfUSBPortsConfig import BiosVfUSBPortsConfig
from imcsdk.mometa.bios.BiosVfUsbXhciSupport import BiosVfUsbXhciSupport
from imcsdk.mometa.bios.BiosVfVgaPriority import BiosVfVgaPriority
from imcsdk.mometa.bios.BiosVfWorkLoadConfig import BiosVfWorkLoadConfig
from imcsdk.mometa.comm.CommHttp import CommHttp
from imcsdk.mometa.comm.CommHttps import CommHttps
from imcsdk.mometa.comm.CommIpmiLan import CommIpmiLan
from imcsdk.mometa.comm.CommKvm import CommKvm
from imcsdk.mometa.comm.CommMailAlert import CommMailAlert
from imcsdk.mometa.comm.CommNtpProvider import CommNtpProvider as ImcCommNtpProvider
from imcsdk.mometa.comm.CommRedfish import CommRedfish
from imcsdk.mometa.comm.CommSavedVMediaMap import CommSavedVMediaMap
from imcsdk.mometa.comm.CommSnmp import CommSnmp
from imcsdk.mometa.comm.CommSsh import CommSsh
from imcsdk.mometa.comm.CommSvcEp import CommSvcEp
from imcsdk.mometa.comm.CommVMedia import CommVMedia
from imcsdk.mometa.comm.CommVMediaMap import CommVMediaMap
from imcsdk.mometa.compute.ComputeRackUnit import ComputeRackUnit
from imcsdk.mometa.compute.ComputeServerRef import ComputeServerRef
from imcsdk.mometa.equipment.EquipmentChassis import EquipmentChassis
from imcsdk.mometa.fan.FanPolicy import FanPolicy
from imcsdk.mometa.ip.IpBlocking import IpBlocking
from imcsdk.mometa.ip.IpFiltering import IpFiltering
from imcsdk.mometa.kmip.KmipServerLogin import KmipServerLogin
from imcsdk.mometa.ldap.LdapCACertificateManagement import LdapCACertificateManagement
from imcsdk.mometa.lsboot.LsbootDef import LsbootDef
from imcsdk.mometa.lsboot.LsbootDevPrecision import LsbootDevPrecision
from imcsdk.mometa.lsboot.LsbootEfi import LsbootEfi
from imcsdk.mometa.lsboot.LsbootHdd import LsbootHdd
from imcsdk.mometa.lsboot.LsbootIscsi import LsbootIscsi
from imcsdk.mometa.lsboot.LsbootLan import LsbootLan
from imcsdk.mometa.lsboot.LsbootNVMe import LsbootNVMe
from imcsdk.mometa.lsboot.LsbootPchStorage import LsbootPchStorage
from imcsdk.mometa.lsboot.LsbootPxe import LsbootPxe
from imcsdk.mometa.lsboot.LsbootSan import LsbootSan
from imcsdk.mometa.lsboot.LsbootSd import LsbootSd
from imcsdk.mometa.lsboot.LsbootStorage import LsbootStorage
from imcsdk.mometa.lsboot.LsbootUefiShell import LsbootUefiShell
from imcsdk.mometa.lsboot.LsbootUsb import LsbootUsb
from imcsdk.mometa.lsboot.LsbootVMedia import LsbootVMedia
from imcsdk.mometa.lsboot.LsbootVirtualMedia import LsbootVirtualMedia
from imcsdk.mometa.mail.MailRecipient import MailRecipient
from imcsdk.mometa.memory.MemoryArray import MemoryArray
from imcsdk.mometa.mgmt.MgmtIf import MgmtIf
from imcsdk.mometa.one.OneTimePrecisionBootDevice import OneTimePrecisionBootDevice
from imcsdk.mometa.platform.PlatformEventFilters import PlatformEventFilters
from imcsdk.mometa.power.PowerBudget import PowerBudget
from imcsdk.mometa.self.SelfEncryptStorageController import SelfEncryptStorageController
from imcsdk.mometa.sol.SolIf import SolIf
from imcsdk.mometa.standard.StandardPowerProfile import StandardPowerProfile
from imcsdk.mometa.storage.StorageController import StorageController
from imcsdk.mometa.storage.StorageFlexFlashController import StorageFlexFlashController
from imcsdk.mometa.storage.StorageFlexFlashOperationalProfile import StorageFlexFlashOperationalProfile
from imcsdk.mometa.storage.StorageLocalDisk import StorageLocalDisk
from imcsdk.mometa.storage.StorageLocalDiskUsage import StorageLocalDiskUsage
from imcsdk.mometa.storage.StorageVirtualDrive import StorageVirtualDrive
from imcsdk.mometa.storage.StorageVirtualDriveCreatorUsingUnusedPhysicalDrive import \
    StorageVirtualDriveCreatorUsingUnusedPhysicalDrive
from imcsdk.mometa.storage.StorageVirtualDriveCreatorUsingVirtualDriveGroup import \
    StorageVirtualDriveCreatorUsingVirtualDriveGroup
from imcsdk.mometa.top.TopSystem import TopSystem as ImcTopSystem

from ucsmsdk.ucsexception import UcsException
from imcsdk.imcexception import ImcException


class UcsImcAdminNetwork(UcsImcConfigObject):
    _CONFIG_NAME = "Admin Network"

    def __init__(self, parent=None, json_content=None):
        UcsImcConfigObject.__init__(self, parent=parent)
        self.admin_duplex = None
        self.admin_port_speed = None
        self.auto_negotiation = None
        self.dynamic_dns_enable = None
        self.dynamic_dns_update_domain = None
        self.dns_alternate_ipv4 = None
        self.dns_alternate_ipv6 = None
        self.dns_preferred_ipv4 = None
        self.dns_preferred_ipv6 = None
        self.enable_ipv6 = None
        self.gateway_ipv4 = None
        self.gateway_ipv6 = None
        self.management_hostname = None
        self.management_ipv4_address = None
        self.management_ipv6_address = None
        self.management_subnet_mask = None
        self.nic_mode = None
        self.nic_redundancy = None
        self.obtain_dns_from_dhcp_v4 = None
        self.obtain_dns_from_dhcp_v6 = None
        self.port_profile = None
        self.prefix_length_ipv6 = None
        self.use_dhcp_v4 = None
        self.use_dhcp_v6 = None
        self.vic_slot = None
        self.vlan_enable = None
        self.vlan_id = None
        self.vlan_priority = None

        if self._config.load_from == "live":
            # Locating SDK objects needed to initialize
            mgmt_if = None
            if "mgmtIf" in self._config.sdk_objects:
                # For rack servers
                if len(self._config.sdk_objects["mgmtIf"]) == 1:
                    mgmt_if = self._config.sdk_objects["mgmtIf"][0]
                # For S3260 chassis servers
                if len(self._config.sdk_objects["mgmtIf"]) > 1:
                    for interface in self._config.sdk_objects["mgmtIf"]:
                        if interface.dn == "sys/chassis-1/if-1":
                            mgmt_if = interface

            if mgmt_if is not None:
                self.auto_negotiation = mgmt_if.auto_neg
                self.dynamic_dns_enable = mgmt_if.ddns_enable
                self.dns_alternate_ipv4 = mgmt_if.dns_alternate
                self.dns_preferred_ipv4 = mgmt_if.dns_preferred
                self.enable_ipv6 = mgmt_if.v6ext_enabled
                self.gateway_ipv4 = mgmt_if.ext_gw
                if self._device.platform_type == "classic":
                    self.management_hostname = mgmt_if.hostname
                elif self._device.platform_type == "modular":
                    self.management_hostname = mgmt_if.v_hostname
                self.management_ipv4_address = mgmt_if.ext_ip
                self.management_subnet_mask = mgmt_if.ext_mask
                self.nic_mode = mgmt_if.nic_mode
                self.obtain_dns_from_dhcp_v4 = mgmt_if.dns_using_dhcp
                if mgmt_if.port_profile != "":
                    self.port_profile = mgmt_if.port_profile
                self.use_dhcp_v4 = mgmt_if.dhcp_enable
                self.vlan_enable = mgmt_if.vlan_enable

                if self.auto_negotiation == "disabled" or self.auto_negotiation == "Disabled":
                    self.admin_duplex = mgmt_if.admin_duplex
                    self.admin_port_speed = mgmt_if.admin_net_speed

                if self.dynamic_dns_enable == "yes" or self.dynamic_dns_enable == "Yes":
                    self.dynamic_dns_update_domain = mgmt_if.ddns_domain

                if self.enable_ipv6 == "yes" or self.enable_ipv6 == "Yes":
                    self.dns_alternate_ipv6 = mgmt_if.v6dns_alternate
                    self.dns_preferred_ipv6 = mgmt_if.v6dns_preferred
                    self.gateway_ipv6 = mgmt_if.v6ext_gw
                    self.management_ipv6_address = mgmt_if.v6ext_ip
                    self.obtain_dns_from_dhcp_v6 = mgmt_if.v6dns_using_dhcp
                    self.prefix_length_ipv6 = mgmt_if.v6prefix
                    self.use_dhcp_v6 = mgmt_if.v6dhcp_enable

                if self.nic_mode != "dedicated":
                    self.nic_redundancy = mgmt_if.nic_redundancy
                if self.nic_mode == "cisco_card":
                    self.vic_slot = mgmt_if.vic_slot

                if self.vlan_enable == "yes" or self.vlan_enable == "Yes":
                    self.vlan_id = mgmt_if.vlan_id
                    self.vlan_priority = mgmt_if.vlan_priority

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error", message="Unable to set attributes from JSON content for Admin Network")

        self.clean_object()

    def push_object(self, commit=True):
        self.logger(message="Pushing Admin Network configuration")

        if self.auto_negotiation == "enabled" or self.auto_negotiation == "Enabled":
            self.admin_duplex = None
            self.admin_port_speed = None
        if self.dynamic_dns_enable == "no" or self.dynamic_dns_enable == "No":
            self.dynamic_dns_update_domain = None
        if self.enable_ipv6 == "no" or self.enable_ipv6 == "No":
            self.dns_alternate_ipv6 = None
            self.dns_preferred_ipv6 = None
            self.gateway_ipv6 = None
            self.management_ipv6_address = None
            self.obtain_dns_from_dhcp_v6 = None
            self.prefix_length_ipv6 = None
            self.use_dhcp_v6 = None
        if self.nic_mode != "cisco_card":
            self.vic_slot = None
        if self.nic_mode == "dedicated":
            self.nic_redundancy = None
        else:
            self.auto_negotiation = None
        if self.port_profile == "":
            self.port_profile = None
        if self.vlan_enable == "no" or self.vlan_enable == "No":
            self.vlan_id = None
            self.vlan_priority = None

        if self._device.platform_type == "classic":
            parent_mo = "sys/rack-unit-1/mgmt"
        elif self._device.platform_type == "modular":
            parent_mo = "sys/chassis-1"

        mo_mgmt_if = MgmtIf(parent_mo_or_dn=parent_mo, admin_duplex=self.admin_duplex,
                            admin_net_speed=self.admin_port_speed, auto_neg=self.auto_negotiation,
                            ddns_domain=self.dynamic_dns_update_domain, ddns_enable=self.dynamic_dns_enable,
                            dhcp_enable=self.use_dhcp_v4, dns_alternate=self.dns_alternate_ipv4,
                            dns_preferred=self.dns_preferred_ipv4, dns_using_dhcp=self.obtain_dns_from_dhcp_v4,
                            ext_gw=self.gateway_ipv4, ext_ip=self.management_ipv4_address,
                            ext_mask=self.management_subnet_mask, hostname=self.management_hostname,
                            nic_mode=self.nic_mode, nic_redundancy=self.nic_redundancy, port_profile=self.port_profile,
                            v6dhcp_enable=self.use_dhcp_v6, v6dns_alternate=self.dns_alternate_ipv6,
                            v6dns_preferred=self.dns_preferred_ipv6, v6dns_using_dhcp=self.obtain_dns_from_dhcp_v6,
                            v6ext_enabled=self.enable_ipv6, v6ext_gw=self.gateway_ipv6,
                            v6ext_ip=self.management_ipv6_address, v6prefix=self.prefix_length_ipv6,
                            vic_slot=self.vic_slot, vlan_enable=self.vlan_enable, vlan_id=self.vlan_id,
                            vlan_priority=self.vlan_priority)
        if commit:
            if self.commit(mo=mo_mgmt_if) != True:
                return False
        return True


class UcsImcTimezoneMgmt(UcsImcConfigObject):
    _CONFIG_NAME = "Timezone Management"

    def __init__(self, parent=None, json_content=None):
        UcsImcConfigObject.__init__(self, parent=parent)
        self.ntp_enabled = None
        self.ntp_server1 = None
        self.ntp_server2 = None
        self.ntp_server3 = None
        self.ntp_server4 = None
        self.zone = None

        if self._config.load_from == "live":
            # Locating SDK objects needed to initialize
            comm_ntp_provider = None
            top_system = None
            if "commNtpProvider" in self._config.sdk_objects:
                if len(self._config.sdk_objects["commNtpProvider"]) == 1:
                    comm_ntp_provider = self._config.sdk_objects["commNtpProvider"][0]

            if "topSystem" in self._config.sdk_objects:
                if len(self._config.sdk_objects["topSystem"]) == 1:
                    top_system = self._config.sdk_objects["topSystem"][0]

            if comm_ntp_provider is not None:
                self.ntp_enabled = comm_ntp_provider.ntp_enable
                for attribute in ["ntp_server1", "ntp_server2", "ntp_server3", "ntp_server4"]:
                    if getattr(comm_ntp_provider, attribute) not in ["", " "]:
                        setattr(self, attribute, getattr(comm_ntp_provider, attribute))

            if top_system is not None:
                self.zone = top_system.time_zone

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
        result = True

        # Configuring Time Zone

        mo_top_system = ImcTopSystem(time_zone=self.zone)
        if commit:
            if self.commit(mo=mo_top_system, detail=self.zone) != True:
                result = False

        # Configuring NTP
        parent_mo = "sys/svc-ext"
        mo_comm_ntp_provider = ImcCommNtpProvider(parent_mo_or_dn=parent_mo, ntp_enable=self.ntp_enabled,
                                                  ntp_server1=self.ntp_server1, ntp_server2=self.ntp_server2,
                                                  ntp_server3=self.ntp_server3, ntp_server4=self.ntp_server4)
        if commit:
            if self.commit(mo=mo_comm_ntp_provider, detail="NTP configuration") != True:
                result = False

        if result:
            return True
        else:
            return False


class UcsImcLocalUser(UcsImcConfigObject):
    _CONFIG_NAME = "Local User"

    def __init__(self, parent=None, json_content=None, aaa_user=None):
        UcsImcConfigObject.__init__(self, parent=parent)
        self.account_status = None
        self.id = None
        self.password = None
        self.role = None
        self.username = None

        if self._config.load_from == "live":
            # Locating SDK objects needed to initialize

            if aaa_user is not None:
                if aaa_user.account_status != "active":
                    self.account_status = aaa_user.account_status
                self.id = aaa_user.id
                if aaa_user.pwd:
                    self.password = aaa_user.pwd
                self.role = aaa_user.priv
                self.username = aaa_user.name

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + self.username + ' (' + self.id +
                                ')')
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + self.username +
                                ' (' + self.id + ')' + ", waiting for a commit")

        parent_mo = "sys/user-ext"
        if self.account_status is not None:
            account_status = self.account_status
        else:
            account_status = "active"
        mo_aaa_user = ImcAaaUser(parent_mo_or_dn=parent_mo, account_status=account_status, id=self.id,
                                 name=self.username, priv=self.role, pwd=self.password)

        if commit:
            if self.commit(mo=mo_aaa_user, detail=self.username + " (" + self.id + ")") != True:
                return False
        return True


class UcsImcLocalUsersProperties(UcsImcConfigObject):
    _CONFIG_NAME = "Local Users Properties"

    def __init__(self, parent=None, json_content=None):
        UcsImcConfigObject.__init__(self, parent=parent)
        self.grace_period = None
        self.notification_period = None
        self.password_expiry_duration = None
        self.password_history = None
        self.password_strength_check = None

        if self._config.load_from == "live":
            # Locating SDK objects needed to initialize
            aaa_user_password_expiration = None
            aaa_user_policy = None
            if "aaaUserPasswordExpiration" in self._config.sdk_objects:
                if len(self._config.sdk_objects["aaaUserPasswordExpiration"]) == 1:
                    aaa_user_password_expiration = self._config.sdk_objects["aaaUserPasswordExpiration"][0]

            if "aaaUserPolicy" in self._config.sdk_objects:
                if len(self._config.sdk_objects["aaaUserPolicy"]) == 1:
                    aaa_user_policy = self._config.sdk_objects["aaaUserPolicy"][0]

            if aaa_user_password_expiration is not None:
                if aaa_user_password_expiration.password_grace_period != "0":
                    self.grace_period = aaa_user_password_expiration.password_grace_period
                if aaa_user_password_expiration.password_notification_period != "15":
                    self.notification_period = aaa_user_password_expiration.password_notification_period
                if aaa_user_password_expiration.password_expiry_duration != "0":
                    self.password_expiry_duration = aaa_user_password_expiration.password_expiry_duration
                if aaa_user_password_expiration.password_history != "0":
                    self.password_history = aaa_user_password_expiration.password_history

            if aaa_user_policy is not None:
                if aaa_user_policy.user_password_policy != "enabled":
                    self.password_strength_check = aaa_user_policy.user_password_policy

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
        result = True

        parent_mo = "sys/user-ext"
        mo_aaa_user_password_expiration =\
            ImcAaaUserPasswordExpiration(parent_mo_or_dn=parent_mo, password_grace_period=self.grace_period,
                                         password_notification_period=self.notification_period,
                                         password_expiry_duration=self.password_expiry_duration,
                                         password_history=self.password_history)
        if self.commit(mo=mo_aaa_user_password_expiration, detail="Password Expiration") != True:
            result = False

        mo_aaa_user_policy = ImcAaaUserPolicy(parent_mo_or_dn=parent_mo,
                                              user_password_policy=self.password_strength_check)
        if commit:
            if self.commit(mo=mo_aaa_user_policy, detail="Password Strength Check") != True:
                result = False

        if result:
            return True
        else:
            return False


class UcsImcServerProperties(UcsImcConfigObject):
    _CONFIG_NAME = "Server/Chassis Properties"

    def __init__(self, parent=None, json_content=None):
        UcsImcConfigObject.__init__(self, parent=parent)
        self.description = None
        self.asset_tag = None
        self.server_sioc_connectivity = None

        if self._config.load_from == "live":
            if self._device.platform_type == "classic":
                if "computeRackUnit" in self._config.sdk_objects:
                    if len(self._config.sdk_objects["computeRackUnit"]) == 1:
                        self.description = self._config.sdk_objects["computeRackUnit"][0].usr_lbl
                        self.asset_tag = self._config.sdk_objects["computeRackUnit"][0].asset_tag
            elif self._device.platform_type == "modular":
                if "equipmentChassis" in self._config.sdk_objects:
                    if len(self._config.sdk_objects["equipmentChassis"]) == 1:
                        self.description = self._config.sdk_objects["equipmentChassis"][0].usr_lbl
                        self.asset_tag = self._config.sdk_objects["equipmentChassis"][0].asset_tag
                        self.server_sioc_connectivity = \
                            self._config.sdk_objects["equipmentChassis"][0].server_sioc_connectivity

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

        parent_mo = "sys"
        mo_server_properties = None
        if self._device.platform_type == "classic":
            mo_server_properties = ComputeRackUnit(parent_mo_or_dn=parent_mo, server_id="1",
                                                   asset_tag=self.asset_tag, usr_lbl=self.description)
        elif self._device.platform_type == "modular":
            mo_server_properties = EquipmentChassis(parent_mo_or_dn=parent_mo, asset_tag=self.asset_tag,
                                                    usr_lbl=self.description,
                                                    server_sioc_connectivity=self.server_sioc_connectivity)

        if commit:
            if self.commit(mo=mo_server_properties) != True:
                return False

        return True


class UcsImcDynamicStorageZoning(UcsImcConfigObject):
    _CONFIG_NAME = "Dynamic Storage Zoning"

    def __init__(self, parent=None, json_content=None):
        UcsImcConfigObject.__init__(self, parent=parent)
        self.disks = []

        if self._config.load_from == "live":
            if "computeServerRef" in self._config.sdk_objects:
                for compute_server_ref in self._config.sdk_objects["computeServerRef"]:
                    disk = {}
                    disk["slot"] = compute_server_ref.slot
                    disk["ownership"] = compute_server_ref.ownership
                    self.disks.append(disk)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

                for element in self.disks:
                    for value in ["slot", "ownership"]:
                        if value not in element:
                            element[value] = None

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration")
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration" +
                                ", waiting for a commit")

        parent_mo = "sys/chassis-1/enc-1"
        mo_compute_server_ref = None

        # Fetching the information needed
        all_compute_server_refs = self._device.query(mode="classid", target="computeServerRef")

        for disk in self.disks:
            live_compute_server_ref = [compute_server_ref for compute_server_ref in all_compute_server_refs
                                       if compute_server_ref.slot == disk["slot"]]
            if len(live_compute_server_ref) == 1:
                if live_compute_server_ref[0].ownership == "none":
                    live_compute_server_ref[0].ownership = disk["ownership"]
                    #mo_compute_server_ref = ComputeServerRef(parent_mo_or_dn=parent_mo, ownership=disk["ownership"],
                    #                                         slot=disk["slot"])
                elif live_compute_server_ref[0].ownership != disk["ownership"]:
                    self.logger(level="debug", message="Un-assigning disk " + disk["id"] + " before changing ownership")
                    # mo_compute_server_ref = ComputeServerRef(parent_mo_or_dn=parent_mo, ownership="none",
                    #                                          slot=disk["slot"])
                    live_compute_server_ref[0].ownership = "none"
                    if commit:
                        if self.commit(mo=live_compute_server_ref[0]) != True:
                            return False
                    # mo_compute_server_ref = ComputeServerRef(parent_mo_or_dn=parent_mo, ownership=disk["ownership"],
                    #                                          slot=disk["slot"])
                    live_compute_server_ref[0].ownership = disk["ownership"]

            if commit:
                if self.commit(mo=live_compute_server_ref[0]) != True:
                    return False

        return True


class UcsImcIpBlockingProperties(UcsImcConfigObject):
    _CONFIG_NAME = "IP Blocking Properties"

    def __init__(self, parent=None, json_content=None):
        UcsImcConfigObject.__init__(self, parent=parent)
        self.enable = None
        self.fail_count = None
        self.fail_window = None
        self.penalty_time = None

        if self._config.load_from == "live":
            if "ipBlocking" in self._config.sdk_objects:
                if len(self._config.sdk_objects["ipBlocking"]) == 1:
                    self.enable = self._config.sdk_objects["ipBlocking"][0].enable
                    self.fail_count = self._config.sdk_objects["ipBlocking"][0].fail_count
                    self.fail_window = self._config.sdk_objects["ipBlocking"][0].fail_window
                    self.penalty_time = self._config.sdk_objects["ipBlocking"][0].penalty_time

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

        parent_mo = "sys/rack-unit-1/mgmt/if-1"
        mo_ip_blocking = IpBlocking(parent_mo_or_dn=parent_mo, enable=self.enable, fail_count=self.fail_count,
                                    fail_window=self.fail_window, penalty_time=self.penalty_time)
        if commit:
            if self.commit(mo=mo_ip_blocking) != True:
                return False
        return True


class UcsImcIpFilteringProperties(UcsImcConfigObject):
    _CONFIG_NAME = "IP Filtering Properties"

    def __init__(self, parent=None, json_content=None):
        UcsImcConfigObject.__init__(self, parent=parent)
        self.enable = None
        self.ip_filter_1 = None
        self.ip_filter_2 = None
        self.ip_filter_3 = None
        self.ip_filter_4 = None

        if self._config.load_from == "live":
            if "ipFiltering" in self._config.sdk_objects:
                if len(self._config.sdk_objects["ipFiltering"]) == 1:
                    self.enable = self._config.sdk_objects["ipFiltering"][0].enable
                    self.ip_filter_1 = self._config.sdk_objects["ipFiltering"][0].filter1
                    self.ip_filter_2 = self._config.sdk_objects["ipFiltering"][0].filter2
                    self.ip_filter_3 = self._config.sdk_objects["ipFiltering"][0].filter3
                    self.ip_filter_4 = self._config.sdk_objects["ipFiltering"][0].filter4

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

        parent_mo = "sys/rack-unit-1/mgmt/if-1"
        mo_ip_filtering = IpFiltering(parent_mo_or_dn=parent_mo, enable=self.enable, filter1=self.ip_filter_1,
                                      filter2=self.ip_filter_2, filter3=self.ip_filter_3, filter4=self.ip_filter_4)
        if commit:
            if self.commit(mo=mo_ip_filtering) != True:
                return False
        return True


class UcsImcPowerPolicies(UcsImcConfigObject):
    _CONFIG_NAME = "Power Policies"

    def __init__(self, parent=None, json_content=None):
        UcsImcConfigObject.__init__(self, parent=parent)
        self.power_restore_policy = None
        self.power_delay_type = None
        self.power_delay_value = None
        self.fan_policy = None

        if self._config.load_from == "live":
            if "biosVfResumeOnACPowerLoss" in self._config.sdk_objects:
                if len(self._config.sdk_objects["biosVfResumeOnACPowerLoss"]) == 1:
                    self.power_delay_type = self._config.sdk_objects["biosVfResumeOnACPowerLoss"][0].delay_type
                    self.power_delay_value = self._config.sdk_objects["biosVfResumeOnACPowerLoss"][0].delay
                    self.power_restore_policy = \
                        self._config.sdk_objects["biosVfResumeOnACPowerLoss"][0].vp_resume_on_ac_power_loss
                    if self.power_restore_policy == "last-state":
                        self.power_restore_policy = "Restore Last State"
                    if self.power_restore_policy == "reset":
                        self.power_restore_policy = "Power On"
                    if self.power_restore_policy == "stay-off":
                        self.power_restore_policy = "Power Off"

            if "fanPolicy" in self._config.sdk_objects:
                if len(self._config.sdk_objects["fanPolicy"]) == 1:
                    self.fan_policy = self._config.sdk_objects["fanPolicy"][0].configured_fan_policy

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

        parent_mo = "sys/rack-unit-1/board"

        power_delay_value = self.power_delay_value
        power_delay_type = self.power_delay_type
        power_restore_policy = None
        if self.power_restore_policy in ["Restore Last State", "restore_last_state", "restore last state"]:
            power_restore_policy = "last-state"
            power_delay_value = None
            power_delay_type = None
        elif self.power_restore_policy in ["Power On", "power_on", "power on"]:
            power_restore_policy = "reset"
        elif self.power_restore_policy in ["Power Off", "power_off", "power off"]:
            power_restore_policy = "stay-off"
            power_delay_value = None
            power_delay_type = None
        mo_bios_vf_resume_on_ac_power_loss = BiosVfResumeOnACPowerLoss(parent_mo_or_dn=parent_mo,
                                                                       vp_resume_on_ac_power_loss=power_restore_policy,
                                                                       delay_type=power_delay_type,
                                                                       delay=power_delay_value)
        mo_fan_policy = FanPolicy(parent_mo_or_dn=parent_mo, configured_fan_policy=self.fan_policy)
        if commit:
            if self.commit(mo=mo_bios_vf_resume_on_ac_power_loss) != True:
                return False
            if self.commit(mo=mo_fan_policy) != True:
                return False
        return True


class UcsImcAdapterCard(UcsImcConfigObject):
    _CONFIG_NAME = "Adapter Card"

    def __init__(self, parent=None, json_content=None, adaptor_unit=None):
        UcsImcConfigObject.__init__(self, parent=parent)
        self.account_status = None
        self.id = None
        self.descr = None
        self.fip_mode = None
        self.lldp = None
        self.vntag_mode = None
        self.vnics = []
        self.vhbas = []

        if self._config.load_from == "live":
            # Locating SDK objects needed to initialize

            if adaptor_unit is not None:
                self.id = adaptor_unit.id
                self.descr = adaptor_unit.description
                for gen_profile in self._config.sdk_objects["adaptorGenProfile"]:
                    if "sys/rack-unit-1/adaptor-" + self.id + "/" in gen_profile.dn:
                        self.fip_mode = gen_profile.fip_mode
                        self.vntag_mode = gen_profile.vntag_mode
                        self.lldp = gen_profile.lldp
                for adaptor_host in self._config.sdk_objects["adaptorHostEthIf"]:
                    if "sys/rack-unit-1/adaptor-" + self.id + "/" in adaptor_host.dn:
                        vnic = {}
                        vnic["name"] = adaptor_host.name
                        vnic["cdn"] = adaptor_host.cdn
                        vnic["mtu"] = adaptor_host.mtu
                        vnic["uplink_port"] = adaptor_host.uplink_port
                        vnic["mac_address"] = adaptor_host.mac
                        vnic["class_of_service"] = adaptor_host.class_of_service
                        vnic["channel_number"] = adaptor_host.channel_number
                        vnic["port_profile"] = adaptor_host.port_profile
                        vnic["pxe_boot"] = adaptor_host.pxe_boot

                        for gen_profile in self._config.sdk_objects["adaptorEthGenProfile"]:
                            if "sys/rack-unit-1/adaptor-" + self.id + "/host-eth-" + adaptor_host.name + "/" \
                                    in gen_profile.dn:
                                vnic["trust_host_cos"] = gen_profile.trusted_class_of_service
                                vnic["pci_order"] = gen_profile.order
                                vnic["default_vlan"] = gen_profile.vlan
                                vnic["vlan_mode"] = gen_profile.vlan_mode
                                vnic["rate_limit"] = gen_profile.rate_limit
                                vnic["vmq"] = gen_profile.vmq
                                vnic["arfs"] = gen_profile.arfs
                                vnic["uplink_failover"] = gen_profile.uplink_failover
                                vnic["uplink_failback_timeout"] = gen_profile.uplink_failback_timeout

                        for interrupt_profile in self._config.sdk_objects["adaptorEthInterruptProfile"]:
                            if "sys/rack-unit-1/adaptor-" + self.id + "/host-eth-" + adaptor_host.name + "/" \
                                    in interrupt_profile.dn:
                                vnic["interrupt_count"] = interrupt_profile.count
                                vnic["interrupt_mode"] = interrupt_profile.mode
                                vnic["coalescing_time"] = interrupt_profile.coalescing_time
                                vnic["coalescing_type"] = interrupt_profile.coalescing_type

                        for queue_profile in self._config.sdk_objects["adaptorEthRecvQueueProfile"]:
                            if "sys/rack-unit-1/adaptor-" + self.id + "/host-eth-" + adaptor_host.name + "/" \
                                    in queue_profile.dn:
                                vnic["receive_queue_count"] = queue_profile.count
                                vnic["receive_queue_ring_size"] = queue_profile.ring_size
                        for work_queue_profile in self._config.sdk_objects["adaptorEthWorkQueueProfile"]:
                            if "sys/rack-unit-1/adaptor-" + self.id + "/host-eth-" + adaptor_host.name + "/" \
                                    in work_queue_profile.dn:
                                vnic["transmit_queue_count"] = work_queue_profile.count
                                vnic["transmit_queue_ring_size"] = work_queue_profile.ring_size
                        for comp_queue_profile in self._config.sdk_objects["adaptorEthCompQueueProfile"]:
                            if "sys/rack-unit-1/adaptor-" + self.id + "/host-eth-" + adaptor_host.name + "/" \
                                    in comp_queue_profile.dn:
                                vnic["completion_queue_count"] = comp_queue_profile.count
                                # vnic["completion_queue_ring_size"] = comp_queue_profile.ring_size
                        for offload_profile in self._config.sdk_objects["adaptorEthOffloadProfile"]:
                            if "sys/rack-unit-1/adaptor-" + self.id + "/host-eth-" + adaptor_host.name + "/" \
                                    in offload_profile.dn:
                                vnic["tcp_rx_offload_checksum_validation"] = offload_profile.tcp_rx_checksum
                                vnic["tcp_tx_offload_checksum_validation"] = offload_profile.tcp_tx_checksum
                                vnic["tcp_segment"] = offload_profile.tcp_segment
                                vnic["tcp_offload_large_receive"] = offload_profile.large_receive
                        for rss_profile in self._config.sdk_objects["adaptorRssProfile"]:
                            if "sys/rack-unit-1/adaptor-" + self.id + "/host-eth-" + adaptor_host.name + "/" \
                                    in rss_profile.dn:
                                vnic["tcp_receive_side_scaling"] = rss_profile.receive_side_scaling
                        for ipv4_rss_profile in self._config.sdk_objects["adaptorIpV4RssHashProfile"]:
                            if "sys/rack-unit-1/adaptor-" + self.id + "/host-eth-" + adaptor_host.name + "/" \
                                    in ipv4_rss_profile.dn:
                                vnic["ipv4_rss"] = ipv4_rss_profile.ip_hash
                                vnic["tcp_ipv4_rss"] = ipv4_rss_profile.tcp_hash
                        for ipv6_rss_profile in self._config.sdk_objects["adaptorIpV6RssHashProfile"]:
                            if "sys/rack-unit-1/adaptor-" + self.id + "/host-eth-" + adaptor_host.name + "/" \
                                    in ipv6_rss_profile.dn:
                                vnic["ipv6_rss"] = ipv6_rss_profile.ip_hash
                                vnic["tcp_ipv6_rss"] = ipv6_rss_profile.tcp_hash
                        for ext_ipv6_rss_profile in self._config.sdk_objects["adaptorExtIpV6RssHashProfile"]:
                            if "sys/rack-unit-1/adaptor-" + self.id + "/host-eth-" + adaptor_host.name + "/" \
                                    in ext_ipv6_rss_profile.dn:
                                vnic["ipv6_extention_rss"] = ext_ipv6_rss_profile.ip_hash
                                vnic["tcp_ipv6_extention_rss"] = ext_ipv6_rss_profile.tcp_hash
                        for usnic in self._config.sdk_objects["adaptorEthUSNICProfile"]:
                            if "sys/rack-unit-1/adaptor-" + self.id + "/host-eth-" + adaptor_host.name + "/" \
                                    in usnic.dn:
                                vnic['usnic'] = usnic.usnic_count
                                vnic['usnic_transmit_queue_count'] = usnic.transmit_queue_count
                                vnic['usnic_transmit_queue_ring_size'] = usnic.transmit_queue_ring_size
                                vnic['usnic_receive_queue_count'] = usnic.receive_queue_count
                                vnic['usnic_receive_queue_ring_size'] = usnic.receive_queue_ring_size
                                vnic['usnic_completion_queue_count'] = usnic.completion_queue_count
                                vnic['usnic_interrupt_count'] = usnic.interrupt_count
                                vnic['usnic_interrupt_coalescing_type'] = usnic.coalescing_type
                                vnic['usnic_interrupt_coalescing_timer_time'] = usnic.coalescing_time
                                vnic['usnic_class_of_service'] = usnic.class_of_service
                                vnic['usnic_large_receive'] = usnic.large_receive
                                vnic['usnic_tcp_segment_offload'] = usnic.tcp_segment
                                vnic['usnic_tcp_tx_checksum'] = usnic.tcp_tx_checksum
                                vnic['usnic_tcp_rx_checksum'] = usnic.tcp_rx_checksum

                        self.vnics.append(vnic)

                for adaptor_host in self._config.sdk_objects["adaptorHostFcIf"]:
                    if "sys/rack-unit-1/adaptor-" + self.id + "/" in adaptor_host.dn:
                        vhba = {}
                        vhba["fc_boot_table"] = []
                        vhba["name"] = adaptor_host.name
                        vhba["target_wwnn"] = adaptor_host.wwnn
                        vhba["target_wwpn"] = adaptor_host.wwpn
                        vhba["fc_san_boot"] = adaptor_host.san_boot
                        # vhba["uplink_port"] = adaptor_host.uplink_port
                        vhba["channel_number"] = adaptor_host.channel_number
                        vhba["port_profile"] = adaptor_host.port_profile
                        for fc_gen_profile in self._config.sdk_objects["adaptorFcGenProfile"]:
                            if "sys/rack-unit-1/adaptor-" + self.id + "/host-fc-" + adaptor_host.name + "/" \
                                    in fc_gen_profile.dn:
                                vhba["persistent_lun_bindings"] = fc_gen_profile.persistent_lun_bind
                                vhba["mac_address"] = fc_gen_profile.mac
                                vhba["vlan"] = fc_gen_profile.vlan
                                vhba["class_of_service"] = fc_gen_profile.class_of_service
                                vhba["rate_limit"] = fc_gen_profile.rate_limit
                                vhba["pcie_device_order"] = fc_gen_profile.order
                                vhba["max_data_field_size"] = fc_gen_profile.max_data_field_size
                                vhba["pci_link"] = fc_gen_profile.pci_link
                        for recovery_profile in self._config.sdk_objects["adaptorFcErrorRecoveryProfile"]:
                            if "sys/rack-unit-1/adaptor-" + self.id + "/host-fc-" + adaptor_host.name + "/" \
                                    in recovery_profile.dn:
                                vhba["edtov"] = recovery_profile.error_detect_timeout
                                vhba["ratov"] = recovery_profile.resource_allocation_timeout
                                vhba["fcp_error_recovery"] = recovery_profile.fcp_error_recovery
                                vhba["link_down_timeout"] = recovery_profile.link_down_timeout
                                vhba["port_down_io_retry_count"] = recovery_profile.port_down_io_retry_count
                                vhba["io_timeout_retry"] = recovery_profile.io_timeout_retry
                        for error_recovery_profile in self._config.sdk_objects["adaptorFcInterruptProfile"]:
                            if "sys/rack-unit-1/adaptor-" + self.id + "/host-fc-" + adaptor_host.name + "/" \
                                    in error_recovery_profile.dn:
                                vhba["interrupt_mode"] = error_recovery_profile.mode
                        for fc_port_profile in self._config.sdk_objects["adaptorFcPortProfile"]:
                            if "sys/rack-unit-1/adaptor-" + self.id + "/host-fc-" + adaptor_host.name + "/" \
                                    in fc_port_profile.dn:
                                vhba["io_throttle_count"] = fc_port_profile.io_throttle_count
                                vhba["luns_per_target"] = fc_port_profile.luns_per_target
                                vhba["lun_queue_depth"] = fc_port_profile.lun_queue_depth
                        for flogi_profile in self._config.sdk_objects["adaptorFcPortFLogiProfile"]:
                            if "sys/rack-unit-1/adaptor-" + self.id + "/host-fc-" + adaptor_host.name + "/" \
                                    in flogi_profile.dn:
                                vhba["flogi_retries"] = flogi_profile.retries
                                vhba["flogi_timeout"] = flogi_profile.timeout
                        for plogi_profile in self._config.sdk_objects["adaptorFcPortPLogiProfile"]:
                            if "sys/rack-unit-1/adaptor-" + self.id + "/host-fc-" + adaptor_host.name + "/" \
                                    in plogi_profile.dn:
                                vhba["plogi_retries"] = plogi_profile.retries
                                vhba["plogi_timeout"] = plogi_profile.timeout
                        for cdb_work_queue_profile in self._config.sdk_objects["adaptorFcCdbWorkQueueProfile"]:
                            if "sys/rack-unit-1/adaptor-" + self.id + "/host-fc-" + adaptor_host.name + "/" \
                                    in cdb_work_queue_profile.dn:
                                vhba["cdb_transmit_queue_timeout"] = cdb_work_queue_profile.count
                                vhba["cdb_transmit_queue_ring_size"] = cdb_work_queue_profile.ring_size
                        for fc_work_queue_profile in self._config.sdk_objects["adaptorFcWorkQueueProfile"]:
                            if "sys/rack-unit-1/adaptor-" + self.id + "/host-fc-" + adaptor_host.name + "/" \
                                    in fc_work_queue_profile.dn:
                                vhba["fc_work_queue_ring_size"] = fc_work_queue_profile.ring_size
                        for fc_recv_queue_profile in self._config.sdk_objects["adaptorFcRecvQueueProfile"]:
                            if "sys/rack-unit-1/adaptor-" + self.id + "/host-fc-" + adaptor_host.name + "/" \
                                    in fc_recv_queue_profile.dn:
                                vhba["fc_receive_queue_ring_size"] = fc_recv_queue_profile.ring_size
                        for boot_entry in self._config.sdk_objects["adaptorFcBootTable"]:
                            if "sys/rack-unit-1/adaptor-" + self.id + "/host-fc-" + adaptor_host.name + "/" \
                                    in boot_entry.dn:
                                entry = {}
                                entry["target_wwpn"] = boot_entry.target_wwpn
                                entry["lun_id"] = boot_entry.boot_lun
                                entry["index"] = boot_entry.index
                                vhba["fc_boot_table"].append(entry)

                        self.vhbas.append(vhba)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

                for element in self.vnics:
                    for value in ["vlan_mode",
                                  "coalescing_type",
                                  "pci_order",
                                  "tcp_ipv6_rss",
                                  "interrupt_mode",
                                  "transmit_queue_ring_size",
                                  "cdn",
                                  "completion_queue_count",
                                  "uplink_failover",
                                  "transmit_queue_count",
                                  "trust_host_cos",
                                  "class_of_service",
                                  "port_profile",
                                  "mac_address",
                                  "name",
                                  "tcp_segment",
                                  "tcp_rx_offload_checksum_validation",
                                  "receive_queue_ring_size",
                                  "default_vlan",
                                  "channel_number",
                                  "rate_limit",
                                  "uplink_failback_timeout",
                                  "mtu",
                                  "ipv6_rss",
                                  "receive_queue_count",
                                  "arfs",
                                  "tcp_offload_large_receive",
                                  "pxe_boot",
                                  "tcp_receive_side_scaling",
                                  "uplink_port",
                                  "tcp_ipv4_rss",
                                  "ipv6_extention_rss",
                                  "tcp_ipv6_extention_rss",
                                  "interrupt_count",
                                  "tcp_tx_offload_checksum_validation",
                                  "ipv4_rss",
                                  "coalescing_time",
                                  "vmq",
                                  "usnic",
                                  "usnic_transmit_queue_count",
                                  "usnic_transmit_queue_ring_size",
                                  "usnic_receive_queue_count",
                                  "usnic_receive_queue_ring_size",
                                  "usnic_completion_queue_count",
                                  "usnic_interrupt_count",
                                  "usnic_interrupt_coalescing_type",
                                  "usnic_interrupt_coalescing_timer_time",
                                  "usnic_class_of_service",
                                  "usnic_large_receive",
                                  "usnic_tcp_segment_offload",
                                  "usnic_tcp_tx_checksum",
                                  "usnic_tcp_rx_checksum"
                                  ]:
                        if value not in element:
                            element[value] = None

                for element in self.vhbas:
                    for value in ["fc_work_queue_ring_size",
                                  "channel_number",
                                  "interrupt_mode",
                                  "link_down_timeout",
                                  "plogi_retries",
                                  "class_of_service",
                                  "port_profile",
                                  "mac_address",
                                  "name",
                                  "cdb_transmit_queue_timeout",
                                  "io_timeout_retry",
                                  "fcp_error_recovery",
                                  "ratov",
                                  "fc_receive_queue_ring_size",
                                  "cdb_transmit_queue_ring_size",
                                  "rate_limit",
                                  "max_data_field_size",
                                  "plogi_timeout",
                                  "target_wwpn",
                                  "pci_link",
                                  "flogi_retries",
                                  "pcie_device_order",
                                  "luns_per_target",
                                  "io_throttle_count",
                                  "vlan",
                                  "edtov",
                                  "fc_san_boot",
                                  "lun_queue_depth",
                                  "target_wwnn",
                                  "flogi_timeout",
                                  "persistent_lun_bindings",
                                  "port_down_io_retry_count",
                                  "fc_boot_table"]:
                        if value not in element:
                            element[value] = None

                        elif value == "fc_boot_table":
                            for subelement in element[value]:
                                for subvalue in ["target_wwpn", "lun_id", "index"]:
                                    if subvalue not in subelement:
                                        subelement[subvalue] = None
        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + self.id)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + self.id)

        parent_mo = "sys/rack-unit-1"
        mo_adaptor_unit = AdaptorUnit(parent_mo_or_dn=parent_mo, id=self.id, description=self.descr)
        AdaptorGenProfile(parent_mo_or_dn=mo_adaptor_unit, fip_mode=self.fip_mode, vntag_mode=self.vntag_mode,
                          lldp=self.lldp)
        if commit:
            if self.commit(mo=mo_adaptor_unit) != True:
                return False

        for vnic in self.vnics:
            mo_adaptor_eth = AdaptorHostEthIf(parent_mo_or_dn=mo_adaptor_unit, name=vnic["name"], cdn=vnic["cdn"],
                                              mtu=vnic["mtu"], uplink_port=vnic["uplink_port"], mac=vnic["mac_address"],
                                              class_of_service=vnic["class_of_service"], pxe_boot=vnic["pxe_boot"],
                                              channel_number=vnic["channel_number"], port_profile=vnic["port_profile"])
            AdaptorEthGenProfile(parent_mo_or_dn=mo_adaptor_eth, trusted_class_of_service=vnic["trust_host_cos"],
                                 order=vnic["pci_order"], vlan=vnic["default_vlan"], vlan_mode=vnic["vlan_mode"],
                                 rate_limit=vnic["rate_limit"], vmq=vnic["vmq"], arfs=vnic["arfs"],
                                 uplink_failover=vnic["uplink_failover"],
                                 uplink_failback_timeout=vnic["uplink_failback_timeout"])
            AdaptorEthInterruptProfile(parent_mo_or_dn=mo_adaptor_eth, count=vnic["interrupt_count"],
                                       mode=vnic["interrupt_mode"], coalescing_time=vnic["coalescing_time"],
                                       coalescing_type=vnic["coalescing_type"])
            AdaptorEthRecvQueueProfile(parent_mo_or_dn=mo_adaptor_eth, count=vnic["receive_queue_count"],
                                       ring_size=vnic["receive_queue_ring_size"])
            AdaptorEthWorkQueueProfile(parent_mo_or_dn=mo_adaptor_eth, count=vnic["transmit_queue_count"],
                                       ring_size=vnic["transmit_queue_ring_size"])
            AdaptorEthCompQueueProfile(parent_mo_or_dn=mo_adaptor_eth, count=vnic["completion_queue_count"],
                                       # ring_size=vnic["completion_queue_ring_size"]
                                       )
            AdaptorEthOffloadProfile(parent_mo_or_dn=mo_adaptor_eth, large_receive=vnic["tcp_offload_large_receive"],
                                     tcp_rx_checksum=vnic["tcp_rx_offload_checksum_validation"],
                                     tcp_segment=vnic["tcp_segment"],
                                     tcp_tx_checksum=vnic["tcp_tx_offload_checksum_validation"])
            AdaptorRssProfile(parent_mo_or_dn=mo_adaptor_eth, receive_side_scaling=vnic["tcp_receive_side_scaling"])
            AdaptorIpV4RssHashProfile(parent_mo_or_dn=mo_adaptor_eth, ip_hash=vnic["ipv4_rss"],
                                      tcp_hash=vnic["tcp_ipv4_rss"])
            AdaptorIpV6RssHashProfile(parent_mo_or_dn=mo_adaptor_eth, ip_hash=vnic["ipv6_rss"],
                                      tcp_hash=vnic["tcp_ipv6_rss"])
            AdaptorExtIpV6RssHashProfile(parent_mo_or_dn=mo_adaptor_eth, ip_hash=vnic["ipv6_extention_rss"],
                                         tcp_hash=vnic["tcp_ipv6_extention_rss"])

            if commit:
                self.commit(mo=mo_adaptor_eth)

            if vnic['usnic']:
                mo_usnic = AdaptorEthUSNICProfile(parent_mo_or_dn=mo_adaptor_eth, usnic_count=vnic['usnic'],
                                                  transmit_queue_count=vnic['usnic_transmit_queue_count'],
                                                  transmit_queue_ring_size=vnic['usnic_transmit_queue_ring_size'],
                                                  receive_queue_count=vnic['usnic_receive_queue_count'],
                                                  receive_queue_ring_size=vnic['usnic_receive_queue_ring_size'],
                                                  completion_queue_count=vnic['usnic_completion_queue_count'],
                                                  interrupt_count=vnic['usnic_interrupt_count'],
                                                  coalescing_type=vnic['usnic_interrupt_coalescing_type'],
                                                  coalescing_time=vnic['usnic_interrupt_coalescing_timer_time'],
                                                  class_of_service=vnic['usnic_class_of_service'],
                                                  large_receive=vnic['usnic_large_receive'],
                                                  tcp_segment=vnic['usnic_tcp_segment_offload'],
                                                  tcp_tx_checksum=vnic['usnic_tcp_tx_checksum'],
                                                  tcp_rx_checksum=vnic['usnic_tcp_rx_checksum'])

                if commit:
                    self.commit(mo=mo_usnic)

        for vhba in self.vhbas:
            mo_adaptor_fc = AdaptorHostFcIf(parent_mo_or_dn=mo_adaptor_unit, name=vhba["name"],
                                            wwnn=vhba["target_wwnn"], wwpn=vhba["target_wwpn"],
                                            san_boot=vhba["fc_san_boot"], channel_number=vhba["channel_number"],
                                            # uplink_port=vhba["uplink_port"],
                                            port_profile=vhba["port_profile"])
            AdaptorFcGenProfile(parent_mo_or_dn=mo_adaptor_fc, persistent_lun_bind=vhba["persistent_lun_bindings"],
                                mac=vhba["mac_address"], vlan=vhba["vlan"], class_of_service=vhba["class_of_service"],
                                rate_limit=vhba["rate_limit"], order=vhba["pcie_device_order"],
                                max_data_field_size=vhba["max_data_field_size"], pci_link=vhba["pci_link"])
            AdaptorFcErrorRecoveryProfile(parent_mo_or_dn=mo_adaptor_fc, error_detect_timeout=vhba["edtov"],
                                          resource_allocation_timeout=vhba["ratov"],
                                          fcp_error_recovery=vhba["fcp_error_recovery"],
                                          link_down_timeout=vhba["link_down_timeout"],
                                          port_down_io_retry_count=vhba["port_down_io_retry_count"],
                                          io_timeout_retry=vhba["io_timeout_retry"])
            AdaptorFcInterruptProfile(parent_mo_or_dn=mo_adaptor_fc, mode=vhba["interrupt_mode"])
            AdaptorFcPortProfile(parent_mo_or_dn=mo_adaptor_fc, io_throttle_count=vhba["io_throttle_count"],
                                 luns_per_target=vhba["luns_per_target"], lun_queue_depth=vhba["lun_queue_depth"])
            AdaptorFcPortFLogiProfile(parent_mo_or_dn=mo_adaptor_fc, retries=vhba["flogi_retries"],
                                      timeout=vhba["flogi_timeout"])
            AdaptorFcPortPLogiProfile(parent_mo_or_dn=mo_adaptor_fc, retries=vhba["plogi_retries"],
                                      timeout=vhba["plogi_timeout"])
            AdaptorFcCdbWorkQueueProfile(parent_mo_or_dn=mo_adaptor_fc, count=vhba["cdb_transmit_queue_timeout"],
                                         ring_size=vhba["cdb_transmit_queue_ring_size"])
            AdaptorFcWorkQueueProfile(parent_mo_or_dn=mo_adaptor_fc, ring_size=vhba["fc_work_queue_ring_size"])
            AdaptorFcRecvQueueProfile(parent_mo_or_dn=mo_adaptor_fc, ring_size=vhba["fc_receive_queue_ring_size"])
            if vhba["fc_boot_table"]:
                for entry_table in vhba["fc_boot_table"]:
                    AdaptorFcBootTable(parent_mo_or_dn=mo_adaptor_fc, boot_lun=entry_table["lun_id"],
                                       target_wwpn=entry_table["target_wwpn"], index=entry_table['index'])

            if commit:
                self.commit(mo=mo_adaptor_fc)

        return True


class UcsImcCommunicationsServices(UcsImcConfigObject):
    _CONFIG_NAME = "Communication Services"

    def __init__(self, parent=None, json_content=None):
        UcsImcConfigObject.__init__(self, parent=parent)
        self.http_state = None
        self.https_state = None
        self.redirect_state = None
        self.http_port = None
        self.https_port = None
        self.session_timeout = None
        # TODO Find the mo for xml api state
        self.xml_api_state = None
        self.ssh_state = None
        self.ssh_port = None
        self.ssh_timeout = None
        self.redfish_state = None
        self.ipmi_over_lan_state = None
        self.ipmi_over_lan_privilege_level_limit = None
        self.ipmi_over_lan_encryption_key = None

        if self._config.load_from == "live":

            if "commHttp" in self._config.sdk_objects:
                if len(self._config.sdk_objects["commHttp"]) == 1:
                    self.http_state = self._config.sdk_objects["commHttp"][0].admin_state
                    self.http_port = self._config.sdk_objects["commHttp"][0].port
                    self.session_timeout = self._config.sdk_objects["commHttp"][0].session_timeout
                    self.redirect_state = self._config.sdk_objects["commHttp"][0].redirect_state

            if "commHttps" in self._config.sdk_objects:
                if len(self._config.sdk_objects["commHttps"]) == 1:
                    self.https_state = self._config.sdk_objects["commHttps"][0].admin_state
                    self.https_port = self._config.sdk_objects["commHttps"][0].port

            if "commSsh" in self._config.sdk_objects:
                if len(self._config.sdk_objects["commSsh"]) == 1:
                    self.ssh_state = self._config.sdk_objects["commSsh"][0].admin_state
                    self.ssh_port = self._config.sdk_objects["commSsh"][0].port
                    self.ssh_timeout = self._config.sdk_objects["commSsh"][0].session_timeout

            if "commRedfish" in self._config.sdk_objects:
                if len(self._config.sdk_objects["commRedfish"]) == 1:
                    self.redfish_state = self._config.sdk_objects["commRedfish"][0].admin_state

            if "commIpmiLan" in self._config.sdk_objects:
                if len(self._config.sdk_objects["commIpmiLan"]) == 1:
                    self.ipmi_over_lan_state = self._config.sdk_objects["commIpmiLan"][0].admin_state
                    self.ipmi_over_lan_privilege_level_limit = self._config.sdk_objects["commIpmiLan"][0].priv
                    self.ipmi_over_lan_encryption_key = self._config.sdk_objects["commIpmiLan"][0].key

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
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration")

        parent_mo = "sys/svc-ext"
        mo_comm_http = CommHttp(parent_mo_or_dn=parent_mo, admin_state=self.http_state, port=self.http_port,
                                session_timeout=self.session_timeout, redirect_state=self.redirect_state)
        mo_comm_https = CommHttps(parent_mo_or_dn=parent_mo, admin_state=self.https_state, port=self.https_port)
        mo_comm_redfish = CommRedfish(parent_mo_or_dn=parent_mo, admin_state=self.redfish_state)
        mo_comm_ssh = CommSsh(parent_mo_or_dn=parent_mo, admin_state=self.ssh_state, port=self.ssh_port,
                              session_timeout=self.ssh_timeout)
        mo_comm_ipmi = None
        if self.ipmi_over_lan_state:
            if self.ipmi_over_lan_state == "enabled":
                mo_comm_ipmi = CommIpmiLan(parent_mo_or_dn=parent_mo, admin_state=self.ipmi_over_lan_state,
                                           priv=self.ipmi_over_lan_privilege_level_limit,
                                           key=self.ipmi_over_lan_encryption_key)
            else:
                mo_comm_ipmi = CommIpmiLan(parent_mo_or_dn=parent_mo, admin_state=self.ipmi_over_lan_state)

        if commit:
            self.commit(mo=mo_comm_http)
            self.commit(mo=mo_comm_https)
            self.commit(mo=mo_comm_redfish)
            self.commit(mo=mo_comm_ssh)
            self.commit(mo=mo_comm_ipmi)


class UcsImcChassisInventory(UcsImcConfigObject):
    _CONFIG_NAME = "Chassis Inventory"

    def __init__(self, parent=None, json_content=None):
        UcsImcConfigObject.__init__(self, parent=parent)
        self.dimm_black_list = None

        if self._config.load_from == "live":
            if "memoryArray" in self._config.sdk_objects:
                if len(self._config.sdk_objects["memoryArray"]) == 1:
                    self.dimm_black_list = self._config.sdk_objects["memoryArray"][0].dimm_black_list

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

        parent_mo = "sys/rack-unit-1/board"
        mo_memory_array = MemoryArray(parent_mo_or_dn=parent_mo, id='1',
                                      dimm_black_list=self.dimm_black_list
                                      )
        if commit:
            if self.commit(mo=mo_memory_array) != True:
                return False
        return True


class UcsImcPowerCapConfiguration(UcsImcConfigObject):
    _CONFIG_NAME = "Power Cap Configuration"

    def __init__(self, parent=None, json_content=None):
        UcsImcConfigObject.__init__(self, parent=parent)
        self.power_capping = None
        self.enable_standard_profile = None
        self.enable_advanced_profile = None
        self.allow_throttle = None
        self.correction_time = None
        self.action = None
        self.hard_cap = None
        self.suspend_period = None
        self.platform_power_limit = None
        self.cpu_power_limit = None
        self.memory_power_limit = None
        self.safe_throttle_level_memory = None
        self.safe_throttle_level_cpu = None
        self.safe_throttle_level_platform = None
        self.failsafe_timeout = None
        self.platform_temp_trigger = None
        self.thermal_power_limit = None

        if self._config.load_from == "live":
            if "powerBudget" in self._config.sdk_objects:
                if len(self._config.sdk_objects["powerBudget"]) == 1:
                    self.power_capping = self._config.sdk_objects["powerBudget"][0].admin_state

            if "standardPowerProfile" in self._config.sdk_objects:
                if len(self._config.sdk_objects["standardPowerProfile"]) == 1:
                    self.enable_standard_profile = self._config.sdk_objects["standardPowerProfile"][0].profile_enabled
                    self.platform_power_limit = self._config.sdk_objects["standardPowerProfile"][0].power_limit
                    self.allow_throttle = self._config.sdk_objects["standardPowerProfile"][0].allow_throttle
                    self.correction_time = self._config.sdk_objects["standardPowerProfile"][0].corr_time
                    self.action = self._config.sdk_objects["standardPowerProfile"][0].corr_action
                    self.hard_cap = self._config.sdk_objects["standardPowerProfile"][0].hard_cap
                    self.suspend_period = self._config.sdk_objects["standardPowerProfile"][0].suspend_period

            if "advancedPowerProfile" in self._config.sdk_objects:
                if len(self._config.sdk_objects["advancedPowerProfile"]) == 1:
                    self.enable_advanced_profile = self._config.sdk_objects["advancedPowerProfile"][0].profile_enabled
                    self.allow_throttle = self._config.sdk_objects["advancedPowerProfile"][0].allow_throttle
                    self.correction_time = self._config.sdk_objects["advancedPowerProfile"][0].corr_time
                    self.action = self._config.sdk_objects["advancedPowerProfile"][0].corr_action
                    self.hard_cap = self._config.sdk_objects["advancedPowerProfile"][0].hard_cap
                    self.suspend_period = self._config.sdk_objects["advancedPowerProfile"][0].suspend_period
                    self.platform_power_limit = self._config.sdk_objects["advancedPowerProfile"][0].power_limit
                    self.cpu_power_limit = self._config.sdk_objects["advancedPowerProfile"][0].cpu_power_limit
                    self.memory_power_limit = self._config.sdk_objects["advancedPowerProfile"][0].memory_power_limit
                    self.safe_throttle_level_memory = \
                        self._config.sdk_objects["advancedPowerProfile"][0].mem_safe_throt_lvl
                    self.safe_throttle_level_cpu = \
                        self._config.sdk_objects["advancedPowerProfile"][0].cpu_safe_throt_lvl
                    self.safe_throttle_level_platform = \
                        self._config.sdk_objects["advancedPowerProfile"][0].plat_safe_throt_lvl
                    self.failsafe_timeout = self._config.sdk_objects["advancedPowerProfile"][0].miss_rdg_timeout
                    self.platform_temp_trigger = self._config.sdk_objects["advancedPowerProfile"][0].platform_thermal
                    self.thermal_power_limit = self._config.sdk_objects["advancedPowerProfile"][0].thermal_pow_limit

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

        parent_mo = "sys/rack-unit-1"
        mo_power_budget = PowerBudget(parent_mo_or_dn=parent_mo, admin_state=self.power_capping)
        mo_std = None
        mo_adv = None
        if self.power_capping == "enabled":
            if self.enable_standard_profile == "yes" and self.enable_advanced_profile == "yes":
                self.logger(level="error", message="Power caping can't be standard and advanced")
            elif self.enable_standard_profile == "yes":
                mo_std = StandardPowerProfile(parent_mo_or_dn="sys/rack-unit-1/budget",
                                              profile_enabled=self.enable_standard_profile,
                                              power_limit=self.platform_power_limit, allow_throttle=self.allow_throttle,
                                              corr_time=self.correction_time, corr_action=self.action,
                                              hard_cap=self.hard_cap, suspend_period=self.suspend_period)
                mo_adv = AdvancedPowerProfile(parent_mo_or_dn="sys/rack-unit-1/budget",
                                              profile_enabled=self.enable_advanced_profile)
            elif self.enable_advanced_profile == "yes":
                mo_adv = AdvancedPowerProfile(parent_mo_or_dn="sys/rack-unit-1/budget",
                                              profile_enabled=self.enable_advanced_profile,
                                              allow_throttle=self.allow_throttle, corr_time=self.correction_time,
                                              corr_action=self.action, hard_cap=self.hard_cap,
                                              suspend_period=self.suspend_period, power_limit=self.platform_power_limit,
                                              cpu_power_limit=self.cpu_power_limit,
                                              memory_power_limit=self.memory_power_limit,
                                              mem_safe_throt_lvl=self.safe_throttle_level_memory,
                                              cpu_safe_throt_lvl=self.safe_throttle_level_cpu,
                                              plat_safe_throt_lvl=self.safe_throttle_level_platform,
                                              miss_rdg_timeout=self.failsafe_timeout,
                                              platform_thermal=self.platform_temp_trigger,
                                              thermal_pow_limit=self.thermal_power_limit)
                mo_std = StandardPowerProfile(parent_mo_or_dn="sys/rack-unit-1/budget",
                                              profile_enabled=self.enable_standard_profile)

        if commit:
            if self.commit(mo=mo_power_budget) != True:
                return False
            if mo_std:
                if self.commit(mo=mo_std) != True:
                    return False
            if mo_adv:
                if self.commit(mo=mo_adv) != True:
                    return False
        return True


class UcsImcVKvmProperties(UcsImcConfigObject):
    _CONFIG_NAME = "vKVM Properties"

    def __init__(self, parent=None, json_content=None):
        UcsImcConfigObject.__init__(self, parent=parent)
        self.virtual_kvm_state = None
        self.max_sessions = None
        self.remorte_port = None
        self.video_encryption_state = None
        self.local_server_video_state = None

        if self._config.load_from == "live":
            if "commKvm" in self._config.sdk_objects:
                if len(self._config.sdk_objects["commKvm"]) == 1:
                    self.virtual_kvm_state = self._config.sdk_objects["commKvm"][0].admin_state
                    self.max_sessions = self._config.sdk_objects["commKvm"][0].total_sessions
                    self.remorte_port = self._config.sdk_objects["commKvm"][0].port
                    self.video_encryption_state = self._config.sdk_objects["commKvm"][0].encryption_state
                    self.local_server_video_state = self._config.sdk_objects["commKvm"][0].local_video_state

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
        mo_comm_kvm = CommKvm(parent_mo_or_dn=parent_mo, admin_state=self.virtual_kvm_state,
                              total_sessions=self.max_sessions, port=self.remorte_port,
                              encryption_state=self.video_encryption_state,
                              local_video_state=self.local_server_video_state)

        if commit:
            if self.commit(mo=mo_comm_kvm) != True:
                return False
        return True


class UcsImcSecureKeyManagement(UcsImcConfigObject):
    _CONFIG_NAME = "Secure Key Management"

    def __init__(self, parent=None, json_content=None):
        UcsImcConfigObject.__init__(self, parent=parent)
        self.kmip_login_state = None
        self.name = None
        self.password = None

        if self._config.load_from == "live":
            if "kmipServerLogin" in self._config.sdk_objects:
                if len(self._config.sdk_objects["kmipServerLogin"]) == 1:
                    self.kmip_login_state = self._config.sdk_objects["kmipServerLogin"][0].account_status
                    self.name = self._config.sdk_objects["kmipServerLogin"][0].name
                    self.password = self._config.sdk_objects["kmipServerLogin"][0].pwd

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

        parent_mo = "sys/kmip-mgmt"
        mo_kmip_server_login = KmipServerLogin(parent_mo_or_dn=parent_mo, pwd=self.password, name=self.name,
                                               account_status=self.kmip_login_state)

        if commit:
            if self.commit(mo=mo_kmip_server_login) != True:
                return False
        return True


class UcsImcSnmp(UcsImcConfigObject):
    _CONFIG_NAME = "SNMP Service"

    def __init__(self, parent=None, json_content=None):
        UcsImcConfigObject.__init__(self, parent=parent)
        self.snmp_state = None
        self.port = None
        self.access_community_string = None
        self.snmp_community_access = None
        self.trap_community_string = None
        self.system_contact = None
        self.system_location = None
        self.snmp_inpute_engine_id = None

        if self._config.load_from == "live":
            if "commSnmp" in self._config.sdk_objects:
                if len(self._config.sdk_objects["commSnmp"]) == 1:
                    self.snmp_state = self._config.sdk_objects["commSnmp"][0].admin_state
                    self.port = self._config.sdk_objects["commSnmp"][0].port
                    self.access_community_string = self._config.sdk_objects["commSnmp"][0].community
                    self.snmp_community_access = self._config.sdk_objects["commSnmp"][0].com2_sec
                    self.trap_community_string = self._config.sdk_objects["commSnmp"][0].trap_community
                    self.system_contact = self._config.sdk_objects["commSnmp"][0].sys_contact
                    self.system_location = self._config.sdk_objects["commSnmp"][0].sys_location
                    self.snmp_inpute_engine_id = self._config.sdk_objects["commSnmp"][0].engine_id_key

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
        mo_comm_snmp = CommSnmp(parent_mo_or_dn=parent_mo,
                                admin_state=self.snmp_state,
                                port=self.port,
                                community=self.access_community_string,
                                com2_sec=self.snmp_community_access,
                                trap_community=self.trap_community_string,
                                sys_contact=self.system_contact,
                                sys_location=self.system_location,
                                engine_id_key=self.snmp_inpute_engine_id
                                )

        if commit:
            if self.commit(mo=mo_comm_snmp) != True:
                return False
        return True


class UcsImcSmtpProperties(UcsImcConfigObject):
    _CONFIG_NAME = "Mail Alert - SMTP Properties"

    def __init__(self, parent=None, json_content=None):
        UcsImcConfigObject.__init__(self, parent=parent)
        self.smtp_state = None
        self.port = None
        self.smtp_server_address = None
        self.minimum_severity_to_report = None
        self.smtp_recipients = []

        if self._config.load_from == "live":
            if "commMailAlert" in self._config.sdk_objects:
                if len(self._config.sdk_objects["commMailAlert"]) == 1:
                    self.snmp_state = self._config.sdk_objects["commMailAlert"][0].admin_state
                    self.port = self._config.sdk_objects["commMailAlert"][0].port
                    self.smtp_server_address = self._config.sdk_objects["commMailAlert"][0].ip_address
                    self.minimum_severity_to_report = self._config.sdk_objects["commMailAlert"][0].min_severity_level
                    for mail_recipient in self._config.sdk_objects["mailRecipient"]:
                        recipient = {}
                        recipient["email"] = mail_recipient.email
                        recipient["id"] = mail_recipient.id
                        if recipient["email"]:
                            self.smtp_recipients.append(recipient)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

                for element in self.smtp_recipients:
                    for value in ["email", "id"]:
                        if value not in element:
                            element[value] = None

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration")
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration" +
                                ", waiting for a commit")

        parent_mo = "sys/svc-ext"
        mo_smtp = CommMailAlert(parent_mo_or_dn=parent_mo,
                                admin_state=self.smtp_state,
                                port=self.port,
                                ip_address=self.smtp_server_address,
                                min_severity_level=self.minimum_severity_to_report
                                )
        for recipient in self.smtp_recipients:
            MailRecipient(parent_mo_or_dn=mo_smtp, id=recipient['id'], email=recipient['email'])

        if commit:
            if self.commit(mo=mo_smtp) != True:
                return False
        return True


class UcsImcPlatformEventFilter(UcsImcConfigObject):
    _CONFIG_NAME = "Platform Event Filter"

    def __init__(self, parent=None, json_content=None, platform_event_filter=None):
        UcsImcConfigObject.__init__(self, parent=parent)
        self.account_status = None
        self.id = None
        # self.event = None
        self.action = None

        if self._config.load_from == "live":
            if platform_event_filter is not None:
                if platform_event_filter.action not in [None, "none"]:
                    self.id = platform_event_filter.id
                    # self.event = platform_event_filter.event
                    self.action = platform_event_filter.action

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
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + self.id)

        parent_mo = "sys/rack-unit-1/event-management"
        mo_event_filter = PlatformEventFilters(parent_mo_or_dn=parent_mo, id=self.id, action=self.action)
                                               # event=self.event,

        if commit:
            if self.commit(mo=mo_event_filter) != True:
                return False

        return True


class UcsImcVirtualMedia(UcsImcConfigObject):
    _CONFIG_NAME = "Virtual Media"

    def __init__(self, parent=None, json_content=None):
        UcsImcConfigObject.__init__(self, parent=parent)
        self.vmedia_state = None
        self.virtual_media_encryption_state = None
        self.lower_power_usb_state = None
        self.mappings = []
        self.saved_mappings = []

        if self._config.load_from == "live":
            if "commVMedia" in self._config.sdk_objects:
                if len(self._config.sdk_objects["commVMedia"]) == 1:
                    self.vmedia_state = self._config.sdk_objects["commVMedia"][0].admin_state
                    self.virtual_media_encryption_state = self._config.sdk_objects["commVMedia"][0].encryption_state
                    self.lower_power_usb_state = self._config.sdk_objects["commVMedia"][0].low_power_usb_state
                    if "commSavedVMediaMap" in self._config.sdk_objects:
                        for mapping in self._config.sdk_objects["commSavedVMediaMap"]:
                            map = {}
                            map["volume"] = mapping.volume_name
                            map["mount_type"] = mapping.map
                            map["remote_share"] = mapping.remote_share
                            map["remote_file"] = mapping.remote_file
                            map["mount_options"] = mapping.mount_options
                            map["password"] = mapping.password
                            map["status"] = "unmaped"
                            self.mappings.append(map)

                    if "commVMediaMap" in self._config.sdk_objects:
                        for mapping in self._config.sdk_objects["commVMediaMap"]:
                            map = {}
                            map["volume"] = mapping.volume_name
                            map["mount_type"] = mapping.map
                            map["remote_share"] = mapping.remote_share
                            map["remote_file"] = mapping.remote_file
                            map["mount_options"] = mapping.mount_options
                            map["password"] = mapping.password
                            map["status"] = "unmaped"
                            self.mappings.append(map)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

                for element in self.mappings:
                    for value in ["volume", "mount_type", "remote_share", "remote_file", "mount_options", "password"]:
                        if value not in element:
                            element[value] = None
                for element in self.saved_mappings:
                    for value in ["volume", "mount_type", "remote_share", "remote_file", "mount_options"]:
                        if value not in element:
                            element[value] = None

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration")
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration" +
                                ", waiting for a commit")

        parent_mo = "sys/svc-ext"
        mo_comm_vmedia = CommVMedia(parent_mo_or_dn=parent_mo, admin_state=self.vmedia_state,
                                    encryption_state=self.virtual_media_encryption_state,
                                    low_power_usb_state=self.lower_power_usb_state)
        if commit:
            if self.commit(mo=mo_comm_vmedia) != True:
                return False

        if self.mappings:
            self.logger(level="warning",
                        message="Add mappings with EasyUCS is not yet possible. Please use the CIMC GUI.")
        # TODO : Not working : "Operation not supported: Update commVMediaMap object not supported.
        #  Try deleting and creating object."
        #  Even if the object does not exist. All attributes from commSavedVMediaMap are readOnly.
        # for map in self.mappings:
        #     mo_map = CommVMediaMap(parent_mo_or_dn=mo_comm_vmedia,
        #                        volume_name=map["volume"],
        #                        map=map["mount_type"],
        #                        remote_share=map["remote_share"],
        #                        remote_file=map["remote_file"],
        #                        mount_options=map["mount_options"],
        #                     password=map["password"]
        #                        )
        #     if commit:
        #         if self.commit(mo=mo_map) != True:
        #             return False
        return True


class UcsImcSerialOverLanProperties(UcsImcConfigObject):
    _CONFIG_NAME = "Serial Over LAN Properties"

    def __init__(self, parent=None, json_content=None):
        UcsImcConfigObject.__init__(self, parent=parent)
        self.serial_over_lan_state = None
        self.baud_rate = None
        self.com_port = None
        self.ssh_port = None

        if self._config.load_from == "live":
            if "solIf" in self._config.sdk_objects:
                if len(self._config.sdk_objects["solIf"]) == 1:
                    self.serial_over_lan_state = self._config.sdk_objects["solIf"][0].admin_state
                    self.baud_rate = self._config.sdk_objects["solIf"][0].speed
                    self.com_port = self._config.sdk_objects["solIf"][0].comport
                    self.ssh_port = self._config.sdk_objects["solIf"][0].ssh_port

                    if self.baud_rate == "115200":
                        self.baud_rate = "115.2 kbps"
                    elif self.baud_rate == "57600":
                        self.baud_rate = "57.6 kbps"
                    elif self.baud_rate == "38400":
                        self.baud_rate = "38.4 kbps"
                    elif self.baud_rate == "19200":
                        self.baud_rate = "19.2 kbps"
                    elif self.baud_rate == "9600":
                        self.baud_rate = "9600 bps"

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

        parent_mo = "sys/rack-unit-1"

        if self.baud_rate == "115.2 kbps":
            baud_rate = "115200"
        elif self.baud_rate == "57.6 kbps":
            baud_rate = "57600"
        elif self.baud_rate == "38.4 kbps":
            baud_rate = "38400"
        elif self.baud_rate == "19.2 kbps":
            baud_rate = "19200"
        elif self.baud_rate == "9600 bps":
            baud_rate = "9600"
        else:
            baud_rate = self.baud_rate

        mo_sol = SolIf(parent_mo_or_dn=parent_mo,
                       admin_state=self.serial_over_lan_state,
                       speed=baud_rate,
                       comport=self.com_port,
                       ssh_port=self.ssh_port)
        if commit:
            if self.commit(mo=mo_sol) != True:
                return False

        return True


class UcsImcBios(UcsImcConfigObject):
    _CONFIG_NAME = "BIOS Properties"

    def __init__(self, parent=None, json_content=None):
        UcsImcConfigObject.__init__(self, parent=parent)
        self.tpm_support = None
        self.power_on_password_support = None
        # Advanced - Processor Configuration
        self.intel_hyper_threading_technology = None
        self.execute_disable = None
        self.intel_vtd = None
        self.intel_pass_through_dma = None
        self.intel_vtd_ats_support = None
        self.hardware_prefetcher = None
        self.dcu_streamer_prefetch = None
        self.direct_cache_access_support = None
        self.enhanced_intel_speedstep_techonology = None
        self.processor_c3_report = None
        self.processor_power_state_c1_enhanced = None
        self.boot_performance_mode = None
        self.energy_performance = None
        self.extended_apic = None
        self.cpu_hwpm = None
        self.processor_cmci = None
        self.number_of_enabled_cores = None
        self.intel_vt = None
        self.intel_interrupt_remapping = None
        self.intel_vtd_coherency_support = None
        self.cpu_performance = None
        self.adjacent_cache_line_prefetcher = None
        self.dcu_ip_prefetcher = None
        self.power_technology = None
        self.intel_turbo_boost_technology = None
        self.processor_c6_report = None
        self.pstate_coordination = None
        self.energy_performance_tuning = None
        self.energy_performance = None
        self.package_c_state_limit = None
        self.workload_configuration = None
        self.cpu_autonomous_cstate = None
        # Advanced - Memory Configuration
        self.select_memory_ras = None
        self.numa = None
        self.channel_interleaving = None
        self.rank_interleaving = None
        self.patrol_scrub = None
        self.demand_scrub = None
        self.altitude = None
        # Advanced - QPI Configuration
        self.qpi_link_frequency_select = None
        self.qpi_snoop_mode = None
        # Advanced - USB Configuration
        self.legacy_usb_support = None
        self.port_60_64_emulation = None
        self.xhci_mode = None
        self.xhci_legacy_support = None
        self.all_usb_devices = None
        self.usb_port_rear = None
        self.usb_port_front = None
        self.usb_port_internal = None
        self.usb_port_kvm = None
        self.usb_port_vmedia = None
        # Advanced - PCI Configuration
        self.mmio_above_4gb = None
        self.sr_iov_support = None
        self.nvme_ssd_hot_plug_support = None
        self.vga_priority = None
        # Advanced - Serial Configuration
        self.out_of_band_management = None
        self.console_redirection = None
        self.terminal_type = None
        self.bits_per_second = None
        self.flow_control = None
        self.putty_keypad = None
        self.redirection_after_bios_post = None
        # Advanced - LOM & PCIe Slots Configuration
        self.cdn_support_for_vic = None
        self.pci_rom_clp = None
        self.pch_sata_mode = None
        self.all_onboard_lom_ports = None
        self.lom_port_1_option_rom = None
        self.lom_port_2_option_rom = None
        self.all_pcie_slots_option_rom = None
        self.pcie_slot_1_option_rom = None
        self.pcie_slot_2_option_rom = None
        self.pcie_slot_mlom_option_rom = None
        self.pcie_slot_hba_option_rom = None
        self.pcie_slot_front_pcie_1_option_rom = None
        self.pcie_slot_front_pcie_2_option_rom = None
        self.pcie_slot_mlom_link_speed = None
        self.pcie_slot_riser_1_link_speed = None
        self.pcie_slot_riser_2_link_speed = None
        self.pcie_slot_front_pcie_1_link_speed = None
        self.pcie_slot_front_pcie_2_link_speed = None
        self.pcie_slot_hba_link_speed = None
        # Server Management
        self.frb2_timer = None
        self.os_watchdog_timer = None
        self.os_watchdog_timer_timeout = None
        self.os_watchdog_timer_policy = None

        if self._config.load_from == "live":

            if self._device.platform_type == "classic":
                bios_dn = "sys/rack-unit-1/bios/bios-settings"
            elif self._device.platform_type == "modular":
                bios_dn = "sys/chassis-1/server-1/bios/bios-settings"  # FIXME: Add support for server-2 in S3260

            if "biosVfTPMSupport" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfTPMSupport"]:
                    if bios_dn in policy.dn:
                        self.tpm_support = policy.vp_tpm_support
            if "biosVfPowerOnPasswordSupport" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfPowerOnPasswordSupport"]:
                    if bios_dn in policy.dn:
                        self.power_on_password_support = policy.vp_pop_support
            # Advanced - Processor Configuration
            if "biosVfIntelHyperThreadingTech" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfIntelHyperThreadingTech"]:
                    if bios_dn in policy.dn:
                        self.intel_hyper_threading_technology = policy.vp_intel_hyper_threading_tech
            if "biosVfCoreMultiProcessing" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfCoreMultiProcessing"]:
                    if bios_dn in policy.dn:
                        self.number_of_enabled_cores = policy.vp_core_multi_processing
            if "biosVfExecuteDisableBit" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfExecuteDisableBit"]:
                    if bios_dn in policy.dn:
                        self.execute_disable = policy.vp_execute_disable_bit
            if "biosVfIntelVTForDirectedIO" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfIntelVTForDirectedIO"]:
                    if bios_dn in policy.dn:
                        self.intel_vtd = policy.vp_intel_vt_for_directed_io
                        self.intel_pass_through_dma = policy.vp_intel_vtd_pass_through_dma_support
                        self.intel_vtd_ats_support = policy.vp_intel_vtdats_support
                        self.intel_interrupt_remapping = policy.vp_intel_vtd_interrupt_remapping
                        self.intel_vtd_coherency_support = policy.vp_intel_vtd_coherency_support
            if "biosVfIntelVirtualizationTechnology" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfIntelVirtualizationTechnology"]:
                    if bios_dn in policy.dn:
                        self.intel_vt = policy.vp_intel_virtualization_technology
            if "biosVfCPUPerformance" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfCPUPerformance"]:
                    if bios_dn in policy.dn:
                        self.cpu_performance = policy.vp_cpu_performance
            if "biosVfHardwarePrefetch" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfHardwarePrefetch"]:
                    if bios_dn in policy.dn:
                        self.hardware_prefetcher = policy.vp_hardware_prefetch
            if "biosVfAdjacentCacheLinePrefetch" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfAdjacentCacheLinePrefetch"]:
                    if bios_dn in policy.dn:
                        self.adjacent_cache_line_prefetcher = policy.vp_adjacent_cache_line_prefetch
            if "biosVfDCUPrefetch" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfDCUPrefetch"]:
                    if bios_dn in policy.dn:
                        self.dcu_streamer_prefetch = policy.vp_streamer_prefetch
                        self.dcu_ip_prefetcher = policy.vp_ip_prefetch
            if "biosVfDirectCacheAccess" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfDirectCacheAccess"]:
                    if bios_dn in policy.dn:
                        self.direct_cache_access_support = policy.vp_direct_cache_access
            if "biosVfCPUPowerManagement" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfCPUPowerManagement"]:
                    if bios_dn in policy.dn:
                        self.power_technology = policy.vp_cpu_power_management
            if "biosVfEnhancedIntelSpeedStepTech" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfEnhancedIntelSpeedStepTech"]:
                    if bios_dn in policy.dn:
                        self.enhanced_intel_speedstep_techonology = policy.vp_enhanced_intel_speed_step_tech
            if "biosVfIntelTurboBoostTech" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfIntelTurboBoostTech"]:
                    if bios_dn in policy.dn:
                        self.intel_turbo_boost_technology = policy.vp_intel_turbo_boost_tech
            if "biosVfProcessorC3Report" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfProcessorC3Report"]:
                    if bios_dn in policy.dn:
                        self.processor_c3_report = policy.vp_processor_c3_report
            if "biosVfProcessorC6Report" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfProcessorC6Report"]:
                    if bios_dn in policy.dn:
                        self.processor_c6_report = policy.vp_processor_c6_report
            if "biosVfProcessorC1E" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfProcessorC1E"]:
                    if bios_dn in policy.dn:
                        self.processor_power_state_c1_enhanced = policy.vp_processor_c1_e
            if "biosVfPStateCoordType" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfPStateCoordType"]:
                    if bios_dn in policy.dn:
                        self.pstate_coordination = policy.vp_p_state_coord_type
            if "biosVfBootPerformanceMode" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfBootPerformanceMode"]:
                    if bios_dn in policy.dn:
                        self.boot_performance_mode = policy.vp_boot_performance_mode
            if "biosVfPwrPerfTuning" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfPwrPerfTuning"]:
                    if bios_dn in policy.dn:
                        self.energy_performance_tuning = policy.vp_pwr_perf_tuning
            if "biosVfCPUEnergyPerformance" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfCPUEnergyPerformance"]:
                    if bios_dn in policy.dn:
                        self.energy_performance = policy.vp_cpu_energy_performance
            if "biosVfPackageCStateLimit" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfPackageCStateLimit"]:
                    if bios_dn in policy.dn:
                        self.package_c_state_limit = policy.vp_package_c_state_limit
            if "biosVfExtendedAPIC" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfExtendedAPIC"]:
                    if bios_dn in policy.dn:
                        self.extended_apic = policy.vp_extended_apic
            if "biosVfWorkLoadConfig" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfWorkLoadConfig"]:
                    if bios_dn in policy.dn:
                        self.workload_configuration = policy.vp_work_load_config
            if "biosVfHWPMEnable" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfHWPMEnable"]:
                    if bios_dn in policy.dn:
                        self.cpu_hwpm = policy.vp_hwpm_enable
            if "biosVfAutonumousCstateEnable" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfAutonumousCstateEnable"]:
                    if bios_dn in policy.dn:
                        self.cpu_autonomous_cstate = policy.vp_autonumous_cstate_enable
            if "biosVfCmciEnable" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfCmciEnable"]:
                    if bios_dn in policy.dn:
                        self.processor_cmci = policy.vp_cmci_enable
            # Advanced - Memory Configuration
            if "biosVfSelectMemoryRASConfiguration" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfSelectMemoryRASConfiguration"]:
                    if bios_dn in policy.dn:
                        self.select_memory_ras = policy.vp_select_memory_ras_configuration
            if "biosVfNUMAOptimized" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfNUMAOptimized"]:
                    if bios_dn in policy.dn:
                        self.numa = policy.vp_numa_optimized
            if "biosVfMemoryInterleave" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfMemoryInterleave"]:
                    if bios_dn in policy.dn:
                        self.channel_interleaving = policy.vp_channel_inter_leave
                        self.rank_interleaving = policy.vp_rank_inter_leave
            if "biosVfPatrolScrub" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfPatrolScrub"]:
                    if bios_dn in policy.dn:
                        self.patrol_scrub = policy.vp_patrol_scrub
            if "biosVfDemandScrub" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfDemandScrub"]:
                    if bios_dn in policy.dn:
                        self.demand_scrub = policy.vp_demand_scrub
            if "biosVfAltitude" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfAltitude"]:
                    if bios_dn in policy.dn:
                        self.altitude = policy.vp_altitude
            # Advanced - QPI Configuration
            if "biosVfQPIConfig" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfQPIConfig"]:
                    if bios_dn in policy.dn:
                        self.qpi_link_frequency_select = policy.vp_qpi_link_frequency
            if "biosVfQpiSnoopMode" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfQpiSnoopMode"]:
                    if bios_dn in policy.dn:
                        self.qpi_snoop_mode = policy.vp_qpi_snoop_mode
            # Advanced - USB Configuration
            if "biosVfLegacyUSBSupport" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfLegacyUSBSupport"]:
                    if bios_dn in policy.dn:
                        self.legacy_usb_support = policy.vp_legacy_usb_support
            if "biosVfUSBEmulation" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfUSBEmulation"]:
                    if bios_dn in policy.dn:
                        self.port_60_64_emulation = policy.vp_usb_emul6064
            if "biosVfPchUsb30Mode" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfPchUsb30Mode"]:
                    if bios_dn in policy.dn:
                        self.xhci_mode = policy.vp_pch_usb30_mode
            if "biosVfUsbXhciSupport" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfUsbXhciSupport"]:
                    if bios_dn in policy.dn:
                        self.xhci_legacy_support = policy.vp_usb_xhci_support
            if "biosVfUSBPortsConfig" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfUSBPortsConfig"]:
                    if bios_dn in policy.dn:
                        self.all_usb_devices = policy.vp_all_usb_devices
                        self.usb_port_front = policy.vp_usb_port_front
                        self.usb_port_rear = policy.vp_usb_port_rear
                        self.usb_port_internal = policy.vp_usb_port_internal
                        self.usb_port_kvm = policy.vp_usb_port_kvm
                        self.usb_port_vmedia = policy.vp_usb_port_v_media
            # Advanced - PCI Configuration
            if "biosVfMemoryMappedIOAbove4GB" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfMemoryMappedIOAbove4GB"]:
                    if bios_dn in policy.dn:
                        self.mmio_above_4gb = policy.vp_memory_mapped_io_above4_gb
            if "biosVfSrIov" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfSrIov"]:
                    if bios_dn in policy.dn:
                        self.sr_iov_support = policy.vp_sr_iov
            if "biosVfPCIeSSDHotPlugSupport" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfPCIeSSDHotPlugSupport"]:
                    if bios_dn in policy.dn:
                        self.nvme_ssd_hot_plug_support = policy.vp_pc_ie_ssd_hot_plug_support
            if "biosVfVgaPriority" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfVgaPriority"]:
                    if bios_dn in policy.dn:
                        self.vga_priority = policy.vp_vga_priority
            # Advanced - Serial Configuration
            if "biosVfOutOfBandMgmtPort" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfOutOfBandMgmtPort"]:
                    if bios_dn in policy.dn:
                        self.out_of_band_management = policy.vp_out_of_band_mgmt_port
            if "biosVfConsoleRedirection" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfConsoleRedirection"]:
                    if bios_dn in policy.dn:
                        self.console_redirection = policy.vp_console_redirection
                        self.terminal_type = policy.vp_terminal_type
                        self.bits_per_second = policy.vp_baud_rate
                        self.flow_control = policy.vp_flow_control
                        self.putty_keypad = policy.vp_putty_key_pad
                        self.redirection_after_bios_post = policy.vp_redirection_after_post
            # Advanced - LOM & PCIe Slots Configuration
            if "biosVfCDNEnable" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfCDNEnable"]:
                    if bios_dn in policy.dn:
                        self.cdn_support_for_vic = policy.vp_cdn_enable
            if "biosVfPciRomClp" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfPciRomClp"]:
                    if bios_dn in policy.dn:
                        self.pci_rom_clp = policy.vp_pci_rom_clp
            if "biosVfSataModeSelect" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfSataModeSelect"]:
                    if bios_dn in policy.dn:
                        self.pch_sata_mode = policy.vp_sata_mode_select
            if "biosVfLOMPortOptionROM" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfLOMPortOptionROM"]:
                    if bios_dn in policy.dn:
                        self.all_onboard_lom_ports = policy.vp_lom_ports_all_state
                        self.lom_port_1_option_rom = policy.vp_lom_port0_state
                        self.lom_port_2_option_rom = policy.vp_lom_port1_state
            if "biosVfPCIOptionROMs" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfPCIOptionROMs"]:
                    if bios_dn in policy.dn:
                        self.all_pcie_slots_option_rom = policy.vp_pci_option_ro_ms
            if "biosVfPCISlotOptionROMEnable" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfPCISlotOptionROMEnable"]:
                    if bios_dn in policy.dn:
                        self.pcie_slot_1_option_rom = policy.vp_slot1_state
                        self.pcie_slot_2_option_rom = policy.vp_slot2_state
                        self.pcie_slot_mlom_option_rom = policy.vp_slot_mlom_state
                        self.pcie_slot_hba_option_rom = policy.vp_slot_hba_state
                        self.pcie_slot_front_pcie_1_option_rom = policy.vp_slot_n1_state
                        self.pcie_slot_front_pcie_2_option_rom = policy.vp_slot_n2_state
                        self.pcie_slot_mlom_link_speed = policy.vp_slot_mlom_link_speed
                        self.pcie_slot_riser_1_link_speed = policy.vp_slot_riser1_link_speed
                        self.pcie_slot_riser_2_link_speed = policy.vp_slot_riser2_link_speed
                        self.pcie_slot_front_pcie_1_link_speed = policy.vp_slot_front_slot5_link_speed
                        self.pcie_slot_front_pcie_2_link_speed = policy.vp_slot_front_slot6_link_speed
                        self.pcie_slot_hba_link_speed = policy.vp_slot_hba_link_speed
            # Server Management
            if "biosVfFRB2Enable" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfFRB2Enable"]:
                    if bios_dn in policy.dn:
                        self.frb2_timer = policy.vp_fr_b2_enable
            if "biosVfOSBootWatchdogTimer" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfOSBootWatchdogTimer"]:
                    if bios_dn in policy.dn:
                        self.os_watchdog_timer = policy.vp_os_boot_watchdog_timer
            if "biosVfOSBootWatchdogTimerPolicy" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfOSBootWatchdogTimerPolicy"]:
                    if bios_dn in policy.dn:
                        self.os_watchdog_timer_policy = policy.vp_os_boot_watchdog_timer_policy
            if "biosVfOSBootWatchdogTimerTimeout" in self._config.sdk_objects:
                for policy in self._config.sdk_objects["biosVfOSBootWatchdogTimerTimeout"]:
                    if bios_dn in policy.dn:
                        self.os_watchdog_timer_timeout = policy.vp_os_boot_watchdog_timer_timeout

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

        if self._device.platform_type == "classic":
            parent_mo = "sys/rack-unit-1/bios"
        elif self._device.platform_type == "modular":
            parent_mo = "sys/chassis-1/server-1/bios"  # FIXME: Add support for setting BIOS params for server-2
        mo_bios_settings = BiosSettings(parent_mo_or_dn=parent_mo)

        BiosVfTPMSupport(parent_mo_or_dn=mo_bios_settings, vp_tpm_support=self.tpm_support)
        BiosVfPowerOnPasswordSupport(parent_mo_or_dn=mo_bios_settings, vp_pop_support=self.power_on_password_support)
        BiosVfIntelHyperThreadingTech(parent_mo_or_dn=mo_bios_settings,
                                      vp_intel_hyper_threading_tech=self.intel_hyper_threading_technology)
        BiosVfCoreMultiProcessing(parent_mo_or_dn=mo_bios_settings,
                                  vp_core_multi_processing=self.number_of_enabled_cores)
        BiosVfExecuteDisableBit(parent_mo_or_dn=mo_bios_settings, vp_execute_disable_bit=self.execute_disable)
        BiosVfIntelVTForDirectedIO(parent_mo_or_dn=mo_bios_settings, vp_intel_vt_for_directed_io=self.intel_vtd,
                                   vp_intel_vtd_pass_through_dma_support=self.intel_pass_through_dma,
                                   vp_intel_vtdats_support=self.intel_vtd_ats_support,
                                   vp_intel_vtd_interrupt_remapping=self.intel_interrupt_remapping,
                                   vp_intel_vtd_coherency_support=self.intel_vtd_coherency_support)
        BiosVfIntelVirtualizationTechnology(parent_mo_or_dn=mo_bios_settings,
                                            vp_intel_virtualization_technology=self.intel_vt)
        BiosVfCPUPerformance(parent_mo_or_dn=mo_bios_settings, vp_cpu_performance=self.cpu_performance)
        BiosVfHardwarePrefetch(parent_mo_or_dn=mo_bios_settings, vp_hardware_prefetch=self.hardware_prefetcher)
        BiosVfAdjacentCacheLinePrefetch(parent_mo_or_dn=mo_bios_settings,
                                        vp_adjacent_cache_line_prefetch=self.adjacent_cache_line_prefetcher)
        BiosVfDCUPrefetch(parent_mo_or_dn=mo_bios_settings, vp_streamer_prefetch=self.dcu_streamer_prefetch,
                          vp_ip_prefetch=self.dcu_ip_prefetcher)
        BiosVfDirectCacheAccess(parent_mo_or_dn=mo_bios_settings,
                                vp_direct_cache_access=self.direct_cache_access_support)
        BiosVfCPUPowerManagement(parent_mo_or_dn=mo_bios_settings, vp_cpu_power_management=self.power_technology)
        BiosVfEnhancedIntelSpeedStepTech(parent_mo_or_dn=mo_bios_settings,
                                         vp_enhanced_intel_speed_step_tech=self.enhanced_intel_speedstep_techonology)
        BiosVfIntelTurboBoostTech(parent_mo_or_dn=mo_bios_settings,
                                  vp_intel_turbo_boost_tech=self.intel_turbo_boost_technology)
        BiosVfProcessorC3Report(parent_mo_or_dn=mo_bios_settings, vp_processor_c3_report=self.processor_c3_report)
        BiosVfProcessorC6Report(parent_mo_or_dn=mo_bios_settings, vp_processor_c6_report=self.processor_c6_report)
        BiosVfProcessorC1E(parent_mo_or_dn=mo_bios_settings, vp_processor_c1_e=self.processor_power_state_c1_enhanced)
        BiosVfPStateCoordType(parent_mo_or_dn=mo_bios_settings, vp_p_state_coord_type=self.pstate_coordination)
        BiosVfBootPerformanceMode(parent_mo_or_dn=mo_bios_settings, vp_boot_performance_mode=self.boot_performance_mode)
        BiosVfPwrPerfTuning(parent_mo_or_dn=mo_bios_settings, vp_pwr_perf_tuning=self.energy_performance_tuning)
        BiosVfCPUEnergyPerformance(parent_mo_or_dn=mo_bios_settings,
                                   vp_cpu_energy_performance=self.energy_performance)
        BiosVfPackageCStateLimit(parent_mo_or_dn=mo_bios_settings, vp_package_c_state_limit=self.package_c_state_limit)
        BiosVfExtendedAPIC(parent_mo_or_dn=mo_bios_settings, vp_extended_apic=self.extended_apic)
        BiosVfWorkLoadConfig(parent_mo_or_dn=mo_bios_settings, vp_work_load_config=self.workload_configuration)
        BiosVfHWPMEnable(parent_mo_or_dn=mo_bios_settings, vp_hwpm_enable=self.cpu_hwpm)
        BiosVfAutonumousCstateEnable(parent_mo_or_dn=mo_bios_settings,
                                     vp_autonumous_cstate_enable=self.cpu_autonomous_cstate)
        BiosVfCmciEnable(parent_mo_or_dn=mo_bios_settings, vp_cmci_enable=self.processor_cmci)
        BiosVfSelectMemoryRASConfiguration(parent_mo_or_dn=mo_bios_settings,
                                           vp_select_memory_ras_configuration=self.select_memory_ras)
        BiosVfNUMAOptimized(parent_mo_or_dn=mo_bios_settings, vp_numa_optimized=self.numa)
        BiosVfMemoryInterleave(parent_mo_or_dn=mo_bios_settings, vp_channel_inter_leave=self.channel_interleaving,
                               vp_rank_inter_leave=self.rank_interleaving)
        BiosVfPatrolScrub(parent_mo_or_dn=mo_bios_settings, vp_patrol_scrub=self.patrol_scrub)
        BiosVfDemandScrub(parent_mo_or_dn=mo_bios_settings, vp_demand_scrub=self.demand_scrub)
        BiosVfAltitude(parent_mo_or_dn=mo_bios_settings, vp_altitude=self.altitude)
        BiosVfQPIConfig(parent_mo_or_dn=mo_bios_settings, vp_qpi_link_frequency=self.qpi_link_frequency_select)
        BiosVfQpiSnoopMode(parent_mo_or_dn=mo_bios_settings, vp_qpi_snoop_mode=self.qpi_snoop_mode)
        BiosVfLegacyUSBSupport(parent_mo_or_dn=mo_bios_settings, vp_legacy_usb_support=self.legacy_usb_support)
        BiosVfUSBEmulation(parent_mo_or_dn=mo_bios_settings, vp_usb_emul6064=self.port_60_64_emulation)
        BiosVfPchUsb30Mode(parent_mo_or_dn=mo_bios_settings, vp_pch_usb30_mode=self.xhci_mode)
        BiosVfUsbXhciSupport(parent_mo_or_dn=mo_bios_settings, vp_usb_xhci_support=self.xhci_legacy_support)
        BiosVfUSBPortsConfig(parent_mo_or_dn=mo_bios_settings, vp_all_usb_devices=self.all_usb_devices,
                             vp_usb_port_front=self.usb_port_front, vp_usb_port_rear=self.usb_port_rear,
                             vp_usb_port_internal=self.usb_port_internal, vp_usb_port_kvm=self.usb_port_kvm,
                             vp_usb_port_v_media=self.usb_port_vmedia)
        BiosVfMemoryMappedIOAbove4GB(parent_mo_or_dn=mo_bios_settings,
                                     vp_memory_mapped_io_above4_gb=self.mmio_above_4gb)
        BiosVfSrIov(parent_mo_or_dn=mo_bios_settings, vp_sr_iov=self.sr_iov_support)
        BiosVfPCIeSSDHotPlugSupport(parent_mo_or_dn=mo_bios_settings,
                                    vp_pc_ie_ssd_hot_plug_support=self.nvme_ssd_hot_plug_support)
        BiosVfVgaPriority(parent_mo_or_dn=mo_bios_settings, vp_vga_priority=self.vga_priority)
        BiosVfOutOfBandMgmtPort(parent_mo_or_dn=mo_bios_settings, vp_out_of_band_mgmt_port=self.out_of_band_management)
        BiosVfConsoleRedirection(parent_mo_or_dn=mo_bios_settings, vp_console_redirection=self.console_redirection,
                                 vp_terminal_type=self.terminal_type, vp_baud_rate=self.bits_per_second,
                                 vp_flow_control=self.flow_control, vp_putty_key_pad=self.putty_keypad,
                                 vp_redirection_after_post=self.redirection_after_bios_post)
        BiosVfCDNEnable(parent_mo_or_dn=mo_bios_settings, vp_cdn_enable=self.cdn_support_for_vic)
        BiosVfPciRomClp(parent_mo_or_dn=mo_bios_settings, vp_pci_rom_clp=self.pci_rom_clp)
        BiosVfSataModeSelect(parent_mo_or_dn=mo_bios_settings, vp_sata_mode_select=self.pch_sata_mode)
        BiosVfLOMPortOptionROM(parent_mo_or_dn=mo_bios_settings, vp_lom_ports_all_state=self.all_onboard_lom_ports,
                               vp_lom_port0_state=self.lom_port_1_option_rom,
                               vp_lom_port1_state=self.lom_port_2_option_rom)
        BiosVfPCIOptionROMs(parent_mo_or_dn=mo_bios_settings, vp_pci_option_ro_ms=self.all_pcie_slots_option_rom)
        BiosVfPCISlotOptionROMEnable(parent_mo_or_dn=mo_bios_settings, vp_slot1_state=self.pcie_slot_1_option_rom,
                                     vp_slot2_state=self.pcie_slot_2_option_rom,
                                     vp_slot_mlom_state=self.pcie_slot_mlom_option_rom,
                                     vp_slot_hba_state=self.pcie_slot_hba_option_rom,
                                     vp_slot_n1_state=self.pcie_slot_front_pcie_1_option_rom,
                                     vp_slot_n2_state=self.pcie_slot_front_pcie_2_option_rom,
                                     vp_slot_mlom_link_speed=self.pcie_slot_mlom_link_speed,
                                     vp_slot_riser1_link_speed=self.pcie_slot_riser_1_link_speed,
                                     vp_slot_riser2_link_speed=self.pcie_slot_riser_2_link_speed,
                                     vp_slot_front_slot5_link_speed=self.pcie_slot_front_pcie_1_link_speed,
                                     vp_slot_front_slot6_link_speed=self.pcie_slot_front_pcie_2_link_speed,
                                     vp_slot_hba_link_speed=self.pcie_slot_hba_link_speed)
        BiosVfFRB2Enable(parent_mo_or_dn=mo_bios_settings, vp_fr_b2_enable=self.frb2_timer)
        BiosVfOSBootWatchdogTimer(parent_mo_or_dn=mo_bios_settings, vp_os_boot_watchdog_timer=self.os_watchdog_timer)
        BiosVfOSBootWatchdogTimerPolicy(parent_mo_or_dn=mo_bios_settings,
                                        vp_os_boot_watchdog_timer_policy=self.os_watchdog_timer_policy)
        BiosVfOSBootWatchdogTimerTimeout(parent_mo_or_dn=mo_bios_settings,
                                         vp_os_boot_watchdog_timer_timeout=self.os_watchdog_timer_timeout)

        if commit:
            if self.commit(mo=mo_bios_settings) != True:
                return False

        return True


class UcsImcLdap(UcsImcConfigObject):
    _CONFIG_NAME = "LDAP Properties"

    def __init__(self, parent=None, json_content=None):
        UcsImcConfigObject.__init__(self, parent=parent)
        self.ldap_state = None
        self.base_dn = None
        self.domain = None
        self.encryption_state = None
        self.binding_certificate_state = None
        self.timeout = None
        self.user_search_precedence = None
        self.binding_method = None
        self.binding_dn = None
        self.binding_password = None
        self.search_filter_attribute = None
        self.search_group_attribute = None
        self.search_attribute = None
        self.nested_group_search_depth = None
        # self.ldap_servers = []
        self.ldap_server_1 = None
        self.ldap_server_port_1 = None
        self.ldap_server_2 = None
        self.ldap_server_port_2 = None
        self.ldap_server_3 = None
        self.ldap_server_port_3 = None
        self.ldap_server_4 = None
        self.ldap_server_port_4 = None
        self.ldap_server_5 = None
        self.ldap_server_port_5 = None
        self.ldap_server_6 = None
        self.ldap_server_port_6 = None
        self.dns_source = None
        self.dns_domain_to_search = None
        self.dns_forest_to_search = None
        self.ldap_group_authorization = None
        self.ldap_groups = []
        self.use_dns_to_configure_ldap_servers = None

        if self._config.load_from == "live":
            if "aaaLdap" in self._config.sdk_objects:
                if len(self._config.sdk_objects["aaaLdap"]) == 1:
                    self.ldap_state = self._config.sdk_objects["aaaLdap"][0].admin_state
                    self.base_dn = self._config.sdk_objects["aaaLdap"][0].basedn
                    self.domain = self._config.sdk_objects["aaaLdap"][0].domain
                    self.encryption_state = self._config.sdk_objects["aaaLdap"][0].encryption
                    if "ldapCACertificateManagement" in self._config.sdk_objects:
                        if len(self._config.sdk_objects["ldapCACertificateManagement"]) == 1:
                            self.binding_certificate_state = \
                                self._config.sdk_objects["ldapCACertificateManagement"][0].binding_certificate
                    self.timeout = self._config.sdk_objects["aaaLdap"][0].timeout
                    self.user_search_precedence = self._config.sdk_objects["aaaLdap"][0].user_search_precedence
                    self.binding_method = self._config.sdk_objects["aaaLdap"][0].bind_method
                    self.binding_dn = self._config.sdk_objects["aaaLdap"][0].bind_dn
                    self.binding_password = self._config.sdk_objects["aaaLdap"][0].password
                    self.search_filter_attribute = self._config.sdk_objects["aaaLdap"][0].filter
                    self.search_group_attribute = self._config.sdk_objects["aaaLdap"][0].group_attribute
                    self.search_attribute = self._config.sdk_objects["aaaLdap"][0].attribute
                    self.nested_group_search_depth = self._config.sdk_objects["aaaLdap"][0].group_nested_search
                    self.ldap_server_1 = self._config.sdk_objects["aaaLdap"][0].ldap_server1
                    self.ldap_server_2 = self._config.sdk_objects["aaaLdap"][0].ldap_server2
                    self.ldap_server_3 = self._config.sdk_objects["aaaLdap"][0].ldap_server3
                    self.ldap_server_4 = self._config.sdk_objects["aaaLdap"][0].ldap_server4
                    self.ldap_server_5 = self._config.sdk_objects["aaaLdap"][0].ldap_server5
                    self.ldap_server_6 = self._config.sdk_objects["aaaLdap"][0].ldap_server6
                    self.ldap_server_port_1 = self._config.sdk_objects["aaaLdap"][0].ldap_server_port1
                    self.ldap_server_port_2 = self._config.sdk_objects["aaaLdap"][0].ldap_server_port2
                    self.ldap_server_port_3 = self._config.sdk_objects["aaaLdap"][0].ldap_server_port3
                    self.ldap_server_port_4 = self._config.sdk_objects["aaaLdap"][0].ldap_server_port4
                    self.ldap_server_port_5 = self._config.sdk_objects["aaaLdap"][0].ldap_server_port5
                    self.ldap_server_port_6 = self._config.sdk_objects["aaaLdap"][0].ldap_server_port6
                    # for i in range(1,7):
                    #     server = {}
                    #     server["ldap_server_"+str(i)] = \
                    #         getattr(self._config.sdk_objects["aaaLdap"][0],"ldap_server"+str(i))
                    #     server["ldap_server_port_"+str(i)] = \
                    #         getattr(self._config.sdk_objects["aaaLdap"][0],"ldap_server_port"+str(i))
                    #     self.ldap_servers.append(server)
                    self.dns_source = self._config.sdk_objects["aaaLdap"][0].dns_domain_source
                    self.dns_domain_to_search = self._config.sdk_objects["aaaLdap"][0].dns_search_domain
                    self.dns_forest_to_search = self._config.sdk_objects["aaaLdap"][0].dns_search_forest
                    self.ldap_group_authorization = self._config.sdk_objects["aaaLdap"][0].group_auth
                    self.use_dns_to_configure_ldap_servers = \
                        self._config.sdk_objects["aaaLdap"][0].locate_directory_using_dns
                    if "aaaLdapRoleGroup" in self._config.sdk_objects:
                        for group in self._config.sdk_objects["aaaLdapRoleGroup"]:
                            ldap_group = {}
                            ldap_group["index"] = group.id
                            ldap_group["group_name"] = group.name
                            ldap_group["group_domain"] = group.domain
                            ldap_group["role"] = group.role
                            if group.name:
                                self.ldap_groups.append(ldap_group)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

                for element in self.ldap_groups:
                    for value in ["index", "group_name", "group_domain", "role"]:
                        if value not in element:
                            element[value] = None

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration")
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration" +
                                ", waiting for a commit")

        parent_mo = "sys"

        if self.user_search_precedence in ["LDAP User Database", "ldap user database", "ldap_user_database"]:
            user_search_precedence = "ldap-user-db"
        elif self.user_search_precedence in ["Local User Database", "local user database", "local_user_database"]:
            user_search_precedence = "local-user-db"
        else:
            user_search_precedence = self.user_search_precedence

        mo_aaa_ldap = AaaLdap(parent_mo_or_dn=parent_mo, admin_state=self.ldap_state, basedn=self.base_dn,
                              domain=self.domain, encryption=self.encryption_state, timeout=self.timeout,
                              user_search_precedence=user_search_precedence, bind_method=self.binding_method,
                              bind_dn=self.binding_dn, password=self.binding_password,
                              filter=self.search_filter_attribute, group_attribute=self.search_group_attribute,
                              attribute=self.search_attribute, group_nested_search=self.nested_group_search_depth,
                              dns_domain_source=self.dns_source, dns_search_domain=self.dns_domain_to_search,
                              dns_search_forest=self.dns_forest_to_search, group_auth=self.ldap_group_authorization,
                              ldap_server1=self.ldap_server_1, ldap_server_port1=self.ldap_server_port_1,
                              ldap_server2=self.ldap_server_2, ldap_server_port2=self.ldap_server_port_2,
                              ldap_server3=self.ldap_server_3, ldap_server_port3=self.ldap_server_port_3,
                              ldap_server4=self.ldap_server_4, ldap_server_port4=self.ldap_server_port_4,
                              ldap_server5=self.ldap_server_5, ldap_server_port5=self.ldap_server_port_5,
                              ldap_server6=self.ldap_server_6, ldap_server_port6=self.ldap_server_port_6,
                              locate_directory_using_dns=self.use_dns_to_configure_ldap_servers)

        if commit:
            if self.commit(mo=mo_aaa_ldap) != True:
                return False

        for group in self.ldap_groups:
            role = group["role"]
            if not role:
                # Default role
                role = "read-only"
            AaaLdapRoleGroup(parent_mo_or_dn=mo_aaa_ldap, id=group["index"], name=group["group_name"],
                             domain=group["group_domain"], role=role)
            if commit:
                if self.commit(mo=mo_aaa_ldap) != True:
                    continue

        mo_certif = LdapCACertificateManagement(parent_mo_or_dn="sys/ldap-ext",
                                                binding_certificate=self.binding_certificate_state)

        if commit:
            if self.commit(mo=mo_certif) != True:
                return False

        return True


class UcsImcBootOrder(UcsImcConfigObject):
    _CONFIG_NAME = "Boot Order"

    def __init__(self, parent=None, json_content=None):
        UcsImcConfigObject.__init__(self, parent=parent)
        self.uefi_secure_boot = None  # TODO: Not found
        self.configured_boot_mode = None
        self.configured_one_time_boot_device = None
        self.basic_boot_devices = []
        self.advanced_boot_devices = []

        if self._config.load_from == "live":
            if "lsbootDevPrecision" in self._config.sdk_objects:
                if len(self._config.sdk_objects["lsbootDevPrecision"]) == 1:
                    self.configured_boot_mode = self._config.sdk_objects["lsbootDevPrecision"][0].configured_boot_mode
                    if "oneTimePrecisionBootDevice" in self._config.sdk_objects:
                        if len(self._config.sdk_objects["oneTimePrecisionBootDevice"]) == 1:
                            if self._config.sdk_objects["oneTimePrecisionBootDevice"][0].device:
                                self.configured_one_time_boot_device = \
                                    self._config.sdk_objects["oneTimePrecisionBootDevice"][0].device

                    if "lsbootVirtualMedia" and "lsbootLan" and "lsbootStorage" and "lsbootEfi" \
                            in self._config.sdk_objects:
                        if self._config.sdk_objects["lsbootVirtualMedia"] or self._config.sdk_objects["lsbootLan"] \
                                or self._config.sdk_objects["lsbootStorage"] or self._config.sdk_objects["lsbootEfi"]:
                            for boot_device in self._config.sdk_objects["lsbootVirtualMedia"]:
                                device = {}
                                if boot_device.access == "read-only":
                                    device["type"] = boot_device.type + "-cdrom"
                                elif boot_device.access == "read-write":
                                    device["type"] = boot_device.type + "-fdd"
                                device["order"] = boot_device.order
                                self.basic_boot_devices.append(device)
                            for boot_device in self._config.sdk_objects["lsbootLan"]:
                                device = {}
                                device["type"] = boot_device.type
                                device["order"] = boot_device.order
                                self.basic_boot_devices.append(device)
                            for boot_device in self._config.sdk_objects["lsbootStorage"]:
                                device = {}
                                device["type"] = boot_device.type
                                device["order"] = boot_device.order
                                self.basic_boot_devices.append(device)
                            for boot_device in self._config.sdk_objects["lsbootEfi"]:
                                device = {}
                                device["type"] = boot_device.type
                                device["order"] = boot_device.order
                                self.basic_boot_devices.append(device)

                    if "lsbootVMedia" and "lsbootPxe" and "lsbootHdd" and "lsbootSd" and "lsbootUsb" and "lsbootSan" \
                            and "lsbootIscsi" and "lsbootPchStorage" and "lsbootUefiShell" and "lsbootNVMe" \
                            in self._config.sdk_objects:
                        if self._config.sdk_objects["lsbootVMedia"] or self._config.sdk_objects["lsbootPxe"] \
                                or self._config.sdk_objects["lsbootHdd"] or self._config.sdk_objects["lsbootSd"] \
                                or self._config.sdk_objects["lsbootUsb"] or self._config.sdk_objects["lsbootSan"] \
                                or self._config.sdk_objects["lsbootIscsi"] \
                                or self._config.sdk_objects["lsbootPchStorage"] \
                                or self._config.sdk_objects["lsbootUefiShell"] \
                                or self._config.sdk_objects["lsbootNVMe"]:
                            for boot_device in self._config.sdk_objects["lsbootVMedia"]:
                                device = {}
                                device["type"] = boot_device.type
                                device["name"] = boot_device.name
                                device["subtype"] = boot_device.subtype
                                device["state"] = boot_device.state
                                device["order"] = boot_device.order
                                self.advanced_boot_devices.append(device)
                            for boot_device in self._config.sdk_objects["lsbootPxe"]:
                                device = {}
                                device["type"] = boot_device.type
                                device["name"] = boot_device.name
                                device["slot"] = boot_device.slot
                                device["port"] = boot_device.port
                                device["state"] = boot_device.state
                                device["order"] = boot_device.order
                                self.advanced_boot_devices.append(device)
                            for boot_device in self._config.sdk_objects["lsbootHdd"]:
                                device = {}
                                device["type"] = boot_device.type
                                device["name"] = boot_device.name
                                device["slot"] = boot_device.slot
                                device["state"] = boot_device.state
                                device["order"] = boot_device.order
                                self.advanced_boot_devices.append(device)
                            for boot_device in self._config.sdk_objects["lsbootSd"]:
                                device = {}
                                device["type"] = boot_device.type
                                device["name"] = boot_device.name
                                device["lun"] = boot_device.lun
                                device["state"] = boot_device.state
                                device["order"] = boot_device.order
                                self.advanced_boot_devices.append(device)
                            for boot_device in self._config.sdk_objects["lsbootUsb"]:
                                device = {}
                                device["type"] = boot_device.type
                                device["name"] = boot_device.name
                                device["state"] = boot_device.state
                                device["order"] = boot_device.order
                                self.advanced_boot_devices.append(device)
                            for boot_device in self._config.sdk_objects["lsbootSan"]:
                                device = {}
                                device["type"] = boot_device.type
                                device["name"] = boot_device.name
                                device["lun"] = boot_device.lun
                                device["slot"] = boot_device.slot
                                device["state"] = boot_device.state
                                device["order"] = boot_device.order
                                self.advanced_boot_devices.append(device)
                            for boot_device in self._config.sdk_objects["lsbootIscsi"]:
                                device = {}
                                device["type"] = boot_device.type
                                device["name"] = boot_device.name
                                device["slot"] = boot_device.slot
                                device["port"] = boot_device.port
                                device["state"] = boot_device.state
                                device["order"] = boot_device.order
                                self.advanced_boot_devices.append(device)
                            for boot_device in self._config.sdk_objects["lsbootPchStorage"]:
                                device = {}
                                device["type"] = boot_device.type
                                device["name"] = boot_device.name
                                device["state"] = boot_device.state
                                device["order"] = boot_device.order
                                self.advanced_boot_devices.append(device)
                            for boot_device in self._config.sdk_objects["lsbootUefiShell"]:
                                device = {}
                                device["type"] = boot_device.type
                                device["name"] = boot_device.name
                                device["state"] = boot_device.state
                                device["order"] = boot_device.order
                                self.advanced_boot_devices.append(device)
                            for boot_device in self._config.sdk_objects["lsbootNVMe"]:
                                device = {}
                                device["type"] = boot_device.type
                                device["name"] = boot_device.name
                                device["state"] = boot_device.state
                                device["order"] = boot_device.order
                                self.advanced_boot_devices.append(device)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

                for element in self.advanced_boot_devices:
                    for value in ["type", "name", "state", "order", "lun", "slot", "port"]:
                        if value not in element:
                            element[value] = None
                for element in self.basic_boot_devices:
                    for value in ["type", "name", "order"]:
                        if value not in element:
                            element[value] = None

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration")
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration" +
                                ", waiting for a commit")

        if self._device.platform_type == "classic":
            parent_mo = "sys/rack-unit-1"
        elif self._device.platform_type == "modular":
            parent_mo = "sys/chassis-1/server-1"  # FIXME: add support for server-2 for S3260

        configured_boot_mode = self.configured_boot_mode
        if self.configured_boot_mode == "None":
            configured_boot_mode = "Legacy"
        mo_boot_precision = LsbootDevPrecision(parent_mo_or_dn=parent_mo, configured_boot_mode=configured_boot_mode)

        if self.configured_one_time_boot_device:
            OneTimePrecisionBootDevice(parent_mo_or_dn=parent_mo, device=self.configured_one_time_boot_device)

        if self.basic_boot_devices:
            mo_boot_def = LsbootDef(parent_mo_or_dn=parent_mo)
            self.basic_boot_devices = sorted(self.basic_boot_devices, key=lambda device: int(device["order"]))
            for device in self.basic_boot_devices:
                if device["type"] == "virtual-media-cdrom":
                    LsbootVirtualMedia(parent_mo_or_dn=mo_boot_def, access="read-only", order=device["order"])
                if device["type"] == "virtual-media-fdd":
                    LsbootVirtualMedia(parent_mo_or_dn=mo_boot_def, access="read-write", order=device["order"])
                if device["type"] == "lan":
                    LsbootLan(parent_mo_or_dn=mo_boot_def, order=device["order"])
                if device["type"] == "storage":
                    LsbootStorage(parent_mo_or_dn=mo_boot_def, order=device["order"])
                if device["type"] == "efi":
                    LsbootEfi(parent_mo_or_dn=mo_boot_def, order=device["order"])
            if commit:
                if self.commit(mo=mo_boot_def) != True:
                    return False

        if self.advanced_boot_devices:
            self.advanced_boot_devices = sorted(self.advanced_boot_devices, key=lambda device: int(device["order"]))
            for device in self.advanced_boot_devices:
                if device["type"].lower() == "vmedia":
                    LsbootVMedia(parent_mo_or_dn=mo_boot_precision, order=device["order"], name=device["name"],
                                 state=device["state"], subtype=device["subtype"])
                if device["type"].lower() == "pxe":
                    LsbootPxe(parent_mo_or_dn=mo_boot_precision, order=device["order"], name=device["name"],
                              state=device["state"], slot=device["slot"], port=device["port"])
                if device["type"].lower() in ["localhdd", "local-hdd"]:
                    LsbootHdd(parent_mo_or_dn=mo_boot_precision, order=device["order"], name=device["name"],
                              state=device["state"], slot=device["slot"])
                if device["type"].lower() in ["sd-card", "sdcard"]:
                    LsbootSd(parent_mo_or_dn=mo_boot_precision, order=device["order"], name=device["name"],
                             state=device["state"], lun=device["lun"])
                if device["type"].lower() == "usb":
                    LsbootUsb(parent_mo_or_dn=mo_boot_precision, order=device["order"], name=device["name"],
                              state=device["state"])
                if device["type"].lower() == "san":
                    LsbootSan(parent_mo_or_dn=mo_boot_precision, order=device["order"], name=device["name"],
                              state=device["state"], slot=device["slot"], lun=device["lun"])
                if device["type"].lower() == "iscsi":
                    LsbootIscsi(parent_mo_or_dn=mo_boot_precision, order=device["order"], name=device["name"],
                                state=device["state"], slot=device["slot"], port=device["port"])
                if device["type"].lower() == "pchstorage":
                    LsbootPchStorage(parent_mo_or_dn=mo_boot_precision, order=device["order"], name=device["name"],
                                     state=device["state"])
                if device["type"].lower() == "uefishell":
                    LsbootUefiShell(parent_mo_or_dn=mo_boot_precision, order=device["order"], name=device["name"],
                                    state=device["state"])
                if device["type"].lower() == "nvme":
                    LsbootNVMe(parent_mo_or_dn=mo_boot_precision, order=device["order"], name=device["name"],
                               state=device["state"])
        if commit:
            if self.commit(mo=mo_boot_precision) != True:
                return False
        return True


class UcsImcStorageController(UcsImcConfigObject):
    _CONFIG_NAME = "Storage Controller"

    def __init__(self, parent=None, json_content=None, storage_controller=None):
        UcsImcConfigObject.__init__(self, parent=parent)
        self.id = None
        self.type = None
        self.virtual_drives = []
        self.local_disks = []
        self.drive_security = []

        if self._config.load_from == "live":
            # Locating SDK objects needed to initialize

            if storage_controller is not None:
                self.id = storage_controller.id
                self.type = storage_controller.type
                if "selfEncryptStorageController" in self._config.sdk_objects:
                    for self_encrypt in self._config.sdk_objects["selfEncryptStorageController"]:
                        if storage_controller.dn in self_encrypt.dn:
                            encrypt = {}
                            # encrypt["key_management"] = self_encrypt.key_management
                            encrypt["security_key_identifier"] = self_encrypt.key_id
                            if encrypt["security_key_identifier"]:
                                encrypt["key_management"] = "local"
                                encrypt["security_key"] = \
                                    self_encrypt.security_key if self_encrypt.security_key != "Security key" else ""
                            else:
                                encrypt["key_management"] = "remote"

                            self.drive_security.append(encrypt)

                for virtual_disk in self._config.sdk_objects["storageVirtualDrive"]:
                    if storage_controller.dn in virtual_disk.dn:
                        drive = {}
                        drive["id"] = virtual_disk.id
                        drive["name"] = virtual_disk.name
                        drive["raid_level"] = virtual_disk.raid_level
                        drive["size"] = virtual_disk.size
                        drive["strip_size"] = virtual_disk.strip_size  # FIXME:  The value '64 KB' is not an element of the set {'64k', '128k', '256k', '512k', '1024k', 'default'}
                        drive["write_policy"] = virtual_disk.requested_write_cache_policy
                        drive["disk_cache_policy"] = virtual_disk.disk_cache_policy.lower()
                        drive["cache_policy"] = virtual_disk.cache_policy
                        if virtual_disk.cache_policy == "Direct":
                            drive["cache_policy"] = "direct-io"  # FIXME: DEBUG - cache_policy valid values are ['', 'cached-io', 'default', 'direct-io']
                        drive["read_policy"] = virtual_disk.read_policy
                        drive["access_policy"] = virtual_disk.access_policy.lower()  # FIXME: DEBUG - access_policy valid values are ['', 'blocked', 'default', 'hidden', 'read-only', 'read-write']
                        if virtual_disk.access_policy == "hidden":
                            drive["status"] = "hidden"
                        elif virtual_disk.access_policy == "Transport Ready":
                            drive["status"] = "transport ready"
                        elif virtual_disk.boot_drive.lower() == "true":
                            drive["status"] = "boot drive"
                        drive["physical_disk_usage"] = []
                        for local_disk in self._config.sdk_objects["storageLocalDiskUsage"]:
                            if virtual_disk.dn + "/" in local_disk.dn:
                                drive["physical_disk_usage"].append(local_disk.physical_drive)
                        self.virtual_drives.append(drive)

                for local_disk in self._config.sdk_objects["storageLocalDisk"]:
                    if storage_controller.dn in local_disk.dn:
                        drive = {}
                        drive["id"] = local_disk.id
                        drive["status"] = local_disk.pd_status
                        drive["dedicated_hot_spare_virtual_drive_id"] = \
                            local_disk.dedicated_hot_spare_for_vd_id \
                                if local_disk.dedicated_hot_spare_for_vd_id != "" else None
                        self.local_disks.append(drive)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

                for element in self.virtual_drives:
                    for value in ["id" "name", "raid_level", "size", "strip_size", "write_policy", "disk_cache_policy",
                                  "cache_policy", "read_policy", "access_policy", "physical_disk_usage",
                                  "virtual_disk_usage", "status"]:
                        if value not in element:
                            element[value] = None

                for element in self.drive_security:
                    for value in ["id", "status", "dedicated_hot_spare_virtual_drive_id"]:
                        if value not in element:
                            element[value] = None

                for element in self.drive_security:
                    for value in ["key_management", "security_key_identifier", "security_key"]:
                        if value not in element:
                            element[value] = None

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + self.id +
                                ". It may take a while.")
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + self.id)

        parent_mo = ""
        if self._device.platform_type == "classic":
            parent_mo = "sys/rack-unit-1/board"
        elif self._device.platform_type == "modular":
            parent_mo = "sys/chassis-1/server-1/board"  # TODO : Fix to add support for server-2 in S3260
        mo_storage_controller = StorageController(parent_mo_or_dn=parent_mo, id=self.id, type=self.type)

        if commit:
            if self.commit(mo=mo_storage_controller) != True:
                return False

        for security in self.drive_security:
            if security["key_management"] == "local":
                if security["security_key"]:
                    if self._device.query(mode="classid", target="selfEncryptStorageController"):
                        mo_encryption = SelfEncryptStorageController(parent_mo_or_dn=mo_storage_controller.dn,
                                                                     key_management=security["key_management"],
                                                                     key_id=security["security_key_identifier"],
                                                                     security_key=security["security_key"],
                                                                     existing_security_key=security["security_key"])
                    else:
                        mo_encryption = SelfEncryptStorageController(parent_mo_or_dn=mo_storage_controller,
                                                                     key_management=security["key_management"],
                                                                     key_id=security["security_key_identifier"],
                                                                     security_key=security["security_key"])

                    if commit:
                        self.commit(mo=mo_encryption)
                else:
                    self.logger(level="warning", message=self._CONFIG_NAME + " Drive Security configuration: " +
                                                         self.id + ": No security key given")
            # TODO Try for remote key management
            elif security["key_management"] == "remote":
                mo_encryption = SelfEncryptStorageController(parent_mo_or_dn=mo_storage_controller,
                                                             key_management=security["key_management"])
                if commit:
                    self.commit(mo=mo_encryption)

        # Fetching the information needed
        all_local_disks = self._device.query(mode="classid", target="storageLocalDisk")
        controller_local_disks = [disk for disk in all_local_disks if mo_storage_controller.dn + "/" in disk.dn]

        all_virtual_drive = self._device.query(mode="classid", target="storageVirtualDrive")
        controller_virtual_drives = [disk for disk in all_virtual_drive if mo_storage_controller.dn + "/" in disk.dn]

        all_local_disk_usage = self._device.query(mode="classid", target="storageLocalDiskUsage")
        controller_disks_used = [local_disk_usage for local_disk_usage in all_local_disk_usage if
                                 mo_storage_controller.dn + "/" in local_disk_usage.dn]

        for drive in self.virtual_drives:

            flag_continue = None
            for virtual_drive in controller_virtual_drives:
                # Case : existing virtual drive to modify
                if virtual_drive.access_policy == "Transport Ready":
                    # Impossible to modify anything if the status is "transport ready"
                    flag_continue = True
                elif virtual_drive.id == drive["id"]:
                    self.logger(level="debug",
                                message=self._CONFIG_NAME + " " + self.id + " - Modifying Virtual Drive " + drive["id"])
                    mo_virtual_drive = StorageVirtualDrive(parent_mo_or_dn=mo_storage_controller,
                                                           id=drive["id"],
                                                           # access_policy=drive["access_policy"],
                                                           cache_policy=drive["cache_policy"],
                                                           disk_cache_policy=drive["disk_cache_policy"],
                                                           raid_level=drive["raid_level"].split("RAID ")[1],
                                                           read_policy=drive["read_policy"],
                                                           requested_write_cache_policy=drive["write_policy"]
                                                           )
                    flag_continue = True
                    if commit:
                        self.commit(mo=mo_virtual_drive)
            if flag_continue:
                continue

            write_policy = drive["write_policy"]
            if write_policy == "always-write-back":
                write_policy = "Always Write Back"
            elif write_policy == "write-back-good-bbu":
                write_policy = "Write Back Good BBU"
            elif write_policy == "write-through":
                write_policy = "Write Through"

            # Case : creating a new virtual drive
            self.logger(level="debug",
                        message=self._CONFIG_NAME + " " + self.id + " - Creating Virtual Drive " + drive["id"])
            requested_drive_group = drive["physical_disk_usage"]
            unconfigured = []
            for drive_id in requested_drive_group:
                for disk in controller_local_disks:
                    if disk.id == drive_id:
                        if disk.drive_state in ["Unconfigured Good", "unconfigured good"]:
                            unconfigured.append(drive_id)
            if len(unconfigured) == len(requested_drive_group):
                # Case : all the local disk are not configured
                mo_virtual_drive = StorageVirtualDriveCreatorUsingUnusedPhysicalDrive(
                    parent_mo_or_dn=mo_storage_controller,
                    virtual_drive_name=drive["name"],
                    raid_level=drive["raid_level"].split("RAID ")[1],
                    size=drive["size"],
                    strip_size=drive["strip_size"],
                    write_policy=write_policy,
                    disk_cache_policy=drive["disk_cache_policy"],
                    cache_policy=drive["cache_policy"],
                    read_policy=drive["read_policy"],
                    access_policy=drive["access_policy"],
                    admin_state="trigger",
                    drive_group=str([int(disk) for disk in drive["physical_disk_usage"]]).replace(' ', '')
                    )
                flag_continue = True
                if commit:
                    if self.commit(mo=mo_virtual_drive) != True:
                        continue
            if flag_continue:
                continue

            # Case : creating a virtual drive from a virtual drive
            virtual_drive_dict = {}
            for i in range(0, len(controller_virtual_drives)):
                virtual_drive_dict[str(i)] = []
            for disk in controller_disks_used:
                virtual_drive_dict[disk.virtual_drive].append(disk.physical_drive)

            virtual_id = ""
            for virtual_id, physical_ids in virtual_drive_dict.items():
                if sorted(physical_ids) == sorted(drive["physical_disk_usage"]):
                    break

            self.logger(level="debug",
                        message=self._CONFIG_NAME + " " + self.id + " - Creating the Virtual Drive " + drive[
                            "id"] + " from Virtual Drive " + virtual_id)

            mo_virtual_drive = StorageVirtualDriveCreatorUsingVirtualDriveGroup(parent_mo_or_dn=mo_storage_controller,
                                                                                virtual_drive_name=drive["name"],
                                                                                size=drive["size"],
                                                                                strip_size=drive["strip_size"],
                                                                                write_policy=write_policy,
                                                                                disk_cache_policy=drive[
                                                                                    "disk_cache_policy"],
                                                                                cache_policy=drive["cache_policy"],
                                                                                read_policy=drive["read_policy"],
                                                                                access_policy=drive["access_policy"],
                                                                                admin_state="trigger",
                                                                                shared_virtual_drive_id=virtual_id
                                                                                )
            flag_continue = True
            if commit:
                if self.commit(mo=mo_virtual_drive) != True:
                    continue

            if flag_continue:
                continue

            # Case : None of the above
            self.logger(level='error',
                        message="Error with " + self._CONFIG_NAME + " configuration: " + self.id +
                                " : Please check the values in the 'physical_disk_usage' section of the config. " +
                                "Impossible to find an existing virtual drive. The disks given are not unconfigured. " +
                                "No virtual drive already has the exact same disks than those given")

        # Handling options only possible through the "admin_action" parameter
        for drive in self.virtual_drives:
            # Check the live status
            live_drive_status = ""
            for virtual_disk in controller_virtual_drives:
                if virtual_disk.id == drive["id"]:
                    if virtual_disk.access_policy == "hidden":
                        live_drive_status = "hidden"
                    elif virtual_disk.access_policy == "Transport Ready":
                        live_drive_status = "transport ready"
                    elif virtual_disk.boot_drive.lower() == "true":
                        live_drive_status = "boot drive"
            if live_drive_status == str(drive["status"]).lower():
                # We skip the drive if the status is the same as the one already configured
                continue
            # We need to clear the previous configuration
            if live_drive_status == "boot drive":
                # Impossible to clear only one drive: All of them or none.
                self.logger(level="warning",
                            message="All boot drives of Storage Controller " + self.id + " have been cleared")
                mo_storage_controller = StorageController(parent_mo_or_dn=parent_mo, id=self.id, type=self.type,
                                                          admin_action="clear-boot-drive")
                if commit:
                    self.commit(mo=mo_storage_controller)
            elif live_drive_status == "hidden":
                mo_virtual_drive = StorageVirtualDrive(parent_mo_or_dn=mo_storage_controller,
                                                       id=drive["id"],
                                                       admin_action="unhide-virtual-drive")
                if commit:
                    self.commit(mo=mo_virtual_drive)
            elif live_drive_status == "transport ready":
                mo_virtual_drive = StorageVirtualDrive(parent_mo_or_dn=mo_storage_controller,
                                                       id=drive["id"],
                                                       admin_action="clear-transport-ready")
                if commit:
                    self.commit(mo=mo_virtual_drive)

            # We configure the new status
            if str(drive["status"]).lower() == "boot drive":
                self.logger(level="debug",
                            message=self._CONFIG_NAME + " configuration: " + self.id + " - Virtual Drive " + drive[
                                "id"] + " - Setting status to " + drive["status"])
                mo_virtual_drive = StorageVirtualDrive(parent_mo_or_dn=mo_storage_controller.dn,
                                                       id=drive["id"],
                                                       admin_action="set-boot-drive")
                if commit:
                    self.commit(mo=mo_virtual_drive)
            elif str(drive["status"]).lower() == "hidden":
                self.logger(level="debug",
                            message=self._CONFIG_NAME + " configuration: " + self.id + " - Virtual Drive " + drive[
                                "id"] + " - Setting status to " + drive["status"])
                mo_virtual_drive = StorageVirtualDrive(parent_mo_or_dn=mo_storage_controller.dn,
                                                       id=drive["id"],
                                                       admin_action="hide-virtual-drive")
                if commit:
                    self.commit(mo=mo_virtual_drive)
            elif str(drive["status"]).lower() == "transport ready":
                self.logger(level="debug",
                            message=self._CONFIG_NAME + " configuration: " + self.id + " - Virtual Drive " + drive[
                                "id"] + " - Setting status to " + drive["status"])
                mo_virtual_drive = StorageVirtualDrive(parent_mo_or_dn=mo_storage_controller.dn, id=drive["id"],
                                                       admin_action="set-transport-ready")
                if commit:
                    self.commit(mo=mo_virtual_drive)

        for disk in self.local_disks:
            # Check the live status
            live_disk_status = ""
            for local_disk in controller_local_disks:
                if local_disk.id == disk["id"]:
                    live_disk_status = local_disk.pd_status

            if live_disk_status.lower() == disk["status"].lower():
                # We skip the drive if the status is the same as the one already configured
                continue

            # We first need to clear the previous configuration
            if "hot spare" in live_disk_status.lower():
                # Remove Dedicated or Global Hot Spare status
                mo_local_disk = StorageLocalDisk(parent_mo_or_dn=mo_storage_controller.dn,
                                                 id=disk["id"],
                                                 admin_action="remove-hot-spare")
                if commit:
                    self.commit(mo=mo_local_disk)
            elif live_disk_status.lower() in ["jbod"] and live_disk_status.lower() != "unconfigured good" \
                    and disk["status"].lower() != "unconfigured good":
                # Remove JBOD status and avoid removing "unconfigured good" if it's already the status of the disk
                mo_local_disk = StorageLocalDisk(parent_mo_or_dn=mo_storage_controller.dn, id=disk["id"],
                                                 admin_action="make-unconfigured-good")
                if commit:
                    self.commit(mo=mo_local_disk)

            # We configure the new status
            if disk["status"].lower() == "global hot spare":
                self.logger(level="debug",
                            message=self._CONFIG_NAME + " configuration: " + self.id + " - Local Disk " + disk[
                                "id"] + " - Setting status to " + disk["status"])
                mo_local_disk = StorageLocalDisk(parent_mo_or_dn=mo_storage_controller.dn, id=disk["id"],
                                                 admin_action="make-global-hot-spare")
                if commit:
                    self.commit(mo=mo_local_disk)

            elif disk["status"].lower() == "dedicated hot spare":
                self.logger(level="debug",
                            message=self._CONFIG_NAME + " configuration: " + self.id + " - Local Disk " + disk[
                                "id"] + " - Setting status to " + disk["status"])
                if disk["dedicated_hot_spare_virtual_drive_id"]:
                    mo_local_disk = \
                        StorageLocalDisk(parent_mo_or_dn=mo_storage_controller.dn, id=disk["id"],
                                         admin_action="make-dedicated-hot-spare",
                                         dedicated_hot_spare_for_vd_id=disk["dedicated_hot_spare_virtual_drive_id"])
                    if commit:
                        self.commit(mo=mo_local_disk)
                else:
                    self.logger(level="warning",
                                message=self._CONFIG_NAME + " Physical Drive " + self.id + " " + disk["id"] +
                                        " configuration: No 'dedicated_hot_spare_virtual_drive_id' given")
            elif disk["status"].lower() == "jbod":
                self.logger(level="debug",
                            message=self._CONFIG_NAME + " configuration: " + self.id + " - Local Disk " + disk[
                                "id"] + " - Setting status to " + disk["status"])
                mo_local_disk = StorageLocalDisk(parent_mo_or_dn=mo_storage_controller.dn, id=disk["id"],
                                                 admin_action="make-jbod")
                if commit:
                    self.commit(mo=mo_local_disk)

            elif disk["status"].lower() == "unconfigured good":
                self.logger(level="debug",
                            message=self._CONFIG_NAME + " configuration: " + self.id + " - Local Disk " + disk[
                                "id"] + " - Setting status to " + disk["status"])
                mo_local_disk = StorageLocalDisk(parent_mo_or_dn=mo_storage_controller.dn, id=disk["id"],
                                                 admin_action="make-unconfigured-good")
                if commit:
                    self.commit(mo=mo_local_disk)

        return True


class UcsImcStorageFlexFlashController(UcsImcConfigObject):
    _CONFIG_NAME = "Storage Flex Flash Controller"

    def __init__(self, parent=None, json_content=None, storage_controller=None):
        UcsImcConfigObject.__init__(self, parent=parent)
        self.id = None
        self.configured_mode = None
        self.slot_1_read_error_threshold = None
        self.slot_2_read_error_threshold = None
        self.slot_1_write_error_threshold = None
        self.slot_2_write_error_threshold = None
        self.primary_card = None
        self.mirror_partition_name = None
        self.auto_sync = None
        self.user_partition_name = None
        self.non_util_card_partition_name = None
        self.util_card = None

        if self._config.load_from == "live":
            # Locating SDK objects needed to initialize

            if storage_controller is not None:
                self.id = storage_controller.id

                for operational_profile in self._config.sdk_objects["storageFlexFlashOperationalProfile"]:
                    if storage_controller.dn in operational_profile.dn:
                        self.configured_mode = operational_profile.operating_mode
                        self.slot_1_read_error_threshold = operational_profile.rd_err_count_slot1_threshold
                        self.slot_2_read_error_threshold = operational_profile.rd_err_count_slot2_threshold
                        self.slot_1_write_error_threshold = operational_profile.wr_err_count_slot1_threshold
                        self.slot_2_write_error_threshold = operational_profile.wr_err_count_slot2_threshold

                if self.configured_mode == "util":
                    for virtual_drive in self._config.sdk_objects["storageFlexFlashVirtualDrive"]:
                        if storage_controller.dn in virtual_drive.dn:
                            if virtual_drive.partition_id == '4':
                                self.user_partition_name = virtual_drive.virtual_drive
                            if virtual_drive.partition_id == '5':
                                self.non_util_card_partition_name = virtual_drive.virtual_drive

                for physical_drive in self._config.sdk_objects["storageFlexFlashPhysicalDrive"]:
                    if storage_controller.dn in physical_drive.dn:
                        if self.configured_mode == "mirror":
                            if physical_drive.card_mode == "mirror-primary":
                                self.primary_card = physical_drive.physical_drive_id
                                self.mirror_partition_name = physical_drive.drives_enabled
                                self.auto_sync = physical_drive.sync_mode
                        elif self.configured_mode == "util":
                            if self.user_partition_name in physical_drive.drives_enabled:
                                self.util_card = physical_drive.physical_drive_id

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
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + self.id)

        parent_mo = "sys/rack-unit-1/board"

        auto_sync = self.auto_sync
        if self.auto_sync == "manual":
            auto_sync = "no"
        if self.auto_sync == "auto":
            auto_sync = "yes"
            
        if self.primary_card:
            primary_card = self.primary_card
            if self.primary_card.lower() in ["1", "slot-1", "slot 1", "slot_1"]:
                primary_card = "slot-1"
            elif self.primary_card.lower() in ["2", "slot-2", "slot 2", "slot_2"]:
                primary_card = "slot-2"
        if self.util_card:
            util_card = self.util_card
            if self.util_card.lower() in ["1", "slot-1", "slot 1", "slot_1"]:
                util_card = "slot-1"
            elif self.util_card.lower() in ["2", "slot-2", "slot 2", "slot_2"]:
                util_card = "slot-2"

        if self.configured_mode == "util":
            mo_storage_controller = \
                StorageFlexFlashController(parent_mo_or_dn=parent_mo, id=self.id, admin_action="configure-cards",
                                           card_slot=util_card, configured_mode=self.configured_mode,
                                           auto_sync=auto_sync,
                                           non_util_partition_name=self.non_util_card_partition_name,
                                           partition_name=self.user_partition_name)
        elif self.configured_mode == "mirror":
            mo_storage_controller = StorageFlexFlashController(parent_mo_or_dn=parent_mo, id=self.id,
                                                               admin_action="configure-cards",
                                                               card_slot=primary_card,
                                                               configured_mode=self.configured_mode,
                                                               auto_sync=auto_sync,
                                                               partition_name=self.mirror_partition_name)

        if commit:
            if self.commit(mo=mo_storage_controller) != True:
                return False

        mo_storage_ope_profile = \
            StorageFlexFlashOperationalProfile(parent_mo_or_dn=mo_storage_controller,
                                               rd_err_count_slot1_threshold=self.slot_1_read_error_threshold,
                                               rd_err_count_slot2_threshold=self.slot_2_read_error_threshold,
                                               wr_err_count_slot1_threshold=self.slot_1_write_error_threshold,
                                               wr_err_count_slot2_threshold=self.slot_2_write_error_threshold)

        if commit:
            if self.commit(mo=mo_storage_ope_profile) != True:
                return False

        return True
