# coding: utf-8
# !/usr/bin/env python

""" system.py: Easy UCS Central System objects """

import hashlib

from config.ucs.object import UcsCentralConfigObject

from ucscsdk.mometa.aaa.AaaDomainGroup import AaaDomainGroup
from ucscsdk.mometa.aaa.AaaLocale import AaaLocale
from ucscsdk.mometa.aaa.AaaOrg import AaaOrg
from ucscsdk.mometa.aaa.AaaPwdProfile import AaaPwdProfile
from ucscsdk.mometa.aaa.AaaRole import AaaRole
from ucscsdk.mometa.aaa.AaaSshAuth import AaaSshAuth
from ucscsdk.mometa.aaa.AaaUser import AaaUser
from ucscsdk.mometa.aaa.AaaUserLocale import AaaUserLocale
from ucscsdk.mometa.aaa.AaaUserRole import AaaUserRole
from ucscsdk.mometa.comm.CommDateTime import CommDateTime
from ucscsdk.mometa.comm.CommDns import CommDns
from ucscsdk.mometa.comm.CommDnsProvider import CommDnsProvider
from ucscsdk.mometa.comm.CommNtpProvider import CommNtpProvider
from ucscsdk.mometa.comm.CommSnmp import CommSnmp
from ucscsdk.mometa.comm.CommSnmpTrap import CommSnmpTrap
from ucscsdk.mometa.comm.CommSnmpUser import CommSnmpUser
from ucscsdk.mometa.comm.CommSyslog import CommSyslog
from ucscsdk.mometa.comm.CommSyslogClient import CommSyslogClient
from ucscsdk.mometa.comm.CommSyslogConsole import CommSyslogConsole
from ucscsdk.mometa.comm.CommSyslogFile import CommSyslogFile
from ucscsdk.mometa.comm.CommSyslogMonitor import CommSyslogMonitor
from ucscsdk.mometa.comm.CommSyslogSource import CommSyslogSource
from ucscsdk.mometa.mgmt.MgmtIPv6IfAddr import MgmtIPv6IfAddr
from ucscsdk.mometa.network.NetworkElement import NetworkElement
from ucscsdk.mometa.top.TopSystem import TopSystem


class UcsCentralDateTimeMgmt(UcsCentralConfigObject):
    _CONFIG_NAME = "Date & Time"
    _UCS_SDK_OBJECT_NAME = "commDateTime"

    def __init__(self, parent=None, json_content=None, comm_date_time=None):
        UcsCentralConfigObject.__init__(self, parent=parent)
        self.ntp_servers = []
        self.timezone = None

        if comm_date_time:
            mo = comm_date_time.dn
        else:
            mo = "org-root/deviceprofile-default/datetime-svc"

        if self._config.load_from == "live":
            if "commDateTime" in self._config.sdk_objects:
                comm_date_time_list = [comm_date_time for comm_date_time in self._config.sdk_objects["commDateTime"]
                                       if mo in comm_date_time.dn]
                if len(comm_date_time_list) == 1:
                    comm_date_time = comm_date_time_list[0]
                    self.timezone = comm_date_time.timezone

            if "commNtpProvider" in self._config.sdk_objects:
                ntp_provider_list = [ntp_provider for ntp_provider in self._config.sdk_objects["commNtpProvider"]
                                     if mo in ntp_provider.dn]
                for ntp_provider in ntp_provider_list:
                    self.ntp_servers.append(ntp_provider.name)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration")
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration" +
                                ", waiting for a commit")

        parent_obj = self._parent
        if parent_obj.__class__.__name__ in ["UcsCentralDomainGroup"]:
            dg_list = []
            while parent_obj.__class__.__name__ in ["UcsCentralDomainGroup"]:
                dg_list.append(parent_obj.name)
                parent_obj = parent_obj._parent
            dg_list.reverse()
            parent_mo = ""
            for dg in dg_list:
                parent_mo += "domaingroup-" + dg + "/"
            parent_mo = parent_mo[:-1]  # We remove the last "/" at the end of the mo
        else:
            parent_mo = "org-root/deviceprofile-default"

        mo_comm_date_time = CommDateTime(parent_mo_or_dn=parent_mo, timezone=self.timezone)
        for ntp in self.ntp_servers:
            CommNtpProvider(parent_mo_or_dn=mo_comm_date_time, name=ntp)

        self._handle.add_mo(mo=mo_comm_date_time, modify_present=True)
        if commit:
            if self.commit() != True:
                return False
        return True


