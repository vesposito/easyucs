# coding: utf-8
# !/usr/bin/env python

""" inventory.py: Easy UCS Deployment Tool """

import re
import urllib
import xml
import xml.etree.ElementTree as ET

from imcsdk.imcexception import ImcException
from ucscsdk.ucscexception import UcscException
from ucsmsdk.ucscoremeta import UcsVersion
from ucsmsdk.ucsexception import UcsException
from ucsmsdk import ucscoreutils

from config.ucs.config import _load_mo_from_xml_element

from inventory.inventory import GenericInventory
from inventory.ucs.adaptor import UcsImcHbaAdapter
from inventory.ucs.chassis import UcsImcSioc
from inventory.ucs.gpu import UcsImcGpu
from inventory.ucs.neighbor import UcsSystemLanNeighbor, UcsSystemSanNeighbor
from inventory.ucs.psu import UcsSystemPsu
from inventory.ucs.storage import UcsSystemStorageController, UcsImcStorageControllerNvmeDrive, \
    UcsSystemStorageControllerNvmeDrive, UcsImcStorageLocalDisk, UcsImcStorageNvmeDrive, UcsImcStorageRaidBattery


class GenericUcsInventory(GenericInventory):
    # List of SDK objects to fetch that are common to UCS System, IMC & UCS Central
    _COMMON_SDK_OBJECTS_TO_FETCH = [
        "adaptorExtEthIf", "adaptorHostEthIf", "adaptorUnit", "computeRackUnit",
        "equipmentChassis", "equipmentLocatorLed", "equipmentPsu",
        "equipmentSystemIOController", "memoryArray", "memoryUnit", "mgmtController", "mgmtIf",
        "processorUnit", "storageController", "storageEnclosure", "storageFlexFlashController",
        "storageLocalDisk", "storageRaidBattery",
    ]

    def __init__(self, parent=None):
        GenericInventory.__init__(self, parent=parent)
        self.export_list = None
        self.handle = self.parent.parent.handle
        self.intersight_status = ""
        self.sdk_objects = {}

    def _fetch_sdk_objects(self, force=False):
        sdk_objects_to_fetch = self._COMMON_SDK_OBJECTS_TO_FETCH
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
                                    # Keep physically removed servers in inventory for pre-assignment validation
                                    if object_class._UCS_SDK_OBJECT_NAME in \
                                            ["computeBlade", "computeRackUnit", "computeServerNode"]:
                                        # Log if server is physically removed from the UCSM domain
                                        if hasattr(sdk_object, "oper_state") and \
                                                sdk_object.oper_state == "removed":
                                            self.logger(
                                                level="info",
                                                message="Found server with serial number '" +
                                                        str(getattr(sdk_object, "serial", "N/A")) +
                                                        "' that is physically removed from the UCSM domain"
                                            )
                                            # Fall through: keep this removed server in the inventory
                                        else:
                                            continue  # Missing for other reasons — retain original filter
                                    else:
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
                                # Also filter storageControllerNVMe of types PCIe-Switch, NVMe-direct-U.2-drives,
                                # NVMe-direct-HHHL-drives or NVMe-direct-E3.S-drives
                                if object_class is UcsImcStorageControllerNvmeDrive and hasattr(sdk_object, "id"):
                                    if any(x in sdk_object.id for x in ["PCIe-Switch", "NVMe-direct-U.2-drives",
                                                                        "NVMe-direct-HHHL-drives",
                                                                        "NVMe-direct-E3.S-drives"]):
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
                                if object_class is UcsImcHbaAdapter and sdk_object.id in ["MRAID", "MRAID1", "MRAID2"]:
                                    continue

                                filtered_sdk_objects_list.append(sdk_object)
                            # Handle the case of LAN/SAN Neighbor objects for which we use fiPortDn attribute
                            elif hasattr(sdk_object, "fi_port_dn"):
                                if dn == sdk_object.fi_port_dn:
                                    filtered_sdk_objects_list.append(sdk_object)

                            # Handle the case of PCIe Nodes GPUs objects for which we use enclosureDn attribute
                            elif hasattr(sdk_object, "enclosure_dn") and "/pcie-node-" in dn:
                                if dn == sdk_object.enclosure_dn:
                                    filtered_sdk_objects_list.append(sdk_object)

                        easyucs_objects_list = []
                        for sdk_object in sorted(filtered_sdk_objects_list,
                                                 key=lambda sdk_obj: [int(t) if t.isdigit() else t.lower()
                                                                      for t in re.split(r'(\d+)', sdk_obj.dn)]):
                            # We instantiate an Inventory Object for each corresponding SDK object
                            easyucs_objects_list.append(object_class(parent, sdk_object))
                        return easyucs_objects_list
        return []

    def find_server_from_serial(self, serial):
        """
        Searches for a server (blade / rack unit / server node) in the inventory by serial number.
        For UcsCentralInventory, servers are nested inside domains so each domain is searched in turn.
        For UcsSystemInventory / UcsImcInventory, chassis, rack_units and rack_enclosures sit directly on self.
        :param serial: The serial number to look up.
        :return: The matching inventory server object if found, None otherwise.
        """
        if not serial:
            return None
        for container in (getattr(self, "domains", None) or [self]):
            all_servers = (
                [blade for chassis in getattr(container, "chassis", [])
                 for blade in getattr(chassis, "blades", [])]
                + list(getattr(container, "rack_units", []))
                + [server_node for rack_enclosure in getattr(container, "rack_enclosures", [])
                   for server_node in getattr(rack_enclosure, "server_nodes", [])]
            )
            result = next((server for server in all_servers if getattr(server, "serial", None) == serial), None)
            if result:
                return result
        return None


