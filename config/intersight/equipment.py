# coding: utf-8
# !/usr/bin/env python

""" equipment.py: Easy UCS Deployment Tool """
import re
from config.intersight.object import IntersightConfigObject


class IntersightEquipment(IntersightConfigObject):
    _CONFIG_NAME = "Equipment"
    _CONFIG_SECTION_NAME = "equipment"
    _CONFIG_SECTION_ATTRIBUTES_MAP = {
        "imm_domains": "IMM Domains",
        "rack_units": "Rack Units"
    }

    def __init__(self, parent=None, equipment=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=equipment)

        self.fabric_interconnects = None # DEPRECATED
        self.imm_domains = []
        self.rack_units = []

        if self._config.load_from == "live":
            for asset_device_registration in self._config.sdk_objects.get("asset_device_registration", []):
                if asset_device_registration.platform_type == "UCSFIISM":
                    # We are working with an IMM domain claimed on this Intersight account
                    self.imm_domains.append(IntersightImmDomain(parent=self,
                                                                asset_device_registration=asset_device_registration))

                elif asset_device_registration.platform_type in ["IMC", "IMCM4", "IMCM5", "IMCRack"] and \
                        not asset_device_registration.parent_connection:
                    # We are working with a standalone rack server (CIMC) (no parent connection to a UCS domain)
                    for compute_rack_unit in self._config.sdk_objects.get("compute_rack_unit", []):
                        if compute_rack_unit.registered_device.moid == asset_device_registration.moid:
                            self.rack_units.append(IntersightComputeRackUnit(parent=self,
                                                                             compute_rack_unit=compute_rack_unit))

                # We sort the list of IMM domains to return objects in an appropriate order
                self.imm_domains = sorted(self.imm_domains,
                                          key=lambda x: x.name if getattr(x, "name", None) else 0)

                # We sort the list of rack servers to return objects in an appropriate order
                self.rack_units = sorted(self.rack_units,
                                         key=lambda x: x.name if getattr(x, "name", None) else 0)

        if self._config.load_from == "file":
            # DEPRECATED starting with EasyUCS 1.0.2: fabric_interconnects
            if equipment is not None and equipment.get("fabric_interconnects"):
                self.imm_domains.append(IntersightImmDomain(self, equipment))
            else:
                self.imm_domains = self._get_generic_element(
                    json_content=equipment,
                    object_class=IntersightImmDomain,
                    name_to_fetch="imm_domains"
                )
            self.rack_units = self._get_generic_element(
                json_content=equipment,
                object_class=IntersightComputeRackUnit,
                name_to_fetch="rack_units"
            )
            
    def _get_generic_element(self, json_content=None, object_class=None, name_to_fetch=None):
        # Generic method to instantiate objects under an Equipment depending on loading from file
        if json_content is not None:
            if name_to_fetch in json_content:
                return [object_class(self, generic) for generic in json_content[name_to_fetch]]
        else:
            return []

    @IntersightConfigObject.update_taskstep_description()
    def push_subobjects(self):
        objects_to_push = ["imm_domains", "rack_units"]
        is_pushed = True
        for config_object_type in objects_to_push:
            if getattr(self, config_object_type) is not None:
                if getattr(self, config_object_type).__class__.__name__ == "list":
                    for subobject in getattr(self, config_object_type):
                        is_pushed = subobject.push_object() and is_pushed

        return is_pushed


class IntersightImmDomain(IntersightConfigObject):
    _CONFIG_NAME = "IMM Domains"
    _CONFIG_SECTION_NAME = "imm_domains"
    _CONFIG_SECTION_ATTRIBUTES_MAP = {
        "chassis": "Chassis",
        "fabric_extenders": "Fabric Extenders",
        "fabric_interconnects": "Fabric Interconnects",
        "rack_units": "Rack Units"
    }

    def __init__(self, parent=None, asset_device_registration=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=asset_device_registration)

        self.chassis = []
        self.fabric_extenders = []
        self.fabric_interconnects = []
        self.name = None
        self.rack_units = []

        if self._config.load_from == "live":
            if self._object.device_hostname:
                self.name = self._object.device_hostname[0]

            # We need to find the "equipment.Chassis" objects that belong to this IMM domain
            for equipment_chassis in self._config.sdk_objects.get("equipment_chassis", []):
                if equipment_chassis.registered_device.moid == asset_device_registration.moid:
                    self.chassis.append(IntersightChassis(parent=self, equipment_chassis=equipment_chassis))

            # We sort the list of chassis to return objects in an appropriate order
            self.chassis = sorted(self.chassis, key=lambda x: x.id if getattr(x, "id", None) else 0)

            # We need to find the "compute.RackUnit" objects that belong to this IMM domain
            for compute_rack_unit in self._config.sdk_objects.get("compute_rack_unit", []):
                parent_asset_device_registration = self.get_config_objects_from_ref(
                    ref=compute_rack_unit.registered_device)
                if len(parent_asset_device_registration) == 1:
                    if parent_asset_device_registration[0].parent_connection:
                        if parent_asset_device_registration[0].parent_connection.moid == \
                                asset_device_registration.moid:
                            self.rack_units.append(
                                IntersightComputeRackUnit(parent=self, compute_rack_unit=compute_rack_unit))

            # We sort the list of rack units to return objects in an appropriate order
            self.rack_units = sorted(self.rack_units, key=lambda x: x.id if getattr(x, "id", None) else 0)

            # We need to find the "network.Element" objects that belong to this IMM domain
            for network_element in self._config.sdk_objects.get("network_element", []):
                if network_element.registered_device.moid == asset_device_registration.moid:
                    self.fabric_interconnects.append(IntersightFabricInterconnect(parent=self,
                                                                                  network_element=network_element))

            # We sort the list of FIs to return objects in an appropriate order
            self.fabric_interconnects = sorted(self.fabric_interconnects,
                                               key=lambda x: x.switch_id if getattr(x, "id", None) else 0)

            # Finally, we need to find the "equipment.Fex" objects that belong to this IMM domain
            for equipment_fex in self._config.sdk_objects.get("equipment_fex", []):
                if equipment_fex.registered_device.moid == asset_device_registration.moid:
                    self.fabric_extenders.append(IntersightFex(parent=self, equipment_fex=equipment_fex))

            # We sort the list of FEXs to return objects in an appropriate order
            self.fabric_extenders = sorted(self.fabric_extenders, key=lambda x: x.id if getattr(x, "id", None) else 0)

        elif self._config.load_from == "file":
            if "chassis" in self._object:
                for chassis in self._object["chassis"]:
                    self.chassis.append(IntersightChassis(parent=self, equipment_chassis=chassis))
            if "fabric_extenders" in self._object:
                for fex in self._object["fabric_extenders"]:
                    self.fabric_extenders.append(IntersightFex(parent=self, equipment_fex=fex))
            if "fabric_interconnects" in self._object:
                for fi in self._object["fabric_interconnects"]:
                    self.fabric_interconnects.append(IntersightFabricInterconnect(parent=self, network_element=fi))
            if "rack_units" in self._object:
                for rack in self._object["rack_units"]:
                    self.rack_units.append(IntersightComputeRackUnit(parent=self, compute_rack_unit=rack))
            for attribute in ["name"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))
        
    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        objects_to_push = ['chassis', 'fabric_extenders', 'fabric_interconnects', 'rack_units']
        is_pushed = True
        for config_object_type in objects_to_push:
            if getattr(self, config_object_type) is not None:
                if getattr(self, config_object_type).__class__.__name__ == "list":
                    for subobject in getattr(self, config_object_type):
                        is_pushed = subobject.push_object() and is_pushed

        return is_pushed


