# coding: utf-8
# !/usr/bin/env python

""" domain_groups.py: Easy UCS Central Domain Groups objects """
from easyucs import __author__, __copyright__, __version__, __status__

import copy

from easyucs.config.object import GenericUcsConfigObject, UcsCentralConfigObject
from easyucs.config.ucs.ucsc.orgs import UcsCentralIpPool

from easyucs import common

from ucscsdk.mometa.org.OrgDomainGroup import OrgDomainGroup
from ucscsdk.mometa.fabric.FabricVlan import FabricVlan
from ucscsdk.mometa.fabric.FabricVlanReq import FabricVlanReq
from ucscsdk.mometa.fabric.FabricNetGroup import FabricNetGroup
from ucscsdk.mometa.fabric.FabricNetGroupReq import FabricNetGroupReq
from ucscsdk.mometa.fabric.FabricPooledVlan import FabricPooledVlan

from ucscsdk.ucscexception import UcscException


class UcsCentralDomainGroup(UcsCentralConfigObject):
    _CONFIG_NAME = "Domain Group"
    _UCS_SDK_OBJECT_NAME = "orgDomainGroup"

    def __init__(self, parent=None, json_content=None, org_domain_group=None):
        UcsCentralConfigObject.__init__(self, parent=parent)
        self.descr = None
        self.name = None

        if self._config.load_from == "live":
            if org_domain_group is not None:
                self._dn = org_domain_group.dn
                self.name = org_domain_group.name
                self.descr = org_domain_group.descr

        elif self._config.load_from == "file":
            if json_content is not None:
                if self.get_attributes_from_json(json_content=json_content):
                    if hasattr(self._parent, '_dn'):
                        self._dn = self._parent._dn + "/domaingroup-" + str(self.name)
                    else:
                        self._dn = "domaingroup-" + str(self.name)
                else:
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.domain_groups = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralDomainGroup,
                                      name_to_fetch="domain_groups")
        self.vlans = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralVlan,
                                      name_to_fetch="vlans")
        self.appliance_vlans = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralApplianceVlan,
                                      name_to_fetch="appliance_vlans")
        self.vlan_groups = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralVlanGroup,
                                      name_to_fetch="vlan_groups")
        self.ip_pools = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralIpPool,
                                      name_to_fetch="ip_pools")

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + str(self.name))
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + str(self.name) +
                                ", waiting for a commit")

        parent_mo = ""
        if hasattr(self._parent, '_dn'):
            parent_mo = self._parent._dn

        mo_org_domain_group = OrgDomainGroup(parent_mo_or_dn=parent_mo, name=self.name, descr=self.descr)

        self._handle.add_mo(mo=mo_org_domain_group, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False

        # We push all subconfig elements, in a specific optimized order to reduce number of reboots
        objects_to_push_in_order = ['vlan_groups', 'ip_pools', 'domain_groups']

        # The VLANs and Appliance VLANs are not pushed with the rest
        vlan_list = None
        if self.vlans and self.appliance_vlans:
            vlan_list = self.vlans + self.appliance_vlans
        elif self.vlans:
            vlan_list = self.vlans
        elif self.appliance_vlans:
            vlan_list = self.appliance_vlans

        if vlan_list:
            for vlan in vlan_list:
                # Handling range of VLAN
                if vlan.prefix:
                    start = int(vlan.id_from)
                    stop = int(vlan.id_to)
                    for i in range(start, stop + 1):
                        vlan_temp = copy.deepcopy(vlan)
                        vlan_temp.id = str(i)
                        vlan_temp.name = vlan_temp.prefix + vlan_temp.id
                        vlan_temp.push_object()
                else:
                    vlan.push_object()

        for config_object in objects_to_push_in_order:
            if getattr(self, config_object) is not None:
                if getattr(self, config_object).__class__.__name__ == "list":
                    for subobject in getattr(self, config_object):
                        subobject.push_object()

        return True

    def _get_generic_element(self, json_content, object_class, name_to_fetch):
        if self._config.load_from == "live":
            list_of_obj = self._config.get_config_objects_under_dn(dn=self._dn, object_class=object_class, parent=self)
            return list_of_obj
        elif self._config.load_from == "file" and json_content is not None:
            if name_to_fetch in json_content:
                return [object_class(self, generic, None) for generic in json_content[name_to_fetch]]
        else:
            return []


class UcsCentralVlan(UcsCentralConfigObject):
    _CONFIG_NAME = "VLAN"
    _UCS_SDK_OBJECT_NAME = "fabricVlan"

    def __init__(self, parent=None, json_content=None, fabric_vlan=None):
        UcsCentralConfigObject.__init__(self, parent=parent)
        self.id = None
        self.name = None
        self.sharing_type = None
        self.org_permissions = []
        self.multicast_policy_name = None
        self.primary_vlan_name = None

        # Range purpose
        self.id_from = None
        self.id_to = None
        self.prefix = None

        if self._config.load_from == "live":
            if fabric_vlan is not None:
                self.id = fabric_vlan.id
                self.name = fabric_vlan.name

                if fabric_vlan.mcast_policy_name != "":
                    self.multicast_policy_name = fabric_vlan.mcast_policy_name
                if fabric_vlan.sharing != "none":
                    self.sharing_type = fabric_vlan.sharing
                    if self.sharing_type in ["community", "isolated"]:
                        self.primary_vlan_name = fabric_vlan.pub_nw_name

                if "fabricVlanReq" in self._config.sdk_objects:
                    for vlan_req in self._config.sdk_objects["fabricVlanReq"]:
                        if vlan_req.name == self.name:
                            org_dn = vlan_req.dn.split("/vlan-req-")[0]
                            self.org_permissions.append(org_dn)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + self.name +
                                ' (' + self.id + ')')
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + self.name +
                                ' (' + self.id + ')' + ", waiting for a commit")

        if hasattr(self._parent, '_dn'):
            parent_mo = self._parent._dn
        else:
            self.logger(level="error",
                        message="Impossible to find the parent dn of " + self._CONFIG_NAME + " : " + str(self.name))
            return False

        mo_fabric_vlan = FabricVlan(parent_mo_or_dn=parent_mo + "/fabric/lan", sharing=self.sharing_type,
                                    name=self.name, id=self.id, mcast_policy_name=self.multicast_policy_name,
                                    pub_nw_name=self.primary_vlan_name)
        self._handle.add_mo(mo=mo_fabric_vlan, modify_present=True)

        if self.org_permissions:
            for organization in self.org_permissions:
                complete_org_path = ""
                for part in organization.split("/"):
                    if "org-" not in part:
                        complete_org_path += "org-"
                    complete_org_path += part + "/"
                complete_org_path = complete_org_path[:-1]  # Remove the trailing "/"
                if not complete_org_path.startswith("org-root"):
                    complete_org_path = "org-root/" + complete_org_path

                mo_fabric_vlan_req = FabricVlanReq(parent_mo_or_dn=complete_org_path, name=self.name)
                self._handle.add_mo(mo=mo_fabric_vlan_req, modify_present=True)

        if commit:
            if self.commit(detail=self.name + " (" + self.id + ")") != True:
                return False

        return True


