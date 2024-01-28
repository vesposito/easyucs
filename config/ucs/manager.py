# coding: utf-8
# !/usr/bin/env python

""" manager.py: Easy UCS Deployment Tool """

import copy
import re
import time
import urllib

from imcsdk.imchandle import ImcHandle
from ucsmsdk.mometa.fabric.FabricEthLanEp import FabricEthLanEp
from ucsmsdk.ucsexception import UcsException
from ucsmsdk.ucshandle import UcsHandle

import common
from __init__ import __version__
from config.manager import GenericConfigManager
from config.plot import UcsSystemOrgConfigPlot, UcsSystemServiceProfileConfigPlot
from config.ucs.cimc.imc import UcsImcAdapterCard, UcsImcAdminNetwork, UcsImcBios, UcsImcBootOrder, \
    UcsImcChassisInventory, UcsImcCommunicationsServices, UcsImcDynamicStorageZoning, UcsImcIpBlockingProperties, \
    UcsImcIpFilteringProperties, UcsImcLdap, UcsImcLocalUser, UcsImcLocalUsersProperties, UcsImcLoggingControls, \
    UcsImcPlatformEventFilter, UcsImcPowerCapConfiguration, UcsImcPowerPolicies, UcsImcSecureKeyManagement, \
    UcsImcSerialOverLanProperties, UcsImcServerProperties, UcsImcSmtpProperties, UcsImcSnmp, UcsImcStorageController, \
    UcsImcStorageFlexFlashController, UcsImcTimezoneMgmt, UcsImcVirtualMedia, UcsImcVKvmProperties
from config.ucs.config import UcsImcConfig, UcsSystemConfig, UcsCentralConfig
from config.ucs.device_connector import UcsDeviceConnector
from config.ucs.ucsc.domain_groups import UcsCentralDomainGroup
from config.ucs.ucsc.orgs import UcsCentralOrg
from config.ucs.ucsc.system import UcsCentralDateTimeMgmt, UcsCentralDns, UcsCentralLocalUser, UcsCentralLocale, \
    UcsCentralManagementInterface, UcsCentralPasswordProfile, UcsCentralRole, UcsCentralSnmp, UcsCentralSyslog, \
    UcsCentralSystem
from config.ucs.ucsm.admin import UcsSystemAuthentication, UcsSystemBackupExportPolicy, UcsSystemCallHome, \
    UcsSystemUcsCentral, UcsSystemCommunicationServices, UcsSystemDns, UcsSystemFaultPolicy, UcsSystemGlobalPolicies, \
    UcsSystemInformation, UcsSystemKmipCertificationPolicy, UcsSystemLdap, UcsSystemLocalUser, \
    UcsSystemLocalUsersProperties, UcsSystemLocale, UcsSystemManagementInterface, UcsSystemOrg, \
    UcsSystemPortAutoDiscoveryPolicy, UcsSystemPreLoginBanner, UcsSystemRadius, UcsSystemRole, UcsSystemSelPolicy, \
    UcsSystemSwitchingMode, UcsSystemSyslog, UcsSystemTacacs, UcsSystemTimezoneMgmt
from config.ucs.ucsm.lan import UcsSystemApplianceNetworkControlPolicy, UcsSystemApplianceVlan, UcsSystemLanPinGroup, \
    UcsSystemLanTrafficMonitoringSession, UcsSystemLinkProfile, UcsSystemNetflowMonitoring, UcsSystemQosSystemClass, \
    UcsSystemSlowDrainTimers, UcsSystemUdldLinkPolicy, UcsSystemVlan, UcsSystemVlanGroup
from config.ucs.ucsm.ports import UcsSystemLanUplinkPort, UcsSystemAppliancePort, UcsSystemServerPort, \
    UcsSystemLanPortChannel, UcsSystemAppliancePortChannel, UcsSystemBreakoutPort, UcsSystemUnifiedStoragePort, \
    UcsSystemUnifiedUplinkPort, UcsSystemFcoeUplinkPort, UcsSystemFcoeStoragePort, UcsSystemSanPortChannel, \
    UcsSystemFcoePortChannel, UcsSystemSanUplinkPort, UcsSystemSanStoragePort, UcsSystemSanUnifiedPort
from config.ucs.ucsm.san import UcsSystemFcZoneProfile, UcsSystemSanPinGroup, UcsSystemSanTrafficMonitoringSession, \
    UcsSystemStorageVsan, UcsSystemVsan


class GenericUcsConfigManager(GenericConfigManager):
    def __init__(self, parent=None):
        GenericConfigManager.__init__(self, parent=parent)

    def _get_service_profiles_hierarchy(self, config_orgs, output_json_orgs):
        """
        Recursively fetches all the service profiles from all the orgs
        :returns: nothing
        """
        for org in config_orgs:
            json_org = {
                "org_name": org.name
            }
            if org.descr:
                json_org["descr"] = org.descr
            if org.service_profiles:
                json_org["service_profiles"] = []
                for service_profile in org.service_profiles:
                    dict_service_profile = {}
                    for field in ["asset_tag", "assigned_server", "name", "policy_owner", "service_profile_template",
                                  "type", "user_label"]:
                        if field == "assigned_server":
                            if hasattr(service_profile, "operational_state") and getattr(service_profile,
                                                                                         "operational_state"):
                                if field in service_profile.operational_state and \
                                        service_profile.operational_state[field]:
                                    dict_service_profile[field] = copy.copy(service_profile.operational_state[field])
                                    for key in service_profile.operational_state[field]:
                                        if not dict_service_profile[field][key]:
                                            dict_service_profile[field].pop(key)
                        elif hasattr(service_profile, field) and getattr(service_profile, field):
                            dict_service_profile[field] = getattr(service_profile, field)
                    json_org["service_profiles"].append(dict_service_profile)

            output_json_orgs.append(json_org)
            if org.orgs:
                json_org["orgs"] = []
                self._get_service_profiles_hierarchy(org.orgs, json_org["orgs"])

                # Removing the orgs which does not have sub-orgs and profiles
                indexes_to_be_removed = []
                for index in range(len(json_org["orgs"])):
                    if "orgs" not in json_org["orgs"][index] and "service_profiles" not in json_org["orgs"][index]:
                        indexes_to_be_removed.append(index)
                for index in sorted(indexes_to_be_removed, reverse=True):
                    del json_org["orgs"][index]
                if not json_org["orgs"]:
                    del json_org["orgs"]

    def get_profiles(self, config=None):
        """
        List all Service Profiles from a given config with some of their key attributes
        :param config: The config from which all the service profiles/templates needs to be obtained
        :return: All service profiles/templates from the config, [] otherwise
        """
        if config is None:
            self.logger(level="error", message="Missing config in get service profiles request!")
            return None

        service_profiles_hierarchy = []
        self._get_service_profiles_hierarchy(config.orgs, service_profiles_hierarchy)

        return service_profiles_hierarchy

    def export_config_plots(self, config=None, export_format="png", directory=None):
        pass

    def generate_config_plots(self, config=None):
        pass


