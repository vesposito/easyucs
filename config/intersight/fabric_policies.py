# coding: utf-8
# !/usr/bin/env python

""" fabric_policies.py: Easy UCS Deployment Tool """
import datetime
from packaging.version import Version
from common import is_mac_address_valid, password_generator
from config.intersight.object import IntersightConfigObject
from config.intersight.server_policies import IntersightNetworkConnectivityPolicy, IntersightNtpPolicy, \
    IntersightSnmpPolicy, IntersightSyslogPolicy, IntersightEthernetNetworkGroupPolicy, \
    IntersightEthernetNetworkControlPolicy

class IntersightAuditDPolicy(IntersightConfigObject):
    _CONFIG_NAME = "AuditD Policy"
    _CONFIG_SECTION_NAME = "auditd_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "auditd.Policy"

    def __init__(self, parent=None, auditd_policy=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=auditd_policy)

        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.name = self.get_attribute(attribute_name="name")
        self.admin_state = self.get_attribute(attribute_name="admin_state")
        self.minimum_severity_to_report = self.get_attribute(
                attribute_name="auditd_log_level", attribute_secondary_name="minimum_severity_to_report")
        self.log_monitor = self.get_attribute(attribute_name="log_monitor")

        if self._config.load_from == "live":
            self.minimum_severity_to_report = self._get_log_level(self.get_attribute(
                attribute_name="auditd_log_level"), mode="file")             
            if self.log_monitor:
                self.log_monitor = self._get_log_monitor(self.log_monitor, mode="live")

    def _get_log_level(self, level, mode="live"):
        log_levels = {
            "notifications": "Notification",
            "emergencies": "Emergency",
            "alerts": "Alert",
            "critical": "Critical",
            "errors": "Error",
            "warnings": "Warning",
            "information": "Information",
            "debugging": "Debugging"
        }
        if mode == "live":
            return next((live for live, file in log_levels.items() if file == level), "notifications")
        elif mode == "file":
            return log_levels.get(level)

    def _get_log_monitor(self, values, mode="file"):
        log_monitor_fields = [
            "all",
            "auth_log_files",
            "cron_files",
            "dns_client_files",
            "docker",
            "kernel_module_mgmt",
            "process_audit",
            "system_log_files",
            "system_login_reboot",
            "system_software",
            "system_time_change",
            "user_group_config_files",
            "user_privilege_mgmt"
        ]

        if mode == "file":
            return {
                field: values.get(field, "no")
                for field in log_monitor_fields
            }
        elif mode == "live":
            return {
                field: getattr(values, field, "no")
                for field in log_monitor_fields
            }
        return values

    def _default_log_monitor(self):
        return {
            "all": "no",
            "auth_log_files": "no",
            "cron_files": "yes",
            "dns_client_files": "no",
            "docker": "no",
            "kernel_module_mgmt": "no",
            "process_audit": "no",
            "system_log_files": "no",
            "system_login_reboot": "no",
            "system_software": "no",
            "system_time_change": "no",
            "user_group_config_files": "no",
            "user_privilege_mgmt": "no"
        }

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.auditd_policy import AuditdPolicy

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        curr_version = None
        if self._device.is_appliance and self._device.version:
            parts = self._device.version.split("-")
            if len(parts) >= 2:
                curr_version = parts[0] + "-" + parts[1].split(".")[0]

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
        if self.admin_state is not None:
            kwargs["admin_state"] = self.admin_state
        if self.minimum_severity_to_report is not None:
            kwargs["auditd_log_level"] = self._get_log_level(self.minimum_severity_to_report)
        if self.log_monitor is not None:    
            if (self._device.is_appliance and curr_version is not None and Version(curr_version) < Version("1.1.8-0")):
                self.logger(
                    level="warning",
                    message=(
                        f"Skipping 'log_monitor' for AuditD Policy '{self.name}'. "
                        f"Intersight Appliance version {self._device.version} "
                        f"does not support this attribute."
                    )
                )
            else:
                kwargs["log_monitor"] = self._get_log_monitor(self.log_monitor)
        elif not (self._device.is_appliance and curr_version is not None and Version(curr_version) < Version("1.1.8-0")):
            kwargs["log_monitor"] = self._default_log_monitor()

        auditd_policy = AuditdPolicy(**kwargs)

        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=auditd_policy, detail=self.name):
            return False

        return True


class IntersightFabricFlowControlPolicy(IntersightConfigObject):
    _CONFIG_NAME = "Flow Control Policy"
    _CONFIG_SECTION_NAME = "flow_control_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "fabric.FlowControlPolicy"

    def __init__(self, parent=None, fabric_flow_control_policy=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=fabric_flow_control_policy)

        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.name = self.get_attribute(attribute_name="name")
        self.priority = self.get_attribute(attribute_name="priority_flow_control_mode",
                                           attribute_secondary_name="priority")
        self.receive = self.get_attribute(attribute_name="receive_direction", attribute_secondary_name="receive")
        self.send = self.get_attribute(attribute_name="send_direction", attribute_secondary_name="send")

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.fabric_flow_control_policy import FabricFlowControlPolicy

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
        if self.priority is not None:
            kwargs["priority_flow_control_mode"] = self.priority
        if self.receive is not None:
            kwargs["receive_direction"] = self.receive
        if self.send is not None:
            kwargs["send_direction"] = self.send

        fabric_flow_control_policy = FabricFlowControlPolicy(**kwargs)

        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=fabric_flow_control_policy,
                           detail=self.name):
            return False

        return True


class IntersightFabricLinkAggregationPolicy(IntersightConfigObject):
    _CONFIG_NAME = "Link Aggregation Policy"
    _CONFIG_SECTION_NAME = "link_aggregation_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "fabric.LinkAggregationPolicy"

    def __init__(self, parent=None, fabric_link_aggregation_policy=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=fabric_link_aggregation_policy)

        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.lacp_rate = self.get_attribute(attribute_name="lacp_rate")
        self.name = self.get_attribute(attribute_name="name")
        self.suspend_individual = self.get_attribute(attribute_name="suspend_individual")

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.fabric_link_aggregation_policy import FabricLinkAggregationPolicy

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
        if self.lacp_rate is not None:
            kwargs["lacp_rate"] = self.lacp_rate
        if self.suspend_individual is not None:
            kwargs["suspend_individual"] = self.suspend_individual

        fabric_link_aggregation_policy = FabricLinkAggregationPolicy(**kwargs)

        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=fabric_link_aggregation_policy,
                           detail=self.name):
            return False

        return True


class IntersightFabricLinkControlPolicy(IntersightConfigObject):
    _CONFIG_NAME = "Link Control Policy"
    _CONFIG_SECTION_NAME = "link_control_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "fabric.LinkControlPolicy"

    def __init__(self, parent=None, fabric_link_control_policy=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=fabric_link_control_policy)

        self.admin_state = None
        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.mode = None
        self.name = self.get_attribute(attribute_name="name")

        if self._config.load_from == "live":
            if hasattr(self._object, "udld_settings"):
                if hasattr(self._object.udld_settings, "admin_state"):
                    self.admin_state = self._object.udld_settings.admin_state
                if hasattr(self._object.udld_settings, "mode"):
                    self.mode = self._object.udld_settings.mode

        elif self._config.load_from == "file":
            for attribute in ["admin_state", "mode"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.fabric_link_control_policy import FabricLinkControlPolicy

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

        if self.admin_state is not None or self.mode is not None:
            from intersight.model.fabric_udld_settings import FabricUdldSettings

            kwargs_udld_settings = {
                "object_type": "fabric.UdldSettings",
                "class_id": "fabric.UdldSettings"
            }
            if self.admin_state is not None:
                kwargs_udld_settings["admin_state"] = self.admin_state
            if self.mode is not None:
                if self.admin_state == "Disabled" and self.mode == "aggressive":
                    self.logger(
                        level="warning",
                        message=f"{self._CONFIG_NAME} '{self.name}': 'mode' cannot be 'aggressive' when "
                                f"'admin_state' is 'Disabled'. Using 'normal' instead."
                    )
                    kwargs_udld_settings["mode"] = "normal"
                else:
                    kwargs_udld_settings["mode"] = self.mode

            kwargs["udld_settings"] = FabricUdldSettings(**kwargs_udld_settings)

        fabric_link_control_policy = FabricLinkControlPolicy(**kwargs)

        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=fabric_link_control_policy,
                           detail=self.name):
            return False

        return True


class IntersightFabricMulticastPolicy(IntersightConfigObject):
    _CONFIG_NAME = "Multicast Policy"
    _CONFIG_SECTION_NAME = "multicast_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "fabric.MulticastPolicy"

    def __init__(self, parent=None, fabric_multicast_policy=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=fabric_multicast_policy)

        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.name = self.get_attribute(attribute_name="name")
        self.igmp_snooping_querier_state = self.get_attribute(attribute_name="querier_state",
                                                              attribute_secondary_name="igmp_snooping_querier_state")
        self.igmp_snooping_state = self.get_attribute(attribute_name="snooping_state",
                                                      attribute_secondary_name="igmp_snooping_state")
        self.querier_ip_address = self.get_attribute(attribute_name="querier_ip_address")
        self.querier_ip_address_peer = self.get_attribute(attribute_name="querier_ip_address_peer")
        self.source_ip_proxy_state = self.get_attribute(attribute_name="src_ip_proxy",
                                                        attribute_secondary_name="source_ip_proxy_state")

    def push_object(self):
        from intersight.model.fabric_multicast_policy import FabricMulticastPolicy

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
        if self.igmp_snooping_querier_state is not None:
            kwargs["querier_state"] = self.igmp_snooping_querier_state
        if self.igmp_snooping_state is not None:
            kwargs["snooping_state"] = self.igmp_snooping_state
        if self.querier_ip_address is not None:
            kwargs["querier_ip_address"] = self.querier_ip_address
        if self.querier_ip_address_peer is not None:
            kwargs["querier_ip_address_peer"] = self.querier_ip_address_peer
        if self.source_ip_proxy_state is not None:
            kwargs["src_ip_proxy"] = self.source_ip_proxy_state

        fabric_multicast_policy = FabricMulticastPolicy(**kwargs)

        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=fabric_multicast_policy,
                           detail=self.name):
            return False

        return True


class IntersightMacSecPolicy(IntersightConfigObject):
    _CONFIG_NAME = "MACsec Policy"
    _CONFIG_SECTION_NAME = "macsec_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "fabric.MacSecPolicy"

    def __init__(self, parent=None, macsec_policy=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=macsec_policy)

        self.name = self.get_attribute(attribute_name="name")
        self.cipher_suite = self.get_attribute(attribute_name="cipher_suite")
        self.confidentiality_offset = self.get_attribute(attribute_name="confidentiality_offset")
        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.include_icv_indicator = self.get_attribute(attribute_name="include_icv_indicator")
        self.key_server_priority = self.get_attribute(attribute_name="key_server_priority")
        self.replay_window_size = self.get_attribute(attribute_name="replay_window_size")
        self.sak_expiry_time = self.get_attribute(attribute_name="sak_expiry_time")
        self.security_policy = self.get_attribute(attribute_name="security_policy")

        self.eapol_configurations = None
        self.fallback_keychain = None
        self.primary_keychain = None

        if self._config.load_from == "live":
            if getattr(self._object, "mac_sec_ea_pol", None):
                eapol_configuration = {
                    "ether_type": self._object.mac_sec_ea_pol.get("ea_pol_ethertype"),
                    "mac_address": self._object.mac_sec_ea_pol.get("ea_pol_mac_address")
                }
                self.eapol_configurations = eapol_configuration
            if hasattr(self._object, "primary_key_chain"):
                self.primary_keychain = self._get_keychain(getattr(self._object, "primary_key_chain", None))
            if hasattr(self._object, "fallback_key_chain"):
                self.fallback_keychain = self._get_keychain(getattr(self._object, "fallback_key_chain", None))

        elif self._config.load_from == "file":
            for attribute in ["eapol_configurations", "fallback_keychain", "primary_keychain"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

            self.clean_object()

    def _get_keychain(self, keychain_obj):

        if keychain_obj is None:
            return None

        keychain = {
            "keychain_name": keychain_obj.get("name")
        }
        if hasattr(keychain_obj, "sec_keys") and getattr(keychain_obj, "sec_keys", None) is not None:
            keys = []
            for key in keychain_obj["sec_keys"]:
                key_dict = {
                    "id": key.get("id"),
                    "cryptographic_algorithm": key.get("cryptographic_algorithm"),
                    "key_type": key.get("key_type")
                }
                if key.get("is_octet_string_set"):
                    self.logger(level="warning",
                                message="The Secret key for the " + self._CONFIG_NAME + " '" + self.name +
                                        "' with Key Id '" + key.get("id") + "' can't be exported")

                # Check if the key is set to be always active
                # If `send_lifetime_unlimited` is True, it means the key is always active,
                # so all other lifetime-related fields are ignored.
                if key.get("send_lifetime_unlimited", None):
                    lifetime = {
                        "always_active": key["send_lifetime_unlimited"]
                    }
                    key_dict["lifetime"] = lifetime
                else:
                    # Configure lifetime configurations since the key is not always active
                    lifetime = {
                        "start_time": key.get("send_lifetime_start_time").isoformat()[:-3] + 'Z',
                        "always_active": key.get("send_lifetime_unlimited"),
                        "timezone": key.get("send_lifetime_time_zone"),
                        "infinite_lifetime": key.get("send_lifetime_infinite")
                    }
                    # If the key does not have an infinite lifetime, set the end_time and duration
                    if not key["send_lifetime_infinite"]:
                        lifetime["end_time"] = key["send_lifetime_end_time"].isoformat()[:-3] + 'Z'
                        lifetime["duration"] = key["send_lifetime_duration"]

                    key_dict["lifetime"] = lifetime

                keys.append(key_dict)

            keychain["keys"] = keys

        return keychain

    def clean_object(self):
        # We use this to make sure all options of a EAPOL Configurations are set to None if they are not present
        if self.eapol_configurations:
            for attribute in ["ether_type", "mac_address"]:
                if attribute not in self.eapol_configurations:
                    self.eapol_configurations[attribute] = None

        # Ensure all expected fields in both primary and fallback keychains are set to None if missing
        for keychain in [self.primary_keychain, self.fallback_keychain]:
            if keychain:
                if "keychain_name" not in keychain:
                    keychain["keychain_name"] = None
                if "keys" not in keychain:
                    keychain["keys"] = None
                else:
                    for key in keychain["keys"]:
                        for attribute in ["cryptographic_algorithm", "id", "secret_key", "key_type"]:
                            if attribute not in key:
                                key[attribute] = None
                        if "lifetime" not in key:
                            key["lifetime"] = None
                        else:
                            for sub_attribute in ["infinite_lifetime", "always_active", "start_time",
                                                  "end_time", "duration", "timezone"]:
                                if sub_attribute not in key["lifetime"]:
                                    key["lifetime"][sub_attribute] = None

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.fabric_mac_sec_policy import FabricMacSecPolicy

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
        if self.cipher_suite is not None:
            kwargs["cipher_suite"] = self.cipher_suite
        if self.confidentiality_offset is not None:
            kwargs["confidentiality_offset"] = self.confidentiality_offset
        if self.include_icv_indicator is not None:
            kwargs["include_icv_indicator"] = self.include_icv_indicator
        if self.key_server_priority is not None:
            kwargs["key_server_priority"] = self.key_server_priority
        if self.replay_window_size is not None:
            kwargs["replay_window_size"] = self.replay_window_size
        if self.sak_expiry_time is not None:
            kwargs["sak_expiry_time"] = self.sak_expiry_time
        if self.security_policy is not None:
            kwargs["security_policy"] = self.security_policy

        # EAPOL Configurations
        if self.eapol_configurations is not None:
            from intersight.model.fabric_mac_sec_ea_pol import FabricMacSecEaPol
            eapol_kwargs = {
                "object_type": "fabric.MacSecEaPol",
                "class_id": "fabric.MacSecEaPol",
                "ea_pol_ethertype": self.eapol_configurations["ether_type"],
                "ea_pol_mac_address": self.eapol_configurations["mac_address"]
            }
            macsec_eapol = FabricMacSecEaPol(**eapol_kwargs)
            kwargs["mac_sec_ea_pol"] = macsec_eapol
        # Primary and Secondary Keychains
        for keychain in ["primary_keychain", "fallback_keychain"]:
            from intersight.model.fabric_sec_key_chain import FabricSecKeyChain
            from intersight.model.fabric_sec_key import FabricSecKey
            if keychain == "primary_keychain":
                key_chain = self.primary_keychain
            else:
                key_chain = self.fallback_keychain
            if key_chain is not None:
                keychain_kwargs = {
                    "object_type": "fabric.SecKeyChain",
                    "class_id": "fabric.SecKeyChain",
                    "name": key_chain["keychain_name"]
                }
                if key_chain.get("keys", []):
                    keys = []
                    for key in key_chain["keys"]:
                        key_kwargs = {
                            "object_type": "fabric.SecKey",
                            "class_id": "fabric.SecKey",
                            "cryptographic_algorithm": key.get("cryptographic_algorithm"),
                            "id": key["id"]
                        }
                        if key.get("secret_key"):
                            key_kwargs["octet_string"] = key["secret_key"]
                        else:
                            self.logger(
                                level="warning",
                                message="No secret key provided for field 'octet_string' of object fabric.SecKey"
                            )
                        if key.get("key_type") is not None:
                            key_kwargs["key_type"] = key["key_type"]
                        if key.get("lifetime"):
                            if key["lifetime"].get("start_time") is not None:
                                key_kwargs["send_lifetime_start_time"] = (
                                    datetime.datetime.fromisoformat(((key["lifetime"]["start_time"]).replace('Z', ':00'))))
                            if key["lifetime"].get("time_zone") is not None:
                                key_kwargs["send_lifetime_time_zone"] = key["lifetime"]["timezone"]
                            if key["lifetime"].get("always_active") is not None:
                                key_kwargs["send_lifetime_unlimited"] = key["lifetime"]["always_active"]
                            if key["lifetime"].get("infinite_lifetime") is not None:
                                key_kwargs["send_lifetime_infinite"] = key["lifetime"]["infinite_lifetime"]
                            if key["lifetime"].get("end_time") is not None:
                                key_kwargs["send_lifetime_end_time"] = (
                                    datetime.datetime.fromisoformat(((key["lifetime"]["end_time"]).replace('Z', ':00'))))
                            if key["lifetime"].get("duration") is not None:
                                key_kwargs["send_lifetime_duration"] = key["lifetime"]["duration"]

                        keys.append(FabricSecKey(**key_kwargs))

                    keychain_kwargs["sec_keys"] = keys

                macsec_keychain = FabricSecKeyChain(**keychain_kwargs)
                if keychain == "primary_keychain":
                    kwargs["primary_key_chain"] = macsec_keychain
                else:
                    kwargs["fallback_key_chain"] = macsec_keychain

        macsec_policy = FabricMacSecPolicy(**kwargs)

        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=macsec_policy, detail=self.name):
            return False

        return True


