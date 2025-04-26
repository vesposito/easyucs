# coding: utf-8
# !/usr/bin/env python

""" config.py: Easy UCS Deployment Tool """

import copy
import urllib3

from intersight.api.aaa_api import AaaApi
from intersight.api.access_api import AccessApi
from intersight.api.adapter_api import AdapterApi
from intersight.api.asset_api import AssetApi
from intersight.api.bios_api import BiosApi
from intersight.api.boot_api import BootApi
from intersight.api.certificatemanagement_api import CertificatemanagementApi
from intersight.api.compute_api import ComputeApi
from intersight.api.chassis_api import ChassisApi
from intersight.api.deviceconnector_api import DeviceconnectorApi
from intersight.api.equipment_api import EquipmentApi
from intersight.api.fabric_api import FabricApi
from intersight.api.fcpool_api import FcpoolApi
from intersight.api.firmware_api import FirmwareApi
from intersight.api.iam_api import IamApi
from intersight.api.ipmioverlan_api import IpmioverlanApi
from intersight.api.ippool_api import IppoolApi
from intersight.api.iqnpool_api import IqnpoolApi
from intersight.api.kvm_api import KvmApi
from intersight.api.macpool_api import MacpoolApi
from intersight.api.memory_api import MemoryApi
from intersight.api.networkconfig_api import NetworkconfigApi
from intersight.api.network_api import NetworkApi
from intersight.api.ntp_api import NtpApi
from intersight.api.organization_api import OrganizationApi
from intersight.api.power_api import PowerApi
from intersight.api.resource_api import ResourceApi
from intersight.api.resourcepool_api import ResourcepoolApi
from intersight.api.sdcard_api import SdcardApi
from intersight.api.server_api import ServerApi
from intersight.api.smtp_api import SmtpApi
from intersight.api.snmp_api import SnmpApi
from intersight.api.sol_api import SolApi
from intersight.api.ssh_api import SshApi
from intersight.api.storage_api import StorageApi
from intersight.api.syslog_api import SyslogApi
from intersight.api.thermal_api import ThermalApi
from intersight.api.uuidpool_api import UuidpoolApi
from intersight.api.vmedia_api import VmediaApi
from intersight.api.vnic_api import VnicApi
from intersight.exceptions import ApiValueError, ApiTypeError, ApiException

from config.config import GenericConfig
from common import read_json_file


