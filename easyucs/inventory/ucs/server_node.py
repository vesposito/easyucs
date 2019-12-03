# coding: utf-8
# !/usr/bin/env python

""" chassis.py: Easy UCS Deployment Tool """
from easyucs import __author__, __copyright__,  __version__, __status__

import json

from easyucs.inventory.object import GenericUcsInventoryObject, UcsImcInventoryObject
from easyucs.inventory.ucs.adaptor import UcsImcAdaptor, UcsImcNetworkAdapter
from easyucs.inventory.ucs.cpu import UcsImcCpu
from easyucs.inventory.ucs.gpu import UcsImcGpu
from easyucs.inventory.ucs.memory import UcsImcMemoryArray
from easyucs.inventory.ucs.mgmt import UcsImcMgmtInterface
from easyucs.inventory.ucs.storage import UcsImcStorageController, UcsImcStorageFlexFlashController
from easyucs.inventory.ucs.tpm import UcsImcTpm
from easyucs.inventory.ucs.psu import UcsImcPsu


class UcsServerNode(GenericUcsInventoryObject):
    _UCS_SDK_OBJECT_NAME = "computeServerNode"

    def __init__(self, parent=None, compute_server_node=None):
        GenericUcsInventoryObject.__init__(self, parent=parent, ucs_sdk_object=compute_server_node)

        self.id = self.get_attribute(ucs_sdk_object=compute_server_node, attribute_name="server_id",
                                     attribute_secondary_name="id")
        self.model = self.get_attribute(ucs_sdk_object=compute_server_node, attribute_name="model")
        self.serial = self.get_attribute(ucs_sdk_object=compute_server_node, attribute_name="serial")
        self.vendor = self.get_attribute(ucs_sdk_object=compute_server_node, attribute_name="vendor")

        self.cpus = self._get_cpus()
        self.gpus = self._get_gpus()
        self.memory_arrays = self._get_memory_arrays()
        self.mgmt_interfaces = self._get_mgmt_interfaces()
        self.storage_flexflash_controllers = self._get_storage_flexflash_controllers()
        self.tpms = self._get_tpms()

    def _get_adaptors(self):
        return []

    def _get_cpus(self):
        return []

    def _get_gpus(self):
        return []

    def _get_memory_arrays(self):
        return []

    def _get_mgmt_interfaces(self):
        return []

    def _get_model_short_name(self):
        """
        Returns server node short name from EasyUCS catalog files
        """
        if self.sku is not None:
            # We use the catalog file to get the server node short name
            try:
                json_file = open("catalog/blades/" + self.sku + ".json")
                blade_catalog = json.load(fp=json_file)
                json_file.close()

                if "model_short_name" in blade_catalog:
                    return blade_catalog["model_short_name"]

            except FileNotFoundError:
                if self.sku_scaled:
                    self.logger(level="error", message="Blade catalog file " + self.sku_scaled + ".json not found")
                else:
                    self.logger(level="error", message="Blade catalog file " + self.sku + ".json not found")
                return None

        return None

    def _get_network_adapters(self):
        return []

    def _get_storage_controllers(self):
        return []

    def _get_storage_flexflash_controllers(self):
        return []

    def _get_tpms(self):
        return []


