# coding: utf-8
# !/usr/bin/env python

""" pools.py: Easy UCS Central Pools objects """

import hashlib

from netaddr import EUI, IPAddress
from ucscsdk.mometa.adaptor.AdaptorCapQual import AdaptorCapQual
from ucscsdk.mometa.adaptor.AdaptorQual import AdaptorQual
from ucscsdk.mometa.compute.ComputeChassisQual import ComputeChassisQual
from ucscsdk.mometa.compute.ComputeDomainGroupQual import ComputeDomainGroupQual
from ucscsdk.mometa.compute.ComputeDomainNameQual import ComputeDomainNameQual
from ucscsdk.mometa.compute.ComputeDomainQual import ComputeDomainQual
from ucscsdk.mometa.compute.ComputeOwnerQual import ComputeOwnerQual
from ucscsdk.mometa.compute.ComputePhysicalQual import ComputePhysicalQual
from ucscsdk.mometa.compute.ComputePool import ComputePool
from ucscsdk.mometa.compute.ComputePooledRackUnit import ComputePooledRackUnit
from ucscsdk.mometa.compute.ComputePooledSlot import ComputePooledSlot
from ucscsdk.mometa.compute.ComputePoolingPolicy import ComputePoolingPolicy
from ucscsdk.mometa.compute.ComputeProductFamilyQual import ComputeProductFamilyQual
from ucscsdk.mometa.compute.ComputeQual import ComputeQual
from ucscsdk.mometa.compute.ComputeRackQual import ComputeRackQual
from ucscsdk.mometa.compute.ComputeSiteQual import ComputeSiteQual
from ucscsdk.mometa.compute.ComputeSlotQual import ComputeSlotQual
from ucscsdk.mometa.compute.ComputeSystemAddrQual import ComputeSystemAddrQual
from ucscsdk.mometa.fcpool.FcpoolBlock import FcpoolBlock
from ucscsdk.mometa.fcpool.FcpoolInitiators import FcpoolInitiators
from ucscsdk.mometa.ippool.IppoolBlock import IppoolBlock
from ucscsdk.mometa.ippool.IppoolIpV6Block import IppoolIpV6Block
from ucscsdk.mometa.ippool.IppoolPool import IppoolPool
from ucscsdk.mometa.iqnpool.IqnpoolBlock import IqnpoolBlock
from ucscsdk.mometa.iqnpool.IqnpoolPool import IqnpoolPool
from ucscsdk.mometa.macpool.MacpoolBlock import MacpoolBlock
from ucscsdk.mometa.macpool.MacpoolPool import MacpoolPool
from ucscsdk.mometa.memory.MemoryQual import MemoryQual
from ucscsdk.mometa.processor.ProcessorQual import ProcessorQual
from ucscsdk.mometa.storage.StorageQual import StorageQual
from ucscsdk.mometa.uuidpool.UuidpoolBlock import UuidpoolBlock
from ucscsdk.mometa.uuidpool.UuidpoolPool import UuidpoolPool


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


