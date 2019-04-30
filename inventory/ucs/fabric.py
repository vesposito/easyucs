# coding: utf-8
# !/usr/bin/env python

""" fabric.py: Easy UCS Deployment Tool """
from __init__ import __author__, __copyright__,  __version__, __status__


from draw.ucs.fabric import UcsSystemDrawFexFront, UcsSystemDrawFexRear, UcsSystemDrawFiRear, UcsSystemDrawFiFront ,UcsSystemDrawGem
from inventory.object import GenericUcsInventoryObject, UcsSystemInventoryObject
from inventory.ucs.port import UcsSystemFexFabricPort, UcsSystemFexHostPort, UcsSystemFiEthPort, UcsSystemFiFcPort
from inventory.ucs.psu import UcsSystemPsu


class UcsFex(GenericUcsInventoryObject):
    _UCS_SDK_OBJECT_NAME = "equipmentFex"

    def __init__(self, parent=None, equipment_fex=None):
        GenericUcsInventoryObject.__init__(self, parent=parent, ucs_sdk_object=equipment_fex)

        self.id = self.get_attribute(ucs_sdk_object=equipment_fex, attribute_name="id")
        self.model = self.get_attribute(ucs_sdk_object=equipment_fex, attribute_name="model")
        self.revision = self.get_attribute(ucs_sdk_object=equipment_fex, attribute_name="revision")
        self.serial = self.get_attribute(ucs_sdk_object=equipment_fex, attribute_name="serial")
        self.switch_id = self.get_attribute(ucs_sdk_object=equipment_fex, attribute_name="switch_id")
        self.vendor = self.get_attribute(ucs_sdk_object=equipment_fex, attribute_name="vendor")

        self.fabric_ports = self._get_fabric_ports()
        self.host_ports = self._get_host_ports()
        self.power_supplies = self._get_power_supplies()

    def _generate_draw(self):
        pass

    def _get_fabric_ports(self):
        return []

    def _get_host_ports(self):
        return []

    def _get_power_supplies(self):
        return []


class UcsFi(GenericUcsInventoryObject):
    _UCS_SDK_OBJECT_NAME = "networkElement"

    def __init__(self, parent=None, network_element=None):
        GenericUcsInventoryObject.__init__(self, parent=parent, ucs_sdk_object=network_element)

        self.id = self.get_attribute(ucs_sdk_object=network_element, attribute_name="id")
        self.model = self.get_attribute(ucs_sdk_object=network_element, attribute_name="model")
        self.revision = self.get_attribute(ucs_sdk_object=network_element, attribute_name="revision")
        self.serial = self.get_attribute(ucs_sdk_object=network_element, attribute_name="serial")
        self.vendor = self.get_attribute(ucs_sdk_object=network_element, attribute_name="vendor")

        self.expansion_modules = self._get_expansion_modules()
        self.ports = self._get_ports()
        self.power_supplies = self._get_power_supplies()

    def _generate_draw(self):
        pass

    def _get_expansion_modules(self):
        return []

    def _get_ports(self):
        return []

    def _get_power_supplies(self):
        return []


class UcsGem(GenericUcsInventoryObject):
    _UCS_SDK_OBJECT_NAME = "equipmentSwitchCard"

    def __init__(self, parent=None, equipment_switch_card=None):
        GenericUcsInventoryObject.__init__(self, parent=parent, ucs_sdk_object=equipment_switch_card)

        self.id = self.get_attribute(ucs_sdk_object=equipment_switch_card, attribute_name="id")
        self.model = self.get_attribute(ucs_sdk_object=equipment_switch_card, attribute_name="model")
        self.revision = self.get_attribute(ucs_sdk_object=equipment_switch_card, attribute_name="revision")
        self.serial = self.get_attribute(ucs_sdk_object=equipment_switch_card, attribute_name="serial")
        self.vendor = self.get_attribute(ucs_sdk_object=equipment_switch_card, attribute_name="vendor")

        self.ports = self._get_ports()

    def _generate_draw(self):
        pass

    def _get_ports(self):
        return []


class UcsSystemFex(UcsFex, UcsSystemInventoryObject):
    _UCS_SDK_CATALOG_OBJECT_NAME = "equipmentFexCapProvider"
    _UCS_SDK_FIRMWARE_RUNNING_SUFFIX = "/slot-1/mgmt/fw-system"

    def __init__(self, parent=None, equipment_fex=None):
        UcsFex.__init__(self, parent=parent, equipment_fex=equipment_fex)
        UcsSystemInventoryObject.__init__(self, parent=parent, ucs_sdk_object=equipment_fex)

    def _generate_draw(self):
        self._draw_rear = UcsSystemDrawFexRear(parent=self)
        self._draw_front = UcsSystemDrawFexFront(parent=self)

    def _get_fabric_ports(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsSystemFexFabricPort,
                                                                  parent=self)
        elif self._inventory.load_from == "file" and "fabric_ports" in self._ucs_sdk_object:
            return [UcsSystemFexFabricPort(self, port) for port in self._ucs_sdk_object["fabric_ports"]]
        else:
            return []

    def _get_host_ports(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsSystemFexHostPort,
                                                                  parent=self)
        elif self._inventory.load_from == "file" and "host_ports" in self._ucs_sdk_object:
            return [UcsSystemFexHostPort(self, port) for port in self._ucs_sdk_object["host_ports"]]
        else:
            return []

    def _get_power_supplies(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsSystemPsu, parent=self)
        elif self._inventory.load_from == "file" and "power_supplies" in self._ucs_sdk_object:
            return [UcsSystemPsu(self, psu) for psu in self._ucs_sdk_object["power_supplies"]]
        else:
            return []


