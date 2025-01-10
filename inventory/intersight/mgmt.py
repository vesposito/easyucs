# coding: utf-8
# !/usr/bin/env python

""" mgmt.py: Easy UCS Deployment Tool """
from inventory.generic.mgmt import GenericMgmtInterface
from inventory.intersight.object import IntersightInventoryObject


class IntersightMgmtInterface(GenericMgmtInterface, IntersightInventoryObject):
    def __init__(self, parent=None, equipment_tpm=None):
        GenericMgmtInterface.__init__(self, parent=parent)
        IntersightInventoryObject.__init__(self, parent=parent, sdk_object=equipment_tpm)

        self.mac = self.get_attribute(attribute_name="mac_address", attribute_secondary_name="mac")
        self.mask = self.get_attribute(attribute_name="mask")

        if self._inventory.load_from == "live":
            pass

        elif self._inventory.load_from == "file":
            for attribute in []:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))
