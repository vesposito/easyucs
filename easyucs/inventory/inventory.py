# coding: utf-8
# !/usr/bin/env python

""" inventory.py: Easy UCS Deployment Tool """
from easyucs import __author__, __copyright__,  __version__, __status__


import re
import time
import uuid
import urllib
import xml

from easyucs.inventory.ucs.chassis import UcsImcSioc
from easyucs.inventory.ucs.neighbor import UcsSystemLanNeighbor, UcsSystemSanNeighbor
from easyucs.inventory.ucs.gpu import UcsImcGpu
from easyucs.inventory.ucs.psu import UcsSystemPsu
from easyucs.inventory.ucs.storage import UcsSystemStorageController, UcsImcStorageControllerNvmeDrive,\
    UcsSystemStorageControllerNvmeDrive, UcsImcStorageRaidBattery

from ucscsdk.ucscexception import UcscException
from ucsmsdk.ucsexception import UcsException
from imcsdk.imcexception import ImcException


class GenericInventory:
    def __init__(self, parent=None):
        self.custom = False
        self.device = parent.parent
        self.device_version = ""
        self.load_from = None
        self.origin = None
        self.status = None
        self.parent = parent
        self.timestamp = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
        self.uuid = uuid.uuid4()

        self._parent_having_logger = self._find_logger()

    def logger(self, level='info', message="No message"):
        if not self._parent_having_logger:
            self._parent_having_logger = self._find_logger()

        if self._parent_having_logger:
            self._parent_having_logger.logger(level=level, message=message)

    def _find_logger(self):
        # Method to find the object having a logger - it can be high up in the hierarchy of objects
        current_object = self
        while hasattr(current_object, 'parent') and not hasattr(current_object, '_logger_handle'):
            current_object = current_object.parent

        if hasattr(current_object, '_logger_handle'):
            return current_object
        else:
            print("WARNING: No logger found in inventory")
            return None

    def __str__(self):
        return str(vars(self))


