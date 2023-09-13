# coding: utf-8
# !/usr/bin/env python

""" inventory.py: Easy UCS Deployment Tool """
import urllib3

from inventory.inventory import GenericInventory

from intersight.api.compute_api import ComputeApi
from intersight.api.equipment_api import EquipmentApi
from intersight.api.network_api import NetworkApi
from intersight.api.top_api import TopApi
from intersight.exceptions import ApiValueError, ApiTypeError, ApiException


class IntersightInventory(GenericInventory):
    def __init__(self, parent=None):
        GenericInventory.__init__(self, parent=parent)

        self.export_list = None
        self.handle = self.parent.parent.handle
        self.sdk_objects = {}

        self.rack_units = []
        self.ucsm_domains = []

        # List of attributes to be exported in an inventory export
        self.export_list = ["rack_units", "ucsm_domains"]

    def _fetch_sdk_objects(self, force=False):
        MAX_OBJECTS_PER_FETCH_CALL = 100

        sdk_objects_to_fetch = [{ComputeApi: ["compute_rack_unit", "compute_blade"]},
                                {EquipmentApi: ["equipment_locator_led", "equipment_psu"]},
                                {NetworkApi: ["network_element"]},
                                {TopApi: ["top_system"]}]
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
                                self.sdk_objects[sdk_object] = getattr(
                                    api, "get_" + sdk_object + "_list")(_request_timeout=self.device.timeout).results
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
                                            message=str(len(self.sdk_objects[sdk_object])) + " objects of class " +
                                            sdk_object + " have been fetched")

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