class IntersightFabricInterconnect(IntersightConfigObject):
    _CONFIG_NAME = "Fabric Interconnect"
    _CONFIG_SECTION_NAME = "fabric_interconnects"
    _INTERSIGHT_SDK_OBJECT_NAME = "network.Element"

    def __init__(self, parent=None, network_element=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=network_element)

        self.name = None
        self.switch_id = self.get_attribute(attribute_name="switch_id")
        self.serial = self.get_attribute(attribute_name="serial")
        self.traffic_mirroring_sessions = None
        self.ports = None

        if self._config.load_from == "live":
            self._get_device_host_name()
            self.traffic_mirroring_sessions = self._get_traffic_mirroring_sessions()
            self.ports = self._get_ports()

        elif self._config.load_from == "file":
            for attribute in ["name", "ports", "traffic_mirroring_sessions"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

    def _get_device_host_name(self):
        # get the host name of the device
        if hasattr(self._object, "registered_device"):
            if self._object.registered_device:
                asset_device_registration_list = self.get_config_objects_from_ref(
                    ref={"object_type": "asset.DeviceRegistration", "moid": self._object.registered_device.moid})
                if len(asset_device_registration_list) != 1:
                    self.logger(level="debug",
                                message="Could not find the appropriate asset.DeviceRegistration " +
                                        "for Fabric Interconnect Serial Number '" + self.serial + "'")
                else:
                    self.name = asset_device_registration_list[0].device_hostname[0]

    def _get_traffic_mirroring_sessions(self):
        # Get the list of traffic mirroring sessions
        span_sessions = []
        if "fabric_span_session" in self._config.sdk_objects:
            for fabric_span_session in self._config.sdk_objects["fabric_span_session"]:
                if  fabric_span_session.network_element.moid == self._moid:
                    span_session = {}
                    span_session.update({
                        "name": fabric_span_session.name,
                        "enable_session": fabric_span_session.admin_state,
                        "enable_span_control_packets": fabric_span_session.span_control_packets
                    })
                    if hasattr(fabric_span_session, "dest_ports"):
                        if fabric_span_session.dest_ports:
                            span_session.update({"destination_port": self._get_destination_port(fabric_span_session)})
                    
                    if hasattr(fabric_span_session, "source_ports"):
                        if fabric_span_session.source_ports:
                            span_session.update(
                                {"uplink_ethernet_ports": self._get_ethernet_ports(fabric_span_session)})

                    if hasattr(fabric_span_session, "source_port_channels"):
                        if fabric_span_session.source_port_channels:
                            span_session.update({"uplink_ethernet_port_channels": self._get_ethernet_port_channels(
                                fabric_span_session)})

                    if hasattr(fabric_span_session, "source_vlans"):
                        if fabric_span_session.source_vlans:
                            span_session.update({"vlans": self._get_vlans(fabric_span_session)})

                    if hasattr(fabric_span_session, "source_virtual_ifs"):
                        if fabric_span_session.source_virtual_ifs:
                            span_session.update({"vnics": self._get_vnics(fabric_span_session)})

                    span_sessions.append(span_session)

            return span_sessions

        return None

    def _get_destination_port(self, fabric_span_session):
        # Determines the details of the span destination ports.
        if "fabric_span_dest_eth_port" in self._config.sdk_objects:
            for destination_port in self._config.sdk_objects["fabric_span_dest_eth_port"]:
                if hasattr(destination_port, "span_session"):
                    dest_port = {}
                    if destination_port.span_session.moid == fabric_span_session.moid:
                        dest_port.update({
                            "aggr_id": destination_port.port_id if destination_port.aggregate_port_id != 0 else None,
                            "slot_id": destination_port.slot_id,
                            "port_id": destination_port.aggregate_port_id if destination_port.aggregate_port_id != 0 \
                                                                          else destination_port.port_id,
                            "admin_speed": destination_port.admin_speed,
                            "fec": destination_port.fec
                        })
                        return dest_port
        return None
    
    def _get_ethernet_ports(self, fabric_span_session):
        # Determines the details of the source uplink ethernet ports.
        if "fabric_span_source_eth_port" in self._config.sdk_objects:
            source_eth_ports = []
            for source_eth_port in self._config.sdk_objects["fabric_span_source_eth_port"]:
                if hasattr(source_eth_port, "span_session"):
                    if source_eth_port.span_session.moid == fabric_span_session.moid:
                        source_eth_ports.append({
                            "aggr_id": source_eth_port.port_id if source_eth_port.aggregate_port_id != 0 else None,
                            "slot_id": source_eth_port.slot_id,
                            "port_id": source_eth_port.aggregate_port_id if source_eth_port.aggregate_port_id != 0 \
                                                                         else source_eth_port.port_id,
                            "direction": source_eth_port.direction
                        })
            return source_eth_ports
        return None
    
    def _get_ethernet_port_channels(self, fabric_span_session):
        # Determines the details of the source uplink ethernet port channels.
        if "fabric_span_source_eth_port_channel" in self._config.sdk_objects:
            source_eth_port_channels = []
            for source_eth_port_channel in self._config.sdk_objects["fabric_span_source_eth_port_channel"]:
                if hasattr(source_eth_port_channel, "span_session"):
                    if source_eth_port_channel.span_session.moid == fabric_span_session.moid:
                        source_eth_port_channels.append({
                            "direction": source_eth_port_channel.direction,
                            "id": source_eth_port_channel.pc_id
                        })
            return source_eth_port_channels
        return None

    @staticmethod
    def _get_action_based_user_label(user_label=None):
        """
        Extracts only action-based user labels from a Fabric Interconnect (FI) user label.

        On Fabric Interconnects (FIs), user labels can be of two types:
        1. Port policy user labels – labels set via port policy, no actions triggered.
        2. Action-based user labels – labels set directly on the FI using "Set User Label" action, always inside < >.

        This function fetches only the action-based labels (inside < >).

        Args:
            user_label (str): The input string containing the user label.

        Returns:
            str: The action-based label found inside < >. Returns None if no action-based label is found
        """

        match = re.search(r"<\s*(.*?)\s*>", user_label)
        if match:
            value = match.group(1)
            return value
        return None

    def _get_ports(self):
        # Determines the details of the source Ethernet and FC ports/port-channels.
        source_eth_ports = []
        source_fc_ports = []
        source_eth_port_channels = []
        source_fc_port_channels = []

        if "ether_physical_port" in self._config.sdk_objects:
            for source_eth_port in self._config.sdk_objects["ether_physical_port"]:
                if any(item.get("moid") == self._moid for item in source_eth_port.ancestors):
                    if source_eth_port.user_label:
                        source_eth_ports.append({
                            "aggr_id": source_eth_port.port_id if source_eth_port.aggregate_port_id != 0 else None,
                            "slot_id": source_eth_port.slot_id,
                            "port_id": source_eth_port.aggregate_port_id
                            if source_eth_port.aggregate_port_id != 0 else source_eth_port.port_id,
                            "user_label": self._get_action_based_user_label(user_label=source_eth_port.user_label)
                        })

        if "fc_physical_port" in self._config.sdk_objects:
            for source_fc_port in self._config.sdk_objects["fc_physical_port"]:
                if any(item.get("moid") == self._moid for item in source_fc_port.ancestors):
                    if source_fc_port.user_label:
                        source_fc_ports.append({
                            "aggr_id": source_fc_port.port_id if source_fc_port.aggregate_port_id != 0 else None,
                            "slot_id": source_fc_port.slot_id,
                            "port_id": source_fc_port.aggregate_port_id
                            if source_fc_port.aggregate_port_id != 0 else source_fc_port.port_id,
                            "user_label": self._get_action_based_user_label(user_label=source_fc_port.user_label)
                        })

        if "ether_port_channel" in self._config.sdk_objects:
            for source_eth_port_channel in self._config.sdk_objects["ether_port_channel"]:
                if (any(item.get("moid") == self._moid for item in source_eth_port_channel.ancestors) and
                        source_eth_port_channel.role in ['HostPC', 'unknown']):
                    if source_eth_port_channel.user_label:
                        source_eth_port_channels.append({
                            "id": source_eth_port_channel.port_channel_id,
                            "user_label": self._get_action_based_user_label(
                                user_label=source_eth_port_channel.user_label)
                        })

        if "fc_port_channel" in self._config.sdk_objects:
            for source_fc_port_channel in self._config.sdk_objects["fc_port_channel"]:
                if any(item.get("moid") == self._moid for item in source_fc_port_channel.ancestors):
                    if source_fc_port_channel.user_label:
                        source_fc_port_channels.append({
                            "id": source_fc_port_channel.port_channel_id,
                            "user_label": self._get_action_based_user_label(
                                user_label=source_fc_port_channel.user_label)
                        })

        ports = {}
        if source_eth_ports:
            ports.update({"ethernet_ports": source_eth_ports})
        if source_fc_ports:
            ports.update({"fc_ports": source_fc_ports})
        if source_eth_port_channels:
            ports.update({"ethernet_port_channels": source_eth_port_channels})
        if source_fc_port_channels:
            ports.update({"fc_port_channels": source_fc_port_channels})

        return ports if ports else None

    def _get_vlans(self, fabric_span_session):
        # Determines the details of the source VLANs.
        if "fabric_span_source_vlan" in self._config.sdk_objects:
            source_vlans = []
            for source_vlan in self._config.sdk_objects["fabric_span_source_vlan"]:
                if hasattr(source_vlan, "span_session"):
                    if source_vlan.span_session.moid == fabric_span_session.moid:
                        source_vlans.append({
                            "direction": source_vlan.direction,
                            "id": source_vlan.vlan_id
                        })
            return source_vlans
        return None
    
    def _get_vnics(self, fabric_span_session):
        # Determines the details of the source vNICs.
        if "fabric_span_source_vnic_eth_if" in self._config.sdk_objects:
            source_vnics = []
            for span_source_vnic_eth_if in self._config.sdk_objects["fabric_span_source_vnic_eth_if"]:
                if hasattr(span_source_vnic_eth_if, "span_session"):
                    if span_source_vnic_eth_if.span_session.moid == fabric_span_session.moid:
                        vnic = {
                            "name": span_source_vnic_eth_if.name,
                            "direction": span_source_vnic_eth_if.direction
                        }
                        for source_vnic in self._config.sdk_objects["vnic_eth_if"]:
                            if span_source_vnic_eth_if.vnic.moid == source_vnic.moid:
                                for server_profile in self._config.sdk_objects["server_profile"]:
                                    if source_vnic.profile.moid == server_profile.moid:
                                        vnic.update({"server_profile": server_profile.name})
                                        for organization in self._config.sdk_objects["organization_organization"]:
                                            if server_profile.organization.moid == organization.moid:
                                                vnic.update({"org": organization.name})
                        source_vnics.append(vnic)

            return source_vnics
        return None

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.fabric_span_session import FabricSpanSession
        
        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}-{self.switch_id}")
        network_element_list = []
        if self.serial:
            network_element_list = self._device.query(object_type="network.Element", filter="Serial eq '%s'" % self.serial)
        elif self.name and self.switch_id:
            asset_device_registration_list = self._device.query(
                object_type="asset.DeviceRegistration",
                filter=f"DeviceHostname in ('{self.name}')"
            )
            if len(asset_device_registration_list) != 1:
                self.logger(level="debug",
                            message="Could not find the appropriate asset.DeviceRegistration " +
                                    "for Fabric Interconnect '" + self.name + "'")
                return False
            else:
                network_element_list = self._device.query(object_type="network.Element", filter=f"RegisteredDevice.Moid eq \
                                        '{asset_device_registration_list[0].moid}'and SwitchId eq '{self.switch_id}'")
        if len(network_element_list) != 1:
            err_message = "Could not find Fabric Interconnect '" + self.name + '-' + self.switch_id + "'"
            self.logger(level="error", message=err_message)
            return False
        elif len(network_element_list) == 1 and self.tags:
            from intersight.model.network_element import NetworkElement
            kwargs = {
                "object_type": "network.Element",
                "class_id": "network.Element"
            }
            if self.tags is not None:
                kwargs["tags"] = self.create_tags()
            kwargs["moid"] = network_element_list[0].moid
            fi = NetworkElement(**kwargs)
            self.commit(
                object_type=self._INTERSIGHT_SDK_OBJECT_NAME,
                key_attributes=["moid"], payload=fi, detail=self.name + ' - Tags',
                modify_present=True)

        if self.serial and self.traffic_mirroring_sessions:
            info_message = (f"The domain '{self.name}' must be claimed first in order to include the traffic mirroring "
                            f"sessions.")
            self.logger(level="info", message=info_message)
            for traffic_mirroring_session in self.traffic_mirroring_sessions:
                self.logger(message=f"Pushing {self._CONFIG_NAME} Traffic Mirroring Session configuration: " \
                            + traffic_mirroring_session["name"])
                
                span_session_kwargs = {
                    "object_type": "fabric.SpanSession",
                    "class_id": "fabric.SpanSession"
                }
                if "name" in traffic_mirroring_session:
                    span_session_kwargs["name"] = traffic_mirroring_session["name"]
                if "enable_session" in traffic_mirroring_session:
                    span_session_kwargs["admin_state"] = traffic_mirroring_session["enable_session"]
                if "enable_span_control_packets" in traffic_mirroring_session:
                    span_session_kwargs["span_control_packets"] = traffic_mirroring_session["enable_span_control_packets"]
                
                if network_element_list:
                    if len(network_element_list) != 1:
                        err_message = "Could not find Fabric Interconnect '" + self.name + '-' + self.switch_id + \
                                      "' to assign Traffic Mirroring Session '" + traffic_mirroring_session["name"] + "'"
                        self.logger(level="error", message=err_message)
                        return False
                    else:
                        span_session_kwargs["network_element"] = self.create_relationship_equivalent(
                            sdk_object=network_element_list[0])
                else:
                    err_message = "Could not find Fabric Interconnect '" + self.name + '-' + self.switch_id + \
                                  "' to assign Traffic Mirroring Session '" + traffic_mirroring_session["name"] + "'"
                    self.logger(level="error", message=err_message)
                    self._config.push_summary_manager.add_object_status(
                        obj=self,
                        obj_detail=f"Fabric Interconnect '{self.name}-{self.switch_id}' with " +
                                   f"Traffic Mirroring Session '" + traffic_mirroring_session["name"] + "'",
                        obj_type="fabric.SpanSession",
                        status="failed",
                        message=err_message
                    )
                    return False
                    
                fabric_span_session = FabricSpanSession(**span_session_kwargs)
                fss = self.commit(
                    object_type="fabric.SpanSession", key_attributes=["name", "network_element"],
                    payload=fabric_span_session,
                    detail="Traffic Mirroring Session: " + traffic_mirroring_session["name"], return_relationship=True
                )
                if not fss:
                    return False

                if traffic_mirroring_session.get("destination_port"):
                    from intersight.model.fabric_span_dest_eth_port import FabricSpanDestEthPort

                    dest_port_kwargs = {
                        "object_type": "fabric.SpanDestEthPort",
                        "class_id": "fabric.SpanDestEthPort",
                        "span_session": fss
                    }
                    # List of attributes for destination ports
                    attributes = ["admin_speed", "slot_id", "fec"]

                    for attr in attributes:
                        value = traffic_mirroring_session["destination_port"].get(attr)
                        if value is not None:
                            dest_port_kwargs[attr] = value

                    aggr_id = traffic_mirroring_session["destination_port"].get("aggr_id", 0)
                    port_id = traffic_mirroring_session["destination_port"].get("port_id", 0)

                    if aggr_id not in [None, 0]:  # We have a breakout port
                        dest_port_kwargs["port_id"] = aggr_id
                        dest_port_kwargs["aggregate_port_id"] = port_id
                    else:
                        dest_port_kwargs["port_id"] = port_id
                        dest_port_kwargs["aggregate_port_id"] = 0

                    fabric_span_dest_eth_port = FabricSpanDestEthPort(**dest_port_kwargs)

                    self.commit(
                        object_type="fabric.SpanDestEthPort", payload=fabric_span_dest_eth_port,
                        detail="Traffic Mirroring Session: " + traffic_mirroring_session["name"] + \
                               " - Destination Port " +
                               str(traffic_mirroring_session["destination_port"].get("port_id", None))
                    )

                if traffic_mirroring_session.get("uplink_ethernet_ports"):
                    from intersight.model.fabric_span_source_eth_port import FabricSpanSourceEthPort

                    for uplink_eth_port in traffic_mirroring_session["uplink_ethernet_ports"]:
                        source_eth_port_kwargs = {
                            "object_type": "fabric.SpanSourceEthPort",
                            "class_id": "fabric.SpanSourceEthPort",
                            "span_session": fss
                        }

                        # list of attributes for source ethernet ports
                        attributes = ["direction", "slot_id"]
                        for attr in attributes:
                            if uplink_eth_port.get(attr) is not None:
                                source_eth_port_kwargs[attr] = uplink_eth_port.get(attr)

                        aggr_id = uplink_eth_port.get("aggr_id", 0)
                        port_id = uplink_eth_port.get("port_id", 0)

                        if aggr_id not in [None, 0]:  # We have a breakout port
                            source_eth_port_kwargs["port_id"] = aggr_id
                            source_eth_port_kwargs["aggregate_port_id"] = port_id
                        else:
                            source_eth_port_kwargs["port_id"] = port_id
                            source_eth_port_kwargs["aggregate_port_id"] = 0

                        fabric_span_source_eth_port = FabricSpanSourceEthPort(**source_eth_port_kwargs)

                        self.commit(object_type="fabric.SpanSourceEthPort", payload=fabric_span_source_eth_port,
                                           detail="Traffic Mirroring Session: " + traffic_mirroring_session["name"] + \
                                            " - Uplink Ethernet Port " + str(uplink_eth_port.get("port_id")))
        
                if traffic_mirroring_session.get("uplink_ethernet_port_channels"):
                    from intersight.model.fabric_span_source_eth_port_channel import FabricSpanSourceEthPortChannel

                    for uplink_eth_port_channel in traffic_mirroring_session["uplink_ethernet_port_channels"]:
                        source_eth_port_channel_kwargs = {
                            "object_type": "fabric.SpanSourceEthPortChannel",
                            "class_id": "fabric.SpanSourceEthPortChannel",
                            "span_session": fss
                        }

                        # list of attributes for ethernet port channels
                        attributes = ["direction", "id"]
                        for attr in attributes:
                            if uplink_eth_port_channel.get(attr) is not None:
                                source_eth_port_channel_kwargs[attr if attr!="id" else "pc_id"] = uplink_eth_port_channel.get(attr)

                        fabric_span_source_eth_port_channel = FabricSpanSourceEthPortChannel(**source_eth_port_channel_kwargs)

                        self.commit(
                            object_type="fabric.SpanSourceEthPortChannel", payload=fabric_span_source_eth_port_channel,
                            detail="Traffic Mirroring Session: " + traffic_mirroring_session["name"] + \
                                   " - Uplink Ethernet Port Channel " + str(uplink_eth_port_channel.get("id"))
                        )
                        
                if traffic_mirroring_session.get("vlans"):
                    from intersight.model.fabric_span_source_vlan import FabricSpanSourceVlan

                    for vlan in traffic_mirroring_session["vlans"]:
                        source_vlan_kwargs = {
                            "object_type": "fabric.SpanSourceVlan",
                            "class_id": "fabric.SpanSourceVlan",
                            "span_session": fss
                        }
                        # list of attributes for vlans
                        attributes = ["direction", "id"]
                        for attr in attributes:
                            if vlan.get(attr) is not None:
                                source_vlan_kwargs[attr if attr!="id" else "vlan_id"] = vlan.get(attr)

                        fabric_span_source_vlan = FabricSpanSourceVlan(**source_vlan_kwargs)

                        self.commit(
                            object_type="fabric.SpanSourceVlan", payload=fabric_span_source_vlan,
                            detail="Traffic Mirroring Session: " + traffic_mirroring_session["name"] + \
                                   " - VLAN " + str(vlan.get("id"))
                        )

                if traffic_mirroring_session.get("vnics"):
                    from intersight.model.fabric_span_source_vnic_eth_if import FabricSpanSourceVnicEthIf

                    for vnic in traffic_mirroring_session["vnics"]:
                        source_vnic_kwargs = {
                            "object_type": "fabric.SpanSourceVnicEthIf",
                            "class_id": "fabric.SpanSourceVnicEthIf",
                            "span_session": fss
                        }

                        if "direction" in vnic and vnic["direction"] is not None:
                            source_vnic_kwargs["direction"] = vnic["direction"]

                        if vnic.get("name") and vnic.get("server_profile") and vnic.get("org"):
                            org_name = vnic["org"]
                            server_profile_name = vnic["server_profile"]
                            vnic_name = vnic["name"]
                            org_object_list = self._device.query(
                                object_type="organization.Organization", 
                                filter=f"Name eq '{org_name}'"
                            )

                            if not org_object_list:
                                err_message = f"Could not find organization.Organization with name '{org_name}'"
                                self.logger(level="warning", message=err_message)
                                continue

                            org_moid = org_object_list[0].moid
                            profile_object_list = self._device.query(
                                object_type="server.Profile", 
                                filter=f"Name eq '{server_profile_name}' and Organization/Moid eq '{org_moid}'"
                            )

                            if not profile_object_list:
                                err_message = f"Could not find server.Profile with name '{server_profile_name}' to assign vNIC - {vnic_name}"
                                self.logger(level="warning", message=err_message)
                                continue

                            profile_moid = profile_object_list[0].moid
                            vnic_eth_if_list = self._device.query(
                                object_type="vnic.EthIf", 
                                filter=f"Name eq '{vnic_name}' and Profile/Moid eq '{profile_moid}'"
                            )

                            if not vnic_eth_if_list:
                                err_message = f"Could not find vnic.EthIf with name - {vnic_name} associated to Server Profile {server_profile_name}"
                                self.logger(level="error", message=err_message)
                                self._config.push_summary_manager.add_object_status(
                                    obj=self, 
                                    obj_detail=f"Fabric Interconnect '{self.name}-{self.switch_id}' with Traffic Mirroring Session '" +
                                               traffic_mirroring_session['name'] + "' - vNIC {vnic_name}",
                                    obj_type="fabric.SpanSourceVnicEthIf", 
                                    status="failed", 
                                    message=err_message
                                )
                                continue

                            # Validate association with Server Profile
                            if len(vnic_eth_if_list) != 1 or vnic_eth_if_list[0].profile.object_type != "server.Profile":
                                err_message = f"Could not find vnic.EthIf with name - {vnic_name} associated to a Server Profile"
                                self.logger(level="error", message=err_message)
                                continue

                            source_vnic_kwargs["vnic"] = self.create_relationship_equivalent(sdk_object=vnic_eth_if_list[0])

                            fabric_span_source_vnic = FabricSpanSourceVnicEthIf(**source_vnic_kwargs)
                            self.commit(
                                object_type="fabric.SpanSourceVnicEthIf", 
                                payload=fabric_span_source_vnic, 
                                detail=f"Traffic Mirroring Session: {traffic_mirroring_session['name']} - vNIC {vnic_name}"
                            )

        if self.serial and self.ports:
            from intersight.model.fabric_port_operation import FabricPortOperation
            from intersight.model.fabric_pc_operation import FabricPcOperation

            # Check if the domain exists before setting user labels on the ports:
            # - If the domain is present, proceed with setting user labels on the ports.
            # - If the domain is not found, log an error message.

            device_filter = (f"ConnectionStatus eq Connected and "
                             f"DeviceHostname in ('{self.name}')")
            registered_device = self._device.query(object_type="asset.DeviceRegistration", filter=device_filter)
            if not registered_device:
                self.logger(
                    level="error",
                    message=(
                        f"Cannot set user labels on the ports: Unable to fetch the target domain '{self.name}'. "
                        f"Please verify the domain and ensure it is correctly registered and connected."
                    )
                )
                return False

            for eth_port in self.ports.get("ethernet_ports", []):
                if eth_port.get("user_label"):
                    ethernet_port_kwargs = {
                        "object_type": "fabric.PortOperation",
                        "class_id": "fabric.PortOperation",
                        "admin_action": "SetUserLabel"
                    }

                    port_info = ""
                    if eth_port["slot_id"] is not None:
                        ethernet_port_kwargs["slot_id"] = eth_port["slot_id"]
                        port_info = f"{eth_port['slot_id']}"
                    if eth_port.get("aggr_id") not in [None, 0]:  # We have a breakout port
                        ethernet_port_kwargs["port_id"] = eth_port["aggr_id"]
                        ethernet_port_kwargs["aggregate_port_id"] = eth_port["port_id"]
                        port_info = f"{port_info}/{eth_port['aggr_id']}/{eth_port['port_id']}"
                    else:
                        ethernet_port_kwargs["port_id"] = eth_port["port_id"]
                        ethernet_port_kwargs["aggregate_port_id"] = 0
                        port_info = f"{port_info}/{eth_port['port_id']}"

                    ethernet_port_kwargs["user_label"] = eth_port["user_label"]

                    if network_element_list:
                        if len(network_element_list) != 1:
                            err_message = (
                                f"Could not find Fabric Interconnect '{self.name}-{self.switch_id}' "
                                f"to set User Label '{eth_port['user_label']}' "
                                f"on Ethernet Port {port_info}."
                            )
                            self.logger(level="error", message=err_message)
                            return False
                        else:
                            ethernet_port_kwargs["network_element"] = self.create_relationship_equivalent(
                                sdk_object=network_element_list[0])
                    else:
                        err_message = (
                            f"Could not find Fabric Interconnect '{self.name}-{self.switch_id}' "
                            f"to set User Label '{eth_port['user_label']}' "
                            f"on Ethernet Port {port_info}."
                        )
                        self.logger(level="error", message=err_message)
                        self._config.push_summary_manager.add_object_status(
                            obj=self,
                            obj_detail=f"Fabric Interconnect '{self.name}-{self.switch_id}' "
                                       f"with User Label '{eth_port['user_label']}' on Ethernet Port {port_info}",
                            obj_type="fabric.PortOperation",
                            status="failed",
                            message=err_message
                        )
                        return False

                    ethernet_port = FabricPortOperation(**ethernet_port_kwargs)

                    self.commit(object_type="fabric.PortOperation", payload=ethernet_port,
                                key_attributes=["network_element"],
                                detail=f"Ethernet Port {port_info} with User Label : "
                                       f"{eth_port['user_label']}",
                                modify_present=True)

            for fc_port in self.ports.get("fc_ports", []):
                if fc_port.get("user_label"):
                    fc_port_kwargs = {
                        "object_type": "fabric.PortOperation",
                        "class_id": "fabric.PortOperation",
                        "admin_action": "SetUserLabel"
                    }

                    port_info = ""
                    if fc_port["slot_id"] is not None:
                        fc_port_kwargs["slot_id"] = fc_port["slot_id"]
                        port_info = f"{fc_port['slot_id']}"
                    if fc_port.get("aggr_id") not in [None, 0]:  # We have a breakout port
                        fc_port_kwargs["port_id"] = fc_port["aggr_id"]
                        fc_port_kwargs["aggregate_port_id"] = fc_port["port_id"]
                        port_info = f"{port_info}/{fc_port['aggr_id']}/{fc_port['port_id']}"
                    else:
                        fc_port_kwargs["port_id"] = fc_port["port_id"]
                        fc_port_kwargs["aggregate_port_id"] = 0
                        port_info = f"{port_info}/{fc_port['port_id']}"

                    fc_port_kwargs["user_label"] = fc_port["user_label"]
                    if network_element_list:
                        if len(network_element_list) != 1:
                            err_message = (
                                f"Could not find Fabric Interconnect '{self.name}-{self.switch_id}' "
                                f"to set User Label '{fc_port['user_label']}' "
                                f"on FC Port {port_info}."
                            )
                            self.logger(level="error", message=err_message)
                            return False
                        else:
                            fc_port_kwargs["network_element"] = self.create_relationship_equivalent(
                                sdk_object=network_element_list[0])
                    else:
                        err_message = (
                            f"Could not find Fabric Interconnect '{self.name}-{self.switch_id}' "
                            f"to set User Label '{fc_port['user_label']}' "
                            f"on FC Port {port_info}."
                        )
                        self.logger(level="error", message=err_message)
                        self._config.push_summary_manager.add_object_status(
                            obj=self,
                            obj_detail=f"Fabric Interconnect '{self.name}-{self.switch_id}' "
                                       f"with User Label '{fc_port['user_label']}' on FC Port {port_info}",
                            obj_type="fabric.PortOperation",
                            status="failed",
                            message=err_message
                        )
                        return False

                    fc_port_op = FabricPortOperation(**fc_port_kwargs)

                    self.commit(object_type="fabric.PortOperation", payload=fc_port_op,
                                key_attributes=["network_element"],
                                detail=f"FC Port with User Label : {fc_port_op['user_label']}",
                                modify_present=True)

            for eth_port_channel in self.ports.get("ethernet_port_channels", []):
                if eth_port_channel.get("user_label"):
                    ethernet_port_channel_kwargs = {
                        "object_type": "fabric.PcOperation",
                        "class_id": "fabric.PcOperation",
                        "admin_action": "SetUserLabel"
                    }

                    if eth_port_channel["id"] is not None:
                        ethernet_port_channel_kwargs["pc_id"] = eth_port_channel["id"]
                    if eth_port_channel["user_label"] is not None:
                        ethernet_port_channel_kwargs["user_label"] = eth_port_channel["user_label"]
                    if network_element_list:
                        if len(network_element_list) != 1:
                            err_message = (
                                f"Could not find Fabric Interconnect '{self.name}-{self.switch_id}' "
                                f"to set User Label '{eth_port_channel['user_label']}' "
                                f"on Ethernet Port Channel {eth_port_channel['id']}."
                            )
                            self.logger(level="error", message=err_message)
                            return False
                        else:
                            ethernet_port_channel_kwargs["network_element"] = self.create_relationship_equivalent(
                                sdk_object=network_element_list[0])
                    else:
                        err_message = (
                            f"Could not find Fabric Interconnect '{self.name}-{self.switch_id}' "
                            f"to set User Label '{eth_port_channel['user_label']}' "
                            f"on Ethernet Port Channel {eth_port_channel['id']}."
                        )
                        self.logger(level="error", message=err_message)
                        self._config.push_summary_manager.add_object_status(
                            obj=self,
                            obj_detail=f"Fabric Interconnect '{self.name}-{self.switch_id}' "
                                       f"with User Label '{eth_port_channel['user_label']}' on "
                                       f"Ethernet Port Channel {eth_port_channel['id']}",
                            obj_type="fabric.PortOperation",
                            status="failed",
                            message=err_message
                        )
                        return False

                    ethernet_port_channel = FabricPcOperation(**ethernet_port_channel_kwargs)

                    self.commit(object_type="fabric.PcOperation",
                                key_attributes=["network_element"], payload=ethernet_port_channel,
                                detail=f"Ethernet Port Channel with User Label : {eth_port_channel['user_label']}",
                                modify_present=True)

            for fc_port_channel in self.ports.get("fc_port_channels", []):
                if fc_port_channel.get("user_label"):
                    fc_port_channel_kwargs = {
                        "object_type": "fabric.PcOperation",
                        "class_id": "fabric.PcOperation",
                        "admin_action": "SetUserLabel"
                    }

                    if fc_port_channel["id"] is not None:
                        fc_port_channel_kwargs["pc_id"] = fc_port_channel["id"]
                    if fc_port_channel["user_label"] is not None:
                        fc_port_channel_kwargs["user_label"] = fc_port_channel["user_label"]
                    if network_element_list:
                        if len(network_element_list) != 1:
                            err_message = (
                                f"Could not find Fabric Interconnect '{self.name}-{self.switch_id}' "
                                f"to set User Label '{fc_port_channel['user_label']}' "
                                f"on FC Port Channel {fc_port_channel['id']}."
                            )
                            self.logger(level="error", message=err_message)
                            return False
                        else:
                            fc_port_channel_kwargs["network_element"] = self.create_relationship_equivalent(
                                sdk_object=network_element_list[0])
                    else:
                        err_message = (
                            f"Could not find Fabric Interconnect '{self.name}-{self.switch_id}' "
                            f"to set User Label '{fc_port_channel['user_label']}' "
                            f"on FC Port Channel {fc_port_channel['id']}."
                        )
                        self.logger(level="error", message=err_message)
                        self._config.push_summary_manager.add_object_status(
                            obj=self,
                            obj_detail=f"Fabric Interconnect '{self.name}-{self.switch_id}' "
                                       f"with User Label '{fc_port_channel['user_label']}' on "
                                       f"FC Port Channel {fc_port_channel['id']}",
                            obj_type="fabric.PortOperation",
                            status="failed",
                            message=err_message
                        )
                        return False

                    fc_port_channel_op = FabricPcOperation(**fc_port_channel_kwargs)

                    self.commit(object_type="fabric.PcOperation",
                                key_attributes=["network_element"], payload=fc_port_channel_op,
                                detail=f"FC Port Channel with User Label : {fc_port_channel['user_label']}",
                                modify_present=True)

        return True


