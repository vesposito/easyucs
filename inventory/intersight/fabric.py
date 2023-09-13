# coding: utf-8
# !/usr/bin/env python

""" fabric.py: Easy UCS Deployment Tool """

from common import read_json_file
from inventory.intersight.object import IntersightInventoryObject
from inventory.intersight.psu import IntersightPsu


class IntersightFi(IntersightInventoryObject):
    def __init__(self, parent=None, network_element=None):
        IntersightInventoryObject.__init__(self, parent=parent, sdk_object=network_element)

        self.id = self.get_attribute(attribute_name="switch_id", attribute_secondary_name="id")
        self.ip_address = self.get_attribute(attribute_name="out_of_band_ip_address",
                                             attribute_secondary_name="ip_address")
        self.ip_gateway = self.get_attribute(attribute_name="out_of_band_ip_gateway",
                                             attribute_secondary_name="ip_gateway")
        self.ip_netmask = self.get_attribute(attribute_name="out_of_band_ip_mask",
                                             attribute_secondary_name="ip_netmask")
        self.mac_address = self.get_attribute(attribute_name="out_of_band_mac", attribute_secondary_name="mac_address")
        self.model = self.get_attribute(attribute_name="model")
        self.revision = self.get_attribute(attribute_name="revision")
        self.serial = self.get_attribute(attribute_name="serial")
        self.vendor = self.get_attribute(attribute_name="vendor")

        self.sku = None

        # self.expansion_modules = self._get_expansion_modules()
        # self.ports = self._get_ports()
        self.power_supplies = self._get_power_supplies()

        if self._inventory.load_from == "live":
            self.sku = self.model

            self.short_name = self._get_model_short_name()

        elif self._inventory.load_from == "file":
            for attribute in ["short_name", "sku"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

    def _get_model_short_name(self):
        """
        Returns Fabric Interconnect short name from EasyUCS catalog files
        """
        if self.sku is not None:
            # We use the catalog file to get the FI short name
            fi_catalog = read_json_file(file_path="catalog/fabric_interconnects/" + self.sku + ".json", logger=self)
            if fi_catalog:
                if "model_short_name" in fi_catalog:
                    return fi_catalog["model_short_name"]

        return None

    def _get_power_supplies(self):
        if self._inventory.load_from == "live":
            return self.get_inventory_objects_from_ref(ref=self._object.psus, object_class=IntersightPsu, parent=self)
        elif self._inventory.load_from == "file" and "power_supplies" in self._object:
            return [IntersightPsu(self, psu) for psu in self._object["power_supplies"]]
        else:
            return []
