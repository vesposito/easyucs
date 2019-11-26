# coding: utf-8
# !/usr/bin/env python

""" transceiver.py: Easy UCS Deployment Tool """
from easyucs import __author__, __copyright__,  __version__, __status__


from easyucs.inventory.object import GenericUcsInventoryObject, UcsImcInventoryObject, UcsSystemInventoryObject


class UcsTransceiver(GenericUcsInventoryObject):
    def __init__(self, parent=None, transceiver=None):
        GenericUcsInventoryObject.__init__(self, parent=parent, ucs_sdk_object=transceiver)

        self.type = self.get_attribute(ucs_sdk_object=transceiver, attribute_name="type")
        self.vendor = self.get_attribute(ucs_sdk_object=transceiver, attribute_name="vendor")


class UcsSystemTransceiver(UcsTransceiver, UcsSystemInventoryObject):
    _UCS_SDK_OBJECT_NAME = "equipmentXcvr"

    def __init__(self, parent=None, equipment_xcvr=None):
        UcsTransceiver.__init__(self, parent=parent, transceiver=equipment_xcvr)

        self.model = self.get_attribute(ucs_sdk_object=equipment_xcvr, attribute_name="model")
        self.revision = self.get_attribute(ucs_sdk_object=equipment_xcvr, attribute_name="revision")
        self.serial = self.get_attribute(ucs_sdk_object=equipment_xcvr, attribute_name="serial")

        UcsSystemInventoryObject.__init__(self, parent=parent, ucs_sdk_object=equipment_xcvr)

        self.sku = None
        self.length = None
        transceiver_types_matrix = {
            # SFP+ 10Gbps Twinax & AOC
            "h10gcu1m": {"sku": "SFP-H10GB-CU1M", "length": "1m"},
            "h10gcu2m": {"sku": "SFP-H10GB-CU2M", "length": "2m"},
            "h10gcu3m": {"sku": "SFP-H10GB-CU3M", "length": "3m"},
            "h10gcu5m": {"sku": "SFP-H10GB-CU5M", "length": "5m"},
            "h10gacu7m": {"sku": "SFP-H10GB-ACU7M", "length": "7m"},
            "h10gacu10m": {"sku": "SFP-H10GB-ACU10M", "length": "10m"},
            "h10gaoc1m": {"sku": "SFP-10G-AOC1M", "length": "1m"},
            "h10gaoc2m": {"sku": "SFP-10G-AOC2M", "length": "2m"},
            "h10gaoc3m": {"sku": "SFP-10G-AOC3M", "length": "3m"},
            "h10gaoc5m": {"sku": "SFP-10G-AOC5M", "length": "5m"},
            "h10gaoc7m": {"sku": "SFP-10G-AOC7M", "length": "7m"},
            "h10gaoc10m": {"sku": "SFP-10G-AOC10M", "length": "10m"},
            # SFP+ 10Gbps Twinax & AOC Indeterminate models
            "h10gacuaoc1m": {"sku": "SFP-H10GB-ACU/AOC1M", "length": "1m"},
            "h10gacuaoc2m": {"sku": "SFP-H10GB-ACU/AOC2M", "length": "2m"},
            "h10gacuaoc3m": {"sku": "SFP-H10GB-ACU/AOC3M", "length": "3m"},
            "h10gacuaoc5m": {"sku": "SFP-H10GB-ACU/AOC5M", "length": "5m"},
            "h10gacuaoc7m": {"sku": "SFP-H10GB-ACU/AOC7M", "length": "7m"},
            "h10gacuaoc10m": {"sku": "SFP-H10GB-ACU/AOC10M", "length": "10m"},
            "h10gacuaoc15m": {"sku": "SFP-H10GB-ACU/AOC15M", "length": "15m"},

            # SFP28 25Gbps Twinax & AOC
            "h25gcu1m": {"sku": "SFP-H25G-CU1M", "length": "1m"},
            "h25gcu2m": {"sku": "SFP-H25G-CU2M", "length": "2m"},
            "h25gcu3m": {"sku": "SFP-H25G-CU3M", "length": "3m"},
            "h25gcu5m": {"sku": "SFP-H25G-CU5M", "length": "5m"},
            "h25gaoc1m": {"sku": "SFP-25G-AOC1M", "length": "1m"},
            "h25gaoc2m": {"sku": "SFP-25G-AOC2M", "length": "2m"},
            "h25gaoc3m": {"sku": "SFP-25G-AOC3M", "length": "3m"},
            "h25gaoc5m": {"sku": "SFP-25G-AOC5M", "length": "5m"},
            "h25gaoc7m": {"sku": "SFP-25G-AOC7M", "length": "7m"},
            "h25gaoc10m": {"sku": "SFP-25G-AOC10M", "length": "10m"},

            # QSFP+ 40Gbps Twinax & AOC
            "qsfph40gcu1m": {"sku": "QSFP-H40G-CU1M", "length": "1m"},
            "qsfph40gcu2m": {"sku": "QSFP-H40G-CU2M", "length": "2m"},
            "qsfph40gcu3m": {"sku": "QSFP-H40G-CU3M", "length": "3m"},
            "qsfph40gcu5m": {"sku": "QSFP-H40G-CU5M", "length": "5m"},
            "qsfph40gacu7m": {"sku": "QSFP-H40G-ACU7M", "length": "7m"},
            "qsfph40gacu10m": {"sku": "QSFP-H40G-ACU10M", "length": "10m"},
            "qsfph40gaoc1m": {"sku": "QSFP-H40G-AOC1M", "length": "1m"},
            "qsfph40gaoc2m": {"sku": "QSFP-H40G-AOC2M", "length": "2m"},
            "qsfph40gaoc3m": {"sku": "QSFP-H40G-AOC3M", "length": "3m"},
            "qsfph40gaoc5m": {"sku": "QSFP-H40G-AOC5M", "length": "5m"},
            "qsfph40gaoc7m": {"sku": "QSFP-H40G-AOC7M", "length": "7m"},
            "qsfph40gaoc10m": {"sku": "QSFP-H40G-AOC10M", "length": "10m"},
            "qsfph40gaoc15m": {"sku": "QSFP-H40G-AOC15M", "length": "15m"},

            # QSFP+ 4x10Gbps Twinax & AOC
            "qsfp4sfp10gcu1m": {"sku": "QSFP-4SFP10G-CU1M", "length": "1m"},
            "qsfp4sfp10gcu2m": {"sku": "QSFP-4SFP10G-CU2M", "length": "2m"},
            "qsfp4sfp10gcu3m": {"sku": "QSFP-4SFP10G-CU3M", "length": "3m"},
            "qsfp4sfp10gcu5m": {"sku": "QSFP-4SFP10G-CU5M", "length": "5m"},
            "qsfp4x10gac7m": {"sku": "QSFP-4X10G-AC7M", "length": "7m"},
            "qsfp4x10gac10m": {"sku": "QSFP-4X10G-AC10M", "length": "10m"},
            "qsfp4x10ga0c1m": {"sku": "QSFP-4X10G-AOC1M", "length": "1m"},
            "qsfp4x10ga0c2m": {"sku": "QSFP-4X10G-AOC2M", "length": "2m"},
            "qsfp4x10ga0c3m": {"sku": "QSFP-4X10G-AOC3M", "length": "3m"},
            "qsfp4x10ga0c5m": {"sku": "QSFP-4X10G-AOC5M", "length": "5m"},
            "qsfp4x10ga0c7m": {"sku": "QSFP-4X10G-AOC7M", "length": "7m"},
            "qsfp4x10ga0c10m": {"sku": "QSFP-4X10G-AOC10M", "length": "10m"},

            # QSFP28 100Gbps Twinax & AOC
            "qsfp100gcu1m": {"sku": "QSFP-100G-CU1M", "length": "1m"},
            "qsfp100gcu2m": {"sku": "QSFP-100G-CU2M", "length": "2m"},
            "qsfp100gcu3m": {"sku": "QSFP-100G-CU3M", "length": "3m"},
            "qsfp100gaoc1m": {"sku": "QSFP-100G-AOC1M", "length": "1m"},
            "qsfp100gaoc2m": {"sku": "QSFP-100G-AOC2M", "length": "2m"},
            "qsfp100gaoc3m": {"sku": "QSFP-100G-AOC3M", "length": "3m"},
            "qsfp100gaoc5m": {"sku": "QSFP-100G-AOC5M", "length": "5m"},
            "qsfp100gaoc7m": {"sku": "QSFP-100G-AOC7M", "length": "7m"},
            "qsfp100gaoc10m": {"sku": "QSFP-100G-AOC10M", "length": "10m"},
            "qsfp100gaoc15m": {"sku": "QSFP-100G-AOC15M", "length": "15m"},
            "qsfp100gaoc20m": {"sku": "QSFP-100G-AOC20M", "length": "20m"},
            "qsfp100gaoc25m": {"sku": "QSFP-100G-AOC25M", "length": "25m"},
            "qsfp100gaoc30m": {"sku": "QSFP-100G-AOC30M", "length": "30m"},

            # QSFP28 4x25Gbps Twinax & AOC
            "qsfp4sfp25gcu1m": {"sku": "QSFP-4SFP25G-CU1M", "length": "1m"},
            "qsfp4sfp25gcu2m": {"sku": "QSFP-4SFP25G-CU2M", "length": "2m"},
            "qsfp4sfp25gcu3m": {"sku": "QSFP-4SFP25G-CU3M", "length": "3m"},
            "qsfp4sfp25gcu5m": {"sku": "QSFP-4SFP25G-CU5M", "length": "5m"},

            # SFP 1Gbps transceivers
            # SFP 1Gbps transceivers Indeterminate models
            "1000baset": {"sku": "GLC-T/TE|SFP-GE-T", "length": "<=100m"},
            "1000basesx": {"sku": "GLC-SX-MM/MMD", "length": "<=1km"},
            "1000baselh": {"sku": "GLC-LH-SM/SMD", "length": "<=10km"},

            # SFP+ 10Gbps transceivers
            "fet": {"sku": "FET-10G", "length": "<=100m"},
            # SFP+ 10Gbps transceivers Indeterminate models
            "10gbasesr": {"sku": "SFP-10G-SR/SR-S", "length": "<=400m"},
            "10gbaselr": {"sku": "SFP-10G-LR/LR-S", "length": "<=10km"},

            # SFP28 25Gbps transceivers
            "h25gsrs": {"sku": "SFP-25G-SR-S", "length": "<=100m"},

            # QSFP+ 40Gbps transceivers
            "qsfpqsa": {"sku": "CVR-QSFP-SFP10G", "length": "n/a"},
            "qsfp40gfet": {"sku": "FET-40G", "length": "<=150m"},
            "qsfp40gsrbd": {"sku": "QSFP-40G-SR-BD", "length": "<=150m"},
            "qsfp40gcsr4": {"sku": "QSFP-40G-CSR4", "length": "<=400m"},
            # QSFP+ 40Gbps transceivers Indeterminate models
            "qsfp40gsr4": {"sku": "QSFP-40G-SR4/SR4-S", "length": "<=150m"},
            "qsfp40glr4": {"sku": "QSFP-40G-LR4/LR4-S", "length": "<=10km"},

            # QSFP28 100Gbps transceivers
            "qsfp100g40gbidi": {"sku": "QSFP-40/100-SRBD", "length": "<=100m"},
            "qsfp100gsmsr": {"sku": "QSFP-100G-SM-SR", "length": "<=2km"},
            "qsfp100gcr4": {"sku": "QSFP-100G-SR4-S", "length": "<=100m"}
        }
        for transceiver_type in transceiver_types_matrix.keys():
            if self.type == transceiver_type:
                self.sku = transceiver_types_matrix[transceiver_type]["sku"]
                self.length = transceiver_types_matrix[transceiver_type]["length"]

        # Manual entries for FC transceivers
        if self._parent.__class__.__name__ == "UcsSystemFiFcPort":
            if self.type in ["sfp", "unknown"]:
                if self.model in ["FTLF8524P2BNL-C2"]:
                    self.sku = "DS-SFP-FC4G-SW"
                    self.length = "<=380m"
                if self.model in ["FTLF8528P2BCV-CS", "FTLF8528P3BCV-C1", "SFBR-5780AMZ-CS2", "SFBR-5780APZ-CS2"]:
                    self.sku = "DS-SFP-FC8G-SW"
                    self.length = "<=190m"
                if self.model in ["FTLF8528P3BCV-CS", "FTLF8529P3BCV-CS", "AFBR-57F5PZ-CS1"]:
                    self.sku = "DS-SFP-FC16G-SW"
                    self.length = "<=125m"
                if self.model in ["FTLF8532P4BCV-C1", "SFBR-57G5MZ-CS1"]:
                    self.sku = "DS-SFP-FC32G-SW"
                    self.length = "<=100m"

        # Manual entries for unknown Ethernet transceivers
        if self._parent.__class__.__name__ == "UcsSystemFiEthPort":
            if self.type in ["unknown"]:
                if self.model in ["74752-9026"]:
                    self.sku = "SFP-H10GB-CU3M"
                    self.length = "3m"


class UcsImcTransceiver(UcsTransceiver, UcsImcInventoryObject):
    _UCS_SDK_OBJECT_NAME = "adaptorConnectorInfo"

    def __init__(self, parent=None, adaptor_connector_info=None):
        UcsTransceiver.__init__(self, parent=parent, transceiver=adaptor_connector_info)

        self.model = self.get_attribute(ucs_sdk_object=adaptor_connector_info, attribute_name="part_number",
                                        attribute_secondary_name="model")
        self.revision = self.get_attribute(ucs_sdk_object=adaptor_connector_info, attribute_name="part_revision",
                                           attribute_secondary_name="revision")

        UcsImcInventoryObject.__init__(self, parent=parent, ucs_sdk_object=adaptor_connector_info)
