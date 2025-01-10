# coding: utf-8
# !/usr/bin/env python

""" cpu.py: Easy UCS Deployment Tool """
from inventory.generic.cpu import GenericCpu
from inventory.intersight.object import IntersightInventoryObject


class IntersightCpu(GenericCpu, IntersightInventoryObject):
    def __init__(self, parent=None, processor_unit=None):
        GenericCpu.__init__(self, parent=parent)
        IntersightInventoryObject.__init__(self, parent=parent, sdk_object=processor_unit)

        self.arch = self.get_attribute(attribute_name="architecture", attribute_secondary_name="arch")
        self.cores = self.get_attribute(attribute_name="num_cores", attribute_secondary_name="cores")
        self.cores_enabled = self.get_attribute(attribute_name="num_cores_enabled",
                                                attribute_secondary_name="cores_enabled", attribute_type="int")
        self.id = self.get_attribute(attribute_name="processor_id", attribute_secondary_name="id")
        self.model = self.get_attribute(attribute_name="model")
        self.part_number = self.get_attribute(attribute_name="part_number")
        self.revision = self.get_attribute(attribute_name="revision")
        self.serial = self.get_attribute(attribute_name="serial")
        self.sku = self.get_attribute(attribute_name="pid", attribute_secondary_name="sku")
        self.speed = self.get_attribute(attribute_name="speed")
        self.threads = self.get_attribute(attribute_name="num_threads", attribute_secondary_name="threads",
                                          attribute_type="int")
        self.vendor = self.get_attribute(attribute_name="vendor")

        self._get_model_short_name()

        if self._inventory.load_from == "live":
            # Speed is stored in GHz, converting it to MHz
            if self.speed:
                self.speed = int(self.speed) * 1000

        elif self._inventory.load_from == "file":
            for attribute in ["sku"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))
