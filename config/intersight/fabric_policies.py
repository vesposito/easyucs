# coding: utf-8
# !/usr/bin/env python

""" fabric_policies.py: Easy UCS Deployment Tool """

from config.intersight.object import IntersightConfigObject
from config.intersight.server_policies import IntersightNetworkConnectivityPolicy, IntersightNtpPolicy, \
    IntersightSnmpPolicy, IntersightSyslogPolicy


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


class IntersightFabricPortPolicy(IntersightConfigObject):
    _CONFIG_NAME = "Port Policy"
    _CONFIG_SECTION_NAME = "port_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "fabric.PortPolicy"

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

            # We use this to make sure all options of an Appliance Port-Channel are set to None if they are not present
            if self.appliance_port_channels:
                for appliance_port_channel in self.appliance_port_channels:
                    for attribute in ["admin_speed", "ethernet_network_control_policy", "ethernet_network_group_policy",
                                      "interfaces", "mode", "pc_id", "priority"]:
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
                    for attribute in ["admin_speed", "aggr_id", "ethernet_network_control_policy",
                                      "ethernet_network_group_policy", "fec", "mode", "port_id", "priority", "slot_id"]:
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
                    for attribute in ["admin_speed", "interfaces", "link_aggregation_policy", "link_control_policy",
                                      "pc_id"]:
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
                    for attribute in ["admin_speed", "aggr_id", "fec", "link_control_policy", "port_id", "slot_id"]:
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
                    for attribute in ["admin_speed", "ethernet_network_group_policy", "flow_control_policy",
                                      "interfaces", "link_aggregation_policy", "link_control_policy", "pc_id"]:
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
                    for attribute in ["admin_speed", "aggr_id", "ethernet_network_group_policy", "fec",
                                      "flow_control_policy", "link_control_policy", "port_id", "slot_id"]:
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
                    for attribute in ["admin_speed", "fill_pattern", "interfaces", "pc_id", "vsan_id"]:
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
                    for attribute in ["admin_speed", "aggr_id", "port_id", "slot_id", "vsan_id"]:
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
                    for attribute in ["admin_speed", "aggr_id", "fill_pattern", "port_id", "slot_id", "vsan_id"]:
                        if attribute not in san_uplink_port:
                            san_uplink_port[attribute] = None

            # We use this to make sure all options of a Server Port are set to None if they are not present
            if self.server_ports:
                for server_port in self.server_ports:
                    for attribute in ["aggr_id", "connected_device_type", "connected_device_id", "fec", "port_id",
                                      "slot_id"]:
                        if attribute not in server_port:
                            server_port[attribute] = None

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
                            eth_network_control_policy = \
                                self.get_config_objects_from_ref(fabric_appliance_pc_role.eth_network_control_policy)
                            if eth_network_control_policy:
                                if len(eth_network_control_policy) == 1:
                                    ethernet_network_control_policy = eth_network_control_policy[0].name
                        if hasattr(fabric_appliance_pc_role, "eth_network_group_policy"):
                            eth_network_group_policy = \
                                self.get_config_objects_from_ref(fabric_appliance_pc_role.eth_network_group_policy)
                            if eth_network_group_policy:
                                if len(eth_network_group_policy) == 1:
                                    ethernet_network_group_policy = eth_network_group_policy[0].name

                        appliance_port_channels.append(
                            {"interfaces": interfaces,
                             "pc_id": fabric_appliance_pc_role.pc_id,
                             "admin_speed": fabric_appliance_pc_role.admin_speed,
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
                            eth_network_control_policy = \
                                self.get_config_objects_from_ref(fabric_appliance_role.eth_network_control_policy)
                            if eth_network_control_policy:
                                if len(eth_network_control_policy) == 1:
                                    ethernet_network_control_policy = eth_network_control_policy[0].name
                        if hasattr(fabric_appliance_role, "eth_network_group_policy"):
                            eth_network_group_policy = \
                                self.get_config_objects_from_ref(fabric_appliance_role.eth_network_group_policy)
                            if eth_network_group_policy:
                                if len(eth_network_group_policy) == 1:
                                    ethernet_network_group_policy = eth_network_group_policy[0].name
                        if fabric_appliance_role.aggregate_port_id != 0:
                            appliance_ports.append({"slot_id": fabric_appliance_role.slot_id,
                                                    "port_id": fabric_appliance_role.aggregate_port_id,
                                                    "aggr_id": fabric_appliance_role.port_id,
                                                    "admin_speed": fabric_appliance_role.admin_speed,
                                                    "fec": fabric_appliance_role.fec,
                                                    "mode": fabric_appliance_role.mode,
                                                    "priority": fabric_appliance_role.priority,
                                                    "ethernet_network_control_policy": ethernet_network_control_policy,
                                                    "ethernet_network_group_policy": ethernet_network_group_policy})
                        else:
                            appliance_ports.append({"slot_id": fabric_appliance_role.slot_id,
                                                    "port_id": fabric_appliance_role.port_id,
                                                    "admin_speed": fabric_appliance_role.admin_speed,
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
                        breakout_ports.append({"slot_id": fabric_port_mode.slot_id,
                                               "port_id": fabric_port_mode.port_id_start,
                                               "mode": "4x10g"})
                    elif fabric_port_mode.port_policy.moid == self._moid and \
                            getattr(fabric_port_mode, "custom_mode", None) == "BreakoutEthernet25G":
                        breakout_ports.append({"slot_id": fabric_port_mode.slot_id,
                                               "port_id": fabric_port_mode.port_id_start,
                                               "mode": "4x25g"})
                    elif fabric_port_mode.port_policy.moid == self._moid and \
                            getattr(fabric_port_mode, "custom_mode", None) == "BreakoutFibreChannel8G":
                        breakout_ports.append({"slot_id": fabric_port_mode.slot_id,
                                               "port_id": fabric_port_mode.port_id_start,
                                               "mode": "4x8g"})
                    elif fabric_port_mode.port_policy.moid == self._moid and \
                            getattr(fabric_port_mode, "custom_mode", None) == "BreakoutFibreChannel16G":
                        breakout_ports.append({"slot_id": fabric_port_mode.slot_id,
                                               "port_id": fabric_port_mode.port_id_start,
                                               "mode": "4x16g"})
                    elif fabric_port_mode.port_policy.moid == self._moid and \
                            getattr(fabric_port_mode, "custom_mode", None) == "BreakoutFibreChannel32G":
                        breakout_ports.append({"slot_id": fabric_port_mode.slot_id,
                                               "port_id": fabric_port_mode.port_id_start,
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
                            fabric_link_aggregation_policy = \
                                self.get_config_objects_from_ref(fabric_fcoe_uplink_pc_role.link_aggregation_policy)
                            if fabric_link_aggregation_policy:
                                if len(fabric_link_aggregation_policy) == 1:
                                    link_aggregation_policy = fabric_link_aggregation_policy[0].name

                        link_control_policy = None
                        if hasattr(fabric_fcoe_uplink_pc_role, "link_control_policy"):
                            fabric_link_control_policy = \
                                self.get_config_objects_from_ref(fabric_fcoe_uplink_pc_role.link_control_policy)
                            if fabric_link_control_policy:
                                if len(fabric_link_control_policy) == 1:
                                    link_control_policy = fabric_link_control_policy[0].name

                        fcoe_port_channels.append({"interfaces": interfaces,
                                                   "pc_id": fabric_fcoe_uplink_pc_role.pc_id,
                                                   "admin_speed": fabric_fcoe_uplink_pc_role.admin_speed,
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
                            fabric_link_control_policy = \
                                self.get_config_objects_from_ref(fabric_fcoe_uplink_role.link_control_policy)
                            if fabric_link_control_policy:
                                if len(fabric_link_control_policy) == 1:
                                    link_control_policy = fabric_link_control_policy[0].name

                        if fabric_fcoe_uplink_role.aggregate_port_id != 0:
                            fcoe_uplink_ports.append({"slot_id": fabric_fcoe_uplink_role.slot_id,
                                                      "port_id": fabric_fcoe_uplink_role.aggregate_port_id,
                                                      "aggr_id": fabric_fcoe_uplink_role.port_id,
                                                      "admin_speed": fabric_fcoe_uplink_role.admin_speed,
                                                      "fec": fabric_fcoe_uplink_role.fec,
                                                      "link_control_policy": link_control_policy})
                        else:
                            fcoe_uplink_ports.append({"slot_id": fabric_fcoe_uplink_role.slot_id,
                                                      "port_id": fabric_fcoe_uplink_role.port_id,
                                                      "aggr_id": None,
                                                      "admin_speed": fabric_fcoe_uplink_role.admin_speed,
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

                        ethernet_network_group_policy = None
                        if hasattr(fabric_uplink_pc_role, "eth_network_group_policy"):
                            eth_network_group_policy = \
                                self.get_config_objects_from_ref(fabric_uplink_pc_role.eth_network_group_policy)
                            if eth_network_group_policy:
                                if len(eth_network_group_policy) == 1:
                                    ethernet_network_group_policy = eth_network_group_policy[0].name

                        flow_control_policy = None
                        if hasattr(fabric_uplink_pc_role, "flow_control_policy"):
                            fabric_flow_control_policy = \
                                self.get_config_objects_from_ref(fabric_uplink_pc_role.flow_control_policy)
                            if fabric_flow_control_policy:
                                if len(fabric_flow_control_policy) == 1:
                                    flow_control_policy = fabric_flow_control_policy[0].name

                        link_aggregation_policy = None
                        if hasattr(fabric_uplink_pc_role, "link_aggregation_policy"):
                            fabric_link_aggregation_policy = \
                                self.get_config_objects_from_ref(fabric_uplink_pc_role.link_aggregation_policy)
                            if fabric_link_aggregation_policy:
                                if len(fabric_link_aggregation_policy) == 1:
                                    link_aggregation_policy = fabric_link_aggregation_policy[0].name

                        link_control_policy = None
                        if hasattr(fabric_uplink_pc_role, "link_control_policy"):
                            fabric_link_control_policy = \
                                self.get_config_objects_from_ref(fabric_uplink_pc_role.link_control_policy)
                            if fabric_link_control_policy:
                                if len(fabric_link_control_policy) == 1:
                                    link_control_policy = fabric_link_control_policy[0].name

                        lan_port_channels.append({"interfaces": interfaces,
                                                  "pc_id": fabric_uplink_pc_role.pc_id,
                                                  "admin_speed": fabric_uplink_pc_role.admin_speed,
                                                  "ethernet_network_group_policy": ethernet_network_group_policy,
                                                  "flow_control_policy": flow_control_policy,
                                                  "link_aggregation_policy": link_aggregation_policy,
                                                  "link_control_policy": link_control_policy})

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
                            fabric_flow_control_policy = \
                                self.get_config_objects_from_ref(fabric_uplink_role.flow_control_policy)
                            if fabric_flow_control_policy:
                                if len(fabric_flow_control_policy) == 1:
                                    flow_control_policy = fabric_flow_control_policy[0].name

                        ethernet_network_group_policy = None
                        if hasattr(fabric_uplink_role, "eth_network_group_policy"):
                            eth_network_group_policy = \
                                self.get_config_objects_from_ref(fabric_uplink_role.eth_network_group_policy)
                            if eth_network_group_policy:
                                if len(eth_network_group_policy) == 1:
                                    ethernet_network_group_policy = eth_network_group_policy[0].name

                        link_control_policy = None
                        if hasattr(fabric_uplink_role, "link_control_policy"):
                            fabric_link_control_policy = \
                                self.get_config_objects_from_ref(fabric_uplink_role.link_control_policy)
                            if fabric_link_control_policy:
                                if len(fabric_link_control_policy) == 1:
                                    link_control_policy = fabric_link_control_policy[0].name
                        if fabric_uplink_role.aggregate_port_id != 0:
                            lan_uplink_ports.append({"slot_id": fabric_uplink_role.slot_id,
                                                     "port_id": fabric_uplink_role.aggregate_port_id,
                                                     "aggr_id": fabric_uplink_role.port_id,
                                                     "admin_speed": fabric_uplink_role.admin_speed,
                                                     "fec": fabric_uplink_role.fec,
                                                     "ethernet_network_group_policy": ethernet_network_group_policy,
                                                     "flow_control_policy": flow_control_policy,
                                                     "link_control_policy": link_control_policy})
                        else:
                            lan_uplink_ports.append({"slot_id": fabric_uplink_role.slot_id,
                                                     "port_id": fabric_uplink_role.port_id,
                                                     "aggr_id": None,
                                                     "admin_speed": fabric_uplink_role.admin_speed,
                                                     "fec": fabric_uplink_role.fec,
                                                     "ethernet_network_group_policy": ethernet_network_group_policy,
                                                     "flow_control_policy": flow_control_policy,
                                                     "link_control_policy": link_control_policy})

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
                        san_port_channels.append({"interfaces": interfaces,
                                                  "pc_id": fabric_fc_uplink_pc_role.pc_id,
                                                  "vsan_id": fabric_fc_uplink_pc_role.vsan_id,
                                                  "admin_speed": fabric_fc_uplink_pc_role.admin_speed,
                                                  "fill_pattern": fabric_fc_uplink_pc_role.fill_pattern})

            return san_port_channels

        return None

    def _get_san_storage_ports(self):
        # Fetches the SAN Storage Ports configuration of a Port Policy
        if "fabric_fc_storage_role" in self._config.sdk_objects:
            san_storage_ports = []
            for fabric_fc_storage_role in self._config.sdk_objects["fabric_fc_storage_role"]:
                if hasattr(fabric_fc_storage_role, "port_policy"):
                    if fabric_fc_storage_role.port_policy.moid == self._moid:
                        if fabric_fc_storage_role.aggregate_port_id != 0:
                            san_storage_ports.append({"slot_id": fabric_fc_storage_role.slot_id,
                                                      "port_id": fabric_fc_storage_role.aggregate_port_id,
                                                      "aggr_id": fabric_fc_storage_role.port_id,
                                                      "admin_speed": fabric_fc_storage_role.admin_speed,
                                                      "vsan_id": fabric_fc_storage_role.vsan_id})
                        else:
                            san_storage_ports.append({"slot_id": fabric_fc_storage_role.slot_id,
                                                      "port_id": fabric_fc_storage_role.port_id,
                                                      "aggr_id": None,
                                                      "admin_speed": fabric_fc_storage_role.admin_speed,
                                                      "vsan_id": fabric_fc_storage_role.vsan_id})

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
                        if fabric_fc_uplink_role.aggregate_port_id != 0:
                            san_uplink_ports.append({"slot_id": fabric_fc_uplink_role.slot_id,
                                                     "port_id": fabric_fc_uplink_role.aggregate_port_id,
                                                     "aggr_id": fabric_fc_uplink_role.port_id,
                                                     "admin_speed": fabric_fc_uplink_role.admin_speed,
                                                     "vsan_id": fabric_fc_uplink_role.vsan_id,
                                                     "fill_pattern": fabric_fc_uplink_role.fill_pattern})
                        else:
                            san_uplink_ports.append({"slot_id": fabric_fc_uplink_role.slot_id,
                                                     "port_id": fabric_fc_uplink_role.port_id,
                                                     "aggr_id": None,
                                                     "admin_speed": fabric_fc_uplink_role.admin_speed,
                                                     "vsan_id": fabric_fc_uplink_role.vsan_id,
                                                     "fill_pattern": fabric_fc_uplink_role.fill_pattern})

            return san_uplink_ports

        return None

    def _get_server_ports(self):
        # Fetches the Server Ports configuration of a Port Policy
        if "fabric_server_role" in self._config.sdk_objects:
            server_ports = []
            for fabric_server_role in self._config.sdk_objects["fabric_server_role"]:
                if hasattr(fabric_server_role, "port_policy"):
                    if fabric_server_role.port_policy.moid == self._moid:
                        server_port = {
                            "slot_id": fabric_server_role.slot_id,
                            "port_id": fabric_server_role.port_id,
                            "aggr_id": None,
                            "connected_device_type": fabric_server_role.preferred_device_type,
                            "connected_device_id": None,
                            "fec": fabric_server_role.fec
                        }
                        if fabric_server_role.aggregate_port_id != 0:
                            server_port["port_id"] = fabric_server_role.aggregate_port_id
                            server_port["aggr_id"] = fabric_server_role.port_id
                        if fabric_server_role.preferred_device_id != 0:
                            server_port["connected_device_id"] = fabric_server_role.preferred_device_id

                        server_ports.append(server_port)

            return server_ports

        return None

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
        if self.san_unified_ports and self.device_model not in ["UCS-FI-6536"]:
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

            for breakout_port in self.breakout_ports:
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
                if appliance_port_channel["mode"] is not None:
                    kwargs["mode"] = appliance_port_channel["mode"]
                if appliance_port_channel["priority"] is not None:
                    kwargs["priority"] = appliance_port_channel["priority"]

                if appliance_port_channel["ethernet_network_control_policy"] is not None:
                    # We first need to identify the Ethernet Network Control Policy object reference
                    ethernet_network_control_policy = self.get_live_object(
                        object_name=appliance_port_channel["ethernet_network_control_policy"],
                        object_type="fabric.EthNetworkControlPolicy"
                    )
                    if ethernet_network_control_policy:
                        kwargs["eth_network_control_policy"] = ethernet_network_control_policy
                    else:
                        self.logger(level="warning",
                                    message="Could not find unique Ethernet Network Control Policy '" +
                                            appliance_port_channel["ethernet_network_control_policy"] +
                                            "' to assign to Appliance Port Channel " +
                                            str(appliance_port_channel["pc_id"]))
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
                        self.logger(level="warning",
                                    message="Could not find unique Ethernet Network Group Policy '" +
                                            appliance_port_channel["ethernet_network_group_policy"] +
                                            "' to assign to Appliance Port Channel " +
                                            str(appliance_port_channel["pc_id"]))
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
                if appliance_port["mode"] is not None:
                    kwargs["mode"] = appliance_port["mode"]
                if appliance_port["priority"] is not None:
                    kwargs["priority"] = appliance_port["priority"]

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
                                        message="Could not find unique Ethernet Network Control Policy '" +
                                                appliance_port["ethernet_network_control_policy"] +
                                                "' to assign to Appliance Port " + str(appliance_port["slot_id"]) +
                                                "/" + str(appliance_port["port_id"]) + "/" +
                                                str(appliance_port["aggr_id"]))
                        else:
                            self.logger(level="warning",
                                        message="Could not find unique Ethernet Network Control Policy '" +
                                                appliance_port["ethernet_network_control_policy"] +
                                                "' to assign to Appliance Port " + str(appliance_port["slot_id"]) +
                                                "/" + str(appliance_port["port_id"]))
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
                                        message="Could not find unique Ethernet Network Group Policy '" +
                                                appliance_port["ethernet_network_group_policy"] +
                                                "' to assign to Appliance Port " + str(appliance_port["slot_id"]) +
                                                "/" + str(appliance_port["port_id"]) + "/" +
                                                str(appliance_port["aggr_id"]))
                        else:
                            self.logger(level="warning",
                                        message="Could not find unique Ethernet Network Group Policy '" +
                                                appliance_port["ethernet_network_group_policy"] +
                                                "' to assign to Appliance Port " + str(appliance_port["slot_id"]) +
                                                "/" + str(appliance_port["port_id"]))
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

                if fcoe_port_channel["link_aggregation_policy"] is not None:
                    # We first need to identify the Link Aggregation Policy object reference
                    link_aggregation_policy = self.get_live_object(
                        object_name=fcoe_port_channel["link_aggregation_policy"],
                        object_type="fabric.LinkAggregationPolicy"
                    )
                    if link_aggregation_policy:
                        kwargs["link_aggregation_policy"] = link_aggregation_policy
                    else:
                        self.logger(level="warning",
                                    message="Could not find unique Link Aggregation Policy '" +
                                            fcoe_port_channel["link_aggregation_policy"] +
                                            "' to assign to FCoE Port Channel " + str(fcoe_port_channel["pc_id"]))
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
                        self.logger(level="warning",
                                    message="Could not find unique Link Control Policy '" +
                                            fcoe_port_channel["link_control_policy"] +
                                            "' to assign to FCoE Port Channel " + str(fcoe_port_channel["pc_id"]))
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
                                        message="Could not find unique Link Control Policy '" +
                                                fcoe_uplink_port["link_control_policy"] +
                                                "' to assign to FCoE Uplink Port " +
                                                str(fcoe_uplink_port["slot_id"]) +
                                                "/" + str(fcoe_uplink_port["port_id"]) + "/" +
                                                str(fcoe_uplink_port["aggr_id"]))
                        else:
                            self.logger(level="warning",
                                        message="Could not find unique Link Control Policy '" +
                                                fcoe_uplink_port["link_control_policy"] +
                                                "' to assign to FCoE Uplink Port " +
                                                str(fcoe_uplink_port["slot_id"]) +
                                                "/" + str(fcoe_uplink_port["port_id"]))
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

                if lan_port_channel["ethernet_network_group_policy"] is not None:
                    # We first need to identify the Ethernet Network Group Policy object reference
                    ethernet_network_group_policy = self.get_live_object(
                        object_name=lan_port_channel["ethernet_network_group_policy"],
                        object_type="fabric.EthNetworkGroupPolicy"
                    )
                    if ethernet_network_group_policy:
                        kwargs["eth_network_group_policy"] = [ethernet_network_group_policy]
                    else:
                        self.logger(level="warning",
                                    message="Could not find unique Ethernet Network Group Policy '" +
                                            lan_port_channel["ethernet_network_group_policy"] +
                                            "' to assign to LAN Port Channel " + str(lan_port_channel["pc_id"]))
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
                                    message="Could not find unique Flow Control Policy '" +
                                            lan_port_channel["flow_control_policy"] +
                                            "' to assign to LAN Port Channel " + str(lan_port_channel["pc_id"]))
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
                                    message="Could not find unique Link Aggregation Policy '" +
                                            lan_port_channel["link_aggregation_policy"] +
                                            "' to assign to LAN Port Channel " + str(lan_port_channel["pc_id"]))
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
                                    message="Could not find unique Link Control Policy '" +
                                            lan_port_channel["link_control_policy"] +
                                            "' to assign to LAN Port Channel " + str(lan_port_channel["pc_id"]))
                        self._config.push_summary_manager.add_object_status(
                            obj=self, obj_detail=f"Attaching Link Control Policy "
                                                 f"'{lan_port_channel['link_control_policy']}'",
                            obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                            message=f"Failed to find Link Control Policy "
                                    f"'{lan_port_channel['link_control_policy']}'"
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

                if lan_uplink_port["ethernet_network_group_policy"] is not None:
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
                                        message="Could not find unique Ethernet Network Group Policy '" +
                                                lan_uplink_port["ethernet_network_group_policy"] +
                                                "' to assign to LAN Uplink Port " +
                                                str(lan_uplink_port["slot_id"]) +
                                                "/" + str(lan_uplink_port["port_id"]) + "/" +
                                                str(lan_uplink_port["aggr_id"]))
                        else:
                            self.logger(level="warning",
                                        message="Could not find unique Ethernet Network Group Policy '" +
                                                lan_uplink_port["ethernet_network_group_policy"] +
                                                "' to assign to LAN Uplink Port " +
                                                str(lan_uplink_port["slot_id"]) +
                                                "/" + str(lan_uplink_port["port_id"]))
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
                                        message="Could not find unique Flow Control Policy '" +
                                                lan_uplink_port["flow_control_policy"] +
                                                "' to assign to LAN Uplink Port " +
                                                str(lan_uplink_port["slot_id"]) +
                                                "/" + str(lan_uplink_port["port_id"]) + "/" +
                                                str(lan_uplink_port["aggr_id"]))
                        else:
                            self.logger(level="warning",
                                        message="Could not find unique Flow Control Policy '" +
                                                lan_uplink_port["flow_control_policy"] +
                                                "' to assign to LAN Uplink Port " +
                                                str(lan_uplink_port["slot_id"]) +
                                                "/" + str(lan_uplink_port["port_id"]))
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
                                        message="Could not find unique Link Control Policy '" +
                                                lan_uplink_port["link_control_policy"] +
                                                "' to assign to LAN Uplink Port " +
                                                str(lan_uplink_port["slot_id"]) +
                                                "/" + str(lan_uplink_port["port_id"]) + "/" +
                                                str(lan_uplink_port["aggr_id"]))
                        else:
                            self.logger(level="warning",
                                        message="Could not find unique Link Control Policy '" +
                                                lan_uplink_port["link_control_policy"] +
                                                "' to assign to LAN Uplink Port " +
                                                str(lan_uplink_port["slot_id"]) +
                                                "/" + str(lan_uplink_port["port_id"]))
                        self._config.push_summary_manager.add_object_status(
                            obj=self, obj_detail=f"Attaching Link Control Policy "
                                                 f"'{lan_uplink_port['link_control_policy']}'",
                            obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                            message=f"Failed to find Link Control Policy "
                                    f"'{lan_uplink_port['link_control_policy']}'"
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
                                        message="Could not find unique LAN Uplink Port " +
                                                str(lan_pin_group["slot_id"]) +
                                                "/" + str(lan_pin_group["port_id"]) + "/" +
                                                str(lan_pin_group["aggr_id"]) + " to map to LAN Pin Group '" +
                                                str(lan_pin_group["name"]) + "'")
                        else:
                            self.logger(level="warning",
                                        message="Could not find unique LAN Uplink Port " +
                                                str(lan_pin_group["slot_id"]) +
                                                "/" + str(lan_pin_group["port_id"]) + " to map to LAN Pin Group '" +
                                                str(lan_pin_group["name"]) + "'")

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
                                    message="Could not find unique LAN Port-Channel PC-" +
                                            str(lan_pin_group["pc_id"]) + " to map to LAN Pin Group '" +
                                            str(lan_pin_group["name"]) + "'")

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
                                        message="Could not find unique " + port_type + " Uplink Port " +
                                                str(san_pin_group["slot_id"]) +
                                                "/" + str(san_pin_group["port_id"]) + "/" +
                                                str(san_pin_group["aggr_id"]) + " to map to SAN Pin Group '" +
                                                str(san_pin_group["name"]) + "'")
                        else:
                            self.logger(level="warning",
                                        message="Could not find unique " + port_type + " Uplink Port " +
                                                str(san_pin_group["slot_id"]) +
                                                "/" + str(san_pin_group["port_id"]) + " to map to SAN Pin Group '" +
                                                str(san_pin_group["name"]) + "'")

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
                                    message="Could not find unique " + port_type + " Port-Channel PC-" +
                                            str(san_pin_group["pc_id"]) + " to map to SAN Pin Group '" +
                                            str(san_pin_group["name"]) + "'")

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
        self.link_control_global_settings = None
        self.mac_address_table_aging = None
        self.mac_aging_time = None
        self.name = self.get_attribute(attribute_name="name")
        self.reserved_vlan_start_id = self.get_attribute(attribute_name="reserved_vlan_start_id")
        self.switching_mode = None
        self.vlan_port_count_optimization = self.get_attribute(attribute_name="vlan_port_optimization_enabled",
                                                               attribute_secondary_name="vlan_port_count_optimization")

        if self._config.load_from == "live":
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
            if hasattr(self._object, "fc_switching_mode"):
                if self._object.fc_switching_mode:
                    self.switching_mode["fc"] = self._object.fc_switching_mode

        elif self._config.load_from == "file":
            for attribute in ["link_control_global_settings", "mac_address_table_aging", "mac_aging_time",
                              "switching_mode"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

        self.clean_object()

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
        self.classes = None

        if self._config.load_from == "live":
            self.classes = self._get_classes()

        elif self._config.load_from == "file":
            for attribute in ["classes"]:
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

        # We now assign the fabric.QosClass objects to the already created fabric.SystemQosPolicy object
        if classes:
            kwargs = {
                "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
                "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
                "organization": self.get_parent_org_relationship(),
                "moid": fsqp.moid,
                "classes": classes
            }
            if self.name is not None:
                kwargs["name"] = self.name

            fabric_system_qos_policy = FabricSystemQosPolicy(**kwargs)

            if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=fabric_system_qos_policy,
                               detail=self.name + " - Classes", modify_present=True):
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
        self.vlans = None

        if self._config.load_from == "live":
            self.vlans = self._get_vlans()

        elif self._config.load_from == "file":
            for attribute in ["vlans"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

            # We use this to make sure all options of a VLAN are set to None if they are not present
            if self.vlans:
                for vlan in self.vlans:
                    for attribute in ["auto_allow_on_uplinks", "id", "multicast_policy", "name", "native_vlan",
                                      "primary_vlan_id", "sharing_type"]:
                        if attribute not in vlan:
                            vlan[attribute] = None

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
                            multicast_policy = self.get_config_objects_from_ref(ref=fabric_vlan.multicast_policy)
                        if multicast_policy:
                            vlans.append({"name": fabric_vlan.name, "id": fabric_vlan.vlan_id,
                                          "auto_allow_on_uplinks": fabric_vlan.auto_allow_on_uplinks,
                                          "native_vlan": fabric_vlan.is_native,
                                          "multicast_policy": multicast_policy[0].name,
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
                    end_vlan_id = non_overlapping_vlans[end-1]["id"]
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
                    for attribute in ["fcoe_vlan_id", "id", "name", "scope", "zoning"]:
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
                                      "fcoe_vlan_id": fabric_vsan.fcoe_vlan, "scope": fabric_vsan.vsan_scope,
                                      "zoning": fabric_vsan.default_zoning})

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
                if vsan["zoning"] is not None:
                    kwargs["default_zoning"] = vsan["zoning"]

                fabric_vsan = FabricVsan(**kwargs)

                detail = self.name + " - VSAN " + str(vsan["name"])
                self.commit(object_type="fabric.Vsan", payload=fabric_vsan, detail=detail,
                            key_attributes=["name", "vsan_id", "fc_network_policy"])

        return True


class IntersightUcsDomainProfile(IntersightConfigObject):
    _CONFIG_NAME = "UCS Domain Profile"
    _CONFIG_SECTION_NAME = "ucs_domain_profiles"
    _INTERSIGHT_SDK_OBJECT_NAME = "fabric.SwitchClusterProfile"
    _POLICY_MAPPING_TABLE = {
        "network_connectivity_policy": IntersightNetworkConnectivityPolicy,
        "ntp_policy": IntersightNtpPolicy,
        "port_policies": {
            "fabric_a": IntersightFabricPortPolicy,
            "fabric_b": IntersightFabricPortPolicy
        },
        "snmp_policy": IntersightSnmpPolicy,
        "switch_control_policy": IntersightFabricSwitchControlPolicy,
        "syslog_policy": IntersightSyslogPolicy,
        "system_qos_policy": IntersightFabricSystemQosPolicy,
        "vlan_policies": {
            "fabric_a": IntersightFabricVlanPolicy,
            "fabric_b": IntersightFabricVlanPolicy
        },
        "vsan_policies": {
            "fabric_a": IntersightFabricVsanPolicy,
            "fabric_b": IntersightFabricVsanPolicy
        }
    }

    def __init__(self, parent=None, fabric_switch_cluster_profile=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=fabric_switch_cluster_profile)

        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.name = self.get_attribute(attribute_name="name")
        self.network_connectivity_policy = None
        self.ntp_policy = None
        self.port_policies = None
        self.snmp_policy = None
        self.switch_control_policy = None
        self.syslog_policy = None
        self.system_qos_policy = None
        self.vlan_policies = None
        self.vsan_policies = None

        if self._config.load_from == "live":
            # We first need to identify the Moids of the fabric.SwitchProfile objects attached to the UCS Domain Profile
            self._switch_profiles_moids = {"fabric_a": None, "fabric_b": None}
            sw_profiles = self.get_config_objects_from_ref(ref=self._object.switch_profiles)
            if sw_profiles:
                for switch_profile in sw_profiles:
                    if switch_profile.name[-2:] == "-A":
                        self._switch_profiles_moids["fabric_a"] = switch_profile.moid
                    elif switch_profile.name[-2:] == "-B":
                        self._switch_profiles_moids["fabric_b"] = switch_profile.moid

            self.network_connectivity_policy = self._get_network_connectivity_policy()
            self.ntp_policy = self._get_ntp_policy()
            self.port_policies = self._get_port_policies()
            self.snmp_policy = self._get_snmp_policy()
            self.switch_control_policy = self._get_switch_control_policy()
            self.syslog_policy = self._get_syslog_policy()
            self.system_qos_policy = self._get_system_qos_policy()
            self.vlan_policies = self._get_vlan_policies()
            self.vsan_policies = self._get_vsan_policies()

        elif self._config.load_from == "file":
            for attribute in ["network_connectivity_policy", "ntp_policy", "port_policies", "snmp_policy",
                              "switch_control_policy", "syslog_policy", "system_qos_policy", "vlan_policies",
                              "vsan_policies"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

            # We use this to make sure all options of a Port/VLAN/VSAN Policy are set to None if they are not present
            if not self.port_policies:
                self.port_policies = {"fabric_a": None, "fabric_b": None}
            if not self.vlan_policies:
                self.vlan_policies = {"fabric_a": None, "fabric_b": None}
            if not self.vsan_policies:
                self.vsan_policies = {"fabric_a": None, "fabric_b": None}

    def _get_network_connectivity_policy(self):
        # Fetches the Network Connectivity Policy assigned to the UCS Domain Profile
        if "networkconfig_policy" in self._config.sdk_objects:
            for networkconfig_policy in self._config.sdk_objects["networkconfig_policy"]:
                if hasattr(networkconfig_policy, "profiles"):
                    for profile in networkconfig_policy.profiles:
                        if profile.moid in self._switch_profiles_moids.values():
                            return networkconfig_policy.name

        return None

    def _get_ntp_policy(self):
        # Fetches the NTP Policy assigned to the UCS Domain Profile
        if "ntp_policy" in self._config.sdk_objects:
            for ntp_policy in self._config.sdk_objects["ntp_policy"]:
                if hasattr(ntp_policy, "profiles"):
                    for profile in ntp_policy.profiles:
                        if profile.moid in self._switch_profiles_moids.values():
                            return ntp_policy.name

        return None

    def _get_port_policies(self):
        # Fetches the Port Policies assigned to the UCS Domain Profile
        port_policies = {"fabric_a": None, "fabric_b": None}
        if "fabric_port_policy" in self._config.sdk_objects:
            for fabric_port_policy in self._config.sdk_objects["fabric_port_policy"]:
                if hasattr(fabric_port_policy, "profiles"):
                    if fabric_port_policy.profiles:
                        for profile in self.get_config_objects_from_ref(ref=fabric_port_policy.profiles):
                            if profile.moid == self._switch_profiles_moids["fabric_a"]:
                                port_policies["fabric_a"] = fabric_port_policy.name
                            elif profile.moid == self._switch_profiles_moids["fabric_b"]:
                                port_policies["fabric_b"] = fabric_port_policy.name

                # We break the loop if we have found a match
                # FIXME : Does not support single Fabric Interconnect scenarios
                if port_policies["fabric_a"] and port_policies["fabric_b"]:
                    return port_policies

        if port_policies["fabric_a"] or port_policies["fabric_b"]:
            return port_policies
        else:
            return None

    def _get_snmp_policy(self):
        # Fetches the SNMP Policy assigned to the UCS Domain Profile
        if "snmp_policy" in self._config.sdk_objects:
            for snmp_policy in self._config.sdk_objects["snmp_policy"]:
                if hasattr(snmp_policy, "profiles"):
                    for profile in snmp_policy.profiles:
                        if profile.moid in self._switch_profiles_moids.values():
                            return snmp_policy.name

        return None

    def _get_switch_control_policy(self):
        # Fetches the Switch Control Policy assigned to the UCS Domain Profile
        if "fabric_switch_control_policy" in self._config.sdk_objects:
            for fabric_switch_control_policy in self._config.sdk_objects["fabric_switch_control_policy"]:
                if hasattr(fabric_switch_control_policy, "profiles"):
                    for profile in fabric_switch_control_policy.profiles:
                        if profile.moid in self._switch_profiles_moids.values():
                            return fabric_switch_control_policy.name

        return None

    def _get_syslog_policy(self):
        # Fetches the Syslog Policy assigned to the UCS Domain Profile
        if "syslog_policy" in self._config.sdk_objects:
            for syslog_policy in self._config.sdk_objects["syslog_policy"]:
                if hasattr(syslog_policy, "profiles"):
                    for profile in syslog_policy.profiles:
                        if profile.moid in self._switch_profiles_moids.values():
                            return syslog_policy.name

        return None

    def _get_system_qos_policy(self):
        # Fetches the System QoS Policy assigned to the UCS Domain Profile
        if "fabric_system_qos_policy" in self._config.sdk_objects:
            for fabric_system_qos_policy in self._config.sdk_objects["fabric_system_qos_policy"]:
                if hasattr(fabric_system_qos_policy, "profiles"):
                    for profile in fabric_system_qos_policy.profiles:
                        if profile.moid in self._switch_profiles_moids.values():
                            return fabric_system_qos_policy.name

        return None

    def _get_vlan_policies(self):
        # Fetches the VLAN Policies assigned to the UCS Domain Profile
        vlan_policies = {"fabric_a": None, "fabric_b": None}
        if "fabric_eth_network_policy" in self._config.sdk_objects:
            for fabric_eth_network_policy in self._config.sdk_objects["fabric_eth_network_policy"]:
                if hasattr(fabric_eth_network_policy, "profiles"):
                    if fabric_eth_network_policy.profiles:
                        for profile in self.get_config_objects_from_ref(ref=fabric_eth_network_policy.profiles):
                            if profile.moid == self._switch_profiles_moids["fabric_a"]:
                                vlan_policies["fabric_a"] = fabric_eth_network_policy.name
                            elif profile.moid == self._switch_profiles_moids["fabric_b"]:
                                vlan_policies["fabric_b"] = fabric_eth_network_policy.name

                # We break the loop if we have found a match
                # FIXME : Does not support single Fabric Interconnect scenarios
                if vlan_policies["fabric_a"] and vlan_policies["fabric_b"]:
                    return vlan_policies

        if vlan_policies["fabric_a"] or vlan_policies["fabric_b"]:
            return vlan_policies
        else:
            return None

    def _get_vsan_policies(self):
        # Fetches the VSAN Policies assigned to the UCS Domain Profile
        vsan_policies = {"fabric_a": None, "fabric_b": None}
        if "fabric_fc_network_policy" in self._config.sdk_objects:
            for fabric_fc_network_policy in self._config.sdk_objects["fabric_fc_network_policy"]:
                if hasattr(fabric_fc_network_policy, "profiles"):
                    if fabric_fc_network_policy.profiles:
                        for profile in self.get_config_objects_from_ref(ref=fabric_fc_network_policy.profiles):
                            if profile.moid == self._switch_profiles_moids["fabric_a"]:
                                vsan_policies["fabric_a"] = fabric_fc_network_policy.name
                            elif profile.moid == self._switch_profiles_moids["fabric_b"]:
                                vsan_policies["fabric_b"] = fabric_fc_network_policy.name

                # We break the loop if we have found a match
                # FIXME : Does not support single Fabric Interconnect scenarios
                if vsan_policies["fabric_a"] and vsan_policies["fabric_b"]:
                    return vsan_policies

        if vsan_policies["fabric_a"] or vsan_policies["fabric_b"]:
            return vsan_policies
        else:
            return None

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.fabric_switch_cluster_profile import FabricSwitchClusterProfile

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        # We identify the parent organization as it will be used many times
        org = self.get_parent_org_relationship()
        if not org:
            return False

        # We first need to push the main fabric.SwitchClusterProfile object
        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": org
        }
        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()

        fabric_switch_cluster_profile = FabricSwitchClusterProfile(**kwargs)

        fscp = self.commit(
            object_type=self._INTERSIGHT_SDK_OBJECT_NAME,
            payload=fabric_switch_cluster_profile,
            detail=self.name,
            return_relationship=True
        )
        if not fscp:
            return False

        # We now need to push the fabric.SwitchProfile objects for both Fabric Interconnects
        # FIXME: Add support for single Fabric Interconnect
        from intersight.model.fabric_switch_profile import FabricSwitchProfile
        kwargs = {
            "object_type": "fabric.SwitchProfile",
            "class_id": "fabric.SwitchProfile",
            "switch_cluster_profile": fscp
        }
        if self.name is not None:
            kwargs["name"] = self.name + "-A"
        if self.descr is not None:
            kwargs["description"] = self.descr

        fabric_switch_profile_a = FabricSwitchProfile(**kwargs)

        fspa = self.commit(
            object_type="fabric.SwitchProfile",
            payload=fabric_switch_profile_a,
            detail=self.name + " - Switch Profile FI A",
            return_relationship=True
        )
        if not fspa:
            return False

        if self.name is not None:
            kwargs["name"] = self.name + "-B"

        fabric_switch_profile_b = FabricSwitchProfile(**kwargs)

        fspb = self.commit(
            object_type="fabric.SwitchProfile",
            payload=fabric_switch_profile_b,
            detail=self.name + " - Switch Profile FI B",
            return_relationship=True
        )
        if not fspb:
            return False

        # We also need to map the VLAN Policies to the just created fabric.SwitchProfile objects
        for fabric_id, vlan_policy_name in self.vlan_policies.items():
            if vlan_policy_name:
                # We first need to identify the VLAN Policy object reference
                vlan_policy = self.get_live_object(
                    object_name=vlan_policy_name,
                    object_type="fabric.EthNetworkPolicy",
                    return_reference=False
                )
                if vlan_policy:
                    # We now need to modify the VLAN Policy to add a relationship to the SwitchProfile
                    if fabric_id == "fabric_a":
                        vlan_policy.profiles.append(fspa)
                    elif fabric_id == "fabric_b":
                        vlan_policy.profiles.append(fspb)

                    fab_id = fabric_id.upper()[-1:]
                    if not self.commit(
                            object_type="fabric.EthNetworkPolicy",
                            payload=vlan_policy,
                            detail=self.name + " - VLAN Policy Switch Profile " + fab_id + " assignment",
                            modify_present=True
                    ):
                        return False
                else:
                    self._config.push_summary_manager.add_object_status(
                        obj=self, obj_detail=f"Attaching VLAN Policy '{vlan_policy_name}'",
                        obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                        message=f"Failed to find VLAN Policy '{vlan_policy_name}'"
                    )

        # We also need to map the VSAN Policies to the just created fabric.SwitchProfile objects
        for fabric_id, vsan_policy_name in self.vsan_policies.items():
            if vsan_policy_name:
                # We first need to identify the VSAN Policy object reference
                vsan_policy = self.get_live_object(
                    object_name=vsan_policy_name,
                    object_type="fabric.FcNetworkPolicy",
                    return_reference=False
                )
                if vsan_policy:
                    # We now need to modify the VSAN Policy to add a relationship to the SwitchProfile
                    if fabric_id == "fabric_a":
                        vsan_policy.profiles.append(fspa)
                    elif fabric_id == "fabric_b":
                        vsan_policy.profiles.append(fspb)

                    fab_id = fabric_id.upper()[-1:]
                    if not self.commit(
                            object_type="fabric.FcNetworkPolicy",
                            payload=vsan_policy,
                            detail=self.name + " - VSAN Policy Switch Profile " + fab_id + " assignment",
                            modify_present=True
                    ):
                        return False
                else:
                    self._config.push_summary_manager.add_object_status(
                        obj=self, obj_detail=f"Attaching VSAN Policy '{vsan_policy_name}'",
                        obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                        message=f"Failed to find VSAN Policy '{vsan_policy_name}'"
                    )

        # We also need to map the Port Policies to the just created fabric.SwitchProfile objects
        for fabric_id, port_policy_name in self.port_policies.items():
            if port_policy_name:
                # We first need to identify the Port Policy object reference
                port_policy = self.get_live_object(
                    object_name=port_policy_name,
                    object_type="fabric.PortPolicy",
                    return_reference=False
                )
                if port_policy:
                    # We now need to modify the Port Policy to add a relationship to the SwitchProfile
                    if fabric_id == "fabric_a":
                        port_policy.profiles.append(fspa)
                    elif fabric_id == "fabric_b":
                        port_policy.profiles.append(fspb)

                    fab_id = fabric_id.upper()[-1:]
                    if not self.commit(
                            object_type="fabric.PortPolicy", payload=port_policy,
                            detail=self.name + " - Port Policy Switch Profile " + fab_id + " assignment",
                            modify_present=True
                    ):
                        return False
                else:
                    self._config.push_summary_manager.add_object_status(
                        obj=self, obj_detail=f"Attaching Port Policy '{port_policy_name}'",
                        obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                        message=f"Failed to find Port Policy '{port_policy_name}'"
                    )

        # We also need to map the SNMP Policy to the just created fabric.SwitchProfile objects
        if self.snmp_policy:
            # We first need to identify the SNMP Policy object reference
            snmp_policy = self.get_live_object(
                object_name=self.snmp_policy,
                object_type="snmp.Policy",
                return_reference=False
            )
            if snmp_policy:
                # We now need to modify the SNMP Policy to add a relationship to the Switch Profile
                snmp_policy.profiles.append(fspa)
                snmp_policy.profiles.append(fspb)

                if not self.commit(
                        object_type="snmp.Policy",
                        payload=snmp_policy,
                        detail=self.name + " - SNMP Policy Switch Profiles assignment",
                        modify_present=True
                ):
                    return False
            else:
                self._config.push_summary_manager.add_object_status(
                    obj=self, obj_detail=f"Attaching SNMP Policy '{self.snmp_policy}'",
                    obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                    message=f"Failed to find SNMP Policy '{self.snmp_policy}'"
                )

        # We also need to map the Switch Control Policy to the just created fabric.SwitchProfile objects
        if self.switch_control_policy:
            # We first need to identify the Switch Control Policy object reference
            sw_ctrl_policy = self.get_live_object(
                object_name=self.switch_control_policy,
                object_type="fabric.SwitchControlPolicy",
                return_reference=False
            )
            if sw_ctrl_policy:
                # We now need to modify the Switch Control Policy to add a relationship to the SwitchProfile
                sw_ctrl_policy.profiles.append(fspa)
                sw_ctrl_policy.profiles.append(fspb)

                if not self.commit(
                        object_type="fabric.SwitchControlPolicy",
                        payload=sw_ctrl_policy,
                        detail=self.name + " - Switch Control Policy Switch Profiles assignment",
                        modify_present=True
                ):
                    return False
            else:
                self._config.push_summary_manager.add_object_status(
                    obj=self, obj_detail=f"Attaching Switch Control Policy '{self.switch_control_policy}'",
                    obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                    message=f"Failed to find Switch Control Policy '{self.switch_control_policy}'"
                )

        # We also need to map the System QoS Policy to the just created fabric.SwitchProfile objects
        if self.system_qos_policy:
            # We first need to identify the System QoS Policy object reference
            qos_policy = self.get_live_object(
                object_name=self.system_qos_policy,
                object_type="fabric.SystemQosPolicy",
                return_reference=False
            )
            if qos_policy:
                # We now need to modify the System QoS Policy to add a relationship to the SwitchProfile
                qos_policy.profiles.append(fspa)
                qos_policy.profiles.append(fspb)

                if not self.commit(
                        object_type="fabric.SystemQosPolicy",
                        payload=qos_policy,
                        detail=self.name + " - System QoS Policy Switch Profiles assignment",
                        modify_present=True
                ):
                    return False
            else:
                self._config.push_summary_manager.add_object_status(
                    obj=self, obj_detail=f"Attaching System QoS Policy '{self.system_qos_policy}'",
                    obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                    message=f"Failed to find System QoS Policy '{self.system_qos_policy}'"
                )

        # We also need to map the Syslog Policy to the just created fabric.SwitchProfile objects
        if self.syslog_policy:
            # We first need to identify the Syslog Policy object reference
            syslog_policy = self.get_live_object(
                object_name=self.syslog_policy,
                object_type="syslog.Policy",
                return_reference=False
            )
            if syslog_policy:
                # We now need to modify the Syslog Policy to add a relationship to the Switch Profile
                syslog_policy.profiles.append(fspa)
                syslog_policy.profiles.append(fspb)

                if not self.commit(
                        object_type="syslog.Policy",
                        payload=syslog_policy,
                        detail=self.name + " - Syslog Policy Switch Profiles assignment",
                        modify_present=True
                ):
                    return False
            else:
                self._config.push_summary_manager.add_object_status(
                    obj=self, obj_detail=f"Attaching Syslog Policy '{self.syslog_policy}'",
                    obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                    message=f"Failed to find Syslog Policy '{self.syslog_policy}'"
                )

        # We also need to map the Network Connectivity Policy to the just created fabric.SwitchProfile objects
        if self.network_connectivity_policy:
            # We first need to identify the Network Connectivity Policy object reference
            network_connectivity_policy = self.get_live_object(
                object_name=self.network_connectivity_policy,
                object_type="networkconfig.Policy",
                return_reference=False
            )
            if network_connectivity_policy:
                network_connectivity_policy.profiles.append(fspa)
                network_connectivity_policy.profiles.append(fspb)

                if not self.commit(
                        object_type="networkconfig.Policy",
                        payload=network_connectivity_policy,
                        detail=self.name + " - Network Connectivity Policy Switch Profiles assignment",
                        modify_present=True
                ):
                    return False
            else:
                self._config.push_summary_manager.add_object_status(
                    obj=self, obj_detail=f"Attaching Network Connectivity Policy '{self.network_connectivity_policy}'",
                    obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                    message=f"Failed to find Network Connectivity Policy '{self.network_connectivity_policy}'"
                )

        # Lastly, we need to map the NTP Policy to the just created fabric.SwitchProfile objects
        if self.ntp_policy:
            # We first need to identify the NTP Policy object reference
            ntp_policy = self.get_live_object(
                object_name=self.ntp_policy,
                object_type="ntp.Policy",
                return_reference=False
            )
            if ntp_policy:
                ntp_policy.profiles.append(fspa)
                ntp_policy.profiles.append(fspb)

                if not self.commit(
                        object_type="ntp.Policy",
                        payload=ntp_policy,
                        detail=self.name + " - NTP Policy Switch Profiles assignment",
                        modify_present=True
                ):
                    return False
            else:
                self._config.push_summary_manager.add_object_status(
                    obj=self, obj_detail=f"Attaching NTP Policy '{self.ntp_policy}'",
                    obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                    message=f"Failed to find NTP Policy '{self.ntp_policy}'"
                )

        return True
