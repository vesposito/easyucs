# coding: utf-8
# !/usr/bin/env python

""" psu.py: Easy UCS Deployment Tool """

from inventory.object import GenericInventoryObject


class GenericPsu(GenericInventoryObject):
    def __init__(self, parent=None):
        GenericInventoryObject.__init__(self, parent=parent)

        self.model = None
        self.sku = None

    def _determine_psu_sku(self):
        # Small fix for when PSU is not present in UCS catalog
        if not self.sku:
            if self.model:
                if self.model in ["N20-PAC5-2500W", "N2200-PAC-400W", "N2200-PAC-400W-B", "NNXA-PAC-650W-PI",
                                  "NXA-PAC-650W-PI", "NXA-PAC-1100W-PE2", "NXA-PAC-1200W-PE"] \
                        or any(self.model.startswith(x) for x in ["UCS-PSU", "UCSB-PSU", "UCSC-PSU", "UCSX-PSU"]):
                    self.sku = self.model

        # Small fix for SKU typos in UCS catalog
        if self.sku == "NXK-PAC-400W ":
            self.sku = "NXK-PAC-400W"
        elif self.sku == "NNXA-PAC-650W-PI":
            self.sku = "NXA-PAC-650W-PI"
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
        elif self.sku == "UCSC-PSU2-1400":
            self.sku = "UCSC-PSU2-1400W"
        elif self.sku in ["UCSB-PSU-2500ACDV-AA26870L-A", "UCSB-PSU-2500ACDV-ECD15020029"]:
            self.sku = "UCSB-PSU-2500ACDV"

        # Some equipmentPsu objects don't have a PID or SKU value. Setting them manually here for known models
        if self.sku is None:
            if self.model in ["DPS-650AB-2 A", "PS-2651-1-LF"]:
                self.sku = "UCSC-PSU-650W"
            elif self.model in ["700-014550-0001"]:
                self.sku = "UCSC-PSUF-1050W"
            elif self.model in ["700-014160-0000", "PS-2771-1S-LF"]:
                self.sku = "UCSC-PSU1-770W"
            elif self.model in ["PS-2112-9S-LF"]:
                self.sku = "UCSC-PSU1-1050W"
            elif self.model in ["PS-2122-9S"]:
                self.sku = "UCSC-PSU1-1200W"
            elif self.model in ["CIS-S-1600ADE000-301", "PS-2162-9S"]:
                self.sku = "UCSC-PSU1-1600W"
            elif self.model in ["ECD15020051"]:
                self.sku = "UCSC-PSU1-2300W"
            elif self.model in ["DPST-1200DB A"]:
                self.sku = "UCSC-PSU2V2-1200W"
            elif self.model in ["DPST-1400AB A"]:
                self.sku = "UCSC-PSU2-1400W"
