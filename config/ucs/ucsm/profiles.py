# coding: utf-8
# !/usr/bin/env python

""" profiles.py: Easy UCS Deployment Tool """

import urllib

from ucscsdk.mometa.vnic.VnicIPv4IscsiAddr import VnicIPv4IscsiAddr
from ucsmsdk.mometa.fabric.FabricNetGroupRef import FabricNetGroupRef
from ucsmsdk.mometa.fabric.FabricVCon import FabricVCon
from ucsmsdk.mometa.ls.LsBinding import LsBinding
from ucsmsdk.mometa.ls.LsPower import LsPower
from ucsmsdk.mometa.ls.LsRequirement import LsRequirement
from ucsmsdk.mometa.ls.LsServer import LsServer
from ucsmsdk.mometa.ls.LsServerExtension import LsServerExtension
from ucsmsdk.mometa.ls.LsVConAssign import LsVConAssign
from ucsmsdk.mometa.lstorage.LstorageProfileBinding import LstorageProfileBinding
from ucsmsdk.mometa.mgmt.MgmtInterface import MgmtInterface
from ucsmsdk.mometa.mgmt.MgmtVnet import MgmtVnet
from ucsmsdk.mometa.storage.StorageIniGroup import StorageIniGroup
from ucsmsdk.mometa.storage.StorageInitiator import StorageInitiator
from ucsmsdk.mometa.vnic.VnicConnDef import VnicConnDef
from ucsmsdk.mometa.vnic.VnicDynamicConPolicyRef import VnicDynamicConPolicyRef
from ucsmsdk.mometa.vnic.VnicEther import VnicEther
from ucsmsdk.mometa.vnic.VnicEtherIf import VnicEtherIf
from ucsmsdk.mometa.vnic.VnicFc import VnicFc
from ucsmsdk.mometa.vnic.VnicFcGroupDef import VnicFcGroupDef
from ucsmsdk.mometa.vnic.VnicFcIf import VnicFcIf
from ucsmsdk.mometa.vnic.VnicFcNode import VnicFcNode
from ucsmsdk.mometa.vnic.VnicIPv4Dhcp import VnicIPv4Dhcp
from ucsmsdk.mometa.vnic.VnicIPv4If import VnicIPv4If
from ucsmsdk.mometa.vnic.VnicIPv4PooledIscsiAddr import VnicIPv4PooledIscsiAddr
from ucsmsdk.mometa.vnic.VnicIScsi import VnicIScsi
from ucsmsdk.mometa.vnic.VnicIScsiAutoTargetIf import VnicIScsiAutoTargetIf
from ucsmsdk.mometa.vnic.VnicIScsiBootParams import VnicIScsiBootParams
from ucsmsdk.mometa.vnic.VnicIScsiBootVnic import VnicIScsiBootVnic
from ucsmsdk.mometa.vnic.VnicIScsiNode import VnicIScsiNode
from ucsmsdk.mometa.vnic.VnicIScsiStaticTargetIf import VnicIScsiStaticTargetIf
from ucsmsdk.mometa.vnic.VnicIpV4MgmtPooledAddr import VnicIpV4MgmtPooledAddr
from ucsmsdk.mometa.vnic.VnicIpV6MgmtPooledAddr import VnicIpV6MgmtPooledAddr
from ucsmsdk.mometa.vnic.VnicLun import VnicLun
from ucsmsdk.mometa.vnic.VnicSriovHpnConPolicyRef import VnicSriovHpnConPolicyRef
from ucsmsdk.mometa.vnic.VnicUsnicConPolicyRef import VnicUsnicConPolicyRef
from ucsmsdk.mometa.vnic.VnicVlan import VnicVlan
from ucsmsdk.mometa.vnic.VnicVmqConPolicyRef import VnicVmqConPolicyRef
from ucsmsdk.ucsbasetype import DnSet, Dn
from ucsmsdk.ucsexception import UcsException
from ucsmsdk.ucsmethodfactory import ls_instantiate_n_named_template, ls_instantiate_template

from config.ucs.object import UcsSystemConfigObject
from config.ucs.ucsm.lan import UcsSystemDynamicVnicConnectionPolicy, UcsSystemIpPool, UcsSystemLanConnectivityPolicy, \
    UcsSystemLanPinGroup, UcsSystemMacPool, UcsSystemNetworkControlPolicy, UcsSystemQosPolicy, \
    UcsSystemSriovHpnConnectionPolicy, UcsSystemUsnicConnectionPolicy, UcsSystemVmqConnectionPolicy, \
    UcsSystemVnicTemplate
from config.ucs.ucsm.san import UcsSystemIqnPool, UcsSystemSanConnectivityPolicy, UcsSystemStorageConnectionPolicy, \
    UcsSystemWwnnPool, UcsSystemSanPinGroup, UcsSystemVhbaTemplate, UcsSystemWwpnPool
from config.ucs.ucsm.servers import UcsSystemBiosPolicy, UcsSystemBootPolicy, UcsSystemGraphicsCardPolicy, \
    UcsSystemHostFirmwarePackage, UcsSystemIpmiAccessProfile, UcsSystemIscsiAdapterPolicy, \
    UcsSystemIscsiAuthenticationProfile, UcsSystemKvmManagementPolicy, UcsSystemLocalDiskConfPolicy, \
    UcsSystemMaintenancePolicy, UcsSystemPersistentMemoryPolicy, UcsSystemVnicVhbaPlacementPolicy, \
    UcsSystemPowerControlPolicy, UcsSystemPowerSyncPolicy, UcsSystemScrubPolicy, \
    UcsSystemSerialOverLanPolicy, UcsSystemServerPool, UcsSystemSpdmCertificatePolicy, UcsSystemThresholdPolicy, \
    UcsSystemUuidPool, UcsSystemVmediaPolicy, UcsSystemEthernetAdapterPolicy, UcsSystemFibreChannelAdapterPolicy
from config.ucs.ucsm.storage import UcsSystemStorageProfile