class UcsSystemInventory(GenericUcsInventory):
    _UCSM_SPECIFIC_SDK_OBJECTS_TO_FETCH = [
        "adaptorUnitExtn", "computeBlade", "computePersonality", "equipmentCrossFabricModule",
        "equipmentFex", "equipmentFruVariant", "equipmentIOCard", "equipmentPcieNode",
        "equipmentRackEnclosure", "equipmentSwitchCard", "equipmentSwitchIOCard",
        "equipmentTpm", "equipmentXcvr", "etherPIo", "etherServerIntFIo", "etherSwitchIntFIo",
        "fcPIo", "firmwareRunning", "firmwareStatus", "graphicsCard", "licenseFeature",
        "licenseFile", "licenseInstance", "licenseServerHostId", "lsServer", "memoryErrorStats",
        "mgmtConnection", "mgmtInterface", "mgmtVnet", "moInvKv", "networkElement",
        "networkLanNeighborEntry", "networkLldpNeighborEntry", "networkSanNeighborEntry",
        "storageEmbeddedStorage", "storageFlexFlashCard", "storageNvmeStats",
        "storageSsdHealthStats", "swVlanPortNs", "topInfoPolicy", "vnicIpV4MgmtPooledAddr",
        "vnicIpV4PooledAddr", "vnicIpV4StaticAddr", "vnicIpV6StaticAddr", "vnicIpV6MgmtPooledAddr",
    ]

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
        sdk_objects_to_fetch = self._UCSM_SPECIFIC_SDK_OBJECTS_TO_FETCH
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

    def _fetch_sdk_objects_from_xml(self, xml_file_path, force=False):
        """
        Alternative to _fetch_sdk_objects() that populates self.sdk_objects by
        parsing a UCSM MIT XML dump file (e.g. mit.xml from a tech-support bundle)
        instead of making live API calls via ucsmsdk.

        :param xml_file_path: Path to the MIT XML file to parse.
        :param force: If True, tolerate parse errors and continue. If False, any
                      XML parse error causes the method to return False.
        :return: True if successful, False otherwise.
        """
        # Full set of class names to extract — the union of the common base list,
        # and all UCS System-specific inventory classes.
        # Note: equipmentManufacturingDef and equipmentLocalDiskDef have DNs under
        # capabilities/ in the MIT XML, so they are collected via the catalog path below.
        sdk_objects_to_fetch = set(
            self._COMMON_SDK_OBJECTS_TO_FETCH +
            self._UCSM_SPECIFIC_SDK_OBJECTS_TO_FETCH
        )

        self.logger(level="debug",
                    message="Fetching " + self.device.metadata.device_type_long + " SDK objects from XML file: " +
                            str(xml_file_path))

        if self.device.task is not None:
            # The XML fetch reads all classes (common, UCSM-specific, and catalog)
            # in a single pass, replacing the three live-fetch steps.  Skip the
            # common and catalog steps so the sequence advances to the UCSM step.
            self.device.task.taskstep_manager.skip_taskstep(
                name="FetchInventoryUcsCommonSdkObjects",
                status_message="Skipped - all inventory SDK objects are fetched together from XML file")
            self.device.task.taskstep_manager.start_taskstep(
                name="FetchInventoryUcsSystemSdkObjects",
                description="Fetching " + self.device.metadata.device_type_long +
                            " SDK Inventory Objects from XML file")

        # Pre-build the class cache: only load SDK classes that are in our target
        # set and are known to ucsmsdk. Classes absent from the SDK are skipped.
        mo_class_cache = {}
        for class_id in sdk_objects_to_fetch:
            try:
                mo_class_cache[class_id] = ucscoreutils.load_class(class_id)
            except Exception:
                self.logger(level="debug", message="No ucsmsdk class for " + class_id + ", skipping")

        # Single-pass iterparse over the flat MIT XML structure.
        parse_error = False
        firmware_package_version = None
        catalog_objects = []
        catalog_class_cache = {}
        try:
            for event, elem in ET.iterparse(xml_file_path, events=('end',)):
                if elem.tag == 'topRoot':
                    elem.clear()
                    continue
                # Opportunistically capture the system firmware version.
                # Primary source: firmwareRunning MO at dn="sys/mgmt/fw-system".
                # Fallback: versionApplication MO at dn="sys/version/application".
                if elem.tag == 'firmwareRunning' and elem.get('dn') == 'sys/mgmt/fw-system':
                    firmware_package_version = elem.get('version')
                elif (elem.tag == 'versionApplication' and elem.get('dn') == 'sys/version/application' and
                      not firmware_package_version):
                    firmware_package_version = elem.get('version')
                # Collect capability provider objects (live equivalent: query_children(in_dn="capabilities"))
                if (elem.get('dn') or '').startswith('capabilities/'):
                    if elem.tag not in catalog_class_cache:
                        try:
                            catalog_class_cache[elem.tag] = ucscoreutils.load_class(elem.tag)
                        except Exception:
                            catalog_class_cache[elem.tag] = None
                    mo_class = catalog_class_cache[elem.tag]
                    if mo_class is not None:
                        try:
                            catalog_objects.append(_load_mo_from_xml_element(mo_class, elem))
                        except Exception as err:
                            self.logger(level="warning",
                                        message="Error instantiating catalog MO " + elem.tag + " from XML: " + str(err))
                elif elem.tag in mo_class_cache:
                    try:
                        mo = _load_mo_from_xml_element(mo_class_cache[elem.tag], elem)
                        self.sdk_objects.setdefault(elem.tag, []).append(mo)
                    except Exception as err:
                        self.logger(level="warning",
                                    message="Error instantiating " + elem.tag + " MO from XML: " + str(err))
                elem.clear()
        except ET.ParseError as err:
            parse_error = True
            self.logger(level="error",
                        message="XML parse error while reading " + str(xml_file_path) + ": " + str(err))

        # Classes absent from the XML are left out of sdk_objects entirely,
        # mirroring live behaviour where absent classes are never inserted.
        # Catalog objects (from capabilities/ DN subtree) are stored under a special key.
        if catalog_objects:
            self.sdk_objects["catalog"] = catalog_objects
            self.logger(level="debug",
                        message="Loaded " + str(len(catalog_objects)) + " catalog objects from XML capabilities/ subtree")
            # _find_equipment_manufacturing_def() and _find_equipment_local_disk_def() look in
            # their own sdk_objects keys (populated by query_classid() in the live path).
            # Since these MOs live under capabilities/ in the XML they end up only in catalog_objects,
            # so we must also expose them under their class-name keys.
            mfg_defs = [o for o in catalog_objects if getattr(o, '_class_id', '') == 'EquipmentManufacturingDef']
            if mfg_defs:
                self.sdk_objects["equipmentManufacturingDef"] = mfg_defs
            local_disk_defs = [o for o in catalog_objects if getattr(o, '_class_id', '') == 'EquipmentLocalDiskDef']
            if local_disk_defs:
                self.sdk_objects["equipmentLocalDiskDef"] = local_disk_defs
        else:
            self.logger(level="warning",
                        message="No catalog objects found in XML; SKU/name lookup will fall back to model number")

        # Set device version from the firmwareRunning MO at sys/mgmt/fw-system or
        # versionApplication MO at sys/version/application so that version-gated
        # logic (e.g. firmware version comparisons) works correctly without a live connection.
        # The version attribute is already a clean string like "4.1(3c)" with no suffix stripping needed.
        if firmware_package_version:
            try:
                self.device.version = UcsVersion(firmware_package_version)
                if hasattr(self.device.version, 'version'):
                    self.device.metadata.device_version = self.device.version.version
                self.logger(level="debug",
                            message="Set device version from XML: " + firmware_package_version)
            except Exception as err:
                self.logger(level="warning",
                            message="Could not parse firmware version '" + firmware_package_version + "': " + str(err))
        else:
            self.logger(level="warning",
                        message="Could not find firmwareRunning (sys/mgmt/fw-system) or versionApplication "
                                "(sys/version/application) MO in XML; device version will not be set")

        if parse_error and not force:
            if self.device.task is not None:
                self.device.task.taskstep_manager.stop_taskstep(
                    name="FetchInventoryUcsSystemSdkObjects", status="failed",
                    status_message="XML parse error while fetching " +
                                   self.device.metadata.device_type_long + " SDK Inventory Objects")
                if not self.device.task.taskstep_manager.is_taskstep_optional(
                        name="FetchInventoryUcsSystemSdkObjects"):
                    return False
            return False

        self.logger(level="debug",
                    message="Finished reading XML file. Loaded " +
                            str(sum(len(v) for v in self.sdk_objects.values())) +
                            " SDK objects across " +
                            str(sum(1 for v in self.sdk_objects.values() if v)) + " classes.")

        if self.device.task is not None:
            self.device.task.taskstep_manager.stop_taskstep(
                name="FetchInventoryUcsSystemSdkObjects", status="successful",
                status_message="Successfully fetched " + self.device.metadata.device_type_long +
                               " SDK Inventory Objects from XML file")
            # The XML pass also collects catalog objects in the same iteration, so
            # skip the separate live-fetch step that would normally follow.
            self.device.task.taskstep_manager.skip_taskstep(
                name="FetchInventoryUcsSystemCatalogSdkObjects",
                status_message="Skipped - catalog objects are collected together from XML file")

        # Apply the same natural-sort-by-DN as the live fetch
        for value in self.sdk_objects.values():
            value.sort(key=lambda obj: [int(t) if t.isdigit() else t.lower()
                                        for t in re.split(r'(\d+)', obj.dn or '')])

        return True


