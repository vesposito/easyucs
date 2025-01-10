# coding: utf-8
# !/usr/bin/env python

""" pools.py: Easy UCS Central Pools objects """

import hashlib

from netaddr import EUI, IPAddress
from ucscsdk.mometa.fcpool.FcpoolBlock import FcpoolBlock
from ucscsdk.mometa.fcpool.FcpoolInitiators import FcpoolInitiators
from ucscsdk.mometa.ippool.IppoolBlock import IppoolBlock
from ucscsdk.mometa.ippool.IppoolIpV6Block import IppoolIpV6Block
from ucscsdk.mometa.ippool.IppoolPool import IppoolPool
from ucscsdk.mometa.iqnpool.IqnpoolBlock import IqnpoolBlock
from ucscsdk.mometa.iqnpool.IqnpoolPool import IqnpoolPool
from ucscsdk.mometa.macpool.MacpoolBlock import MacpoolBlock
from ucscsdk.mometa.macpool.MacpoolPool import MacpoolPool
from ucscsdk.mometa.uuidpool.UuidpoolBlock import UuidpoolBlock
from ucscsdk.mometa.uuidpool.UuidpoolPool import UuidpoolPool
from ucscsdk.mometa.compute.ComputePool import ComputePool
from ucscsdk.mometa.compute.ComputePooledRackUnit import ComputePooledRackUnit
from ucscsdk.mometa.compute.ComputePooledSlot import ComputePooledSlot
from ucscsdk.mometa.compute.ComputePoolingPolicy import ComputePoolingPolicy

from config.ucs.object import UcsCentralConfigObject


class UcsCentralIpPool(UcsCentralConfigObject):
    _CONFIG_NAME = "IP Pool"
    _CONFIG_SECTION_NAME = "ip_pools"
    _UCS_SDK_OBJECT_NAME = "ippoolPool"

    def __init__(self, parent=None, json_content=None, ippool_pool=None):
        UcsCentralConfigObject.__init__(self, parent=parent, ucs_sdk_object=ippool_pool)
        self.descr = None
        self.name = None
        self.ip_blocks = []
        self.ipv6_blocks = []
        self.operational_state = {}

        if self._config.load_from == "live":
            if ippool_pool is not None:
                self.name = ippool_pool.name
                self.descr = ippool_pool.descr
                self.operational_state = {
                    "size": ippool_pool.size,
                    "assigned": ippool_pool.assigned
                }

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

        self.clean_object()

    def clean_object(self):
        UcsCentralConfigObject.clean_object(self)
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

        for value in ["assigned", "size"]:
            if value not in self.operational_state:
                self.operational_state[value] = None

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

        mo_ippool_pool = IppoolPool(parent_mo_or_dn=parent_mo, descr=self.descr, name=self.name)
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
                                                   scope=block["scope"], qualifier=block["id_range_access_control"])
                elif block["size"]:
                    ip_pool_to = block["from"]
                    for i in range(int(block["size"]) - 1):
                        ip_pool_to = IPAddress(ip_pool_to) + 1
                    block["to"] = str(ip_pool_to)
                    mo_ip_pool_block = IppoolBlock(parent_mo_or_dn=mo_ippool_pool, to=block["to"], r_from=block["from"],
                                                   def_gw=block["gateway"], prim_dns=block["primary_dns"],
                                                   sec_dns=block["secondary_dns"], subnet=block["netmask"],
                                                   scope=block["scope"], qualifier=block["id_range_access_control"])
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
                    for i in range(int(block["size"]) - 1):
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


