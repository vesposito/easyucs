# coding: utf-8
# !/usr/bin/env python

""" device.py: Easy UCS Deployment Tool """

import base64
import datetime
import importlib
import json
import re
import time

import intersight
import intersight.signing
import requests
import urllib3
from intersight import __version__ as intersight_sdk_version
from intersight.api.access_api import AccessApi
from intersight.api.adapter_api import AdapterApi
from intersight.api.appliance_api import ApplianceApi
from intersight.api.bios_api import BiosApi
from intersight.api.boot_api import BootApi
from intersight.api.certificatemanagement_api import CertificatemanagementApi
from intersight.api.chassis_api import ChassisApi
from intersight.api.compute_api import ComputeApi
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
from intersight.model.fabric_switch_cluster_profile import FabricSwitchClusterProfile
from intersight.model.mo_mo_ref import MoMoRef
from intersight.model.organization_organization import OrganizationOrganization
from intersight.model.resource_group import ResourceGroup
from werkzeug.utils import secure_filename

import common
from __init__ import EASYUCS_ROOT
from cache.intersight.manager import IntersightCacheManager
from config.intersight.manager import IntersightConfigManager
from device.delete_summary_manager import DeleteSummaryManager
from device.device import GenericDevice
from inventory.intersight.manager import IntersightInventoryManager
from report.intersight.manager import IntersightReportManager

urllib3.disable_warnings()