class IntersightFabricPortPolicy(IntersightConfigObject):
    _CONFIG_NAME = "Port Policy"
    _CONFIG_SECTION_NAME = "port_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "fabric.PortPolicy"
    MAX_ENGPS_PER_LAN_UPLINK = 50
    MAX_ENGPS_PER_LAN_PORT_CHANNEL = 50
    _POLICY_MAPPING_TABLE = {
        "appliance_port_channels": [
            {
                "ethernet_network_control_policy": IntersightEthernetNetworkControlPolicy,
                "ethernet_network_group_policy": IntersightEthernetNetworkGroupPolicy
            }
        ],
        "appliance_ports": [
            {
                "ethernet_network_control_policy": IntersightEthernetNetworkControlPolicy,
                "ethernet_network_group_policy": IntersightEthernetNetworkGroupPolicy
            }
        ],
        "fcoe_port_channels": [
            {
                "link_aggregation_policy": IntersightFabricLinkAggregationPolicy,
                "link_control_policy": IntersightFabricLinkControlPolicy
            }
        ],
        "fcoe_uplink_ports": [
            {
                "link_control_policy": IntersightFabricLinkControlPolicy
            }
        ],
        "lan_port_channels": [
            {
                "ethernet_network_group_policies": [IntersightEthernetNetworkGroupPolicy],
                "ethernet_network_group_policy": IntersightEthernetNetworkGroupPolicy,  # Deprecated
                "flow_control_policy": IntersightFabricFlowControlPolicy,
                "link_aggregation_policy": IntersightFabricLinkAggregationPolicy,
                "link_control_policy": IntersightFabricLinkControlPolicy,
                "macsec_policy": IntersightMacSecPolicy
            }
        ],
        "lan_uplink_ports": [
            {
                "ethernet_network_group_policies": [IntersightEthernetNetworkGroupPolicy],
                "ethernet_network_group_policy": IntersightEthernetNetworkGroupPolicy,  # Deprecated
                "flow_control_policy": IntersightFabricFlowControlPolicy,
                "link_control_policy": IntersightFabricLinkControlPolicy,
                "macsec_policy": IntersightMacSecPolicy
            }
        ]
    }

    def __init__(self, parent=None, fabric_port_policy=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=fabric_port_policy)

        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.device_model = self.get_attribute(attribute_name="device_model")
        self.name = self.get_attribute(attribute_name="name")
        self.appliance_port_channels = None
        self.appliance_ports = None
        self.breakout_ports = None
        self.fcoe_port_channels = None
        self.fcoe_uplink_ports = None
        self.lan_pin_groups = None
        self.lan_port_channels = None
        self.lan_uplink_ports = None
        self.san_pin_groups = None
        self.san_port_channels = None
        self.san_storage_ports = None
        self.san_unified_ports = None
        self.san_uplink_ports = None
        self.server_ports = None

        if self._config.load_from == "live":
            # Fix for invalid eCMC model for pre-released units
            if self.device_model == "UCSXE-ECMC":
                self.device_model = "UCSXE-ECMC-G1"

            self.appliance_port_channels = self._get_appliance_port_channels()
            self.appliance_ports = self._get_appliance_ports()
            self.breakout_ports = self._get_breakout_ports()
            self.fcoe_port_channels = self._get_fcoe_port_channels()
            self.fcoe_uplink_ports = self._get_fcoe_uplink_ports()
            self.lan_pin_groups = self._get_lan_pin_groups()
            self.lan_port_channels = self._get_lan_port_channels()
            self.lan_uplink_ports = self._get_lan_uplink_ports()
            self.san_pin_groups = self._get_san_pin_groups()
            self.san_port_channels = self._get_san_port_channels()
            self.san_storage_ports = self._get_san_storage_ports()
            self.san_unified_ports = self._get_san_unified_ports()
            self.san_uplink_ports = self._get_san_uplink_ports()
            self.server_ports = self._get_server_ports()

        elif self._config.load_from == "file":
            for attribute in ["appliance_port_channels", "appliance_ports", "breakout_ports", "fcoe_port_channels",
                              "fcoe_uplink_ports", "lan_pin_groups", "lan_port_channels", "lan_uplink_ports",
                              "san_pin_groups", "san_port_channels", "san_storage_ports", "san_uplink_ports",
                              "san_unified_ports", "server_ports"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))
        self.clean_object()

    def _get_appliance_port_channels(self):
        # Fetches the Appliance Port Channels configuration of a Port Policy
        if "fabric_appliance_pc_role" in self._config.sdk_objects:
            appliance_port_channels = []
            for fabric_appliance_pc_role in self._config.sdk_objects["fabric_appliance_pc_role"]:
                if hasattr(fabric_appliance_pc_role, "port_policy"):
                    if fabric_appliance_pc_role.port_policy.moid == self._moid:
                        interfaces = []
                        if hasattr(fabric_appliance_pc_role, "ports"):
                            for port in fabric_appliance_pc_role.ports:
                                if port.aggregate_port_id != 0:
                                    interfaces.append({"slot_id": port.slot_id, "port_id": port.aggregate_port_id,
                                                       "aggr_id": port.port_id})
                                else:
                                    interfaces.append({"slot_id": port.slot_id, "port_id": port.port_id,
                                                       "aggr_id": None})

                        ethernet_network_control_policy = None
                        ethernet_network_group_policy = None
                        if hasattr(fabric_appliance_pc_role, "eth_network_control_policy"):
                            ethernet_network_control_policy = self._get_policy_name(
                                fabric_appliance_pc_role.eth_network_control_policy)
                        if hasattr(fabric_appliance_pc_role, "eth_network_group_policy"):
                            ethernet_network_group_policy = self._get_policy_name(
                                fabric_appliance_pc_role.eth_network_group_policy)

                        admin_speed = None
                        enable_25g_auto_neg = None
                        if hasattr(fabric_appliance_pc_role, "admin_speed"):
                            admin_speed = fabric_appliance_pc_role.admin_speed
                            if fabric_appliance_pc_role.admin_speed == "NegAuto25Gbps":
                                admin_speed = "25Gbps"
                                enable_25g_auto_neg = True

                        fec = None
                        if hasattr(fabric_appliance_pc_role, "fec"):
                            fec = fabric_appliance_pc_role.fec
                        user_label = fabric_appliance_pc_role.user_label
                        appliance_port_channels.append(
                            {"interfaces": interfaces,
                             "pc_id": fabric_appliance_pc_role.pc_id,
                             "user_label": user_label if user_label else None,
                             "admin_speed": admin_speed,
                             "fec": fec,
                             "enable_25gb_copper_cable_negotiation": enable_25g_auto_neg,
                             "mode": fabric_appliance_pc_role.mode,
                             "priority": fabric_appliance_pc_role.priority,
                             "ethernet_network_control_policy": ethernet_network_control_policy,
                             "ethernet_network_group_policy": ethernet_network_group_policy})

            return appliance_port_channels

        return None

    def _get_appliance_ports(self):
        # Fetches the Appliance Ports configuration of a Port Policy
        if "fabric_appliance_role" in self._config.sdk_objects:
            appliance_ports = []
            for fabric_appliance_role in self._config.sdk_objects["fabric_appliance_role"]:
                if hasattr(fabric_appliance_role, "port_policy"):
                    if fabric_appliance_role.port_policy.moid == self._moid:
                        ethernet_network_control_policy = None
                        ethernet_network_group_policy = None
                        if hasattr(fabric_appliance_role, "eth_network_control_policy"):
                            ethernet_network_control_policy = self._get_policy_name(
                                fabric_appliance_role.eth_network_control_policy)
                        if hasattr(fabric_appliance_role, "eth_network_group_policy"):
                            ethernet_network_group_policy = self._get_policy_name(
                                fabric_appliance_role.eth_network_group_policy)

                        admin_speed = None
                        enable_25g_auto_neg = None
                        if hasattr(fabric_appliance_role, "admin_speed"):
                            admin_speed = fabric_appliance_role.admin_speed
                            if fabric_appliance_role.admin_speed == "NegAuto25Gbps":
                                admin_speed = "25Gbps"
                                enable_25g_auto_neg = True

                        user_label = fabric_appliance_role.user_label
                        if fabric_appliance_role.aggregate_port_id != 0:
                            appliance_ports.append({"slot_id": fabric_appliance_role.slot_id,
                                                    "port_id": fabric_appliance_role.aggregate_port_id,
                                                    "aggr_id": fabric_appliance_role.port_id,
                                                    "user_label": user_label if user_label else None,
                                                    "admin_speed": admin_speed,
                                                    "enable_25gb_copper_cable_negotiation": enable_25g_auto_neg,
                                                    "fec": fabric_appliance_role.fec,
                                                    "mode": fabric_appliance_role.mode,
                                                    "priority": fabric_appliance_role.priority,
                                                    "ethernet_network_control_policy": ethernet_network_control_policy,
                                                    "ethernet_network_group_policy": ethernet_network_group_policy})
                        else:
                            appliance_ports.append({"slot_id": fabric_appliance_role.slot_id,
                                                    "port_id": fabric_appliance_role.port_id,
                                                    "user_label": user_label if user_label else None,
                                                    "aggr_id": None,
                                                    "admin_speed": admin_speed,
                                                    "enable_25gb_copper_cable_negotiation": enable_25g_auto_neg,
                                                    "fec": fabric_appliance_role.fec,
                                                    "mode": fabric_appliance_role.mode,
                                                    "priority": fabric_appliance_role.priority,
                                                    "ethernet_network_control_policy": ethernet_network_control_policy,
                                                    "ethernet_network_group_policy": ethernet_network_group_policy})

            return appliance_ports

        return None

    def _get_breakout_ports(self):
        # Fetches the Breakout Ports configuration of a Port Policy
        if "fabric_port_mode" in self._config.sdk_objects:
            breakout_ports = []
            for fabric_port_mode in self._config.sdk_objects["fabric_port_mode"]:
                if hasattr(fabric_port_mode, "port_policy"):
                    if fabric_port_mode.port_policy.moid == self._moid and \
                            getattr(fabric_port_mode, "custom_mode", None) == "BreakoutEthernet10G":
                        if fabric_port_mode.port_id_start and fabric_port_mode.port_id_end:
                            for port_id in range(fabric_port_mode.port_id_start, fabric_port_mode.port_id_end + 1):
                                breakout_ports.append({"slot_id": fabric_port_mode.slot_id,
                                                       "port_id": port_id,
                                                       "mode": "4x10g"})
                    elif fabric_port_mode.port_policy.moid == self._moid and \
                            getattr(fabric_port_mode, "custom_mode", None) == "BreakoutEthernet25G":
                        if fabric_port_mode.port_id_start and fabric_port_mode.port_id_end:
                            for port_id in range(fabric_port_mode.port_id_start, fabric_port_mode.port_id_end + 1):
                                breakout_ports.append({"slot_id": fabric_port_mode.slot_id,
                                                       "port_id": port_id,
                                                       "mode": "4x25g"})
                    elif fabric_port_mode.port_policy.moid == self._moid and \
                            getattr(fabric_port_mode, "custom_mode", None) == "BreakoutEthernet2x100G":
                        if fabric_port_mode.port_id_start and fabric_port_mode.port_id_end:
                            for port_id in range(fabric_port_mode.port_id_start, fabric_port_mode.port_id_end + 1):
                                breakout_ports.append({"slot_id": fabric_port_mode.slot_id,
                                                       "port_id": port_id,
                                                       "mode": "2x100g"})
                    elif fabric_port_mode.port_policy.moid == self._moid and \
                            getattr(fabric_port_mode, "custom_mode", None) == "BreakoutEthernet4x100G":
                        if fabric_port_mode.port_id_start and fabric_port_mode.port_id_end:
                            for port_id in range(fabric_port_mode.port_id_start, fabric_port_mode.port_id_end + 1):
                                breakout_ports.append({"slot_id": fabric_port_mode.slot_id,
                                                       "port_id": port_id,
                                                       "mode": "4x100g"})
                    elif fabric_port_mode.port_policy.moid == self._moid and \
                            getattr(fabric_port_mode, "custom_mode", None) == "BreakoutFibreChannel8G":
                        if fabric_port_mode.port_id_start and fabric_port_mode.port_id_end:
                            for port_id in range(fabric_port_mode.port_id_start, fabric_port_mode.port_id_end + 1):
                                breakout_ports.append({"slot_id": fabric_port_mode.slot_id,
                                                       "port_id": port_id,
                                                       "mode": "4x8g"})
                    elif fabric_port_mode.port_policy.moid == self._moid and \
                            getattr(fabric_port_mode, "custom_mode", None) == "BreakoutFibreChannel16G":
                        if fabric_port_mode.port_id_start and fabric_port_mode.port_id_end:
                            for port_id in range(fabric_port_mode.port_id_start, fabric_port_mode.port_id_end + 1):
                                breakout_ports.append({"slot_id": fabric_port_mode.slot_id,
                                                       "port_id": port_id,
                                                       "mode": "4x16g"})
                    elif fabric_port_mode.port_policy.moid == self._moid and \
                            getattr(fabric_port_mode, "custom_mode", None) == "BreakoutFibreChannel32G":
                        if fabric_port_mode.port_id_start and fabric_port_mode.port_id_end:
                            for port_id in range(fabric_port_mode.port_id_start, fabric_port_mode.port_id_end + 1):
                                breakout_ports.append({"slot_id": fabric_port_mode.slot_id,
                                                       "port_id": port_id,
                                                       "mode": "4x32g"})

            return breakout_ports

        return None

    def _get_fcoe_port_channels(self):
        # Fetches the FCoE Port Channels configuration of a Port Policy
        if "fabric_fcoe_uplink_pc_role" in self._config.sdk_objects:
            fcoe_port_channels = []
            for fabric_fcoe_uplink_pc_role in self._config.sdk_objects["fabric_fcoe_uplink_pc_role"]:
                if hasattr(fabric_fcoe_uplink_pc_role, "port_policy"):
                    if fabric_fcoe_uplink_pc_role.port_policy.moid == self._moid:
                        interfaces = []
                        if hasattr(fabric_fcoe_uplink_pc_role, "ports"):
                            for port in fabric_fcoe_uplink_pc_role.ports:
                                if port.aggregate_port_id != 0:
                                    interfaces.append({"slot_id": port.slot_id, "port_id": port.aggregate_port_id,
                                                       "aggr_id": port.port_id})
                                else:
                                    interfaces.append({"slot_id": port.slot_id, "port_id": port.port_id,
                                                       "aggr_id": None})

                        link_aggregation_policy = None
                        if hasattr(fabric_fcoe_uplink_pc_role, "link_aggregation_policy"):
                            link_aggregation_policy = self._get_policy_name(
                                fabric_fcoe_uplink_pc_role.link_aggregation_policy)

                        link_control_policy = None
                        if hasattr(fabric_fcoe_uplink_pc_role, "link_control_policy"):
                            link_control_policy = self._get_policy_name(
                                fabric_fcoe_uplink_pc_role.link_control_policy)

                        admin_speed = None
                        enable_25g_auto_neg = None
                        if hasattr(fabric_fcoe_uplink_pc_role, "admin_speed"):
                            admin_speed = fabric_fcoe_uplink_pc_role.admin_speed
                            if fabric_fcoe_uplink_pc_role.admin_speed == "NegAuto25Gbps":
                                admin_speed = "25Gbps"
                                enable_25g_auto_neg = True

                        fec = None
                        if hasattr(fabric_fcoe_uplink_pc_role, "fec"):
                            fec = fabric_fcoe_uplink_pc_role.fec

                        user_label = fabric_fcoe_uplink_pc_role.user_label
                        fcoe_port_channels.append({"interfaces": interfaces,
                                                   "pc_id": fabric_fcoe_uplink_pc_role.pc_id,
                                                   "user_label": user_label if user_label else None,
                                                   "admin_speed": admin_speed,
                                                   "fec": fec,
                                                   "enable_25gb_copper_cable_negotiation": enable_25g_auto_neg,
                                                   "link_aggregation_policy": link_aggregation_policy,
                                                   "link_control_policy": link_control_policy})

            return fcoe_port_channels

        return None

    def _get_fcoe_uplink_ports(self):
        # Fetches the FCoE Uplink Ports configuration of a Port Policy
        if "fabric_fcoe_uplink_role" in self._config.sdk_objects:
            fcoe_uplink_ports = []
            for fabric_fcoe_uplink_role in self._config.sdk_objects["fabric_fcoe_uplink_role"]:
                if hasattr(fabric_fcoe_uplink_role, "port_policy"):
                    if fabric_fcoe_uplink_role.port_policy.moid == self._moid:
                        link_control_policy = None
                        if hasattr(fabric_fcoe_uplink_role, "link_control_policy"):
                            link_control_policy = self._get_policy_name(fabric_fcoe_uplink_role.link_control_policy)

                        admin_speed = None
                        enable_25g_auto_neg = None
                        if hasattr(fabric_fcoe_uplink_role, "admin_speed"):
                            admin_speed = fabric_fcoe_uplink_role.admin_speed
                            if fabric_fcoe_uplink_role.admin_speed == "NegAuto25Gbps":
                                admin_speed = "25Gbps"
                                enable_25g_auto_neg = True

                        user_label = fabric_fcoe_uplink_role.user_label
                        if fabric_fcoe_uplink_role.aggregate_port_id != 0:
                            fcoe_uplink_ports.append({"slot_id": fabric_fcoe_uplink_role.slot_id,
                                                      "port_id": fabric_fcoe_uplink_role.aggregate_port_id,
                                                      "aggr_id": fabric_fcoe_uplink_role.port_id,
                                                      "user_label": user_label if user_label else None,
                                                      "admin_speed": admin_speed,
                                                      "enable_25gb_copper_cable_negotiation": enable_25g_auto_neg,
                                                      "fec": fabric_fcoe_uplink_role.fec,
                                                      "link_control_policy": link_control_policy})
                        else:
                            fcoe_uplink_ports.append({"slot_id": fabric_fcoe_uplink_role.slot_id,
                                                      "port_id": fabric_fcoe_uplink_role.port_id,
                                                      "user_label": user_label if user_label else None,
                                                      "aggr_id": None,
                                                      "admin_speed": admin_speed,
                                                      "enable_25gb_copper_cable_negotiation": enable_25g_auto_neg,
                                                      "fec": fabric_fcoe_uplink_role.fec,
                                                      "link_control_policy": link_control_policy})

            return fcoe_uplink_ports

        return None

    def _get_lan_pin_groups(self):
        # Fetches the LAN Pin Groups configuration of a Port Policy
        if "fabric_lan_pin_group" in self._config.sdk_objects:
            lan_pin_groups = []
            for fabric_lan_pin_group in self._config.sdk_objects["fabric_lan_pin_group"]:
                if hasattr(fabric_lan_pin_group, "port_policy"):
                    if fabric_lan_pin_group.port_policy.moid == self._moid:
                        target_interface_slot_id = None
                        target_interface_port_id = None
                        target_interface_aggr_id = None
                        target_interface_pc_id = None
                        if hasattr(fabric_lan_pin_group, "pin_target_interface_role"):
                            pin_target_interface_role = \
                                self.get_config_objects_from_ref(fabric_lan_pin_group.pin_target_interface_role)
                            if pin_target_interface_role:
                                if len(pin_target_interface_role) == 1:
                                    if pin_target_interface_role[0].object_type == "fabric.UplinkRole":
                                        target_interface_slot_id = pin_target_interface_role[0].slot_id
                                        if pin_target_interface_role[0].aggregate_port_id != 0:
                                            target_interface_port_id = pin_target_interface_role[0].aggregate_port_id
                                            target_interface_aggr_id = pin_target_interface_role[0].port_id
                                        else:
                                            target_interface_port_id = pin_target_interface_role[0].port_id
                                            target_interface_aggr_id = None

                                    elif pin_target_interface_role[0].object_type == "fabric.UplinkPcRole":
                                        target_interface_pc_id = pin_target_interface_role[0].pc_id

                        lan_pin_groups.append({"name": fabric_lan_pin_group.name,
                                               "slot_id": target_interface_slot_id,
                                               "port_id": target_interface_port_id,
                                               "aggr_id": target_interface_aggr_id,
                                               "pc_id": target_interface_pc_id})

            return lan_pin_groups

        return None

    def _get_lan_port_channels(self):
        # Fetches the LAN Port Channels configuration of a Port Policy
        if "fabric_uplink_pc_role" in self._config.sdk_objects:
            lan_port_channels = []
            for fabric_uplink_pc_role in self._config.sdk_objects["fabric_uplink_pc_role"]:
                if hasattr(fabric_uplink_pc_role, "port_policy"):
                    if fabric_uplink_pc_role.port_policy.moid == self._moid:
                        interfaces = []
                        if hasattr(fabric_uplink_pc_role, "ports"):
                            for port in fabric_uplink_pc_role.ports:
                                if port.aggregate_port_id != 0:
                                    interfaces.append({"slot_id": port.slot_id, "port_id": port.aggregate_port_id,
                                                       "aggr_id": port.port_id})
                                else:
                                    interfaces.append({"slot_id": port.slot_id, "port_id": port.port_id,
                                                       "aggr_id": None})

                        ethernet_network_group_policies = None
                        if hasattr(fabric_uplink_pc_role, "eth_network_group_policy") \
                                and fabric_uplink_pc_role.eth_network_group_policy:
                            ref = fabric_uplink_pc_role.eth_network_group_policy
                            ref_list = ref if isinstance(ref, list) else [ref]
                            ethernet_network_group_policies = []
                            for ref_item in ref_list:
                                policy_name = self._get_policy_name(ref_item)
                                if policy_name:
                                    ethernet_network_group_policies.append(policy_name)
                            if not ethernet_network_group_policies:
                                ethernet_network_group_policies = None

                        flow_control_policy = None
                        if hasattr(fabric_uplink_pc_role, "flow_control_policy"):
                            flow_control_policy = self._get_policy_name(fabric_uplink_pc_role.flow_control_policy)

                        link_aggregation_policy = None
                        if hasattr(fabric_uplink_pc_role, "link_aggregation_policy"):
                            link_aggregation_policy = self._get_policy_name(
                                fabric_uplink_pc_role.link_aggregation_policy)

                        link_control_policy = None
                        if hasattr(fabric_uplink_pc_role, "link_control_policy"):
                            link_control_policy = self._get_policy_name(fabric_uplink_pc_role.link_control_policy)

                        macsec_policy = None
                        if hasattr(fabric_uplink_pc_role, "mac_sec_policy"):
                            macsec_policy = self._get_policy_name(fabric_uplink_pc_role.mac_sec_policy)

                        admin_speed = None
                        enable_25g_auto_neg = None
                        if hasattr(fabric_uplink_pc_role, "admin_speed"):
                            admin_speed = fabric_uplink_pc_role.admin_speed
                            if fabric_uplink_pc_role.admin_speed == "NegAuto25Gbps":
                                admin_speed = "25Gbps"
                                enable_25g_auto_neg = True
                        
                        fec = None
                        if hasattr(fabric_uplink_pc_role, "fec"):
                            fec = fabric_uplink_pc_role.fec

                        user_label = fabric_uplink_pc_role.user_label
                        lan_port_channels.append({"interfaces": interfaces,
                                                  "pc_id": fabric_uplink_pc_role.pc_id,
                                                  "user_label": user_label if user_label else None,
                                                  "admin_speed": admin_speed,
                                                  "enable_25gb_copper_cable_negotiation": enable_25g_auto_neg,
                                                  "ethernet_network_group_policies": ethernet_network_group_policies,
                                                  "fec": fec,
                                                  "flow_control_policy": flow_control_policy,
                                                  "link_aggregation_policy": link_aggregation_policy,
                                                  "link_control_policy": link_control_policy,
                                                  "macsec_policy": macsec_policy})

            return lan_port_channels

        return None

    def _get_lan_uplink_ports(self):
        # Fetches the LAN Uplink Ports configuration of a Port Policy
        if "fabric_uplink_role" in self._config.sdk_objects:
            lan_uplink_ports = []
            for fabric_uplink_role in self._config.sdk_objects["fabric_uplink_role"]:
                if hasattr(fabric_uplink_role, "port_policy"):
                    if fabric_uplink_role.port_policy.moid == self._moid:
                        flow_control_policy = None
                        if hasattr(fabric_uplink_role, "flow_control_policy"):
                            flow_control_policy = self._get_policy_name(fabric_uplink_role.flow_control_policy)

                        ethernet_network_group_policies = None
                        if hasattr(fabric_uplink_role, "eth_network_group_policy") \
                                and fabric_uplink_role.eth_network_group_policy:
                            ref = fabric_uplink_role.eth_network_group_policy
                            ref_list = ref if isinstance(ref, list) else [ref]
                            ethernet_network_group_policies = []
                            for ref_item in ref_list:
                                policy_name = self._get_policy_name(ref_item)
                                if policy_name:
                                    ethernet_network_group_policies.append(policy_name)
                            if not ethernet_network_group_policies:
                                ethernet_network_group_policies = None

                        link_control_policy = None
                        if hasattr(fabric_uplink_role, "link_control_policy"):
                            link_control_policy = self._get_policy_name(fabric_uplink_role.link_control_policy)

                        macsec_policy = None
                        if hasattr(fabric_uplink_role, "mac_sec_policy"):
                            macsec_policy = self._get_policy_name(fabric_uplink_role.mac_sec_policy)

                        admin_speed = None
                        enable_25g_auto_neg = None
                        if hasattr(fabric_uplink_role, "admin_speed"):
                            admin_speed = fabric_uplink_role.admin_speed
                            if fabric_uplink_role.admin_speed == "NegAuto25Gbps":
                                admin_speed = "25Gbps"
                                enable_25g_auto_neg = True

                        user_label = fabric_uplink_role.user_label
                        if fabric_uplink_role.aggregate_port_id != 0:
                            lan_uplink_ports.append({"slot_id": fabric_uplink_role.slot_id,
                                                     "port_id": fabric_uplink_role.aggregate_port_id,
                                                     "aggr_id": fabric_uplink_role.port_id,
                                                     "user_label": user_label if user_label else None,
                                                     "admin_speed": admin_speed,
                                                     "enable_25gb_copper_cable_negotiation": enable_25g_auto_neg,
                                                     "fec": fabric_uplink_role.fec,
                                                     "ethernet_network_group_policies": ethernet_network_group_policies,
                                                     "flow_control_policy": flow_control_policy,
                                                     "link_control_policy": link_control_policy,
                                                     "macsec_policy": macsec_policy})
                        else:
                            lan_uplink_ports.append({"slot_id": fabric_uplink_role.slot_id,
                                                     "port_id": fabric_uplink_role.port_id,
                                                     "user_label": user_label if user_label else None,
                                                     "aggr_id": None,
                                                     "admin_speed": admin_speed,
                                                     "enable_25gb_copper_cable_negotiation": enable_25g_auto_neg,
                                                     "fec": fabric_uplink_role.fec,
                                                     "ethernet_network_group_policies": ethernet_network_group_policies,
                                                     "flow_control_policy": flow_control_policy,
                                                     "link_control_policy": link_control_policy,
                                                     "macsec_policy": macsec_policy})

            return lan_uplink_ports

        return None

    def _get_san_pin_groups(self):
        # Fetches the SAN Pin Groups configuration of a Port Policy
        if "fabric_san_pin_group" in self._config.sdk_objects:
            san_pin_groups = []
            for fabric_san_pin_group in self._config.sdk_objects["fabric_san_pin_group"]:
                if hasattr(fabric_san_pin_group, "port_policy"):
                    if fabric_san_pin_group.port_policy.moid == self._moid:
                        target_interface_slot_id = None
                        target_interface_port_id = None
                        target_interface_aggr_id = None
                        target_interface_pc_id = None
                        fcoe = False
                        if hasattr(fabric_san_pin_group, "pin_target_interface_role"):
                            pin_target_interface_role = \
                                self.get_config_objects_from_ref(fabric_san_pin_group.pin_target_interface_role)
                            if pin_target_interface_role:
                                if len(pin_target_interface_role) == 1:
                                    if pin_target_interface_role[0].object_type in \
                                            ["fabric.FcUplinkRole", "fabric.FcoeUplinkRole"]:
                                        target_interface_slot_id = pin_target_interface_role[0].slot_id
                                        if pin_target_interface_role[0].aggregate_port_id != 0:
                                            target_interface_port_id = pin_target_interface_role[0].aggregate_port_id
                                            target_interface_aggr_id = pin_target_interface_role[0].port_id
                                        else:
                                            target_interface_port_id = pin_target_interface_role[0].port_id
                                            target_interface_aggr_id = None

                                    elif pin_target_interface_role[0].object_type in \
                                            ["fabric.FcUplinkPcRole", "fabric.FcoeUplinkPcRole"]:
                                        target_interface_pc_id = pin_target_interface_role[0].pc_id

                                    if "Fcoe" in pin_target_interface_role[0].object_type:
                                        fcoe = True

                        san_pin_groups.append({"name": fabric_san_pin_group.name,
                                               "fcoe": fcoe,
                                               "slot_id": target_interface_slot_id,
                                               "port_id": target_interface_port_id,
                                               "aggr_id": target_interface_aggr_id,
                                               "pc_id": target_interface_pc_id})

            return san_pin_groups

        return None

    def _get_san_port_channels(self):
        # Fetches the SAN Port Channels configuration of a Port Policy
        if "fabric_fc_uplink_pc_role" in self._config.sdk_objects:
            san_port_channels = []
            for fabric_fc_uplink_pc_role in self._config.sdk_objects["fabric_fc_uplink_pc_role"]:
                if hasattr(fabric_fc_uplink_pc_role, "port_policy"):
                    if fabric_fc_uplink_pc_role.port_policy.moid == self._moid:
                        interfaces = []
                        if hasattr(fabric_fc_uplink_pc_role, "ports"):
                            for port in fabric_fc_uplink_pc_role.ports:
                                if port.aggregate_port_id != 0:
                                    interfaces.append({"slot_id": port.slot_id, "port_id": port.aggregate_port_id,
                                                       "aggr_id": port.port_id})
                                else:
                                    interfaces.append({"slot_id": port.slot_id, "port_id": port.port_id,
                                                       "aggr_id": None})
                        user_label = fabric_fc_uplink_pc_role.user_label
                        san_port_channels.append({"interfaces": interfaces,
                                                  "pc_id": fabric_fc_uplink_pc_role.pc_id,
                                                  "vsan_id": fabric_fc_uplink_pc_role.vsan_id,
                                                  "admin_speed": fabric_fc_uplink_pc_role.admin_speed,
                                                  "fill_pattern": fabric_fc_uplink_pc_role.fill_pattern,
                                                  "user_label": user_label if user_label else None})

            return san_port_channels

        return None

    def _get_san_storage_ports(self):
        # Fetches the SAN Storage Ports configuration of a Port Policy
        if "fabric_fc_storage_role" in self._config.sdk_objects:
            san_storage_ports = []
            for fabric_fc_storage_role in self._config.sdk_objects["fabric_fc_storage_role"]:
                if hasattr(fabric_fc_storage_role, "port_policy"):
                    if fabric_fc_storage_role.port_policy.moid == self._moid:
                        user_label = fabric_fc_storage_role.user_label
                        if fabric_fc_storage_role.aggregate_port_id != 0:
                            san_storage_ports.append({"slot_id": fabric_fc_storage_role.slot_id,
                                                      "port_id": fabric_fc_storage_role.aggregate_port_id,
                                                      "aggr_id": fabric_fc_storage_role.port_id,
                                                      "admin_speed": fabric_fc_storage_role.admin_speed,
                                                      "vsan_id": fabric_fc_storage_role.vsan_id,
                                                      "user_label": user_label if user_label else None})
                        else:
                            san_storage_ports.append({"slot_id": fabric_fc_storage_role.slot_id,
                                                      "port_id": fabric_fc_storage_role.port_id,
                                                      "aggr_id": None,
                                                      "admin_speed": fabric_fc_storage_role.admin_speed,
                                                      "vsan_id": fabric_fc_storage_role.vsan_id,
                                                      "user_label": user_label if user_label else None})

            return san_storage_ports

        return None

    def _get_san_unified_ports(self):
        # Fetches the Unified Ports configuration of a Port Policy
        if "fabric_port_mode" in self._config.sdk_objects:
            for fabric_port_mode in self._config.sdk_objects["fabric_port_mode"]:
                if hasattr(fabric_port_mode, "port_policy"):
                    if fabric_port_mode.port_policy.moid == self._moid and \
                            getattr(fabric_port_mode, "custom_mode", None) == "FibreChannel":
                        return {"slot_id": fabric_port_mode.slot_id,
                                "port_id_start": fabric_port_mode.port_id_start,
                                "port_id_end": fabric_port_mode.port_id_end}

        return None

    def _get_san_uplink_ports(self):
        # Fetches the SAN Uplink Ports configuration of a Port Policy
        if "fabric_fc_uplink_role" in self._config.sdk_objects:
            san_uplink_ports = []
            for fabric_fc_uplink_role in self._config.sdk_objects["fabric_fc_uplink_role"]:
                if hasattr(fabric_fc_uplink_role, "port_policy"):
                    if fabric_fc_uplink_role.port_policy.moid == self._moid:
                        user_label = fabric_fc_uplink_role.user_label
                        if fabric_fc_uplink_role.aggregate_port_id != 0:
                            san_uplink_ports.append({"slot_id": fabric_fc_uplink_role.slot_id,
                                                     "port_id": fabric_fc_uplink_role.aggregate_port_id,
                                                     "aggr_id": fabric_fc_uplink_role.port_id,
                                                     "admin_speed": fabric_fc_uplink_role.admin_speed,
                                                     "vsan_id": fabric_fc_uplink_role.vsan_id,
                                                     "fill_pattern": fabric_fc_uplink_role.fill_pattern,
                                                     "user_label": user_label if user_label else None})
                        else:
                            san_uplink_ports.append({"slot_id": fabric_fc_uplink_role.slot_id,
                                                     "port_id": fabric_fc_uplink_role.port_id,
                                                     "aggr_id": None,
                                                     "admin_speed": fabric_fc_uplink_role.admin_speed,
                                                     "vsan_id": fabric_fc_uplink_role.vsan_id,
                                                     "fill_pattern": fabric_fc_uplink_role.fill_pattern,
                                                     "user_label": user_label if user_label else None})

            return san_uplink_ports

        return None

    def _get_server_ports(self):
        # Fetches the Server Ports configuration of a Port Policy
        if "fabric_server_role" in self._config.sdk_objects:
            server_ports = []
            for fabric_server_role in self._config.sdk_objects["fabric_server_role"]:
                if hasattr(fabric_server_role, "port_policy"):
                    if fabric_server_role.port_policy.moid == self._moid:
                        user_label = fabric_server_role.user_label
                        server_port = {
                            "slot_id": fabric_server_role.slot_id,
                            "port_id": fabric_server_role.port_id,
                            "aggr_id": None,
                            "connected_device_type": fabric_server_role.preferred_device_type,
                            "connected_device_id": None,
                            "fec": fabric_server_role.fec,
                            "user_label": user_label if user_label else None
                        }
                        if fabric_server_role.aggregate_port_id != 0:
                            server_port["port_id"] = fabric_server_role.aggregate_port_id
                            server_port["aggr_id"] = fabric_server_role.port_id
                        if fabric_server_role.preferred_device_id != 0:
                            server_port["connected_device_id"] = fabric_server_role.preferred_device_id

                        server_ports.append(server_port)

            return server_ports

        return None

    def clean_object(self):
        # We use this to make sure all options of an Appliance Port-Channel are set to None if they are not present
        if self.appliance_port_channels:
            for appliance_port_channel in self.appliance_port_channels:
                for attribute in ["admin_speed", "enable_25gb_copper_cable_negotiation",
                                  "ethernet_network_control_policy", "ethernet_network_group_policy", "fec",
                                  "interfaces", "mode", "pc_id", "priority", "user_label"]:
                    if attribute not in appliance_port_channel:
                        appliance_port_channel[attribute] = None

                if appliance_port_channel["interfaces"]:
                    for interface in appliance_port_channel["interfaces"]:
                        for attribute_intf in ["aggr_id", "port_id", "slot_id"]:
                            if attribute_intf not in interface:
                                interface[attribute_intf] = None

        # We use this to make sure all options of an Appliance Port are set to None if they are not present
        if self.appliance_ports:
            for appliance_port in self.appliance_ports:
                for attribute in ["admin_speed", "aggr_id", "enable_25gb_copper_cable_negotiation",
                                  "ethernet_network_control_policy", "ethernet_network_group_policy", "fec",
                                  "mode", "port_id", "priority", "slot_id", "user_label"]:
                    if attribute not in appliance_port:
                        appliance_port[attribute] = None

        # We use this to make sure all options of Breakout Ports are set to None if they are not present
        if self.breakout_ports:
            for breakout_port in self.breakout_ports:
                for attribute in ["mode", "port_id", "slot_id"]:
                    if attribute not in breakout_port:
                        breakout_port[attribute] = None

        # We use this to make sure all options of a FCoE Port-Channel are set to None if they are not present
        if self.fcoe_port_channels:
            for fcoe_port_channel in self.fcoe_port_channels:
                for attribute in ["admin_speed", "enable_25gb_copper_cable_negotiation", "fec", "interfaces",
                                  "link_aggregation_policy", "link_control_policy", "pc_id", "user_label"]:
                    if attribute not in fcoe_port_channel:
                        fcoe_port_channel[attribute] = None

                if fcoe_port_channel["interfaces"]:
                    for interface in fcoe_port_channel["interfaces"]:
                        for attribute_intf in ["aggr_id", "port_id", "slot_id"]:
                            if attribute_intf not in interface:
                                interface[attribute_intf] = None

        # We use this to make sure all options of a FCoE Uplink Port are set to None if they are not present
        if self.fcoe_uplink_ports:
            for fcoe_uplink_port in self.fcoe_uplink_ports:
                for attribute in ["admin_speed", "aggr_id", "enable_25gb_copper_cable_negotiation", "fec",
                                  "link_control_policy", "port_id", "slot_id", "user_label"]:
                    if attribute not in fcoe_uplink_port:
                        fcoe_uplink_port[attribute] = None

        # We use this to make sure all options of a LAN Pin Group are set to None if they are not present
        if self.lan_pin_groups:
            for lan_pin_group in self.lan_pin_groups:
                for attribute in ["aggr_id", "name", "pc_id", "port_id", "slot_id"]:
                    if attribute not in lan_pin_group:
                        lan_pin_group[attribute] = None

        # We use this to make sure all options of a LAN Port-Channel are set to None if they are not present
        if self.lan_port_channels:
            for lan_port_channel in self.lan_port_channels:
                for attribute in ["admin_speed", "enable_25gb_copper_cable_negotiation",
                                  "ethernet_network_group_policies", "ethernet_network_group_policy",
                                  "fec", "flow_control_policy", "interfaces", "link_aggregation_policy",
                                  "link_control_policy", "macsec_policy", "pc_id", "user_label"]:
                    if attribute not in lan_port_channel:
                        lan_port_channel[attribute] = None

                if lan_port_channel["interfaces"]:
                    for interface in lan_port_channel["interfaces"]:
                        for attribute_intf in ["aggr_id", "port_id", "slot_id"]:
                            if attribute_intf not in interface:
                                interface[attribute_intf] = None

        # We use this to make sure all options of a LAN Uplink Port are set to None if they are not present
        if self.lan_uplink_ports:
            for lan_uplink_port in self.lan_uplink_ports:
                for attribute in ["admin_speed", "aggr_id", "enable_25gb_copper_cable_negotiation",
                                  "ethernet_network_group_policies", "ethernet_network_group_policy", "fec",
                                  "flow_control_policy", "link_control_policy", "macsec_policy", "port_id",
                                  "slot_id", "user_label"]:
                    if attribute not in lan_uplink_port:
                        lan_uplink_port[attribute] = None

        # We use this to make sure all options of a SAN Pin Group are set to None if they are not present
        if self.san_pin_groups:
            for san_pin_group in self.san_pin_groups:
                for attribute in ["aggr_id", "fcoe", "name", "pc_id", "port_id", "slot_id"]:
                    if attribute not in san_pin_group:
                        san_pin_group[attribute] = None

        # We use this to make sure all options of a SAN Port-Channel are set to None if they are not present
        if self.san_port_channels:
            for san_port_channel in self.san_port_channels:
                for attribute in ["admin_speed", "fill_pattern", "interfaces", "pc_id", "vsan_id", "user_label"]:
                    if attribute not in san_port_channel:
                        san_port_channel[attribute] = None

                if san_port_channel["interfaces"]:
                    for interface in san_port_channel["interfaces"]:
                        for attribute_intf in ["aggr_id", "port_id", "slot_id"]:
                            if attribute_intf not in interface:
                                interface[attribute_intf] = None

        # We use this to make sure all options of a SAN Storage Port are set to None if they are not present
        if self.san_storage_ports:
            for san_storage_port in self.san_storage_ports:
                for attribute in ["admin_speed", "aggr_id", "port_id", "slot_id", "vsan_id", "user_label"]:
                    if attribute not in san_storage_port:
                        san_storage_port[attribute] = None

        # We use this to make sure all options of SAN Unified Ports are set to None if they are not present
        if self.san_unified_ports:
            for attribute in ["port_id_end", "port_id_start", "slot_id"]:
                if attribute not in self.san_unified_ports:
                    self.san_unified_ports[attribute] = None

        # We use this to make sure all options of a SAN Uplink Port are set to None if they are not present
        if self.san_uplink_ports:
            for san_uplink_port in self.san_uplink_ports:
                for attribute in ["admin_speed", "aggr_id", "fill_pattern", "port_id", "slot_id", "vsan_id",
                                  "user_label"]:
                    if attribute not in san_uplink_port:
                        san_uplink_port[attribute] = None

        # We use this to make sure all options of a Server Port are set to None if they are not present
        if self.server_ports:
            for server_port in self.server_ports:
                for attribute in ["aggr_id", "connected_device_type", "connected_device_id", "fec", "port_id",
                                  "slot_id", "user_label"]:
                    if attribute not in server_port:
                        server_port[attribute] = None

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.fabric_port_policy import FabricPortPolicy

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        # We first need to push the main fabric.PortPolicy object
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
        if self.device_model is not None:
            kwargs["device_model"] = self.device_model

        fabric_port_policy = FabricPortPolicy(**kwargs)

        fpp = self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=fabric_port_policy,
                          detail=self.name, return_relationship=True)
        if not fpp:
            return False

        failed_to_push_port_policy_attributes = False
        # We start with SAN Unified Ports so that SAN Uplink Ports and SAN Port-Channels configuration work properly
        # We only do this for FI models that do not use FC Breakout - otherwise Unified Ports are configured as part
        # of Breakout config
        if self.san_unified_ports and self.device_model not in ["UCS-FI-6536", "UCSX-S9108-100G"]:
            # We now need to push the fabric.PortMode object for Unified Port configuration
            from intersight.model.fabric_port_mode import FabricPortMode

            kwargs = {
                "object_type": "fabric.PortMode",
                "class_id": "fabric.PortMode",
                "custom_mode": "FibreChannel",
                "port_policy": fpp
            }
            if self.san_unified_ports["slot_id"] is not None:
                kwargs["slot_id"] = self.san_unified_ports["slot_id"]
            if self.san_unified_ports["port_id_start"] is not None:
                kwargs["port_id_start"] = self.san_unified_ports["port_id_start"]
            if self.san_unified_ports["port_id_end"] is not None:
                kwargs["port_id_end"] = self.san_unified_ports["port_id_end"]

            fabric_port_mode = FabricPortMode(**kwargs)

            if not self.commit(object_type="fabric.PortMode", payload=fabric_port_mode,
                               detail=self.name + " - SAN Unified Ports",
                               key_attributes=["port_policy", "custom_mode", "slot_id"]):
                failed_to_push_port_policy_attributes = True

        # We continue with Breakout Ports so that all broken ports roles configuration work properly
        if self.breakout_ports:
            # We now need to push the fabric.PortMode object for Breakout Port configuration
            from intersight.model.fabric_port_mode import FabricPortMode

            # We push breakout ports in reverse order in order to properly support FI 6536 (EASYUCS-1119)
            for breakout_port in sorted(self.breakout_ports, key=lambda x: -int(x["port_id"])):
                kwargs = {
                    "object_type": "fabric.PortMode",
                    "class_id": "fabric.PortMode",
                    "port_policy": fpp
                }
                if breakout_port["slot_id"] is not None:
                    kwargs["slot_id"] = breakout_port["slot_id"]
                if breakout_port["port_id"] is not None:
                    kwargs["port_id_start"] = breakout_port["port_id"]
                    kwargs["port_id_end"] = breakout_port["port_id"]
                if breakout_port["mode"] in ["4x10g"]:
                    kwargs["custom_mode"] = "BreakoutEthernet10G"
                elif breakout_port["mode"] in ["4x25g"]:
                    kwargs["custom_mode"] = "BreakoutEthernet25G"
                elif breakout_port["mode"] in ["2x100g"]:
                    kwargs["custom_mode"] = "BreakoutEthernet2x100G"
                elif breakout_port["mode"] in ["4x100g"]:
                    kwargs["custom_mode"] = "BreakoutEthernet4x100G"
                elif breakout_port["mode"] in ["4x8g"]:
                    kwargs["custom_mode"] = "BreakoutFibreChannel8G"
                elif breakout_port["mode"] in ["4x16g"]:
                    kwargs["custom_mode"] = "BreakoutFibreChannel16G"
                elif breakout_port["mode"] in ["4x32g"]:
                    kwargs["custom_mode"] = "BreakoutFibreChannel32G"

                fabric_port_mode = FabricPortMode(**kwargs)

                detail = self.name + " - Breakout Port " + str(breakout_port["slot_id"]) + "/" + str(
                    breakout_port["port_id"])
                if not self.commit(object_type="fabric.PortMode", payload=fabric_port_mode, detail=detail,
                                   key_attributes=["port_policy", "slot_id", "port_id_start", "port_id_end"]):
                    failed_to_push_port_policy_attributes = True

        if self.appliance_port_channels:
            # We now need to push the fabric.AppliancePcRole object for each Appliance Port Channel configuration
            from intersight.model.fabric_appliance_pc_role import FabricAppliancePcRole
            from intersight.model.fabric_port_identifier import FabricPortIdentifier

            for appliance_port_channel in self.appliance_port_channels:
                ports = []
                if appliance_port_channel["interfaces"]:
                    for interface in appliance_port_channel["interfaces"]:
                        kwargs = {
                            "object_type": "fabric.PortIdentifier",
                            "class_id": "fabric.PortIdentifier",
                        }
                        if interface["slot_id"] is not None:
                            kwargs["slot_id"] = interface["slot_id"]
                        if interface["aggr_id"] not in [None, 0]:  # We have a breakout port
                            kwargs["port_id"] = interface["aggr_id"]
                            kwargs["aggregate_port_id"] = interface["port_id"]
                        else:
                            kwargs["port_id"] = interface["port_id"]
                            kwargs["aggregate_port_id"] = 0

                        fabric_port_identifier = FabricPortIdentifier(**kwargs)
                        ports.append(fabric_port_identifier)

                kwargs = {
                    "object_type": "fabric.AppliancePcRole",
                    "class_id": "fabric.AppliancePcRole",
                    "port_policy": fpp,
                    "ports": ports
                }
                if appliance_port_channel["pc_id"] is not None:
                    kwargs["pc_id"] = appliance_port_channel["pc_id"]
                if appliance_port_channel["admin_speed"] is not None:
                    kwargs["admin_speed"] = appliance_port_channel["admin_speed"]
                if appliance_port_channel["fec"] is not None:
                    kwargs["fec"] = appliance_port_channel["fec"]
                if appliance_port_channel["enable_25gb_copper_cable_negotiation"]:
                    kwargs["admin_speed"] = "NegAuto25Gbps"
                if appliance_port_channel["mode"] is not None:
                    kwargs["mode"] = appliance_port_channel["mode"]
                if appliance_port_channel["priority"] is not None:
                    kwargs["priority"] = appliance_port_channel["priority"]
                if appliance_port_channel["user_label"] is not None:
                    kwargs["user_label"] = appliance_port_channel["user_label"]

                if appliance_port_channel["ethernet_network_control_policy"] is not None:
                    # We first need to identify the Ethernet Network Control Policy object reference
                    ethernet_network_control_policy = self.get_live_object(
                        object_name=appliance_port_channel["ethernet_network_control_policy"],
                        object_type="fabric.EthNetworkControlPolicy"
                    )
                    if ethernet_network_control_policy:
                        kwargs["eth_network_control_policy"] = ethernet_network_control_policy
                    else:
                        self.logger(
                            level="warning",
                            message=f"Could not find unique Ethernet Network Control Policy "
                                    f"'{appliance_port_channel['ethernet_network_control_policy']}' "
                                    f"to assign to Appliance Port Channel {appliance_port_channel['pc_id']}"
                        )
                        self._config.push_summary_manager.add_object_status(
                            obj=self, obj_detail=f"Attaching Ethernet Network Control Policy "
                                                 f"'{appliance_port_channel['ethernet_network_control_policy']}'",
                            obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                            message=f"Failed to find Ethernet Network Control Policy "
                                    f"'{appliance_port_channel['ethernet_network_control_policy']}'"
                        )

                if appliance_port_channel["ethernet_network_group_policy"] is not None:
                    # We first need to identify the Ethernet Network Group Policy object reference
                    ethernet_network_group_policy = self.get_live_object(
                        object_name=appliance_port_channel["ethernet_network_group_policy"],
                        object_type="fabric.EthNetworkGroupPolicy"
                    )
                    if ethernet_network_group_policy:
                        kwargs["eth_network_group_policy"] = ethernet_network_group_policy
                    else:
                        self.logger(
                            level="warning",
                            message=f"Could not find unique Ethernet Network Group Policy "
                                    f"'{appliance_port_channel['ethernet_network_group_policy']}' "
                                    f"to assign to Appliance Port Channel {appliance_port_channel['pc_id']}"
                        )
                        self._config.push_summary_manager.add_object_status(
                            obj=self, obj_detail=f"Attaching Ethernet Network Group Policy "
                                                 f"'{appliance_port_channel['ethernet_network_group_policy']}'",
                            obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                            message=f"Failed to find Ethernet Network Group Policy "
                                    f"'{appliance_port_channel['ethernet_network_group_policy']}'"
                        )

                fabric_appliance_pc_role = FabricAppliancePcRole(**kwargs)

                detail = self.name + " - Appliance Port Channel " + str(appliance_port_channel["pc_id"])
                if not self.commit(object_type="fabric.AppliancePcRole", payload=fabric_appliance_pc_role,
                                   detail=detail, key_attributes=["port_policy", "pc_id"]):
                    failed_to_push_port_policy_attributes = True

        if self.appliance_ports:
            # We now need to push the fabric.ApplianceRole object for each Appliance Port configuration
            from intersight.model.fabric_appliance_role import FabricApplianceRole

            for appliance_port in self.appliance_ports:
                kwargs = {
                    "object_type": "fabric.ApplianceRole",
                    "class_id": "fabric.ApplianceRole",
                    "port_policy": fpp
                }
                if appliance_port["slot_id"] is not None:
                    kwargs["slot_id"] = appliance_port["slot_id"]
                if appliance_port["aggr_id"] not in [None, 0]:  # We have a breakout port
                    kwargs["port_id"] = appliance_port["aggr_id"]
                    kwargs["aggregate_port_id"] = appliance_port["port_id"]
                else:
                    kwargs["port_id"] = appliance_port["port_id"]
                    kwargs["aggregate_port_id"] = 0
                if appliance_port["fec"] is not None:
                    kwargs["fec"] = appliance_port["fec"]
                if appliance_port["admin_speed"] is not None:
                    kwargs["admin_speed"] = appliance_port["admin_speed"]
                if appliance_port["enable_25gb_copper_cable_negotiation"]:
                    kwargs["admin_speed"] = "NegAuto25Gbps"
                if appliance_port["mode"] is not None:
                    kwargs["mode"] = appliance_port["mode"]
                if appliance_port["priority"] is not None:
                    kwargs["priority"] = appliance_port["priority"]
                if appliance_port["user_label"] is not None:
                    kwargs["user_label"] = appliance_port["user_label"]

                if appliance_port["ethernet_network_control_policy"] is not None:
                    # We first need to identify the Ethernet Network Control Policy object reference
                    ethernet_network_control_policy = self.get_live_object(
                        object_name=appliance_port["ethernet_network_control_policy"],
                        object_type="fabric.EthNetworkControlPolicy"
                    )
                    if ethernet_network_control_policy:
                        kwargs["eth_network_control_policy"] = ethernet_network_control_policy
                    else:
                        if appliance_port["aggr_id"]:
                            self.logger(level="warning",
                                        message=f"Could not find unique Ethernet Network Control Policy "
                                                f"'{appliance_port['ethernet_network_control_policy']}' "
                                                f"to assign to Appliance Port {appliance_port['slot_id']}/"
                                                f"{appliance_port['port_id']}/{appliance_port['aggr_id']}")
                        else:
                            self.logger(level="warning",
                                        message=f"Could not find unique Ethernet Network Control Policy "
                                                f"'{appliance_port['ethernet_network_control_policy']}' "
                                                f"to assign to Appliance Port {appliance_port['slot_id']}/"
                                                f"{appliance_port['port_id']}")
                        self._config.push_summary_manager.add_object_status(
                            obj=self, obj_detail=f"Attaching Ethernet Network Control Policy "
                                                 f"'{appliance_port['ethernet_network_control_policy']}'",
                            obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                            message=f"Failed to find Ethernet Network Control Policy "
                                    f"'{appliance_port['ethernet_network_control_policy']}'"
                        )

                if appliance_port["ethernet_network_group_policy"] is not None:
                    # We first need to identify the Ethernet Network Group Policy object reference
                    ethernet_network_group_policy = self.get_live_object(
                        object_name=appliance_port["ethernet_network_group_policy"],
                        object_type="fabric.EthNetworkGroupPolicy"
                    )
                    if ethernet_network_group_policy:
                        kwargs["eth_network_group_policy"] = ethernet_network_group_policy
                    else:
                        if appliance_port["aggr_id"]:
                            self.logger(level="warning",
                                        message=f"Could not find unique Ethernet Network Group Policy "
                                                f"'{appliance_port['ethernet_network_group_policy']}' "
                                                f"to assign to Appliance Port {appliance_port['slot_id']}/"
                                                f"{appliance_port['port_id']}/{appliance_port['aggr_id']}")
                        else:
                            self.logger(level="warning",
                                        message=f"Could not find unique Ethernet Network Group Policy "
                                                f"'{appliance_port['ethernet_network_group_policy']}' "
                                                f"to assign to Appliance Port {appliance_port['slot_id']}/"
                                                f"{appliance_port['port_id']}")
                        self._config.push_summary_manager.add_object_status(
                            obj=self, obj_detail=f"Attaching Ethernet Network Group Policy "
                                                 f"'{appliance_port['ethernet_network_group_policy']}'",
                            obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                            message=f"Failed to find Ethernet Network Group Policy "
                                    f"'{appliance_port['ethernet_network_group_policy']}'"
                        )

                fabric_appliance_role = FabricApplianceRole(**kwargs)

                if appliance_port["aggr_id"]:
                    detail = self.name + " - Appliance Port " + str(appliance_port["slot_id"]) + "/" + \
                             str(appliance_port["port_id"]) + "/" + str(appliance_port["aggr_id"])
                else:
                    detail = self.name + " - Appliance Port " + str(appliance_port["slot_id"]) + "/" + \
                             str(appliance_port["port_id"])

                if not self.commit(object_type="fabric.ApplianceRole", payload=fabric_appliance_role, detail=detail,
                                   key_attributes=["port_policy", "slot_id", "port_id", "aggregate_port_id"]):
                    failed_to_push_port_policy_attributes = True

        if self.fcoe_port_channels:
            # We now need to push the fabric.FcoeUplinkPcRole object for each FCoE Port Channel configuration
            from intersight.model.fabric_fcoe_uplink_pc_role import FabricFcoeUplinkPcRole
            from intersight.model.fabric_port_identifier import FabricPortIdentifier

            for fcoe_port_channel in self.fcoe_port_channels:
                ports = []
                if fcoe_port_channel["interfaces"]:
                    for interface in fcoe_port_channel["interfaces"]:
                        kwargs = {
                            "object_type": "fabric.PortIdentifier",
                            "class_id": "fabric.PortIdentifier",
                        }
                        if interface["slot_id"] is not None:
                            kwargs["slot_id"] = interface["slot_id"]
                        if interface["aggr_id"] not in [None, 0]:  # We have a breakout port
                            kwargs["port_id"] = interface["aggr_id"]
                            kwargs["aggregate_port_id"] = interface["port_id"]
                        else:
                            kwargs["port_id"] = interface["port_id"]
                            kwargs["aggregate_port_id"] = 0

                        fabric_port_identifier = FabricPortIdentifier(**kwargs)
                        ports.append(fabric_port_identifier)

                kwargs = {
                    "object_type": "fabric.FcoeUplinkPcRole",
                    "class_id": "fabric.FcoeUplinkPcRole",
                    "port_policy": fpp,
                    "ports": ports
                }
                if fcoe_port_channel["pc_id"] is not None:
                    kwargs["pc_id"] = fcoe_port_channel["pc_id"]
                if fcoe_port_channel["admin_speed"] is not None:
                    kwargs["admin_speed"] = fcoe_port_channel["admin_speed"]
                if fcoe_port_channel["fec"] is not None:
                    kwargs["fec"] = fcoe_port_channel["fec"]
                if fcoe_port_channel["enable_25gb_copper_cable_negotiation"]:
                    kwargs["admin_speed"] = "NegAuto25Gbps"
                if fcoe_port_channel["user_label"] is not None:
                    kwargs["user_label"] = fcoe_port_channel["user_label"]

                if fcoe_port_channel["link_aggregation_policy"] is not None:
                    # We first need to identify the Link Aggregation Policy object reference
                    link_aggregation_policy = self.get_live_object(
                        object_name=fcoe_port_channel["link_aggregation_policy"],
                        object_type="fabric.LinkAggregationPolicy"
                    )
                    if link_aggregation_policy:
                        kwargs["link_aggregation_policy"] = link_aggregation_policy
                    else:
                        self.logger(
                            level="warning",
                            message=f"Could not find unique Link Aggregation Policy "
                                    f"'{fcoe_port_channel['link_aggregation_policy']}' "
                                    f"to assign to FCoE Port Channel {fcoe_port_channel['pc_id']}"
                        )
                        self._config.push_summary_manager.add_object_status(
                            obj=self, obj_detail=f"Attaching Link Aggregation Policy "
                                                 f"'{fcoe_port_channel['link_aggregation_policy']}'",
                            obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                            message=f"Failed to find Link Aggregation Policy "
                                    f"'{fcoe_port_channel['link_aggregation_policy']}'"
                        )

                if fcoe_port_channel["link_control_policy"] is not None:
                    # We first need to identify the Link Control Policy object reference
                    link_control_policy = self.get_live_object(
                        object_name=fcoe_port_channel["link_control_policy"],
                        object_type="fabric.LinkControlPolicy"
                    )
                    if link_control_policy:
                        kwargs["link_control_policy"] = link_control_policy
                    else:
                        self.logger(
                            level="warning",
                            message=f"Could not find unique Link Control Policy "
                                    f"'{fcoe_port_channel['link_control_policy']}' "
                                    f"to assign to FCoE Port Channel {fcoe_port_channel['pc_id']}"
                        )
                        self._config.push_summary_manager.add_object_status(
                            obj=self, obj_detail=f"Attaching Link Control Policy "
                                                 f"'{fcoe_port_channel['link_control_policy']}'",
                            obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                            message=f"Failed to find Link Control Policy "
                                    f"'{fcoe_port_channel['link_control_policy']}'"
                        )

                fabric_fcoe_uplink_pc_role = FabricFcoeUplinkPcRole(**kwargs)

                detail = self.name + " - FCoE Port Channel " + str(fcoe_port_channel["pc_id"])
                if not self.commit(object_type="fabric.FcoeUplinkPcRole", payload=fabric_fcoe_uplink_pc_role,
                                   detail=detail, key_attributes=["port_policy", "pc_id"]):
                    failed_to_push_port_policy_attributes = True

        if self.fcoe_uplink_ports:
            # We now need to push the fabric.UplinkFcoeRole object for each SAN Uplink Port configuration
            from intersight.model.fabric_fcoe_uplink_role import FabricFcoeUplinkRole

            for fcoe_uplink_port in self.fcoe_uplink_ports:
                kwargs = {
                    "object_type": "fabric.FcoeUplinkRole",
                    "class_id": "fabric.FcoeUplinkRole",
                    "port_policy": fpp
                }
                if fcoe_uplink_port["slot_id"] is not None:
                    kwargs["slot_id"] = fcoe_uplink_port["slot_id"]
                if fcoe_uplink_port["aggr_id"] not in [None, 0]:  # We have a breakout port
                    kwargs["port_id"] = fcoe_uplink_port["aggr_id"]
                    kwargs["aggregate_port_id"] = fcoe_uplink_port["port_id"]
                else:
                    kwargs["port_id"] = fcoe_uplink_port["port_id"]
                    kwargs["aggregate_port_id"] = 0
                if fcoe_uplink_port["fec"] is not None:
                    kwargs["fec"] = fcoe_uplink_port["fec"]
                if fcoe_uplink_port["admin_speed"] is not None:
                    kwargs["admin_speed"] = fcoe_uplink_port["admin_speed"]
                if fcoe_uplink_port["enable_25gb_copper_cable_negotiation"]:
                    kwargs["admin_speed"] = "NegAuto25Gbps"
                if fcoe_uplink_port["user_label"] is not None:
                    kwargs["user_label"] = fcoe_uplink_port["user_label"]

                if fcoe_uplink_port["link_control_policy"] is not None:
                    # We first need to identify the Link Control Policy object reference
                    link_control_policy = self.get_live_object(
                        object_name=fcoe_uplink_port["link_control_policy"],
                        object_type="fabric.LinkControlPolicy"
                    )
                    if link_control_policy:
                        kwargs["link_control_policy"] = link_control_policy
                    else:
                        if fcoe_uplink_port["aggr_id"]:
                            self.logger(level="warning",
                                        message=f"Could not find unique Link Control Policy "
                                                f"'{fcoe_uplink_port['link_control_policy']}' "
                                                f"to assign to FCoE Uplink Port {fcoe_uplink_port['slot_id']}/"
                                                f"{fcoe_uplink_port['port_id']}/{fcoe_uplink_port['aggr_id']}")
                        else:
                            self.logger(level="warning",
                                        message=f"Could not find unique Link Control Policy "
                                                f"'{fcoe_uplink_port['link_control_policy']}' "
                                                f"to assign to FCoE Uplink Port {fcoe_uplink_port['slot_id']}/"
                                                f"{fcoe_uplink_port['port_id']}")
                        self._config.push_summary_manager.add_object_status(
                            obj=self, obj_detail=f"Attaching Link Control Policy "
                                                 f"'{fcoe_uplink_port['link_control_policy']}'",
                            obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                            message=f"Failed to find Link Control Policy "
                                    f"'{fcoe_uplink_port['link_control_policy']}'"
                        )

                fabric_fcoe_uplink_role = FabricFcoeUplinkRole(**kwargs)

                if fcoe_uplink_port["aggr_id"]:
                    detail = self.name + " - FCoE Uplink Port " + str(fcoe_uplink_port["slot_id"]) + "/" + \
                             str(fcoe_uplink_port["port_id"]) + "/" + str(fcoe_uplink_port["aggr_id"])
                else:
                    detail = self.name + " - FCoE Uplink Port " + str(fcoe_uplink_port["slot_id"]) + "/" + \
                             str(fcoe_uplink_port["port_id"])
                if not self.commit(object_type="fabric.FcoeUplinkRole", payload=fabric_fcoe_uplink_role,
                                   detail=detail, key_attributes=["port_policy", "slot_id", "port_id"]):
                    failed_to_push_port_policy_attributes = True

        if self.lan_port_channels:
            # We now need to push the fabric.UplinkPcRole object for each LAN Port Channel configuration
            from intersight.model.fabric_uplink_pc_role import FabricUplinkPcRole
            from intersight.model.fabric_port_identifier import FabricPortIdentifier

            for lan_port_channel in self.lan_port_channels:
                ports = []
                if lan_port_channel["interfaces"]:
                    for interface in lan_port_channel["interfaces"]:
                        kwargs = {
                            "object_type": "fabric.PortIdentifier",
                            "class_id": "fabric.PortIdentifier",
                        }
                        if interface["slot_id"] is not None:
                            kwargs["slot_id"] = interface["slot_id"]
                        if interface["aggr_id"] not in [None, 0]:  # We have a breakout port
                            kwargs["port_id"] = interface["aggr_id"]
                            kwargs["aggregate_port_id"] = interface["port_id"]
                        else:
                            kwargs["port_id"] = interface["port_id"]
                            kwargs["aggregate_port_id"] = 0

                        fabric_port_identifier = FabricPortIdentifier(**kwargs)
                        ports.append(fabric_port_identifier)

                kwargs = {
                    "object_type": "fabric.UplinkPcRole",
                    "class_id": "fabric.UplinkPcRole",
                    "port_policy": fpp,
                    "ports": ports
                }
                if lan_port_channel["pc_id"] is not None:
                    kwargs["pc_id"] = lan_port_channel["pc_id"]
                if lan_port_channel["admin_speed"] is not None:
                    kwargs["admin_speed"] = lan_port_channel["admin_speed"]
                if lan_port_channel["fec"] is not None:
                    kwargs["fec"] = lan_port_channel["fec"]
                if lan_port_channel["enable_25gb_copper_cable_negotiation"]:
                    kwargs["admin_speed"] = "NegAuto25Gbps"
                if lan_port_channel["user_label"] is not None:
                    kwargs["user_label"] = lan_port_channel["user_label"]

                if lan_port_channel["ethernet_network_group_policies"] is not None:
                    # We first need to identify the Ethernet Network Group Policies objects references
                    kwargs["eth_network_group_policy"] = []
                    for engp in lan_port_channel["ethernet_network_group_policies"]:
                        ethernet_network_group_policy = self.get_live_object(
                            object_name=engp,
                            object_type="fabric.EthNetworkGroupPolicy"
                        )
                        if ethernet_network_group_policy:
                            kwargs["eth_network_group_policy"].append(ethernet_network_group_policy)
                        else:
                            self.logger(level="warning",
                                        message=f"Could not find unique Ethernet Network Group Policy '{engp}' "
                                                f"to assign to LAN Port Channel {lan_port_channel['pc_id']}")
                            self._config.push_summary_manager.add_object_status(
                                obj=self, obj_detail=f"Attaching Ethernet Network Group Policy '{engp}'",
                                obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                                message=f"Failed to find Ethernet Network Group Policy '{engp}'"
                            )

                elif lan_port_channel["ethernet_network_group_policy"] is not None:
                    # We keep this section for compatibility purposes, but "ethernet_network_group_policy" attribute
                    # is deprecated starting with EasyUCS 1.0.2 (replaced by "ethernet_network_group_policies")
                    # We first need to identify the Ethernet Network Group Policy object reference
                    ethernet_network_group_policy = self.get_live_object(
                        object_name=lan_port_channel["ethernet_network_group_policy"],
                        object_type="fabric.EthNetworkGroupPolicy"
                    )
                    if ethernet_network_group_policy:
                        kwargs["eth_network_group_policy"] = [ethernet_network_group_policy]
                    else:
                        self.logger(level="warning",
                                    message=f"Could not find unique Ethernet Network Group Policy "
                                            f"'{lan_port_channel['ethernet_network_group_policy']}' "
                                            f"to assign to LAN Port Channel {lan_port_channel['pc_id']}")
                        self._config.push_summary_manager.add_object_status(
                            obj=self, obj_detail=f"Attaching Ethernet Network Group Policy "
                                                 f"'{lan_port_channel['ethernet_network_group_policy']}'",
                            obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                            message=f"Failed to find Ethernet Network Group Policy "
                                    f"'{lan_port_channel['ethernet_network_group_policy']}'"
                        )

                if lan_port_channel["flow_control_policy"] is not None:
                    # We first need to identify the Flow Control Policy object reference
                    flow_control_policy = self.get_live_object(
                        object_name=lan_port_channel["flow_control_policy"],
                        object_type="fabric.FlowControlPolicy"
                    )
                    if flow_control_policy:
                        kwargs["flow_control_policy"] = flow_control_policy
                    else:
                        self.logger(level="warning",
                                    message=f"Could not find unique Flow Control Policy "
                                            f"'{lan_port_channel['flow_control_policy']}' "
                                            f"to assign to LAN Port Channel {lan_port_channel['pc_id']}")
                        self._config.push_summary_manager.add_object_status(
                            obj=self, obj_detail=f"Attaching Flow Control Policy "
                                                 f"'{lan_port_channel['flow_control_policy']}'",
                            obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                            message=f"Failed to find Flow Control Policy "
                                    f"'{lan_port_channel['flow_control_policy']}'"
                        )

                if lan_port_channel["link_aggregation_policy"] is not None:
                    # We first need to identify the Link Aggregation Policy object reference
                    link_aggregation_policy = self.get_live_object(
                        object_name=lan_port_channel["link_aggregation_policy"],
                        object_type="fabric.LinkAggregationPolicy"
                    )
                    if link_aggregation_policy:
                        kwargs["link_aggregation_policy"] = link_aggregation_policy
                    else:
                        self.logger(level="warning",
                                    message=f"Could not find unique Link Aggregation Policy "
                                            f"'{lan_port_channel['link_aggregation_policy']}' "
                                            f"to assign to LAN Port Channel {lan_port_channel['pc_id']}")
                        self._config.push_summary_manager.add_object_status(
                            obj=self, obj_detail=f"Attaching Link Aggregation Policy "
                                                 f"'{lan_port_channel['link_aggregation_policy']}'",
                            obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                            message=f"Failed to find Link Aggregation Policy "
                                    f"'{lan_port_channel['link_aggregation_policy']}'"
                        )

                if lan_port_channel["link_control_policy"] is not None:
                    # We first need to identify the Link Control Policy object reference
                    link_control_policy = self.get_live_object(
                        object_name=lan_port_channel["link_control_policy"],
                        object_type="fabric.LinkControlPolicy"
                    )
                    if link_control_policy:
                        kwargs["link_control_policy"] = link_control_policy
                    else:
                        self.logger(level="warning",
                                    message=f"Could not find unique Link Control Policy "
                                            f"'{lan_port_channel['link_control_policy']}' "
                                            f"to assign to LAN Port Channel {lan_port_channel['pc_id']}")
                        self._config.push_summary_manager.add_object_status(
                            obj=self, obj_detail=f"Attaching Link Control Policy "
                                                 f"'{lan_port_channel['link_control_policy']}'",
                            obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                            message=f"Failed to find Link Control Policy "
                                    f"'{lan_port_channel['link_control_policy']}'"
                        )

                if lan_port_channel["macsec_policy"] is not None:
                    # We first need to identify the MACsec Policy object reference
                    macsec_policy = self.get_live_object(
                        object_name=lan_port_channel["macsec_policy"],
                        object_type="fabric.MacSecPolicy"
                    )
                    if macsec_policy:
                        kwargs["mac_sec_policy"] = macsec_policy
                    else:
                        self.logger(level="warning",
                                    message=f"Could not find unique MACsec Policy "
                                            f"'{lan_port_channel['macsec_policy']}' "
                                            f"to assign to LAN Port Channel {lan_port_channel['pc_id']}")
                        self._config.push_summary_manager.add_object_status(
                            obj=self, obj_detail=f"Attaching MACsec Policy "
                                                 f"'{lan_port_channel['macsec_policy']}'",
                            obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                            message=f"Failed to find MACsec Policy "
                                    f"'{lan_port_channel['macsec_policy']}'"
                        )

                fabric_uplink_pc_role = FabricUplinkPcRole(**kwargs)

                detail = self.name + " - LAN Port Channel " + str(lan_port_channel["pc_id"])
                if not self.commit(object_type="fabric.UplinkPcRole", payload=fabric_uplink_pc_role, detail=detail,
                                   key_attributes=["port_policy", "pc_id"]):
                    failed_to_push_port_policy_attributes = True

        if self.lan_uplink_ports:
            # We now need to push the fabric.UplinkRole object for each LAN Uplink Port configuration
            from intersight.model.fabric_uplink_role import FabricUplinkRole

            for lan_uplink_port in self.lan_uplink_ports:
                kwargs = {
                    "object_type": "fabric.UplinkRole",
                    "class_id": "fabric.UplinkRole",
                    "port_policy": fpp
                }
                if lan_uplink_port["slot_id"] is not None:
                    kwargs["slot_id"] = lan_uplink_port["slot_id"]
                if lan_uplink_port["aggr_id"] not in [None, 0]:  # We have a breakout port
                    kwargs["port_id"] = lan_uplink_port["aggr_id"]
                    kwargs["aggregate_port_id"] = lan_uplink_port["port_id"]
                else:
                    kwargs["port_id"] = lan_uplink_port["port_id"]
                    kwargs["aggregate_port_id"] = 0
                if lan_uplink_port["fec"] is not None:
                    kwargs["fec"] = lan_uplink_port["fec"]
                if lan_uplink_port["admin_speed"] is not None:
                    kwargs["admin_speed"] = lan_uplink_port["admin_speed"]
                if lan_uplink_port["enable_25gb_copper_cable_negotiation"]:
                    kwargs["admin_speed"] = "NegAuto25Gbps"
                if lan_uplink_port["user_label"] is not None:
                    kwargs["user_label"] = lan_uplink_port["user_label"]

                if lan_uplink_port["ethernet_network_group_policies"] is not None:
                    # We first need to identify the Ethernet Network Group Policies objects references
                    kwargs["eth_network_group_policy"] = []
                    for engp in lan_uplink_port["ethernet_network_group_policies"]:
                        ethernet_network_group_policy = self.get_live_object(
                            object_name=engp,
                            object_type="fabric.EthNetworkGroupPolicy"
                        )
                        if ethernet_network_group_policy:
                            kwargs["eth_network_group_policy"].append(ethernet_network_group_policy)
                        else:
                            if lan_uplink_port["aggr_id"]:
                                self.logger(level="warning",
                                            message=f"Could not find unique Ethernet Network Group Policy '{engp}' "
                                                    f"to assign to LAN Uplink Port {lan_uplink_port['slot_id']}/"
                                                    f"{lan_uplink_port['port_id']}/{lan_uplink_port['aggr_id']}")
                            else:
                                self.logger(level="warning",
                                            message=f"Could not find unique Ethernet Network Group Policy '{engp}' "
                                                    f"to assign to LAN Uplink Port {lan_uplink_port['slot_id']}/"
                                                    f"{lan_uplink_port['port_id']}")
                            self._config.push_summary_manager.add_object_status(
                                obj=self, obj_detail=f"Attaching Ethernet Network Group Policy '{engp}'",
                                obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                                message=f"Failed to find Ethernet Network Group Policy '{engp}'"
                            )

                elif lan_uplink_port["ethernet_network_group_policy"] is not None:
                    # We keep this section for compatibility purposes, but "ethernet_network_group_policy" attribute
                    # is deprecated starting with EasyUCS 1.0.2 (replaced by "ethernet_network_group_policies")
                    # We first need to identify the Ethernet Network Group Policy object reference
                    ethernet_network_group_policy = self.get_live_object(
                        object_name=lan_uplink_port["ethernet_network_group_policy"],
                        object_type="fabric.EthNetworkGroupPolicy"
                    )
                    if ethernet_network_group_policy:
                        kwargs["eth_network_group_policy"] = [ethernet_network_group_policy]
                    else:
                        if lan_uplink_port["aggr_id"]:
                            self.logger(level="warning",
                                        message=f"Could not find unique Ethernet Network Group Policy "
                                                f"'{lan_uplink_port['ethernet_network_group_policy']}' "
                                                f"to assign to LAN Uplink Port {lan_uplink_port['slot_id']}/"
                                                f"{lan_uplink_port['port_id']}/{lan_uplink_port['aggr_id']}")
                        else:
                            self.logger(level="warning",
                                        message=f"Could not find unique Ethernet Network Group Policy "
                                                f"'{lan_uplink_port['ethernet_network_group_policy']}' "
                                                f"to assign to LAN Uplink Port {lan_uplink_port['slot_id']}/"
                                                f"{lan_uplink_port['port_id']}")
                        self._config.push_summary_manager.add_object_status(
                            obj=self, obj_detail=f"Attaching Ethernet Network Group Policy "
                                                 f"'{lan_uplink_port['ethernet_network_group_policy']}'",
                            obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                            message=f"Failed to find Ethernet Network Group Policy "
                                    f"'{lan_uplink_port['ethernet_network_group_policy']}'"
                        )

                if lan_uplink_port["flow_control_policy"] is not None:
                    # We first need to identify the Flow Control Policy object reference
                    flow_control_policy = self.get_live_object(
                        object_name=lan_uplink_port["flow_control_policy"],
                        object_type="fabric.FlowControlPolicy"
                    )
                    if flow_control_policy:
                        kwargs["flow_control_policy"] = flow_control_policy
                    else:
                        if lan_uplink_port["aggr_id"]:
                            self.logger(level="warning",
                                        message=f"Could not find unique Flow Control Policy "
                                                f"'{lan_uplink_port['flow_control_policy']}' "
                                                f"to assign to LAN Uplink Port {lan_uplink_port['slot_id']}/"
                                                f"{lan_uplink_port['port_id']}/{lan_uplink_port['aggr_id']}")
                        else:
                            self.logger(level="warning",
                                        message=f"Could not find unique Flow Control Policy "
                                                f"'{lan_uplink_port['flow_control_policy']}' "
                                                f"to assign to LAN Uplink Port {lan_uplink_port['slot_id']}/"
                                                f"{lan_uplink_port['port_id']}")
                        self._config.push_summary_manager.add_object_status(
                            obj=self, obj_detail=f"Attaching Flow Control Policy "
                                                 f"'{lan_uplink_port['flow_control_policy']}'",
                            obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                            message=f"Failed to find Flow Control Policy "
                                    f"'{lan_uplink_port['flow_control_policy']}'"
                        )

                if lan_uplink_port["link_control_policy"] is not None:
                    # We first need to identify the Link Control Policy object reference
                    link_control_policy = self.get_live_object(
                        object_name=lan_uplink_port["link_control_policy"],
                        object_type="fabric.LinkControlPolicy"
                    )
                    if link_control_policy:
                        kwargs["link_control_policy"] = link_control_policy
                    else:
                        if lan_uplink_port["aggr_id"]:
                            self.logger(level="warning",
                                        message=f"Could not find unique Link Control Policy "
                                                f"'{lan_uplink_port['link_control_policy']}' "
                                                f"to assign to LAN Uplink Port {lan_uplink_port['slot_id']}/"
                                                f"{lan_uplink_port['port_id']}/{lan_uplink_port['aggr_id']}")
                        else:
                            self.logger(level="warning",
                                        message=f"Could not find unique Link Control Policy "
                                                f"'{lan_uplink_port['link_control_policy']}' "
                                                f"to assign to LAN Uplink Port {lan_uplink_port['slot_id']}/"
                                                f"{lan_uplink_port['port_id']}")
                        self._config.push_summary_manager.add_object_status(
                            obj=self, obj_detail=f"Attaching Link Control Policy "
                                                 f"'{lan_uplink_port['link_control_policy']}'",
                            obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                            message=f"Failed to find Link Control Policy "
                                    f"'{lan_uplink_port['link_control_policy']}'"
                        )

                if lan_uplink_port["macsec_policy"] is not None:
                    # We first need to identify the MACsec Policy object reference
                    macsec_policy = self.get_live_object(
                        object_name=lan_uplink_port["macsec_policy"],
                        object_type="fabric.MacSecPolicy"
                    )
                    if macsec_policy:
                        kwargs["mac_sec_policy"] = macsec_policy
                    else:
                        if lan_uplink_port["aggr_id"]:
                            self.logger(level="warning",
                                        message=f"Could not find unique MACsec Policy "
                                                f"'{lan_uplink_port['macsec_policy']}' "
                                                f"to assign to LAN Uplink Port {lan_uplink_port['slot_id']}/"
                                                f"{lan_uplink_port['port_id']}/{lan_uplink_port['aggr_id']}")
                        else:
                            self.logger(level="warning",
                                        message=f"Could not find unique MACsec Policy "
                                                f"'{lan_uplink_port['macsec_policy']}' "
                                                f"to assign to LAN Uplink Port {lan_uplink_port['slot_id']}/"
                                                f"{lan_uplink_port['port_id']}")
                        self._config.push_summary_manager.add_object_status(
                            obj=self, obj_detail=f"Attaching MACsec Policy "
                                                 f"'{lan_uplink_port['macsec_policy']}'",
                            obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                            message=f"Failed to find MACsec Policy "
                                    f"'{lan_uplink_port['macsec_policy']}'"
                        )

                fabric_uplink_role = FabricUplinkRole(**kwargs)

                if lan_uplink_port["aggr_id"]:
                    detail = self.name + " - LAN Uplink Port " + str(lan_uplink_port["slot_id"]) + "/" + \
                             str(lan_uplink_port["port_id"]) + "/" + str(lan_uplink_port["aggr_id"])
                else:
                    detail = self.name + " - LAN Uplink Port " + str(lan_uplink_port["slot_id"]) + "/" + \
                             str(lan_uplink_port["port_id"])

                if not self.commit(object_type="fabric.UplinkRole", payload=fabric_uplink_role, detail=detail,
                                   key_attributes=["port_policy", "slot_id", "port_id", "aggregate_port_id"]):
                    failed_to_push_port_policy_attributes = True

        if self.san_port_channels:
            # We now need to push the fabric.FcUplinkPcRole object for each SAN Port Channel configuration
            from intersight.model.fabric_fc_uplink_pc_role import FabricFcUplinkPcRole
            from intersight.model.fabric_port_identifier import FabricPortIdentifier

            for san_port_channel in self.san_port_channels:
                ports = []
                if san_port_channel["interfaces"]:
                    for interface in san_port_channel["interfaces"]:
                        kwargs = {
                            "object_type": "fabric.PortIdentifier",
                            "class_id": "fabric.PortIdentifier",
                        }
                        if interface["slot_id"] is not None:
                            kwargs["slot_id"] = interface["slot_id"]
                        if interface["aggr_id"] not in [None, 0]:  # We have a breakout port
                            kwargs["port_id"] = interface["aggr_id"]
                            kwargs["aggregate_port_id"] = interface["port_id"]
                        else:
                            kwargs["port_id"] = interface["port_id"]
                            kwargs["aggregate_port_id"] = 0

                        fabric_port_identifier = FabricPortIdentifier(**kwargs)
                        ports.append(fabric_port_identifier)

                kwargs = {
                    "object_type": "fabric.FcUplinkPcRole",
                    "class_id": "fabric.FcUplinkPcRole",
                    "port_policy": fpp,
                    "ports": ports
                }
                if san_port_channel["pc_id"] is not None:
                    kwargs["pc_id"] = san_port_channel["pc_id"]
                if san_port_channel["admin_speed"] is not None:
                    kwargs["admin_speed"] = san_port_channel["admin_speed"]
                if san_port_channel["vsan_id"] is not None:
                    kwargs["vsan_id"] = san_port_channel["vsan_id"]
                if san_port_channel["fill_pattern"] is not None:
                    kwargs["fill_pattern"] = san_port_channel["fill_pattern"]
                if san_port_channel["user_label"] is not None:
                    kwargs["user_label"] = san_port_channel["user_label"]

                fabric_fc_uplink_pc_role = FabricFcUplinkPcRole(**kwargs)

                detail = self.name + " - SAN Port Channel " + str(san_port_channel["pc_id"])
                if not self.commit(object_type="fabric.FcUplinkPcRole", payload=fabric_fc_uplink_pc_role,
                                   detail=detail, key_attributes=["port_policy", "pc_id"]):
                    failed_to_push_port_policy_attributes = True

        if self.san_storage_ports:
            # We now need to push the fabric.StorageFcRole object for each SAN Storage Port configuration
            from intersight.model.fabric_fc_storage_role import FabricFcStorageRole

            for san_storage_port in self.san_storage_ports:
                kwargs = {
                    "object_type": "fabric.FcStorageRole",
                    "class_id": "fabric.FcStorageRole",
                    "port_policy": fpp
                }
                if san_storage_port["slot_id"] is not None:
                    kwargs["slot_id"] = san_storage_port["slot_id"]
                if san_storage_port["aggr_id"] not in [None, 0]:  # We have a breakout port
                    kwargs["port_id"] = san_storage_port["aggr_id"]
                    kwargs["aggregate_port_id"] = san_storage_port["port_id"]
                else:
                    kwargs["port_id"] = san_storage_port["port_id"]
                    kwargs["aggregate_port_id"] = 0
                if san_storage_port["admin_speed"] is not None:
                    kwargs["admin_speed"] = san_storage_port["admin_speed"]
                if san_storage_port["vsan_id"] is not None:
                    kwargs["vsan_id"] = san_storage_port["vsan_id"]
                if san_storage_port["user_label"] is not None:
                    kwargs["user_label"] = san_storage_port["user_label"]

                fabric_fc_storage_role = FabricFcStorageRole(**kwargs)

                if san_storage_port["aggr_id"]:
                    detail = self.name + " - SAN Storage Port " + str(san_storage_port["slot_id"]) + "/" + \
                             str(san_storage_port["port_id"]) + "/" + str(san_storage_port["aggr_id"])
                else:
                    detail = self.name + " - SAN Storage Port " + str(san_storage_port["slot_id"]) + "/" + \
                             str(san_storage_port["port_id"])
                if not self.commit(object_type="fabric.FcStorageRole", payload=fabric_fc_storage_role, detail=detail,
                                   key_attributes=["port_policy", "slot_id", "port_id", "aggregate_port_id"]):
                    failed_to_push_port_policy_attributes = True

        if self.san_uplink_ports:
            # We now need to push the fabric.UplinkFcRole object for each SAN Uplink Port configuration
            from intersight.model.fabric_fc_uplink_role import FabricFcUplinkRole

            for san_uplink_port in self.san_uplink_ports:
                kwargs = {
                    "object_type": "fabric.FcUplinkRole",
                    "class_id": "fabric.FcUplinkRole",
                    "port_policy": fpp
                }
                if san_uplink_port["slot_id"] is not None:
                    kwargs["slot_id"] = san_uplink_port["slot_id"]
                if san_uplink_port["aggr_id"] not in [None, 0]:  # We have a breakout port
                    kwargs["port_id"] = san_uplink_port["aggr_id"]
                    kwargs["aggregate_port_id"] = san_uplink_port["port_id"]
                else:
                    kwargs["port_id"] = san_uplink_port["port_id"]
                    kwargs["aggregate_port_id"] = 0
                if san_uplink_port["fill_pattern"] is not None:
                    kwargs["fill_pattern"] = san_uplink_port["fill_pattern"]
                if san_uplink_port["admin_speed"] is not None:
                    kwargs["admin_speed"] = san_uplink_port["admin_speed"]
                if san_uplink_port["vsan_id"] is not None:
                    kwargs["vsan_id"] = san_uplink_port["vsan_id"]
                if san_uplink_port["user_label"] is not None:
                    kwargs["user_label"] = san_uplink_port["user_label"]

                fabric_fc_uplink_role = FabricFcUplinkRole(**kwargs)

                if san_uplink_port["aggr_id"]:
                    detail = self.name + " - SAN Uplink Port " + str(san_uplink_port["slot_id"]) + "/" + \
                             str(san_uplink_port["port_id"]) + "/" + str(san_uplink_port["aggr_id"])
                else:
                    detail = self.name + " - SAN Uplink Port " + str(san_uplink_port["slot_id"]) + "/" + \
                             str(san_uplink_port["port_id"])
                if not self.commit(object_type="fabric.FcUplinkRole", payload=fabric_fc_uplink_role, detail=detail,
                                   key_attributes=["port_policy", "slot_id", "port_id", "aggregate_port_id"]):
                    failed_to_push_port_policy_attributes = True

        if self.server_ports:
            # We now need to push the fabric.ServerRole object for each Server Port configuration
            from intersight.model.fabric_server_role import FabricServerRole

            for server_port in self.server_ports:
                kwargs = {
                    "object_type": "fabric.ServerRole",
                    "class_id": "fabric.ServerRole",
                    "port_policy": fpp
                }
                if server_port["slot_id"] is not None:
                    kwargs["slot_id"] = server_port["slot_id"]
                if server_port["aggr_id"] not in [None, 0]:  # We have a breakout port
                    kwargs["port_id"] = server_port["aggr_id"]
                    kwargs["aggregate_port_id"] = server_port["port_id"]
                else:
                    kwargs["port_id"] = server_port["port_id"]
                    kwargs["aggregate_port_id"] = 0
                if server_port["connected_device_type"] is not None:
                    kwargs["preferred_device_type"] = server_port["connected_device_type"]
                if server_port["connected_device_id"] is not None:
                    kwargs["preferred_device_id"] = server_port["connected_device_id"]
                if server_port["user_label"] is not None:
                    kwargs["user_label"] = server_port["user_label"]

                fabric_server_role = FabricServerRole(**kwargs)

                if server_port["aggr_id"]:
                    detail = self.name + " - Server Port " + str(server_port["slot_id"]) + "/" + \
                             str(server_port["port_id"]) + "/" + str(server_port["aggr_id"])
                else:
                    detail = self.name + " - Server Port " + str(server_port["slot_id"]) + "/" + \
                             str(server_port["port_id"])

                if not self.commit(object_type="fabric.ServerRole", payload=fabric_server_role, detail=detail,
                                   key_attributes=["port_policy", "slot_id", "port_id", "aggregate_port_id"]):
                    failed_to_push_port_policy_attributes = True

        # We end with LAN/SAN Pin Groups as we need the uplink interfaces to be created first
        if self.lan_pin_groups:
            # We now need to push the fabric.LanPinGroup object for each LAN Pin Group configuration
            from intersight.model.fabric_lan_pin_group import FabricLanPinGroup

            for lan_pin_group in self.lan_pin_groups:
                kwargs = {
                    "object_type": "fabric.LanPinGroup",
                    "class_id": "fabric.LanPinGroup",
                    "name": lan_pin_group["name"],
                    "port_policy": fpp
                }
                if lan_pin_group["slot_id"] is not None:
                    # We need to identify the LAN Uplink Port object reference
                    filter_string = "PortPolicy.Moid eq '" + str(fpp.moid) + "' and SlotId eq " + \
                                    str(lan_pin_group["slot_id"]) + " and PortId eq "
                    if lan_pin_group["aggr_id"] not in [None, 0]:  # We have a breakout port
                        filter_string += str(lan_pin_group["aggr_id"]) + " and AggregatePortId eq " + \
                                         str(lan_pin_group["port_id"])
                    else:
                        filter_string += str(lan_pin_group["port_id"])
                    pin_target_interface_role = self.get_live_object(
                        query_filter=filter_string, object_type="fabric.UplinkRole"
                    )
                    if pin_target_interface_role:
                        kwargs["pin_target_interface_role"] = pin_target_interface_role
                    else:
                        if lan_pin_group["aggr_id"]:
                            self.logger(level="warning",
                                        message=f"Could not find unique LAN Uplink Port {lan_pin_group['slot_id']}/"
                                                f"{lan_pin_group['port_id']}/{lan_pin_group['aggr_id']} "
                                                f"to map to LAN Pin Group '{lan_pin_group['name']}'")
                        else:
                            self.logger(level="warning",
                                        message=f"Could not find unique LAN Uplink Port {lan_pin_group['slot_id']}/"
                                                f"{lan_pin_group['port_id']} to map to LAN Pin Group "
                                                f"'{lan_pin_group['name']}'")

                elif lan_pin_group["pc_id"] is not None:
                    # We need to identify the LAN Port-Channel object reference
                    filter_string = "PortPolicy.Moid eq '" + str(fpp.moid) + "' and PcId eq " + \
                                    str(lan_pin_group["pc_id"])
                    pin_target_interface_role = self.get_live_object(
                        query_filter=filter_string, object_type="fabric.UplinkPcRole"
                    )
                    if pin_target_interface_role:
                        kwargs["pin_target_interface_role"] = pin_target_interface_role
                    else:
                        self.logger(level="warning",
                                    message=f"Could not find unique LAN Port-Channel PC-"
                                            f"{lan_pin_group['pc_id']} to map to LAN Pin Group "
                                            f"'{lan_pin_group['name']}'")

                fabric_lan_pin_group = FabricLanPinGroup(**kwargs)

                if lan_pin_group["slot_id"]:
                    if lan_pin_group["aggr_id"]:
                        detail = self.name + " - LAN Pin Group '" + str(lan_pin_group["name"]) + "' (" + \
                                 str(lan_pin_group["slot_id"]) + "/" + str(lan_pin_group["port_id"]) + "/" + \
                                 str(lan_pin_group["aggr_id"]) + ")"
                    else:
                        detail = self.name + " - LAN Pin Group '" + str(lan_pin_group["name"]) + "' (" + \
                                 str(lan_pin_group["slot_id"]) + "/" + str(lan_pin_group["port_id"]) + ")"
                else:
                    detail = self.name + " - LAN Pin Group '" + str(lan_pin_group["name"]) + "' (PC-" + \
                             str(lan_pin_group["pc_id"]) + ")"

                if not self.commit(object_type="fabric.LanPinGroup", payload=fabric_lan_pin_group, detail=detail,
                                   key_attributes=["port_policy", "pin_target_interface_role"]):
                    failed_to_push_port_policy_attributes = True

        if self.san_pin_groups:
            # We now need to push the fabric.SanPinGroup object for each SAN Pin Group configuration
            from intersight.model.fabric_san_pin_group import FabricSanPinGroup

            for san_pin_group in self.san_pin_groups:
                kwargs = {
                    "object_type": "fabric.SanPinGroup",
                    "class_id": "fabric.SanPinGroup",
                    "name": san_pin_group["name"],
                    "port_policy": fpp
                }
                if san_pin_group["slot_id"] is not None:
                    # We need to identify the SAN/FCoE Uplink Port object reference
                    filter_string = "PortPolicy.Moid eq '" + str(fpp.moid) + "' and SlotId eq " + \
                                    str(san_pin_group["slot_id"]) + " and PortId eq "
                    if san_pin_group["aggr_id"] not in [None, 0]:  # We have a breakout port
                        filter_string += str(san_pin_group["aggr_id"]) + " and AggregatePortId eq " + \
                                         str(san_pin_group["port_id"])
                    else:
                        filter_string += str(san_pin_group["port_id"])
                    if san_pin_group["fcoe"]:
                        object_type = "fabric.FcoeUplinkRole"
                    else:
                        object_type = "fabric.FcUplinkRole"
                    pin_target_interface_role = self.get_live_object(
                        query_filter=filter_string, object_type=object_type
                    )
                    if pin_target_interface_role:
                        kwargs["pin_target_interface_role"] = pin_target_interface_role
                    else:
                        if san_pin_group["fcoe"]:
                            port_type = "FCoE"
                        else:
                            port_type = "SAN"
                        if san_pin_group["aggr_id"]:
                            self.logger(level="warning",
                                        message=f"Could not find unique {port_type} Uplink Port "
                                                f"{san_pin_group['slot_id']}/"
                                                f"{san_pin_group['port_id']}/{san_pin_group['aggr_id']} "
                                                f"to map to SAN Pin Group '{san_pin_group['name']}'")
                        else:
                            self.logger(level="warning",
                                        message=f"Could not find unique {port_type} Uplink Port "
                                                f"{san_pin_group['slot_id']}/"
                                                f"{san_pin_group['port_id']} to map to SAN Pin Group "
                                                f"'{san_pin_group['name']}'")

                elif san_pin_group["pc_id"] is not None:
                    # We need to identify the SAN Port-Channel object reference
                    filter_string = "PortPolicy.Moid eq '" + str(fpp.moid) + "' and PcId eq " + \
                                    str(san_pin_group["pc_id"])
                    if san_pin_group["fcoe"]:
                        object_type = "fabric.FcoeUplinkPcRole"
                    else:
                        object_type = "fabric.FcUplinkPcRole"
                    pin_target_interface_role = self.get_live_object(
                        query_filter=filter_string, object_type=object_type
                    )
                    if pin_target_interface_role:
                        kwargs["pin_target_interface_role"] = pin_target_interface_role
                    else:
                        if san_pin_group["fcoe"]:
                            port_type = "FCoE"
                        else:
                            port_type = "SAN"
                        self.logger(level="warning",
                                    message=f"Could not find unique {port_type} Port-Channel "
                                            f"PC-{san_pin_group['pc_id']} "
                                            f"to map to SAN Pin Group '{san_pin_group['name']}'")

                fabric_san_pin_group = FabricSanPinGroup(**kwargs)

                if san_pin_group["slot_id"]:
                    if san_pin_group["aggr_id"]:
                        detail = self.name + " - SAN Pin Group '" + str(san_pin_group["name"]) + "' (" + \
                                 str(san_pin_group["slot_id"]) + "/" + str(san_pin_group["port_id"]) + "/" + \
                                 str(san_pin_group["aggr_id"]) + ")"
                    else:
                        detail = self.name + " - SAN Pin Group '" + str(san_pin_group["name"]) + "' (" + \
                                 str(san_pin_group["slot_id"]) + "/" + str(san_pin_group["port_id"]) + ")"
                else:
                    detail = self.name + " - SAN Pin Group '" + str(san_pin_group["name"]) + "' (PC-" + \
                             str(san_pin_group["pc_id"]) + ")"

                if not self.commit(object_type="fabric.SanPinGroup", payload=fabric_san_pin_group, detail=detail,
                                   key_attributes=["port_policy", "pin_target_interface_role"]):
                    failed_to_push_port_policy_attributes = True

        if failed_to_push_port_policy_attributes:
            return False
        return True