class UcsSystemConfigManager(GenericUcsConfigManager):
    def __init__(self, parent=None):
        GenericUcsConfigManager.__init__(self, parent=parent)
        self.config_class_name = UcsSystemConfig

    def check_if_push_config_requires_reboot(self, uuid=None):
        """
        Checks if the specified config will require at least one reboot when pushed to the live system
        :param uuid: The UUID of the config to be pushed. If not specified, the most recent config will be used
        :return: True if config push will require at least one reboot, False otherwise
        """
        # FIXME: Instead of returning True, return the number of reboots required + where they are needed
        # FIXME: This will be useful for setting the progress bar more precisely

        if uuid is None:
            self.logger(level="debug", message="No config UUID specified in config push request. Using latest.")
            config = self.get_latest_config()
        else:
            # Find the config that needs to be pushed
            config_list = [config for config in self.config_list if config.uuid == uuid]
            if len(config_list) != 1:
                self.logger(level="error", message="Failed to locate config with UUID " + str(uuid) + " for push")
                return False
            else:
                config = config_list[0]

        if config:
            # We first make sure we are connected to the device
            self.parent.connect(bypass_version_checks=True)
            # FIXME: if only checking for config reboot, need to disconnect from device at the end

            if config.check_if_ports_config_requires_reboot():
                self.logger(level="warning", message="Config will require reboot because of port type changes")
                return True

            if config.check_if_switching_mode_config_requires_reboot():
                self.logger(level="warning", message="Config will require reboot because of switching mode changes")
                return True

        else:
            self.logger(level="error", message="No config to check for reboot!")
            return False

    def export_config_plots(self, config=None, export_format="png", directory=None):
        if directory is None:
            self.logger(level="debug",
                        message="No directory specified in export config plots request. Using local folder.")
            directory = "."

        if config is None:
            config = self.get_latest_config()
            self.logger(level="debug", message="No config UUID specified in export config plots request. Using latest.")

            if config is None:
                self.logger(level="error", message="No config found. Unable to export plots.")
                return False

        if config.service_profile_plots:
            config.service_profile_plots.export_plots(export_format=export_format, directory=directory)
        if config.orgs_plot:
            config.orgs_plot.export_plots(export_format=export_format, directory=directory)
        if not config.orgs_plot and not config.service_profile_plots:
            self.logger(level="error", message="No plots found. Unable to export plots.")
            return False

        return True

    def fetch_config(self, force=False):
        self.logger(message="Fetching config from live device (can take several minutes)")
        config = UcsSystemConfig(parent=self)
        config.metadata.origin = "live"
        config.metadata.easyucs_version = __version__
        config.load_from = "live"
        config._fetch_sdk_objects(force=force)

        # If any of the mandatory tasksteps fails then return None
        from api.api_server import easyucs
        if easyucs and self.parent.task and \
                easyucs.task_manager.is_any_taskstep_failed(uuid=self.parent.task.metadata.uuid):
            self.logger(level="error", message="Failed to fetch one or more SDK objects. Stopping the config fetch.")
            return None

        self.logger(level="debug", message="Finished fetching UCS SDK objects for config")

        # Put in order the items to append
        config.system.append(UcsSystemInformation(parent=config))
        config.pre_login_banner = UcsSystemPreLoginBanner(parent=config).message

        config.timezone_mgmt.append(UcsSystemTimezoneMgmt(parent=config))
        # In case Timezone Mgmt is empty, we remove it to avoid having an empty object in the config
        if not config.timezone_mgmt[0].zone and not config.timezone_mgmt[0].ntp:
            config.timezone_mgmt = []

        config.switching_mode.append(UcsSystemSwitchingMode(parent=config))
        config.communication_services.append(UcsSystemCommunicationServices(parent=config))
        device_connector = UcsDeviceConnector(parent=config)
        if device_connector.intersight_url:
            config.device_connector.append(device_connector)
        if "faultPolicy" in config.sdk_objects:
            config.global_fault_policy.append(
                UcsSystemFaultPolicy(parent=config, fault_policy=config.sdk_objects["faultPolicy"][0]))
        config.syslog.append(UcsSystemSyslog(parent=config))
        config.radius.append(UcsSystemRadius(parent=config))
        config.tacacs.append(UcsSystemTacacs(parent=config))
        config.ldap.append(UcsSystemLdap(parent=config))
        config.authentication.append(UcsSystemAuthentication(parent=config))
        config.call_home.append(UcsSystemCallHome(parent=config))
        config.backup_export_policy.append(UcsSystemBackupExportPolicy(parent=config))
        config.global_policies.append(UcsSystemGlobalPolicies(parent=config))
        config.dns.extend(UcsSystemDns(parent=config).dns)
        if "mgmtKmipCertPolicy" in config.sdk_objects:
            if config.sdk_objects["mgmtKmipCertPolicy"]:
                config.kmip_client_cert_policy.append(UcsSystemKmipCertificationPolicy(parent=config))
        config.local_users_properties.append(UcsSystemLocalUsersProperties(parent=config))
        config.sel_policy.append(UcsSystemSelPolicy(parent=config))
        if "computePortDiscPolicy" in config.sdk_objects:
            config.port_auto_discovery_policy.append(UcsSystemPortAutoDiscoveryPolicy(
                parent=config, compute_port_disc_policy=config.sdk_objects["computePortDiscPolicy"][0]))

        if "qosclassSlowDrain" in config.sdk_objects:
            if config.sdk_objects["qosclassSlowDrain"]:
                config.slow_drain_timers.append(UcsSystemSlowDrainTimers(parent=config))

        for ucs_central in config.sdk_objects['policyControlEp']:
            config.ucs_central.append(UcsSystemUcsCentral(parent=config))

        for network_element in config.sdk_objects["networkElement"]:
            config.management_interfaces.append(UcsSystemManagementInterface(parent=config,
                                                                             network_element=network_element))

        for aaa_locale in config.sdk_objects['aaaLocale']:
            config.locales.append(UcsSystemLocale(parent=config, aaa_locale=aaa_locale))

        for aaa_role in config.sdk_objects["aaaRole"]:
            config.roles.append(UcsSystemRole(parent=config, aaa_role=aaa_role))

        for aaa_user in config.sdk_objects["aaaUser"]:
            # We except users that have been automatically pushed by UCS Central for cross-launch authentication since
            # they are for internal use. They begin with "ucsc_".
            if hasattr(aaa_user, "name"):
                if aaa_user.name.startswith("ucsc_"):
                    self.logger(level="debug", message="Ignoring Local User " + aaa_user.name +
                                                       " since it has been pushed by UCS Central")
                else:
                    config.local_users.append(UcsSystemLocalUser(parent=config, aaa_user=aaa_user))

        for qos_class in list(config.sdk_objects["qosclassEthClassified"] + config.sdk_objects["qosclassFc"] +
                              config.sdk_objects["qosclassEthBE"]):
            config.qos_system_class.append(UcsSystemQosSystemClass(parent=config, qos_class=qos_class))

        if "fabricFcZoneProfile" in config.sdk_objects:
            for fabric_fc_zone_profile in config.sdk_objects["fabricFcZoneProfile"]:
                config.fc_zone_profiles.append(UcsSystemFcZoneProfile(parent=config,
                                                                      fabric_fc_zone_profile=fabric_fc_zone_profile))

        for fabric_udld_link_policy in config.sdk_objects["fabricUdldLinkPolicy"]:
            config.udld_link_policies.append(UcsSystemUdldLinkPolicy(parent=config,
                                                                     fabric_udld_link_policy=fabric_udld_link_policy))

        for fabric_eth_link_profile in config.sdk_objects["fabricEthLinkProfile"]:
            config.link_profiles.append(UcsSystemLinkProfile(parent=config,
                                                             fabric_eth_link_profile=fabric_eth_link_profile))

        for nwctrl_definition in config.sdk_objects["nwctrlDefinition"]:
            if nwctrl_definition.dn.startswith("fabric/eth-estc"):
                config.appliance_network_control_policies.append(
                    UcsSystemApplianceNetworkControlPolicy(parent=config, nwctrl_definition=nwctrl_definition))

        # Port configuration
        # We start with Unified Uplink & Unified Storage ports, as those are special and group 2 roles in 1
        for ether_pio in config.sdk_objects["etherPIo"]:
            if ether_pio.if_role == "network-fcoe-uplink":
                config.unified_uplink_ports.append(UcsSystemUnifiedUplinkPort(parent=config, ether_pio=ether_pio))

        for ether_pio in config.sdk_objects["etherPIo"]:
            if ether_pio.if_role == "fcoe-nas-storage":
                config.unified_storage_ports.append(UcsSystemUnifiedStoragePort(parent=config, ether_pio=ether_pio))

        for fabric_eth_lan_ep in config.sdk_objects["fabricEthLanEp"]:
            config.lan_uplink_ports.append(UcsSystemLanUplinkPort(parent=config, fabric_eth_lan_ep=fabric_eth_lan_ep))

        # We remove LAN Uplink ports that are already part of Unified Uplink ports
        for unified_uplink_port in config.unified_uplink_ports:
            for lan_uplink_port in config.lan_uplink_ports:
                if (unified_uplink_port.fabric == lan_uplink_port.fabric) & (
                        unified_uplink_port.slot_id == lan_uplink_port.slot_id) & (
                        unified_uplink_port.port_id == lan_uplink_port.port_id) & (
                        unified_uplink_port.aggr_id == lan_uplink_port.aggr_id):
                    config.lan_uplink_ports.remove(lan_uplink_port)

        # We also add server ports that are part of a port-channel (fabricDceSwSrvPcEp) since they are auto created
        for fabric_dce_sw_srv_ep in sorted(config.sdk_objects["fabricDceSwSrvEp"] +
                                           config.sdk_objects["fabricDceSwSrvPcEp"],
                                           key=lambda port: [int(t) if t.isdigit() else t.lower()
                                                             for t in re.split('(\d+)', port.dn)]):
            config.server_ports.append(UcsSystemServerPort(parent=config, fabric_dce_sw_srv_ep=fabric_dce_sw_srv_ep))

        for fabric_eth_estc_ep in config.sdk_objects["fabricEthEstcEp"]:
            config.appliance_ports.append(UcsSystemAppliancePort(parent=config, fabric_eth_estc_ep=fabric_eth_estc_ep))

        # We remove Appliance ports that are already part of Unified Storage ports
        for unified_storage_port in config.unified_storage_ports:
            for appliance_port in config.appliance_ports:
                if (unified_storage_port.fabric == appliance_port.fabric) & (
                        unified_storage_port.slot_id == appliance_port.slot_id) & (
                        unified_storage_port.port_id == appliance_port.port_id) & (
                        unified_storage_port.aggr_id == appliance_port.aggr_id):
                    config.appliance_ports.remove(appliance_port)

        for fabric_vlan in config.sdk_objects["fabricVlan"]:
            if fabric_vlan.dn.startswith("fabric/lan"):
                config.vlans.append(UcsSystemVlan(parent=config, fabric_vlan=fabric_vlan))
            elif fabric_vlan.dn.startswith("fabric/eth-estc"):
                config.appliance_vlans.append(UcsSystemApplianceVlan(parent=config, fabric_vlan=fabric_vlan))

        for fabric_fc_san_ep in config.sdk_objects["fabricFcSanEp"]:
            config.san_uplink_ports.append(UcsSystemSanUplinkPort(parent=config, fabric_fc_san_ep=fabric_fc_san_ep))

        for fabric_fc_estc_ep in config.sdk_objects["fabricFcEstcEp"]:
            config.san_storage_ports.append(UcsSystemSanStoragePort(parent=config, fabric_fc_estc_ep=fabric_fc_estc_ep))

        for fabric_fcoe_san_ep in config.sdk_objects["fabricFcoeSanEp"]:
            config.fcoe_uplink_ports.append(UcsSystemFcoeUplinkPort(parent=config,
                                                                    fabric_fcoe_san_ep=fabric_fcoe_san_ep))

        # We remove FCoE Uplink ports that are already part of Unified Uplink ports
        for unified_uplink_port in config.unified_uplink_ports:
            for fcoe_uplink_port in config.fcoe_uplink_ports:
                if (unified_uplink_port.fabric == fcoe_uplink_port.fabric) & (
                        unified_uplink_port.slot_id == fcoe_uplink_port.slot_id) & (
                        unified_uplink_port.port_id == fcoe_uplink_port.port_id) & (
                        unified_uplink_port.aggr_id == fcoe_uplink_port.aggr_id):
                    config.fcoe_uplink_ports.remove(fcoe_uplink_port)

        for fabric_fcoe_estc_ep in config.sdk_objects["fabricFcoeEstcEp"]:
            config.fcoe_storage_ports.append(UcsSystemFcoeStoragePort(parent=config,
                                                                      fabric_fcoe_estc_ep=fabric_fcoe_estc_ep))

        # We remove FCoE Storage ports that are already part of Unified Storage ports
        for unified_storage_port in config.unified_storage_ports:
            for fcoe_storage_port in config.fcoe_storage_ports:
                if (unified_storage_port.fabric == fcoe_storage_port.fabric) & (
                        unified_storage_port.slot_id == fcoe_storage_port.slot_id) & (
                        unified_storage_port.port_id == fcoe_storage_port.port_id) & (
                        unified_storage_port.aggr_id == fcoe_storage_port.aggr_id):
                    config.fcoe_storage_ports.remove(fcoe_storage_port)

        for fabric_vsan in config.sdk_objects["fabricVsan"]:
            if fabric_vsan.dn.startswith("fabric/san"):
                config.vsans.append(UcsSystemVsan(parent=config, fabric_vsan=fabric_vsan))
            elif fabric_vsan.dn.startswith("fabric/fc-estc"):
                config.storage_vsans.append(UcsSystemStorageVsan(parent=config, fabric_vsan=fabric_vsan))

        for fabric_eth_lan_pc in config.sdk_objects["fabricEthLanPc"]:
            config.lan_port_channels.append(UcsSystemLanPortChannel(parent=config, fabric_eth_lan_pc=fabric_eth_lan_pc))

        for fabric_fcoe_san_pc in config.sdk_objects["fabricFcoeSanPc"]:
            config.fcoe_port_channels.append(
                UcsSystemFcoePortChannel(parent=config, fabric_fcoe_san_pc=fabric_fcoe_san_pc))

        for fabric_fc_san_pc in config.sdk_objects["fabricFcSanPc"]:
            config.san_port_channels.append(
                UcsSystemSanPortChannel(parent=config, fabric_fc_san_pc=fabric_fc_san_pc))

        for fabric_eth_estc_pc in config.sdk_objects["fabricEthEstcPc"]:
            config.appliance_port_channels.append(UcsSystemAppliancePortChannel(parent=config,
                                                                                fabric_eth_estc_pc=fabric_eth_estc_pc))

        for fabric_net_group in config.sdk_objects["fabricNetGroup"]:
            # We skip specific internal VLAN Groups that are used for VLAN Port Count Optimization feature
            if fabric_net_group.type in ["vlan-compression", "vlan-uncompressed", "vp-compression"]:
                self.logger(level="debug", message="Skipping internal VLAN Group " + fabric_net_group.name)
            else:
                config.vlan_groups.append(UcsSystemVlanGroup(parent=config, fabric_net_group=fabric_net_group))

        for fabric_lan_pin_group in config.sdk_objects["fabricLanPinGroup"]:
            config.lan_pin_groups.append(UcsSystemLanPinGroup(parent=config, fabric_lan_pin_group=fabric_lan_pin_group))

        for fabric_san_pin_group in config.sdk_objects["fabricSanPinGroup"]:
            config.san_pin_groups.append(UcsSystemSanPinGroup(parent=config, fabric_san_pin_group=fabric_san_pin_group))

        if "fabricBreakout" in config.sdk_objects:
            for fabric_breakout in config.sdk_objects["fabricBreakout"]:
                config.breakout_ports.append(UcsSystemBreakoutPort(parent=config, fabric_breakout=fabric_breakout))

                # EASYUCS-1076: It can happen that UCSM shows a port being both configured as Breakout and Server port.
                # We remove the server port config in this case
                for server_port in config.server_ports:
                    if (server_port.fabric == fabric_breakout.dn.split('/')[2]) & (
                            server_port.slot_id == fabric_breakout.slot_id) & (
                            server_port.port_id == fabric_breakout.port_id) & (
                            server_port.aggr_id is None):
                        self.logger(
                            level="warning",
                            message=f"Removed Server Port " +
                                    f"{server_port.fabric}/{server_port.slot_id}/{server_port.port_id} from config " +
                                    f"due to it being also configured as a Breakout Port"
                        )
                        config.server_ports.remove(server_port)

        if "fcPIo" in config.sdk_objects:
            if config.sdk_objects["fcPIo"]:
                fi_a_fc_ports_presence = False
                fi_b_fc_ports_presence = False
                for fc_pio in config.sdk_objects["fcPIo"]:
                    if fc_pio.dn.startswith("sys/switch-A/"):
                        fi_a_fc_ports_presence = True
                    if fc_pio.dn.startswith("sys/switch-B/"):
                        fi_b_fc_ports_presence = True
                # We only add items to the list of unified ports if we have FC ports and we are not using 1st Gen FIs
                if fi_a_fc_ports_presence and self.parent.fi_a_model not in ["N10-S6100", "N10-S6200"]:
                    config.san_unified_ports.append(UcsSystemSanUnifiedPort(parent=config, fabric="A"))
                if fi_b_fc_ports_presence and self.parent.fi_b_model not in ["N10-S6100", "N10-S6200"]:
                    config.san_unified_ports.append(UcsSystemSanUnifiedPort(parent=config, fabric="B"))

        if "fabricEthMon" in config.sdk_objects:
            for fabric_eth_mon in config.sdk_objects["fabricEthMon"]:
                config.lan_traffic_monitoring_sessions.append(
                    UcsSystemLanTrafficMonitoringSession(parent=config, fabric_eth_mon=fabric_eth_mon)
                )

        if "fabricFcMon" in config.sdk_objects:
            for fabric_fc_mon in config.sdk_objects["fabricFcMon"]:
                config.san_traffic_monitoring_sessions.append(
                    UcsSystemSanTrafficMonitoringSession(parent=config, fabric_fc_mon=fabric_fc_mon)
                )

        if "fabricEthLanFlowMonitoring" in config.sdk_objects:
            for fabric_eth_lan_flow_monitoring in config.sdk_objects["fabricEthLanFlowMonitoring"]:
                config.netflow_monitoring.append(
                    UcsSystemNetflowMonitoring(parent=config,
                                               fabric_eth_lan_flow_monitoring=fabric_eth_lan_flow_monitoring)
                )

        for org_org in sorted(config.sdk_objects["orgOrg"], key=lambda org: org.dn):
            if org_org.dn == "org-root":
                config.orgs.append(UcsSystemOrg(parent=config, org_org=org_org))
                break

        # Removing the list of SDK objects fetched from the live UCS device
        config.sdk_objects = None
        self.config_list.append(config)
        self.logger(message="Finished fetching config with UUID " + str(config.uuid) + " from live device")
        return config.uuid

    def generate_config_plots(self, config=None):
        if config is None:
            config = self.get_latest_config()
            self.logger(level="debug",
                        message="No config UUID specified in generate config plots request. Using latest.")

            if config is None:
                self.logger(level="error", message="No config found. Unable to generate config plots.")
                return False

        if self.parent.task is not None:
            self.parent.task.taskstep_manager.start_taskstep(
                name="GenerateReportDrawConfigUcsSystem",
                description="Generating plots for device " + self.parent.target)
        self.logger(level="debug", message="Generating plots for device " + self.parent.target + " using config: " +
                                           str(config.uuid))

        config.service_profile_plots = UcsSystemServiceProfileConfigPlot(parent=self, config=config)
        if config.orgs[0].orgs:  # If 'root' is not the only organization
            config.orgs_plot = UcsSystemOrgConfigPlot(parent=self, config=config)

        if self.parent.task is not None:
            self.parent.task.taskstep_manager.stop_taskstep(
                name="GenerateReportDrawConfigUcsSystem", status="successful",
                status_message="Finished generating plots for device " + self.parent.target)

        return True

    def push_config(self, uuid=None, reset=False, fi_ip_list=[], bypass_version_checks=False, force=False):
        """
        Push the specified config to the live system
        :param uuid: The UUID of the config to be pushed. If not specified, the most recent config will be used
        :param reset: Whether the device must be reset before pushing the config
        :param fi_ip_list: List of DHCP IP addresses taken by each FI after the reset
        :param bypass_version_checks: Whether the minimum version checks should be bypassed when connecting
        :param force: Force the push to proceed even in-case of critical errors.
        :return: True if config push was successful, False otherwise
        """
        if uuid is None:
            self.logger(level="debug", message="No config UUID specified in config push request. Using latest.")
            config = self.get_latest_config()
        else:
            # Find the config that needs to be pushed
            config_list = [config for config in self.config_list if str(config.uuid) == str(uuid)]
            if len(config_list) != 1:
                self.logger(level="error", message="Failed to locate config with UUID " + str(uuid) + " for push")
                return False
            else:
                config = config_list[0]

        if config:
            if reset:
                # Check if the DHCP IP addresses are available before resetting
                if not fi_ip_list:
                    message_str = "No DHCP IP addresses given"
                    self.logger(level="error", message=message_str)
                    return False
                # TODO Check if IP addresses are valid

                # Check if the admin password is available before resetting
                for user in config.local_users:
                    if user.id:
                        if user.id == "admin":
                            if not user.password:
                                # Admin password is a mandatory input
                                message_str = "Reset aborted: Could not find password for user admin in config"
                                self.logger(level="error", message=message_str)
                                return False

                # Performing reset
                self.logger(message="Resetting device " + self.parent.target + " before pushing configuration")
                erase_virtual_drives = False
                erase_flexflash = False
                clear_sel_logs = False
                if 'erase_all_virtual_drives_before_reset' in config.options.keys():
                    if config.options['erase_all_virtual_drives_before_reset'] == "yes":
                        self.logger(message="erase_all_virtual_drives_before_reset option is set")
                        erase_virtual_drives = True
                if 'erase_all_flexflash_before_reset' in config.options.keys():
                    if config.options['erase_all_flexflash_before_reset'] == "yes":
                        self.logger(message="erase_all_flexflash_before_reset option is set")
                        erase_flexflash = True
                if 'clear_all_sel_logs_before_reset' in config.options.keys():
                    if config.options['clear_all_sel_logs_before_reset'] == "yes":
                        self.logger(message="clear_all_sel_logs_before_reset option is set")
                        clear_sel_logs = True
                if not self.parent.reset(erase_virtual_drives=erase_virtual_drives,
                                         erase_flexflash=erase_flexflash,
                                         clear_sel_logs=clear_sel_logs,
                                         bypass_version_checks=bypass_version_checks):
                    message_str = "Error while performing device reset"
                    self.logger(level="error", message=message_str)
                    return False

                # Clearing device target, username & password since they might change in the new config
                self.parent.target = ""
                self.parent.username = ""
                self.parent.password = ""

                if self.parent.sys_mode == "cluster":
                    message_str = "Waiting up to 780 seconds for both Fabric Interconnects to come back"
                    self.logger(message=message_str)
                elif self.parent.sys_mode == "stand-alone":
                    message_str = "Waiting up to 780 seconds for Fabric Interconnect to come back"
                    self.logger(message=message_str)
                if self.parent.task is not None:
                    self.parent.task.taskstep_manager.start_taskstep(
                        name="WaitForRebootAfterResetUcsSystem", description=message_str)
                time.sleep(300)

                if not self.parent.wait_for_reboot_after_reset(timeout=480, fi_ip_list=fi_ip_list):
                    message_str = "Could not reconnect to Fabric Interconnect(s) after reset"
                    if self.parent.task is not None:
                        self.parent.task.taskstep_manager.stop_taskstep(
                            name="WaitForRebootAfterResetUcsSystem", status="failed", status_message=message_str)
                    self.logger(level="error", message=message_str)
                    return False
                self.parent.set_task_progression(20)
                if self.parent.task is not None:
                    self.parent.task.taskstep_manager.stop_taskstep(
                        name="WaitForRebootAfterResetUcsSystem", status="successful",
                        status_message="Successfully reconnected to Fabric Interconnect(s) after reset")

                # Performing initial setup
                message_str = "Performing initial setup using the following IP address(es): (" + \
                              ", ".join(fi_ip_list) + ")"
                if self.parent.task is not None:
                    self.parent.task.taskstep_manager.start_taskstep(
                        name="InitialSetupUcsSystem", description=message_str)
                self.logger(message=message_str)
                if not self.parent.initial_setup(fi_ip_list=fi_ip_list, config=config):
                    message_str = "Error while performing initial setup"
                    if self.parent.task is not None:
                        self.parent.task.taskstep_manager.stop_taskstep(
                            name="InitialSetupUcsSystem", status="failed", status_message=message_str)
                    self.logger(level="error", message=message_str)
                    return False
                if self.parent.task is not None:
                    self.parent.task.taskstep_manager.stop_taskstep(
                        name="InitialSetupUcsSystem", status="successful",
                        status_message="Successfully performed initial setup using the following IP address(es): (" +
                                       ", ".join(fi_ip_list) + ")"
                    )

                # Wait loop for FI cluster election to complete
                if self.parent.sys_mode == "cluster":
                    message_str = "Waiting up to 240 seconds for cluster election to complete"
                    if self.parent.task is not None:
                        self.parent.task.taskstep_manager.start_taskstep(
                            name="WaitForClusterElectionUcsSystem", description=message_str)
                    self.logger(message=message_str)
                    time.sleep(80)

                    if config.system:
                        if config.system[0].virtual_ip:
                            self.parent.target = config.system[0].virtual_ip
                        elif config.system[0].virtual_ipv6:
                            self.parent.target = config.system[0].virtual_ipv6
                    if not self.parent.target:
                        message_str = "Could not determine target IP of the device in the config"
                        if self.parent.task is not None:
                            self.parent.task.taskstep_manager.stop_taskstep(
                                name="WaitForClusterElectionUcsSystem", status="failed", status_message=message_str)
                        self.logger(level="error", message=message_str)
                        return False

                elif self.parent.sys_mode == "stand-alone":
                    message_str = "Waiting up to 180 seconds for initial configuration to complete"
                    if self.parent.task is not None:
                        self.parent.task.taskstep_manager.start_taskstep(
                            name="WaitForClusterElectionUcsSystem", description=message_str)
                    self.logger(message=message_str)
                    time.sleep(20)

                    # TODO Handle Ipv6
                    if config.management_interfaces:
                        for management_interface in config.management_interfaces:
                            if management_interface.fabric.upper() == 'A':
                                if management_interface.ip:
                                    self.parent.target = management_interface.ip

                    if not self.parent.target:
                        message_str = "Could not determine target IP of the device in the config"
                        if self.parent.task is not None:
                            self.parent.task.taskstep_manager.stop_taskstep(
                                name="WaitForClusterElectionUcsSystem", status="failed", status_message=message_str)
                        self.logger(level="error", message=message_str)
                        return False

                if not config.local_users:
                    # Could not find local_users in config - Admin password is a mandatory parameter - Exiting
                    message_str = "Could not find users in config"
                    if self.parent.task is not None:
                        self.parent.task.taskstep_manager.stop_taskstep(
                            name="WaitForClusterElectionUcsSystem", status="failed", status_message=message_str)
                    self.logger(level="error", message=message_str)
                    return False

                # Going through all users to find admin
                for user in config.local_users:
                    if user.id:
                        if user.id == "admin":
                            self.parent.username = "admin"
                            if user.password:
                                self.parent.password = user.password
                            else:
                                # Admin password is a mandatory input
                                message_str = "Could not find password for user id admin in config."
                                if self.parent.task is not None:
                                    self.parent.task.taskstep_manager.stop_taskstep(
                                        name="WaitForClusterElectionUcsSystem", status="failed",
                                        status_message=message_str)
                                self.logger(level="warning", message=message_str)
                                return False

                # We need to refresh the UCS device handle so that it has the right attributes
                self.parent.handle = UcsHandle(ip=self.parent.target, username=self.parent.username,
                                               password=self.parent.password)
                # We also need to refresh the config handle
                config.refresh_config_handle()

                if not common.check_web_page(device=self.parent, url="https://" + self.parent.target, str_match="Cisco",
                                             timeout=160):
                    message_str = "Impossible to reconnect to UCS system"
                    if self.parent.task is not None:
                        self.parent.task.taskstep_manager.stop_taskstep(
                            name="WaitForClusterElectionUcsSystem", status="failed", status_message=message_str)
                    self.logger(level="error", message=message_str)
                    return False
                self.parent.set_task_progression(40)

                # Reconnecting and waiting for HA cluster to be ready (if in cluster mode)
                # or FI to be ready (if in stand-alone mode)
                if not self.parent.connect(bypass_version_checks=True, retries=3):
                    message_str = "Impossible to reconnect to UCS system"
                    if self.parent.task is not None:
                        self.parent.task.taskstep_manager.stop_taskstep(
                            name="WaitForClusterElectionUcsSystem", status="failed", status_message=message_str)
                    self.logger(level="error", message=message_str)
                    return False
                if self.parent.sys_mode == "cluster":
                    if self.parent.task is not None:
                        self.parent.task.taskstep_manager.stop_taskstep(
                            name="WaitForClusterElectionUcsSystem", status="successful",
                            status_message="Cluster election successfully completed and device reconnected")

                    message_str = "Waiting up to 300 seconds for UCS HA cluster to be ready..."
                    if self.parent.task is not None:
                        self.parent.task.taskstep_manager.start_taskstep(
                            name="WaitForClusterHaReadyUcsSystem", description=message_str)
                    self.logger(message=message_str)
                    if not self.parent.wait_for_ha_cluster_ready(timeout=300):
                        message_str = "Timeout exceeded while waiting for UCS HA cluster to be in ready state"
                        if self.parent.task is not None:
                            self.parent.task.taskstep_manager.stop_taskstep(
                                name="WaitForClusterHaReadyUcsSystem", status="failed", status_message=message_str)
                        self.logger(level="error", message=message_str)
                        return False
                    if self.parent.task is not None:
                        self.parent.task.taskstep_manager.stop_taskstep(
                            name="WaitForClusterHaReadyUcsSystem", status="successful",
                            status_message="UCS HA Cluster in ready state")
                elif self.parent.sys_mode == "stand-alone":
                    if self.parent.task is not None:
                        self.parent.task.taskstep_manager.stop_taskstep(
                            name="WaitForClusterElectionUcsSystem", status="successful",
                            status_message="Initial configuration successfully completed and device reconnected")

                    message_str = "Waiting up to 300 seconds for UCS stand-alone FI to be ready..."
                    if self.parent.task is not None:
                        self.parent.task.taskstep_manager.start_taskstep(
                            name="WaitForClusterHaReadyUcsSystem", description=message_str)
                    self.logger(message=message_str)
                    if not self.parent.wait_for_standalone_fi_ready(timeout=300):
                        message_str = "Timeout exceeded while waiting for UCS stand-alone FI to be ready"
                        if self.parent.task is not None:
                            self.parent.task.taskstep_manager.stop_taskstep(
                                name="WaitForClusterHaReadyUcsSystem", status="failed", status_message=message_str)
                        self.logger(level="error", message=message_str)
                        return False
                    if self.parent.task is not None:
                        self.parent.task.taskstep_manager.stop_taskstep(
                            name="WaitForClusterHaReadyUcsSystem", status="successful",
                            status_message="UCS stand-alone FI in ready state")
                self.parent.set_task_progression(45)

                # We bypass version checks for the rest of the procedure as potential warning has already been made
                bypass_version_checks = True

            else:
                if self.parent.task is not None:
                    self.parent.task.taskstep_manager.skip_taskstep(
                        name="ClearIntersightClaimStatus", status_message="Skipping device reset")
                    self.parent.task.taskstep_manager.skip_taskstep(
                        name="DecommissionAllRackServers", status_message="Skipping device reset")
                    self.parent.task.taskstep_manager.skip_taskstep(
                        name="EraseFiConfigurations", status_message="Skipping device reset")
                    self.parent.task.taskstep_manager.skip_taskstep(
                        name="WaitForRebootAfterResetUcsSystem", status_message="Skipping device reset")
                    self.parent.task.taskstep_manager.skip_taskstep(
                        name="InitialSetupUcsSystem", status_message="Skipping device reset")
                    self.parent.task.taskstep_manager.skip_taskstep(
                        name="WaitForClusterElectionUcsSystem", status_message="Skipping device reset")
                    self.parent.task.taskstep_manager.skip_taskstep(
                        name="WaitForClusterHaReadyUcsSystem", status_message="Skipping device reset")

            # Pushing configuration to the device
            # We first make sure we are connected to the device
            if not self.parent.connect(bypass_version_checks=bypass_version_checks, force=True):
                return False

            self.parent.set_task_progression(50)
            self.logger(message="Pushing configuration " + str(config.uuid) + " to " + self.parent.target)

            # We push all config elements, in a specific optimized order to reduce number of reboots
            if self.parent.task is not None:
                self.parent.task.taskstep_manager.start_taskstep(
                    name="PushAdminSectionUcsSystem", description="Pushing Admin section of config")
            self.logger(message="Now configuring Admin section")
            is_pushed = True
            if config.system:
                is_pushed = config.system[0].push_object() and is_pushed
            for management_interface in config.management_interfaces:
                is_pushed = management_interface.push_object() and is_pushed
            if config.call_home:
                is_pushed = config.call_home[0].push_object() and is_pushed
            for timezone_mgmt in config.timezone_mgmt:
                is_pushed = timezone_mgmt.push_object() and is_pushed
            if config.local_users_properties:
                is_pushed = config.local_users_properties[0].push_object() and is_pushed
            if config.dns:
                # Exception for DNS
                dns = UcsSystemDns(parent=config)
                dns.dns = config.dns
                is_pushed = dns.push_object() and is_pushed
            if config.pre_login_banner:
                banner = UcsSystemPreLoginBanner(parent=config)
                banner.message = config.pre_login_banner
                is_pushed = banner.push_object() and is_pushed
            if config.communication_services:
                is_pushed = config.communication_services[0].push_object() and is_pushed
            if config.device_connector:
                is_pushed = config.device_connector[0].push_object() and is_pushed
            if config.global_fault_policy:
                is_pushed = config.global_fault_policy[0].push_object() and is_pushed
            if config.syslog:
                is_pushed = config.syslog[0].push_object() and is_pushed
            for locale in config.locales:
                is_pushed = locale.push_object() and is_pushed
            for role in config.roles:
                is_pushed = role.push_object() and is_pushed
            for local_user in config.local_users:
                is_pushed = local_user.push_object() and is_pushed
            if config.backup_export_policy:
                is_pushed = config.backup_export_policy[0].push_object() and is_pushed
            if config.radius:
                is_pushed = config.radius[0].push_object() and is_pushed
            if config.tacacs:
                is_pushed = config.tacacs[0].push_object() and is_pushed
            if config.ldap:
                is_pushed = config.ldap[0].push_object() and is_pushed
            if config.authentication:
                is_pushed = config.authentication[0].push_object() and is_pushed

            if self.parent.task is not None:
                self.parent.task.taskstep_manager.stop_taskstep(
                    name="PushAdminSectionUcsSystem", status="successful",
                    status_message="Successfully pushed Admin section of config")
            self.parent.set_task_progression(60)

            if self.parent.task is not None:
                self.parent.task.taskstep_manager.start_taskstep(
                    name="PushEquipmentSectionUcsSystem", description="Pushing Equipment section of config")
            self.logger(message="Now configuring Equipment section")
            if config.global_policies:
                is_pushed = config.global_policies[0].push_object() and is_pushed
            if config.kmip_client_cert_policy:
                is_pushed = config.kmip_client_cert_policy[0].push_object() and is_pushed
            if config.sel_policy:
                is_pushed = config.sel_policy[0].push_object() and is_pushed
            if config.slow_drain_timers:
                is_pushed = config.slow_drain_timers[0].push_object() and is_pushed
            for qos_system_class in config.qos_system_class:
                if config.check_if_switching_mode_config_requires_reboot() and \
                        self.parent.fi_a_model == "UCS-FI-6332-16UP":
                    self.logger(level="debug",
                                message="The QoS System Class will be committed alongside the Switching Mode push")
                    is_pushed = qos_system_class.push_object(commit=False) and is_pushed
                else:
                    is_pushed = qos_system_class.push_object() and is_pushed

            for switching_mode in config.switching_mode:
                is_pushed = switching_mode.push_object() and is_pushed

            if self.parent.task is not None:
                self.parent.task.taskstep_manager.stop_taskstep(
                    name="PushEquipmentSectionUcsSystem", status="successful",
                    status_message="Successfully pushed Equipment section of config")
            self.parent.set_task_progression(65)

            if self.parent.task is not None:
                self.parent.task.taskstep_manager.start_taskstep(
                    name="PushVlanVsanSectionUcsSystem", description="Pushing VLAN/VSAN section of config")
            self.logger(message="Now configuring VLAN/VSAN section")
            for vlan in config.vlans:
                # Handling range of VLAN
                if vlan.prefix:
                    start = int(vlan.id_from)
                    stop = int(vlan.id_to)
                    for i in range(start, stop + 1):
                        vlan_temp = copy.deepcopy(vlan)
                        vlan_temp.id = str(i)
                        vlan_temp.name = vlan_temp.prefix + vlan_temp.id
                        is_pushed = vlan_temp.push_object() and is_pushed
                else:
                    is_pushed = vlan.push_object() and is_pushed

            for vlan in config.appliance_vlans:
                # Handling range of Appliance VLAN
                if vlan.prefix:
                    start = int(vlan.id_from)
                    stop = int(vlan.id_to)
                    for i in range(start, stop + 1):
                        vlan_temp = copy.deepcopy(vlan)
                        vlan_temp.id = str(i)
                        vlan_temp.name = vlan_temp.prefix + vlan_temp.id
                        is_pushed = vlan_temp.push_object() and is_pushed
                else:
                    is_pushed = vlan.push_object() and is_pushed
            for vlan_group in config.vlan_groups:
                is_pushed = vlan_group.push_object() and is_pushed
            for vsan in config.vsans:
                is_pushed = vsan.push_object() and is_pushed
            for storage_vsan in config.storage_vsans:
                is_pushed = storage_vsan.push_object() and is_pushed

            if self.parent.task is not None:
                self.parent.task.taskstep_manager.stop_taskstep(
                    name="PushVlanVsanSectionUcsSystem", status="successful",
                    status_message="Successfully pushed VLAN/VSAN section of config")
            self.parent.set_task_progression(70)

            if self.parent.task is not None:
                self.parent.task.taskstep_manager.start_taskstep(
                    name="PushFiPortsSectionUcsSystem", description="Pushing FI ports section of config")
            self.logger(message="Now configuring FI ports")
            # The following section might need a reboot of the FIs
            # We do not commit yet to avoid multiple configuration requests of the same port id
            for breakout_port in config.breakout_ports:
                is_pushed = breakout_port.push_object(commit=False) and is_pushed
            for san_uplink_port in config.san_uplink_ports:
                is_pushed = san_uplink_port.push_object(commit=False) and is_pushed
            for san_storage_port in config.san_storage_ports:
                is_pushed = san_storage_port.push_object(commit=False) and is_pushed
            for san_unified_port in config.san_unified_ports:
                is_pushed = san_unified_port.push_object(commit=False) and is_pushed

            # Handling Breakout ports - We keep them in lists to configure them later
            ports_with_aggr_id = []
            ports_converted_to_native_40g = []
            # We first fetch the list of Breakout ports to see if we have to un-configure some of them
            fabricbreakout_list = []
            try:
                fabricbreakout_list = config.handle.query_classid("fabricBreakout")
            except ConnectionRefusedError:
                self.logger(level="error", message="Error while communicating with UCS System")
            except UcsException as err:
                self.logger(level="error", message="Unable to fetch Breakout ports: " + err.error_descr)
            except urllib.error.URLError:
                self.logger(level="error", message="Timeout error while fetching Breakout ports")

            for port in config.lan_uplink_ports + config.fcoe_uplink_ports + config.unified_uplink_ports + \
                    config.unified_storage_ports + config.fcoe_storage_ports + config.appliance_ports:
                # We exclude ports that have an aggr_id value as the breakout might not have been configured yet
                if port.aggr_id:
                    ports_with_aggr_id.append(port)
                # We also exclude ports that are currently in Breakout mode and need to be configured as native 40G
                # We remove the Breakout port so that it is included in the next commit
                else:
                    for fabricbreakout in fabricbreakout_list:
                        if port.fabric.upper() == fabricbreakout.dn.split("/")[2] \
                                and port.slot_id == fabricbreakout.slot_id \
                                and port.port_id == fabricbreakout.port_id \
                                and port.aggr_id is None:
                            self.logger(level="debug", message="Breakout port " + port.fabric + "/" + port.slot_id +
                                                               "/" + port.port_id +
                                                               " will be converted to native Ethernet")
                            config.handle.remove_mo(fabricbreakout)
                            ports_converted_to_native_40g.append(port)
                # For ports that are not Breakout-related, we include them in the next commit
                if port not in ports_converted_to_native_40g and port not in ports_with_aggr_id:
                    is_pushed = port.push_object(commit=False) and is_pushed

            # Handling the specific case of server ports
            # For ports that are currently FC ports and need to be changed to server ports, we configure them
            # temporarily as disabled LAN uplink ports, to force Unified Port conversion of FC to Ethernet
            # For ports that are currently Breakout ports and need to be changed to server ports, we un-configure them
            # as Breakout ports, to force Breakout conversion to native 40G Ethernet
            # FIXME: We could add a check that Unified Port conversion will work by making sure the range is complete
            # We first fetch the list of FC ports to see if we have to un-configure some of them
            fcpio_list = []
            try:
                fcpio_list = config.handle.query_classid("fcPIo")
            except ConnectionRefusedError:
                self.logger(level="error", message="Error while communicating with UCS System")
            except UcsException as err:
                self.logger(level="error", message="Unable to fetch FC ports: " + err.error_descr)
            except urllib.error.URLError:
                self.logger(level="error", message="Timeout error while fetching FC ports")

            for server_port in config.server_ports:
                for fcpio in fcpio_list:
                    if server_port.fabric.upper() == fcpio.switch_id and server_port.slot_id == fcpio.slot_id \
                            and server_port.port_id == fcpio.port_id and server_port.aggr_id is None:
                        mo = FabricEthLanEp(parent_mo_or_dn="fabric/lan/" + server_port.fabric.upper(),
                                            admin_state="disabled", port_id=server_port.port_id,
                                            slot_id=server_port.slot_id)
                        self.logger(level="debug", message="FC port " + server_port.fabric + "/" + server_port.slot_id +
                                                           "/" + server_port.port_id + " will be converted to Ethernet")
                        config.handle.add_mo(mo)
                for fabricbreakout in fabricbreakout_list:
                    if server_port.fabric.upper() == fabricbreakout.dn.split("/")[2] \
                            and server_port.slot_id == fabricbreakout.slot_id \
                            and server_port.port_id == fabricbreakout.port_id and server_port.aggr_id is None:
                        self.logger(level="debug", message="Breakout port " + server_port.fabric + "/" +
                                                           server_port.slot_id + "/" + server_port.port_id +
                                                           " will be converted to native Ethernet")
                        config.handle.remove_mo(fabricbreakout)

            need_reboot = config.check_if_ports_config_requires_reboot()
            try:
                config.handle.commit()

            except UcsException as err:
                # We discard the commit buffer in order to avoid resending the bad buffer content in the next commit
                config.handle.commit_buffer_discard()
                need_reboot = False
                self.logger(level="error", message="Error in configuring FI ports: " + err.error_descr)
            except Exception:
                # We discard the commit buffer in order to avoid resending the bad buffer content in the next commit
                config.handle.commit_buffer_discard()
                need_reboot = False
                self.logger(level="error", message="Unknown error in configuring FI ports")

            if self.parent.task is not None:
                self.parent.task.taskstep_manager.stop_taskstep(
                    name="PushFiPortsSectionUcsSystem", status="successful",
                    status_message="Successfully pushed FI ports section of config")
            self.parent.set_task_progression(75)

            # Reboot handling
            if need_reboot:
                message_str = "Waiting up to 900 seconds for Fabric Interconnect(s) to come back"
                if self.parent.task is not None:
                    self.parent.task.taskstep_manager.start_taskstep(
                        name="WaitForRebootAfterPushFiPortsUcsSystem", description=message_str)
                self.logger(message="Caution: The system will reboot in a few seconds!")
                self.logger(message=message_str)
                time.sleep(420)

                if not common.check_web_page(device=self.parent, url="https://" + self.parent.target, str_match="Cisco",
                                             timeout=480):
                    message_str = "Impossible to reconnect to UCS system"
                    if self.parent.task is not None:
                        self.parent.task.taskstep_manager.stop_taskstep(
                            name="WaitForRebootAfterPushFiPortsUcsSystem", status="failed", status_message=message_str)
                    self.logger(level="error", message=message_str)
                    return False

                # Need to reconnect
                self.parent.connect(bypass_version_checks=True)
                if self.parent.task is not None:
                    self.parent.task.taskstep_manager.stop_taskstep(
                        name="WaitForRebootAfterPushFiPortsUcsSystem", status="successful",
                        status_message="Successfully reconnected to Fabric Interconnect(s) after push of FI ports")
                self.logger(message="Reconnected to system: " + self.parent.name + " running version: " +
                                    self.parent.version.version)

                # We now fetch the HA state to make sure both FIs are back online and in sync. This is to avoid the
                # case where a single FI has rebooted with port type changes, and UCS Manager responds on the remaining
                # FI before reboot is complete. This lead to UCS Manager not knowing about those port type changes
                # We only do this if we are in cluster mode
                if self.parent.sys_mode == "cluster":
                    message_str = "Waiting up to 300 seconds for UCS HA cluster to be ready..."
                    if self.parent.task is not None:
                        self.parent.task.taskstep_manager.start_taskstep(
                            name="WaitForClusterHaReadyAfterPushFiPortsUcsSystem", description=message_str)
                    self.logger(message=message_str)
                    if not self.parent.wait_for_ha_cluster_ready(timeout=300):
                        message_str = "Timeout exceeded while waiting for UCS HA cluster to be in ready state"
                        if self.parent.task is not None:
                            self.parent.task.taskstep_manager.stop_taskstep(
                                name="WaitForClusterHaReadyAfterPushFiPortsUcsSystem", status="failed",
                                status_message=message_str)
                        self.logger(level="error", message=message_str)
                        return False

                    if self.parent.task is not None:
                        self.parent.task.taskstep_manager.stop_taskstep(
                            name="WaitForClusterHaReadyAfterPushFiPortsUcsSystem", status="successful",
                            status_message="UCS HA Cluster in ready state")

                    # We now fetch the FSM state of the physical ports configuration to make sure it is 100%, in order
                    # to make sure the new port configuration has been taken into account before configuring anything
                    # else
                    message_str = "Waiting up to 300 seconds for FSM state of physical ports to reach 100%..."
                    if self.parent.task is not None:
                        self.parent.task.taskstep_manager.start_taskstep(
                            name="WaitForFiPortsFsmStateUcsSystem", description=message_str)
                    self.logger(message=message_str)
                    if not self.parent.wait_for_fsm_complete(ucs_sdk_object_class="swPhys", timeout=300):
                        message_str = "Timeout exceeded while waiting for FSM state of physical ports to reach 100%"
                        if self.parent.task is not None:
                            self.parent.task.taskstep_manager.stop_taskstep(
                                name="WaitForFiPortsFsmStateUcsSystem", status="failed", status_message=message_str)
                        self.logger(level="error", message=message_str)
                        return False

                    if self.parent.task is not None:
                        self.parent.task.taskstep_manager.stop_taskstep(
                            name="WaitForFiPortsFsmStateUcsSystem", status="successful",
                            status_message="UCS FI ports FSM state at 100%")

                else:
                    if self.parent.task is not None:
                        self.parent.task.taskstep_manager.skip_taskstep(
                            name="WaitForClusterHaReadyAfterPushFiPortsUcsSystem",
                            status_message="Skipping wait for HA state as device is in stand-alone mode")
                        self.parent.task.taskstep_manager.skip_taskstep(
                            name="WaitForFiPortsFsmStateUcsSystem",
                            status_message="Skipping wait for FI ports FSM state as device is in stand-alone mode")

            else:
                if self.parent.task is not None:
                    self.parent.task.taskstep_manager.skip_taskstep(
                        name="WaitForRebootAfterPushFiPortsUcsSystem",
                        status_message="Skipping wait for reboot after FI ports config push as no reboot is required")
                    self.parent.task.taskstep_manager.skip_taskstep(
                        name="WaitForClusterHaReadyAfterPushFiPortsUcsSystem",
                        status_message="Skipping wait for HA state as no reboot is required")
                    self.parent.task.taskstep_manager.skip_taskstep(
                        name="WaitForFiPortsFsmStateUcsSystem",
                        status_message="Skipping wait for FI ports FSM state as no reboot is required")

            # End of section needing reboot of the FI

            # We now need to push the config to ports that are in Breakout or were converted back to native
            # as they were excluded previously in case a reboot was needed
            for port in ports_with_aggr_id + ports_converted_to_native_40g:
                is_pushed = port.push_object() and is_pushed

            self.parent.set_task_progression(80)

            # We take care of server ports at the end to support discovery in order (using a timer)
            # Checking if "discover_server_ports_in_order" option is set in config
            ordered_discovery = False
            if 'discover_server_ports_in_order' in config.options.keys():
                if config.options['discover_server_ports_in_order'] == "yes":
                    ordered_discovery = True
                    self.logger(message="discover_server_ports_in_order is set, a 20s delay will be applied between " +
                                        "each server port")
            for server_port in config.server_ports:
                is_pushed = server_port.push_object() and is_pushed
                if ordered_discovery:
                    # Adding a sleep timer to make sure chassis/rack servers are discovered in order
                    time.sleep(20)

            self.parent.set_task_progression(85)

            if self.parent.task is not None:
                self.parent.task.taskstep_manager.start_taskstep(
                    name="PushFiPortChannelsSectionUcsSystem", description="Pushing FI Port-Channels section of config")

            for lan_port_channel in config.lan_port_channels:
                is_pushed = lan_port_channel.push_object() and is_pushed
            for fcoe_port_channel in config.fcoe_port_channels:
                is_pushed = fcoe_port_channel.push_object() and is_pushed
            for san_port_channel in config.san_port_channels:
                is_pushed = san_port_channel.push_object() and is_pushed
            for appliance_port_channel in config.appliance_port_channels:
                is_pushed = appliance_port_channel.push_object() and is_pushed

            for lan_pin_group in config.lan_pin_groups:
                is_pushed = lan_pin_group.push_object() and is_pushed
            for san_pin_group in config.san_pin_groups:
                is_pushed = san_pin_group.push_object() and is_pushed

            for fc_zone_profile in config.fc_zone_profiles:
                is_pushed = fc_zone_profile.push_object() and is_pushed

            for udld_link_policy in config.udld_link_policies:
                is_pushed = udld_link_policy.push_object() and is_pushed
            for link_profile in config.link_profiles:
                is_pushed = link_profile.push_object() and is_pushed
            for appliance_network_control_policy in config.appliance_network_control_policies:
                is_pushed = appliance_network_control_policy.push_object() and is_pushed

            for port_auto_discovery_policy in config.port_auto_discovery_policy:
                is_pushed = port_auto_discovery_policy.push_object() and is_pushed

            for lan_traffic_monitoring_session in config.lan_traffic_monitoring_sessions:
                is_pushed = lan_traffic_monitoring_session.push_object() and is_pushed

            for san_traffic_monitoring_session in config.san_traffic_monitoring_sessions:
                is_pushed = san_traffic_monitoring_session.push_object() and is_pushed

            for netflow_monitoring in config.netflow_monitoring:
                is_pushed = netflow_monitoring.push_object() and is_pushed

            if self.parent.task is not None:
                self.parent.task.taskstep_manager.stop_taskstep(
                    name="PushFiPortChannelsSectionUcsSystem", status="successful",
                    status_message="Successfully pushed FI Port-Channels section of config")
            self.parent.set_task_progression(90)

            if self.parent.task is not None:
                self.parent.task.taskstep_manager.start_taskstep(
                    name="PushOrgsSectionUcsSystem", description="Pushing Orgs section of config")

            for org in config.orgs:
                is_pushed = org.push_object() and is_pushed

            if self.parent.task is not None:
                self.parent.task.taskstep_manager.stop_taskstep(
                    name="PushOrgsSectionUcsSystem", status="successful",
                    status_message="Successfully pushed Orgs section of config")

            # We handle UCS Central at the very end, because it might push config to the UCS system and create
            # connectivity issues
            if config.ucs_central:
                is_pushed = config.ucs_central[0].push_object() and is_pushed

            if is_pushed:
                self.logger(message="Successfully pushed configuration " + str(config.uuid) + " to " + self.parent.target)

            # We disconnect from the device
            self.parent.disconnect()
            self.parent.set_task_progression(100)

            return True
        else:
            self.logger(level="error", message="No config to push!")
            return False

    def _fill_config_from_json(self, config=None, config_json=None):
        """
        Fills config using parsed JSON config file
        :param config: config to be filled
        :param config_json: parsed JSON content containing config
        :return: True if successful, False otherwise
        """
        if config is None or config_json is None:
            self.logger(level="debug", message="Missing config or config_json parameter!")
            return False

        if "system" in config_json:
            config.system.append(UcsSystemInformation(parent=config, json_content=config_json["system"][0]))
        if "dns" in config_json:
            # Exception for DNS
            config.dns.extend(config_json["dns"])
        if "pre_login_banner" in config_json:
            # Exception for pre login banner
            config.pre_login_banner = config_json["pre_login_banner"]
        if "timezone_mgmt" in config_json:
            for timezone_mgmt in config_json["timezone_mgmt"]:
                config.timezone_mgmt.append(UcsSystemTimezoneMgmt(parent=config, json_content=timezone_mgmt))
        if "locales" in config_json:
            for locale in config_json["locales"]:
                config.locales.append(UcsSystemLocale(parent=config, json_content=locale))
        if "roles" in config_json:
            for role in config_json["roles"]:
                config.roles.append(UcsSystemRole(parent=config, json_content=role))
        if "kmip_client_cert_policy" in config_json:
            config.kmip_client_cert_policy.append(
                UcsSystemKmipCertificationPolicy(parent=config, json_content=config_json["kmip_client_cert_policy"][0]))
        if "local_users_properties" in config_json:
            config.local_users_properties.append(
                UcsSystemLocalUsersProperties(parent=config, json_content=config_json["local_users_properties"][0]))
        if "local_users" in config_json:
            for local_user in config_json["local_users"]:
                config.local_users.append(UcsSystemLocalUser(parent=config, json_content=local_user))
        if "sel_policy" in config_json:
            config.sel_policy.append(UcsSystemSelPolicy(parent=config, json_content=config_json["sel_policy"][0]))
        if "slow_drain_timers" in config_json:
            config.slow_drain_timers.append(UcsSystemSlowDrainTimers(parent=config,
                                                                     json_content=config_json["slow_drain_timers"][0]))
        if "switching_mode" in config_json:
            config.switching_mode.append(UcsSystemSwitchingMode(parent=config,
                                                                json_content=config_json["switching_mode"][0]))
        if "ucs_central" in config_json:
            config.ucs_central.append(UcsSystemUcsCentral(parent=config, json_content=config_json["ucs_central"][0]))
        if "qos_system_class" in config_json:
            for qos_system_class in config_json["qos_system_class"]:
                config.qos_system_class.append(UcsSystemQosSystemClass(parent=config, json_content=qos_system_class))
        if "fc_zone_profiles" in config_json:
            for policy in config_json["fc_zone_profiles"]:
                config.fc_zone_profiles.append(UcsSystemFcZoneProfile(parent=config, json_content=policy))
        if "udld_link_policies" in config_json:
            for policy in config_json["udld_link_policies"]:
                config.udld_link_policies.append(UcsSystemUdldLinkPolicy(parent=config, json_content=policy))
        if "link_profiles" in config_json:
            for policy in config_json["link_profiles"]:
                config.link_profiles.append(UcsSystemLinkProfile(parent=config, json_content=policy))
        if "appliance_network_control_policies" in config_json:
            for policy in config_json["appliance_network_control_policies"]:
                config.appliance_network_control_policies.append(
                    UcsSystemApplianceNetworkControlPolicy(parent=config, json_content=policy))
        if "communication_services" in config_json:
            config.communication_services.append(
                UcsSystemCommunicationServices(parent=config, json_content=config_json["communication_services"][0]))
        if "device_connector" in config_json:
            config.device_connector.append(
                UcsDeviceConnector(parent=config, json_content=config_json["device_connector"][0]))
        if "global_fault_policy" in config_json:
            config.global_fault_policy.append(
                UcsSystemFaultPolicy(parent=config, json_content=config_json["global_fault_policy"][0]))
        if "syslog" in config_json:
            config.syslog.append(UcsSystemSyslog(parent=config, json_content=config_json["syslog"][0]))
        if "radius" in config_json:
            config.radius.append(UcsSystemRadius(parent=config, json_content=config_json["radius"][0]))
        if "tacacs" in config_json:
            config.tacacs.append(UcsSystemTacacs(parent=config, json_content=config_json["tacacs"][0]))
        if "ldap" in config_json:
            config.ldap.append(UcsSystemLdap(parent=config, json_content=config_json["ldap"][0]))
        if "authentication" in config_json:
            config.authentication.append(
                UcsSystemAuthentication(parent=config, json_content=config_json["authentication"][0]))
        if "call_home" in config_json:
            config.call_home.append(UcsSystemCallHome(parent=config, json_content=config_json["call_home"][0]))
        if "backup_export_policy" in config_json:
            config.backup_export_policy.append(
                UcsSystemBackupExportPolicy(parent=config, json_content=config_json["backup_export_policy"][0]))
        if "global_policies" in config_json:
            config.global_policies.append(UcsSystemGlobalPolicies(parent=config,
                                                                  json_content=config_json["global_policies"][0]))
        if "management_interfaces" in config_json:
            for management_interface_json in config_json["management_interfaces"]:
                config.management_interfaces.append(
                    UcsSystemManagementInterface(parent=config, json_content=management_interface_json))
        if "lan_uplink_ports" in config_json:
            for lan_uplink_port in config_json["lan_uplink_ports"]:
                config.lan_uplink_ports.append(UcsSystemLanUplinkPort(parent=config, json_content=lan_uplink_port))
        if "server_ports" in config_json:
            for server_port in config_json["server_ports"]:
                config.server_ports.append(UcsSystemServerPort(parent=config, json_content=server_port))
        if "appliance_ports" in config_json:
            for appliance_port in config_json["appliance_ports"]:
                config.appliance_ports.append(UcsSystemAppliancePort(parent=config, json_content=appliance_port))
        if "vlans" in config_json:
            for vlan in config_json["vlans"]:
                config.vlans.append(UcsSystemVlan(parent=config, json_content=vlan))
        if "appliance_vlans" in config_json:
            for appliance_vlan in config_json["appliance_vlans"]:
                config.appliance_vlans.append(UcsSystemApplianceVlan(parent=config, json_content=appliance_vlan))
        if "san_uplink_ports" in config_json:
            for san_uplink_port in config_json["san_uplink_ports"]:
                config.san_uplink_ports.append(UcsSystemSanUplinkPort(parent=config, json_content=san_uplink_port))
        if "san_storage_ports" in config_json:
            for san_storage_port in config_json["san_storage_ports"]:
                config.san_storage_ports.append(UcsSystemSanStoragePort(parent=config, json_content=san_storage_port))
        if "fcoe_uplink_ports" in config_json:
            for fcoe_uplink_port in config_json["fcoe_uplink_ports"]:
                config.fcoe_uplink_ports.append(UcsSystemFcoeUplinkPort(parent=config, json_content=fcoe_uplink_port))
        if "fcoe_storage_ports" in config_json:
            for fcoe_storage_port in config_json["fcoe_storage_ports"]:
                config.fcoe_storage_ports.append(UcsSystemFcoeStoragePort(parent=config,
                                                                          json_content=fcoe_storage_port))
        if "unified_uplink_ports" in config_json:
            for unified_uplink_port in config_json["unified_uplink_ports"]:
                config.unified_uplink_ports.append(UcsSystemUnifiedUplinkPort(parent=config,
                                                                              json_content=unified_uplink_port))
        if "unified_storage_ports" in config_json:
            for unified_storage_port in config_json["unified_storage_ports"]:
                config.unified_storage_ports.append(UcsSystemUnifiedStoragePort(parent=config,
                                                                                json_content=unified_storage_port))
        if "vsans" in config_json:
            for vsan in config_json["vsans"]:
                config.vsans.append(UcsSystemVsan(parent=config, json_content=vsan))
        if "storage_vsans" in config_json:
            for storage_vsan in config_json["storage_vsans"]:
                config.storage_vsans.append(UcsSystemStorageVsan(parent=config, json_content=storage_vsan))
        if "lan_port_channels" in config_json:
            for lan_port_channel in config_json["lan_port_channels"]:
                config.lan_port_channels.append(UcsSystemLanPortChannel(parent=config, json_content=lan_port_channel))
        if "fcoe_port_channels" in config_json:
            for fcoe_port_channel in config_json["fcoe_port_channels"]:
                config.fcoe_port_channels.append(UcsSystemFcoePortChannel(parent=config,
                                                                          json_content=fcoe_port_channel))
        if "san_port_channels" in config_json:
            for san_port_channel in config_json["san_port_channels"]:
                config.san_port_channels.append(UcsSystemSanPortChannel(parent=config, json_content=san_port_channel))
        if "appliance_port_channels" in config_json:
            for appliance_port_channel in config_json["appliance_port_channels"]:
                config.appliance_port_channels.append(
                    UcsSystemAppliancePortChannel(parent=config, json_content=appliance_port_channel))
        if "vlan_groups" in config_json:
            for vlan_group in config_json["vlan_groups"]:
                config.vlan_groups.append(UcsSystemVlanGroup(parent=config, json_content=vlan_group))
        if "lan_pin_groups" in config_json:
            for lan_pin_group in config_json["lan_pin_groups"]:
                config.lan_pin_groups.append(UcsSystemLanPinGroup(parent=config, json_content=lan_pin_group))
        if "san_pin_groups" in config_json:
            for san_pin_group in config_json["san_pin_groups"]:
                config.san_pin_groups.append(UcsSystemSanPinGroup(parent=config, json_content=san_pin_group))
        if "breakout_ports" in config_json:
            for breakout_port in config_json["breakout_ports"]:
                config.breakout_ports.append(UcsSystemBreakoutPort(parent=config, json_content=breakout_port))
        if "san_unified_ports" in config_json:
            for san_unified_port in config_json["san_unified_ports"]:
                config.san_unified_ports.append(UcsSystemSanUnifiedPort(parent=config, json_content=san_unified_port))
        if "port_auto_discovery_policy" in config_json:
            for port_auto_discovery_policy in config_json["port_auto_discovery_policy"]:
                config.port_auto_discovery_policy.append(
                    UcsSystemPortAutoDiscoveryPolicy(parent=config, json_content=port_auto_discovery_policy))
        if "lan_traffic_monitoring_sessions" in config_json:
            for lan_traffic_monitoring_session in config_json["lan_traffic_monitoring_sessions"]:
                config.lan_traffic_monitoring_sessions.append(
                    UcsSystemLanTrafficMonitoringSession(parent=config, json_content=lan_traffic_monitoring_session))
        if "san_traffic_monitoring_sessions" in config_json:
            for san_traffic_monitoring_session in config_json["san_traffic_monitoring_sessions"]:
                config.san_traffic_monitoring_sessions.append(
                    UcsSystemSanTrafficMonitoringSession(parent=config, json_content=san_traffic_monitoring_session))
        if "netflow_monitoring" in config_json:
            for netflow_monitoring in config_json["netflow_monitoring"]:
                config.netflow_monitoring.append(
                    UcsSystemNetflowMonitoring(parent=config, json_content=netflow_monitoring))

        if "orgs" in config_json:
            for org in config_json["orgs"]:
                if "name" in org:
                    if org["name"] == "root":
                        config.orgs.append(UcsSystemOrg(parent=config, json_content=org))
                    else:
                        self.logger(level="error", message="Org 'root' not found. Org 'root' is mandatory." +
                                                           " No org configuration will be fetched")

        return True


