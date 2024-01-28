# coding: utf-8
# !/usr/bin/env python

""" settings.py: Easy UCS Deployment Tool """

import re

from config.intersight.object import IntersightConfigObject

from config.intersight.chassis_profiles import (
    IntersightUcsChassisProfile,
)
from config.intersight.pools import (
    IntersightIpPool,
    IntersightIqnPool,
    IntersightMacPool,
    IntersightResourcePool,
    IntersightUuidPool,
    IntersightWwnnPool,
    IntersightWwpnPool,
)
from config.intersight.fabric_policies import (
    IntersightFabricFlowControlPolicy,
    IntersightFabricLinkAggregationPolicy,
    IntersightFabricLinkControlPolicy,
    IntersightFabricMulticastPolicy,
    IntersightFabricPortPolicy,
    IntersightFabricSwitchControlPolicy,
    IntersightFabricSystemQosPolicy,
    IntersightFabricVlanPolicy,
    IntersightFabricVsanPolicy,
    IntersightUcsDomainProfile,
)
from config.intersight.server_policies import (
    IntersightAdapterConfigurationPolicy,
    IntersightBiosPolicy,
    IntersightBootPolicy,
    IntersightCertificateManagementPolicy,
    IntersightDeviceConnectorPolicy,
    IntersightEthernetAdapterPolicy,
    IntersightEthernetNetworkControlPolicy,
    IntersightEthernetNetworkGroupPolicy,
    IntersightEthernetNetworkPolicy,
    IntersightEthernetQosPolicy,
    IntersightDriveSecurityPolicy,
    IntersightFcZonePolicy,
    IntersightFibreChannelAdapterPolicy,
    IntersightFibreChannelNetworkPolicy,
    IntersightFibreChannelQosPolicy,
    IntersightFirmwarePolicy,
    IntersightImcAccessPolicy,
    IntersightIpmiOverLanPolicy,
    IntersightIscsiAdapterPolicy,
    IntersightIscsiBootPolicy,
    IntersightIscsiStaticTargetPolicy,
    IntersightLanConnectivityPolicy,
    IntersightLdapPolicy,
    IntersightLocalUserPolicy,
    IntersightNetworkConnectivityPolicy,
    IntersightNtpPolicy,
    IntersightPersistentMemoryPolicy,
    IntersightPowerPolicy,
    IntersightSanConnectivityPolicy,
    IntersightSdCardPolicy,
    IntersightSerialOverLanPolicy,
    IntersightSmtpPolicy,
    IntersightSnmpPolicy,
    IntersightSshPolicy,
    IntersightStoragePolicy,
    IntersightSyslogPolicy,
    IntersightThermalPolicy,
    IntersightVirtualKvmPolicy,
    IntersightVirtualMediaPolicy
)
from config.intersight.server_profiles import (
    IntersightUcsServerProfile,
    IntersightUcsServerProfileTemplate,
)


class IntersightAccountDetails(IntersightConfigObject):
    _CONFIG_NAME = "Account Details"
    _CONFIG_SECTION_NAME = "account_details"
    _INTERSIGHT_SDK_OBJECT_NAME = "iam.SessionLimits"

    def __init__(self, parent=None, iam_session_limits=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=iam_session_limits)

        self.account_name = None
        self.default_idle_timeout = self.get_attribute(attribute_name="idle_time_out",
                                                       attribute_secondary_name="default_idle_timeout")
        self.default_session_timeout = self.get_attribute(attribute_name="session_time_out",
                                                          attribute_secondary_name="default_session_timeout")
        self.per_user_limit = self.get_attribute(attribute_name="per_user_limit")

        if self._config.load_from == "live":
            self.account_name = self._get_account_name()

        elif self._config.load_from == "file":
            for attribute in ["account_name"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

    def _get_account_name(self):
        # Fetches the Intersight account name
        if "iam_account" in self._config.sdk_objects:
            if len(self._config.sdk_objects["iam_account"]) != 1:
                self.logger(level="error",
                            message="Unable to determine a unique iam.Account object for fetching the account name")
                return None

            if hasattr(self._config.sdk_objects["iam_account"][0], "name"):
                return self._config.sdk_objects["iam_account"][0].name

        return None

    @IntersightConfigObject.update_taskstep_description(attribute_name="account_name")
    def push_object(self):
        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.account_name}")

        # We first need to fetch the existing iam.SessionLimits object
        iam_session_limits_list = self._device.query(object_type=self._INTERSIGHT_SDK_OBJECT_NAME)

        if len(iam_session_limits_list) != 1:
            self.logger(level="error", message="Could not push " + self._CONFIG_NAME + ". " +
                                               "Could not find existing iam.SessionLimits object")
            return False

        iam_session_limits = iam_session_limits_list[0]
        something_to_commit = False
        if self.default_idle_timeout:
            iam_session_limits.idle_time_out = self.default_idle_timeout
            something_to_commit = True
        if self.default_session_timeout:
            iam_session_limits.session_time_out = self.default_session_timeout
            something_to_commit = True
        if self.per_user_limit:
            iam_session_limits.per_user_limit = self.per_user_limit
            something_to_commit = True

        if something_to_commit:
            if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=iam_session_limits,
                               key_attributes=["moid"], detail=self.account_name):
                return False

        return True


