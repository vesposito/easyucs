# coding: utf-8
# !/usr/bin/env python

""" device.py: Easy UCS Deployment Tool """

import datetime
import http
import os
import re
import socket
import threading
import time
import urllib

import paramiko
import requests
from imcsdk import __version__ as imcsdk_sdk_version
from imcsdk.imccoremeta import ImcVersion
from imcsdk.imcexception import ImcException
from imcsdk.imchandle import ImcHandle
from imcsdk.imcmeta import VersionMeta as ImcVersionMeta
from imcsdk.mometa.comm.CommSsh import CommSsh as imcsdk_CommSsh
from ucscsdk import __version__ as ucscsdk_sdk_version
from ucscsdk.ucsccoremeta import UcscVersion
from ucscsdk.ucscexception import UcscException
from ucscsdk.ucschandle import UcscHandle
from ucscsdk.ucscmeta import VersionMeta as UcscVersionMeta
from ucsmsdk import __version__ as ucsmsdk_sdk_version
from ucsmsdk.mometa.comm.CommSsh import CommSsh as ucsmsdk_CommSsh
from ucsmsdk.mometa.firmware.FirmwareDownloader import FirmwareDownloader
from ucsmsdk.ucscoremeta import UcsVersion
from ucsmsdk.ucsexception import UcsException
from ucsmsdk.ucshandle import UcsHandle
from ucsmsdk.ucsmeta import version as ucsmsdk_ucs_version

import common
from backup.ucs.manager import UcsCentralBackupManager, UcsImcBackupManager, UcsSystemBackupManager
from config.ucs.manager import UcsImcConfigManager, UcsSystemConfigManager, UcsCentralConfigManager
from device.device import GenericDevice
from device.device_connector import DeviceConnector
from inventory.ucs.manager import UcsImcInventoryManager, UcsSystemInventoryManager, UcsCentralInventoryManager
from report.ucs.manager import UcsCentralReportManager, UcsImcReportManager, UcsSystemReportManager


class GenericUcsDevice(GenericDevice, DeviceConnector):
    _MAX_PUSH_ATTEMPTS = 3
    _PUSH_INTERVAL_AFTER_FAIL = 5

    def __init__(self, parent=None, uuid=None, target="", user="", password="", is_hidden=False, is_system=False,
                 system_usage=None, logger_handle_log_level="info", log_file_path=None, bypass_connection_checks=False,
                 bypass_version_checks=False, user_label=""):
        GenericDevice.__init__(self, parent=parent, uuid=uuid, target=target, password=password, user=user,
                               is_hidden=is_hidden, is_system=is_system, system_usage=system_usage,
                               logger_handle_log_level=logger_handle_log_level, log_file_path=log_file_path,
                               bypass_connection_checks=bypass_connection_checks,
                               bypass_version_checks=bypass_version_checks,
                               user_label=user_label)

        self.handle = None
        self.intersight_status = "unknown"

        self.metadata.device_type = "ucs"
        self.metadata.device_type_long = "UCS Generic"

        self._device_connector_info = {}

        # Commit parameters
        self.push_attempts = self._MAX_PUSH_ATTEMPTS
        self.push_interval_after_fail = self._PUSH_INTERVAL_AFTER_FAIL

    def connect(self, auto_refresh=None, force=None, bypass_version_checks=False, retries=1):
        """
        Establishes connection to the device
        :param auto_refresh: if set to True, refreshes the UCS login cookie continuously
        :param force: if set to True, reconnects even if cookie exists and is valid for respective connection
        :param bypass_version_checks: Whether the minimum version checks should be bypassed when connecting
        :param retries: Number of retries after unsuccessful connections before exiting
        :return: True if connection successfully established, False otherwise
        """
        task_name = None
        if self.metadata.device_type == "cimc":
            task_name = "ConnectUcsImcDevice"
        elif self.metadata.device_type == "ucsc":
            task_name = "ConnectUcsCentralDevice"
        elif self.metadata.device_type == "ucsm":
            task_name = "ConnectUcsSystemDevice"

        if self.task is not None and task_name is not None:
            self.task.taskstep_manager.start_taskstep(
                name=task_name,
                description="Connecting to " + self.metadata.device_type_long + " device")
        self.logger(level="debug",
                    message="Using " + self.metadata.device_type_long + " SDK version " + str(self.version_sdk))
        for i in range(retries):
            if i != 0:
                self.logger(message="Connection attempt number " + str(i + 1))
                time.sleep(5)
            self.logger(message="Trying to connect to " + self.metadata.device_type_long + ": " + self.target)
            try:
                self.handle.login(auto_refresh=auto_refresh, force=force)
                self._set_device_name_and_version()
                self.metadata.timestamp_last_connected = datetime.datetime.now()
                self.metadata.is_reachable = True
                if self.metadata.device_type in ["cimc", "ucsm"]:
                    self._set_device_connector_info()

                version = "unknown"
                if self.version:
                    if hasattr(self.version, "version"):
                        version = self.version.version

                self.logger(message="Connected to " + str(self.name) + " running version " + version)

                # Verify if version running is above the minimum required version
                if self.version.__le__(self.version_min_required):
                    if not bypass_version_checks:
                        from api.api_server import easyucs
                        if easyucs:
                            self.metadata.is_reachable = False
                            self.logger(
                                level="error",
                                message="EasyUCS supports version " + self.version_min_required.version +
                                        " and above. Your version " + self.version.version + " is not supported."
                            )
                            return False
                        else:
                            self.logger(
                                level="warning",
                                message="EasyUCS supports version " + self.version_min_required.version +
                                        " and above. Your version " + self.version.version + " is not supported."
                            )
                            if not common.query_yes_no(
                                    "Are you sure you want to continue with an unsupported version?"):
                                # User declined continue with unsupported version query
                                self.disconnect()
                                exit()
                    else:
                        self.logger(level="warning", message="EasyUCS supports version " +
                                                             self.version_min_required.version + " and above. Your " +
                                                             "version " + self.version.version + " is not supported.")

                # Verify if version running is supported by SDK version
                sdk_name = ""
                if isinstance(self.version_max_supported_by_sdk, UcsVersion):
                    sdk_name = "ucsmsdk"
                elif isinstance(self.version_max_supported_by_sdk, ImcVersion):
                    sdk_name = "imcsdk"
                elif isinstance(self.version_max_supported_by_sdk, UcscVersion):
                    sdk_name = "ucscsdk"

                if self.version.__ge__(self.version_max_supported_by_sdk):
                    self.logger(level="debug", message="Version " + self.version.version +
                                                       " running is not yet supported by " + sdk_name + "!")

                if self.task is not None and task_name is not None:
                    self.task.taskstep_manager.stop_taskstep(
                        name=task_name, status="successful",
                        status_message="Successfully connected to " + self.metadata.device_type_long + " device " +
                                       str(self.name))
                return True

            except urllib.error.URLError as err:
                if type(err.reason) == TimeoutError:
                    self.logger(level="error", message="Timeout while trying to connect to " +
                                                       self.metadata.device_type_long + ": " + self.target)
                elif type(err.reason) == ConnectionRefusedError:
                    self.logger(level="error", message="Connection refused while trying to connect to " +
                                                       self.metadata.device_type_long + ": " + self.target)
                else:
                    self.logger(level="error", message="URL error while trying to connect to " +
                                                       self.metadata.device_type_long + ": " + self.target + ": " +
                                                       str(err))
                continue
            except (UcsException, ImcException) as err:
                if err.error_code in ["554", "572"]:
                    self.logger(level="error", message="User " + self.username +
                                                       " reached maximum session limit while trying to connect to "
                                                       + self.metadata.device_type_long + ": " + self.target)
                elif err.error_code == "ERR-xml-parse-error":
                    self.logger(level="error", message="Error while trying to connect to " +
                                                       self.metadata.device_type_long + ": " +
                                                       self.target + ": " + str(err))
                elif err.error_code == "551":
                    self.logger(level="error", message="Authentication failed while trying to connect to " +
                                                       self.metadata.device_type_long + ": " + self.target)
                elif err.error_code == "2001":
                    self.logger(level="error", message="XML API Service is disabled on device " +
                                                       self.metadata.device_type_long + ": " + self.target)
                elif err.error_code == "ERR-secondary-node":
                    self.logger(level="error", message="UCSM is not available on secondary node of " +
                                                       self.metadata.device_type_long + ": " + self.target)
                else:
                    self.logger(level="error", message="Unknown error while trying to connect " +
                                                       self.metadata.device_type_long + ": " + self.target + ": " +
                                                       str(err))
                continue
            except UcscException as err:
                if err.error_code in ["547"]:
                    self.logger(level="error", message="Authentication failed while trying to connect to " +
                                                       self.metadata.device_type_long + ": " + self.target)
                elif err.error_code in ["ERR-xml-parse-error"]:
                    self.logger(level="error", message="Error while trying to connect to " +
                                                       self.metadata.device_type_long + ": " +
                                                       self.target + ": " + str(err))
                else:
                    self.logger(level="error", message="Unknown error while trying to connect " +
                                                       self.metadata.device_type_long + ": " + self.target + ": " +
                                                       str(err))
                continue
            except Exception as err:
                self.logger(level="error", message="Error while trying to connect to " +
                                                   self.metadata.device_type_long + ": " + self.target + ": " +
                                                   str(err), set_api_error_message=False)
                continue
        self.metadata.is_reachable = False
        if self.task is not None and task_name is not None:
            self.task.taskstep_manager.stop_taskstep(
                name=task_name, status="failed",
                status_message="Error while connecting to " + self.metadata.device_type_long + " device " +
                               str(self.name))
        return False

    def disconnect(self):
        """
        Disconnects from the device
        :return: True if disconnection is successful, False otherwise
        """
        task_name = None
        if self.metadata.device_type == "cimc":
            task_name = "DisconnectUcsImcDevice"
        elif self.metadata.device_type == "ucsc":
            task_name = "DisconnectUcsCentralDevice"
        elif self.metadata.device_type == "ucsm":
            task_name = "DisconnectUcsSystemDevice"

        if self.task is not None and task_name is not None:
            self.task.taskstep_manager.start_taskstep(
                name=task_name,
                description="Disconnecting from " + self.metadata.device_type_long + " device " + str(self.name))
        self.logger(message="Disconnecting from " + self.metadata.device_type_long + ": " + str(self.name))
        try:
            self.handle.logout()
        except Exception:
            self.logger(level="error",
                        message="Could not disconnect from " + self.metadata.device_type_long + ": " + str(self.name))
            if self.task is not None and task_name is not None:
                self.task.taskstep_manager.stop_taskstep(
                    name=task_name, status="failed",
                    status_message="Error while disconnecting from " + self.metadata.device_type_long + " device " +
                                   str(self.name))
            return False

        if self.task is not None and task_name is not None:
            self.task.taskstep_manager.stop_taskstep(
                name=task_name, status="successful",
                status_message="Successfully disconnected from " + self.metadata.device_type_long + " device " +
                               str(self.name))
        return True

    def is_connected(self):
        """
        Checks if the handle is still connected
        :return: True if connected, False otherwise
        """

        try:
            if self.handle:
                if self.__class__.__name__ == "UcsSystem":
                    if self.handle.is_valid():
                        return True
                    else:
                        return False
                elif self.__class__.__name__ in ["UcsImc", "UcsCentral"]:
                    try:
                        self.handle.query_dn("sys")
                        return True
                    except Exception:
                        return False
            else:
                self.logger(level="error",
                            message="No handle detected. Impossible to check if the handle is still connected")
                return False
        except Exception as err:
            self.logger(level="debug", message="Error while trying to check if still connected: " + str(err))
            return False

    def _set_device_name_and_version(self):
        pass


