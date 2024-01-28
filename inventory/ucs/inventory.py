# coding: utf-8
# !/usr/bin/env python

""" inventory.py: Easy UCS Deployment Tool """

import re
import urllib
import xml

from imcsdk.imcexception import ImcException
from ucscsdk.ucscexception import UcscException
from ucsmsdk.ucsexception import UcsException

from inventory.inventory import GenericInventory
from inventory.ucs.adaptor import UcsImcHbaAdapter
from inventory.ucs.chassis import UcsImcSioc
from inventory.ucs.gpu import UcsImcGpu
from inventory.ucs.neighbor import UcsSystemLanNeighbor, UcsSystemSanNeighbor
from inventory.ucs.psu import UcsSystemPsu
from inventory.ucs.storage import UcsSystemStorageController, UcsImcStorageControllerNvmeDrive, \
    UcsSystemStorageControllerNvmeDrive, UcsImcStorageLocalDisk, UcsImcStorageNvmeDrive, UcsImcStorageRaidBattery


class GenericUcsInventory(GenericInventory):
    def __init__(self, parent=None):
        GenericInventory.__init__(self, parent=parent)
        self.export_list = None
        self.handle = self.parent.parent.handle
        self.intersight_status = ""
        self.sdk_objects = {}

    def _fetch_sdk_objects(self, force=False):
        # List of SDK objects to fetch that are common to UCS System, IMC & UCS Central
        sdk_objects_to_fetch = ["adaptorExtEthIf", "adaptorHostEthIf", "adaptorUnit", "computeRackUnit",
                                "equipmentChassis", "equipmentLocatorLed", "equipmentPsu",
                                "equipmentSystemIOController", "memoryArray", "memoryUnit", "mgmtController", "mgmtIf",
                                "processorUnit", "storageController", "storageEnclosure", "storageFlexFlashController",
                                "storageLocalDisk", "storageRaidBattery"]
        self.logger(level="debug", message="Fetching common UCS SDK objects for inventory")

        if self.device.task is not None:
            self.device.task.taskstep_manager.start_taskstep(name="FetchInventoryUcsCommonSdkObjects",
                                                             description="Fetching common UCS SDK Inventory Objects")

        failed_to_fetch = []
        for sdk_object_name in sdk_objects_to_fetch:
            try:
                self.sdk_objects[sdk_object_name] = self.handle.query_classid(sdk_object_name)
                self.logger(level="debug", message="Fetched " + str(len(self.sdk_objects[sdk_object_name])) +
                                                   " objects of class " + sdk_object_name)
            except (UcsException, ImcException, UcscException) as err:
                if err.error_code in ["ERR-xml-parse-error", "0"] and \
                        "no class named " + sdk_object_name in err.error_descr:
                    self.logger(level="debug", message="No UCS class named " + sdk_object_name)
                elif err.error_code in ["2500"] and \
                        "MO is not supported on this UCS-C server platform." in err.error_descr:
                    self.logger(level="debug", message="No UCS class named " + sdk_object_name)
                else:
                    failed_to_fetch.append(sdk_object_name)
                    self.logger(level="error",
                                message="Error while trying to fetch " + self.device.metadata.device_type_long +
                                        " class " + sdk_object_name + ": " + str(err))

            except ConnectionRefusedError:
                failed_to_fetch.append(sdk_object_name)
                self.logger(level="error",
                            message="Error while communicating with " + self.device.metadata.device_type_long +
                                    " for class " + sdk_object_name + ": Connection refused")
            except urllib.error.URLError:
                failed_to_fetch.append(sdk_object_name)
                self.logger(level="error", message="Timeout error while fetching " +
                                                   self.device.metadata.device_type_long + " class " + sdk_object_name)
            except Exception as err:
                failed_to_fetch.append(sdk_object_name)
                self.logger(level="error", message="Error while fetching " + self.device.metadata.device_type_long +
                                                   " class " + sdk_object_name + ": " + str(err))

        if failed_to_fetch:
            duplicate_failed_to_fetch = failed_to_fetch.copy()
            for sdk_object_name in duplicate_failed_to_fetch:
                self.logger(level="info", message="Retrying to fetch " + sdk_object_name)
                try:
                    self.sdk_objects[sdk_object_name] = self.handle.query_classid(sdk_object_name)
                    self.logger(level="debug", message="Fetched " + str(len(self.sdk_objects[sdk_object_name])) +
                                                       " objects of class " + sdk_object_name)
                    failed_to_fetch.remove(sdk_object_name)
                except (UcsException, ImcException, UcscException) as err:
                    self.logger(level="error",
                                message="Error while trying to fetch " + self.device.metadata.device_type_long +
                                        " class " + sdk_object_name + ": " + str(err))

                except ConnectionRefusedError:
                    self.logger(level="error",
                                message="Error while communicating with " + self.device.metadata.device_type_long +
                                        " for class " + sdk_object_name + ": Connection refused")
                except urllib.error.URLError:
                    self.logger(level="error", message="Timeout error while fetching " +
                                                       self.device.metadata.device_type_long + " class " + sdk_object_name)
                except Exception as err:
                    self.logger(level="error", message="Error while fetching " + self.device.metadata.device_type_long +
                                                       " class " + sdk_object_name + ": " + str(err))

        # In case we still have SDK objects that failed to fetch, we list them in a warning message
        if failed_to_fetch:
            for sdk_object_name in failed_to_fetch:
                self.logger(level="warning",
                            message="Impossible to fetch " + sdk_object_name + " after 2 attempts.")

        if self.device.task is not None:
            if not failed_to_fetch:
                self.device.task.taskstep_manager.stop_taskstep(
                    name="FetchInventoryUcsCommonSdkObjects", status="successful",
                    status_message="Successfully fetched common UCS SDK Inventory Objects")
            elif force:
                self.device.task.taskstep_manager.stop_taskstep(
                    name="FetchInventoryUcsCommonSdkObjects", status="successful",
                    status_message="Fetched common UCS SDK Inventory Objects with errors (forced)")
            else:
                self.device.task.taskstep_manager.stop_taskstep(
                    name="FetchInventoryUcsCommonSdkObjects", status="failed",
                    status_message="Error while fetching common UCS SDK Inventory Objects")

                # If any of the mandatory tasksteps fails then return False
                if not self.device.task.taskstep_manager.is_taskstep_optional(name="FetchInventoryUcsCommonSdkObjects"):
                    return False
        return True

    def get_inventory_objects_under_dn(self, dn=None, object_class=None, parent=None):
        if dn is not None and object_class is not None and parent is not None:
            if hasattr(object_class, "_UCS_SDK_OBJECT_NAME"):
                if object_class._UCS_SDK_OBJECT_NAME in self.sdk_objects.keys():
                    if self.sdk_objects[object_class._UCS_SDK_OBJECT_NAME] is not None:
                        # We filter out SDK objects that are not under this Dn
                        filtered_sdk_objects_list = []
                        for sdk_object in self.sdk_objects[object_class._UCS_SDK_OBJECT_NAME]:
                            if dn + "/" in sdk_object.dn:
                                # Also filter objects that have a "presence" attribute set as "missing"
                                if hasattr(sdk_object, "presence") and sdk_object.presence == "missing":
                                    continue
                                # Also filter absent adaptorConnectorInfo on standalone servers
                                if hasattr(sdk_object, "present") and sdk_object.present in ["N/A", "NO", "No"]:
                                    continue
                                # Also filter absent storageRaidBattery on standalone servers
                                if hasattr(sdk_object, "battery_present") and sdk_object.battery_present != "true":
                                    continue
                                # Also filter absent storageFlexFlashPhysicalDrive on standalone servers
                                if object_class._UCS_SDK_OBJECT_NAME == "storageFlexFlashPhysicalDrive":
                                    if hasattr(sdk_object, "capacity"):
                                        if sdk_object.capacity == "0 MB":
                                            continue
                                # Also filter absent equipmentTpm on standalone servers
                                if hasattr(sdk_object, "presence") and sdk_object.presence == "empty":
                                    continue
                                # Also filter equipmentSwitchCard that are on slot 1 (base module)
                                if object_class._UCS_SDK_OBJECT_NAME == "equipmentSwitchCard"\
                                        and hasattr(sdk_object, "id") and sdk_object.id == "1":
                                    continue
                                # Also filter pciEquipSlot that are not GPUs for UcsImcGpu
                                if object_class is UcsImcGpu and hasattr(sdk_object, "vendor"):
                                    if sdk_object.vendor not in ["0x10de", "0x1002"]:  # NVIDIA or AMD
                                        continue
                                # Also filter absent equipmentSystemIOController on standalone S3260
                                if object_class is UcsImcSioc and hasattr(sdk_object, "pid"):
                                    if sdk_object.pid == "N/A":
                                        continue
                                # Also filter storageControllerNVMe of types PCIe-Switch, NVMe-direct-U.2-drives or
                                # NVMe-direct-HHHL-drives
                                if object_class is UcsImcStorageControllerNvmeDrive and hasattr(sdk_object, "id"):
                                    if any(x in sdk_object.id for x in ["PCIe-Switch", "NVMe-direct-U.2-drives",
                                                                        "NVMe-direct-HHHL-drives"]):
                                        continue
                                # Also filter absent DIMMs reported by UCS Manager as "NO DIMM"
                                if hasattr(sdk_object, "model") and sdk_object.model == "NO DIMM":
                                    continue
                                # Also filter storageController of types other than NVME for
                                # UcsSystemStorageControllerNvmeDrive
                                if object_class is UcsSystemStorageControllerNvmeDrive and hasattr(sdk_object, "type"):
                                    if sdk_object.type not in ["NVME"]:
                                        continue
                                # Also filter storageController of type NVME for UcsSystemStorageController
                                if object_class is UcsSystemStorageController and hasattr(sdk_object, "type"):
                                    if sdk_object.type in ["NVME"]:
                                        continue
                                # Also filter equipmentPsu that have an ID of 0
                                if object_class is UcsSystemPsu and sdk_object.id == "0":
                                    continue
                                # Also filter storageRaidBattery objects for M.2 MSTOR-RAID controllers
                                if object_class is UcsImcStorageRaidBattery and "storage-SATA-MSTOR-RAID" \
                                        in sdk_object.dn:
                                    continue
                                # Also filter storageLocalDisk objects with drive_slot_status set to "Absent"
                                if object_class is UcsImcStorageLocalDisk and hasattr(sdk_object, "drive_slot_status"):
                                    if sdk_object.drive_slot_status in ["Absent"]:
                                        continue
                                # Also filter storageNVMePhysicalDrive objects with drive_slot_status set to "Absent"
                                if object_class is UcsImcStorageNvmeDrive and hasattr(sdk_object, "drive_slot_status"):
                                    if sdk_object.drive_slot_status in ["Absent"]:
                                        continue
                                # Filter only HBA adapters for UcsImcHbaAdapter objects
                                if object_class is UcsImcHbaAdapter and "HBA" not in sdk_object.model:
                                    continue
                                if object_class is UcsImcHbaAdapter and "SAS HBA" in sdk_object.model:
                                    continue

                                filtered_sdk_objects_list.append(sdk_object)
                            # Handle the case of LAN/SAN Neighbor objects for which we use fiPortDn attribute
                            elif hasattr(sdk_object, "fi_port_dn"):
                                if dn == sdk_object.fi_port_dn:
                                    filtered_sdk_objects_list.append(sdk_object)

                        easyucs_objects_list = []
                        for sdk_object in sorted(filtered_sdk_objects_list,
                                                 key=lambda sdk_obj: [int(t) if t.isdigit() else t.lower()
                                                                      for t in re.split('(\d+)', sdk_obj.dn)]):
                            # We instantiate an Inventory Object for each corresponding SDK object
                            easyucs_objects_list.append(object_class(parent, sdk_object))
                        return easyucs_objects_list
        return []


