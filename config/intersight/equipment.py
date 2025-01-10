
# coding: utf-8
# !/usr/bin/env python

""" equipment.py: Easy UCS Deployment Tool """

from config.intersight.object import IntersightConfigObject

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

        if self._config.load_from == "live":
            self._get_device_host_name()
            self.traffic_mirroring_sessions = self._get_traffic_mirroring_sessions()

        elif self._config.load_from == "file":
            for attribute in ["name", "traffic_mirroring_sessions"]:
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
                            span_session.update({"uplink_ethernet_ports": self._get_ethernet_ports(fabric_span_session)})

                    if hasattr(fabric_span_session, "source_port_channels"):
                        if fabric_span_session.source_port_channels:
                            span_session.update({"uplink_ethernet_port_channels": self._get_ethernet_port_channels(fabric_span_session)})

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
                                        vnic.update({
                                            "server_profile": server_profile.name
                                        })
                                        for organization in self._config.sdk_objects["organization_organization"]:
                                            if server_profile.organization.moid == organization.moid:
                                                vnic.update({
                                                    "org": organization.name
                                                })
                        source_vnics.append(vnic)

            return source_vnics
        return None

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.fabric_span_session import FabricSpanSession
        
        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}-{self.switch_id}")

        network_element_list = self._device.query(object_type="network.Element", filter="Serial eq '%s'" % self.serial)
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
            info_message = f"The domain '{self.name}' must be claimed first in order to include the traffic mirroring sessions."
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
                        span_session_kwargs["network_element"] = self.create_relationship_equivalent(sdk_object=network_element_list[0])
                else:
                    err_message = "Could not find Fabric Interconnect '" + self.name + '-' + self.switch_id + \
                                  "' to assign Traffic Mirroring Session '" + traffic_mirroring_session["name"] + "'"
                    self.logger(level="error", message=err_message)
                    self._config.push_summary_manager.add_object_status(
                            obj=self, obj_detail=f"Fabric Interconnect '{self.name}-{self.switch_id}' with Traffic Mirroring Session '" + \
                            traffic_mirroring_session["name"] + "'", obj_type="fabric.SpanSession", status="failed", message=err_message
                        )
                    return False
                    
                fabric_span_session = FabricSpanSession(**span_session_kwargs)
                fss = self.commit(object_type="fabric.SpanSession", key_attributes=["name", "network_element"], payload=fabric_span_session,
                        detail="Traffic Mirroring Session: " + traffic_mirroring_session["name"], return_relationship=True)
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

                    self.commit(object_type="fabric.SpanDestEthPort", payload=fabric_span_dest_eth_port,
                                detail="Traffic Mirroring Session: " + traffic_mirroring_session["name"] + \
                                " - Destination Port " + str(traffic_mirroring_session["destination_port"].get("port_id", None)))

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

                        self.commit(object_type="fabric.SpanSourceEthPortChannel", payload=fabric_span_source_eth_port_channel,
                                           detail="Traffic Mirroring Session: " + traffic_mirroring_session["name"] + \
                                           " - Uplink Ethernet Port Channel " + str(uplink_eth_port_channel.get("id")))
                        
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

                        self.commit(object_type="fabric.SpanSourceVlan", payload=fabric_span_source_vlan,
                                           detail="Traffic Mirroring Session: " + traffic_mirroring_session["name"] + \
                                                  " - VLAN " + str(vlan.get("id")))

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

        return True

