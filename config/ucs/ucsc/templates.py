# coding: utf-8
# !/usr/bin/env python

""" templates.py: Easy UCS Central Policies objects """

from config.ucs.object import UcsCentralConfigObject
from ucscsdk.mometa.fabric.FabricNetGroupRef import FabricNetGroupRef

from ucscsdk.mometa.vnic.VnicDynamicConPolicyRef import VnicDynamicConPolicyRef
from ucscsdk.mometa.vnic.VnicEtherIf import VnicEtherIf
from ucscsdk.mometa.vnic.VnicFcIf import VnicFcIf
from ucscsdk.mometa.vnic.VnicLanConnTempl import VnicLanConnTempl
from ucscsdk.mometa.vnic.VnicSanConnTempl import VnicSanConnTempl
from ucscsdk.mometa.vnic.VnicUsnicConPolicyRef import VnicUsnicConPolicyRef
from ucscsdk.mometa.vnic.VnicVmqConPolicyRef import VnicVmqConPolicyRef
from config.ucs.ucsc.policies import (UcsCentralDynamicVnicConnectionPolicy, UcsCentralMacPool,
                                      UcsCentralNetworkControlPolicy, UcsCentralQosPolicy, UcsCentralThresholdPolicy,
                                      UcsCentralUsnicConnectionPolicy, UcsCentralVmqConnectionPolicy, UcsCentralWwpnPool)