class IntersightFabricSwitchControlPolicy(IntersightConfigObject):
    _CONFIG_NAME = "Switch Control Policy"
    _CONFIG_SECTION_NAME = "switch_control_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "fabric.SwitchControlPolicy"

    def __init__(self, parent=None, fabric_switch_control_policy=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=fabric_switch_control_policy)

        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.fabric_port_channel_vhba_reset = None
        self.enable_aes_encryption_key = None
        self.aes_encryption_key = None
        self.link_control_global_settings = None
        self.mac_address_table_aging = None
        self.mac_aging_time = None
        self.disable_mac_address_learning_vlans = None
        self.name = self.get_attribute(attribute_name="name")
        self.reserved_vlan_start_id = self.get_attribute(attribute_name="reserved_vlan_start_id")
        self.switching_mode = None
        self.target_platform = self.get_attribute(attribute_name="target_platform")
        self.enable_jumbo_frames = None
        self.vlan_port_count_optimization = self.get_attribute(attribute_name="vlan_port_optimization_enabled",
                                                               attribute_secondary_name="vlan_port_count_optimization")

        if self._config.load_from == "live":
            if hasattr(self._object, "fabric_pc_vhba_reset"):
                if self._object.fabric_pc_vhba_reset in ["Disabled"]:
                    self.fabric_port_channel_vhba_reset = False
                elif self._object.fabric_pc_vhba_reset in ["Enabled"]:
                    self.fabric_port_channel_vhba_reset = True
            if hasattr(self._object, "mac_aging_settings"):
                if hasattr(self._object.mac_aging_settings, "mac_aging_option"):
                    self.mac_address_table_aging = self._object.mac_aging_settings.mac_aging_option
                    if self.mac_address_table_aging in ["Custom"]:
                        self.mac_aging_time = self._object.mac_aging_settings.mac_aging_time
            if hasattr(self._object, "udld_settings"):
                if self._object.udld_settings:
                    self.link_control_global_settings = {
                        "message_interval": self._object.udld_settings.message_interval,
                        "recovery_action": self._object.udld_settings.recovery_action
                    }
            self.switching_mode = {"ethernet": None, "fc": None}
            if hasattr(self._object, "ethernet_switching_mode"):
                if self._object.ethernet_switching_mode:
                    self.switching_mode["ethernet"] = self._object.ethernet_switching_mode
                    if self._object.ethernet_switching_mode == "switch":
                        if hasattr(self._object, "mac_learning_settings"):
                            if self._object.mac_learning_settings:
                                self.disable_mac_address_learning_vlans = self._object.mac_learning_settings.disabled_vlans
            self.enable_aes_encryption_key = False
            if hasattr(self._object, "is_aes_primary_key_set") and self._object.is_aes_primary_key_set:
                self.enable_aes_encryption_key = True
                if self._object.is_aes_primary_key_set:
                    self.logger(level="warning",
                                message="AES Encryption Key of " + self._CONFIG_NAME + " '" + self.name +
                                        "' can't be exported")
            if hasattr(self._object, "fc_switching_mode"):
                if self._object.fc_switching_mode:
                    self.switching_mode["fc"] = self._object.fc_switching_mode
            if self.target_platform == "Unified Edge" and hasattr(self._object, "enable_jumbo_frame"):
                self.enable_jumbo_frames = self._object.enable_jumbo_frame

        elif self._config.load_from == "file":
            for attribute in ["aes_encryption_key", "disable_mac_address_learning_vlans", "enable_aes_encryption_key",
                              "enable_jumbo_frames","fabric_port_channel_vhba_reset", "link_control_global_settings",
                              "mac_address_table_aging", "mac_aging_time","switching_mode"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

        self.clean_object()

    def is_valid_aes_primary_key(self, key_value=None):
        """
        Validates whether the provided value is suitable for 'aes_primary_key' based on its pattern:
        - Empty string is allowed
        - Otherwise, must be 16 to 64 characters with no spaces or double quotes.

        :param key_value: String to validate as 'aes_primary_key'
        :return: True if valid, False otherwise
        """
        import re
        if key_value is None:
            return False

        pattern = r'^$|^[^"\s]{16,64}$'
        if re.match(pattern, key_value):
            return True
        return False

    def clean_object(self):
        # We use this to make sure all options of Link Control Global Settings are set to None if not present
        if self.link_control_global_settings:
            for attribute in ["message_interval", "recovery_action"]:
                if attribute not in self.link_control_global_settings:
                    self.link_control_global_settings[attribute] = None

        # We use this to make sure all options of Switching Mode are set to None if not present
        if self.switching_mode:
            for attribute in ["ethernet", "fc"]:
                if attribute not in self.switching_mode:
                    self.switching_mode[attribute] = None

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.fabric_switch_control_policy import FabricSwitchControlPolicy

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
        if self.target_platform is not None:
            kwargs["target_platform"] = self.target_platform
        if self.enable_jumbo_frames is not None:
            kwargs["enable_jumbo_frame"] = self.enable_jumbo_frames
        if self.fabric_port_channel_vhba_reset is not None:
            if self.fabric_port_channel_vhba_reset is True:
                kwargs["fabric_pc_vhba_reset"] = "Enabled"
            elif self.fabric_port_channel_vhba_reset is False:
                kwargs["fabric_pc_vhba_reset"] = "Disabled"
        if self.enable_aes_encryption_key:
            random_password = password_generator(password_length=16)
            if self.aes_encryption_key is not None:
                kwargs["aes_primary_key"] = self.aes_encryption_key
            elif random_password:
                kwargs["aes_primary_key"] = random_password
                self.logger(
                    level="debug",
                    message="Using randomly generated password for field 'aes_primary_key' of "
                            "object fabric.SwitchControlPolicy"
                )
            else:
                self.logger(
                    level="warning",
                    message="No aes_primary_key provided for field 'aes_primary_key' of object "
                            "fabric.SwitchControlPolicy"
                )
        if self.reserved_vlan_start_id is not None:
            kwargs["reserved_vlan_start_id"] = self.reserved_vlan_start_id
        if self.vlan_port_count_optimization is not None:
            kwargs["vlan_port_optimization_enabled"] = self.vlan_port_count_optimization
        if self.mac_address_table_aging is not None:
            from intersight.model.fabric_mac_aging_settings import FabricMacAgingSettings

            kwargs_mac_aging_settings = {
                "object_type": "fabric.MacAgingSettings",
                "class_id": "fabric.MacAgingSettings",
                "mac_aging_option": self.mac_address_table_aging
            }
            if self.mac_address_table_aging in ["Custom"]:
                if self.mac_aging_time is not None:
                    kwargs_mac_aging_settings["mac_aging_time"] = self.mac_aging_time

            kwargs["mac_aging_settings"] = FabricMacAgingSettings(**kwargs_mac_aging_settings)

        if self.link_control_global_settings is not None:
            from intersight.model.fabric_udld_global_settings import FabricUdldGlobalSettings

            kwargs_link_control_global_settings = {
                "object_type": "fabric.UdldGlobalSettings",
                "class_id": "fabric.UdldGlobalSettings"
            }
            if "message_interval" in self.link_control_global_settings:
                kwargs_link_control_global_settings["message_interval"] = \
                    self.link_control_global_settings["message_interval"]
            if "recovery_action" in self.link_control_global_settings:
                kwargs_link_control_global_settings["recovery_action"] = \
                    self.link_control_global_settings["recovery_action"]

            kwargs["udld_settings"] = FabricUdldGlobalSettings(**kwargs_link_control_global_settings)

        if self.switching_mode is not None:
            if self.switching_mode.get("ethernet"):
                kwargs["ethernet_switching_mode"] = self.switching_mode["ethernet"]
            if self.switching_mode.get("fc"):
                kwargs["fc_switching_mode"] = self.switching_mode["fc"]

        if self.disable_mac_address_learning_vlans is not None:
            if self.switching_mode.get("ethernet") == "switch":
                from intersight.model.fabric_mac_learning_settings import FabricMacLearningSettings

                kwargs_mac_learning_settings = {
                    "object_type": "fabric.MacLearningSettings",
                    "class_id": "fabric.MacLearningSettings",
                    "disabled_vlans": self.disable_mac_address_learning_vlans
                }
                kwargs["mac_learning_settings"] = FabricMacLearningSettings(**kwargs_mac_learning_settings)

        fabric_switch_control_policy = FabricSwitchControlPolicy(**kwargs)

        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=fabric_switch_control_policy,
                           detail=self.name):
            return False

        return True


