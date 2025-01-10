# coding: utf-8
# !/usr/bin/env python

""" adaptor.py: Easy UCS Deployment Tool """

from common import read_json_file
from inventory.generic.adaptor import GenericAdaptor
from inventory.ucs.object import GenericUcsInventoryObject, UcsImcInventoryObject, UcsSystemInventoryObject
from inventory.ucs.port import UcsImcAdaptorPort, UcsImcNetworkAdapterPort, UcsSystemAdaptorPort, \
    UcsSystemNicAdaptorPort


class UcsAdaptor(GenericAdaptor, GenericUcsInventoryObject):
    def __init__(self, parent=None, adaptor_unit=None):
        GenericAdaptor.__init__(self, parent=parent)
        GenericUcsInventoryObject.__init__(self, parent=parent, ucs_sdk_object=adaptor_unit)

        self.model = self.get_attribute(ucs_sdk_object=adaptor_unit, attribute_name="model")

        self.ports = self._get_ports()

    def _get_ports(self):
        return []


class UcsSystemAdaptor(UcsAdaptor, UcsSystemInventoryObject):
    _UCS_SDK_OBJECT_NAME = "adaptorUnit"
    _UCS_SDK_CATALOG_OBJECT_NAME = "adaptorFruCapProvider"
    _UCS_SDK_FIRMWARE_RUNNING_SUFFIX = "/mgmt/fw-system"

    def __init__(self, parent=None, adaptor_unit=None):
        UcsAdaptor.__init__(self, parent=parent, adaptor_unit=adaptor_unit)

        self.blade_id = self.get_attribute(ucs_sdk_object=adaptor_unit, attribute_name="blade_id")
        self.id = self.get_attribute(ucs_sdk_object=adaptor_unit, attribute_name="id")
        self.pci_slot = self.get_attribute(ucs_sdk_object=adaptor_unit, attribute_name="pci_slot")
        self.revision = self.get_attribute(ucs_sdk_object=adaptor_unit, attribute_name="revision")
        self.serial = self.get_attribute(ucs_sdk_object=adaptor_unit, attribute_name="serial")
        self.vendor = self.get_attribute(ucs_sdk_object=adaptor_unit, attribute_name="vendor")

        UcsSystemInventoryObject.__init__(self, parent=parent, ucs_sdk_object=adaptor_unit)

        self.imm_compatible = None
        self.short_name = None
        if self._inventory.load_from == "live":
            self.driver_name_ethernet = None
            self.driver_name_fibre_channel = None
            self.driver_version_ethernet = None
            self.driver_version_fibre_channel = None
            self.short_name = self._get_model_short_name()
            self.imm_compatible = self._get_imm_compatibility()
        elif self._inventory.load_from == "file":
            for attribute in ["driver_name_ethernet", "driver_name_fibre_channel", "driver_version_ethernet",
                              "driver_version_fibre_channel", "imm_compatible", "short_name"]:
                setattr(self, attribute, None)
                if attribute in adaptor_unit:
                    setattr(self, attribute, self.get_attribute(ucs_sdk_object=adaptor_unit, attribute_name=attribute))

    def _get_ports(self):
        if self._inventory.load_from == "live":
            ports = self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsSystemAdaptorPort,
                                                                   parent=self)
            if not ports:
                # In case the ports are not VIC ports, we try with NIC ports instead
                ports = self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsSystemNicAdaptorPort,
                                                                       parent=self)
            return ports
        elif self._inventory.load_from == "file" and "ports" in self._ucs_sdk_object:
            return [UcsSystemAdaptorPort(self, port) for port in self._ucs_sdk_object["ports"]]
        else:
            return []


class UcsSystemAdaptorPortExpander(UcsAdaptor, UcsSystemInventoryObject):
    _UCS_SDK_OBJECT_NAME = "adaptorUnitExtn"
    _UCS_SDK_CATALOG_OBJECT_NAME = "adaptorFruCapProvider"

    def __init__(self, parent=None, adaptor_unit_extn=None):
        UcsAdaptor.__init__(self, parent=parent, adaptor_unit=adaptor_unit_extn)

        self.id = self.get_attribute(ucs_sdk_object=adaptor_unit_extn, attribute_name="id")
        self.revision = self.get_attribute(ucs_sdk_object=adaptor_unit_extn, attribute_name="revision")
        self.serial = self.get_attribute(ucs_sdk_object=adaptor_unit_extn, attribute_name="serial")
        self.vendor = self.get_attribute(ucs_sdk_object=adaptor_unit_extn, attribute_name="vendor")

        UcsSystemInventoryObject.__init__(self, parent=parent, ucs_sdk_object=adaptor_unit_extn)

        self.imm_compatible = None
        self.short_name = None
        if self._inventory.load_from == "live":
            self.short_name = self._get_model_short_name()
            self.imm_compatible = self._get_imm_compatibility()
        elif self._inventory.load_from == "file":
            for attribute in ["imm_compatible", "short_name"]:
                setattr(self, attribute, None)
                if attribute in adaptor_unit_extn:
                    setattr(self, attribute, self.get_attribute(ucs_sdk_object=adaptor_unit_extn,
                                                                attribute_name=attribute))


