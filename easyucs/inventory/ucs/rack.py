# coding: utf-8
# !/usr/bin/env python

""" rack.py: Easy UCS Deployment Tool """
from easyucs import __author__, __copyright__,  __version__, __status__

import json

from easyucs.inventory.object import GenericUcsInventoryObject, UcsImcInventoryObject, UcsSystemInventoryObject
from easyucs.inventory.ucs.adaptor import UcsImcAdaptor, UcsImcNetworkAdapter, UcsSystemAdaptor
from easyucs.inventory.ucs.cpu import UcsImcCpu, UcsSystemCpu
from easyucs.inventory.ucs.gpu import UcsImcGpu, UcsSystemGpu
from easyucs.inventory.ucs.memory import UcsImcMemoryArray, UcsSystemMemoryArray
from easyucs.inventory.ucs.mgmt import UcsImcMgmtInterface, UcsSystemMgmtInterface
from easyucs.inventory.ucs.psu import UcsImcPsu, UcsSystemPsu
from easyucs.inventory.ucs.storage import UcsImcStorageController, UcsImcStorageFlexFlashController,\
    UcsImcStorageControllerNvmeDrive, UcsImcStorageNvmeDrive, UcsSystemStorageController,\
    UcsSystemStorageControllerNvmeDrive, UcsSystemStorageFlexFlashController
from easyucs.inventory.ucs.tpm import UcsImcTpm, UcsSystemTpm
from easyucs.draw.ucs.rack import UcsSystemDrawRackFront, UcsSystemDrawRackRear, UcsImcDrawRackFront, UcsImcDrawRackRear, UcsSystemDrawRackEnclosureFront, UcsSystemDrawRackEnclosureRear, UcsImcDrawRackEnclosureFront, UcsImcDrawRackEnclosureRear


