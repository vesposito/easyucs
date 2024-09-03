# coding: utf-8
# !/usr/bin/env python

""" device_connector.py: Easy UCS Deployment Tool
Device connector class"""

import json
import time
import requests
import urllib3


class DeviceConnector:
    """
    Class which contains functions used on a device connector.
    Can ONLY be inherited, DO NOT create an object of this class.
    """

    def set_device_connector_access_mode(self, access_mode="read-only"):
        """
        Adds access mode details to UCS device connector
        :param access_mode: Access mode to be set (read-only or allow-control)
        :return: True if details added successfully, False otherwise
        """
        if self.metadata.device_type not in ["cimc", "ucsm"]:
            self.logger(level="error", message="Unsupported device type: " + self.metadata.device_type_long)
            return False

        # Disable warning at each request
        urllib3.disable_warnings()

        login_cookie = self.handle.cookie
        auth_header = {'ucsmcookie': f"ucsm-cookie={login_cookie}"}

        if self.task is not None:
            self.task.taskstep_manager.start_taskstep(
                name="SetDeviceConnectorAccessMode", description=f"Setting device connector access mode of "
                                                                 f"{self.metadata.device_type_long} device {self.name}")

        # Constructing payload
        payload = {
            "AdminState": True,
            "ReadOnlyMode": False
        }
        if access_mode == "read-only":
            payload["ReadOnlyMode"] = True

        if login_cookie:
            err_message = ""
            try:
                uri = "https://" + self.target + "/connector/Systems"
                response = requests.put(uri, verify=False, headers=auth_header, data=json.dumps(payload))
                if response.status_code == 200:
                    message = f"Successfully set device connector access mode of " \
                              f"{self.metadata.device_type_long} device '{self.name}' to '{access_mode}'."
                    if self.task is not None:
                        self.task.taskstep_manager.stop_taskstep(name="SetDeviceConnectorAccessMode",
                                                                 status="successful", status_message=message)
                    self.logger(level="info", message=message)
                    return True
                else:
                    err_message = (f"Failed to set device connector access mode of {self.metadata.device_type_long}"
                                   f" device {self.name}.")
                    self.logger(level="error", message=err_message)
            except Exception as err:
                err_message = (f"Failed to set device connector access mode of {self.metadata.device_type_long} "
                               f"device {self.name}.")
                self.logger(level="error", message=f"{err_message} Error: {str(err)}")

            if self.task is not None:
                self.task.taskstep_manager.stop_taskstep(name="SetDeviceConnectorAccessMode", status="failed",
                                                         status_message=err_message)
            return False

    def set_device_connector_proxy(self, proxy_enabled=False, proxy_host=None, proxy_port=None,
                                   proxy_authentication=False, proxy_username=None, proxy_password=None):
        """
        Adds proxy details to UCS device connector
        :param proxy_enabled: Flag to know whether device connector proxy is enabled
        :param proxy_host: IP or FQDN of the proxy host
        :param proxy_port: Port exposed from proxy host for connection
        :param proxy_authentication: Flag to know whether authentication is enabled in proxy server(True or False)
        :param proxy_username: Username for proxy
        :param proxy_password: Password for proxy
        :return: True if details added successfully, False otherwise
        """
        if self.metadata.device_type not in ["cimc", "imm", "ucsm"]:
            self.logger(level="error", message="Unsupported device type: " + self.metadata.device_type_long)
            return False

        # Disable warning at each request
        urllib3.disable_warnings()

        if self.metadata.device_type in ["cimc", "ucsm"]:
            login_cookie = self.handle.cookie
            auth_header = {'ucsmcookie': f"ucsm-cookie={login_cookie}"}
        else:
            login_cookie = self._session_id
            auth_header = {'Cookie': f"sessionId={login_cookie}"}

        if self.task is not None:
            self.task.taskstep_manager.start_taskstep(
                name="ConfigureDeviceConnectorProxy", description=f"Configuring device connector proxy of "
                                                                  f"{self.metadata.device_type_long} device")

        # Constructing payload
        if proxy_enabled:
            payload = {
                "ProxyHost": proxy_host,
                "ProxyPort": proxy_port,
                "AuthenticationEnabled": proxy_authentication,
                "ProxyType": "Manual"
            }
            if proxy_authentication:
                payload["ProxyUsername"] = proxy_username
                payload["ProxyPassword"] = proxy_password
        else:
            payload = {
                "ProxyType": "Disabled"
            }

        if login_cookie:
            err_message = ""
            try:
                uri = "https://" + self.target + "/connector/HttpProxies"
                response = requests.put(uri, verify=False, headers=auth_header, data=json.dumps(payload))
                if response.status_code == 200:
                    message = (f"Successfully configured device connector proxy of {self.metadata.device_type_long}"
                               f" device {self.name}.")
                    if self.task is not None:
                        self.task.taskstep_manager.stop_taskstep(name="ConfigureDeviceConnectorProxy",
                                                                 status="successful", status_message=message)
                    self.logger(level="info", message=message)
                    return True
                else:
                    err_message = (f"Failed to configure device connector proxy of {self.metadata.device_type_long}"
                                   f" device {self.name}.")
                    self.logger(level="error", message=err_message)
            except Exception as err:
                err_message = (f"Failed to configure device connector proxy of {self.metadata.device_type_long} device "
                               f"{self.name}.")
                self.logger(level="error", message=err_message + str(err))

            if self.task is not None:
                self.task.taskstep_manager.stop_taskstep(name="ConfigureDeviceConnectorProxy", status="failed",
                                                         status_message=err_message)
            return False

    def claim_to_intersight(self, intersight_device, access_mode=None, proxy_details=None):
        """
        Claims UCS device to the given Intersight device
        :param access_mode: Device connector access mode
        :param intersight_device: Intersight device to which the UCS device should be claimed
        :param proxy_details: Device connector proxy details to be set to connect to intersight
        :return: True if claiming operation is successful, False otherwise
        """

        from intersight.model.asset_device_claim import AssetDeviceClaim
        from intersight.model.appliance_device_claim import ApplianceDeviceClaim
        from intersight.api.asset_api import AssetApi
        from intersight.api.appliance_api import ApplianceApi
        from intersight.exceptions import ApiValueError, ApiTypeError, ApiException

        if self.metadata.device_type not in ["cimc", "imm", "ucsm"]:
            self.logger(level="error", message="Unsupported device type: " + self.metadata.device_type_long)
            return False

        if not self.is_connected():
            return False

        if self.metadata.device_connector_claim_status == "claimed":
            self.logger(level="info",
                        message=f"{self.metadata.device_type_long} device {self.name}" +
                                f" is already claimed to account {self.metadata.device_connector_ownership_name}.")
            
            if self.task is not None:
                # If the device is already claimed then we skip the task steps SetDeviceConnectorAccessMode and
                # ConfigureDeviceConnectorProxy, and fail the task step ClaimDeviceToIntersight.
                self.task.taskstep_manager.skip_taskstep(
                    name="SetDeviceConnectorAccessMode",
                    status_message=f"Skipping setting device connector access mode of "
                                   f"{self.metadata.device_type_long} device {self.name}"
                )
                self.task.taskstep_manager.skip_taskstep(
                    name="ConfigureDeviceConnectorProxy",
                    status_message=f"Skipped configuring device connector proxy of "
                                   f"{self.metadata.device_type_long} device {self.name}"
                )
                self.task.taskstep_manager.stop_taskstep(
                    name="ClaimDeviceToIntersight", status="failed",
                    status_message=f"{self.metadata.device_type_long} device {self.name}" +
                                   f" is already claimed to account {self.metadata.device_connector_ownership_name}.")
            return False

        # Checking and resetting Device Connector if necessary
        if not intersight_device.is_appliance:
            # Determine the expected Cloud DNS value based on the target
            if "qa.starshipcloud.com" in intersight_device.target:
                expected_cloud_dns = ["qaconnect.starshipcloud.com"]
            elif "staging.starshipcloud.com" in intersight_device.target:
                expected_cloud_dns = ["stagingconnect.starshipcloud.com"]
            else:
                # List of acceptable DNS values for Intersight prod
                expected_cloud_dns = [
                    "svc.ucs-connect.com",
                    "svc.intersight.com",
                    "svc-static1.intersight.com",
                    "svc-static1.ucs-connect.com"
                ]
            # Retrieve current Cloud DNS value from the Device Connector
            current_cloud_dns = self._device_connector_info.get("Intersight URL")
            # Compare current Cloud DNS with the expected Cloud DNS
            if current_cloud_dns not in expected_cloud_dns:
                # Call reset_device_connector if Cloud DNS values are different
                self.reset_device_connector(intersight_device.target)

        # Setting the device connector access mode (only for CIMC and UCSM devices)
        if self.metadata.device_type in ["cimc", "ucsm"] and access_mode:
            self.set_device_connector_access_mode(access_mode=access_mode)
        elif self.task is not None:
            self.task.taskstep_manager.skip_taskstep(
                name="SetDeviceConnectorAccessMode",
                status_message=f"Skipping setting device connector access mode of {self.metadata.device_type_long} "
                               f"device {self.name}"
            )

        # Setting the device connector proxy settings
        if proxy_details:
            self.set_device_connector_proxy(**proxy_details)
        elif self.task is not None:
            self.task.taskstep_manager.skip_taskstep(
                name="ConfigureDeviceConnectorProxy",
                status_message=f"Skipped configuring device connector proxy of {self.metadata.device_type_long} "
                               f"device {self.name}"
            )

        # Waiting until connection is established or failed
        self._set_device_connector_info(wait_for_connection_status=True)

        if self.task is not None:
            self.task.taskstep_manager.start_taskstep(name="ClaimDeviceToIntersight",
                                                      description="Claiming UCS device to Intersight")

        if self._device_connector_info.get("Connection State") in ["DNS Not Configured", "Http Proxy Connect Error",
                                                                   "Intersight Network Error"]:
            err_message = f"Error while claiming {self.metadata.device_type_long} {self.name} to " \
                          f"{intersight_device.metadata.device_type_long} {intersight_device.target}. " \
                          f"{self._device_connector_info['Connection State']}."
            self.logger(level="error", message=err_message)
            if self.task is not None:
                self.task.taskstep_manager.stop_taskstep(name="ClaimDeviceToIntersight", status="failed",
                                                         status_message=err_message)
            return False

        if intersight_device.is_appliance:
            platform_type = ""
            if self.metadata.device_type == "cimc":
                platform_type = "IMC"
            elif self.metadata.device_type == "ucsm":
                platform_type = "UCSFI"
            elif self.metadata.device_type == "imm":
                platform_type = "UCSFIISM"

            try:
                appliance_api = ApplianceApi(api_client=intersight_device.handle)
                kwargs = {
                    "Hostname": self.target,
                    "Username": self.username,
                    "Password": self.password,
                    "PlatformType": platform_type
                }
                appliance_api.create_appliance_device_claim(ApplianceDeviceClaim(**kwargs))
                self.logger(level="info",
                            message=f"Claiming of {self.metadata.device_type_long} {self.name}" +
                                    f" started on {intersight_device.metadata.device_type_long}" +
                                    f" {intersight_device.target}")
                if self.task is not None:
                    self.task.taskstep_manager.stop_taskstep(
                        name="ClaimDeviceToIntersight", status="successful",
                        status_message=f"Claiming of {self.metadata.device_type_long} {self.name}" +
                                       f" started on {intersight_device.metadata.device_type_long}" +
                                       f" {intersight_device.target}")
            except (ApiValueError, ApiTypeError, ApiException) as err:
                self.logger(level="error",
                            message=f"Error while claiming {self.metadata.device_type_long} {self.name}" +
                                    f" to {intersight_device.metadata.device_type_long}" +
                                    f" {intersight_device.target}: {str(err)}")
                if self.task is not None:
                    self.task.taskstep_manager.stop_taskstep(
                        name="ClaimDeviceToIntersight", status="failed",
                        status_message=f"Error while claiming {self.metadata.device_type_long} {self.name}" +
                                       f" to {intersight_device.metadata.device_type_long}" +
                                       f" {intersight_device.target}")
                return False
        else:
            # We are in SaaS condition
            if "Claim Code" not in self._device_connector_info:
                self.logger(level="error",
                            message=f"Error while claiming {self.metadata.device_type_long} {self.name}" +
                                    f" to {intersight_device.metadata.device_type_long} {intersight_device.name}:" +
                                    f" 'Claim Code' not found, please check proxy settings or try"
                                    f" again after some time")
                if self.task is not None:
                    self.task.taskstep_manager.stop_taskstep(
                        name="ClaimDeviceToIntersight", status="failed",
                        status_message=f"Error while claiming {self.metadata.device_type_long} {self.name}" +
                                       f" to {intersight_device.metadata.device_type_long}" +
                                       f" {intersight_device.target}: 'Claim Code' not found, please check proxy "
                                       f"settings or try again after some time")
                return False

            try:
                kwargs = {
                    "SecurityToken": self._device_connector_info["Claim Code"],
                    "SerialNumber": self._device_connector_info["Device ID"]
                }

                asset_api = AssetApi(api_client=intersight_device.handle)
                asset_api.create_asset_device_claim(AssetDeviceClaim(**kwargs))
                self.logger(level="info",
                            message=f"{self.metadata.device_type_long} device {self.name} claimed to " +
                                    f"{intersight_device.metadata.device_type_long} {intersight_device.name}")
                if self.task is not None:
                    self.task.taskstep_manager.stop_taskstep(
                        name="ClaimDeviceToIntersight", status="successful",
                        status_message=f"Successfully claimed {self.metadata.device_type_long} device " +
                                       f"{self.name} to {intersight_device.metadata.device_type_long} " +
                                       f"{intersight_device.name}")
            except (ApiValueError, ApiTypeError, ApiException) as err:
                self.logger(level="error",
                            message=f"Error while claiming {self.metadata.device_type_long} {self.name}" +
                                    f" to {intersight_device.metadata.device_type_long} {intersight_device.name}:" +
                                    f" {str(err)}")
                if self.task is not None:
                    self.task.taskstep_manager.stop_taskstep(
                        name="ClaimDeviceToIntersight", status="failed",
                        status_message=f"Error while claiming {self.metadata.device_type_long} {self.name}" +
                                       f" to {intersight_device.metadata.device_type_long}" +
                                       f" {intersight_device.name}")
                return False
            except Exception as err:
                self.logger(level="error",
                            message=f"Error while claiming {self.metadata.device_type_long} {self.name}" +
                                    f" to {intersight_device.metadata.device_type_long} {intersight_device.name}:" +
                                    f" {str(err)}")
                if self.task is not None:
                    self.task.taskstep_manager.stop_taskstep(
                        name="ClaimDeviceToIntersight", status="failed",
                        status_message=f"Error while claiming {self.metadata.device_type_long} {self.name}" +
                                       f" to {intersight_device.metadata.device_type_long}" +
                                       f" {intersight_device.name}")
                return False

        if self.task is not None:
            self.logger(message="Refreshing Intersight Device Connector info")
            self.task.taskstep_manager.start_taskstep(name="RefreshIntersightClaimStatus",
                                                      description="Refreshing Intersight Device Connector info")
            # We force an update of the Device Connector info and check periodically for 3 mins
            count = 18
            while self.metadata.device_connector_claim_status == "unclaimed" and count:
                time.sleep(10)
                self._set_device_connector_info()
                count -= 1
            if self.metadata.device_connector_claim_status == "claimed":
                self.task.taskstep_manager.stop_taskstep(
                    name="RefreshIntersightClaimStatus", status="successful",
                    status_message="Successfully refreshed Intersight Device Connector Info"
                )
                from api.api_server import easyucs
                if easyucs:
                    easyucs.repository_manager.save_metadata(metadata=self.metadata)
            else:
                self.task.taskstep_manager.stop_taskstep(
                    name="RefreshIntersightClaimStatus", status="failed",
                    status_message="Failed refreshing Intersight Device Connector Info"
                )

        return True

    def reset_device_connector(self, intersight_target="svc.intersight.com"):
        """
        Resets Device Connector
        :return: True if successful, False otherwise
        """
        if self.metadata.device_type not in ["cimc", "imm", "ucsm"]:
            self.logger(level="error", message="Unsupported device type: " + self.metadata.device_type_long)
            return False

        # Disable warning at each request
        urllib3.disable_warnings()

        if not self.is_connected():
            return False

        message_str = "Resetting Device Connector of " + self.metadata.device_type_long + " device " + self.name
        if self.task is not None:
            self.task.taskstep_manager.start_taskstep(name="ResetDeviceConnector", description=message_str)

        self.logger(message=message_str)

        uri = "https://" + self.target + "/connector/DeviceConnections"

        if self.metadata.device_type in ["cimc", "ucsm"]:
            login_cookie = self.handle.cookie
            auth_header = {'ucsmcookie': f"ucsm-cookie={login_cookie}"}
        else:
            login_cookie = self._session_id
            auth_header = {'Cookie': f"sessionId={login_cookie}"}

        if login_cookie:
            try:
                if intersight_target.endswith("qa.starshipcloud.com"):
                    cloud_dns = "qaconnect.starshipcloud.com"
                elif intersight_target.endswith("staging.starshipcloud.com"):
                    cloud_dns = "stagingconnect.starshipcloud.com"
                else:
                    cloud_dns = "svc.intersight.com"
                data = json.dumps({"CloudDns": cloud_dns, "ForceResetIdentity": True, "ResetIdentity": True})
                response = requests.put(uri, verify=False, headers=auth_header, data=data)
                if response.status_code == 200:
                    if response.json():
                        self._set_device_connector_info()
                        if self.task is not None:
                            self.task.taskstep_manager.stop_taskstep(
                                name="ResetDeviceConnector", status="successful",
                                status_message=f"Successfully reset {self.metadata.device_type_long} device " +
                                               f"{self.name} Device Connector")
                        self.logger(message="Device Connector reset on " + self.metadata.device_type_long +
                                            " " + self.name)

                    # We reset all Device Connector metadata info
                    self.metadata.device_connector_claim_status = "unclaimed"
                    self.metadata.device_connector_ownership_name = None
                    self.metadata.device_connector_ownership_user = None
                    self.metadata.intersight_device_uuid = None
                    from api.api_server import easyucs
                    if easyucs:
                        easyucs.repository_manager.save_metadata(metadata=self.metadata)

                    return True
                else:
                    if self.task is not None:
                        self.task.taskstep_manager.stop_taskstep(
                            name="ResetDeviceConnector", status="failed",
                            status_message=f"Error while clearing {self.metadata.device_type_long} {self.name}" +
                                           f" Intersight Claim Status: {str(response.status_code)}")
                    self.logger(level="error", message="Error while resetting Device Connector: " +
                                                       str(response.status_code))
                    return False
            except Exception as err:
                if self.task is not None:
                    self.task.taskstep_manager.stop_taskstep(
                        name="ResetDeviceConnector", status="failed",
                        status_message=f"Error while clearing {self.metadata.device_type_long} {self.name}" +
                                       f" Intersight Claim Status: Couldn't request the device connector information" +
                                       f" from the API")
                self.logger(level="error",
                            message="Couldn't request the device connector information from the API: " + str(err))
        else:
            if self.task is not None:
                self.task.taskstep_manager.stop_taskstep(
                    name="ResetDeviceConnector", status="failed",
                    status_message=f"Error while clearing {self.metadata.device_type_long} {self.name}" +
                                   f" Intersight Claim Status: No login cookie")
            self.logger(level="error",
                        message="No login cookie, no request can be made to find device connector information")
        return False

    def _set_device_connector_info(self, wait_for_connection_status=False):
        """
        Performs all requests to the device connector to get the necessary information and populate the metadata
        with the most significant info + a dictionary containing all info
        :param wait_for_connection_status: Flag if set to True, before fetching the info wait until connection is
        established or failed
        :return: True if info collected correctly, False otherwise
        """
        if self.metadata.device_type not in ["cimc", "imm", "ucsm"]:
            self.logger(level="error", message="Unsupported device type: " + self.metadata.device_type_long)
            return False

        # Disable warning at each request
        urllib3.disable_warnings()

        if not self.is_connected():
            return False

        base_uri = "https://" + self.target

        dict_requests = {"/Systems": None,
                         "/Versions": None,
                         "/DeviceConnections": None,
                         "/DeviceIdentifiers": None,
                         "/SecurityTokens": None,
                         "/HttpProxies": None}

        # Sanity check
        if self.metadata.device_type in ["cimc", "ucsm"]:
            login_cookie = self.handle.cookie
            auth_header = {'ucsmcookie': f"ucsm-cookie={login_cookie}"}
        else:
            login_cookie = self._session_id
            auth_header = {'Cookie': f"sessionId={login_cookie}"}

        if login_cookie:
            # Wait until the connection is established or there is network error
            if wait_for_connection_status:
                uri = base_uri + "/connector/Systems"
                count = 0
                while count < 12:
                    try:
                        response = requests.get(uri, verify=False, headers=auth_header)
                        if response.status_code == 200:
                            resp = response.json()
                            if len(resp) > 0:
                                resp = resp[0]
                                if resp.get("ConnectionState") in ["Connected", "DNS Not Configured",
                                                                   "Http Proxy Connect Error",
                                                                   "Intersight Network Error"]:
                                    self.logger(level="info", message=f"Connection state of device connector is: "
                                                                      f"{resp.get('ConnectionState')}")
                                    break
                        else:
                            self.logger(level="error",
                                        message="Error while checking the device connector connection state:")
                            break
                    except Exception as err:
                        self.logger(level="error", message="Error while checking the device connector connection state:"
                                                           + str(err))
                        break
                    time.sleep(10)
                    count += 1

            for end_uri, value in dict_requests.items():
                uri = base_uri + "/connector" + end_uri
                try:
                    response = requests.get(uri, verify=False, headers=auth_header)
                    if "error" not in response.text:
                        dict_requests[end_uri] = response.json()
                except Exception as err:
                    self.logger(level="error", message="Couldn't request the device connector information " +
                                                       "from the API for config: " + str(err))
                    return False
        else:
            self.logger(level="error",
                        message="No login cookie, no request can be made to find device connector information")
            return False

        device_connector_info = {}
        if isinstance(dict_requests["/Systems"], list):
            if "ConnectionState" in dict_requests["/Systems"][0]:
                device_connector_info["Connection State"] = dict_requests["/Systems"][0]["ConnectionState"]
            if "AccountOwnershipState" in dict_requests["/Systems"][0]:
                device_connector_info["Claim Status"] = dict_requests["/Systems"][0]["AccountOwnershipState"]
                if dict_requests["/Systems"][0]["AccountOwnershipState"] == "Not Claimed":
                    # We change the name to a more usable one
                    self.metadata.device_connector_claim_status = "unclaimed"
                else:
                    # it should result in "claimed"
                    self.metadata.device_connector_claim_status = dict_requests["/Systems"][0][
                        "AccountOwnershipState"].lower()
            if "AccountOwnershipName" in dict_requests["/Systems"][0]:
                if dict_requests["/Systems"][0]["AccountOwnershipName"]:
                    # We need to check the value as this value exists even if not claimed
                    device_connector_info["Claimed Account"] = dict_requests["/Systems"][0]["AccountOwnershipName"]
                    self.metadata.device_connector_ownership_name = dict_requests["/Systems"][0]["AccountOwnershipName"]
            if "AccountOwnershipUser" in dict_requests["/Systems"][0]:
                if dict_requests["/Systems"][0]["AccountOwnershipUser"]:
                    device_connector_info["Claimed User"] = dict_requests["/Systems"][0]["AccountOwnershipUser"]
                    self.metadata.device_connector_ownership_user = dict_requests["/Systems"][0]["AccountOwnershipUser"]
        if isinstance(dict_requests["/DeviceConnections"], list):
            if "CloudDns" in dict_requests["/DeviceConnections"][0]:
                device_connector_info["Intersight URL"] = dict_requests["/DeviceConnections"][0]["CloudDns"]
        if isinstance(dict_requests["/Versions"], list):
            if "Version" in dict_requests["/Versions"][0]:
                device_connector_info["Version"] = dict_requests["/Versions"][0]["Version"]
        if isinstance(dict_requests["/HttpProxies"], list):
            if "ProxyType" in dict_requests["/HttpProxies"][0]:
                if dict_requests["/HttpProxies"][0]["ProxyType"] == "Manual":
                    if "ProxyHost" in dict_requests["/HttpProxies"][0]:
                        device_connector_info["Proxy"] = dict_requests["/HttpProxies"][0]["ProxyHost"]
                else:
                    device_connector_info["Proxy"] = dict_requests["/HttpProxies"][0]["ProxyType"]
        if isinstance(dict_requests["/DeviceIdentifiers"], list):
            if "Id" in dict_requests["/DeviceIdentifiers"][0]:
                device_connector_info["Device ID"] = dict_requests["/DeviceIdentifiers"][0]["Id"]
        if isinstance(dict_requests["/SecurityTokens"], list):
            if wait_for_connection_status and "Duration" in dict_requests["/SecurityTokens"][0]:
                # Claim code expires after 10 minutes by default
                # Checking if the expiry duration is less than 10 seconds, if yes wait and fetch the new claim code
                # This is done to avoid using the expired claim code while claiming the device to intersight
                if dict_requests["/SecurityTokens"][0]["Duration"] < 10:
                    time.sleep(dict_requests["/SecurityTokens"][0]["Duration"] + 2)
                    uri = base_uri + "/connector" + "/SecurityTokens"
                    try:
                        response = requests.get(uri, verify=False, headers=auth_header)
                        if "error" not in response.text:
                            dict_requests["/SecurityTokens"] = response.json()
                        else:
                            dict_requests["/SecurityTokens"] = None
                            self.logger(level="error", message="Error while fetching claim code from SecurityTokens "
                                                               "API")
                    except Exception as err:
                        self.logger(level="error", message="Error while fetching claim code from SecurityTokens API: "
                                                           + str(err))
                        return False
            if dict_requests["/SecurityTokens"] and "Token" in dict_requests["/SecurityTokens"][0]:
                # No need to check the value as this value doesn't exist if claimed
                device_connector_info["Claim Code"] = dict_requests["/SecurityTokens"][0]["Token"]

        # Trying to determine if the Intersight target of this device exists as a device in EasyUCS.
        # If so, we link its UUID to this device
        # We only do this for claimed devices and if we are running with the EasyUCS DeviceManager
        found_intersight_device = False
        if device_connector_info.get("Intersight URL"):
            if device_connector_info["Intersight URL"] in ["svc.ucs-connect.com", "svc.intersight.com",
                                                           "svc-static1.intersight.com", "svc-static1.ucs-connect.com"]:
                intersight_url = "www.intersight.com"
            else:
                # This is an Intersight Appliance. We need to remove the prefix "dc-" to the URL
                if device_connector_info["Intersight URL"].startswith("dc-"):
                    intersight_url = device_connector_info["Intersight URL"][3:]
                else:
                    intersight_url = device_connector_info["Intersight URL"]
            if self.metadata.device_connector_claim_status == "claimed":
                from api.api_server import easyucs
                if easyucs:
                    for device_metadata in easyucs.repository_manager.get_metadata(object_type="device"):
                        if device_metadata.device_type == "intersight":
                            if device_metadata.target == intersight_url:
                                if device_metadata.device_name == device_connector_info.get("Claimed Account"):
                                    found_intersight_device = True
                                    self.metadata.intersight_device_uuid = device_metadata.uuid
                                    self.logger(
                                        level="info",
                                        message="This device is claimed to Intersight device with UUID: " +
                                                str(device_metadata.uuid)
                                    )
                                    break

                    if not found_intersight_device:
                        self.logger(level="debug", message="Could not find the Intersight device to which this " +
                                                           self.metadata.device_type_long + " device is claimed")

            if not found_intersight_device:
                self.metadata.intersight_device_uuid = None

        self._device_connector_info = device_connector_info

        return True