class IntersightFabricSystemQosPolicy(IntersightConfigObject):
    _CONFIG_NAME = "System QoS Policy"
    _CONFIG_SECTION_NAME = "system_qos_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "fabric.SystemQosPolicy"

    def __init__(self, parent=None, fabric_system_qos_policy=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=fabric_system_qos_policy)

        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.name = self.get_attribute(attribute_name="name")
        self.target_platform = self.get_attribute(attribute_name="target_platform")
        self.classes = None
        self.watchdog_enabled = None
        self.pfc_watchdog_configuration = None

        if self._config.load_from == "live":
            self.classes = self._get_classes()
            self.pfc_watchdog_configuration = self._get_pfc_watchdog()

        elif self._config.load_from == "file":
            for attribute in ["classes", "pfc_watchdog_configuration", "watchdog_enabled"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

            # We use this to make sure all options of a QoS class are set to None if they are not present
            if self.classes:
                for qos_class in self.classes:
                    for attribute in ["cos", "mtu", "multicast_optimized", "packet_drop", "priority", "state",
                                      "weight"]:
                        if attribute not in qos_class:
                            qos_class[attribute] = None

            # We use this to make sure all options of the pfc_watchdog_configuration are set to None if not present
            if self.pfc_watchdog_configuration:
                for attribute in ["shutdown_multiplier", "watchdog_interval"]:
                    if attribute not in self.pfc_watchdog_configuration:
                        self.pfc_watchdog_configuration[attribute] = None

            if self.watchdog_enabled is not True:
                self.pfc_watchdog_configuration = None

    def _get_classes(self):
        # Fetches the QoS Classes configuration of a System QoS Policy
        if hasattr(self._object, "classes"):
            classes = []
            for fabric_qos_class in self._object.classes:
                classes.append({"priority": fabric_qos_class.name, "state": fabric_qos_class.admin_state,
                                "cos": fabric_qos_class.cos, "packet_drop": fabric_qos_class.packet_drop,
                                "weight": fabric_qos_class.weight, "mtu": fabric_qos_class.mtu,
                                "multicast_optimized": fabric_qos_class.multicast_optimize})

            return classes

        return None

    def _get_pfc_watchdog(self):
        # Fetches the PFC Watchdog configuration of a System QoS Policy
        if hasattr(self._object, "pfc_watchdog") and self._object.pfc_watchdog:
            pfc_watchdog = self._object.pfc_watchdog
            self.watchdog_enabled = pfc_watchdog.is_watchdog_enabled
            if self.watchdog_enabled:
                pfc_watchdog_dict = {}
                if hasattr(pfc_watchdog, "watchdog_interval"):
                    pfc_watchdog_dict["watchdog_interval"] = pfc_watchdog.watchdog_interval
                if hasattr(pfc_watchdog, "shutdown_multiplier"):
                    pfc_watchdog_dict["shutdown_multiplier"] = pfc_watchdog.shutdown_multiplier
                return pfc_watchdog_dict

        return None

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.fabric_system_qos_policy import FabricSystemQosPolicy

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        # We first need to push the main fabric.SystemQosPolicy object
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
        if self.target_platform is not None:
            kwargs["target_platform"] = self.target_platform

        fabric_system_qos_policy = FabricSystemQosPolicy(**kwargs)

        fsqp = self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=fabric_system_qos_policy,
                           detail=self.name)
        if not fsqp:
            return False

        # EASYUCS-891: In case the parent System QoS Policy object already exists, we should not be overwriting it if
        # overwrite flag is disabled (i.e. status="skipped"). As such, we should check for its presence before
        # doing anything, and if it exists, we should exit the `push_object()` function.
        if self._config.push_summary_manager.get_last_object_status(obj=self) in ["skipped"] and \
                not getattr(self._config, "update_existing_intersight_objects", False):
            return True

        # We now create the fabric.QosClass objects for each QoS class
        classes = []
        if self.classes:
            from intersight.model.fabric_qos_class import FabricQosClass
            for qos_class in self.classes:
                kwargs = {
                    "object_type": "fabric.QosClass",
                    "class_id": "fabric.QosClass"
                }
                if qos_class["priority"] is not None:
                    kwargs["name"] = qos_class["priority"]
                if qos_class["state"] is not None:
                    kwargs["admin_state"] = qos_class["state"]
                if qos_class["cos"] is not None:
                    kwargs["cos"] = qos_class["cos"]
                if qos_class["packet_drop"] is not None:
                    kwargs["packet_drop"] = qos_class["packet_drop"]
                if qos_class["weight"] is not None:
                    kwargs["weight"] = qos_class["weight"]
                if qos_class["mtu"] is not None:
                    kwargs["mtu"] = qos_class["mtu"]
                if qos_class["multicast_optimized"] is not None:
                    kwargs["multicast_optimize"] = qos_class["multicast_optimized"]

                classes.append(FabricQosClass(**kwargs))

        # Handling PFC Watchdog configuration if it is enabled
        pfc_watchdog = None
        if self.watchdog_enabled is not None:
            from intersight.model.fabric_pfc_watch_dog import FabricPfcWatchDog
            kwargs_pfc_watchdog = {
                "class_id": "fabric.PfcWatchDog",
                "object_type": "fabric.PfcWatchDog",
                "is_watchdog_enabled": self.watchdog_enabled
            }
            if self.watchdog_enabled and self.pfc_watchdog_configuration:
                if "watchdog_interval" in self.pfc_watchdog_configuration:
                    kwargs_pfc_watchdog["watchdog_interval"] = self.pfc_watchdog_configuration["watchdog_interval"]
                if "shutdown_multiplier" in self.pfc_watchdog_configuration:
                    kwargs_pfc_watchdog["shutdown_multiplier"] = self.pfc_watchdog_configuration[
                        "shutdown_multiplier"]

            pfc_watchdog = FabricPfcWatchDog(**kwargs_pfc_watchdog)

        # We now assign the fabric.QosClass/pfc_watchdog objects to the already created fabric.SystemQosPolicy object
        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": self.get_parent_org_relationship(),
            "moid": fsqp.moid,
        }
        if self.name is not None:
            kwargs["name"] = self.name
        if classes:
            kwargs["classes"] = classes
        if pfc_watchdog:
            kwargs["pfc_watchdog"] = pfc_watchdog

        fabric_system_qos_policy = FabricSystemQosPolicy(**kwargs)

        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=fabric_system_qos_policy,
                           detail=self.name, modify_present=True):
            return False

        return True


