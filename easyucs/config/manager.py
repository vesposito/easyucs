# coding: utf-8
# !/usr/bin/env python

""" manager.py: Easy UCS Deployment Tool """
from easyucs import __author__, __copyright__,  __version__, __status__


import json
import jsonschema
import os
import re
import time
import urllib
import uuid
import copy

from packaging import version as packaging_version

from ucsmsdk.ucshandle import UcsHandle
from ucsmsdk.ucsexception import UcsException
from ucsmsdk.mometa.fabric.FabricEthLanEp import FabricEthLanEp

from imcsdk.imchandle import ImcHandle

from easyucs.config.config import UcsImcConfig, UcsSystemConfig, UcsCentralConfig
from easyucs.config.plot import UcsSystemConfigPlot, UcsSystemOrgConfigPlot, UcsSystemServiceProfileConfigPlot

from easyucs.config.ucs.ucsc.orgs import UcsCentralOrg
from easyucs.config.ucs.ucsc.domain_groups import UcsCentralDomainGroup
from easyucs.config.ucs.imc import UcsImcAdminNetwork, UcsImcLocalUser, UcsImcLocalUsersProperties, UcsImcServerProperties,\
    UcsImcTimezoneMgmt, UcsImcIpFilteringProperties, UcsImcIpBlockingProperties, UcsImcPowerPolicies,\
    UcsImcAdapterCard, UcsImcCommunicationsServices, UcsImcChassisInventory, UcsImcPowerCapConfiguration,\
    UcsImcVKvmProperties, UcsImcSecureKeyManagement, UcsImcSnmp, UcsImcSmtpProperties, UcsImcPlatformEventFilter,\
    UcsImcVirtualMedia, UcsImcSerialOverLanProperties, UcsImcBios, UcsImcLdap, UcsImcBootOrder,\
    UcsImcStorageController, UcsImcStorageFlexFlashController, UcsImcDynamicStorageZoning
from easyucs.config.ucs.admin import UcsSystemDns, UcsSystemInformation, UcsSystemManagementInterface, UcsSystemOrg, \
    UcsSystemTimezoneMgmt, UcsSystemLocalUser, UcsSystemRole, UcsSystemLocale, UcsSystemLocalUsersProperties, \
    UcsSystemCommunicationServices, UcsSystemGlobalPolicies, UcsSystemPreLoginBanner, UcsSystemBackupExportPolicy,\
    UcsSystemSelPolicy, UcsSystemSwitchingMode, UcsSystemUcsCentral, UcsSystemRadius, UcsSystemTacacs, UcsSystemLdap,\
    UcsSystemCallHome, UcsSystemPortAutoDiscoveryPolicy
from easyucs.config.ucs.lan import UcsSystemVlan, UcsSystemApplianceVlan, UcsSystemLanUplinkPort, UcsSystemLanPortChannel,\
    UcsSystemServerPort, UcsSystemAppliancePort, UcsSystemAppliancePortChannel, UcsSystemLanPinGroup,\
    UcsSystemVlanGroup, UcsSystemQosSystemClass, UcsSystemUnifiedStoragePort, UcsSystemUnifiedUplinkPort,\
    UcsSystemBreakoutPort, UcsSystemUdldLinkPolicy, UcsSystemLinkProfile, UcsSystemApplianceNetworkControlPolicy,\
    UcsSystemSlowDrainTimers
from easyucs.config.ucs.san import UcsSystemVsan, UcsSystemStorageVsan, UcsSystemSanUplinkPort, UcsSystemSanStoragePort,\
    UcsSystemFcoeUplinkPort, UcsSystemFcoeStoragePort, UcsSystemFcoePortChannel, UcsSystemSanPortChannel,\
    UcsSystemSanPinGroup, UcsSystemSanUnifiedPort, UcsSystemFcZoneProfile
from easyucs import export
from easyucs import common