class UcsImcConfigManager(GenericUcsConfigManager):
    def __init__(self, parent=None):
        GenericUcsConfigManager.__init__(self, parent=parent)
        self.config_class_name = UcsImcConfig

    def get_profiles(self, config=None):
        self.logger(level="error", message="Not available for device of type " + self.parent.metadata.device_type_long)

    def fetch_config(self, force=False):
        self.logger(message="Fetching config from live device (can take several minutes)")
        config = UcsImcConfig(parent=self)
        config.metadata.origin = "live"
        config.metadata.easyucs_version = __version__
        config.load_from = "live"
        config._fetch_sdk_objects(force=force)

        # If any of the mandatory tasksteps fails then return None
        from api.api_server import easyucs
        if easyucs and self.parent.task and \
                easyucs.task_manager.is_any_taskstep_failed(uuid=self.parent.task.metadata.uuid):
            self.logger(level="error", message="Failed to fetch one or more SDK objects. Stopping the config fetch.")
            return None

        self.logger(level="debug", message="Finished fetching UCS SDK objects for config")

        # Put in order the items to append
        config.admin_networking.append(UcsImcAdminNetwork(parent=config))
        config.timezone_mgmt.append(UcsImcTimezoneMgmt(parent=config))
        for local_user in config.sdk_objects.get("aaaUser", []):
            if local_user.account_status != "inactive":
                config.local_users.append(UcsImcLocalUser(parent=config, aaa_user=local_user))
        config.local_users_properties.append(UcsImcLocalUsersProperties(parent=config))
        config.server_properties.append(UcsImcServerProperties(parent=config))
        config.ip_blocking_properties.append(UcsImcIpBlockingProperties(parent=config))
        config.ip_filtering_properties.append(UcsImcIpFilteringProperties(parent=config))
        config.power_policies.append(UcsImcPowerPolicies(parent=config))
        for adapter_card in config.sdk_objects.get("adaptorUnit", []):
            config.adapter_cards.append(UcsImcAdapterCard(parent=config, adaptor_unit=adapter_card))
        config.communications_services.append(UcsImcCommunicationsServices(parent=config))
        device_connector = UcsDeviceConnector(parent=config)
        if device_connector.intersight_url:
            config.device_connector.append(device_connector)
        config.chassis_inventory.append(UcsImcChassisInventory(parent=config))
        config.power_cap_configuration.append(UcsImcPowerCapConfiguration(parent=config))
        config.virtual_kvm_properties.append(UcsImcVKvmProperties(parent=config))
        config.secure_key_management.append(UcsImcSecureKeyManagement(parent=config))
        config.snmp.append(UcsImcSnmp(parent=config))
        config.logging_controls.append(UcsImcLoggingControls(parent=config))
        config.smtp_properties.append(UcsImcSmtpProperties(parent=config))
        for platform_event_filter in config.sdk_objects.get("platformEventFilters", []):
            config.platform_event_filters.append(UcsImcPlatformEventFilter(parent=config,
                                                                           platform_event_filter=platform_event_filter))
        # Delete empty filters
        config.platform_event_filters = [i for i in config.platform_event_filters if i.id]

        config.virtual_media.append(UcsImcVirtualMedia(parent=config))
        config.serial_over_lan_properties.append(UcsImcSerialOverLanProperties(parent=config))
        config.bios_settings.append(UcsImcBios(parent=config))
        # Same error message in the GUI
        if not config.bios_settings:
            self.logger(level="warning", message="No BIOS Data found: BIOS Set-up token data not available. " +
                                                 "Please power on/reboot the host.")
        config.ldap_settings.append(UcsImcLdap(parent=config))
        config.boot_order_properties.append(UcsImcBootOrder(parent=config))
        config.dynamic_storage_zoning.append(UcsImcDynamicStorageZoning(parent=config))
        for storage_controller in config.sdk_objects.get("storageController", []):
            config.storage_controllers.append(UcsImcStorageController(parent=config,
                                                                      storage_controller=storage_controller))
        for storage_flex_flash_controller in config.sdk_objects.get("storageFlexFlashController", []):
            config.storage_flex_flash_controllers.append(
                UcsImcStorageFlexFlashController(parent=config, storage_controller=storage_flex_flash_controller))

        # Removing the list of SDK objects fetched from the live UCS device
        config.sdk_objects = None
        self.config_list.append(config)
        self.logger(message="Finished fetching config with UUID " + str(config.uuid) + " from live device")
        return config.uuid

    def push_config(self, uuid=None, reset=False, imc_ip=None, bypass_version_checks=False, force=False):
        """
       Push the specified config to the live system
       :param uuid: The UUID of the config to be pushed. If not specified, the most recent config will be used
       :param reset: Whether the device must be reset before pushing the config
       :param imc_ip: DHCP IP address taken by the CIMC after the reset
       :param bypass_version_checks: Whether the minimum version checks should be bypassed when connecting
       :param force: Force the push to proceed even in-case of critical errors.
       :return: True if config push was successful, False otherwise
       """
        if uuid is None:
            self.logger(level="debug", message="No config UUID specified in config push request. Using latest.")
            config = self.get_latest_config()
        else:
            # Find the config that needs to be pushed
            config_list = [config for config in self.config_list if config.uuid == uuid]
            if len(config_list) != 1:
                self.logger(level="error", message="Failed to locate config with UUID " + str(uuid) + " for push")
                return False
            else:
                config = config_list[0]

        if config:
            if reset:
                # Check if the DHCP IP address is available before resetting
                if not imc_ip:
                    self.logger(level="error", message="No DHCP IP address given")
                    return False

                # Check if the admin password is available before resetting
                for user in config.local_users:
                    if user.username:
                        if user.username == "admin":
                            if not user.password:
                                # Admin password is a mandatory input
                                self.logger(level="error",
                                            message="Reset aborted: Could not find password for user admin in config")
                                return False

                # Performing reset
                self.logger(message="Resetting device " + self.parent.target + " before pushing configuration")
                erase_virtual_drives = False
                erase_flexflash = False
                clear_sel_logs = False
                set_drives_status = None
                if 'erase_all_virtual_drives_before_reset' in config.options.keys():
                    if config.options['erase_all_virtual_drives_before_reset'] == "yes":
                        self.logger(message="erase_all_virtual_drives_before_reset option is set")
                        erase_virtual_drives = True
                if 'erase_all_flexflash_before_reset' in config.options.keys():
                    if config.options['erase_all_flexflash_before_reset'] == "yes":
                        self.logger(message="erase_all_flexflash_before_reset option is set")
                        erase_flexflash = True
                if 'clear_all_sel_logs_before_reset' in config.options.keys():
                    if config.options['clear_all_sel_logs_before_reset'] == "yes":
                        self.logger(message="clear_all_sel_logs_before_reset option is set")
                        clear_sel_logs = True
                if 'set_drives_to_status' in config.options.keys():
                    if config.options['set_drives_to_status'] == "jbod":
                        self.logger(message="Setting drives to the requested status: " +
                                            config.options['set_drives_to_status'])
                        set_drives_status = config.options['set_drives_to_status']

                    if config.options['set_drives_to_status'] == "unconfigured-good":
                        self.logger(message="Setting drives to the requested status: " +
                                            config.options['set_drives_to_status'])
                        set_drives_status = config.options['set_drives_to_status']
                if not self.parent.reset(erase_virtual_drives=erase_virtual_drives, erase_flexflash=erase_flexflash,
                                         clear_sel_logs=clear_sel_logs, set_drives_status=set_drives_status):
                    self.logger(level="error", message="Error while performing device reset")
                    return False

                # Clearing device target, username & password since they might change in the new config
                self.parent.target = ""
                self.parent.username = ""
                self.parent.password = ""

                self.logger(message="Waiting up to 480 seconds for UCS IMC to come back")
                time.sleep(200)
                if not self.parent.wait_for_reboot_after_reset(timeout=280, imc_ip=imc_ip):
                    self.logger(level="error", message="Could not reconnect to UCS IMC after reset")
                    return False
                self.parent.set_task_progression(20)

                # Performing initial setup
                self.logger(message="Performing initial setup using the following IP address: " + str(imc_ip))
                if not self.parent.initial_setup(imc_ip=imc_ip, config=config):
                    self.logger(level="error", message="Error while performing initial setup")
                    return False

                # We now need to get the new IP address and admin password from the configuration
                if config.admin_networking[0].management_ipv4_address:
                    imc_target_ip_address = config.admin_networking[0].management_ipv4_address
                else:
                    self.logger(level="error",
                                message="Could not find Management IP address of UCS IMC in the config")
                    return False

                if not config.local_users:
                    self.logger(level="error", message="Could not find local_users in the config")
                    return False

                # Going through all users to find admin
                target_admin_password = ""
                for user in config.local_users:
                    if user.username:
                        if user.username == "admin":
                            if user.password:
                                target_admin_password = user.password
                            else:
                                # Admin password is a mandatory input - Exiting
                                self.logger(level="error",
                                            message="Could not find password for user id admin in the config")
                                return False

                # We went through all users - Making sure we got the information we needed
                if not target_admin_password:
                    self.logger(level="error", message="Could not find user id admin in the config")
                    return False

                # We need to refresh the UCS device handle so that it has the right attributes
                self.parent.handle = ImcHandle(ip=imc_target_ip_address, username="admin",
                                               password=target_admin_password)
                self.parent.target = imc_target_ip_address

                # Changing handle to the new one
                config.refresh_config_handle()

                self.logger(level="debug",
                            message="Waiting for the IMC to come back with the IP " + imc_target_ip_address)
                if not self.parent.wait_for_reboot_after_reset(timeout=120, imc_ip=imc_target_ip_address):
                    return False
                self.parent.set_task_progression(40)

            # Pushing configuration to the device
            # We first make sure we are connected to the device
            if not self.parent.connect(bypass_version_checks=bypass_version_checks):
                return False
            self.parent.set_task_progression(50)
            self.logger(message="Pushing configuration " + str(config.uuid) + " to " + self.parent.target)

            # We push all config elements, in a specific optimized order to reduce number of reboots
            is_pushed = True
            if config.admin_networking:
                old_session_id = self.parent.handle.session_id

                admin_network_push_resp = config.admin_networking[0].push_object()
                is_pushed = admin_network_push_resp and is_pushed
                if admin_network_push_resp:
                    # We now need to get the new IP address from the configuration
                    if config.admin_networking[0].management_ipv4_address:
                        self.parent.target = config.admin_networking[0].management_ipv4_address

                    # We wait for IMC to come back in case IP Add or NIC Mode Changed
                    self.logger(message="Waiting up to 90 seconds for UCS IMC to come back")
                    time.sleep(40)
                    if not self.parent.wait_for_reboot_after_reset(timeout=50, imc_ip=self.parent.target):
                        self.logger(level="error", message="Could not reconnect to UCS IMC after reset")
                        return False
                    # We need to refresh the UCS device handle so that it has the right attributes
                    self.parent.handle = ImcHandle(ip=self.parent.target, username=self.parent.username,
                                                   password=self.parent.password)

                    # Changing handle to the new one
                    config.refresh_config_handle()
                    # We need to reconnect to the device
                    if not self.parent.connect(bypass_version_checks=bypass_version_checks):
                        return False

                    self.logger(message="Old session id " + str(old_session_id) + " will self timeout")

            if config.timezone_mgmt:
                is_pushed = config.timezone_mgmt[0].push_object() and is_pushed
            if config.local_users_properties:
                is_pushed = config.local_users_properties[0].push_object() and is_pushed
            for local_user in config.local_users:
                is_pushed = local_user.push_object() and is_pushed
            if "clear_intersight_claim_status" in config.options.keys():
                if config.options["clear_intersight_claim_status"] == "yes":
                    self.parent.clear_intersight_claim_status()
                    self.parent.connect()
            if config.device_connector:
                is_pushed = config.device_connector[0].push_object() and is_pushed

            self.parent.set_task_progression(60)

            if config.server_properties:
                is_pushed = config.server_properties[0].push_object() and is_pushed
            if config.ip_blocking_properties:
                is_pushed = config.ip_blocking_properties[0].push_object() and is_pushed
            if config.ip_filtering_properties:
                is_pushed = config.ip_filtering_properties[0].push_object() and is_pushed
            if config.power_policies:
                is_pushed = config.power_policies[0].push_object() and is_pushed
            for adapter_card in config.adapter_cards:
                is_pushed = adapter_card.push_object() and is_pushed
            if config.communications_services:
                is_pushed = config.communications_services[0].push_object() and is_pushed
            if config.chassis_inventory:
                is_pushed = config.chassis_inventory[0].push_object() and is_pushed
            if config.power_cap_configuration:
                is_pushed = config.power_cap_configuration[0].push_object() and is_pushed
            if config.virtual_kvm_properties:
                is_pushed = config.virtual_kvm_properties[0].push_object() and is_pushed
            if config.secure_key_management:
                is_pushed = config.secure_key_management[0].push_object() and is_pushed

            self.parent.set_task_progression(70)

            if config.snmp:
                is_pushed = config.snmp[0].push_object() and is_pushed
            if config.smtp_properties:
                is_pushed = config.smtp_properties[0].push_object() and is_pushed
            if config.logging_controls:
                is_pushed = config.logging_controls[0].push_object() and is_pushed
            for platform_event_filter in config.platform_event_filters:
                is_pushed = platform_event_filter.push_object() and is_pushed
            if config.virtual_media:
                is_pushed = config.virtual_media[0].push_object() and is_pushed
            if config.serial_over_lan_properties:
                is_pushed = config.serial_over_lan_properties[0].push_object() and is_pushed

            self.parent.set_task_progression(80)

            if config.bios_settings:
                is_pushed = config.bios_settings[0].push_object() and is_pushed

            self.parent.set_task_progression(90)

            if config.ldap_settings:
                is_pushed = config.ldap_settings[0].push_object() and is_pushed
            if config.boot_order_properties:
                is_pushed = config.boot_order_properties[0].push_object() and is_pushed
            if config.dynamic_storage_zoning:
                is_pushed = config.dynamic_storage_zoning[0].push_object() and is_pushed
            for storage_controller in config.storage_controllers:
                is_pushed = storage_controller.push_object() and is_pushed
            for storage_flex_flash_controller in config.storage_flex_flash_controllers:
                is_pushed = storage_flex_flash_controller.push_object() and is_pushed

            if is_pushed:
                self.logger(message="Successfully pushed configuration " + str(config.uuid) + " to " + self.parent.target)

            # We disconnect from the device
            self.parent.disconnect()
            self.parent.set_task_progression(100)

            return True
        else:
            self.logger(level="error", message="No config to push!")
            return False

    def _fill_config_from_json(self, config=None, config_json=None):
        """
        Fills config using parsed JSON config file
        :param config: config to be filled
        :param config_json: parsed JSON content containing config
        :return: True if successful, False otherwise
        """
        if config is None or config_json is None:
            self.logger(level="debug", message="Missing config or config_json parameter!")
            return False

        # Put in order the items to append
        if "admin_networking" in config_json:
            config.admin_networking.append(UcsImcAdminNetwork(parent=config,
                                                              json_content=config_json["admin_networking"][0]))

        if "timezone_mgmt" in config_json:
            config.timezone_mgmt.append(UcsImcTimezoneMgmt(parent=config, json_content=config_json["timezone_mgmt"][0]))

        if "local_users" in config_json:
            for local_user in config_json["local_users"]:
                if "account_status" not in local_user:
                    config.local_users.append(UcsImcLocalUser(parent=config, json_content=local_user))
                elif local_user["account_status"] == "active":
                    config.local_users.append(UcsImcLocalUser(parent=config, json_content=local_user))

        if "local_users_properties" in config_json:
            config.local_users_properties.append(
                UcsImcLocalUsersProperties(parent=config, json_content=config_json["local_users_properties"][0]))

        if "server_properties" in config_json:
            config.server_properties.append(UcsImcServerProperties(parent=config,
                                                                   json_content=config_json["server_properties"][0]))

        if "ip_blocking_properties" in config_json:
            config.ip_blocking_properties.append(
                UcsImcIpBlockingProperties(parent=config, json_content=config_json["ip_blocking_properties"][0]))

        if "ip_filtering_properties" in config_json:
            config.ip_filtering_properties.append(
                UcsImcIpFilteringProperties(parent=config, json_content=config_json["ip_filtering_properties"][0]))

        if "power_policies" in config_json:
            config.power_policies.append(UcsImcPowerPolicies(parent=config,
                                                             json_content=config_json["power_policies"][0]))

        if "adapter_cards" in config_json:
            for adapter_card in config_json["adapter_cards"]:
                config.adapter_cards.append(UcsImcAdapterCard(parent=config, json_content=adapter_card))

        if "communications_services" in config_json:
            config.communications_services.append(
                UcsImcCommunicationsServices(parent=config, json_content=config_json["communications_services"][0]))

        if "device_connector" in config_json:
            config.device_connector.append(
                UcsDeviceConnector(parent=config, json_content=config_json["device_connector"][0]))

        if "chassis_inventory" in config_json:
            config.chassis_inventory.append(
                UcsImcChassisInventory(parent=config, json_content=config_json["chassis_inventory"][0]))
        if "power_cap_configuration" in config_json:
            config.power_cap_configuration.append(
                UcsImcPowerCapConfiguration(parent=config, json_content=config_json["power_cap_configuration"][0]))
        if "virtual_kvm_properties" in config_json:
            config.virtual_kvm_properties.append(
                UcsImcVKvmProperties(parent=config, json_content=config_json["virtual_kvm_properties"][0]))
        if "secure_key_management" in config_json:
            config.secure_key_management.append(
                UcsImcSecureKeyManagement(parent=config, json_content=config_json["secure_key_management"][0]))
        if "snmp" in config_json:
            config.snmp.append(
                UcsImcSnmp(parent=config, json_content=config_json["snmp"][0]))
        if "smtp_properties" in config_json:
            config.smtp_properties.append(
                UcsImcSmtpProperties(parent=config, json_content=config_json["smtp_properties"][0]))
        if "logging_controls" in config_json:
            config.logging_controls.append(
                UcsImcLoggingControls(parent=config, json_content=config_json["logging_controls"][0]))
        if "platform_event_filters" in config_json:
            for platform_event in config_json["platform_event_filters"]:
                config.platform_event_filters.append(UcsImcPlatformEventFilter(parent=config,
                                                                               json_content=platform_event))
        if "virtual_media" in config_json:
            config.virtual_media.append(
                UcsImcVirtualMedia(parent=config, json_content=config_json["virtual_media"][0]))
        if "serial_over_lan_properties" in config_json:
            config.serial_over_lan_properties.append(
                UcsImcSerialOverLanProperties(parent=config,
                                              json_content=config_json["serial_over_lan_properties"][0]))
        if "bios_settings" in config_json:
            config.bios_settings.append(
                UcsImcBios(parent=config, json_content=config_json["bios_settings"][0]))
        if "ldap_settings" in config_json:
            config.ldap_settings.append(
                UcsImcLdap(parent=config, json_content=config_json["ldap_settings"][0]))
        if "boot_order_properties" in config_json:
            config.boot_order_properties.append(
                UcsImcBootOrder(parent=config, json_content=config_json["boot_order_properties"][0]))
        if "dynamic_storage_zoning" in config_json:
            config.dynamic_storage_zoning.append(
                UcsImcDynamicStorageZoning(parent=config, json_content=config_json["dynamic_storage_zoning"][0]))
        if "storage_controllers" in config_json:
            for storage_controller in config_json["storage_controllers"]:
                config.storage_controllers.append(UcsImcStorageController(parent=config,
                                                                          json_content=storage_controller))
        if "storage_flex_flash_controllers" in config_json:
            for storage_flex_flash_controller in config_json["storage_flex_flash_controllers"]:
                config.storage_flex_flash_controllers.append(
                    UcsImcStorageFlexFlashController(parent=config, json_content=storage_flex_flash_controller))

        return True