class UcsSystemServiceProfile(UcsSystemConfigObject):
    _CONFIG_NAME = "Service Profile"
    _CONFIG_SECTION_NAME = "service_profiles"
    _UCS_SDK_OBJECT_NAME = "lsServer"
    _POLICY_MAPPING_TABLE = {
        "bios_policy": UcsSystemBiosPolicy,
        "boot_policy": UcsSystemBootPolicy,
        "dynamic_vnic_connection_policy": UcsSystemDynamicVnicConnectionPolicy,
        "graphics_card_policy": UcsSystemGraphicsCardPolicy,
        "host_firmware_package": UcsSystemHostFirmwarePackage,
        "inband_ipv4_pool": UcsSystemIpPool,
        "inband_ipv6_pool": UcsSystemIpPool,
        "ipmi_access_profile": UcsSystemIpmiAccessProfile,
        "iscsi_boot_parameters": [
            {
                "initiator_ip_address_policy": UcsSystemIpPool,
                "iqn_pool": UcsSystemIqnPool
            }
        ],
        "iscsi_iqn_pool_name": UcsSystemIqnPool,
        "iscsi_vnics": [
            {
                "iscsi_adapter_policy": UcsSystemIscsiAdapterPolicy,
                "authentication_profile": UcsSystemIscsiAuthenticationProfile
            }
        ],
        "kvm_management_policy": UcsSystemKvmManagementPolicy,
        "lan_connectivity_policy": UcsSystemLanConnectivityPolicy,
        "local_disk_configuration_policy": UcsSystemLocalDiskConfPolicy,
        "maintenance_policy": UcsSystemMaintenancePolicy,
        "outband_ipv4_pool": UcsSystemIpPool,
        "persistent_memory_policy": UcsSystemPersistentMemoryPolicy,
        "placement_policy": UcsSystemVnicVhbaPlacementPolicy,
        "power_control_policy": UcsSystemPowerControlPolicy,
        "power_sync_policy": UcsSystemPowerSyncPolicy,
        "san_connectivity_policy": UcsSystemSanConnectivityPolicy,
        "scrub_policy": UcsSystemScrubPolicy,
        "serial_over_lan_policy": UcsSystemSerialOverLanPolicy,
        "server_pool": UcsSystemServerPool,
        "spdm_certificate_policy": UcsSystemSpdmCertificatePolicy,
        "storage_profile": UcsSystemStorageProfile,
        "threshold_policy": UcsSystemThresholdPolicy,
        "uuid_pool": UcsSystemUuidPool,
        "vmedia_policy": UcsSystemVmediaPolicy,
        "wwnn_pool": UcsSystemWwnnPool,
        "vnics": [
            {
                "adapter_policy": UcsSystemEthernetAdapterPolicy,
                "mac_address_pool": UcsSystemMacPool,
                "network_control_policy": UcsSystemNetworkControlPolicy,
                "pin_group": UcsSystemLanPinGroup,
                "qos_policy": UcsSystemQosPolicy,
                "sriov_hpn_connection_policy": UcsSystemSriovHpnConnectionPolicy,
                "stats_threshold_policy": UcsSystemThresholdPolicy,
                "usnic_connection_policy": UcsSystemUsnicConnectionPolicy,
                "vmq_connection_policy": UcsSystemVmqConnectionPolicy,
                "vnic_template": UcsSystemVnicTemplate
            }
        ],
        "vhbas": [
            {
                "adapter_policy": UcsSystemFibreChannelAdapterPolicy,
                "pin_group": UcsSystemSanPinGroup,
                "qos_policy": UcsSystemQosPolicy,
                "stats_threshold_policy": UcsSystemThresholdPolicy,
                "vhba_template": UcsSystemVhbaTemplate,
                "wwpn_pool": UcsSystemWwpnPool
            }
        ],
        "vhba_initiator_groups": [
            {
                "storage_connection_policy": UcsSystemStorageConnectionPolicy
            }
        ]
    }

    def __init__(self, parent=None, json_content=None, ls_server=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=ls_server)

        self.service_profile_template = None
        self.suffix_start_number = None
        self.number_of_instances = None
        # Identify Service Profile
        self.descr = None
        self.name = None
        self.type = None
        self.user_label = None
        self.asset_tag = None
        self.uuid_pool = None
        self.uuid = None
        # Storage Provisioning
        self.storage_profile = None
        self.specific_storage_profile = None
        self.local_disk_configuration_policy = None
        self.specific_local_disk_configuration_policy = None
        # Networking
        self.dynamic_vnic_connection_policy = None
        self.specific_dynamic_vnic_connection_policy = None
        self.lan_connectivity_policy = None
        self.vnics = []
        self.iscsi_vnics = []
        self.iscsi_initiator_name = None
        self.iscsi_iqn_pool_name = None
        # SAN Connectivity
        self.san_connectivity_policy = None
        self.wwnn_pool = None
        self.wwnn = None
        self.vhbas = []
        # Zoning
        self.vhba_initiator_groups = []
        # vNIC/vHBA Placement
        self.placement_policy = None
        self.placement = []
        self.specific_placement = []
        # vMedia Policy
        self.vmedia_policy = None
        self.specific_vmedia_policy = None
        # Server Boot Order
        self.boot_policy = None
        self.specific_boot_policy = None
        self.iscsi_boot_parameters = []
        # Maintenance Policy
        self.maintenance_policy = None
        # Server Assignment
        self.servers = []
        self.server_pool = None
        self.server_power_state = None
        self.server_pool_qualification = None
        self.restrict_migration = None
        self.host_firmware_package = None
        # Optional Policies
        self.bios_policy = None
        self.ipmi_access_profile = None
        self.serial_over_lan_policy = None
        self.specific_serial_over_lan_policy = None
        self.outband_ipv4_pool = None
        self.outband_ipv4 = None
        self.inband_network = None
        self.inband_ipv6_pool = None
        self.inband_ipv6 = None
        self.inband_ipv4_pool = None
        self.inband_ipv4 = None
        self.threshold_policy = None
        self.power_control_policy = None
        self.scrub_policy = None
        self.kvm_management_policy = None
        self.spdm_certificate_policy = None
        self.graphics_card_policy = None
        self.power_sync_policy = None
        self.persistent_memory_policy = None
        # Operational State
        self.operational_state = {}
        oper_inband_ipv4_pool = None
        oper_inband_ipv6_pool = None
        oper_lan_connectivity_policy = None
        oper_san_connectivity_policy = None
        oper_server_pool = None
        oper_storage_profile = None
        oper_wwnn_pool = None

        if self._config.load_from == "live":
            if ls_server is not None:
                self._dn = ls_server.dn
                self.name = ls_server.name
                self.descr = ls_server.descr
                self.type = ls_server.type
                self.user_label = ls_server.usr_lbl
                self.service_profile_template = ls_server.src_templ_name

                if "template" in self.type:
                    self._CONFIG_NAME = "Service Profile Template"
                if self.policy_owner == "ucs-central":
                    self._CONFIG_NAME = "Global " + self._CONFIG_NAME

                if "lsServerExtension" in self._parent._config.sdk_objects:
                    for ext in self._config.sdk_objects["lsServerExtension"]:
                        if self._parent._dn:
                            if self._parent._dn + "/ls-" + self.name + "/" in ext.dn:
                                self.asset_tag = ext.asset_tag

                parent_template_type = None
                if self.service_profile_template:
                    # We first try to get the SP Template object by using the operSrcTemplName attribute value
                    if ls_server.oper_src_templ_name:
                        mo_template_ls_list = [ls for ls in self._config.sdk_objects["lsServer"] if
                                               ls.dn == ls_server.oper_src_templ_name]
                        if len(mo_template_ls_list) == 1:
                            parent_template_type = mo_template_ls_list[0].type
                    else:
                        # If the operSrcTemplName attribute is not set (e.g. with UCS Central), we try to find the SP
                        # Template using a query for its name. In case it is the only object with this name, we use it
                        mo_template_ls_list = [ls for ls in self._config.sdk_objects["lsServer"] if
                                               ls.name == self.service_profile_template]
                        if len(mo_template_ls_list) == 1:
                            parent_template_type = mo_template_ls_list[0].type

                    if self.policy_owner in ["ucs-central"]:
                        # if the source template name is a Global SP Template from UCS Central
                        self.service_profile_template = "ucs-central/" + self.service_profile_template

                self.dynamic_vnic_connection_policy = ls_server.dynamic_con_policy_name
                self.bios_policy = ls_server.bios_profile_name
                self.host_firmware_package = ls_server.host_fw_policy_name
                self.local_disk_configuration_policy = ls_server.local_disk_policy_name
                self.maintenance_policy = ls_server.maint_policy_name
                self.scrub_policy = ls_server.scrub_policy_name
                self.uuid_pool = ls_server.ident_pool_name
                self.uuid = ls_server.uuid
                if not self.uuid_pool and self.uuid == "derived":
                    self.uuid = "hardware-default"

                self.vmedia_policy = ls_server.vmedia_policy_name
                self.boot_policy = ls_server.boot_policy_name
                self.power_sync_policy = ls_server.power_sync_policy_name
                self.power_control_policy = ls_server.power_policy_name
                self.serial_over_lan_policy = ls_server.sol_policy_name
                self.ipmi_access_profile = ls_server.mgmt_access_policy_name
                self.placement_policy = ls_server.vcon_profile_name
                self.threshold_policy = ls_server.stats_policy_name
                self.kvm_management_policy = ls_server.kvm_mgmt_policy_name
                self.spdm_certificate_policy = ls_server.spdm_certificate_policy_name
                self.graphics_card_policy = ls_server.graphics_card_policy_name
                self.persistent_memory_policy = ls_server.persistent_memory_policy_name
                if ls_server.ext_ip_state == "pooled":
                    # We only fetch the Outband IPv4 Pool if it is configured explicitely. Other options ("none"
                    # or "static") correspond respectively to using the default ext-mgmt pool and using a statically
                    # assigned IP address to the CIMC
                    self.outband_ipv4_pool = ls_server.ext_ip_pool_name
                    if "vnicIpV4PooledAddr" in self._parent._config.sdk_objects:
                        for pool in self._config.sdk_objects["vnicIpV4PooledAddr"]:
                            if self._parent._dn:
                                if self._parent._dn + "/ls-" + self.name + "/" + "ipv4-pooled-addr" in pool.dn:
                                    self.outband_ipv4 = pool.addr
                                    break

                elif ls_server.ext_ip_state == "static":
                    self.outband_ipv4_pool = None
                    if "vnicIpV4StaticAddr" in self._parent._config.sdk_objects:
                        for pool in self._config.sdk_objects["vnicIpV4StaticAddr"]:
                            if self._parent._dn:
                                if self._parent._dn + "/ls-" + self.name + "/" + "ipv4-static-addr" in pool.dn:
                                    self.outband_ipv4 = pool.addr
                                    break

                if "cimcvmediaMountConfigDef" in self._parent._config.sdk_objects:
                    for specific_vmedia in self._config.sdk_objects["cimcvmediaMountConfigDef"]:
                        if self._parent._dn:
                            if self._parent._dn + "/ls-" + self.name + "/" in specific_vmedia.dn:
                                self.specific_vmedia_policy = UcsSystemVmediaPolicy(
                                    parent=self, cimcvmedia_mount_config_policy=specific_vmedia
                                )

                if "lsbootDef" in self._parent._config.sdk_objects:
                    for specific_boot in self._config.sdk_objects["lsbootDef"]:
                        if self._parent._dn:
                            if self._parent._dn + "/ls-" + self.name + "/" in specific_boot.dn:
                                self.specific_boot_policy = UcsSystemBootPolicy(
                                    parent=self, lsboot_policy=specific_boot
                                )

                if "lstorageProfileDef" in self._parent._config.sdk_objects:
                    for specific_storage_profile in self._config.sdk_objects["lstorageProfileDef"]:
                        if self._parent._dn:
                            if self._parent._dn + "/ls-" + self.name + "/" in specific_storage_profile.dn:
                                self.specific_storage_profile = UcsSystemStorageProfile(
                                    parent=self, lstorage_profile=specific_storage_profile
                                )

                if "solConfig" in self._parent._config.sdk_objects:
                    for specific_sol in self._config.sdk_objects["solConfig"]:
                        if self._parent._dn:
                            if self._parent._dn + "/ls-" + self.name + "/" in specific_sol.dn:
                                self.specific_serial_over_lan_policy = UcsSystemSerialOverLanPolicy(
                                    parent=self, sol_policy=specific_sol
                                )
                                # Since we are using a Specific SoL Policy, we are removing the mapping to the
                                # "default" SoL Policy that is always there in UCSM
                                self.serial_over_lan_policy = None

                if "storageLocalDiskConfigDef" in self._parent._config.sdk_objects:
                    for specific_local_disk_config_pol in self._config.sdk_objects["storageLocalDiskConfigDef"]:
                        if self._parent._dn:
                            if self._parent._dn + "/ls-" + self.name + "/" in specific_local_disk_config_pol.dn:
                                self.specific_local_disk_configuration_policy = UcsSystemLocalDiskConfPolicy(
                                    parent=self, storage_local_disk_config_policy=specific_local_disk_config_pol
                                )

                                # In some specific cases, the Service Profile can have both a Local Disk Config Policy
                                # and a Specific Local Disk Config Policy applied to it. We only keep the specific as
                                # that is what the UCSM GUI shows in such a scenario (EASYUCS-1046)
                                if self.local_disk_configuration_policy:
                                    self.logger(
                                        level="warning",
                                        message=f"Ignoring Local Disk Configuration Policy " +
                                                f"'{self.local_disk_configuration_policy}' due to Specific Local " +
                                                f"Disk Configuration Policy being configured for {self._CONFIG_NAME} " +
                                                f"'{self.name}'"
                                    )
                                    self.local_disk_configuration_policy = None

                if "vnicDynamicCon" in self._parent._config.sdk_objects:
                    for specific_dyn_vnic_conn_pol in self._config.sdk_objects["vnicDynamicCon"]:
                        if self._parent._dn:
                            if self._parent._dn + "/ls-" + self.name + "/" in specific_dyn_vnic_conn_pol.dn:
                                self.specific_dynamic_vnic_connection_policy = UcsSystemDynamicVnicConnectionPolicy(
                                    parent=self, vnic_dynamic_con_policy=specific_dyn_vnic_conn_pol
                                )

                if "vnicFcNode" in self._parent._config.sdk_objects:
                    for pool in self._config.sdk_objects["vnicFcNode"]:
                        if self._parent._dn:
                            if self._parent._dn + "/ls-" + self.name + "/" in pool.dn:
                                self.wwnn_pool = pool.ident_pool_name
                                self.wwnn = pool.addr

                                oper_wwnn_pool = self.get_operational_state(
                                    policy_dn=pool.oper_ident_pool_name,
                                    separator="/wwn-pool-",
                                    policy_name="wwnn_pool"
                                )
                                break

                if "lsRequirement" in self._parent._config.sdk_objects:
                    for pool in self._config.sdk_objects["lsRequirement"]:
                        if self._parent._dn:
                            if self._parent._dn + "/ls-" + self.name + "/" in pool.dn:
                                self.server_pool = pool.name
                                self.server_pool_qualification = pool.qualifier
                                self.restrict_migration = pool.restrict_migration

                                oper_server_pool = self.get_operational_state(
                                    policy_dn=pool.oper_name,
                                    separator="/compute-pool-",
                                    policy_name="server_pool"
                                )

                if "lstorageProfileBinding" in self._parent._config.sdk_objects:
                    for profile in self._config.sdk_objects["lstorageProfileBinding"]:
                        if self._parent._dn:
                            if self._parent._dn + "/ls-" + self.name + "/" in profile.dn:
                                self.storage_profile = profile.storage_profile_name

                                oper_storage_profile = self.get_operational_state(
                                    policy_dn=profile.oper_storage_profile_name,
                                    separator="/profile-",
                                    policy_name="storage_profile"
                                )

                if "mgmtVnet" in self._parent._config.sdk_objects:
                    for vnet in self._config.sdk_objects["mgmtVnet"]:
                        if self._parent._dn:
                            if self._parent._dn + "/ls-" + self.name + "/" in vnet.dn:
                                self.inband_network = vnet.name

                if ls_server.ext_ip_state == "pooled":
                    if "vnicIpV4MgmtPooledAddr" in self._parent._config.sdk_objects:
                        for pool in self._config.sdk_objects["vnicIpV4MgmtPooledAddr"]:
                            if self._parent._dn:
                                if self._parent._dn + "/ls-" + self.name + "/" in pool.dn:
                                    self.inband_ipv4_pool = pool.name
                                    if pool.addr not in ["", "0.0.0.0"]:
                                        self.inband_ipv4 = pool.addr

                                    oper_inband_ipv4_pool = self.get_operational_state(
                                        policy_dn=pool.oper_name,
                                        separator="/ip-pool-",
                                        policy_name="inband_ipv4_pool"
                                    )
                                    break

                elif ls_server.ext_ip_state == "static":
                    if "vnicIpV4StaticAddr" in self._parent._config.sdk_objects:
                        for pool in self._config.sdk_objects["vnicIpV4StaticAddr"]:
                            if self._parent._dn:
                                if self._parent._dn + "/ls-" + self.name + "/" + "iface-in-band/" in pool.dn:
                                    self.inband_ipv4_pool = None
                                    if pool.addr not in ["", "0.0.0.0"]:
                                        self.inband_ipv4 = pool.addr
                                        break

                if ls_server.ext_ip_state == "pooled":
                    if "vnicIpV6MgmtPooledAddr" in self._parent._config.sdk_objects:
                        for pool in self._config.sdk_objects["vnicIpV6MgmtPooledAddr"]:
                            if self._parent._dn:
                                if self._parent._dn + "/ls-" + self.name + "/" in pool.dn:
                                    self.inband_ipv6_pool = pool.name
                                    if pool.addr not in ["", "::"]:
                                        self.inband_ipv6 = pool.addr

                                    oper_inband_ipv6_pool = self.get_operational_state(
                                        policy_dn=pool.oper_name,
                                        separator="/ip-pool-",
                                        policy_name="inband_ipv6_pool"
                                    )
                                    break

                elif ls_server.ext_ip_state == "static":
                    if "vnicIpV6StaticAddr" in self._parent._config.sdk_objects:
                        for pool in self._config.sdk_objects["vnicIpV6StaticAddr"]:
                            if self._parent._dn:
                                if self._parent._dn + "/ls-" + self.name + "/" + "iface-in-band/" in pool.dn:
                                    self.inband_ipv6_pool = None
                                    if pool.addr not in ["", "::"]:
                                        self.inband_ipv6 = pool.addr
                                        break

                if "vnicConnDef" in self._parent._config.sdk_objects:
                    for profile in self._config.sdk_objects["vnicConnDef"]:
                        if self._parent._dn:
                            if self._parent._dn + "/ls-" + self.name + "/" in profile.dn:
                                self.san_connectivity_policy = profile.san_conn_policy_name
                                self.lan_connectivity_policy = profile.lan_conn_policy_name
                                oper_lan_connectivity_policy = self.get_operational_state(
                                    policy_dn=profile.oper_lan_conn_policy_name,
                                    separator="/lan-conn-pol-",
                                    policy_name="lan_connectivity_policy"
                                )
                                oper_san_connectivity_policy = self.get_operational_state(
                                    policy_dn=profile.oper_san_conn_policy_name,
                                    separator="/san-conn-pol-",
                                    policy_name="san_connectivity_policy"
                                )

                if "lsBinding" in self._parent._config.sdk_objects:
                    for ls_binding in self._config.sdk_objects["lsBinding"]:
                        if self._parent._dn:
                            if self._parent._dn + "/ls-" + self.name + "/" in ls_binding.dn:
                                server = {}
                                if "chassis" in ls_binding.pn_dn and "blade" in ls_binding.pn_dn:
                                    server.update({"chassis_id": ls_binding.pn_dn.split("/")[1].split("-")[1]})
                                    server.update({"blade": ls_binding.pn_dn.split("/")[2].split("-")[1]})
                                    self.servers.append(server)
                                elif "rack-unit" in ls_binding.pn_dn:
                                    server.update({"rack_id": ls_binding.pn_dn.split("/")[1].split("-")[2]})
                                    self.servers.append(server)

                if "lsPower" in self._parent._config.sdk_objects:
                    for policy in self._config.sdk_objects["lsPower"]:
                        if self._parent._dn:
                            if self._parent._dn + "/ls-" + self.name + "/" in policy.dn:
                                self.server_power_state = policy.state

                if "vnicIScsiNode" in self._parent._config.sdk_objects:
                    for policy in self._config.sdk_objects["vnicIScsiNode"]:
                        if self._parent._dn:
                            if self._parent._dn + "/ls-" + self.name + "/" in policy.dn:
                                self.iscsi_initiator_name = policy.initiator_name
                                self.iscsi_iqn_pool_name = policy.iqn_ident_pool_name

                # We first construct sub-lists of interfaces that belong to this Service Profile
                # to reduce the number of objects we need to loop through
                vnic_ether_list = []
                if "vnicEther" in self._parent._config.sdk_objects and self._parent._dn:
                    vnic_ether_list = [vnic for vnic in self._config.sdk_objects["vnicEther"] if
                                       self._parent._dn + "/ls-" + self.name + "/" in vnic.dn]
                vnic_fc_list = []
                if "vnicFc" in self._parent._config.sdk_objects and self._parent._dn:
                    vnic_fc_list = [vhba for vhba in self._config.sdk_objects["vnicFc"] if
                                    self._parent._dn + "/ls-" + self.name + "/" in vhba.dn]

                if self.type in ["initial-template", "updating-template"] and not self.lan_connectivity_policy \
                        or self.type in ["instance"]:
                    # We only fetch vNICs when LAN Connectivity Policy is not set for a Service Profile Template
                    # For a Service Profile Instance, we always fetch vNICs details to gather assigned identifiers

                    # We first construct a sub-list of the vnicEtherIf objects that belong to this Service Profile
                    # to reduce the number of objects we need to loop through
                    vnic_ether_if_list = []
                    if "vnicEtherIf" in self._config.sdk_objects and self._parent._dn:
                        vnic_ether_if_list = [vlan for vlan in self._config.sdk_objects["vnicEtherIf"]
                                              if self._parent._dn + "/ls-" + self.name + "/" in vlan.dn]

                    if "vnicEther" in self._parent._config.sdk_objects:
                        for vnic_ether in vnic_ether_list:
                            if self._parent._dn:
                                if self._parent._dn + "/ls-" + self.name + "/" in vnic_ether.dn:
                                    vnic = {"_object_type": "vnics"}
                                    vnic.update({"name": vnic_ether.name})
                                    oper_state = {}
                                    if vnic_ether.addr != "derived":
                                        vnic.update({"mac_address": vnic_ether.addr})
                                    elif not vnic_ether.ident_pool_name and vnic_ether.addr == "derived":
                                        vnic.update({"mac_address": "hardware-default"})
                                    vnic.update({"mac_address_pool": vnic_ether.ident_pool_name})
                                    vnic.update({"order": vnic_ether.order})
                                    if vnic["order"] == "unspecified":
                                        vnic["order"] = None
                                    vnic.update({"fabric": vnic_ether.switch_id})
                                    vnic.update({"q_in_q": vnic_ether.q_in_q})
                                    vnic.update({"pin_group": vnic_ether.pin_to_group_name})
                                    vnic.update({"cdn_source": vnic_ether.cdn_source})
                                    vnic.update({"cdn_name": vnic_ether.admin_cdn_name})
                                    vnic.update({"adapter_policy": vnic_ether.adaptor_profile_name})
                                    vnic.update({"qos_policy": vnic_ether.qos_policy_name})
                                    vnic.update({"network_control_policy": vnic_ether.nw_ctrl_policy_name})
                                    vnic.update({"mtu": vnic_ether.mtu})
                                    vnic.update({"vnic_template": vnic_ether.nw_templ_name})
                                    vnic.update({"redundancy_pair": vnic_ether.redundancy_pair_type})
                                    vnic.update({"stats_threshold_policy": vnic_ether.stats_policy_name})

                                    if "vnicDynamicConPolicyRef" in self._parent._config.sdk_objects:
                                        for vnic_policy in self._config.sdk_objects["vnicDynamicConPolicyRef"]:
                                            if self._parent._dn + "/ls-" + self.name + "/" + "ether-" + \
                                                    vnic['name'] + "/" in vnic_policy.dn:
                                                vnic.update({"dynamic_vnic": vnic_policy.con_policy_name})
                                                oper_state.update(
                                                    self.get_operational_state(
                                                        policy_dn=vnic_policy.oper_con_policy_name,
                                                        separator="/dynamic-con-",
                                                        policy_name="dynamic_vnic"
                                                    )
                                                )
                                    if "vnicUsnicConPolicyRef" in self._parent._config.sdk_objects:
                                        for vnic_policy in self._config.sdk_objects["vnicUsnicConPolicyRef"]:
                                            if self._parent._dn + "/ls-" + self.name + "/" + "ether-" + \
                                                    vnic['name'] + "/" in vnic_policy.dn:
                                                vnic.update(
                                                    {"usnic_connection_policy": vnic_policy.con_policy_name})
                                                oper_state.update(
                                                    self.get_operational_state(
                                                        policy_dn=vnic_policy.oper_con_policy_name,
                                                        separator="/usnic-con-",
                                                        policy_name="usnic_connection_policy"
                                                    )
                                                )
                                    if "vnicVmqConPolicyRef" in self._parent._config.sdk_objects:
                                        for vnic_policy in self._config.sdk_objects["vnicVmqConPolicyRef"]:
                                            if self._parent._dn + "/ls-" + self.name + "/" + "ether-" + \
                                                    vnic['name'] + "/" in vnic_policy.dn:
                                                vnic.update({"vmq_connection_policy": vnic_policy.con_policy_name})
                                                oper_state.update(
                                                    self.get_operational_state(
                                                        policy_dn=vnic_policy.oper_con_policy_name,
                                                        separator="/vmq-con-",
                                                        policy_name="vmq_connection_policy"
                                                    )
                                                )
                                    if "vnicSriovHpnConPolicyRef" in self._parent._config.sdk_objects:
                                        for vnic_policy in self._config.sdk_objects["vnicSriovHpnConPolicyRef"]:
                                            if self._parent._dn + "/ls-" + self.name + "/" + "ether-" + \
                                                    vnic['name'] + "/" in vnic_policy.dn:
                                                vnic.update(
                                                    {"sriov_hpn_connection_policy": vnic_policy.con_policy_name})
                                                oper_state.update(
                                                    self.get_operational_state(
                                                        policy_dn=vnic_policy.oper_con_policy_name,
                                                        separator="/sriov-hpn-con-",
                                                        policy_name="sriov_hpn_connection_policy"
                                                    )
                                                )
                                    if "vnicEtherIf" in self._config.sdk_objects:
                                        vnic.update({"vlans": []})
                                        for vlan in vnic_ether_if_list:
                                            if self._parent._dn + "/ls-" + self.name + "/" + "ether-" + \
                                                    vnic['name'] + "/" in vlan.dn:
                                                if vlan.default_net in ["yes", "true"]:
                                                    vnic.update({"vlan_native": vlan.name})
                                                else:
                                                    vnic['vlans'].append(vlan.name)
                                                if vlan.is_qin_q_vlan in ["yes", "true"]:
                                                    vnic.update({"vlan_q_in_q": vlan.name})

                                    if "fabricNetGroupRef" in self._parent._config.sdk_objects:
                                        vnic.update({"vlan_groups": []})
                                        for vlan_group in self._config.sdk_objects["fabricNetGroupRef"]:
                                            if self._parent._dn + "/ls-" + self.name + "/" + "ether-" + \
                                                    vnic['name'] + "/" in vlan_group.dn:
                                                vnic['vlan_groups'].append(vlan_group.name)

                                    # Fetching the operational state of the referenced policies
                                    oper_state.update(
                                        self.get_operational_state(
                                            policy_dn=vnic_ether.oper_adaptor_profile_name,
                                            separator="/eth-profile-",
                                            policy_name="adapter_policy"
                                        )
                                    )
                                    oper_state.update(
                                        self.get_operational_state(
                                            policy_dn=vnic_ether.oper_ident_pool_name,
                                            separator="/mac-pool-",
                                            policy_name="mac_address_pool"
                                        )
                                    )
                                    oper_state.update(
                                        self.get_operational_state(
                                            policy_dn=vnic_ether.oper_nw_ctrl_policy_name,
                                            separator="/nwctrl-",
                                            policy_name="network_control_policy"
                                        )
                                    )
                                    oper_state.update(
                                        self.get_operational_state(
                                            policy_dn=vnic_ether.oper_pin_to_group_name,
                                            separator="/lan-pin-group-",
                                            policy_name="pin_group"
                                        )
                                    )
                                    oper_state.update(
                                        self.get_operational_state(
                                            policy_dn=vnic_ether.oper_qos_policy_name,
                                            separator="/ep-qos-",
                                            policy_name="qos_policy"
                                        )
                                    )
                                    oper_state.update(
                                        self.get_operational_state(
                                            policy_dn=vnic_ether.oper_stats_policy_name,
                                            separator="/thr-policy-",
                                            policy_name="stats_threshold_policy"
                                        )
                                    )
                                    oper_state.update(
                                        self.get_operational_state(
                                            policy_dn=vnic_ether.oper_nw_templ_name,
                                            separator="/lan-conn-templ-",
                                            policy_name="vnic_template"
                                        )
                                    )
                                    if vnic_ether.oper_host_port in ["ANY"]:
                                        oper_state.update({"host_port": "any"})
                                    elif vnic_ether.oper_host_port not in ["", "NONE"]:
                                        oper_state.update({"host_port": vnic_ether.oper_host_port})
                                    else:
                                        oper_state.update({"host_port": None})

                                    if vnic_ether.oper_vcon not in ["any"]:
                                        oper_state.update({"vcon": vnic_ether.oper_vcon})
                                    else:
                                        oper_state.update({"vcon": None})

                                    if vnic_ether.oper_order not in ["", "unspecified"]:
                                        oper_state.update({"order": vnic_ether.oper_order})
                                    else:
                                        oper_state.update({"order": None})

                                    vnic['operational_state'] = oper_state

                                    self.vnics.append(vnic)

                if "vnicIScsi" in self._parent._config.sdk_objects:
                    for vnic_iscsi in self._config.sdk_objects["vnicIScsi"]:
                        if self._parent._dn:
                            if self._parent._dn + "/ls-" + self.name + "/" in vnic_iscsi.dn:
                                vnic = {}
                                vnic.update({"name": vnic_iscsi.name})
                                vnic.update({"iscsi_adapter_policy": vnic_iscsi.adaptor_profile_name})
                                vnic.update({"overlay_vnic": vnic_iscsi.vnic_name})
                                vnic.update({"authentication_profile": vnic_iscsi.auth_profile_name})

                                if vnic_iscsi.addr != "derived":
                                    vnic.update({"mac_address": vnic_iscsi.addr})
                                elif not vnic_iscsi.ident_pool_name and vnic_iscsi.addr == "derived":
                                    vnic.update({"mac_address": "hardware-default"})
                                vnic.update({"mac_address_pool": vnic_iscsi.ident_pool_name})
                                if "vnicVlan" in self._parent._config.sdk_objects:
                                    for vlan in self._config.sdk_objects["vnicVlan"]:
                                        if vnic_iscsi.dn in vlan.dn:
                                            vnic.update({"vlan": vlan.vlan_name})
                                # Fetching the operational state of the referenced policies
                                oper_state = {}
                                oper_state.update(
                                    self.get_operational_state(
                                        policy_dn=vnic_iscsi.oper_auth_profile_name,
                                        separator="/iscsi-auth-profile-",
                                        policy_name="authentication_profile"
                                    )
                                )
                                oper_state.update(
                                    self.get_operational_state(
                                        policy_dn=vnic_iscsi.oper_adaptor_profile_name,
                                        separator="/iscsi-profile-",
                                        policy_name="iscsi_adapter_policy"
                                    )
                                )
                                vnic["operational_state"] = oper_state
                                self.iscsi_vnics.append(vnic)

                if self.type in ["initial-template", "updating-template"] and not self.san_connectivity_policy \
                        or self.type in ["instance"]:
                    # We only fetch vHBAs when SAN Connectivity Policy is not set for a Service Profile Template
                    # For a Service Profile Instance, we fetch vHBAs details to gather assigned identifiers

                    # We first construct a sub-list of the vnicFcIf objects that belong to this Service Profile
                    # to reduce the number of objects we need to loop through
                    vnic_fc_if_list = []
                    if "vnicFcIf" in self._config.sdk_objects and self._parent._dn:
                        vnic_fc_if_list = [vsan for vsan in self._config.sdk_objects["vnicFcIf"]
                                           if self._parent._dn + "/ls-" + self.name + "/" in vsan.dn]

                    if "vnicFc" in self._parent._config.sdk_objects:
                        for vnic_fc in vnic_fc_list:
                            if self._parent._dn:
                                if self._parent._dn + "/ls-" + self.name + "/" in vnic_fc.dn:
                                    vhba = {"_object_type": "vhbas"}
                                    vhba.update({"name": vnic_fc.name})
                                    vhba.update({"wwpn_pool": vnic_fc.ident_pool_name})
                                    if vnic_fc.addr != "derived":
                                        vhba.update({"wwpn": vnic_fc.addr})
                                    elif not vnic_fc.ident_pool_name and vnic_fc.addr == "derived":
                                        vhba.update({"wwpn": "derived"})
                                    vhba.update({"order": vnic_fc.order})
                                    if vhba["order"] == "unspecified":
                                        vhba["order"] = None
                                    vhba.update({"fabric": vnic_fc.switch_id})
                                    vhba.update({"max_data_field_size": vnic_fc.max_data_field_size})
                                    vhba.update({"pin_group": vnic_fc.pin_to_group_name})
                                    vhba.update({"adapter_policy": vnic_fc.adaptor_profile_name})
                                    vhba.update({"qos_policy": vnic_fc.qos_policy_name})
                                    vhba.update({"vhba_template": vnic_fc.nw_templ_name})
                                    vhba.update({"stats_threshold_policy": vnic_fc.stats_policy_name})
                                    vhba.update({"persistent_binding": vnic_fc.pers_bind})
                                    if "vnicFcIf" in self._config.sdk_objects:
                                        for vsan in vnic_fc_if_list:
                                            if self._parent._dn + "/ls-" + self.name + "/" + "fc-" + \
                                                    vhba['name'] + "/" in vsan.dn:
                                                vhba.update({"vsan": vsan.name})

                                    # Fetching the operational state of the referenced policies
                                    oper_state = {}
                                    oper_state.update(
                                        self.get_operational_state(
                                            policy_dn=vnic_fc.oper_adaptor_profile_name,
                                            separator="/fc-profile-",
                                            policy_name="adapter_policy"
                                        )
                                    )
                                    oper_state.update(
                                        self.get_operational_state(
                                            policy_dn=vnic_fc.oper_pin_to_group_name,
                                            separator="/san-pin-group-",
                                            policy_name="pin_group"
                                        )
                                    )
                                    oper_state.update(
                                        self.get_operational_state(
                                            policy_dn=vnic_fc.oper_qos_policy_name,
                                            separator="/ep-qos-",
                                            policy_name="qos_policy"
                                        )
                                    )
                                    oper_state.update(
                                        self.get_operational_state(
                                            policy_dn=vnic_fc.oper_stats_policy_name,
                                            separator="/thr-policy-",
                                            policy_name="stats_threshold_policy"
                                        )
                                    )
                                    oper_state.update(
                                        self.get_operational_state(
                                            policy_dn=vnic_fc.oper_nw_templ_name,
                                            separator="/san-conn-templ-",
                                            policy_name="vhba_template"
                                        )
                                    )
                                    oper_state.update(
                                        self.get_operational_state(
                                            policy_dn=vnic_fc.oper_ident_pool_name,
                                            separator="/wwn-pool-",
                                            policy_name="wwpn_pool"
                                        )
                                    )
                                    if vnic_fc.oper_host_port in ["ANY"]:
                                        oper_state.update({"host_port": "any"})
                                    elif vnic_fc.oper_host_port not in ["", "NONE"]:
                                        oper_state.update({"host_port": vnic_fc.oper_host_port})
                                    else:
                                        oper_state.update({"host_port": None})

                                    if vnic_fc.oper_vcon not in ["any"]:
                                        oper_state.update({"vcon": vnic_fc.oper_vcon})
                                    else:
                                        oper_state.update({"vcon": None})

                                    if vnic_fc.oper_order not in ["", "unspecified"]:
                                        oper_state.update({"order": vnic_fc.oper_order})
                                    else:
                                        oper_state.update({"order": None})

                                    vhba['operational_state'] = oper_state

                                    self.vhbas.append(vhba)

                if "lsVConAssign" in self._parent._config.sdk_objects:
                    for vcon in self._config.sdk_objects["lsVConAssign"]:
                        if self._parent._dn:
                            if self._parent._dn + "/ls-" + self.name + "/" in vcon.dn:
                                place = {}
                                place.update({"host_port": vcon.admin_host_port})
                                if place["host_port"] == "ANY":
                                    place["host_port"] = "any"
                                elif place["host_port"] == "NONE":
                                    place["host_port"] = None
                                place.update({"vcon": vcon.admin_vcon})
                                place.update({"order": vcon.order})
                                if place["order"] == "unspecified":
                                    place["order"] = None
                                if vcon.transport == "ethernet":
                                    place.update({"vnic": vcon.vnic_name})
                                elif vcon.transport == "fc":
                                    place.update({"vhba": vcon.vnic_name})
                                self.placement.append(place)

                if "fabricVCon" in self._parent._config.sdk_objects:
                    for vcon in self._config.sdk_objects["fabricVCon"]:
                        if self._parent._dn:
                            if self._parent._dn + "/ls-" + self.name + "/" in vcon.dn:
                                if vcon.inst_type == "manual":
                                    for vnic in vnic_ether_list:
                                        if self._parent._dn:
                                            if self._parent._dn + "/ls-" + self.name + "/" in vnic.dn:
                                                if vnic.admin_vcon == vcon.id:
                                                    place = {}
                                                    place.update({"vcon": vcon.id})
                                                    place.update({"vnic": vnic.name})
                                                    place.update({"host_port": vnic.admin_host_port})
                                                    if place["host_port"] == "ANY":
                                                        place["host_port"] = "any"
                                                    elif place["host_port"] == "NONE":
                                                        place["host_port"] = None
                                                    self.specific_placement.append(place)
                                                    continue
                                    for vnic in self._config.sdk_objects["vnicFc"]:
                                        if self._parent._dn:
                                            if self._parent._dn + "/ls-" + self.name + "/" in vnic.dn:
                                                if vnic.admin_vcon == vcon.id:
                                                    place = {}
                                                    place.update({"vcon": vcon.id})
                                                    place.update({"vhba": vnic.name})
                                                    place.update({"host_port": vnic.admin_host_port})
                                                    if place["host_port"] == "ANY":
                                                        place["host_port"] = "any"
                                                    elif place["host_port"] == "NONE":
                                                        place["host_port"] = None
                                                    self.specific_placement.append(place)

                if "storageIniGroup" in self._parent._config.sdk_objects:
                    for initiator_group in self._config.sdk_objects["storageIniGroup"]:
                        if self._parent._dn:
                            if self._parent._dn + "/ls-" + self.name + "/" in initiator_group.dn:
                                initiator = {}
                                oper_state = {}
                                initiator.update({"name": initiator_group.name})
                                initiator.update({"descr": initiator_group.descr})
                                if "vnicFcGroupDef" in self._parent._config.sdk_objects:
                                    for fc_group in self._config.sdk_objects["vnicFcGroupDef"]:
                                        if initiator_group.dn in fc_group.dn:
                                            initiator.update(
                                                {"storage_connection_policy": fc_group.storage_conn_policy_name})
                                            oper_state.update(
                                                self.get_operational_state(
                                                    policy_dn=fc_group.oper_storage_conn_policy_name,
                                                    separator="/storage-connpolicy-",
                                                    policy_name="storage_connection_policy"
                                                )
                                            )
                                            break
                                if "storageInitiator" in self._parent._config.sdk_objects:
                                    initiator.update({"initiators": []})
                                    for sto_init in self._config.sdk_objects["storageInitiator"]:
                                        if initiator_group.dn in sto_init.dn:
                                            initiator['initiators'].append(sto_init.name)
                                initiator['operational_state'] = oper_state
                                self.vhba_initiator_groups.append(initiator)

                if "vnicIScsiBootVnic" in self._parent._config.sdk_objects:
                    for mo in self._config.sdk_objects["vnicIScsiBootVnic"]:
                        if self._parent._dn:
                            if self._parent._dn + "/ls-" + self.name + "/" in mo.dn:
                                boot_param = {"_object_type": "iscsi_boot_parameters"}
                                boot_param.update({"iscsi_vnic_name": mo.name})
                                boot_param.update({"authentication_profile": mo.auth_profile_name})
                                boot_param.update({"iqn_pool": mo.iqn_ident_pool_name})
                                # Setting iSCSI Target Interface Type as "Static" by default. This
                                # will be overwritten for vNICs which has vnicIScsiAutoTargetIf Property
                                boot_param.update({"iscsi_target_interface": "Static"})
                                if mo.initiator_name != "derived":
                                    boot_param.update({"iqn": mo.initiator_name})
                                if "vnicIPv4PooledIscsiAddr" in self._parent._config.sdk_objects:
                                    for mo_ip_pool in self._config.sdk_objects["vnicIPv4PooledIscsiAddr"]:
                                        if mo.dn in mo_ip_pool.dn:
                                            boot_param.update({
                                                "initiator_ip_address_policy": mo_ip_pool.ident_pool_name,
                                                "ipv4_address": mo_ip_pool.addr,
                                                "subnet_mask": mo_ip_pool.subnet,
                                                "default_gateway": mo_ip_pool.def_gw,
                                                "primary_dns": mo_ip_pool.prim_dns,
                                                "secondary_dns": mo_ip_pool.sec_dns})
                                if "vnicIPv4IscsiAddr" in self._parent._config.sdk_objects:
                                    for mo_ipv4_iscsi_addr in self._config.sdk_objects["vnicIPv4IscsiAddr"]:
                                        if mo.dn in mo_ipv4_iscsi_addr.dn:
                                            boot_param.update({
                                                "ipv4_address": mo_ipv4_iscsi_addr.addr,
                                                "subnet_mask": mo_ipv4_iscsi_addr.subnet,
                                                "default_gateway": mo_ipv4_iscsi_addr.def_gw,
                                                "primary_dns": mo_ipv4_iscsi_addr.prim_dns,
                                                "secondary_dns": mo_ipv4_iscsi_addr.sec_dns})
                                if "vnicIScsiAutoTargetIf" in self._parent._config.sdk_objects:
                                    for mo_if_auto in self._config.sdk_objects["vnicIScsiAutoTargetIf"]:
                                        if mo.dn in mo_if_auto.dn:
                                            boot_param["iscsi_target_interface"] = "Auto"
                                            boot_param.update({"dhcp_vendor_id": mo_if_auto.dhcp_vendor_id})
                                            # Since we have a DHCP Vendor ID for Auto Target Interface, we empty the
                                            # Initiator IP Address Policy (IQN Pool), as this is mutually exclusive
                                            if "iqn_pool" in boot_param:
                                                boot_param.pop("iqn_pool")
                                boot_param.update({"iscsi_static_targets": []})
                                if "vnicIScsiStaticTargetIf" in self._parent._config.sdk_objects:
                                    for mo_if in self._config.sdk_objects["vnicIScsiStaticTargetIf"]:
                                        if mo.dn in mo_if.dn:
                                            interface = {}
                                            interface.update({"name": mo_if.name})
                                            interface.update({"port": mo_if.port})
                                            interface.update({"authentication_profile": mo_if.auth_profile_name})
                                            interface.update({"ip_address": mo_if.ip_address})
                                            interface.update({"priority": mo_if.priority})
                                            if "vnicLun" in self._parent._config.sdk_objects:
                                                for mo_lun in self._config.sdk_objects["vnicLun"]:
                                                    if mo_if.dn in mo_lun.dn:
                                                        interface.update({"lun_id": mo_lun.id})
                                            # Fetching the operational state of the referenced policies
                                            authentication_profile = self.get_operational_state(
                                                policy_dn=mo_if.oper_auth_profile_name,
                                                separator="/iscsi-auth-profile-",
                                                policy_name="authentication_profile"
                                            )
                                            if mo_if.auth_profile_name:
                                                if not authentication_profile:
                                                    for mo_if_if in self._config.sdk_objects["vnicIScsiStaticTargetIf"]:
                                                        if self._parent._dn + "/ls-" + self.name + "/iscsi-" + \
                                                                mo.name + "/vlan" in mo_if_if.dn:
                                                            authentication_profile = self.get_operational_state(
                                                                policy_dn=mo_if_if.oper_auth_profile_name,
                                                                separator="/iscsi-auth-profile-",
                                                                policy_name="authentication_profile"
                                                            )
                                                            break
                                            operational_state = {}
                                            operational_state.update(authentication_profile)
                                            interface.update({"operational_state":
                                                              operational_state})
                                            boot_param["iscsi_static_targets"].append(interface)

                                self.iscsi_boot_parameters.append(boot_param)

                # Fetching the operational state of the referenced policies
                self.operational_state = {}
                self.operational_state.update(
                    self.get_operational_state(
                        policy_dn=ls_server.oper_bios_profile_name,
                        separator="/bios-prof-",
                        policy_name="bios_policy"
                    )
                )
                self.operational_state.update(
                    self.get_operational_state(
                        policy_dn=ls_server.oper_boot_policy_name,
                        separator="/boot-policy-",
                        policy_name="boot_policy"
                    )
                )
                self.operational_state.update(
                    self.get_operational_state(
                        policy_dn=ls_server.oper_dynamic_con_policy_name,
                        separator="/dynamic-con-",
                        policy_name="dynamic_vnic_connection_policy"
                    )
                )
                self.operational_state.update(
                    self.get_operational_state(
                        policy_dn=ls_server.oper_ext_ip_pool_name,
                        separator="/ip-pool-",
                        policy_name="outband_ipv4_pool"
                    )
                )
                self.operational_state.update(
                    self.get_operational_state(
                        policy_dn=ls_server.oper_graphics_card_policy_name,
                        separator="/graphics-card-policy-",
                        policy_name="graphics_card_policy"
                    )
                )
                self.operational_state.update(
                    self.get_operational_state(
                        policy_dn=ls_server.oper_host_fw_policy_name,
                        separator="/fw-host-pack-",
                        policy_name="host_firmware_package"
                    )
                )
                self.operational_state.update(
                    self.get_operational_state(
                        policy_dn=ls_server.oper_ident_pool_name,
                        separator="/uuid-pool-",
                        policy_name="uuid_pool"
                    )
                )
                self.operational_state.update(
                    self.get_operational_state(
                        policy_dn=ls_server.oper_kvm_mgmt_policy_name,
                        separator="/kvm-mgmt-policy-",
                        policy_name="kvm_management_policy"
                    )
                )
                self.operational_state.update(
                    self.get_operational_state(
                        policy_dn=ls_server.oper_local_disk_policy_name,
                        separator="/local-disk-config-",
                        policy_name="local_disk_configuration_policy"
                    )
                )
                self.operational_state.update(
                    self.get_operational_state(
                        policy_dn=ls_server.oper_maint_policy_name,
                        separator="/maint-",
                        policy_name="maintenance_policy"
                    )
                )
                self.operational_state.update(
                    self.get_operational_state(
                        policy_dn=ls_server.oper_mgmt_access_policy_name,
                        separator="/auth-profile-",
                        policy_name="ipmi_access_profile"
                    )
                )
                self.operational_state.update(
                    self.get_operational_state(
                        policy_dn=ls_server.oper_spdm_certificate_policy_name,
                        separator="/spdm-cert-policy-",
                        policy_name="spdm_certificate_policy"
                    )
                )
                self.operational_state.update(
                    self.get_operational_state(
                        policy_dn=ls_server.oper_persistent_memory_policy_name,
                        separator="/pmemory-policy-",
                        policy_name="persistent_memory_policy"
                    )
                )
                self.operational_state.update(
                    self.get_operational_state(
                        policy_dn=ls_server.oper_power_policy_name,
                        separator="/power-policy-",
                        policy_name="power_control_policy"
                    )
                )
                self.operational_state.update(
                    self.get_operational_state(
                        policy_dn=ls_server.oper_power_sync_policy_name,
                        separator="/power-sync-",
                        policy_name="power_sync_policy"
                    )
                )
                self.operational_state.update(
                    self.get_operational_state(
                        policy_dn=ls_server.oper_scrub_policy_name,
                        separator="/scrub-",
                        policy_name="scrub_policy"
                    )
                )
                self.operational_state.update(
                    self.get_operational_state(
                        policy_dn=ls_server.oper_sol_policy_name,
                        separator="/sol-",
                        policy_name="serial_over_lan_policy"
                    )
                )
                self.operational_state.update(
                    self.get_operational_state(
                        policy_dn=ls_server.oper_src_templ_name,
                        separator="/ls-",
                        policy_name="service_profile_template"
                    )
                )
                self.operational_state.update(
                    self.get_operational_state(
                        policy_dn=ls_server.oper_stats_policy_name,
                        separator="/thr-policy-",
                        policy_name="threshold_policy"
                    )
                )
                self.operational_state.update(
                    self.get_operational_state(
                        policy_dn=ls_server.oper_vcon_profile_name,
                        separator="/vcon-profile-",
                        policy_name="placement_policy"
                    )
                )
                self.operational_state.update(
                    self.get_operational_state(
                        policy_dn=ls_server.oper_vmedia_policy_name,
                        separator="/mnt-cfg-policy-",
                        policy_name="vmedia_policy"
                    )
                )
                if oper_inband_ipv4_pool:
                    self.operational_state.update(oper_inband_ipv4_pool)
                if oper_inband_ipv6_pool:
                    self.operational_state.update(oper_inband_ipv6_pool)
                if oper_lan_connectivity_policy:
                    self.operational_state.update(oper_lan_connectivity_policy)
                if oper_san_connectivity_policy:
                    self.operational_state.update(oper_san_connectivity_policy)
                if oper_server_pool:
                    self.operational_state.update(oper_server_pool)
                if oper_storage_profile:
                    self.operational_state.update(oper_storage_profile)
                if oper_wwnn_pool:
                    self.operational_state.update(oper_wwnn_pool)
                if ls_server.pn_dn:
                    assigned_server = {
                        "server_id": None,
                        "chassis_id": None,
                        "slot_id": None
                    }
                    if ls_server.pn_dn.startswith("sys/chassis"):
                        assigned_server["chassis_id"] = ls_server.pn_dn.split("sys/chassis-")[1].split("/blade-")[0]
                        assigned_server["slot_id"] = ls_server.pn_dn.split("/blade-")[1]
                    elif ls_server.pn_dn.startswith("sys/rack-unit"):
                        assigned_server["server_id"] = ls_server.pn_dn.split("sys/rack-unit-")[1]
                    if "computeBoard" in self._parent._config.sdk_objects:
                        for compute_board in self._config.sdk_objects["computeBoard"]:
                            if ls_server.pn_dn + "/board" == compute_board.dn:
                                assigned_server["serial_number"] = compute_board.serial
                                break

                    self.operational_state.update({"assigned_server": assigned_server})

                if ls_server.oper_state:
                    self.operational_state.update({"profile_state": ls_server.oper_state})

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

                # We reconstruct the DN of the Service Profile object as we need it for Specific Policies under SP
                if self._parent._dn:
                    self._dn = self._parent._dn + "/ls-" + str(self.name)

                if "template" in self.type:
                    self._CONFIG_NAME = "Service Profile Template"
                if self.policy_owner == "ucs-central":
                    self._CONFIG_NAME = "Global " + self._CONFIG_NAME

                # We handle the Specific Policies under Service Profile
                if "specific_boot_policy" in json_content:
                    self.specific_boot_policy = UcsSystemBootPolicy(
                        parent=self, json_content=json_content["specific_boot_policy"]
                    )
                if "specific_dynamic_vnic_connection_policy" in json_content:
                    self.specific_dynamic_vnic_connection_policy = UcsSystemDynamicVnicConnectionPolicy(
                        parent=self, json_content=json_content["specific_dynamic_vnic_connection_policy"]
                    )
                if "specific_local_disk_configuration_policy" in json_content:
                    self.specific_local_disk_configuration_policy = UcsSystemLocalDiskConfPolicy(
                        parent=self, json_content=json_content["specific_local_disk_configuration_policy"]
                    )
                if "specific_serial_over_lan_policy" in json_content:
                    self.specific_serial_over_lan_policy = UcsSystemSerialOverLanPolicy(
                        parent=self, json_content=json_content["specific_serial_over_lan_policy"]
                    )
                if "specific_storage_profile" in json_content:
                    self.specific_storage_profile = UcsSystemStorageProfile(
                        parent=self, json_content=json_content["specific_storage_profile"]
                    )
                if "specific_vmedia_policy" in json_content:
                    self.specific_vmedia_policy = UcsSystemVmediaPolicy(
                        parent=self, json_content=json_content["specific_vmedia_policy"]
                    )


        self.clean_object()

    def clean_object(self):
        UcsSystemConfigObject.clean_object(self)

        for element in self.vhbas:
            for value in ["adapter_policy", "vhba_template", "fabric", "name", "order", "wwpn_pool",
                          "pin_group", "max_data_field_size", "qos_policy", "vsan", "stats_threshold_policy",
                          "persistent_binding", "wwpn", "operational_state"]:
                if value not in element:
                    element[value] = None

            # Flagging this as a vHBA
            element["_object_type"] = "vhbas"

            if element["operational_state"]:
                for policy in ["adapter_policy", "pin_group", "qos_policy", "stats_threshold_policy",
                               "vhba_template", "wwpn_pool"]:
                    if policy not in element["operational_state"]:
                        element["operational_state"][policy] = None
                    elif element["operational_state"][policy]:
                        for value in ["name", "org"]:
                            if value not in element["operational_state"][policy]:
                                element["operational_state"][policy][value] = None

                for state in ["host_port", "order", "vcon"]:
                    if state not in element["operational_state"]:
                        element["operational_state"][state] = None

        for element in self.vhba_initiator_groups:
            for value in ["descr", "initiators", "name", "operational_state", "storage_connection_policy"]:
                if value not in element:
                    element[value] = None

            if element["operational_state"]:
                if "storage_connection_policy" not in element["operational_state"]:
                    element["operational_state"]["storage_connection_policy"] = None
                elif element["operational_state"]["storage_connection_policy"]:
                    for value in ["name", "org"]:
                        if value not in element["operational_state"]["storage_connection_policy"]:
                            element["operational_state"]["storage_connection_policy"][value] = None

        for element in self.iscsi_vnics:
            for value in ["name", "vlan", "mac_address_pool", "iscsi_adapter_policy", "mac_address",
                          "overlay_vnic", "operational_state"]:
                if value not in element:
                    element[value] = None

            if element["operational_state"]:
                for policy in ["iscsi_adapter_policy"]:
                    if policy not in element["operational_state"]:
                        element["operational_state"][policy] = None
                    elif element["operational_state"][policy]:
                        for value in ["name", "org"]:
                            if value not in element["operational_state"][policy]:
                                element["operational_state"][policy][value] = None

        for element in self.placement:
            for value in ["vcon", "vnic", "vhba", "order", "host_port"]:
                if value not in element:
                    element[value] = None

        for element in self.specific_placement:
            for value in ["vcon", "vnic", "vhba"]:
                if value not in element:
                    element[value] = None

        for element in self.vnics:
            for value in ["vlans", "vnic_template", "adapter_policy", "name", "cdn_source", "cdn_name",
                          "vlan_native", "vlan_q_in_q", "order", "fabric", "q_in_q", "mac_address_pool", "mtu",
                          "qos_policy", "network_control_policy", "dynamic_vnic", "pin_group",
                          "stats_threshold_policy", "mac_address", "vlan_groups", "operational_state",
                          "redundancy_pair", "usnic_connection_policy", "vmq_connection_policy",
                          "sriov_hpn_connection_policy"]:
                if value not in element:
                    element[value] = None

            # Flagging this as a vNIC
            element["_object_type"] = "vnics"

            if element["operational_state"]:
                for policy in ["adapter_policy", "mac_address_pool", "network_control_policy", "pin_group",
                               "qos_policy", "sriov_hpn_connection_policy", "stats_threshold_policy",
                               "usnic_connection_policy", "vmq_connection_policy", "vnic_template"]:
                    if policy not in element["operational_state"]:
                        element["operational_state"][policy] = None
                    elif element["operational_state"][policy]:
                        for value in ["name", "org"]:
                            if value not in element["operational_state"][policy]:
                                element["operational_state"][policy][value] = None

                for state in ["host_port", "order", "vcon"]:
                    if state not in element["operational_state"]:
                        element["operational_state"][state] = None

        for element in self.iscsi_boot_parameters:
            for value in ["iscsi_vnic_name", "authentication_profile", "iqn_pool",
                          "initiator_ip_address_policy", "iscsi_target_interface", "iscsi_static_targets",
                          "dhcp_vendor_id", "priority", "iqn", "default_gateway", "ipv4_address",
                          "primary_dns", "secondary_dns", "subnet_mask"]:
                if value not in element:
                    element[value] = None

            # Flagging this as an iscsi_boot_parameter
            element["_object_type"] = "iscsi_boot_parameters"

            if element["iscsi_static_targets"]:
                for subelement in element["iscsi_static_targets"]:
                    for subvalue in ["name", "port", "lun_id", "authentication_profile", "ip_address"]:
                        if subvalue not in subelement:
                            subelement[subvalue] = None
            else:
                element["iscsi_static_targets"] = []

        if not self.operational_state:
            self.operational_state = {}
        for policy in [
            "bios_policy", "boot_policy", "dynamic_vnic_connection_policy", "graphics_card_policy",
            "host_firmware_package", "inband_ipv4_pool", "inband_ipv4", "inband_ipv6_pool", "inband_ipv6",
            "ipmi_access_profile", "kvm_management_policy", "lan_connectivity_policy",
            "local_disk_configuration_policy", "maintenance_policy", "outband_ipv4_pool", "outband_ipv4"
                                                                                          "persistent_memory_policy",
            "placement_policy", "power_control_policy", "power_sync_policy",
            "san_connectivity_policy", "scrub_policy", "serial_over_lan_policy", "server_pool",
            "service_profile_template", "spdm_certificate_policy", "storage_profile", "threshold_policy",
            "uuid_pool", "vmedia_policy", "wwnn_pool", "wwnn"
        ]:
            if policy not in self.operational_state:
                self.operational_state[policy] = None
            elif self.operational_state[policy]:
                for value in ["name", "org"]:
                    if value not in self.operational_state[policy]:
                        self.operational_state[policy][value] = None

        if "assigned_server" not in self.operational_state:
            self.operational_state["assigned_server"] = None
        elif self.operational_state["assigned_server"]:
            for value in ["server_id", "chassis_id", "slot_id"]:
                if value not in self.operational_state["assigned_server"]:
                    self.operational_state["assigned_server"][value] = None

        if "profile_state" not in self.operational_state:
            self.operational_state["profile_state"] = None

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + str(self.name))
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + str(self.name) +
                                ", waiting for a commit")

        if hasattr(self._parent, '_dn'):
            parent_mo = self._parent._dn
        else:
            self.logger(level="error",
                        message="Impossible to find the parent dn of " + self._CONFIG_NAME + " : " + str(self.name))
            return False

        outband_ipv4_pool_state = None
        if self.outband_ipv4_pool:
            outband_ipv4_pool_state = "pooled"

        uuid_pool = self.uuid_pool
        uuid = self.uuid
        if self.uuid == "hardware-default":
            uuid = "derived"
            uuid_pool = None

        mo_ls_server = LsServer(parent_mo_or_dn=parent_mo,
                                name=self.name,
                                type=self.type,
                                bios_profile_name=self.bios_policy,
                                boot_policy_name=self.boot_policy,
                                descr=self.descr,
                                usr_lbl=self.user_label,
                                dynamic_con_policy_name=self.dynamic_vnic_connection_policy,
                                host_fw_policy_name=self.host_firmware_package,
                                local_disk_policy_name=self.local_disk_configuration_policy,
                                maint_policy_name=self.maintenance_policy,
                                scrub_policy_name=self.scrub_policy,
                                ident_pool_name=uuid_pool,
                                uuid=uuid,
                                vmedia_policy_name=self.vmedia_policy,
                                power_sync_policy_name=self.power_sync_policy,
                                power_policy_name=self.power_control_policy,
                                sol_policy_name=self.serial_over_lan_policy,
                                mgmt_access_policy_name=self.ipmi_access_profile,
                                vcon_profile_name=self.placement_policy,
                                stats_policy_name=self.threshold_policy,
                                kvm_mgmt_policy_name=self.kvm_management_policy,
                                spdm_certificate_policy_name=self.spdm_certificate_policy,
                                graphics_card_policy_name=self.graphics_card_policy,
                                persistent_memory_policy_name=self.persistent_memory_policy,
                                ext_ip_pool_name=self.outband_ipv4_pool,
                                ext_ip_state=outband_ipv4_pool_state)

        self._handle.add_mo(mo=mo_ls_server, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False

        # Push Specific Policies
        is_pushed = True
        if self.specific_boot_policy:
            is_pushed = self.specific_boot_policy.push_object() and is_pushed
        if self.specific_dynamic_vnic_connection_policy:
            is_pushed = self.specific_dynamic_vnic_connection_policy.push_object() and is_pushed
        if self.specific_local_disk_configuration_policy:
            is_pushed = self.specific_local_disk_configuration_policy.push_object() and is_pushed
        if self.specific_serial_over_lan_policy:
            is_pushed = self.specific_serial_over_lan_policy.push_object() and is_pushed
        if self.specific_storage_profile:
            is_pushed = self.specific_storage_profile.push_object() and is_pushed
        if self.specific_vmedia_policy:
            is_pushed = self.specific_vmedia_policy.push_object() and is_pushed

        # Add Asset Tag
        if self.asset_tag:
            LsServerExtension(parent_mo_or_dn=mo_ls_server, asset_tag=self.asset_tag)

        # Add WWNN Pool
        if self.wwnn_pool:
            VnicFcNode(parent_mo_or_dn=mo_ls_server, ident_pool_name=self.wwnn_pool, addr=self.wwnn)

        # Add Server Pool
        if self.server_pool:
            LsRequirement(parent_mo_or_dn=mo_ls_server, name=self.server_pool, qualifier=self.server_pool_qualification,
                          restrict_migration=self.restrict_migration)

        # Add a Storage Profile
        if self.storage_profile:
            LstorageProfileBinding(parent_mo_or_dn=mo_ls_server, storage_profile_name=self.storage_profile)

        # Add SAN and/or LAN Connectivity Policy
        if self.san_connectivity_policy or self.lan_connectivity_policy:
            VnicConnDef(parent_mo_or_dn=mo_ls_server, san_conn_policy_name=self.san_connectivity_policy,
                        lan_conn_policy_name=self.lan_connectivity_policy)

        # Add Inband Management IP Address
        if self.inband_ipv4_pool or self.inband_ipv6_pool or self.inband_network:
            mo_mgmt_int = MgmtInterface(parent_mo_or_dn=mo_ls_server,
                                        ip_v4_state="pooled",
                                        ip_v6_state="pooled",
                                        mode="in-band")
            mo_vnet = MgmtVnet(parent_mo_or_dn=mo_mgmt_int, id="1", name=self.inband_network)
            VnicIpV4MgmtPooledAddr(parent_mo_or_dn=mo_vnet, name=self.inband_ipv4_pool)
            VnicIpV6MgmtPooledAddr(parent_mo_or_dn=mo_vnet, name=self.inband_ipv6_pool)

        # Add the power state to be applied when a server pool is associated with the server
        # Status : only "admin-down", "admin-up", "down" or "up" - are used in a service profile
        # "soft-shut-down-only" can also be found as a state
        if self.server_power_state:
            LsPower(parent_mo_or_dn=mo_ls_server, state=self.server_power_state)

        # Add association to a server
        for server in self.servers:
            if ("chassis_id" and "blade") in server and "rack_id" not in server:
                server = "sys/chassis-" + server["chassis_id"] + "/blade-" + server["blade"]
            elif ("chassis_id" and "blade") not in server and "rack_id" in server:
                server = "sys/rack-unit-" + server["rack_id"]
            else:
                self.logger(level="error",
                            message="Wrong server details (chassis & blade /rack unit) for association "
                                    + "with service profile " + str(self.name))
                server = None
            LsBinding(parent_mo_or_dn=mo_ls_server, pn_dn=server)

        # Add all the elements above. The elements below have all their own commit
        self._handle.add_mo(mo=mo_ls_server, modify_present=True)
        if commit:
            if self.commit(detail="Service Profile " + str(self.name) + " - Policies") != True:
                return False

        if self.iscsi_initiator_name or self.iscsi_vnics:
            mo_node = VnicIScsiNode(parent_mo_or_dn=mo_ls_server, iqn_ident_pool_name=self.iscsi_iqn_pool_name,
                                    initiator_name=self.iscsi_initiator_name)
            for iscsi_vnic in self.iscsi_vnics:
                mac_address_pool = iscsi_vnic['mac_address_pool']
                mac_address = iscsi_vnic["mac_address"]
                if mac_address == "hardware-default":
                    mac_address = None
                mo_vnic_iscsi = VnicIScsi(parent_mo_or_dn=mo_ls_server,
                                          adaptor_profile_name=iscsi_vnic["iscsi_adapter_policy"],
                                          ident_pool_name=mac_address_pool,
                                          addr=mac_address,
                                          name=iscsi_vnic['name'],
                                          vnic_name=iscsi_vnic["overlay_vnic"])
                VnicVlan(parent_mo_or_dn=mo_vnic_iscsi, vlan_name=iscsi_vnic["vlan"])
                self._handle.add_mo(mo=mo_vnic_iscsi, modify_present=True)

            self._handle.add_mo(mo=mo_node, modify_present=True)
            if commit:
                if self.commit(detail="iSCSI vNICs & Initiator Name of Service Profile " + mo_ls_server.name) != True:
                    return False

        for vnic in self.vnics:
            if vnic['fabric']:
                vnic['fabric'] = vnic['fabric'].upper()

            mac_address_pool = vnic['mac_address_pool']
            mac_address = vnic["mac_address"]
            if mac_address == "hardware-default":
                mac_address = "derived"
                mac_address_pool = None

            mo_vnic_ether = VnicEther(parent_mo_or_dn=mo_ls_server,
                                      name=vnic['name'],
                                      pin_to_group_name=vnic['pin_group'],
                                      order=vnic['order'],
                                      switch_id=vnic['fabric'],
                                      q_in_q=vnic['q_in_q'],
                                      admin_cdn_name=vnic['cdn_name'],
                                      cdn_source=vnic['cdn_source'],
                                      nw_ctrl_policy_name=vnic['network_control_policy'],
                                      adaptor_profile_name=vnic['adapter_policy'],
                                      qos_policy_name=vnic['qos_policy'],
                                      ident_pool_name=mac_address_pool,
                                      mtu=vnic['mtu'],
                                      nw_templ_name=vnic['vnic_template'],
                                      # redundancy_pair_type=vnic['redundancy_pair'],
                                      stats_policy_name=vnic['stats_threshold_policy'],
                                      addr=mac_address)

            if vnic['dynamic_vnic']:
                VnicDynamicConPolicyRef(parent_mo_or_dn=mo_vnic_ether, con_policy_name=vnic['dynamic_vnic'])
            elif vnic['sriov_hpn_connection_policy']:
                VnicSriovHpnConPolicyRef(parent_mo_or_dn=mo_vnic_ether,
                                         con_policy_name=vnic['sriov_hpn_connection_policy'])
            elif vnic['usnic_connection_policy']:
                VnicUsnicConPolicyRef(parent_mo_or_dn=mo_vnic_ether, con_policy_name=vnic['usnic_connection_policy'])
            elif vnic['vmq_connection_policy']:
                VnicVmqConPolicyRef(parent_mo_or_dn=mo_vnic_ether, con_policy_name=vnic['vmq_connection_policy'])

            if vnic['vlan_native']:
                if vnic['vlan_q_in_q'] == vnic['vlan_native']:
                    vnic_q_in_q = "yes"
                else:
                    vnic_q_in_q = "no"
                VnicEtherIf(parent_mo_or_dn=mo_vnic_ether, name=vnic['vlan_native'], default_net="yes",
                            is_qin_q_vlan=vnic_q_in_q)
            if vnic['vlans']:
                for vlan in vnic['vlans']:
                    if vnic['vlan_q_in_q'] == vlan:
                        vnic_q_in_q = "yes"
                    else:
                        vnic_q_in_q = "no"
                    VnicEtherIf(parent_mo_or_dn=mo_vnic_ether, name=vlan, default_net="no", is_qin_q_vlan=vnic_q_in_q)
            if vnic['vlan_groups']:
                for vlan_group in vnic['vlan_groups']:
                    FabricNetGroupRef(parent_mo_or_dn=mo_vnic_ether, name=vlan_group)

            self._handle.add_mo(mo=mo_vnic_ether, modify_present=True)
            if commit:
                if self.commit(detail=vnic['name']) != True:
                    return False

        for vhba in self.vhbas:
            if vhba['fabric']:
                vhba['fabric'] = vhba['fabric'].upper()
            mo_vnic_fc = VnicFc(parent_mo_or_dn=mo_ls_server,
                                name=vhba['name'],
                                max_data_field_size=vhba['max_data_field_size'],
                                order=vhba['order'],
                                switch_id=vhba['fabric'],
                                pin_to_group_name=vhba['pin_group'],
                                ident_pool_name=vhba['wwpn_pool'],
                                adaptor_profile_name=vhba['adapter_policy'],
                                qos_policy_name=vhba['qos_policy'],
                                nw_templ_name=vhba['vhba_template'],
                                stats_policy_name=vhba['stats_threshold_policy'],
                                pers_bind=vhba['persistent_binding'],
                                addr=vhba["wwpn"])
            if vhba['vsan']:
                VnicFcIf(parent_mo_or_dn=mo_vnic_fc, name=vhba['vsan'])
            self._handle.add_mo(mo=mo_vnic_fc, modify_present=True)
            if commit:
                if self.commit(detail=vhba['name']) != True:
                    return False

        specific_placement = False
        for place in self.specific_placement:
            if "vcon" in place:
                if place["vcon"] and not specific_placement:
                    specific_placement = True
                    # We first need to modify the fabric v con to put them in manual placement
                    FabricVCon(parent_mo_or_dn=mo_ls_server, id="1", inst_type="manual")
                    FabricVCon(parent_mo_or_dn=mo_ls_server, id="2", inst_type="manual")
                    FabricVCon(parent_mo_or_dn=mo_ls_server, id="3", inst_type="manual")
                    FabricVCon(parent_mo_or_dn=mo_ls_server, id="4", inst_type="manual")

                    self._handle.add_mo(mo=mo_ls_server, modify_present=True)
        if commit and specific_placement:
            if self.commit(detail="Manual specific placement") != True:
                return False
        for place in self.specific_placement:
            # Then, we set the placement
            if "vcon" in place:
                if place["vcon"]:
                    if ("vhba" in place) or ("vnic" in place):
                        if 'vhba' in place:
                            if place["vhba"]:
                                mo_vnic = VnicFc(parent_mo_or_dn=mo_ls_server, admin_vcon=place["vcon"],
                                                 name=place["vhba"], order=place["vcon"])
                                if place["host_port"] == "any":
                                    host_port = "ANY"
                                else:
                                    host_port = place["host_port"]
                                mo_vcon = LsVConAssign(parent_mo_or_dn=mo_ls_server, admin_vcon=place["vcon"],
                                                       admin_host_port=host_port, order=place["vcon"], transport="fc",
                                                       vnic_name=place["vhba"])
                                self._handle.add_mo(mo=mo_vnic, modify_present=True)
                                self._handle.add_mo(mo=mo_vcon, modify_present=True)
                                if commit:
                                    if self.commit(detail="Manual specific placement of " + place["vhba"]) != True:
                                        return False
                        if 'vnic' in place:
                            if place["vnic"]:
                                mo_vnic = VnicEther(parent_mo_or_dn=mo_ls_server, admin_vcon=place["vcon"],
                                                    name=place["vnic"], order=place["vcon"])
                                if place["host_port"] == "any":
                                    host_port = "ANY"
                                else:
                                    host_port = place["host_port"]
                                mo_vcon = LsVConAssign(parent_mo_or_dn=mo_ls_server, admin_vcon=place["vcon"],
                                                       admin_host_port=host_port, order=place["vcon"],
                                                       transport="ethernet", vnic_name=place["vnic"])
                                self._handle.add_mo(mo=mo_vnic, modify_present=True)
                                self._handle.add_mo(mo=mo_vcon, modify_present=True)
                                if commit:
                                    if self.commit(detail="Manual specific placement of " + place["vnic"]) != True:
                                        return False

        for place in self.placement:
            if ("vhba" in place) or ("vnic" in place):
                transport = ""
                name = ""
                if 'vnic' in place:
                    if place['vnic']:
                        transport = 'ethernet'
                        name = place['vnic']
                if 'vhba' in place:
                    if place['vhba']:
                        transport = 'fc'
                        name = place['vhba']
                mo_vcon_assign = LsVConAssign(parent_mo_or_dn=mo_ls_server, admin_vcon=place['vcon'],
                                              order=place['order'], transport=transport, vnic_name=name)
                self._handle.add_mo(mo=mo_vcon_assign, modify_present=True)
                if commit:
                    if self.commit(detail=name) != True:
                        return False

        for initiator in self.vhba_initiator_groups:
            mo_ini_group = StorageIniGroup(parent_mo_or_dn=mo_ls_server, name=initiator['name'],
                                           descr=initiator['descr'])

            if initiator['storage_connection_policy']:
                VnicFcGroupDef(parent_mo_or_dn=mo_ini_group,
                               storage_conn_policy_name=initiator['storage_connection_policy'])
            if initiator['initiators']:
                for sto_initiator in initiator['initiators']:
                    StorageInitiator(parent_mo_or_dn=mo_ini_group, name=sto_initiator)

            self._handle.add_mo(mo=mo_ini_group, modify_present=True)
            if commit:
                if self.commit(detail=initiator['name']) != True:
                    return False

        for iscsi_boot_parameter in self.iscsi_boot_parameters:
            mo_iscsi_boot_params = VnicIScsiBootParams(parent_mo_or_dn=mo_ls_server)

            if iscsi_boot_parameter["dhcp_vendor_id"]:
                mo_iscsi_boot_vnic = VnicIScsiBootVnic(parent_mo_or_dn=mo_iscsi_boot_params,
                                                       name=iscsi_boot_parameter["iscsi_vnic_name"]
                                                       )
                mo_ipv4_if = VnicIPv4If(parent_mo_or_dn=mo_iscsi_boot_vnic)
                mo_ipv4_dhcp = VnicIPv4Dhcp(parent_mo_or_dn=mo_ipv4_if)
                VnicIScsiAutoTargetIf(parent_mo_or_dn=mo_iscsi_boot_vnic,
                                      dhcp_vendor_id=iscsi_boot_parameter["dhcp_vendor_id"])
            else:
                mo_iscsi_boot_vnic = VnicIScsiBootVnic(parent_mo_or_dn=mo_iscsi_boot_params,
                                                       auth_profile_name=iscsi_boot_parameter[
                                                           "authentication_profile"],
                                                       iqn_ident_pool_name=iscsi_boot_parameter["iqn_pool"],
                                                       initiator_name=iscsi_boot_parameter["iqn"],
                                                       name=iscsi_boot_parameter["iscsi_vnic_name"])
                mo_ipv4_if = VnicIPv4If(parent_mo_or_dn=mo_iscsi_boot_vnic)
                if iscsi_boot_parameter["initiator_ip_address_policy"]:
                    VnicIPv4PooledIscsiAddr(parent_mo_or_dn=mo_ipv4_if,
                                            ident_pool_name=iscsi_boot_parameter["initiator_ip_address_policy"])
                else:
                    for ip_type in ["ipv4-pooled-iscsiaddr", "ipv4-dhcp", "ipv4iscsi"]:
                        mo_ipv4_if_delete = self._handle.query_dn(str(mo_ipv4_if.dn) + "/" + ip_type)
                        if mo_ipv4_if_delete:
                            self._handle.remove_mo(mo_ipv4_if_delete)
                    # This code is not working. Need to revisit. If "mo_ipv4_if.dn" is used instead of "mo_ipv4_if",
                    # code execution continues without any error. For actual functionality, "mo_ipv4_if" has to be used.
                    # But this will throw following error - ValueError: parent mo or dn must be specified
                    VnicIPv4IscsiAddr(parent_mo_or_dn=mo_ipv4_if.dn, addr=iscsi_boot_parameter["ipv4_address"],
                                      def_gw=iscsi_boot_parameter["default_gateway"],
                                      prim_dns=iscsi_boot_parameter["primary_dns"],
                                      sec_dns=iscsi_boot_parameter["secondary_dns"],
                                      subnet=iscsi_boot_parameter["subnet_mask"])

                for target in iscsi_boot_parameter["iscsi_static_targets"]:
                    mo_static_target_if = VnicIScsiStaticTargetIf(parent_mo_or_dn=mo_iscsi_boot_vnic,
                                                                  ip_address=target["ip_address"],
                                                                  name=target["name"],
                                                                  port=target["port"],
                                                                  auth_profile_name=target["authentication_profile"],
                                                                  priority=target["priority"])
                    VnicLun(parent_mo_or_dn=mo_static_target_if,
                            id=target["lun_id"])

            self._handle.add_mo(mo=mo_iscsi_boot_params, modify_present=True)
            if commit:
                if self.commit(detail=iscsi_boot_parameter["iscsi_vnic_name"]) != True:
                    return False

        return True and is_pushed

    def instantiate_profile(self):
        self.logger(message="Instantiating " + self._CONFIG_NAME +
                            " configuration from " + str(self.service_profile_template))

        if hasattr(self._parent, '_dn'):
            parent_mo = self._parent._dn
        else:
            self.logger(level="error",
                        message="Impossible to find the parent dn of " + self._CONFIG_NAME + " : " + str(self.name))
            return False

        if not hasattr(self, 'suffix_start_number'):
            self.suffix_start_number = "1"
        if not hasattr(self, 'number_of_instances'):
            self.number_of_instances = "1"

        # Creating the path to the template. Example = "org-root/org-DevTeam/ls-Template"
        template_name, template_org_path = self._config.get_operational_policy_name_and_org_path(
            source_object=self,
            policy_type="service_profile_template")
        if template_name and template_org_path:
            source_dn = "org-" + template_org_path.replace("/", "/org-") + "/ls-" + self.service_profile_template
        else:
            source_dn = parent_mo + "/ls-" + self.service_profile_template

        if self.suffix_start_number and self.number_of_instances:
            dn_set = DnSet()
            for i in range(int(self.suffix_start_number),
                           int(self.number_of_instances) + int(self.suffix_start_number)):
                dn = Dn()
                dn.attr_set("value", str(self.name + str(i)))
                dn_set.child_add(dn)

            elem = ls_instantiate_n_named_template(cookie=self._handle.cookie,
                                                   dn=source_dn,
                                                   in_error_on_existing="false", in_name_set=dn_set,
                                                   in_target_org=parent_mo, in_hierarchical="false")

            for i in range(self._device.push_attempts):
                try:
                    if i:
                        self.logger(level="warning",
                                    message="Trying to push again the instantiated service profile(s) from " +
                                            str(self.service_profile_template))
                    self._handle.process_xml_elem(elem)
                    self.logger(level='debug',
                                message=self.number_of_instances + " " + self._CONFIG_NAME + " instantiated from " +
                                str(self.service_profile_template) + " starting with " + str(self.name) +
                                self.suffix_start_number)
                    return True
                except ConnectionRefusedError:
                    self.logger(level="error", message="Connection refused while trying to instantiate from " +
                                                       str(self.service_profile_template))
                except UcsException as err:
                    self.logger(level="error",
                                message="Error while trying to instantiate from " +
                                        str(self.service_profile_template) + " " + err.error_descr)
                except urllib.error.URLError:
                    self.logger(
                        level="error", message="Timeout while trying to instantiate from " +
                        str(self.service_profile_template))

        else:
            elem = ls_instantiate_template(cookie=self._handle.cookie,
                                           dn=source_dn,
                                           in_error_on_existing="false",
                                           in_server_name=self.name,
                                           in_target_org=parent_mo, in_hierarchical="false")

            for i in range(self._device.push_attempts):
                try:
                    if i:
                        self.logger(level="warning",
                                    message="Trying to push again the instantiated service profile(s) from " +
                                            str(self.service_profile_template))
                    self._handle.process_xml_elem(elem)
                    self.logger(level='debug',
                                message=self._CONFIG_NAME + " " + str(self.name) + " instantiated from " +
                                str(self.service_profile_template))
                    return True
                except ConnectionRefusedError:
                    self.logger(level="error", message="Connection refused while trying to instantiate from " +
                                                       str(self.service_profile_template))
                except UcsException as err:
                    self.logger(level="error",
                                message="Error while trying to instantiate from " +
                                        str(self.service_profile_template) + " " + err.error_descr)
                except urllib.error.URLError:
                    self.logger(
                        level="error", message="Timeout while trying to instantiate from " +
                        str(self.service_profile_template))
