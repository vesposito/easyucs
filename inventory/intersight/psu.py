# coding: utf-8
# !/usr/bin/env python

""" psu.py: Easy UCS Deployment Tool """

from inventory.intersight.object import IntersightInventoryObject


class IntersightPsu(IntersightInventoryObject):
    def __init__(self, parent=None, equipment_psu=None):
        IntersightInventoryObject.__init__(self, parent=parent, sdk_object=equipment_psu)

        self.firmware_version = self.get_attribute(attribute_name="psu_fw_version",
                                                   attribute_secondary_name="firmware_version")
        self.id = self.get_attribute(attribute_name="psu_id", attribute_secondary_name="id", attribute_type="str")
        self.model = self.get_attribute(attribute_name="model")
        self.part_number = self.get_attribute(attribute_name="part_number")
        self.revision = self.get_attribute(attribute_name="revision")
        self.serial = self.get_attribute(attribute_name="serial")
        self.sku = self.get_attribute(attribute_name="sku")
        self.vendor = self.get_attribute(attribute_name="vendor")
        self.vid = self.get_attribute(attribute_name="vid")
