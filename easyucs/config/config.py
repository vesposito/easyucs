# coding: utf-8
# !/usr/bin/env python

""" config.py: Easy UCS Deployment Tool """
from easyucs import __author__, __copyright__,  __version__, __status__


import http
import re
import time
import uuid
import urllib
import xml

from ucsmsdk.ucsexception import UcsException
from imcsdk.imcexception import ImcException
from ucscsdk.ucscexception import UcscException
from ucsmsdk.ucscoremeta import UcsVersion


class GenericConfig:
    def __init__(self, parent=None):
        self.custom = None
        self.device = parent.parent
        self.device_version = ""
        self.load_from = None
        self.options = {}
        self.origin = None
        self.parent = parent
        self.status = None
        self.timestamp = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
        self.uuid = uuid.uuid4()

        self._parent_having_logger = self._find_logger()

    def logger(self, level='info', message="No message"):
        if not self._parent_having_logger:
            self._parent_having_logger = self._find_logger()

        if self._parent_having_logger:
            self._parent_having_logger.logger(level=level, message=message)

    def _find_logger(self):
        # Method to find the object having a logger - it can be high up in the hierarchy of objects
        current_object = self
        while hasattr(current_object, 'parent') and not hasattr(current_object, '_logger_handle'):
            current_object = current_object.parent

        if hasattr(current_object, '_logger_handle'):
            return current_object
        else:
            print("WARNING: No logger found in config")
            return None

    def __str__(self):
        return str(vars(self))


class GenericUcsConfig(GenericConfig):
    def __init__(self, parent=None):
        GenericConfig.__init__(self, parent=parent)
        self.export_list = None
        self.handle = self.parent.parent.handle
        self.intersight_status = ""
        self.sdk_objects = {}

    def _fetch_sdk_objects(self):
        # List of SDK objects to fetch that are common to UCS System & IMC
        sdk_objects_to_fetch = ["aaaUser", "commNtpProvider", "topSystem"]
        self.logger(level="debug", message="Fetching common UCS SDK objects for config")
        for sdk_object_name in sdk_objects_to_fetch:
            try:
                self.sdk_objects[sdk_object_name] = self.handle.query_classid(sdk_object_name)
            except (UcsException, ImcException) as err:
                if err.error_code == "ERR-xml-parse-error" and "no class named " + sdk_object_name in err.error_descr:
                    self.logger(level="debug", message="No UCS class named " + sdk_object_name)
                else:
                    self.logger(level="error", message="Error while trying to fetch UCS class " + sdk_object_name +
                                                       ": " + str(err))
            except ConnectionRefusedError:
                self.logger(level="error", message="Error while communicating with UCS class " + sdk_object_name +
                                                   ": Connection refused")
            except urllib.error.URLError:
                self.logger(level="error", message="Timeout error while fetching UCS class " + sdk_object_name)

    def get_config_objects_under_dn(self, dn=None, object_class=None, parent=None):
        if dn is not None and object_class is not None and parent is not None:
            if hasattr(object_class, "_UCS_SDK_OBJECT_NAME"):
                if object_class._UCS_SDK_OBJECT_NAME in self.sdk_objects.keys():
                    if self.sdk_objects[object_class._UCS_SDK_OBJECT_NAME] is not None:
                        # We filter out SDK objects that are not under this Dn
                        filtered_sdk_objects_list = []
                        for sdk_object in self.sdk_objects[object_class._UCS_SDK_OBJECT_NAME]:
                            if sdk_object.dn.startswith(dn + '/'):
                                if "/" not in sdk_object.dn[len(dn + "/"):]:
                                    # WWPN, WWNN and WWXN use the same object class.
                                    # We use the "purpose" parameter to differentiate them.
                                    if object_class.__name__ in ["UcsSystemWwpnPool", "UcsCentralWwpnPool"]:
                                        if sdk_object.purpose != "port-wwn-assignment":
                                            continue
                                    if object_class.__name__ in ["UcsSystemWwnnPool", "UcsCentralWwnnPool"]:
                                        if sdk_object.purpose != "node-wwn-assignment":
                                            continue
                                    if object_class.__name__ in ["UcsSystemWwxnPool", "UcsCentralWwxnPool"]:
                                        if sdk_object.purpose != "node-and-port-wwn-assignment":
                                            continue
                                    filtered_sdk_objects_list.append(sdk_object)

                                elif "/domaingroup-" not in sdk_object.dn[len(dn):]:
                                    # dn with / even after removing parent dn and do not have another domaingroup parent
                                    if object_class.__name__ in ["UcsCentralVlan"]:
                                        if sdk_object.dn[len(dn + "/"):].startswith("fabric/eth-estc"):
                                            continue
                                        else:
                                            filtered_sdk_objects_list.append(sdk_object)
                                    if object_class.__name__ in ["UcsCentralApplianceVlan"]:
                                        if sdk_object.dn[len(dn + "/"):].startswith("fabric/lan"):
                                            continue
                                        else:
                                            filtered_sdk_objects_list.append(sdk_object)

                                    if object_class.__name__ in ["UcsCentralVlanGroup"]:
                                        if sdk_object.dn[len(dn + "/"):].startswith("fabric/lan/net-group"):
                                            filtered_sdk_objects_list.append(sdk_object)

                            elif sdk_object.dn.startswith("fabric/lan/flowctrl/policy-"):
                                # Exception for Flow Control Policy
                                filtered_sdk_objects_list.append(sdk_object)

                        easyucs_objects_list = []
                        for sdk_object in sorted(filtered_sdk_objects_list,
                                                 key=lambda sdk_obj: [int(t) if t.isdigit() else t.lower()
                                                                      for t in re.split('(\d+)', sdk_obj.dn)]):
                            # We instantiate a Config Object for each corresponding SDK object
                            easyucs_objects_list.append(object_class(parent, None, sdk_object))
                        return easyucs_objects_list
        return []

    def refresh_config_handle(self):
        """
        Change all the references to a UCS Handle in a config in case of a change of handle attributes
        (IP address, username or password). For example: During a reset, or after an initial setup
        Check the first layer of the config and the second layer. No other _handle should be in another layer.

        :return: True if successful, False otherwise
        """
        self.handle = self.parent.parent.handle

        self._refresh_handle(current_object=self, handle=self.parent.parent.handle)

        self.logger(level="debug", message="Successfully refreshed config handle")
        return True

    def _refresh_handle(self, current_object=None, handle=None):
        """
        Recursively resets the reference to a UCS handle
        :param current_object: portion of the config file currently being looked at
        :return: nothing
        """
        if hasattr(current_object, "_handle"):
            current_object._handle = handle

        for attr in vars(current_object):
            if not attr.startswith('_') and not attr == "dn" and getattr(current_object, attr) is not None:
                obj = getattr(current_object, attr)
                if isinstance(obj, list):
                    for subobject in obj:
                        if not isinstance(subobject, (str, float, int, dict)):
                            self._refresh_handle(current_object=subobject, handle=handle)