class UcsImcServerNode(UcsServerNode, UcsImcInventoryObject):
    def __init__(self, parent=None, compute_server_node=None):
        UcsServerNode.__init__(self, parent=parent, compute_server_node=compute_server_node)

        self.memory_available = self.get_attribute(ucs_sdk_object=compute_server_node, attribute_name="available_memory",
                                                   attribute_secondary_name="memory_available", attribute_type="int")
        self.memory_total = self.get_attribute(ucs_sdk_object=compute_server_node, attribute_name="total_memory",
                                               attribute_secondary_name="memory_total", attribute_type="int")

        UcsImcInventoryObject.__init__(self, parent=parent, ucs_sdk_object=compute_server_node)

        # Adding a human-readable attribute for memory capacity
        self.memory_total_marketing = None
        if self.memory_total:
            if self.memory_total / 1024 < 1024:
                memory_total_gb = str(self.memory_total / 1024)
                memory_total_gb = memory_total_gb.rstrip('0').rstrip('.') if '.' in memory_total_gb else memory_total_gb
                self.memory_total_marketing = memory_total_gb + " GB"
            else:
                memory_total_tb = str(self.memory_total / 1048576)
                memory_total_tb = memory_total_tb.rstrip('0').rstrip('.') if '.' in memory_total_tb else memory_total_tb
                self.memory_total_marketing = memory_total_tb + " TB"

        # Since we don't have a catalog item for finding the SKU, we set it manually here
        self.sku = self.model

        # We copy id to slot_id for coherency, since slot_id exists for Blade objects in UCSM but not for Server Node
        # objects in IMC, and S3260 server nodes are displayed as Blades in UCSM
        self.slot_id = self.id

        self.locator_led_status = None

        self.short_name = self._get_model_short_name()

        self.adaptors = self._get_adaptors() + self._get_network_adapters()
        self.storage_controllers = self._get_storage_controllers()

        self.os_arch = None
        self.os_kernel_version = None
        self.os_patch_version = None
        self.os_release_version = None
        self.os_type = None
        self.os_ucs_tool_version = None
        self.os_update_version = None
        self.os_vendor = None
        if self._inventory.load_from == "live":
            self.locator_led_status = self._determine_locator_led_status()
            self._get_os_details()

        elif self._inventory.load_from == "file":
            for attribute in ["locator_led_status", "os_arch", "os_kernel_version", "os_patch_version",
                              "os_release_version", "os_type", "os_ucs_tool_version", "os_update_version", "os_vendor"]:
                setattr(self, attribute, None)
                if attribute in compute_server_node:
                    setattr(self, attribute, self.get_attribute(ucs_sdk_object=compute_server_node,
                                                                attribute_name=attribute))

    def _get_adaptors(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsImcAdaptor, parent=self)
        elif self._inventory.load_from == "file" and "adaptors" in self._ucs_sdk_object:
            return [UcsImcAdaptor(self, adaptor_unit) for adaptor_unit in self._ucs_sdk_object["adaptors"]
                    if adaptor_unit["type"] == "vic"]
        else:
            return []

    def _get_cpus(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsImcCpu, parent=self)
        elif self._inventory.load_from == "file" and "cpus" in self._ucs_sdk_object:
            return [UcsImcCpu(self, cpu) for cpu in self._ucs_sdk_object["cpus"]]
        else:
            return []

    def _get_gpus(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsImcGpu, parent=self)
        elif self._inventory.load_from == "file" and "gpus" in self._ucs_sdk_object:
            return [UcsImcGpu(self, gpu) for gpu in self._ucs_sdk_object["gpus"]]
        else:
            return []

    def _get_memory_arrays(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsImcMemoryArray,
                                                                  parent=self)
        elif self._inventory.load_from == "file" and "memory_arrays" in self._ucs_sdk_object:
            return [UcsImcMemoryArray(self, memory_array) for memory_array in self._ucs_sdk_object["memory_arrays"]]
        else:
            return []

    def _get_mgmt_interfaces(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn + "/mgmt",
                                                                  object_class=UcsImcMgmtInterface, parent=self)
        elif self._inventory.load_from == "file" and "mgmt_interfaces" in self._ucs_sdk_object:
            return [UcsImcMgmtInterface(self, mgmt_if) for mgmt_if in self._ucs_sdk_object["mgmt_interfaces"]]
        else:
            return []

    def _get_network_adapters(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsImcNetworkAdapter,
                                                                  parent=self)
        elif self._inventory.load_from == "file" and "adaptors" in self._ucs_sdk_object:
            return [UcsImcNetworkAdapter(self, network_adapter_unit) for network_adapter_unit in
                    self._ucs_sdk_object["adaptors"] if network_adapter_unit["type"] in ["nic", "cna"]]
        else:
            return []

    def _get_os_details(self):
        # We check if we already have fetched the list of moInvKv objects
        if "moInvKv" not in self._inventory.sdk_objects:
            return False
        if self._inventory.sdk_objects["moInvKv"] is not None:
            # We need to filter out moInvKv objects that are not for this server node id
            mo_inv_kv_list = [mo_inv_kv for mo_inv_kv in self._inventory.sdk_objects["moInvKv"]
                              if "sys/chassis-" + self.chassis_id + "/server-" + self.id + "/inv-kv-hostOs/" in
                              mo_inv_kv.dn]
            if len(mo_inv_kv_list) > 0:
                self.logger(level="debug", message="Found " + str(len(mo_inv_kv_list)) +
                                                   " ucs-tools inventory elements for server node " + self.id)

            # We set the list of attributes from the various moInvKv objects attached to this server node id
            ucs_drivers = {}
            for mo_inv_kv in mo_inv_kv_list:
                if hasattr(mo_inv_kv, "key") and hasattr(mo_inv_kv, "value"):
                    if mo_inv_kv.key == "os.arch" and mo_inv_kv.value != "":
                        self.os_arch = mo_inv_kv.value
                    if mo_inv_kv.key == "os.kernelVersionString" and mo_inv_kv.value != "":
                        self.os_kernel_version = mo_inv_kv.value
                    if mo_inv_kv.key == "os.patchVersionString" and mo_inv_kv.value != "":
                        self.os_patch_version = mo_inv_kv.value
                    if mo_inv_kv.key == "os.releaseVersionString" and mo_inv_kv.value != "":
                        self.os_release_version = mo_inv_kv.value
                    if mo_inv_kv.key == "os.type" and mo_inv_kv.value != "":
                        self.os_type = mo_inv_kv.value
                    if mo_inv_kv.key == "os.ucsToolVersion" and mo_inv_kv.value != "":
                        self.os_ucs_tool_version = mo_inv_kv.value
                    if mo_inv_kv.key == "os.updateVersionString" and mo_inv_kv.value != "":
                        self.os_update_version = mo_inv_kv.value
                    if mo_inv_kv.key == "os.vendor" and mo_inv_kv.value != "":
                        self.os_vendor = mo_inv_kv.value

                    if "os.driver" in mo_inv_kv.key:
                        driver_key_string = mo_inv_kv.key.split(".")
                        if driver_key_string[-2] not in ucs_drivers.keys():
                            ucs_drivers[driver_key_string[-2]] = {"description": None, "name": None, "version": None}

                        if driver_key_string[-1] in ["name", "description", "version"]:
                            ucs_drivers[driver_key_string[-2]][driver_key_string[-1]] = mo_inv_kv.value

            # We loop through the UCS drivers to set adaptor & storage controller driver versions in associated objects
            for identifier in ucs_drivers.keys():
                current_driver = ucs_drivers[identifier]

                # UCS VIC Ethernet driver
                if current_driver["name"] in ["enic", "nenic"]:
                    # Finding the associated adaptors to set driver versions
                    for adaptor in self.adaptors:
                        if adaptor.sku in ["UCSB-MLOM-40G-01", "UCSB-MLOM-40G-03", "UCSC-MLOM-C10T-02",
                                           "UCSC-MLOM-C40Q-03", "UCSC-MLOM-CSC-02", "UCSC-PCIE-C10T-02",
                                           "UCSC-PCIE-C40Q-02", "UCSC-PCIE-C40Q-03", "UCSC-PCIE-CSC-02",
                                           "UCS-VIC-M82-8P"]:
                            adaptor.driver_name_ethernet = current_driver["name"]
                            adaptor.driver_version_ethernet = current_driver["version"]
                            self.logger(level="debug",
                                        message="Found Ethernet VIC driver (" + current_driver["name"] + ") version " +
                                                current_driver["version"] + " for adaptor " + adaptor.id +
                                                " of server node " + self.id)

                # UCS VIC Fibre Channel driver
                if current_driver["name"] in ["fnic"]:
                    # Finding the associated adaptors to set driver versions
                    for adaptor in self.adaptors:
                        if adaptor.sku in ["UCSB-MLOM-40G-01", "UCSB-MLOM-40G-03", "UCSC-MLOM-C10T-02",
                                           "UCSC-MLOM-C40Q-03", "UCSC-MLOM-CSC-02", "UCSC-PCIE-C10T-02",
                                           "UCSC-PCIE-C40Q-02", "UCSC-PCIE-C40Q-03", "UCSC-PCIE-CSC-02",
                                           "UCS-VIC-M82-8P"]:
                            adaptor.driver_name_fibre_channel = current_driver["name"]
                            adaptor.driver_version_fibre_channel = current_driver["version"]
                            self.logger(level="debug",
                                        message="Found Fibre Channel VIC driver (" + current_driver["name"] +
                                                ") version " + current_driver["version"] + " for adaptor " +
                                                adaptor.id + " of server node " + self.id)

                # Avago/LSI MegaRAID SAS driver
                if current_driver["name"] in ["lsi_mr3", "megaraid_sas"]:
                    # Finding the associated storage controllers to set driver versions
                    for storage_controller in self.storage_controllers:
                        if any(x in storage_controller.name for x in ["MegaRAID", "FlexStorage"]):
                            storage_controller.driver_name = current_driver["name"]
                            storage_controller.driver_version = current_driver["version"]
                            self.logger(level="debug",
                                        message="Found Storage controller driver (" + current_driver["name"] +
                                                ") version " + current_driver["version"] + " for storage controller " +
                                                storage_controller.id + " of server node " + self.id)

            return True
        else:
            return False

    def _get_storage_controllers(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsImcStorageController,
                                                                  parent=self)
        elif self._inventory.load_from == "file" and "storage_controllers" in self._ucs_sdk_object:
            return [UcsImcStorageController(self, storage_controller) for storage_controller in
                    self._ucs_sdk_object["storage_controllers"]]
        else:
            return []

    def _get_storage_flexflash_controllers(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn,
                                                                  object_class=UcsImcStorageFlexFlashController,
                                                                  parent=self)
        elif self._inventory.load_from == "file" and "storage_flexflash_controllers" in self._ucs_sdk_object:
            return [UcsImcStorageFlexFlashController(self, storage_flexflash_controller) for
                    storage_flexflash_controller in self._ucs_sdk_object["storage_flexflash_controllers"]]
        else:
            return []

    def _get_tpms(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsImcTpm, parent=self)
        elif self._inventory.load_from == "file" and "tpms" in self._ucs_sdk_object:
            return [UcsImcTpm(self, tpm) for tpm in self._ucs_sdk_object["tpms"]]
        else:
            return []
