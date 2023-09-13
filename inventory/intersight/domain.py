# coding: utf-8
# !/usr/bin/env python

""" domain.py: Easy UCS Deployment Tool """

from inventory.intersight.fabric import IntersightFi
from inventory.intersight.object import IntersightInventoryObject


class IntersightUcsmDomain(IntersightInventoryObject):
    def __init__(self, parent=None, top_system=None):
        IntersightInventoryObject.__init__(self, parent=parent, sdk_object=top_system)

        self.ipv4_address = self.get_attribute(attribute_name="ipv4_address")
        self.ipv6_address = self.get_attribute(attribute_name="ipv6_address")
        self.name = self.get_attribute(attribute_name="name")

        self.fabric_interconnects = self._get_fabric_interconnects()

        # if self._inventory.load_from == "live":
        #     print("Live")
        # elif self._inventory.load_from == "file":
        #     for attribute in []:
        #         setattr(self, attribute, None)
        #         if attribute in self._object:
        #             setattr(self, attribute, self.get_attribute(attribute_name=attribute))

    def _get_fabric_interconnects(self):
        if self._inventory.load_from == "live":
            return self.get_inventory_objects_from_ref(ref=self._object.network_elements, object_class=IntersightFi,
                                                       parent=self)
        elif self._inventory.load_from == "file" and "fabric_interconnects" in self._object:
            return [IntersightFi(self, fi) for fi in self._object["fabric_interconnects"]]
        else:
            return []
