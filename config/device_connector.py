# coding: utf-8
# !/usr/bin/env python

""" device_connector.py: Easy UCS Deployment Tool """

from config.object import GenericConfigObject


class DeviceConnector(GenericConfigObject):
    _CONFIG_NAME = "Device Connector"
    _CONFIG_SECTION_NAME = "device_connector"

    def __init__(self, parent=None, json_content=None):
        GenericConfigObject.__init__(self, parent=parent)
        self._connector_uri = self._device.target + "/connector"

        self.enabled = None
        self.intersight_url = None
        self.dns_configuration = None
        self.ntp_configuration = None
        self.proxy_configuration = None
        self.read_only = None  # Only for UCS
        self.tunneled_kvm = None  # Only for UCS IMC
        self.configuration_from_intersight_only = None  # Only for UCS IMC

        if self._config.load_from == "live":
            self._get_device_connections()
            self._get_http_proxies()
            self._get_common_configs()
            self._get_systems()
            if "Imc" in self._device.__class__.__name__:
                self._get_device_configurations()

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content, allow_int=True, allow_bool=True):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def clean_object(self):
        if self.dns_configuration:
            for value in ["domain_name", "dns_servers"]:
                if value not in self.dns_configuration:
                    self.dns_configuration[value] = None

        if self.ntp_configuration:
            for value in ["ntp_servers"]:
                if value not in self.ntp_configuration:
                    self.ntp_configuration[value] = None

        if self.proxy_configuration:
            for value in ["enable_proxy", "proxy_host", "proxy_port", "enable_proxy_authentication",
                          "proxy_username", "proxy_password"]:
                if value not in self.proxy_configuration:
                    self.proxy_configuration[value] = None

    def _get_common_configs(self):
        # TODO: Move this API calling code to _fetch_api_objects() functions across all device types (imm domain,
        #  ucsm, cimc)
        uri = "https://" + self._connector_uri + "/CommConfigs"
        response = self._device.get_request(uri=uri)

        # Sanity check
        if not response:
            self.logger(level="error", message="GET /CommConfigs failed to return a valid response")
            return

        if response[0].get("NtpServers"):
            self.ntp_configuration = {
                "ntp_servers": response[0]["NtpServers"]
            }

        if response[0].get("DomainName"):
            if not self.dns_configuration:
                self.dns_configuration = {}
            self.dns_configuration["domain_name"] = response[0].get("DomainName")

        if response[0].get("NameServers"):
            if not self.dns_configuration:
                self.dns_configuration = {}
            self.dns_configuration["dns_servers"] = response[0].get("NameServers")

    def _get_device_connections(self):
        # TODO: Move this API calling code to _fetch_api_objects() functions across all device types (imm domain,
        #  ucsm, cimc)
        uri = "https://" + self._connector_uri + "/DeviceConnections"
        response = self._device.get_request(uri=uri)

        # Sanity check
        if not response:
            self.logger(level="error", message="GET /DeviceConnections failed to return a valid response")
            return

        self.intersight_url = response[0]["CloudDns"].lower()
        if self.intersight_url in ["svc.ucs-connect.com", "svc.intersight.com", "svc-static1.intersight.com",
                                   "svc-static1.ucs-connect.com"]:
            self.intersight_url = "svc.intersight.com"

    def _get_device_configurations(self):
        # TODO: Move this API calling code to _fetch_api_objects() functions across all device types (imm domain,
        #  ucsm, cimc)
        uri = "https://" + self._connector_uri + "/DeviceConfigurations"
        response = self._device.get_request(uri=uri)

        # Sanity check
        if not response:
            self.logger(level="error", message="GET /DeviceConfigurations failed to return a valid response")
            return

        self.tunneled_kvm = response[0]["KVMTunnellingEnabled"]
        self.configuration_from_intersight_only = response[0]["ConfigurationLockoutEnabled"]

    def _get_systems(self):
        # TODO: Move this API calling code to _fetch_api_objects() functions across all device types (imm domain,
        #  ucsm, cimc)
        uri = "https://" + self._connector_uri + "/Systems"
        response = self._device.get_request(uri=uri)

        # Sanity check
        if not response:
            self.logger(level="error", message="GET /Systems failed to return a valid response")
            return

        self.enabled = response[0]["AdminState"]
        if "Ucs" in self._device.__class__.__name__:
            self.read_only = response[0]["ReadOnlyMode"]

    def _get_http_proxies(self):
        # TODO: Move this API calling code to _fetch_api_objects() functions across all device types (imm domain,
        #  ucsm, cimc)
        uri = "https://" + self._connector_uri + "/HttpProxies"
        response = self._device.get_request(uri=uri)

        # Sanity check
        if not response:
            self.logger(level="error", message="GET /HttpProxies failed to return a valid response")
            return

        self.proxy_configuration = {
            "enable_proxy": True if response[0]["ProxyType"].lower() == "manual" else False
        }
        if self.proxy_configuration["enable_proxy"]:
            self.proxy_configuration["proxy_host"] = response[0]["ProxyHost"]
            self.proxy_configuration["proxy_port"] = response[0]["ProxyPort"]
            if "ProxyUsername" in response[0]:
                self.proxy_configuration["enable_proxy_authentication"] = True
                self.proxy_configuration["proxy_username"] = response[0]["ProxyUsername"]
                self.logger(level="warning",
                            message=f"Password of {self._CONFIG_NAME} Proxy username can't be exported")

    def push_object(self):
        # Configuring Device Connector Proxy
        if self.proxy_configuration and self.proxy_configuration.get("enable_proxy", False):
            payload = {
                "ProxyHost": self.proxy_configuration["proxy_host"],
                "ProxyPort": self.proxy_configuration["proxy_port"],
                "AuthenticationEnabled": self.proxy_configuration["enable_proxy_authentication"],
                "ProxyType": "Manual",
                "ProxyUsername": "",
                "ProxyPassword": ""
            }
            if self.proxy_configuration.get("enable_proxy_authentication", False):
                payload["ProxyUsername"] = self.proxy_configuration["proxy_username"]
                payload["ProxyPassword"] = self.proxy_configuration.get("proxy_password")
        else:
            payload = {
                "ProxyType": "Disabled"
            }

        # Pushing the proxy configuration
        uri = "https://" + self._parent_having_logger.target + "/connector/HttpProxies"
        self._device.put_request(uri=uri, payload=payload)

        # Configuring NTP details
        common_config_payload = {}
        if self.ntp_configuration and self.ntp_configuration.get("ntp_servers"):
            common_config_payload["NtpServers"] = self.ntp_configuration.get("ntp_servers")

        # Configuring domain name
        if self.dns_configuration and self.dns_configuration.get("domain_name"):
            common_config_payload["DomainName"] = self.dns_configuration.get("domain_name")

        # Configuring DNS name servers
        if self.dns_configuration and self.dns_configuration.get("dns_servers"):
            common_config_payload["NameServers"] = self.dns_configuration.get("dns_servers")

        # Pushing the common configuration
        if common_config_payload:
            uri = "https://" + self._parent_having_logger.target + "/connector/CommConfigs"
            self._device.put_request(uri=uri, payload=payload)

        # Pushing Intersight Device Connections
        if self.intersight_url:
            data = {
                "CloudDns": self.intersight_url,
                "ForceResetIdentity": True
            }
            uri = "https://" + self._parent_having_logger.target + "/connector/DeviceConnections"
            self._device.put_request(uri=uri, payload=data)

        # Pushing Intersight Systems
        if self._device.metadata.device_type not in ["imm_domain"]:
            payload = {
                "AdminState": self.enabled
            }
            if "ImmDomain" not in self.__class__.__name__:
                payload["ReadOnlyMode"] = self.read_only
            uri = "https://" + self._parent_having_logger.target + "/connector/Systems"
            self._device.put_request(uri=uri, payload=payload)

        # Pushing Intersight Device configuration
        if self._device.metadata.device_type not in ["cimc"]:
            payload = {
                "KVMTunnellingEnabled": self.tunneled_kvm,
                "ConfigurationLockoutEnabled": self.configuration_from_intersight_only
            }
            uri = "https://" + self._parent_having_logger.target + "/connector/DeviceConfigurations"
            self._device.put_request(uri=uri, payload=payload)

        return True