class UcsImcAdaptor(UcsAdaptor, UcsImcInventoryObject):
    _UCS_SDK_OBJECT_NAME = "adaptorUnit"
    _UCS_SDK_CATALOG_OBJECT_NAME = "pidCatalogPCIAdapter"
    _UCS_SDK_CATALOG_IDENTIFY_ATTRIBUTE = "slot"
    _UCS_SDK_OBJECT_IDENTIFY_ATTRIBUTE = "pci_slot"

    def __init__(self, parent=None, adaptor_unit=None):
        UcsAdaptor.__init__(self, parent=parent, adaptor_unit=adaptor_unit)

        self.id = self.get_attribute(ucs_sdk_object=adaptor_unit, attribute_name="id")
        self.pci_slot = self.get_attribute(ucs_sdk_object=adaptor_unit, attribute_name="pci_slot")
        self.serial = self.get_attribute(ucs_sdk_object=adaptor_unit, attribute_name="serial")
        self.type = "vic"
        self.vendor = self.get_attribute(ucs_sdk_object=adaptor_unit, attribute_name="vendor")

        UcsImcInventoryObject.__init__(self, parent=parent, ucs_sdk_object=adaptor_unit)

        # Small fix for when Adaptor VIC is not present in UCS IMC catalog
        if hasattr(self, "sku"):
            if not self.sku:
                if self.model in ["N2XX-ACPCI01", "UCSC-PCIE-CSC-02", "UCSC-PCIE-C10T-02", "UCSC-MLOM-CSC-02",
                                  "UCSC-MLOM-C10T-02", "UCSC-PCIE-C40Q-02", "UCSC-PCIE-C40Q-03", "UCSC-MLOM-C40Q-03",
                                  "UCSC-PCIE-C25Q-04", "UCSC-MLOM-C25Q-04", "UCSC-M-V25-04", "UCSC-M-V100-04",
                                  "UCSC-PCIE-C100-04", "UCSC-MLOM-C100-04", "UCSC-P-V5Q50G", "UCSC-M-V5Q50G",
                                  "UCSC-P-V5D200G", "UCSC-M-V5D200G"]:
                    self.sku = self.model

        self.short_name = None
        if self._inventory.load_from == "live":
            if not self._find_pci_details():
                self.option_rom_status = None
                self.version = None
            self.short_name = self._get_model_short_name()
        elif self._inventory.load_from == "file":
            for attribute in ["option_rom_status", "short_name", "version"]:
                setattr(self, attribute, None)
                if attribute in adaptor_unit:
                    setattr(self, attribute, self.get_attribute(ucs_sdk_object=adaptor_unit, attribute_name=attribute))

    def _find_pci_details(self):
        # We check if we already have fetched the list of pciEquipSlot objects
        if self._inventory.sdk_objects["pciEquipSlot"] is not None:
            pci_equip_slot_list = [pci_equip_slot for pci_equip_slot in self._inventory.sdk_objects["pciEquipSlot"]
                                   if "sys/rack-unit-" + self._parent.id + "/" in pci_equip_slot.dn
                                   and self.pci_slot == pci_equip_slot.id]

            # We fetch the pciEquipSlot details if there is one and only one pciEquipSlot object in the list
            if len(pci_equip_slot_list) == 1:
                self.option_rom_status = pci_equip_slot_list[0].option_rom_status
                self.version = pci_equip_slot_list[0].version
                if self.sku is None and pci_equip_slot_list[0].pid:
                    self.sku = pci_equip_slot_list[0].pid
                return True

        return False

    def _get_ports(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsImcAdaptorPort,
                                                                  parent=self)
        elif self._inventory.load_from == "file" and "ports" in self._ucs_sdk_object:
            return [UcsImcAdaptorPort(self, port) for port in self._ucs_sdk_object["ports"]]
        else:
            return []


