# coding: utf-8
# !/usr/bin/env python

""" fabric.py: Easy UCS Deployment Tool """

from inventory.generic.fabric import GenericFex, GenericFi
from inventory.intersight.object import IntersightInventoryObject
from inventory.intersight.port import IntersightFexFabricPort, IntersightFiEthPort, IntersightFiFcPort, \
    IntersightFexHostPort
from inventory.intersight.psu import IntersightPsu


class IntersightFex(GenericFex, IntersightInventoryObject):
    def __init__(self, parent=None, equipment_fex=None):
        GenericFex.__init__(self, parent=parent)
        IntersightInventoryObject.__init__(self, parent=parent, sdk_object=equipment_fex)

        self.id = self.get_attribute(attribute_name="module_id", attribute_secondary_name="id")
        self.model = self.get_attribute(attribute_name="model")
        self.name = self.get_attribute(attribute_name="description", attribute_secondary_name="name")
        self.part_number = self.get_attribute(attribute_name="part_number")
        self.revision = self.get_attribute(attribute_name="revision")
        self.serial = self.get_attribute(attribute_name="serial")
        self.switch_id = self.get_attribute(attribute_name="connection_path", attribute_secondary_name="switch_id")
        self.vendor = self.get_attribute(attribute_name="vendor")

        self.firmware_version = None
        self.fabric_ports = self._get_fabric_ports()
        self.host_ports = self._get_host_ports()
        self.power_supplies = self._get_power_supplies()

        if self._inventory.load_from == "live":
            self.locator_led_status = self._determine_locator_led_status()
            self.sku = self.model
            self.short_name = self._get_model_short_name()

            # Manual fix for invalid description
            if self.name == "Unknown Module":
                self.name = None

            if self._parent.__class__.__name__ in ["IntersightUcsmDomain", "IntersightImmDomain"]:
                # FEXs do not have a firmware package version info in Intersight.
                # Using the parent FI's package version instead
                if not self.firmware_version:
                    if hasattr(self._parent, "fabric_interconnects"):
                        for fi in self._parent.fabric_interconnects:
                            if fi.id == self.switch_id:
                                if hasattr(fi, "firmware_version"):
                                    self.firmware_version = fi.firmware_version

        elif self._inventory.load_from == "file":
            for attribute in ["firmware_version", "locator_led_status", "short_name", "sku"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

    def _get_fabric_ports(self):
        if self._inventory.load_from == "live":
            return self.get_inventory_objects_from_ref(ref=self._object.network_ports,
                                                       object_class=IntersightFexFabricPort, parent=self)
        elif self._inventory.load_from == "file" and "fabric_ports" in self._object:
            return [IntersightFexFabricPort(self, port) for port in self._object["fabric_ports"]]
        else:
            return []

    def _get_host_ports(self):
        if self._inventory.load_from == "live":
            return self.get_inventory_objects_from_ref(ref=self._object.host_ports,
                                                       object_class=IntersightFexHostPort, parent=self)
        elif self._inventory.load_from == "file" and "host_ports" in self._object:
            return [IntersightFexHostPort(self, port) for port in self._object["host_ports"]]
        else:
            return []

    def _get_power_supplies(self):
        if self._inventory.load_from == "live":
            return self.get_inventory_objects_from_ref(ref=self._object.psus, object_class=IntersightPsu, parent=self)
        elif self._inventory.load_from == "file" and "power_supplies" in self._object:
            return [IntersightPsu(self, psu) for psu in self._object["power_supplies"]]
        else:
            return []


class IntersightFi(GenericFi, IntersightInventoryObject):
    def __init__(self, parent=None, network_element=None):
        GenericFi.__init__(self, parent=parent)
        IntersightInventoryObject.__init__(self, parent=parent, sdk_object=network_element)

        self.id = self.get_attribute(attribute_name="switch_id", attribute_secondary_name="id")
        self.ip_address = self.get_attribute(attribute_name="out_of_band_ip_address",
                                             attribute_secondary_name="ip_address")
        self.ip_gateway = self.get_attribute(attribute_name="out_of_band_ip_gateway",
                                             attribute_secondary_name="ip_gateway")
        self.ip_netmask = self.get_attribute(attribute_name="out_of_band_ip_mask",
                                             attribute_secondary_name="ip_netmask")
        self.mac_address = self.get_attribute(attribute_name="out_of_band_mac", attribute_secondary_name="mac_address")
        self.model = self.get_attribute(attribute_name="model")
        self.revision = self.get_attribute(attribute_name="revision")
        self.serial = self.get_attribute(attribute_name="serial")
        self.vendor = self.get_attribute(attribute_name="vendor")

        self.expansion_modules = []
        self.firmware_version = None
        self.ports = self._get_ports()
        self.power_supplies = self._get_power_supplies()

        if self._inventory.load_from == "live":
            self.locator_led_status = self._determine_locator_led_status()
            self.sku = self.model
            self.short_name = self._get_model_short_name()
            self.name = self._get_name()

            if self._parent.__class__.__name__ == "IntersightImmDomain":
                # We need to find the "management.Controller" object that belongs to this FI to inventory subcomponents
                management_controller = self.get_inventory_objects_from_ref(ref=self._object.management_controller)
                if len(management_controller) == 1:
                    self.firmware_version = self._determine_firmware_version(
                        source_obj=management_controller[0], filter_attr="dn", filter_value="-system")
                else:
                    self.logger(level="debug",
                                message="Unable to find unique management.Controller object for FI with ID " +
                                        str(self.id))
            elif self._parent.__class__.__name__ == "IntersightUcsmDomain":
                self.firmware_version = self._determine_firmware_version()

        elif self._inventory.load_from == "file":
            for attribute in ["firmware_version", "locator_led_status", "name", "short_name", "sku"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

    def _get_ports(self):
        if self._inventory.load_from == "live":
            port_list = []
            for equipment_switch_card in self.get_inventory_objects_from_ref(ref=self._object.cards):
                # We inventory all physical ports (Eth and FC)
                for port_group in self.get_inventory_objects_from_ref(ref=equipment_switch_card.port_groups):
                    port_list.extend(self.get_inventory_objects_from_ref(
                        ref=port_group.ethernet_ports, object_class=IntersightFiEthPort, parent=self))
                    port_list.extend(self.get_inventory_objects_from_ref(
                        ref=port_group.fc_ports, object_class=IntersightFiFcPort, parent=self))
                    # We also inventory all breakout ports (Eth and FC)
                    for port_sub_group in self.get_inventory_objects_from_ref(ref=port_group.sub_groups):
                        port_list.extend(self.get_inventory_objects_from_ref(
                            ref=port_sub_group.ethernet_ports, object_class=IntersightFiEthPort, parent=self))
                        port_list.extend(self.get_inventory_objects_from_ref(
                            ref=port_sub_group.fc_ports, object_class=IntersightFiFcPort, parent=self))
            if port_list:
                # Sort ports by port_id for easier readability
                port_list = sorted(port_list,
                                   key=lambda x: (x.aggr_port_id, x.port_id) if x.aggr_port_id is not None else (
                                   x.port_id, 0) if x.port_id is not None else (0, 0))
            return port_list
        elif self._inventory.load_from == "file" and "ports" in self._object:
            return ([IntersightFiEthPort(self, port) for port in self._object["ports"] if
                    port.get("transport") == "ether"] +
                    [IntersightFiFcPort(self, port) for port in self._object["ports"] if
                     port.get("transport") == "fc"])

    def _get_power_supplies(self):
        if self._inventory.load_from == "live":
            return self.get_inventory_objects_from_ref(ref=self._object.psus, object_class=IntersightPsu, parent=self)
        elif self._inventory.load_from == "file" and "power_supplies" in self._object:
            return [IntersightPsu(self, psu) for psu in self._object["power_supplies"]]
        else:
            return []