class UcsCentralServerPoolPolicyQualifications(UcsCentralConfigObject):
    _CONFIG_NAME = "Server Pool Policy Qualification"
    _CONFIG_SECTION_NAME = "server_pool_policy_qualifications"
    _UCS_SDK_OBJECT_NAME = "computeQual"

    def __init__(self, parent=None, json_content=None, compute_qual=None):
        UcsCentralConfigObject.__init__(self, parent=parent, ucs_sdk_object=compute_qual)
        self.name = None
        self.descr = None
        self.qualifications = []

        if self._config.load_from == "live":
            if compute_qual is not None:
                self.name = compute_qual.name
                self.descr = compute_qual.descr

                if "computePhysicalQual" in self._parent._config.sdk_objects:
                    for qualif in self._config.sdk_objects["computePhysicalQual"]:
                        if self._parent._dn:
                            if self._parent._dn + "/blade-qualifier-" + self.name + "/" in qualif.dn:
                                qualification = {}
                                qualification.update({"type": "server_pid"})
                                qualification.update({"server_pid": qualif.model})
                                self.qualifications.append(qualification)
                                break

                if "computeDomainQual" in self._parent._config.sdk_objects:
                    for qualif in self._config.sdk_objects["computeDomainQual"]:
                        if self._parent._dn:
                            if self._parent._dn + "/blade-qualifier-" + self.name + "/" in qualif.dn:
                                qualification = {}
                                qualification.update({"type": "domain_qual"})
                                qualification.update({"domain_qual_name": qualif.name})
                                qualification_policies = []

                                if "computeRackQual" in self._parent._config.sdk_objects:
                                    for qualif_elm in self._config.sdk_objects["computeRackQual"]:
                                        if self._parent._dn:
                                            if self._parent._dn + "/blade-qualifier-" + self.name + "/Domain-qualifier-" + \
                                                    qualif.name + "/" in qualif_elm.dn:
                                                qualification_element = {}
                                                qualification_element.update({"type": "domain_qual_rack"})
                                                qualification_element.update({"first_rack_id": qualif_elm.min_id})
                                                qualification_element.update({"last_rack_id": qualif_elm.max_id})
                                                qualification_policies.append(qualification_element)

                                if "computeChassisQual" in self._parent._config.sdk_objects:
                                    for qualif_elm in self._config.sdk_objects["computeChassisQual"]:
                                        if self._parent._dn:
                                            if self._parent._dn + "/blade-qualifier-" + self.name + "/Domain-qualifier-" + \
                                                    qualif.name + "/" in qualif_elm.dn:
                                                qualification_element = {}
                                                qualification_element.update({"type": "domain_qual_chassis"})
                                                qualification_element.update({"first_chassis_id": qualif_elm.min_id})
                                                qualification_element.update({"last_chassis_id": qualif_elm.max_id})
                                                qualification_element["server_qualifications"] = []
                                                if "computeSlotQual" in self._parent._config.sdk_objects:
                                                    for slot_qualif in self._config.sdk_objects["computeSlotQual"]:
                                                        if self._parent._dn + "/blade-qualifier-" + self.name + "/Domain-qualifier-" + \
                                                                qualif.name + "/chassis-from-" + qualif_elm.min_id + "-to-" + \
                                                                qualif_elm.max_id + "/" in slot_qualif.dn:
                                                            slot_qualification = {}
                                                            slot_qualification.update(
                                                                {"first_slot_id": slot_qualif.min_id})
                                                            slot_qualification.update(
                                                                {"last_slot_id": slot_qualif.max_id})
                                                            qualification_element["server_qualifications"].append(
                                                                slot_qualification)
                                                qualification_policies.append(qualification_element)

                                if "computeDomainGroupQual" in self._parent._config.sdk_objects:
                                    for qualif_elm in self._config.sdk_objects["computeDomainGroupQual"]:
                                        if self._parent._dn:
                                            if self._parent._dn + "/blade-qualifier-" + self.name + "/Domain-qualifier-" + \
                                                    qualif.name + "/" in qualif_elm.dn:
                                                qualification_element = {}
                                                qualification_element.update({"type": "domain_qual_group"})
                                                # Converting Domain Group name to user readable name.
                                                # Eg:  domaingroup-root/domaingroup-EU-root-1 is changed to root/EU-root-1
                                                qualification_element.update(
                                                    {"domain_group_dn": '/'.join(
                                                        [domaingrp.replace('domaingroup-', '', 1)
                                                         for domaingrp in qualif_elm.domain_group_dn.split('/')])})
                                                qualification_element.update({"hierarchical": qualif_elm.hierarchical})
                                                qualification_element.update({"name": qualif_elm.name})
                                                qualification_policies.append(qualification_element)

                                if "computeDomainNameQual" in self._parent._config.sdk_objects:
                                    for qualif_elm in self._config.sdk_objects["computeDomainNameQual"]:
                                        if self._parent._dn:
                                            if self._parent._dn + "/blade-qualifier-" + self.name + "/Domain-qualifier-" + \
                                                    qualif.name + "/" in qualif_elm.dn:
                                                qualification_element = {}
                                                qualification_element.update({"type": "domain_qual_group_name"})
                                                qualification_element.update({"name": qualif_elm.name})
                                                qualification_policies.append(qualification_element)

                                if "computeOwnerQual" in self._parent._config.sdk_objects:
                                    for qualif_elm in self._config.sdk_objects["computeOwnerQual"]:
                                        if self._parent._dn:
                                            if self._parent._dn + "/blade-qualifier-" + self.name + "/Domain-qualifier-" + \
                                                    qualif.name + "/" in qualif_elm.dn:
                                                qualification_element = {}
                                                qualification_element.update({"type": "domain_qual_owner"})
                                                qualification_element.update({"name": qualif_elm.name})
                                                qualification_element.update({"regex": qualif_elm.regex})
                                                qualification_policies.append(qualification_element)

                                if "computeProductFamilyQual" in self._parent._config.sdk_objects:
                                    for qualif_elm in self._config.sdk_objects["computeProductFamilyQual"]:
                                        if self._parent._dn:
                                            if self._parent._dn + "/blade-qualifier-" + self.name + "/Domain-qualifier-" + \
                                                    qualif.name + "/" in qualif_elm.dn:
                                                qualification_element = {}
                                                qualification_element.update({"type": "domain_qual_product"})
                                                qualification_element.update(
                                                    {"product_family": qualif_elm.product_family})
                                                qualification_policies.append(qualification_element)

                                if "computeSiteQual" in self._parent._config.sdk_objects:
                                    for qualif_elm in self._config.sdk_objects["computeSiteQual"]:
                                        if self._parent._dn:
                                            if self._parent._dn + "/blade-qualifier-" + self.name + "/Domain-qualifier-" + \
                                                    qualif.name + "/" in qualif_elm.dn:
                                                qualification_element = {}
                                                qualification_element.update({"type": "domain_qual_site"})
                                                qualification_element.update({"name": qualif_elm.name})
                                                qualification_element.update({"regex": qualif_elm.regex})
                                                qualification_policies.append(qualification_element)

                                if "computeSystemAddrQual" in self._parent._config.sdk_objects:
                                    for qualif_elm in self._config.sdk_objects["computeSystemAddrQual"]:
                                        if self._parent._dn:
                                            if self._parent._dn + "/blade-qualifier-" + self.name + "/Domain-qualifier-" + \
                                                    qualif.name + "/" in qualif_elm.dn:
                                                qualification_element = {}
                                                qualification_element.update({"min_addr": qualif_elm.min_addr})
                                                qualification_element.update({"max_addr": qualif_elm.max_addr})
                                                qualification_element.update({"type": "domain_qual_system_addr"})
                                                qualification_policies.append(qualification_element)

                                if len(qualification_policies) > 0:
                                    qualification["domain_qualifications"] = qualification_policies
                                self.qualifications.append(qualification)

                if "adaptorQual" in self._parent._config.sdk_objects:
                    for qualif in self._config.sdk_objects["adaptorQual"]:
                        if self._parent._dn:
                            if self._parent._dn + "/blade-qualifier-" + self.name + "/" in qualif.dn:
                                qualification = {}
                                qualification.update({"type": "adapter"})
                                adapter_policies = []
                                if "adaptorCapQual" in self._parent._config.sdk_objects:
                                    for adapt_qualif in self._config.sdk_objects["adaptorCapQual"]:
                                        if self._parent._dn + "/blade-qualifier-" + self.name + "/adaptor/cap-" \
                                                in adapt_qualif.dn:
                                            qualification_element = {}
                                            qualification_element.update(
                                                {"adapter_maximum_capacity": adapt_qualif.maximum})
                                            qualification_element.update({"adapter_type": adapt_qualif.type})
                                            qualification_element.update({"adapter_pid": adapt_qualif.model})
                                            adapter_policies.append(qualification_element)
                                if len(adapter_policies) > 0:
                                    qualification['adapter_qualifications'] = adapter_policies
                                self.qualifications.append(qualification)

                if "processorQual" in self._parent._config.sdk_objects:
                    for qualif in self._config.sdk_objects["processorQual"]:
                        if self._parent._dn:
                            if self._parent._dn + "/blade-qualifier-" + self.name + "/" in qualif.dn:
                                qualification = {}
                                qualification.update({"type": "cpu-cores"})
                                # Convert cpu speed value from float to integer and assigning as string
                                if qualif.speed:
                                    if qualif.speed == "unspecified":
                                        qualification.update({"cpu_speed": qualif.speed})
                                    else:
                                        qualification.update({"cpu_speed": str(int(float(qualif.speed)))})
                                qualification.update({"cpu_stepping": qualif.stepping})
                                qualification.update({"min_cores": qualif.min_cores})
                                qualification.update({"max_cores": qualif.max_cores})
                                qualification.update({"min_threads": qualif.min_threads})
                                qualification.update({"max_threads": qualif.max_threads})
                                qualification.update({"min_procs": qualif.min_procs})
                                qualification.update({"max_procs": qualif.max_procs})
                                qualification.update({"processor_architecture": qualif.arch})
                                qualification.update({"processor_pid": qualif.model})
                                self.qualifications.append(qualification)
                                break

                if "memoryQual" in self._parent._config.sdk_objects:
                    for qualif in self._config.sdk_objects["memoryQual"]:
                        if self._parent._dn:
                            if self._parent._dn + "/blade-qualifier-" + self.name + "/" in qualif.dn:
                                qualification = {}
                                qualification.update({"type": "memory"})
                                qualification.update({"clock": qualif.clock})
                                qualification.update({"data_rate": qualif.speed})
                                # Convert latency value from float to integer and assigning as string
                                if qualif.latency:
                                    if qualif.latency == "unspecified":
                                        qualification.update({"latency": qualif.latency})
                                    else:
                                        qualification.update({"latency": str(int(float(qualif.latency)))})
                                qualification.update({"min_cap": qualif.min_cap})
                                qualification.update({"max_cap": qualif.max_cap})
                                qualification.update({"units": qualif.units})
                                qualification.update({"width": qualif.width})
                                self.qualifications.append(qualification)
                                break

                if "storageQual" in self._parent._config.sdk_objects:
                    for qualif in self._config.sdk_objects["storageQual"]:
                        if self._parent._dn:
                            if self._parent._dn + "/blade-qualifier-" + self.name + "/" in qualif.dn:
                                qualification = {}
                                qualification.update({"type": "storage"})
                                if qualif.diskless == 'yes':
                                    qualification.update({"diskless": qualif.diskless})
                                else:
                                    qualification.update({"min_cap": qualif.min_cap})
                                    qualification.update({"max_cap": qualif.max_cap})
                                    qualification.update({"disk_type": qualif.disk_type})
                                    qualification.update({"diskless": qualif.diskless})
                                    qualification.update({"number_of_blocks": qualif.number_of_blocks})
                                    qualification.update({"block_size": qualif.block_size})
                                    qualification.update({"units": qualif.units})
                                    qualification.update({"per_disk_cap": qualif.per_disk_cap})
                                    qualification.update(
                                        {"number_of_flexflash_cards": qualif.number_of_flex_flash_cards})
                                self.qualifications.append(qualification)
                                break

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def clean_object(self):
        UcsCentralConfigObject.clean_object(self)

        # We need to set all values that are not present in the config file to None
        for element in self.qualifications:
            for value in [
                "adapter_maximum_capacity", "adapter_pid", "adapter_qualifications", "adapter_type",
                "block_size", "clock", "cpu_speed", "cpu_stepping", "data_rate", "diskless", "disk_type",
                "domain_qualifications", "domain_qual_name", "latency", "max_cap", "min_cap", "max_cores",
                "min_cores", "min_procs", "max_procs", "max_threads", "min_threads", "number_of_blocks",
                "number_of_flexflash_cards", "per_disk_cap", "processor_architecture",
                "processor_pid", "server_pid", "type", "units", "width"]:
                if value not in element:
                    element[value] = None

            if element["domain_qualifications"]:
                for subelement in element["domain_qualifications"]:
                    for value in ["domain_group_dn", "first_chassis_id", "first_rack_id", "hierarchical",
                                  "last_chassis_id", "last_rack_id", "max_addr", "min_addr", "name",
                                  "product_family", "regex", "server_qualifications", "type"]:
                        if value not in subelement:
                            subelement[value] = None
                    if subelement["server_qualifications"]:
                        for server_subelement in subelement["server_qualifications"]:
                            for value in ["first_slot_id", "last_slot_id"]:
                                if value not in server_subelement:
                                    server_subelement[value] = None
            if element["adapter_qualifications"]:
                for subelement in element["adapter_qualifications"]:
                    for value in ["adapter_maximum_capacity", "adapter_pid", "adapter_type"]:
                        if value not in subelement:
                            subelement[value] = None

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

        mo_compute_qual = ComputeQual(parent_mo_or_dn=parent_mo, name=self.name, descr=self.descr)
        if self.qualifications:
            for qualification in self.qualifications:
                if qualification["type"] == "server_pid":
                    ComputePhysicalQual(parent_mo_or_dn=mo_compute_qual, model=qualification['server_pid'])

                elif qualification["type"] == "domain_qual":
                    mo_compute_domain_qual = ComputeDomainQual(parent_mo_or_dn=mo_compute_qual,
                                                               name=qualification["domain_qual_name"])
                    if qualification["domain_qualifications"]:
                        for domain_qualification_policies in qualification["domain_qualifications"]:

                            if domain_qualification_policies["type"] == "domain_qual_rack":
                                last_rack_id = None
                                if "number_of_servers" in domain_qualification_policies:
                                    last_rack_id = str(int(domain_qualification_policies['first_rack_id']) +
                                                       int(domain_qualification_policies['number_of_servers']) - 1)
                                    # If last_rack_id is above 255, assign last_rack_id value to 255
                                    if int(last_rack_id) > 255:
                                        last_rack_id = '255'
                                elif "last_rack_id" in domain_qualification_policies:
                                    last_rack_id = domain_qualification_policies['last_rack_id']
                                ComputeRackQual(
                                    parent_mo_or_dn=mo_compute_domain_qual,
                                    min_id=domain_qualification_policies['first_rack_id'],
                                    max_id=last_rack_id)

                            elif domain_qualification_policies["type"] == "domain_qual_chassis":
                                last_chassis_id = None
                                if "number_of_chassis" in domain_qualification_policies:
                                    last_chassis_id = str(int(domain_qualification_policies['first_chassis_id']) +
                                                          int(domain_qualification_policies['number_of_chassis']) - 1)
                                    # If last_chassis_id is above 255, assign last_chassis_id value to 255
                                    if int(last_chassis_id) > 255:
                                        last_chassis_id = '255'
                                elif domain_qualification_policies["last_chassis_id"]:
                                    last_chassis_id = domain_qualification_policies['last_chassis_id']
                                mo_chassis_qual = ComputeChassisQual(
                                    parent_mo_or_dn=mo_compute_domain_qual,
                                    min_id=domain_qualification_policies['first_chassis_id'],
                                    max_id=last_chassis_id)
                                if domain_qualification_policies['server_qualifications']:
                                    for slot_id_range in domain_qualification_policies['server_qualifications']:
                                        last_slot_id = None
                                        if "number_of_slots" in slot_id_range:
                                            last_slot_id = str(int(slot_id_range['first_slot_id']) +
                                                               int(slot_id_range['number_of_slots']) - 1)
                                            # If last_slot id is above 8, assign last_slot id value to 8
                                            if int(last_slot_id) > 8:
                                                last_slot_id = '8'
                                        elif "last_slot_id" in slot_id_range:
                                            last_slot_id = slot_id_range['last_slot_id']
                                        ComputeSlotQual(parent_mo_or_dn=mo_chassis_qual, max_id=last_slot_id,
                                                        min_id=slot_id_range['first_slot_id'])

                            elif domain_qualification_policies["type"] == "domain_qual_group":
                                # Converting user readable Domain Group name to sdk acceptable Domain Group Dn
                                # Eg:  root/EU-root-1 is changed to domaingroup-root/domaingroup-EU-root-1
                                domain_dn = '/'.join(["domaingroup-"+dmndn for dmndn in
                                                      domain_qualification_policies["domain_group_dn"].split('/')])
                                ComputeDomainGroupQual(parent_mo_or_dn=mo_compute_domain_qual,
                                                       domain_group_dn=domain_dn,
                                                       hierarchical=domain_qualification_policies["hierarchical"],
                                                       name=domain_qualification_policies["name"])

                            elif domain_qualification_policies["type"] == "domain_qual_group_name":
                                ComputeDomainNameQual(parent_mo_or_dn=mo_compute_domain_qual,
                                                      name=domain_qualification_policies["name"])

                            elif domain_qualification_policies["type"] == "domain_qual_owner":
                                ComputeOwnerQual(parent_mo_or_dn=mo_compute_domain_qual,
                                                 name=domain_qualification_policies["name"],
                                                 regex=domain_qualification_policies["regex"])

                            elif domain_qualification_policies["type"] == "domain_qual_product":
                                ComputeProductFamilyQual(parent_mo_or_dn=mo_compute_domain_qual,
                                                         product_family=domain_qualification_policies["product_family"])

                            elif domain_qualification_policies["type"] == "domain_qual_site":
                                ComputeSiteQual(parent_mo_or_dn=mo_compute_domain_qual,
                                                name=domain_qualification_policies["name"],
                                                regex=domain_qualification_policies["regex"])

                            elif domain_qualification_policies["type"] == "domain_qual_system_addr":
                                ComputeSystemAddrQual(parent_mo_or_dn=mo_compute_domain_qual,
                                                      min_addr=domain_qualification_policies["min_addr"],
                                                      max_addr=domain_qualification_policies["max_addr"])

                elif qualification["type"] == "adapter":
                    mo_adaptor_qual = AdaptorQual(parent_mo_or_dn=mo_compute_qual)
                    if qualification["adapter_qualifications"]:
                        for adapter_qualification in qualification["adapter_qualifications"]:
                            AdaptorCapQual(
                                parent_mo_or_dn=mo_adaptor_qual,
                                maximum=adapter_qualification['adapter_maximum_capacity'],
                                type=adapter_qualification['adapter_type'],
                                model=adapter_qualification['adapter_pid'])

                elif qualification["type"] == "cpu-cores":
                    ProcessorQual(parent_mo_or_dn=mo_compute_qual, min_cores=qualification['min_cores'],
                                  max_cores=qualification['max_cores'], min_threads=qualification['min_threads'],
                                  max_threads=qualification['max_threads'], min_procs=qualification['min_procs'],
                                  max_procs=qualification['max_procs'], speed=qualification['cpu_speed'],
                                  arch=qualification['processor_architecture'], model=qualification['processor_pid'],
                                  stepping=qualification['cpu_stepping'])

                elif qualification["type"] == "memory":
                    MemoryQual(parent_mo_or_dn=mo_compute_qual, min_cap=qualification['min_cap'],
                               max_cap=qualification['max_cap'], clock=qualification['clock'],
                               latency=qualification['latency'], width=qualification['width'],
                               units=qualification['units'], speed=qualification["data_rate"])

                elif qualification["type"] == "storage":
                    StorageQual(parent_mo_or_dn=mo_compute_qual, min_cap=qualification['min_cap'],
                                per_disk_cap=qualification['per_disk_cap'],
                                block_size=qualification['block_size'],
                                number_of_blocks=qualification['number_of_blocks'],
                                max_cap=qualification['max_cap'], disk_type=qualification['disk_type'],
                                units=qualification['units'],
                                number_of_flex_flash_cards=qualification['number_of_flexflash_cards'],
                                diskless=qualification['diskless'])

        self._handle.add_mo(mo=mo_compute_qual, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True


class UcsCentralServerPool(UcsCentralConfigObject):
    _CONFIG_NAME = "Server Pool"
    _CONFIG_SECTION_NAME = "server_pools"
    _UCS_SDK_OBJECT_NAME = "computePool"
    _POLICY_MAPPING_TABLE = {
        "qualification_policies": UcsCentralServerPoolPolicyQualifications
    }

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