class UcsSystemFi(UcsFi, UcsSystemInventoryObject):
    _UCS_SDK_CATALOG_OBJECT_NAME = "equipmentSwitchCapProvider"
    _UCS_SDK_FIRMWARE_RUNNING_SUFFIX = "/mgmt/fw-system"

    def __init__(self, parent=None, network_element=None):
        UcsFi.__init__(self, parent=parent, network_element=network_element)

        self.ip_address = self.get_attribute(ucs_sdk_object=network_element, attribute_name="oob_if_ip",
                                             attribute_secondary_name="ip_address")
        self.ip_gateway = self.get_attribute(ucs_sdk_object=network_element, attribute_name="oob_if_gw",
                                             attribute_secondary_name="ip_gateway")
        self.ip_netmask = self.get_attribute(ucs_sdk_object=network_element, attribute_name="oob_if_mask",
                                             attribute_secondary_name="ip_netmask")
        self.mac_address = self.get_attribute(ucs_sdk_object=network_element, attribute_name="oob_if_mac",
                                              attribute_secondary_name="mac_address")

        self.locator_led_status = None

        # UCS Mini Fabric Interconnect is a bit different - The CapProvider object needs to be changed
        if self.model == "UCS-FI-M-6324":
            self._UCS_SDK_CATALOG_OBJECT_NAME = "equipmentSwitchIOCardCapProvider"

        UcsSystemInventoryObject.__init__(self, parent=parent, ucs_sdk_object=network_element)

        if self._inventory.load_from == "live":
            self.locator_led_status = self._determine_locator_led_status()
        elif self._inventory.load_from == "file":
            for attribute in ["locator_led_status"]:
                setattr(self, attribute, None)
                if attribute in network_element:
                    setattr(self, attribute, self.get_attribute(ucs_sdk_object=network_element,
                                                                attribute_name=attribute))

    def _generate_draw(self):
        self._draw_rear = UcsSystemDrawFiRear(parent=self)
        if self.model != "UCS-FI-M-6324":
            self._draw_front = UcsSystemDrawFiFront(parent=self)

    def _get_expansion_modules(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsSystemGem, parent=self)
        elif self._inventory.load_from == "file" and "expansion_modules" in self._ucs_sdk_object:
            return [UcsSystemGem(self, gem) for gem in self._ucs_sdk_object["expansion_modules"]]
        else:
            return []

    def _get_ports(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsSystemFiEthPort,
                                                                  parent=self) +\
                   self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsSystemFiFcPort,
                                                                  parent=self)
        elif self._inventory.load_from == "file" and "ports" in self._ucs_sdk_object:
            return [UcsSystemFiEthPort(self, port) for port in self._ucs_sdk_object["ports"] if
                    port["transport"] == "ether"] +\
                   [UcsSystemFiFcPort(self, port) for port in self._ucs_sdk_object["ports"] if
                    port["transport"] == "fc"]
        else:
            return []

    def _get_power_supplies(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsSystemPsu, parent=self)
        elif self._inventory.load_from == "file" and "power_supplies" in self._ucs_sdk_object:
            return [UcsSystemPsu(self, psu) for psu in self._ucs_sdk_object["power_supplies"]]
        else:
            return []


class UcsSystemGem(UcsGem, UcsSystemInventoryObject):
    _UCS_SDK_CATALOG_OBJECT_NAME = "equipmentGemCapProvider"

    def __init__(self, parent=None, equipment_switch_card=None):
        UcsGem.__init__(self, parent=parent, equipment_switch_card=equipment_switch_card)
        UcsSystemInventoryObject.__init__(self, parent=parent, ucs_sdk_object=equipment_switch_card)

    def _generate_draw(self):
        self._draw = UcsSystemDrawGem(parent=self)

    def _get_ports(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsSystemFiEthPort,
                                                                  parent=self) +\
                   self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsSystemFiFcPort,
                                                                  parent=self)
        elif self._inventory.load_from == "file" and "ports" in self._ucs_sdk_object:
            return [UcsSystemFiEthPort(self, port) for port in self._ucs_sdk_object["ports"] if
                    port["transport"] == "ether"] +\
                   [UcsSystemFiFcPort(self, port) for port in self._ucs_sdk_object["ports"] if
                    port["transport"] == "fc"]
        else:
            return []
