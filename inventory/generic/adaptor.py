# coding: utf-8
# !/usr/bin/env python

""" adaptor.py: Easy UCS Deployment Tool """

from common import read_json_file
from inventory.object import GenericInventoryObject


class GenericAdaptor(GenericInventoryObject):
    def __init__(self, parent=None):
        GenericInventoryObject.__init__(self, parent=parent)

        self.model = None
        self.model_short_name = None
        self.pci_slot = None
        self.sku = None
        self.type = None

    def _determine_adaptor_sku_and_type(self, vendor="", device="", subvendor="", subdevice=""):
        if vendor and device and subvendor and subdevice:
            # Broadcom
            if (vendor, device, subvendor, subdevice) == ("0x14e4", "0x1639", "0x14e4", "0x1639"):
                self.sku = "N2XX-ABPCI01"
            elif (vendor, device, subvendor, subdevice) == ("0x14e4", "0x164f", "0x14e4", "0x4113"):
                self.sku = "N2XX-ABPCI02"
            elif (vendor, device, subvendor, subdevice) == ("0x14e4", "0x1639", "0x14e4", "0x0906"):
                self.sku = "N2XX-ABPCI03"
            elif (vendor, device, subvendor, subdevice) == ("0x14e4", "0x1662", "0x1137", "0x0087"):
                self.sku = "UCSC-PCIE-BSFP"
            elif (vendor, device, subvendor, subdevice) == ("0x14e4", "0x1662", "0x1137", "0x007c"):
                self.sku = "UCSX-MLOM-001"
            elif (vendor, device, subvendor, subdevice) == ("0x14e4", "0x1662", "0x1137", "0x0088"):
                self.sku = "UCSC-PCIE-BTG"
            elif (vendor, device, subvendor, subdevice) == ("0x14e4", "0x16ae", "0x1137", "0x00cb"):
                self.sku = "UCSC-PCIE-B3SFP"
            # Cisco
            elif (vendor, device, subvendor, subdevice) == ("0x1137", "0x0042", "0x1137", "0x0047"):
                self.sku = "N2XX-ACPCI01"
            # Emulex
            elif (vendor, device, subvendor, subdevice) == ("0x19a2", "0x0700", "0x10df", "0xe602"):
                self.sku = "N2XX-AEPCI01"
            elif (vendor, device, subvendor, subdevice) == ("0x10df", "0xfe00", "0x10df", "0xfe00"):
                self.sku = "N2XX-AEPCI03"
            elif (vendor, device, subvendor, subdevice) == ("0x10df", "0xf100", "0x10df", "0xf100"):
                self.sku = "N2XX-AEPCI05"
            elif (vendor, device, subvendor, subdevice) == ("0x19a2", "0x0710", "0x10df", "0xe702"):
                self.sku = "UCSC-PCIE-ESFP"
            elif (vendor, device, subvendor, subdevice) == ("0x10df", "0xe200", "0x10df", "0xe280"):
                self.sku = "UCSC-PCIE-E16002"
            elif (vendor, device, subvendor, subdevice) == ("0x10df", "0x0720", "0x10df", "0xe800"):
                self.sku = "UCSC-PCIE-E14102"
            elif (vendor, device, subvendor, subdevice) == ("0x10df", "0x0720", "0x10df", "0xe867"):
                self.sku = "UCSC-PCIE-E14102B"
            elif (vendor, device, subvendor, subdevice) == ("0x10df", "0xe300", "0x10df", "0xe310"):
                self.sku = "UCSC-PCIE-BD16GF"
            elif (vendor, device, subvendor, subdevice) == ("0x10df", "0xe300", "0x10df", "0xe301"):
                self.sku = "UCSC-PCIE-BS32GF"
            elif (vendor, device, subvendor, subdevice) == ("0x10df", "0xe300", "0x10df", "0xe300"):
                self.sku = "UCSC-PCIE-BD32GF"
            # Intel
            elif (vendor, device, subvendor, subdevice) == ("0x8086", "0x10fb", "0x8086", "0x000c"):
                self.sku = "N2XX-AIPCI01"
            elif (vendor, device, subvendor, subdevice) == ("0x8086", "0x10e8", "0x8086", "0xa02b"):
                self.sku = "N2XX-AIPCI02"
            elif (vendor, device, subvendor, subdevice) == ("0x8086", "0x1521", "0x1137", "0x00b9"):
                self.sku = "UCSC-PCIE-IRJ45"
            elif (vendor, device, subvendor, subdevice) == ("0x8086", "0x1521", "0x1137", "0x023e"):
                self.sku = "UCSC-PCIE-IRJ45"
            elif (vendor, device, subvendor, subdevice) == ("0x8086", "0x1521", "0x1137", "0x0133"):
                self.sku = "UCSC-MLOM-IRJ45"
            elif (vendor, device, subvendor, subdevice) == ("0x8086", "0x1521", "0x1137", "0x00d3"):
                self.sku = None  # Onboard 1G LoM
                self.type = "nic"
            elif (vendor, device, subvendor, subdevice) == ("0x8086", "0x1528", "0x1137", "0x00d4"):
                self.sku = None  # Onboard 10G LoM (M5)
                self.type = "nic"
            elif (vendor, device, subvendor, subdevice) == ("0x8086", "0x1563", "0x1137", "0x02b3"):
                self.sku = None  # Onboard 10G LoM (M6)
                self.type = "nic"
            elif (vendor, device, subvendor, subdevice) == ("0x8086", "0x1528", "0x1137", "0x00bf"):
                self.sku = "UCSC-PCIE-ITG"
            elif (vendor, device, subvendor, subdevice) == ("0x8086", "0x1563", "0x1137", "0x01a2"):
                self.sku = "UCSC-PCIE-ID10GC"
            elif (vendor, device, subvendor, subdevice) == ("0x8086", "0x1572", "0x1137", "0x020a"):
                self.sku = "UCSC-PCIE-ID10GF"
            elif (vendor, device, subvendor, subdevice) == ("0x8086", "0x1572", "0x1137", "0x013b"):
                self.sku = "UCSC-PCIE-IQ10GF"
            elif (vendor, device, subvendor, subdevice) == ("0x8086", "0x1589", "0x1137", "0x020b"):
                self.sku = "UCSC-PCIE-IQ10GC"
            elif (vendor, device, subvendor, subdevice) == ("0x8086", "0x1583", "0x1137", "0x013c"):
                self.sku = "UCSC-PCIE-ID40GF"
            elif (vendor, device, subvendor, subdevice) == ("0x8086", "0x158b", "0x1137", "0x0225"):
                self.sku = "UCSC-PCIE-ID25GF"
            elif (vendor, device, subvendor, subdevice) == ("0x8086", "0x15ff", "0x1137", "0x02c2"):
                self.sku = "UCSC-P-IQ10GC"
            elif (vendor, device, subvendor, subdevice) == ("0x8086", "0x159b", "0x1137", "0x02be"):
                self.sku = "UCSC-P-I8D25GF"
            elif (vendor, device, subvendor, subdevice) == ("0x8086", "0x1593", "0x1137", "0x02c3"):
                self.sku = "UCSC-P-I8Q25GF"
            elif (vendor, device, subvendor, subdevice) == ("0x8086", "0x1592", "0x1137", "0x02bf"):
                self.sku = "UCSC-P-I8D100GF"
            elif (vendor, device, subvendor, subdevice) == ("0x8086", "0x15ff", "0x1137", "0x02d9"):
                self.sku = "UCSC-O-ID10GC"
            # Mellanox
            elif (vendor, device, subvendor, subdevice) == ("0x15b3", "0x6750", "0x15b3", "0x0016"):
                self.sku = "N2XX-AMPCI01"
            elif (vendor, device, subvendor, subdevice) == ("0x15b3", "0x1015", "0x1137", "0x2aa"):
                self.sku = "UCSC-P-M4D25GF"
            elif (vendor, device, subvendor, subdevice) == ("0x15b3", "0x1017", "0x1137", "0x2ab"):
                self.sku = "UCSC-P-M5D25GF"
            elif (vendor, device, subvendor, subdevice) == ("0x15b3", "0x1017", "0x1137", "0x2b6"):
                self.sku = "UCSC-P-M5S100GF"
            elif (vendor, device, subvendor, subdevice) == ("0x15b3", "0x1019", "0x1137", "0x2ac"):
                self.sku = "UCSC-P-M5D100GF"
            elif (vendor, device, subvendor, subdevice) == ("0x15b3", "0x101d", "0x1137", "0x2cb"):
                self.sku = "UCSC-P-M6DD100GF"
            # QLogic
            elif (vendor, device, subvendor, subdevice) == ("0x1077", "0x8000", "0x1077", "0x017e"):
                self.sku = "N2XX-AQPCI01"
            elif (vendor, device, subvendor, subdevice) == ("0x1077", "0x2432", "0x1077", "0x0138"):
                self.sku = "N2XX-AQPCI03"
            elif (vendor, device, subvendor, subdevice) == ("0x1077", "0x2532", "0x1077", "0x015d"):
                self.sku = "N2XX-AQPCI05"
            elif (vendor, device, subvendor, subdevice) == ("0x1077", "0x8020", "0x1077", "0x0207"):
                self.sku = "UCSC-PCIE-QSFP"
            elif (vendor, device, subvendor, subdevice) == ("0x1077", "0x8030", "0x1077", "0x0274"):
                self.sku = "UCSC-PCIE-Q2672"
            elif (vendor, device, subvendor, subdevice) == ("0x1077", "0x8030", "0x1077", "0x0271"):
                self.sku = "UCSC-PCIE-Q8362"
            elif (vendor, device, subvendor, subdevice) == ("0x14e4", "0x161a", "0x1137", "0x0153"):
                self.sku = "UCSC-PCIE-QNICBT"
            elif (vendor, device, subvendor, subdevice) == ("0x14e4", "0x161a", "0x1137", "0x0152"):
                self.sku = "UCSC-PCIE-QNICSFP"
            elif (vendor, device, subvendor, subdevice) == ("0x1077", "0x2261", "0x1077", "0x02c7"):
                self.sku = "UCSC-PCIE-QD16GF"
            # Added to workaround incorrect subdevice ID (0x2c7 instead of 0x02c7)
            elif (vendor, device, subvendor, subdevice) == ("0x1077", "0x2261", "0x1077", "0x2c7"):
                self.sku = "UCSC-PCIE-QD16GF"
            elif (vendor, device, subvendor, subdevice) == ("0x1077", "0x2261", "0x1077", "0x02b6"):
                self.sku = "UCSC-PCIE-QD32GF"
            elif (vendor, device, subvendor, subdevice) == ("0x1077", "0x8070", "0x1137", "0x0246"):
                self.sku = "UCSC-PCIE-QD25GF"
            elif (vendor, device, subvendor, subdevice) == ("0x1077", "0x1634", "0x1137", "0x0245"):
                self.sku = "UCSC-PCIE-QD40GF"
            elif (vendor, device, subvendor, subdevice) == ("0x1077", "0x1644", "0x1137", "0x0257"):
                self.sku = "UCSC-PCIE-QS100GF"
            elif (vendor, device, subvendor, subdevice) == ("0x1077", "0x8070", "0x1077", "0x0019"):
                self.sku = "UCSC-OCP-QD25GF"
            else:
                self.logger(level="warning", message=f"Impossible to determine Adaptor SKU from unknown PCI " +
                                                     f"device '{vendor}, {device}, {subvendor}, {subdevice}'")

        # Manual entries
        if self.model == "Intel MLOM Quad Port 1Gb RJ45 NIC":
            self.sku = "UCSC-MLOM-IRJ45"
        elif self.model == "Intel i350 Quad Port 1Gb Adapter":
            self.sku = "UCSC-PCIE-IRJ45"
        elif self.model == "Intel X520-DA2 10 Gbps 2 port NIC":
            self.sku = "N2XX-AIPCI01"
        elif self.model == "Intel X710-DA4 Quad Port 10Gb SFP+ converged NIC":
            self.sku = "UCSC-PCIE-IQ10GF"
        elif self.model == "Intel XL710-QDA2 Dual Port 40Gb QSFP converged NIC":
            self.sku = "UCSC-PCIE-ID40GF"
        elif self.model == "Cisco - Intel E810XXVDA2 2x25/10 GbE SFP PCIe NIC":
            self.sku = "UCSC-P-I8D25GF"

        # Getting adaptor type info from catalog files
        if self.sku:
            adaptor_catalog = read_json_file("catalog/adaptors/" + self.sku + ".json")
            if adaptor_catalog:
                self.type = adaptor_catalog.get("adaptor_type")

        # Setting adaptor type for adaptors not present in the catalog files
        if self.sku in ["UCSC-PCIE-E14102B", "UCSC-PCIE-E14102", "UCSC-PCIE-QSFP", "UCSC-PCIE-Q8362"]:
            self.type = "cna"
        elif self.sku in ["N2XX-AEPCI03", "N2XX-AEPCI05", "UCSC-P-Q7D64GF"]:
            self.type = "hba"
        elif self.sku in ["UCSC-PCIE-B3SFP", "UCSC-PCIE-BTG", "UCSC-P-IQ1GC", "N2XX-AMPCI01", "UCSC-P-MCD100GF",
                          "UCSC-P-MDD100GF", "UCSC-P-N6D25GF", "UCSC-P-N7Q25GF", "UCSC-P-N7D200GF", "UCSC-PCIE-QNICBT",
                          "UCSC-PCIE-QNICSFP", "UCSC-PCIE-QD10GC", "UCSC-O-N6CD25GF", "UCSC-O-N6CD100GF"]:
            self.type = "nic"
        elif self.sku in []:
            self.type = "vic"
        elif self.pci_slot == "L":  # For LoM ports
            self.type = "nic"
        elif self.pci_slot == "14" and self._parent.sku == "UCS-S3260-M5SRB":  # For LoM on S3260 M5 server node
            self.type = "nic"
        elif not self.type:
            self.logger(level="warning", message=f"Impossible to determine Adaptor Type from unknown PCI " +
                                                 f"device '{self.sku}': '{vendor}, {device}, {subvendor}, {subdevice}'")

    def _get_imm_compatibility(self):
        """
        Returns adaptor IMM Compatibility from EasyUCS catalog files
        """
        if self.sku is not None:
            # We use the catalog file to get the adaptor IMM Compatibility
            adaptor_catalog = read_json_file(file_path="catalog/adaptors/" + self.sku + ".json", logger=self)
            if not adaptor_catalog:
                # If we are on a S3260 chassis, we look for the catalog file in the io_modules folder
                adaptor_catalog = read_json_file(file_path="catalog/io_modules/" + self.sku + ".json", logger=self)

            if adaptor_catalog:
                if "imm_compatible" in adaptor_catalog:
                    return adaptor_catalog["imm_compatible"]

        return None

    def _get_model_short_name(self):
        """
        Returns adaptor short name from EasyUCS catalog files
        """
        if self.sku is not None:
            # We use the catalog file to get the adaptor short name
            adaptor_catalog = read_json_file(file_path="catalog/adaptors/" + self.sku + ".json", logger=self)
            if not adaptor_catalog:
                # If we are on a S3260 chassis, we look for the catalog file in the io_modules folder
                adaptor_catalog = read_json_file(file_path="catalog/io_modules/" + self.sku + ".json", logger=self)

            if adaptor_catalog:
                if "model_short_name" in adaptor_catalog:
                    return adaptor_catalog["model_short_name"]

        return None
