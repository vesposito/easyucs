# coding: utf-8
# !/usr/bin/env python

""" chassis.py: Easy UCS Deployment Tool """

from inventory.generic.chassis import GenericChassis, GenericIom, GenericXfm
from inventory.intersight.blade import IntersightComputeBlade
from inventory.intersight.fabric import IntersightFi
from inventory.intersight.object import IntersightInventoryObject
from inventory.intersight.pcie_node import IntersightPcieNode
from inventory.intersight.port import IntersightIomPort
from inventory.intersight.psu import IntersightPsu


class IntersightChassis(GenericChassis, IntersightInventoryObject):
    def __init__(self, parent=None, equipment_chassis=None):
        GenericChassis.__init__(self, parent=parent)
        IntersightInventoryObject.__init__(self, parent=parent, sdk_object=equipment_chassis)

        self.id = self.get_attribute(attribute_name="chassis_id", attribute_secondary_name="id")
        self.model = self.get_attribute(attribute_name="model")
        self.name = self.get_attribute(attribute_name="product_name", attribute_secondary_name="name")
        self.part_number = self.get_attribute(attribute_name="part_number")
        self.revision = self.get_attribute(attribute_name="revision")
        self.serial = self.get_attribute(attribute_name="serial")
        self.user_label = self.get_attribute(attribute_name="user_label")
        self.vendor = self.get_attribute(attribute_name="vendor")
        self.vid = self.get_attribute(attribute_name="vid")

        self.blades = self._get_blades()
        self.fabric_interconnects = []
        self.io_modules = self._get_io_modules()
        self.pcie_nodes = []
        self.power_supplies = self._get_power_supplies()
        self.x_fabric_modules = self._get_x_fabric_modules()

        if self._inventory.load_from == "live":
            self.locator_led_status = self._determine_locator_led_status()
            self.sku = self.model

            # Manually fixing old UCS X-Series chassis SKU
            if self.sku in ["UCSBX-9508"]:
                self.sku = "UCSX-9508"

            # Manually fixing UCS C3X60 chassis SKU
            if self.sku == "UCSC-C3X60-BASE":
                self.sku = "UCSC-C3X60"

            # We need to find the "compute.Blade" objects that belong to this chassis to inventory PCIe nodes
            compute_blades = self.get_inventory_objects_from_ref(ref=self._object.blades)
            for compute_blade in compute_blades:
                self.pcie_nodes.extend(self.get_inventory_objects_from_ref(
                    ref=compute_blade.pci_nodes, object_class=IntersightPcieNode, parent=self))

            # We need to find the "equipment.IoCard" objects that belong to this chassis to inventory FI-IOM/IFMs
            equipment_io_cards = self.get_inventory_objects_from_ref(ref=self._object.ioms)
            embedded_fi_sn = []
            for equipment_io_card in equipment_io_cards:
                if equipment_io_card.model in ["UCS-FI-M-6324", "UCSX-S9108-100G"]:
                    embedded_fi_sn.append(equipment_io_card.serial)

            if embedded_fi_sn:
                embedded_fi_list = [fi for fi in self._inventory.sdk_objects.get("network_element", []) if
                                    fi.serial in embedded_fi_sn]
                for embedded_fi in embedded_fi_list:
                    self.fabric_interconnects.append(IntersightFi(parent=self, network_element=embedded_fi))

            # We sort the list of FIs to return objects in an appropriate order
            self.fabric_interconnects = sorted(self.fabric_interconnects,
                                               key=lambda x: x.id if getattr(x, "id", None) else 0)

            self.short_name = self._get_model_short_name()
            self.slots_max = self._get_chassis_slots_max()
            self.slots_populated = self._calculate_chassis_slots_populated()
            self.slots_free_half = self._calculate_chassis_slots_free_half()
            self.slots_free_full = self._calculate_chassis_slots_free_full()

        elif self._inventory.load_from == "file":
            if "fabric_interconnects" in self._object:
                for fabric_interconnect in self._object["fabric_interconnects"]:
                    self.fabric_interconnects.append(IntersightFi(parent=self, network_element=fabric_interconnect))
            if "pcie_nodes" in self._object:
                for pcie_node in self._object["pcie_nodes"]:
                    self.pcie_nodes.append(IntersightPcieNode(parent=self, pci_node=pcie_node))
            for attribute in ["locator_led_status", "short_name", "sku", "slots_free_half", "slots_free_full",
                              "slots_max", "slots_populated"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

    def _get_blades(self):
        if self._inventory.load_from == "live":
            return self.get_inventory_objects_from_ref(ref=self._object.blades, object_class=IntersightComputeBlade,
                                                       parent=self)
        elif self._inventory.load_from == "file" and "blades" in self._object:
            return [IntersightComputeBlade(self, blade) for blade in self._object["blades"]]
        else:
            return []

    def _get_io_modules(self):
        if self._inventory.load_from == "live":
            return self.get_inventory_objects_from_ref(ref=self._object.ioms, object_class=IntersightIom, parent=self)
        elif self._inventory.load_from == "file" and "io_modules" in self._object:
            return [IntersightIom(self, iom) for iom in self._object["io_modules"]]
        else:
            return []

    def _get_power_supplies(self):
        if self._inventory.load_from == "live":
            return self.get_inventory_objects_from_ref(ref=self._object.psus, object_class=IntersightPsu, parent=self)
        elif self._inventory.load_from == "file" and "power_supplies" in self._object:
            return [IntersightPsu(self, psu) for psu in self._object["power_supplies"]]
        else:
            return []

    def _get_x_fabric_modules(self):
        if self._inventory.load_from == "live":
            return self.get_inventory_objects_from_ref(ref=self._object.expander_modules, object_class=IntersightXfm,
                                                       parent=self)
        elif self._inventory.load_from == "file" and "x_fabric_modules" in self._object:
            return [IntersightXfm(self, xfm) for xfm in self._object["x_fabric_modules"]]
        else:
            return []


class IntersightIom(GenericIom, IntersightInventoryObject):
    def __init__(self, parent=None, equipment_io_card=None):
        GenericIom.__init__(self, parent=parent)
        IntersightInventoryObject.__init__(self, parent=parent, sdk_object=equipment_io_card)

        self.firmware_version = self.get_attribute(attribute_name="version",
                                                   attribute_secondary_name="firmware_version")
        self.id = self.get_attribute(attribute_name="module_id", attribute_secondary_name="id")
        self.model = self.get_attribute(attribute_name="model")
        self.name = self.get_attribute(attribute_name="product_name", attribute_secondary_name="name")
        self.part_number = self.get_attribute(attribute_name="part_number")
        self.revision = self.get_attribute(attribute_name="revision")
        self.serial = self.get_attribute(attribute_name="serial")
        self.switch_id = self.get_attribute(attribute_name="connection_path", attribute_secondary_name="switch_id")
        self.vendor = self.get_attribute(attribute_name="vendor")
        self.vid = self.get_attribute(attribute_name="vid")

        self.ports = self._get_ports()

        if self._inventory.load_from == "live":
            self.sku = self.model

            self.short_name = self._get_model_short_name()

        elif self._inventory.load_from == "file":
            for attribute in ["short_name", "sku"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

    def _get_ports(self):
        if self._inventory.load_from == "live":
            return self.get_inventory_objects_from_ref(ref=self._object.network_ports, object_class=IntersightIomPort, parent=self)
        elif self._inventory.load_from == "file" and "ports" in self._object:
            return [IntersightIomPort(self, port) for port in self._object["ports"]]
        else:
            return []


class IntersightXfm(GenericXfm, IntersightInventoryObject):
    def __init__(self, parent=None, equipment_expander_module=None):
        GenericXfm.__init__(self, parent=parent)
        IntersightInventoryObject.__init__(self, parent=parent, sdk_object=equipment_expander_module)

        self.id = self.get_attribute(attribute_name="module_id", attribute_secondary_name="id")
        self.model = self.get_attribute(attribute_name="model")
        self.part_number = self.get_attribute(attribute_name="part_number")
        self.revision = self.get_attribute(attribute_name="revision")
        self.serial = self.get_attribute(attribute_name="serial")
        self.vendor = self.get_attribute(attribute_name="vendor")

        if self._inventory.load_from == "live":
            self.sku = self.model

            self.short_name = self._get_model_short_name()

        elif self._inventory.load_from == "file":
            for attribute in ["short_name", "sku"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))
