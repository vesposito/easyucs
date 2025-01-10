# coding: utf-8
# !/usr/bin/env python

""" adaptor.py: Easy UCS Deployment Tool """
from inventory.generic.adaptor import GenericAdaptor
from inventory.intersight.object import IntersightInventoryObject
from inventory.intersight.port import IntersightAdaptorPort


class IntersightAdaptor(GenericAdaptor, IntersightInventoryObject):
    def __init__(self, parent=None, processor_unit=None):
        GenericAdaptor.__init__(self, parent=parent)
        IntersightInventoryObject.__init__(self, parent=parent, sdk_object=processor_unit)

        self.id = self.get_attribute(attribute_name="adapter_id", attribute_secondary_name="id")
        self.model = self.get_attribute(attribute_name="model")
        self.part_number = self.get_attribute(attribute_name="part_number")
        self.pci_slot = self.get_attribute(attribute_name="pci_slot")
        self.revision = self.get_attribute(attribute_name="revision")
        self.serial = self.get_attribute(attribute_name="serial")
        self.vendor = self.get_attribute(attribute_name="vendor")
        self.vid = self.get_attribute(attribute_name="vid")

        self.ports = self._get_ports()

        if self._inventory.load_from == "live":
            self.sku = self.model
            self.short_name = self._get_model_short_name()

            self._determine_adaptor_sku_and_type()

            self.adaptor_expanders = self._get_adaptor_expanders()

            # Sometimes ports are numbered from 0, sometimes from 1. Standardizing starting from 1
            if self.ports:
                if self.ports[0].port_id == "0":
                    for port in self.ports:
                        port.port_id = str(int(port.port_id) + 1)

            # We need to find the "management.Controller" object that belongs to this adapter to inventory subcomponents
            management_controller = self.get_inventory_objects_from_ref(ref=self._object.controller)
            if len(management_controller) == 1:
                self.firmware_version = self._determine_firmware_version(
                    source_obj=management_controller[0], filter_attr="dn", filter_value="-system")
            else:
                self.logger(level="debug",
                            message="Unable to find unique management.Controller object for adapter with ID " +
                                    str(self.id))

        elif self._inventory.load_from == "file":
            for attribute in ["firmware_version", "short_name", "sku"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

    def _get_adaptor_expanders(self):
        if self._inventory.load_from == "live":
            return self.get_inventory_objects_from_ref(ref=self._object.adapter_unit_expander,
                                                       object_class=IntersightAdaptorExpander, parent=self)

    def _get_ports(self):
        if self._inventory.load_from == "live":
            return self.get_inventory_objects_from_ref(ref=self._object.ext_eth_ifs,
                                                       object_class=IntersightAdaptorPort, parent=self)
        elif self._inventory.load_from == "file" and "ports" in self._object:
            return [IntersightAdaptorPort(self, port) for port in self._object["ports"]]
        else:
            return []


class IntersightAdaptorExpander(GenericAdaptor, IntersightInventoryObject):
    def __init__(self, parent=None, processor_unit=None):
        GenericAdaptor.__init__(self, parent=parent)
        IntersightInventoryObject.__init__(self, parent=parent, sdk_object=processor_unit)

        self.model = self.get_attribute(attribute_name="model")
        self.part_number = self.get_attribute(attribute_name="part_number")
        self.revision = self.get_attribute(attribute_name="revision")
        self.serial = self.get_attribute(attribute_name="serial")
        self.vendor = self.get_attribute(attribute_name="vendor")
        self.vid = self.get_attribute(attribute_name="vid")

        if self._inventory.load_from == "live":
            self.sku = self.model
            self.short_name = self._get_model_short_name()

        elif self._inventory.load_from == "file":
            for attribute in ["short_name", "sku"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))
