# coding: utf-8
# !/usr/bin/env python

""" psu.py: Easy UCS Deployment Tool """
from inventory.generic.psu import GenericPsu
from inventory.ucs.object import GenericUcsInventoryObject, UcsImcInventoryObject, UcsSystemInventoryObject


class UcsPsu(GenericPsu, GenericUcsInventoryObject):
    _UCS_SDK_OBJECT_NAME = "equipmentPsu"

    def __init__(self, parent=None, equipment_psu=None):
        GenericPsu.__init__(self, parent=parent)
        GenericUcsInventoryObject.__init__(self, parent=parent, ucs_sdk_object=equipment_psu)

        self.id = self.get_attribute(ucs_sdk_object=equipment_psu, attribute_name="id")
        self.model = self.get_attribute(ucs_sdk_object=equipment_psu, attribute_name="model")
        self.serial = self.get_attribute(ucs_sdk_object=equipment_psu, attribute_name="serial")
        self.vendor = self.get_attribute(ucs_sdk_object=equipment_psu, attribute_name="vendor")


class UcsSystemPsu(UcsPsu, UcsSystemInventoryObject):
    _UCS_SDK_CATALOG_OBJECT_NAME = "equipmentPsuCapProvider"
    _UCS_SDK_FIRMWARE_RUNNING_SUFFIX = "/fw-system"

    def __init__(self, parent=None, equipment_psu=None):
        UcsPsu.__init__(self, parent=parent, equipment_psu=equipment_psu)

        self.revision = self.get_attribute(ucs_sdk_object=equipment_psu, attribute_name="revision")

        UcsSystemInventoryObject.__init__(self, parent=parent, ucs_sdk_object=equipment_psu)

        self._determine_psu_sku()


class UcsImcPsu(UcsPsu, UcsImcInventoryObject):
    def __init__(self, parent=None, equipment_psu=None):
        UcsPsu.__init__(self, parent=parent, equipment_psu=equipment_psu)

        self.firmware_version = self.get_attribute(ucs_sdk_object=equipment_psu, attribute_name="fw_version",
                                                   attribute_secondary_name="firmware_version")

        UcsImcInventoryObject.__init__(self, parent=parent, ucs_sdk_object=equipment_psu)

        # Since we don't have a catalog item for finding the SKU, we set it manually here
        self.sku = self.get_attribute(ucs_sdk_object=equipment_psu, attribute_name="pid",
                                      attribute_secondary_name="sku")

        self._determine_psu_sku()