class IntersightChassis(IntersightConfigObject):
    _CONFIG_NAME = "Chassis"
    _CONFIG_SECTION_NAME = "chassis"
    _INTERSIGHT_SDK_OBJECT_NAME = "equipment.Chassis"

    def __init__(self, parent=None, equipment_chassis=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=equipment_chassis)

        self.name = self.get_attribute(attribute_name="name")
        self.id = self.get_attribute(attribute_name="chassis_id", attribute_secondary_name="id")
        self.serial = self.get_attribute(attribute_name="serial")
        self.user_label = self.get_attribute(attribute_name="user_label")
        self.blades = None

        if self._config.load_from == "live":
            self.blades = self._get_blades()

        elif self._config.load_from == "file":
            for attribute in ["blades"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))
            self.clean_object()

    def clean_object(self):
        # We use this to make sure all options of blades are set to None if they are not present
        if self.blades:
            for blade in self.blades:
                for attribute in ["asset_tag", "name", "serial", "slot_id", "tags", "user_label"]:
                    if attribute not in blade:
                        blade[attribute] = None

    def _get_blades(self):
        # Get the list of Blades
        blades = []
        if "compute_blade" in self._config.sdk_objects:
            for compute_blade in self._config.sdk_objects["compute_blade"]:
                if compute_blade.equipment_chassis.moid == self._moid:
                    blade = {}
                    blade.update({
                        "name": compute_blade.name,
                        "serial": compute_blade.serial,
                        "slot_id": compute_blade.slot_id
                    })
                    if getattr(compute_blade, "tags"):
                        blade["tags"] = []
                        for tag in compute_blade.tags:
                            if not tag.get("key", "").endswith("LicenseTier"):  # Ignoring system defined tags
                                blade["tags"].append({"key": tag["key"], "value": tag["value"]})
                    for compute_server_setting in self._config.sdk_objects["compute_server_setting"]:
                        if compute_server_setting.server.moid == compute_blade.moid:
                                blade.update({"asset_tag": compute_server_setting.server_config.asset_tag 
                                              if compute_server_setting.server_config.asset_tag else None, 
                                              "user_label": compute_server_setting.server_config.user_label
                                              if compute_server_setting.server_config.user_label else None})
                                break
                    blades.append(blade)

            return blades
        return None

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")
        if self.serial:
            filter_key, filter_value = "Serial", self.serial
        elif self.id and self._parent.name:
            filter_key, filter_value = "Name", self._parent.name + "-" + str(self.id)
        elif self.name:
            filter_key, filter_value = "Name", self.name
        filter_str = f"{filter_key} eq '{filter_value}'"
        equipment_chassis_list = self._device.query(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, filter=filter_str)
        if len(equipment_chassis_list) != 1:
            err_message = "Could not find Chassis '" + self.name + "'"
            self.logger(level="error", message=err_message)
            return False
        elif len(equipment_chassis_list) == 1 and (self.tags or self.user_label):
            from intersight.model.equipment_chassis import EquipmentChassis
            kwargs = {
                "object_type": "equipment.Chassis",
                "class_id": "equipment.Chassis"
            }
            if self.tags is not None:
                kwargs["tags"] = self.create_tags()
            if self.user_label is not None:
                kwargs["user_label"] = self.user_label
            kwargs["moid"] = equipment_chassis_list[0].moid
            chassis = EquipmentChassis(**kwargs)
            self.commit(
                object_type=self._INTERSIGHT_SDK_OBJECT_NAME,
                key_attributes=["moid"], payload=chassis, detail=self.name + ' - Tags or User Label',
                modify_present=True
            )

        if self.blades:
            from intersight.model.compute_blade import ComputeBlade
            for blade in self.blades:
                self.logger(message=f"Pushing Blade Configuration: " + blade["name"])
                if blade.get("serial"):
                    filter_key, filter_value = "Serial", blade.get("serial")
                elif self.id and self._parent.name and blade.get('slot_id'):
                    filter_key, filter_value = "Name", self._parent.name + "-" + str(self.id) + "-" + str(
                        blade.get('slot_id'))
                elif self.name:
                    filter_key, filter_value = "Name", self.name
                filter_str = f"{filter_key} eq '{filter_value}'"
                compute_blade_list = self._device.query(object_type="compute.Blade", filter=filter_str)
                if len(compute_blade_list) != 1:
                    err_message = "Could not find Blade '" + blade["name"] + "'"
                    self.logger(level="error", message=err_message)
                    return False
                elif len(compute_blade_list) == 1 and (blade.get("tags") or blade.get("user_label")):
                    compute_blade_kwargs = {
                        "object_type": "compute.Blade",
                        "class_id": "compute.Blade"
                    }
                    if blade.get("tags", []) is not None:
                        # Ensuring the blade server's LicenseTier tag is retained while adding other tags
                        with_license_tier_tag = [{"key": blade_tag.get("key"), "value": blade_tag.get("value")} \
                            for blade_tag in compute_blade_list[0].tags if blade_tag.get("key", "") == "Intersight.LicenseTier"]
                        with_license_tier_tag.extend(blade.get("tags"))
                        compute_blade_kwargs["tags"] = with_license_tier_tag
                        compute_blade_kwargs["moid"] = compute_blade_list[0].moid

                        compute_blade = ComputeBlade(**compute_blade_kwargs)
                        self.commit(
                            object_type="compute.Blade", key_attributes=["moid"], payload=compute_blade,
                            detail="Blade - " + blade["name"] + ' - Tags', modify_present=True
                        )
                    if blade.get("user_label") or blade.get("asset_tag"):
                        from intersight.model.compute_server_setting import ComputeServerSetting

                        compute_server_config_kwargs = {
                            "object_type": "compute.ServerConfig",
                            "class_id": "compute.ServerConfig"
                        }
                        if blade.get("user_label") is not None:
                            compute_server_config_kwargs["user_label"] = blade.get("user_label")
                        if blade.get("asset_tag") is not None:
                            compute_server_config_kwargs["asset_tag"] = blade.get("asset_tag")
                        compute_server_setting_list = self._device.query(object_type="compute.ServerSetting", filter=f"Server.Moid eq '{compute_blade_list[0].moid}'")
                        if len(compute_server_setting_list) == 1:
                            compute_server_setting_kwargs = {
                                "object_type": "compute.ServerSetting",
                                "class_id": "compute.ServerSetting"
                            }
                            compute_server_setting_kwargs["server_config"] = compute_server_config_kwargs
                            compute_server_setting_kwargs["moid"] = compute_server_setting_list[0].moid
                            compute_server_setting = ComputeServerSetting(**compute_server_setting_kwargs)
                            self.commit(
                                object_type="compute.ServerSetting", key_attributes=["moid"], payload=compute_server_setting,
                                detail="Blade - " + blade["name"] + ' - Asset Tag or User Label', modify_present=True
                            )

        return True