class UcsSystemConfig(GenericUcsConfig):
    _BIOS_TOKENS_MIN_REQUIRED_VERSION = "3.2(1d)"

    def __init__(self, parent=None):
        self.service_profile_plots = None
        self.orgs_plot = None

        self.appliance_network_control_policies = []
        self.appliance_port_channels = []
        self.appliance_ports = []
        self.appliance_vlans = []
        self.backup_export_policy = []
        self.breakout_ports = []
        self.call_home = []
        self.communication_services = []
        self.dns = []
        self.fc_zone_profiles = []
        self.fcoe_port_channels = []
        self.fcoe_storage_ports = []
        self.fcoe_uplink_ports = []
        self.global_policies = []
        self.lan_pin_groups = []
        self.lan_port_channels = []
        self.lan_uplink_ports = []
        self.ldap = []
        self.link_profiles = []
        self.local_users = []
        self.local_users_properties = []
        self.locales = []
        self.management_interfaces = []
        self.orgs = []
        self.port_auto_discovery_policy = []
        self.pre_login_banner = ""
        self.qos_system_class = []
        self.radius = []
        self.roles = []
        self.san_pin_groups = []
        self.san_port_channels = []
        self.san_storage_ports = []
        self.san_unified_ports = []
        self.san_uplink_ports = []
        self.sel_policy = []
        self.server_ports = []
        self.slow_drain_timers = []
        self.storage_vsans = []
        self.switching_mode = []
        self.system = []
        self.tacacs = []
        self.timezone_mgmt = []
        self.ucs_central = []
        self.udld_link_policies = []
        self.unified_storage_ports = []
        self.unified_uplink_ports = []
        self.vlan_groups = []
        self.vlans = []
        self.vsans = []
        GenericUcsConfig.__init__(self, parent=parent)

        # List of attributes to be exported in a config export
        self.export_list = ['appliance_network_control_policies', 'appliance_port_channels', 'appliance_ports',
                            'appliance_vlans', 'backup_export_policy', 'breakout_ports', 'call_home',
                            'communication_services', 'dns', 'fcoe_port_channels', 'fcoe_storage_ports',
                            'fcoe_uplink_ports', 'global_policies', 'lan_pin_groups',
                            'lan_port_channels', 'lan_uplink_ports', 'ldap', 'link_profiles', 'local_users',
                            'local_users_properties', 'locales', 'management_interfaces', 'orgs',
                            'port_auto_discovery_policy', 'pre_login_banner', 'qos_system_class',
                            'radius', 'roles', 'san_pin_groups', 'san_port_channels', 'san_storage_ports',
                            'san_unified_ports', 'san_uplink_ports', 'sel_policy', 'server_ports', 'slow_drain_timers',
                            'storage_vsans', 'switching_mode', 'system', 'tacacs', 'timezone_mgmt', 'ucs_central',
                            'fc_zone_profiles',
                            'udld_link_policies', 'unified_storage_ports', 'unified_uplink_ports', 'vlan_groups',
                            'vlans', 'vsans']

    def check_if_ports_config_requires_reboot(self):
        """
        Checks if the specified config will require a reboot because of port type changes (Unified Ports, Breakout)
        :return: True if config push will require a reboot because of port type changes, False otherwise
        """
        # FIXME: make sure we are connected to the live system
        # FIXME: IMPROVEMENT: determine the exact list of reboot reasons and return them as a dict

        # We first need to check for current ports types on the live system
        try:
            etherpio_list = self.device.query(mode="classid", target="etherPIo")
            fcpio_list = self.device.query(mode="classid", target="fcPIo")
        except ConnectionRefusedError:
            self.logger(level="error", message="Error while communicating with UCS System")
            return
        except UcsException:
            self.logger(level="error", message="Unable to fetch current ports types on UCS System")
            return
        except urllib.error.URLError:
            self.logger(level="error", message="Timeout error while fetching current ports types on UCS System")
            return

        # We create lists of ports of type Ethernet or FC from the configuration
        eth_port_config_list = [{"fabric": eth_port.fabric, "slot_id": eth_port.slot_id, "port_id": eth_port.port_id,
                                 "aggr_id": eth_port.aggr_id} for eth_port in (self.lan_uplink_ports +
                                                                               self.fcoe_storage_ports +
                                                                               self.fcoe_uplink_ports +
                                                                               self.appliance_ports +
                                                                               self.server_ports +
                                                                               self.unified_storage_ports +
                                                                               self.unified_uplink_ports)]

        fc_port_config_list = [{"fabric": fc_port.fabric, "slot_id": fc_port.slot_id, "port_id": fc_port.port_id} for
                               fc_port in (self.san_storage_ports + self.san_uplink_ports)]

        # We add the list of unified ports - since they are given as a range, we need to handle this differently
        for entry in self.san_unified_ports:
            start = int(entry.port_id_start)
            end = int(entry.port_id_end)
            for port in range(start, end + 1):
                fc_port_config_list.append({"fabric": entry.fabric, "slot_id": entry.slot_id, "port_id": str(port)})

        # We then deduplicate the list
        fc_port_config_list = [dict(t) for t in set([tuple(d.items()) for d in fc_port_config_list])]

        # We check if there are Ethernet ports that will need to be converted to FC ports
        for fc_port in fc_port_config_list:
            for eth_port in etherpio_list:
                if fc_port["fabric"] == eth_port.switch_id and fc_port["slot_id"] == eth_port.slot_id and\
                        fc_port["port_id"] == eth_port.port_id and eth_port.aggr_port_id == "0":
                    self.logger(level="debug", message="A reboot will be required because Ethernet ports will be " +
                                                       "converted to FC ports")
                    return True

        # We check if there are FC ports that will need to be converted to Ethernet ports
        for eth_port in eth_port_config_list:
            for fc_port in fcpio_list:
                if eth_port["fabric"] == fc_port.switch_id and eth_port["slot_id"] == fc_port.slot_id and\
                        eth_port["port_id"] == fc_port.port_id:
                    self.logger(level="debug", message="A reboot will be required because FC ports will be " +
                                                       "converted to Ethernet ports")
                    return True

        # We check if there are native Ethernet ports that will need to be converted to Breakout ports
        for breakout_port in self.breakout_ports:
            for eth_port in etherpio_list:
                if breakout_port.fabric == eth_port.switch_id and breakout_port.slot_id == eth_port.slot_id and\
                        breakout_port.port_id == eth_port.port_id and eth_port.aggr_port_id == "0":
                    self.logger(level="debug", message="A reboot will be required because Ethernet ports will be " +
                                                       "converted to Breakout ports")
                    return True

        # We check if there are Breakout ports that will need to be converted to native Ethernet ports
        for etherpio in etherpio_list:
            for eth_port in eth_port_config_list:
                if etherpio.switch_id == eth_port["fabric"] and etherpio.slot_id == eth_port["slot_id"] and\
                        etherpio.aggr_port_id == eth_port["port_id"] and eth_port["aggr_id"] is None:
                    self.logger(level="debug", message="A reboot will be required because Breakout ports will be " +
                                                       "converted to Ethernet ports")
                    return True

        return False

    def check_if_switching_mode_config_requires_reboot(self):
        """
        Checks if the specified config will require a reboot because of switching mode (Ethernet & FC)
        :return: True if config push will require a reboot because of switching mode changes, False otherwise
        """
        # FIXME: make sure we are connected to the live system
        # FIXME: IMPROVEMENT: determine the exact list of reboot reasons and return them as a dict

        # We first need to check for current Ethernet & FC switching modes on the live system
        try:
            fabric_lan_cloud_list = self.device.query(mode="classid", target="fabricLanCloud")
            fabric_san_cloud_list = self.device.query(mode="classid", target="fabricSanCloud")

            if fabric_lan_cloud_list:
                fabric_lan_cloud = fabric_lan_cloud_list[0]
            else:
                self.logger(level="error", message="Could not get currently running Ethernet switching mode")
                return None

            if fabric_san_cloud_list:
                fabric_san_cloud = fabric_san_cloud_list[0]
            else:
                self.logger(level="error", message="Could not get currently running FC switching mode")
                return None

            # We get the running Ethernet & FC switching mode
            eth_switching_mode = fabric_lan_cloud.mode
            fc_switching_mode = fabric_san_cloud.mode

            # We check if the Ethernet switching mode in the config is different from the running mode
            if self.switching_mode:
                if self.switching_mode[0].ethernet_mode != eth_switching_mode:
                    self.logger(level="debug",
                                message="A reboot will be required because Ethernet switching mode will be changed")
                    return True

            # We check if the FC switching mode in the config is different from the running mode
            if self.switching_mode:
                if self.switching_mode[0].fc_mode != fc_switching_mode:
                    self.logger(level="debug",
                                message="A reboot will be required because FC switching mode will be changed")
                    return True

            return False
        except Exception:
            self.logger(level="error", message="Error while trying to fetch switching mode info on the live system")
            return False

    def _fetch_sdk_objects(self):
        GenericUcsConfig._fetch_sdk_objects(self)

        version_min_required = UcsVersion(self._BIOS_TOKENS_MIN_REQUIRED_VERSION)

        # Depending on the UCSM version, we only fetch some SDK objects in order to gain time by making fewer queries
        if self.device.version.__ge__(version_min_required):
            bios_sdk_objects_to_fetch = ['biosTokenParam', 'biosTokenSettings']
        else:
            bios_sdk_objects_to_fetch = ['biosVfASPMSupport', 'biosVfAllUSBDevices', 'biosVfAltitude',
                                         'biosVfAssertNMIOnPERR', 'biosVfBootOptionRetry',
                                         'biosVfCPUHardwarePowerManagement', 'biosVfCPUPerformance',
                                         'biosVfConsistentDeviceNameControl', 'biosVfConsoleRedirection',
                                         'biosVfCoreMultiProcessing', 'biosVfDDR3VoltageSelection',
                                         'biosVfDRAMClockThrottling', 'biosVfDirectCacheAccess',
                                         'biosVfDramRefreshRate', 'biosVfEnergyPerformanceTuning',
                                         'biosVfEnhancedIntelSpeedStepTech', 'biosVfExecuteDisableBit',
                                         'biosVfFRB2Timer', 'biosVfFrequencyFloorOverride', 'biosVfFrontPanelLockout',
                                         'biosVfIOEMezz1OptionROM', 'biosVfIOENVMe1OptionROM',
                                         'biosVfIOENVMe2OptionROM', 'biosVfIOESlot1OptionROM',
                                         'biosVfIOESlot2OptionROM', 'biosVfIntegratedGraphics',
                                         'biosVfIntegratedGraphicsApertureSize', 'biosVfIntelEntrySASRAIDModule',
                                         'biosVfIntelHyperThreadingTech', 'biosVfIntelTrustedExecutionTechnology',
                                         'biosVfIntelTurboBoostTech', 'biosVfIntelVTForDirectedIO',
                                         'biosVfIntelVirtualizationTechnology', 'biosVfInterleaveConfiguration',
                                         'biosVfLocalX2Apic', 'biosVfLvDIMMSupport', 'biosVfMaxVariableMTRRSetting',
                                         'biosVfMaximumMemoryBelow4GB', 'biosVfMemoryMappedIOAbove4GB',
                                         'biosVfMirroringMode', 'biosVfNUMAOptimized',
                                         'biosVfOSBootWatchdogTimerPolicy', 'biosVfOSBootWatchdogTimerTimeout',
                                         'biosVfOnboardGraphics', 'biosVfOnboardStorage', 'biosVfOutOfBandManagement',
                                         'biosVfPCILOMPortsConfiguration', 'biosVfPCIROMCLP', 'biosVfPCISlotLinkSpeed',
                                         'biosVfPCISlotOptionROMEnable', 'biosVfPOSTErrorPause',
                                         'biosVfPSTATECoordination', 'biosVfPackageCStateLimit', 'biosVfProcessorC1E',
                                         'biosVfProcessorC3Report', 'biosVfProcessorC6Report',
                                         'biosVfProcessorC7Report', 'biosVfProcessorCMCI', 'biosVfProcessorCState',
                                         'biosVfProcessorEnergyConfiguration', 'biosVfProcessorPrefetchConfig',
                                         'biosVfQPILinkFrequencySelect', 'biosVfQPISnoopMode', 'biosVfQuietBoot',
                                         'biosVfRedirectionAfterBIOSPOST', 'biosVfResumeOnACPowerLoss',
                                         'biosVfSBMezz1OptionROM', 'biosVfSBNVMe1OptionROM', 'biosVfSIOC1OptionROM',
                                         'biosVfSIOC2OptionROM', 'biosVfScrubPolicies',
                                         'biosVfSelectMemoryRASConfiguration', 'biosVfSerialPortAEnable',
                                         'biosVfTrustedPlatformModule', 'biosVfUSBBootConfig', 'biosVfUSBConfiguration',
                                         'biosVfUSBFrontPanelAccessLock', 'biosVfUSBPortConfiguration',
                                         'biosVfUSBSystemIdlePowerOptimizingSetting', 'biosVfVGAPriority',
                                         'biosVfWorkloadConfiguration']

        # List of SDK objects to fetch that are only available in UCS System
        sdk_objects_to_fetch = ['aaaEpAuthProfile', 'aaaEpUser', 'aaaLdapEp', 'aaaLdapGroup', 'aaaLdapGroupRule',
                                'aaaLdapProvider', 'aaaLocale', 'aaaOrg', 'aaaPreLoginBanner', 'aaaProviderGroup',
                                'aaaProviderRef', 'aaaPwdProfile', 'aaaRadiusEp', 'aaaRadiusProvider', 'aaaRole',
                                'aaaSshAuth', 'aaaTacacsPlusEp', 'aaaTacacsPlusProvider', 'aaaUserEp', 'aaaUserLocale',
                                'aaaUserRole', 'adaptorCapQual', 'adaptorEthAdvFilterProfile', 'adaptorEthArfsProfile',
                                'adaptorEthCompQueueProfile', 'adaptorEthFailoverProfile', 'adaptorEthInterruptProfile',
                                'adaptorEthInterruptScalingProfile', 'adaptorEthNVGREProfile',
                                'adaptorEthOffloadProfile', 'adaptorEthRecvQueueProfile', 'adaptorEthRoCEProfile',
                                'adaptorEthVxLANProfile', 'adaptorEthWorkQueueProfile', 'adaptorFcCdbWorkQueueProfile',
                                'adaptorFcErrorRecoveryProfile', 'adaptorFcFnicProfile', 'adaptorFcInterruptProfile',
                                'adaptorFcPortFLogiProfile', 'adaptorFcPortPLogiProfile', 'adaptorFcPortProfile',
                                'adaptorFcRecvQueueProfile', 'adaptorFcVhbaTypeProfile', 'adaptorFcWorkQueueProfile',
                                'adaptorHostEthIfProfile', 'adaptorHostFcIfProfile', 'adaptorHostIscsiIfProfile',
                                'adaptorProtocolProfile', 'adaptorQual', 'adaptorRssProfile', 'biosVProfile',
                                'callhomeAnonymousReporting', 'callhomeDest', 'callhomeEp',
                                'callhomePeriodicSystemInventory', 'callhomePolicy', 'callhomeProfile', 'callhomeSmtp',
                                'callhomeSource', 'cimcvmediaConfigMountEntry', 'cimcvmediaMountConfigPolicy',
                                'commCimcWebService', 'commCimxml', 'commDateTime', 'commDns', 'commDnsProvider',
                                'commHttp', 'commHttps', 'commShellSvcLimits', 'commSnmp', 'commSnmpTrap',
                                'commSnmpUser', 'commSsh', 'commTelnet', 'commWebSvcLimits', 'computeChassisDiscPolicy',
                                'computeChassisQual', 'computeGraphicsCardPolicy', 'computeHwChangeDiscPolicy',
                                'computeKvmMgmtPolicy', 'computeMemoryConfigPolicy', 'computePhysicalQual',
                                'computePool', 'computePooledRackUnit', 'computePooledSlot', 'computePoolingPolicy',
                                'computePortDiscPolicy', 'computePowerSyncPolicy', 'computePsuPolicy', 'computeQual',
                                'computeRackQual', 'computeScrubPolicy', 'computeServerDiscPolicy',
                                'computeServerMgmtPolicy', 'computeSlotQual', 'cpmaintMaintPolicy', 'diagMemoryTest',
                                'diagRunPolicy', 'dpsecMac', 'epqosDefinition', 'epqosEgress', 'equipmentBinding',
                                'equipmentChassisProfile', 'equipmentComputeConnPolicy', 'etherPIo', 'fabricBreakout',
                                'fabricDceSwSrvEp', 'fabricDceSwSrvPcEp', 'fabricEthEstcEp', 'fabricEthEstcPc',
                                'fabricEthEstcPcEp', 'fabricEthLanEp', 'fabricEthLanPc', 'fabricEthLanPcEp',
                                'fabricEthLinkProfile', 'fabricEthTargetEp', 'fabricEthVlanPc', 'fabricEthVlanPortEp',
                                'fabricFcEndpoint', 'fabricFcEstcEp', 'fabricFcSan', 'fabricFcSanEp', 'fabricFcSanPc',
                                'fabricFcSanPcEp', 'fabricFcUserZone', 'fabricFcVsanPc', 'fabricFcVsanPortEp',
                                'fabricFcZoneProfile', 'fabricFcoeEstcEp', 'fabricFcoeSanEp', 'fabricFcoeSanPc',
                                'fabricFcoeSanPcEp', 'fabricFcoeVsanPortEp', 'fabricLacpPolicy', 'fabricLanCloud',
                                'fabricLanPinGroup', 'fabricLanPinTarget', 'fabricMulticastPolicy', 'fabricNetGroup',
                                'fabricNetGroupRef', 'fabricOrgVlanPolicy', 'fabricPooledVlan', 'fabricSanCloud',
                                'fabricSanPinGroup', 'fabricSanPinTarget', 'fabricUdldLinkPolicy', 'fabricUdldPolicy',
                                'fabricVCon', 'fabricVConProfile', 'fabricVlan', 'fabricVlanGroupReq', 'fabricVlanReq',
                                'fabricVsan', 'fcPIo', 'fcpoolBlock', 'fcpoolInitiators', 'firmwareAutoSyncPolicy',
                                'firmwareChassisPack', 'firmwareComputeHostPack', 'firmwareExcludeChassisComponent',
                                'firmwareExcludeServerComponent', 'firmwarePackItem', 'flowctrlItem', 'ippoolBlock',
                                'ippoolIpV6Block', 'ippoolPool', 'iqnpoolBlock', 'iqnpoolPool', 'iscsiAuthProfile',
                                'lsBinding', 'lsPower', 'lsRequirement', 'lsServer', 'lsServerExtension',
                                'lsVConAssign', 'lsbootBootSecurity', 'lsbootDefaultLocalImage', 'lsbootEFIShell',
                                'lsbootEmbeddedLocalDiskImage', 'lsbootEmbeddedLocalDiskImagePath',
                                'lsbootEmbeddedLocalLunImage', 'lsbootIScsi', 'lsbootIScsiImagePath', 'lsbootLan',
                                'lsbootLanImagePath', 'lsbootLocalDiskImage', 'lsbootLocalDiskImagePath',
                                'lsbootLocalHddImage', 'lsbootLocalLunImagePath', 'lsbootNvme', 'lsbootPolicy',
                                'lsbootSan', 'lsbootSanCatSanImage', 'lsbootSanCatSanImagePath', 'lsbootStorage',
                                'lsbootUEFIBootParam', 'lsbootUsbExternalImage', 'lsbootUsbFlashStorageImage',
                                'lsbootUsbInternalImage', 'lsbootVirtualMedia', 'lsmaintMaintPolicy',
                                'lstorageControllerDef', 'lstorageControllerModeConfig', 'lstorageControllerRef',
                                'lstorageDasScsiLun', 'lstorageDiskGroupConfigPolicy', 'lstorageDiskGroupQualifier',
                                'lstorageDiskSlot', 'lstorageDiskZoningPolicy', 'lstorageLocal',
                                'lstorageLocalDiskConfigRef', 'lstorageLogin', 'lstorageLunSetConfig',
                                'lstorageProfile', 'lstorageProfileBinding', 'lstorageRemote',
                                'lstorageSasExpanderConfigPolicy', 'lstorageVirtualDriveDef', 'macpoolBlock',
                                'macpoolPool', 'memoryQual', 'mgmtBackupExportExtPolicy', 'mgmtBackupPolicy',
                                'mgmtCfgExportPolicy', 'mgmtIPv6IfAddr', 'mgmtInbandProfile', 'networkElement',
                                'nwctrlDefinition', 'orgOrg', 'policyCommunication', 'policyConfigBackup',
                                'policyControlEp', 'policyDateTime', 'policyDns', 'policyEquipment', 'policyFault',
                                'policyInfraFirmware', 'policyMEp', 'policyMonitoring', 'policyPortConfig',
                                'policyPowerMgmt', 'policyPsu', 'policySecurity', 'powerGroupQual', 'powerMgmtPolicy',
                                'powerPolicy', 'processorQual', 'qosclassEthBE', 'qosclassEthClassified', 'qosclassFc',
                                'qosclassSlowDrain', 'solPolicy', 'statsThrFloatDefinition', 'statsThrFloatValue',
                                'statsThresholdClass', 'statsThresholdPolicy', 'storageConnectionPolicy',
                                'storageFcTargetEp', 'storageIniGroup', 'storageInitiator',
                                'storageLocalDiskConfigPolicy', 'storageQual', 'storageVsanRef',
                                'sysdebugBackupBehavior', 'sysdebugMEpLogPolicy', 'topInfoPolicy', 'uuidpoolBlock',
                                'uuidpoolPool', 'vnicConnDef', 'vnicDynamicConPolicy', 'vnicDynamicConPolicyRef',
                                'vnicEther', 'vnicEtherIf', 'vnicFc', 'vnicFcGroupDef', 'vnicFcIf', 'vnicFcNode',
                                'vnicIPv4Dhcp', 'vnicIPv4If', 'vnicIPv4PooledIscsiAddr', 'vnicIScsi',
                                'vnicIScsiAutoTargetIf', 'vnicIScsiBootParams', 'vnicIScsiBootVnic', 'vnicIScsiLCP',
                                'vnicIScsiNode', 'vnicIScsiStaticTargetIf', 'vnicIpV4MgmtPooledAddr',
                                'vnicIpV6MgmtPooledAddr', 'vnicLanConnPolicy', 'vnicLanConnTempl', 'vnicLun',
                                'vnicSanConnPolicy', 'vnicSanConnTempl', 'vnicUsnicConPolicyRef', 'vnicVhbaBehPolicy',
                                'vnicVlan', 'vnicVmqConPolicyRef', 'vnicVnicBehPolicy'] + bios_sdk_objects_to_fetch

        self.logger(level="debug", message="Fetching UCS System SDK objects for config")
        failed_to_fetch = []
        for sdk_object_name in sdk_objects_to_fetch:
            try:
                self.sdk_objects[sdk_object_name] = self.handle.query_classid(sdk_object_name)
            except (UcsException, ImcException) as err:
                if err.error_code == "ERR-xml-parse-error" and "no class named " + sdk_object_name in err.error_descr:
                    self.logger(level="debug", message="No UCS class named " + sdk_object_name)
                else:
                    self.logger(level="error", message="Error while trying to fetch UCS class " + sdk_object_name +
                                                       ": " + str(err))
                    failed_to_fetch.append(sdk_object_name)
            except ConnectionRefusedError:
                self.logger(level="error", message="Error while communicating with UCS class " + sdk_object_name +
                                                   ": Connection refused")
            except urllib.error.URLError:
                self.logger(level="error", message="Timeout error while fetching UCS class " + sdk_object_name)
                failed_to_fetch.append(sdk_object_name)
            except http.client.RemoteDisconnected:
                self.logger(level="error", message="Connection closed while fetching UCS class " + sdk_object_name)
                failed_to_fetch.append(sdk_object_name)

        # We retry all SDK objects that failed to fetch properly
        if failed_to_fetch:
            for sdk_object_name in failed_to_fetch:
                self.logger(level="info", message="Retrying to fetch " + sdk_object_name)
                try:
                    self.sdk_objects[sdk_object_name] = self.handle.query_classid(sdk_object_name)
                    failed_to_fetch.remove(sdk_object_name)
                except (UcsException, ImcException) as err:
                    self.logger(level="error", message="Error while trying to fetch UCS System class " +
                                                       sdk_object_name + ": " + str(err))
                except ConnectionRefusedError:
                    self.logger(level="error", message="Error while communicating with UCS class " +
                                                       sdk_object_name + ": Connection refused")
                except urllib.error.URLError:
                    self.logger(level="error", message="Timeout error while fetching UCS class " + sdk_object_name)

        # In case we still have SDK objects that failed to fetch, we list them in a warning message
        if failed_to_fetch:
            for sdk_object_name in failed_to_fetch:
                self.logger(level="warning", message="Impossible to fetch " + sdk_object_name + " after 2 attempts.")

        # We sort all sdk objects by their DN in human readable format
        for key, value in self.sdk_objects.items():
            value.sort(key=lambda obj: [int(t) if t.isdigit() else t.lower() for t in re.split('(\d+)', obj.dn)])


