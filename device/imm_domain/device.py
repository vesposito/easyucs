# coding: utf-8
# !/usr/bin/env python

""" device.py: Easy UCS Deployment Tool """

import paramiko
import requests
import socket
import time

import common
from config.imm_domain.manager import ImmDomainConfigManager
from device.device import GenericDevice
from device.device_connector import DeviceConnector
from inventory.imm_domain.manager import ImmDomainInventoryManager


class ImmDomainDevice(GenericDevice, DeviceConnector):
    """
    Creates a device of type IMM Domain.
    If you are creating an IMM Domain device then only create the object of ImmDomainDevice, do not create the
    IMM Domain FI devices separately.
    """

    def __init__(self, parent=None, uuid=None, target=None, username=None, password=None, sub_device_uuids=None,
                 fi_a=None, fi_b=None, standalone=False, is_hidden=False, is_system=False, system_usage=None,
                 logger_handle_log_level="info", log_file_path=None, user_label=""):
        GenericDevice.__init__(self, parent=parent, uuid=uuid, target=target, user=username, password=password,
                               is_hidden=is_hidden, is_system=is_system, system_usage=system_usage,
                               log_file_path=log_file_path, logger_handle_log_level=logger_handle_log_level,
                               sub_device_uuids=sub_device_uuids, user_label=user_label)
        self._session_id = None
        self._csrf_token = None

        self.fi_a = fi_a
        self.fi_b = fi_b

        self.metadata.device_type = "imm_domain"
        self.metadata.device_type_long = "IMM Domain"

        if not self.metadata.sub_device_uuids and not \
                (self.metadata.is_system and self.metadata.system_usage == "catalog"):
            # An IMM Domain device will have at least one IMM Domain FI.
            self.fi_a = ImmDomainFiDevice(parent=parent, target=target, username=username, password=password, node="A",
                                          is_hidden=True, parent_device=self)
            self.sub_devices.append(self.fi_a)
            self.metadata.sub_device_uuids = [str(self.fi_a.uuid)]
            if not standalone:
                self.fi_b = ImmDomainFiDevice(parent=parent, target=target, username=username, password=password,
                                              node="B", is_hidden=True, parent_device=self)
                self.sub_devices.append(self.fi_b)
                self.metadata.sub_device_uuids.append(str(self.fi_b.uuid))

        self.config_manager = ImmDomainConfigManager(parent=self)
        self.inventory_manager = ImmDomainInventoryManager(parent=self)

    def connect(self, force=None, bypass_version_checks=False, retries=1):
        """
        Establishes connection to the device
        :param force: if set to True, reconnects even if cookie exists and is valid for respective connection
        :param bypass_version_checks: Whether the minimum version checks should be bypassed when connecting
        :param retries: Number of retries after unsuccessful connections before exiting
        :return: True if connection successfully established, False otherwise
        """
        if self.task is not None:
            self.task.taskstep_manager.start_taskstep(
                name="ConnectImmDomainDevice",
                description="Connecting to " + self.metadata.device_type_long + " device")

        for i in range(retries):
            if i != 0:
                self.logger(level="debug", message="Connection attempt number " + str(i + 1))
                time.sleep(5)
            self.logger(level="info", message=f"Trying to connect to {self.metadata.device_type_long}: {self.target}")
            try:
                payload = {
                    "User": self.metadata.username,
                    "Password": self.metadata.password
                }
                response = requests.post(url=f"https://{self.target}/Login", json=payload, verify=False)
                if response.status_code != 200:
                    self.logger(level="error",
                                message=f"Couldn't login to the device connector, response: {response.text}")
                    continue
                elif "InvalidRequest" in response.text:
                    self.logger(level="error", message=response.json()["message"])
                    continue
                self._csrf_token = response.headers["X-Csrf-Token"]

                response = response.json()
                self._session_id = response["SessionId"]

                self._set_device_name_and_version()
                self._set_device_connector_info(wait_for_connection_status=True)
                self.metadata.is_reachable = True

                if self.task is not None:
                    self.task.taskstep_manager.stop_taskstep(
                        name="ConnectImmDomainDevice", status="successful",
                        status_message="Successfully connected to " + self.metadata.device_type_long + " device " +
                                       str(self.name))
                return True
            except Exception as err:
                self.logger(level="error", message="Error while trying to connect to " +
                                                   self.metadata.device_type_long + ": " +
                                                   self.target + ": " + str(err))
                continue

        self.metadata.is_reachable = False
        if self.task is not None:
            self.task.taskstep_manager.stop_taskstep(
                name="ConnectImmDomainDevice", status="failed",
                status_message="Error while connecting to " + self.metadata.device_type_long + " device " +
                               str(self.name))
        return False

    def disconnect(self):
        """
        Disconnects from the device
        :return: True if disconnection is successful, False otherwise
        """
        if self.task is not None:
            self.task.taskstep_manager.start_taskstep(
                name="DisconnectImmDomainDevice",
                description="Disconnecting from " + self.metadata.device_type_long + " device " + str(self.name))
        self.logger(message="Disconnecting from " + self.metadata.device_type_long + ": " + str(self.name))
        try:
            response = requests.post(url=f"https://{self.target}/Logout",
                                     headers={'Cookie': f"sessionId={self._session_id}",
                                              'X-Csrf-Token': self._csrf_token},
                                     verify=False)
            if response.status_code != 200:
                self.logger(level="error",
                            message=f"Couldn't logout to the device connector, response: {response.text}")
            elif "InvalidRequest" in response.text:
                self.logger(level="error", message=response.json()["message"])
            else:
                self._session_id = None
                self._csrf_token = None

                if self.task is not None:
                    self.task.taskstep_manager.stop_taskstep(
                        name="DisconnectImmDomainDevice", status="successful",
                        status_message="Successfully disconnected from " + self.metadata.device_type_long + " device " +
                                       str(self.name))
                return True
        except Exception as err:
            self.logger(level="error",
                        message=f"Could not disconnect from {self.metadata.device_type_long} '{str(self.name)}': {err}")
        if self.task is not None:
            self.task.taskstep_manager.stop_taskstep(
                name="DisconnectImmDomainDevice", status="failed",
                status_message="Error while disconnecting from " + self.metadata.device_type_long + " device " +
                               str(self.name))
        return False

    def initial_setup(self, fi_ip_list=None, config=None, target_admin_password=None):
        """
        Performs initial setup of IMM System
        :param fi_ip_list: List of DHCP IP addresses taken by the Fabric Interconnect(s) after boot stage
        :param config: Config of device to be used for initial setup (for Hostname/IP/DNS/Domain Name)
        :param target_admin_password: Password to be used for IMM setup
        :return: True if initial setup is successful, False otherwise
        """

        if not config or not fi_ip_list or not target_admin_password:
            self.logger(level="error",
                        message="Please provide config OR FI IP list with the admin password to do the initial setup")
            return False
        self.set_task_progression(10)

        fi_a_dhcp_ip_address = ""
        fi_b_dhcp_ip_address = ""
        fi_a_target_ip_address = ""
        fi_b_target_ip_address = ""
        target_netmask = ""
        target_sysname = ""
        target_domain_name = ""
        target_dns = ""
        target_gateway = ""

        self.logger(message="Performing initial setup of IMM")

        if self.task is not None:
            self.task.taskstep_manager.start_taskstep(
                name="ValidateImmDomainConfigAndSetupDetails",
                description=f"Validating the contents of the IMM config and provided setup details")

        # Getting fabric information from config
        if not config.system_information or not config.system_information[0].fabric_interconnects:
            message_str = "Could not find fabric information parameters in source config"
            self.logger(level="error", message=message_str)
            if self.task is not None:
                self.task.taskstep_manager.stop_taskstep(
                    name="ValidateImmDomainConfigAndSetupDetails", status="failed", status_message=message_str)
            return False

        if len(fi_ip_list) == 1:
            # Standalone mode is not supported in IMM
            message_str = "FI IP list have only one IP. Standalone mode is not supported in IMM"
            self.logger(level="error", message=message_str)
            if self.task is not None:
                self.task.taskstep_manager.stop_taskstep(
                    name="ValidateImmDomainConfigAndSetupDetails", status="failed", status_message=message_str)
            return False

        elif len(fi_ip_list) == 2:
            # We are doing an initial setup in cluster mode
            fi_a_dhcp_ip_address = fi_ip_list[0]
            fi_b_dhcp_ip_address = fi_ip_list[1]

            # Ensure Fabric A and Fabric B IPs are not the same
            if fi_a_dhcp_ip_address == fi_b_dhcp_ip_address:
                message_str = f"Fabric A and Fabric B cannot have the same DHCP IP address: {fi_a_dhcp_ip_address}"
                self.logger(level="error", message=message_str)
                if self.task is not None:
                    self.task.taskstep_manager.stop_taskstep(
                        name="ValidateImmDomainConfigAndSetupDetails", status="failed", status_message=message_str)
                return False

            if not common.is_ip_address_valid(fi_a_dhcp_ip_address):
                message_str = f"{fi_a_dhcp_ip_address} is not a valid DHCP IP address for Fabric A"
                self.logger(level="error", message=message_str)
                if self.task is not None:
                    self.task.taskstep_manager.stop_taskstep(
                        name="ValidateImmDomainConfigAndSetupDetails", status="failed", status_message=message_str)
                return False

            if not common.is_ip_address_valid(fi_b_dhcp_ip_address):
                message_str = f"{fi_b_dhcp_ip_address} is not a valid DHCP IP address for Fabric B"
                self.logger(level="error", message=message_str)
                if self.task is not None:
                    self.task.taskstep_manager.stop_taskstep(
                        name="ValidateImmDomainConfigAndSetupDetails", status="failed", status_message=message_str)
                return False

            # Going through all entries in fabric_interconnects to find the right one
            for fabric_interconnect in config.system_information[0].fabric_interconnects:
                if fabric_interconnect.get("fabric").upper() == 'A':
                    if fabric_interconnect.get("ip"):
                        fi_a_target_ip_address = fabric_interconnect.get("ip")
                        self.logger(message="Using IP address for Fabric A: " + fi_a_target_ip_address)
                    else:
                        # IP address of FI A is a mandatory input - Exiting
                        message_str = "Could not find Management IP address of Fabric A in config"
                        self.logger(level="error", message=message_str)
                        if self.task is not None:
                            self.task.taskstep_manager.stop_taskstep(
                                name="ValidateImmDomainConfigAndSetupDetails", status="failed", status_message=message_str)
                        return False

                    if fabric_interconnect.get("netmask"):
                        target_netmask = fabric_interconnect.get("netmask")
                        self.logger(message="Using netmask for Cluster: " + target_netmask)

                    if fabric_interconnect.get("gateway"):
                        target_gateway = fabric_interconnect.get("gateway")
                        self.logger(message="Using gateway for Cluster: " + target_gateway)

                if fabric_interconnect.get("fabric").upper() == 'B':
                    if fabric_interconnect.get("ip"):
                        fi_b_target_ip_address = fabric_interconnect.get("ip")
                        self.logger(message="Using IP address for Fabric B: " + fi_b_target_ip_address)
                    else:
                        # IP address of FI B is a mandatory input - Exiting
                        message_str = "Could not find Management IP address of Fabric B in config"
                        self.logger(level="error", message=message_str)
                        if self.task is not None:
                            self.task.taskstep_manager.stop_taskstep(
                                name="ValidateImmDomainConfigAndSetupDetails", status="failed", status_message=message_str)
                        return False

                    if fabric_interconnect.get("netmask"):
                        # Using netmask of FI A if already found
                        if not target_netmask:
                            target_netmask = fabric_interconnect.get("netmask")
                            self.logger(message="Using netmask for Cluster: " + target_netmask)

                    if fabric_interconnect.get("gateway"):
                        # Using gateway of FI A if already found
                        if not target_gateway:
                            target_gateway = fabric_interconnect.get("gateway")
                            self.logger(message="Using gateway for Cluster: " + target_gateway)

            # We went through all entries in fabric_interconnect - making sure we got the information we needed
            if not fi_a_target_ip_address or not fi_b_target_ip_address or not target_netmask or not target_gateway:
                message_str = "Could not find IP-addresses/netmask/gateway for Fabric A or B in config"
                self.logger(level="error", message=message_str)
                if self.task is not None:
                    self.task.taskstep_manager.stop_taskstep(
                        name="ValidateImmDomainConfigAndSetupDetails", status="failed", status_message=message_str)
                return False

        # Fetching system name
        if config.system_information[0].name:
            target_sysname = config.system_information[0].name
            self.logger(message="Using System Name: " + target_sysname)
        else:
            # system name is a mandatory input - Exiting
            message_str = "Could not find system name in config"
            self.logger(level="error", message=message_str)
            if self.task is not None:
                self.task.taskstep_manager.stop_taskstep(
                    name="ValidateImmDomainConfigAndSetupDetails", status="failed", status_message=message_str)
            return False

        # Getting fabric information from config
        if not config.device_connector:
            message_str = "Could not find device connector parameters in config"
            self.logger(level="error", message=message_str)
            if self.task is not None:
                self.task.taskstep_manager.stop_taskstep(
                    name="ValidateImmDomainConfigAndSetupDetails", status="failed", status_message=message_str)
            return False

        # Fetching Domain Name
        if config.device_connector[0].dns_configuration and \
                config.device_connector[0].dns_configuration.get("domain_name"):
            target_domain_name = config.device_connector[0].dns_configuration.get("domain_name")
            self.logger(message="Using Domain name: " + target_domain_name)
        else:
            # Domain name is not a mandatory input - Generates warning
            self.logger(level="warning", message="Could not find DNS Domain Name in config - Skipping")

        # Getting DNS config
        # NOTE: What happens when we have 2 DNS servers. Currently, we are always taking the first one.
        if (config.device_connector[0].dns_configuration and
                not config.device_connector[0].dns_configuration.get("dns_servers")):
            # Storing ... as dns to get empty strings after split operation for payload
            target_dns = "..."
            self.logger(level="warning", message="Could not find DNS parameters in source config")
        elif (config.device_connector[0].dns_configuration and
              common.is_ip_address_valid(config.device_connector[0].dns_configuration.get("dns_servers")[0])):
            # We only support setting a single DNS server
            target_dns = config.device_connector[0].dns_configuration.get("dns_servers")[0]
            self.logger(message="Using DNS server: " + target_dns)
        else:
            # Storing ... as dns to get empty strings after split operation for payload
            target_dns = "..."
            self.logger(level="warning",
                        message=f"Invalid or missing DNS server configuration. Proceeding without a DNS server.")

        if self.task is not None:
            self.task.taskstep_manager.stop_taskstep(
                name="ValidateImmDomainConfigAndSetupDetails", status="successful",
                status_message="Successfully validated the IMM config and provided setup details")

        if self.task is not None:
            self.task.taskstep_manager.start_taskstep(
                name="SetupFabricA",
                description=f"Setting up Fabric A in IMM mode")

        payload_fi_a_step_1 = {"mgmt_mode": "intersight"}

        payload_fi_a_step_2 = {
                                'hidden_init': 'hidden_init',
                                'mgmt_mode': 'intersight',
                                'cluster': '1',
                                'ooblocalFIIP1': '',
                                'ooblocalFIIP2': '',
                                'ooblocalFIIP3': '',
                                'ooblocalFIIP4': '',
                                'ooblocalFIIPv6': '',
                                'switchFabric': '1',
                                'ipformat': '1',
                                'virtualIP1': '',
                                'virtualIP2': '',
                                'virtualIP3': '',
                                'virtualIP4': '',
                                'yes_or_no_passwd': '2',
                                'systemName': target_sysname,
                                'adminPasswd': target_admin_password,
                                'adminPasswd1': target_admin_password,
                                'oobIP1': fi_a_target_ip_address.split(".")[0],
                                'oobIP2': fi_a_target_ip_address.split(".")[1],
                                'oobIP3': fi_a_target_ip_address.split(".")[2],
                                'oobIP4': fi_a_target_ip_address.split(".")[3],
                                'oobNM1': target_netmask.split(".")[0],
                                'oobNM2': target_netmask.split(".")[1],
                                'oobNM3': target_netmask.split(".")[2],
                                'oobNM4': target_netmask.split(".")[3],
                                'oobGW1': target_gateway.split(".")[0],
                                'oobGW2': target_gateway.split(".")[1],
                                'oobGW3': target_gateway.split(".")[2],
                                'oobGW4': target_gateway.split(".")[3],
                                'dns1': target_dns.split(".")[0],
                                'dns2': target_dns.split(".")[1],
                                'dns3': target_dns.split(".")[2],
                                'dns4': target_dns.split(".")[3],
                                'domainName': target_domain_name,
                                'pasadena1': '',
                                'pasadena2': '',
                                'pasadena3': '',
                                'pasadena4': '',
                                'pasadenaSecret': '',
                                'virtualIPv6': '',
                                'yes_or_no_passwd_ipv6': '1',
                                'systemNameipv6': '',
                                'adminPasswdipv6': '',
                                'adminPasswd1ipv6': '',
                                'oobIPv6': '',
                                'oobPrefix': '',
                                'oobIPv6GW': '',
                                'IPv6dns': '',
                                'domainNameipv6': '',
                                'IPv6pasadena': '',
                                'ipv6pasadenaSecret': ''}

        payload_fi_b_step_1 = {'hidden_forcePeerA': '',
                               'mgmt_mode': 'ucsm',
                               'cluster': '1',
                               'switchFabric': '2',
                               'adminPasswd': target_admin_password}

        payload_fi_b_step_2 = {'hidden_forcePeerA': '',
                               'mgmt_mode': 'intersight',
                               'cluster': '1',
                               'switchFabric': '2',
                               'adminPasswd': ''}

        payload_fi_b_step_3 = {'hidden_init': 'hidden_init',
                               'mgmt_mode': 'intersight',
                               'oobIP1': fi_b_target_ip_address.split(".")[0],
                               'oobIP2': fi_b_target_ip_address.split(".")[1],
                               'oobIP3': fi_b_target_ip_address.split(".")[2],
                               'oobIP4': fi_b_target_ip_address.split(".")[3],
                               'oobIPv6': ''}

        url_fi_a = "https://" + fi_a_dhcp_ip_address + "/cgi-bin/initial_setup_new.cgi"
        url_fi_b_add_cluster = "https://" + fi_b_dhcp_ip_address + "/cgi-bin/initial_setup_clusteradd.cgi"
        url_fi_b_setup_oob = "https://" + fi_b_dhcp_ip_address + "/cgi-bin/initial_setup_oob.cgi"

        # Disable requests warnings about HTTPS
        requests.packages.urllib3.disable_warnings()

        # Since both FIs reboot during the erase configuration process, checking reachability immediately may fail.
        # Therefore, it is recommended to wait approximately 10 minutes while monitoring FI's status
        # before proceeding with the initial configuration.
        # The timeout for the check_Webpage function has been updated to 10 minutes accordingly.
        self.logger(message="Checking if both Fabric Interconnects are ready for initial setup...")
        for fi_ip in fi_ip_list:
            if not common.check_web_page(device=self, url="https://" + fi_ip, str_match="Express Setup",
                                         timeout=600):
                message_str = f"Fabric Interconnect {fi_ip} is not ready for initial setup"
                self.logger(level="error", message=message_str)
                if self.task is not None:
                    self.task.taskstep_manager.stop_taskstep(
                        name="SetupFabricA", status="failed", status_message=message_str)
                return False

        # Send Management Mode to FI A
        resp = self.post_request_initial_setup(request_url=url_fi_a, request_payload=payload_fi_a_step_1,
                                               error_message="send management mode to Fabric A")
        if not resp or resp.status_code != 200:
            message_str = "Error while setting up Fabric A in IMM Mode"
            self.logger(level="error", message=message_str)
            if self.task is not None:
                self.task.taskstep_manager.stop_taskstep(
                    name="SetupFabricA", status="failed", status_message=message_str)
            return False

        # Send configuration to FI A
        resp = self.post_request_initial_setup(request_url=url_fi_a, request_payload=payload_fi_a_step_2,
                                               error_message="send initial configuration to Fabric A")
        if not resp or resp.status_code != 200:
            message_str = "Error while setting up Fabric A in IMM Mode"
            self.logger(level="error", message=message_str)
            if self.task is not None:
                self.task.taskstep_manager.stop_taskstep(
                    name="SetupFabricA", status="failed", status_message=message_str)
            return False

        self.logger(message="Sent initial configuration to FI A")
        self.set_task_progression(30)

        message_str = "Successfully completed setting up Fabric A in IMM mode"
        if self.task is not None:
            self.task.taskstep_manager.stop_taskstep(
                name="SetupFabricA", status="successful",
                status_message=message_str)

        self.logger(message=message_str)

        if self.task is not None:
            self.task.taskstep_manager.start_taskstep(
                name="WaitForFabricAToBeReachable",
                description=f"Waiting until Fabric A IP is reachable")

        self.logger(message="Waiting up to 15 minutes for FI A configuration to be processed")

        # Immediate verification of IP reachability may fail because the device connector requires approximately 15
        # minutes of time to reset after the initial setup.
        # A 2-minute pause is added to allow for initial stabilization.
        time.sleep(120)

        # Wait until FI A has processed configuration - needed for FI B to recognize that its peer is configured
        if not common.check_web_page(self, "https://" + fi_a_target_ip_address, "device-console", 780):
            message_str = "Impossible to reconnect to Fabric A after the initial configuration"
            self.logger(level="error", message=message_str)
            if self.task is not None:
                self.task.taskstep_manager.stop_taskstep(
                    name="WaitForFabricAToBeReachable", status="failed", status_message=message_str)
            return False

        message_str = "Fabric A is configured in IMM mode and is reachable"
        if self.task is not None:
            self.task.taskstep_manager.stop_taskstep(
                name="WaitForFabricAToBeReachable", status="successful",
                status_message=message_str)
        self.logger(message=message_str)
        self.set_task_progression(60)

        if self.task is not None:
            self.task.taskstep_manager.start_taskstep(
                name="SetupFabricB",
                description=f"Setting up Fabric B in IMM mode")

        # send initial configuration to FI B - Step 1
        resp = self.post_request_initial_setup(request_url=url_fi_b_add_cluster, request_payload=payload_fi_b_step_1,
                                               error_message="send initial configuration to FI B - Step 1")
        if not resp or resp.status_code != 200:
            message_str = "Error while setting up Fabric B step-1 in IMM Mode"
            self.logger(level="error", message=message_str)
            if self.task is not None:
                self.task.taskstep_manager.stop_taskstep(
                    name="SetupFabricB", status="failed", status_message=message_str)
            return False

        self.set_task_progression(80)
        self.logger(message="Sent initial configuration to FI B")

        # send initial configuration to FI B - Step 2
        resp = self.post_request_initial_setup(request_url=url_fi_b_setup_oob, request_payload=payload_fi_b_step_2,
                                               error_message="send initial configuration to FI B - Step 2")
        if not resp or resp.status_code != 200:
            message_str = "Error while setting up Fabric B step-2 in IMM Mode"
            self.logger(level="error", message=message_str)
            if self.task is not None:
                self.task.taskstep_manager.stop_taskstep(
                    name="SetupFabricB", status="failed", status_message=message_str)
            return False

        # send initial configuration to FI B - Step 3
        resp = self.post_request_initial_setup(request_url=url_fi_b_setup_oob, request_payload=payload_fi_b_step_3,
                                               error_message="send initial configuration to FI B - Step 3")
        if not resp or resp.status_code != 200:
            message_str = "Error while setting up Fabric B step-3 in IMM Mode"
            self.logger(level="error", message=message_str)
            if self.task is not None:
                self.task.taskstep_manager.stop_taskstep(
                    name="SetupFabricB", status="failed", status_message=message_str)
            return False

        message_str = "Successfully completed setting up Fabric B in IMM mode"
        if self.task is not None:
            self.task.taskstep_manager.stop_taskstep(
                name="SetupFabricB", status="successful",
                status_message=message_str)

        self.logger(message=message_str)

        # Updating the device and its sub devices credentials
        self.target = self.metadata.target = self.fi_a.target = self.fi_a.metadata.target = fi_a_target_ip_address
        self.fi_b.target = self.fi_b.metadata.target = fi_b_target_ip_address
        self.username = self.metadata.username = self.fi_a.username = self.fi_a.metadata.username = "admin"
        self.fi_b.username = self.fi_b.metadata.username = "admin"
        self.password = self.metadata.password = self.fi_a.password = self.fi_a.metadata.password = \
            target_admin_password
        self.fi_b.password = self.fi_b.metadata.password = target_admin_password

        if self.task is not None:
            self.task.taskstep_manager.start_taskstep(
                name="WaitForFabricBToBeReachable",
                description=f"Waiting until Fabric B IP is reachable")

        self.logger(message="Waiting up to 15 minutes for FI B configuration to be processed")

        # Immediate verification of IP reachability may fail because the device connector requires approximately 15
        # minutes of time to reset after the initial setup.
        # A 2-minute pause is added to allow for initial stabilization.
        time.sleep(120)

        # Wait until FI B has processed configuration - needed for FI B to recognize that its peer is configured
        if not common.check_web_page(self, "https://" + fi_b_target_ip_address, "device-console", 780):
            message_str = "Impossible to reconnect to Fabric B after the initial configuration"
            self.logger(level="error", message=message_str)
            if self.task is not None:
                self.task.taskstep_manager.stop_taskstep(
                    name="WaitForFabricBToBeReachable", status="failed", status_message=message_str)
            return False

        message_str = "Fabric B is configured in IMM mode and is reachable"
        if self.task is not None:
            self.task.taskstep_manager.stop_taskstep(
                name="WaitForFabricBToBeReachable", status="successful",
                status_message=message_str)
        self.logger(message=message_str)

        self.set_task_progression(100)
        return True

    def is_connected(self):
        """
        Checks if the session id is still valid
        :return: True if connected, False otherwise
        """
        if self._session_id and self._csrf_token:
            # TODO: Check whether session id is valid
            return True
        return False

    def reset(self, bypass_version_checks=False, reset_device_connector=False):
        """
        Erases all configuration from the UCS System
        :param bypass_version_checks: Whether the minimum version checks should be bypassed when connecting
        :param reset_device_connector: Whether the Device Connector should be reset if claimed
        :return: True if reset is successful, False otherwise
        """

        self.set_task_progression(5)
        # First, make sure we are connected to the device
        if not self.connect(bypass_version_checks=bypass_version_checks):
            self.logger(level="error", message="Unable to connect to IMM Domain")
            return False

        if reset_device_connector and self.metadata.device_connector_claim_status == "claimed":
            # If the IMM Domain device is claimed to Intersight, unclaim the device
            if not self.reset_device_connector():
                self.logger(level="error", message=f"Error while un-claiming the {self.metadata.device_type_long} "
                                                   f"device {self.name} from Intersight")
                return False
        else:
            if self.task is not None:
                self.task.taskstep_manager.skip_taskstep(
                    name="ResetDeviceConnector",
                    status_message=f"Skipping the unclaim of {self.metadata.device_type_long} device {self.name} since "
                                   f"it is not claimed to Intersight"
                )

        if self.task is not None:
            self.task.taskstep_manager.start_taskstep(
                name="EraseFiConfigurations",
                description=f"Resetting Fabric Interconnects of {self.metadata.device_type_long} device {self.name}")

        ip_sw_addr = []

        if len(self.sub_devices) == 2:
            self.logger(level="debug", message="Trying to get Fabric Interconnects IP addresses")
        elif len(self.sub_devices) == 1:
            self.logger(level="debug", message="Trying to get Fabric Interconnect IP address")
        else:
            message_str = "Unable to find Fabric Interconnects to reset"
            self.logger(level="error", message=message_str)
            if self.task is not None:
                self.task.taskstep_manager.stop_taskstep(
                    name="EraseFiConfigurations", status="failed", status_message=message_str)
            return False

        try:
            # Get IP address of FI A
            ip_a = self.sub_devices[0].target
            ip_sw_addr.append(ip_a)
            self.logger(level="debug", message="IP address of FI A: " + ip_a)

        except Exception as err:
            message_str = "Cannot get IP address of Fabric Interconnect A"
            self.logger(level="error", message=message_str + ": " + str(err))
            if self.task is not None:
                self.task.taskstep_manager.stop_taskstep(
                    name="EraseFiConfigurations", status="failed", status_message=message_str)
            return False

        try:
            # Get IP address of FI B if present (in cluster mode only)
            if len(self.sub_devices) == 2:
                ip_b = self.sub_devices[1].target
                ip_sw_addr.append(ip_b)
                self.logger(level="debug", message="IP address of FI B: " + ip_b)

        except Exception as err:
            message_str = "Cannot get IP address of Fabric Interconnect B"
            self.logger(level="error", message=message_str + ": " + str(err))
            if self.task is not None:
                self.task.taskstep_manager.stop_taskstep(
                    name="EraseFiConfigurations", status="failed", status_message=message_str)
            return False

        for ip in ip_sw_addr:
            self.logger(message="Resetting Fabric Interconnect with IP address: " + ip)

            # Establishing connection to FI
            try:
                error_msg = None
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(ip, port=22, username=self.username, password=self.password, banner_timeout=30)

            except paramiko.AuthenticationException:
                error_msg = "Authentication failed when connecting to Fabric Interconnect " + ip
                self.logger(level="error", message=error_msg)

            except TypeError as err:
                self.logger(level="debug",
                            message="Error while connecting to Fabric Interconnect " + ip + ": " + str(err))
                error_msg = "Error while connecting to Fabric Interconnect " + ip + ". Please try again."
                self.logger(level="error", message=error_msg)

            except Exception as err:
                error_msg = "Error while connecting to Fabric Interconnect " + ip
                self.logger(level="error", message=error_msg + ": " + str(err))

            if error_msg:
                if self.task is not None:
                    self.task.taskstep_manager.stop_taskstep(
                        name="EraseFiConfigurations", status="failed", status_message=error_msg)
                return False

            # Erasing configuration of FI
            try:
                error_msg = None
                channel = client.invoke_shell()
                channel.settimeout(20)

                self.logger(level="debug", message="\tSending 'erase-configuration'")
                channel.send('erase-configuration\n')

                buff = ""
                while not "Enter 'y' to continue:" in buff:
                    resp = channel.recv(9999)
                    buff += resp.decode("utf-8")

                self.logger(level="debug", message="\tSending confirmation")
                channel.send('y\n')
                time.sleep(5)
                self.set_task_progression(10)

            except paramiko.ChannelException as err:
                error_msg = "Communication failed with Fabric Interconnect " + ip
                self.logger(level="error", message=error_msg + ": " + str(err))

            except (paramiko.buffered_pipe.PipeTimeout, socket.timeout):
                error_msg = "Timeout while communicating with Fabric Interconnect " + ip
                self.logger(level="error", message=error_msg)

            except Exception as err:
                error_msg = "Error while erasing the configuration of Fabric Interconnect " + ip
                self.logger(level="error", message=error_msg + ": " + str(err))

            if error_msg:
                if self.task is not None:
                    self.task.taskstep_manager.stop_taskstep(
                        name="EraseFiConfigurations", status="failed", status_message=error_msg)
                return False

        if self.task is not None:
            self.task.taskstep_manager.stop_taskstep(
                name="EraseFiConfigurations", status="successful",
                status_message=f"Successfully reset Fabric Interconnects of {self.metadata.device_type_long} " +
                               f"device {self.name}"
            )
        return True

    def _set_device_name_and_version(self):
        """
        Sets the device name and version attributes of the device. Also sets the FI model attributes
        :return: nothing
        """
        if self._session_id and self._csrf_token:
            response = self.get_request(uri=f"https://{self.target}/DomainName")
            if not response:
                return
            self.name = self.metadata.device_name = response["DomainName"]

            response = self.get_request(uri=f"https://{self.target}/connector/Versions")
            if not response:
                return
            self.version = self.metadata.device_version = response[0]["Version"]

            response = self.get_request(uri=f"https://{self.target}/SystemInfo")
            if not response:
                return
            if self.fi_a:
                self.fi_a.node = response["FIA"]["Node"]
                self.fi_a.model = response["FIA"]["Model"]
                self.fi_a.version = self.fi_a.metadata.device_version = response["FIA"]["FwVersion"]
                self.fi_a.metadata.device_name = self.fi_a.name = response["FIA"]["HostName"] + "-A"
                self.fi_a.metadata.target = self.fi_a.target = response["FIA"]["MgmtIpv4"]
            if self.fi_b:
                self.fi_b.node = response["FIB"]["Node"]
                self.fi_b.model = response["FIB"]["Model"]
                self.fi_b.version = self.fi_b.metadata.device_version = response["FIB"]["FwVersion"]
                self.fi_b.metadata.device_name = self.fi_b.name = response["FIB"]["HostName"] + "-B"
                self.fi_b.metadata.target = self.fi_b.target = response["FIB"]["MgmtIpv4"]


class ImmDomainFiDevice(GenericDevice):

    def __init__(self, parent=None, uuid=None, target=None, username=None, password=None, parent_device=None, node=None,
                 parent_device_uuid=None, is_hidden=True, is_system=False, system_usage=None,
                 logger_handle_log_level="info", log_file_path=None, user_label=""):
        GenericDevice.__init__(self, parent=parent, uuid=uuid, target=target, is_hidden=is_hidden, user=username,
                               is_system=is_system, system_usage=system_usage, password=password,
                               logger_handle_log_level=logger_handle_log_level, log_file_path=log_file_path,
                               user_label=user_label)

        self.parent_device = parent_device
        self.model = None
        self.node = node
        self.version = None

        self.metadata.device_type = "imm_domain_fi"
        self.metadata.device_type_long = "IMM Domain FI"
        self.metadata.parent_device_uuid = parent_device_uuid

        if not self.metadata.parent_device_uuid and self.parent_device:
            self.metadata.parent_device_uuid = self.parent_device.uuid
