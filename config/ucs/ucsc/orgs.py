# coding: utf-8
# !/usr/bin/env python

""" orgs.py: Easy UCS Central Orgs objects """

from ucscsdk.mometa.compute.ComputeOwnerQual import ComputeOwnerQual
from ucscsdk.mometa.compute.ComputeSiteQual import ComputeSiteQual
from ucscsdk.mometa.compute.ComputeSystemAddrQual import ComputeSystemAddrQual
from ucscsdk.mometa.compute.ComputeSystemQual import ComputeSystemQual
from ucscsdk.mometa.org.OrgOrg import OrgOrg

from config.ucs.object import UcsCentralConfigObject
from config.ucs.ucsc.pools import UcsCentralIpPool, UcsCentralIqnPool, UcsCentralMacPool, \
    UcsCentralServerPool, UcsCentralUuidPool, UcsCentralWwnnPool, UcsCentralWwpnPool, UcsCentralWwxnPool
from config.ucs.ucsc.policies import UcsCentralBiosPolicy, UcsCentralBootPolicy, UcsCentralChassisFirmwarePackage, \
    UcsCentralComputeConnectionPolicy,  UcsCentralDiskGroupPolicy, UcsCentralDiskZoningPolicy, \
    UcsCentralDynamicVnicConnectionPolicy, UcsCentralEthernetAdapterPolicy, UcsCentralFibreChannelAdapterPolicy, \
    UcsCentralGraphicsCardPolicy, UcsCentralHostFirmwarePackage, UcsCentralHostInterfacePlacementPolicy, \
    UcsCentralIdRangeAccessControlPolicy, UcsCentralIpmiAccessProfile, UcsCentralIscsiAdapterPolicy, \
    UcsCentralIscsiAuthenticationProfile, UcsCentralLanConnectivityPolicy, UcsCentralLocalDiskConfPolicy,  \
    UcsCentralMaintenancePolicy, UcsCentralNetworkControlPolicy, UcsCentralPowerControlPolicy,\
    UcsCentralPowerSyncPolicy, UcsCentralQosPolicy, UcsCentralSanConnectivityPolicy, UcsCentralScrubPolicy, \
    UcsCentralSerialOverLanPolicy, UcsCentralServerPoolPolicyQualifications, UcsCentralStorageConnectionPolicy, \
    UcsCentralStorageProfile, UcsCentralThresholdPolicy, UcsCentralUsnicConnectionPolicy, UcsCentralVmediaPolicy, \
    UcsCentralVmqConnectionPolicy

from config.ucs.ucsc.profiles import UcsCentralChassisProfile, UcsCentralServiceProfile
from config.ucs.ucsc.templates import UcsCentralVhbaTemplate, UcsCentralVnicTemplate


