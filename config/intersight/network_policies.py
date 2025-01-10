# !/usr/bin/env python

""" network_policies.py: Easy UCS Deployment Tool """
from config.intersight.object import IntersightConfigObject
from config.intersight.pools import IntersightMacPool, IntersightIqnPool
from config.intersight.pools import IntersightWwnnPool, IntersightWwpnPool
from config.intersight.server_policies import (IntersightEthernetAdapterPolicy, IntersightEthernetNetworkControlPolicy,
                                               IntersightEthernetNetworkGroupPolicy, IntersightEthernetNetworkPolicy,
                                               IntersightEthernetQosPolicy, IntersightFcZonePolicy,
                                               IntersightFibreChannelAdapterPolicy, IntersightFibreChannelNetworkPolicy,
                                               IntersightFibreChannelQosPolicy, IntersightIscsiBootPolicy)


class IntersightGenericVnic:
    UCS_TO_INTERSIGHT_POLICY_MAPPING_TABLE = {
        "adapter_policy": "ethernet_adapter_policy",
        "network_control_policy": "ethernet_network_control_policy",
        "qos_policy": "ethernet_qos_policy"
    }
    UCS_TO_INTERSIGHT_POOL_MAPPING_TABLE = {
        "mac_address_pool": IntersightMacPool,
        # IQN Pool from Global Identifier
        "iscsi_iqn_pool_name": IntersightIqnPool,
        # IQN Pool from Individual iSCSI vNIC
        "iqn_pool": IntersightIqnPool
    }


class IntersightVnic(dict, IntersightGenericVnic):
    def __init__(self, *args, **kwargs):
        super(IntersightVnic, self).__init__(*args, **kwargs)
        self['_CONFIG_NAME'] = self.get('_CONFIG_NAME', 'vNIC')