class UcsCentralVhbaTemplate(UcsCentralConfigObject):
    _CONFIG_NAME = "vHBA Template"
    _CONFIG_SECTION_NAME = "vhba_templates"
    _UCS_SDK_OBJECT_NAME = "vnicSanConnTempl"
    _POLICY_MAPPING_TABLE = {
        "pin_group": None,
        "qos_policy": UcsCentralQosPolicy,
        "stats_threshold_policy": UcsCentralThresholdPolicy,
        "wwpn_pool": UcsCentralWwpnPool
    }

    def __init__(self, parent=None, json_content=None, vhba_san_conn_templ=None):
        UcsCentralConfigObject.__init__(self, parent=parent, ucs_sdk_object=vhba_san_conn_templ)
        self.name = None
        self.fabric = None
        self.descr = None
        self.redundancy_type = None
        self.peer_redundancy_template = None
        self.template_type = None
        self.qos_policy = None
        self.pin_group = None
        self.max_data_field_size = None
        self.vsan = None
        self.wwpn_pool = None
        self.stats_threshold_policy = None
        self.operational_state = None

        if self._config.load_from == "live":
            if vhba_san_conn_templ is not None:
                self.name = vhba_san_conn_templ.name
                self.fabric = vhba_san_conn_templ.switch_id
                self.descr = vhba_san_conn_templ.descr
                self.redundancy_type = vhba_san_conn_templ.redundancy_pair_type
                self.peer_redundancy_template = vhba_san_conn_templ.peer_redundancy_templ_name
                self.template_type = vhba_san_conn_templ.templ_type
                self.qos_policy = vhba_san_conn_templ.qos_policy_name
                self.pin_group = vhba_san_conn_templ.pin_to_group_name
                self.max_data_field_size = vhba_san_conn_templ.max_data_field_size
                self.wwpn_pool = vhba_san_conn_templ.ident_pool_name
                self.stats_threshold_policy = vhba_san_conn_templ.stats_policy_name

                if "vnicFcIf" in self._config.sdk_objects and not self.vsan:
                    if self._parent._dn:
                        vsans = [vlan for vlan in self._config.sdk_objects["vnicFcIf"] if
                                 self._parent._dn + "/san-conn-templ-" + self.name + "/" in vlan.dn]
                        if len(vsans) == 1:
                            self.vsan = vsans[0].name
                        elif len(vsans) == 0:
                            self.logger(level="error",
                                        message=f"Missing at-least one VSAN in {self._CONFIG_NAME}: {str(self.name)}")
                        else:
                            self.logger(level="error",
                                        message=f"More than one VSAN can be found in {self._CONFIG_NAME}: "
                                                f"{str(self.name)}")

                # Fetching the operational state of the referenced policies
                self.operational_state = {}
                if vhba_san_conn_templ.oper_peer_redundancy_templ_name:
                    peer_redundancy_template_in_use = {
                        "org": '/'.join(
                            [oper_state.replace("org-", "", 1)
                             for oper_state in
                             vhba_san_conn_templ.oper_peer_redundancy_templ_name.split(
                                "/san-conn-templ-")[0].split("/")]),
                        "name": vhba_san_conn_templ.oper_peer_redundancy_templ_name.split("/san-conn-templ-")[1]}
                    self.operational_state.update(
                        {"peer_redundancy_template": peer_redundancy_template_in_use})
                else:
                    self.operational_state.update({"peer_redundancy_template": None})
                if vhba_san_conn_templ.oper_qos_policy_name:
                    qos_policy_in_use = {
                        "org": '/'.join(
                            [oper_state.replace("org-", "", 1)
                             for oper_state in vhba_san_conn_templ.oper_qos_policy_name.split("/ep-qos-")
                             [0].split("/")]),
                        "name": vhba_san_conn_templ.oper_qos_policy_name.split("/ep-qos-")[1]}
                    self.operational_state.update({"qos_policy": qos_policy_in_use})
                else:
                    self.operational_state.update({"qos_policy": None})
                if vhba_san_conn_templ.oper_stats_policy_name:
                    stats_policy_in_use = {
                        "org": '/'.join(
                            [oper_state.replace("org-", "", 1)
                             for oper_state in vhba_san_conn_templ.oper_stats_policy_name.split(
                                "/thr-policy-")[0].split("/")]),
                        "name": vhba_san_conn_templ.oper_stats_policy_name.split("/thr-policy-")[1]}
                    self.operational_state.update({"stats_threshold_policy": stats_policy_in_use})
                else:
                    self.operational_state.update({"stats_threshold_policy": None})

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

                for policy in ["peer_redundancy_template", "qos_policy", "stats_threshold_policy"]:
                    if not self.operational_state:
                        self.operational_state = {}
                    if policy not in self.operational_state:
                        self.operational_state[policy] = None
                    else:
                        for value in ["name", "org"]:
                            if value not in self.operational_state[policy]:
                                self.operational_state[policy][value] = None

        self.clean_object()

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

        redundancy_pair_type = "none" if self.redundancy_type == "no-redundancy" else self.redundancy_type
        mo_vnic_san_conn_temp = VnicSanConnTempl(parent_mo_or_dn=parent_mo, switch_id=self.fabric.upper(),
                                                 name=self.name, descr=self.descr,
                                                 redundancy_pair_type=redundancy_pair_type,
                                                 qos_policy_name=self.qos_policy,
                                                 peer_redundancy_templ_name=self.peer_redundancy_template,
                                                 templ_type=self.template_type, ident_pool_name=self.wwpn_pool,
                                                 max_data_field_size=self.max_data_field_size,
                                                 pin_to_group_name=self.pin_group,
                                                 stats_policy_name=self.stats_threshold_policy)
        if self.vsan:
            VnicFcIf(parent_mo_or_dn=mo_vnic_san_conn_temp, name=self.vsan)

        self._handle.add_mo(mo=mo_vnic_san_conn_temp, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True


class UcsCentralVnicTemplate(UcsCentralConfigObject):
    _CONFIG_NAME = "vNIC Template"
    _CONFIG_SECTION_NAME = "vnic_templates"
    _UCS_SDK_OBJECT_NAME = "vnicLanConnTempl"
    _POLICY_MAPPING_TABLE = {
        "dynamic_vnic_connection_policy": UcsCentralDynamicVnicConnectionPolicy,
        "mac_address_pool": UcsCentralMacPool,
        "network_control_policy": UcsCentralNetworkControlPolicy,
        "pin_group": None,
        "qos_policy": UcsCentralQosPolicy,
        "stats_threshold_policy": UcsCentralThresholdPolicy,
        "usnic_connection_policy": UcsCentralUsnicConnectionPolicy,
        "vmq_connection_policy": UcsCentralVmqConnectionPolicy,
    }

    def __init__(self, parent=None, json_content=None, vnic_lan_conn_templ=None):
        UcsCentralConfigObject.__init__(self, parent=parent, ucs_sdk_object=vnic_lan_conn_templ)
        self.name = None
        self.fabric = None
        self.descr = None
        self.dynamic_vnic_connection_policy = None
        self.redundancy_type = None
        self.peer_redundancy_template = None
        self.qos_policy = None
        self.cdn_source = None
        self.cdn_name = None
        self.target = []
        self.mtu = None
        self.mac_address_pool = None
        self.template_type = None
        self.pin_group = None
        self.stats_threshold_policy = None
        self.network_control_policy = None
        self.usnic_connection_policy = None
        self.vlan_native = None
        self.vlans = []
        self.vlan_groups = []
        self.vmq_connection_policy = None
        self.operational_state = None

        if self._config.load_from == "live":
            if vnic_lan_conn_templ is not None:
                self.name = vnic_lan_conn_templ.name
                self.fabric = vnic_lan_conn_templ.switch_id
                self.descr = vnic_lan_conn_templ.descr
                self.redundancy_type = vnic_lan_conn_templ.redundancy_pair_type
                self.peer_redundancy_template = vnic_lan_conn_templ.peer_redundancy_templ_name
                self.qos_policy = vnic_lan_conn_templ.qos_policy_name
                self.cdn_source = vnic_lan_conn_templ.cdn_source
                self.cdn_name = vnic_lan_conn_templ.admin_cdn_name
                self.target = vnic_lan_conn_templ.target.split(',')
                self.mtu = vnic_lan_conn_templ.mtu
                self.mac_address_pool = vnic_lan_conn_templ.ident_pool_name
                self.template_type = vnic_lan_conn_templ.templ_type
                self.pin_group = vnic_lan_conn_templ.pin_to_group_name
                self.stats_threshold_policy = vnic_lan_conn_templ.stats_policy_name
                self.network_control_policy = vnic_lan_conn_templ.nw_ctrl_policy_name
                self.operational_state = {}

                # Looking for the connection_policy
                if ("vnicDynamicConPolicyRef" in self._parent._config.sdk_objects and
                        not self.dynamic_vnic_connection_policy):
                    for policy in self._config.sdk_objects["vnicDynamicConPolicyRef"]:
                        if self._parent._dn:
                            if self._parent._dn + "/lan-conn-templ-" + self.name + "/" in policy.dn:
                                self.dynamic_vnic_connection_policy = policy.con_policy_name
                                self.operational_state.update(
                                    self.get_operational_state(
                                        policy_dn=policy.oper_con_policy_name,
                                        separator="/dynamic-con-",
                                        policy_name="dynamic_vnic_connection_policy"
                                    )
                                )
                                break
                if "vnicUsnicConPolicyRef" in self._parent._config.sdk_objects and not self.usnic_connection_policy:
                    for policy in self._config.sdk_objects["vnicUsnicConPolicyRef"]:
                        if self._parent._dn:
                            if self._parent._dn + "/lan-conn-templ-" + self.name + "/" in policy.dn:
                                self.usnic_connection_policy = policy.con_policy_name
                                self.operational_state.update(
                                    self.get_operational_state(
                                        policy_dn=policy.oper_con_policy_name,
                                        separator="/usnic-con-",
                                        policy_name="usnic_connection_policy"
                                    )
                                )
                                break
                if "vnicVmqConPolicyRef" in self._parent._config.sdk_objects and not self.vmq_connection_policy:
                    for policy in self._config.sdk_objects["vnicVmqConPolicyRef"]:
                        if self._parent._dn:
                            if self._parent._dn + "/lan-conn-templ-" + self.name + "/" in policy.dn:
                                self.vmq_connection_policy = policy.con_policy_name
                                self.operational_state.update(
                                    self.get_operational_state(
                                        policy_dn=policy.oper_con_policy_name,
                                        separator="/vmq-con-",
                                        policy_name="vmq_connection_policy"
                                    )
                                )
                                break
                if "vnicEtherIf" in self._config.sdk_objects:
                    if self._parent._dn:
                        vlans = [vlan for vlan in self._config.sdk_objects["vnicEtherIf"] if
                                 self._parent._dn + "/lan-conn-templ-" + self.name + "/" in vlan.dn]
                        if vlans:
                            for vlan in vlans:
                                if vlan.default_net in ["yes", "true"]:
                                    self.vlan_native = vlan.name
                                else:
                                    self.vlans.append(vlan.name)
                if "fabricNetGroupRef" in self._config.sdk_objects:
                    if self._parent._dn:
                        vlans = [vlan for vlan in self._config.sdk_objects["fabricNetGroupRef"] if
                                 self._parent._dn + "/lan-conn-templ-" + self.name + "/" in vlan.dn]
                        if vlans:
                            for vlan in vlans:
                                self.vlan_groups.append(vlan.name)

                # Fetching the operational state of the referenced policies
                self.operational_state.update(
                    self.get_operational_state(
                        policy_dn=vnic_lan_conn_templ.oper_nw_ctrl_policy_name,
                        separator="/nwctrl-",
                        policy_name="network_control_policy"
                    )
                )
                self.operational_state.update(
                    self.get_operational_state(
                        policy_dn=vnic_lan_conn_templ.oper_peer_redundancy_templ_name,
                        separator="/lan-conn-templ-",
                        policy_name="peer_redundancy_template"
                    )
                )
                self.operational_state.update(
                    self.get_operational_state(
                        policy_dn=vnic_lan_conn_templ.oper_qos_policy_name,
                        separator="/ep-qos-",
                        policy_name="qos_policy"
                    )
                )
                self.operational_state.update(
                    self.get_operational_state(
                        policy_dn=vnic_lan_conn_templ.oper_stats_policy_name,
                        separator="/thr-policy-",
                        policy_name="stats_threshold_policy"
                    )
                )

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

                for policy in ["dynamic_vnic_connection_policy", "mac_address_pool", "network_control_policy",
                               "peer_redundancy_template", "qos_policy", "stats_threshold_policy",
                               "usnic_connection_policy", "vmq_connection_policy"]:
                    if not self.operational_state:
                        self.operational_state = {}
                    if policy not in self.operational_state:
                        self.operational_state[policy] = None
                    else:
                        for value in ["name", "org"]:
                            if value not in self.operational_state[policy]:
                                self.operational_state[policy][value] = None

        self.clean_object()

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

        target = None
        if self.target:
            if self.target.__class__.__name__ == "list":
                target = ','.join(self.target)
            # Target can be "adaptor" in the SDK but written "adapter" in the GUI
            target = target.replace("adapter", "adaptor")

        redundancy_pair_type = "none" if self.redundancy_type == "no-redundancy" else self.redundancy_type
        mo_vnic_lan_conn_temp = VnicLanConnTempl(parent_mo_or_dn=parent_mo, switch_id=self.fabric.upper(),
                                                 name=self.name, descr=self.descr, target=target,
                                                 cdn_source=self.cdn_source,
                                                 nw_ctrl_policy_name=self.network_control_policy,
                                                 admin_cdn_name=self.cdn_name,
                                                 redundancy_pair_type=redundancy_pair_type,
                                                 qos_policy_name=self.qos_policy,
                                                 peer_redundancy_templ_name=self.peer_redundancy_template,
                                                 templ_type=self.template_type, mtu=self.mtu,
                                                 ident_pool_name=self.mac_address_pool,
                                                 pin_to_group_name=self.pin_group,
                                                 stats_policy_name=self.stats_threshold_policy)

        if self.dynamic_vnic_connection_policy:
            VnicDynamicConPolicyRef(parent_mo_or_dn=mo_vnic_lan_conn_temp,
                                    con_policy_name=self.dynamic_vnic_connection_policy)
        if self.usnic_connection_policy:
            VnicUsnicConPolicyRef(parent_mo_or_dn=mo_vnic_lan_conn_temp,
                                  con_policy_name=self.usnic_connection_policy)
        if self.vmq_connection_policy:
            VnicVmqConPolicyRef(parent_mo_or_dn=mo_vnic_lan_conn_temp,
                                con_policy_name=self.vmq_connection_policy)

        # self._handle.add_mo(mo=mo_vnic_lan_conn_temp, modify_present=True)
        # if commit:
        #     if self.commit(detail=self.name) != True:
        #         return False

        if self.vlans:
            for vlan in self.vlans:
                if vlan == self.vlan_native:
                    # Avoid an issue when the native VLAN is written in the VLANS section and VLAN Native parameter
                    continue
                VnicEtherIf(parent_mo_or_dn=mo_vnic_lan_conn_temp, name=vlan, default_net="no")
        if self.vlan_native:
            VnicEtherIf(parent_mo_or_dn=mo_vnic_lan_conn_temp, name=self.vlan_native, default_net="yes")
        if self.vlan_groups:
            for vlan in self.vlan_groups:
                FabricNetGroupRef(parent_mo_or_dn=mo_vnic_lan_conn_temp, name=vlan)

        self._handle.add_mo(mo=mo_vnic_lan_conn_temp, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
