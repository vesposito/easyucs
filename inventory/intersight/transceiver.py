# coding: utf-8
# !/usr/bin/env python

""" transceiver.py: Easy UCS Deployment Tool """
from inventory.generic.transceiver import GenericTransceiver
from inventory.intersight.object import IntersightInventoryObject


class IntersightTransceiver(GenericTransceiver, IntersightInventoryObject):
    def __init__(self, parent=None, equipment_transceiver=None):
        GenericTransceiver.__init__(self, parent=parent)
        IntersightInventoryObject.__init__(self, parent=parent, sdk_object=equipment_transceiver)

        self.model = self.get_attribute(attribute_name="model")
        self.revision = self.get_attribute(attribute_name="revision")
        self.serial = self.get_attribute(attribute_name="serial")
        self.type = self.get_attribute(attribute_name="type")
        self.vendor = self.get_attribute(attribute_name="vendor")

        if self._inventory.load_from == "live":
            if not self.sku:
                if self.type:
                    if any(self.type.startswith(x) for x in ["SFP-", "QSFP-", "DS-SFP-", "GLC-"]):
                        self.sku = self.type
            if not self.sku:
                if self.model:
                    if any(self.model.startswith(x) for x in ["SFP-", "QSFP-", "DS-SFP-", "GLC-"]):
                        self.sku = self.model
            if not self.sku:
                if self._object.name:
                    if any(self._object.name.startswith(x) for x in ["SFP-", "QSFP-", "DS-SFP-", "GLC-"]):
                        self.sku = self._object.name
                    elif self._object.name == "1000base-T":
                        self.sku = "GLC-T/TE|SFP-GE-T"

            if not self.sku:
                # Trying to determine SKU manually
                self._determine_sku_manually()

            if not self.sku:
                self.logger(
                    level="debug",
                    message=f"Unable to determine transceiver SKU for port of class " +
                            f"'{self._parent.__class__.__name__}' with serial '{self.serial}', " +
                            f"type '{self.type}', model '{self.model}' and name '{self._object.name}'"
                )

            # Getting length info from catalog file
            self._get_length_info()

        elif self._inventory.load_from == "file":
            for attribute in ["sku"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))
