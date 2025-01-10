
from cache.cache import GenericCache
import os
import common
from intersight.api.organization_api import OrganizationApi
from intersight.exceptions import OpenApiException


class IntersightCache(GenericCache):
    def __init__(self, parent=None):
        GenericCache.__init__(self, parent=parent)

        self.server_details = None
        self.orgs = {"default": ""}
        self.os_firmware_data = None

    def fetch_server_details(self):
        """
        TODO: Implement the logic to fetch server details for Intersight devices in the future.
        """
        pass

    def fetch_orgs(self):
        """
        Fetches the Intersight Organizations
        :return: Org list if successful, None otherwise
        """
        if self.device.task is not None:
            self.device.task.taskstep_manager.start_taskstep(name="FetchOrgs",
                                                             description="Fetching Intersight Organizations")

        cached_orgs = {
            "timestamp": common.get_timestamp(),
        }
        org_api = OrganizationApi(api_client=self.device.handle)
        try:
            orgs = org_api.get_organization_organization_list(expand="ResourceGroups,SharedWithResources",
                                                              _request_timeout=self.device.timeout, orderby="Name")

        except OpenApiException as err:
            self.logger(level="error", message=f"Unable to get the list of Orgs (with SharedWithResources): {err}")
            try:
                orgs = org_api.get_organization_organization_list(expand="ResourceGroups",
                                                                  _request_timeout=self.device.timeout, orderby="Name")
            except OpenApiException as err:
                message_str = f"Unable to get the list of Orgs: {err}"
                self.logger(level="error", message=message_str)
                if self.device.task is not None:
                    self.device.task.taskstep_manager.stop_taskstep(
                        name="FetchOrgs", status="failed",
                        status_message=message_str[:255])
                return None

        if not orgs.results:
            message_str = "No org found"
            self.logger(level="error", message=message_str)
            if self.device.task is not None:
                self.device.task.taskstep_manager.stop_taskstep(
                    name="FetchOrgs", status="failed",
                    status_message=message_str[:255])
            return None

        for result in orgs.results:
            cached_orgs[result.name] = {
                "description": result.description,
                "is_shared": False,
                "resource_groups": [],
                "shared_with_orgs": []
            }
            if result.resource_groups:
                cached_orgs[result.name]["resource_groups"] = [rg.name for rg in result.resource_groups]
            if getattr(result, "shared_with_resources", None):
                cached_orgs[result.name]["shared_with_orgs"] = [
                    resource.name for resource in getattr(result, "shared_with_resources", [])
                    if resource.object_type == "organization.Organization"
                ]
                if cached_orgs[result.name]["shared_with_orgs"]:
                    cached_orgs[result.name]["is_shared"] = True

        self.orgs = cached_orgs
        if self.device.task is not None:
            self.device.task.taskstep_manager.stop_taskstep(
                name="FetchOrgs", status="successful",
                status_message="Successfully fetched Organizations from Intersight")

        return cached_orgs

    def fetch_os_firmware_data(self):
        """
        Function to get the OS and Firmware metadata
        :return: A dictionary containing OS and Firmware data, None otherwise
        """
        if self.device.task is not None:
            self.device.task.taskstep_manager.start_taskstep(name="FetchOSFirmwareDataObjectsIntersight",
                                                             description="Fetching OS and Firmware Objects")

        result = {
            "timestamp": common.get_timestamp(),
            "os": {},
            "firmware": []
        }
        operating_system_vendors = self.device.query(object_type="hcl.OperatingSystemVendor")
        operating_systems = self.device.query(object_type="hcl.OperatingSystem")
        operating_system_distributions = self.device.query(object_type="os.Distribution")
        firmware_distributables = self.device.query(object_type="firmware.Distributable", filter="Origin eq System")

        if not all([True if obj else False for obj in [operating_system_vendors, operating_systems,
                                                       operating_system_distributions, firmware_distributables]]):
            if self.device.task is not None:
                self.device.task.taskstep_manager.stop_taskstep(
                    name="FetchOSFirmwareDataObjectsIntersight", status="failed",
                    status_message="Error while fetching OS and Firmware Objects from Intersight")
            return None

        if not hasattr(operating_system_distributions[0], "vendor") or not hasattr(operating_system_distributions[0],
                                                                                   "label"):
            use_hcl_os = True
        else:
            use_hcl_os = False

        for os_vendor in operating_system_vendors:
            result["os"][os_vendor.name] = []
            if not use_hcl_os:
                for os_distribution in operating_system_distributions:
                    if os_distribution.vendor.moid == os_vendor.moid:
                        result["os"][os_vendor.name].append(os_distribution.label)
            else:
                for hcl_os in operating_systems:
                    if hcl_os.vendor.moid == os_vendor.moid:
                        result["os"][os_vendor.name].append(hcl_os.version)
            result["os"][os_vendor.name].sort()

        for firmware_distributable in firmware_distributables:
            result["firmware"].append({
                "firmware_image_type": firmware_distributable.image_type,
                "name": firmware_distributable.name,
                "supported_models": firmware_distributable.supported_models,
                "version": firmware_distributable.version
            })

        if self.device.task is not None:
            self.device.task.taskstep_manager.stop_taskstep(
                name="FetchOSFirmwareDataObjectsIntersight", status="successful",
                status_message="Successfully fetched OS and Firmware objects from Intersight")

        self.os_firmware_data = result

        return result

    def get_os_firmware_data(self):
        """
        Function to get the OS and Firmware data from the device
        :return: Returns dictionary containing OS and Firmware data, None otherwise
        """

        return self.os_firmware_data

    def get_orgs(self):
        """
        Function to get the OS and Firmware data from the device
        :return: Returns dictionary containing orgs data
        """

        return self.orgs
