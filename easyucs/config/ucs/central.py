# coding: utf-8
# !/usr/bin/env python

""" central.py: Easy UCS Deployment Tool """
from easyucs import __author__, __copyright__,  __version__, __status__

import copy
import sys
import time
import urllib

from netaddr import EUI, IPAddress

from easyucs.config.object import GenericUcsConfigObject, UcsCentralConfigObject

from easyucs import common

from ucscsdk.mometa.org.OrgOrg import OrgOrg
from ucscsdk.mometa.org.OrgDomainGroup import OrgDomainGroup
from ucscsdk.mometa.macpool.MacpoolPool import MacpoolPool
from ucscsdk.mometa.macpool.MacpoolBlock import MacpoolBlock
from ucscsdk.mometa.fcpool.FcpoolInitiators import FcpoolInitiators
from ucscsdk.mometa.fcpool.FcpoolBlock import FcpoolBlock
from ucscsdk.mometa.uuidpool.UuidpoolPool import UuidpoolPool
from ucscsdk.mometa.uuidpool.UuidpoolBlock import UuidpoolBlock
from ucscsdk.mometa.fabric.FabricVlan import FabricVlan
from ucscsdk.mometa.fabric.FabricVlanReq import FabricVlanReq
from ucscsdk.mometa.fabric.FabricNetGroup import FabricNetGroup
from ucscsdk.mometa.fabric.FabricNetGroupReq import FabricNetGroupReq
from ucscsdk.mometa.fabric.FabricPooledVlan import FabricPooledVlan
from ucscsdk.mometa.ippool.IppoolPool import IppoolPool
from ucscsdk.mometa.ippool.IppoolBlock import IppoolBlock
from ucscsdk.mometa.ippool.IppoolIpV6Block import IppoolIpV6Block

from ucscsdk.ucscexception import UcscException


