# coding: utf-8
# !/usr/bin/env python

""" psu.py: Easy UCS Deployment Tool """

from inventory.ucs.object import GenericUcsInventoryObject, UcsImcInventoryObject, UcsSystemInventoryObject


class UcsPsu(GenericUcsInventoryObject):
    _UCS_SDK_OBJECT_NAME = "equipmentPsu"

    def __init__(self, parent=None, equipment_psu=None):
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

        # Small fix for SKU typos in UCS catalog
        if hasattr(self, "sku"):
            if self.sku == "NXK-PAC-400W ":
                self.sku = "NXK-PAC-400W"
            elif self.sku == " UCSC-PSUF-1050W ":
                self.sku = "UCSC-PSUF-1050W"
            elif self.sku == "UCSC-PSU1-1050W-341-0638-03":
                self.sku = "UCSC-PSU1-1050W"
            elif self.sku == "UCSC-PSU1-1200W-341-0775-01":
                self.sku = "UCSC-PSU1-1200W"
            elif self.sku == "UCSC-PSU1-1600W-341-0732-04":
                self.sku = "UCSC-PSU1-1600W"
            elif self.sku == "UCSC-PSU1-2300W-341-0770-01":
                self.sku = "UCSC-PSU1-2300W"

        # Small fix for when PSU is not present in UCS catalog
        if hasattr(self, "sku"):
            if not self.sku:
                if self.model:
                    if self.model in ["N2200-PAC-400W", "N2200-PAC-400W-B", "NXA-PAC-1100W-PE2", "NXA-PAC-1200W-PE"] \
                            or self.model.startswith("UCSC-PSU") or self.model.startswith("UCS-PSU"):
                        self.sku = self.model


class UcsImcPsu(UcsPsu, UcsImcInventoryObject):
    def __init__(self, parent=None, equipment_psu=None):
        UcsPsu.__init__(self, parent=parent, equipment_psu=equipment_psu)

        self.firmware_version = self.get_attribute(ucs_sdk_object=equipment_psu, attribute_name="fw_version",
                                                   attribute_secondary_name="firmware_version")

        UcsImcInventoryObject.__init__(self, parent=parent, ucs_sdk_object=equipment_psu)

        # Since we don't have a catalog item for finding the SKU, we set it manually here
        self.sku = self.get_attribute(ucs_sdk_object=equipment_psu, attribute_name="pid",
                                      attribute_secondary_name="sku")

        # Some equipmentPsu objects don't have a PID or SKU value. Setting them manually here for known models
        if self.sku is None:
            if self.model in ["DPS-650AB-2 A", "PS-2651-1-LF"]:
                self.sku = "UCSC-PSU-650W"
            if self.model in ["PS-2771-1S-LF"]:
                self.sku = "UCSC-PSU1-770W"
            if self.model in ["DPST-1200DB A"]:
                self.sku = "UCSC-PSU2V2-1200W"
            if self.model in ["DPST-1400AB A"]:
                self.sku = "UCSC-PSU2-1400W"

        # Fix for some wrongly labeled PSU PIDs
        if self.sku == "UCSC-PSU2-1400":
            self.sku = "UCSC-PSU2-1400W"