class UcsCentralConfigManager(GenericUcsConfigManager):
    def __init__(self, parent=None):
        GenericUcsConfigManager.__init__(self, parent=parent)
        self.config_class_name = UcsCentralConfig

    def fetch_config(self, force=False):
        self.logger(message="Fetching config from live device (can take several minutes)")
        config = UcsCentralConfig(parent=self)
        config.metadata.origin = "live"
        config.metadata.easyucs_version = __version__
        config.load_from = "live"
        config._fetch_sdk_objects(force=force)

        # If any of the mandatory tasksteps fails then return None
        from api.api_server import easyucs
        if easyucs and self.parent.task and \
                easyucs.task_manager.is_any_taskstep_failed(uuid=self.parent.task.metadata.uuid):
            self.logger(level="error", message="Failed to fetch one or more SDK objects. Stopping the config fetch.")
            return None

        self.logger(level="debug", message="Finished fetching UCS SDK objects for config")

        # Put in order the items to append
        config.system.append(UcsCentralSystem(parent=config))

        for network_element in config.sdk_objects["networkElement"]:
            if network_element.dn.startswith("sys/"):
                config.management_interfaces.append(UcsCentralManagementInterface(parent=config,
                                                                                  network_element=network_element))

        config.date_time.append(UcsCentralDateTimeMgmt(parent=config))
        config.dns.append(UcsCentralDns(parent=config))
        config.syslog.append(UcsCentralSyslog(parent=config))
        config.snmp.append(UcsCentralSnmp(parent=config))
        config.password_profile.append(UcsCentralPasswordProfile(parent=config))

        for aaa_locale in config.sdk_objects['aaaLocale']:
            if "org-root/deviceprofile-default" in aaa_locale.dn:
                config.locales.append(UcsCentralLocale(parent=config, aaa_locale=aaa_locale))
        for aaa_role in config.sdk_objects["aaaRole"]:
            if "org-root/deviceprofile-default" in aaa_role.dn:
                config.roles.append(UcsCentralRole(parent=config, aaa_role=aaa_role))
        for aaa_user in config.sdk_objects["aaaUser"]:
            if "org-root/deviceprofile-default" in aaa_user.dn:
                config.local_users.append(UcsCentralLocalUser(parent=config, aaa_user=aaa_user))

        for org_org in sorted(config.sdk_objects["orgOrg"], key=lambda org: org.dn):
            if org_org.dn == "org-root":
                config.orgs.append(UcsCentralOrg(parent=config, org_org=org_org))
                break

        for org_domain_group in sorted(config.sdk_objects["orgDomainGroup"], key=lambda org: org.dn):
            if org_domain_group.dn == "domaingroup-root":
                config.domain_groups.append(UcsCentralDomainGroup(parent=config, org_domain_group=org_domain_group))
                break

        # Determining VxAN aliasing
        if config._determine_vxan_aliasing():
            self.logger(level="debug", message=self.parent.metadata.device_type_long + " config is using VxAN aliasing")

        # Removing the list of SDK objects fetched from the live UCS device
        config.sdk_objects = None
        self.config_list.append(config)
        self.logger(message="Finished fetching config with UUID " + str(config.uuid) + " from live device")
        return config.uuid

    def push_config(self, uuid=None, reset=False, bypass_version_checks=False, force=False):
        """
       Push the specified config to the live system
       :param uuid: The UUID of the config to be pushed. If not specified, the most recent config will be used
       :param reset: Whether the device must be reset before pushing the config
       :param bypass_version_checks: Whether the minimum version checks should be bypassed when connecting
       :param force: Force the push to proceed even in-case of critical errors.
       :return: True if config push was successful, False otherwise
       """
        if uuid is None:
            self.logger(level="debug", message="No config UUID specified in config push request. Using latest.")
            config = self.get_latest_config()
        else:
            # Find the config that needs to be pushed
            config_list = [config for config in self.config_list if config.uuid == uuid]
            if len(config_list) != 1:
                self.logger(level="error", message="Failed to locate config with UUID " + str(uuid) + " for push")
                return False
            else:
                config = config_list[0]
        if config:
            # Pushing configuration to the device
            # We first make sure we are connected to the device
            if not self.parent.connect(bypass_version_checks=bypass_version_checks):
                return False
            self.parent.set_task_progression(50)
            self.logger(message="Pushing configuration " + str(config.uuid) + " to " + self.parent.target)

            # We push all config elements, in a specific optimized order to reduce number of reboots
            is_pushed = True
            if config.system:
                is_pushed = config.system[0].push_object() and is_pushed
            for management_interface in config.management_interfaces:
                is_pushed = management_interface.push_object() and is_pushed
            for dns in config.dns:
                is_pushed = dns.push_object() and is_pushed
            for syslog in config.syslog:
                is_pushed = syslog.push_object() and is_pushed
            for snmp in config.snmp:
                is_pushed = snmp.push_object() and is_pushed
            if config.password_profile:
                is_pushed = config.password_profile[0].push_object() and is_pushed
            for locale in config.locales:
                is_pushed = locale.push_object() and is_pushed
            for role in config.roles:
                is_pushed = role.push_object() and is_pushed
            for local_user in config.local_users:
                is_pushed = local_user.push_object() and is_pushed

            if config.orgs:
                for org in config.orgs:
                    is_pushed = org.push_object() and is_pushed

            # We put these objects at the end, since they are likely to cause a disconnect
            for date_time in config.date_time:
                is_pushed = date_time.push_object() and is_pushed

            if is_pushed:
                self.logger(message="Successfully pushed configuration " + str(config.uuid) + " to " + self.parent.target)

            # We disconnect from the device
            self.parent.disconnect()
            self.parent.set_task_progression(100)

            return True
        else:
            self.logger(level="error", message="No config to push!")
            return False

    def _fill_config_from_json(self, config=None, config_json=None):
        """
        Fills config using parsed JSON config file
        :param config: config to be filled
        :param config_json: parsed JSON content containing config
        :return: True if successful, False otherwise
        """
        if config is None or config_json is None:
            self.logger(level="debug", message="Missing config or config_json parameter!")
            return False

        # Put in order the items to append
        if "system" in config_json:
            config.system.append(UcsCentralSystem(parent=config, json_content=config_json["system"][0]))
        if "management_interfaces" in config_json:
            for management_interface_json in config_json["management_interfaces"]:
                config.management_interfaces.append(
                    UcsCentralManagementInterface(parent=config, json_content=management_interface_json))
        if "date_time" in config_json:
            for date_time in config_json["date_time"]:
                config.date_time.append(UcsCentralDateTimeMgmt(parent=config, json_content=date_time))
        if "dns" in config_json:
            for dns in config_json["dns"]:
                config.dns.append(UcsCentralDns(parent=config, json_content=dns))
        if "syslog" in config_json:
            for syslog in config_json["syslog"]:
                config.syslog.append(UcsCentralSyslog(parent=config, json_content=syslog))
        if "snmp" in config_json:
            for snmp in config_json["snmp"]:
                config.snmp.append(UcsCentralSnmp(parent=config, json_content=snmp))
        if "password_profile" in config_json:
            for password_profile in config_json["password_profile"]:
                config.password_profile.append(UcsCentralPasswordProfile(parent=config, json_content=password_profile))
        if "locales" in config_json:
            for locale in config_json["locales"]:
                config.locales.append(UcsCentralLocale(parent=config, json_content=locale))
        if "roles" in config_json:
            for role in config_json["roles"]:
                config.roles.append(UcsCentralRole(parent=config, json_content=role))
        if "local_users" in config_json:
            for local_user in config_json["local_users"]:
                config.local_users.append(UcsCentralLocalUser(parent=config, json_content=local_user))

        if "orgs" in config_json:
            for org in config_json["orgs"]:
                if "name" in org:
                    if org["name"] == "root":
                        config.orgs.append(UcsCentralOrg(parent=config, json_content=org))
                    else:
                        self.logger(level="error",
                                    message="Org 'root' not found. Org 'root' is mandatory. " +
                                            "No org configuration will be fetched")
        if "domain_groups" in config_json:
            for dg in config_json["domain_groups"]:
                if "name" in dg:
                    if dg["name"] == "root":
                        config.domain_groups.append(UcsCentralDomainGroup(parent=config, json_content=dg))
                    else:
                        self.logger(level="error",
                                    message="Domain Group 'root' not found. Domain Group 'root' is mandatory. " +
                                            "No domain group configuration will be fetched")

        # Determining VxAN aliasing
        if config._determine_vxan_aliasing():
            self.logger(level="debug",
                        message=self.parent.metadata.device_type_long + " config is using VxAN aliasing")

        return True