class UcsCentralOrg(UcsCentralConfigObject):
    _CONFIG_NAME = "Organization"
    _UCS_SDK_OBJECT_NAME = "orgOrg"

    def __init__(self, parent=None, json_content=None, org_org=None):
        UcsCentralConfigObject.__init__(self, parent=parent)
        self.descr = None
        self.name = None

        if self._config.load_from == "live":
            if org_org is not None:
                self._dn = org_org.dn
                self.name = org_org.name
                self.descr = org_org.descr

        elif self._config.load_from == "file":
            if json_content is not None:
                if self.get_attributes_from_json(json_content=json_content):
                    if hasattr(self._parent, '_dn'):
                        self._dn = self._parent._dn + "/org-" + str(self.name)
                    else:
                        self._dn = "org-" + str(self.name)
                else:
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.orgs = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralOrg, name_to_fetch="orgs")

        self.mac_pools = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralMacPool,
                                      name_to_fetch="mac_pools")
        self.uuid_pools = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralUuidPool,
                                      name_to_fetch="uuid_pools")
        self.wwnn_pools = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralWwnnPool,
                                      name_to_fetch="wwnn_pools")
        self.wwpn_pools = \
            self._get_generic_element(json_content=json_content, object_class=UcsCentralWwpnPool,
                                      name_to_fetch="wwpn_pools")
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

        mo_org_org = OrgOrg(parent_mo_or_dn=parent_mo, name=self.name, descr=self.descr)

        self._handle.add_mo(mo=mo_org_org, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False

        # We push all subconfig elements, in a specific optimized order to reduce number of reboots
        # TODO: Verify order
        objects_to_push_in_order = ['mac_pools', 'orgs', 'uuid_pools', 'wwnn_pools', 'wwpn_pools', 'ip_pools']

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


class UcsCentralMacPool(UcsCentralConfigObject):
    _CONFIG_NAME = "MAC Pool"
    _UCS_SDK_OBJECT_NAME = "macpoolPool"

    def __init__(self, parent=None, json_content=None, macpool_pool=None):
        UcsCentralConfigObject.__init__(self, parent=parent)
        self.descr = None
        self.name = None
        self.mac_blocks = []

        if self._config.load_from == "live":
            if macpool_pool is not None:
                self.name = macpool_pool.name
                self.descr = macpool_pool.descr

                if "macpoolBlock" in self._parent._config.sdk_objects:
                    for pool_block in self._config.sdk_objects["macpoolBlock"]:
                        if self._parent._dn:
                            if self._parent._dn + "/mac-pool-" + self.name + "/block-" in pool_block.dn:
                                block = {}
                                block.update({"to": pool_block.to})
                                block.update({"from": pool_block.r_from})
                                block.update({"size": None})
                                block.update({"id_range_access_control": pool_block.qualifier})
                                self.mac_blocks.append(block)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

                for element in self.mac_blocks:
                    for value in ["to", "from", "size", "id_range_access_control"]:
                        if value not in element:
                            element[value] = None

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

        mo_macpool_pool = MacpoolPool(parent_mo_or_dn=parent_mo,
                                      descr=self.descr,
                                      name=self.name)
        if self.mac_blocks:
            for block in self.mac_blocks:
                if block["to"]:
                    MacpoolBlock(parent_mo_or_dn=mo_macpool_pool, to=block["to"],
                                 r_from=block["from"], qualifier=block["id_range_access_control"])
                elif block["size"]:
                    mac_pool_to = EUI(block["from"])
                    for i in range(int(block["size"])-1):
                        mac_pool_to = EUI(int(mac_pool_to)+1)
                    mac_pool_to = str(mac_pool_to).replace("-", ":")
                    MacpoolBlock(parent_mo_or_dn=mo_macpool_pool, to=mac_pool_to,
                                 r_from=block["from"], qualifier=block["id_range_access_control"])

        self._handle.add_mo(mo=mo_macpool_pool, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True


class UcsCentralUuidPool(UcsCentralConfigObject):
    _CONFIG_NAME = "UUID Pool"
    _UCS_SDK_OBJECT_NAME = "uuidpoolPool"

    def __init__(self, parent=None, json_content=None, uuidpool_pool=None):
        UcsCentralConfigObject.__init__(self, parent=parent)
        self.descr = None
        self.name = None
        self.prefix = None
        self.uuid_blocks = []

        if self._config.load_from == "live":
            if uuidpool_pool is not None:
                self.name = uuidpool_pool.name
                self.descr = uuidpool_pool.descr
                self.prefix = uuidpool_pool.prefix

                if "uuidpoolBlock" in self._parent._config.sdk_objects:
                    for pool_block in self._config.sdk_objects["uuidpoolBlock"]:
                        if self._parent._dn:
                            if self._parent._dn + "/uuid-pool-" + self.name + "/block-" in pool_block.dn:
                                block = {}
                                block.update({"to": pool_block.to})
                                block.update({"from": pool_block.r_from})
                                block.update({"size": None})
                                block.update({"id_range_access_control": pool_block.qualifier})
                                self.uuid_blocks.append(block)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

                for element in self.uuid_blocks:
                    for value in ["to", "from", "size", "id_range_access_control"]:
                        if value not in element:
                            element[value] = None

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

        # If the prefix is an empty string the SDK raise an error
        prefix = None
        if self.prefix:
            prefix = self.prefix
        mo_uuidpool_pool = UuidpoolPool(parent_mo_or_dn=parent_mo,
                                        descr=self.descr,
                                        name=self.name,
                                        prefix=prefix)
        self._handle.add_mo(mo=mo_uuidpool_pool, modify_present=True)

        if self.uuid_blocks:
            for block in self.uuid_blocks:
                if block["to"]:
                    UuidpoolBlock(parent_mo_or_dn=mo_uuidpool_pool, to=block["to"], r_from=block["from"],
                                  qualifier=block["id_range_access_control"])
                elif block["size"]:
                    # Convert from hexa to int
                    uuid_pool_to = int(block["from"].replace("-", ""), 16)
                    for i in range(int(block["size"])-1):
                        uuid_pool_to = uuid_pool_to + 1
                    # Convert to hexa
                    uuid_pool_to = hex(uuid_pool_to).split("0x")[1]
                    if len(uuid_pool_to) != 16:
                        # Add the missing 0 to get 16 letters in the string. We lost some 0 during the conversion
                        uuid_pool_to = "0" * (16-len(uuid_pool_to)) + uuid_pool_to
                    uuid_pool_to = uuid_pool_to[0:4] + "-" + uuid_pool_to[4:]

                    UuidpoolBlock(parent_mo_or_dn=mo_uuidpool_pool, to=uuid_pool_to, r_from=block["from"],
                                  qualifier=block["id_range_access_control"])

        self._handle.add_mo(mo=mo_uuidpool_pool, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False


class UcsCentralWwnnPool(UcsCentralConfigObject):
    _CONFIG_NAME = "WWNN Pool"
    _UCS_SDK_OBJECT_NAME = "fcpoolInitiators"

    def __init__(self, parent=None, json_content=None, wwnnpool_pool=None):
        UcsCentralConfigObject.__init__(self, parent=parent)
        self.descr = None
        self.name = None
        self.wwnn_blocks = []

        if self._config.load_from == "live":
            if wwnnpool_pool is not None:
                self.name = wwnnpool_pool.name
                self.descr = wwnnpool_pool.descr

                if "fcpoolBlock" in self._parent._config.sdk_objects:
                    for pool_block in self._config.sdk_objects["fcpoolBlock"]:
                        if self._parent._dn:
                            if self._parent._dn + "/wwn-pool-" + self.name + "/block-" in pool_block.dn:
                                block = {}
                                block.update({"to": pool_block.to})
                                block.update({"from": pool_block.r_from})
                                block.update({"size": None})
                                block.update({"id_range_access_control": pool_block.qualifier})
                                self.wwnn_blocks.append(block)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

                for element in self.wwnn_blocks:
                    for value in ["to",
                                  "from",
                                  "size",
                                  "id_range_access_control"
                                  ]:
                        if value not in element:
                            element[value] = None

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

        mo_fc_pool_init = FcpoolInitiators(parent_mo_or_dn=parent_mo,
                                           descr=self.descr,
                                           name=self.name,
                                           purpose="node-wwn-assignment"
                                           )
        if self.wwnn_blocks:
            for block in self.wwnn_blocks:
                if block["to"]:
                    FcpoolBlock(parent_mo_or_dn=mo_fc_pool_init, to=block["to"], r_from=block["from"],
                                qualifier=block["id_range_access_control"])
                elif block["size"]:
                    wwnn_pool_to = block["from"]
                    # Convert from hexa to int
                    wwnn_pool_to = int(wwnn_pool_to.replace(":", ""), 16)
                    for i in range(int(block["size"]) - 1):
                        wwnn_pool_to = wwnn_pool_to + 1
                    # Convert to hexa
                    wwnn_pool_to = hex(wwnn_pool_to).split("0x")[1]
                    if len(wwnn_pool_to) != 16:
                        # Add the missing 0 to get 16 letters in the string. We lost some 0 during the conversion
                        wwnn_pool_to = "0" * (16-len(wwnn_pool_to)) + wwnn_pool_to
                    wwnn_pool_to = wwnn_pool_to[0:2] + ":" + wwnn_pool_to[2:4] + ":" + wwnn_pool_to[4:6] + ":" + \
                                   wwnn_pool_to[6:8] + ":" + wwnn_pool_to[8:10] + ":" + wwnn_pool_to[10:12] + ":" + \
                                   wwnn_pool_to[12:14] + ":" + wwnn_pool_to[14:16]

                    FcpoolBlock(parent_mo_or_dn=mo_fc_pool_init, to=wwnn_pool_to,
                                r_from=block["from"], qualifier=block["id_range_access_control"])

        self._handle.add_mo(mo=mo_fc_pool_init, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False


class UcsCentralWwpnPool(UcsCentralConfigObject):
    _CONFIG_NAME = "WWPN Pool"
    _UCS_SDK_OBJECT_NAME = "fcpoolInitiators"

    def __init__(self, parent=None, json_content=None, wwpnpool_pool=None):
        UcsCentralConfigObject.__init__(self, parent=parent)
        self.descr = None
        self.name = None
        self.wwpn_blocks = []

        if self._config.load_from == "live":
            if wwpnpool_pool is not None:
                self.name = wwpnpool_pool.name
                self.descr = wwpnpool_pool.descr

                if "fcpoolBlock" in self._parent._config.sdk_objects:
                    for pool_block in self._config.sdk_objects["fcpoolBlock"]:
                        if self._parent._dn:
                            if self._parent._dn + "/wwn-pool-" + self.name + "/block-" in pool_block.dn:
                                block = {}
                                block.update({"to": pool_block.to})
                                block.update({"from": pool_block.r_from})
                                block.update({"size": None})
                                block.update({"id_range_access_control": pool_block.qualifier})
                                self.wwpn_blocks.append(block)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

                for element in self.wwpn_blocks:
                    for value in ["to",
                                  "from",
                                  "size",
                                  "id_range_access_control"
                                  ]:
                        if value not in element:
                            element[value] = None

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

        mo_fc_pool_init = FcpoolInitiators(parent_mo_or_dn=parent_mo,
                                           descr=self.descr,
                                           name=self.name,
                                           purpose="port-wwn-assignment"
                                           )
        if self.wwpn_blocks:
            for block in self.wwpn_blocks:
                if block["to"]:
                    FcpoolBlock(parent_mo_or_dn=mo_fc_pool_init, to=block["to"], r_from=block["from"],
                                qualifier=block["id_range_access_control"])
                elif block["size"]:
                    wwpn_pool_to = block["from"]
                    # Convert from hexa to int
                    wwpn_pool_to = int(wwpn_pool_to.replace(":", ""), 16)
                    for i in range(int(block["size"]) - 1):
                        wwpn_pool_to = wwpn_pool_to + 1
                    # Convert to hexa
                    wwpn_pool_to = hex(wwpn_pool_to).split("0x")[1]
                    if len(wwpn_pool_to) != 16:
                        # Add the missing 0 to get 16 letters in the string. We lost some 0 during the conversion
                        wwpn_pool_to = "0" * (16-len(wwpn_pool_to)) + wwpn_pool_to
                    wwpn_pool_to = wwpn_pool_to[0:2] + ":" + wwpn_pool_to[2:4] + ":" + wwpn_pool_to[4:6] + ":" + \
                                   wwpn_pool_to[6:8] + ":" + wwpn_pool_to[8:10] + ":" + wwpn_pool_to[10:12] + ":" + \
                                   wwpn_pool_to[12:14] + ":" + wwpn_pool_to[14:16]

                    FcpoolBlock(parent_mo_or_dn=mo_fc_pool_init, to=wwpn_pool_to,
                                r_from=block["from"], qualifier=block["id_range_access_control"])

        self._handle.add_mo(mo=mo_fc_pool_init, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False


class UcsCentralIpPool(UcsCentralConfigObject):
    _CONFIG_NAME = "IP Pool"
    _UCS_SDK_OBJECT_NAME = "ippoolPool"

    def __init__(self, parent=None, json_content=None, ippool_pool=None):
        UcsCentralConfigObject.__init__(self, parent=parent)
        self.descr = None
        self.name = None
        self.ip_blocks = []
        self.ipv6_blocks = []

        if self._config.load_from == "live":
            if ippool_pool is not None:
                self.name = ippool_pool.name
                self.descr = ippool_pool.descr

                if "ippoolBlock" in self._parent._config.sdk_objects:
                    for pool_block in self._config.sdk_objects["ippoolBlock"]:
                        if self._parent._dn:
                            if self._parent._dn + "/ip-pool-" + self.name + "/block-" in pool_block.dn:
                                block = {}
                                block.update({"gateway": pool_block.def_gw})
                                block.update({"primary_dns": pool_block.prim_dns})
                                block.update({"secondary_dns": pool_block.sec_dns})
                                block.update({"netmask": pool_block.subnet})
                                block.update({"to": pool_block.to})
                                block.update({"from": pool_block.r_from})
                                block.update({"scope": pool_block.scope})
                                block.update({"id_range_access_control": pool_block.qualifier})
                                block.update({"size": None})
                                self.ip_blocks.append(block)

                if "ippoolIpV6Block" in self._parent._config.sdk_objects:
                    for pool_block in self._config.sdk_objects["ippoolIpV6Block"]:
                        if self._parent._dn:
                            if self._parent._dn + "/ip-pool-" + self.name + "/v6block-" in pool_block.dn:
                                block = {}
                                block.update({"gateway": pool_block.def_gw})
                                block.update({"primary_dns": pool_block.prim_dns})
                                block.update({"secondary_dns": pool_block.sec_dns})
                                block.update({"prefix": pool_block.prefix})
                                block.update({"to": pool_block.to})
                                block.update({"from": pool_block.r_from})
                                block.update({"scope": pool_block.scope})
                                block.update({"id_range_access_control": pool_block.qualifier})
                                block.update({"size": None})
                                self.ipv6_blocks.append(block)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

                for element in self.ip_blocks:
                    for value in ["gateway", "primary_dns", "secondary_dns", "netmask", "to", "from", "size",
                                  "id_range_access_control", "scope"]:
                        if value not in element:
                            element[value] = None

                for element in self.ipv6_blocks:
                    for value in ["gateway", "primary_dns", "secondary_dns", "prefix", "to", "from", "size",
                                  "id_range_access_control", "scope"]:
                        if value not in element:
                            element[value] = None

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

        mo_ippool_pool = IppoolPool(parent_mo_or_dn=parent_mo,
                                    descr=self.descr,
                                    name=self.name)
        self._handle.add_mo(mo=mo_ippool_pool, modify_present=True)
        if commit:
            if self.commit() != True:
                return False

        if self.ip_blocks:
            for block in self.ip_blocks:
                mo_ip_pool_block = None
                if block["to"]:
                    mo_ip_pool_block = IppoolBlock(parent_mo_or_dn=mo_ippool_pool, to=block["to"], r_from=block["from"],
                                                   def_gw=block["gateway"], prim_dns=block["primary_dns"],
                                                   sec_dns=block["secondary_dns"], subnet=block["netmask"],
                                                   scope=block["scope"],
                                                   qualifier=block["id_range_access_control"])
                elif block["size"]:
                    ip_pool_to = block["from"]
                    for i in range(int(block["size"])-1):
                        ip_pool_to = IPAddress(ip_pool_to) + 1
                    block["to"] = str(ip_pool_to)
                    mo_ip_pool_block = IppoolBlock(parent_mo_or_dn=mo_ippool_pool, to=block["to"],
                                                   r_from=block["from"],
                                                   def_gw=block["gateway"], prim_dns=block["primary_dns"],
                                                   sec_dns=block["secondary_dns"], subnet=block["netmask"],
                                                   scope=block["scope"],
                                                   qualifier=block["id_range_access_control"])
                if mo_ip_pool_block:
                    self._handle.add_mo(mo=mo_ip_pool_block, modify_present=True)
                    if commit:
                        if self.commit() != True:
                            return False

        if self.ipv6_blocks:
            for block in self.ipv6_blocks:
                mo_ip_pool_block = None
                if block["to"]:
                    mo_ip_pool_block = IppoolIpV6Block(parent_mo_or_dn=mo_ippool_pool, to=block["to"],
                                                       r_from=block["from"], def_gw=block["gateway"],
                                                       prim_dns=block["primary_dns"], sec_dns=block["secondary_dns"],
                                                       prefix=block["prefix"])
                elif block["size"]:
                    ip_pool_to = block["from"]
                    for i in range(int(block["size"])-1):
                        ip_pool_to = IPAddress(ip_pool_to) + 1
                    block["to"] = str(ip_pool_to)
                    mo_ip_pool_block = IppoolIpV6Block(parent_mo_or_dn=mo_ippool_pool, to=block["to"],
                                                       r_from=block["from"], def_gw=block["gateway"],
                                                       prim_dns=block["primary_dns"], sec_dns=block["secondary_dns"],
                                                       prefix=block["prefix"])
                if mo_ip_pool_block:
                    self._handle.add_mo(mo=mo_ip_pool_block, modify_present=True)
                    if commit:
                        if self.commit() != True:
                            return False

        return True


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
        # TODO: Verify order
        objects_to_push_in_order = ['domain_groups', 'vlan_groups', 'ip_pools']

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