class UcsSystemInventory(GenericUcsInventory):
    def __init__(self, parent=None):
        self.chassis = []
        self.device_connector = []
        self.fabric_extenders = []
        self.fabric_interconnects = []
        self.lan_neighbors = []
        self.rack_enclosures = []
        self.rack_units = []
        self.san_neighbors = []

        self._draw_infra_san_neighbors = None
        self._draw_infra_lan_neighbors = None
        self._draw_infra_rack_service_profiles = None
        self._draw_infra_rack_enclosure_service_profiles = None
        self._draw_infra_chassis_service_profiles = None
        # Set the list of Service Profile template used for Infra Draw of Service Profiles on chassis and racks
        self._draw_color_list_per_sp_template = [{"color": "lightblue", "template_name": "", "template_org": ""},
                                                 {"color": "green", "template_name": "", "template_org": ""},
                                                 {"color": "red", "template_name": "", "template_org": ""},
                                                 {"color": "pink", "template_name": "", "template_org": ""},
                                                 {"color": "violet", "template_name": "", "template_org": ""},
                                                 {"color": "brown", "template_name": "", "template_org": ""},
                                                 {"color": "orange", "template_name": "", "template_org": ""},
                                                 {"color": "gold", "template_name": "", "template_org": ""},
                                                 {"color": "slateblue", "template_name": "", "template_org": ""},
                                                 {"color": "salmon", "template_name": "", "template_org": ""},
                                                 {"color": "olive", "template_name": "", "template_org": ""},
                                                 {"color": "antiquewhite", "template_name": "", "template_org": ""},
                                                 {"color": "burlywood", "template_name": "", "template_org": ""},
                                                 {"color": "greenyellow", "template_name": "", "template_org": ""},
                                                 {"color": "goldenrod", "template_name": "", "template_org": ""},
                                                 {"color": "lavender", "template_name": "", "template_org": ""},
                                                 {"color": "darkkhaki", "template_name": "", "template_org": ""},
                                                 {"color": "blueviolet", "template_name": "", "template_org": ""},
                                                 {"color": "chartreuse", "template_name": "", "template_org": ""},
                                                 {"color": "darkcyan", "template_name": "", "template_org": ""},
                                                 {"color": "deepskyblue", "template_name": "", "template_org": ""},
                                                 {"color": "darkgreen", "template_name": "", "template_org": ""},
                                                 {"color": "indianred", "template_name": "", "template_org": ""},
                                                 {"color": "magenta", "template_name": "", "template_org": ""},
                                                 {"color": "cadetblue", "template_name": "", "template_org": ""},
                                                 {"color": "hotpink", "template_name": "", "template_org": ""},
                                                 {"color": "yellowgreen", "template_name": "", "template_org": ""},
                                                 {"color": "darkseagreen", "template_name": "", "template_org": ""},
                                                 {"color": "skyblue", "template_name": "", "template_org": ""},
                                                 {"color": "mediumpurple", "template_name": "", "template_org": ""},
                                                 {"color": "azure", "template_name": "", "template_org": ""},
                                                 {"color": "bisque", "template_name": "", "template_org": ""}]

        GenericUcsInventory.__init__(self, parent=parent)

        # List of attributes to be exported in an inventory export
        self.export_list = ["chassis", "device_connector", "fabric_extenders", "fabric_interconnects", "lan_neighbors",
                            "rack_enclosures", "rack_units", "san_neighbors"]

    def _fetch_sdk_objects(self, force=False):
        GenericUcsInventory._fetch_sdk_objects(self, force=force)

        # If any of the mandatory tasksteps fails then return False
        from api.api_server import easyucs
        if easyucs and self.device.task and \
                easyucs.task_manager.is_any_taskstep_failed(uuid=self.device.task.metadata.uuid):
            self.logger(level="error", message="Failed to fetch one or more common SDK objects. "
                                               "Stopping the inventory fetch.")
            return False

        # List of SDK objects to fetch that are specific to UCS System
        sdk_objects_to_fetch = ["adaptorUnitExtn", "computeBlade", "computePersonality", "equipmentCrossFabricModule",
                                "equipmentFex", "equipmentFruVariant", "equipmentIOCard", "equipmentRackEnclosure",
                                "equipmentSwitchCard", "equipmentSwitchIOCard", "equipmentTpm", "equipmentXcvr",
                                "etherPIo", "etherServerIntFIo", "etherSwitchIntFIo", "fcPIo", "firmwareRunning",
                                "firmwareStatus", "graphicsCard", "licenseFeature", "licenseFile", "licenseInstance",
                                "licenseServerHostId", "lsServer", "memoryErrorStats", "mgmtConnection",
                                "mgmtInterface", "mgmtVnet", "moInvKv", "networkElement", "networkLanNeighborEntry",
                                "networkLldpNeighborEntry", "networkSanNeighborEntry", "storageEmbeddedStorage",
                                "storageFlexFlashCard", "storageNvmeStats", "storageSsdHealthStats", "swVlanPortNs",
                                "vnicIpV4MgmtPooledAddr", "vnicIpV4PooledAddr", "vnicIpV4StaticAddr",
                                "vnicIpV6StaticAddr", "vnicIpV6MgmtPooledAddr"]
        self.logger(level="debug",
                    message="Fetching " + self.device.metadata.device_type_long + " SDK objects for inventory")

        if self.device.task is not None:
            self.device.task.taskstep_manager.start_taskstep(
                name="FetchInventoryUcsSystemSdkObjects",
                description="Fetching " + self.device.metadata.device_type_long + " SDK Inventory Objects")

        failed_to_fetch = []
        for sdk_object_name in sdk_objects_to_fetch:
            try:
                self.sdk_objects[sdk_object_name] = self.handle.query_classid(sdk_object_name)
                self.logger(level="debug", message="Fetched " + str(len(self.sdk_objects[sdk_object_name])) +
                                                   " objects of class " + sdk_object_name)
            except (UcsException, ImcException) as err:
                if err.error_code in ["ERR-xml-parse-error", "0"] and \
                        "no class named " + sdk_object_name in err.error_descr:
                    self.logger(level="debug", message="No " + self.device.metadata.device_type_long +
                                                       " class named " + sdk_object_name)
                else:
                    failed_to_fetch.append(sdk_object_name)
                    self.logger(level="error",
                                message="Error while trying to fetch " + self.device.metadata.device_type_long +
                                        " class " + sdk_object_name + ": " + str(err))
            except ConnectionRefusedError:
                failed_to_fetch.append(sdk_object_name)
                self.logger(level="error",
                            message="Error while communicating with " + self.device.metadata.device_type_long +
                                    " for class " + sdk_object_name + ": Connection refused")
            except urllib.error.URLError:
                failed_to_fetch.append(sdk_object_name)
                self.logger(level="error", message="Timeout error while fetching " +
                                                   self.device.metadata.device_type_long + " class " + sdk_object_name)
            except Exception as err:
                failed_to_fetch.append(sdk_object_name)
                self.logger(level="error", message="Error while fetching " + self.device.metadata.device_type_long +
                                                   " class " + sdk_object_name + ": " + str(err))

        # We retry all SDK objects that failed to fetch properly
        if failed_to_fetch:
            duplicate_failed_to_fetch = failed_to_fetch.copy()
            for sdk_object_name in duplicate_failed_to_fetch:
                self.logger(level="info", message="Retrying to fetch " + sdk_object_name)
                try:
                    self.sdk_objects[sdk_object_name] = self.handle.query_classid(sdk_object_name)
                    self.logger(level="debug", message="Fetched " + str(len(self.sdk_objects[sdk_object_name])) +
                                                       " objects of class " + sdk_object_name)
                    failed_to_fetch.remove(sdk_object_name)
                except (UcsException, ImcException) as err:
                    self.logger(level="error",
                                message="Error while trying to fetch " + self.device.metadata.device_type_long +
                                        " class " + sdk_object_name + ": " + str(err))
                except ConnectionRefusedError:
                    self.logger(level="error",
                                message="Error while communicating with " + self.device.metadata.device_type_long +
                                        " for class " + sdk_object_name + ": Connection refused")
                except urllib.error.URLError:
                    self.logger(level="error", message="Timeout error while fetching " +
                                                       self.device.metadata.device_type_long + " class " +
                                                       sdk_object_name)
                except Exception as err:
                    self.logger(level="error", message="Error while fetching " + self.device.metadata.device_type_long +
                                                       " class " + sdk_object_name + ": " + str(err))

        # In case we still have SDK objects that failed to fetch, we list them in a warning message
        if failed_to_fetch:
            for sdk_object_name in failed_to_fetch:
                self.logger(level="warning",
                            message="Impossible to fetch " + sdk_object_name + " after 2 attempts.")

        if self.device.task is not None:
            if not failed_to_fetch:
                self.device.task.taskstep_manager.stop_taskstep(
                    name="FetchInventoryUcsSystemSdkObjects", status="successful",
                    status_message="Successfully fetched " + self.device.metadata.device_type_long +
                                   " SDK Inventory Objects")
            elif force:
                self.device.task.taskstep_manager.stop_taskstep(
                    name="FetchInventoryUcsSystemSdkObjects", status="successful",
                    status_message="Fetched " + self.device.metadata.device_type_long +
                                   " SDK Inventory Objects with errors (forced)")
            else:
                self.device.task.taskstep_manager.stop_taskstep(
                    name="FetchInventoryUcsSystemSdkObjects", status="failed",
                    status_message="Error while fetching " + self.device.metadata.device_type_long +
                                   " SDK Inventory Objects")

                # If any of the mandatory tasksteps fails then return False
                if not self.device.task.taskstep_manager.is_taskstep_optional(name="FetchInventoryUcsSystemSdkObjects"):
                    return False

        # Catalog SDK objects
        if self.device.task is not None:
            self.device.task.taskstep_manager.start_taskstep(
                name="FetchInventoryUcsSystemCatalogSdkObjects",
                description="Fetching " + self.device.metadata.device_type_long + " SDK catalog Inventory Objects")

        issue_while_fetching = False
        try:
            self.logger(level="debug", message="Fetching " + self.device.metadata.device_type_long +
                                               " SDK catalog objects for inventory")
            self.sdk_objects["catalog"] = self.handle.query_children(in_dn="capabilities")
            self.sdk_objects["equipmentManufacturingDef"] = self.handle.query_classid("equipmentManufacturingDef")
            self.sdk_objects["equipmentLocalDiskDef"] = self.handle.query_classid("equipmentLocalDiskDef")
        except (UcsException, ImcException) as err:
            issue_while_fetching = True
            self.logger(level="error",
                        message="Error while trying to fetch " + self.device.metadata.device_type_long +
                                " catalog classes: " + str(err))
        except urllib.error.URLError as err:
            issue_while_fetching = True
            self.logger(level="error",
                        message="URLError while trying to fetch " + self.device.metadata.device_type_long +
                                " catalog classes: " + str(err))
        except Exception as err:
            issue_while_fetching = True
            self.logger(level="error",
                        message="Unexpected Error while trying to fetch " + self.device.metadata.device_type_long +
                                " catalog classes: " + str(err))

        if self.device.task is not None:
            if not issue_while_fetching:
                self.device.task.taskstep_manager.stop_taskstep(
                    name="FetchInventoryUcsSystemCatalogSdkObjects", status="successful",
                    status_message="Successfully fetched " + self.device.metadata.device_type_long +
                                   " catalog SDK Inventory Objects")
            elif force:
                self.device.task.taskstep_manager.stop_taskstep(
                    name="FetchInventoryUcsSystemCatalogSdkObjects", status="successful",
                    status_message="Fetched " + self.device.metadata.device_type_long +
                                   " catalog SDK Inventory Objects with errors (forced)")
            else:
                self.device.task.taskstep_manager.stop_taskstep(
                    name="FetchInventoryUcsSystemCatalogSdkObjects", status="failed",
                    status_message="Error while fetching " + self.device.metadata.device_type_long +
                                   " catalog SDK Inventory Objects")

                # If any of the mandatory tasksteps fails then return False
                if not self.device.task.taskstep_manager.is_taskstep_optional(
                        name="FetchInventoryUcsSystemCatalogSdkObjects"):
                    return False

        return True

    def _get_lan_neighbors(self):
        # Determining the LAN neighbors from the CDP and LLDP neighbor entries of all ports of all FIs
        lan_neighbors_group_number = {}
        lan_neighbors_group_number_counter = 0
        lan_neighbors_list = []
        lan_neighbors_system_name_list = []
        for fi in self.fabric_interconnects:
            for port in fi.ports:
                if port.transport == "ether":
                    for lan_neighbor_entry in port.neighbor_entries:
                        if lan_neighbor_entry.system_name not in lan_neighbors_system_name_list:
                            # This is a new neighbor - We add it to the list
                            lan_neighbors_system_name_list.append(lan_neighbor_entry.system_name)
                            # We check if the port is a member of a port-channel - might indicate that this neighbor is
                            # part of a mLAG/vPC/VSS
                            if port.is_port_channel_member:
                                if port.pc_id not in lan_neighbors_group_number.keys():
                                    lan_neighbors_group_number[port.pc_id] = lan_neighbors_group_number_counter
                                    lan_neighbors_group_number_counter += 1
                                lan_neighbors_list.append(
                                    UcsSystemLanNeighbor(parent=self, ucs_system_lan_neighbor_entry=lan_neighbor_entry,
                                                         ucs_system_fi_eth_port=port,
                                                         group_number=lan_neighbors_group_number[port.pc_id]))
                            else:
                                lan_neighbors_list.append(
                                    UcsSystemLanNeighbor(parent=self, ucs_system_lan_neighbor_entry=lan_neighbor_entry,
                                                         ucs_system_fi_eth_port=port))

                        elif lan_neighbor_entry.system_name in lan_neighbors_system_name_list:
                            # We already have an existing UcsSystemLanNeighbor object for this neighbor entry.Finding it
                            for easyucs_lan_neighbor in lan_neighbors_list:
                                if lan_neighbor_entry.system_name == easyucs_lan_neighbor.system_name:
                                    # We found it - Adding peer information to this neighbor
                                    easyucs_lan_neighbor.peer_ports.append(port)

        # Determining the LAN neighbors from the CDP and LLDP neighbor entries of all ports on GEMs attached to all FIs
        for fi in self.fabric_interconnects:
            for gem in fi.expansion_modules:
                for port in gem.ports:
                    if port.transport == "ether":
                        for lan_neighbor_entry in port.neighbor_entries:
                            if lan_neighbor_entry.system_name not in lan_neighbors_system_name_list:
                                # This is a new neighbor - We add it to the list
                                lan_neighbors_system_name_list.append(lan_neighbor_entry.system_name)
                                # We check if the port is a member of a port-channel - might indicate that this neighbor
                                # is part of a mLAG/vPC/VSS
                                if port.is_port_channel_member:
                                    if port.pc_id not in lan_neighbors_group_number.keys():
                                        lan_neighbors_group_number[port.pc_id] = lan_neighbors_group_number_counter
                                        lan_neighbors_group_number_counter += 1
                                    lan_neighbors_list.append(
                                        UcsSystemLanNeighbor(parent=self,
                                                             ucs_system_lan_neighbor_entry=lan_neighbor_entry,
                                                             ucs_system_fi_eth_port=port,
                                                             group_number=lan_neighbors_group_number[port.pc_id]))
                                else:
                                    lan_neighbors_list.append(
                                        UcsSystemLanNeighbor(parent=self,
                                                             ucs_system_lan_neighbor_entry=lan_neighbor_entry,
                                                             ucs_system_fi_eth_port=port))

                            elif lan_neighbor_entry.system_name in lan_neighbors_system_name_list:
                                # We already have an existing UcsSystemLanNeighbor object for this neighbor. Finding it
                                for easyucs_lan_neighbor in lan_neighbors_list:
                                    if lan_neighbor_entry.system_name == easyucs_lan_neighbor.system_name:
                                        # We found it - Adding peer information to this neighbor
                                        easyucs_lan_neighbor.peer_ports.append(port)

        self.logger(message="The list of LAN neighbors is: " + str(lan_neighbors_system_name_list))
        return lan_neighbors_list

    def _get_san_neighbors(self):
        # Determining the SAN neighbors from SAN neighbor entries of all ports of all FIs
        san_neighbors_fabric_nwwn_list = []
        san_neighbors_list = []
        for fi in self.fabric_interconnects:
            for port in fi.ports:
                if port.transport == "fc":
                    for san_neighbor_entry in port.neighbor_entries:
                        if san_neighbor_entry.fabric_nwwn not in san_neighbors_fabric_nwwn_list:
                            # This is a new neighbor - We add it to the list and create a new object
                            san_neighbors_fabric_nwwn_list.append(san_neighbor_entry.fabric_nwwn)
                            san_neighbors_list.append(
                                UcsSystemSanNeighbor(parent=self, ucs_system_san_neighbor_entry=san_neighbor_entry,
                                                     ucs_system_fi_fc_port=port))

                        elif san_neighbor_entry.fabric_nwwn in san_neighbors_fabric_nwwn_list:
                            # We already have an existing UcsSystemSanNeighbor object for this neighbor. Finding it
                            for ucs_system_san_neighbor in san_neighbors_list:
                                if san_neighbor_entry.fabric_nwwn == ucs_system_san_neighbor.fabric_nwwn:
                                    # We found it - Adding peer information to this neighbor
                                    ucs_system_san_neighbor.peer_ports.append(port)

        # Determining the SAN neighbors from the SAN neighbor entries of all ports on GEMs attached to all FIs
        for fi in self.fabric_interconnects:
            for gem in fi.expansion_modules:
                for port in gem.ports:
                    if port.transport == "fc":
                        for san_neighbor_entry in port.neighbor_entries:
                            if san_neighbor_entry.fabric_nwwn not in san_neighbors_fabric_nwwn_list:
                                # This is a new neighbor - We add it to the list and create a new object
                                san_neighbors_fabric_nwwn_list.append(san_neighbor_entry.fabric_nwwn)
                                san_neighbors_list.append(
                                    UcsSystemSanNeighbor(parent=self, ucs_system_san_neighbor_entry=san_neighbor_entry,
                                                         ucs_system_fi_fc_port=port))

                            elif san_neighbor_entry.system_name in san_neighbors_fabric_nwwn_list:
                                # We already have an existing EasyUcsSanNeighbor object for this neighbor. Finding it
                                for ucs_system_san_neighbor in san_neighbors_list:
                                    if san_neighbor_entry.fabric_nwwn == ucs_system_san_neighbor.fabric_nwwn:
                                        # We found it - Adding peer information to this neighbor
                                        ucs_system_san_neighbor.peer_ports.append(port)

        self.logger(message="The list of SAN neighbors is: " + str(san_neighbors_fabric_nwwn_list))
        return san_neighbors_list


