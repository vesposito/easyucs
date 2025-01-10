# coding: utf-8
# !/usr/bin/env python

""" transceiver.py: Easy UCS Deployment Tool """
from common import read_json_file
from inventory.object import GenericInventoryObject


class GenericTransceiver(GenericInventoryObject):
    def __init__(self, parent=None):
        GenericInventoryObject.__init__(self, parent=parent)

        self.length = None
        self.sku = None

    def _determine_sku_manually(self):
        if hasattr(self, "model"):
            # Manual entries for Ethernet transceivers
            if self._parent.__class__.__name__ in ["IntersightFiEthPort", "UcsSystemFiEthPort"]:
                if self.model in ["ABCU-5710RZ-CS4", "ABCU-5710RZ-CS5", "SP7041-R"]:
                    self.sku = "GLC-T"
                elif self.model in ["74752-9026"]:
                    self.sku = "SFP-H10GB-CU3M"
                elif self.model in ["FTL410QT3C-C1"]:
                    self.sku = "FET-40G"
                elif self.model in ["AFBR-79EBPZ-CS2"]:
                    self.sku = "QSFP-40G-SR-BD"

            # Manual entries for FC transceivers
            if self._parent.__class__.__name__ in ["IntersightFiFcPort", "UcsSystemFiFcPort"]:
                if self.model in ["FTLF8524P2BNL-C2"]:
                    self.sku = "DS-SFP-FC4G-SW"
                elif self.model in ["FTLF8528P2BCV-CS", "FTLF8528P3BCV-C1", "SFBR-5780AMZ-CS1", "SFBR-5780AMZ-CS2",
                                    "SFBR-5780APZ", "SFBR-5780APZ-CS2"]:
                    self.sku = "DS-SFP-FC8G-SW"
                elif self.model in ["FTLF8528P3BCV-CS", "FTLF8529P3BCV-CS", "AFBR-57F5PZ-CS1", "RTXM228-561-C99"]:
                    self.sku = "DS-SFP-FC16G-SW"
                elif self.model in ["FTLF8532P4BCV-C1", "FTLF8532P4BCV-C2", "RTXM330-561-C99", "SFBR-57G5MZ-CS1",
                                    "TR-PB85S-NCI"]:
                    self.sku = "DS-SFP-FC32G-SW"
                elif self.model in ["FTLC9555FEPM", "FTLC9555FEPM-C1"]:
                    self.sku = "DS-SFP-4X32G-SW"
                elif hasattr(self, "type") and self.type in ["4x32gsw"]:
                    self.sku = "DS-SFP-4X32G-SW"

    def _get_length_info(self):
        # Getting length info from catalog file
        transceiver_skus = read_json_file("catalog/transceivers/skus.json")
        if self.sku in transceiver_skus.keys():
            self.length = transceiver_skus[self.sku].get("length")

    def _get_sku_info(self):
        # Getting SKU info from types file
        transceiver_types = read_json_file("catalog/transceivers/types.json")
        if hasattr(self, "type"):
            if self.type in transceiver_types.keys():
                self.sku = transceiver_types[self.type].get("sku")