class UcsImcConfig(GenericUcsConfig):
    def __init__(self, parent=None):
        self.adapter_cards = []
        self.admin_networking = []
        self.bios_settings = []
        self.boot_order_properties = []
        self.chassis_inventory = []
        self.communications_services = []
        self.dynamic_storage_zoning = []
        self.ip_blocking_properties = []
        self.ip_filtering_properties = []
        self.ldap_settings = []
        self.local_users = []
        self.local_users_properties = []
        self.platform_event_filters = []
        self.power_cap_configuration = []
        self.power_policies = []
        self.secure_key_management = []
        self.serial_over_lan_properties = []
        self.server_properties = []
        self.smtp_properties = []
        self.snmp = []
        self.storage_controllers = []
        self.storage_flex_flash_controllers = []
        self.timezone_mgmt = []
        self.virtual_kvm_properties = []
        self.virtual_media = []
        GenericUcsConfig.__init__(self, parent=parent)

        # List of attributes to be exported in a config export
        self.export_list = ['adapter_cards', 'admin_networking', 'bios_settings', 'boot_order_properties',
                            'chassis_inventory', 'communications_services', 'dynamic_storage_zoning',
                            'ip_blocking_properties', 'ip_filtering_properties', 'ldap_settings', 'local_users',
                            'local_users_properties', 'platform_event_filters', 'power_cap_configuration',
                            'power_policies', 'secure_key_management', 'serial_over_lan_properties',
                            'server_properties', 'smtp_properties', 'snmp', 'storage_controllers',
                            'storage_flex_flash_controllers', 'timezone_mgmt', 'virtual_kvm_properties',
                            'virtual_media']

    def _fetch_sdk_objects(self):
        GenericUcsConfig._fetch_sdk_objects(self)

        # List of SDK objects to fetch that are only available in IMC
        sdk_objects_to_fetch = ['aaaLdap', 'aaaLdapRoleGroup', 'aaaUserPasswordExpiration', 'aaaUserPolicy',
                                'adaptorEthCompQueueProfile', 'adaptorEthGenProfile', 'adaptorEthInterruptProfile',
                                'adaptorEthOffloadProfile', 'adaptorEthRecvQueueProfile', 'adaptorEthUSNICProfile',
                                'adaptorEthWorkQueueProfile', 'adaptorExtIpV6RssHashProfile', 'adaptorFcBootTable',
                                'adaptorFcCdbWorkQueueProfile', 'adaptorFcErrorRecoveryProfile', 'adaptorFcGenProfile',
                                'adaptorFcInterruptProfile', 'adaptorFcPortFLogiProfile', 'adaptorFcPortPLogiProfile',
                                'adaptorFcPortProfile', 'adaptorFcRecvQueueProfile', 'adaptorFcWorkQueueProfile',
                                'adaptorGenProfile', 'adaptorHostEthIf', 'adaptorHostFcIf', 'adaptorIpV4RssHashProfile',
                                'adaptorIpV6RssHashProfile', 'adaptorRssProfile', 'adaptorUnit', 'advancedPowerProfile',
                                'biosVfAdjacentCacheLinePrefetch', 'biosVfAltitude', 'biosVfAutonumousCstateEnable',
                                'biosVfBootPerformanceMode', 'biosVfCDNEnable', 'biosVfCPUEnergyPerformance',
                                'biosVfCPUPerformance', 'biosVfCPUPowerManagement', 'biosVfCmciEnable',
                                'biosVfConsoleRedirection', 'biosVfCoreMultiProcessing', 'biosVfDCUPrefetch',
                                'biosVfDemandScrub', 'biosVfDirectCacheAccess', 'biosVfEnhancedIntelSpeedStepTech',
                                'biosVfExecuteDisableBit', 'biosVfExtendedAPIC', 'biosVfFRB2Enable', 'biosVfHWPMEnable',
                                'biosVfHardwarePrefetch', 'biosVfIntelHyperThreadingTech', 'biosVfIntelTurboBoostTech',
                                'biosVfIntelVTForDirectedIO', 'biosVfIntelVirtualizationTechnology',
                                'biosVfLOMPortOptionROM', 'biosVfLegacyUSBSupport', 'biosVfMemoryInterleave',
                                'biosVfMemoryMappedIOAbove4GB', 'biosVfNUMAOptimized', 'biosVfOSBootWatchdogTimer',
                                'biosVfOSBootWatchdogTimerPolicy', 'biosVfOSBootWatchdogTimerTimeout',
                                'biosVfOSBootWatchdogTimerTimeout', 'biosVfOutOfBandMgmtPort', 'biosVfPCIOptionROMs',
                                'biosVfPCISlotOptionROMEnable', 'biosVfPCIeSSDHotPlugSupport', 'biosVfPStateCoordType',
                                'biosVfPackageCStateLimit', 'biosVfPatrolScrub', 'biosVfPchUsb30Mode',
                                'biosVfPciRomClp', 'biosVfPowerOnPasswordSupport', 'biosVfProcessorC1E',
                                'biosVfProcessorC3Report', 'biosVfProcessorC6Report', 'biosVfPwrPerfTuning',
                                'biosVfQPIConfig', 'biosVfQpiSnoopMode', 'biosVfResumeOnACPowerLoss',
                                'biosVfSataModeSelect', 'biosVfSelectMemoryRASConfiguration', 'biosVfSrIov',
                                'biosVfTPMSupport', 'biosVfUSBEmulation', 'biosVfUSBPortsConfig',
                                'biosVfUsbXhciSupport', 'biosVfVgaPriority', 'biosVfWorkLoadConfig', 'commHttp',
                                'commHttps', 'commIpmiLan', 'commKvm', 'commMailAlert', 'commRedfish',
                                'commSavedVMediaMap', 'commSnmp', 'commSsh', 'commVMedia', 'commVMediaMap',
                                'computeRackUnit', 'computeServerRef', 'equipmentChassis', 'fanPolicy', 'ipBlocking',
                                'ipFiltering', 'kmipServerLogin', 'ldapCACertificateManagement', 'lsbootDef',
                                'lsbootDevPrecision', 'lsbootEfi', 'lsbootHdd', 'lsbootIscsi', 'lsbootLan',
                                'lsbootNVMe', 'lsbootPchStorage', 'lsbootPxe', 'lsbootSan', 'lsbootSd', 'lsbootStorage',
                                'lsbootUefiShell', 'lsbootUsb', 'lsbootVMedia', 'lsbootVirtualMedia', 'mailRecipient',
                                'memoryArray', 'mgmtIf', 'oneTimePrecisionBootDevice', 'platformEventFilters',
                                'powerBudget', 'selfEncryptStorageController', 'solIf', 'standardPowerProfile',
                                'storageController', 'storageFlexFlashOperationalProfile',
                                'storageFlexFlashPhysicalDrive', 'storageFlexFlashVirtualDrive',
                                'storageFlexFlashController', 'storageLocalDisk', 'storageLocalDiskUsage',
                                'storageVirtualDrive']

        self.logger(level="debug", message="Fetching UCS IMC SDK objects for config")
        failed_to_fetch = []
        for sdk_object_name in sdk_objects_to_fetch:
            try:
                self.sdk_objects[sdk_object_name] = self.handle.query_classid(sdk_object_name)
            except (UcsException, ImcException) as err:
                if err.error_code == "ERR-xml-parse-error" and "no class named " + sdk_object_name in err.error_descr:
                    self.logger(level="debug", message="No UCS IMC class named " + sdk_object_name)
                else:
                    self.logger(level="error", message="Error while trying to fetch UCS IMC class " + sdk_object_name +
                                                       ": " + str(err))
                    failed_to_fetch.append(sdk_object_name)
            except ConnectionRefusedError:
                self.logger(level="error", message="Error while communicating with UCS IMC class " + sdk_object_name +
                                                   ": Connection refused")
            except urllib.error.URLError:
                self.logger(level="error", message="Timeout error while fetching UCS IMC class " + sdk_object_name)
                failed_to_fetch.append(sdk_object_name)
            # Prevent rare exception due to Server Error return when fetching UCS IMC class
            except xml.etree.ElementTree.ParseError as err:
                self.logger(level="error", message="Error while trying to fetch UCS IMC class " + sdk_object_name +
                                                   ": " + str(err))

        # We retry all SDK objects that failed to fetch properly
        if failed_to_fetch:
            for sdk_object_name in failed_to_fetch:
                self.logger(level="info", message="Retrying to fetch " + sdk_object_name)
                try:
                    self.sdk_objects[sdk_object_name] = self.handle.query_classid(sdk_object_name)
                    failed_to_fetch.remove(sdk_object_name)
                except (UcsException, ImcException) as err:
                    self.logger(level="error", message="Error while trying to fetch UCS IMC class " +
                                                       sdk_object_name + ": " + str(err))
                except ConnectionRefusedError:
                    self.logger(level="error", message="Error while communicating with UCS IMC class " +
                                                       sdk_object_name + ": Connection refused")
                except urllib.error.URLError:
                    self.logger(level="error", message="Timeout error while fetching UCS IMC class " + sdk_object_name)

        # In case we still have SDK objects that failed to fetch, we list them in a warning message
        if failed_to_fetch:
            for sdk_object_name in failed_to_fetch:
                self.logger(level="warning", message="Impossible to fetch " + sdk_object_name + " after 2 attempts.")


