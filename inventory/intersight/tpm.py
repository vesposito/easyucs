# coding: utf-8
# !/usr/bin/env python

""" tpm.py: Easy UCS Deployment Tool """
from inventory.generic.tpm import GenericTpm
from inventory.intersight.object import IntersightInventoryObject


class IntersightTpm(GenericTpm, IntersightInventoryObject):
    def __init__(self, parent=None, equipment_tpm=None):
        GenericTpm.__init__(self, parent=parent)
        IntersightInventoryObject.__init__(self, parent=parent, sdk_object=equipment_tpm)

        self.activation_status = self.get_attribute(attribute_name="activation_status")
        self.admin_state = self.get_attribute(attribute_name="admin_state")
        self.id = self.get_attribute(attribute_name="tpm_id", attribute_secondary_name="id")
        self.model = self.get_attribute(attribute_name="model")
        self.ownership = self.get_attribute(attribute_name="ownership")
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