class IntersightOrganization(IntersightConfigObject):
    _CONFIG_NAME = "Organization"
    _CONFIG_SECTION_NAME = "orgs"
    _CONFIG_SECTION_ATTRIBUTES_MAP = {
        "adapter_configuration_policies": "Adapter Configuration Policies",
        "bios_policies": "BIOS Policies",
        "boot_policies": "Boot Policies",
        "certificate_management_policies": "Certificate Management Policies",
        "device_connector_policies": "Device Connector Policies",
        "drive_security_policies": "Drive Security Policies",
        "ethernet_adapter_policies": "Ethernet Adapter Policies",
        "ethernet_network_control_policies": "Ethernet Network Control Policies",
        "ethernet_network_group_policies": "Ethernet Network Group Policies",
        "ethernet_network_policies": "Ethernet Network Policies",
        "ethernet_qos_policies": "Ethernet QOS Policies",
        "fc_zone_policies": "FC Zone Policies",
        "fibre_channel_adapter_policies": "Fibre Channel Adapter Policies",
        "fibre_channel_network_policies": "Fibre Channel Network Policies",
        "fibre_channel_qos_policies": "Fibre Channel QOS Policies",
        "firmware_policies": "Firmware Policies",
        "flow_control_policies": "Flow Control Policies",
        "imc_access_policies": "IMC Access Policies",
        "ip_pools": "IP Pools",
        "ipmi_over_lan_policies": "IPMI Over LAN Policies",
        "iqn_pools": "IQN Pools",
        "iscsi_adapter_policies": "iSCSI Adapter Policies",
        "iscsi_boot_policies": "iSCSI Boot Policies",
        "iscsi_static_target_policies": "iSCSI Static Target Policies",
        "lan_connectivity_policies": "LAN Connectivity Policies",
        "ldap_policies": "LDAP Policies",
        "link_aggregation_policies": "Link Aggregation Policies",
        "link_control_policies": "Link Control Policies",
        "local_user_policies": "Local User Policies",
        "mac_pools": "MAC Pools",
        "multicast_policies": "Multicast Policies",
        "network_connectivity_policies": "Network Connectivity Policies",
        "ntp_policies": "NTP Policies",
        "port_policies": "Port Policies",
        "power_policies": "Power Policies",
        "resource_pools": "Resource Pools",
        "san_connectivity_policies": "SAN Connectivity Policies",
        "sd_card_policies": "SD Card Policies",
        "serial_over_lan_policies": "Serial Over LAN Policies",
        "smtp_policies": "SMTP Policies",
        "snmp_policies": "SNMP Policies",
        "ssh_policies": "SSH Policies",
        "storage_policies": "Storage Policies",
        "switch_control_policies": "Switch Control Policies",
        "syslog_policies": "Syslog Policies",
        "system_qos_policies": "System QOS Policies",
        "thermal_policies": "Thermal Policies",
        "ucs_chassis_profiles": "UCS Chassis Profiles",
        "ucs_domain_profiles": "UCS Domain Profiles",
        "ucs_server_profile_templates": "UCS Server Profile Templates",
        "ucs_server_profiles": "UCS Server Profiles",
        "uuid_pools": "UUID Pools",
        "virtual_kvm_policies": "Virtual KVM Policies",
        "virtual_media_policies": "Virtual Media Policies",
        "vlan_policies": "VLAN Policies",
        "vsan_policies": "VSAN Policies",
        "wwnn_pools": "WWNN Pools",
        "wwpn_pools": "WWPN Pools"
    }
    _INTERSIGHT_SDK_OBJECT_NAME = "organization.Organization"

    def __init__(self, parent=None, organization_organization=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=organization_organization)

        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.name = self.get_attribute(attribute_name="name")
        self.resource_groups = None
        self.shared_with_orgs = None
        self._shared_with_me_orgs = None

        if self._config.load_from == "live":
            self.resource_groups = self._get_resource_groups_names()
            self.shared_with_orgs = self._get_shared_with_org_names()

        elif self._config.load_from == "file":
            for attribute in ["resource_groups", "shared_with_orgs"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

        # Pools
        self.ip_pools = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightIpPool,
            name_to_fetch="ip_pools",
        )
        self.iqn_pools = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightIqnPool,
            name_to_fetch="iqn_pools",
        )
        self.mac_pools = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightMacPool,
            name_to_fetch="mac_pools",
        )
        self.resource_pools = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightResourcePool,
            name_to_fetch="resource_pools",
        )
        self.uuid_pools = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightUuidPool,
            name_to_fetch="uuid_pools",
        )
        self.wwnn_pools = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightWwnnPool,
            name_to_fetch="wwnn_pools",
        )
        self.wwpn_pools = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightWwpnPool,
            name_to_fetch="wwpn_pools",
        )

        # Fabric Policies
        self.flow_control_policies = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightFabricFlowControlPolicy,
            name_to_fetch="flow_control_policies",
        )
        self.link_aggregation_policies = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightFabricLinkAggregationPolicy,
            name_to_fetch="link_aggregation_policies",
        )
        self.link_control_policies = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightFabricLinkControlPolicy,
            name_to_fetch="link_control_policies",
        )
        self.port_policies = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightFabricPortPolicy,
            name_to_fetch="port_policies",
        )
        self.power_policies = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightPowerPolicy,
            name_to_fetch="power_policies",
        )
        self.switch_control_policies = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightFabricSwitchControlPolicy,
            name_to_fetch="switch_control_policies",
        )
        self.system_qos_policies = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightFabricSystemQosPolicy,
            name_to_fetch="system_qos_policies",
        )
        self.multicast_policies = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightFabricMulticastPolicy,
            name_to_fetch="multicast_policies",
        )
        self.vlan_policies = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightFabricVlanPolicy,
            name_to_fetch="vlan_policies",
        )
        self.vsan_policies = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightFabricVsanPolicy,
            name_to_fetch="vsan_policies",
        )
        self.ucs_domain_profiles = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightUcsDomainProfile,
            name_to_fetch="ucs_domain_profiles",
        )

        # Server Policies
        self.adapter_configuration_policies = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightAdapterConfigurationPolicy,
            name_to_fetch="adapter_configuration_policies",
        )
        self.bios_policies = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightBiosPolicy,
            name_to_fetch="bios_policies",
        )
        self.boot_policies = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightBootPolicy,
            name_to_fetch="boot_policies",
        )
        self.certificate_management_policies = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightCertificateManagementPolicy,
            name_to_fetch="certificate_management_policies",
        )
        self.device_connector_policies = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightDeviceConnectorPolicy,
            name_to_fetch="device_connector_policies",
        )
        self.drive_security_policies = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightDriveSecurityPolicy,
            name_to_fetch="drive_security_policies",
        )
        self.ethernet_adapter_policies = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightEthernetAdapterPolicy,
            name_to_fetch="ethernet_adapter_policies",
        )
        self.ethernet_network_control_policies = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightEthernetNetworkControlPolicy,
            name_to_fetch="ethernet_network_control_policies",
        )
        self.ethernet_network_group_policies = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightEthernetNetworkGroupPolicy,
            name_to_fetch="ethernet_network_group_policies",
        )
        self.ethernet_network_policies = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightEthernetNetworkPolicy,
            name_to_fetch="ethernet_network_policies",
        )
        self.ethernet_qos_policies = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightEthernetQosPolicy,
            name_to_fetch="ethernet_qos_policies",
        )
        self.fc_zone_policies = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightFcZonePolicy,
            name_to_fetch="fc_zone_policies",
        )
        self.fibre_channel_adapter_policies = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightFibreChannelAdapterPolicy,
            name_to_fetch="fibre_channel_adapter_policies",
        )
        self.fibre_channel_network_policies = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightFibreChannelNetworkPolicy,
            name_to_fetch="fibre_channel_network_policies",
        )
        self.fibre_channel_qos_policies = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightFibreChannelQosPolicy,
            name_to_fetch="fibre_channel_qos_policies",
        )
        self.firmware_policies = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightFirmwarePolicy,
            name_to_fetch="firmware_policies",
        )
        self.imc_access_policies = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightImcAccessPolicy,
            name_to_fetch="imc_access_policies",
        )
        self.ipmi_over_lan_policies = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightIpmiOverLanPolicy,
            name_to_fetch="ipmi_over_lan_policies",
        )
        self.iscsi_adapter_policies = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightIscsiAdapterPolicy,
            name_to_fetch="iscsi_adapter_policies",
        )
        self.iscsi_boot_policies = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightIscsiBootPolicy,
            name_to_fetch="iscsi_boot_policies",
        )
        self.iscsi_static_target_policies = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightIscsiStaticTargetPolicy,
            name_to_fetch="iscsi_static_target_policies",
        )
        self.lan_connectivity_policies = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightLanConnectivityPolicy,
            name_to_fetch="lan_connectivity_policies",
        )
        self.ldap_policies = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightLdapPolicy,
            name_to_fetch="ldap_policies",
        )
        self.local_user_policies = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightLocalUserPolicy,
            name_to_fetch="local_user_policies",
        )
        self.network_connectivity_policies = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightNetworkConnectivityPolicy,
            name_to_fetch="network_connectivity_policies",
        )
        self.ntp_policies = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightNtpPolicy,
            name_to_fetch="ntp_policies",
        )
        self.persistent_memory_policies = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightPersistentMemoryPolicy,
            name_to_fetch="persistent_memory_policies",
        )
        self.san_connectivity_policies = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightSanConnectivityPolicy,
            name_to_fetch="san_connectivity_policies",
        )
        self.sd_card_policies = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightSdCardPolicy,
            name_to_fetch="sd_card_policies",
        )
        self.serial_over_lan_policies = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightSerialOverLanPolicy,
            name_to_fetch="serial_over_lan_policies",
        )
        self.smtp_policies = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightSmtpPolicy,
            name_to_fetch="smtp_policies",
        )
        self.snmp_policies = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightSnmpPolicy,
            name_to_fetch="snmp_policies",
        )
        self.ssh_policies = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightSshPolicy,
            name_to_fetch="ssh_policies",
        )
        self.storage_policies = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightStoragePolicy,
            name_to_fetch="storage_policies",
        )
        self.syslog_policies = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightSyslogPolicy,
            name_to_fetch="syslog_policies",
        )
        self.thermal_policies = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightThermalPolicy,
            name_to_fetch="thermal_policies",
        )
        self.virtual_kvm_policies = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightVirtualKvmPolicy,
            name_to_fetch="virtual_kvm_policies",
        )
        self.virtual_media_policies = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightVirtualMediaPolicy,
            name_to_fetch="virtual_media_policies",
        )
        self.ucs_chassis_profiles = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightUcsChassisProfile,
            name_to_fetch="ucs_chassis_profiles",
        )

        # Server Profile Templates
        # We need to parse templates before profiles, because we need the template obj to identify the IMC Access Policy
        # attached to the profiles (when cloning Intersight config with identities preservation).
        self.ucs_server_profile_templates = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightUcsServerProfileTemplate,
            name_to_fetch="ucs_server_profile_templates",
        )

        # Server Profiles
        self.ucs_server_profiles = self._get_generic_element(
            json_content=organization_organization,
            object_class=IntersightUcsServerProfile,
            name_to_fetch="ucs_server_profiles",
        )

    def _get_generic_element(self, json_content, object_class, name_to_fetch):
        # Generic method to instantiate objects under an Org depending on loading from live or from file
        if self._config.load_from == "live":
            list_of_obj = self.instantiate_config_objects_under_org(org=self, object_class=object_class)
            return list_of_obj
        elif self._config.load_from == "file" and json_content is not None:
            if name_to_fetch in json_content:
                return [object_class(self, generic) for generic in json_content[name_to_fetch]]
        else:
            return []

    def _get_resource_groups_names(self):
        if hasattr(self._object, "resource_groups"):
            if self._object.resource_groups:
                resource_group_list = self.get_config_objects_from_ref(ref=self._object.resource_groups)
                if (len(resource_group_list)) == 0:
                    self.logger(level="debug",
                                message="Could not find any assigned Resource Group for Organization " + self.name)
                    return None
                else:
                    # We return a list of the resource_group names
                    resource_group_names = []
                    for resource_group in resource_group_list:
                        if hasattr(resource_group, "name"):
                            resource_group_names.append(resource_group.name)

                    return resource_group_names
        return None

    def _get_shared_with_org_names(self):
        if hasattr(self._object, "shared_with_resources"):
            if self._object.shared_with_resources:
                resources_list = self.get_config_objects_from_ref(ref=self._object.shared_with_resources)
                if (len(resources_list)) == 0:
                    self.logger(level="debug",
                                message="Could not find any shared with resources for Organization " + self.name)
                    return None
                else:
                    # We return a list of the resource_group names
                    org_names = []
                    for resource in resources_list:
                        if getattr(resource, "object_type", None) == "organization.Organization" and \
                                hasattr(resource, "name"):
                            org_names.append(resource.name)

                    return org_names

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.organization_organization import OrganizationOrganization

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        # Flag to determine whether to delete the resource group membership of the shared organization.
        delete_existing_resource_group_memberships_for_intersight_shared_orgs = \
            self._config.delete_existing_resource_group_memberships_for_intersight_shared_orgs
        # Flag to determine whether to update an already existing object in Intersight or not. Has to be set only
        # when below 2nd condition is true.
        modify_present = False

        # Determining the list of Resource Groups we assign to our organization
        # Intersight does not allow shared organizations to have resource groups. So, to manage
        # organization + resource group "push" we have the following scenario:
        # 1. Resource group present + No Shared Orgs: Get the resource groups and attach them to the organization.
        # 2. Resource group present + Share Orgs are present +
        # delete_existing_resource_group_memberships_for_intersight_shared_orgs flag is set: In this case do not fetch
        # and resource groups and proceed with empty resource group list
        # 3. Resource group present + Share Orgs are present +
        # delete_existing_resource_group_memberships_for_intersight_shared_orgs flag is false: Raise an error
        # explaining that "Intersight does not support attaching resource groups to shared organizations."
        resource_group_list = []
        if self.resource_groups:
            if not self.shared_with_orgs:
                for resource_group in self.resource_groups:
                    # We need to retrieve the resource.Group object for assigning the correct Resource Group
                    rg_list = self._device.query(object_type="resource.Group", filter="Name eq '%s'" % resource_group)

                    if rg_list:
                        if len(rg_list) != 1:
                            self.logger(level="warning",
                                        message="Could not find unique Resource Group '" + resource_group +
                                                "' to assign to Organization '" + self.name + "'")
                        else:
                            resource_group_list.append(self.create_relationship_equivalent(sdk_object=rg_list[0]))

                    else:
                        self.logger(level="warning",
                                    message="Could not find Resource Group '" + resource_group +
                                            "' to assign to Organization '" + self.name + "'")
            elif delete_existing_resource_group_memberships_for_intersight_shared_orgs:
                modify_present = True
                self.logger(level="info", message=f"This org {self.name} is shared with other organization, deleting "
                                                  "all the associated Resource Group memberships.")
            else:
                err_message = f"Failed to push organization '{self.name}'. An organization in Intersight cannot have " \
                              f"Resource Groups if it's also shared with other organizations."
                self.logger(level="error", message=err_message)
                self._config.push_summary_manager.add_object_status(obj=self, obj_detail=self.name,
                                                                    obj_type=self._INTERSIGHT_SDK_OBJECT_NAME,
                                                                    status="failed", message=err_message)
                return False

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME
        }
        if resource_group_list or delete_existing_resource_group_memberships_for_intersight_shared_orgs:
            kwargs["resource_groups"] = resource_group_list
        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()

        organization_organization = OrganizationOrganization(**kwargs)

        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=organization_organization,
                           detail=self.name, modify_present=modify_present):
            return False

        return True

    @IntersightConfigObject.update_taskstep_description()
    def push_sharing_rules(self):
        # Create the sharing rules, if this org is shared with other orgs
        if self.shared_with_orgs:
            # We now need to bulk push the iam.SharingRules object
            from intersight.model.bulk_request import BulkRequest
            from intersight.model.bulk_sub_request import BulkSubRequest
            from intersight.model.mo_base_mo import MoBaseMo

            bulk_request_kwargs = {
                "uri": "/v1/iam/SharingRules",
                "verb": "POST",
                "requests": []
            }
            requests = []

            for shared_with_org in self.shared_with_orgs:
                body_kwargs = {
                    "object_type": "iam.SharingRule",
                    "class_id": "iam.SharingRule",
                    "shared_resource": self.get_org_relationship(org_name=self.name),
                    "shared_with_resource": self.get_org_relationship(org_name=shared_with_org)
                }

                body = MoBaseMo(**body_kwargs)

                sub_request_kwargs = {
                    "object_type": "bulk.RestSubRequest",
                    "class_id": "bulk.RestSubRequest",
                    "body": body
                }

                sub_request = BulkSubRequest(**sub_request_kwargs)

                requests.append(sub_request)

            bulk_request_kwargs["requests"] = requests
            bulk_request = BulkRequest(**bulk_request_kwargs)

            detail = f"{self.name} - Sharing Rules - Sharing Org with {self.shared_with_orgs})"
            if not self.commit(object_type="bulk.Request", payload=bulk_request, detail=detail, key_attributes=[]):
                return False
        return True

    @IntersightConfigObject.update_taskstep_description()
    def push_subobjects(self):
        # We push all subconfig elements, in a specific optimized order
        # TODO: Verify order
        objects_to_push_in_order = [
            'ip_pools', 'iqn_pools', 'mac_pools', 'resource_pools', 'uuid_pools', 'wwnn_pools', 'wwpn_pools',
            'flow_control_policies', 'link_aggregation_policies', 'link_control_policies', 'switch_control_policies',
            'system_qos_policies', 'multicast_policies', 'vlan_policies', 'vsan_policies', 'local_user_policies',
            'adapter_configuration_policies', 'bios_policies', 'boot_policies', 'certificate_management_policies',
            'device_connector_policies', 'drive_security_policies', 'ethernet_adapter_policies',
            'ethernet_network_control_policies', 'ethernet_network_group_policies', 'ethernet_network_policies',
            'ethernet_qos_policies', 'fc_zone_policies', 'fibre_channel_adapter_policies',
            'fibre_channel_network_policies', 'fibre_channel_qos_policies', 'firmware_policies', 'imc_access_policies',
            'ipmi_over_lan_policies', 'iscsi_adapter_policies', 'iscsi_static_target_policies', 'iscsi_boot_policies',
            'ldap_policies', 'network_connectivity_policies', 'ntp_policies', 'persistent_memory_policies',
            'power_policies', 'sd_card_policies', 'serial_over_lan_policies', 'smtp_policies', 'snmp_policies',
            'ssh_policies', 'storage_policies', 'syslog_policies', 'thermal_policies', 'virtual_kvm_policies',
            'virtual_media_policies', 'lan_connectivity_policies', 'san_connectivity_policies', 'port_policies',
            'ucs_domain_profiles', 'ucs_chassis_profiles', 'ucs_server_profile_templates', 'ucs_server_profiles']

        is_pushed = True
        for config_object_type in objects_to_push_in_order:
            if getattr(self, config_object_type) is not None:
                if getattr(self, config_object_type).__class__.__name__ == "list":
                    for subobject in getattr(self, config_object_type):
                        is_pushed = subobject.push_object() and is_pushed

        return is_pushed