class UcsCentralApplianceVlan(UcsCentralConfigObject):
    _CONFIG_NAME = "Appliance VLAN"
    _UCS_SDK_OBJECT_NAME = "fabricVlan"

    def __init__(self, parent=None, json_content=None, fabric_vlan=None):
        UcsCentralConfigObject.__init__(self, parent=parent)
        self.id = None
        self.name = None
        self.sharing_type = None
        self.org_permissions = []
        self.multicast_policy_name = None
        self.primary_vlan_name = None

        # Range purpose
        self.id_from = None
        self.id_to = None
        self.prefix = None

        if self._config.load_from == "live":
            if fabric_vlan is not None:
                self.id = fabric_vlan.id
                self.name = fabric_vlan.name

                if fabric_vlan.mcast_policy_name != "":
                    self.multicast_policy_name = fabric_vlan.mcast_policy_name
                if fabric_vlan.sharing != "none":
                    self.sharing_type = fabric_vlan.sharing
                    if self.sharing_type in ["community", "isolated"]:
                        self.primary_vlan_name = fabric_vlan.pub_nw_name

                if "fabricVlanReq" in self._config.sdk_objects:
                    for vlan_req in self._config.sdk_objects["fabricVlanReq"]:
                        if vlan_req.name == self.name:
                            org_dn = vlan_req.dn.split("/vlan-req-")[0]
                            self.org_permissions.append(org_dn)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + self.name +
                                ' (' + self.id + ')')
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + self.name +
                                ' (' + self.id + ')' + ", waiting for a commit")

        if hasattr(self._parent, '_dn'):
            parent_mo = self._parent._dn
        else:
            self.logger(level="error",
                        message="Impossible to find the parent dn of " + self._CONFIG_NAME + " : " + str(self.name))
            return False

        mo_fabric_vlan = FabricVlan(parent_mo_or_dn=parent_mo + "/fabric/eth-estc", sharing=self.sharing_type,
                                    name=self.name, id=self.id, mcast_policy_name=self.multicast_policy_name,
                                    pub_nw_name=self.primary_vlan_name)
        self._handle.add_mo(mo=mo_fabric_vlan, modify_present=True)

        if self.org_permissions:
            for organization in self.org_permissions:
                complete_org_path = ""
                for part in organization.split("/"):
                    if "org-" not in part:
                        complete_org_path += "org-"
                    complete_org_path += part + "/"
                complete_org_path = complete_org_path[:-1]  # Remove the trailing "/"
                if not complete_org_path.startswith("org-root"):
                    complete_org_path = "org-root/" + complete_org_path

                mo_fabric_vlan_req = FabricVlanReq(parent_mo_or_dn=complete_org_path, name=self.name)
                self._handle.add_mo(mo=mo_fabric_vlan_req, modify_present=True)

        if commit:
            if self.commit(detail=self.name + " (" + self.id + ")") != True:
                return False

        return True