class UcsImcNetworkAdapter(UcsAdaptor, UcsImcInventoryObject):
    _UCS_SDK_OBJECT_NAME = "networkAdapterUnit"
    _UCS_SDK_CATALOG_OBJECT_NAME = "pidCatalogPCIAdapter"
    _UCS_SDK_CATALOG_IDENTIFY_ATTRIBUTE = "slot"
    _UCS_SDK_OBJECT_IDENTIFY_ATTRIBUTE = "pci_slot"

    def __init__(self, parent=None, network_adapter_unit=None):
        UcsAdaptor.__init__(self, parent=parent, adaptor_unit=network_adapter_unit)

        self.pci_slot = self.get_attribute(ucs_sdk_object=network_adapter_unit, attribute_name="slot",
                                           attribute_secondary_name="pci_slot")
        self.num_intf = self.get_attribute(ucs_sdk_object=network_adapter_unit, attribute_name="num_intf")

        UcsImcInventoryObject.__init__(self, parent=parent, ucs_sdk_object=network_adapter_unit)

        self.id = None
        self.short_name = None
        if self._inventory.load_from == "live":
            self.id = self.pci_slot
            if not self._find_pci_details():
                self.option_rom_status = None
                self.vendor = None
                self.version = None

            # We default the interface type to "unknown"
            self.type = "unknown"

            # Handling potentially incomplete UCS catalog entries (when SKU is not found)
            if self.sku not in [None, "NA", "N/A"]:
                # We do not perform this operation for S3260 server node LoM ports since there is no PID for those
                if self.pci_slot not in ["SBLoM1"]:
                    if hasattr(self, "_pid_catalog"):
                        if all(hasattr(self._pid_catalog, attr) for attr in ["vendor", "device", "subvendor",
                                                                             "subdevice"]):
                            vendor = self._pid_catalog.vendor
                            device = self._pid_catalog.device
                            subvendor = self._pid_catalog.subvendor
                            subdevice = self._pid_catalog.subdevice

                            self._determine_adaptor_sku_and_type(vendor=vendor, device=device, subvendor=subvendor,
                                                                 subdevice=subdevice)
            else:
                if self.type == "unknown":
                    self._determine_adaptor_sku_and_type()

            self.short_name = self._get_model_short_name()

        elif self._inventory.load_from == "file":
            for attribute in ["id", "option_rom_status", "short_name", "type", "vendor", "version"]:
                setattr(self, attribute, None)
                if attribute in network_adapter_unit:
                    setattr(self, attribute, self.get_attribute(ucs_sdk_object=network_adapter_unit,
                                                                attribute_name=attribute))

    def _find_pci_details(self):
        # We check if we already have fetched the list of pciEquipSlot objects
        if self._inventory.sdk_objects["pciEquipSlot"] is not None:
            pci_equip_slot_list = [pci_equip_slot for pci_equip_slot in self._inventory.sdk_objects["pciEquipSlot"]
                                   if "sys/rack-unit-" + self._parent.id + "/" in pci_equip_slot.dn
                                   and self.pci_slot == pci_equip_slot.id]

            # We fetch the pciEquipSlot details if there is one and only one pciEquipSlot object in the list
            if len(pci_equip_slot_list) == 1:
                self.option_rom_status = pci_equip_slot_list[0].option_rom_status
                self.vendor = pci_equip_slot_list[0].vendor
                self.version = pci_equip_slot_list[0].version
                if self.sku is None and pci_equip_slot_list[0].pid:
                    self.sku = pci_equip_slot_list[0].pid
                return True

        return False

    def _get_ports(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsImcNetworkAdapterPort,
                                                                  parent=self)
        elif self._inventory.load_from == "file" and "ports" in self._ucs_sdk_object:
            return [UcsImcNetworkAdapterPort(self, port) for port in self._ucs_sdk_object["ports"]]
        else:
            return []