class UcsCentralDns(UcsCentralConfigObject):
    _CONFIG_NAME = "DNS"
    _UCS_SDK_OBJECT_NAME = "commDns"

    def __init__(self, parent=None, json_content=None, comm_dns=None):
        UcsCentralConfigObject.__init__(self, parent=parent)
        self.dns_servers = []
        self.domain_name = None

        if comm_dns:
            mo = comm_dns.dn
        else:
            mo = "org-root/deviceprofile-default/dns-svc"

        if self._config.load_from == "live":
            if "commDnsProvider" in self._config.sdk_objects:
                dns_list = [dns for dns in self._config.sdk_objects["commDnsProvider"] if mo in dns.dn]
                for dns in dns_list:
                    self.dns_servers.append(dns.name)

            if "commDns" in self._config.sdk_objects:
                dns_list = [dns for dns in self._config.sdk_objects["commDns"] if mo in dns.dn]
                if len(dns_list) == 1:
                    comm_dns = dns_list[0]
                    self.domain_name = comm_dns.domain

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration")
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration" +
                                ", waiting for a commit")

        parent_obj = self._parent
        if parent_obj.__class__.__name__ in ["UcsCentralDomainGroup"]:
                dg_list = []
                while parent_obj.__class__.__name__ in ["UcsCentralDomainGroup"]:
                    dg_list.append(parent_obj.name)
                    parent_obj = parent_obj._parent
                dg_list.reverse()
                parent_mo = ""
                for dg in dg_list:
                    parent_mo += "domaingroup-" + dg + "/"
                parent_mo = parent_mo[:-1]  # We remove the last "/" at the end of the mo
        else:
            parent_mo = "org-root/deviceprofile-default"

        for dns_server in self.dns_servers:
            mo_comm_dns_provider = CommDnsProvider(parent_mo_or_dn=parent_mo, name=dns_server)
            self._handle.add_mo(mo_comm_dns_provider, modify_present=True)

        mo_comm_dns = CommDns(parent_mo_or_dn=parent_mo, domain=self.domain_name)
        self._handle.add_mo(mo=mo_comm_dns, modify_present=True)

        if commit:
            if self.commit() != True:
                return False
        return True


class UcsCentralLocalUser(UcsCentralConfigObject):
    _CONFIG_NAME = "Local User"
    _UCS_SDK_OBJECT_NAME = "aaaUser"

    def __init__(self, parent=None, json_content=None, aaa_user=None):
        UcsCentralConfigObject.__init__(self, parent=parent)
        self.name = None
        self.descr = None
        self.first_name = None
        self.last_name = None
        self.email = None
        self.phone = None
        self.password = None
        self.account_status = None
        self.ssh_key = None
        self.expiration = None
        self.roles = []
        self.locales = []

        if aaa_user:
            mo = aaa_user.dn
        else:
            mo = "org-root/deviceprofile-default"

        if self._config.load_from == "live":
            if aaa_user is not None:
                self.account_status = aaa_user.account_status
                self.descr = aaa_user.descr
                self.email = aaa_user.email
                self.first_name = aaa_user.first_name
                self.name = aaa_user.name
                self.last_name = aaa_user.last_name
                self.phone = aaa_user.phone
                self.password = aaa_user.pwd

                self.logger(level="warning", message="Password of " + self._CONFIG_NAME + " " + self.name +
                                                     " can't be exported")

                self.expiration = aaa_user.expiration
                if self.expiration == "never":
                    self.expiration = None

                if mo == "org-root/deviceprofile-default":
                    mo += "/user-" + self.name

                if "aaaSshAuth" in self._config.sdk_objects:
                    ssh_key = [ssh_key.data for ssh_key in self._config.sdk_objects["aaaSshAuth"]
                               if mo + "/user-" + self.name + "/" in ssh_key.dn]
                    if ssh_key:
                        self.ssh_key = ssh_key[0]

                if "aaaUserLocale" in self._config.sdk_objects:
                    locale_list = [locale for locale in self._config.sdk_objects["aaaUserLocale"]
                                   if mo + "/user-" + self.name + "/" in locale.dn]
                    for locale in locale_list:
                        self.locales.append(locale.name)

                if "aaaUserRole" in self._config.sdk_objects:
                    role_list = [role for role in self._config.sdk_objects["aaaUserRole"]
                                 if mo + "/user-" + self.name + "/" in role.dn]
                    for role in role_list:
                        self.roles.append(role.name)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration")
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration" +
                                ", waiting for a commit")

        parent_obj = self._parent
        if parent_obj.__class__.__name__ in ["UcsCentralDomainGroup"]:
            dg_list = []
            while parent_obj.__class__.__name__ in ["UcsCentralDomainGroup"]:
                dg_list.append(parent_obj.name)
                parent_obj = parent_obj._parent
            dg_list.reverse()
            parent_mo = ""
            for dg in dg_list:
                parent_mo += "domaingroup-" + dg + "/"
            parent_mo = parent_mo[:-1]  # We remove the last "/" at the end of the mo
        else:
            parent_mo = "org-root/deviceprofile-default"

        expires = "no"
        if self.expiration:
            expires = "yes"
        mo_user = AaaUser(parent_mo_or_dn=parent_mo, name=self.name, first_name=self.first_name, descr=self.descr,
                          last_name=self.last_name, email=self.email, phone=self.phone, pwd=self.password,
                          account_status=self.account_status, expires=expires, expiration=self.expiration)
        for locale in self.locales:
            AaaUserLocale(parent_mo_or_dn=mo_user, name=locale)
        for role in self.roles:
            AaaUserRole(parent_mo_or_dn=mo_user, name=role)

        if self.ssh_key:
            AaaSshAuth(parent_mo_or_dn=mo_user, data=self.ssh_key, str_type="key")
        self._handle.add_mo(mo_user, modify_present=True)

        if commit:
            committed = self.commit(show=False)
            if committed != True:
                # We handle this specific error
                if hasattr(committed, "error_descr"):
                    if committed.error_descr == \
                            "Password history check: user should not use the previously used password.":
                        self.logger(level="warning",
                                    message="The password history of " + self.name + " will be deleted")
                        # We add again this user but with the clear pwd history value at "yes"
                        mo_aaa_user = AaaUser(parent_mo_or_dn=parent_mo, name=self.name, first_name=self.first_name,
                                              last_name=self.last_name, email=self.email, phone=self.phone,
                                              pwd=self.password, account_status=self.account_status, expires=expires,
                                              expiration=self.expiration, descr=self.descr, clear_pwd_history="yes")
                        self._handle.add_mo(mo_aaa_user, modify_present=True)
                        if self.commit() != True:
                            return False
                    else:
                        # The print value of commit is True so we need to log the error if it is not the expected error
                        self.logger(level="error",
                                    message="Error in configuring " + self._CONFIG_NAME + ": " + committed.error_descr)
                return False
            self.logger(message="Successfully configured " + self._CONFIG_NAME + " configuration: " + self.name)
        return True