class UcsCentralDomainGroupQualificationPolicy(UcsCentralConfigObject):
    _CONFIG_NAME = "Domain Group Qualification Policy"
    _CONFIG_SECTION_NAME = "domain_group_qualification_policies"
    _UCS_SDK_OBJECT_NAME = "computeSystemQual"

    def __init__(self, parent=None, json_content=None, compute_system_qual=None):
        UcsCentralConfigObject.__init__(self, parent=parent, ucs_sdk_object=compute_system_qual)
        self.descr = None
        self.ip_address_qualifiers = []
        self.name = None
        self.owner_qualifiers = []
        self.site_qualifiers = []

        if self._config.load_from == "live":
            if compute_system_qual is not None:
                self.name = compute_system_qual.name
                self.descr = compute_system_qual.descr

                if "computeOwnerQual" in self._parent._config.sdk_objects:
                    for compute_owner_qual in self._config.sdk_objects["computeOwnerQual"]:
                        if "org-root/system-qualifier-" + self.name + "/owner-" in compute_owner_qual.dn:
                            owner_qualifier = {}
                            owner_qualifier.update({"name": compute_owner_qual.name})
                            owner_qualifier.update({"owner_name": compute_owner_qual.regex})
                            self.owner_qualifiers.append(owner_qualifier)

                if "computeSiteQual" in self._parent._config.sdk_objects:
                    for compute_site_qual in self._config.sdk_objects["computeSiteQual"]:
                        if "org-root/system-qualifier-" + self.name + "/site-" in compute_site_qual.dn:
                            site_qualifier = {}
                            site_qualifier.update({"name": compute_site_qual.name})
                            site_qualifier.update({"site_name": compute_site_qual.regex})
                            self.site_qualifiers.append(site_qualifier)

                if "computeSystemAddrQual" in self._parent._config.sdk_objects:
                    for compute_system_addr_qual in self._config.sdk_objects["computeSystemAddrQual"]:
                        if "org-root/system-qualifier-" + self.name + "/ip-from-" in compute_system_addr_qual.dn:
                            ip_addr_qualifier = {}
                            ip_addr_qualifier.update({"from": compute_system_addr_qual.min_addr})
                            ip_addr_qualifier.update({"to": compute_system_addr_qual.max_addr})
                            self.ip_address_qualifiers.append(ip_addr_qualifier)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

                for element in self.owner_qualifiers:
                    for value in ["name", "owner_name"]:
                        if value not in element:
                            element[value] = None

                for element in self.site_qualifiers:
                    for value in ["name", "site_name"]:
                        if value not in element:
                            element[value] = None

                for element in self.ip_address_qualifiers:
                    for value in ["from", "to"]:
                        if value not in element:
                            element[value] = None

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + str(self.name))
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + str(self.name) +
                                ", waiting for a commit")

        mo_compute_system_qual = ComputeSystemQual(parent_mo_or_dn="org-root", descr=self.descr, name=self.name)

        if self.owner_qualifiers:
            for owner_qualifier in self.owner_qualifiers:
                ComputeOwnerQual(parent_mo_or_dn=mo_compute_system_qual, name=owner_qualifier["name"],
                                 regex=owner_qualifier["owner_name"])

        if self.site_qualifiers:
            for site_qualifier in self.site_qualifiers:
                ComputeSiteQual(parent_mo_or_dn=mo_compute_system_qual, name=site_qualifier["name"],
                                regex=site_qualifier["site_name"])

        if self.ip_address_qualifiers:
            for ip_addr_qualifier in self.ip_address_qualifiers:
                ComputeSystemAddrQual(parent_mo_or_dn=mo_compute_system_qual, min_addr=ip_addr_qualifier["from"],
                                      max_addr=ip_addr_qualifier["to"])

        self._handle.add_mo(mo=mo_compute_system_qual, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True


class UcsCentralOrg(UcsCentralConfigObject):
    _CONFIG_NAME = "Organization"
    _CONFIG_SECTION_NAME = "orgs"
    _CONFIG_SECTION_ATTRIBUTES_MAP = {
        "bios_policies": "BIOS Policies",
        "boot_policies": "Boot Policies",
        "chassis_firmware_packages": "Chassis Firmware Packages",
        "chassis_profiles": "Chassis Profiles",
        "compute_connection_policies": "Compute Connection Policies",
        "disk_group_policies": "Disk Group Policies",
        "disk_zoning_policies": "Disk Zoning Policies",
        "domain_group_qualification_policies": "Domain Group Qualification Policies",
        "dynamic_vnic_connection_policies": "Dynamic vNIC Connection Policies",
        "ethernet_adapter_policies": "Ethernet Adapter Policies",
        "fibre_channel_adapter_policies": "Fibre Channel Adapter Policies",
        "graphics_card_policies": "Graphics Card Policies",
        "host_firmware_packages": "Host Firmware Packages",
        "host_interface_placement_policies": "Host Interface Placement Policies",
        "id_range_access_control_policies": "ID Range Access Control Policies",
        "ip_pools": "IP Pools",
        "ipmi_access_profiles": "IPMI Access Profiles",
        "iqn_pools": "IQN Pools",
        "iscsi_adapter_policies": "iSCSI Adapter Policies",
        "iscsi_authentication_profiles": "iSCSI Authentication Profiles",
        "lan_connectivity_policies": "LAN Connectivity Policies",
        "local_disk_config_policies": "Local Disk Config Policies",
        "mac_pools": "MAC Pools",
        "maintenance_policies": "Maintenance Policies",
        "network_control_policies": "Network Control Policies",
        "orgs": "Organizations",
        "power_control_policies": "Power Control Policies",
        "power_sync_policies": "Power Sync Policies",
        "qos_policies": "QoS Policies",
        "san_connectivity_policies": "SAN Connectivity Policies",
        "scrub_policies": "Scrub Policies",
        "serial_over_lan_policies": "Serial Over LAN Policies",
        "server_pool_policy_qualifications": "Server Pool Policy Qualifications",
        "server_pools": "Server Pools",
        "service_profiles": "Service Profiles",
        "storage_connection_policies": "Storage Connection Policies",
        "storage_profiles": "Storage Profiles",
        "threshold_policies": "Threshold Policies",
        "usnic_connection_policies": "usNIC Connection Policies",
        "uuid_pools": "UUID Pools",
        "vhba_templates": "vHBA Templates",
        "vmedia_policies": "vMedia Policies",
        "vmq_connection_policies": "VMQ Connection Policies",
        "vnic_templates": "vNIC Templates",
        "wwnn_pools": "WWNN Pools",
        "wwpn_pools": "WWPN Pools",
        "wwxn_pools": "WWxN Pools"
    }
    _UCS_SDK_OBJECT_NAME = "orgOrg"

    def __init__(self, parent=None, json_content=None, org_org=None):
        UcsCentralConfigObject.__init__(self, parent=parent, ucs_sdk_object=org_org)
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
            self._get_generic_element(json_content=json_content, object_class=UcsCentralOrg, name_to_fetch="orgs")

        if self._dn == "org-root":
            # The following objects can only exist in the root org
            self.domain_group_qualification_policies = \
                self._get_generic_element(json_content=json_content,
                                          object_class=UcsCentralDomainGroupQualificationPolicy,
                                          name_to_fetch="domain_group_qualification_policies")
        else:
            self.domain_group_qualification_policies = None

        self.logger(level="debug", message="Building internal objects for policies of Org " + self.get_org_path())

        self.bios_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralBiosPolicy,
                                      name_to_fetch="bios_policies")
        self.boot_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralBootPolicy,
                                      name_to_fetch="boot_policies")
        self.chassis_firmware_packages = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralChassisFirmwarePackage,
                                      name_to_fetch="chassis_firmware_packages")
        self.chassis_profiles = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralChassisProfile,
                                      name_to_fetch="chassis_profiles")
        self.compute_connection_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralComputeConnectionPolicy,
                                      name_to_fetch="compute_connection_policies")
        self.disk_group_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralDiskGroupPolicy,
                                      name_to_fetch="disk_group_policies")
        self.disk_zoning_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralDiskZoningPolicy,
                                      name_to_fetch="disk_zoning_policies")
        self.dynamic_vnic_connection_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralDynamicVnicConnectionPolicy,
                                      name_to_fetch="dynamic_vnic_connection_policies")
        self.ethernet_adapter_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralEthernetAdapterPolicy,
                                      name_to_fetch="ethernet_adapter_policies")
        self.fibre_channel_adapter_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralFibreChannelAdapterPolicy,
                                      name_to_fetch="fibre_channel_adapter_policies")
        self.graphics_card_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralGraphicsCardPolicy,
                                      name_to_fetch="graphics_card_policies")
        self.host_firmware_packages = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralHostFirmwarePackage,
                                      name_to_fetch="host_firmware_packages")
        self.host_interface_placement_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralHostInterfacePlacementPolicy,
                                      name_to_fetch="host_interface_placement_policies")
        self.id_range_access_control_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralIdRangeAccessControlPolicy,
                                      name_to_fetch="id_range_access_control_policies")
        self.ip_pools = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralIpPool,
                                      name_to_fetch="ip_pools")
        self.ipmi_access_profiles = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralIpmiAccessProfile,
                                      name_to_fetch="ipmi_access_profiles")
        self.iqn_pools = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralIqnPool,
                                      name_to_fetch="iqn_pools")
        self.iscsi_adapter_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralIscsiAdapterPolicy,
                                      name_to_fetch="iscsi_adapter_policies")
        self.iscsi_authentication_profiles = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralIscsiAuthenticationProfile,
                                      name_to_fetch="iscsi_authentication_profiles")
        self.lan_connectivity_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralLanConnectivityPolicy,
                                      name_to_fetch="lan_connectivity_policies")
        self.local_disk_config_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralLocalDiskConfPolicy,
                                      name_to_fetch="local_disk_config_policies")
        self.mac_pools = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralMacPool,
                                      name_to_fetch="mac_pools")
        self.maintenance_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralMaintenancePolicy,
                                      name_to_fetch="maintenance_policies")
        self.network_control_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralNetworkControlPolicy,
                                      name_to_fetch="network_control_policies")
        self.power_control_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralPowerControlPolicy,
                                      name_to_fetch="power_control_policies")
        self.power_sync_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralPowerSyncPolicy,
                                      name_to_fetch="power_sync_policies")
        self.qos_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralQosPolicy,
                                      name_to_fetch="qos_policies")
        self.san_connectivity_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralSanConnectivityPolicy,
                                      name_to_fetch="san_connectivity_policies")
        self.scrub_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralScrubPolicy,
                                      name_to_fetch="scrub_policies")
        self.serial_over_lan_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralSerialOverLanPolicy,
                                      name_to_fetch="serial_over_lan_policies")
        self.server_pool_policy_qualifications = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralServerPoolPolicyQualifications,
                                      name_to_fetch="server_pool_policy_qualifications")
        self.server_pools = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralServerPool,
                                      name_to_fetch="server_pools")
        self.service_profiles = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralServiceProfile,
                                      name_to_fetch="service_profiles")
        self.storage_connection_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralStorageConnectionPolicy,
                                      name_to_fetch="storage_connection_policies")
        self.storage_profiles = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralStorageProfile,
                                      name_to_fetch="storage_profiles")
        self.threshold_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralThresholdPolicy,
                                      name_to_fetch="threshold_policies")
        self.usnic_connection_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralUsnicConnectionPolicy,
                                      name_to_fetch="usnic_connection_policies")
        self.uuid_pools = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralUuidPool,
                                      name_to_fetch="uuid_pools")
        self.vhba_templates = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralVhbaTemplate,
                                      name_to_fetch="vhba_templates")
        self.vmedia_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralVmediaPolicy,
                                      name_to_fetch="vmedia_policies")
        self.vmq_connection_policies = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralVmqConnectionPolicy,
                                      name_to_fetch="vmq_connection_policies")
        self.vnic_templates = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralVnicTemplate,
                                      name_to_fetch="vnic_templates")
        self.wwnn_pools = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralWwnnPool,
                                      name_to_fetch="wwnn_pools")
        self.wwpn_pools = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralWwpnPool,
                                      name_to_fetch="wwpn_pools")
        self.wwxn_pools = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralWwxnPool,
                                      name_to_fetch="wwxn_pools")

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
        objects_to_push_in_order = [
            'domain_group_qualification_policies', 'mac_pools', 'uuid_pools', 'wwnn_pools', 'wwpn_pools', 'wwxn_pools',
            'ip_pools', 'iqn_pools', 'server_pools', 'chassis_firmware_packages', 'serial_over_lan_policies',
            'disk_group_policies', 'disk_zoning_policies', 'dynamic_vnic_connection_policies',
            'ethernet_adapter_policies', 'fibre_channel_adapter_policies', 'graphics_card_policies',
            'host_firmware_packages', 'host_interface_placement_policies', 'id_range_access_control_policies',
            'ipmi_access_profiles', 'iscsi_adapter_policies', 'iscsi_authentication_profiles',
            'local_disk_config_policies', 'maintenance_policies', 'power_control_policies', 'power_sync_policies',
            'qos_policies', 'server_pool_policy_qualifications', 'threshold_policies', 'compute_connection_policies',
            'chassis_profiles', 'bios_policies', 'boot_policies', 'network_control_policies', 'scrub_policies',
            'storage_connection_policies', 'storage_profiles', 'usnic_connection_policies', 'vhba_templates',
            'vmedia_policies', 'vmq_connection_policies', 'vnic_templates', 'lan_connectivity_policies',
            'san_connectivity_policies', 'service_profiles', 'orgs']

        for config_object in objects_to_push_in_order:
            if getattr(self, config_object) is not None:
                if getattr(self, config_object).__class__.__name__ == "list":
                    for subobject in getattr(self, config_object):
                        subobject.push_object()

        # HANDLING OF Instantiate CHASSIS PROFILES
        # All Chassis Profile Templates are pushed in objects_to_push_in_order, pushing instantiate profiles as mentioned below.
        # so that instantiation can find the required Template from current or previous org.
        if self.chassis_profiles:
            for chassis_profile in self.chassis_profiles:
                if chassis_profile.type not in ["initial-template", "updating-template"]:
                    if all(getattr(chassis_profile, attr) for attr in ["chassis_profile_template", "name"]):
                        chassis_profile.instantiate_profile()

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

    def get_org_path(self):
        """
        Returns the "readable" org path of the current org based on its DN
        """
        return '/'.join([dn.replace("org-", "", 1) for dn in self._dn.split("/")])