class IntersightFabricVlanPolicy(IntersightConfigObject):
    _CONFIG_NAME = "VLAN Policy"
    _CONFIG_SECTION_NAME = "vlan_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "fabric.EthNetworkPolicy"
    _POLICY_MAPPING_TABLE = {
        "vlans": [
            {
                "multicast_policy": IntersightFabricMulticastPolicy
            }
        ]
    }

    def __init__(self, parent=None, fabric_eth_network_policy=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=fabric_eth_network_policy)

        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.name = self.get_attribute(attribute_name="name")
        self.target_platform = self.get_attribute(attribute_name="target_platform")
        self.vlans = None

        if self._config.load_from == "live":
            self.vlans = self._get_vlans()

        elif self._config.load_from == "file":
            for attribute in ["vlans"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

        self.clean_object()

    def _get_vlans(self):
        # Fetches the VLANs configuration of a VLAN Policy
        if "fabric_vlan" in self._config.sdk_objects:
            vlans = []
            for fabric_vlan in self._config.sdk_objects["fabric_vlan"]:
                if hasattr(fabric_vlan, "eth_network_policy"):
                    if fabric_vlan.eth_network_policy.moid == self._moid:
                        sharing_type = None
                        primary_vlan_id = None
                        multicast_policy = None
                        if fabric_vlan.sharing_type not in ["None"]:
                            sharing_type = fabric_vlan.sharing_type
                            if fabric_vlan.sharing_type not in ["None", "Primary"]:
                                # Private VLAN ID attribute is only applicable for Community & Isolated sharing types
                                primary_vlan_id = fabric_vlan.primary_vlan_id
                        else:
                            # We only fetch the Multicast Policy if there is no Private VLAN config
                            if fabric_vlan.multicast_policy:
                                multicast_policy = self._get_policy_name(policy=fabric_vlan.multicast_policy)
                        if multicast_policy:
                            vlans.append({"name": fabric_vlan.name, "id": fabric_vlan.vlan_id,
                                          "auto_allow_on_uplinks": fabric_vlan.auto_allow_on_uplinks,
                                          "native_vlan": fabric_vlan.is_native,
                                          "multicast_policy": multicast_policy,
                                          "sharing_type": sharing_type,
                                          "primary_vlan_id": primary_vlan_id})
                        else:
                            if sharing_type:
                                vlans.append({"name": fabric_vlan.name, "id": fabric_vlan.vlan_id,
                                              "auto_allow_on_uplinks": fabric_vlan.auto_allow_on_uplinks,
                                              "native_vlan": fabric_vlan.is_native,
                                              "sharing_type": sharing_type,
                                              "primary_vlan_id": primary_vlan_id})
                            else:
                                vlans.append({"name": fabric_vlan.name, "id": fabric_vlan.vlan_id,
                                              "auto_allow_on_uplinks": fabric_vlan.auto_allow_on_uplinks,
                                              "native_vlan": fabric_vlan.is_native,
                                              "multicast_policy": "",
                                              "sharing_type": sharing_type,
                                              "primary_vlan_id": primary_vlan_id})

            return vlans

        return None

    def clean_object(self):
        # We use this to make sure all options of a VLAN are set to None if they are not present
        if self.vlans:
            for vlan in self.vlans:
                for attribute in ["auto_allow_on_uplinks", "id", "multicast_policy", "name", "native_vlan",
                                  "primary_vlan_id", "sharing_type"]:
                    if attribute not in vlan:
                        vlan[attribute] = None

    @staticmethod
    def _find_overlapping_vlans(existing_vlans=None, to_be_pushed_vlans=None):
        """
        Function to find the overlapping and non overlapping VLANs between the live device and the config file
        :param existing_vlans: Object of type [fabric.Vlan,...]
        :param to_be_pushed_vlans: List of vlans from the config file
        :return: overlapping_vlans and non overlapping_vlans lists (sorted by VLAN ID)
        """
        # If there are no 'existing_vlans' then there are no overlapping vlans and all are non overlapping vlans.
        # And if there are no 'to_be_pushed_vlans' then also there are no overlapping vlans.
        if not existing_vlans or not to_be_pushed_vlans:
            return [], to_be_pushed_vlans

        overlapping_vlans = []
        non_overlapping_vlans = []

        existing_vlans_ids = [device_vlan.vlan_id for device_vlan in existing_vlans]
        for config_vlan in to_be_pushed_vlans:
            if config_vlan["id"] in existing_vlans_ids:
                overlapping_vlans.append(config_vlan)
            else:
                non_overlapping_vlans.append(config_vlan)

        # Sorting the VLANs in the descending order of sharing type and ascending order of VLAN IDs. We do this to make
        # sure to push the "Primary" VLANs first and then the rest of the VLANs.
        overlapping_vlans.sort(key=lambda vlan: (str(vlan["sharing_type"]), -vlan["id"]), reverse=True)
        non_overlapping_vlans.sort(key=lambda vlan: (str(vlan["sharing_type"]), -vlan["id"]), reverse=True)

        return overlapping_vlans, non_overlapping_vlans

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.fabric_eth_network_policy import FabricEthNetworkPolicy

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        # We first need to push the main fabric.EthNetworkPolicy object
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
        if self.target_platform is not None:
            kwargs["target_platform"] = self.target_platform

        fabric_eth_network_policy = FabricEthNetworkPolicy(**kwargs)

        fenp = self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=fabric_eth_network_policy,
                           detail=self.name, return_relationship=True)
        if not fenp:
            return False

        # For pushing 1000s of VLANs we follow the same procedure as Intersight UI.
        # We first find the existing VLANs in the VLAN policy. Using existing VLANs (fenp_vlans) and the VLANs
        # which needs to be pushed (self.vlans), we try to create a list of VLANs which needs to be
        # updated (overlapping VLANs) and VLANs which needs to be newly created (non overlapping VLANs).
        # - VLANs which needs to be updated (Overlapping VLANs) have to be individually pushed to intersight.
        # - VLANs which needs to be newly created (non Overlapping VLANs) are bulk pushed.

        # Get the VLANs associated with the above Fabric Ethernet Network Policy
        fenp_vlans = self._device.query(object_type="fabric.Vlan", filter=f"EthNetworkPolicy.Moid eq '{fenp.moid}'")

        # Find overlapping and non overlapping VLANs between fenp_vlans and self.vlans
        overlapping_vlans, non_overlapping_vlans = self._find_overlapping_vlans(existing_vlans=fenp_vlans,
                                                                                to_be_pushed_vlans=self.vlans)

        # VLANs which needs to be newly created (Non Overlapping VLANs) are bulk pushed.
        if non_overlapping_vlans:
            # We now need to bulk push the fabric.Vlan object for each VLAN in the list
            from intersight.model.bulk_request import BulkRequest
            from intersight.model.bulk_sub_request import BulkSubRequest
            from intersight.model.mo_base_mo import MoBaseMo

            bulk_request_kwargs = {
                "uri": "/v1/fabric/Vlans",
                "verb": "POST",
                "requests": []
            }
            requests = []

            for vlan in non_overlapping_vlans:
                # We first need to identify the Multicast Policy object reference
                multicast_policy_relationship = None
                if vlan.get("multicast_policy"):
                    fabric_multicast_policy = self.get_live_object(
                        object_name=vlan["multicast_policy"],
                        object_type="fabric.MulticastPolicy"
                    )
                    if fabric_multicast_policy:
                        multicast_policy_relationship = fabric_multicast_policy
                    else:
                        self.logger(level="warning",
                                    message="Could not find Multicast Policy '" + vlan["multicast_policy"] +
                                            "' to assign to VLAN " + vlan["name"])
                        self._config.push_summary_manager.add_object_status(
                            obj=self, obj_detail=f"Attaching Multicast Policy '{vlan['multicast_policy']}'",
                            obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                            message=f"Failed to find Multicast Policy '{vlan['multicast_policy']}'"
                        )

                body_kwargs = {
                    "class_id": "fabric.Vlan",
                    "object_type": "fabric.Vlan",
                    "multicast_policy": multicast_policy_relationship,
                    "eth_network_policy": fenp
                }
                if vlan["name"] is not None:
                    body_kwargs["name"] = vlan["name"]
                if vlan["id"] is not None:
                    body_kwargs["vlan_id"] = vlan["id"]
                if vlan["native_vlan"] is not None:
                    body_kwargs["is_native"] = vlan["native_vlan"]
                if vlan["auto_allow_on_uplinks"] is not None:
                    body_kwargs["auto_allow_on_uplinks"] = vlan["auto_allow_on_uplinks"]
                if vlan["sharing_type"] is not None:
                    body_kwargs["sharing_type"] = vlan["sharing_type"]
                else:
                    body_kwargs["sharing_type"] = "None"
                if vlan["primary_vlan_id"] is not None:
                    body_kwargs["primary_vlan_id"] = vlan["primary_vlan_id"]

                body = MoBaseMo(**body_kwargs)

                sub_request_kwargs = {
                    "object_type": "bulk.RestSubRequest",
                    "class_id": "bulk.RestSubRequest",
                    "body": body
                }

                sub_request = BulkSubRequest(**sub_request_kwargs)

                requests.append(sub_request)

            # Bulk API can send maximum 100 requests per call. So we send the requests in groups of 100.
            start = 0
            end = 100
            while start < len(requests):
                start_vlan_id = non_overlapping_vlans[start]["id"]
                if end - 1 < len(non_overlapping_vlans):
                    end_vlan_id = non_overlapping_vlans[end - 1]["id"]
                else:
                    end_vlan_id = non_overlapping_vlans[-1]["id"]
                bulk_request_kwargs["requests"] = requests[start:end]
                bulk_request = BulkRequest(**bulk_request_kwargs)

                detail = f"{self.name} - {len(bulk_request_kwargs['requests'])} VLANs Between VLAN IDs " \
                         f"({start_vlan_id}, {end_vlan_id})"
                self.commit(object_type="bulk.Request", payload=bulk_request, detail=detail, key_attributes=[])
                start = end
                end += 100

        # VLANs which needs to be updated (Overlapping VLANs) have to be individually pushed to intersight.
        if overlapping_vlans:
            # We now need to push the fabric.Vlan object for each VLAN in the list
            from intersight.model.fabric_vlan import FabricVlan

            for vlan in overlapping_vlans:
                # We first need to identify the Multicast Policy object reference
                multicast_policy_relationship = None
                if vlan.get("multicast_policy"):
                    fabric_multicast_policy = self.get_live_object(
                        object_name=vlan["multicast_policy"],
                        object_type="fabric.MulticastPolicy"
                    )
                    if fabric_multicast_policy:
                        multicast_policy_relationship = fabric_multicast_policy
                    else:
                        self.logger(level="warning",
                                    message="Could not find Multicast Policy '" + vlan["multicast_policy"] +
                                            "' to assign to VLAN " + vlan["name"])
                        self._config.push_summary_manager.add_object_status(
                            obj=self, obj_detail=f"Attaching Multicast Policy '{vlan['multicast_policy']}'",
                            obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                            message=f"Failed to find Multicast Policy '{vlan['multicast_policy']}'"
                        )

                kwargs = {
                    "object_type": "fabric.Vlan",
                    "class_id": "fabric.Vlan",
                    "multicast_policy": multicast_policy_relationship,
                    "eth_network_policy": fenp
                }
                if vlan["name"] is not None:
                    kwargs["name"] = vlan["name"]
                if vlan["id"] is not None:
                    kwargs["vlan_id"] = vlan["id"]
                if vlan["native_vlan"] is not None:
                    kwargs["is_native"] = vlan["native_vlan"]
                if vlan["auto_allow_on_uplinks"] is not None:
                    kwargs["auto_allow_on_uplinks"] = vlan["auto_allow_on_uplinks"]
                if vlan["sharing_type"] is not None:
                    kwargs["sharing_type"] = vlan["sharing_type"]
                else:
                    kwargs["sharing_type"] = "None"
                if vlan["primary_vlan_id"] is not None:
                    kwargs["primary_vlan_id"] = vlan["primary_vlan_id"]

                fabric_vlan = FabricVlan(**kwargs)

                detail = self.name + " - VLAN " + str(vlan["name"])
                if vlan.get("id", None) == 1:
                    # We always overwrite VLAN 1 because it gets automatically created by Intersight backend upon
                    # creation of the VLAN Policy
                    self.commit(object_type="fabric.Vlan", payload=fabric_vlan, detail=detail,
                                key_attributes=["name", "vlan_id", "eth_network_policy"], modify_present=True)
                elif getattr(self._config, "update_existing_intersight_objects", False):
                    # Because this VLAN is a part of Overlapping VLANs (which means it already exists in Intersight),
                    # we only run the commit when we have set the "update_existing_intersight_objects" option.
                    # This is done to avoid querying for existing VLANs again in commit().
                    self.commit(object_type="fabric.Vlan", payload=fabric_vlan, detail=detail,
                                key_attributes=["name", "vlan_id", "eth_network_policy"])
                else:
                    # We skip pushing this particular object
                    self.logger(level="info", message=f"Skipping push of object type fabric.Vlan with "
                                                      f"name='{vlan['name']}' and vlan_id='{vlan['id']}' and "
                                                      f"EthNetworkPolicy.Moid='{fenp.moid}' as it already exists")
                    pass

        return True