class GenericConfigManager:
    def __init__(self, parent=None):
        self.config_class_name = None
        self.config_list = []
        self.parent = parent

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
            print("WARNING: No logger found in Inventory Manager")
            return None

    def fetch_config(self):
        return None

    def export_config(self, uuid=None, export_format="json", directory=None, filename=None):
        """
        Exports the specified config in the specified export format to the specified filename
        :param uuid: The UUID of the config to be exported. If not specified, the most recent config will be used
        :param export_format: The export format (e.g. "json")
        :param directory: The directory containing the export file
        :param filename: The name of the file containing the exported content
        :return: True if export is successful, False otherwise
        """
        if export_format not in ["json"]:
            self.logger(level="error", message="Requested config export format not supported!")
            return False
        if filename is None:
            self.logger(level="error", message="Missing filename in config export request!")
            return False
        if not directory:
            self.logger(level="debug",
                        message="No directory specified in config export request. Using local folder.")
            directory = "."

        if uuid is None:
            self.logger(level="debug", message="No config UUID specified in config export request. Using latest.")
            config = self.get_latest_config()
        else:
            # Find the config that needs to be exported
            config_list = [config for config in self.config_list if config.uuid == uuid]
            if len(config_list) != 1:
                self.logger(level="error", message="Failed to locate config with UUID " + str(uuid) + " for export")
                return False
            else:
                config = config_list[0]

        if config is None:
            # We could not find any config
            self.logger(level="error", message="Could not find any config to export!")
            return False
        if config.export_list is None or len(config.export_list) == 0:
            # Nothing to export
            self.logger(level="error", message="Nothing to export on the selected config!")
            return False

        self.logger(level="debug", message="Using config " + str(config.uuid) + " for export")

        if export_format == "json":
            self.logger(level="debug", message="Requested config export format is JSON")
            header_json = {}
            header_json["metadata"] = [export.generate_json_metadata_header(file_type="config", config=config)]
            config_json = {}
            config_json["easyucs"] = header_json
            config_json["config"] = {}
            for export_attribute in config.export_list:
                # We check if the attribute to be exported is an empty list, in which case, we don't export it
                if isinstance(getattr(config, export_attribute), list):
                    if len(getattr(config, export_attribute)) == 0:
                        continue
                config_json["config"][export_attribute] = []
                if isinstance(getattr(config, export_attribute), list):
                    count = 0
                    for config_object in getattr(config, export_attribute):
                        if isinstance(config_object, str):
                            config_json["config"][export_attribute].append(config_object)
                        elif isinstance(config_object, list):
                            config_json["config"][export_attribute].extend(config_object)
                        else:
                            config_json["config"][export_attribute].append({})
                            export.export_attributes_json(config_object,
                                                          config_json["config"][export_attribute][count])
                        count += 1
                elif isinstance(getattr(config, export_attribute), str):
                    config_json["config"][export_attribute] = getattr(config, export_attribute)
                else:
                    config_object = getattr(config, export_attribute)
                    config_json["config"][export_attribute].append({})
                    export.export_attributes_json(config_object, config_json["config"][export_attribute][0])

            # Calculate md5 hash of entire JSON file and adding it to header before exporting
            config_json = export.insert_json_metadata_hash(json_content=config_json)

            self.logger(message="Exporting config " + str(config.uuid) + " to file: " + directory + "/" + filename)
            if not os.path.exists(directory):
                self.logger(message="Creating directory " + directory)
                os.makedirs(directory)
            with open(directory + '/' + filename, 'w') as config_json_file:
                json.dump(config_json, config_json_file, indent=3)
            config_json_file.close()
            return True

    def import_config(self, import_format="json", directory=None, filename=None, config=None):
        """
        Imports the specified config in the specified import format from the specified filename
        :param import_format: The import format (e.g. "json")
        :param directory: The directory containing the import file
        :param filename: The name of the file containing the content to be imported
        :param config: The config content to be imported (if no directory/filename provided)
        :return: True if import is successful, False otherwise
        """
        if import_format not in ["json"]:
            self.logger(level="error", message="Requested config import format not supported!")
            return False

        # If no config content is provided, we need to open the file using directory and filename arguments
        if config is None:
            if filename is None:
                self.logger(level="error", message="Missing filename in config import request!")
                return False
            if directory is None:
                self.logger(level="debug",
                            message="No directory specified in config import request. Using local folder.")
                directory = "."

            # Making sure config file exists
            if not os.path.exists(directory + '/' + filename):
                self.logger(level="error",
                            message="Requested config file: " + directory + "/" + filename + " does not exist!")
                return False

            if import_format == "json":
                self.logger(level="debug", message="Requested config import format is JSON")
                with open(directory + '/' + filename, 'r') as config_json_file:
                    try:
                        complete_json = json.load(config_json_file)
                    except json.decoder.JSONDecodeError as err:
                        self.logger(level="error",
                                    message="Invalid config JSON file " + directory + "/" + filename + ": " + str(err))
                        return False
                config_json_file.close()

        else:
            if import_format == "json":
                self.logger(level="debug", message="Requested config import format is JSON")
                if isinstance(config, str):
                    complete_json = json.loads(config)
                elif isinstance(config, dict):
                    complete_json = config
                else:
                    self.logger(level="error", message="Unable to import config")
                    return False

        if import_format in ["json"]:
            # We verify that the JSON content is valid
            if not self._validate_config_from_json(config_json=complete_json):
                self.logger(message="Can't import invalid config JSON file")
                return False
            else:
                self.logger(message="Successfully validated config JSON file")

            # We verify the hash of the file to check if it has been modified
            custom = False
            if not export.verify_json_metadata_hash(json_content=complete_json):
                self.logger(message="Hash of the imported file does not verify. Config will be marked as custom")
                custom = True

            # We make sure there is a "config" section in the file
            if "config" in complete_json:
                config_json = complete_json["config"]
            else:
                self.logger(level="error", message="No config section in JSON file. Could not import config")
                return False

            # We create a new config object
            config = self.config_class_name(parent=self)
            config.load_from = "file"

            # We set the origin of the config as "import"
            config.origin = "import"

            # We set the custom flag of the config
            if custom:
                config.custom = True

            # We fetch all options set in "easyucs" section of the file
            if "easyucs" in complete_json:
                if "options" in complete_json["easyucs"]:
                    self.logger(level="debug", message="Importing options from config file")
                    for option in complete_json["easyucs"]["options"]:
                        config.options.update(option)
                if "metadata" in complete_json["easyucs"]:
                    if "uuid" in complete_json["easyucs"]["metadata"][0]:
                        config.uuid = uuid.UUID(complete_json["easyucs"]["metadata"][0]["uuid"])
                    if "device_version" in complete_json["easyucs"]["metadata"][0]:
                        config.device_version = complete_json["easyucs"]["metadata"][0]["device_version"]
                    if "intersight_status" in complete_json["easyucs"]["metadata"][0]:
                        config.intersight_status = complete_json["easyucs"]["metadata"][0]["intersight_status"]

            # We start filling up the config
            self.logger(message="Importing config from " + import_format)
            result = self._fill_config_from_json(config=config, config_json=config_json)
            if result:
                self.logger(message="Config import successful. Appending config to the list of configs for device " +
                                    str(self.parent.uuid))
                # We add the config to the list of configs
                self.config_list.append(config)
                return True
            else:
                self.logger(level="error", message="Config import failed!")
                return False

    def _validate_config_from_json(self, config_json=None):
        pass

    def push_config(self, uuid=None):
        """
        Push the specified config on the live system
        :param uuid: The UUID of the config to be exported. If not specified, the most recent config will be used
        :return: True if config push was successful, False otherwise
        """
        return False

    def _fill_config_from_json(self, config=None, config_json=None):
        """
        Fills config using parsed JSON config file
        :param config: config to be filled
        :param config_json: parsed JSON content containing config
        :return: True if successful, False otherwise
        """
        return False

    def get_latest_config(self):
        """
        Returns the most recent config from the config list
        :return: GenericConfig (or subclass), None if no config is found
        """
        if len(self.config_list) == 0:
            return None
        return sorted(self.config_list, key=lambda config: config.timestamp)[-1]

    def find_config_by_uuid(self, uuid):
        """
        Search a config with a specific UUID

        :param uuid:
        :return: config if found, None otherwise
        """

        config_list = [config for config in self.config_list if str(config.uuid) == str(uuid)]
        if len(config_list) != 1:
            self.logger(level="error", message="Failed to locate config with UUID " + str(uuid))
            return None
        else:
            return config_list[0]

    def remove_config(self, uuid):
        """
        Removes the specified config from the repository
        :param uuid: The UUID of the config to be deleted
        :return: True if delete is successful, False otherwise
        """

        # Find the config that needs to be removed
        config = self.find_config_by_uuid(uuid=uuid)
        if not config:
            return False
        else:
            config_to_remove = config

        # Remove the config from the list of devices
        self.config_list.remove(config_to_remove)

        # Delete the config in the repository
        directory = "repository/" + str(self.parent.uuid) + "/configs/config-" + str(uuid) + ".json"

        if os.path.exists(directory):
            os.remove(directory)
        else:
            print("Config not found in repository. Nothing to delete.")
            return False

        return True