class UcsCentralLocale(UcsCentralConfigObject):
    _CONFIG_NAME = "Locale"
    _UCS_SDK_OBJECT_NAME = "aaaLocale"

    def __init__(self, parent=None, json_content=None, aaa_locale=None):
        UcsCentralConfigObject.__init__(self, parent=parent)
        self.name = None
        self.descr = None
        self.domain_groups = []
        self.organizations = []

        if aaa_locale:
            mo = aaa_locale.dn
        else:
            mo = "org-root/deviceprofile-default"

        if self._config.load_from == "live":
            if aaa_locale is not None:
                self.name = aaa_locale.name
                self.descr = aaa_locale.descr

                if mo == "org-root/deviceprofile-default":
                    mo += "/locale-" + self.name

                if "aaaOrg" in self._config.sdk_objects:
                    for organization in self._config.sdk_objects["aaaOrg"]:
                        if mo + "/org-" in organization.dn:
                            self.organizations.append(organization.org_dn)

                if "aaaDomainGroup" in self._config.sdk_objects:
                    for domain_group in self._config.sdk_objects["aaaDomainGroup"]:
                        if mo + "/domaingroup-" in domain_group.dn:
                            self.domain_groups.append(domain_group.domaingroup_dn)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration")
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration" +
                                ", waiting for a commit")

        parent_obj = self._parent
        if parent_obj.__class__.__name__ in ["UcsCentralDomainGroup"]:
            dg_list = []
            while parent_obj.__class__.__name__ in ["UcsCentralDomainGroup"]:
                dg_list.append(parent_obj.name)
                parent_obj = parent_obj._parent
            dg_list.reverse()
            parent_mo = ""
            for dg in dg_list:
                parent_mo += "domaingroup-" + dg + "/"
            parent_mo = parent_mo[:-1]  # We remove the last "/" at the end of the mo
        else:
            parent_mo = "org-root/deviceprofile-default"

        mo_locale = AaaLocale(parent_mo_or_dn=parent_mo, name=self.name, descr=self.descr)

        if self.organizations:
            for organization in self.organizations:
                complete_org_path = ""
                for part in organization.split("/"):
                    if "org-" not in part:
                        complete_org_path += "org-"
                    complete_org_path += part + "/"
                complete_org_path = complete_org_path[:-1]  # Remove the trailing "/"
                if not complete_org_path.startswith("org-root"):
                    complete_org_path = "org-root/" + complete_org_path

                # We use a MD5 hashing function for the name of the AaaOrg object, since Central automatically generates
                # a numerical ID when doing the action from the GUI.
                AaaOrg(parent_mo_or_dn=mo_locale, name=hashlib.md5(complete_org_path.encode()).hexdigest()[:16],
                       descr="", org_dn=complete_org_path)

        if self.domain_groups:
            for domain_group in self.domain_groups:
                complete_dg_path = ""
                for part in domain_group.split("/"):
                    if "domaingroup-" not in part:
                        complete_dg_path += "domaingroup-"
                    complete_dg_path += part + "/"
                complete_dg_path = complete_dg_path[:-1]  # Remove the trailing "/"
                if not complete_dg_path.startswith("domaingroup-root"):
                    complete_dg_path = "domaingroup-root/" + complete_dg_path

                # We use a MD5 hashing function for the name of the AaaDomainGroup object, since Central automatically
                # generates a numerical ID when doing the action from the GUI.
                AaaDomainGroup(parent_mo_or_dn=mo_locale, name=hashlib.md5(complete_dg_path.encode()).hexdigest()[:16],
                               descr="", domaingroup_dn=complete_dg_path)

        self._handle.add_mo(mo_locale, modify_present=True)

        if commit:
            if self.commit() != True:
                return False
        return True