class UcsSystem(GenericUcsDevice):
    UCS_SYSTEM_MIN_REQUIRED_VERSION = "3.1(3a)"

    def __init__(self, parent=None, uuid=None, target="", user="", password="", is_hidden=False, is_system=False,
                 system_usage=None, logger_handle_log_level="info", log_file_path=None, bypass_connection_checks=False,
                 bypass_version_checks=False, user_label=""):
        GenericUcsDevice.__init__(self, parent=parent, uuid=uuid, target=target, password=password, user=user,
                                  is_hidden=is_hidden, is_system=is_system, system_usage=system_usage,
                                  logger_handle_log_level=logger_handle_log_level, log_file_path=log_file_path,
                                  bypass_connection_checks=bypass_connection_checks,
                                  bypass_version_checks=bypass_version_checks, user_label=user_label)
        self.fi_a_model = ""
        self.fi_b_model = ""
        self.handle = UcsHandle(ip=target, username=user, password=password)
        self.handle.set_mode_threading()
        self.sys_mode = ""
        self.version_max_supported_by_sdk = UcsVersion(ucsmsdk_ucs_version())
        self.version_min_required = UcsVersion(self.UCS_SYSTEM_MIN_REQUIRED_VERSION)
        self.version_sdk = str(ucsmsdk_sdk_version)
        self.backup_manager = UcsSystemBackupManager(parent=self)
        self.config_manager = UcsSystemConfigManager(parent=self)
        self.inventory_manager = UcsSystemInventoryManager(parent=self)
        self.report_manager = UcsSystemReportManager(parent=self)
        self.timeout = 120
        self._set_device_name_and_version()

        self.metadata.device_type = "ucsm"
        self.metadata.device_type_long = "UCS System"

    def initial_setup(self, fi_ip_list=[], config=None):
        """
        Performs initial setup of UCS System
        :param fi_ip_list: List of DHCP IP addresses taken by the Fabric Interconnect(s) after boot stage
        :param config: Config of device to be used for initial setup (for Hostname/IP/DNS/Domain Name)
        :return: True if initial setup is successful, False otherwise
        """

        if config is None:
            return False
        if not fi_ip_list:
            return False

        self.set_task_progression(25)

        fi_a_dhcp_ip_address = ""
        fi_b_dhcp_ip_address = ""
        fi_a_target_ip_address = ""
        fi_b_target_ip_address = ""
        target_netmask = ""
        target_gateway = ""
        target_sysname = ""
        target_vip = ""
        target_domain_name = ""
        target_admin_password = ""
        target_dns1 = ""

        self.logger(message="Performing initial setup of UCS System")

        # Getting management interfaces configuration parameters
        if not config.management_interfaces:
            self.logger(level="error", message="Could not find management interfaces parameters in config")
            return False

        if len(fi_ip_list) == 1:
            # We are doing an initial setup in standalone mode
            fi_a_dhcp_ip_address = fi_ip_list[0]
            if not common.is_ip_address_valid(fi_a_dhcp_ip_address):
                self.logger(level="error",
                            message=fi_a_dhcp_ip_address + " is not a valid DHCP IP address for Fabric Interconnect A")
                return False

            # Going through all entries in management_interfaces to find the right one
            for management_interface in config.management_interfaces:
                if management_interface.fabric.upper() == 'A':
                    if management_interface.ip:
                        fi_a_target_ip_address = management_interface.ip
                        self.logger(message="Using IP address for Fabric A: " + fi_a_target_ip_address)
                    else:
                        # IP address of FI A is a mandatory input - Exiting
                        self.logger(level="error", message="Could not find Management IP address of FI A in config")
                        return False

                    if management_interface.netmask:
                        target_netmask = management_interface.netmask
                        self.logger(message="Using netmask for Fabric A: " + target_netmask)
                    else:
                        # Netmask of FI A is a mandatory input - Exiting
                        self.logger(level="error", message="Could not find netmask of FI A in config")
                        return False

                    if management_interface.gateway:
                        target_gateway = management_interface.gateway
                        self.logger(message="Using gateway for Fabric A: " + target_gateway)
                    else:
                        # Default gateway of FI A is not a mandatory input - Displaying warning message
                        self.logger(
                            level="warning",
                            message="Could not find gateway of FI A in config! Proceeding without default gateway")

            # We went through all entries in management_interfaces - making sure we got the information we needed
            if not fi_a_target_ip_address or not target_netmask:
                self.logger(level="error", message="Could not find IP address and netmask for FI A in config")
                return False

            # Generates warning in case no default gateway has been set
            if not target_gateway:
                self.logger(level="warning",
                            message="Could not find gateway of FI A in config! Proceeding without default gateway")

        elif len(fi_ip_list) == 2:
            # We are doing an initial setup in cluster mode
            fi_a_dhcp_ip_address = fi_ip_list[0]
            fi_b_dhcp_ip_address = fi_ip_list[1]

            if not common.is_ip_address_valid(fi_a_dhcp_ip_address):
                self.logger(level="error",
                            message=fi_a_dhcp_ip_address + " is not a valid DHCP IP address for Fabric Interconnect A")
                return False
            if not common.is_ip_address_valid(fi_b_dhcp_ip_address):
                self.logger(level="error",
                            message=fi_b_dhcp_ip_address + " is not a valid DHCP IP address for Fabric Interconnect B")
                return False

            # Going through all entries in management_interfaces to find the right one
            for management_interface in config.management_interfaces:
                if management_interface.fabric.upper() == 'A':
                    if management_interface.ip:
                        fi_a_target_ip_address = management_interface.ip
                        self.logger(message="Using IP address for FI A: " + fi_a_target_ip_address)
                    else:
                        # IP address of FI A is a mandatory input - Exiting
                        self.logger(level="error", message="Could not find Management IP address of FI A in config")
                        return False

                    if management_interface.netmask:
                        target_netmask = management_interface.netmask
                        self.logger(message="Using netmask for Cluster: " + target_netmask)

                    if management_interface.gateway:
                        target_gateway = management_interface.gateway
                        self.logger(message="Using gateway for Cluster: " + target_gateway)

                if management_interface.fabric.upper() == 'B':
                    if management_interface.ip:
                        fi_b_target_ip_address = management_interface.ip
                        self.logger(message="Using IP address for FI B: " + fi_b_target_ip_address)
                    else:
                        # IP address of FI B is a mandatory input - Exiting
                        self.logger(level="error", message="Could not find Management IP address of FI B in config")
                        return False

                    if management_interface.netmask:
                        # Using netmask of FI A if already found
                        if not target_netmask:
                            target_netmask = management_interface.netmask
                            self.logger(message="Using netmask for Cluster: " + target_netmask)

                    if management_interface.gateway:
                        # Using gateway of FI A if already found
                        if not target_gateway:
                            target_gateway = management_interface.gateway
                            self.logger(message="Using gateway for Cluster: " + target_gateway)

            # We went through all entries in management_interfaces - making sure we got the information we needed
            if not fi_a_target_ip_address or not fi_b_target_ip_address or not target_netmask:
                self.logger(level="error", message="Could not find IP addresses and netmask for FI A and B in config")
                return False

            # Generates warning in case no default gateway has been set
            if not target_gateway:
                self.logger(level="warning",
                            message="Could not find gateway of FI A or B in config! Proceeding without default gateway")

        # Getting system configuration parameters
        if len(config.system) != 1:
            self.logger(level="error", message="Could not find system parameters in config")
            return False

        # Fetching system name
        if config.system[0].name:
            target_sysname = config.system[0].name
            self.logger(message="Using System Name: " + target_sysname)
        else:
            # sysname is a mandatory input - Exiting
            self.logger(level="error", message="Could not find system name in config")
            return False

        # Fetching VIP or FI A IP Address (for stand-alone):
        # FIXME: We only support IPv4 for now
        if fi_b_dhcp_ip_address:
            if config.system[0].virtual_ip:
                target_vip = config.system[0].virtual_ip
                self.logger(message="Using IP address for Cluster: " + target_vip)
            else:
                self.logger(level="error", message="Could not find system virtual_ip in config")
                return False
        elif fi_a_dhcp_ip_address:
            self.logger(message="Using IP address of FI A for UCS Manager: " + fi_a_target_ip_address)

        # Fetching Domain Name
        if config.system[0].domain_name:
            target_domain_name = config.system[0].domain_name
            self.logger(message="Using Domain name: " + target_domain_name)
        else:
            # Domain name is not a mandatory input - Generates warning
            self.logger(level="warning", message="Could not find system domain_name in config")

        # Getting admin password
        if not config.local_users:
            # Could not find local_users in config - Admin password is a mandatory parameter - Exiting
            self.logger(level="error", message="Could not find users in config")
            return False

        # Going through all users to find admin
        for user in config.local_users:
            if user.id:
                if user.id == "admin":
                    if user.password:
                        target_admin_password = user.password
                        self.logger(message="Using password for admin user: " + target_admin_password)
                    else:
                        # Admin password is a mandatory input - Exiting
                        self.logger(level="error", message="Could not find password for user id admin in config")
                        return False

        # We went through all users - Making sure we got the information we needed
        if not target_admin_password:
            self.logger(level="error", message="Could not find user id admin in config")
            return False

        # Getting DNS config
        if not config.dns:
            self.logger(level="warning", message="Could not find DNS parameters in config")

        # We only support setting a single DNS server
        if common.is_ip_address_valid(config.dns[0]):
            target_dns1 = config.dns[0]
            self.logger(message="Using DNS server: " + target_dns1)
        else:
            self.logger(level="warning", message="DNS server " + config.dns[0] + " is not a valid IP address!")

        # FIXME: Handle empty optional inputs

        # if cluster mode
        if fi_a_target_ip_address and fi_b_target_ip_address:
            payload_fi_a = {'hidden_init': 'hidden_init',
                            'cluster': '1',
                            'ooblocalFIIP1': '',
                            'ooblocalFIIP2': '',
                            'ooblocalFIIP3': '',
                            'ooblocalFIIP4': '',
                            'ooblocalFIIPv6': '',
                            'switchFabric': '1',
                            'ipformat': '1',
                            'virtualIP1': target_vip.split(".")[0],
                            'virtualIP2': target_vip.split(".")[1],
                            'virtualIP3': target_vip.split(".")[2],
                            'virtualIP4': target_vip.split(".")[3],
                            'yes_or_no_passwd': '2',
                            'systemName': target_sysname,
                            'adminPasswd': target_admin_password,
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
                            'dns1': target_dns1.split(".")[0],
                            'dns2': target_dns1.split(".")[1],
                            'dns3': target_dns1.split(".")[2],
                            'dns4': target_dns1.split(".")[3],
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
                                   'cluster': '1',
                                   'switchFabric': '2',
                                   'adminPasswd': target_admin_password}

            payload_fi_b_step_2 = {'hidden_init': 'hidden_init',
                                   'oobIP1': fi_b_target_ip_address.split(".")[0],
                                   'oobIP2': fi_b_target_ip_address.split(".")[1],
                                   'oobIP3': fi_b_target_ip_address.split(".")[2],
                                   'oobIP4': fi_b_target_ip_address.split(".")[3],
                                   'oobIPv6': ''}

            url_fi_a = "https://" + fi_a_dhcp_ip_address + "/cgi-bin/initial_setup_new.cgi"
            url_fi_b_step_1 = "https://" + fi_b_dhcp_ip_address + "/cgi-bin/initial_setup_clusteradd.cgi"
            url_fi_b_step_2 = "https://" + fi_b_dhcp_ip_address + "/cgi-bin/initial_setup_oob.cgi"

            # Disable requests warnings about HTTPS
            requests.packages.urllib3.disable_warnings()

            # Checking status of FIs before sending initial configuration
            self.logger(message="Checking if both Fabric Interconnects are ready for initial setup...")
            for fi_ip in fi_ip_list:
                if not common.check_web_page(device=self, url="https://" + fi_ip, str_match="Express Setup",
                                             timeout=30):
                    self.logger(level="error",
                                message="Fabric Interconnect " + fi_ip + " is not ready for initial setup")
                    return False

            # Send configuration to FI A
            if not self.post_requests(request_url=url_fi_a, request_payload=payload_fi_a,
                                      error_message="send initial configuration to FI A"):
                return False
            self.logger(message="Sent initial configuration to FI A")
            self.set_task_progression(30)

            # Wait until FI A has processed configuration - needed for FI B to recognize that its peer is configured
            self.logger(message="Waiting up to 180 seconds for FI A configuration to be processed")
            if not common.check_web_page(self, "https://" + fi_a_target_ip_address, "Cisco", 180):
                self.logger(level="error", message="Impossible to reconnect to FI A after the initial configuration")
                return False

            # Send password of FI A to FI B - Step 1
            if not self.post_requests(request_url=url_fi_b_step_1, request_payload=payload_fi_b_step_1,
                                      error_message="send initial configuration to FI B - Step 1"):
                return False

            # Send local IP address to FI B - Step 2
            if not self.post_requests(request_url=url_fi_b_step_2, request_payload=payload_fi_b_step_2,
                                      error_message="send initial configuration to FI B - Step 2"):
                return False
            self.logger(message="Sent initial configuration to FI B")

        # if stand-alone mode
        else:
            payload_fi_a = {'hidden_init': 'hidden_init',
                            'cluster': '2',
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
                            'dns1': target_dns1.split(".")[0],
                            'dns2': target_dns1.split(".")[1],
                            'dns3': target_dns1.split(".")[2],
                            'dns4': target_dns1.split(".")[3],
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

            url_fi_a = "https://" + fi_a_dhcp_ip_address + "/cgi-bin/initial_setup_new.cgi"

            # Disable requests warnings about HTTPS
            requests.packages.urllib3.disable_warnings()

            # Checking status of FI A before sending initial configuration
            self.logger(message="Checking if the Fabric Interconnect is ready for initial setup...")
            for fi_ip in fi_ip_list:
                if not common.check_web_page(device=self, url="https://" + fi_ip, str_match="Express Setup",
                                             timeout=30):
                    self.logger(level="error",
                                message="Fabric Interconnect " + fi_ip + " is not ready for initial setup")
                    return False

            # Send configuration to FI A
            if not self.post_requests(url_fi_a, payload_fi_a,
                                      error_message="send initial configuration to FI"):
                return False
            self.logger(message="Sent initial configuration to FI")
            self.set_task_progression(30)

        self.set_task_progression(35)
        return True

    def reset(self, bypass_version_checks=False, reset_device_connector=False, clear_sel_logs=False,
              decommission_rack_servers=False, erase_flexflash=False, erase_virtual_drives=False,
              unregister_from_central=True):
        """
        Erases all configuration from the UCS System
        :param bypass_version_checks: Whether the minimum version checks should be bypassed when connecting
        :param reset_device_connector: Whether the Device Connector should be reset if claimed
        :param clear_sel_logs: Whether SEL Logs should be cleared before reset
        :param decommission_rack_servers: Whether rack servers should be decommissioned before reset
        :param erase_flexflash: Whether FlexFlash should be formatted before reset
        :param erase_virtual_drives: Whether existing virtual drives should be erased from servers before reset
        :param unregister_from_central: Whether to unregister UCS Manager from UCS Central
        :return: True if reset is successful, False otherwise
        """

        self.set_task_progression(5)
        # First, make sure we are connected to the device
        if not self.connect(bypass_version_checks=bypass_version_checks):
            self.logger(level="error", message="Unable to connect to UCS System")
            return False

        if reset_device_connector and self.metadata.device_connector_claim_status == "claimed":
            # If the UCSM device is claimed to Intersight, unclaim the device
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

        if decommission_rack_servers:
            # Decommissioning Rack servers
            if not self.decommission_all_rack_servers():
                self.logger(level="error", message=f"Error while performing decommission of rack servers in "
                                                   f"{self.metadata.device_type_long} device {self.name}")
                return False
        else:
            if self.task is not None:
                self.task.taskstep_manager.skip_taskstep(
                    name="DecommissionAllRackServers",
                    status_message=f"Skipping the decommissioning of rack servers in {self.metadata.device_type_long} "
                                   f"device {self.name}"
                )

        if erase_flexflash:
            self.erase_flexflash()

        if erase_virtual_drives:
            self.erase_virtual_drives()

        if clear_sel_logs:
            self.clear_sel_logs()

        if self.task is not None:
            self.task.taskstep_manager.start_taskstep(
                name="EraseFiConfigurations",
                description=f"Resetting Fabric Interconnects of {self.metadata.device_type_long} device {self.name}")

        # Verifying that SSH Service is enabled before trying to connect
        self.logger(level="debug", message="Verifying that SSH service is enabled on UCS System")
        try:
            ssh = self.handle.query_dn("sys/svc-ext/ssh-svc")
            ssh_admin_state = ssh.admin_state

        except Exception as err:
            message_str = "Unable to get SSH service state"
            self.logger(level="error", message=message_str + ": " + str(err))
            if self.task is not None:
                self.task.taskstep_manager.stop_taskstep(
                    name="EraseFiConfigurations", status="failed", status_message=message_str)
            return False

        try:
            if ssh_admin_state != "enabled":
                self.logger(level="warning", message="SSH service is disabled on UCS System! Enabling it before reset.")

                mo_ssh = ucsmsdk_CommSsh(parent_mo_or_dn="sys/svc-ext", admin_state="enabled")
                self.handle.set_mo(mo_ssh)
                self.handle.commit()
                self.logger(level="debug", message="SSH service is enabled on UCS System")
                time.sleep(5)

        except Exception as err:
            message_str = "Unable to set SSH service admin state to 'enabled'"
            self.logger(level="error", message=message_str + ": " + str(err))
            if self.task is not None:
                self.task.taskstep_manager.stop_taskstep(
                    name="EraseFiConfigurations", status="failed", status_message=message_str)
            return False

        if unregister_from_central:
            # Check if device is registered with UCS Central, in which case, gently remove it from Central
            self.logger(level="debug", message="Verifying UCS Central Registration state on UCS System")
            try:
                ucs_central_registration_state = ""
                ucs_central_reg_name = ""
                ucs_central = self.handle.query_dn("sys/control-ep-policy")
                if ucs_central:
                    ucs_central_registration_state = ucs_central.registration_state
                    ucs_central_reg_name = ucs_central.svc_reg_name

            except Exception as err:
                message_str = "Unable to get UCS Central Registration state"
                self.logger(level="error", message=message_str + ": " + str(err))
                if self.task is not None:
                    self.task.taskstep_manager.stop_taskstep(
                        name="EraseFiConfigurations", status="failed", status_message=message_str)
                return False

            try:
                if ucs_central_registration_state == "registered":
                    self.logger(level="warning",
                                message="UCS System is registered with UCS Central " + ucs_central_reg_name +
                                        "! Unregistering it before reset.")
                    self.handle.remove_mo(ucs_central)
                    self.handle.commit()
                    time.sleep(5)
                    # Waiting for UCSM to be ready after unregistering with UCS Central
                    self.wait_for_reboot_after_reset(fi_ip_list=[self.target])
                    # Try to connect again after beeing disconnected due to unregistering with UCS Central
                    if not self.connect(bypass_version_checks=bypass_version_checks):
                        message_str = "Unable to connect to UCS System"
                        self.logger(level="error", message=message_str)
                        if self.task is not None:
                            self.task.taskstep_manager.stop_taskstep(
                                name="EraseFiConfigurations", status="failed", status_message=message_str)
                        return False

            except Exception as err:
                message_str = "Unable to unregister UCS System from UCS Central " + ucs_central_reg_name
                self.logger(level="error", message=message_str + ": " + str(err))
                if self.task is not None:
                    self.task.taskstep_manager.stop_taskstep(
                        name="EraseFiConfigurations", status="failed", status_message=message_str)
                return False

        ip_sw_addr = []

        if self.sys_mode == "cluster":
            self.logger(level="debug", message="Trying to get Fabric Interconnects IP addresses")
        else:
            self.logger(level="debug", message="Trying to get Fabric Interconnect IP address")

        try:
            # Get IP address of FI A
            # We use self.query() instead of handle.query_dn() to support retries. In some rare cases, if UCS System is
            # unregistered from Central, reconnection might not work properly right away (API does not respond)
            switch_a = self.query(mode="dn", target="sys/switch-A")
            ip_a = switch_a.oob_if_ip
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
            if self.sys_mode == "cluster":
                switch_b = self.query(mode="dn", target="sys/switch-B")
                ip_b = switch_b.oob_if_ip
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

                self.logger(level="debug", message="\tConnecting to local-mgmt")
                channel.send('connect local-mgmt\n')

                buff = ""
                while not buff.endswith("(local-mgmt)# "):
                    resp = channel.recv(9999)
                    buff += resp.decode("utf-8")
                buff = ""

                self.logger(level="debug", message="\tSending 'erase configuration'")
                channel.send('erase configuration\n')
                while not buff.endswith("(yes/no):"):
                    resp = channel.recv(9999)
                    buff += resp.decode("utf-8")

                self.logger(level="debug", message="\tSending confirmation")
                channel.send('yes\n')
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

    def regenerate_certificate(self):
        """
        Regenerates default keyring certificate. The default lifespan is one year.
        :return: True if successful, False otherwise
        """
        from cryptography import x509
        from cryptography.hazmat.backends import default_backend

        if not self.is_connected():
            self.connect()
        try:
            if self.task is not None:
                self.task.taskstep_manager.start_taskstep(
                    name="RegenerateDefaultKeyringCertificate",
                    description=f"Regenerating Default Keyring Certificate of {self.metadata.device_type_long} " +
                                f"device {self.name}")

            self.logger(level="info", message="Regenerating Default Keyring Certificate")

            mo_keyring = self.handle.query_dn("sys/pki-ext/keyring-default")
            mo_keyring.regen = "true"

            cert = x509.load_pem_x509_certificate(mo_keyring.cert.encode(), default_backend())

            self.logger(level="info", message="Current certificate valid until " + str(cert.not_valid_after_utc))

            self.handle.add_mo(mo=mo_keyring, modify_present=True)
            self.handle.commit()
            self.logger(level="info", message="Default Keyring Certificate Regenerated")

            if self.task is not None:
                self.task.taskstep_manager.stop_taskstep(
                    name="RegenerateDefaultKeyringCertificate", status="successful",
                    status_message=f"Successfully regenerated Default Keyring Certificate of " +
                                   f"{self.metadata.device_type_long} device {self.name}")

            self.disconnect()

            if self.task is not None:
                self.task.taskstep_manager.start_taskstep(
                    name="WaitForCertificateLoad",
                    description=f"Waiting up to 30 seconds for the new certificate to be loaded on " +
                                f"{self.metadata.device_type_long} device {self.name}")
            self.logger(level="info", message="Waiting up to 60 seconds for the new certificate to be loaded")
            time.sleep(20)
            if not common.check_web_page(device=self, url="https://" + self.target, str_match="Cisco", timeout=40):
                error_msg = "Impossible to reconnect after Regenerating Default Keyring Certificate"
                self.logger(level="error", message=error_msg)
                if self.task is not None:
                    self.task.taskstep_manager.stop_taskstep(
                        name="WaitForCertificateLoad", status="failed", status_message=error_msg)
                return False

            if self.task is not None:
                self.task.taskstep_manager.stop_taskstep(
                    name="WaitForCertificateLoad", status="successful",
                    status_message=f"Successfully loaded new certificate of " +
                                   f"{self.metadata.device_type_long} device {self.name}")

            self.connect()

            if self.task is not None:
                self.task.taskstep_manager.start_taskstep(
                    name="CheckNewCertificateValidity",
                    description=f"Checking validity of the new certificate loaded on " +
                                f"{self.metadata.device_type_long} device {self.name}")
            mo_keyring = self.handle.query_dn("sys/pki-ext/keyring-default")
            cert = x509.load_pem_x509_certificate(mo_keyring.cert.encode(), default_backend())
            self.logger(level="info", message="New certificate valid until " + str(cert.not_valid_after_utc))
            if self.task is not None:
                self.task.taskstep_manager.stop_taskstep(
                    name="CheckNewCertificateValidity", status="successful",
                    status_message=f"New certificate valid until " + str(cert.not_valid_after_utc) + " on " +
                                   f"{self.metadata.device_type_long} device {self.name}")

            return True

        except UcsException as err:
            error_msg = "Error while Regenerating Default Keyring Certificate: " + err.error_descr
            self.logger(level="error", message=error_msg)
            if self.task is not None:
                self.task.taskstep_manager.stop_taskstep(
                    name="RegenerateDefaultKeyringCertificate", status="failed", status_message=error_msg)
            return False
        except urllib.error.URLError:
            error_msg = "Timeout Error while Regenerating Default Keyring Certificate"
            self.logger(level="error", message=error_msg)
            if self.task is not None:
                self.task.taskstep_manager.stop_taskstep(
                    name="RegenerateDefaultKeyringCertificate", status="failed", status_message=error_msg)
            return False
        except Exception as err:
            error_msg = "Error while Regenerating Default Keyring Certificate: " + str(err)
            self.logger(level="error", message=error_msg)
            if self.task is not None:
                self.task.taskstep_manager.stop_taskstep(
                    name="RegenerateDefaultKeyringCertificate", status="failed", status_message=error_msg)
            return False

    def is_certificate_expired(self):
        """
        Checks if default keyring certificate is expired.
        :return: True if expired, False otherwise
        """
        from cryptography import x509
        from cryptography.hazmat.backends import default_backend

        if not self.is_connected():
            self.connect()
        try:
            mo_keyring = self.handle.query_dn("sys/pki-ext/keyring-default")
            cert = x509.load_pem_x509_certificate(mo_keyring.cert.encode(), default_backend())
            mo_fault = self.handle.query_dn("sys/pki-ext/keyring-default/fault-F0909")

            if not mo_fault:
                self.logger(
                    message="The default keyring certificate is still valid until " + str(cert.not_valid_after))
                return False

            if mo_fault.severity == "cleared":
                self.logger(
                    message="The default keyring certificate is still valid until " + str(cert.not_valid_after))
                return False

            self.logger(message="The default keyring certificate is expired since " + str(cert.not_valid_after))

            return True

        except UcsException as err:
            self.logger(level="error",
                        message="Error while checking expiration of Default Keyring Certificate" + err.error_descr)
            return False
        except urllib.error.URLError:
            self.logger(level="error",
                        message="Error while checking expiration of Default Keyring Certificate: Timeout error")
            return False
        except Exception as err:
            self.logger(level="error",
                        message="Error while checking expiration of Default Keyring Certificate: " + str(err))
            return False

    def clear_user_sessions(self, check_ssh=False):
        """
        Clear all user sessions
        :param check_ssh: Check with the live system if SSH is enabled. False by default because the system might be
        crowded with sessions, and it might be impossible to check
        :return: True if is successful, False otherwise
        """

        if check_ssh:
            # Verifying that SSH Service is enabled before trying to connect with Paramiko
            if not self.is_connected():
                self.connect()
            self.logger(level="debug", message="Verifying that SSH service is enabled on UCS")
            try:
                ssh = self.handle.query_dn("sys/svc-ext/ssh-svc")
                ssh_admin_state = ssh.admin_state

            except Exception:
                self.logger(level="error", message="Unable to get SSH service state on UCS")
                return False

            try:
                if ssh_admin_state != "enabled":
                    self.logger(level="warning", message="SSH service is disabled on UCS. Enabling it")

                    mo_ssh = ucsmsdk_CommSsh(parent_mo_or_dn="sys/svc-ext", admin_state="enabled")
                    self.handle.set_mo(mo_ssh)
                    self.handle.commit()
                    self.logger(level="debug", message="SSH service is enabled on UCS")
                    time.sleep(5)

            except Exception:
                self.logger(level="error", message="Unable to set SSH service admin state to 'enabled'")
                return False

        # Establishing connection to UCS
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(self.handle.ip, port=22, username=self.username, password=self.password, banner_timeout=30)

        except paramiko.AuthenticationException:
            self.logger(level="error", message="Authentication failed when connecting to UCS System " + self.handle.ip)
            return False

        except paramiko.ssh_exception.NoValidConnectionsError as err:
            self.logger(level="error",
                        message="Error while connecting to UCS System " + self.handle.ip + ": " + err.strerror)
            return False

        except TypeError as err:
            self.logger(level="debug",
                        message="Error while connecting to UCS System " + self.handle.ip + ": " + str(err))
            self.logger(level="error",
                        message="Error while connecting to UCS System " + self.handle.ip + ". Please try again.")
            return False

        # Clearing all user sessions of UCS System
        try:
            self.logger(message="Clearing all user sessions")
            channel = client.invoke_shell()
            channel.settimeout(20)

            self.logger(level="debug", message="\tSending 'scope security'")
            channel.send('scope security\n')

            buff = ""
            while not buff.endswith("security # "):
                resp = channel.recv(9999)
                buff += resp.decode("utf-8")
            buff = ""

            self.logger(level="debug", message="\tSending 'clear-user-sessions all'")
            channel.send('clear-user-sessions all\n')
            while not buff.endswith("yes/no):"):
                resp = channel.recv(9999)
                buff += resp.decode("utf-8")

            self.logger(level="debug", message="\tSending confirmation")
            channel.send('yes\n')
            self.logger(message="All user sessions cleared")
            time.sleep(5)

        except paramiko.ChannelException as err:
            self.logger(level="error",
                        message="Communication failed with UCS System " + self.handle.ip + ": " + str(err))
            return False

        except (paramiko.buffered_pipe.PipeTimeout, socket.timeout):
            self.logger(level="error", message="Timeout while communicating with UCS System " + self.handle.ip)
            return False

        return True

    def decommission_all_rack_servers(self):
        """
        Decommissions all rack servers connected to the UCS System.
        This is a necessary operation before converting a UCSM domain to Intersight Managed Mode (IMM)
        :return: True if successful, False otherwise
        """
        from ucsmsdk.mometa.compute.ComputeRackUnit import ComputeRackUnit

        if self.task is not None:
            self.task.taskstep_manager.start_taskstep(
                name="DecommissionAllRackServers", description=f"Decommissioning all rack servers in "
                                                               f"{self.metadata.device_type_long} device "
                                                               f"{self.name}")

        if not self.is_connected():
            self.connect()
        self.logger(level="info", message="Decommissioning all discovered Rack Servers")
        all_rack_servers = self.handle.query_classid("computeRackUnit")
        error_msg = None
        for rack_server in all_rack_servers:
            try:
                self.logger(level="debug", message="Decommissioning server " + rack_server.id +
                                                   " with serial " + rack_server.serial)
                mo_rack_server = ComputeRackUnit(parent_mo_or_dn="sys", id=rack_server.id, lc="decommission")
                self.handle.add_mo(mo=mo_rack_server, modify_present=True)
                self.handle.commit()

            except UcsException as err:
                error_msg = "Error while decommissioning server " + rack_server.id
                self.logger(level="error", message=error_msg + ": " + err.error_descr)
            except urllib.error.URLError:
                error_msg = "Timeout Error while decommissioning server " + rack_server.id
                self.logger(level="error", message=error_msg)
            except Exception as err:
                error_msg = "Error while decommissioning server " + rack_server.id
                self.logger(level="error", message=error_msg + ": " + str(err))

            if error_msg:
                if self.task is not None:
                    self.task.taskstep_manager.stop_taskstep(
                        name="DecommissionAllRackServers", status="failed", status_message=error_msg)
                return False

        if self.task is not None:
            self.task.taskstep_manager.stop_taskstep(
                name="DecommissionAllRackServers", status="successful",
                status_message=f"Successfully decommissioned all rack servers in {self.metadata.device_type_long} "
                               f"device {self.name}")
        return True

    def erase_virtual_drives(self):
        """
        Erases all virtual drives (removes all LUNs) from all servers in the UCS System.
        :return: True if successful, False otherwise
        """
        from ucsmsdk.mometa.storage.StorageVirtualDrive import StorageVirtualDrive

        if not self.is_connected():
            self.connect()
        self.logger(level="info", message="Erasing all Virtual Drives of all discovered servers")
        all_virtual_drives = self.handle.query_classid("storageVirtualDrive")
        for virtual_drive in all_virtual_drives:
            if "PCH" in virtual_drive.dn:
                self.logger(level="warning",
                            message="LUN on PCH controller will not be deleted. (" + virtual_drive.dn + ")")
            else:
                try:
                    self.logger(level="debug", message="Erasing Virtual Drive: " + virtual_drive.dn)
                    mo_virtual_drive = \
                        StorageVirtualDrive(parent_mo_or_dn='/'.join(virtual_drive.dn.split('/')[:-1]),
                                            id=virtual_drive.id, admin_action_trigger="triggered",
                                            admin_state="delete")
                    self.handle.add_mo(mo=mo_virtual_drive, modify_present=True)
                    self.handle.commit()

                except UcsException as err:
                    self.logger(level="error",
                                message="Error while deleting LUN " + virtual_drive.dn + ": " + err.error_descr)
                    return False
                except urllib.error.URLError:
                    self.logger(level="error",
                                message="Timeout Error while while deleting LUN " + virtual_drive.dn)
                    return False
                except Exception as err:
                    self.logger(level="error", message="Error while deleting LUN " + virtual_drive.dn + ": " + str(err))
                    return False
        return True

    def erase_flexflash(self):
        """
        Performs a format operation on all FlexFlash controllers from all servers in the UCS System
        :return: True if successful, False otherwise
        """
        from ucsmsdk.mometa.storage.StorageFlexFlashController import StorageFlexFlashController

        if not self.is_connected():
            self.connect()
        self.logger(level="info", message="Formatting all FlexFlash cards of all discovered servers")
        all_flex_flash_controller = self.handle.query_classid("storageFlexFlashController")
        for flex_flash_controller in all_flex_flash_controller:
            if int(flex_flash_controller.physical_drive_count) > 0:
                try:
                    self.logger(level="debug", message="Formatting SD card(s) of controller " +
                                                       flex_flash_controller.dn)
                    mo_flex_flash = \
                        StorageFlexFlashController(
                            parent_mo_or_dn='/'.join(flex_flash_controller.dn.split('/')[:-1]),
                            operation_request="format", id=flex_flash_controller.id)
                    self.handle.add_mo(mo=mo_flex_flash, modify_present=True)
                    self.handle.commit()
                except UcsException as err:
                    self.logger(level="error", message="Error while formatting SD Card(s) of controller " +
                                                       flex_flash_controller.dn + " : " + err.error_descr)
                except urllib.error.URLError:
                    self.logger(level="error", message="Timeout Error while formatting SD Card(s) of controller " +
                                                       flex_flash_controller.dn)
                except Exception as err:
                    self.logger(level="error", message="Error while formatting SD Card(s) of controller " +
                                                       flex_flash_controller.dn + ": " + str(err))
        return True

    def clear_sel_logs(self):
        """
        Clears SEL Logs from all servers in the UCS System
        :return: True if successful, False otherwise
        """
        from ucsmsdk.mometa.sysdebug.SysdebugMEpLog import SysdebugMEpLog

        if not self.is_connected():
            self.connect()

        if self.task is not None:
            self.task.taskstep_manager.start_taskstep(
                name="ClearSelLogsUcsSystem", description="Clearing all System Event Logs of all discovered servers")

        self.logger(level="info", message="Clearing all System Event Logs of all discovered servers")
        all_logs = self.handle.query_classid("sysdebugMEpLog")
        return_code = True
        for log in all_logs:
            try:
                self.logger(level="debug", message="Clearing SEL Log: " + log.dn)
                mo_sel_log = SysdebugMEpLog(parent_mo_or_dn='/'.join(log.dn.split('/')[:-1]),
                                            admin_state="clear", id="0", type="SEL")
                self.handle.add_mo(mo=mo_sel_log, modify_present=True)
                self.handle.commit()
            except UcsException as err:
                self.logger(level="error",
                            message="Error while clearing SEL Logs in " + log.dn + " : " + err.error_descr)
                return_code = False
            except urllib.error.URLError:
                self.logger(level="error",
                            message="Timeout Error while clearing SEL Logs in " + log.dn)
                return_code = False
            except Exception as err:
                self.logger(level="error", message="Error while clearing SEL Logs in " + log.dn + ": " + str(err))
                return_code = False

        if return_code:
            self.logger(level="info", message="Successfully cleared all System Event Logs of all discovered servers")
            if self.task is not None:
                self.task.taskstep_manager.stop_taskstep(
                    name="ClearSelLogsUcsSystem", status="successful",
                    status_message=f"Successfully cleared all System Event Logs of all discovered servers")
        else:
            if self.task is not None:
                self.task.taskstep_manager.stop_taskstep(
                    name="ClearSelLogsUcsSystem", status="failed",
                    status_message=f"Failed to clear all System Event Logs of all discovered servers")

        return return_code

    def set_drives_status(self, status=None):
        # TODO : Not used until all status conditions and behaviour are decided
        """
        Set all the drives to the status specified.
        If jbod specified: all the unconfigured-good drives will be set to jbod
        If unconfigured-good specified: all the jbod drives will be set to unconfigured-good
        :param status: jbod or unconfigured-good
        :return: True, False otherwise
        """
        from ucsmsdk.mometa.storage.StorageLocalDisk import StorageLocalDisk

        if status:
            all_storage_drives = self.query(target="storageLocalDisk", mode="classid")
            for storage_drive in all_storage_drives:
                if status == "jbod":
                    # We search for unconfigured-good drives
                    if storage_drive.disk_state == "unconfigured-good":
                        self.logger(level="debug", message="Setting status jbod on physical drive: " + storage_drive.dn)
                        try:
                            mo_local_disk = StorageLocalDisk(
                                parent_mo_or_dn="/".join(storage_drive.dn.split("/")[0:-1]),
                                admin_action="jbod",
                                admin_action_trigger="triggered", id=storage_drive.id)
                            self.handle.add_mo(mo=mo_local_disk, modify_present=True)
                            self.handle.commit()
                        except UcsException as err:
                            self.logger(level="error",
                                        message="Error in setting new status " + status + " to physical drive " +
                                                storage_drive.dn + " : " + err.error_descr)
                elif status == "unconfigured-good":
                    # We search for jbod drives
                    if storage_drive.disk_state == "jbod":
                        self.logger(level="debug",
                                    message="Setting status unconfigured-good on physical drive: " + storage_drive.dn)
                        try:
                            mo_local_disk = StorageLocalDisk(
                                parent_mo_or_dn="/".join(storage_drive.dn.split("/")[0:-1]),
                                admin_action="unconfigured-good",
                                admin_action_trigger="triggered", id=storage_drive.id)
                            self.handle.add_mo(mo=mo_local_disk, modify_present=True)
                            self.handle.commit()
                        except UcsException as err:
                            self.logger(level="error",
                                        message="Error in setting new status " + status + " to physical drive " +
                                                storage_drive.dn + " : " + err.error_descr)
                else:
                    self.logger(level="error", message="Status requested does not exist " + status)
                    return False
        else:
            self.logger(level="error", message="No status requested!")
            return False
        return True

    def query(self, mode="", target=None, filter_str=None, retries=3):
        """
        Uses the query of the handle and add a retry function
        :param mode: "dn" or "classid"
        :param target:
        :param filter_str:
        :param retries:
        :return:
        """

        if not mode:
            self.logger(level="error", message="A mode of query must be filled")
            return []
        if not target:
            self.logger(level="error", message="A target of query must be filled")
            return []
        if mode not in ["classid", "dn"]:
            self.logger(level="error", message="The mode query must be 'classid' or 'dn'")
            return []
        for i in range(retries):
            if i:
                self.logger(level="warning", message="Retrying to fetch " + target + " (attempt " + str(i + 1) + ")")
            try:
                if not self.is_connected():
                    self.connect()
                if mode == "classid":
                    classid_list = self.handle.query_classid(target, filter_str=filter_str)
                    return classid_list
                elif mode == "dn":
                    dn_list = self.handle.query_dn(target)
                    return dn_list
            except ConnectionRefusedError as err:
                self.logger(level="debug", message="Error while querying UCS System: " + str(err))
            except UcsException as err:
                self.logger(level="debug", message="Unable to fetch " + target + ": " + err.error_descr)
            except urllib.error.URLError:
                self.logger(level="debug", message="Timeout error while fetching " + target)
            time.sleep(self.push_interval_after_fail)

        self.logger(level="error", message="Unable to fetch " + target + " after " + str(retries) + " attempts")
        return []

    def post_requests(self, request_url=None, request_payload=None, retries=3, error_message=""):
        """
        Performs an HTTP POST (using Requests) of the specified payload to the specified URL, with a retry mechanism
        :param request_url: ex. "https://10.0.0.1/cgi-bin/initial_setup_new.cgi"
        :param request_payload:
        :param retries: Number of retries
        :param error_message: ex. "send initial configuration to FI B"
        :return:
        """

        for i in range(retries):
            if i:
                self.logger(level="warning", message="Retrying to do a request to " + error_message)
            try:
                req = requests.post(request_url, request_payload, verify=False)
                return req
            except (ConnectionRefusedError, ValueError, requests.exceptions.ChunkedEncodingError) as err:
                self.logger(level="debug",
                            message="Failed to " + error_message + " : " + str(err))
            except Exception as err:
                self.logger(level="debug",
                            message="Failed to " + error_message + " : " + str(err))
            time.sleep(self.push_interval_after_fail)

        self.logger(level="error", message="Unable to " + error_message + " after " + str(retries) + " attempts")
        return False

    def upload_file(self, directory=None, filename=None):
        """
        Uploads a file to UCSM. Used in combination with threading so that EasyUCS can time out the upload operation
        :param directory: Directory in which the file is located
        :param filename: Name of file to be uploaded
        :return: True if upload operation has finished, False otherwise
        """
        if not directory or not filename:
            return False

        uri_suffix = "operations/file-%s/image.txt" % filename
        if not self.is_connected():
            self.connect()
        self.handle.file_upload(url_suffix=uri_suffix, file_dir=directory, file_name=filename)

        self.logger(level="debug", message="Finished uploading file")
        return True

    def upload_local_firmware_image(self, image_directory=None, image_name=None, timeout=900):
        """
        Uploads the local firmware image to UCSM
        :param image_directory:
        :param image_name:
        :param timeout:
        :return: True if upload is successful, False otherwise
        """
        if not image_directory or not image_name:
            return False

        image_file_path = os.path.join(image_directory, image_name)

        if not os.path.exists(image_file_path):
            self.logger(level="error", message="File " + str(image_file_path) + " does not exist!")
            return False

        firmware_downloader = FirmwareDownloader(parent_mo_or_dn="sys/fw-catalogue", file_name=image_name,
                                                 server="local", protocol="local", admin_state="restart")

        if not self.is_connected():
            self.connect()

        self.logger(message="Starting upload of firmware image " + str(image_file_path))

        self.logger(level="debug", message="Starting new thread for firmware image upload")
        upload = threading.Thread(target=self.upload_file, args=(image_directory, image_name))
        upload.start()

        self.logger(message="Waiting up to " + str(timeout) +
                            " seconds for the firmware image to be uploaded to the UCS System")
        start = time.time()
        while (time.time() - start) < timeout:
            if not upload.is_alive():
                self.logger(level="debug", message="Thread for firmware image upload is finished")
                break
            self.logger(level="debug",
                        message="Waiting for upload operation on thread " + str(upload.getName()) + " to finish...")
            time.sleep(20)

        if upload.is_alive():
            self.logger(level="debug", message="Timeout exceeded. Killing thread " + str(upload.getName()) + "...")
            upload.stop()

        self.handle.add_mo(firmware_downloader, modify_present=True)
        self.handle.commit()

        timeout = 180
        self.logger(message="Waiting up to " + str(timeout) +
                            " seconds for the firmware upload operation to finish...")
        start = time.time()
        while (time.time() - start) < timeout:
            try:
                firmware_downloader = self.handle.query_dn(firmware_downloader.dn)
                if firmware_downloader.transfer_state == "downloaded":
                    self.logger(message="Successfully uploaded firmware image " + str(image_file_path))
                    return True
                elif firmware_downloader.transfer_state == "failed":
                    self.logger(level="error", message="Failed to upload firmware image " + str(image_file_path))
                    return False
            except UcsException as err:
                self.logger(level="error", message="Failed to fetch status of firmware upload operation")

            self.logger(level="debug", message="Waiting for the firmware upload operation to finish...")
            time.sleep(20)

    def wait_for_fsm_complete(self, ucs_sdk_object_class=None, timeout=300):
        """
        Waits for UCS FSM state of given UCS SDK Object class to reach 100%
        :param ucs_sdk_object_class: UCS SDK FSM object with fsmProgr attribute
        :param timeout: time in seconds above which the wait will be considered failed
        :return: True when FSM has reached 100%, False if timeout exceeded or error
        """
        if ucs_sdk_object_class is None:
            return False

        start = time.time()
        while (time.time() - start) < timeout:
            result = []
            try:
                ucs_sdk_object_list = self.handle.query_classid(ucs_sdk_object_class)
            except UcsException as err:
                if err.error_descr == "Authorization required":
                    # After a change of switching mode the user is disconnected (in stand-alone mode)
                    self.logger(level="debug", message="Authorization required detected. Reconnecting")
                    self.connect(force=True, auto_refresh=True)
                    continue
                else:
                    self.logger(level="error", message="Unable to get the FSM progress of " + ucs_sdk_object_class +
                                                       ": " + err.error_descr)
                    return False
            except http.client.RemoteDisconnected:
                # After a change of switching mode the user is disconnected (in stand-alone mode)
                self.logger(level="debug", message="Remote Disconnected. Reconnecting")
                self.connect(force=True, auto_refresh=True)
                continue

            for obj in ucs_sdk_object_list:
                if obj.fsm_progr == "100":
                    result.append(obj)

            if len(result) == len(ucs_sdk_object_list):
                self.logger(level="debug",
                            message="All objects of class " + ucs_sdk_object_class + " have an FSM progress at 100%")
                return True
            self.logger(level="debug", message="Re-checking FSM progress of " + ucs_sdk_object_class)
            time.sleep(20)

        return False

    def wait_for_fsm_status(self, ucs_sdk_object_dn=None, status="", timeout=300, attribute="fsm_status"):
        """
        Waits for UCS FSM status of given UCS SDK Object to reach given status
        :param ucs_sdk_object_dn: DN of UCS SDK object with fsmStatus attribute
        :param status: string with exact status to watch for
        :param timeout: time in seconds above which the wait will be considered failed
        :param attribute: the attribute to track
        :return: True when FSM has reached given status, False if timeout exceeded or error
        """
        if ucs_sdk_object_dn is None:
            return False
        if status == "":
            return False

        start = time.time()
        while (time.time() - start) < timeout:
            try:
                ucs_sdk_object = self.handle.query_dn(ucs_sdk_object_dn)
            except UcsException as err:
                if err.error_descr == "Authorization required":
                    # After a change of switching mode the user is disconnected (in stand-alone mode)
                    self.logger(level="debug", message="Authorization required detected. Reconnecting")
                    self.connect(force=True, auto_refresh=True)
                    continue
                else:
                    self.logger(level="error",
                                message="Unable to fetch object with DN " + ucs_sdk_object_dn + ": " + err.error_descr)
                    return False
            except http.client.RemoteDisconnected:
                # After a change of switching mode the user is disconnected (in stand-alone mode)
                self.logger(level="debug", message="Remote Disconnected. Reconnecting")
                self.connect(force=True, auto_refresh=True)
                continue
            except urllib.error.URLError as err:
                self.logger(level="error", message="Failed to connect to UCS System: " + str(err))
                return False

            if not ucs_sdk_object:
                self.logger(level="error", message="Unable to fetch object with DN " + ucs_sdk_object_dn)
                return False

            if hasattr(ucs_sdk_object, attribute):
                if getattr(ucs_sdk_object, attribute) == status:
                    self.logger(level="debug",
                                message="Object with DN " + ucs_sdk_object_dn + " has an FSM state with status "
                                        + status)
                    return True
            else:
                self.logger(level="error",
                            message="Object with DN " + ucs_sdk_object_dn + " does not have an FSM status")
                return False

            self.logger(level="debug", message="Re-checking FSM state of object with DN " + ucs_sdk_object_dn)
            time.sleep(20)

        return False

    def wait_for_ha_cluster_ready(self, timeout=300):
        """
        Waits for UCS HA Cluster to be in ready state.
        In case the UCS Cluster does not have any chassis/rack server connected, waits for both FIs management state to
        be UP and in sync
        :param timeout: time in seconds above which the wait will be considered failed
        :return: True when cluster is in ready state, False if timeout exceeded
        """
        # We only do this if we are in cluster mode
        if self.sys_mode == "cluster":
            start = time.time()
            while (time.time() - start) < timeout:
                try:
                    mgmt_entity_list = self.handle.query_classid("mgmtEntity")
                except UcsException as err:
                    self.logger(level="error",
                                message="Unable to get the list of mgmtEntity objects: " + err.error_descr)
                    return False

                for mgmt_entity in mgmt_entity_list:
                    if mgmt_entity.ha_ready == "yes":
                        self.logger(level="debug", message="HA cluster is in ready state")
                        return True
                    elif mgmt_entity.ha_failure_reason == "chassisConfigIncomplete":
                        if mgmt_entity.state == "up" and mgmt_entity.mgmt_services_state == "up" \
                                and mgmt_entity.umbilical_state == "full":
                            self.logger(level="debug",
                                        message="HA cluster is not ready but both FIs are in UP state and in sync")
                            return True
                self.logger(level="debug", message="Re-checking HA cluster state...")
                time.sleep(20)
        return False

    def wait_for_standalone_fi_ready(self, timeout=300):
        """
        Right after initial setup, Fabric Interconnect mode is configured to be primary for Ethernet and FC.
        This method waits for UCS Stand-Alone FI to be in ready state
        :param timeout: time in seconds above which the wait will be considered failed
        :return: True when FI is in ready state, False if timeout exceeded
        """
        # We only do this if we are in stand-alone mode
        if self.sys_mode == "stand-alone":
            try:
                fabric_lan_cloud_mo = self.handle.query_dn("fabric/lan")
                fabric_san_cloud_mo = self.handle.query_dn("fabric/san")
            except UcsException as err:
                self.logger(level="error",
                            message="Unable to fetch fabricLanCloud and fabricSanCloud objects: " + err.error_descr)
                return False

            mo_list = [fabric_lan_cloud_mo, fabric_san_cloud_mo]
            for mo in mo_list:
                if mo.fsm_status == "SwitchModeSwConfigLocal":
                    self.logger(
                        message="Please wait for Fabric Interconnect Switching Mode to be configured Primary")
                    if not self.wait_for_fsm_complete(ucs_sdk_object_class=mo.__class__.__name__, timeout=timeout):
                        self.logger(level="error",
                                    message="Timeout exceeded while waiting for FSM state of switching mode " +
                                            "to reach Primary")
                        return False
            return True
        return False

    def wait_for_reboot_after_reset(self, timeout=480, fi_ip_list=[]):
        """
        Waits for Fabric Interconnect(s) to reboot after a complete reset
        :param timeout: time in seconds above which the wait will be considered failed
        :param fi_ip_list: list of DHCP IP addresses taken by each FI after the reset
        :return: True when Fabric Interconnect(s) has(have) rebooted, False if timeout exceeded
        """
        if not fi_ip_list:
            self.logger(level="error", message="No DHCP IP addresses given")
            return False

        # If cluster
        if len(fi_ip_list) == 2:
            self.logger(level="info", message="Waiting for both FIs to come back after reset")
            if not common.check_web_page(self, "https://" + fi_ip_list[0], "Cisco", timeout):
                self.logger(level="error",
                            message="Impossible to reconnect to FI " + fi_ip_list[0] + " after the reset")
                return False
            if not common.check_web_page(self, "https://" + fi_ip_list[1], "Cisco", timeout):
                self.logger(level="error",
                            message="Impossible to reconnect to FI " + fi_ip_list[1] + " after the reset")
                return False

        # If only one FI
        elif len(fi_ip_list) == 1:
            self.logger(level="info", message="Waiting for FI to come back after reset")
            if not common.check_web_page(self, "https://" + fi_ip_list[0], "Cisco", timeout):
                self.logger(level="error",
                            message="Impossible to reconnect to FI " + fi_ip_list[0] + " after the reset")
                return False

        return True

    def _set_device_name_and_version(self):
        """
        Sets the device name and version attributes of the device. Also sets the FI model attributes
        :return: nothing
        """
        if self.handle.session_id:  # We first make sure we have already connected at least once to avoid timeout
            if self.handle.is_valid():  # We then make sure the session is still valid
                try:
                    self.sys_mode = self.handle.query_classid("topSystem")[0].mode
                    self.fi_a_model = self.handle.query_classid(class_id="networkElement",
                                                                filter_str="(dn,'sys/switch-A')")[0].model
                    if self.sys_mode != "stand-alone":
                        self.fi_b_model = self.handle.query_classid(class_id="networkElement",
                                                                    filter_str="(dn,'sys/switch-B')")[0].model
                except UcsException as err:
                    self.logger(level="error", message="Unable to get the FI system mode & model: " + err.error_descr)

                # Trying to fetch Intersight claim status
                # TODO add more efficient way to get device connector info
                try:
                    cloud_device_connector = self.handle.query_classid("cloudDeviceConnectorEp")
                    if cloud_device_connector:
                        self.intersight_status = cloud_device_connector[0].claim_state
                        if self.intersight_status == "none":
                            self.intersight_status = "unknown"
                except UcsException as err:
                    if hasattr(err, "error_descr"):
                        if err.error_descr == 'XML PARSING ERROR: no class named cloudDeviceConnectorEp':
                            self.logger(level="debug",
                                        message="No class named cloudDeviceConnectorEp on this version of UCS Manager")
                    self.logger(level="debug", message="Unable to determine Intersight claim status through UCSM API")

        self.name = self.handle.ucs
        self.version = self.handle.version
        self.metadata.device_name = self.name
        if hasattr(self.version, "version"):
            self.metadata.device_version = self.version.version

        # Handling the case of versions unknown to the SDK
        if hasattr(self.version, "version"):
            if not hasattr(self.version, "major"):
                # Trying to determine the version we're running
                major = ""
                regex_major = r"(^\d+)\."
                res_major = re.search(regex_major, self.version.version)
                if res_major is not None:
                    major = res_major.group(1)

                minor = ""
                regex_minor = r"\.(\d+)\("
                res_minor = re.search(regex_minor, self.version.version)
                if res_minor is not None:
                    minor = res_minor.group(1)

                mr = ""
                regex_mr = r"\((\d).*"
                res_mr = re.search(regex_mr, self.version.version)
                if res_mr is not None:
                    mr = res_mr.group(1)

                version = major + "." + minor + "(" + mr + "a)"
                self.logger(level="warning", message="Running unknown version " + self.version.version +
                                                     ". Using version " + version + " as version number instead.")
                self.version = UcsVersion(version)


class UcsImc(GenericUcsDevice):
    UCS_IMC_MIN_REQUIRED_VERSION = "3.0(1c)"

    def __init__(self, parent=None, uuid=None, target="", user="", password="", is_hidden=False, is_system=False,
                 system_usage=None, logger_handle_log_level="info", log_file_path=None, bypass_connection_checks=False,
                 bypass_version_checks=False, user_label=""):
        GenericUcsDevice.__init__(self, parent=parent, uuid=uuid, target=target, user=user, password=password,
                                  is_hidden=is_hidden, is_system=is_system, system_usage=system_usage,
                                  logger_handle_log_level=logger_handle_log_level, log_file_path=log_file_path,
                                  bypass_connection_checks=bypass_connection_checks,
                                  bypass_version_checks=bypass_version_checks, user_label=user_label)
        self.handle = ImcHandle(ip=target, username=user, password=password)
        self.platform_type = ""
        self.version_min_required = ImcVersion(self.UCS_IMC_MIN_REQUIRED_VERSION)
        self.version_sdk = str(imcsdk_sdk_version)
        self.backup_manager = UcsImcBackupManager(parent=self)
        self.config_manager = UcsImcConfigManager(parent=self)
        self.inventory_manager = UcsImcInventoryManager(parent=self)
        self.report_manager = UcsImcReportManager(parent=self)
        self._set_device_name_and_version()
        self._set_sdk_version()
        self.model = self.handle.model

        self.metadata.device_type = "cimc"
        self.metadata.device_type_long = "UCS IMC"

    def initial_setup(self, imc_ip=None, config=None, bypass_version_checks=False):
        """
        Performs initial setup of UCS IMC
        :param imc_ip: DHCP IP address taken by the CIMC after boot stage
        :param config: Config of device to be used for initial setup (for Hostname/IP/DNS/Domain Name)
        :param bypass_version_checks: Whether the minimum version checks should be bypassed when connecting
        :return: True if initial setup is successful, False otherwise
        """

        if config is None:
            return False
        if imc_ip is None:
            return False

        self.set_task_progression(25)

        imc_dhcp_ip_address = ""
        imc_target_ip_address = ""
        target_netmask = ""
        target_gateway = ""
        target_sysname = ""
        target_admin_password = ""
        target_dns_preferred = ""

        self.logger(message="Performing initial setup of UCS IMC")

        # Getting management interfaces configuration parameters
        if not config.admin_networking:
            self.logger(level="error", message="Could not find admin networking parameters in config")
            return False

        if imc_ip:
            # We are doing an initial setup
            imc_dhcp_ip_address = imc_ip
            if not common.is_ip_address_valid(imc_dhcp_ip_address):
                self.logger(level="error",
                            message=imc_dhcp_ip_address + " is not a valid DHCP IP address for UCS IMC")
                return False

            if config.admin_networking[0].management_ipv4_address:
                imc_target_ip_address = config.admin_networking[0].management_ipv4_address
                self.logger(message="Using IP address for UCS IMC: " + imc_target_ip_address)
            else:
                # IP address of UCS IMC is a mandatory input - Exiting
                self.logger(level="error", message="Could not find Management IP address of UCS IMC in config")
                return False

            if config.admin_networking[0].management_subnet_mask:
                target_netmask = config.admin_networking[0].management_subnet_mask
                self.logger(message="Using netmask for UCS IMC: " + target_netmask)
            else:
                # Netmask of UCS IMC is a mandatory input - Exiting
                self.logger(level="error", message="Could not find netmask of UCS IMC in config")
                return False

            if config.admin_networking[0].gateway_ipv4:
                target_gateway = config.admin_networking[0].gateway_ipv4
                self.logger(message="Using gateway for UCS IMC: " + target_gateway)
            else:
                # Default gateway of UCS IMC is not a mandatory input - Displaying warning message
                self.logger(
                    level="warning",
                    message="Could not find gateway of UCS IMC in config! Proceeding without default gateway")

            # We went through all entries in management_interfaces - making sure we got the information we needed
            if not imc_target_ip_address or not target_netmask:
                self.logger(level="error", message="Could not find IP address and netmask for UCS IMC in config")
                return False

        # Fetching system name
        if config.admin_networking[0].management_hostname:
            target_sysname = config.admin_networking[0].management_hostname
            self.logger(message="Using System Name: " + target_sysname)
        else:
            # sysname is a mandatory input - Exiting
            self.logger(level="error", message="Could not find management hostname in config")
            return False

        # Getting admin password
        if not config.local_users:
            # Could not find local_users in config - Admin password is a mandatory parameter - Exiting
            self.logger(level="error", message="Could not find users in config")
            return False

        # Going through all users to find admin
        for user in config.local_users:
            if user.username:
                if user.username == "admin":
                    if user.password:
                        target_admin_password = user.password
                        self.logger(message="Using password for admin user: " + target_admin_password)
                    else:
                        # Admin password is a mandatory input - Exiting
                        self.logger(level="error", message="Could not find password for user id admin in config")
                        return False

        # We went through all users - Making sure we got the information we needed
        if not target_admin_password:
            self.logger(level="error", message="Could not find user id admin in config")
            return False

        # Getting DNS config
        if config.admin_networking[0].dns_preferred_ipv4:
            target_dns_preferred = config.admin_networking[0].dns_preferred_ipv4
            self.logger(message="Using DNS for UCS IMC: " + target_dns_preferred)
        else:
            self.logger(level="warning", message="Could not find DNS parameters in config")

        self.logger(level="debug", message="Pushing initial configuration : new management IP and password")
        self.target = imc_dhcp_ip_address
        self.password = "password"
        self.username = "admin"

        # We need to refresh the UCS device handle so that it has the right attributes
        self.handle = ImcHandle(self.target, self.username, self.password)

        # Changing handle to the new one
        config.refresh_config_handle()

        is_pushed = True
        if self.connect(bypass_version_checks=bypass_version_checks):
            # Setting the handle with the DHCP IP Address
            config.refresh_config_handle()
            # Pushing objects / Changing handle
            if config.local_users_properties:
                is_pushed = config.local_users_properties[0].push_object() and is_pushed
            for local_user in config.local_users:
                is_pushed = local_user.push_object() and is_pushed
            if config.admin_networking:
                is_pushed = config.admin_networking[0].push_object() and is_pushed
            self.set_task_progression(35)
            return is_pushed
        else:
            return False

    def reset(self, erase_virtual_drives=False, erase_flexflash=False, clear_sel_logs=False, set_drives_status=None,
              bypass_version_checks=False, reset_device_connector=False):
        """
        Erases all configuration from the UCS IMC
        :param erase_virtual_drives: Whether existing virtual drives should be erased from server before reset
        :param erase_flexflash: Whether FlexFlash should be formatted before reset
        :param clear_sel_logs: Whether SEL Log should be cleared before reset
        :param set_drives_status: The status to which the drives should be set before reset
        :param bypass_version_checks: Whether the minimum version checks should be bypassed when connecting
        :param reset_device_connector: Whether the Device Connector should be reset if claimed
        :return: True if reset is successful, False otherwise
        """

        self.set_task_progression(5)
        # First, make sure we are connected to the device
        if not self.connect(bypass_version_checks=bypass_version_checks):
            self.logger(level="error", message="Unable to connect to UCS IMC")
            return False

        if reset_device_connector and self.metadata.device_connector_claim_status == "claimed":
            # If the UCS IMC device is claimed to Intersight unclaim the device
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

        if erase_flexflash:
            self.erase_flexflash()

        if erase_virtual_drives:
            self.erase_virtual_drives()

        if clear_sel_logs:
            self.clear_sel_logs()

        if set_drives_status:
            self.set_drives_status(status=set_drives_status)

        if self.task is not None:
            self.task.taskstep_manager.start_taskstep(
                name="EraseConfiguration",
                description=f"Resetting Fabric Interconnects of {self.metadata.device_type_long} device {self.name}")

        # Verifying that SSH Service is enabled before trying to connect
        self.logger(level="debug", message="Verifying that SSH service is enabled on UCS IMC")
        try:
            ssh = self.handle.query_dn("sys/svc-ext/ssh-svc")
            ssh_admin_state = ssh.admin_state

        except Exception as err:
            message_str = "Unable to get SSH service state on UCS IMC"
            self.logger(level="error", message=message_str + ": " + str(err))
            if self.task is not None:
                self.task.taskstep_manager.stop_taskstep(
                    name="EraseConfiguration", status="failed", status_message=message_str)
            return False

        try:
            if ssh_admin_state != "enabled":
                self.logger(level="warning", message="SSH service is disabled on UCS IMC! Enabling it")

                mo_ssh = imcsdk_CommSsh(parent_mo_or_dn="sys/svc-ext", admin_state="enabled")
                self.handle.set_mo(mo_ssh)
                self.logger(level="debug", message="SSH service is enabled on UCS IMC")
                time.sleep(5)

        except Exception as err:
            message_str = "Unable to set SSH service admin state to 'enabled'"
            self.logger(level="error", message=message_str + ": " + str(err))
            if self.task is not None:
                self.task.taskstep_manager.stop_taskstep(
                    name="EraseConfiguration", status="failed", status_message=message_str)
            return False

        # Verifying that server is powered on (necessary for performing factory default operation)
        self.logger(level="debug",
                    message="Verifying that server is powered on (necessary for performing factory default operation)")
        try:
            from imcsdk.mometa.compute.ComputeRackUnit import ComputeRackUnit
            rack = self.handle.query_dn("sys/rack-unit-1")
            if rack:
                if rack.oper_power == "off":
                    self.logger(message="Powering on server to perform reset operation")
                    mo = ComputeRackUnit(server_id="1", parent_mo_or_dn="sys", admin_power="up")
                    self.handle.set_mo(mo=mo)
            else:
                message_str = "Unable to get server power state via UCS IMC"
                self.logger(level="error", message=message_str)
                if self.task is not None:
                    self.task.taskstep_manager.stop_taskstep(
                        name="EraseConfiguration", status="failed", status_message=message_str)
                return False

        except Exception as err:
            message_str = "Unable to get server power state via UCS IMC"
            self.logger(level="error", message=message_str + ": " + str(err))
            if self.task is not None:
                self.task.taskstep_manager.stop_taskstep(
                    name="EraseConfiguration", status="failed", status_message=message_str)
            return False

        self.logger(level="debug", message="Trying to get the UCS IMC IP")
        try:
            # Get IP address of UCS IMC
            switch = self.handle.query_dn("sys/rack-unit-1/mgmt/if-1")
            ip = switch.ext_ip
            self.logger(level="debug", message="IP address of UCS IMC: " + ip)

        except Exception as err:
            message_str = "Cannot get IP address of UCS IMC"
            self.logger(level="error", message=message_str + ": " + str(err))
            if self.task is not None:
                self.task.taskstep_manager.stop_taskstep(
                    name="EraseConfiguration", status="failed", status_message=message_str)
            return False

        self.logger(message="Resetting IMC with IP address: " + ip)

        # Establishing connection to UCS IMC
        try:
            error_msg = None
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(ip, port=22, username=self.username, password=self.password, banner_timeout=30)

        except paramiko.AuthenticationException:
            error_msg = "Authentication failed when connecting to UCS IMC " + ip
            self.logger(level="error", message=error_msg)

        except TypeError as err:
            error_msg = "Error while connecting to Fabric Interconnect " + ip
            self.logger(level="debug", message=error_msg + ": " + str(err))
            self.logger(level="error", message=error_msg + ". Please try again.")

        except Exception as err:
            error_msg = "Error while connecting to UCS IMC " + ip
            self.logger(level="error", message=error_msg + ": " + str(err))

        if error_msg:
            if self.task is not None:
                self.task.taskstep_manager.stop_taskstep(
                    name="EraseConfiguration", status="failed", status_message=error_msg)
            return False

        # Erasing configuration of IMC
        try:
            error_msg = None
            channel = client.invoke_shell()
            channel.settimeout(20)

            self.logger(level="debug", message="\tSending 'scope chassis'")
            channel.send('scope chassis\n')

            buff = ""
            while not buff.endswith("chassis # "):
                resp = channel.recv(9999)
                buff += resp.decode("utf-8")
            buff = ""

            self.logger(level="debug", message="\tSending 'factory-default all'")
            channel.send('factory-default bmc vic\n')
            while not buff.endswith("[y|N]"):
                resp = channel.recv(9999)
                buff += resp.decode("utf-8")

            self.logger(level="debug", message="\tSending confirmation")
            channel.send('y\n')
            time.sleep(5)
            self.set_task_progression(10)

        except paramiko.ChannelException as err:
            error_msg = "Communication failed with UCS IMC " + ip + ": " + str(err)
            self.logger(level="error", message=error_msg)

        except (paramiko.buffered_pipe.PipeTimeout, socket.timeout):
            error_msg = "Timeout while communicating with UCS IMC " + ip
            self.logger(level="error", message=error_msg)

        except Exception as err:
            error_msg = "Error while erasing the configuration of UCS IMC " + ip
            self.logger(level="error", message=error_msg + str(err))

        if error_msg:
            if self.task is not None:
                self.task.taskstep_manager.stop_taskstep(
                    name="EraseConfiguration", status="failed", status_message=error_msg)
            return False

        if self.task is not None:
            self.task.taskstep_manager.stop_taskstep(
                name="EraseConfiguration", status="successful", status_message=error_msg)
        return True

    def regenerate_certificate(self):
        """
        Regenerates self-signed certificate. The default lifespan is 3 years.
        :return: True if successful, False otherwise
        """
        from imcsdk.mometa.generate.GenerateCertificateSigningRequest import GenerateCertificateSigningRequest

        country_codes = {
            "Albania": "AL",
            "Algeria": "DZ",
            "American Samoa": "AS",
            "Andorra": "AD",
            "Angola": "AO",
            "Anguilla": "AI",
            "Antarctica": "AQ",
            "Antigua and Barbuda": "AG",
            "Argentina": "AR",
            "Armenia": "AM",
            "Aruba": "AW",
            "Australia": "AU",
            "Austria": "AT",
            "Azerbaijan": "AZ",
            "Bahamas": "BS",
            "Bahrain": "BH",
            "Bangladesh": "BD",
            "Barbados": "BB",
            "Belarus": "BY",
            "Belgium": "BE",
            "Belize": "BZ",
            "Benin": "BJ",
            "Bermuda": "BM",
            "Bhutan": "BT",
            "Bolivia": "BO",
            "Bosnia and Herzegovina": "BA",
            "Botswana": "BW",
            "Bouvet Island": "BV",
            "Brazil": "BR",
            "British Indian Ocean Territory": "IO",
            "Brunei Darussalam": "BN",
            "Bulgaria": "BG",
            "Burkina Faso": "BF",
            "Burundi": "BI",
            "Cambodia": "KH",
            "Cameroon": "CM",
            "Canada": "CA",
            "Cape Verde": "CV",
            "Cayman Islands": "KY",
            "Central African Republic": "CF",
            "Chad": "TD",
            "Chile": "CL",
            "China": "CN",
            "Christmas Island": "CX",
            "Cocos (Keeling) Islands": "CC",
            "Colombia": "CO",
            "Comoros": "KM",
            "Congo": "CD",
            "Cook Islands": "CK",
            "Costa Rica": "CR",
            "Cote D'Ivoire (Ivory Coast)": "CI",
            "Croatia (Hrvatska)": "HR",
            "Cuba": "CU",
            "Cyprus": "CY",
            "Czech Republic": "CZ",
            "Czechoslovakia": "CZ",
            "Denmark": "DK",
            "Djibouti": "DJ",
            "Dominica": "DM",
            "Dominican Republic": "DO",
            "East Timor": "TL",
            "Ecuador": "EC",
            "Egypt": "EG",
            "El Salvador": "SV",
            "Equatorial Guinea": "GQ",
            "Eritrea": "ER",
            "Estonia": "EE",
            "Ethiopia": "ET",
            "Falkland Islands (Malvinas)": "FK",
            "Faroe Islands": "FO",
            "Fiji": "FJ",
            "Finland": "FI",
            "France": "FR",
            "France, Metropolitan": "FX",
            "French Guiana": "GF",
            "French Polynesia": "PF",
            "French Southern Territories": "TF",
            "Gabon": "GA",
            "Gambia": "GM",
            "Georgia": "GE",
            "Germany": "DE",
            "Ghana": "GH",
            "Gibraltar": "GI",
            "Great Britain (UK)": "UK",
            "Greece": "GR",
            "Greenland": "GL",
            "Grenada": "GD",
            "Guadeloupe": "GP",
            "Guam": "GU",
            "Guatemala": "GT",
            "Guinea": "GN",
            "Guinea-Bissau": "GW",
            "Guyana": "GY",
            "Haiti": "HT",
            "Heard and McDonald Islands": "HM",
            "Honduras": "HN",
            "Hong Kong": "HK",
            "Hungary": "HU",
            "Iceland": "IS",
            "India": "IN",
            "Indonesia": "ID",
            "Iran": "IR",
            "Iraq": "IQ",
            "Ireland": "IE",
            "Israel": "IL",
            "Italy": "IT",
            "Jamaica": "JM",
            "Japan": "JP",
            "Jordan": "JO",
            "Kazakhstan": "KZ",
            "Kenya": "KE",
            "Kiribati": "KI",
            "Korea (North)": "KP",
            "Korea (South)": "KR",
            "Kuwait": "KW",
            "Kyrgyzstan": "KG",
            "Laos": "LA",
            "Latvia": "LV",
            "Lebanon": "LB",
            "Lesotho": "LS",
            "Liberia": "LR",
            "Libya": "LY",
            "Liechtenstein": "LI",
            "Lithuania": "LT",
            "Luxembourg": "LU",
            "Macau": "MO",
            "Macedonia": "MK",
            "Madagascar": "MG",
            "Malawi": "MW",
            "Malaysia": "MY",
            "Maldives": "MV",
            "Mali": "ML",
            "Malta": "MT",
            "Marshall Islands": "MH",
            "Martinique": "MQ",
            "Mauritania": "MR",
            "Mauritius": "MU",
            "Mayotte": "YT",
            "Mexico": "MX",
            "Micronesia": "FM",
            "Moldova": "MD",
            "Monaco": "MC",
            "Mongolia": "MN",
            "Montserrat": "MS",
            "Morocco": "MA",
            "Mozambique": "MZ",
            "Myanmar": "MM",
            "Namibia": "NA",
            "Nauru": "NR",
            "Nepal": "NP",
            "Netherlands": "NL",
            "Netherlands Antilles": "AN",
            "Neutral Zone": "NT",
            "New Caledonia": "NC",
            "New Zealand (Aotearoa)": "NZ",
            "Nicaragua": "NI",
            "Niger": "NE",
            "Nigeria": "NG",
            "Niue": "NU",
            "Norfolk Island": "NF",
            "Northern Mariana Islands": "MP",
            "Norway": "NO",
            "Oman": "OM",
            "Pakistan": "PK",
            "Palau": "PW",
            "Panama": "PA",
            "Papua New Guinea": "PG",
            "Paraguay": "PY",
            "Peru": "PE",
            "Philippines": "PH",
            "Pitcairn": "PN",
            "Poland": "PL",
            "Portugal": "PT",
            "Puerto Rico": "PR",
            "Qatar": "QA",
            "Reunion": "RE",
            "Romania": "RO",
            "Russian Federation": "RU",
            "Rwanda": "RW",
            "S. Georgia and S. Sandwich Isls.": "GS",
            "Saint Kitts and Nevis": "KN",
            "Saint Lucia": "LC",
            "Saint Vincent and the Grenadines": "VC",
            "Samoa": "WS",
            "San Marino": "SM",
            "Sao Tome and Principe": "ST",
            "Saudi Arabia": "SA",
            "Senegal": "SN",
            "Seychelles": "SC",
            "Sierra Leone": "SL",
            "Singapore": "SG",
            "Slovak Republic": "SK",
            "Slovenia": "SI",
            "Solomon Islands": "SB",
            "Somalia": "SO",
            "South Africa": "ZA",
            "Spain": "ES",
            "Sri Lanka": "LK",
            "St. Helena": "SH",
            "St. Pierre and Miquelon": "PM",
            "Sudan": "SD",
            "Suriname": "SR",
            "Svalbard and Jan Mayen Islands": "SJ",
            "Swaziland": "SZ",
            "Sweden": "SE",
            "Switzerland": "CH",
            "Syria": "SY",
            "Taiwan": "TW",
            "Tajikistan": "TJ",
            "Tanzania": "TZ",
            "Thailand": "TH",
            "Togo": "TG",
            "Tokelau": "TK",
            "Tonga": "TO",
            "Trinidad and Tobago": "TT",
            "Tunisia": "TN",
            "Turkey": "TR",
            "Turkmenistan": "TM",
            "Turks and Caicos Islands": "TC",
            "Tuvalu": "TV",
            "US Minor Outlying Islands": "UM",
            "USSR (former)": "SU",
            "Uganda": "UG",
            "Ukraine": "UA",
            "United Arab Emirates": "AE",
            "United Kingdom": "GB",
            "United States": "US",
            "Uruguay": "UY",
            "Uzbekistan": "UZ",
            "Vanuatu": "VU",
            "Vatican City State (Holy See)": "VA",
            "Venezuela": "VE",
            "Viet Nam": "VN",
            "Virgin Islands (British)": "VG",
            "Virgin Islands (U.S.)": "VI",
            "Wallis and Futuna Islands": "WF",
            "Western Sahara": "EH",
            "Yemen": "YE",
            "Yugoslavia": "YU",
            "Zaire": "ZR",
            "Zambia": "ZM",
            "Zimbabwe": "ZW",
        }
        inv_country_codes = {v: k for k, v in country_codes.items()}

        if not self.is_connected():
            self.connect()
        try:
            message_str = f"Getting current Certificate of {self.metadata.device_type_long} device {self.name}"
            if self.task is not None:
                self.task.taskstep_manager.start_taskstep(name="GetCurrentCertificateUcsImc", description=message_str)
            self.logger(level="info", message=message_str)

            current_cert = self.handle.query_classid("CurrentCertificate")

            if current_cert:
                self.logger(level="info", message="Current certificate valid until " + str(current_cert[0].valid_to))
                if self.task is not None:
                    self.task.taskstep_manager.stop_taskstep(
                        name="GetCurrentCertificateUcsImc", status="successful",
                        status_message=f"Successfully queried current Certificate of " +
                                       f"{self.metadata.device_type_long} device {self.name}")
            else:
                self.logger(level="error", message="Unable to get current certificate")
                if self.task is not None:
                    self.task.taskstep_manager.stop_taskstep(
                        name="GetCurrentCertificateUcsImc", status="failed",
                        status_message=f"Unable to get current Certificate of " +
                                       f"{self.metadata.device_type_long} device {self.name}")
                return False

            message_str = f"Generating new self-signed CSR for {self.metadata.device_type_long} device {self.name}"
            if self.task is not None:
                self.task.taskstep_manager.start_taskstep(name="GenerateSelfSignedCertificateSigningRequestUcsImc",
                                                          description=message_str)
            self.logger(level="info", message=message_str)

            mo = GenerateCertificateSigningRequest(parent_mo_or_dn="sys/cert-mgmt")

            params = {
                "common_name": current_cert[0].common_name,
                "organization": current_cert[0].organization,
                "locality": current_cert[0].locality,
                "state": current_cert[0].state,
                "country_code": inv_country_codes.get(current_cert[0].country_code, None),
                "organizational_unit": current_cert[0].organizational_unit,
                "email": None,
                "self_signed": "yes"
            }

            mo.set_prop_multiple(**params)
            self.handle.add_mo(mo, modify_present=True)

            mo = self.handle.query_classid("GenerateCertificateSigningRequest")
            if mo[0].csr_status == "Completed CSR":
                if self.task is not None:
                    self.task.taskstep_manager.stop_taskstep(
                        name="GenerateSelfSignedCertificateSigningRequestUcsImc", status="successful",
                        status_message=f"Successfully generated new self-signed CSR for " +
                                       f"{self.metadata.device_type_long} device {self.name}")
            else:
                self.logger(level="error", message="Unable to get CSR status")
                if self.task is not None:
                    self.task.taskstep_manager.stop_taskstep(
                        name="GenerateSelfSignedCertificateSigningRequestUcsImc", status="failed",
                        status_message=f"Unable to get status of new self-signed CSR for " +
                                       f"{self.metadata.device_type_long} device {self.name}")
                return False

            self.disconnect()

            if self.task is not None:
                self.task.taskstep_manager.start_taskstep(
                    name="WaitForCertificateLoad",
                    description=f"Waiting up to 60 seconds for the new certificate to be loaded on " +
                                f"{self.metadata.device_type_long} device {self.name}")
            self.logger(level="info", message="Waiting up to 60 seconds for the new certificate to be loaded")
            time.sleep(30)
            if not common.check_web_page(device=self, url="https://" + self.target, str_match="Cisco", timeout=30):
                error_msg = "Impossible to reconnect after Regenerating Self-Signed Certificate"
                self.logger(level="error", message=error_msg)
                if self.task is not None:
                    self.task.taskstep_manager.stop_taskstep(
                        name="WaitForCertificateLoad", status="failed", status_message=error_msg)
                return False

            if self.task is not None:
                self.task.taskstep_manager.stop_taskstep(
                    name="WaitForCertificateLoad", status="successful",
                    status_message=f"Successfully loaded new certificate of " +
                                   f"{self.metadata.device_type_long} device {self.name}")

            self.connect(retries=5)

            if self.task is not None:
                self.task.taskstep_manager.start_taskstep(
                    name="CheckNewCertificateValidity",
                    description=f"Checking validity of the new certificate loaded on " +
                                f"{self.metadata.device_type_long} device {self.name}")
            current_cert = self.handle.query_classid("CurrentCertificate")

            self.logger(level="info", message="New certificate valid until " + str(current_cert[0].valid_to))
            if self.task is not None:
                self.task.taskstep_manager.stop_taskstep(
                    name="CheckNewCertificateValidity", status="successful",
                    status_message=f"New certificate valid until " + str(current_cert[0].valid_to) + " on "
                                   f"{self.metadata.device_type_long} device {self.name}")

            return True

        except ImcException as err:
            error_msg = "Error while Regenerating Self-signed Certificate: " + err.error_descr
            self.logger(level="error", message=error_msg)
            if self.task is not None:
                self.task.taskstep_manager.stop_taskstep(
                    name="GenerateSelfSignedCertificateSigningRequestUcsImc", status="failed", status_message=error_msg)
            return False
        except urllib.error.URLError:
            error_msg = "Timeout Error while Regenerating Self-Signed Certificate"
            self.logger(level="error", message=error_msg)
            if self.task is not None:
                self.task.taskstep_manager.stop_taskstep(
                    name="GenerateSelfSignedCertificateSigningRequestUcsImc", status="failed", status_message=error_msg)
            return False
        except Exception as err:
            error_msg = "Error while Regenerating Self-Signed Certificate: " + str(err)
            self.logger(level="error", message=error_msg)
            if self.task is not None:
                self.task.taskstep_manager.stop_taskstep(
                    name="GenerateSelfSignedCertificateSigningRequestUcsImc", status="failed", status_message=error_msg)
            return False

    def is_certificate_expired(self):
        """
        Checks if existing certificate is expired.
        :return: True if expired, False otherwise
        """

        if not self.is_connected():
            self.connect()
        try:
            current_cert = self.handle.query_classid("CurrentCertificate")
            valid_until = datetime.datetime.strptime(current_cert[0].valid_to, '%b %d %H:%M:%S %Y %Z')

            if not datetime.datetime.now() > valid_until:
                self.logger(
                    message="The default keyring certificate is still valid until " + str(current_cert[0].valid_to))
                return False

            self.logger(message="The default keyring certificate is expired since " + str(current_cert[0].valid_to))

            return True

        except UcsException as err:
            self.logger(level="error",
                        message="Error while checking expiration of Default Keyring Certificate" + err.error_descr)
            return False
        except urllib.error.URLError:
            self.logger(level="error",
                        message="Error while checking expiration of Default Keyring Certificate: Timeout error")
            return False
        except Exception as err:
            self.logger(level="error",
                        message="Error while checking expiration of Default Keyring Certificate: " + str(err))
            return False

    def clear_user_sessions(self, check_ssh=False):
        """
        Clear all user sessions
        :param check_ssh: Check with the live system if SSH is enabled. False by default because the system might be
        crowded with sessions, and it might be impossible to check
        :return: True if is successful, False otherwise
        """

        if check_ssh:
            # Verifying that SSH Service is enabled before trying to connect with Paramiko
            if not self.is_connected():
                self.connect()
            self.logger(level="debug", message="Verifying that SSH service is enabled on UCS")
            try:
                ssh = self.handle.query_dn("sys/svc-ext/ssh-svc")
                ssh_admin_state = ssh.admin_state

            except Exception:
                self.logger(level="error", message="Unable to get SSH service state on UCS")
                return False

            try:
                if ssh_admin_state != "enabled":
                    self.logger(level="warning", message="SSH service is disabled on UCS. Enabling it")

                    mo_ssh = imcsdk_CommSsh(parent_mo_or_dn="sys/svc-ext", admin_state="enabled")
                    self.handle.set_mo(mo_ssh)
                    self.handle.commit()
                    self.logger(level="debug", message="SSH service is enabled on UCS")
                    time.sleep(5)

            except Exception:
                self.logger(level="error", message="Unable to set SSH service admin state to 'enabled'")
                return False

        # Establishing connection to UCS
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(self.handle.ip, port=22, username=self.username, password=self.password, banner_timeout=30)

        except paramiko.AuthenticationException:
            self.logger(level="error", message="Authentication failed when connecting to UCS IMC " + self.handle.ip)
            return False

        except paramiko.ssh_exception.NoValidConnectionsError as err:
            self.logger(level="error",
                        message="Error while connecting to UCS IMC " + self.handle.ip + ": " + err.strerror)
            return False

        except TypeError as err:
            self.logger(level="debug",
                        message="Error while connecting to UCS IMC " + self.handle.ip + ": " + str(err))
            self.logger(level="error",
                        message="Error while connecting to UCS IMC " + self.handle.ip + ". Please try again.")
            return False

        # Clearing all user sessions of UCS System
        try:
            self.logger(message="Clearing all user sessions")
            channel = client.invoke_shell()
            channel.settimeout(20)

            self.logger(level="debug", message="\tSending 'show user-session | grep yes'")
            channel.send('show user-session | grep yes\n')

            buff = ""
            while not buff.endswith("# "):
                resp = channel.recv(9999)
                buff += resp.decode("utf-8")

            # Identifying the session numbers to terminate
            sessions_numbers_list = []
            for line in buff.splitlines():
                # We only keep lines that contain session entries for xmlapi and CLI
                if not any(x in line for x in ["xmlapi", "CLI"]):
                    continue
                regex_session = r'^(\d+)'
                res_session = re.search(regex_session, line)
                if res_session is not None:
                    sessions_numbers_list.append(res_session.group(0))

            if sessions_numbers_list:
                self.logger(level="debug",
                            message="There are " + str(len(sessions_numbers_list)) + " sessions to terminate")
                for session_number in sessions_numbers_list:
                    self.logger(level="debug", message="\tSending 'scope user-session " + session_number + "'")
                    channel.send('scope user-session ' + session_number + '\n')

                    self.logger(level="debug", message="\tSending terminate")
                    channel.send('terminate\n')

                    self.logger(level="debug", message="\tSending top")
                    channel.send('top\n')

                self.logger(message="All user sessions cleared")
                time.sleep(5)
            else:
                self.logger(message="No user sessions to clear!")

            # Properly disconnect from SSH
            client.close()

        except paramiko.ChannelException as err:
            self.logger(level="error",
                        message="Communication failed with UCS IMC " + self.handle.ip + ": " + str(err))
            return False

        except (paramiko.buffered_pipe.PipeTimeout, socket.timeout):
            self.logger(level="error", message="Timeout while communicating with UCS IMC " + self.handle.ip)
            return False

        return True

    def erase_virtual_drives(self):
        # Removing Drive Security on the Storage Controllers
        from imcsdk.mometa.self.SelfEncryptStorageController import SelfEncryptStorageController
        from imcsdk.mometa.storage.StorageController import StorageController

        if not self.is_connected():
            self.connect()
        self.logger(level="info", message="Erasing all Virtual Drives")
        all_drive_security = self.handle.query_classid("selfEncryptStorageController")
        for drive_security in all_drive_security:
            mo_security = SelfEncryptStorageController(parent_mo_or_dn=drive_security.dn.split("/ctr-")[0],
                                                       admin_action="disable-self-encrypt")
            try:
                self.handle.set_mo(mo=mo_security)
            except ImcException as err:
                self.logger(level="error",
                            message="Error in resetting IMC Device: " + err.error_descr)

        # Clear all configuration on the Storage Controllers
        all_storage_controllers = self.handle.query_classid("storageController")
        for storage_controller in all_storage_controllers:
            self.logger(level="debug", message="Clearing all config on storage controller: " + storage_controller.dn)
            mo_storage_controller = StorageController(parent_mo_or_dn=storage_controller.dn.split("/storage")[0],
                                                      id=storage_controller.id, type=storage_controller.type,
                                                      admin_action="clear-all-config")
            try:
                self.handle.set_mo(mo=mo_storage_controller)
            except ImcException as err:
                self.logger(level="error",
                            message="Error in resetting IMC Device: " + err.error_descr)

    def erase_flexflash(self):
        # Resetting Flex Flash Controller options
        from imcsdk.mometa.storage.StorageFlexFlashController import StorageFlexFlashController
        from imcsdk.mometa.storage.StorageFlexFlashVirtualDrive import StorageFlexFlashVirtualDrive

        if not self.is_connected():
            self.connect()
        self.logger(level="info", message="Formatting FlexFlash cards")
        all_flex_flash_controller = self.handle.query_classid("storageFlexFlashController")
        for flex_flash_controller in all_flex_flash_controller:
            # Deleting data on the drives
            all_virtual_drives = self.handle.query_classid("storageFlexFlashVirtualDrive")
            for virtual_drive in all_virtual_drives:
                if flex_flash_controller.dn in virtual_drive.dn:
                    self.logger(level="debug", message="Formatting FlexFlash : " + virtual_drive.dn)
                    if "Syncing" in virtual_drive.operation_in_progress:
                        # Cancel the currently running syncing process / Only possible for mirror config
                        # This prevents the call for erasing the SD cards to fail because of the sync in progress
                        mo_flex_flash = StorageFlexFlashController(
                            parent_mo_or_dn=flex_flash_controller.dn.split("/storage")[0],
                            id=flex_flash_controller.id,
                            admin_action="configure-cards",
                            card_slot="slot-1",
                            configured_mode="mirror", auto_sync="no",
                            partition_name="Hypervisor")
                        try:
                            self.handle.set_mo(mo=mo_flex_flash)
                        except ImcException as err:
                            self.logger(level="error",
                                        message="Error in resetting IMC Device: " + err.error_descr)

                        # Erase VD
                        mo_virtual_drive = StorageFlexFlashVirtualDrive(
                            parent_mo_or_dn=virtual_drive.dn.split("/vd")[0],
                            partition_id=virtual_drive.partition_id,
                            admin_action="erase-vd")
                        try:
                            self.handle.set_mo(mo=mo_virtual_drive)
                        except ImcException as err:
                            self.logger(level="error",
                                        message="Error in resetting IMC Device: " + err.error_descr)
                    if "NA" in virtual_drive.operation_in_progress:
                        # Erase VD
                        mo_virtual_drive = StorageFlexFlashVirtualDrive(
                            parent_mo_or_dn=virtual_drive.dn.split("/vd")[0],
                            partition_id=virtual_drive.partition_id,
                            admin_action="erase-vd")
                        try:
                            self.handle.set_mo(mo=mo_virtual_drive)
                        except ImcException as err:
                            self.logger(level="error",
                                        message="Error in resetting IMC Device: " + err.error_descr)
                    if "Erasing" in virtual_drive.operation_in_progress:
                        self.logger(level="info",
                                    message="Erasing process already in progress")

    def clear_sel_logs(self):
        # Clear all SEL logs
        from imcsdk.mometa.sysdebug.SysdebugMEpLog import SysdebugMEpLog

        if not self.is_connected():
            self.connect()

        if self.task is not None:
            self.task.taskstep_manager.start_taskstep(name="ClearSelLogsUcsImc",
                                                      description="Clearing System Event Logs")

        self.logger(level="info", message="Clearing System Event Logs")
        all_logs = self.handle.query_classid("sysdebugMEpLog")

        for log in all_logs:
            if log.type == "SEL":
                try:
                    self.logger(level="debug", message="Clearing SEL: " + log.dn)
                    mo_sel_log = SysdebugMEpLog(parent_mo_or_dn='/'.join(log.dn.split('/')[:-1]),
                                                admin_state="clear", id="0", type="SEL")
                    self.handle.set_mo(mo=mo_sel_log)
                except ImcException as err:
                    self.logger(level="error",
                                message="Error while clearing SEL Logs in " + log.dn + " : " + err.error_descr)
                    if self.task is not None:
                        self.task.taskstep_manager.stop_taskstep(
                            name="ClearSelLogsUcsImc", status="failed",
                            status_message="Error while clearing SEL Logs in " + log.dn + " : " + err.error_descr)
                    return False
                except urllib.error.URLError:
                    self.logger(level="error",
                                message="Timeout Error while clearing SEL Logs in " + log.dn)
                    if self.task is not None:
                        self.task.taskstep_manager.stop_taskstep(
                            name="ClearSelLogsUcsImc", status="failed",
                            status_message="Error while clearing SEL Logs in " + log.dn)
                    return False
                except Exception as err:
                    self.logger(level="error", message="Error while clearing SEL Logs in " + log.dn + ": " + str(err))
                    if self.task is not None:
                        self.task.taskstep_manager.stop_taskstep(
                            name="ClearSelLogsUcsImc", status="failed",
                            status_message="Error while clearing SEL Logs in " + log.dn + ": " + str(err))
                    return False
                break

        self.logger(level="info", message="Successfully cleared System Event Logs")
        if self.task is not None:
            self.task.taskstep_manager.stop_taskstep(
                name="ClearSelLogsUcsImc", status="successful",
                status_message=f"Successfully cleared System Event Logs")
        return True

    def set_drives_status(self, status=None):
        """
        Set all the drives to the status specified.
        If jbod specified: all the unconfigured-good drives will be set to jbod
        If unconfigured-good specified: all the jbod drives will be set to jbod
        :param status: jbod or unconfigured-good
        :return: True, False otherwise
        """

        if status:
            all_storage_drives = self.handle.query_classid("storageLocalDisk")
            for storage_drive in all_storage_drives:
                if status == "jbod":
                    # We search for unconfigured-good drives
                    if storage_drive.pd_status == "Unconfigured Good":
                        self.logger(level="debug", message="Setting status jbod on physical drive: " + storage_drive.dn)
                        storage_drive.admin_action = "make-jbod"
                        try:
                            self.handle.set_mo(mo=storage_drive)
                        except ImcException as err:
                            self.logger(level="error",
                                        message="Error in setting new status " + status + " to physical drive " +
                                                storage_drive.dn + " : " + err.error_descr)
                elif status == "unconfigured-good":
                    # We search for jbod drives
                    if storage_drive.pd_status == "JBOD":
                        self.logger(level="debug",
                                    message="Setting status unconfigured-good on physical drive: " + storage_drive.dn)
                        storage_drive.admin_action = "make-unconfigured-good"
                        try:
                            self.handle.set_mo(mo=storage_drive)
                        except ImcException as err:
                            self.logger(level="error",
                                        message="Error in setting new status " + status + " to physical drive " +
                                                storage_drive.dn + " : " + err.error_descr)
                else:
                    self.logger(level="error", message="Status requested does not exist " + status)
                    return False
        else:
            self.logger(level="error", message="No status requested!")
            return False
        return True

    def query(self, mode="", target=None, retries=3):
        """
        Uses the query of the handle and add a retry function
        :param mode: "dn" or "classid"
        :param target: target of the query (dn or classid)
        :param retries: number of retries before considering the query is failed
        :return: the result of the query, or an empty list if query failed or not found
        """
        if not mode:
            self.logger(level="error", message="A mode of query must be filled")
            return []
        if not target:
            self.logger(level="error", message="A target of query must be filled")
            return []
        if mode not in ["classid", "dn"]:
            self.logger(level="error", message="The mode query must be 'classid' or 'dn'")
            return []

        for i in range(retries):
            if i:
                self.logger(level="warning", message="Retrying to fetch " + target + " (attempt " + str(i + 1) + ")")
            try:
                if not self.is_connected():
                    self.connect()
                if mode == "classid":
                    classid_list = self.handle.query_classid(target)
                    return classid_list
                elif mode == "dn":
                    dn_list = self.handle.query_dn(target)
                    return dn_list
            except ConnectionRefusedError as err:
                self.logger(level="error", message="Error while querying UCS IMC: " + str(err))
            except UcsException as err:
                self.logger(level="error", message="Unable to fetch " + target + " " + err.error_descr)
            except urllib.error.URLError:
                self.logger(level="error", message="Timeout error while fetching " + target)
            time.sleep(self.device.push_interval_after_fail)
        return []

    def wait_for_reboot_after_reset(self, timeout=480, imc_ip=None):
        """
        Waits for IMC to reboot after a complete reset
        :param timeout: time in seconds above which the wait will be considered failed
        :param imc_ip: DHCP IP address taken by the CIMC after the reset
        :return: True when IMC has rebooted, False if timeout exceeded
        """
        if not imc_ip:
            self.logger(level="error", message="No DHCP IP address given")
            return False
        else:
            self.logger(level="info", message="Waiting for UCS IMC to come back after reset")
            if not common.check_web_page(self, "https://" + imc_ip, "Cisco", timeout):
                self.logger(level="error",
                            message="Impossible to reconnect to UCS IMC " + imc_ip + " after the reset")
                return False
        return True

    def _set_device_name_and_version(self):
        """
        Sets the device name and version attributes of the device.
        :return: nothing
        """
        self.name = self.handle.imc
        self.version = self.handle.version
        self.metadata.device_name = self.name
        if hasattr(self.version, "version"):
            self.metadata.device_version = self.version.version
        if self.handle.session_id:  # We first make sure we have already connected at least once to avoid crash
            self.platform_type = self.handle.platform
            self.logger(level="debug", message="Detected IMC platform type: " + self.platform_type)

    def _set_sdk_version(self):
        """
        Figures out the highest UCS IMC version supported by imcsdk
        :return: nothing
        """
        supported_versions_list = [getattr(ImcVersionMeta(), attr) for attr in dir(ImcVersionMeta())
                                   if "Version" in attr]
        if not len(supported_versions_list):
            self.version_max_supported_by_sdk = None

        max_supported_version = ImcVersion("")
        for version in supported_versions_list:
            if version.compare_to(max_supported_version) == 1:
                max_supported_version = version

        self.version_max_supported_by_sdk = max_supported_version


class UcsCentral(GenericUcsDevice):
    UCS_CENTRAL_MIN_REQUIRED_VERSION = "2.0(1a)"

    def __init__(self, parent=None, uuid=None, target="", user="", password="", is_hidden=False, is_system=False,
                 system_usage=None, logger_handle_log_level="info", log_file_path=None, bypass_connection_checks=False,
                 bypass_version_checks=False, user_label=""):
        GenericUcsDevice.__init__(self, parent=parent, uuid=uuid, target=target, password=password, user=user,
                                  is_hidden=is_hidden, is_system=is_system, system_usage=system_usage,
                                  logger_handle_log_level=logger_handle_log_level, log_file_path=log_file_path,
                                  bypass_connection_checks=bypass_connection_checks,
                                  bypass_version_checks=bypass_version_checks, user_label=user_label)

        self.handle = UcscHandle(ip=target, username=user, password=password)
        self.handle.set_mode_threading()
        self.version_min_required = UcscVersion(self.UCS_CENTRAL_MIN_REQUIRED_VERSION)
        self.version_sdk = str(ucscsdk_sdk_version)
        self.backup_manager = UcsCentralBackupManager(parent=self)
        self.config_manager = UcsCentralConfigManager(parent=self)
        self.inventory_manager = UcsCentralInventoryManager(parent=self)
        self.report_manager = UcsCentralReportManager(parent=self)
        self._set_sdk_version()
        self._set_device_name_and_version()

        self.metadata.device_type = "ucsc"
        self.metadata.device_type_long = "UCS Central"

    def clear_user_sessions(self):
        """
        Clear all user sessions
        :return: True if is successful, False otherwise
        """

        # Establishing connection to UCS
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(self.handle.ip, port=22, username=self.username, password=self.password, banner_timeout=30)

        except paramiko.AuthenticationException:
            self.logger(level="error", message="Authentication failed when connecting to UCS Central " + self.handle.ip)
            return False

        except paramiko.ssh_exception.NoValidConnectionsError as err:
            self.logger(level="error",
                        message="Error while connecting to UCS Central " + self.handle.ip + ": " + err.strerror)
            return False

        except TypeError as err:
            self.logger(level="debug",
                        message="Error while connecting to UCS Central " + self.handle.ip + ": " + str(err))
            self.logger(level="error",
                        message="Error while connecting to UCS Central " + self.handle.ip + ". Please try again.")
            return False

        # Clearing all user sessions of UCS Central
        try:
            self.logger(message="Clearing all user sessions")
            channel = client.invoke_shell()
            channel.settimeout(20)

            self.logger(level="debug", message="\tSending 'scope security'")
            channel.send('scope security\n')

            buff = ""
            while not buff.endswith("security # "):
                resp = channel.recv(9999)
                buff += resp.decode("utf-8")
            buff = ""

            self.logger(level="debug", message="\tSending 'clear-user-sessions all'")
            channel.send('clear-user-sessions all\n')
            while not buff.endswith("yes/no):"):
                resp = channel.recv(9999)
                buff += resp.decode("utf-8")

            self.logger(level="debug", message="\tSending confirmation")
            channel.send('yes\n')
            self.logger(message="All user sessions cleared")
            time.sleep(5)

        except paramiko.ChannelException as err:
            self.logger(level="error",
                        message="Communication failed with UCS Central " + self.handle.ip + ": " + str(err))
            return False

        except (paramiko.buffered_pipe.PipeTimeout, socket.timeout):
            self.logger(level="error", message="Timeout while communicating with UCS Central " + self.handle.ip)
            return False

        return True

    def query(self, mode="", target=None, filter_str=None, retries=3):
        """
        Uses the query of the handle and add a retry function
        :param mode: "dn" or "classid"
        :param target:
        :param filter_str:
        :param retries:
        :return:
        """

        if not mode:
            self.logger(level="error", message="A mode of query must be filled")
            return []
        if not target:
            self.logger(level="error", message="A target of query must be filled")
            return []
        if mode not in ["classid", "dn"]:
            self.logger(level="error", message="The mode query must be 'classid' or 'dn'")
            return []
        for i in range(retries):
            if i:
                self.logger(level="warning", message="Retrying to fetch " + target + " (attempt " + str(i + 1) + ")")
            try:
                if not self.is_connected():
                    self.connect()
                if mode == "classid":
                    classid_list = self.handle.query_classid(class_id=target, filter_str=filter_str)
                    return classid_list
                elif mode == "dn":
                    dn_list = self.handle.query_dn(dn=target)
                    return dn_list
            except ConnectionRefusedError as err:
                self.logger(level="debug", message="Error while querying UCS Central: " + str(err))
            except UcscException as err:
                self.logger(level="debug", message="Unable to fetch " + target + ": " + err.error_descr)
            except urllib.error.URLError:
                self.logger(level="debug", message="Timeout error while fetching " + target)
            time.sleep(self.push_interval_after_fail)

        self.logger(level="error", message="Unable to fetch " + target + " after " + str(retries) + " attempts")
        return []

    def _set_sdk_version(self):
        """
        Figures out the highest UCS Central version supported by ucscsdk
        :return: nothing
        """
        supported_versions_list = [getattr(UcscVersionMeta(), attr) for attr in dir(UcscVersionMeta())
                                   if "Version" in attr]
        if not len(supported_versions_list):
            self.version_max_supported_by_sdk = None

        max_supported_version = UcscVersion("2.0(1a)")
        for version in supported_versions_list:
            if version.compare_to(max_supported_version) == 1:
                max_supported_version = version

        self.version_max_supported_by_sdk = max_supported_version

    def _set_device_name_and_version(self):
        """
        Sets the device name and version attributes of the device.
        :return: nothing
        """
        self.name = self.handle.ucs
        self.version = self.handle.version
        if self.handle.session_id:  # We first make sure we have already connected at least once to avoid timeout
            if self.is_connected():  # We then make sure the session is still valid
                try:
                    top_system = self.handle.query_dn("sys")
                    if top_system:
                        self.name = top_system.name

                except Exception:
                    self.logger(level="debug", message="Unable to find topSystem object of UCS Central " + self.target)

        self.metadata.device_name = self.name
        if hasattr(self.version, "version"):
            self.metadata.device_version = self.version.version