class GenericUcsInventory(GenericInventory):
    def __init__(self, parent=None):
        GenericInventory.__init__(self, parent=parent)
        self.export_list = None
        self.handle = self.parent.parent.handle
        self.intersight_status = ""
        self.sdk_objects = {}

    def _fetch_sdk_objects(self):
        # List of SDK objects to fetch that are common to UCS System, IMC & UCS Central
        sdk_objects_to_fetch = ["adaptorExtEthIf", "adaptorUnit", "computeRackUnit", "equipmentChassis",
                                "equipmentLocatorLed", "equipmentPsu", "equipmentSystemIOController", "memoryArray",
                                "memoryUnit", "mgmtController", "mgmtIf", "processorUnit", "storageController",
                                "storageEnclosure", "storageFlexFlashController", "storageLocalDisk",
                                "storageRaidBattery"]
        self.logger(level="debug", message="Fetching common UCS SDK objects for inventory")
        for sdk_object_name in sdk_objects_to_fetch:
            try:
                self.sdk_objects[sdk_object_name] = self.handle.query_classid(sdk_object_name)
            except (UcsException, ImcException, UcscException) as err:
                if err.error_code == "ERR-xml-parse-error" and "no class named " + sdk_object_name in err.error_descr:
                    self.logger(level="debug", message="No UCS class named " + sdk_object_name)
                else:
                    self.logger(level="error", message="Error while trying to fetch UCS class " + sdk_object_name +
                                                       ": " + str(err))
            except ConnectionRefusedError:
                self.logger(level="error", message="Error while communicating with UCS class " + sdk_object_name +
                                                   ": Connection refused")
            except urllib.error.URLError:
                self.logger(level="error", message="Timeout error while fetching UCS class " + sdk_object_name)

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
                                if hasattr(sdk_object, "present") and sdk_object.present == "N/A":
                                    continue
                                # Also filter absent storageRaidBattery on standalone servers
                                if hasattr(sdk_object, "battery_present") and sdk_object.battery_present == "false":
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
        self.export_list = ["chassis", "fabric_extenders", "fabric_interconnects", "lan_neighbors", "rack_enclosures",
                            "rack_units", "san_neighbors"]

    def _fetch_sdk_objects(self):
        GenericUcsInventory._fetch_sdk_objects(self)

        # List of SDK objects to fetch that are specific to UCS System
        sdk_objects_to_fetch = ["computeBlade", "equipmentFex", "equipmentFruVariant", "equipmentIOCard",
                                "equipmentRackEnclosure", "equipmentSwitchCard", "equipmentSwitchIOCard",
                                "equipmentTpm", "equipmentXcvr", "etherPIo", "etherServerIntFIo", "etherSwitchIntFIo",
                                "fcPIo", "firmwareRunning", "graphicsCard", "licenseFeature", "licenseFile",
                                "licenseInstance", "licenseServerHostId", "lsServer", "mgmtConnection", "moInvKv",
                                "networkElement", "networkLanNeighborEntry", "networkLldpNeighborEntry",
                                "networkSanNeighborEntry", "storageFlexFlashCard", "storageNvmeStats"]
        self.logger(level="debug", message="Fetching UCS System SDK objects for inventory")
        for sdk_object_name in sdk_objects_to_fetch:
            try:
                self.sdk_objects[sdk_object_name] = self.handle.query_classid(sdk_object_name)
            except (UcsException, ImcException) as err:
                if err.error_code == "ERR-xml-parse-error" and "no class named " + sdk_object_name in err.error_descr:
                    self.logger(level="debug", message="No UCS class named " + sdk_object_name)
                else:
                    self.logger(level="error", message="Error while trying to fetch UCS class " + sdk_object_name +
                                                       ": " + str(err))
            except ConnectionRefusedError:
                self.logger(level="error", message="Error while communicating with UCS class " + sdk_object_name +
                                                   ": Connection refused")
            except urllib.error.URLError:
                self.logger(level="error", message="Timeout error while fetching UCS class " + sdk_object_name)

        # Catalog SDK objects
        try:
            self.sdk_objects["catalog"] = self.handle.query_children(in_dn="capabilities")
            self.sdk_objects["equipmentManufacturingDef"] = self.handle.query_classid("equipmentManufacturingDef")
            self.sdk_objects["equipmentLocalDiskDef"] = self.handle.query_classid("equipmentLocalDiskDef")
        except (UcsException, ImcException) as err:
            self.logger(level="error",
                        message="Error while trying to fetch UCS System catalog classes: " + str(err))

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
                            # We already have an existing EasyUcsLanNeighbor object for this neighbor entry. Finding it
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
                                        EasyUcsLanNeighbor(parent=self,
                                                           ucs_system_lan_neighbor_entry=lan_neighbor_entry,
                                                           ucs_system_fi_eth_port=port,
                                                           group_number=lan_neighbors_group_number[port.pc_id]))
                                else:
                                    lan_neighbors_list.append(
                                        EasyUcsLanNeighbor(parent=self,
                                                           ucs_system_lan_neighbor_entry=lan_neighbor_entry,
                                                           ucs_system_fi_eth_port=port))

                            elif lan_neighbor_entry.system_name in lan_neighbors_system_name_list:
                                # We already have an existing EasyUcsLanNeighbor object for this neighbor. Finding it
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
        self.rack_enclosures = []  # Used for server nodes inside rack enclosures like C4200
        self.rack_units = []
        GenericUcsInventory.__init__(self, parent=parent)

        # List of attributes to be exported in an inventory export
        self.export_list = ["chassis", "rack_enclosures", "rack_units"]

    def _fetch_sdk_objects(self):
        GenericUcsInventory._fetch_sdk_objects(self)

        # List of SDK objects to fetch that are specific to IMC
        sdk_objects_to_fetch = ["adaptorConnectorInfo", "computeServerNode", "equipmentRackEnclosure",
                                "equipmentSharedIOModule", "equipmentTpm", "ioControllerNVMePhysicalDrive",
                                "networkAdapterEthIf", "networkAdapterUnit", "pciEquipSlot", "storageControllerNVMe",
                                "storageEnclosureDisk", "storageFlexFlashControllerProps",
                                "storageFlexFlashPhysicalDrive", "storageLocalDiskProps", "storageNVMePhysicalDrive"]
        self.logger(level="debug", message="Fetching UCS IMC SDK objects for inventory")
        for sdk_object_name in sdk_objects_to_fetch:
            try:
                self.sdk_objects[sdk_object_name] = self.handle.query_classid(sdk_object_name)
            except ImcException as err:
                if err.error_code == "ERR-xml-parse-error" and "no class named " + sdk_object_name in err.error_descr:
                    self.logger(level="debug", message="No UCS IMC class named " + sdk_object_name)
                else:
                    self.logger(level="error", message="Error while trying to fetch UCS IMC class " + sdk_object_name +
                                                       ": " + str(err))
            # Prevent rare exception due to Server Error return when fetching UCS IMC class
            except xml.etree.ElementTree.ParseError as err:
                self.logger(level="error", message="Error while trying to fetch UCS IMC class " + sdk_object_name +
                                                   ": " + str(err))

        # Catalog SDK objects
        try:
            compute_boards = self.handle.query_classid("computeBoard")
            self.logger(level="debug",
                        message="Found " + str(len(compute_boards)) + " computeBoard object(s) for catalog")
            self.sdk_objects["catalog"] = []
            for compute_board in compute_boards:
                self.sdk_objects["catalog"].extend(self.handle.query_children(in_dn=compute_board.dn + "/pid"))

            self.logger(level="debug", message="Catalog has " + str(len(self.sdk_objects["catalog"])) + " objects")

        except ImcException as err:
            self.logger(level="error",
                        message="Error while trying to fetch UCS IMC catalog classes: " + str(err))