class UcsCentralManagementInterface(UcsCentralConfigObject):
    _CONFIG_NAME = "Management Interface"

    def __init__(self, parent=None, json_content=None, network_element=None):
        UcsCentralConfigObject.__init__(self, parent=parent)
        self.node = "primary"
        self.gateway = None
        self.gateway_v6 = None
        self.ip = None
        self.ipv6 = None
        self.netmask = None
        self.prefix = None

        if self._config.load_from == "live":
            if network_element is not None:
                if network_element.id == "A":
                    self.node = "primary"
                elif network_element.id == "B":
                    self.node = "secondary"
                self.ip = network_element.oob_if_ip
                self.netmask = network_element.oob_if_mask
                self.gateway = network_element.oob_if_gw

            if "mgmtIPv6IfAddr" in self._config.sdk_objects:
                for mgmt_ipv6_ifaddr in self._config.sdk_objects["mgmtIPv6IfAddr"]:
                    if "sys/switch-" + network_element.id + "/" in mgmt_ipv6_ifaddr.dn:
                        self.ipv6 = mgmt_ipv6_ifaddr.addr
                        self.prefix = mgmt_ipv6_ifaddr.prefix
                        self.gateway_v6 = mgmt_ipv6_ifaddr.def_gw

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration for node " + self.node)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration for node" +
                                self.node + ", waiting for a commit")

        # TODO : Add check if IP mgmt int is different from the one configured and reset the handle if this is the case

        fabric = "A"
        if self.node == "primary":
            fabric = "A"
        elif self.node == "secondary":
            fabric = "B"

        # Checking if the IPv4 and/or IPv6 parameters are given
        if self.ip and self.netmask and self.gateway:
            mo_network_element = NetworkElement(parent_mo_or_dn="sys", id=fabric, oob_if_ip=self.ip,
                                                oob_if_gw=self.gateway, oob_if_mask=self.netmask)
            self._handle.add_mo(mo=mo_network_element, modify_present=True)
            self.logger(level="debug", message="IPv4 parameters for " + self._CONFIG_NAME + " " + self.node + " set")

        if self.ipv6 and self.prefix and self.gateway_v6:
            mo_mgmt_ipv6_if_addr = MgmtIPv6IfAddr(parent_mo_or_dn="sys/switch-" + fabric + "/ifConfig-ipv6",
                                                  addr=self.ipv6, def_gw=self.gateway_v6, prefix=self.prefix)
            self._handle.add_mo(mo=mo_mgmt_ipv6_if_addr, modify_present=True)
            self.logger(level="debug", message="IPv6 parameters for " + self._CONFIG_NAME + " " + self.node + " set")

        if commit:
            if self.commit() != True:
                return False
        return True


