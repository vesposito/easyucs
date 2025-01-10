# coding: utf-8
# !/usr/bin/env python

""" gpu.py: Easy UCS Deployment Tool """
from inventory.generic.gpu import GenericGpu
from inventory.intersight.object import IntersightInventoryObject


class IntersightGpu(GenericGpu, IntersightInventoryObject):
    def __init__(self, parent=None, graphics_card=None):
        GenericGpu.__init__(self, parent=parent)
        IntersightInventoryObject.__init__(self, parent=parent, sdk_object=graphics_card)

        self.firmware_version = self.get_attribute(attribute_name="firmware_version")
        self.id = self.get_attribute(attribute_name="gpu_id", attribute_secondary_name="id")
        self.model = self.get_attribute(attribute_name="model")
        self.name = self.get_attribute(attribute_name="description", attribute_secondary_name="name")
        self.part_number = self.get_attribute(attribute_name="part_number")
        self.pci_slot = self.get_attribute(attribute_name="pci_slot")
        self.revision = self.get_attribute(attribute_name="revision")
        self.serial = self.get_attribute(attribute_name="serial")
        self.vendor = self.get_attribute(attribute_name="vendor")

        if self._inventory.load_from == "live":
            self.sku = self.model

        elif self._inventory.load_from == "file":
            for attribute in ["sku"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))