class IntersightResourceGroup(IntersightConfigObject):
    _CONFIG_NAME = "Resource Group"
    _CONFIG_SECTION_NAME = "resource_groups"
    _INTERSIGHT_SDK_OBJECT_NAME = "resource.Group"

    def __init__(self, parent=None, resource_group=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=resource_group)

        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.name = self.get_attribute(attribute_name="name")
        self.devices = None
        self.memberships = None

        if self._config.load_from == "live":
            self.memberships = self._determine_memberships()
            if self.memberships == "custom":
                self.devices = self._get_member_devices()

        elif self._config.load_from == "file":
            for attribute in ["devices", "memberships"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

    def _determine_memberships(self):
        # Determines if the Resource Group has a memberships set to "All" or "Custom"
        if hasattr(self._object, "qualifier"):
            if self._object.qualifier == "Allow-All":
                return "all"
            else:
                return "custom"

        return None

    def _get_member_devices(self):
        # Get the list of member devices per Resource Group in case memberships is "custom"
        # We read the PerTypeCombinedSelector attribute of the resource.Group to find the devices
        if hasattr(self._object, "per_type_combined_selector"):
            if self._object.per_type_combined_selector:
                device_list = []
                for per_type_combined_selector in self._object.per_type_combined_selector:
                    combined_selector = per_type_combined_selector.combined_selector
                    selector_object_type = per_type_combined_selector.selector_object_type

                    if selector_object_type == "asset.DeviceRegistration":
                        # We use a regex to get the MOIDs of devices member of the org
                        regex_device_moid = r"([a-f0-9]{24})"
                        res_devices = re.findall(regex_device_moid, combined_selector)

                        for device_moid in res_devices:
                            asset_device_registration_list = self.get_config_objects_from_ref(
                                ref={"object_type": "asset.DeviceRegistration", "moid": device_moid})
                            if len(asset_device_registration_list) != 1:
                                self.logger(level="debug",
                                            message="Could not find the appropriate asset.DeviceRegistration " +
                                                    "for Resource Group '" + self.name + "'")
                            else:
                                device_name = asset_device_registration_list[0].device_hostname[0]
                                device_list.append({"moid": device_moid, "name": device_name})
                        return device_list

        return None

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.resource_group import ResourceGroup

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        # Determining if we have a custom membership with a list of devices
        moid_list = []
        if self.memberships == "custom" and self.devices:
            for device in self.devices:
                if "moid" in device:
                    moid_list.append(device["moid"])
                elif "name" in device:
                    # We need to retrieve the device MOID for setting membership
                    device_list = self._device.query(object_type="asset.DeviceRegistration",
                                                     filter="contains(DeviceHostname, '%s')" % device["name"])

                    if device_list:
                        if len(device_list) != 1:
                            self.logger(level="warning",
                                        message="Could not find device '" + device["name"] +
                                                "' to assign membership to Resource Group " + self.name)
                        else:
                            if hasattr(device_list[0], "moid"):
                                moid_list.append(device_list[0].moid)
                            else:
                                self.logger(level="warning",
                                            message="Could not find moid for device '" + device["name"] +
                                                    "' to assign membership to Resource Group " + self.name)
                    else:
                        self.logger(level="warning", message="Could not find device '" + device["name"] +
                                                             "' to assign membership to Resource Group " + self.name)

        from intersight.model.resource_selector import ResourceSelector

        selector = "/api/v1/asset/DeviceRegistrations"
        if self.memberships == "custom" and moid_list:
            selector += "?$filter=Moid in ('"
            selector += "','".join(moid_list)
            selector += "')"

        resource_selector = ResourceSelector(
            object_type="resource.Selector",
            class_id="resource.Selector",
            selector=selector
        )

        kwargs = {
            "object_type": "resource.Group",
            "class_id": "resource.Group"
        }
        if self.name is not None:
            kwargs["name"] = self.name
        if self.memberships == "all":
            kwargs["qualifier"] = "Allow-All"
        else:
            kwargs["qualifier"] = "Allow-Selectors"
            if moid_list:
                kwargs["selectors"] = [resource_selector]
            else:
                # EASYUCS-893: If there is no device Moid found for the selector, we push an empty list instead
                kwargs["selectors"] = []

        resource_group = ResourceGroup(**kwargs)

        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=resource_group, detail=self.name):
            return False

        return True


