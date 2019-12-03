# coding: utf-8
# !/usr/bin/env python

""" domain.py: Easy UCS Deployment Tool """
from easyucs import __author__, __copyright__,  __version__, __status__


import json

from easyucs.inventory.object import GenericUcsInventoryObject, UcsCentralInventoryObject
from easyucs.inventory.ucs.chassis import UcsSystemChassis
from easyucs.inventory.ucs.fabric import UcsSystemFex, UcsSystemFi
from easyucs.inventory.ucs.rack import UcsSystemRack


class UcsDomain(GenericUcsInventoryObject):
    _UCS_SDK_OBJECT_NAME = "computeSystem"

    def __init__(self, parent=None, compute_system=None):
        GenericUcsInventoryObject.__init__(self, parent=parent, ucs_sdk_object=compute_system)

        self.id = self.get_attribute(ucs_sdk_object=compute_system, attribute_name="id")


class UcsCentralDomain(UcsDomain, UcsCentralInventoryObject):
    def __init__(self, parent=None, compute_system=None):
        UcsDomain.__init__(self, parent=parent, compute_system=compute_system)

        self.address = self.get_attribute(ucs_sdk_object=compute_system, attribute_name="address")
        self.assigned_domain_group = self.get_attribute(ucs_sdk_object=compute_system, attribute_name="oper_group_dn",
                                                        attribute_secondary_name="assigned_domain_group")
        self.descr = self.get_attribute(ucs_sdk_object=compute_system, attribute_name="descr")
        self.product_family = self.get_attribute(ucs_sdk_object=compute_system, attribute_name="product_family")
        self.servers_available = self.get_attribute(ucs_sdk_object=compute_system,
                                                    attribute_name="available_physical_cnt",
                                                    attribute_secondary_name="servers_available")
        self.servers_total = self.get_attribute(ucs_sdk_object=compute_system, attribute_name="total_physical_cnt",
                                                attribute_secondary_name="servers_total")
        self.site = self.get_attribute(ucs_sdk_object=compute_system, attribute_name="site")

        UcsCentralInventoryObject.__init__(self, parent=parent, ucs_sdk_object=compute_system)

        self.firmware_package_version = self.get_attribute(ucs_sdk_object=compute_system,
                                                           attribute_name="fw_package_version")
        self.name = self.get_attribute(ucs_sdk_object=compute_system, attribute_name="name")

        self.chassis = self._get_chassis()
        self.fabric_extenders = self._get_fabric_extenders()
        self.fabric_interconnects = self._get_fabric_interconnects()
        self.rack_units = self._get_rack_units()

        if self._inventory.load_from == "live":
            pass

        elif self._inventory.load_from == "file":
            for attribute in ["firmware_package_version", "name"]:
                setattr(self, attribute, None)
                if attribute in compute_system:
                    setattr(self, attribute, self.get_attribute(ucs_sdk_object=compute_system,
                                                                attribute_name=attribute))

    def _get_chassis(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsSystemChassis,
                                                                  parent=self)
        elif self._inventory.load_from == "file" and "chassis" in self._ucs_sdk_object:
            return [UcsSystemChassis(self, chassis) for chassis in self._ucs_sdk_object["chassis"]]
        else:
            return []

    def _get_fabric_extenders(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsSystemFex, parent=self)
        elif self._inventory.load_from == "file" and "fabric_extenders" in self._ucs_sdk_object:
            return [UcsSystemFex(self, fex) for fex in self._ucs_sdk_object["fabric_extenders"]]
        else:
            return []

    def _get_fabric_interconnects(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsSystemFi, parent=self)
        elif self._inventory.load_from == "file" and "fabric_interconnects" in self._ucs_sdk_object:
            return [UcsSystemFi(self, fi) for fi in self._ucs_sdk_object["fabric_interconnects"]]
        else:
            return []

    def _get_rack_units(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsSystemRack, parent=self)
        elif self._inventory.load_from == "file" and "rack_units" in self._ucs_sdk_object:
            return [UcsSystemRack(self, rack_unit) for rack_unit in self._ucs_sdk_object["rack_units"]]
        else:
            return []