class UcsCentralIqnPool(UcsCentralConfigObject):
    _CONFIG_NAME = "IQN Pool"
    _CONFIG_SECTION_NAME = "iqn_pools"
    _UCS_SDK_OBJECT_NAME = "iqnpoolPool"

    def __init__(self, parent=None, json_content=None, iqnpool_pool=None):
        UcsCentralConfigObject.__init__(self, parent=parent, ucs_sdk_object=iqnpool_pool)
        self.descr = None
        self.name = None
        self.prefix = None
        self.iqn_blocks = []
        self.operational_state = {}

        if self._config.load_from == "live":
            if iqnpool_pool is not None:
                self.name = iqnpool_pool.name
                self.descr = iqnpool_pool.descr
                self.prefix = iqnpool_pool.prefix
                self.operational_state = {
                    "size": iqnpool_pool.size,
                    "assigned": iqnpool_pool.assigned
                }

                if "iqnpoolBlock" in self._parent._config.sdk_objects:
                    for pool_block in self._config.sdk_objects["iqnpoolBlock"]:
                        if self._parent._dn:
                            if self._parent._dn + "/iqn-pool-" + self.name + "/iqn-suffix-" in pool_block.dn:
                                block = {}
                                block.update({"to": pool_block.to})
                                block.update({"from": pool_block.r_from})
                                block.update({"size": None})
                                block.update({"suffix": pool_block.suffix})
                                block.update({"id_range_access_control": pool_block.qualifier})
                                self.iqn_blocks.append(block)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def clean_object(self):
        UcsCentralConfigObject.clean_object(self)

        for element in self.iqn_blocks:
            for value in ["to", "from", "size", "suffix", "id_range_access_control"]:
                if value not in element:
                    element[value] = None

        for value in ["assigned", "size"]:
            if value not in self.operational_state:
                self.operational_state[value] = None

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

        mo_iqn_pool_init = IqnpoolPool(parent_mo_or_dn=parent_mo, descr=self.descr,
                                       name=self.name, prefix=self.prefix)
        if self.iqn_blocks:
            for block in self.iqn_blocks:
                if block["to"]:
                    IqnpoolBlock(parent_mo_or_dn=mo_iqn_pool_init, to=block["to"], r_from=block["from"],
                                 suffix=block["suffix"], qualifier=block["id_range_access_control"])
                elif block["size"]:
                    iqn_pool_to = int(block["from"])
                    for i in range(int(block["size"]) - 1):
                        iqn_pool_to = iqn_pool_to + 1
                    iqn_pool_to = str(iqn_pool_to)
                    IqnpoolBlock(parent_mo_or_dn=mo_iqn_pool_init, to=iqn_pool_to, r_from=block["from"],
                                 suffix=block["suffix"], qualifier=block["id_range_access_control"])

        self._handle.add_mo(mo=mo_iqn_pool_init, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False


class UcsCentralMacPool(UcsCentralConfigObject):
    _CONFIG_NAME = "MAC Pool"
    _CONFIG_SECTION_NAME = "mac_pools"
    _UCS_SDK_OBJECT_NAME = "macpoolPool"

    def __init__(self, parent=None, json_content=None, macpool_pool=None):
        UcsCentralConfigObject.__init__(self, parent=parent, ucs_sdk_object=macpool_pool)
        self.descr = None
        self.name = None
        self.mac_blocks = []
        self.operational_state = {}

        if self._config.load_from == "live":
            if macpool_pool is not None:
                self.name = macpool_pool.name
                self.descr = macpool_pool.descr
                self.operational_state = {
                    "size": macpool_pool.size,
                    "assigned": macpool_pool.assigned
                }

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

        self.clean_object()

    def clean_object(self):
        UcsCentralConfigObject.clean_object(self)

        for element in self.mac_blocks:
            for value in ["to", "from", "size", "id_range_access_control"]:
                if value not in element:
                    element[value] = None

        for value in ["assigned", "size"]:
            if value not in self.operational_state:
                self.operational_state[value] = None

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
                    for i in range(int(block["size"]) - 1):
                        mac_pool_to = EUI(int(mac_pool_to) + 1)
                    mac_pool_to = str(mac_pool_to).replace("-", ":")
                    MacpoolBlock(parent_mo_or_dn=mo_macpool_pool, to=mac_pool_to,
                                 r_from=block["from"], qualifier=block["id_range_access_control"])

        self._handle.add_mo(mo=mo_macpool_pool, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True


class UcsCentralServerPool(UcsCentralConfigObject):
    _CONFIG_NAME = "Server Pool"
    _CONFIG_SECTION_NAME = "server_pools"
    _UCS_SDK_OBJECT_NAME = "computePool"

    def __init__(self, parent=None, json_content=None, compute_pool=None):
        UcsCentralConfigObject.__init__(self, parent=parent, ucs_sdk_object=compute_pool)
        self.descr = None
        self.name = None
        self.servers = []
        self.systemId = None
        self.qualification_policies = []

        if self._config.load_from == "live":
            if compute_pool is not None:
                self.name = compute_pool.name
                self.descr = compute_pool.descr
                if "computePoolingPolicy" in self._config.sdk_objects:
                    for compute_pooling_policy in self._config.sdk_objects["computePoolingPolicy"]:
                        if self._parent._dn + "/compute-pool-" + self.name in compute_pooling_policy.pool_dn:
                            self.qualification_policies.append(compute_pooling_policy.qualifier)

                if "computePooledSlot" in self._parent._config.sdk_objects:
                    for pool_block in self._config.sdk_objects["computePooledSlot"]:
                        if self._parent._dn:
                            # We avoid adding blade servers that are automatically added by a qualification policy
                            if pool_block.owner != "policy":
                                if self._parent._dn + "/compute-pool-" + self.name + "/" in pool_block.dn:
                                    block = {}
                                    block.update({"chassis_id": pool_block.chassis_id})
                                    block.update({"slot_id": pool_block.slot_id})
                                    block.update({"system_id": pool_block.system_id})
                                    self.servers.append(block)

                if "computePooledRackUnit" in self._parent._config.sdk_objects:
                    for pool_block in self._config.sdk_objects["computePooledRackUnit"]:
                        if self._parent._dn:
                            # We avoid adding rack servers that are automatically added by a qualification policy
                            if pool_block.owner != "policy":
                                if self._parent._dn + "/compute-pool-" + self.name + "/" in pool_block.dn:
                                    block = {}
                                    block.update({"rack_id": pool_block.id})
                                    block.update({"system_id": pool_block.system_id})
                                    self.servers.append(block)

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
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " +
                                self.name + ", waiting for a commit")

        if hasattr(self._parent, '_dn'):
            parent_mo = self._parent._dn
        else:
            self.logger(level="error",
                        message="Impossible to find the parent dn of " + self._CONFIG_NAME + " : " + str(self.name))
            return False
        mo_compute_pool = ComputePool(parent_mo_or_dn=parent_mo, descr=self.descr, name=self.name)
        if self.servers:
            for server in self.servers:
                if "rack_id" in server:
                    ComputePooledRackUnit(
                        parent_mo_or_dn=mo_compute_pool, system_id=server['system_id'], id=server['rack_id'])
                elif "chassis_id" in server and "slot_id" in server:
                    ComputePooledSlot(parent_mo_or_dn=mo_compute_pool, system_id=server['system_id'],
                                      chassis_id=server['chassis_id'], slot_id=server['slot_id'])

        self._handle.add_mo(mo=mo_compute_pool, modify_present=True)
        if self.qualification_policies:
            for qual_policy in self.qualification_policies:
                # We use a MD5 hashing function for the name of the ComputePoolingPolicy object,
                # since Central automatically generates a numerical ID when doing the action from the GUI.

                self._dn = self._parent._dn + "/pooling-policy-" + self.name
                mo_compute_pooling_policy = ComputePoolingPolicy(
                    parent_mo_or_dn="org-root", name="easyucs-" + hashlib.md5(self._dn.encode()).hexdigest()[: 8],
                    descr="Server pool policy is created by easyucs", qualifier=qual_policy, pool_dn=self._parent._dn +
                    "/compute-pool-" + self.name)
                self._handle.add_mo(mo=mo_compute_pooling_policy, modify_present=True)

        if commit:
            if self.commit(detail=self.name) != True:
                return False


class UcsCentralUuidPool(UcsCentralConfigObject):
    _CONFIG_NAME = "UUID Pool"
    _CONFIG_SECTION_NAME = "uuid_pools"
    _UCS_SDK_OBJECT_NAME = "uuidpoolPool"

    def __init__(self, parent=None, json_content=None, uuidpool_pool=None):
        UcsCentralConfigObject.__init__(self, parent=parent, ucs_sdk_object=uuidpool_pool)
        self.descr = None
        self.name = None
        self.prefix = None
        self.uuid_blocks = []
        self.operational_state = {}

        if self._config.load_from == "live":
            if uuidpool_pool is not None:
                self.name = uuidpool_pool.name
                self.descr = uuidpool_pool.descr
                self.prefix = uuidpool_pool.prefix
                self.operational_state = {
                    "size": uuidpool_pool.size,
                    "assigned": uuidpool_pool.assigned
                }

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

        self.clean_object()

    def clean_object(self):
        UcsCentralConfigObject.clean_object(self)

        for element in self.uuid_blocks:
            for value in ["to", "from", "size", "id_range_access_control"]:
                if value not in element:
                    element[value] = None

        for value in ["assigned", "size"]:
            if value not in self.operational_state:
                self.operational_state[value] = None

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
                    for i in range(int(block["size"]) - 1):
                        uuid_pool_to = uuid_pool_to + 1
                    # Convert to hexa
                    uuid_pool_to = hex(uuid_pool_to).split("0x")[1]
                    if len(uuid_pool_to) != 16:
                        # Add the missing 0 to get 16 letters in the string. We lost some 0 during the conversion
                        uuid_pool_to = "0" * (16 - len(uuid_pool_to)) + uuid_pool_to
                    uuid_pool_to = uuid_pool_to[0:4] + "-" + uuid_pool_to[4:]

                    UuidpoolBlock(parent_mo_or_dn=mo_uuidpool_pool, to=uuid_pool_to, r_from=block["from"],
                                  qualifier=block["id_range_access_control"])

        self._handle.add_mo(mo=mo_uuidpool_pool, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False


class UcsCentralWwnnPool(UcsCentralConfigObject):
    _CONFIG_NAME = "WWNN Pool"
    _CONFIG_SECTION_NAME = "wwnn_pools"
    _UCS_SDK_OBJECT_NAME = "fcpoolInitiators"

    def __init__(self, parent=None, json_content=None, wwnnpool_pool=None):
        UcsCentralConfigObject.__init__(self, parent=parent, ucs_sdk_object=wwnnpool_pool)
        self.descr = None
        self.name = None
        self.wwnn_blocks = []
        self.operational_state = {}

        if self._config.load_from == "live":
            if wwnnpool_pool is not None:
                self.name = wwnnpool_pool.name
                self.descr = wwnnpool_pool.descr
                self.operational_state = {
                    "size": wwnnpool_pool.size,
                    "assigned": wwnnpool_pool.assigned
                }

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

        self.clean_object()

    def clean_object(self):
        UcsCentralConfigObject.clean_object(self)

        for element in self.wwnn_blocks:
            for value in ["to", "from", "size", "id_range_access_control"]:
                if value not in element:
                    element[value] = None

        for value in ["assigned", "size"]:
            if value not in self.operational_state:
                self.operational_state[value] = None

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
                        wwnn_pool_to = "0" * (16 - len(wwnn_pool_to)) + wwnn_pool_to
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
    _CONFIG_SECTION_NAME = "wwpn_pools"
    _UCS_SDK_OBJECT_NAME = "fcpoolInitiators"

    def __init__(self, parent=None, json_content=None, wwpnpool_pool=None):
        UcsCentralConfigObject.__init__(self, parent=parent, ucs_sdk_object=wwpnpool_pool)
        self.descr = None
        self.name = None
        self.wwpn_blocks = []
        self.operational_state = {}

        if self._config.load_from == "live":
            if wwpnpool_pool is not None:
                self.name = wwpnpool_pool.name
                self.descr = wwpnpool_pool.descr
                self.operational_state = {
                    "size": wwpnpool_pool.size,
                    "assigned": wwpnpool_pool.assigned
                }

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

        self.clean_object()

    def clean_object(self):
        UcsCentralConfigObject.clean_object(self)

        for element in self.wwpn_blocks:
            for value in ["to", "from", "size", "id_range_access_control"]:
                if value not in element:
                    element[value] = None

        for value in ["assigned", "size"]:
            if value not in self.operational_state:
                self.operational_state[value] = None

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
                        wwpn_pool_to = "0" * (16 - len(wwpn_pool_to)) + wwpn_pool_to
                    wwpn_pool_to = wwpn_pool_to[0:2] + ":" + wwpn_pool_to[2:4] + ":" + wwpn_pool_to[4:6] + ":" + \
                        wwpn_pool_to[6:8] + ":" + wwpn_pool_to[8:10] + ":" + wwpn_pool_to[10:12] + ":" + \
                        wwpn_pool_to[12:14] + ":" + wwpn_pool_to[14:16]

                    FcpoolBlock(parent_mo_or_dn=mo_fc_pool_init, to=wwpn_pool_to,
                                r_from=block["from"], qualifier=block["id_range_access_control"])

        self._handle.add_mo(mo=mo_fc_pool_init, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False


class UcsCentralWwxnPool(UcsCentralConfigObject):
    _CONFIG_NAME = "WWxN Pool"
    _CONFIG_SECTION_NAME = "wwxn_pools"
    _UCS_SDK_OBJECT_NAME = "fcpoolInitiators"

    def __init__(self, parent=None, json_content=None, wwxnpool_pool=None):
        UcsCentralConfigObject.__init__(self, parent=parent, ucs_sdk_object=wwxnpool_pool)
        self.descr = None
        self.name = None
        self.max_ports_per_node = None
        self.wwxn_blocks = []
        self.operational_state = {}

        if self._config.load_from == "live":
            if wwxnpool_pool is not None:
                self.name = wwxnpool_pool.name
                self.descr = wwxnpool_pool.descr
                self.max_ports_per_node = wwxnpool_pool.max_ports_per_node.split("upto")[1]
                self.operational_state = {
                    "size": wwxnpool_pool.size,
                    "assigned": wwxnpool_pool.assigned
                }

                if "fcpoolBlock" in self._parent._config.sdk_objects:
                    for pool_block in self._config.sdk_objects["fcpoolBlock"]:
                        if self._parent._dn:
                            if self._parent._dn + "/wwn-pool-" + self.name + "/block-" in pool_block.dn:
                                block = {}
                                block.update({"to": pool_block.to})
                                block.update({"from": pool_block.r_from})
                                block.update({"size": None})
                                block.update({"id_range_access_control": pool_block.qualifier})
                                self.wwxn_blocks.append(block)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def clean_object(self):
        UcsCentralConfigObject.clean_object(self)

        for element in self.wwxn_blocks:
            for value in ["to", "from", "size", "id_range_access_control"]:
                if value not in element:
                    element[value] = None

        for value in ["assigned", "size"]:
            if value not in self.operational_state:
                self.operational_state[value] = None

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

        max_ports_per_node = None
        if self.max_ports_per_node:
            max_ports_per_node = "upto" + self.max_ports_per_node

        mo_fc_pool_init = FcpoolInitiators(parent_mo_or_dn=parent_mo,
                                           descr=self.descr,
                                           name=self.name,
                                           max_ports_per_node=max_ports_per_node,
                                           purpose="node-and-port-wwn-assignment"
                                           )
        if self.wwxn_blocks:
            for block in self.wwxn_blocks:
                if block["to"]:
                    FcpoolBlock(parent_mo_or_dn=mo_fc_pool_init, to=block["to"], r_from=block["from"],
                                qualifier=block["id_range_access_control"])
                elif block["size"]:
                    wwxn_pool_to = block["from"]
                    # Convert from hexa to int
                    wwxn_pool_to = int(wwxn_pool_to.replace(":", ""), 16)
                    for i in range(int(block["size"]) - 1):
                        wwxn_pool_to = wwxn_pool_to + 1
                    # Convert to hexa
                    wwxn_pool_to = hex(wwxn_pool_to).split("0x")[1]
                    if len(wwxn_pool_to) != 16:
                        # Add the missing 0 to get 16 letters in the string. We lost some 0 during the conversion
                        wwxn_pool_to = "0" * (16 - len(wwxn_pool_to)) + wwxn_pool_to
                    wwxn_pool_to = wwxn_pool_to[0:2] + ":" + wwxn_pool_to[2:4] + ":" + wwxn_pool_to[4:6] + ":" + \
                        wwxn_pool_to[6:8] + ":" + wwxn_pool_to[8:10] + ":" + wwxn_pool_to[10:12] + ":" + \
                        wwxn_pool_to[12:14] + ":" + wwxn_pool_to[14:16]

                    FcpoolBlock(parent_mo_or_dn=mo_fc_pool_init, to=wwxn_pool_to,
                                r_from=block["from"], qualifier=block["id_range_access_control"])

        self._handle.add_mo(mo=mo_fc_pool_init, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