class GenericUcsConfigManager(GenericConfigManager):
    def __init__(self, parent=None):
        GenericConfigManager.__init__(self, parent=parent)

    def export_config_plots(self, config=None, export_format="png", directory=None):
        pass

    def generate_config_plots(self, config=None):
        pass


class UcsSystemConfigManager(GenericUcsConfigManager):
    def __init__(self, parent=None):
        GenericUcsConfigManager.__init__(self, parent=parent)
        self.config_class_name = UcsSystemConfig

    def generate_config_plots(self, config=None):
        if config is None:
            config = self.get_latest_config()
            self.logger(level="debug",
                        message="No config UUID specified in generate config plots request. Using latest.")

            if config is None:
                self.logger(level="error", message="No config found. Unable to generate config plots.")
                return False

        self.logger(level="debug", message="Generating plots for device " + self.parent.target + " using config: " +
                                           str(config.uuid))

        config.service_profile_plots = UcsSystemServiceProfileConfigPlot(parent=self, config=config)
        if config.orgs[0].orgs:  # If 'root' is not the only organization
            config.orgs_plot = UcsSystemOrgConfigPlot(parent=self, config=config)

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

    def fetch_config(self):
        self.logger(message="Fetching config from live device (can take several minutes)")
        config = UcsSystemConfig(parent=self)
        config.origin = "live"
        config.load_from = "live"
        config._fetch_sdk_objects()
        self.logger(level="debug", message="Finished fetching UCS SDK objects for config")

        # Put in order the items to append
        config.system.append(UcsSystemInformation(parent=config))
        config.pre_login_banner = UcsSystemPreLoginBanner(parent=config).message
        config.timezone_mgmt.append(UcsSystemTimezoneMgmt(parent=config))
        config.switching_mode.append(UcsSystemSwitchingMode(parent=config))
        config.communication_services.append(UcsSystemCommunicationServices(parent=config))
        config.radius.append(UcsSystemRadius(parent=config))
        config.tacacs.append(UcsSystemTacacs(parent=config))
        config.ldap.append(UcsSystemLdap(parent=config))
        config.call_home.append(UcsSystemCallHome(parent=config))
        config.backup_export_policy.append(UcsSystemBackupExportPolicy(parent=config))
        config.global_policies.append(UcsSystemGlobalPolicies(parent=config))
        config.dns.extend(UcsSystemDns(parent=config).dns)
        config.local_users_properties.append(UcsSystemLocalUsersProperties(parent=config))
        config.sel_policy.append(UcsSystemSelPolicy(parent=config))
        config.port_auto_discovery_policy.append(UcsSystemPortAutoDiscoveryPolicy(parent=config))

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

        for fabric_eth_lan_ep in config.sdk_objects["fabricEthLanEp"]:
            config.lan_uplink_ports.append(UcsSystemLanUplinkPort(parent=config, fabric_eth_lan_ep=fabric_eth_lan_ep))

        # We also add server ports that are part of a port-channel (fabricDceSwSrvPcEp) since they are auto created
        for fabric_dce_sw_srv_ep in sorted(config.sdk_objects["fabricDceSwSrvEp"] +
                                           config.sdk_objects["fabricDceSwSrvPcEp"],
                                           key=lambda port: [int(t) if t.isdigit() else t.lower()
                                                             for t in re.split('(\d+)', port.dn)]):
            config.server_ports.append(UcsSystemServerPort(parent=config, fabric_dce_sw_srv_ep=fabric_dce_sw_srv_ep))

        for fabric_eth_estc_ep in config.sdk_objects["fabricEthEstcEp"]:
            config.appliance_ports.append(UcsSystemAppliancePort(parent=config, fabric_eth_estc_ep=fabric_eth_estc_ep))

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

        for fabric_fcoe_estc_ep in config.sdk_objects["fabricFcoeEstcEp"]:
            config.fcoe_storage_ports.append(UcsSystemFcoeStoragePort(parent=config,
                                                                      fabric_fcoe_estc_ep=fabric_fcoe_estc_ep))

        for ether_pio in config.sdk_objects["etherPIo"]:
            if ether_pio.if_role == "network-fcoe-uplink":
                config.unified_uplink_ports.append(UcsSystemUnifiedUplinkPort(parent=config, ether_pio=ether_pio))
        
        for ether_pio in config.sdk_objects["etherPIo"]:
            if ether_pio.if_role == "fcoe-nas-storage":
                config.unified_storage_ports.append(UcsSystemUnifiedStoragePort(parent=config, ether_pio=ether_pio))

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
            config.vlan_groups.append(UcsSystemVlanGroup(parent=config, fabric_net_group=fabric_net_group))

        for fabric_lan_pin_group in config.sdk_objects["fabricLanPinGroup"]:
            config.lan_pin_groups.append(UcsSystemLanPinGroup(parent=config, fabric_lan_pin_group=fabric_lan_pin_group))
            
        for fabric_san_pin_group in config.sdk_objects["fabricSanPinGroup"]:
            config.san_pin_groups.append(UcsSystemSanPinGroup(parent=config, fabric_san_pin_group=fabric_san_pin_group))
            
        if "fabricBreakout" in config.sdk_objects:
            for fabric_breakout in config.sdk_objects["fabricBreakout"]:
                config.breakout_ports.append(UcsSystemBreakoutPort(parent=config, fabric_breakout=fabric_breakout))

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

        for org_org in sorted(config.sdk_objects["orgOrg"], key=lambda org: org.dn):
            if org_org.dn == "org-root":
                config.orgs.append(UcsSystemOrg(parent=config, org_org=org_org))

        # Removing the list of SDK objects fetched from the live UCS device
        config.sdk_objects = None
        self.config_list.append(config)
        self.logger(message="Finished fetching config with UUID " + str(config.uuid) + " from live device")
        return config.uuid

    def push_config(self, uuid=None, reset=False, fi_ip_list=[], bypass_version_checks=False):
        """
        Push the specified config to the live system
        :param uuid: The UUID of the config to be pushed. If not specified, the most recent config will be used
        :param reset: Whether or not the device must be reset before pushing the config
        :param fi_ip_list: List of DHCP IP addresses taken by each FI after the reset
        :param bypass_version_checks: Whether or not the minimum version checks should be bypassed when connecting
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
                # Check if the DHCP IP addresses are available before resetting
                if not fi_ip_list:
                    self.logger(level="error", message="No DHCP IP addresses given")
                    return False
                # TODO Check if IP addresses are valid

                # Check if the admin password is available before resetting
                for user in config.local_users:
                    if user.id:
                        if user.id == "admin":
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
                    self.logger(level="error", message="Error while performing device reset")
                    return False

                # Clearing device target, username & password since they might change in the new config
                self.parent.target = ""
                self.parent.username = ""
                self.parent.password = ""

                if self.parent.sys_mode == "cluster":
                    self.logger(message="Waiting up to 780 seconds for both Fabric Interconnects to come back")
                elif self.parent.sys_mode == "stand-alone":
                    self.logger(message="Waiting up to 780 seconds for Fabric Interconnect to come back")
                time.sleep(300)

                if not self.parent.wait_for_reboot_after_reset(timeout=480, fi_ip_list=fi_ip_list):
                    self.logger(level="error", message="Could not reconnect to Fabric Interconnect(s) after reset")
                    return False
                self.parent.set_task_progression(20)

                # Performing initial setup
                self.logger(message="Performing initial setup using the following IP address(es): " + str(fi_ip_list))
                if not self.parent.initial_setup(fi_ip_list=fi_ip_list, config=config):
                    self.logger(level="error", message="Error while performing initial setup")
                    return False

                # Wait loop for FI cluster election to complete
                if self.parent.sys_mode == "cluster":
                    self.logger(message="Waiting up to 240 seconds for cluster election to complete")
                    time.sleep(80)

                    if config.system:
                        if config.system[0].virtual_ip:
                            self.parent.target = config.system[0].virtual_ip
                        elif config.system[0].virtual_ipv6:
                            self.parent.target = config.system[0].virtual_ipv6
                    if not self.parent.target:
                        self.logger(level="error", message="Could not determine target IP of the device")
                        return False

                elif self.parent.sys_mode == "stand-alone":
                    self.logger(message="Waiting up to 180 seconds for initial configuration to complete")
                    time.sleep(20)

                    # TODO Handle Ipv6
                    if config.management_interfaces:
                        for management_interface in config.management_interfaces:
                            if management_interface.fabric.upper() == 'A':
                                if management_interface.ip:
                                    self.parent.target = management_interface.ip

                    if not self.parent.target:
                        self.logger(level="error",
                                          message="Could not determine target IP of the device in the config")
                        return False

                if not config.local_users:
                    # Could not find local_users in config - Admin password is a mandatory parameter - Exiting
                    self.logger(level="error", message="Could not find users in config")
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
                                self.logger(level="warning",
                                            message="Could not find password for user id admin in config.")
                                return False

                # We need to refresh the UCS device handle so that it has the right attributes
                self.parent.handle = UcsHandle(ip=self.parent.target, username=self.parent.username,
                                               password=self.parent.password)
                # We also need to refresh the config handle
                config.refresh_config_handle()

                if not common.check_web_page(device=self.parent, url="https://" + self.parent.target, str_match="Cisco",
                                             timeout=160):
                    self.logger(level="error", message="Impossible to reconnect to UCS system")
                    return False
                self.parent.set_task_progression(40)

                # Reconnecting and waiting for HA cluster to be ready (if in cluster mode)
                # or FI to be ready (if in stand-alone mode)
                if not self.parent.connect(bypass_version_checks=True, retries=3):
                    self.logger(level="error", message="Impossible to reconnect to UCS system")
                    return False
                if self.parent.sys_mode == "cluster":
                    self.logger(message="Waiting up to 300 seconds for UCS HA cluster to be ready...")
                    if not self.parent.wait_for_ha_cluster_ready(timeout=300):
                        self.logger(level="error",
                                    message="Timeout exceeded while waiting for UCS HA cluster to be in ready state")
                        return False
                elif self.parent.sys_mode == "stand-alone":
                    self.logger(message="Waiting up to 300 seconds for UCS stand-alone FI to be ready...")
                    if not self.parent.wait_for_standalone_fi_ready(timeout=300):
                        self.logger(level="error",
                                    message="Timeout exceeded while waiting for UCS stand-alone FI to be ready")
                        return False
                self.parent.set_task_progression(45)

                # We bypass version checks for the rest of the procedure as potential warning has already been made
                bypass_version_checks = True

            # Pushing configuration to the device
            # We first make sure we are connected to the device
            if not self.parent.connect(bypass_version_checks=bypass_version_checks, force=True):
                return False

            self.parent.set_task_progression(50)
            self.logger(message="Pushing configuration " + str(config.uuid) + " to " + self.parent.target)

            # We push all config elements, in a specific optimized order to reduce number of reboots
            self.logger(message="Now configuring Admin section")
            if config.system:
                config.system[0].push_object()
            for management_interface in config.management_interfaces:
                management_interface.push_object()
            if config.call_home:
                config.call_home[0].push_object()
            for timezone_mgmt in config.timezone_mgmt:
                timezone_mgmt.push_object()
            if config.local_users_properties:
                config.local_users_properties[0].push_object()
            if config.dns:
                # Exception for DNS
                dns = UcsSystemDns(parent=config)
                dns.dns = config.dns
                dns.push_object()
            if config.pre_login_banner:
                banner = UcsSystemPreLoginBanner(parent=config)
                banner.message = config.pre_login_banner
                banner.push_object()
            if config.communication_services:
                config.communication_services[0].push_object()
            for locale in config.locales:
                locale.push_object()
            for role in config.roles:
                role.push_object()
            for local_user in config.local_users:
                local_user.push_object()
            if config.backup_export_policy:
                config.backup_export_policy[0].push_object()
            if config.radius:
                config.radius[0].push_object()
            if config.tacacs:
                config.tacacs[0].push_object()
            if config.ldap:
                config.ldap[0].push_object()

            self.parent.set_task_progression(60)

            self.logger(message="Now configuring Equipment section")
            if config.global_policies:
                config.global_policies[0].push_object()
            if config.sel_policy:
                config.sel_policy[0].push_object()
            if config.slow_drain_timers:
                config.slow_drain_timers[0].push_object()
            for qos_system_class in config.qos_system_class:
                if config.check_if_switching_mode_config_requires_reboot() and\
                        self.parent.fi_a_model == "UCS-FI-6332-16UP":
                    self.logger(level="debug",
                                message="The QoS System Class will be committed alongside the Switching Mode push")
                    qos_system_class.push_object(commit=False)
                else:
                    qos_system_class.push_object()

            for switching_mode in config.switching_mode:
                switching_mode.push_object()

            self.parent.set_task_progression(65)

            self.logger(message="Now configuring VLAN/VSAN section")
            for vlan in config.vlans:
                # Handling range of VLAN
                if vlan.prefix:
                    start = int(vlan.id_from)
                    stop = int(vlan.id_to)
                    for i in range(start, stop+1):
                        vlan_temp = copy.deepcopy(vlan)
                        vlan_temp.id = str(i)
                        vlan_temp.name = vlan_temp.prefix + vlan_temp.id
                        vlan_temp.push_object()
                else:
                    vlan.push_object()

            for vlan in config.appliance_vlans:
                # Handling range of Appliance VLAN
                if vlan.prefix:
                    start = int(vlan.id_from)
                    stop = int(vlan.id_to)
                    for i in range(start, stop+1):
                        vlan_temp = copy.deepcopy(vlan)
                        vlan_temp.id = str(i)
                        vlan_temp.name = vlan_temp.prefix + vlan_temp.id
                        vlan_temp.push_object()
                else:
                    vlan.push_object()
            for vlan_group in config.vlan_groups:
                vlan_group.push_object()
            for vsan in config.vsans:
                vsan.push_object()
            for storage_vsan in config.storage_vsans:
                storage_vsan.push_object()

            self.parent.set_task_progression(70)

            self.logger(message="Now configuring FI ports")
            # The following section might need a reboot of the FIs
            # We do not commit yet to avoid multiple configuration requests of the same port id
            for breakout_port in config.breakout_ports:
                breakout_port.push_object(commit=False)
            for san_uplink_port in config.san_uplink_ports:
                san_uplink_port.push_object(commit=False)
            for san_storage_port in config.san_storage_ports:
                san_storage_port.push_object(commit=False)
            for san_unified_port in config.san_unified_ports:
                san_unified_port.push_object(commit=False)

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
                    port.push_object(commit=False)

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

            self.parent.set_task_progression(75)

            # Reboot handling
            if need_reboot:
                self.logger(message="Caution: The system will reboot in a few seconds!")
                self.logger(message="Waiting up to 900 seconds for FIs to come back")
                time.sleep(420)

                if not common.check_web_page(device=self.parent, url="https://" + self.parent.target, str_match="Cisco",
                                             timeout=480):
                    self.logger(level="error", message="Impossible to reconnect to UCS system")
                    return False

                # Need to reconnect
                self.parent.connect(bypass_version_checks=True)
                self.logger(message="Reconnected to system: " + self.parent.name + " running version: " +
                                    self.parent.version.version)

                # We now fetch the HA state to make sure both FIs are back online and in sync. This is to avoid the
                # case where a single FI has rebooted with port type changes, and UCS Manager responds on the remaining
                # FI before reboot is complete. This lead to UCS Manager not knowing about those port type changes
                # We only do this if we are in cluster mode
                if self.parent.sys_mode == "cluster":
                    self.logger(message="Waiting up to 300 seconds for UCS HA cluster to be ready...")
                    if not self.parent.wait_for_ha_cluster_ready(timeout=300):
                        self.logger(level="error",
                                    message="Timeout exceeded while waiting for UCS HA cluster to be in ready state")
                        return False

                    # We now fetch the FSM state of the physical ports configuration to make sure it is 100%, in order
                    # to make sure the new port configuration has been taken into account before configuring anything
                    # else
                    self.logger(message="Waiting up to 300 seconds for FSM state of physical ports to reach 100%...")
                    if not self.parent.wait_for_fsm_complete(ucs_sdk_object_class="swPhys", timeout=300):
                        self.logger(level="error", message="Timeout exceeded while waiting for FSM state of physical " +
                                                           "ports to reach 100%")
                        return False

            # End of section needing reboot of the FI

            # We now need to push the config to ports that are in Breakout or were converted back to native
            # as they were excluded previously in case a reboot was needed
            for port in ports_with_aggr_id + ports_converted_to_native_40g:
                port.push_object()

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
                server_port.push_object()
                if ordered_discovery:
                    # Adding a sleep timer to make sure chassis/rack servers are discovered in order
                    time.sleep(20)

            self.parent.set_task_progression(85)

            for lan_port_channel in config.lan_port_channels:
                lan_port_channel.push_object()
            for fcoe_port_channel in config.fcoe_port_channels:
                fcoe_port_channel.push_object()
            for san_port_channel in config.san_port_channels:
                san_port_channel.push_object()
            for appliance_port_channel in config.appliance_port_channels:
                appliance_port_channel.push_object()

            for lan_pin_group in config.lan_pin_groups:
                lan_pin_group.push_object()
            for san_pin_group in config.san_pin_groups:
                san_pin_group.push_object()

            for fc_zone_profile in config.fc_zone_profiles:
                fc_zone_profile.push_object()

            for udld_link_policy in config.udld_link_policies:
                udld_link_policy.push_object()
            for link_profile in config.link_profiles:
                link_profile.push_object()
            for appliance_network_control_policy in config.appliance_network_control_policies:
                appliance_network_control_policy.push_object()

            for port_auto_discovery_policy in config.port_auto_discovery_policy:
                port_auto_discovery_policy.push_object()

            self.parent.set_task_progression(90)

            for org in config.orgs:
                org.push_object()

            # We handle UCS Central at the very end, because it might push config to the UCS system and create
            # connectivity issues
            if config.ucs_central:
                config.ucs_central[0].push_object()

            self.logger(message="Successfully pushed configuration " + str(config.uuid) + " to " + self.parent.target)

            # We disconnect from the device
            self.parent.disconnect()
            self.parent.set_task_progression(100)

        else:
            self.logger(level="error", message="No config to push!")
            return False

    def _validate_config_from_json(self, config_json=None):
        """
        Validates a config using the JSON schema definition
        :param config_json: JSON content containing config to be validated
        :return: True if config is valid, False otherwise
        """

        # Open JSON master schema for a UCS System config
        json_file = open("schema/ucs/ucsm/master.json")
        json_string = json_file.read()
        json_file.close()
        json_schema = json.loads(json_string)

        schema_path = 'file:///{0}/'.format(
            os.path.dirname(os.path.abspath("schema/ucs/ucsm/master.json")).replace("\\", "/"))
        resolver = jsonschema.RefResolver(schema_path, json_schema)
        format_checker = jsonschema.FormatChecker()

        try:
            jsonschema.validate(config_json, json_schema, resolver=resolver, format_checker=format_checker)
        except jsonschema.ValidationError as err:
            absolute_path = []
            for path in err.absolute_path:
                absolute_path.append(path)

            # TODO: Improve error logging by providing a simple explanation when JSON file is not valid
            self.logger(level="error", message="Invalid config JSON file in " + str(absolute_path))
            self.logger(level="error", message="Failed to validate config JSON file using schema: " + str(err.message))
            return False
        except jsonschema.SchemaError as err:
            self.logger(level="error", message="Failed to validate config JSON file due to schema error: " + str(err))
            return False

        # We now validate that the easyucs_version of the file is not greater than the running version of EasyUCS
        easyucs_version_from_file = config_json["easyucs"]["metadata"][0]["easyucs_version"]
        if packaging_version.parse(easyucs_version_from_file) > packaging_version.parse(__version__):
            self.logger(level="error",
                        message="Failed to validate config JSON file because it has been created using a more " +
                                "recent version of EasyUCS (" + easyucs_version_from_file + " > " + __version__ + ")")
            return False

        return True
    
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
        if "radius" in config_json:
            config.radius.append(UcsSystemRadius(parent=config, json_content=config_json["radius"][0]))
        if "tacacs" in config_json:
            config.tacacs.append(UcsSystemTacacs(parent=config, json_content=config_json["tacacs"][0]))
        if "ldap" in config_json:
            config.ldap.append(UcsSystemLdap(parent=config, json_content=config_json["ldap"][0]))
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

    def fetch_config(self):
        self.logger(message="Fetching config from live device (can take several minutes)")
        config = UcsImcConfig(parent=self)
        config.origin = "live"
        config.load_from = "live"
        config._fetch_sdk_objects()
        self.logger(level="debug", message="Finished fetching UCS SDK objects for config")

        # Put in order the items to append
        config.admin_networking.append(UcsImcAdminNetwork(parent=config))
        config.timezone_mgmt.append(UcsImcTimezoneMgmt(parent=config))
        for local_user in config.sdk_objects["aaaUser"]:
            if local_user.account_status != "inactive":
                config.local_users.append(UcsImcLocalUser(parent=config, aaa_user=local_user))
        config.local_users_properties.append(UcsImcLocalUsersProperties(parent=config))
        config.server_properties.append(UcsImcServerProperties(parent=config))
        config.ip_blocking_properties.append(UcsImcIpBlockingProperties(parent=config))
        config.ip_filtering_properties.append(UcsImcIpFilteringProperties(parent=config))
        config.power_policies.append(UcsImcPowerPolicies(parent=config))
        for adapter_card in config.sdk_objects["adaptorUnit"]:
            config.adapter_cards.append(UcsImcAdapterCard(parent=config, adaptor_unit=adapter_card))
        config.communications_services.append(UcsImcCommunicationsServices(parent=config))
        config.chassis_inventory.append(UcsImcChassisInventory(parent=config))
        config.power_cap_configuration.append(UcsImcPowerCapConfiguration(parent=config))
        config.virtual_kvm_properties.append(UcsImcVKvmProperties(parent=config))
        config.secure_key_management.append(UcsImcSecureKeyManagement(parent=config))
        config.snmp.append(UcsImcSnmp(parent=config))
        config.smtp_properties.append(UcsImcSmtpProperties(parent=config))
        for platform_event_filter in config.sdk_objects["platformEventFilters"]:
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
        for storage_controller in config.sdk_objects["storageController"]:
            config.storage_controllers.append(UcsImcStorageController(parent=config,
                                                                      storage_controller=storage_controller))
        for storage_flex_flash_controller in config.sdk_objects["storageFlexFlashController"]:
            config.storage_flex_flash_controllers.append(
                UcsImcStorageFlexFlashController(parent=config, storage_controller=storage_flex_flash_controller))

        # Removing the list of SDK objects fetched from the live UCS device
        config.sdk_objects = None
        self.config_list.append(config)
        self.logger(message="Finished fetching config with UUID " + str(config.uuid) + " from live device")
        return config.uuid

    def push_config(self, uuid=None, reset=False, imc_ip=None, bypass_version_checks=False):
        """
       Push the specified config to the live system
       :param uuid: The UUID of the config to be pushed. If not specified, the most recent config will be used
       :param reset: Whether or not the device must be reset before pushing the config
       :param imc_ip: DHCP IP address taken by the CIMC after the reset
       :param bypass_version_checks: Whether or not the minimum version checks should be bypassed when connecting
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
            if config.admin_networking:
                config.admin_networking[0].push_object()
            if config.timezone_mgmt:
                config.timezone_mgmt[0].push_object()
            if config.local_users_properties:
                config.local_users_properties[0].push_object()
            for local_user in config.local_users:
                local_user.push_object()

            self.parent.set_task_progression(60)

            if config.server_properties:
                config.server_properties[0].push_object()
            if config.ip_blocking_properties:
                config.ip_blocking_properties[0].push_object()
            if config.ip_filtering_properties:
                config.ip_filtering_properties[0].push_object()
            if config.power_policies:
                config.power_policies[0].push_object()
            for adapter_card in config.adapter_cards:
                adapter_card.push_object()
            if config.communications_services:
                config.communications_services[0].push_object()
            if config.chassis_inventory:
                config.chassis_inventory[0].push_object()
            if config.power_cap_configuration:
                config.power_cap_configuration[0].push_object()
            if config.virtual_kvm_properties:
                config.virtual_kvm_properties[0].push_object()
            if config.secure_key_management:
                config.secure_key_management[0].push_object()

            self.parent.set_task_progression(70)

            if config.snmp:
                config.snmp[0].push_object()
            if config.smtp_properties:
                config.smtp_properties[0].push_object()
            for platform_event_filter in config.platform_event_filters:
                platform_event_filter.push_object()
            if config.virtual_media:
                config.virtual_media[0].push_object()
            if config.serial_over_lan_properties:
                config.serial_over_lan_properties[0].push_object()

            self.parent.set_task_progression(80)

            if config.bios_settings:
                config.bios_settings[0].push_object()

            self.parent.set_task_progression(90)

            if config.ldap_settings:
                config.ldap_settings[0].push_object()
            if config.boot_order_properties:
                config.boot_order_properties[0].push_object()
            if config.dynamic_storage_zoning:
                config.dynamic_storage_zoning[0].push_object()
            for storage_controller in config.storage_controllers:
                storage_controller.push_object()
            for storage_flex_flash_controller in config.storage_flex_flash_controllers:
                storage_flex_flash_controller.push_object()

            self.logger(message="Successfully pushed configuration " + str(config.uuid) + " to " + self.parent.target)

            # We disconnect from the device
            self.parent.disconnect()
            self.parent.set_task_progression(100)

    def _validate_config_from_json(self, config_json=None):
        """
        Validates a config using the JSON schema definition
        :param config_json: JSON content containing config to be validated
        :return: True if config is valid, False otherwise
        """

        # Open JSON master schema for a UCS CIMC config
        json_file = open("schema/ucs/cimc/master.json")
        json_string = json_file.read()
        json_file.close()
        json_schema = json.loads(json_string)

        schema_path = 'file:///{0}/'.format(
            os.path.dirname(os.path.abspath("schema/ucs/cimc/master.json")).replace("\\", "/"))
        resolver = jsonschema.RefResolver(schema_path, json_schema)
        format_checker = jsonschema.FormatChecker()

        try:
            jsonschema.validate(config_json, json_schema, resolver=resolver, format_checker=format_checker)
        except jsonschema.ValidationError as err:
            absolute_path = []
            while True:
                try:
                    value = err.absolute_path.popleft()
                    if value != 0:
                        absolute_path.append(value)
                except IndexError:
                    break
            # TODO: Improve error logging by providing a simple explanation when JSON file is not valid
            self.logger(level="error", message="Invalid config JSON file in " + str(absolute_path))
            self.logger(level="error", message="Failed to validate config JSON file using schema: " + str(err.message))
            return False
        except jsonschema.SchemaError as err:
            self.logger(level="error", message="Failed to validate config JSON file due to schema error: " + str(err))
            return False

        # We now validate that the easyucs_version of the file is not greater than the running version of EasyUCS
        easyucs_version_from_file = config_json["easyucs"]["metadata"][0]["easyucs_version"]
        if packaging_version.parse(easyucs_version_from_file) > packaging_version.parse(__version__):
            self.logger(level="error",
                        message="Failed to validate config JSON file because it has been created using a more " +
                                "recent version of EasyUCS (" + easyucs_version_from_file + " > " + __version__ + ")")
            return False

        return True

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
                        config.orgs.append(UcsCentralDomainGroup(parent=config, json_content=dg))
                    else:
                        self.logger(level="error",
                                    message="Domain Group 'root' not found. Domain Group 'root' is mandatory. " +
                                            "No domain group configuration will be fetched")
        return True

    def push_config(self, uuid=None, bypass_version_checks=False):
        """
       Push the specified config to the live system
       :param uuid: The UUID of the config to be pushed. If not specified, the most recent config will be used
       :param bypass_version_checks: Whether or not the minimum version checks should be bypassed when connecting
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
            if config.orgs:
                for org in config.orgs:
                    org.push_object()

            self.logger(message="Successfully pushed configuration " + str(config.uuid) + " to " + self.parent.target)

            # We disconnect from the device
            self.parent.disconnect()
            self.parent.set_task_progression(100)

    def fetch_config(self):
        self.logger(message="Fetching config from live device (can take several minutes)")
        config = UcsCentralConfig(parent=self)
        config.origin = "live"
        config.load_from = "live"
        config._fetch_sdk_objects()
        self.logger(level="debug", message="Finished fetching UCS SDK objects for config")

        # Put in order the items to append
        for org_org in sorted(config.sdk_objects["orgOrg"], key=lambda org: org.dn):
            if org_org.dn == "org-root":
                config.orgs.append(UcsCentralOrg(parent=config, org_org=org_org))
        for org_domain_group in sorted(config.sdk_objects["orgDomainGroup"], key=lambda org: org.dn):
            if org_domain_group.dn == "domaingroup-root":
                config.domain_groups.append(UcsCentralDomainGroup(parent=config, org_domain_group=org_domain_group))

        # Removing the list of SDK objects fetched from the live UCS device
        config.sdk_objects = None
        self.config_list.append(config)
        self.logger(message="Finished fetching config with UUID " + str(config.uuid) + " from live device")
        return config.uuid

    def _validate_config_from_json(self, config_json=None):
        """
        Validates a config using the JSON schema definition
        :param config_json: JSON content containing config to be validated
        :return: True if config is valid, False otherwise
        """

        # Open JSON master schema for a UCS Central config
        json_file = open("schema/ucs/ucsc/master.json")
        json_string = json_file.read()
        json_file.close()
        json_schema = json.loads(json_string)

        schema_path = 'file:///{0}/'.format(
            os.path.dirname(os.path.abspath("schema/ucs/ucsc/master.json")).replace("\\", "/"))
        resolver = jsonschema.RefResolver(schema_path, json_schema)
        format_checker = jsonschema.FormatChecker()

        try:
            jsonschema.validate(config_json, json_schema, resolver=resolver, format_checker=format_checker)
        except jsonschema.ValidationError as err:
            absolute_path = []
            while True:
                try:
                    value = err.absolute_path.popleft()
                    if value != 0:
                        absolute_path.append(value)
                except IndexError:
                    break
            # TODO: Improve error logging by providing a simple explanation when JSON file is not valid
            self.logger(level="error", message="Invalid config JSON file in " + str(absolute_path))
            self.logger(level="error", message="Failed to validate config JSON file using schema: " + str(err.message))
            return False
        except jsonschema.SchemaError as err:
            self.logger(level="error", message="Failed to validate config JSON file due to schema error: " + str(err))
            return False

        # We now validate that the easyucs_version of the file is not greater than the running version of EasyUCS
        easyucs_version_from_file = config_json["easyucs"]["metadata"][0]["easyucs_version"]
        if packaging_version.parse(easyucs_version_from_file) > packaging_version.parse(__version__):
            self.logger(level="error",
                        message="Failed to validate config JSON file because it has been created using a more " +
                                "recent version of EasyUCS (" + easyucs_version_from_file + " > " + __version__ + ")")
            return False

        return True