class IntersightFabricVsanPolicy(IntersightConfigObject):
    _CONFIG_NAME = "VSAN Policy"
    _CONFIG_SECTION_NAME = "vsan_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "fabric.FcNetworkPolicy"

    def __init__(self, parent=None, fabric_fc_network_policy=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=fabric_fc_network_policy)

        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.name = self.get_attribute(attribute_name="name")
        self.uplink_trunking = self.get_attribute(attribute_name="enable_trunking",
                                                  attribute_secondary_name="uplink_trunking")
        self.vsans = None

        if self._config.load_from == "live":
            self.vsans = self._get_vsans()

        elif self._config.load_from == "file":
            for attribute in ["vsans"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

            # We use this to make sure all options of a VSAN are set to None if they are not present
            if self.vsans:
                for vsan in self.vsans:
                    for attribute in ["fcoe_vlan_id", "id", "name", "scope"]:
                        if attribute not in vsan:
                            vsan[attribute] = None

    def _get_vsans(self):
        # Fetches the VSANs configuration of a VSAN Policy
        if "fabric_vsan" in self._config.sdk_objects:
            vsans = []
            for fabric_vsan in self._config.sdk_objects["fabric_vsan"]:
                if hasattr(fabric_vsan, "fc_network_policy"):
                    if fabric_vsan.fc_network_policy.moid == self._moid:
                        vsans.append({"name": fabric_vsan.name, "id": fabric_vsan.vsan_id,
                                      "fcoe_vlan_id": fabric_vsan.fcoe_vlan, "scope": fabric_vsan.vsan_scope})

            return vsans

        return None

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.fabric_fc_network_policy import FabricFcNetworkPolicy

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        # We first need to push the main fabric.FcNetworkPolicy object
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
        if self.uplink_trunking is not None:
            kwargs["enable_trunking"] = self.uplink_trunking

        fabric_fc_network_policy = FabricFcNetworkPolicy(**kwargs)

        ffnp = self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=fabric_fc_network_policy,
                           detail=self.name, return_relationship=True)
        if not ffnp:
            return False

        if self.vsans:
            # We now need to push the fabric.Vsan object for each VSAN in the list
            from intersight.model.fabric_vsan import FabricVsan

            for vsan in self.vsans:
                kwargs = {
                    "object_type": "fabric.Vsan",
                    "class_id": "fabric.Vsan",
                    "fc_network_policy": ffnp
                }
                if vsan["name"] is not None:
                    kwargs["name"] = vsan["name"]
                if vsan["id"] is not None:
                    kwargs["vsan_id"] = vsan["id"]
                if vsan["fcoe_vlan_id"] is not None:
                    kwargs["fcoe_vlan"] = vsan["fcoe_vlan_id"]
                if vsan["scope"] is not None:
                    kwargs["vsan_scope"] = vsan["scope"]

                fabric_vsan = FabricVsan(**kwargs)

                detail = self.name + " - VSAN " + str(vsan["name"])
                self.commit(object_type="fabric.Vsan", payload=fabric_vsan, detail=detail,
                            key_attributes=["name", "vsan_id", "fc_network_policy"])

        return True