class UcsCentralPasswordProfile(UcsCentralConfigObject):
    _CONFIG_NAME = "Password Profile"
    _UCS_SDK_OBJECT_NAME = "aaaPwdProfile"

    def __init__(self, parent=None, json_content=None, aaa_pwd_profile=None):
        UcsCentralConfigObject.__init__(self, parent=parent)
        self.password_strength_check = None
        self.change_interval = None
        self.no_change_interval = None
        self.change_during_interval = None
        self.change_count = None
        self.history_count = None

        if aaa_pwd_profile:
            mo = aaa_pwd_profile.dn
        else:
            mo = "org-root/deviceprofile-default"

        if self._config.load_from == "live":
            if "aaaPwdProfile" in self._config.sdk_objects:
                aaa_pwd_profile_list = [aaa_pwd_profile for aaa_pwd_profile in self._config.sdk_objects["aaaPwdProfile"]
                                        if mo in aaa_pwd_profile.dn]
                if len(aaa_pwd_profile_list) == 1:
                    aaa_pwd_profile = aaa_pwd_profile_list[0]
                    self.password_strength_check = aaa_pwd_profile.pwd_strength_check
                    self.change_interval = aaa_pwd_profile.change_interval
                    self.no_change_interval = aaa_pwd_profile.no_change_interval
                    self.change_during_interval = aaa_pwd_profile.change_during_interval
                    self.change_count = aaa_pwd_profile.change_count
                    self.history_count = aaa_pwd_profile.history_count

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration")
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration" +
                                ", waiting for a commit")

        parent_obj = self._parent
        if parent_obj.__class__.__name__ in ["UcsCentralDomainGroup"]:
            dg_list = []
            while parent_obj.__class__.__name__ in ["UcsCentralDomainGroup"]:
                dg_list.append(parent_obj.name)
                parent_obj = parent_obj._parent
            dg_list.reverse()
            parent_mo = ""
            for dg in dg_list:
                parent_mo += "domaingroup-" + dg + "/"
            parent_mo = parent_mo[:-1]  # We remove the last "/" at the end of the mo
        else:
            parent_mo = "org-root/deviceprofile-default"

        mo_aaa_pwd_profile = AaaPwdProfile(parent_mo_or_dn=parent_mo, no_change_interval=self.no_change_interval,
                                           change_interval=self.change_interval, history_count=self.history_count,
                                           change_count=self.change_count,
                                           change_during_interval=self.change_during_interval,
                                           pwd_strength_check=self.password_strength_check)

        self._handle.add_mo(mo=mo_aaa_pwd_profile, modify_present=True)

        if commit:
            if self.commit() != True:
                return False
        return True


class UcsCentralRole(UcsCentralConfigObject):
    _CONFIG_NAME = "Role"
    _UCS_SDK_OBJECT_NAME = "aaaRole"

    def __init__(self, parent=None, json_content=None, aaa_role=None):
        UcsCentralConfigObject.__init__(self, parent=parent)
        self.name = None
        self.privileges = []

        if aaa_role:
            mo = aaa_role.dn
        else:
            mo = "org-root/deviceprofile-default"

        if self._config.load_from == "live":
            if aaa_role is not None:
                self.name = aaa_role.name
                role_privilege = aaa_role.priv
                if role_privilege:
                    privilege_list = role_privilege.split(',')
                    for priv in privilege_list:
                        self.privileges.append(priv)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration")
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration" +
                                ", waiting for a commit")

        parent_obj = self._parent
        if parent_obj.__class__.__name__ in ["UcsCentralDomainGroup"]:
            dg_list = []
            while parent_obj.__class__.__name__ in ["UcsCentralDomainGroup"]:
                dg_list.append(parent_obj.name)
                parent_obj = parent_obj._parent
            dg_list.reverse()
            parent_mo = ""
            for dg in dg_list:
                parent_mo += "domaingroup-" + dg + "/"
            parent_mo = parent_mo[:-1]  # We remove the last "/" at the end of the mo
        else:
            parent_mo = "org-root/deviceprofile-default"

        privileges = None
        if self.privileges:
            privileges = ",".join(self.privileges)
        mo_role = AaaRole(parent_mo_or_dn=parent_mo, name=self.name, descr="", priv=privileges)
        self._handle.add_mo(mo_role, modify_present=True)

        if commit:
            if self.commit() != True:
                return False
        return True


