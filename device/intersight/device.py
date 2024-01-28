# coding: utf-8
# !/usr/bin/env python

""" device.py: Easy UCS Deployment Tool """

import base64
import datetime
import importlib
import intersight
import json
import re
import requests
import time
import urllib3

import intersight.signing
from intersight.api.access_api import AccessApi
from intersight.api.adapter_api import AdapterApi
from intersight.api.appliance_api import ApplianceApi
from intersight.api.bios_api import BiosApi
from intersight.api.boot_api import BootApi
from intersight.api.certificatemanagement_api import CertificatemanagementApi
from intersight.api.chassis_api import ChassisApi
from intersight.api.deviceconnector_api import DeviceconnectorApi
from intersight.api.fabric_api import FabricApi
from intersight.api.fcpool_api import FcpoolApi
from intersight.api.firmware_api import FirmwareApi
from intersight.api.iam_api import IamApi
from intersight.api.ipmioverlan_api import IpmioverlanApi
from intersight.api.ippool_api import IppoolApi
from intersight.api.iqnpool_api import IqnpoolApi
from intersight.api.kvm_api import KvmApi
from intersight.api.license_api import LicenseApi
from intersight.api.macpool_api import MacpoolApi
from intersight.api.memory_api import MemoryApi
from intersight.api.networkconfig_api import NetworkconfigApi
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

from intersight.api_client import ApiClient
from intersight.configuration import Configuration
from intersight.exceptions import ApiValueError, ApiTypeError, ApiException, OpenApiException
from intersight import __version__ as intersight_sdk_version

from config.intersight.manager import IntersightConfigManager
from inventory.intersight.manager import IntersightInventoryManager
from report.intersight.manager import IntersightReportManager
from device.device import GenericDevice
import common

urllib3.disable_warnings()


