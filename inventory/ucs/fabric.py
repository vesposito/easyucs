# coding: utf-8
# !/usr/bin/env python

""" fabric.py: Easy UCS Deployment Tool """

from draw.ucs.fabric import UcsFexDrawFront, UcsFexDrawRear, UcsFiDrawRear, UcsFiDrawFront, \
    UcsSystemDrawGem
from inventory.generic.fabric import GenericFex, GenericFi
from inventory.ucs.object import GenericUcsInventoryObject, UcsSystemInventoryObject
from inventory.ucs.port import UcsSystemFexFabricPort, UcsSystemFexHostPort, UcsSystemFiEthPort, UcsSystemFiFcPort
from inventory.ucs.psu import UcsSystemPsu


class UcsFex(GenericFex, GenericUcsInventoryObject):
    _UCS_SDK_OBJECT_NAME = "equipmentFex"

    def __init__(self, parent=None, equipment_fex=None):
        GenericFex.__init__(self, parent=parent)
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

    def _get_fabric_ports(self):
        return []

    def _get_host_ports(self):
        return []

    def _get_power_supplies(self):
        return []


class UcsFi(GenericFi, GenericUcsInventoryObject):
    _UCS_SDK_OBJECT_NAME = "networkElement"

    def __init__(self, parent=None, network_element=None):
        GenericFi.__init__(self, parent=parent)
        GenericUcsInventoryObject.__init__(self, parent=parent, ucs_sdk_object=network_element)

        self.id = self.get_attribute(ucs_sdk_object=network_element, attribute_name="id")
        self.model = self.get_attribute(ucs_sdk_object=network_element, attribute_name="model")
        self.revision = self.get_attribute(ucs_sdk_object=network_element, attribute_name="revision")
        self.serial = self.get_attribute(ucs_sdk_object=network_element, attribute_name="serial")
        self.vendor = self.get_attribute(ucs_sdk_object=network_element, attribute_name="vendor")

        self.expansion_modules = self._get_expansion_modules()
        self.ports = self._get_ports()
        self.power_supplies = self._get_power_supplies()

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

        self.imm_compatible = None
        self.short_name = None

        UcsSystemInventoryObject.__init__(self, parent=parent, ucs_sdk_object=equipment_fex)

        if self._inventory.load_from == "live":
            self.locator_led_status = self._determine_locator_led_status()
            self.short_name = self._get_model_short_name()
            self.imm_compatible = self._get_imm_compatibility()

            # FEXs do not have a firmware package version info in UCSM. Using the parent FI's package version instead
            if not self.firmware_package_version:
                if hasattr(self._parent, "fabric_interconnects"):
                    for fi in self._parent.fabric_interconnects:
                        if fi.id == self.switch_id:
                            if hasattr(fi, "firmware_package_version"):
                                self.firmware_package_version = fi.firmware_package_version
        elif self._inventory.load_from == "file":
            for attribute in ["imm_compatible", "locator_led_status", "short_name"]:
                setattr(self, attribute, None)
                if attribute in equipment_fex:
                    setattr(self, attribute, self.get_attribute(ucs_sdk_object=equipment_fex,
                                                                attribute_name=attribute))

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

        self.imm_compatible = None
        self.license_host_id = None
        self.licenses = []
        self.locator_led_status = None
        self.short_name = None
        self.vlan_port_count = None

        # UCS Mini/X-Direct Fabric Interconnect is a bit different - The CapProvider object needs to be changed
        if self.model in ["UCS-FI-M-6324", "UCSX-S9108-100G"]:
            self._UCS_SDK_CATALOG_OBJECT_NAME = "equipmentSwitchIOCardCapProvider"

        UcsSystemInventoryObject.__init__(self, parent=parent, ucs_sdk_object=network_element)

        if self._inventory.load_from == "live":
            self.license_host_id = self._get_license_host_id()
            self._get_licenses()
            self._get_vlan_port_count()
            self.locator_led_status = self._determine_locator_led_status()
            self.short_name = self._get_model_short_name()
            self.imm_compatible = self._get_imm_compatibility()
        elif self._inventory.load_from == "file":
            for attribute in ["imm_compatible", "license_host_id", "licenses", "locator_led_status", "short_name",
                              "vlan_port_count"]:
                setattr(self, attribute, None)
                if attribute in network_element:
                    setattr(self, attribute, self.get_attribute(ucs_sdk_object=network_element,
                                                                attribute_name=attribute))

    def _get_expansion_modules(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsSystemGem, parent=self)
        elif self._inventory.load_from == "file" and "expansion_modules" in self._ucs_sdk_object:
            return [UcsSystemGem(self, gem) for gem in self._ucs_sdk_object["expansion_modules"]]
        else:
            return []

    def _get_license_host_id(self):
        if self._inventory.load_from == "live":
            if "licenseServerHostId" in self._inventory.sdk_objects:
                if self._inventory.sdk_objects["licenseServerHostId"] is not None:
                    for license_server_host_id in self._inventory.sdk_objects["licenseServerHostId"]:
                        if license_server_host_id.scope == self.id:
                            return license_server_host_id.host_id
        return None

    def _get_licenses(self):
        if self._inventory.load_from == "live":
            if "licenseInstance" in self._inventory.sdk_objects:
                if self._inventory.sdk_objects["licenseInstance"] is not None:
                    for license_instance in self._inventory.sdk_objects["licenseInstance"]:
                        if license_instance.scope == self.id:
                            self.licenses.append({"feature": license_instance.feature,
                                                  "grace_period_used_days": round(int(
                                                      license_instance.grace_period_used) / 86400),
                                                  "quantity": int(license_instance.abs_quant),
                                                  "quantity_available": int(license_instance.abs_quant) - int(
                                                      license_instance.used_quant),
                                                  "quantity_default": int(license_instance.def_quant),
                                                  "quantity_used": int(license_instance.used_quant),
                                                  "sku": license_instance.sku,
                                                  "status": license_instance.oper_state})

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

    def _get_vlan_port_count(self):
        if self._inventory.load_from == "live":
            if "swVlanPortNs" in self._inventory.sdk_objects:
                if self._inventory.sdk_objects["swVlanPortNs"] is not None:
                    self.vlan_port_count = {}
                    for vlan_port_count_instance in self._inventory.sdk_objects["swVlanPortNs"]:
                        if vlan_port_count_instance.switch_id == self.id:
                            self.vlan_port_count["access_vlan_port_count"] = \
                                vlan_port_count_instance.access_vlan_port_count
                            self.vlan_port_count["border_vlan_port_count"] = \
                                vlan_port_count_instance.border_vlan_port_count
                            self.vlan_port_count["compressed_optimization_sets"] = \
                                vlan_port_count_instance.compressed_optimization_sets
                            self.vlan_port_count["limit"] = vlan_port_count_instance.limit
                            self.vlan_port_count["limit_with_compression"] = \
                                vlan_port_count_instance.vlan_comp_on_limit
                            self.vlan_port_count["total_optimization_sets"] = \
                                vlan_port_count_instance.total_optimization_sets
                            self.vlan_port_count["total_vlan_port_count"] = \
                                vlan_port_count_instance.total_vlan_port_count
                            try:
                                self.vlan_port_count["usage_percent"] = \
                                    str(round(int(vlan_port_count_instance.total_vlan_port_count) /
                                              int(vlan_port_count_instance.limit) * 100, 2))
                            except TypeError:
                                # For releases < 2.2.3a that do not have a value for the total_vlan_port_count attribute
                                self.vlan_port_count["usage_percent"] = None
                            self.vlan_port_count["vlan_compression_state"] = "disabled"
                            if vlan_port_count_instance.vlan_comp_on_limit == vlan_port_count_instance.limit:
                                if self.model not in ["N10-S6100", "N10-S6200", "UCS-FI-M-6324"]:
                                    self.vlan_port_count["vlan_compression_state"] = "enabled"


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
