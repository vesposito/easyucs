# coding: utf-8
# !/usr/bin/env python

""" device.py: Easy UCS Deployment Tool """

import datetime
import importlib
import json
import os
import re
import requests
import urllib3
import base64

import intersight.signing

from intersight.api.appliance_api import ApplianceApi
from intersight.api.organization_api import OrganizationApi
from intersight.api.iam_api import IamApi
from intersight.api.feedback_api import FeedbackApi
from intersight.api_client import ApiClient
from intersight.configuration import Configuration
from intersight.exceptions import ApiValueError, ApiTypeError, ApiException, OpenApiException
from intersight import __version__ as intersight_sdk_version

import common
from config.intersight.manager import IntersightConfigManager
from config.intersight.object import IntersightConfigObject
from config.intersight.server_profiles import IntersightUcsServerProfile, IntersightUcsServerProfileTemplate
from device.device import GenericDevice
from inventory.intersight.manager import IntersightInventoryManager
from report.intersight.manager import IntersightReportManager
from repository.manager import RepositoryManager

urllib3.disable_warnings()


class IntersightDevice(GenericDevice):
    INTERSIGHT_APPLIANCE_MIN_REQUIRED_VERSION = "1.0.9-615"

    def __init__(self, parent=None, uuid=None, target="www.intersight.com", key_id="", private_key_path="",
                 is_hidden=False, is_system=False, system_usage=None, proxy=None, proxy_user=None, proxy_password=None,
                 logger_handle_log_level="info", log_file_path=None, bypass_version_checks=False):

        self.key_id = key_id
        self.private_key_path = private_key_path

        GenericDevice.__init__(self, parent=parent, uuid=uuid, target=target, password="", user="",
                               is_hidden=is_hidden, is_system=is_system, system_usage=system_usage,
                               logger_handle_log_level=logger_handle_log_level, log_file_path=log_file_path,
                               bypass_version_checks=bypass_version_checks)

        self.handle = None
        self.is_appliance = False
        self.name = target
        # Setting the max timeout of 5min for Intersight Connection Failure.
        self.timeout = 5
        self.version_sdk = str(intersight_sdk_version)

        self.metadata.device_type = "intersight"
        if any(target.endswith(x) for x in ["intersight.com", "starshipcloud.com"]):
            self.metadata.device_type_long = "Intersight SaaS"
        elif target in [None, self.metadata.device_type + "_catalog.easyucs"]:
            self.metadata.device_type_long = "Intersight"
        else:
            self.metadata.device_type_long = "Intersight Appliance"
            self.is_appliance = True

        if key_id and private_key_path:
            with open(self.private_key_path, 'r') as f:
                private_key = f.read()

            if re.search('BEGIN RSA PRIVATE KEY', private_key):
                # API Key v2 format
                signing_algorithm = intersight.signing.ALGORITHM_RSASSA_PKCS1v15
                signing_scheme = intersight.signing.SCHEME_RSA_SHA256
                hash_algorithm = intersight.signing.HASH_SHA256

            elif re.search('BEGIN EC PRIVATE KEY', private_key):
                # API Key v3 format
                signing_algorithm = intersight.signing.ALGORITHM_ECDSA_MODE_DETERMINISTIC_RFC6979
                signing_scheme = intersight.signing.SCHEME_HS2019
                hash_algorithm = intersight.signing.HASH_SHA256

            else:
                raise Exception("Invalid Private Key. It does not correspond to an API Key for OpenAPI schema version "
                                "2 or 3.")

            signing_info = intersight.signing.HttpSigningConfiguration(
                key_id=key_id,
                private_key_path=private_key_path,
                signing_scheme=signing_scheme,
                signing_algorithm=signing_algorithm,
                hash_algorithm=hash_algorithm,
                signed_headers=[
                    intersight.signing.HEADER_REQUEST_TARGET,
                    intersight.signing.HEADER_CREATED,
                    intersight.signing.HEADER_EXPIRES,
                    intersight.signing.HEADER_HOST,
                    intersight.signing.HEADER_DATE,
                    intersight.signing.HEADER_DIGEST,
                    'Content-Type',
                    'User-Agent'
                ],
                signature_max_validity=datetime.timedelta(minutes=5)
            )

            configuration = Configuration(host="https://" + target, signing_info=signing_info)

            # If a proxy has been set, we set it in the configuration parameters
            configuration.proxy = proxy
            # Proxy with authentication
            if proxy_user and proxy_password:
                proxy_auth = proxy_user + ":" + proxy_password
                proxy_auth_bytes = proxy_auth.encode("utf-8")
                proxy_auth_hash = base64.b64encode(proxy_auth_bytes).decode("utf-8")
                configuration.proxy_headers = {"Proxy-Authorization": f"Basic {proxy_auth_hash}"}

            # This is required in case of an API mismatch between Intersight and the SDK. It will allow the SDK to work
            # with a higher version of the API (unknown attributes) without raising exceptions
            configuration.discard_unknown_keys = True

            # FIXME: Temporary fixes for SDK issues - March 2021 - "minimum"
            # Temporary fix for SDK issue in validating fabric.MacAgingSettings macAgingTime value being 0
            # Temporary fix for SDK issue in validating ippool.IpV6Config prefix value being 0
            configuration.disabled_client_side_validations = "minimum"

            # This is required for Intersight Appliances that do not have a valid SSL certificate
            if not any(target.endswith(x) for x in ["intersight.com", "starshipcloud.com"]):
                configuration.verify_ssl = False

            self.handle = ApiClient(configuration)
            self.handle.set_default_header('Content-Type', 'application/json')

        self.version_min_required = self.INTERSIGHT_APPLIANCE_MIN_REQUIRED_VERSION

        self.config_manager = IntersightConfigManager(parent=self)
        self.inventory_manager = IntersightInventoryManager(parent=self)
        self.report_manager = IntersightReportManager(parent=self)

    def connect(self, bypass_version_checks=False):
        """
        Establishes connection to the device. Since Intersight does not require a connection, we use this
        method to verify that we are able to establish connectivity and gather name and version of the device
        :param bypass_version_checks: Whether the minimum version checks should be bypassed when connecting
        :return: True if connection successfully established, False otherwise
        """
        if self.task is not None:
            self.task.taskstep_manager.start_taskstep(name="ConnectIntersightDevice",
                                                      description="Connecting to " + self.metadata.device_type_long +
                                                                  " device")
        self.logger(level="debug", message="Using Intersight SDK version " + str(self.version_sdk))
        try:
            self._set_device_name_and_version()
            self.metadata.cached_orgs = self.get_orgs()
            self.metadata.timestamp_last_connected = datetime.datetime.now()
            self.metadata.is_reachable = True

            version = "unknown"
            if self.version:
                version = self.version

            self.logger(message="Connected to " + self.target + " (" + str(self.name) + ") running version " + version)

            # Verify if version running is above the minimum required version
            valid_version = True
            if self.version and self.is_appliance:
                try:
                    if "1.0.9-" in self.version:
                        build = self.version.split("-")[1]

                        if "1.0.9-" in self.version_min_required:
                            build_min = self.version_min_required.split("-")[1]

                            if build and build_min:
                                if int(build) < int(build_min):
                                    valid_version = False

                except Exception as err:
                    self.logger(level="debug", message="Could not perform minimum version check: " + str(err))

            if not valid_version:
                if not bypass_version_checks:
                    from api.api_server import easyucs
                    if easyucs:
                        self.metadata.is_reachable = False
                        self.logger(level="error", message="EasyUCS supports version " +
                                                           self.version_min_required + " and above.Your version"
                                                           + version + " is not supported.")
                        return False
                    else:
                        if not common.query_yes_no("Are you sure you want to continue with an unsupported version?"):
                            # User declined continue with unsupported version query
                            self.disconnect()
                            exit()
                else:
                    self.logger(level="warning", message="EasyUCS supports version " + self.version_min_required
                                                         + " and above. Your version " + version + " is not supported.")

            if self.task is not None:
                self.task.taskstep_manager.stop_taskstep(
                    name="ConnectIntersightDevice", status="successful",
                    status_message="Successfully connected to " + self.metadata.device_type_long + " device " +
                                   str(self.name))
            return True

        except Exception as err:
            self.metadata.is_reachable = False
            self.logger(level="error", message="Error while trying to connect to " + self.metadata.device_type_long +
                                               ": " + self.target + ": " + str(err))
        if self.task is not None:
            self.task.taskstep_manager.stop_taskstep(
                name="ConnectIntersightDevice", status="failed",
                status_message="Error while connecting to " + self.metadata.device_type_long + " device " +
                               str(self.name))
        return False

    def disconnect(self):
        """
        Intersight OpenAPI does not require a disconnection mechanism
        Maintaining the disconnect() call for compatibility reasons
        :return: True
        """
        if self.task is not None:
            self.task.taskstep_manager.skip_taskstep(
                name="DisconnectIntersightDevice",
                status_message="Disconnecting from " + self.metadata.device_type_long + " device " + str(self.name))
        return True

    def query(self, object_type="", filter="", expand="", retry=True):
        """
        Queries Intersight for one or multiple object(s) specified by its(their) type and a filter
        :param object_type: The object type of the object that is to be queried (e.g. "ntp.Policy")
        :param filter: A filter string to reduce the results to only specific objects
        :param expand: An expand string consisting of a list of attributes that should be expanded in the results
        :param retry: A flag to retry if query API fails
        :return: An empty list if no result, a list of Intersight SDK objects if found
        """

        if not object_type:
            self.logger(level="error", message="An object_type must be provided for the query")
            return []

        timeout = self.timeout
        if not retry:
            timeout = self.timeout * 2

        # We first need to decompose the object type to use the appropriate API
        api_prefix = object_type.split(".")[0]

        # We dynamically import the intersight module that we need for talking to the API
        api_module = importlib.import_module('intersight.api.' + api_prefix + '_api')
        api_class = getattr(api_module, api_prefix.title() + 'Api')
        api_instance = api_class(self.handle)

        # We also decompose the object type to get the name of the API call we need to make
        sdk_object_type = re.sub(r'(?<!^)(?=[A-Z])', '_', object_type.replace(".", "")).lower()

        try:
            MAX_OBJECTS_PER_FETCH_CALL = 100

            # We first query the API to get the number of objects that will be returned
            count_response = getattr(api_instance, "get_" + sdk_object_type + "_list")(
                count=True, filter=filter, _request_timeout=timeout)

            if count_response:
                count_value = count_response["count"]
                if count_value == 0:
                    results = []
                elif count_value <= MAX_OBJECTS_PER_FETCH_CALL:
                    results = getattr(api_instance, "get_" + sdk_object_type + "_list")(
                        filter=filter, expand=expand, _request_timeout=timeout).results
                else:
                    self.logger(level="debug", message=f"{str(count_value)} objects of class {sdk_object_type} are "
                                                       f"to be fetched using pagination")
                    start_value = 0
                    results = []
                    while start_value < count_value:
                        results += getattr(api_instance, "get_" + sdk_object_type + "_list")(
                            filter=filter, expand=expand, skip=start_value, top=MAX_OBJECTS_PER_FETCH_CALL,
                            _request_timeout=timeout).results
                        start_value += MAX_OBJECTS_PER_FETCH_CALL

                    self.logger(level="debug",
                                message=f"{str(len(results))} objects of class {sdk_object_type} have been fetched")
            else:
                # We query the API
                results = getattr(api_instance, "get_" + sdk_object_type + "_list")(
                    filter=filter, expand=expand, _request_timeout=timeout).results
            return results

        except (ApiValueError, ApiTypeError, ApiException) as err:
            error_message = str(err)
            if "Reason: Bad Gateway" in error_message:
                error_message = "Bad Gateway"
            else:
                # We try to simplify the error message displayed
                if hasattr(err, "body"):
                    try:
                        err_json = json.loads(err.body)
                        if "message" in err_json:
                            error_message = str(err_json["message"])
                    except json.decoder.JSONDecodeError as err_json_decode:
                        self.logger(level="error", message="JSON Decode error while fetching objects of class " +
                                                           sdk_object_type + ": " + str(err_json_decode))
                        pass
            self.logger(level="error",
                        message="Failed to fetch objects of class " + sdk_object_type + ": " + error_message)
        except AttributeError as err:
            self.logger(level="error",
                        message="Failed to fetch objects of class " + sdk_object_type + ": " + str(err))
        except urllib3.exceptions.MaxRetryError as err:
            self.logger(level="error",
                        message="Failed to fetch objects of class " + sdk_object_type + ": " + str(err))
        if retry:
            self.logger(level="info", message="Retrying to fetch objects of class " + sdk_object_type)
            return self.query(object_type=object_type, filter=filter, retry=False)

        return []

    def _get_apidocs_version(self):
        """
        Fetches the Intersight API version from APIdocs page
        :return: version if successful, None otherwise
        """
        requests.packages.urllib3.disable_warnings()

        url = "https://" + self.target + "/apidocs/apirefs/"
        try:
            page = requests.get(url, verify=False, timeout=5)
            regex_version = r"an-apidocs/(\d+\.\d+\.\d+-\d+)/build"
            res = re.search(regex_version, page.text)
            if res is not None:
                return res.group(1)

        except Exception as err:
            self.logger(level="error", message="Unable to determine Intersight API version: " + str(err))

        return None

    def get_orgs(self):
        """
        Fetches the Intersight Organizations
        :return: Org list if successful, None otherwise
        """
        cached_orgs = {}
        org_api = OrganizationApi(api_client=self.handle)
        try:
            orgs = org_api.get_organization_organization_list(_request_timeout=self.timeout, orderby="Name")
            if not orgs.results:
                self.logger(level="error", message="No org found")
                return None

            for result in orgs.results:
                cached_orgs[result.name] = result.description

            return cached_orgs

        except OpenApiException:
            self.logger(level="error", message="Unable to get the List of Orgs")
            return None

    def _set_device_name_and_version(self):
        appliance_api = ApplianceApi(api_client=self.handle)
        try:
            system_info = appliance_api.get_appliance_system_info_list(_request_timeout=self.timeout)

            if system_info.results:
                self.version = system_info.results[0].version
                self.metadata.device_version = self.version
                self.is_appliance = True

        except OpenApiException:
            self.logger(level="debug", message="Target is not an Intersight Appliance.")
            self.version = self._get_apidocs_version()
            self.metadata.device_version = self.version

        account_api = IamApi(api_client=self.handle)
        account = account_api.get_iam_account_list(_request_timeout=self.timeout)

        if account.results and not self.is_appliance:
            self.name = account.results[0].name
            self.metadata.device_name = self.name

    def send_feedback(self, feedback_type="Evaluation", comment="", evaluation="", follow_up=False,
                      alternative_follow_up_emails=None):
        """
        Sends the feedback to the Intersight
        :param feedback_type: Type of the feedback "Evaluation", "Bug"
        :param comment: Comment in the feedback (max_length=1500)
        :param evaluation: Evaluation of the tool "Excellent", "Poor", "Fair", "Good"
        :param follow_up: True is follow up required False otherwise
        :param alternative_follow_up_emails: Follow-up emails (max=5)
        :return True if successful False otherwise
        """
        if feedback_type not in ["Evaluation", "Bug"]:
            self.logger(level="error", message="Invalid Feedback Type")
            return False
        if len(comment) > 1500:
            self.logger(level="error", message="Length of comment should be less than 1500 characters.")
            return False
        if evaluation != "" and evaluation not in ["Excellent", "Poor", "Fair", "Good"]:
            self.logger(level="error", message="Invalid Evaluation Value")
            return False
        if alternative_follow_up_emails is not None and len(alternative_follow_up_emails) > 5:
            self.logger(level="error", message="Maximum number of alternate follow up emails can be 5")
            return False

        if alternative_follow_up_emails is None:
            alternative_follow_up_emails = []
        if feedback_type == "Bug" and len(alternative_follow_up_emails) > 0:
            follow_up = True

        from intersight.model.feedback_feedback_post import FeedbackFeedbackPost
        from intersight.model.feedback_feedback_data import FeedbackFeedbackData
        from intersight.model.mo_tag import MoTag

        if feedback_type == "Bug":
            feedback_data = FeedbackFeedbackData(type=feedback_type, comment=comment, follow_up=follow_up,
                                                 alternative_follow_up_emails=alternative_follow_up_emails)
        else:
            feedback_data = FeedbackFeedbackData(type=feedback_type, comment=comment, evaluation=evaluation)
        feedback_tag = MoTag(key="Source", value="EasyUCS")
        feedback_model = FeedbackFeedbackPost(feedback_data=feedback_data, tags=[feedback_tag])

        try:
            feedback_api = FeedbackApi(api_client=self.handle)
            feedback_api.create_feedback_feedback_post(feedback_model)
        except urllib3.exceptions.MaxRetryError as err:
            self.logger(level="error", message="Max retries exceeded while sending feedback to " +
                                               self.metadata.device_type_long + ": " + str(err))
            return False
        except Exception as err:
            if hasattr(err, 'reason'):
                if err.reason == "Unauthorized":
                    self.logger(level="error", message="Unauthorized connection while sending feedback to " +
                                                       self.metadata.device_type_long + ": " + str(err))
                else:
                    self.logger(level="error", message="Error while trying to send the feedback to " +
                                                       self.metadata.device_type_long + ": " + self.target + ": " +
                                                       str(err))
            else:
                self.logger(level="error", message="Error while sending the feedback: " + str(err))
            return False

        return True

    def get_os_firmware_data(self):
        """
        Function to get the OS and Firmware data from the device
        :return: Returns dictionary containing OS and Firmware data, None otherwise
        """
        if not self.metadata.cache_path:
            self.logger(level="error", message="OS and Firmware cached data not found")
            return None

        os_firmware_data = common.read_json_file(
            file_path=os.path.join(self.metadata.cache_path,
                                   RepositoryManager.REPOSITORY_DEVICES_OS_FIRMWARE_FILE_NAME),
            logger=self)

        if not os_firmware_data:
            self.logger(level="error", message="OS and Firmware cached data not found")
            return None
        return os_firmware_data

    def fetch_os_firmware_data(self):
        """
        Function to get the OS and Firmware metadata
        :return: A dictionary containing OS and Firmware data, None otherwise
        """
        if self.task is not None:
            self.task.taskstep_manager.start_taskstep(name="FetchOSFirmwareDataObjectsIntersight",
                                                      description="Fetching OS and Firmware Objects")

        result = {
            "os": {},
            "firmware": []
        }
        operating_system_vendors = self.query(object_type="hcl.OperatingSystemVendor")
        operating_systems = self.query(object_type="hcl.OperatingSystem")
        operating_system_distributions = self.query(object_type="os.Distribution")
        firmware_distributables = self.query(object_type="firmware.Distributable", filter="Origin eq System")

        if not all([True if obj else False for obj in [operating_system_vendors, operating_systems,
                                                       operating_system_distributions, firmware_distributables]]):
            if self.task is not None:
                self.task.taskstep_manager.stop_taskstep(
                    name="FetchOSFirmwareDataObjectsIntersight", status="failed",
                    status_message="Error while fetching OS and Firmware Objects from Intersight")
            return None

        if not hasattr(operating_system_distributions[0], "vendor") or not hasattr(operating_system_distributions[0], "label"):
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

        if self.task is not None:
            self.task.taskstep_manager.stop_taskstep(
                name="FetchOSFirmwareDataObjectsIntersight", status="successful",
                status_message="Successfully fetched OS and Firmware objects from Intersight")

        return result

    def sync_to_software_repository(self, description=None, file_download_link=None, image_type=None,
                                    firmware_image_type=None, name=None, org_name=None, supported_models=None,
                                    tags=None, vendor=None, version=None):
        """
        Creates Software Repository Link in Intersight device
        :param description: Description of the Software Repository Link
        :param file_download_link: HTTP(S) Link to download the file
        :param image_type: Type of the Software Repository Link os/firmware/scu
        :param firmware_image_type: Image type for firmware links
        :param name: Name of the Software Repository Link
        :param org_name: Organization name where link is saved
        :param supported_models: Models supported
        :param tags: Tags of the Software Repository Link
        :param vendor: Vendor of the OS
        :param version: Version of image
        :return: True if successful, False otherwise
        """
        if image_type not in ["firmware", "os", "scu"]:
            self.logger(level="error", message="Invalid file type: " + image_type)
            return False

        common_mandatory_fields = ["file_download_link", "org_name", "name", "version"]
        image_type_mandatory_fields = {
            "firmware": common_mandatory_fields + ["firmware_image_type", "supported_models"],
            "os": common_mandatory_fields + ["vendor"],
            "scu": common_mandatory_fields + ["supported_models"]
        }
        for field in image_type_mandatory_fields[image_type]:
            if not eval(field):
                self.logger(level="error", message=f"Missing field '{field}' for {image_type} link")
                return False

        if self.task is not None:
            self.task.taskstep_manager.start_taskstep(name="PushSoftwareRepositoryLinksIntersight",
                                                      description=f"Syncing file '{file_download_link}' to intersight "
                                                                  f"repo")

        try:
            # Fetching the organization object from Intersight
            object_list = self.query(object_type="organization.Organization", filter=f"Name eq {org_name}")
            if len(object_list) != 1:
                err_message = f"Organization '{org_name}' not found"
                self.logger(level="error", message=err_message)
                if self.task is not None:
                    self.task.taskstep_manager.stop_taskstep(
                        name="PushSoftwareRepositoryLinksIntersight", status="failed", status_message=err_message)
                return False
            org_obj = object_list[0]

            # Fetching the software repository catalog object for the organization from Intersight
            object_list = self.query(object_type="softwarerepository.Catalog",
                                     filter=f"Organization.Moid eq '{org_obj.moid}'")
            if len(object_list) != 1:
                err_message = f"Could not find catalog object for the organization: '{org_name}'"
                self.logger(level="error", message=err_message)
                if self.task is not None:
                    self.task.taskstep_manager.stop_taskstep(
                        name="PushSoftwareRepositoryLinksIntersight", status="failed", status_message=err_message)
                return False
            catalog_obj = object_list[0]

            from intersight.model.mo_mo_ref import MoMoRef
            from intersight.model.mo_tag import MoTag

            # Creating a reference object of the software repository catalog object
            catalog_ref = MoMoRef(moid=catalog_obj.moid, class_id='mo.MoRef', object_type="softwarerepository.Catalog")

            result = None
            if image_type == "os":
                from intersight.api.softwarerepository_api import SoftwarerepositoryApi
                from intersight.model.softwarerepository_operating_system_file import \
                    SoftwarerepositoryOperatingSystemFile
                from intersight.model.softwarerepository_http_server import SoftwarerepositoryHttpServer

                source_model = SoftwarerepositoryHttpServer(location_link=file_download_link)

                kwargs = {
                    "name": name,
                    "version": version,
                    "catalog": catalog_ref,
                    "source": source_model,
                    "vendor": vendor
                }
                if tags:
                    kwargs["tags"] = [MoTag(**tag) for tag in tags]
                if description:
                    kwargs["description"] = description

                operating_system_file_object = SoftwarerepositoryOperatingSystemFile(**kwargs)

                software_repository_api = SoftwarerepositoryApi(api_client=self.handle)
                result = software_repository_api.create_softwarerepository_operating_system_file(
                    operating_system_file_object)

            elif image_type == "firmware":
                from intersight.api.firmware_api import FirmwareApi
                from intersight.model.firmware_distributable import FirmwareDistributable
                from intersight.model.softwarerepository_http_server import SoftwarerepositoryHttpServer

                source_model = SoftwarerepositoryHttpServer(location_link=file_download_link)

                kwargs = {
                    "name": name,
                    "version": version,
                    "catalog": catalog_ref,
                    "supported_models": supported_models,
                    "source": source_model,
                    "image_type": firmware_image_type,
                    "import_action": "None",
                    "origin": "User"
                }
                if tags:
                    kwargs["tags"] = [MoTag(**tag) for tag in tags]
                if description:
                    kwargs["description"] = description

                firmware_file_object = FirmwareDistributable(**kwargs)

                firmware_api = FirmwareApi(api_client=self.handle)
                result = firmware_api.create_firmware_distributable(firmware_file_object)

            elif image_type == "scu":
                from intersight.api.firmware_api import FirmwareApi
                from intersight.model.firmware_server_configuration_utility_distributable \
                    import FirmwareServerConfigurationUtilityDistributable
                from intersight.model.softwarerepository_http_server import SoftwarerepositoryHttpServer

                source_model = SoftwarerepositoryHttpServer(location_link=file_download_link)
                kwargs = {
                    "name": name,
                    "version": version,
                    "catalog": catalog_ref,
                    "supported_models": supported_models,
                    "source": source_model
                }
                if tags:
                    kwargs["tags"] = [MoTag(**tag) for tag in tags]
                if description:
                    kwargs["description"] = description

                scu_file_object = FirmwareServerConfigurationUtilityDistributable(**kwargs)

                firmware_api = FirmwareApi(api_client=self.handle)
                result = firmware_api.create_firmware_server_configuration_utility_distributable(scu_file_object)

            if result:
                self.logger(level="info",
                            message=f"Successfully created software repository {image_type} link.")

                if self.task is not None:
                    self.task.taskstep_manager.stop_taskstep(
                        name="PushSoftwareRepositoryLinksIntersight", status="successful",
                        status_message=f"Successfully created software repository {image_type} link in intersight")

                return True
            else:
                self.logger(level="error",
                            message=f"Failed to create software repository {image_type} link.")

        except (ApiValueError, ApiTypeError, ApiException) as err:
            error_message = str(err)
            if "Reason: Bad Gateway" in error_message:
                error_message = "Bad Gateway"
            else:
                # We try to simplify the error message displayed
                if hasattr(err, "body"):
                    try:
                        err_json = json.loads(err.body)
                        if "message" in err_json:
                            error_message = str(err_json["message"])
                    except json.decoder.JSONDecodeError as err_json_decode:
                        self.logger(level="error", message=f"JSON Decode error while creating software repository "
                                                           f"{image_type} link: {str(err_json_decode)}")
            self.logger(level="error",
                        message=f"Failed to create software repository {image_type} link: {error_message}")
        except AttributeError as err:
            self.logger(level="error",
                        message=f"Failed to create software repository {image_type} link: {str(err)}")
        except urllib3.exceptions.MaxRetryError as err:
            self.logger(level="error",
                        message=f"Failed to create software repository {image_type} link: {str(err)}")

        if self.task is not None:
            self.task.taskstep_manager.stop_taskstep(
                name="PushSoftwareRepositoryLinksIntersight", status="failed",
                status_message="Error while while syncing to software repository. Check logs.")

        return False
