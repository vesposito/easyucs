# coding: utf-8
# !/usr/bin/env python

""" chassis.py: Easy UCS Deployment Tool """
from easyucs import __author__, __copyright__,  __version__, __status__


import json

from easyucs.inventory.object import GenericUcsInventoryObject, UcsSystemInventoryObject
from easyucs.inventory.ucs.adaptor import UcsSystemAdaptor
from easyucs.inventory.ucs.cpu import UcsSystemCpu
from easyucs.inventory.ucs.gpu import UcsSystemGpu
from easyucs.inventory.ucs.memory import UcsSystemMemoryArray
from easyucs.inventory.ucs.mgmt import UcsSystemMgmtInterface
from easyucs.inventory.ucs.storage import UcsSystemStorageController, UcsSystemStorageControllerNvmeDrive,\
    UcsSystemStorageFlexFlashController, UcsSystemStorageEnclosure
from easyucs.inventory.ucs.tpm import UcsSystemTpm
from easyucs.inventory.ucs.psu import UcsSystemPsu


class UcsBlade(GenericUcsInventoryObject):
    _UCS_SDK_OBJECT_NAME = "computeBlade"

    def __init__(self, parent=None, compute_blade=None):
        GenericUcsInventoryObject.__init__(self, parent=parent, ucs_sdk_object=compute_blade)

        self.model = self.get_attribute(ucs_sdk_object=compute_blade, attribute_name="model")
        self.revision = self.get_attribute(ucs_sdk_object=compute_blade, attribute_name="revision")
        self.serial = self.get_attribute(ucs_sdk_object=compute_blade, attribute_name="serial")
        self.slot_id = self.get_attribute(ucs_sdk_object=compute_blade, attribute_name="slot_id")
        self.user_label = self.get_attribute(ucs_sdk_object=compute_blade, attribute_name="usr_lbl",
                                             attribute_secondary_name="user_label")
        self.vendor = self.get_attribute(ucs_sdk_object=compute_blade, attribute_name="vendor")

        self.adaptors = self._get_adaptors()
        self.cpus = self._get_cpus()
        self.gpus = self._get_gpus()
        self.memory_arrays = self._get_memory_arrays()
        self.mgmt_interfaces = self._get_mgmt_interfaces()
        self.nvme_drives = self._get_nvme_drives()
        self.storage_controllers = self._get_storage_controllers()
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
        Returns blade server short name from EasyUCS catalog files
        """
        if self.sku is not None:
            # We use the catalog file to get the blade short name
            try:
                if self.sku_scaled:
                    json_file = open("catalog/blades/" + self.sku_scaled + ".json")
                else:
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

    def _get_nvme_drives(self):
        return []

    def _get_storage_controllers(self):
        return []

    def _get_storage_flexflash_controllers(self):
        return []

    def _get_tpms(self):
        return []


class UcsSystemBlade(UcsBlade, UcsSystemInventoryObject):
    _UCS_SDK_CATALOG_OBJECT_NAME = "equipmentBladeCapProvider"
    _UCS_SDK_FIRMWARE_RUNNING_SUFFIX = "/mgmt/fw-system"

    def __init__(self, parent=None, compute_blade=None):
        UcsBlade.__init__(self, parent=parent, compute_blade=compute_blade)

        self.assigned_to_dn = self.get_attribute(ucs_sdk_object=compute_blade, attribute_name="assigned_to_dn")
        self.association = self.get_attribute(ucs_sdk_object=compute_blade, attribute_name="association")
        self.chassis_id = self.get_attribute(ucs_sdk_object=compute_blade, attribute_name="chassis_id")
        self.id = self.get_attribute(ucs_sdk_object=compute_blade, attribute_name="server_id",
                                     attribute_secondary_name="id")
        self.memory_available = self.get_attribute(ucs_sdk_object=compute_blade, attribute_name="available_memory",
                                                   attribute_secondary_name="memory_available", attribute_type="int")
        self.memory_total = self.get_attribute(ucs_sdk_object=compute_blade, attribute_name="total_memory",
                                               attribute_secondary_name="memory_total", attribute_type="int")
        self.scaled_mode = self.get_attribute(ucs_sdk_object=compute_blade, attribute_name="scaled_mode")

        UcsSystemInventoryObject.__init__(self, parent=parent, ucs_sdk_object=compute_blade)

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

        self.locator_led_status = None
        self.os_arch = None
        self.os_kernel_version = None
        self.os_patch_version = None
        self.os_release_version = None
        self.os_type = None
        self.os_ucs_tool_version = None
        self.os_update_version = None
        self.os_vendor = None
        self.service_profile_org = None
        self.service_profile_name = None
        self.service_profile_template = None
        self.service_profile_template_org = None
        self.service_profile_template_name = None
        self.short_name = None
        self.sku_scaled = None
        if self._inventory.load_from == "live":
            # Handle specific case of SKU for B260 M4 / B460 M4
            if self.scaled_mode is not None:
                if self.scaled_mode == "single":
                    self.sku_scaled = self.sku + "C"
                elif self.scaled_mode == "scaled":
                    self.sku_scaled = self.sku + "A"

            self.short_name = self._get_model_short_name()
            self.locator_led_status = self._determine_locator_led_status()
            self._get_os_details()
            if self.assigned_to_dn is not None and self.assigned_to_dn != "":
                self.service_profile_org = self.assigned_to_dn.split("/ls-")[0]
                self.service_profile_name = self.assigned_to_dn.split("/")[-1].split("ls-")[-1]
                self.service_profile_template = self._get_service_profile_template()
                if self.service_profile_template is not None and self.service_profile_template != "" and \
                        "org" in self.service_profile_template:
                    self.service_profile_template_org = self.service_profile_template.split("/ls-")[0]
                    self.service_profile_template_name = self.service_profile_template.split("/")[-1].split("ls-")[-1]
                elif self.service_profile_template is not None and self.service_profile_template != "":
                    self.service_profile_template_org = "UCS Central"
                    self.service_profile_template_name = self.service_profile_template
                else:
                    self.service_profile_template = None
            else:
                self.assigned_to_dn = None

        elif self._inventory.load_from == "file":
            for attribute in ["locator_led_status", "os_arch", "os_kernel_version", "os_patch_version",
                              "os_release_version", "os_type", "os_ucs_tool_version", "os_update_version", "os_vendor",
                              "service_profile_org", "service_profile_name", "service_profile_template",
                              "service_profile_template_org", "service_profile_template_name", "short_name",
                              "sku_scaled"]:
                setattr(self, attribute, None)
                if attribute in compute_blade:
                    setattr(self, attribute, self.get_attribute(ucs_sdk_object=compute_blade,
                                                                attribute_name=attribute))

    def _get_adaptors(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsSystemAdaptor,
                                                                  parent=self)
        elif self._inventory.load_from == "file" and "adaptors" in self._ucs_sdk_object:
            return [UcsSystemAdaptor(self, adaptor) for adaptor in self._ucs_sdk_object["adaptors"]]
        else:
            return []

    def _get_cpus(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsSystemCpu, parent=self)
        elif self._inventory.load_from == "file" and "cpus" in self._ucs_sdk_object:
            return [UcsSystemCpu(self, cpu) for cpu in self._ucs_sdk_object["cpus"]]
        else:
            return []

    def _get_gpus(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsSystemGpu, parent=self)
        elif self._inventory.load_from == "file" and "gpus" in self._ucs_sdk_object:
            return [UcsSystemGpu(self, gpu) for gpu in self._ucs_sdk_object["gpus"]]
        else:
            return []

    def _get_memory_arrays(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsSystemMemoryArray,
                                                                  parent=self)
        elif self._inventory.load_from == "file" and "memory_arrays" in self._ucs_sdk_object:
            return [UcsSystemMemoryArray(self, memory_array) for memory_array in
                    self._ucs_sdk_object["memory_arrays"]]
        else:
            return []

    def _get_mgmt_interfaces(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn + "/mgmt",
                                                                  object_class=UcsSystemMgmtInterface, parent=self)
        elif self._inventory.load_from == "file" and "mgmt_interfaces" in self._ucs_sdk_object:
            return [UcsSystemMgmtInterface(self, mgmt_if) for mgmt_if in self._ucs_sdk_object["mgmt_interfaces"]]
        else:
            return []

    def _get_nvme_drives(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn,
                                                                  object_class=UcsSystemStorageControllerNvmeDrive,
                                                                  parent=self)
        elif self._inventory.load_from == "file" and "nvme_drives" in self._ucs_sdk_object:
            return [UcsSystemStorageControllerNvmeDrive(self, nvme_drive) for nvme_drive in
                    self._ucs_sdk_object["nvme_drives"]]
        else:
            return []

    def _get_os_details(self):
        # We check if we already have fetched the list of moInvKv objects
        if "moInvKv" not in self._inventory.sdk_objects:
            return False
        if self._inventory.sdk_objects["moInvKv"] is not None:
            # We need to filter out moInvKv objects that are not for this blade id
            mo_inv_kv_list = [mo_inv_kv for mo_inv_kv in self._inventory.sdk_objects["moInvKv"]
                              if "sys/chassis-" + self.chassis_id + "/blade-" + self.slot_id + "/inv-kv-hostOs/" in
                              mo_inv_kv.dn]
            if len(mo_inv_kv_list) > 0:
                self.logger(level="debug", message="Found " + str(len(mo_inv_kv_list)) +
                                                   " ucs-tools inventory elements for blade " + self.id)

            # We set the list of attributes from the various moInvKv objects attached to this blade id
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
                        if adaptor.sku in [
                            "UCSB-MLOM-40G-01",  # VIC 1240
                            "UCS-VIC-M82-8P",  # VIC 1280
                            "UCSB-MLOM-40G-03",  # VIC 1340
                            "UCSB-VIC-M83-8P",  # VIC 1380
                            "UCSB-MLOM-40G-04",  # VIC 1440
                            "UCSB-VIC-M84-4P",  # VIC 1480
                            "UCSC-PCIE-CSC-02",  # VIC 1225
                            "UCSC-PCIE-C10T-02",  # VIC 1225T
                            "UCSC-MLOM-CSC-02",  # VIC 1227
                            "UCSC-MLOM-C10T-02",  # VIC 1227T
                            "UCSC-PCIE-C40Q-02",  # VIC 1285
                            "UCSC-PCIE-C40Q-03",  # VIC 1385
                            "UCSC-MLOM-C40Q-03",  # VIC 1387
                            "UCSC-PCIE-C25Q-04",  # VIC 1455
                            "UCSC-MLOM-C25Q-04",  # VIC 1457
                            "UCSC-PCIE-C100-04",  # VIC 1485
                            "UCSC-MLOM-C100-04"  # VIC 1487
                        ]:
                            adaptor.driver_name_ethernet = current_driver["name"]
                            adaptor.driver_version_ethernet = current_driver["version"]
                            self.logger(level="debug",
                                        message="Found Ethernet VIC driver (" + str(current_driver["name"]) +
                                                ") version " + str(current_driver["version"]) + " for adaptor " +
                                                str(adaptor.id) + " of blade " + str(self.id))

                # UCS VIC Fibre Channel driver
                if current_driver["name"] in ["fnic", "nfnic"]:
                    # Finding the associated adaptors to set driver versions
                    for adaptor in self.adaptors:
                        if adaptor.sku in [
                            "UCSB-MLOM-40G-01",  # VIC 1240
                            "UCS-VIC-M82-8P",  # VIC 1280
                            "UCSB-MLOM-40G-03",  # VIC 1340
                            "UCSB-VIC-M83-8P",  # VIC 1380
                            "UCSB-MLOM-40G-04",  # VIC 1440
                            "UCSB-VIC-M84-4P",  # VIC 1480
                            "UCSC-PCIE-CSC-02",  # VIC 1225
                            "UCSC-PCIE-C10T-02",  # VIC 1225T
                            "UCSC-MLOM-CSC-02",  # VIC 1227
                            "UCSC-MLOM-C10T-02",  # VIC 1227T
                            "UCSC-PCIE-C40Q-02",  # VIC 1285
                            "UCSC-PCIE-C40Q-03",  # VIC 1385
                            "UCSC-MLOM-C40Q-03",  # VIC 1387
                            "UCSC-PCIE-C25Q-04",  # VIC 1455
                            "UCSC-MLOM-C25Q-04",  # VIC 1457
                            "UCSC-PCIE-C100-04",  # VIC 1485
                            "UCSC-MLOM-C100-04"  # VIC 1487
                        ]:
                            adaptor.driver_name_fibre_channel = current_driver["name"]
                            adaptor.driver_version_fibre_channel = current_driver["version"]
                            self.logger(level="debug",
                                        message="Found Fibre Channel VIC driver (" + str(current_driver["name"]) +
                                                ") version " + str(current_driver["version"]) + " for adaptor " +
                                                str(adaptor.id) + " of blade " + str(self.id))

                # Avago/LSI MegaRAID SAS driver
                if current_driver["name"] in ["lsi_mr3", "megaraid_sas"]:
                    # Finding the associated storage controllers to set driver versions
                    for storage_controller in self.storage_controllers:
                        if any(x in storage_controller.name for x in ["MegaRAID", "FlexStorage"]):
                            storage_controller.driver_name = current_driver["name"]
                            storage_controller.driver_version = current_driver["version"]
                            self.logger(level="debug",
                                        message="Found Storage controller driver (" + str(current_driver["name"]) +
                                                ") version " + str(current_driver["version"]) +
                                                " for storage controller " + str(storage_controller.id) +
                                                " of blade " + str(self.id))

            return True
        else:
            return False

    def _get_service_profile_template(self):
        # We check if we already have fetched the list of lsServer objects
        if self._inventory.sdk_objects["lsServer"] is not None:
            # We need to filter out lsServer objects that are not for this blade id
            ls_server_list = [ls_server for ls_server in self._inventory.sdk_objects["lsServer"]
                              if ls_server.pn_dn == "sys/chassis-" + self.chassis_id + "/blade-" + self.slot_id]

            # We return the SP Template name only if we have a single element in ls_server_list
            if len(ls_server_list) != 1:
                return None
            else:
                # If operSrcTemplName is empty, we use srcTemplName (useful for Template coming from UCS Central):
                if ls_server_list[0].oper_src_templ_name != "":
                    return ls_server_list[0].oper_src_templ_name
                elif ls_server_list[0].src_templ_name != "":
                    return ls_server_list[0].src_templ_name
        return None

    def _get_storage_controllers(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsSystemStorageController,
                                                                  parent=self)
        elif self._inventory.load_from == "file" and "storage_controllers" in self._ucs_sdk_object:
            return [UcsSystemStorageController(self, storage_controller) for storage_controller in
                    self._ucs_sdk_object["storage_controllers"]]
        else:
            return []

    def _get_storage_flexflash_controllers(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn,
                                                                  object_class=UcsSystemStorageFlexFlashController,
                                                                  parent=self)
        elif self._inventory.load_from == "file" and "storage_flexflash_controllers" in self._ucs_sdk_object:
            return [UcsSystemStorageFlexFlashController(self, storage_flexflash_controller) for
                    storage_flexflash_controller in self._ucs_sdk_object["storage_flexflash_controllers"]]
        else:
            return []

    def _get_tpms(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsSystemTpm, parent=self)
        elif self._inventory.load_from == "file" and "tpms" in self._ucs_sdk_object:
            return [UcsSystemTpm(self, tpm) for tpm in self._ucs_sdk_object["tpms"]]
        else:
            return []