class UcsCentralVlanGroup(UcsCentralConfigObject):
    _CONFIG_NAME = "VLAN Group"
    _UCS_SDK_OBJECT_NAME = "fabricNetGroup"

    def __init__(self, parent=None, json_content=None, fabric_net_group=None):
        UcsCentralConfigObject.__init__(self, parent=parent)
        self.name = None
        self.vlans = []
        self.native_vlan = None
        self.org_permissions = []

        if self._config.load_from == "live":
            if fabric_net_group is not None:
                self.name = fabric_net_group.name
                self.native_vlan = fabric_net_group.native_net

                if "fabricPooledVlan" in self._config.sdk_objects:
                    vlans = [vlan for vlan in self._config.sdk_objects["fabricPooledVlan"]
                             if "fabric/lan/net-group-" + self.name in vlan.dn]
                    if vlans:
                        for vlan in vlans:
                            if vlan.name != self.native_vlan:
                                self.vlans.append(vlan.name)

                if "fabricNetGroupReq" in self._config.sdk_objects:
                    for ng_req in self._config.sdk_objects["fabricNetGroupReq"]:
                        if ng_req.name == self.name:
                            org_dn = ng_req.dn.split("/ngreq-")[0]
                            self.org_permissions.append(org_dn)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + str(self.name))
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + str(self.name) +
                                ", waiting for a commit")

        if hasattr(self._parent, '_dn'):
            parent_mo = self._parent._dn
        else:
            self.logger(level="error",
                        message="Impossible to find the parent dn of " + self._CONFIG_NAME + " : " + str(self.name))
            return False
        mo_fabric_net_group = FabricNetGroup(parent_mo_or_dn=parent_mo + "/fabric/lan",
                                             native_net=self.native_vlan,
                                             name=self.name)
        self._handle.add_mo(mo=mo_fabric_net_group, modify_present=True)

        if commit:
            if self.commit(detail=self.name) != True:
                return False

        if self.vlans:
            for vlan in self.vlans:
                FabricPooledVlan(parent_mo_or_dn=mo_fabric_net_group, name=vlan)
                self._handle.add_mo(mo=mo_fabric_net_group, modify_present=True)

                if commit:
                    self.commit(detail="vlan: " + vlan)

        if self.native_vlan:
            FabricPooledVlan(parent_mo_or_dn=mo_fabric_net_group, name=self.native_vlan)
            self._handle.add_mo(mo=mo_fabric_net_group, modify_present=True)

            if commit:
                self.commit(detail="native_vlan: " + self.native_vlan)

        if self.org_permissions:
            for organization in self.org_permissions:
                complete_org_path = ""
                for part in organization.split("/"):
                    if "org-" not in part:
                        complete_org_path += "org-"
                    complete_org_path += part + "/"
                complete_org_path = complete_org_path[:-1]  # Remove the trailing "/"
                if not complete_org_path.startswith("org-root"):
                    complete_org_path = "org-root/" + complete_org_path

                mo_fabric_ng_req = FabricNetGroupReq(parent_mo_or_dn=complete_org_path, name=self.name)
                self._handle.add_mo(mo=mo_fabric_ng_req, modify_present=True)

                if commit:
                    self.commit(detail="Org permission: " + organization)

        return True