class IntersightDevice(GenericDevice):
    INTERSIGHT_APPLIANCE_MIN_REQUIRED_VERSION = "1.1.2-0"

    def __init__(self, parent=None, uuid=None, target="us-east-1.intersight.com", key_id="", private_key_path="",
                 is_hidden=False, is_system=False, system_usage=None, proxy=None, proxy_user=None, proxy_password=None,
                 logger_handle_log_level="info", log_file_path=None, bypass_connection_checks=False,
                 bypass_version_checks=False, user_label=""):

        self.key_id = key_id
        self.private_key_path = private_key_path

        GenericDevice.__init__(self, parent=parent, uuid=uuid, target=target, password="", user="",
                               is_hidden=is_hidden, is_system=is_system, system_usage=system_usage,
                               logger_handle_log_level=logger_handle_log_level, log_file_path=log_file_path,
                               bypass_connection_checks=bypass_connection_checks,
                               bypass_version_checks=bypass_version_checks, user_label=user_label)

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

        self.cache_manager = IntersightCacheManager(parent=self)
        self.config_manager = IntersightConfigManager(parent=self)
        self.inventory_manager = IntersightInventoryManager(parent=self)
        self.report_manager = IntersightReportManager(parent=self)
        self.delete_summary_manager = DeleteSummaryManager(parent=self)

    def clear_config(self, orgs=None, delete_settings=False, bypass_version_checks=False, force=False):
        """
        Clears configuration by deleting objects from the Intersight device
        (optionally limited to the list of orgs provided).

        This function iterates through various object classes and their associated objects
        specified in the `objects_to_remove_in_order` list, retrieves a list of objects for each class,
        and attempts to delete them.
        Args:
            orgs (list): Optional list of organization names to restrict the clear operation to. If not set, we
            delete everything.
            bypass_version_checks(boolean): Whether the minimum version checks should be bypassed when connecting
            delete_settings (boolean): If enabled, then we also delete all the settings associated with the
            Intersight account. This cannot be True if 'orgs' is specified.
            force (boolean): Force the clear process to proceed even if license validation fails.

        Returns:
            bool: True if the cleaning process was successful.
        """

        if orgs and delete_settings:
            self.logger(level="error", message="Deleting settings in case of a partial delete is prohibited.")
            return False

        if force:
            self.task.taskstep_manager.skip_taskstep(name="ValidateIntersightLicense",
                                                     status_message="Skipped license validation since forced")
            self.logger(level="warning", message="Skipping license validation due to force clear.")
        elif not self.validate_intersight_license():
            return False

        def is_profile_unassigned(api_class_object, sdk_object_name, object_moid, retries=30):
            """
            Function to poll for unassignment completion.

            This function repeatedly checks the status of a specified object (e.g., server profile,
            chassis profile, or fabric switch cluster profile) to determine if it has been unassigned.
            If the object becomes unassigned within the allowed retries, the
            function returns True; otherwise, it returns False.

            Returns:
                bool: True if the profile is unassigned, False otherwise.
            """
            profile_unassigned = False
            retry_count = 0
            assigned_value = None

            while retry_count < retries:
                profile = getattr(api_class_object, f"get_{sdk_object_name}_by_moid")(moid=object_moid)
                if sdk_object_name == "server_profile":
                    assigned_value = profile.get('assigned_server')
                elif sdk_object_name == "chassis_profile":
                    assigned_value = profile.get('assigned_chassis')
                elif sdk_object_name == "fabric_switch_cluster_profile":
                    assigned_value = profile.get('deployed_switches')

                # Check the unassignment status
                if not assigned_value or assigned_value == "None":
                    self.logger(level="debug",
                                message=f"Profile of type '{profile.object_type}' and name '{profile.name}' is "
                                        f"unassigned (MOID: {profile.moid})")
                    profile_unassigned = True
                    break
                else:
                    self.logger(level="debug",
                                message=f"{profile.object_type} {profile.name} is still associated. Retrying...")

                # Sleep if unassignment is not complete
                time.sleep(10)

                retry_count += 1

            return profile_unassigned

        # Define a list of objects to remove, including associated classes.
        # It is essential to maintain the below order to ensure the correct sequence of deletion.
        objects_to_remove_in_order = [
            {ServerApi: ["server_profile", "server_profile_template"]},
            {ChassisApi: ["chassis_profile", "chassis_profile_template"]},
            {VnicApi: [
                "vnic_lan_connectivity_policy", "vnic_san_connectivity_policy", "vnic_vnic_template",
                "vnic_vhba_template", "vnic_eth_qos_policy", "vnic_eth_network_policy", "vnic_fc_qos_policy",
                "vnic_fc_network_policy", "vnic_iscsi_boot_policy", "vnic_iscsi_adapter_policy",
                "vnic_iscsi_static_target_policy", "vnic_eth_adapter_policy", "vnic_fc_adapter_policy"
            ]},
            {FabricApi: ["fabric_switch_cluster_profile",
                         "fabric_switch_cluster_profile_template",
                         "fabric_port_policy", "fabric_flow_control_policy", "fabric_link_aggregation_policy",
                         "fabric_link_control_policy", "fabric_switch_control_policy", "fabric_system_qos_policy",
                         "fabric_eth_network_policy",  "fabric_fc_network_policy",
                         "fabric_multicast_policy", "fabric_eth_network_group_policy",
                         "fabric_eth_network_control_policy", "fabric_fc_zone_policy"]},
            {NtpApi: ["ntp_policy"]},
            {SnmpApi: ["snmp_policy"]},
            {SyslogApi: ["syslog_policy"]},
            {SmtpApi: ["smtp_policy"]},
            {FirmwareApi: ["firmware_policy"]},
            {CertificatemanagementApi: ["certificatemanagement_policy"]},
            {MemoryApi: ["memory_persistent_memory_policy", "memory_policy"]},
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
            {ComputeApi: ["compute_scrub_policy"]},
            {DeviceconnectorApi: ["deviceconnector_policy"]},
            {AdapterApi: ["adapter_config_policy"]},
            {IppoolApi: ["ippool_reservation", "ippool_pool"]},
            {MacpoolApi: ["macpool_reservation", "macpool_pool"]},
            {FcpoolApi: ["fcpool_reservation", "fcpool_pool"]},
            {IqnpoolApi: ["iqnpool_reservation",  "iqnpool_pool"]},
            {UuidpoolApi: ["uuidpool_reservation", "uuidpool_pool"]},
            {ResourcepoolApi: ["resourcepool_membership_reservation", "resourcepool_pool",
                               "resourcepool_qualification_policy"]},
            {IamApi: ["iam_user_group", "iam_user", "iam_end_point_user_policy", "iam_end_point_user",
                      "iam_permission", "iam_ldap_policy", "iam_sharing_rule"]},
            {OrganizationApi: ["organization_organization"]}
        ]

        settings_sdk_objects = ["iam_user_group", "iam_user",  "iam_permission"]

        # A set containing moid of all the organizations to be deleted
        orgs_to_be_deleted = set()
        if orgs:
            message_str = f"Deleting selected organization of Intersight device '{self.name}'"
            self.logger(level="info", message=f"{message_str}: {str(orgs)}")
            for org_name in orgs:
                org_objects = self.query(api_class=OrganizationApi, sdk_object_type="organization_organization",
                                         filter=f"Name eq '{org_name}'")
                if org_objects:
                    orgs_to_be_deleted.add(org_objects[0].moid)
                else:
                    self.logger(level="warning",
                                message=f"Organization '{org_name}' not found in Intersight account '{self.name}'. "
                                        f"Continuing without deleting it.")

            if not orgs_to_be_deleted:
                info_message = f"None of the organization selected exists in Intersight account {self.name}"
                self.logger(level="warning", message=f"{info_message}: {str(orgs)}")
                if self.task is not None:
                    self.task.taskstep_manager.stop_taskstep(name="ClearConfigIntersightDevice", status="successful",
                                                             status_message=message_str)
                return True
        else:
            # We delete the resource groups only when we are deleting all the Intersight configuration.
            objects_to_remove_in_order.append({ResourceApi: ["resource_group"]})

            # Added to handle cases of orphaned objects that need to be deleted.
            # By adding these sdk_objects to specific positions in the objects_to_remove_in_order list,
            # we ensure the sequential order of deletion is maintained
            # when we are deleting all the Intersight configuration (i.e., when no orgs are provided).

            possible_orphaned_obj = {
                FabricApi: [
                    ("fabric_switch_profile", 1),
                    ("fabric_switch_profile_template", 3),
                    ("fabric_vlan", 11),
                    ("fabric_vsan", 13)
                ],
                IppoolApi: [("ippool_ip_lease", 1)],
                MacpoolApi: [("macpool_lease", 1)],
                FcpoolApi: [("fcpool_lease", 1)],
                IqnpoolApi: [("iqnpool_lease", 1)],
                UuidpoolApi: [("uuidpool_uuid_lease", 1)],
                ResourcepoolApi: [("resourcepool_lease", 1)]
            }
            # Update each entry in the objects_to_remove_in_order list at the position specified
            for obj in objects_to_remove_in_order:
                for api_type, elements in possible_orphaned_obj.items():
                    if api_type in obj:
                        for element, index in elements:
                            obj[api_type].insert(index, element)

            message_str = f"Deleting all configuration from Intersight device '{self.name}'"
            self.logger(level="info", message=message_str)

        if self.task is not None:
            self.task.taskstep_manager.start_taskstep(name="ClearConfigIntersightDevice", description=message_str)

        # Defining some fields which will be needed for fetching the objects form Intersight.

        # We only delete Resource groups that are used for multi-tenancy by assigning to organizations i.e. of
        # type "rbac"
        query_filters = {
            "resource_group": "Type eq rbac"
        }

        last_organization = None
        error_encountered = False
        for api_class_dict in objects_to_remove_in_order:
            for api_class, sdk_objects_list in api_class_dict.items():
                api = api_class(api_client=self.handle)

                for sdk_object in sdk_objects_list:
                    # If "delete_settings" is not set, then skip the deletion of settings objects
                    if not delete_settings and sdk_object in settings_sdk_objects:
                        continue

                    # Retrieve the objects for the current object class
                    results = self.query(api_class=api_class, sdk_object_type=sdk_object,
                                         filter=query_filters.get(sdk_object, ""))
                    filtered_results = []
                    for result in results:
                        # Intersight provides pre-built workflows, tasks and policies to end users through global
                        # catalogs. Objects that are made available through global catalogs are said to have a
                        # 'shared' ownership. We do not delete such objects.
                        if hasattr(result, "shared_scope") and result.shared_scope == "shared":
                            continue
                        # We skip some System defined objects which exists on appliance. These objects do not
                        # belong to any organization and cannot be deleted. So we skip deleting them.
                        # In Appliance version 1.1.0-0, we have 'ntp.Policy' and 'networkconfig.Policy' policy named
                        # 'APPLIANCE-DEFAULT' which are system defined.
                        if hasattr(result, "tags"):
                            result_is_system_defined = False
                            for tag in result.tags:
                                if tag and tag.get('key') == "cisco.meta.appliance.default":
                                    result_is_system_defined = True
                                    self.logger(level="debug",
                                                message=f"Skipping {result.object_type} with name "
                                                        f"{getattr(result, 'name', '')} as it is System defined")
                                    self.delete_summary_manager.add_obj_status(
                                        obj=result,
                                        status="skipped",
                                        message="Appliance system defined Object"
                                    )
                                    break
                            if result_is_system_defined:
                                continue

                        # We skip some System defined objects which exists on appliance for the software repository
                        if sdk_object == "organization_organization":
                            # We can't delete org "private-catalog" on an Intersight Appliance device
                            if self.is_appliance and getattr(result, "name", None) in ["private-catalog"]:
                                self.logger(level="debug",
                                            message=f"Skipping {result.object_type} with name "
                                                    f"{getattr(result, 'name', '')} as it is System defined")
                                self.delete_summary_manager.add_obj_status(
                                    obj=result,
                                    status="skipped",
                                    message="Appliance system defined Object"
                                )
                                continue

                        elif sdk_object == "resource_group":
                            # We don't delete RG "private-catalog-rg" on an Intersight Appliance device
                            if self.is_appliance and getattr(result, "name", None) in ["private-catalog-rg"]:
                                self.logger(level="debug",
                                            message=f"Skipping {result.object_type} with name "
                                                    f"{getattr(result, 'name', '')} as it is System defined")
                                self.delete_summary_manager.add_obj_status(
                                    obj=result,
                                    status="skipped",
                                    message="Appliance system defined Object"
                                )
                                continue

                        # If we need to restrict the deletion to a list of organizations, then we need to handle some
                        # of these specific objects as they do not contain a direct reference to organization object.
                        if orgs_to_be_deleted:
                            if sdk_object == "iam_sharing_rule":
                                if result.shared_with_resource.moid in orgs_to_be_deleted:
                                    filtered_results.append(result)
                            elif sdk_object == "organization_organization":
                                if result.moid in orgs_to_be_deleted:
                                    filtered_results.append(result)
                            else:
                                if result.organization.moid in orgs_to_be_deleted:
                                    filtered_results.append(result)
                        else:
                            # If we do not restrict the deletion to a list of organizations, then we need to add all
                            # the objects to the filtered list.
                            filtered_results.append(result)

                    # Loop through all profile objects and unassign them if they are assigned. This is necessary
                    # before deleting any profile object. We unassign all profiles first because the unassignment
                    # process can take several minutes. During deletion, we wait for the unassignment to complete
                    # before proceeding with the deletion.
                    if sdk_object in ["server_profile", "chassis_profile", "fabric_switch_cluster_profile"]:
                        for profile in filtered_results:
                            try:
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
                                # If the SDK object is a fabric_switch_cluster_profile
                                # iterate through associated two switch profiles, unassigning each one in turn.
                                elif sdk_object == "fabric_switch_cluster_profile" and \
                                        profile.get('deployed_switches') is not None:
                                    self.logger(level="debug",
                                                message=f"Unassigning {profile.object_type}: {profile.name} "
                                                        f"(MOID: {profile.moid})")
                                    # Extract switch profiles and their MOIDs
                                    switch_profiles = getattr(profile, "switch_profiles", [])
                                    for switch_profile_ref in switch_profiles:
                                        self.logger(level="debug",
                                                    message=f"Unassigning {switch_profile_ref.object_type}: "
                                                            f"(MOID: {switch_profile_ref.moid})")
                                        # Unassign the switch profile
                                        getattr(api, f"patch_fabric_switch_profile")(moid=switch_profile_ref.moid,
                                                                                     fabric_switch_profile={
                                                                                         "action": "Unassign"})
                            except (ApiValueError, ApiTypeError, ApiException) as err:
                                error_encountered = True
                                self.logger(level="error",
                                            message="Failed to delete objects of class " + sdk_object + ": " +
                                                    str(err))
                                self.delete_summary_manager.add_obj_status(obj=profile, status="failed", message=str(err))
                            except AttributeError as attr_err:
                                error_encountered = True
                                self.logger(level="error",
                                            message="Failed to delete objects of class " + sdk_object + ": " +
                                                    str(attr_err))
                                self.delete_summary_manager.add_obj_status(obj=profile, status="failed", message=str(attr_err))
                            except urllib3.exceptions.MaxRetryError as err:
                                error_encountered = True
                                self.logger(level="error",
                                            message="Failed to delete objects of class " + sdk_object + ": " + str(err))
                                self.delete_summary_manager.add_obj_status(obj=profile, status="failed", message=str(err))

                    for obj in filtered_results:
                        try:
                            if sdk_object in ["server_profile", "chassis_profile", "fabric_switch_cluster_profile"]:
                                # Function call for Polling
                                if not is_profile_unassigned(api_class_object=api, sdk_object_name=sdk_object,
                                                             object_moid=obj.moid):
                                    self.logger(
                                        level="error",
                                        message=f"Unable to unassign profile of type '{obj.object_type}' and name " +
                                                f"'{obj.name}' (MOID: {obj.moid})."
                                    )
                                    continue
                            # Skip deletion of the iam_user if name is "admin".
                            elif sdk_object == "iam_user" and getattr(obj, "name", "") == "admin":
                                continue
                            elif sdk_object == "iam_permission":
                                # We skip the deletion of system defined objects
                                skip_object = False
                                for tag in obj.tags:
                                    if tag and tag.get("key") == "cisco.meta.creatorType" and \
                                            tag.get("value") == "SystemDefined":
                                        skip_object = True
                                        self.delete_summary_manager.add_obj_status(obj=obj, status="skipped",
                                                                                   message="System defined Objects")
                                        break
                                if skip_object:
                                    continue
                            elif sdk_object == "organization_organization":
                                # If the organization to be deleted is the last organization in the Intersight
                                # account, then we don't delete that organization. Rather, we rename that organization
                                # name to "default". This is done to deliver a factory reset environment to the user.
                                org_objects = self.query(api_class=OrganizationApi,
                                                         sdk_object_type="organization_organization")
                                if (len(org_objects) == 1) or (len(org_objects) == 2 and self.is_appliance and
                                        getattr(obj, "name", None) != "private-catalog" and
                                        any(getattr(x, "name", None) == "private-catalog" for x in org_objects)):
                                    # "obj" is the last organization which is being deleted
                                    last_organization = obj
                                    if org_objects[0].name != "default":
                                        self.logger(level="info", message=f"Renaming the last organization "
                                                                          f"'{org_objects[0].name}' to 'default'")
                                        last_organization = api.patch_organization_organization(
                                            moid=org_objects[0].moid,
                                            organization_organization={"name": "default"}
                                        )
                                    continue
                            elif sdk_object == "resource_group":
                                # If the resource group to be deleted belongs to the last organization in the
                                # Intersight account, then we don't delete that resource group. Rather, we rename
                                # that resource group to "default". This is done to deliver a factory reset
                                # environment to the user.

                                if last_organization is None:
                                    # This indicates that one or more organizations failed to delete,
                                    # which may impact deletion of resource group associated with these organizations.
                                    self.logger(level="warning",
                                                message="Deletion of some organizations failed, "
                                                        "which may prevent removal of associated resource groups.")
                                if last_organization and any([org_moref.moid == last_organization.moid
                                                              for org_moref in obj.organizations]):
                                    # "obj" is the resource group belonging to the last organization 'default'
                                    if obj.name != "default":
                                        self.logger(level="info",
                                                    message=f"Renaming the resource group '{obj.name}' attached to "
                                                            f"'default' organization to 'default'")
                                        api.patch_resource_group(moid=obj.moid, resource_group={"name": "default"})
                                    continue

                            if getattr(obj, "name", None):
                                self.logger(level="info", message=f"Deleting {obj.object_type} with name {obj.name} "
                                                                  f"(MOID {obj.moid})")
                            else:
                                self.logger(level="info",
                                            message=f"Deleting {obj.object_type} with MOID {obj.moid}")

                            # Deleting the object
                            getattr(api, f"delete_{sdk_object}")(moid=obj.moid)
                            self.delete_summary_manager.add_obj_status(obj=obj, status="success")
                        except (ApiValueError, ApiTypeError, ApiException) as err:
                            if getattr(err, "body", None):
                                try:
                                    err_body = json.loads(err.body)
                                    if err_body.get("code") == "InvalidUrl":
                                        self.logger(level="warning",
                                                    message="Skipped deleting unsupported objects of class " +
                                                            sdk_object)
                                        self.delete_summary_manager.add_obj_status(obj=obj, status="skipped",
                                                                                   message=err_body.get("message", str(err)))
                                    else:
                                        error_encountered = True
                                        self.logger(level="error", message="Failed to delete objects of class " +
                                                                           sdk_object + ": " + str(err))
                                        self.delete_summary_manager.add_obj_status(obj=obj, status="failed",
                                                                                   message=err_body.get("message", str(err)))
                                except json.decoder.JSONDecodeError:
                                    error_encountered = True
                                    self.logger(level="debug",
                                                message="Failed to load error message body in JSON format")
                                    self.logger(level="error",
                                                message="Failed to delete objects of class " + sdk_object + ": " +
                                                        str(err))
                                    self.delete_summary_manager.add_obj_status(obj=obj, status="failed", message=str(err))
                            else:
                                error_encountered = True
                                self.logger(level="error",
                                            message="Failed to delete objects of class " + sdk_object + ": " +
                                                    str(err))
                                self.delete_summary_manager.add_obj_status(obj=obj, status="failed", message=str(err))
                        except AttributeError as attr_err:
                            error_encountered = True
                            self.logger(level="error",
                                        message="Failed to delete objects of class " + sdk_object + ": " +
                                                str(attr_err))
                            self.delete_summary_manager.add_obj_status(obj=obj, status="failed", message=str(attr_err))
                        except urllib3.exceptions.MaxRetryError as err:
                            error_encountered = True
                            self.logger(level="error",
                                        message="Failed to delete objects of class " + sdk_object + ": " + str(err))
                            self.delete_summary_manager.add_obj_status(obj=obj, status="failed", message=str(err))

        if last_organization and not last_organization.resource_groups:
            # If the last organization does not have a resource group attached, then we
            # create one and attach it.
            try:
                # Check if a resource group with the name 'default' already exists
                existing_resource_groups = ResourceApi(api_client=self.handle).get_resource_group_list()
                default_group = next((group for group in existing_resource_groups.results if group.name == "default"),
                                     None)
                if default_group:
                    self.logger(level="debug", message=f"Resource group 'default' already exists.")
                    response = default_group  # Use the existing resource group
                else:
                    self.logger(level="info", message=f"Creating a resource group with name 'default'")
                    response = ResourceApi(api_client=self.handle).create_resource_group(
                        resource_group=ResourceGroup(name="default"))
                if response:
                    OrganizationApi(api_client=self.handle).patch_organization_organization(
                        moid=last_organization.moid,
                        organization_organization=OrganizationOrganization(
                            resource_groups=[MoMoRef(moid=response.moid, class_id='mo.MoRef',
                                                     object_type=response.object_type)]
                        )
                    )
            except Exception as e:
                self.logger(level="error", message=f"An error occurred while making sure the last "
                                                   f"organization have a resource group: {str(e)}")

        # Check if any errors were encountered
        if not error_encountered:
            if orgs:
                message_str = f"Successfully cleared config of selected orgs in Intersight device '{self.name}'"
                self.logger(level="error", message=f"{message_str}: {str(orgs)}")
            else:
                message_str = f"Successfully cleared config of the Intersight device '{self.name}'"
                self.logger(level="error", message=message_str)
        else:
            if orgs:
                message_str = f"Cleaning of selected organizations in Intersight device '{self.name}' is " \
                              f"successful with errors. Check logs for details."
            else:
                message_str = f"Cleaning of Intersight device '{self.name}' is successful with errors. " \
                              f"Check logs for details."
            self.logger(level="error", message=message_str)

        # Update the cache with the latest organizations
        if self.cache_manager.cache.fetch_orgs():
            self.cache_manager.save_to_cache(cache_key="orgs")

        if self.task is not None:
            self.task.taskstep_manager.stop_taskstep(name="ClearConfigIntersightDevice", status="successful",
                                                     status_message=message_str)
        return True

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
            if self.cache_manager.cache.fetch_orgs():
                self.cache_manager.save_to_cache(cache_key="orgs")
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
                    pattern = r"(\d+)\.(\d+)\.(\d+)-(\d+)(\.rc\.(\d+))?"
                    matches = re.match(pattern, self.version)
                    if matches.group():
                        major = matches.group(1)
                        minor = matches.group(2)
                        mr = matches.group(3)
                        patch = matches.group(4)
                        rc = matches.group(6)

                        matches = re.match(pattern, self.version_min_required)
                        if matches.group():
                            major_min = matches.group(1)
                            minor_min = matches.group(2)
                            mr_min = matches.group(3)
                            patch_min = matches.group(4)
                            rc_min = matches.group(6)

                            for (ver, ver_min) in [(major, major_min), (minor, minor_min), (mr, mr_min),
                                                   (patch, patch_min), (rc, rc_min)]:
                                if ver and ver_min:
                                    # Check if the current version component exceeds the minimum required component.
                                    # If a component is greater than the minimum, the version is valid, and we can
                                    # stop checking further.
                                    if int(ver) > int(ver_min):
                                        break
                                    # If a component is less than the minimum required, mark the version as invalid
                                    # and exit the loop.
                                    if int(ver) < int(ver_min):
                                        valid_version = False
                                        break

                except Exception as err:
                    self.logger(level="debug", message="Could not perform minimum version check: " + str(err))

            if not valid_version:
                if not bypass_version_checks:
                    from api.api_server import easyucs
                    if easyucs:
                        self.metadata.is_reachable = False
                        self.logger(
                            level="error",
                            message="EasyUCS supports version " + self.version_min_required +
                                    " and above. Your version " + version + " is not supported."
                        )
                        return False
                    else:
                        self.logger(
                            level="warning",
                            message="EasyUCS supports version " + self.version_min_required +
                                    " and above. Your version " + version + " is not supported."
                        )
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

    def create_vmedia_policy(self, description=None, device_name=None, enable_low_power_usb=None,
                             enable_virtual_encryption=None, enable_virtual_media=None, name=None, org_name=None,
                             tags=None, vmedia_mount=None):
        """
        Creates vMedia Policy in Intersight.
        :param description: Description of the vMedia Policy.
        :param device_name: Name of the Intersight device.
        :param enable_low_power_usb: Enable/Disable low power USB of the vMedia Policy.
        :param enable_virtual_encryption: Enable/Disable virtual encryption of the vMedia Policy.
        :param enable_virtual_media: Enable/Disable the virtual media.
        :param name: Name of the vMedia Policy.
        :param org_name: Organization name in which the vMedia Policy is created.
        :param tags: Tags of the vMedia Policy.
        :param vmedia_mount: Virtual media mount of the vMedia Policy.
        :return: True if successful, False otherwise.
        """

        if not name:
            self.logger(level="error", message="No Name specified to create vMedia Policy")
            return False
        if not device_name:
            self.logger(level="error", message="No Intersight device specified")
            return False

        if self.task is not None:
            self.task.taskstep_manager.start_taskstep(
                name="PushVmediaPolicyIntersight",
                description=f"creating vMedia policy '{name}' in Intersight device '{device_name}'"
            )
        try:
            # Fetching the organization object from Intersight
            object_list = self.query(object_type="organization.Organization", filter=f"Name eq '{org_name}'")
            if len(object_list) != 1:
                err_message = f"Organization '{org_name}' not found"
                self.logger(level="error", message=err_message)
                if self.task is not None:
                    self.task.taskstep_manager.stop_taskstep(
                        name="PushVmediaPolicyIntersight", status="failed", status_message=err_message)
                return False
            org_obj = object_list[0]

            from intersight.model.mo_tag import MoTag
            from intersight.model.mo_mo_ref import MoMoRef
            mo_mo_ref = MoMoRef(moid=org_obj.moid, class_id='mo.MoRef', object_type=org_obj.object_type)

            from intersight.model.vmedia_policy import VmediaPolicy
            from intersight.api.vmedia_api import VmediaApi
            kwargs = {
                "object_type": "vmedia.Policy",
                "class_id": "vmedia.Policy",
                "organization": mo_mo_ref,
                "name": name,
                "enabled": enable_virtual_media
            }

            if tags is not None:
                kwargs["tags"] = [MoTag(**tag) for tag in tags]
            if description is not None:
                kwargs["description"] = description
            if enable_virtual_encryption is not None:
                kwargs["encryption"] = enable_virtual_encryption
            if enable_low_power_usb is not None:
                kwargs["low_power_usb"] = enable_low_power_usb
            if vmedia_mount is not None:
                from intersight.model.vmedia_mapping import VmediaMapping
                kwargs["mappings"] = []
                kwargs_vmedia_mount = {
                    "object_type": "vmedia.Mapping",
                    "class_id": "vmedia.Mapping",
                    "device_type": "cdd",
                    "mount_protocol": "https"
                }
                if vmedia_mount["name"] is not None:
                    kwargs_vmedia_mount["volume_name"] = vmedia_mount["name"]
                if vmedia_mount["file_location"] is not None:
                    kwargs_vmedia_mount["file_location"] = vmedia_mount["file_location"]

                kwargs["mappings"].append(VmediaMapping(**kwargs_vmedia_mount))

            vmedia_policy_object = VmediaPolicy(**kwargs)
            vmedia_api = VmediaApi(api_client=self.handle)
            result = vmedia_api.create_vmedia_policy(vmedia_policy_object)
            if result:
                self.logger(level="info",
                            message=f"Successfully created vMedia policy '{name}' in Intersight device '{device_name}'")

                if self.task is not None:
                    self.task.taskstep_manager.stop_taskstep(
                        name="PushVmediaPolicyIntersight", status="successful",
                        status_message=f"Successfully created vMedia policy '{name}' in Intersight device " +
                                       f"'{device_name}'"
                    )

                return True
            else:
                self.logger(level="error",
                            message=f"Failed to create vMedia policy '{name}' in Intersight device '{device_name}'")

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
                        self.logger(level="error", message=f"JSON Decode error while creating vMedia Policy '{name}': "
                                                           f"{str(err_json_decode)}")
            self.logger(
                level="error",
                message=f"Failed to create vMedia policy '{name}' in Intersight device '{device_name}': {error_message}"
            )
        except AttributeError as err:
            self.logger(
                level="error",
                message=f"Failed to create vMedia policy '{name}' in Intersight device '{device_name}': {str(err)}"
            )
        except urllib3.exceptions.MaxRetryError as err:
            self.logger(
                level="error",
                message=f"Failed to create vMedia policy '{name}' in Intersight device '{device_name}': {str(err)}"
            )

        if self.task is not None:
            self.task.taskstep_manager.stop_taskstep(
                name="PushVmediaPolicyIntersight", status="failed",
                status_message=f"Error while creating vMedia policy '{name}' in Intersight device '{device_name}'. " +
                               f"Check logs."
            )

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

    def query(self, api_class=None, sdk_object_type="", object_type="", filter="", expand="", orderby="", retry=True):
        """
        Queries Intersight for one or multiple object(s) specified by its(their) type and a filter. Make sure to
        provide either 'object_type' OR both 'api_class' and 'sdk_object_type'.
        :param api_class: The Intersight SDK class of the object that is to be queried (e.g. "ServerApi")
        :param sdk_object_type: The object name which will be used to call the API (e.g. "server_profile")
        :param object_type: The object type of the object that is to be queried (e.g. "ntp.Policy")
        :param filter: A filter string to reduce the results to only specific objects
        :param expand: An expand string consisting of a list of attributes that should be expanded in the results
        :param orderby: Determines what properties are used to sort list.(e.g. "CreateTime desc")
        :param retry: A flag to retry if query API fails
        :return: An empty list if no result, a list of Intersight SDK objects if found
        """

        if not object_type and not (api_class and sdk_object_type):
            self.logger(level="error",
                        message="An 'object_type' or 'api_class and sdk_object_type' must be provided for the query")
            return []

        timeout = self.timeout
        if not retry:
            timeout = self.timeout * 2

        if object_type:
            # We first need to decompose the object type to use the appropriate API
            api_prefix = object_type.split(".")[0]

            # We dynamically import the intersight module that we need for talking to the API
            api_module = importlib.import_module('intersight.api.' + api_prefix + '_api')
            api_class = getattr(api_module, api_prefix.title() + 'Api')

            # We also decompose the object type to get the name of the API call we need to make
            sdk_object_type = re.sub(r'(?<!^)(?=[A-Z])', '_', object_type.replace(".", "")).lower()

        api_instance = api_class(self.handle)

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
                        filter=filter, expand=expand, _request_timeout=timeout, orderby=orderby).results
                else:
                    self.logger(level="debug", message=f"{str(count_value)} objects of class {sdk_object_type} are "
                                                       f"to be fetched using pagination")
                    start_value = 0
                    results = []
                    while start_value < count_value:
                        results += getattr(api_instance, "get_" + sdk_object_type + "_list")(
                            filter=filter, expand=expand, skip=start_value, top=MAX_OBJECTS_PER_FETCH_CALL,
                            _request_timeout=timeout, orderby=orderby).results
                        start_value += MAX_OBJECTS_PER_FETCH_CALL

                    self.logger(level="debug",
                                message=f"{str(len(results))} objects of class {sdk_object_type} have been fetched")
            else:
                # We query the API
                results = getattr(api_instance, "get_" + sdk_object_type + "_list")(
                    filter=filter, expand=expand, _request_timeout=timeout, orderby=orderby).results
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
            return self.query(api_class=api_class, sdk_object_type=sdk_object_type, object_type=object_type,
                              expand=expand, filter=filter, orderby=orderby, retry=False)

        return []

    def _get_apidocs_version(self):
        """
        Fetches the Intersight API version from APIdocs page
        :return: version if successful, None otherwise
        """
        requests.packages.urllib3.disable_warnings()

        url = "https://" + self.target + "/apidocs/apirefs/"
        try:
            if self.metadata.use_proxy:
                proxy_url, _, _ = common.get_proxy_url(include_authentication=True, logger=self)
                page = requests.get(url, verify=False, timeout=5, proxies={"http": proxy_url, "https": proxy_url})
            else:
                page = requests.get(url, verify=False, timeout=5)
            regex_version = r"an-apidocs/(\d+\.\d+\.\d+-\d+)/"
            res = re.search(regex_version, page.text)
            if res is not None:
                return res.group(1)

        except Exception as err:
            self.logger(level="error", message="Unable to determine Intersight API version: " + str(err))

        return None

    def _set_device_name_and_version(self):
        appliance_api = ApplianceApi(api_client=self.handle)
        try:
            system_info = appliance_api.get_appliance_system_info_list(_request_timeout=self.timeout, select="Version")

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

    def get_os_firmware_data(self):
        """
        Function to get the OS and Firmware data from the device
        :return: Returns dictionary containing OS and Firmware data, None otherwise
        """
        if not self.metadata.cache_path:
            self.logger(level="error", message="OS and Firmware cached data not found")
            return None

        os_firmware_data = common.read_json_file(
            file_path=os.path.join(self.metadata.cache_path,
                                   RepositoryManager.REPOSITORY_DEVICES_OS_FIRMWARE_FILE_NAME),
            logger=self)

        if not os_firmware_data:
            self.logger(level="error", message="OS and Firmware cached data not found")
            return None
        return os_firmware_data

    def fetch_os_firmware_data(self):
        """
        Function to get the OS and Firmware metadata
        :return: A dictionary containing OS and Firmware data, None otherwise
        """
        if self.task is not None:
            self.task.taskstep_manager.start_taskstep(name="FetchOSFirmwareDataObjectsIntersight",
                                                      description="Fetching OS and Firmware Objects")

        result = {
            "os": {},
            "firmware": []
        }
        operating_system_vendors = self.query(object_type="hcl.OperatingSystemVendor")
        operating_systems = self.query(object_type="hcl.OperatingSystem")
        operating_system_distributions = self.query(object_type="os.Distribution")
        firmware_distributables = self.query(object_type="firmware.Distributable", filter="Origin eq System")

        if not all([True if obj else False for obj in [operating_system_vendors, operating_systems,
                                                       operating_system_distributions, firmware_distributables]]):
            if self.task is not None:
                self.task.taskstep_manager.stop_taskstep(
                    name="FetchOSFirmwareDataObjectsIntersight", status="failed",
                    status_message="Error while fetching OS and Firmware Objects from Intersight")
            return None

        if not hasattr(operating_system_distributions[0], "vendor") or not hasattr(operating_system_distributions[0],
                                                                                   "label"):
            use_hcl_os = True
        else:
            use_hcl_os = False

        for os_vendor in operating_system_vendors:
            result["os"][os_vendor.name] = []
            if not use_hcl_os:
                for os_distribution in operating_system_distributions:
                    if os_distribution.vendor.moid == os_vendor.moid:
                        result["os"][os_vendor.name].append(os_distribution.label)
            else:
                for hcl_os in operating_systems:
                    if hcl_os.vendor.moid == os_vendor.moid:
                        result["os"][os_vendor.name].append(hcl_os.version)
            result["os"][os_vendor.name].sort()

        for firmware_distributable in firmware_distributables:
            result["firmware"].append({
                "firmware_image_type": firmware_distributable.image_type,
                "name": firmware_distributable.name,
                "supported_models": firmware_distributable.supported_models,
                "version": firmware_distributable.version
            })

        if self.task is not None:
            self.task.taskstep_manager.stop_taskstep(
                name="FetchOSFirmwareDataObjectsIntersight", status="successful",
                status_message="Successfully fetched OS and Firmware objects from Intersight")

        return result

    def sync_to_software_repository(self, description=None, file_download_link=None, file_path=None, image_type=None,
                                    firmware_image_type=None, name=None, org_name=None, supported_models=None,
                                    tags=None, vendor=None, version=None):
        """
        Creates Software Repository Link in Intersight device
        :param description: Description of the Software Repository Link
        :param file_download_link: HTTP(S) Link to download the file
        :param file_path: File path of the Software Repository
        :param image_type: Type of the Software Repository Link os/firmware/scu
        :param firmware_image_type: Image type for firmware links
        :param name: Name of the Software Repository Link
        :param org_name: Organization name where link is saved
        :param supported_models: Models supported
        :param tags: Tags of the Software Repository Link
        :param vendor: Vendor of the OS
        :param version: Version of image
        :return: True if successful, False otherwise
        """
        if image_type not in ["firmware", "os", "scu", "os_configuration"]:
            self.logger(level="error", message="Invalid file type: " + image_type)
            return False

        common_mandatory_fields = ["org_name", "name", "version"]
        image_type_mandatory_fields = {
            "firmware": common_mandatory_fields + ["file_download_link", "firmware_image_type", "supported_models"],
            "os": common_mandatory_fields + ["file_download_link", "vendor"],
            "scu": common_mandatory_fields + ["file_download_link", "supported_models"],
            "os_configuration": common_mandatory_fields + ["vendor", "file_path"]
        }
        for field in image_type_mandatory_fields[image_type]:
            if not eval(field):
                self.logger(level="error", message=f"Missing field '{field}' for {image_type} link")
                return False

        if self.task is not None:
            self.task.taskstep_manager.start_taskstep(name="PushSoftwareRepositoryLinksIntersight",
                                                      description=f"Syncing file '{file_download_link}' to intersight "
                                                                  f"repo")

        try:
            # Fetching the organization object from Intersight
            object_list = self.query(object_type="organization.Organization", filter=f"Name eq '{org_name}'")
            if len(object_list) != 1:
                err_message = f"Organization '{org_name}' not found"
                self.logger(level="error", message=err_message)
                if self.task is not None:
                    self.task.taskstep_manager.stop_taskstep(
                        name="PushSoftwareRepositoryLinksIntersight", status="failed", status_message=err_message)
                return False
            org_obj = object_list[0]

            # Fetching the software repository catalog object for the organization from Intersight
            object_list = self.query(object_type="softwarerepository.Catalog",
                                     filter=f"Organization.Moid eq '{org_obj.moid}'")
            if len(object_list) != 1:
                err_message = f"Could not find catalog object for the organization: '{org_name}'"
                self.logger(level="error", message=err_message)
                if self.task is not None:
                    self.task.taskstep_manager.stop_taskstep(
                        name="PushSoftwareRepositoryLinksIntersight", status="failed", status_message=err_message)
                return False
            catalog_obj = object_list[0]

            from intersight.model.mo_mo_ref import MoMoRef
            from intersight.model.mo_tag import MoTag

            # Creating a reference object of the software repository catalog object
            catalog_ref = MoMoRef(moid=catalog_obj.moid, class_id='mo.MoRef', object_type="softwarerepository.Catalog")

            result = None
            if image_type == "os":
                from intersight.api.softwarerepository_api import SoftwarerepositoryApi
                from intersight.model.softwarerepository_operating_system_file import \
                    SoftwarerepositoryOperatingSystemFile
                from intersight.model.softwarerepository_http_server import SoftwarerepositoryHttpServer

                source_model = SoftwarerepositoryHttpServer(location_link=file_download_link)

                kwargs = {
                    "name": name,
                    "version": version,
                    "catalog": catalog_ref,
                    "source": source_model,
                    "vendor": vendor
                }
                if tags:
                    kwargs["tags"] = [MoTag(**tag) for tag in tags]
                if description:
                    kwargs["description"] = description

                operating_system_file_object = SoftwarerepositoryOperatingSystemFile(**kwargs)

                software_repository_api = SoftwarerepositoryApi(api_client=self.handle)
                result = software_repository_api.create_softwarerepository_operating_system_file(
                    operating_system_file_object)

            elif image_type == "firmware":
                from intersight.api.firmware_api import FirmwareApi
                from intersight.model.firmware_distributable import FirmwareDistributable
                from intersight.model.softwarerepository_http_server import SoftwarerepositoryHttpServer

                source_model = SoftwarerepositoryHttpServer(location_link=file_download_link)

                kwargs = {
                    "name": name,
                    "version": version,
                    "catalog": catalog_ref,
                    "supported_models": supported_models,
                    "source": source_model,
                    "image_type": firmware_image_type,
                    "import_action": "None",
                    "origin": "User"
                }
                if tags:
                    kwargs["tags"] = [MoTag(**tag) for tag in tags]
                if description:
                    kwargs["description"] = description

                firmware_file_object = FirmwareDistributable(**kwargs)

                firmware_api = FirmwareApi(api_client=self.handle)
                result = firmware_api.create_firmware_distributable(firmware_file_object)

            elif image_type == "scu":
                from intersight.api.firmware_api import FirmwareApi
                from intersight.model.firmware_server_configuration_utility_distributable \
                    import FirmwareServerConfigurationUtilityDistributable
                from intersight.model.softwarerepository_http_server import SoftwarerepositoryHttpServer

                source_model = SoftwarerepositoryHttpServer(location_link=file_download_link)
                kwargs = {
                    "name": name,
                    "version": version,
                    "catalog": catalog_ref,
                    "supported_models": supported_models,
                    "source": source_model
                }
                if tags:
                    kwargs["tags"] = [MoTag(**tag) for tag in tags]
                if description:
                    kwargs["description"] = description

                scu_file_object = FirmwareServerConfigurationUtilityDistributable(**kwargs)

                firmware_api = FirmwareApi(api_client=self.handle)
                result = firmware_api.create_firmware_server_configuration_utility_distributable(scu_file_object)

            elif image_type == "os_configuration":
                if file_download_link.rsplit('/', 1)[-1].endswith((".iso", ".bin")):
                    err_message = (f"Failed to create software repository {image_type} link: " +
                                   f"Provided configuration file is invalid")
                    self.logger(level="error", message=err_message)
                    if self.task is not None:
                        self.task.taskstep_manager.stop_taskstep(
                            name="PushSoftwareRepositoryLinksIntersight", status="failed", status_message=err_message)
                        return False
                # setting the maximum allowed OS configuration file size to 10 MB
                elif os.path.getsize(file_path) > 10 * (10 ** 6):
                    err_message = (f"Failed to create software repository {image_type} link: " +
                                   f"File size exceeds the maximum allowed size (10 MB).")
                    self.logger(level="error", message=err_message)
                    if self.task is not None:
                        self.task.taskstep_manager.stop_taskstep(
                            name="PushSoftwareRepositoryLinksIntersight", status="failed", status_message=err_message)
                        return False
                from intersight.api.os_api import OsApi
                from intersight.model.os_configuration_file import \
                    OsConfigurationFile

                operating_systems = self.query(object_type="hcl.OperatingSystem", filter=f"Version eq '{version}'")

                # Fetching the os catalog object for the organization from Intersight
                catalog_objects = self.query(object_type="os.Catalog",
                                             filter=f"Organization.Moid eq '{org_obj.moid}'")
                if len(object_list) != 1:
                    err_message = f"Could not find os catalog object for the organization: '{org_name}'"
                    self.logger(level="error", message=err_message)
                    if self.task is not None:
                        self.task.taskstep_manager.stop_taskstep(
                            name="PushSoftwareRepositoryLinksIntersight", status="failed", status_message=err_message)
                    return False

                catalog_obj = catalog_objects[0]
                from intersight.model.mo_mo_ref import MoMoRef

                # Creating a reference object of the os catalog
                catalog_ref = MoMoRef(moid=catalog_obj.moid, class_id='mo.MoRef', object_type="os.Catalog")

                # Creating a reference object of the hcl operating system
                operating_system_ref = MoMoRef(moid=operating_systems[0].moid, class_id='mo.MoRef',
                                               object_type="hcl.OperatingSystem")

                kwargs = {
                    "name": secure_filename(name),
                    "catalog": catalog_ref,
                    "distributions": [operating_system_ref]
                }
                absolute_path = os.path.abspath(os.path.join(EASYUCS_ROOT, file_path))
                if os.path.exists(absolute_path):
                    with open(absolute_path, 'r') as file:
                        file_contents = file.read()
                    if file_contents:
                        kwargs["file_content"] = file_contents
                if tags:
                    kwargs["tags"] = [MoTag(**tag) for tag in tags]
                if description:
                    kwargs["description"] = description

                os_configuration_file_obj = OsConfigurationFile(**kwargs)

                os_configuration_file_api = OsApi(api_client=self.handle)
                result = os_configuration_file_api.create_os_configuration_file(
                    os_configuration_file_obj)

            if result:
                self.logger(level="info",
                            message=f"Successfully created software repository {image_type} link.")

                if self.task is not None:
                    self.task.taskstep_manager.stop_taskstep(
                        name="PushSoftwareRepositoryLinksIntersight", status="successful",
                        status_message=f"Successfully created software repository {image_type} link in intersight")

                return True
            else:
                self.logger(level="error",
                            message=f"Failed to create software repository {image_type} link.")

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
                        self.logger(level="error", message=f"JSON Decode error while creating software repository "
                                                           f"{image_type} link: {str(err_json_decode)}")
            self.logger(level="error",
                        message=f"Failed to create software repository {image_type} link: {error_message}")
        except AttributeError as err:
            self.logger(level="error",
                        message=f"Failed to create software repository {image_type} link: {str(err)}")
        except urllib3.exceptions.MaxRetryError as err:
            self.logger(level="error",
                        message=f"Failed to create software repository {image_type} link: {str(err)}")
        except UnicodeDecodeError:
            self.logger(level="error",
                        message=f"Failed to create software repository {image_type} link: " +
                                f"Provided configuration file is invalid")

        if self.task is not None:
            self.task.taskstep_manager.stop_taskstep(
                name="PushSoftwareRepositoryLinksIntersight", status="failed",
                status_message="Error while while syncing to software repository. Check logs.")

        return False

    def validate_intersight_license(self):
        """
        Validates if the intersight account has essential license
        :return: True if intersight has valid license, False otherwise
        """
        if self.task is not None:
            self.task.taskstep_manager.start_taskstep(
                name="ValidateIntersightLicense", description="Validating if Intersight has Essentials license")

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
                    status_message="Intersight should have 'Essentials' or 'Advantage' license to perform"
                                   "fetch/push operation. To bypass this check enable the 'Force' option and try again"
                )
            return False

        license_states = []
        for license_details in license_info_list.get("results", []):
            if license_details.get("license_state") in ["Compliance", "TrialPeriod", "OutOfCompliance"]:
                self.logger(level="info", message="Successfully validated the Intersight license")
                if self.task is not None:
                    self.task.taskstep_manager.stop_taskstep(
                        name="ValidateIntersightLicense", status="successful",
                        status_message="Successfully validated the Intersight license")
                return True
            license_states.append(license_details.get("license_state"))

        self.logger(level="error", message="Intersight should have 'Essential' or 'Advantage' license to perform"
                                           " fetch/push operation.")
        if self.task is not None:
            self.task.taskstep_manager.stop_taskstep(
                name="ValidateIntersightLicense", status="failed",
                status_message=f"Your Intersight license is in '{', '.join(license_states)}' state, which might prevent"
                               f" some operations to complete properly. To bypass this check enable the 'Force' option "
                               f"and try again.")
        return False

    def monitor_profile_deployment(self, profile):
        """
        Monitors the deployment workflows for the given profile.

        :param profile: Fabric switch cluster profile object.
        :return: str - Final status of the workflows ("COMPLETED", "TIME_OUT", "FAILED") or None on error.
        """

        # Check if the profile is a domain profile before performing deployment monitoring.
        if not isinstance(profile, FabricSwitchClusterProfile):
            self.logger(level="error",
                        message="Currently, this function supports monitoring the deployment of domain profiles only.")
            return False
        try:
            self.logger(message=f"Started monitoring deployment workflows for profile {profile.name}.")

            # Filter string for querying workflows by switch profile MOIDs
            moid_list = ', '.join(f"'{profile.switch_profiles[i].moid}'" for i in range(profile.switch_profiles_count))
            workflow_filter = f"WorkflowCtx.InitiatorCtx.InitiatorMoid in ({moid_list})"

            # Set timeout duration
            timeout_duration = 3600
            start_time = time.time()

            while time.time() - start_time < timeout_duration:

                # Brief pause before checking workflow status to reduce load
                time.sleep(10)

                # Retrieve workflow
                all_workflows = self.query(object_type="workflow.WorkflowInfo", filter=workflow_filter,
                                           orderby="CreateTime desc")

                # Fetch the latest workflows matching the number of switch profiles in the deployment.
                # Each switch_profile of domain profile corresponds to one deployment workflow, so we limit the results
                # to the count of `switch_profiles_count`.
                workflow_info = all_workflows[:profile.switch_profiles_count]

                if all(workflow.status == "COMPLETED" for workflow in workflow_info):
                    return True
                elif any(workflow.status == "FAILED" for workflow in workflow_info):

                    # Retrieve the 'moid' of the first workflow with status "FAILED" using 'next',
                    # as all failed workflows are expected to share the same failure reason.

                    failed_workflow_moid = next(
                        (workflow["moid"] for workflow in workflow_info if workflow["status"] == "FAILED"), None)

                    # Fetch failure reason using "workflow.TaskInfo" object
                    failure_reasons = [task.failure_reason for task in self.query(
                        object_type="workflow.TaskInfo", filter=f"WorkflowInfo.Moid eq '{failed_workflow_moid}'") if
                                       task.failure_reason]
                    self.logger(level="error", message=f"Deployment failed : {'; '.join(failure_reasons)}")

                    return False

                elif any(workflow.status in ["RUNNING", "WAITING"] for workflow in workflow_info):
                    self.logger(level="debug", message="Deployment still in progress...")

            # Timeout if workflows do not complete within duration
            self.logger(level="error", message="Deployment timed out. Check logs for details.")
            return False

        except OpenApiException as error:
            self.logger(level="error", message=f"Failed to retrieve workflow information: {error}")
            return False

    def _perform_domain_profile_deployment(self, imm_domain_name=None, domain_profile=None):
        """
        Deploys the domain profile to Fabric Interconnects (FIs) after assignment. Used by deploy_domain_profile().

        :param imm_domain_name: IMM domain device name.
        :param domain_profile: Fabric switch cluster profile object.
        :return: bool - True if deployment is successful, False otherwise.
        """
        try:
            fabric_api = FabricApi(api_client=self.handle)

            # Check if the domain profile is already deployed. If yes, skip the DeployDomainProfile task step;
            # if no, proceed with deploying the domain profile.
            if domain_profile.deploy_status != 'None':
                message = (f"UCS Domain Profile {domain_profile.name} is already deployed on Fabric Interconnect "
                           f"{imm_domain_name}. So skipping deployment.")
                if self.task:
                    self.task.taskstep_manager.skip_taskstep(name="DeployDomainProfile", status_message=message)
                self.logger(level="warning", message=message)
                return True

            else:
                self.logger(message=f"Starting deployment of domain profile {domain_profile.name} "
                                    f"to Fabric Interconnect {imm_domain_name}.")
                if self.task:
                    self.task.taskstep_manager.start_taskstep(name="DeployDomainProfile",
                                                              description=f"Deploy Domain Profile {domain_profile.name}")
                # Initiate deployment for each switch profile in the profile
                for i in range(domain_profile.switch_profiles_count):
                    fabric_api.patch_fabric_switch_profile(
                        moid=domain_profile.switch_profiles[i].moid,
                        fabric_switch_profile={"Action": "Deploy"}
                    )

                # Monitor deployment process and check completion status
                deployment_status = self.monitor_profile_deployment(domain_profile)
                if deployment_status:
                    message = f"Deployment of domain profile {domain_profile.name} completed successfully."
                    self.logger(level="debug", message=message)
                    if self.task:
                        self.task.taskstep_manager.stop_taskstep(
                            name="DeployDomainProfile", status="successful",
                            status_message=message)
                else:
                    self.logger(level="error", message="Deployment of domain profile Failed. Please check logs.",
                                set_api_error_message=False)
                    if self.task:
                        self.task.taskstep_manager.stop_taskstep(name="DeployDomainProfile", status="failed",
                                                                 status_message="Deployment of domain profile failed.")
                    return False

        except OpenApiException as err:
            self.logger(level="error", message=f"Failed to deploy domain profile: {err}")
            if self.task:
                self.task.taskstep_manager.stop_taskstep(name="DeployDomainProfile", status="failed",
                                                         status_message=str(err)[:255])
            return False

        return True

    def _assign_domain_profile(self, imm_domain_name=None, domain_profile=None,
                               network_elements=None):
        """
        Assigns a domain profile to Fabric Interconnects (FIs) if it is not already assigned. Used by deploy_domain_profile()
        Used by deploy_domain_profile()

        :param imm_domain_name: IMM domain device name.
        :param domain_profile: The fabric switch cluster profile object.
        :param network_elements: List of network elements associated with the device.
        :return: bool - True if assignment is successful, False otherwise.
        """
        try:
            self.logger(message=f"Starting the assignment of domain profile {domain_profile.name} "
                                f"to Fabric Interconnect {imm_domain_name}.")

            # Check for missing network elements for FI-A and FI-B, before assignment of domain profile
            switch_ids = {fi.switch_id for fi in network_elements}
            missing_switches = {'A', 'B'} - switch_ids

            if missing_switches:
                self.logger(
                    level="error",
                    message=(
                        f"Cannot proceed with Assignment: The registered device {imm_domain_name} is missing "
                        f"network elements for the following switches: {', '.join(sorted(missing_switches))}. "
                        f"Ensure both FI-A and FI-B are properly configured."
                    )
                )
                return False

            fabric_api = FabricApi(api_client=self.handle)

            if self.task:
                self.task.taskstep_manager.start_taskstep(name="AssignDomainProfile",
                                                          description="Assign Domain Profile")

            # Check if the domain profile is already assigned.
            # If assigned, verify it's linked to the intended Fabric Interconnect (FI).
            # If assigned to the intended FI, skip the task. If not, set the task as failed.
            # If not assigned, proceed with assignment of domain profile.

            if domain_profile.config_context.config_state == "Not-assigned":

                # Assign domain profile to each Fabric Interconnect
                for i in range(domain_profile.switch_profiles_count):
                    fabric_api.patch_fabric_switch_profile(
                        moid=domain_profile.switch_profiles[i].moid,
                        fabric_switch_profile={"AssignedSwitch": network_elements[i].moid}
                    )

                # Mark task step as successful if assignment completed
                message_str = (f"Successfully assigned domain profile {domain_profile.name} to "
                               f"Fabric Interconnect {imm_domain_name}.")
                if self.task:
                    self.task.taskstep_manager.stop_taskstep(
                        name="AssignDomainProfile",
                        status="successful",
                        status_message=message_str)
                self.logger(message=message_str)
                return True

            elif domain_profile.config_context.config_state in ("Assigned", "Associated"):

                # Verify if domain profile is assigned to Intended FI
                for i in range(domain_profile.switch_profiles_count):
                    assigned_profile = self.query(object_type="fabric.SwitchProfile",
                                                  filter=f"Moid eq '{domain_profile.switch_profiles[i].moid}'")

                    # Continue if the profile is assigned to the intended network element FI
                    if assigned_profile[0].assigned_switch.moid == network_elements[i].moid:
                        continue

                    # Stop deployment if domain profile is assigned to a different FI
                    message_str = f"Domain profile is already assigned to a different domain."
                    if self.task is not None:
                        self.task.taskstep_manager.stop_taskstep(
                            name="AssignDomainProfile", status="failed",
                            status_message=message_str
                        )
                    self.logger(level="error", message=message_str)
                    return False

                # Skip assignment if domain profile is already assigned to intended FI
                message = (f"UCS Domain Profile {domain_profile.name} is already assigned to Fabric Interconnect "
                           f"{imm_domain_name}. So skipping assignment.")
                self.logger(level="warning", message=message)
                if self.task:
                    self.task.taskstep_manager.skip_taskstep(name="AssignDomainProfile", status_message=message)
            else:
                message_str = (f"Deployment cannot proceed as domain profile '{domain_profile.name}' is in "
                               f"unknown state: {domain_profile.config_context.config_state}.")
                self.logger(level="error", message=message_str)
                if self.task is not None:
                    self.task.taskstep_manager.stop_taskstep(
                        name="AssignDomainProfile", status="failed", status_message=message_str[:255]
                    )
                return False

        except OpenApiException as err:
            self.logger(level="error",
                        message=f"Failed to assign UCS Domain Profile {domain_profile.name} to Fabric Interconnect "
                                f"{imm_domain_name}: {str(err)}")
            if self.task is not None:
                self.task.taskstep_manager.stop_taskstep(
                    name="AssignDomainProfile", status="failed", status_message=str(err)[:255]
                )
            return False

        return True

    def deploy_domain_profile(self, org_name=None, domain_profile_name=None, imm_domain_name=None):
        """
        Checks if domain profile is assigned; if not, it assigns and deploys it.

        :param org_name: Name of the organization to which the domain profile belongs.
        :param domain_profile_name: Name of the domain profile to deploy on the Fabric Interconnect.
        :param imm_domain_name: IMM domain device name.
        :return: bool - True if deployment is successful, False otherwise.
        """

        try:
            # Retrieve registration details of the devices claimed to Intersight
            # - Filters for devices with 'Connected' status and a specific hostname
            device_filter = (f"ConnectionStatus eq Connected and "
                             f"DeviceHostname in ('{imm_domain_name}')")
            registered_devices = self.query(object_type="asset.DeviceRegistration", filter=device_filter)
            if not registered_devices:
                self.logger(
                    level="error",
                    message=f"Deployment cannot proceed: Unable to fetch the target domain '{imm_domain_name}'. "
                            f"Please verify the domain name and ensure it is correctly registered and connected."
                )
                return False

            # Retrieve the Organization Moid using the organization name to identify the correct Switch cluster profile
            org = self.query(object_type='organization.Organization', filter=f"Name eq '{org_name}'")
            if not org:
                self.logger(
                    level="error",
                    message=f"Cannot proceed with deployment: The specified organization {org_name} does not exist."
                )
                return False

            # Check whether the specified organization associated with the resource group has the necessary permissions
            # to access the claimed device.
            has_permission = False
            for resource_org in registered_devices[0].permission_resources:
                if resource_org.moid == org[0].moid:
                    has_permission = True
                    break
            if not has_permission:
                self.logger(
                    level="error",
                    message=f"Cannot proceed with deployment: The target IMM domain '{imm_domain_name}' is not part of "
                            f"any Resource Group assigned to the organization '{org_name}'."
                )
                return False

            # Get the domain profile and attached Fabric Interconnect (FI) information
            # - Filters for the UCS domain profile based on its name and organization
            switch_cluster_profile_filter = f"Name eq '{domain_profile_name}' and Organization.Moid eq '{org[0].moid}'"
            switch_cluster_profile = self.query(object_type="fabric.SwitchClusterProfile",
                                                filter=switch_cluster_profile_filter)

            # Check the status of the switch_cluster_profile, ensuring it is not in "Failed," "Out-of-sync," or
            # "Pending-changes" states.
            if not switch_cluster_profile:
                self.logger(
                    level="error",
                    message=f"Cannot proceed with deployment: Domain profile '{domain_profile_name}' not found in "
                            f"organization '{org_name}'."
                )
                return False
            elif switch_cluster_profile[0].config_context.config_state in ("Failed", "Out-of-sync", "Pending-changes",
                                                                           "Validating", "Configuring"):
                self.logger(
                    level="error",
                    message=f"Deployment cannot proceed as domain profile '{domain_profile_name}' is in "
                            f"inconsistent state: {switch_cluster_profile[0].config_context.config_state}."
                )
                return False

            # Retrieve the network elements associated with the registered device
            # - Based on the Moid (unique ID) of the registered device, get FIs network element info
            network_elements_filter = f"RegisteredDevice.Moid eq '{registered_devices[0].moid}'"
            network_elements = self.query(object_type="network.Element", filter=network_elements_filter)
            if not network_elements:
                self.logger(
                    level="error",
                    message=f"Cannot proceed with deployment: Unable to retrieve network elements for the "
                            f"registered device '{imm_domain_name}'."
                )
                return False

            # Deploy the domain profile if the assignment is completed successfully.
            if self._assign_domain_profile(imm_domain_name, switch_cluster_profile[0], network_elements):
                if self._perform_domain_profile_deployment(imm_domain_name, switch_cluster_profile[0]):
                    self.logger(
                        level="info",
                        message=f"Successfully completed assignment and deployment of domain profile "
                                f"{domain_profile_name}.")
                    return True

        except OpenApiException as error:
            self.logger(level="error", message=f"Error in assign and deployment process: {error}.")
            return False

        return False