class UcsCentralSnmp(UcsCentralConfigObject):
    _CONFIG_NAME = "SNMP"
    _UCS_SDK_OBJECT_NAME = "commSnmp"

    def __init__(self, parent=None, json_content=None, comm_snmp=None):
        UcsCentralConfigObject.__init__(self, parent=parent)
        self.state = None
        self.community = None
        self.contact = None
        self.location = None
        self.snmp_traps = []
        self.snmp_users = []

        if comm_snmp:
            mo = comm_snmp.dn
        else:
            mo = "org-root/deviceprofile-default/snmp-svc"

        if self._config.load_from == "live":
            if comm_snmp is None:
                if "commSnmp" in self._config.sdk_objects:
                    comm_snmp_list = [comm_snmp for comm_snmp in self._config.sdk_objects["commSnmp"]
                                      if comm_snmp.dn == "org-root/deviceprofile-default/snmp-svc"]
                    if len(comm_snmp_list) == 1:
                        comm_snmp = comm_snmp_list[0]

            if comm_snmp is not None:
                self.state = comm_snmp.admin_state
                self.community = comm_snmp.community
                self.contact = comm_snmp.sys_contact
                self.location = comm_snmp.sys_location

            # SNMP Traps
            if "commSnmpTrap" in self._config.sdk_objects:
                comm_snmp_trap_list = [comm_snmp_trap for comm_snmp_trap in self._config.sdk_objects["commSnmpTrap"]
                                       if mo + "/snmp-trap" in comm_snmp_trap.dn]
                if len(comm_snmp_trap_list) == 1:
                    comm_snmp_trap = comm_snmp_trap_list[0]
                    self.snmp_traps.append({"hostname": comm_snmp_trap.hostname,
                                            "community": comm_snmp_trap.community,
                                            "port": comm_snmp_trap.port,
                                            "version": comm_snmp_trap.version,
                                            "notification_type": comm_snmp_trap.notification_type,
                                            "v3privilege": comm_snmp_trap.v3_privilege})

            # SNMP Users
            if "commSnmpUser" in self._config.sdk_objects:
                comm_snmp_user_list = [comm_snmp_user for comm_snmp_user in
                                       self._config.sdk_objects["commSnmpUser"]
                                       if mo + "/snmpv3-user-" in comm_snmp_user.dn]
                if len(comm_snmp_user_list) == 1:
                    comm_snmp_user = comm_snmp_user_list[0]
                    self.snmp_users.append({"name": comm_snmp_user.name,
                                            "descr": comm_snmp_user.descr,
                                            "privacy_password": comm_snmp_user.privpwd,
                                            "password": comm_snmp_user.pwd,
                                            "auth_type": comm_snmp_user.auth,
                                            "use_aes": comm_snmp_user.use_aes})

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

                for element in self.snmp_traps:
                    for value in ["hostname", "community", "port", "version", "notification_type", "v3privilege"]:
                        if value not in element:
                            element[value] = None

                for element in self.snmp_users:
                    for value in ["name", "descr", "privacy_password", "password", "auth_type", "use_aes"]:
                        if value not in element:
                            element[value] = None

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration")
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration" +
                                ", waiting for a commit")

        parent_obj = self._parent
        if parent_obj.__class__.__name__ in ["UcsCentralDomainGroup"]:
            dg_list = []
            while parent_obj.__class__.__name__ in ["UcsCentralDomainGroup"]:
                dg_list.append(parent_obj.name)
                parent_obj = parent_obj._parent
            dg_list.reverse()
            parent_mo = ""
            for dg in dg_list:
                parent_mo += "domaingroup-" + dg + "/"
            parent_mo = parent_mo[:-1]  # We remove the last "/" at the end of the mo
        else:
            parent_mo = "org-root/deviceprofile-default"

        mo_comm_snmp = CommSnmp(parent_mo_or_dn=parent_mo, admin_state=self.state, community=self.community,
                                sys_contact=self.contact, sys_location=self.location)

        if self.snmp_users:
            for user in self.snmp_users:
                CommSnmpUser(parent_mo_or_dn=mo_comm_snmp, name=user["name"], descr=user["descr"],
                             pwd=user["password"], privpwd=user["privacy_password"], auth=user["auth_type"],
                             use_aes=user["use_aes"])
        if self.snmp_traps:
            for trap in self.snmp_traps:
                CommSnmpTrap(parent_mo_or_dn=mo_comm_snmp, hostname=trap["hostname"], community=trap["community"],
                             port=trap["port"], version=trap["version"], notification_type=trap["notification_type"],
                             v3_privilege=trap["v3privilege"])

        self._handle.add_mo(mo_comm_snmp, modify_present=True)

        if commit:
            if self.commit() != True:
                return False
        return True