class IntersightVnicTemplate(IntersightConfigObject, IntersightGenericVnic):
    _CONFIG_NAME = "vNIC Templates"
    _CONFIG_SECTION_NAME = "vnic_templates"
    _INTERSIGHT_SDK_OBJECT_NAME = "vnic.VnicTemplate"
    _POLICY_MAPPING_TABLE = {
        "ethernet_adapter_policy": IntersightEthernetAdapterPolicy,
        "ethernet_network_control_policy": IntersightEthernetNetworkControlPolicy,
        "ethernet_network_group_policy": IntersightEthernetNetworkGroupPolicy,
        "ethernet_network_policy": IntersightEthernetNetworkPolicy,
        "ethernet_qos_policy": IntersightEthernetQosPolicy,
        "iscsi_boot_policy": IntersightIscsiBootPolicy,
        "mac_address_pool": IntersightMacPool,
        "usnic_settings": {
            "usnic_adapter_policy": IntersightEthernetAdapterPolicy
        },
        "vmq_settings": {
            "vmmq_adapter_policy": IntersightEthernetAdapterPolicy
        }
    }

    def __init__(self, parent=None, vnic_template=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=vnic_template)

        self.cdn_source = None
        self.cdn_value = None
        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.enable_failover = self.get_attribute(attribute_name="failover_enabled",
                                                  attribute_secondary_name="enable_failover")
        self.enable_override = self.get_attribute(attribute_name="enable_override")
        self.ethernet_adapter_policy = None
        self.ethernet_network_control_policy = None
        self.ethernet_network_group_policy = None
        self.ethernet_qos_policy = None
        self.iscsi_boot_policy = None
        self.mac_address_pool = None
        self.name = self.get_attribute(attribute_name="name")
        self.pin_group_name = None
        self.sriov_settings = None
        self.switch_id = self.get_attribute(attribute_name="switch_id")
        self.usnic_settings = None
        self.vmq_settings = None

        if self._config.load_from == "live":
            # Fetch Consistent Device Naming (CDN)
            if getattr(self._object, "cdn", None):
                self.cdn_source = self._object.cdn.source
                self.cdn_value = self._object.cdn.value
            # Fetch MAC Address Pool
            if getattr(self._object, "mac_pool", None):
                mac_pool = self._get_policy_name(policy=self._object.mac_pool)
                if mac_pool:
                    self.mac_address_pool = mac_pool
            # Fetch Ethernet Network Group Policy
            if getattr(self._object, "fabric_eth_network_group_policy", None):
                if len(self._object.fabric_eth_network_group_policy) == 1:
                    fabric_eth_network_group_policy = self._get_policy_name(
                        policy=self._object.fabric_eth_network_group_policy[0])
                    if fabric_eth_network_group_policy:
                        self.ethernet_network_group_policy = fabric_eth_network_group_policy
                else:
                    self.logger(level="error", message="Multiple Ethernet Network Group Policies " +
                                                               "assigned to vNIC " + self._object.name)
            # Fetch Ethernet Network Control Policy
            if getattr(self._object, "fabric_eth_network_control_policy", None):
                fabric_eth_network_control_policy = \
                    self._get_policy_name(policy=self._object.fabric_eth_network_control_policy)
                if fabric_eth_network_control_policy:
                    self.ethernet_network_control_policy = fabric_eth_network_control_policy
            # Fetch Ethernet Qos Policy
            if getattr(self._object, "eth_qos_policy", None):
                eth_qos_policy = self._get_policy_name(policy=self._object.eth_qos_policy)
                if eth_qos_policy:
                    self.ethernet_qos_policy = eth_qos_policy
            # Fetch Ethernet Adapter Policy
            if getattr(self._object, "eth_adapter_policy", None):
                eth_adapter_policy = self._get_policy_name(policy=self._object.eth_adapter_policy)
                if eth_adapter_policy:
                    self.ethernet_adapter_policy = eth_adapter_policy
            # Fetch iSCSI Boot Policy
            if getattr(self._object, "iscsi_boot_policy", None):
                iscsi_boot_policy = self._get_policy_name(policy=self._object.iscsi_boot_policy)
                if iscsi_boot_policy:
                    self.iscsi_boot_policy = iscsi_boot_policy
            if getattr(self._object, "pin_group_name", None):
                self.pin_group_name = self._object.pin_group_name if self._object.pin_group_name else None
            # Fetch usNIC connection settings
            if getattr(self._object, "usnic_settings", None):
                if self._object.usnic_settings.count > 0:
                    self.usnic_settings = {
                        "number_of_usnics": self._object.usnic_settings.count
                    }
                    if self._object.usnic_settings.usnic_adapter_policy:
                        # usNIC Settings is not a reference object, rather it's a complex type in the
                        # intersight backend. Which means there is no Moid or Name attributes in
                        # usNIC Settings. So to fetch usNIC Adapter Policy we iterate over the fetched
                        # Eth Adapter Policy SDK objects and find the relevant object.
                        for vnic_eth_adapter_policy in self._config.sdk_objects["vnic_eth_adapter_policy"]:
                            if self._object.usnic_settings.usnic_adapter_policy == \
                                    vnic_eth_adapter_policy.moid:
                                self.usnic_settings = {
                                    "usnic_adapter_policy": self._get_policy_name(
                                        policy=vnic_eth_adapter_policy)
                                }
                                break
            # Fetch VMQ connection settings
            if getattr(self._object, "vmq_settings", None):
                if self._object.vmq_settings.enabled:
                    self.vmq_settings = {
                        "enable_virtual_machine_multi_queue": self._object.vmq_settings.multi_queue_support
                    }
                    if not self._object.vmq_settings.multi_queue_support:
                        self.vmq_settings = {
                            "number_of_interrupts": self._object.vmq_settings.num_interrupts,
                            "number_of_virtual_machine_queues": self._object.vmq_settings.num_vmqs
                        }
                    else:
                        self.vmq_settings = {
                            "number_of_sub_vnics": self._object.vmq_settings.num_sub_vnics
                        }
                        # VMQ Settings is not a reference object, rather it's a complex type in the
                        # intersight backend. Which means there is no Moid or Name attributes in
                        # VMQ Settings. So to fetch VMQ Adapter Policy we iterate over the fetched
                        # Eth Adapter Policy SDK objects and find the relevant object.
                        for vmmq_adapter_policy in self._config.sdk_objects["vnic_eth_adapter_policy"]:
                            if self._object.vmq_settings.vmmq_adapter_policy == vmmq_adapter_policy.moid:
                                self.vmq_settings = {
                                    "vmmq_adapter_policy": self._get_policy_name(
                                    policy=vmmq_adapter_policy)
                                }
                                break
            # Fetch SR-IOV connection settings
            if getattr(self._object, "sriov_settings", None):
                if self._object.sriov_settings.enabled:
                    self.sriov_settings = {
                        "number_of_vfs": self._object.sriov_settings.vf_count,
                        "receive_queue_count_per_vf": self._object.sriov_settings.rx_count_per_vf,
                        "transmit_queue_count_per_vf": self._object.sriov_settings.tx_count_per_vf,
                        "completion_queue_count_per_vf": self._object.sriov_settings.comp_count_per_vf,
                        "interrupt_count_per_vf": self._object.sriov_settings.int_count_per_vf
                    }

        elif self._config.load_from == "file":
            for attribute in ["cdn_source", "cdn_value", "ethernet_adapter_policy", "ethernet_network_control_policy",
                              "ethernet_network_group_policy", "ethernet_qos_policy", "iscsi_boot_policy",
                              "mac_address_pool", "sriov_settings", "usnic_settings", "vmq_settings"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

        self.clean_object()

    def clean_object(self):
        # We use this to make sure all options of a vnic settings are set to None if they are not present
        if self.sriov_settings:
            for attribute in ["completion_queue_count_per_vf", "interrupt_count_per_vf", "number_of_vfs",
                              "receive_queue_count_per_vf", "transmit_queue_count_per_vf"]:
                if attribute not in self.sriov_settings.keys():
                    self.sriov_settings[attribute] = None

        if self.usnic_settings:
            for attribute in ["class_of_service", "number_of_usnics", "usnic_adapter_policy"]:
                if attribute not in self.usnic_settings.keys():
                    self.usnic_settings[attribute] = None

        if self.vmq_settings:
            for attribute in ["enable_virtual_machine_multi_queue", "number_of_interrupts",
                              "number_of_sub_vnics", "number_of_virtual_machine_queues",
                              "vmmq_adapter_policy"]:
                if attribute not in self.vmq_settings.keys():
                    self.vmq_settings[attribute] = None

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.vnic_vnic_template import VnicVnicTemplate

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": self.get_parent_org_relationship()
        }
        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()
        if self.enable_override is not None:
            kwargs["enable_override"] = self.enable_override
        if self.enable_failover is not None:
            kwargs["failover_enabled"] = self.enable_failover
        if self.pin_group_name is not None:
            kwargs["pin_group_name"] = self.pin_group_name
        if self.switch_id is not None:
            kwargs["switch_id"] = self.switch_id

        # Handling the CDN settings of the vNIC Template
        from intersight.model.vnic_cdn import VnicCdn
        kwargs_cdn = {
            "object_type": "vnic.Cdn",
            "class_id": "vnic.Cdn"
        }
        if self.cdn_source:
            kwargs_cdn["source"] = self.cdn_source
        if self.cdn_value is not None:
            kwargs_cdn["value"] = self.cdn_value
        # We only add the CDN Settings if at least one attribute is set
        if self.cdn_source or self.cdn_value:
            kwargs["cdn"] = VnicCdn(**kwargs_cdn)
        # Handling the policies attachments of the vNIC Template
        if self.ethernet_adapter_policy is not None:
            # We need to identify the Ethernet Adapter Policy object reference
            eth_adapter_policy = self.get_live_object(
                object_name=self.ethernet_adapter_policy,
                object_type="vnic.EthAdapterPolicy"
            )
            if eth_adapter_policy:
                kwargs["eth_adapter_policy"] = eth_adapter_policy
            else:
                self._config.push_summary_manager.add_object_status(
                    obj=self, obj_detail=f"Attaching Eth Adapter Policy '{self.ethernet_adapter_policy}' "
                                         f"to - vNIC Template - {str(self.name)}",
                    obj_type="vnic.EthIf", status="failed",
                    message=f"Failed to find Eth Adapter Policy '{self.ethernet_adapter_policy}'"
                )

        if self.ethernet_network_control_policy is not None:
            # We need to identify the Ethernet Network Control Policy object reference
            eth_nw_ctrl_policy = self.get_live_object(
                object_name=self.ethernet_network_control_policy,
                object_type="fabric.EthNetworkControlPolicy"
            )
            if eth_nw_ctrl_policy:
                kwargs["fabric_eth_network_control_policy"] = eth_nw_ctrl_policy
            else:
                self._config.push_summary_manager.add_object_status(
                    obj=self, obj_detail=f"Attaching Eth Network Control Policy "
                                         f"'{self.ethernet_network_control_policy}' to - vNIC Template - "
                                         f"{str(self.name)}",
                    obj_type="vnic.EthIf", status="failed",
                    message=f"Failed to find Eth Network Control Policy "
                            f"'{self.ethernet_network_control_policy}'"
                )

        if self.ethernet_network_group_policy is not None:
            # We need to identify the Ethernet Network Group Policy object reference
            eth_nw_grp_policy = self.get_live_object(
                object_name=self.ethernet_network_group_policy,
                object_type="fabric.EthNetworkGroupPolicy"
            )
            if eth_nw_grp_policy:
                kwargs["fabric_eth_network_group_policy"] = [eth_nw_grp_policy]
            else:
                self._config.push_summary_manager.add_object_status(
                    obj=self, obj_detail=f"Attaching Eth Network Group Policy "
                                         f"'{self.ethernet_network_group_policy}' to vNIC Template - "
                                         f"{str(self.name)}",
                    obj_type="vnic.EthIf", status="failed",
                    message=f"Failed to find Eth Network Group Policy '{self.ethernet_network_group_policy}'"
                )

        if self.ethernet_qos_policy is not None:
            # We need to identify the Ethernet QoS Policy object reference
            eth_qos_policy = self.get_live_object(
                object_name=self.ethernet_qos_policy,
                object_type="vnic.EthQosPolicy"
            )
            if eth_qos_policy:
                kwargs["eth_qos_policy"] = eth_qos_policy
            else:
                self._config.push_summary_manager.add_object_status(
                    obj=self, obj_detail=f"Attaching Eth QOS Policy '{self.ethernet_qos_policy}' "
                                         f"to vNIC Template - {str(self.name)}",
                    obj_type="vnic.EthIf", status="failed",
                    message=f"Failed to find Eth OQS Policy '{self.ethernet_qos_policy}'"
                )

        if self.iscsi_boot_policy is not None:
            # We need to identify the iSCSI Boot Policy object reference
            iscsi_boot_policy = self.get_live_object(
                object_name=self.iscsi_boot_policy,
                object_type="vnic.IscsiBootPolicy"
            )
            if iscsi_boot_policy:
                kwargs["iscsi_boot_policy"] = iscsi_boot_policy
            else:
                self._config.push_summary_manager.add_object_status(
                    obj=self, obj_detail=f"Attaching iSCSI Boot Policy '{self.iscsi_boot_policy}' "
                                         f"to vNIC Template - {str(self.name)}",
                    obj_type="vnic.EthIf", status="failed",
                    message=f"Failed to find iSCSI Boot Policy '{self.iscsi_boot_policy}'"
                )

        if self.mac_address_pool is not None:
            # We need to identify the MAC Pool object reference
            mac_pool = self.get_live_object(
                object_name=self.mac_address_pool,
                object_type="macpool.Pool"
            )
            if mac_pool:
                kwargs["mac_pool"] = mac_pool
            else:
                self._config.push_summary_manager.add_object_status(
                    obj=self, obj_detail=f"Attaching MAC Pool '{self.mac_address_pool}' to vNIC Template - "
                                         f"{str(self.name)}",
                    obj_type="vnic.EthIf", status="failed",
                    message=f"Failed to find MAC Pool '{self.mac_address_pool}'"
                )

        # Handling the usNIC Settings of the vNIC Template
        if self.usnic_settings is not None:
            from intersight.model.vnic_usnic_settings import VnicUsnicSettings
            kwargs_usnic = {
                "object_type": "vnic.UsnicSettings",
                "class_id": "vnic.UsnicSettings"
            }
            if self.usnic_settings.get("number_of_usnics") is not None:
                kwargs_usnic["count"] = self.usnic_settings["number_of_usnics"]
            if self.usnic_settings.get("usnic_adapter_policy") is not None:
                eth_adapter_policy = self.get_live_object(
                    object_name=self.usnic_settings.get("usnic_adapter_policy"),
                    object_type="vnic.EthAdapterPolicy"
                )
                if eth_adapter_policy:
                    kwargs_usnic["usnic_adapter_policy"] = eth_adapter_policy.moid
                else:
                    self._config.push_summary_manager.add_object_status(
                        obj=self,
                        obj_detail=f"Attaching Eth Adapter Policy "
                                   f"'{self.usnic_settings['usnic_adapter_policy']}' "
                                   f"to - vNIC Template - {str(self.name)} - usNIC Settings",
                        obj_type="vnic.EthIf", status="failed",
                        message=f"Failed to find Eth Adapter Policy "
                                f"'{self.usnic_settings['usnic_adapter_policy']}'"
                    )
            kwargs["usnic_settings"] = VnicUsnicSettings(**kwargs_usnic)

        # Handling the VMQ Settings of the vNIC
        if self.vmq_settings is not None:
            from intersight.model.vnic_vmq_settings import VnicVmqSettings
            kwargs_vmq = {
                "object_type": "vnic.VmqSettings",
                "class_id": "vnic.VmqSettings",
                "enabled": True
            }
            if self.vmq_settings.get("enable_virtual_machine_multi_queue") is not None:
                kwargs_vmq["multi_queue_support"] = self.vmq_settings["enable_virtual_machine_multi_queue"]
            if self.vmq_settings.get("number_of_sub_vnics") is not None:
                kwargs_vmq["num_sub_vnics"] = self.vmq_settings["number_of_sub_vnics"]
            if self.vmq_settings.get("vmmq_adapter_policy") is not None:
                eth_adapter_policy = self.get_live_object(
                    object_name=self.vmq_settings.get("vmmq_adapter_policy"),
                    object_type="vnic.EthAdapterPolicy"
                )
                if eth_adapter_policy:
                    kwargs_vmq["vmmq_adapter_policy"] = eth_adapter_policy.moid
                else:
                    self._config.push_summary_manager.add_object_status(
                        obj=self,
                        obj_detail=f"Attaching Eth Adapter Policy "
                                   f"'{self.vmq_settings['vmmq_adapter_policy']}' "
                                   f"to - vNIC Template - {str(self.name)} - VMQ Settings",
                        obj_type="vnic.EthIf", status="failed",
                        message=f"Failed to find Eth Adapter Policy "
                                f"'{self.vmq_settings['vmmq_adapter_policy']}'"
                    )
            if self.vmq_settings.get("number_of_interrupts") is not None:
                kwargs_vmq["num_interrupts"] = self.vmq_settings["number_of_interrupts"]
            if self.vmq_settings.get("number_of_virtual_machine_queues") is not None:
                kwargs_vmq["num_vmqs"] = self.vmq_settings["number_of_virtual_machine_queues"]
            kwargs["vmq_settings"] = VnicVmqSettings(**kwargs_vmq)

        # Handling the SRIOV Settings of the vNIC Template
        if self.sriov_settings is not None:
            from intersight.model.vnic_sriov_settings import VnicSriovSettings
            kwargs_sriov = {
                "object_type": "vnic.SriovSettings",
                "class_id": "vnic.SriovSettings",
                "enabled": True
            }
            if self.sriov_settings.get("number_of_vfs") is not None:
                kwargs_sriov["vf_count"] = self.sriov_settings["number_of_vfs"]
            if self.sriov_settings.get("receive_queue_count_per_vf") is not None:
                kwargs_sriov["rx_count_per_vf"] = self.sriov_settings["receive_queue_count_per_vf"]
            if self.sriov_settings.get("transmit_queue_count_per_vf") is not None:
                kwargs_sriov["tx_count_per_vf"] = self.sriov_settings["transmit_queue_count_per_vf"]
            if self.sriov_settings.get("completion_queue_count_per_vf") is not None:
                kwargs_sriov["comp_count_per_vf"] = self.sriov_settings["completion_queue_count_per_vf"]
            if self.sriov_settings.get("interrupt_count_per_vf") is not None:
                kwargs_sriov["int_count_per_vf"] = self.sriov_settings["interrupt_count_per_vf"]
            kwargs["sriov_settings"] = VnicSriovSettings(**kwargs_sriov)

        vnic_template_payload = VnicVnicTemplate(**kwargs)

        if not self.commit(object_type="vnic.VnicTemplate", payload=vnic_template_payload,
                           detail=self.name + " - vNIC Template" + str(self.name),
                           key_attributes=["name"]):
            return False
        return True