class IntersightConfig(GenericConfig):
    _CONFIG_SECTION_ATTRIBUTES_MAP = {
        "account_details": "Account Details",
        "equipment": "Equipment",
        "orgs": "Organizations",
        "resource_groups": "Resource Groups",
        "roles": "Roles",
        "user_groups": "User Groups",
        "users": "Users"
    }

    def __init__(self, parent=None, settings={}):
        GenericConfig.__init__(self, parent=parent)

        self.update_existing_intersight_objects = settings.get("update_existing_intersight_objects", False)
        self.delete_existing_resource_group_memberships_for_intersight_shared_orgs = \
            settings.get("delete_existing_resource_group_memberships_for_intersight_shared_orgs", False)
        self.export_list = None
        self.handle = self.parent.parent.handle
        self.sdk_objects = {}

        self.account_details = []
        self.equipment = []
        self.orgs = []
        self.resource_groups = []
        self.roles = []
        self.user_groups = []
        self.users = []

        # List of attributes to be exported in a config export
        self.export_list = self._CONFIG_SECTION_ATTRIBUTES_MAP.keys()

        self.bios_table = None
        bios_table = read_json_file(file_path="config/intersight/bios_table.json", logger=self)
        if bios_table:
            self.bios_table = bios_table

    def _fetch_sdk_objects(self, force=False):
        MAX_OBJECTS_PER_FETCH_CALL = 100

        sdk_objects_to_fetch = [{AaaApi: ["aaa_retention_policy"]},
                                {AccessApi: ["access_policy"]},
                                {AdapterApi: ["adapter_config_policy"]},
                                {AssetApi: ["asset_device_registration"]},
                                {BiosApi: ["bios_policy"]},
                                {BootApi: ["boot_precision_policy"]},
                                {CertificatemanagementApi: ["certificatemanagement_policy"]},
                                {ChassisApi: ["chassis_profile", "chassis_profile_template"]},
                                {ComputeApi: ["compute_blade", "compute_rack_unit", "compute_scrub_policy", 
                                              "compute_server_setting"]},
                                {DeviceconnectorApi: ["deviceconnector_policy"]},
                                {EquipmentApi: ["equipment_chassis", "equipment_fex"]},
                                {FabricApi: ["fabric_appliance_pc_role", "fabric_appliance_role",
                                             "fabric_eth_network_control_policy", "fabric_eth_network_group_policy",
                                             "fabric_eth_network_policy", "fabric_fc_network_policy",
                                             "fabric_fc_storage_role", "fabric_fc_uplink_pc_role",
                                             "fabric_fc_uplink_role", "fabric_fc_zone_policy",
                                             "fabric_fcoe_uplink_pc_role", "fabric_fcoe_uplink_role",
                                             "fabric_flow_control_policy", "fabric_lan_pin_group",
                                             "fabric_link_aggregation_policy", "fabric_link_control_policy",
                                             "fabric_multicast_policy", "fabric_port_mode", "fabric_port_policy",
                                             "fabric_san_pin_group", "fabric_server_role", "fabric_span_session",
                                             "fabric_span_dest_eth_port", "fabric_span_source_vlan", "fabric_span_source_vnic_eth_if",
                                             "fabric_span_source_eth_port", "fabric_span_source_eth_port_channel",
                                             "fabric_switch_cluster_profile", "fabric_switch_cluster_profile_template",
                                             "fabric_switch_control_policy", "fabric_switch_profile",
                                             "fabric_switch_profile_template", "fabric_system_qos_policy", "fabric_vlan",
                                             "fabric_vsan", "fabric_uplink_pc_role", "fabric_uplink_role"]},
                                {FcpoolApi: ["fcpool_pool", "fcpool_reservation", "fcpool_lease"]},
                                {FirmwareApi: ["firmware_policy"]},
                                {IamApi: ["iam_account", "iam_end_point_role", "iam_end_point_user",
                                          "iam_end_point_user_policy", "iam_end_point_user_role", "iam_idp",
                                          "iam_ldap_group", "iam_ldap_policy", "iam_ldap_provider", "iam_permission",
                                          "iam_qualifier", "iam_resource_limits", "iam_resource_roles", "iam_role",
                                          "iam_session_limits", "iam_user", "iam_user_group"]},
                                {IppoolApi: ["ippool_pool", "ippool_reservation", "ippool_ip_lease"]},
                                {IpmioverlanApi: ["ipmioverlan_policy"]},
                                {IqnpoolApi: ["iqnpool_pool", "iqnpool_reservation", "iqnpool_lease"]},
                                {KvmApi: ["kvm_policy"]},
                                {MacpoolApi: ["macpool_pool", "macpool_reservation"]},
                                {MemoryApi: ["memory_persistent_memory_policy", "memory_policy"]},
                                {NetworkconfigApi: ["networkconfig_policy"]},
                                {NetworkApi: ["network_element"]},
                                {NtpApi: ["ntp_policy"]},
                                {OrganizationApi: ["organization_organization"]},
                                {PowerApi: ["power_policy"]},
                                {ResourceApi: ["resource_group"]},
                                {ResourcepoolApi: ["resourcepool_pool", "resourcepool_qualification_policy"]},
                                {SdcardApi: ["sdcard_policy"]},
                                {ServerApi: ["server_profile_template", "server_profile"]},
                                {SmtpApi: ["smtp_policy"]},
                                {SnmpApi: ["snmp_policy"]},
                                {SolApi: ["sol_policy"]},
                                {SshApi: ["ssh_policy"]},
                                {StorageApi: ["storage_storage_policy", "storage_drive_group",
                                              "storage_drive_security_policy"]},
                                {SyslogApi: ["syslog_policy"]},
                                {ThermalApi: ["thermal_policy"]},
                                {UuidpoolApi: ["uuidpool_pool", "uuidpool_reservation", "uuidpool_uuid_lease"]},
                                {VmediaApi: ["vmedia_policy"]},
                                {VnicApi: ["vnic_eth_adapter_policy", "vnic_eth_if", "vnic_eth_network_policy",
                                           "vnic_eth_qos_policy", "vnic_fc_adapter_policy", "vnic_fc_if",
                                           "vnic_fc_network_policy", "vnic_fc_qos_policy", "vnic_iscsi_adapter_policy",
                                           "vnic_iscsi_boot_policy", "vnic_iscsi_static_target_policy",
                                           "vnic_lan_connectivity_policy", "vnic_san_connectivity_policy",
                                           "vnic_vhba_template", "vnic_vnic_template"]}]
        self.logger(level="debug", message="Fetching " + self.device.metadata.device_type_long + " objects for config")
        if self.device.task is not None:
            self.device.task.taskstep_manager.start_taskstep(
                name="FetchConfigIntersightSdkObjects",
                description="Fetching " + self.device.metadata.device_type_long + " SDK Config Objects")

        # "failed_to_fetch" is a list of {api_name: sdk_objects}, which failed to be fetched
        failed_to_fetch = []
        for sdk_dict in sdk_objects_to_fetch:
            for api_name, sdk_objects_list in sdk_dict.items():
                api = api_name(api_client=self.handle)
                # "sdk_objects_failed_to_fetch" is a list of all the sdk_objects which failed to be fetched
                sdk_objects_failed_to_fetch = []
                for sdk_object in sdk_objects_list:
                    self.sdk_objects[sdk_object] = []
                    # TODO: Handle retry in case of ApiException
                    try:
                        # We first query the API to get the number of objects that will be returned
                        count_response = getattr(api, "get_" + sdk_object + "_list")(
                            count=True, _request_timeout=self.device.timeout)
                        if count_response:
                            count_value = count_response["count"]
                            if count_value == 0:
                                self.sdk_objects[sdk_object] = []
                            elif count_value <= MAX_OBJECTS_PER_FETCH_CALL:
                                self.sdk_objects[sdk_object] = getattr(
                                    api, "get_" + sdk_object + "_list")(_request_timeout=self.device.timeout).results
                            else:
                                self.logger(level="debug", message=str(count_value) + " objects of class " +
                                            sdk_object + " are to be fetched using pagination")
                                start_value = 0
                                while start_value < count_value:
                                    self.sdk_objects[sdk_object] += getattr(api, "get_" + sdk_object + "_list")(
                                        skip=start_value, top=MAX_OBJECTS_PER_FETCH_CALL,
                                        _request_timeout=self.device.timeout).results
                                    start_value += MAX_OBJECTS_PER_FETCH_CALL

                            self.logger(level="debug",
                                        message="Fetched " + str(len(self.sdk_objects[sdk_object])) +
                                                " objects of class " + sdk_object)

                        else:
                            self.sdk_objects[sdk_object] = getattr(
                                api, "get_" + sdk_object + "_list")(_request_timeout=self.device.timeout).results
                    except (ApiValueError, ApiTypeError, ApiException) as err:
                        if getattr(err, "body", None):
                            import json
                            try:
                                err_body = json.loads(err.body)
                                if err_body.get("code") == "InvalidUrl":
                                    self.logger(level="warning",
                                                message="Skipped fetching unsupported objects of class " + sdk_object)
                            except json.decoder.JSONDecodeError:
                                self.logger(level="debug", message="Failed to load error message body in JSON format")
                                sdk_objects_failed_to_fetch.append(sdk_object)
                                self.logger(level="error",
                                            message="Failed to fetch objects of class " + sdk_object + ": " + str(err))
                        else:
                            sdk_objects_failed_to_fetch.append(sdk_object)
                            self.logger(level="error",
                                        message="Failed to fetch objects of class " + sdk_object + ": " + str(err))
                    except AttributeError as err:
                        sdk_objects_failed_to_fetch.append(sdk_object)
                        self.logger(level="error",
                                    message="Failed to fetch objects of class " + sdk_object + ": " + str(err))
                    except urllib3.exceptions.MaxRetryError as err:
                        sdk_objects_failed_to_fetch.append(sdk_object)
                        self.logger(level="error",
                                    message="Failed to fetch objects of class " + sdk_object + ": " + str(err))
                if sdk_objects_failed_to_fetch:
                    failed_to_fetch.append({api_name: sdk_objects_failed_to_fetch})

        # We retry all SDK objects that failed to fetch properly
        # "retry_failed_to_fetch" is a list of {api_name: sdk_objects}, which failed to be fetched even after a retry
        retry_failed_to_fetch = []
        if failed_to_fetch:
            for sdk_dict in failed_to_fetch:
                for api_name, sdk_objects_list in sdk_dict.items():
                    api = api_name(api_client=self.handle)
                    # "retry_sdk_objects_failed_to_fetch" is a list of all the sdk_objects which failed to be fetched
                    # even after a retry
                    retry_sdk_objects_failed_to_fetch = []
                    for sdk_object in sdk_objects_list:
                        self.logger(level="info", message="Retrying to fetch " + sdk_object)
                        self.sdk_objects[sdk_object] = []
                        try:
                            # We first query the API to get the number of objects that will be returned
                            count_response = getattr(api, "get_" + sdk_object + "_list")(
                                count=True, _request_timeout=self.device.timeout * 2)
                            if count_response:
                                count_value = count_response["count"]
                                if count_value == 0:
                                    self.sdk_objects[sdk_object] = []
                                elif count_value <= MAX_OBJECTS_PER_FETCH_CALL:
                                    self.sdk_objects[sdk_object] = getattr(
                                        api, "get_" + sdk_object + "_list")(
                                        _request_timeout=self.device.timeout * 2).results
                                else:
                                    self.logger(level="debug",
                                                message=str(count_value) + " objects of class " + sdk_object +
                                                " are to be fetched using pagination")
                                    start_value = 0
                                    while start_value < count_value:
                                        self.sdk_objects[sdk_object] += getattr(api, "get_" + sdk_object + "_list")(
                                            skip=start_value, top=MAX_OBJECTS_PER_FETCH_CALL,
                                            _request_timeout=self.device.timeout * 2).results
                                        start_value += MAX_OBJECTS_PER_FETCH_CALL

                                self.logger(level="debug",
                                            message="Fetched " + str(len(self.sdk_objects[sdk_object])) +
                                                    " objects of class " + sdk_object)

                            else:
                                self.sdk_objects[sdk_object] = getattr(
                                    api, "get_" + sdk_object + "_list")(_request_timeout=self.device.timeout * 2
                                                                        ).results
                        except (ApiValueError, ApiTypeError, ApiException) as err:
                            if getattr(err, "body", None):
                                import json
                                try:
                                    err_body = json.loads(err.body)
                                    if err_body.get("code") == "InvalidUrl":
                                        self.logger(level="warning",
                                                    message="Skipped fetching unsupported objects of class " +
                                                            sdk_object)
                                except json.decoder.JSONDecodeError:
                                    self.logger(level="debug",
                                                message="Failed to load error message body in JSON format")
                                    retry_sdk_objects_failed_to_fetch.append(sdk_object)
                                    self.logger(level="error",
                                                message="Failed to fetch objects of class " + sdk_object + ": " + str(
                                                    err))
                            else:
                                retry_sdk_objects_failed_to_fetch.append(sdk_object)
                                self.logger(level="error",
                                            message="Failed to fetch objects of class " + sdk_object + ": " + str(err))
                        except AttributeError as err:
                            retry_sdk_objects_failed_to_fetch.append(sdk_object)
                            self.logger(level="error",
                                        message="Failed to fetch objects of class " + sdk_object + ": " + str(err))
                        except urllib3.exceptions.MaxRetryError as err:
                            retry_sdk_objects_failed_to_fetch.append(sdk_object)
                            self.logger(level="error",
                                        message="Failed to fetch objects of class " + sdk_object + ": " + str(err))
                    if retry_sdk_objects_failed_to_fetch:
                        retry_failed_to_fetch.append({api_name: retry_sdk_objects_failed_to_fetch})

        # In case we still have SDK objects that failed to fetch, we list them in a warning message
        if retry_failed_to_fetch:
            for sdk_dict in retry_failed_to_fetch:
                for api_name, sdk_objects_list in sdk_dict.items():
                    for sdk_object in sdk_objects_list:
                        self.logger(level="warning", message="Impossible to fetch " + sdk_object + " after 2 attempts.")

        if self.device.task is not None:
            if not retry_failed_to_fetch:
                self.device.task.taskstep_manager.stop_taskstep(
                    name="FetchConfigIntersightSdkObjects", status="successful",
                    status_message="Successfully fetched " + self.device.metadata.device_type_long +
                                   " SDK Config Objects")
            elif force:
                self.device.task.taskstep_manager.stop_taskstep(
                    name="FetchConfigIntersightSdkObjects", status="successful",
                    status_message="Fetched " + self.device.metadata.device_type_long +
                                   " SDK Config Objects with errors (forced)")
            else:
                self.device.task.taskstep_manager.stop_taskstep(
                    name="FetchConfigIntersightSdkObjects", status="failed",
                    status_message="Error while fetching " + self.device.metadata.device_type_long +
                                   " SDK Config Objects")

                # If any of the mandatory tasksteps fails then return False
                if not self.device.task.taskstep_manager.is_taskstep_optional(name="FetchConfigIntersightSdkObjects"):
                    return False

        return True

    def get_object(self, object_type=None, name="", org_name="", debug=True):
        """
        Gets an object from the config given its type, name and optional org name
        :param object_type: type of object to get (class)
        :param name: name of the object to get
        :param org_name: org name of the object to get (optional)
        :param debug: If True then we log the debug messages, otherwise we don't
        :return: object if successful, None otherwise
        """
        if object_type is None:
            self.logger(level="error", message="Missing object type in get object request")
            return None

        if not name:
            self.logger(level="error", message="Invalid name in get object request")
            return None

        # If the object to be fetched is in a shared org, then we update the org_name and name field.
        if "/" in name:
            org_name = name.split("/")[0]
            name = name.split("/")[1]

        # Determining the section name to look for in the config
        if not hasattr(object_type, "_CONFIG_SECTION_NAME"):
            self.logger(level="error", message="Invalid object type in get object request")
            return None
        section_name = object_type._CONFIG_SECTION_NAME

        if org_name:
            # Identifying the org in which to look for in the config
            if not self.orgs:
                self.logger(level="debug", message="Could not find org " + str(org_name) + " in config")
                return None

            found_org = None
            for org in self.orgs:
                if org.name == org_name:
                    found_org = org
                    break
            if not found_org:
                self.logger(level="debug", message="Could not find org " + str(org_name) + " in config")
                return None

            # Checking in the section name of the found org if an object with the given name exists
            if not hasattr(found_org, section_name):
                if debug:
                    self.logger(level="debug", message="No section named " + section_name + " in org " + str(org_name))
                return None
            if not getattr(found_org, section_name):
                if debug:
                    self.logger(level="debug",
                                message="No item in section " + section_name + " of org " + str(org_name))
                return None
            if not isinstance(getattr(found_org, section_name), list):
                self.logger(level="debug",
                            message="Section " + section_name + " in org " + str(org_name) +
                                    " is not a list of objects")
                return None
            for obj in getattr(found_org, section_name):
                if hasattr(obj, "name"):
                    if obj.name == name and isinstance(obj, object_type):
                        return obj

            if debug:
                self.logger(level="debug", message="Could not find " + object_type._CONFIG_NAME +
                                                   " with name " + str(name) + " in org " + str(org_name))
        else:
            # Checking in the section name of the found org if an object with the given name exists
            if not hasattr(self, section_name):
                if debug:
                    self.logger(level="debug", message="No section named " + section_name + " in config")
                return None
            if not getattr(self, section_name):
                if debug:
                    self.logger(level="debug",
                                message="No item in section " + section_name + " of config")
                return None
            if not isinstance(getattr(self, section_name), list):
                self.logger(level="debug",
                            message="Section " + section_name + " in config is not a list of objects")
                return None

            for obj in getattr(self, section_name):
                if hasattr(obj, "name"):
                    if obj.name == name and isinstance(obj, object_type):
                        return obj

            if debug:
                self.logger(level="debug", message="Could not find " + object_type._CONFIG_NAME +
                                                   " with name " + str(name) + " in config.")
        return None