class UcsImcInventory(GenericUcsInventory):
    def __init__(self, parent=None):
        self.chassis = []  # Used for chassis models like S3260
        self.device_connector = []
        self.rack_enclosures = []  # Used for server nodes inside rack enclosures like C4200
        self.rack_units = []
        GenericUcsInventory.__init__(self, parent=parent)

        # List of attributes to be exported in an inventory export
        self.export_list = ["chassis", "device_connector", "rack_enclosures", "rack_units"]

    def _fetch_sdk_objects(self, force=False):
        GenericUcsInventory._fetch_sdk_objects(self, force=force)

        # If any of the mandatory tasksteps fails then return False
        from api.api_server import easyucs
        if easyucs and self.device.task and \
                easyucs.task_manager.is_any_taskstep_failed(uuid=self.device.task.metadata.uuid):
            self.logger(level="error", message="Failed to fetch one or more common SDK objects. "
                                               "Stopping the inventory fetch.")
            return False

        # List of SDK objects to fetch that are specific to IMC
        sdk_objects_to_fetch = ["adaptorConnectorInfo", "computeServerNode", "equipmentRackEnclosure",
                                "equipmentSharedIOModule", "equipmentTpm", "gpuInventory",
                                "ioControllerNVMePhysicalDrive", "ioExpander", "networkAdapterEthIf",
                                "networkAdapterUnit", "pciAdapterFruInventory", "pciAdapterFruInventoryInfo",
                                "pciEquipSlot", "storageControllerNVMe", "storageEnclosureDisk",
                                "storageFlexFlashControllerProps", "storageFlexFlashPhysicalDrive",
                                "storageLocalDiskProps", "storageNVMePhysicalDrive", "systemBoardUnit"]
        self.logger(level="debug",
                    message="Fetching " + self.device.metadata.device_type_long + " SDK objects for inventory")

        if self.device.task is not None:
            self.device.task.taskstep_manager.start_taskstep(
                name="FetchInventoryUcsImcSdkObjects",
                description="Fetching " + self.device.metadata.device_type_long + " SDK Inventory Objects")

        failed_to_fetch = []
        for sdk_object_name in sdk_objects_to_fetch:
            try:
                self.sdk_objects[sdk_object_name] = self.handle.query_classid(sdk_object_name)
                self.logger(level="debug", message="Fetched " + str(len(self.sdk_objects[sdk_object_name])) +
                                                   " objects of class " + sdk_object_name)
            except ImcException as err:
                if err.error_code in ["ERR-xml-parse-error", "0"] and \
                        "no class named " + sdk_object_name in err.error_descr:
                    self.logger(level="debug", message="No " + self.device.metadata.device_type_long +
                                                       " class named " + sdk_object_name)
                elif err.error_code in ["2500"] and \
                        "MO is not supported on this UCS-C server platform." in err.error_descr:
                    self.logger(level="debug", message="No UCS class named " + sdk_object_name)
                else:
                    failed_to_fetch.append(sdk_object_name)
                    self.logger(level="error",
                                message="Error while trying to fetch " + self.device.metadata.device_type_long +
                                        " class " + sdk_object_name + ": " + str(err))
            # Prevent rare exception due to Server Error return when fetching UCS IMC class
            except xml.etree.ElementTree.ParseError as err:
                failed_to_fetch.append(sdk_object_name)
                self.logger(level="error",
                            message="Error while trying to fetch " + self.device.metadata.device_type_long +
                                    " class " + sdk_object_name + ": " + str(err))
            except Exception as err:
                failed_to_fetch.append(sdk_object_name)
                self.logger(level="error",
                            message="Error while fetching " + self.device.metadata.device_type_long +
                                    " class " + sdk_object_name + ": " + str(err))

        # We retry all SDK objects that failed to fetch properly
        if failed_to_fetch:
            duplicate_failed_to_fetch = failed_to_fetch.copy()
            for sdk_object_name in duplicate_failed_to_fetch:
                self.logger(level="info", message="Retrying to fetch " + sdk_object_name)
                try:
                    self.sdk_objects[sdk_object_name] = self.handle.query_classid(sdk_object_name)
                    self.logger(level="debug", message="Fetched " + str(len(self.sdk_objects[sdk_object_name])) +
                                                       " objects of class " + sdk_object_name)
                    failed_to_fetch.remove(sdk_object_name)
                except ImcException as err:
                    self.logger(level="error",
                                message="Error while trying to fetch " + self.device.metadata.device_type_long +
                                        " class " + sdk_object_name + ": " + str(err))
                    # Prevent rare exception due to Server Error return when fetching UCS IMC class
                except xml.etree.ElementTree.ParseError as err:
                    self.logger(level="error",
                                message="Error while trying to fetch " + self.device.metadata.device_type_long +
                                        " class " + sdk_object_name + ": " + str(err))
                except Exception as err:
                    self.logger(level="error",
                                message="Error while fetching " + self.device.metadata.device_type_long +
                                        " class " + sdk_object_name + ": " + str(err))

        # In case we still have SDK objects that failed to fetch, we list them in a warning message
        if failed_to_fetch:
            for sdk_object_name in failed_to_fetch:
                self.logger(level="warning",
                            message="Impossible to fetch " + sdk_object_name + " after 2 attempts.")

        if self.device.task is not None:
            if not failed_to_fetch:
                self.device.task.taskstep_manager.stop_taskstep(
                    name="FetchInventoryUcsImcSdkObjects", status="successful",
                    status_message="Successfully fetched " + self.device.metadata.device_type_long +
                                   " SDK Inventory Objects")
            elif force:
                self.device.task.taskstep_manager.stop_taskstep(
                    name="FetchInventoryUcsImcSdkObjects", status="successful",
                    status_message="Fetched " + self.device.metadata.device_type_long +
                                   " SDK Inventory Objects with errors (forced)")
            else:
                self.device.task.taskstep_manager.stop_taskstep(
                    name="FetchInventoryUcsImcSdkObjects", status="failed",
                    status_message="Error while fetching " + self.device.metadata.device_type_long +
                                   " SDK Inventory Objects")

                # If any of the mandatory tasksteps fails then return False
                if not self.device.task.taskstep_manager.is_taskstep_optional(name="FetchInventoryUcsImcSdkObjects"):
                    return False

        # Catalog SDK objects
        if self.device.task is not None:
            self.device.task.taskstep_manager.start_taskstep(
                name="FetchInventoryUcsImcCatalogSdkObjects",
                description="Fetching " + self.device.metadata.device_type_long + " SDK catalog Inventory Objects")

        issue_while_fetching = False
        try:
            self.logger(level="debug", message="Fetching " + self.device.metadata.device_type_long +
                                               " SDK catalog objects for inventory")
            compute_boards = self.handle.query_classid("computeBoard")
            self.logger(level="debug",
                        message="Found " + str(len(compute_boards)) + " computeBoard object(s) for catalog")
            self.sdk_objects["catalog"] = []
            for compute_board in compute_boards:
                self.sdk_objects["catalog"].extend(self.handle.query_children(in_dn=compute_board.dn + "/pid"))

            self.logger(level="debug", message="Catalog has " + str(len(self.sdk_objects["catalog"])) + " objects")

        except ImcException as err:
            issue_while_fetching = True
            self.logger(level="error", message="Error while trying to fetch " + self.device.metadata.device_type_long +
                                               " catalog classes: " + str(err))

        if self.device.task is not None:
            if not issue_while_fetching:
                self.device.task.taskstep_manager.stop_taskstep(
                    name="FetchInventoryUcsImcCatalogSdkObjects", status="successful",
                    status_message="Successfully fetched " + self.device.metadata.device_type_long +
                                   " catalog SDK Inventory Objects")
            else:
                self.device.task.taskstep_manager.stop_taskstep(
                    name="FetchInventoryUcsImcCatalogSdkObjects", status="failed",
                    status_message="Error while fetching " + self.device.metadata.device_type_long +
                                   " catalog SDK Inventory Objects")

                # If any of the mandatory tasksteps fails then return False
                if not self.device.task.taskstep_manager.is_taskstep_optional(
                        name="FetchInventoryUcsImcCatalogSdkObjects"):
                    return False

        return True