class UcsCentralInventory(GenericUcsInventory):
    def __init__(self, parent=None):
        self.domains = []
        GenericUcsInventory.__init__(self, parent=parent)

        # List of attributes to be exported in an inventory export
        self.export_list = ["domains"]

    def _fetch_sdk_objects(self):
        GenericUcsInventory._fetch_sdk_objects(self)

        # List of SDK objects to fetch that are specific to UCS Central
        sdk_objects_to_fetch = ["computeBlade", "computeSystem", "equipmentFex", "equipmentFruVariant",
                                "equipmentIOCard", "equipmentSwitchCard", "equipmentSwitchIOCard", "equipmentXcvr",
                                "etherPIo", "etherServerIntFIo", "etherSwitchIntFIo", "fcPIo", "firmwareRunning",
                                "graphicsCard", "licenseFeature", "licenseFile", "licenseInstance",
                                "licenseServerHostId", "lsServer", "mgmtConnection", "networkElement",
                                "storageFlexFlashCard", "storageNvmeStats"]
        self.logger(level="debug", message="Fetching UCS Central SDK objects for inventory")
        for sdk_object_name in sdk_objects_to_fetch:
            try:
                self.sdk_objects[sdk_object_name] = self.handle.query_classid(sdk_object_name)
            except UcscException as err:
                if err.error_code == "ERR-xml-parse-error" and "no class named " + sdk_object_name in err.error_descr:
                    self.logger(level="debug", message="No UCS class named " + sdk_object_name)
                else:
                    self.logger(level="error", message="Error while trying to fetch UCS class " + sdk_object_name +
                                                       ": " + str(err))
            except ConnectionRefusedError:
                self.logger(level="error", message="Error while communicating with UCS class " + sdk_object_name +
                                                   ": Connection refused")
            except urllib.error.URLError:
                self.logger(level="error", message="Timeout error while fetching UCS class " + sdk_object_name)

        # Catalog SDK objects
        try:
            self.sdk_objects["catalog"] = self.handle.query_children(in_dn="capabilities")
            self.sdk_objects["equipmentManufacturingDef"] = self.handle.query_classid(
                "equipmentManufacturingDef")
            self.sdk_objects["equipmentLocalDiskDef"] = self.handle.query_classid("equipmentLocalDiskDef")
        except UcscException as err:
            self.logger(level="error",
                        message="Error while trying to fetch UCS Central catalog classes: " + str(err))