class IntersightDevice(GenericDevice):
    INTERSIGHT_APPLIANCE_MIN_REQUIRED_VERSION = "1.0.9-631"

    def __init__(self, parent=None, uuid=None, target="www.intersight.com", key_id="", private_key_path="",
                 is_hidden=False, is_system=False, system_usage=None, proxy=None, proxy_user=None, proxy_password=None,
                 logger_handle_log_level="info", log_file_path=None, bypass_version_checks=False):

        self.key_id = key_id
        self.private_key_path = private_key_path

        GenericDevice.__init__(self, parent=parent, uuid=uuid, target=target, password="", user="",
                               is_hidden=is_hidden, is_system=is_system, system_usage=system_usage,
                               logger_handle_log_level=logger_handle_log_level, log_file_path=log_file_path,
                               bypass_version_checks=bypass_version_checks)

        self.handle = None
        self.is_appliance = False
        self.name = target
        # Setting the max timeout of 5min for Intersight Connection Failure.
        self.timeout = 5
        self.version_sdk = str(intersight_sdk_version)

        self.metadata.device_type = "intersight"
        if any(target.endswith(x) for x in ["intersight.com", "starshipcloud.com"]):
            self.metadata.device_type_long = "Intersight SaaS"
        elif target in [None, self.metadata.device_type + "_catalog.easyucs"]:
            self.metadata.device_type_long = "Intersight"
        else:
            self.metadata.device_type_long = "Intersight Appliance"
            self.is_appliance = True

        if key_id and private_key_path:
            with open(self.private_key_path, 'r') as f:
                private_key = f.read()

            if re.search('BEGIN RSA PRIVATE KEY', private_key):
                # API Key v2 format
                signing_algorithm = intersight.signing.ALGORITHM_RSASSA_PKCS1v15
                signing_scheme = intersight.signing.SCHEME_RSA_SHA256
                hash_algorithm = intersight.signing.HASH_SHA256

            elif re.search('BEGIN EC PRIVATE KEY', private_key):
                # API Key v3 format
                signing_algorithm = intersight.signing.ALGORITHM_ECDSA_MODE_DETERMINISTIC_RFC6979
                signing_scheme = intersight.signing.SCHEME_HS2019
                hash_algorithm = intersight.signing.HASH_SHA256

            else:
                raise Exception("Invalid Private Key. It does not correspond to an API Key for OpenAPI schema version "
                                "2 or 3.")

            signing_info = intersight.signing.HttpSigningConfiguration(
                key_id=key_id,
                private_key_path=private_key_path,
                signing_scheme=signing_scheme,
                signing_algorithm=signing_algorithm,
                hash_algorithm=hash_algorithm,
                signed_headers=[
                    intersight.signing.HEADER_REQUEST_TARGET,
                    intersight.signing.HEADER_CREATED,
                    intersight.signing.HEADER_EXPIRES,
                    intersight.signing.HEADER_HOST,
                    intersight.signing.HEADER_DATE,
                    intersight.signing.HEADER_DIGEST,
                    'Content-Type',
                    'User-Agent'
                ],
                signature_max_validity=datetime.timedelta(minutes=5)
            )

            configuration = Configuration(host="https://" + target, signing_info=signing_info)

            # If a proxy has been set, we set it in the configuration parameters
            configuration.proxy = proxy
            # Proxy with authentication
            if proxy_user and proxy_password:
                proxy_auth = proxy_user + ":" + proxy_password
                proxy_auth_bytes = proxy_auth.encode("utf-8")
                proxy_auth_hash = base64.b64encode(proxy_auth_bytes).decode("utf-8")
                configuration.proxy_headers = {"Proxy-Authorization": f"Basic {proxy_auth_hash}"}

            # This is required in case of an API mismatch between Intersight and the SDK. It will allow the SDK to work
            # with a higher version of the API (unknown attributes) without raising exceptions
            configuration.discard_unknown_keys = True

            # FIXME: Temporary fixes for SDK issues - March 2021 - "minimum"
            # Temporary fix for SDK issue in validating fabric.MacAgingSettings macAgingTime value being 0
            # Temporary fix for SDK issue in validating ippool.IpV6Config prefix value being 0
            configuration.disabled_client_side_validations = "minimum"

            # This is required for Intersight Appliances that do not have a valid SSL certificate
            if not any(target.endswith(x) for x in ["intersight.com", "starshipcloud.com"]):
                configuration.verify_ssl = False

            self.handle = ApiClient(configuration)
            self.handle.set_default_header('Content-Type', 'application/json')

        self.version_min_required = self.INTERSIGHT_APPLIANCE_MIN_REQUIRED_VERSION

        self.config_manager = IntersightConfigManager(parent=self)
        self.inventory_manager = IntersightInventoryManager(parent=self)
        self.report_manager = IntersightReportManager(parent=self)

    def clear(self, orgs=None):
        """
        Clears configuration by deleting objects from the Intersight device
        (optionally limited to the list of orgs provided).

        This function iterates through various object classes and their associated objects
        specified in the `objects_to_remove_in_order` list, retrieves a list of objects for each class,
        and attempts to delete them.
        Args:
            orgs (list): Optional list of organization names to restrict the clear operation to.

        Returns:
            bool: True if the cleaning process was successful.
        """
        is_cleared = True
        max_objects_per_fetch_call = 100
        # Define a list of objects to remove, including associated classes.
        # It is essential to maintain the below order to ensure the correct sequence of deletion.
        objects_to_remove_in_order = [
            {ServerApi: ["server_profile", "server_profile_template"]},
            {ChassisApi: ["chassis_profile"]},
            {VnicApi: [
                "vnic_lan_connectivity_policy", "vnic_san_connectivity_policy",
                "vnic_eth_qos_policy", "vnic_eth_network_policy",
                "vnic_fc_qos_policy", "vnic_fc_network_policy",
                "vnic_iscsi_adapter_policy", "vnic_iscsi_static_target_policy",
                "vnic_iscsi_boot_policy", "vnic_eth_adapter_policy", "vnic_fc_adapter_policy"
            ]},
            {FabricApi: ["fabric_switch_profile", "fabric_switch_cluster_profile", "fabric_switch_profile",
                         "fabric_flow_control_policy",
                         "fabric_link_aggregation_policy", "fabric_link_control_policy", "fabric_switch_control_policy",
                         "fabric_system_qos_policy", "fabric_port_policy", "fabric_eth_network_policy",
                         "fabric_vlan", "fabric_fc_network_policy", "fabric_vsan", "fabric_multicast_policy",
                         "fabric_eth_network_group_policy", "fabric_eth_network_control_policy",
                         "fabric_fc_zone_policy"]},
            {NtpApi: ["ntp_policy"]},
            {SnmpApi: ["snmp_policy"]},
            {SyslogApi: ["syslog_policy"]},
            {SmtpApi: ["smtp_policy"]},
            {FirmwareApi: ["firmware_policy"]},
            {CertificatemanagementApi: ["certificatemanagement_policy"]},
            {MemoryApi: ["memory_persistent_memory_policy"]},
            {NetworkconfigApi: ["networkconfig_policy"]},
            {BootApi: ["boot_precision_policy"]},
            {KvmApi: ["kvm_policy"]},
            {VmediaApi: ["vmedia_policy"]},
            {SolApi: ["sol_policy"]},
            {SshApi: ["ssh_policy"]},
            {IpmioverlanApi: ["ipmioverlan_policy"]},
            {AccessApi: ["access_policy"]},
            {SdcardApi: ["sdcard_policy"]},
            {BiosApi: ["bios_policy"]},
            {StorageApi: ["storage_storage_policy", "storage_drive_security_policy"]},
            {ThermalApi: ["thermal_policy"]},
            {PowerApi: ["power_policy"]},
            {DeviceconnectorApi: ["deviceconnector_policy"]},
            {AdapterApi: ["adapter_config_policy"]},
            {IppoolApi: ["ippool_reservation", "ippool_pool"]},
            {MacpoolApi: ["macpool_reservation", "macpool_lease", "macpool_pool"]},
            {FcpoolApi: ["fcpool_reservation", "fcpool_pool"]},
            {IqnpoolApi: ["iqnpool_reservation", "iqnpool_pool"]},
            {UuidpoolApi: ["uuidpool_reservation", "uuidpool_pool"]},
            {ResourcepoolApi: ["resourcepool_pool"]},
            {IamApi: [
                "iam_end_point_user_policy", "iam_end_point_user_role",
                "iam_end_point_user", "iam_permission", "iam_ldap_policy", "iam_sharing_rule"
            ]},
            {OrganizationApi: ["organization_organization"]},
            {ResourceApi: ["resource_group"]}
        ]

        count_value = 0

        for api_class_dict in objects_to_remove_in_order:
            for api_class, sdk_objects_list in api_class_dict.items():
                api = api_class(api_client=self.handle)

                for sdk_object in sdk_objects_list:
                    try:
                        # Retrieve the count and objects for the current object class
                        count_response = getattr(api, f"get_{sdk_object}_list")(count=True, expand='Organization')
                        if count_response:
                            count_value = count_response["count"]
                        if count_value <= max_objects_per_fetch_call:
                            results = getattr(api, f"get_{sdk_object}_list")(expand='Organization').results
                        else:
                            self.logger(level="debug",
                                        message=f"{count_value} objects of class {sdk_object} to be fetched using "
                                                f"pagination")
                            results = []
                            start_value = 0
                            while start_value < count_value:
                                results += getattr(api, f"get_{sdk_object}_list")(
                                    skip=start_value, top=max_objects_per_fetch_call, expand='Organization').results
                                start_value += max_objects_per_fetch_call

                        # Unassigning Server/Chassis/Domain profiles, if assigned before proceeding with object deletion
                        for profile in results:
                            if not orgs or (hasattr(profile, 'organization') and profile.organization and
                                            hasattr(profile.organization, 'name') and
                                            profile.organization.name in orgs):
                                # Unassigning Server Profiles
                                if sdk_object == "server_profile" and profile.get('assigned_server') is not None:
                                    self.logger(level="debug",
                                                message=f"Unassigning {profile.object_type}: {profile.name} " +
                                                        f"(MOID: {profile.moid})")
                                    getattr(api, f"patch_{sdk_object}")(moid=profile.moid,
                                                                        server_profile={"action": "Unassign"})
                                # Unassigning Chassis profiles
                                elif sdk_object == "chassis_profile" and profile.get('assigned_chassis') is not None:
                                    self.logger(level="debug",
                                                message=f"Unassigning {profile.object_type}: {profile.name} " +
                                                        f"(MOID: {profile.moid})")
                                    getattr(api, f"patch_{sdk_object}")(moid=profile.moid,
                                                                        chassis_profile={"action": "Unassign"})
                                # Unassigning Domain profiles
                                elif sdk_object == "fabric_switch_cluster_profile" and profile.get(
                                        'deployed_switches') != "None":
                                    self.logger(level="debug",
                                                message=f"Unassigning {profile.object_type}: {profile.name} " +
                                                        f"(MOID: {profile.moid})")
                                    getattr(api, f"patch_{sdk_object}")(moid=profile.moid,
                                                                        fabric_switch_cluster_profile={
                                                                            "action": "Unassign"})

                        # Looping through the results and deleting the relevant ones
                        for obj in results:
                            if not orgs or (hasattr(obj, 'organization') and obj.organization and
                                                 hasattr(obj.organization,
                                                         'name') and obj.organization.name in orgs):
                                assigned_value = None
                                if sdk_object in ["server_profile", "chassis_profile", "fabric_switch_cluster_profile"]:

                                    # Poll to check for unassignment completion
                                    unassignment_complete = False
                                    max_retries = 30
                                    retry_count = 0

                                    while not unassignment_complete and retry_count < max_retries:

                                        profile = getattr(api, f"get_{sdk_object}_by_moid")(moid=obj.moid)
                                        if sdk_object == "server_profile":
                                            assigned_value = profile.get('assigned_server')

                                        elif sdk_object == "chassis_profile":
                                            assigned_value = profile.get('assigned_chassis')

                                        elif sdk_object == "fabric_switch_cluster_profile":
                                            assigned_value = profile.get('deployed_switches')

                                        # Check the unassignment status
                                        if assigned_value is None or assigned_value == "None":
                                            unassignment_complete = True
                                            self.logger(level="debug",
                                                        message=f"Unassignment Completed: {obj.object_type}: " +
                                                                f"{obj.name} (MOID: {obj.moid})")
                                        else:
                                            self.logger(
                                                level="debug",
                                                message=f"{obj.object_type} {obj.name} is still associated. Retrying..."
                                            )

                                        # Sleep only if unassignment is not complete
                                        if not unassignment_complete:
                                            time.sleep(10)

                                        retry_count += 1

                                    # Check if the unassignment was successful before proceeding with deletion
                                    if unassignment_complete:
                                        # Delete the object
                                        self.logger(
                                            level="info",
                                            message=f"Deleting {obj.object_type} {obj.name} with MOID {obj.moid}"
                                        )
                                        getattr(api, f"delete_{sdk_object}")(moid=obj.moid)
                                    else:
                                        self.logger(
                                            level="warning",
                                            message=f"Max retries reached. Unable to unassign {obj.object_type}: " +
                                                    f"{obj.name} (MOID: {obj.moid})."
                                        )

                                elif sdk_object == "iam_permission":
                                    # Logic to delete IAM permissions
                                    excluded_policy_names = [
                                        "Workload Optimizer Advisor", "Workload Optimizer Automator",
                                        "Workload Optimizer Deployer",
                                        "Device Administrator", "Server Administrator", "User Access Administrator",
                                        "Device Technician",
                                        "Workload Optimizer Observer", "Account Administrator", "Read-Only",
                                        "HyperFlex Cluster Administrator", "Workload Optimizer Administrator"
                                    ]
                                    if obj.name not in excluded_policy_names:
                                        self.logger(
                                            level="info",
                                            message=f"Deleting {obj.object_type} {obj.name} with MOID {obj.moid}"
                                        )
                                        getattr(api, f"delete_{sdk_object}")(moid=obj.moid)

                                elif sdk_object == "resource_group":
                                    # Logic to delete resource groups
                                    excluded_resource_policies = ["default", "default-rg", "License-Standard",
                                                                  "License-Essential", "License-Advantage",
                                                                  "License-Premier"]
                                    if obj.name not in excluded_resource_policies:
                                        self.logger(
                                            level="info",
                                            message=f"Deleting {obj.object_type} {obj.name} with MOID {obj.moid}"
                                        )
                                        getattr(api, f"delete_{sdk_object}")(moid=obj.moid)

                                else:
                                    # If the obj is "Shared". It will be skipped from deletion.
                                    if obj.get('shared_scope') == 'shared':
                                        self.logger(
                                            level="debug",
                                            message=f"Skipped as Shared {obj.object_type} {obj.name} (MOID: {obj.moid})"
                                        )
                                        continue
                                    else:
                                        self.logger(level="info",
                                                    message=f"Deleting {obj.object_type} with MOID {obj.moid}")
                                        getattr(api, f"delete_{sdk_object}")(moid=obj.moid)

                            else:
                                # Skip if Organisation is not present
                                self.logger(level="debug",
                                            message=f"Skipping {obj.object_type} (MOID: {obj.moid})")
                    except (ApiValueError, ApiTypeError, ApiException) as err:
                        is_cleared = False
                        if getattr(err, "body", None):
                            try:
                                err_body = json.loads(err.body)
                                if err_body.get("code") == "InvalidUrl":
                                    self.logger(level="warning",
                                                message="Skipped deleting unsupported objects of class " + sdk_object)
                            except json.decoder.JSONDecodeError:
                                self.logger(level="debug", message="Failed to load error message body in JSON format")
                                self.logger(level="error",
                                            message="Failed to delete objects of class " + sdk_object + ": " + str(err))
                        else:
                            self.logger(level="error",
                                        message="Failed to delete objects of class " + sdk_object + ": " + str(err))
                    except AttributeError as attr_err:
                        is_cleared = False
                        self.logger(level="error",
                                    message="Failed to delete objects of class " + sdk_object + ": " + str(attr_err))
                    except urllib3.exceptions.MaxRetryError as err:
                        is_cleared = False
                        self.logger(level="error",
                                    message="Failed to delete objects of class " + sdk_object + ": " + str(err))

        return is_cleared

    def connect(self, bypass_version_checks=False):
        """
        Establishes connection to the device. Since Intersight does not require a connection, we use this
        method to verify that we are able to establish connectivity and gather name and version of the device
        :param bypass_version_checks: Whether the minimum version checks should be bypassed when connecting
        :return: True if connection successfully established, False otherwise
        """
        if self.task is not None:
            self.task.taskstep_manager.start_taskstep(name="ConnectIntersightDevice",
                                                      description="Connecting to " + self.metadata.device_type_long +
                                                                  " device")
        self.logger(level="debug", message="Using Intersight SDK version " + str(self.version_sdk))
        try:
            self._set_device_name_and_version()
            self.metadata.cached_orgs = self.get_orgs()
            self.metadata.timestamp_last_connected = datetime.datetime.now()
            self.metadata.is_reachable = True

            version = "unknown"
            if self.version:
                version = self.version

            self.logger(message="Connected to " + self.target + " (" + str(self.name) + ") running version " + version)

            # Verify if version running is above the minimum required version
            valid_version = True
            if self.version and self.is_appliance:
                try:
                    if "1.0.9-" in self.version:
                        build = self.version.split("-")[1]

                        if "1.0.9-" in self.version_min_required:
                            build_min = self.version_min_required.split("-")[1]

                            if build and build_min:
                                if int(build) < int(build_min):
                                    valid_version = False

                except Exception as err:
                    self.logger(level="debug", message="Could not perform minimum version check: " + str(err))

            if not valid_version:
                if not bypass_version_checks:
                    from api.api_server import easyucs
                    if easyucs:
                        self.metadata.is_reachable = False
                        self.logger(level="error", message="EasyUCS supports version " +
                                                           self.version_min_required + " and above.Your version"
                                                           + version + " is not supported.")
                        return False
                    else:
                        if not common.query_yes_no("Are you sure you want to continue with an unsupported version?"):
                            # User declined continue with unsupported version query
                            self.disconnect()
                            exit()
                else:
                    self.logger(level="warning", message="EasyUCS supports version " + self.version_min_required
                                                         + " and above. Your version " + version + " is not supported.")

            if self.task is not None:
                self.task.taskstep_manager.stop_taskstep(
                    name="ConnectIntersightDevice", status="successful",
                    status_message="Successfully connected to " + self.metadata.device_type_long + " device " +
                                   str(self.name))
            return True

        except Exception as err:
            self.metadata.is_reachable = False
            self.logger(level="error", message="Error while trying to connect to " + self.metadata.device_type_long +
                                               ": " + self.target + ": " + str(err))
        if self.task is not None:
            self.task.taskstep_manager.stop_taskstep(
                name="ConnectIntersightDevice", status="failed",
                status_message="Error while connecting to " + self.metadata.device_type_long + " device " +
                               str(self.name))
        return False

    def disconnect(self):
        """
        Intersight OpenAPI does not require a disconnection mechanism
        Maintaining the disconnect() call for compatibility reasons
        :return: True
        """
        if self.task is not None:
            self.task.taskstep_manager.skip_taskstep(
                name="DisconnectIntersightDevice",
                status_message="Disconnecting from " + self.metadata.device_type_long + " device " + str(self.name))
        return True

    def query(self, object_type="", filter="", expand="", retry=True):
        """
        Queries Intersight for one or multiple object(s) specified by its(their) type and a filter
        :param object_type: The object type of the object that is to be queried (e.g. "ntp.Policy")
        :param filter: A filter string to reduce the results to only specific objects
        :param expand: An expand string consisting of a list of attributes that should be expanded in the results
        :param retry: A flag to retry if query API fails
        :return: An empty list if no result, a list of Intersight SDK objects if found
        """

        if not object_type:
            self.logger(level="error", message="An object_type must be provided for the query")
            return []

        timeout = self.timeout
        if not retry:
            timeout = self.timeout * 2

        # We first need to decompose the object type to use the appropriate API
        api_prefix = object_type.split(".")[0]

        # We dynamically import the intersight module that we need for talking to the API
        api_module = importlib.import_module('intersight.api.' + api_prefix + '_api')
        api_class = getattr(api_module, api_prefix.title() + 'Api')
        api_instance = api_class(self.handle)

        # We also decompose the object type to get the name of the API call we need to make
        sdk_object_type = re.sub(r'(?<!^)(?=[A-Z])', '_', object_type.replace(".", "")).lower()

        try:
            MAX_OBJECTS_PER_FETCH_CALL = 100

            # We first query the API to get the number of objects that will be returned
            count_response = getattr(api_instance, "get_" + sdk_object_type + "_list")(
                count=True, filter=filter, _request_timeout=timeout)

            if count_response:
                count_value = count_response["count"]
                if count_value == 0:
                    results = []
                elif count_value <= MAX_OBJECTS_PER_FETCH_CALL:
                    results = getattr(api_instance, "get_" + sdk_object_type + "_list")(
                        filter=filter, expand=expand, _request_timeout=timeout).results
                else:
                    self.logger(level="debug", message=f"{str(count_value)} objects of class {sdk_object_type} are "
                                                       f"to be fetched using pagination")
                    start_value = 0
                    results = []
                    while start_value < count_value:
                        results += getattr(api_instance, "get_" + sdk_object_type + "_list")(
                            filter=filter, expand=expand, skip=start_value, top=MAX_OBJECTS_PER_FETCH_CALL,
                            _request_timeout=timeout).results
                        start_value += MAX_OBJECTS_PER_FETCH_CALL

                    self.logger(level="debug",
                                message=f"{str(len(results))} objects of class {sdk_object_type} have been fetched")
            else:
                # We query the API
                results = getattr(api_instance, "get_" + sdk_object_type + "_list")(
                    filter=filter, expand=expand, _request_timeout=timeout).results
            return results

        except (ApiValueError, ApiTypeError, ApiException) as err:
            error_message = str(err)
            if "Reason: Bad Gateway" in error_message:
                error_message = "Bad Gateway"
            else:
                # We try to simplify the error message displayed
                if hasattr(err, "body"):
                    try:
                        err_json = json.loads(err.body)
                        if "message" in err_json:
                            error_message = str(err_json["message"])
                    except json.decoder.JSONDecodeError as err_json_decode:
                        self.logger(level="error", message="JSON Decode error while fetching objects of class " +
                                                           sdk_object_type + ": " + str(err_json_decode))
                        pass
            self.logger(level="error",
                        message="Failed to fetch objects of class " + sdk_object_type + ": " + error_message)
        except AttributeError as err:
            self.logger(level="error",
                        message="Failed to fetch objects of class " + sdk_object_type + ": " + str(err))
        except urllib3.exceptions.MaxRetryError as err:
            self.logger(level="error",
                        message="Failed to fetch objects of class " + sdk_object_type + ": " + str(err))
        if retry:
            self.logger(level="info", message="Retrying to fetch objects of class " + sdk_object_type)
            return self.query(object_type=object_type, filter=filter, retry=False)

        return []

    def _get_apidocs_version(self):
        """
        Fetches the Intersight API version from APIdocs page
        :return: version if successful, None otherwise
        """
        requests.packages.urllib3.disable_warnings()

        url = "https://" + self.target + "/apidocs/apirefs/"
        try:
            page = requests.get(url, verify=False, timeout=5)
            regex_version = r"an-apidocs/(\d+\.\d+\.\d+-\d+)/build"
            res = re.search(regex_version, page.text)
            if res is not None:
                return res.group(1)

        except Exception as err:
            self.logger(level="error", message="Unable to determine Intersight API version: " + str(err))

        return None

    def get_orgs(self):
        """
        Fetches the Intersight Organizations
        :return: Org list if successful, None otherwise
        """
        cached_orgs = {}
        org_api = OrganizationApi(api_client=self.handle)
        try:
            orgs = org_api.get_organization_organization_list(expand="ResourceGroups,SharedWithResources",
                                                              _request_timeout=self.timeout, orderby="Name")

        except OpenApiException as err:
            self.logger(level="error", message=f"Unable to get the list of Orgs (with SharedWithResources): {err}")
            try:
                orgs = org_api.get_organization_organization_list(expand="ResourceGroups",
                                                                  _request_timeout=self.timeout, orderby="Name")
            except OpenApiException as err:
                self.logger(level="error", message=f"Unable to get the list of Orgs: {err}")
                return None

        if not orgs.results:
            self.logger(level="error", message="No org found")
            return None

        for result in orgs.results:
            cached_orgs[result.name] = {
                "description": result.description,
                "is_shared": False,
                "resource_groups": [],
                "shared_with_orgs": []
            }
            if result.resource_groups:
                cached_orgs[result.name]["resource_groups"] = [rg.name for rg in result.resource_groups]
            if getattr(result, "shared_with_resources", None):
                cached_orgs[result.name]["shared_with_orgs"] = [
                    resource.name for resource in getattr(result, "shared_with_resources", [])
                    if resource.object_type == "organization.Organization"
                ]
                if cached_orgs[result.name]["shared_with_orgs"]:
                    cached_orgs[result.name]["is_shared"] = True

        return cached_orgs

    def _set_device_name_and_version(self):
        appliance_api = ApplianceApi(api_client=self.handle)
        try:
            system_info = appliance_api.get_appliance_system_info_list(_request_timeout=self.timeout)

            if system_info.results:
                self.version = system_info.results[0].version
                self.metadata.device_version = self.version
                self.is_appliance = True

        except OpenApiException:
            self.logger(level="debug", message="Target is not an Intersight Appliance.")
            self.version = self._get_apidocs_version()
            self.metadata.device_version = self.version

        account_api = IamApi(api_client=self.handle)
        account = account_api.get_iam_account_list(_request_timeout=self.timeout)

        if account.results and not self.is_appliance:
            self.name = account.results[0].name
            self.metadata.device_name = self.name

    def validate_intersight_license(self):
        """
        Validates if the intersight account has essential license
        :return: True if intersight has valid license, False otherwise
        """
        if self.task is not None:
            self.task.taskstep_manager.start_taskstep(
                name="ValidateIntersightLicense", description="Validating if Intersight has Essential license")

        try:
            license_api = LicenseApi(api_client=self.handle)
            license_info_list = license_api.get_license_license_info_list(filter="LicenseType eq Essential",
                                                                          _request_timeout=self.timeout)
        except Exception as err:
            self.logger(level="error", message="Failed to fetch license details for " +
                                               self.metadata.device_type_long + ": " + str(err))
            if self.task is not None:
                self.task.taskstep_manager.stop_taskstep(
                    name="ValidateIntersightLicense", status="failed",
                    status_message="Intersight should have 'Essential' or 'Advantage' license to "
                                   "perform fetch/push operation.")
            return False

        for license_details in license_info_list.get("results", []):
            if license_details.get("license_state") in ["Compliance", "TrialPeriod"]:
                self.logger(level="info",
                            message="Successfully validated the license of intersight.")
                if self.task is not None:
                    self.task.taskstep_manager.stop_taskstep(
                        name="ValidateIntersightLicense", status="successful",
                        status_message="Successfully validated the license of intersight")
                return True

        self.logger(level="error", message="Intersight should have 'Essential' or 'Advantage' license to perform"
                                           " fetch/push operation.")
        if self.task is not None:
            self.task.taskstep_manager.stop_taskstep(
                name="ValidateIntersightLicense", status="failed",
                status_message="Intersight should have 'Essential' or 'Advantage' license to "
                               "perform fetch/push operation.")
        return False