class IntersightComputeRackUnit(IntersightConfigObject):
    _CONFIG_NAME = "Rack Unit"
    _CONFIG_SECTION_NAME = "rack_units"
    _INTERSIGHT_SDK_OBJECT_NAME = "compute.RackUnit"

    def __init__(self, parent=None, compute_rack_unit=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=compute_rack_unit)

        self.id = self.get_attribute(attribute_name="server_id", attribute_secondary_name="id")
        self.name = self.get_attribute(attribute_name="name")
        self.serial = self.get_attribute(attribute_name="serial")
        self.asset_tag = None
        self.user_label = None

        if self._config.load_from == "live":
            if self._parent.__class__.__name__ not in ["IntersightImmDomain", "IntersightUcsmDomain"]:
                # We use the server name as the ID for Intersight Standalone Mode
                self.id = self.name

            for compute_server_setting in self._config.sdk_objects["compute_server_setting"]:
                if compute_server_setting.server.moid == self._moid:
                    self.asset_tag = compute_server_setting.server_config.asset_tag \
                          if compute_server_setting.server_config.asset_tag else None 
                    self.user_label = compute_server_setting.server_config.user_label \
                          if compute_server_setting.server_config.user_label else None

        elif self._config.load_from == "file":
            for attribute in ["asset_tag", "user_label"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")
        if self.serial:
            filter_key, filter_value = "Serial", self.serial
        elif self.id and self._parent.name:
            filter_key, filter_value = "Name", self._parent.name + "-" + str(self.id)
        elif self.name:
            filter_key, filter_value = "Name", self.name
        filter_str = f"{filter_key} eq '{filter_value}'"
        compute_rack_unit_list = self._device.query(object_type="compute.RackUnit", filter=filter_str)
        if len(compute_rack_unit_list) != 1:
            err_message = "Could not find Rack '" + self.name + "'"
            self.logger(level="error", message=err_message)
            return False
        elif len(compute_rack_unit_list) == 1 and (self.tags or self.user_label):
            from intersight.model.compute_rack_unit import ComputeRackUnit
            compute_rack_unit_kwargs = {
                "object_type": "compute.RackUnit",
                "class_id": "compute.RackUnit"
            }
            if self.tags is not None:
                # Ensuring the rack server's LicenseTier tag is retained while adding other tags
                with_license_tier_tag = [{"key": rack_tag.get("key"), "value": rack_tag.get("value")} \
                    for rack_tag in compute_rack_unit_list[0].tags if rack_tag.get("key", "") == "Intersight.LicenseTier"]
                with_license_tier_tag.extend(self.tags)
                compute_rack_unit_kwargs["tags"] = with_license_tier_tag
                compute_rack_unit_kwargs["moid"] = compute_rack_unit_list[0].moid

                compute_rack_unit = ComputeRackUnit(**compute_rack_unit_kwargs)
                self.commit(
                    object_type=self._INTERSIGHT_SDK_OBJECT_NAME,
                    key_attributes=["moid"], payload=compute_rack_unit, detail=self.name + ' - Tags',
                    modify_present=True)
            
            if self.user_label or self.asset_tag:
                from intersight.model.compute_server_setting import ComputeServerSetting

                compute_server_config_kwargs = {
                    "object_type": "compute.ServerConfig",
                    "class_id": "compute.ServerConfig"
                }
                if self.user_label is not None:
                    compute_server_config_kwargs["user_label"] = self.user_label
                if self.asset_tag is not None:
                    compute_server_config_kwargs["asset_tag"] = self.asset_tag

                compute_server_setting_list = self._device.query(object_type="compute.ServerSetting", filter=f"Server.Moid eq '{compute_rack_unit_list[0].moid}'")
                if len(compute_server_setting_list) == 1:
                    compute_server_setting_kwargs = {
                        "object_type": "compute.ServerSetting",
                        "class_id": "compute.ServerSetting"
                    }
                    compute_server_setting_kwargs["server_config"] = compute_server_config_kwargs
                    compute_server_setting_kwargs["moid"] = compute_server_setting_list[0].moid
                    compute_server_setting = ComputeServerSetting(**compute_server_setting_kwargs)
                    self.commit(
                        object_type="compute.ServerSetting", key_attributes=["moid"], payload=compute_server_setting,
                        detail=self.name + ' - Asset Tag or User Label', modify_present=True
                    )

        return True


class IntersightFex(IntersightConfigObject):
    _CONFIG_NAME = "Fabric Extender"
    _CONFIG_SECTION_NAME = "fabric_extenders"
    _INTERSIGHT_SDK_OBJECT_NAME = "equipment.Fex"

    def __init__(self, parent=None, equipment_fex=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=equipment_fex)

        self.id = self.get_attribute(attribute_name="module_id", attribute_secondary_name="id")
        self.name = self.get_attribute(attribute_name="description", attribute_secondary_name="name")
        self.serial = self.get_attribute(attribute_name="serial")
        self.switch_id = self.get_attribute(attribute_name="connection_path", attribute_secondary_name="switch_id")

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration:")
        filter_str = None
        if self.serial:
            filter_str = f"Serial eq '{self.serial}'"
        elif self.id and self._parent.name and self.switch_id:
            filter_str = f"ConnectionPath eq '{self.switch_id}' and ModuleId eq {self.id}"
        equipment_fex_list = self._device.query(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, filter=filter_str)
        if equipment_fex_list:
            asset_device_registration_list = self._device.query(
                object_type="asset.DeviceRegistration",
                filter=f"Moid eq '{equipment_fex_list[0].registered_device.moid}'"
            )
            if len(asset_device_registration_list) != 1:
                    self.logger(level="debug",
                                message="Could not find the appropriate asset.DeviceRegistration " +
                                        "for Fabric Extender '" + self.serial + "'")
                    return False
            else:
                device_hostname = asset_device_registration_list[0].device_hostname
                if self._parent.name not in device_hostname:
                    equipment_fex_list = []
        if len(equipment_fex_list) != 1:
            err_message = "Could not find Fabric Extender '" + self.serial + "'"
            self.logger(level="error", message=err_message)
            return False
        elif len(equipment_fex_list) == 1 and self.tags :
            from intersight.model.equipment_fex import EquipmentFex
            equipment_fex_kwargs = {
                "object_type": "equipment.Fex",
                "class_id": "equipment.Fex"
            }
            if self.tags is not None:
                equipment_fex_kwargs["tags"] = self.create_tags()
            equipment_fex_kwargs["moid"] = equipment_fex_list[0].moid
            equipment_fex = EquipmentFex(**equipment_fex_kwargs)
            self.commit(
                object_type=self._INTERSIGHT_SDK_OBJECT_NAME, key_attributes=["moid"], payload=equipment_fex,
                detail=self.serial + ' - Tags', modify_present=True
            )

        return True