class UcsCentralInventory(GenericUcsInventory):
    def __init__(self, parent=None):
        self.domains = []
        GenericUcsInventory.__init__(self, parent=parent)

        # List of attributes to be exported in an inventory export
        self.export_list = ["domains"]

    def _fetch_sdk_objects(self, force=False):
        GenericUcsInventory._fetch_sdk_objects(self, force=force)

        # If any of the mandatory tasksteps fails then return False
        from api.api_server import easyucs
        if easyucs and self.device.task and \
                easyucs.task_manager.is_any_taskstep_failed(uuid=self.device.task.metadata.uuid):
            self.logger(level="error", message="Failed to fetch one or more common SDK objects. "
                                               "Stopping the inventory fetch.")
            return False

        # List of SDK objects to fetch that are specific to UCS Central
        sdk_objects_to_fetch = ["computeBlade", "computeSystem", "equipmentFex", "equipmentFruVariant",
                                "equipmentIOCard", "equipmentSwitchCard", "equipmentSwitchIOCard", "equipmentXcvr",
                                "etherPIo", "etherServerIntFIo", "etherSwitchIntFIo", "fcPIo", "firmwareRunning",
                                "firmwareStatus", "graphicsCard", "licenseFeature", "licenseFile", "licenseInstance",
                                "licenseServerHostId", "lsServer", "mgmtConnection", "mgmtInterface", "mgmtVnet",
                                "networkElement", "storageFlexFlashCard", "storageNvmeStats", "storageSsdHealthStats",
                                "vnicIpV4MgmtPooledAddr", "vnicIpV4PooledAddr", "vnicIpV4StaticAddr",
                                "vnicIpV6StaticAddr", "vnicIpV6MgmtPooledAddr"]
        self.logger(level="debug",
                    message="Fetching " + self.device.metadata.device_type_long + " SDK objects for inventory")

        if self.device.task is not None:
            self.device.task.taskstep_manager.start_taskstep(
                name="FetchInventoryUcsCentralSdkObjects",
                description="Fetching " + self.device.metadata.device_type_long + " SDK Inventory Objects")

        failed_to_fetch = []
        for sdk_object_name in sdk_objects_to_fetch:
            try:
                self.sdk_objects[sdk_object_name] = self.handle.query_classid(sdk_object_name)
                self.logger(level="debug", message="Fetched " + str(len(self.sdk_objects[sdk_object_name])) +
                                                   " objects of class " + sdk_object_name)
            except UcscException as err:
                if err.error_code in ["ERR-xml-parse-error", "0"] and \
                        "no class named " + sdk_object_name in err.error_descr:
                    self.logger(level="debug", message="No " + self.device.metadata.device_type_long +
                                                       " class named " + sdk_object_name)
                else:
                    failed_to_fetch.append(sdk_object_name)
                    self.logger(level="error",
                                message="Error while trying to fetch " + self.device.metadata.device_type_long +
                                        " class " + sdk_object_name + ": " + str(err))
            except ConnectionRefusedError:
                failed_to_fetch.append(sdk_object_name)
                self.logger(level="error",
                            message="Error while communicating with " + self.device.metadata.device_type_long +
                                    " for class " + sdk_object_name + ": Connection refused")
            except urllib.error.URLError:
                failed_to_fetch.append(sdk_object_name)
                self.logger(level="error",
                            message="Timeout error while fetching " + self.device.metadata.device_type_long +
                                    " class " + sdk_object_name)
            except Exception as err:
                failed_to_fetch.append(sdk_object_name)
                self.logger(level="error", message="Error while fetching " + self.device.metadata.device_type_long +
                                                   " class " + sdk_object_name + ": " + str(err))

        # We retry all SDK objects that failed to fetch properly
        if failed_to_fetch:
            duplicate_failed_to_fetch = failed_to_fetch.copy()
            for sdk_object_name in duplicate_failed_to_fetch:
                self.logger(level="info", message="Retrying to fetch " + sdk_object_name)
                try:
                    self.sdk_objects[sdk_object_name] = self.handle.query_classid(sdk_object_name)
                    self.logger(level="debug", message="Fetched " + str(len(self.sdk_objects[sdk_object_name])) +
                                                       " objects of class " + sdk_object_name)
                    failed_to_fetch.remove(sdk_object_name)
                except UcscException as err:
                    self.logger(level="error",
                                message="Error while trying to fetch " + self.device.metadata.device_type_long +
                                        " class " + sdk_object_name + ": " + str(err))
                except ConnectionRefusedError:
                    self.logger(level="error",
                                message="Error while communicating with " + self.device.metadata.device_type_long +
                                        " for class " + sdk_object_name + ": Connection refused")
                except urllib.error.URLError:
                    self.logger(level="error",
                                message="Timeout error while fetching " + self.device.metadata.device_type_long +
                                        " class " + sdk_object_name)
                except Exception as err:
                    self.logger(level="error", message="Error while fetching " + self.device.metadata.device_type_long +
                                                       " class " + sdk_object_name + ": " + str(err))

        # In case we still have SDK objects that failed to fetch, we list them in a warning message
        if failed_to_fetch:
            for sdk_object_name in failed_to_fetch:
                self.logger(level="warning",
                            message="Impossible to fetch " + sdk_object_name + " after 2 attempts.")

        if self.device.task is not None:
            if not failed_to_fetch:
                self.device.task.taskstep_manager.stop_taskstep(
                    name="FetchInventoryUcsCentralSdkObjects", status="successful",
                    status_message="Successfully fetched " + self.device.metadata.device_type_long +
                                   " SDK Inventory Objects")
            elif force:
                self.device.task.taskstep_manager.stop_taskstep(
                    name="FetchInventoryUcsCentralSdkObjects", status="successful",
                    status_message="Fetched " + self.device.metadata.device_type_long +
                                   " SDK Inventory Objects with errors (forced)")
            else:
                self.device.task.taskstep_manager.stop_taskstep(
                    name="FetchInventoryUcsCentralSdkObjects", status="failed",
                    status_message="Error while fetching " + self.device.metadata.device_type_long +
                                   " SDK Inventory Objects")

                # If any of the mandatory tasksteps fails then return False
                if not self.device.task.taskstep_manager.is_taskstep_optional(
                        name="FetchInventoryUcsCentralSdkObjects"):
                    return False

        # Catalog SDK objects
        if self.device.task is not None:
            self.device.task.taskstep_manager.start_taskstep(
                name="FetchInventoryUcsCentralCatalogSdkObjects",
                description="Fetching " + self.device.metadata.device_type_long + " SDK catalog Inventory Objects")

        issue_while_fetching = False
        try:
            self.logger(level="debug", message="Fetching " + self.device.metadata.device_type_long +
                                               " SDK catalog objects for inventory")
            self.sdk_objects["catalog"] = self.handle.query_children(in_dn="capabilities")
            self.sdk_objects["equipmentManufacturingDef"] = self.handle.query_classid("equipmentManufacturingDef")
            self.sdk_objects["equipmentLocalDiskDef"] = self.handle.query_classid("equipmentLocalDiskDef")
        except UcscException as err:
            issue_while_fetching = True
            self.logger(level="error", message="Error while trying to fetch " + self.device.metadata.device_type_long +
                                               " catalog classes: " + str(err))
        except Exception as err:
            issue_while_fetching = True
            self.logger(level="error", message="Unexpected error while trying to fetch " +
                                               self.device.metadata.device_type_long + " catalog classes: " + str(err))

        if self.device.task is not None:
            if not issue_while_fetching:
                self.device.task.taskstep_manager.stop_taskstep(
                    name="FetchInventoryUcsCentralCatalogSdkObjects", status="successful",
                    status_message="Successfully fetched " + self.device.metadata.device_type_long +
                                   " catalog SDK Inventory Objects")
            else:
                self.device.task.taskstep_manager.stop_taskstep(
                    name="FetchInventoryUcsCentralCatalogSdkObjects", status="failed",
                    status_message="Error while fetching " + self.device.metadata.device_type_long +
                                   " catalog SDK Inventory Objects")

                # If any of the mandatory tasksteps fails then return False
                if not self.device.task.taskstep_manager.is_taskstep_optional(
                        name="FetchInventoryUcsCentralCatalogSdkObjects"):
                    return False

        return True