class UcsRack(GenericUcsInventoryObject):
    _UCS_SDK_OBJECT_NAME = "computeRackUnit"

    def __init__(self, parent=None, compute_rack_unit=None):
        GenericUcsInventoryObject.__init__(self, parent=parent, ucs_sdk_object=compute_rack_unit)

        self.id = self.get_attribute(ucs_sdk_object=compute_rack_unit, attribute_name="server_id",
                                     attribute_secondary_name="id")
        self.memory_available = self.get_attribute(ucs_sdk_object=compute_rack_unit, attribute_name="available_memory",
                                                   attribute_secondary_name="memory_available", attribute_type="int")
        self.memory_speed = self.get_attribute(ucs_sdk_object=compute_rack_unit, attribute_name="memory_speed",
                                               attribute_type="int")
        self.memory_total = self.get_attribute(ucs_sdk_object=compute_rack_unit, attribute_name="total_memory",
                                               attribute_secondary_name="memory_total", attribute_type="int")
        self.model = self.get_attribute(ucs_sdk_object=compute_rack_unit, attribute_name="model")
        self.serial = self.get_attribute(ucs_sdk_object=compute_rack_unit, attribute_name="serial")
        self.slot_id = self.get_attribute(ucs_sdk_object=compute_rack_unit, attribute_name="slot_id")
        self.user_label = self.get_attribute(ucs_sdk_object=compute_rack_unit, attribute_name="usr_lbl",
                                             attribute_secondary_name="user_label")
        self.vendor = self.get_attribute(ucs_sdk_object=compute_rack_unit, attribute_name="vendor")

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

        self.adaptors = self._get_adaptors()
        self.cpus = self._get_cpus()
        self.gpus = self._get_gpus()
        self.memory_arrays = self._get_memory_arrays()
        self.mgmt_interfaces = self._get_mgmt_interfaces()
        self.nvme_drives = self._get_nvme_drives()
        if self.slot_id in [None, "0"]:  # We only get power supplies for rack servers that are not part of an enclosure
            self.power_supplies = self._get_power_supplies()
        self.storage_controllers = self._get_storage_controllers()
        self.storage_flexflash_controllers = self._get_storage_flexflash_controllers()
        self.tpms = self._get_tpms()

    def _generate_draw(self):
        pass

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
        Returns rack server short name from EasyUCS catalog files
        """
        if self.sku is not None:
            # We use the catalog file to get the rack short name
            try:
                if self.sku in ["UCSC-C125"]:
                    json_file = open("catalog/server_nodes/" + self.sku + ".json")
                else:
                    json_file = open("catalog/racks/" + self.sku + ".json")
                rack_catalog = json.load(fp=json_file)
                json_file.close()

                if "model_short_name" in rack_catalog:
                    return rack_catalog["model_short_name"]

            except FileNotFoundError:
                self.logger(level="error", message="Rack catalog file " + self.sku + ".json not found")
                return None

        return None

    def _get_nvme_drives(self):
        return []

    def _get_power_supplies(self):
        return []

    def _get_storage_controllers(self):
        return []

    def _get_storage_flexflash_controllers(self):
        return []

    def _get_tpms(self):
        return []


class UcsRackEnclosure(GenericUcsInventoryObject):
    _UCS_SDK_OBJECT_NAME = "equipmentRackEnclosure"

    def __init__(self, parent=None, equipment_rack_enclosure=None):
        GenericUcsInventoryObject.__init__(self, parent=parent, ucs_sdk_object=equipment_rack_enclosure)

        self.model = self.get_attribute(ucs_sdk_object=equipment_rack_enclosure, attribute_name="model")
        self.serial = self.get_attribute(ucs_sdk_object=equipment_rack_enclosure, attribute_name="serial")

        self.power_supplies = self._get_power_supplies()
        self.server_nodes = self._get_server_nodes()

    def _get_power_supplies(self):
        return []

    def _get_server_nodes(self):
        return []


class UcsSystemRack(UcsRack, UcsSystemInventoryObject):
    _UCS_SDK_CATALOG_OBJECT_NAME = "equipmentRackUnitCapProvider"
    _UCS_SDK_FIRMWARE_RUNNING_SUFFIX = "/mgmt/fw-system"

    def __init__(self, parent=None, compute_rack_unit=None):
        UcsRack.__init__(self, parent=parent, compute_rack_unit=compute_rack_unit)

        self.assigned_to_dn = self.get_attribute(ucs_sdk_object=compute_rack_unit, attribute_name="assigned_to_dn")
        self.association = self.get_attribute(ucs_sdk_object=compute_rack_unit, attribute_name="association")
        self.enclosure_id = self.get_attribute(ucs_sdk_object=compute_rack_unit, attribute_name="enclosure_id")
        self.revision = self.get_attribute(ucs_sdk_object=compute_rack_unit, attribute_name="revision")

        UcsSystemInventoryObject.__init__(self, parent=parent, ucs_sdk_object=compute_rack_unit)

        self.locator_led_status = None
        self.mgmt_connection_type = None
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
        if self._inventory.load_from == "live":
            self.short_name = self._get_model_short_name()
            self.mgmt_connection_type = self._get_mgmt_connection_type()
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
            for attribute in ["locator_led_status", "mgmt_connection_type", "os_arch", "os_kernel_version",
                              "os_patch_version", "os_release_version", "os_type", "os_ucs_tool_version",
                              "os_update_version", "os_vendor", "service_profile_org", "service_profile_name",
                              "service_profile_template", "service_profile_template_org",
                              "service_profile_template_name", "short_name"]:
                setattr(self, attribute, None)
                if attribute in compute_rack_unit:
                    setattr(self, attribute, self.get_attribute(ucs_sdk_object=compute_rack_unit,
                                                                attribute_name=attribute))

    def _generate_draw(self):
        self._draw_front = UcsSystemDrawRackFront(parent=self)
        self._draw_rear = UcsSystemDrawRackRear(parent=self)
        self._draw_infra = None

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

    def _get_mgmt_connection_type(self):
        # We check if we already have fetched the list of mgmtConnection objects
        if self._inventory.sdk_objects["mgmtConnection"] is not None:
            mgmt_connection_list = [mgmt_connection for mgmt_connection in self._inventory.sdk_objects["mgmtConnection"]
                                    if "sys/rack-unit-" + self.id + "/" in mgmt_connection.dn]

            # We return the mgmtConnection type if there is one and only one mgmtConnection object in the list
            if len(mgmt_connection_list) == 1:
                return mgmt_connection_list[0].type

        return None

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
            # We need to filter out moInvKv objects that are not for this rack id
            mo_inv_kv_list = [mo_inv_kv for mo_inv_kv in self._inventory.sdk_objects["moInvKv"]
                              if "sys/rack-unit-" + self.id + "/inv-kv-hostOs/" in mo_inv_kv.dn]
            if len(mo_inv_kv_list) > 0:
                self.logger(level="debug", message="Found " + str(len(mo_inv_kv_list)) +
                                                   " ucs-tools inventory elements for rack-unit " + self.id)

            # We set the list of attributes from the various moInvKv objects attached to this rack id
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

                # If driver name is unknown, we skip its entry
                if current_driver["name"] is None:
                    continue

                # UCS VIC Ethernet driver
                if current_driver["name"] in ["enic", "nenic"]:
                    # Finding the associated adaptors to set driver versions
                    for adaptor in self.adaptors:
                        if adaptor.sku is None:
                            continue
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
                                        message="Found Ethernet VIC driver (" + current_driver["name"] + ") version " +
                                                current_driver["version"] + " for adaptor " + adaptor.id +
                                                " of rack-unit " + self.id)

                # UCS VIC Fibre Channel driver
                if current_driver["name"] in ["fnic", "nfnic"]:
                    # Finding the associated adaptors to set driver versions
                    for adaptor in self.adaptors:
                        if adaptor.sku is None:
                            continue
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
                                        message="Found Fibre Channel VIC driver (" + current_driver["name"] +
                                                ") version " + current_driver["version"] + " for adaptor " +
                                                adaptor.id + " of rack-unit " + self.id)

                # Avago/LSI MegaRAID SAS driver
                if current_driver["name"] in ["lsi_mr3", "megaraid_sas"]:
                    # Finding the associated storage controllers to set driver versions
                    for storage_controller in self.storage_controllers:
                        if storage_controller.name is None:
                            continue
                        if any(x in storage_controller.name for x in ["MegaRAID", "FlexStorage"]):
                            storage_controller.driver_name = current_driver["name"]
                            storage_controller.driver_version = current_driver["version"]
                            self.logger(level="debug",
                                        message="Found Storage controller driver (" + current_driver["name"] +
                                                ") version " + current_driver["version"] + " for storage controller " +
                                                storage_controller.id + " of rack-unit " + self.id)

            return True
        else:
            return False

    def _get_power_supplies(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsSystemPsu, parent=self)
        elif self._inventory.load_from == "file" and "power_supplies" in self._ucs_sdk_object:
            return [UcsSystemPsu(self, psu) for psu in self._ucs_sdk_object["power_supplies"]]
        else:
            return []

    def _get_service_profile_template(self):
        # We check if we already have fetched the list of lsServer objects
        if self._inventory.sdk_objects["lsServer"] is not None:
            # We need to filter out lsServer objects that are not for this rack id
            ls_server_list = [ls_server for ls_server in self._inventory.sdk_objects["lsServer"]
                              if ls_server.pn_dn == "sys/rack-unit-" + self.id]

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


class UcsSystemRackEnclosure(UcsRackEnclosure, UcsSystemInventoryObject):
    _UCS_SDK_CATALOG_OBJECT_NAME = "equipmentRackEnclosureCapProvider"

    def __init__(self, parent=None, equipment_rack_enclosure=None):
        UcsRackEnclosure.__init__(self, parent=parent, equipment_rack_enclosure=equipment_rack_enclosure)

        self.id = self.get_attribute(ucs_sdk_object=equipment_rack_enclosure, attribute_name="id")
        self.revision = self.get_attribute(ucs_sdk_object=equipment_rack_enclosure, attribute_name="revision")
        self.vendor = self.get_attribute(ucs_sdk_object=equipment_rack_enclosure, attribute_name="vendor")

        UcsSystemInventoryObject.__init__(self, parent=parent, ucs_sdk_object=equipment_rack_enclosure)

    def _generate_draw(self):
        self._draw_front = UcsSystemDrawRackEnclosureFront(parent=self)
        self._draw_rear = UcsSystemDrawRackEnclosureRear(parent=self)
        self._draw_infra = None

    def _get_power_supplies(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsSystemPsu, parent=self)
        elif self._inventory.load_from == "file" and "power_supplies" in self._ucs_sdk_object:
            return [UcsSystemPsu(self, psu) for psu in self._ucs_sdk_object["power_supplies"]]
        else:
            return []

    def _get_server_nodes(self):
        if self._inventory.load_from == "live":
            # We force the dn manually since computeRackUnit objects are not under equipmentRackEnclosure in UCSM SDK
            # We only get computeRackUnit objects that have an enclosureId value that is not "0"
            racks = self._inventory.get_inventory_objects_under_dn(dn="sys", object_class=UcsSystemRack, parent=self)
            return [rack for rack in racks if rack.enclosure_id != "0"]
            #return self._inventory.get_inventory_objects_under_dn(dn="sys", object_class=UcsSystemRack, parent=self)
        elif self._inventory.load_from == "file" and "server_nodes" in self._ucs_sdk_object:
            return [UcsSystemRack(self, server_node) for server_node in self._ucs_sdk_object["server_nodes"]]
        else:
            return []


class UcsImcRack(UcsRack, UcsImcInventoryObject):
    def __init__(self, parent=None, compute_rack_unit=None):
        UcsRack.__init__(self, parent=parent, compute_rack_unit=compute_rack_unit)

        self.name = self.get_attribute(ucs_sdk_object=compute_rack_unit, attribute_name="name")

        UcsImcInventoryObject.__init__(self, parent=parent, ucs_sdk_object=compute_rack_unit)

        self.locator_led_status = None
        self.short_name = None

        # Since we don't have a catalog item for finding the SKU, we set it manually here
        self.sku = self.model

        self.adaptors = self._get_adaptors() + self._get_network_adapters()

        if self._inventory.load_from == "live":
            self.short_name = self._get_model_short_name()
            self.locator_led_status = self._determine_locator_led_status()
        elif self._inventory.load_from == "file":
            for attribute in ["locator_led_status", "short_name"]:
                setattr(self, attribute, None)
                if attribute in compute_rack_unit:
                    setattr(self, attribute, self.get_attribute(ucs_sdk_object=compute_rack_unit,
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

    def _get_nvme_drives(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsImcStorageNvmeDrive,
                                                                  parent=self) +\
                   self._inventory.get_inventory_objects_under_dn(dn=self.dn,
                                                                  object_class=UcsImcStorageControllerNvmeDrive,
                                                                  parent=self)
        elif self._inventory.load_from == "file" and "nvme_drives" in self._ucs_sdk_object:
            return [UcsImcStorageNvmeDrive(self, nvme_drive) for nvme_drive in self._ucs_sdk_object["nvme_drives"]]
        else:
            return []

    def _get_power_supplies(self):
        if self._inventory.load_from == "live":
            return self._inventory.get_inventory_objects_under_dn(dn=self.dn, object_class=UcsImcPsu, parent=self)
        elif self._inventory.load_from == "file" and "power_supplies" in self._ucs_sdk_object:
            return [UcsImcPsu(self, psu) for psu in self._ucs_sdk_object["power_supplies"]]
        else:
            return []

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

    def _generate_draw(self):
        self._draw_front = UcsImcDrawRackFront(parent=self)
        self._draw_rear = UcsImcDrawRackRear(parent=self)


class UcsImcRackEnclosure(UcsRackEnclosure, UcsImcInventoryObject):
    def __init__(self, parent=None, equipment_rack_enclosure=None):
        UcsRackEnclosure.__init__(self, parent=parent, equipment_rack_enclosure=equipment_rack_enclosure)

        UcsImcInventoryObject.__init__(self, parent=parent, ucs_sdk_object=equipment_rack_enclosure)

        # Since we don't have a catalog item for finding the SKU, we set it manually here
        self.sku = self.model

    def _get_power_supplies(self):
        if self._inventory.load_from == "live":
            # We force the dn manually since equipmentPsu objects are not under equipmentRackEnclosure in IMC SDK
            return self._inventory.get_inventory_objects_under_dn(dn="sys/rack-unit-1", object_class=UcsImcPsu,
                                                                  parent=self)
        elif self._inventory.load_from == "file" and "power_supplies" in self._ucs_sdk_object:
            return [UcsImcPsu(self, psu) for psu in self._ucs_sdk_object["power_supplies"]]
        else:
            return []

    def _get_server_nodes(self):
        if self._inventory.load_from == "live":
            # We force the dn manually since computeRackUnit objects are not under equipmentRackEnclosure in IMC SDK
            return self._inventory.get_inventory_objects_under_dn(dn="sys", object_class=UcsImcRack, parent=self)
        elif self._inventory.load_from == "file" and "server_nodes" in self._ucs_sdk_object:
            return [UcsImcRack(self, server_node) for server_node in self._ucs_sdk_object["server_nodes"]]
        else:
            return []

    def _generate_draw(self):
        self._draw_front = UcsImcDrawRackEnclosureFront(parent=self)
        self._draw_rear = UcsImcDrawRackEnclosureRear(parent=self)