class UcsCentralSyslog(UcsCentralConfigObject):
    _CONFIG_NAME = "Syslog"
    _UCS_SDK_OBJECT_NAME = "commSyslog"

    def __init__(self, parent=None, json_content=None, comm_syslog=None):
        UcsCentralConfigObject.__init__(self, parent=parent)
        self.local_destinations = []
        self.local_sources = []
        self.remote_destinations = []

        if comm_syslog:
            mo = comm_syslog.dn
        else:
            mo = "org-root/deviceprofile-default/syslog"

        if self._config.load_from == "live":
            # Local sources
            if "commSyslogSource" in self._config.sdk_objects:
                comm_syslog_source_list = [comm_syslog_source for comm_syslog_source
                                           in self._config.sdk_objects["commSyslogSource"]
                                           if mo + "/source" in comm_syslog_source.dn]
                if len(comm_syslog_source_list) == 1:
                    comm_syslog = comm_syslog_source_list[0]
                    self.local_sources.append({"faults": comm_syslog.faults,
                                               "audits": comm_syslog.audits,
                                               "events": comm_syslog.events})

            # Local destinations
            if "commSyslogConsole" in self._config.sdk_objects:
                comm_syslog_console_list = [comm_syslog_console for comm_syslog_console
                                            in self._config.sdk_objects["commSyslogConsole"]
                                            if mo + "/console" in comm_syslog_console.dn]
                if len(comm_syslog_console_list) == 1:
                    comm_syslog = comm_syslog_console_list[0]
                    self.local_destinations.append({"console": [{"admin_state": comm_syslog.admin_state,
                                                                 "level": comm_syslog.severity}]})

            if "commSyslogMonitor" in self._config.sdk_objects:
                comm_syslog_monitor_list = [comm_syslog_monitor for comm_syslog_monitor
                                            in self._config.sdk_objects["commSyslogMonitor"]
                                            if mo + "/monitor" in comm_syslog_monitor.dn]
                if len(comm_syslog_monitor_list) == 1:
                    comm_syslog = comm_syslog_monitor_list[0]
                    self.local_destinations.append({"monitor": [{"admin_state": comm_syslog.admin_state,
                                                                 "level": comm_syslog.severity}]})

            if "commSyslogFile" in self._config.sdk_objects:
                comm_syslog_file_list = [comm_syslog_file for comm_syslog_file
                                         in self._config.sdk_objects["commSyslogFile"]
                                         if mo + "/file" in comm_syslog_file.dn]
                if len(comm_syslog_file_list) == 1:
                    comm_syslog = comm_syslog_file_list[0]
                    self.local_destinations.append({"file": [{"admin_state": comm_syslog.admin_state,
                                                              "level": comm_syslog.severity,
                                                              "name": comm_syslog.name,
                                                              "size": comm_syslog.size}]})

            # Remote destinations
            if "commSyslogClient" in self._config.sdk_objects:
                comm_syslog_client_list = [comm_syslog_client for comm_syslog_client
                                           in self._config.sdk_objects["commSyslogClient"]
                                           if mo + "/client-primary" in comm_syslog_client.dn]
                if len(comm_syslog_client_list) == 1:
                    comm_syslog = comm_syslog_client_list[0]
                    self.remote_destinations.append({"primary_server": [{"admin_state": comm_syslog.admin_state,
                                                                         "level": comm_syslog.severity,
                                                                         "hostname": comm_syslog.hostname,
                                                                         "facility": comm_syslog.forwarding_facility}]})

            if "commSyslogClient" in self._config.sdk_objects:
                comm_syslog_client_list = [comm_syslog_client for comm_syslog_client
                                           in self._config.sdk_objects["commSyslogClient"]
                                           if mo + "/client-secondary" in comm_syslog_client.dn]
                if len(comm_syslog_client_list) == 1:
                    comm_syslog = comm_syslog_client_list[0]
                    self.remote_destinations.append({"secondary_server": [{"admin_state": comm_syslog.admin_state,
                                                                           "level": comm_syslog.severity,
                                                                           "hostname": comm_syslog.hostname,
                                                                           "facility": comm_syslog.forwarding_facility
                                                                           }]})

            if "commSyslogClient" in self._config.sdk_objects:
                comm_syslog_client_list = [comm_syslog_client for comm_syslog_client
                                           in self._config.sdk_objects["commSyslogClient"]
                                           if mo + "/client-tertiary" in comm_syslog_client.dn]
                if len(comm_syslog_client_list) == 1:
                    comm_syslog = comm_syslog_client_list[0]
                    self.remote_destinations.append({"tertiary_server": [{"admin_state": comm_syslog.admin_state,
                                                                          "level": comm_syslog.severity,
                                                                          "hostname": comm_syslog.hostname,
                                                                          "facility": comm_syslog.forwarding_facility
                                                                          }]})

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

                for element in self.local_destinations:
                    for value in ["console", "monitor", "file"]:
                        if value not in element:
                            element[value] = None

                for element in self.remote_destinations:
                    for value in ["primary_server", "secondary_server", "tertiary_server"]:
                        if value not in element:
                            element[value] = None

                for element in self.local_sources:
                    for value in ["faults", "audits", "events"]:
                        if value not in element:
                            element[value] = None

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration")
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration" +
                                ", waiting for a commit")

        parent_obj = self._parent
        if parent_obj.__class__.__name__ in ["UcsCentralDomainGroup"]:
            dg_list = []
            while parent_obj.__class__.__name__ in ["UcsCentralDomainGroup"]:
                dg_list.append(parent_obj.name)
                parent_obj = parent_obj._parent
            dg_list.reverse()
            parent_mo = ""
            for dg in dg_list:
                parent_mo += "domaingroup-" + dg + "/"
            parent_mo = parent_mo[:-1]  # We remove the last "/" at the end of the mo
        else:
            parent_mo = "org-root/deviceprofile-default/syslog"

        # In case we are in a Domain Group, the parent commSyslog object must first be created if it does not exist
        if "domaingroup-" in parent_mo:
            mo_comm_syslog = CommSyslog(parent_mo_or_dn=parent_mo)
            self._handle.add_mo(mo_comm_syslog, modify_present=True)
            parent_mo = mo_comm_syslog

        # Local destinations
        for local_dest in self.local_destinations:
            if "console" in local_dest:
                if local_dest["console"]:
                    mo_comm_syslog_console = CommSyslogConsole(parent_mo_or_dn=parent_mo,
                                                               admin_state=local_dest["console"][0]["admin_state"],
                                                               severity=local_dest["console"][0]["level"])
                    self._handle.add_mo(mo_comm_syslog_console, modify_present=True)

            if "monitor" in local_dest:
                if local_dest["monitor"]:
                    mo_comm_syslog_monitor = CommSyslogMonitor(parent_mo_or_dn=parent_mo,
                                                               admin_state=local_dest["monitor"][0]["admin_state"],
                                                               severity=local_dest["monitor"][0]["level"])
                    self._handle.add_mo(mo_comm_syslog_monitor, modify_present=True)

            if "file" in local_dest:
                if local_dest["file"]:
                    mo_comm_syslog_file = CommSyslogFile(parent_mo_or_dn=parent_mo,
                                                         admin_state=local_dest["file"][0]["admin_state"],
                                                         severity=local_dest["file"][0]["level"],
                                                         name=local_dest["file"][0]["name"],
                                                         size=local_dest["file"][0]["size"])
                    self._handle.add_mo(mo_comm_syslog_file, modify_present=True)

        # Remote destinations
        for remote_dest in self.remote_destinations:
            if "primary_server" in remote_dest:
                if remote_dest["primary_server"]:
                    mo_comm_syslog_client = \
                        CommSyslogClient(parent_mo_or_dn=parent_mo, name="primary",
                                         admin_state=remote_dest["primary_server"][0]["admin_state"],
                                         severity=remote_dest["primary_server"][0]["level"],
                                         forwarding_facility=remote_dest["primary_server"][0]["facility"],
                                         hostname=remote_dest["primary_server"][0]["hostname"])
                    self._handle.add_mo(mo_comm_syslog_client, modify_present=True)

            if "secondary_server" in remote_dest:
                if remote_dest["secondary_server"]:
                    mo_comm_syslog_client = \
                        CommSyslogClient(parent_mo_or_dn=parent_mo, name="secondary",
                                         admin_state=remote_dest["secondary_server"][0]["admin_state"],
                                         severity=remote_dest["secondary_server"][0]["level"],
                                         forwarding_facility=remote_dest["secondary_server"][0]["facility"],
                                         hostname=remote_dest["secondary_server"][0]["hostname"])
                    self._handle.add_mo(mo_comm_syslog_client, modify_present=True)

            if "tertiary_server" in remote_dest:
                if remote_dest["tertiary_server"]:
                    mo_comm_syslog_client = \
                        CommSyslogClient(parent_mo_or_dn=parent_mo, name="tertiary",
                                         admin_state=remote_dest["tertiary_server"][0]["admin_state"],
                                         severity=remote_dest["tertiary_server"][0]["level"],
                                         forwarding_facility=remote_dest["tertiary_server"][0]["facility"],
                                         hostname=remote_dest["tertiary_server"][0]["hostname"])
                    self._handle.add_mo(mo_comm_syslog_client, modify_present=True)

        # Local sources
        for local_source in self.local_sources:
            faults = None
            audits = None
            events = None
            if "faults" in local_source:
                faults = local_source["faults"]
            if "audits" in local_source:
                audits = local_source["audits"]
            if "events" in local_source:
                events = local_source["events"]

            mo_comm_syslog_source = CommSyslogSource(parent_mo_or_dn=parent_mo, faults=faults, audits=audits,
                                                     events=events)
            self._handle.add_mo(mo_comm_syslog_source, modify_present=True)

        if commit:
            if self.commit() != True:
                return False
        return True


class UcsCentralSystem(UcsCentralConfigObject):
    _CONFIG_NAME = "System Information"
    _UCS_SDK_OBJECT_NAME = "topSystem"

    def __init__(self, parent=None, json_content=None):
        UcsCentralConfigObject.__init__(self, parent=parent)
        self.descr = None
        self.name = None
        self.mode = None

        if self._config.load_from == "live":
            top_system = None
            if "topSystem" in self._config.sdk_objects:
                if len(self._config.sdk_objects["topSystem"]) == 1:
                    top_system = self._config.sdk_objects["topSystem"][0]

            if top_system is not None:
                self.name = top_system.name
                self.mode = top_system.mode
                self.descr = top_system.descr

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration")
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration" +
                                ", waiting for a commit")

        if self.mode == "cluster":
            self.logger(level="warning", message="Setting UCS Central in cluster mode is not supported by EasyUCS!")

        mo_top_system = TopSystem(name=self.name, descr=self.descr)
        self._handle.add_mo(mo=mo_top_system, modify_present=True)

        if commit:
            if self.commit() != True:
                return False
        return True