class IntersightRole(IntersightConfigObject):
    _CONFIG_NAME = "Role"
    _CONFIG_SECTION_NAME = "roles"
    _INTERSIGHT_SDK_OBJECT_NAME = "iam.Permission"

    def __init__(self, parent=None, iam_permission=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=iam_permission)

        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.name = self.get_attribute(attribute_name="name")
        self.operational_state = {}

        if self._config.load_from == "live":
            self.access_control = None
            self.scope = None
            self.privileges = None
            self.scope = self._determine_scope()
            if self.scope:
                if self.scope == "all":
                    self.privileges = self._get_privileges_names()
                elif self.scope == "organization":
                    self.access_control = self._get_access_control()
            if hasattr(self._object, "tags") and self._object.tags:
                for tag in self._object.tags:
                    if "cisco.meta.creatorType" == tag["key"]:
                        self.operational_state["creator_type"] = tag["value"]
                        break

        elif self._config.load_from == "file":
            for attribute in ["access_control", "operational_state", "privileges", "scope"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

            if self.operational_state:
                for value in ["creator_type"]:
                    if value not in self.operational_state:
                        self.operational_state[value] = None

    def _determine_scope(self):
        # Determines if the role has a scope "all" or is limited to a set of organizations
        if hasattr(self._object, "resource_roles"):
            if isinstance(self._object.resource_roles, list):
                if len(self._object.resource_roles) != 0:
                    return "organization"
                else:
                    return "all"
            elif not self._object.resource_roles:
                return "all"
        return None

    def _get_access_control(self):
        # Get the list of privileges names per organization in case Role is in scope "organization"
        if hasattr(self._object, "resource_roles"):
            if self._object.resource_roles is not None:
                iam_resource_roles_list = \
                    self.get_config_objects_from_ref(ref=self._object.resource_roles)
                if (len(iam_resource_roles_list)) == 0:
                    self.logger(level="debug", message="Could not find the appropriate iam.ResourceRoles for " +
                                                       " iam.Permission with MOID " + str(self._moid))
                    return None
                else:
                    # We return a list of dict containing the org names and matching iam_roles names
                    access_control = []
                    for iam_resource_roles in iam_resource_roles_list:
                        access_control_entry = None
                        if hasattr(iam_resource_roles, "resource"):
                            if iam_resource_roles.resource is not None:
                                organization_organization_list = \
                                    self.get_config_objects_from_ref(ref=iam_resource_roles.resource)
                                if (len(organization_organization_list)) != 1:
                                    self.logger(level="debug",
                                                message="Could not find the appropriate organization.Organization " +
                                                        " for iam.ResourceRole with MOID " + iam_resource_roles.moid)
                                    continue
                                else:
                                    org_name = organization_organization_list[0].name
                                    access_control_entry = {"organization": org_name}

                        if hasattr(iam_resource_roles, "roles"):
                            if iam_resource_roles.roles is not None:
                                iam_role_list = \
                                    self.get_config_objects_from_ref(ref=iam_resource_roles.roles)
                                if (len(iam_role_list)) == 0:
                                    self.logger(level="debug",
                                                message="Could not find any iam.Role for iam.ResourceRole with MOID " +
                                                        iam_resource_roles.moid)
                                    continue
                                else:
                                    access_control_entry["privileges"] = []
                                    for iam_role in iam_role_list:
                                        access_control_entry["privileges"].append(iam_role.name)

                        if access_control_entry:
                            access_control.append(access_control_entry)

                    return access_control
            return None

    def _get_privileges_names(self):
        # Get the list of privileges names in case Role is in scope "all"
        if hasattr(self._object, "roles"):
            if self._object.roles is not None:
                iam_role_list = self.get_config_objects_from_ref(ref=self._object.roles)
                if (len(iam_role_list)) == 0:
                    self.logger(level="debug",
                                message="Could not find the appropriate iam.Role for iam.Permission with MOID " +
                                        str(self._moid))
                    return None
                else:
                    # We return a list of the iam_role names
                    iam_role_names = []
                    for iam_role in iam_role_list:
                        if hasattr(iam_role, "name"):
                            iam_role_names.append(iam_role.name)

                    return iam_role_names
        return None

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.iam_permission import IamPermission

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        iam_permission = None
        if self.scope == "all":
            # Determining the list of privileges we assign to our role
            privilege_list = []
            if self.privileges:
                for privilege in self.privileges:
                    # We need to retrieve the iam.Role object for assigning the correct privilege
                    iam_role_list = self._device.query(object_type="iam.Role", filter="Name eq '%s'" % privilege)

                    if iam_role_list:
                        if len(iam_role_list) != 1:
                            self.logger(level="warning",
                                        message="Could not find privilege '" + privilege + "' to assign to role " +
                                                self.name)
                        else:
                            privilege_list.append(iam_role_list[0])

                    else:
                        self.logger(level="warning", message="Could not find privilege '" + privilege +
                                                             "' to assign to role " + self.name)

            # We first need to create a list of iam.RoleRelationship objects to assign to our user
            role_relationship_list = []
            for privilege in privilege_list:
                role_relationship_list.append(self.create_relationship_equivalent(sdk_object=privilege))

            kwargs = {
                "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
                "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
                "roles": role_relationship_list
            }
            if self.name is not None:
                kwargs["name"] = self.name
            if self.descr is not None:
                kwargs["description"] = self.descr

            iam_permission = IamPermission(**kwargs)

        elif self.scope == "organization":
            # We first need to create the role without associated access control
            kwargs = {
                "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
                "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            }
            if self.name is not None:
                kwargs["name"] = self.name
            if self.descr is not None:
                kwargs["description"] = self.descr

            iam_permission = IamPermission(**kwargs)

        ip = self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=iam_permission, detail=self.name,
                         return_relationship=True)
        if not ip:
            return False

        if self.scope == "organization":
            from intersight.model.iam_resource_roles import IamResourceRoles
            # We now need to create the iam.ResourceRoles for each entry in the access control
            for access_control in self.access_control:
                org_name = access_control["organization"]

                # We need to retrieve the organization.Organization object for assigning the correct access control
                org_list = self._device.query(object_type="organization.Organization", filter="Name eq '%s'" % org_name)

                if org_list:
                    if len(org_list) != 1:
                        self.logger(level="warning",
                                    message="Could not find organization '" + org_name + "' to assign to role " +
                                            self.name)
                        continue
                    else:
                        org = org_list[0]

                else:
                    self.logger(level="warning",
                                message="Could not find organization '" + org_name + "' to assign to role " + self.name)
                    continue

                # We create the equivalent org relationship
                from intersight.model.mo_base_mo_relationship import MoBaseMoRelationship
                org_relationship = MoBaseMoRelationship(
                    object_type="organization.Organization",
                    class_id="mo.MoRef",
                    moid=org.moid
                )

                # We now need to retrieve the iam.Role object for each entry in the privileges list and commit the
                # corresponding access control
                privilege_list = []
                for privilege in access_control["privileges"]:
                    iam_role_list = self._device.query(object_type="iam.Role", filter="Name eq '%s'" % privilege)

                    if iam_role_list:
                        if len(iam_role_list) != 1:
                            self.logger(level="warning",
                                        message="Could not find privilege '" + privilege + "' to assign to role " +
                                                self.name + " in org " + org_name)
                            continue
                        else:
                            privilege_list.append(iam_role_list[0])

                    else:
                        self.logger(level="warning",
                                    message="Could not find privilege '" + privilege + "' to assign to role " +
                                            self.name + " in org " + org_name)
                        continue

                # We need to create a list of iam.RoleRelationship objects to assign to our user
                role_relationship_list = []
                for privilege in privilege_list:
                    role_relationship_list.append(self.create_relationship_equivalent(sdk_object=privilege))

                iam_resource_roles = IamResourceRoles(
                    object_type="iam.ResourceRoles",
                    class_id="iam.ResourceRoles",
                    permission=ip,
                    resource=org_relationship,
                    roles=role_relationship_list
                )

                if not self.commit(object_type="iam.ResourceRoles", payload=iam_resource_roles,
                                   detail=self.name + " - Access Control for Org " + org_name):
                    return False

        return True


class IntersightUser(IntersightConfigObject):
    _CONFIG_NAME = "User"
    _CONFIG_SECTION_NAME = "users"
    _INTERSIGHT_SDK_OBJECT_NAME = "iam.User"

    def __init__(self, parent=None, iam_user=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=iam_user)

        self.email = self.get_attribute(attribute_name="email")
        self.name = self.get_attribute(attribute_name="name")

        self.identity_provider = None
        self.roles = []

        if self._config.load_from == "live":
            self.identity_provider = self._get_identity_provider_name()
            self.roles = self._get_roles_names()

        elif self._config.load_from == "file":
            for attribute in ["identity_provider", "roles"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

    def _get_identity_provider_name(self):
        if hasattr(self._object, "idp"):
            if self._object.idp is not None:
                idp_list = self.get_config_objects_from_ref(ref=self._object.idp)
                if (len(idp_list)) == 0:
                    self.logger(level="debug",
                                message="Could not find the appropriate iam.Idp for iam.User with MOID " +
                                str(self._moid))
                    return None
                else:
                    # We return the iam_idp found name value
                    if hasattr(idp_list[0], "name"):
                        return idp_list[0].name
            else:
                # IDP is empty, so it means we are using the default "Cisco" or "Local" IDP
                if self._device.is_appliance:
                    return "Local"
                return "Cisco"

        return None

    def _get_roles_names(self):
        if hasattr(self._object, "permissions"):
            if self._object.permissions is not None:
                iam_permission_list = self.get_config_objects_from_ref(ref=self._object.permissions)
                if (len(iam_permission_list)) == 0:
                    self.logger(level="debug",
                                message="Could not find the appropriate iam.Permission for iam.User with MOID " +
                                        str(self._moid))
                    return None
                else:
                    # We return a list of the iam_permission names
                    iam_permission_names = []
                    for iam_permission in iam_permission_list:
                        if hasattr(iam_permission, "name"):
                            iam_permission_names.append(iam_permission.name)

                    return iam_permission_names
        return None

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.iam_user import IamUser

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        # Determining the list of roles we assign to our user
        role_list = []
        if self.roles:
            for role in self.roles:
                # We need to retrieve the iam.Permission object for assigning the correct role
                iam_permission_list = self._device.query(object_type="iam.Permission", filter="Name eq '%s'" % role)

                if iam_permission_list:
                    if len(iam_permission_list) != 1:
                        self.logger(level="warning",
                                    message="Could not find role '" + role + "' to assign to user " + self.name)
                    else:
                        role_list.append(iam_permission_list[0])

                else:
                    self.logger(level="warning",
                                message="Could not find role '" + role + "' to assign to user " + self.name)

        # We first need to create a list of iam.PermissionRelationship objects to assign to our user
        permission_relationship_list = []
        for role in role_list:
            permission_relationship_list.append(self.create_relationship_equivalent(sdk_object=role))

        # We now need to take care of the Identity Provider attribute
        if self._device.is_appliance:
            self.identity_provider = "Local"
        if self.identity_provider and (self.identity_provider != "Cisco" or self._device.is_appliance):
            identity_provider_relationship = None
            iam_idp_list = self._device.query(object_type="iam.Idp", filter="Name eq '%s'" % self.identity_provider)
            if iam_idp_list:
                if len(iam_idp_list) != 1:
                    self.logger(level="warning", message="Could not find Identity Provider '" + self.identity_provider +
                                                         "' to assign to user " + self.email)
                else:
                    identity_provider_relationship = self.create_relationship_equivalent(sdk_object=iam_idp_list[0])

            else:
                self.logger(level="warning", message="Could not find Identity Provider '" + self.identity_provider +
                                                     "' to assign to user " + self.email)

            iam_user = IamUser(
                object_type=self._INTERSIGHT_SDK_OBJECT_NAME,
                class_id=self._INTERSIGHT_SDK_OBJECT_NAME,
                email=self.email,
                idp=identity_provider_relationship,
                idpreference=None,
                permissions=permission_relationship_list
            )
        else:
            # In case Identity Provider is not present - default value is "Cisco" and is the Reference Identity Provider
            identity_provider_reference_relationship = None
            iam_idpreference_list = self._device.query(object_type="iam.IdpReference", filter="Name eq '%s'" % "Cisco")
            if iam_idpreference_list:
                if len(iam_idpreference_list) != 1:
                    self.logger(level="warning", message="Could not find Identity Provider Reference 'Cisco' to " +
                                                         "assign to user " + self.email)
                else:
                    identity_provider_reference_relationship = \
                        self.create_relationship_equivalent(sdk_object=iam_idpreference_list[0])

            else:
                self.logger(level="warning", message="Could not find Identity Provider Reference 'Cisco' to assign " +
                                                     "to user " + self.email)

            iam_user = IamUser(
                object_type=self._INTERSIGHT_SDK_OBJECT_NAME,
                class_id=self._INTERSIGHT_SDK_OBJECT_NAME,
                email=self.email,
                idp=None,
                idpreference=identity_provider_reference_relationship,
                permissions=permission_relationship_list
            )

        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=iam_user, key_attributes=["email"],
                           detail=self.email):
            return False

        return True


class IntersightUserGroup(IntersightConfigObject):
    _CONFIG_NAME = "User Group"
    _CONFIG_SECTION_NAME = "user_groups"
    _INTERSIGHT_SDK_OBJECT_NAME = "iam.UserGroup"

    def __init__(self, parent=None, iam_user_group=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=iam_user_group)

        self.name = self.get_attribute(attribute_name="name")

        self.group_name_in_identity_provider = None
        self.identity_provider = None
        self.roles = []

        if self._config.load_from == "live":
            self.group_name_in_identity_provider = self._get_group_name_in_idp()
            self.identity_provider = self._get_identity_provider_name()
            self.roles = self._get_roles_names()

        elif self._config.load_from == "file":
            for attribute in ["group_name_in_identity_provider", "identity_provider", "roles"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

    def _get_group_name_in_idp(self):
        if hasattr(self._object, "qualifier"):
            if self._object.qualifier is not None:
                qualifier_list = self.get_config_objects_from_ref(ref=self._object.qualifier)
                if (len(qualifier_list)) == 0:
                    self.logger(level="debug",
                                message="Could not find the appropriate iam.Qualifier for iam.UserGroup with MOID " +
                                str(self._moid))
                    return None
                else:
                    # We return the iam_qualifier found value
                    if hasattr(qualifier_list[0], "value"):
                        return qualifier_list[0].value[0]

        return None

    def _get_identity_provider_name(self):
        if hasattr(self._object, "idp"):
            if self._object.idp is not None:
                idp_list = self.get_config_objects_from_ref(ref=self._object.idp)
                if (len(idp_list)) == 0:
                    self.logger(level="debug",
                                message="Could not find the appropriate Identity Provider for user with MOID " +
                                str(self._moid))
                    return None
                else:
                    # We return the iam_idp found name value
                    if hasattr(idp_list[0], "name"):
                        return idp_list[0].name
            else:
                # IDP is empty, so it means we are using the default "Cisco" or "Local" IDP
                if self._device.is_appliance:
                    return "Local"
                return "Cisco"

        return None

    def _get_roles_names(self):
        if hasattr(self._object, "permissions"):
            if self._object.permissions is not None:
                iam_permission_list = self.get_config_objects_from_ref(ref=self._object.permissions)
                if (len(iam_permission_list)) == 0:
                    self.logger(level="debug",
                                message="Could not find the appropriate iam.Permission for user with MOID " +
                                        str(self._moid))
                    return None
                else:
                    # We return a list of the iam_permission names
                    iam_permission_names = []
                    for iam_permission in iam_permission_list:
                        if hasattr(iam_permission, "name"):
                            iam_permission_names.append(iam_permission.name)

                    return iam_permission_names
        return None

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.iam_user_group import IamUserGroup

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        # Determining the list of roles we assign to our user group
        role_list = []
        if self.roles:
            for role in self.roles:
                # We need to retrieve the iam.Permission object for assigning the correct role
                iam_permission_list = self._device.query(object_type="iam.Permission", filter="Name eq '%s'" % role)

                if iam_permission_list:
                    if len(iam_permission_list) != 1:
                        self.logger(level="warning",
                                    message="Could not find role '" + role + "' to assign to user " + self.name)
                    else:
                        role_list.append(iam_permission_list[0])

                else:
                    self.logger(level="warning",
                                message="Could not find role '" + role + "' to assign to user " + self.name)

        # We now need to create a list of iam.PermissionRelationship objects to assign to our user
        permission_relationship_list = []
        for role in role_list:
            permission_relationship_list.append(self.create_relationship_equivalent(sdk_object=role))

        # Then we need to take care of the Identity Provider attribute
        if self._device.is_appliance:
            self.identity_provider = "Local"
        if self.identity_provider and (self.identity_provider != "Cisco" or self._device.is_appliance):
            identity_provider_relationship = None
            iam_idp_list = self._device.query(object_type="iam.Idp", filter="Name eq '%s'" % self.identity_provider)
            if iam_idp_list:
                if len(iam_idp_list) != 1:
                    self.logger(level="warning", message="Could not find Identity Provider '" + self.identity_provider +
                                                         "' to assign to user group " + self.name)
                else:
                    identity_provider_relationship = self.create_relationship_equivalent(sdk_object=iam_idp_list[0])

            else:
                self.logger(level="warning", message="Could not find Identity Provider '" + self.identity_provider +
                                                     "' to assign to user group " + self.name)

            iam_user_group = IamUserGroup(
                object_type=self._INTERSIGHT_SDK_OBJECT_NAME,
                class_id=self._INTERSIGHT_SDK_OBJECT_NAME,
                name=self.name,
                idp=identity_provider_relationship,
                idpreference=None,
                permissions=permission_relationship_list
            )
        else:
            # In case Identity Provider is not present - default value is "Cisco" and is the Reference Identity Provider
            identity_provider_reference_relationship = None
            iam_idpreference_list = self._device.query(object_type="iam.IdpReference", filter="Name eq '%s'" % "Cisco")
            if iam_idpreference_list:
                if len(iam_idpreference_list) != 1:
                    self.logger(level="warning", message="Could not find Identity Provider Reference 'Cisco' to " +
                                                         "assign to user group " + self.name)
                else:
                    identity_provider_reference_relationship = \
                        self.create_relationship_equivalent(sdk_object=iam_idpreference_list[0])

            else:
                self.logger(level="warning", message="Could not find Identity Provider Reference 'Cisco' to assign " +
                                                     "to user group " + self.name)

            iam_user_group = IamUserGroup(
                object_type=self._INTERSIGHT_SDK_OBJECT_NAME,
                class_id=self._INTERSIGHT_SDK_OBJECT_NAME,
                name=self.name,
                idp=None,
                idpreference=identity_provider_reference_relationship,
                permissions=permission_relationship_list
            )

        iug = self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=iam_user_group, detail=self.name,
                          return_relationship=True)
        if not iug:
            return False

        # Finally we need to push the associated iam.Qualifier
        from intersight.model.iam_qualifier import IamQualifier

        iam_qualifier = IamQualifier(
            object_type="iam.Qualifier",
            class_id="iam.Qualifier",
            value=[self.group_name_in_identity_provider],
            usergroup=iug
        )

        if not self.commit(object_type="iam.Qualifier", payload=iam_qualifier,
                           detail=self.name + "- IAM Qualifier"):
            return False

        return True
