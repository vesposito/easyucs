# coding: utf-8
# !/usr/bin/env python

""" inventory.py: Easy UCS Deployment Tool """
import urllib3
from intersight.api.adapter_api import AdapterApi
from intersight.api.asset_api import AssetApi
from intersight.api.compute_api import ComputeApi
from intersight.api.equipment_api import EquipmentApi
from intersight.api.ether_api import EtherApi
from intersight.api.fc_api import FcApi
from intersight.api.firmware_api import FirmwareApi
from intersight.api.graphics_api import GraphicsApi
from intersight.api.management_api import ManagementApi
from intersight.api.memory_api import MemoryApi
from intersight.api.network_api import NetworkApi
from intersight.api.pci_api import PciApi
from intersight.api.port_api import PortApi
from intersight.api.processor_api import ProcessorApi
from intersight.api.storage_api import StorageApi
from intersight.api.top_api import TopApi
from intersight.exceptions import ApiValueError, ApiTypeError, ApiException

from inventory.inventory import GenericInventory


class IntersightInventory(GenericInventory):
    def __init__(self, parent=None):
        GenericInventory.__init__(self, parent=parent)

        self.export_list = None
        self.handle = self.parent.parent.handle
        self.sdk_objects = {}

        self.imm_domains = []
        self.rack_units = []
        self.ucsm_domains = []

        # List of attributes to be exported in an inventory export
        self.export_list = ["imm_domains", "rack_units", "ucsm_domains"]

    def _fetch_sdk_objects(self, force=False):
        MAX_OBJECTS_PER_FETCH_CALL = 1000

        sdk_objects_to_fetch = [
            {AdapterApi: ["adapter_ext_eth_interface", "adapter_unit", "adapter_unit_expander"]},
            {AssetApi: ["asset_device_registration"]},
            {ComputeApi: ["compute_blade", "compute_board", "compute_rack_unit"]},
            {EquipmentApi: ["equipment_chassis", "equipment_expander_module", "equipment_fex", "equipment_io_card",
                            "equipment_locator_led", "equipment_psu", "equipment_switch_card", "equipment_tpm",
                            "equipment_transceiver"]},
            {EtherApi: ["ether_host_port", "ether_network_port", "ether_physical_port"]},
            {FcApi: ["fc_physical_port"]},
            {FirmwareApi: ["firmware_running_firmware"]},
            {GraphicsApi: ["graphics_card"]},
            {ManagementApi: ["management_controller", "management_interface"]},
            {MemoryApi: ["memory_array", "memory_unit"]},
            {NetworkApi: ["network_element"]},
            {PciApi: ["pci_node"]},
            {PortApi: ["port_group", "port_sub_group"]},
            {ProcessorApi: ["processor_unit"]},
            {StorageApi: ["storage_battery_backup_unit", "storage_controller", "storage_physical_disk"]},
            {TopApi: ["top_system"]}
        ]
        self.logger(level="debug",
                    message="Fetching " + self.device.metadata.device_type_long + " objects for inventory")

        if self.device.task is not None:
            self.device.task.taskstep_manager.start_taskstep(
                name="FetchInventoryIntersightSdkObjects",
                description="Fetching " + self.device.metadata.device_type_long + " SDK Inventory Objects")

        issue_while_fetching = False
        for sdk_dict in sdk_objects_to_fetch:
            for api_name, sdk_objects_list in sdk_dict.items():
                api = api_name(api_client=self.handle)
                for sdk_object in sdk_objects_list:
                    self.sdk_objects[sdk_object] = []
                    # TODO: Handle retry in case of ApiException
                    try:
                        # We first query the API to get the number of objects that will be returned
                        count_response = getattr(api, "get_" + sdk_object + "_list")(
                            count=True, _request_timeout=self.device.timeout)
                        if count_response:
                            count_value = count_response["count"]
                            if count_value == 0:
                                self.sdk_objects[sdk_object] = []
                            elif count_value <= MAX_OBJECTS_PER_FETCH_CALL:
                                self.sdk_objects[sdk_object] = getattr(api, "get_" + sdk_object + "_list")(
                                    top=MAX_OBJECTS_PER_FETCH_CALL,
                                    _request_timeout=self.device.timeout).results
                            else:
                                self.logger(level="debug", message=str(count_value) + " objects of class " +
                                            sdk_object + " are to be fetched using pagination")
                                start_value = 0
                                while start_value < count_value:
                                    self.sdk_objects[sdk_object] += getattr(api, "get_" + sdk_object + "_list")(
                                        skip=start_value, top=MAX_OBJECTS_PER_FETCH_CALL,
                                        _request_timeout=self.device.timeout).results
                                    start_value += MAX_OBJECTS_PER_FETCH_CALL

                            self.logger(level="debug",
                                        message="Fetched " + str(len(self.sdk_objects[sdk_object])) +
                                                " objects of class " + sdk_object)

                        else:
                            self.sdk_objects[sdk_object] = getattr(
                                api, "get_" + sdk_object + "_list")(_request_timeout=self.device.timeout).results
                    except (ApiValueError, ApiTypeError, ApiException) as err:
                        issue_while_fetching = True
                        self.logger(level="error",
                                    message="Failed to fetch objects of class " + sdk_object + ": " + str(err))
                    except AttributeError as err:
                        issue_while_fetching = True
                        self.logger(level="error",
                                    message="Failed to fetch objects of class " + sdk_object + ": " + str(err))
                    except urllib3.exceptions.MaxRetryError as err:
                        issue_while_fetching = True
                        self.logger(level="error",
                                    message="Failed to fetch objects of class " + sdk_object + ": " + str(err))

        if self.device.task is not None:
            if not issue_while_fetching:
                self.device.task.taskstep_manager.stop_taskstep(
                    name="FetchInventoryIntersightSdkObjects", status="successful",
                    status_message="Successfully fetched " + self.device.metadata.device_type_long +
                                   " SDK Inventory Objects")
            elif force:
                self.device.task.taskstep_manager.stop_taskstep(
                    name="FetchInventoryIntersightSdkObjects", status="successful",
                    status_message="Fetched " + self.device.metadata.device_type_long +
                                   " SDK Inventory Objects with errors (forced)")
            else:
                self.device.task.taskstep_manager.stop_taskstep(
                    name="FetchInventoryIntersightSdkObjects", status="failed",
                    status_message="Error while fetching " + self.device.metadata.device_type_long +
                                   " SDK Inventory Objects")

                # If any of the mandatory tasksteps fails then return False
                if not self.device.task.taskstep_manager.is_taskstep_optional(
                        name="FetchInventoryIntersightSdkObjects"):
                    return False

        return True