class IntersightGenericVhba:
    UCS_TO_INTERSIGHT_POLICY_MAPPING_TABLE = {
        "adapter_policy": "fibre_channel_adapter_policy",
        "qos_policy": "fibre_channel_qos_policy"
    }
    UCS_TO_INTERSIGHT_POOL_MAPPING_TABLE = {
        "wwnn_pool": IntersightWwnnPool,
        "wwpn_pool": IntersightWwpnPool
    }


class IntersightVhba(dict, IntersightGenericVhba):
    def __init__(self, *args, **kwargs):
        super(IntersightVhba, self).__init__(*args, **kwargs)
        self['_CONFIG_NAME'] = self.get('_CONFIG_NAME', 'vHBA')


class IntersightVhbaTemplate(IntersightConfigObject, IntersightGenericVhba):
    _CONFIG_NAME = "vHBA Templates"
    _CONFIG_SECTION_NAME = "vhba_templates"
    _INTERSIGHT_SDK_OBJECT_NAME = "vnic.VhbaTemplate"
    _POLICY_MAPPING_TABLE = {
        "fc_zone_policies": [IntersightFcZonePolicy],
        "fibre_channel_adapter_policy": IntersightFibreChannelAdapterPolicy,
        "fibre_channel_network_policy": IntersightFibreChannelNetworkPolicy,
        "fibre_channel_qos_policy": IntersightFibreChannelQosPolicy,
        "wwpn_pool": IntersightWwpnPool
    }

    def __init__(self, parent=None, vhba_template=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=vhba_template)

        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.enable_override = self.get_attribute(attribute_name="enable_override")
        self.fc_zone_policies = None
        self.fibre_channel_adapter_policy = None
        self.fibre_channel_network_policy = None
        self.fibre_channel_qos_policy = None
        self.name = self.get_attribute(attribute_name="name")
        self.persistent_lun_bindings = self.get_attribute(attribute_name="persistent_bindings",
                                                          attribute_secondary_name="persistent_lun_bindings")
        self.pin_group_name = None
        self.switch_id = self.get_attribute(attribute_name="switch_id")
        self.vhba_type = self.get_attribute(attribute_name="type")
        self.wwpn_pool = None

        if self._config.load_from == "live":

            # Fetch Fibre Channel Adapter Policy
            if getattr(self._object, "fc_adapter_policy", None):
                fc_adapter_policy = self._get_policy_name(policy=self._object.fc_adapter_policy)
                if fc_adapter_policy:
                    self.fibre_channel_adapter_policy = fc_adapter_policy
            # Fetch Fibre Channel Network Policy
            if getattr(self._object, "fc_network_policy", None):
                fc_network_policy = self._get_policy_name(policy=self._object.fc_network_policy)
                if fc_network_policy:
                    self.fibre_channel_network_policy = fc_network_policy
            # Fetch Fibre Channel Qos Policy
            if getattr(self._object, "fc_qos_policy", None):
                fc_qos_policy = self._get_policy_name(policy=self._object.fc_qos_policy)
                if fc_qos_policy:
                    self.fibre_channel_qos_policy = fc_qos_policy
            # Fetch Fibre Channel Zone Policies
            if getattr(self._object, "fc_zone_policies", None):
                fc_zone_policy_list = []
                for fc_zone_policy_ref in self._object.fc_zone_policies:
                    fc_zone_policy = self._get_policy_name(policy=fc_zone_policy_ref)
                    if fc_zone_policy:
                        fc_zone_policy_list.append(fc_zone_policy)
                self.fc_zone_policies = fc_zone_policy_list
            if getattr(self._object, "pin_group_name", None):
                self.pin_group_name = self._object.pin_group_name if self._object.pin_group_name else None
            # Fetch the WWPN Address Pool
            if getattr(self._object, "wwpn_pool", None):
                wwpn_pool = self._get_policy_name(policy=self._object.wwpn_pool)
                if wwpn_pool:
                    self.wwpn_pool = wwpn_pool
        elif self._config.load_from == "file":
            for attribute in ["fc_zone_policies", "fibre_channel_adapter_policy", "fibre_channel_network_policy",
                              "fibre_channel_qos_policy", "pin_group_name", "wwpn_pool"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.vnic_vhba_template import VnicVhbaTemplate

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": self.get_parent_org_relationship()
        }
        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()
        if self.enable_override is not None:
            kwargs["enable_override"] = self.enable_override
        if self.pin_group_name is not None:
            kwargs["pin_group_name"] = self.pin_group_name
        if self.switch_id is not None:
            kwargs["switch_id"] = self.switch_id
        if self.vhba_type is not None:
            kwargs["type"] = self.vhba_type
        if self.persistent_lun_bindings is not None:
            kwargs["persistent_bindings"] = self.persistent_lun_bindings

        if self.wwpn_pool is not None:
            # We need to identify the WWPN Pool object reference
            # Since WWPN & WWNN share the same object type, we need to specify a query filter
            if "/" in self.wwpn_pool:
                wwpn_pool_name = self.wwpn_pool.split("/")[1]
                wwpn_pool_org_ref = self.get_org_relationship(org_name=self.wwpn_pool.split("/")[0])
                wwpn_pool = None
                if wwpn_pool_org_ref:
                    wwpn_pool = self.get_live_object(
                        object_name=wwpn_pool_name,
                        object_type="fcpool.Pool",
                        query_filter="Name eq '" + wwpn_pool_name + "' and Organization/Moid eq '" +
                                     wwpn_pool_org_ref.moid + "' and PoolPurpose eq 'WWPN'"
                    )
            else:
                wwpn_pool = self.get_live_object(
                    object_name=self.wwpn_pool,
                    object_type="fcpool.Pool",
                    query_filter="Name eq '" + self.wwpn_pool + "' and Organization/Moid eq '" +
                                 self.get_parent_org_relationship().moid + "' and PoolPurpose eq 'WWPN'"
                )
            if wwpn_pool:
                kwargs["wwpn_pool"] = wwpn_pool
            else:
                self._config.push_summary_manager.add_object_status(
                    obj=self, obj_detail=f"Attaching WWPN Pool '{self.wwpn_pool}' to vHBA Template - "
                                         f"{str(self.name)}",
                    obj_type="vnic.FcIf", status="failed",
                    message=f"Failed to find WWPN Pool '{self.wwpn_pool}'"
                )

        # Handling the policies attachments of the vHBA Template
        if self.fc_zone_policies is not None:
            # We need to identify the FC Zone Policy object reference
            fc_zone_policy_list = []
            for fc_zone_policy in self.fc_zone_policies:
                live_fc_zone_policy = self.get_live_object(
                    object_name=fc_zone_policy,
                    object_type="fabric.FcZonePolicy"
                )
                if live_fc_zone_policy:
                    fc_zone_policy_list.append(live_fc_zone_policy)
                else:
                    self._config.push_summary_manager.add_object_status(
                        obj=self, obj_detail=f"Attaching FC Zone Policy '{fc_zone_policy}' to vHBA Template - "
                                             f"{str(self.name)}",
                        obj_type="vnic.FcIf", status="failed",
                        message=f"Failed to find FC Zone Policy '{fc_zone_policy}'"
                    )
            kwargs["fc_zone_policies"] = fc_zone_policy_list

        if self.fibre_channel_adapter_policy is not None:
            # We need to identify the Fibre Channel Adapter Policy object reference
            fc_adapter_policy = self.get_live_object(
                object_name=self.fibre_channel_adapter_policy,
                object_type="vnic.FcAdapterPolicy"
            )
            if fc_adapter_policy:
                kwargs["fc_adapter_policy"] = fc_adapter_policy
            else:
                self._config.push_summary_manager.add_object_status(
                    obj=self, obj_detail=f"Attaching FC Adapter Policy '{self.fibre_channel_adapter_policy}'"
                                         f" to vHBA Template - {str(self.name)}",
                    obj_type="vnic.FcIf", status="failed",
                    message=f"Failed to find FC Adapter Policy '{self.fibre_channel_adapter_policy}'"
                )

        if self.fibre_channel_network_policy is not None:
            # We need to identify the Fibre Channel Network Policy object reference
            fc_nw_policy = self.get_live_object(
                object_name=self.fibre_channel_network_policy,
                object_type="vnic.FcNetworkPolicy"
            )
            if fc_nw_policy:
                kwargs["fc_network_policy"] = fc_nw_policy
            else:
                self._config.push_summary_manager.add_object_status(
                    obj=self, obj_detail=f"Attaching FC Network Policy '{self.fibre_channel_network_policy}'"
                                         f" to vHBA Template - {str(self.name)}",
                    obj_type="vnic.FcIf", status="failed",
                    message=f"Failed to find FC Network Policy '{self.fibre_channel_network_policy}'"
                )

        if self.fibre_channel_qos_policy is not None:
            # We need to identify the Fibre Channel QoS Policy object reference
            fc_qos_policy = self.get_live_object(
                object_name=self.fibre_channel_qos_policy,
                object_type="vnic.FcQosPolicy"
            )
            if fc_qos_policy:
                kwargs["fc_qos_policy"] = fc_qos_policy
            else:
                self._config.push_summary_manager.add_object_status(
                    obj=self, obj_detail=f"Attaching FC QOS Policy '{self.fibre_channel_qos_policy}' to "
                                         f"vHBA Template - {str(self.name)}",
                    obj_type="vnic.FcIf", status="failed",
                    message=f"Failed to find FC QOS Policy '{self.fibre_channel_qos_policy}'"
                )

        vhba_template_payload = VnicVhbaTemplate(**kwargs)
        if not self.commit(object_type="vnic.VhbaTemplate", payload=vhba_template_payload,
                           detail=self.name + " - vHBA Template" + str(self.name),
                           key_attributes=["name"]):
            return False
        return True