class IntersightNetFlowConfigurationPolicy(IntersightConfigObject):
    _CONFIG_NAME = "NetFlow Configuration Policy"
    _CONFIG_SECTION_NAME = "netflow_configuration_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "fabric.NetFlowPolicy"

    def __init__(self, parent=None, netflow_configuration_policy=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=netflow_configuration_policy)

        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.name = self.get_attribute(attribute_name="name")
        self.flow_definitions = None
        self.flow_exporters = None
        self.flow_monitors = None

        if self._config.load_from == "live":
            if "fabric_net_flow_record" in self._config.sdk_objects:
                netflow_record_definitions = []
                for netflow_record in self._config.sdk_objects["fabric_net_flow_record"]:
                    if hasattr(netflow_record, "net_flow_policy"):
                        records = {}
                        if netflow_record.net_flow_policy.moid == self._moid:
                            records["name"] = netflow_record.name
                            records["record_type"] = netflow_record.record_type
                            keys = []
                            if netflow_record.record_type == "L2":
                                if netflow_record.l2_flow_key.destination_mac:
                                    keys.append("destination_mac_address")
                                if netflow_record.l2_flow_key.ether_type:
                                    keys.append("ether_type")
                                if netflow_record.l2_flow_key.source_mac:
                                    keys.append("source_mac_address")

                            if netflow_record.record_type == "IPv4":
                                if netflow_record.ipv4_flow_key.destination_ip_address:
                                    keys.append("destination_ip_address")
                                if netflow_record.ipv4_flow_key.destination_port:
                                    keys.append("destination_port")
                                if netflow_record.ipv4_flow_key.protocol:
                                    keys.append("protocol")
                                if netflow_record.ipv4_flow_key.source_ip_address:
                                    keys.append("source_ip_address")
                                if netflow_record.ipv4_flow_key.source_port:
                                    keys.append("source_port")
                                if netflow_record.ipv4_flow_key.tos:
                                    keys.append("tos")

                            if netflow_record.record_type == "IPv6":
                                if netflow_record.ipv6_flow_key.destination_ip_address:
                                    keys.append("destination_ip_address")
                                if netflow_record.ipv6_flow_key.destination_port:
                                    keys.append("destination_port")
                                if netflow_record.ipv6_flow_key.protocol:
                                    keys.append("protocol")
                                if netflow_record.ipv6_flow_key.source_ip_address:
                                    keys.append("source_ip_address")
                                if netflow_record.ipv6_flow_key.source_port:
                                    keys.append("source_port")

                            if keys:
                                records["keys"] = keys

                            if netflow_record.flow_non_key:
                                non_keys = []
                                if netflow_record.flow_non_key.byte_counters:
                                    non_keys.append("byte_counters")
                                if netflow_record.flow_non_key.first_system_time:
                                    non_keys.append("first_system_time")
                                if netflow_record.flow_non_key.last_system_time:
                                    non_keys.append("last_system_time")
                                if netflow_record.flow_non_key.packet_counters:
                                    non_keys.append("packet_counters")
                                if non_keys:
                                    records["non_keys"] = non_keys
                        if records:
                            netflow_record_definitions.append(records)
                if netflow_record_definitions:
                    self.flow_definitions = netflow_record_definitions

            if "fabric_net_flow_exporter" in self._config.sdk_objects:
                flow_exporters = []
                for netflow_exporter in self._config.sdk_objects["fabric_net_flow_exporter"]:
                    if hasattr(netflow_exporter, "net_flow_policy"):
                        exporters = {}
                        if netflow_exporter.net_flow_policy.moid == self._moid:
                            exporters["name"] = netflow_exporter.name
                            flow_collector = {}
                            if netflow_exporter.destination:
                                flow_collector["destination_ip_address"] = netflow_exporter.destination
                            if netflow_exporter.udp_port:
                                flow_collector["udp_port"] = netflow_exporter.udp_port
                            if netflow_exporter.gateway_ip:
                                flow_collector["gateway_ip_address"] = netflow_exporter.gateway_ip
                            if netflow_exporter.dscp:
                                flow_collector["dscp"] = netflow_exporter.dscp
                            if flow_collector:
                                exporters["flow_collector"] = flow_collector
                            timeouts = {}
                            if netflow_exporter.template_data_timeout:
                                timeouts["template_data_timeout"] = netflow_exporter.template_data_timeout
                            if netflow_exporter.option_exporter_stats_timeout:
                                timeouts["option_exporter_stats_timeout"] = \
                                    netflow_exporter.option_exporter_stats_timeout
                            if netflow_exporter.option_interface_table_timeout:
                                timeouts["option_interface_table_timeout"] = \
                                    netflow_exporter.option_interface_table_timeout
                            if timeouts:
                                exporters["timeouts"] = timeouts
                            if netflow_exporter.source_interface:
                                exporter_interfaces = {}
                                if netflow_exporter.source_interface.vlan_id:
                                    exporter_interfaces["vlan_id"] = netflow_exporter.source_interface.vlan_id
                                if netflow_exporter.source_interface.switch_aip:
                                    exporter_interfaces["switch_a_ip"] = netflow_exporter.source_interface.switch_aip
                                if netflow_exporter.source_interface.switch_asubnetmask:
                                    exporter_interfaces["switch_a_subnet_mask"] = \
                                        netflow_exporter.source_interface.switch_asubnetmask
                                if netflow_exporter.source_interface.switch_bip:
                                    exporter_interfaces["switch_b_ip"] = netflow_exporter.source_interface.switch_bip
                                if netflow_exporter.source_interface.switch_bsubnetmask:
                                    exporter_interfaces["switch_b_subnet_mask"] = \
                                        netflow_exporter.source_interface.switch_bsubnetmask
                                if exporter_interfaces:
                                    exporters["exporter_interfaces"] = exporter_interfaces
                        if exporters:
                            flow_exporters.append(exporters)
                if flow_exporters:
                    self.flow_exporters = flow_exporters

            if "fabric_net_flow_monitor" in self._config.sdk_objects:
                flow_monitors = []
                for netflow_monitor in self._config.sdk_objects["fabric_net_flow_monitor"]:
                    if hasattr(netflow_monitor, "net_flow_policy"):
                        monitors = {}
                        if netflow_monitor.net_flow_policy.moid == self._moid:
                            monitors["name"] = netflow_monitor.name
                            if netflow_monitor.flow_record:
                                record_moid = netflow_monitor.flow_record.moid
                                record_name = next(
                                    (r.name for r in self._config.sdk_objects.get("fabric_net_flow_record", [])
                                     if r.moid == record_moid),
                                    None
                                )
                                if record_name:
                                    monitors["flow_record"] = record_name
                            if netflow_monitor.flow_exporters:
                                fes = []
                                for fe in netflow_monitor.flow_exporters:
                                    fe_moid = fe.moid
                                    fe_name = next(
                                        (f.name for f in self._config.sdk_objects.get("fabric_net_flow_exporter", [])
                                         if f.moid == fe_moid),
                                        None
                                    )
                                    if fe_name:
                                        fes.append(fe_name)
                                monitors["flow_exporters"] = fes
                            if monitors:
                                flow_monitors.append(monitors)
                if flow_monitors:
                    self.flow_monitors = flow_monitors

        elif self._config.load_from == "file":
            for attribute in ["flow_definitions", "flow_exporters", "flow_monitors"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

            if self.flow_definitions:
                for flow_def in self.flow_definitions:
                    for attribute in ["name", "record_type", "keys", "non_keys"]:
                        if attribute not in flow_def:
                            flow_def[attribute] = None

            if self.flow_exporters:
                for exporter in self.flow_exporters:
                    for attribute in ["name", "flow_collector", "timeouts", "exporter_interfaces"]:
                        if attribute not in exporter:
                            exporter[attribute] = None
                    if exporter["flow_collector"]:
                        for attribute in ["destination_ip_address", "udp_port", "gateway_ip_address", "dscp"]:
                            if attribute not in exporter["flow_collector"]:
                                exporter["flow_collector"][attribute] = None
                    if exporter["timeouts"]:
                        for attribute in ["template_data_timeout", "option_exporter_stats_timeout",
                                          "option_interface_table_timeout"]:
                            if attribute not in exporter["timeouts"]:
                                exporter["timeouts"][attribute] = None
                    if exporter["exporter_interfaces"]:
                        for attribute in ["vlan_id", "switch_a_ip", "switch_a_subnet_mask",
                                          "switch_b_ip", "switch_b_subnet_mask"]:
                            if attribute not in exporter["exporter_interfaces"]:
                                exporter["exporter_interfaces"][attribute] = None

            if self.flow_monitors:
                for monitor in self.flow_monitors:
                    for attribute in ["name", "flow_record", "flow_exporters"]:
                        if attribute not in monitor:
                            monitor[attribute] = None

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.fabric_net_flow_policy import FabricNetFlowPolicy

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

        fabric_net_flow_policy = FabricNetFlowPolicy(**kwargs)

        nfp = self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=fabric_net_flow_policy,
                          detail=self.name, return_relationship=True)
        if not nfp:
            return False

        if self.flow_definitions:
            from intersight.model.fabric_net_flow_record import FabricNetFlowRecord

            for flow_def in self.flow_definitions:
                record_kwargs = {
                    "object_type": "fabric.NetFlowRecord",
                    "class_id": "fabric.NetFlowRecord",
                    "net_flow_policy": nfp
                }
                if flow_def["name"] is not None:
                    record_kwargs["name"] = flow_def["name"]
                if flow_def["record_type"] is not None:
                    record_kwargs["record_type"] = flow_def["record_type"]

                if flow_def.get("record_type") == "L2" and flow_def.get("keys"):
                    from intersight.model.fabric_l2_flow_key import FabricL2FlowKey
                    l2_kwargs = {
                        "class_id": "fabric.L2FlowKey",
                        "object_type": "fabric.L2FlowKey"
                    }
                    for key in flow_def["keys"]:
                        if key == "destination_mac_address":
                            l2_kwargs["destination_mac"] = True
                        elif key == "ether_type":
                            l2_kwargs["ether_type"] = True
                        elif key == "source_mac_address":
                            l2_kwargs["source_mac"] = True
                    record_kwargs["l2_flow_key"] = FabricL2FlowKey(**l2_kwargs)

                elif flow_def.get("record_type") == "IPv4" and flow_def.get("keys"):
                    from intersight.model.fabric_ipv4_flow_key import FabricIpv4FlowKey
                    ipv4_kwargs = {
                        "class_id": "fabric.Ipv4FlowKey",
                        "object_type": "fabric.Ipv4FlowKey"
                    }
                    for key in flow_def["keys"]:
                        if key == "destination_ip_address":
                            ipv4_kwargs["destination_ip_address"] = True
                        elif key == "destination_port":
                            ipv4_kwargs["destination_port"] = True
                        elif key == "protocol":
                            ipv4_kwargs["protocol"] = True
                        elif key == "source_ip_address":
                            ipv4_kwargs["source_ip_address"] = True
                        elif key == "source_port":
                            ipv4_kwargs["source_port"] = True
                        elif key == "tos":
                            ipv4_kwargs["tos"] = True
                    record_kwargs["ipv4_flow_key"] = FabricIpv4FlowKey(**ipv4_kwargs)

                elif flow_def.get("record_type") == "IPv6" and flow_def.get("keys"):
                    from intersight.model.fabric_ipv6_flow_key import FabricIpv6FlowKey
                    ipv6_kwargs = {
                        "class_id": "fabric.Ipv6FlowKey",
                        "object_type": "fabric.Ipv6FlowKey"
                    }
                    for key in flow_def["keys"]:
                        if key == "destination_ip_address":
                            ipv6_kwargs["destination_ip_address"] = True
                        elif key == "destination_port":
                            ipv6_kwargs["destination_port"] = True
                        elif key == "protocol":
                            ipv6_kwargs["protocol"] = True
                        elif key == "source_ip_address":
                            ipv6_kwargs["source_ip_address"] = True
                        elif key == "source_port":
                            ipv6_kwargs["source_port"] = True
                    record_kwargs["ipv6_flow_key"] = FabricIpv6FlowKey(**ipv6_kwargs)

                if flow_def.get("non_keys"):
                    from intersight.model.fabric_flow_non_key import FabricFlowNonKey
                    non_key_kwargs = {
                        "class_id": "fabric.FlowNonKey",
                        "object_type": "fabric.FlowNonKey"
                    }
                    for non_key in flow_def["non_keys"]:
                        if non_key == "byte_counters":
                            non_key_kwargs["byte_counters"] = True
                        elif non_key == "first_system_time":
                            non_key_kwargs["first_system_time"] = True
                        elif non_key == "last_system_time":
                            non_key_kwargs["last_system_time"] = True
                        elif non_key == "packet_counters":
                            non_key_kwargs["packet_counters"] = True
                    record_kwargs["flow_non_key"] = FabricFlowNonKey(**non_key_kwargs)

                fabric_net_flow_record = FabricNetFlowRecord(**record_kwargs)
                detail = f"{self.name} - Flow Record '{flow_def['name']}'"
                self.commit(object_type="fabric.NetFlowRecord", payload=fabric_net_flow_record,
                            detail=detail, key_attributes=["name", "net_flow_policy"])

        if self.flow_exporters:
            from intersight.model.fabric_net_flow_exporter import FabricNetFlowExporter

            for exporter in self.flow_exporters:
                exporter_kwargs = {
                    "object_type": "fabric.NetFlowExporter",
                    "class_id": "fabric.NetFlowExporter",
                    "net_flow_policy": nfp
                }
                if exporter["name"] is not None:
                    exporter_kwargs["name"] = exporter["name"]

                if exporter.get("flow_collector"):
                    fc = exporter["flow_collector"]
                    if fc.get("destination_ip_address") is not None:
                        exporter_kwargs["destination"] = fc["destination_ip_address"]
                    if fc.get("udp_port") is not None:
                        exporter_kwargs["udp_port"] = fc["udp_port"]
                    if fc.get("gateway_ip_address") is not None:
                        exporter_kwargs["gateway_ip"] = fc["gateway_ip_address"]
                    if fc.get("dscp") is not None:
                        exporter_kwargs["dscp"] = fc["dscp"]

                if exporter.get("timeouts"):
                    t = exporter["timeouts"]
                    if t.get("template_data_timeout") is not None:
                        exporter_kwargs["template_data_timeout"] = t["template_data_timeout"]
                    if t.get("option_exporter_stats_timeout") is not None:
                        exporter_kwargs["option_exporter_stats_timeout"] = t["option_exporter_stats_timeout"]
                    if t.get("option_interface_table_timeout") is not None:
                        exporter_kwargs["option_interface_table_timeout"] = t["option_interface_table_timeout"]

                if exporter.get("exporter_interfaces"):
                    from intersight.model.fabric_vlan_export_interface import FabricVlanExportInterface
                    ei = exporter["exporter_interfaces"]
                    si_kwargs = {
                        "class_id": "fabric.VlanExportInterface",
                        "object_type": "fabric.VlanExportInterface"
                    }
                    if ei.get("vlan_id") is not None:
                        si_kwargs["vlan_id"] = ei["vlan_id"]
                    if ei.get("switch_a_ip") is not None:
                        si_kwargs["switch_aip"] = ei["switch_a_ip"]
                    if ei.get("switch_a_subnet_mask") is not None:
                        si_kwargs["switch_asubnetmask"] = ei["switch_a_subnet_mask"]
                    if ei.get("switch_b_ip") is not None:
                        si_kwargs["switch_bip"] = ei["switch_b_ip"]
                    if ei.get("switch_b_subnet_mask") is not None:
                        si_kwargs["switch_bsubnetmask"] = ei["switch_b_subnet_mask"]
                    exporter_kwargs["source_interface"] = FabricVlanExportInterface(**si_kwargs)

                fabric_net_flow_exporter = FabricNetFlowExporter(**exporter_kwargs)
                detail = f"{self.name} - Flow Exporter '{exporter['name']}'"
                self.commit(object_type="fabric.NetFlowExporter", payload=fabric_net_flow_exporter,
                            detail=detail, key_attributes=["name", "net_flow_policy"])

        if self.flow_monitors:
            from intersight.model.fabric_net_flow_monitor import FabricNetFlowMonitor

            for monitor in self.flow_monitors:
                monitor_kwargs = {
                    "object_type": "fabric.NetFlowMonitor",
                    "class_id": "fabric.NetFlowMonitor",
                    "net_flow_policy": nfp
                }
                if monitor["name"] is not None:
                    monitor_kwargs["name"] = monitor["name"]

                if monitor.get("flow_record"):
                    flow_record = self.get_live_object(
                        object_name=monitor["flow_record"],
                        object_type="fabric.NetFlowRecord",
                        query_filter=f"NetFlowPolicy.Moid eq '{nfp.moid}' and Name eq '{monitor['flow_record']}'"
                    )
                    if flow_record:
                        monitor_kwargs["flow_record"] = flow_record
                    else:
                        self.logger(level="warning",
                                    message=f"Could not find Flow Record '{monitor['flow_record']}' "
                                            f"for Flow Monitor '{monitor['name']}' in policy '{self.name}'")
                        self._config.push_summary_manager.add_object_status(
                            obj=self,
                            obj_detail=f"Attaching Flow Record '{monitor['flow_record']}' to "
                                       f"Flow Monitor '{monitor['name']}'",
                            obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                            message=f"Failed to find Flow Record '{monitor['flow_record']}'"
                        )

                if monitor.get("flow_exporters"):
                    exporters = []
                    for exporter_name in monitor["flow_exporters"]:
                        flow_exporter = self.get_live_object(
                            object_name=exporter_name,
                            object_type="fabric.NetFlowExporter",
                            query_filter=f"NetFlowPolicy.Moid eq '{nfp.moid}' and Name eq '{exporter_name}'"
                        )
                        if flow_exporter:
                            exporters.append(flow_exporter)
                        else:
                            self.logger(level="warning",
                                        message=f"Could not find Flow Exporter '{exporter_name}' "
                                                f"for Flow Monitor '{monitor['name']}' in policy '{self.name}'")
                            self._config.push_summary_manager.add_object_status(
                                obj=self,
                                obj_detail=f"Attaching Flow Exporter '{exporter_name}' to "
                                           f"Flow Monitor '{monitor['name']}'",
                                obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                                message=f"Failed to find Flow Exporter '{exporter_name}'"
                            )
                    if exporters:
                        monitor_kwargs["flow_exporters"] = exporters

                fabric_net_flow_monitor = FabricNetFlowMonitor(**monitor_kwargs)
                detail = f"{self.name} - Flow Monitor '{monitor['name']}'"
                self.commit(object_type="fabric.NetFlowMonitor", payload=fabric_net_flow_monitor,
                            detail=detail, key_attributes=["name", "net_flow_policy"])

        return True