class UcsImcInventory(GenericUcsInventory):
    _IMC_SPECIFIC_SDK_OBJECTS_TO_FETCH = [
        "adaptorConnectorInfo", "computeServerNode", "equipmentRackEnclosure",
        "equipmentSharedIOModule", "equipmentTpm", "gpuInventory",
        "ioControllerNVMePhysicalDrive", "ioExpander", "networkAdapterEthIf",
        "networkAdapterUnit", "pciAdapterFruInventory", "pciAdapterFruInventoryInfo",
        "pciEquipSlot", "storageControllerNVMe", "storageEnclosureDisk",
        "storageFlexFlashControllerProps", "storageFlexFlashPhysicalDrive",
        "storageLocalDiskProps", "storageNVMePhysicalDrive", "systemBoardUnit"
    ]

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
        sdk_objects_to_fetch = self._IMC_SPECIFIC_SDK_OBJECTS_TO_FETCH
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
    _CENTRAL_SPECIFIC_SDK_OBJECTS_TO_FETCH = [
        "computeBlade", "computeSystem", "equipmentFex", "equipmentFruVariant",
        "equipmentIOCard", "equipmentSwitchCard", "equipmentSwitchIOCard", "equipmentXcvr",
        "etherPIo", "etherServerIntFIo", "etherSwitchIntFIo", "fcPIo", "firmwareRunning",
        "firmwareStatus", "graphicsCard", "licenseFeature", "licenseFile", "licenseInstance",
        "licenseServerHostId", "lsServer", "mgmtConnection", "mgmtInterface", "mgmtVnet",
        "networkElement", "storageFlexFlashCard", "storageNvmeStats", "storageSsdHealthStats",
        "vnicIpV4MgmtPooledAddr", "vnicIpV4PooledAddr", "vnicIpV4StaticAddr",
        "vnicIpV6StaticAddr", "vnicIpV6MgmtPooledAddr"
    ]

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
        sdk_objects_to_fetch = self._CENTRAL_SPECIFIC_SDK_OBJECTS_TO_FETCH
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