class UcsCentralConfig(GenericUcsConfig):
    def __init__(self, parent=None):
        self.orgs = []
        self.domain_groups = []

        GenericUcsConfig.__init__(self, parent=parent)

        # List of attributes to be exported in a config export
        self.export_list = ['orgs', 'domain_groups']

    def _fetch_sdk_objects(self):
        GenericUcsConfig._fetch_sdk_objects(self)

        # List of SDK objects to fetch that are only available in Central
        sdk_objects_to_fetch = ['orgOrg', 'macpoolPool', 'macpoolBlock', 'fcpoolInitiators', 'fcpoolBlock',
                                'uuidpoolPool', 'uuidpoolBlock', 'orgDomainGroup', 'fabricVlanReq', 'fabricVlan',
                                'fabricNetGroup', 'fabricPooledVlan', 'fabricNetGroupReq', 'ippoolPool',
                                'ippoolBlock', 'ippoolIpV6Block']

        self.logger(level="debug", message="Fetching UCS Central SDK objects for config")
        failed_to_fetch = []
        for sdk_object_name in sdk_objects_to_fetch:
            try:
                self.sdk_objects[sdk_object_name] = self.handle.query_classid(sdk_object_name)
            except UcscException as err:
                if err.error_code == "ERR-xml-parse-error" and "no class named " + sdk_object_name in err.error_descr:
                    self.logger(level="debug", message="No UCS Central class named " + sdk_object_name)
                else:
                    self.logger(level="error", message="Error while trying to fetch UCS Central class " +
                                                       sdk_object_name + ": " + str(err))
                    failed_to_fetch.append(sdk_object_name)
            except ConnectionRefusedError:
                self.logger(level="error", message="Error while communicating with UCS Central class " +
                                                   sdk_object_name + ": Connection refused")
            except urllib.error.URLError:
                self.logger(level="error", message="Timeout error while fetching UCS Central class " + sdk_object_name)
                failed_to_fetch.append(sdk_object_name)

        # We retry all SDK objects that failed to fetch properly
        if failed_to_fetch:
            for sdk_object_name in failed_to_fetch:
                self.logger(level="info", message="Retrying to fetch " + sdk_object_name)
                try:
                    self.sdk_objects[sdk_object_name] = self.handle.query_classid(sdk_object_name)
                    failed_to_fetch.remove(sdk_object_name)
                except UcscException as err:
                    self.logger(level="error", message="Error while trying to fetch UCS Central class " +
                                                       sdk_object_name + ": " + str(err))
                except ConnectionRefusedError:
                    self.logger(level="error", message="Error while communicating with UCS Central class " +
                                                       sdk_object_name + ": Connection refused")
                except urllib.error.URLError:
                    self.logger(level="error", message="Timeout error while fetching UCS Central class " +
                                                       sdk_object_name)

        # In case we still have SDK objects that failed to fetch, we list them in a warning message
        if failed_to_fetch:
            for sdk_object_name in failed_to_fetch:
                self.logger(level="warning", message="Impossible to fetch " + sdk_object_name + " after 2 attempts.")
