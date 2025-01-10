# coding: utf-8
# !/usr/bin/env python

""" storage.py: Easy UCS Deployment Tool """
import re

from inventory.object import GenericInventoryObject


class GenericStorageController(GenericInventoryObject):
    def __init__(self, parent=None):
        GenericInventoryObject.__init__(self, parent=parent)

        self.sku = None


class GenericStorageLocalDisk(GenericInventoryObject):
    def __init__(self, parent=None):
        GenericInventoryObject.__init__(self, parent=parent)

        self.drive_type = None
        self.link_speed = None
        self.model = None
        self.rotational_speed_marketing = None
        self.size_marketing = None
        self.sku = None

    def _determine_size_and_rpm(self, description=""):
        if description:
            regex = r"(\d+\.?\dK) RPM"
            res = re.search(regex, description)
            if res is not None:
                self.rotational_speed_marketing = res.group(1)

            regex = r"(\d+\.?\d?) ?[GT]B"
            res = re.search(regex, description)
            if res is not None:
                self.size_marketing = res.group(0).replace(" ", "")

    def _determine_nvme_slot_type(self):
        if getattr(self, "id") and "FRONT-NVME-" in self.id:
            self.slot_type = "sff-nvme"
            regex = r"\d+"
            res = re.search(regex, self.id)
            if res is not None:
                self.id = str(res.group(0))
        elif self.model is not None:
            if "HHHL" in self.model:
                self.slot_type = "pcie-nvme"

        if not self.slot_type:
            if getattr(self, "pci_slot") and self.pci_slot:
                if any(x in self.pci_slot for x in ["FRONT", "REAR", "U.2", "U.3"]):
                    if self._parent.__class__.__name__ in ["IntersightBlade", "UcsSystemBlade"] and \
                            self._parent.model in ["UCSB-B200-M6"]:
                        self.slot_type = "sff-7mm-m6-nvme"
                    else:
                        self.slot_type = "sff-nvme"
                else:
                    self.slot_type = "pcie-nvme"

    def _format_link_speed(self):
        # SAS / SATA speeds
        if self.link_speed in ["1.5", "1-5-gbps", "1.5 Gb/s"]:
            self.link_speed = float(1.5)
        elif self.link_speed in ["3", "3-gbps", "3.0 Gb/s"]:
            self.link_speed = float(3)
        elif self.link_speed in ["6", "6-gbps", "6.0 Gb/s"]:
            self.link_speed = float(6)
        elif self.link_speed in ["12", "12-gbps", "12.0 Gb/s"]:
            self.link_speed = float(12)
        elif self.link_speed in ["24", "24-gbps", "24.0 Gb/s"]:
            self.link_speed = float(24)

        # NVMe speeds
        elif self.link_speed in ["2.5", "2-5-gtps"]:
            self.link_speed = float(2.5)
        elif self.link_speed in ["5", "5-gtps"]:
            self.link_speed = float(5)
        elif self.link_speed in ["8", "8-gtps"]:
            self.link_speed = float(8)
        elif self.link_speed in ["16", "16-gtps"]:
            self.link_speed = float(16)

    def _format_rotational_speed_marketing(self):
        # Properly format rotational_speed_marketing so that it fits the display on disk drives for the pictures
        if self.rotational_speed_marketing in [15000]:
            self.rotational_speed_marketing = "15K"
        elif self.rotational_speed_marketing in [10, 10000, 10025, 10520]:
            self.rotational_speed_marketing = "10K"
        elif self.rotational_speed_marketing in [7200, 7202, 72000]:
            self.rotational_speed_marketing = "7.2K"
        elif self.rotational_speed_marketing in [5400]:
            self.rotational_speed_marketing = "5.4K"
        elif self.rotational_speed_marketing == 0:
            self.rotational_speed_marketing = None

    def _format_size_marketing(self):
        # Properly format size_marketing so that it fits the display on disk drives for the pictures
        if self.size_marketing is not None:
            if self.size_marketing < 1000:
                self.size_marketing = str(int(self.size_marketing)) + "GB"
            elif self.size_marketing >= 1000:
                if (self.size_marketing / 1000).is_integer():
                    self.size_marketing = str(int(self.size_marketing / 1000)) + "TB"
                else:
                    if str(round(self.size_marketing / 1000, ndigits=1))[-2:] == ".0":
                        self.size_marketing = str(int(self.size_marketing / 1000)) + "TB"
                    else:
                        self.size_marketing = str(round(self.size_marketing / 1000, ndigits=1)) + "TB"

        # Manual adjustment for wrong round up of some drives
        size_adjustment_table = {
            "98GB": "100GB",
            "118GB": "120GB",
            "147GB": "146GB",
            "238GB": "240GB",
            "298GB": "300GB",
            "299GB": "300GB",
            "398GB": "400GB",
            "598GB": "600GB",
            "798GB": "800GB",
            "801GB": "800GB",
            "958GB": "960GB",
            "998GB": "1TB",
            "7.7TB": "7.6TB"
        }
        # Adjustment table specific for SSD sizes
        ssd_size_adjustment_table = {
            "1.8TB": "1.9TB",
        }
        if self.size_marketing in size_adjustment_table.keys():
            self.size_marketing = size_adjustment_table[self.size_marketing]
        if self.drive_type == "SSD":
            if self.size_marketing in ssd_size_adjustment_table.keys():
                self.size_marketing = ssd_size_adjustment_table[self.size_marketing]


class GenericStorageRaidBattery(GenericInventoryObject):
    def __init__(self, parent=None):
        GenericInventoryObject.__init__(self, parent=parent)

        self.sku = None