class UcsImcHbaAdapter(UcsAdaptor, UcsImcInventoryObject):
    _UCS_SDK_OBJECT_NAME = "pciEquipSlot"
    _UCS_SDK_CATALOG_OBJECT_NAME = "pidCatalogPCIAdapter"
    _UCS_SDK_CATALOG_IDENTIFY_ATTRIBUTE = "slot"
    _UCS_SDK_OBJECT_IDENTIFY_ATTRIBUTE = "id"

    def __init__(self, parent=None, pci_equip_slot=None):
        UcsAdaptor.__init__(self, parent=parent, adaptor_unit=pci_equip_slot)

        self.id = self.get_attribute(ucs_sdk_object=pci_equip_slot, attribute_name="id")
        self.option_rom_status = self.get_attribute(ucs_sdk_object=pci_equip_slot, attribute_name="option_rom_status")
        self.pci_slot = self.get_attribute(ucs_sdk_object=pci_equip_slot, attribute_name="controller_reported",
                                           attribute_secondary_name="pci_slot")
        self.type = "hba"
        self.vendor = self.get_attribute(ucs_sdk_object=pci_equip_slot, attribute_name="vendor")
        self.version = self.get_attribute(ucs_sdk_object=pci_equip_slot, attribute_name="version")

        UcsImcInventoryObject.__init__(self, parent=parent, ucs_sdk_object=pci_equip_slot)

        self.short_name = None
        if self._inventory.load_from == "live":

            wwpn_info = self._find_adaptor_sku_and_wwpn_info()
            if wwpn_info:
                self.ports = []
                for port_info in wwpn_info.values():
                    self.ports.append(port_info)

            # Handling potentially incomplete UCS catalog entries (when SKU is not found)
            if self.sku is None:
                if hasattr(self, "_pid_catalog"):
                    if all(hasattr(self._pid_catalog, attr) for attr in ["vendor", "device", "subvendor", "subdevice"]):
                        vendor = self._pid_catalog.vendor
                        device = self._pid_catalog.device
                        subvendor = self._pid_catalog.subvendor
                        subdevice = self._pid_catalog.subdevice

                        self._determine_adaptor_sku_and_type(vendor=vendor, device=device, subvendor=subvendor,
                                                             subdevice=subdevice)

            if self.sku is None:
                if pci_equip_slot.pid:
                    self.sku = pci_equip_slot.pid

            self.short_name = self._get_model_short_name()

        elif self._inventory.load_from == "file":
            for attribute in ["short_name"]:
                setattr(self, attribute, None)
                if attribute in pci_equip_slot:
                    setattr(self, attribute, self.get_attribute(ucs_sdk_object=pci_equip_slot,
                                                                attribute_name=attribute))

    def _find_adaptor_sku_and_wwpn_info(self):
        if "pciAdapterFruInventory" not in self._inventory.sdk_objects.keys():
            return None

        # We check if we already have fetched the list of pciAdapterFruInventory objects
        if self._inventory.sdk_objects["pciAdapterFruInventory"] is not None:

            # We need to find the matching pciAdapterFruInventory object
            pci_adapter_fru_inventory_list = [pci_adapter_fru_inventory for pci_adapter_fru_inventory in
                                              self._inventory.sdk_objects["pciAdapterFruInventory"] if
                                              self.pci_slot == pci_adapter_fru_inventory.id]
            if (len(pci_adapter_fru_inventory_list)) != 1:
                self.logger(level="debug",
                            message="Could not find the corresponding pciAdapterFruInventory for object with DN " +
                                    self.dn + " of model \"" + self.model + "\" with ID " + self.id)

                return None
            else:
                if all(hasattr(pci_adapter_fru_inventory_list[0], attr) for attr in ["vendor_id", "device_id",
                                                                                     "sub_vendor_id", "sub_device_id"]):
                    vendor = pci_adapter_fru_inventory_list[0].vendor_id.lower()
                    device = pci_adapter_fru_inventory_list[0].device_id.lower()
                    subvendor = pci_adapter_fru_inventory_list[0].sub_vendor_id.lower()
                    subdevice = pci_adapter_fru_inventory_list[0].sub_device_id.lower()
                    self._determine_adaptor_sku_and_type(vendor=vendor, device=device, subvendor=subvendor,
                                                         subdevice=subdevice)

                    # We check if we already have fetched the list of pciAdapterFruInventoryInfo objects
                    if self._inventory.sdk_objects["pciAdapterFruInventoryInfo"] is not None:

                        # We need to find the matching pciAdapterFruInventoryInfo objects
                        pci_adapter_fru_inventory_info_list = \
                            [pci_adapter_fru_inventory_info for pci_adapter_fru_inventory_info in
                             self._inventory.sdk_objects["pciAdapterFruInventoryInfo"] if
                             pci_adapter_fru_inventory_list[0].dn + "/" in pci_adapter_fru_inventory_info.dn]

                        wwpn_info = {}
                        for fru_inv_info in pci_adapter_fru_inventory_info_list:
                            wwpn_info[fru_inv_info.id] = {"wwpn": fru_inv_info.wwpn,
                                                          "factory_wwpn": fru_inv_info.factory_wwpn,
                                                          "port_id": fru_inv_info.id}

                        if wwpn_info:
                            return wwpn_info

        return None
