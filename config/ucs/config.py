# coding: utf-8
# !/usr/bin/env python

""" config.py: Easy UCS Deployment Tool """

import http
import re
import urllib
import xml
import xml.etree.ElementTree as ET
from collections import defaultdict

from imcsdk.imcexception import ImcException
from ucscsdk.ucscexception import UcscException
from ucsmsdk.ucscoremeta import UcsVersion
from ucscsdk.ucsccoremeta import UcscVersion
from ucsmsdk.ucsexception import UcsException
from ucsmsdk import ucscoreutils

from config.config import GenericConfig
from config.ucs.object import GenericUcsConfigObject


def _load_mo_from_xml_element(mo_class, elem):
    """
    Instantiate a typed ucsmsdk MO from an XML element, without going through the
    normal __init__ constructor.

    The normal constructor enforces validation rules (naming patterns, READ_ONLY
    restrictions) that reject values that are perfectly valid when read back from
    a live system or an MIT XML dump (e.g. usernames with backslashes, read-only
    computed properties like 'priv'). Bypassing __init__ avoids all of that.

    Strategy:
      1. Allocate the object via __new__ (no __init__ called).
      2. Set the minimum internal state that ManagedObject.from_xml() requires.
      3. Pre-initialise every known property to None so that attribute access on
         properties absent from the XML element does not raise AttributeError.
      4. Call from_xml(elem), which populates all attributes present in the XML
         using object.__setattr__ directly, bypassing all validation.

    :param mo_class: A ucsmsdk MO class (e.g. AaaUser, FabricVlan, ...).
    :param elem:     An xml.etree.ElementTree.Element whose tag matches the class.
    :return:         A fully populated MO instance.
    """
    mo = object.__new__(mo_class)
    object.__setattr__(mo, '_dirty_mask', 0)
    object.__setattr__(mo, '_ManagedObject__xtra_props', {})
    object.__setattr__(mo, '_ManagedObject__xtra_props_dirty_mask', 0x1)
    object.__setattr__(mo, '_class_id', mo_class.__name__)
    for prop_name in mo_class.prop_meta:
        object.__setattr__(mo, prop_name, None)
    mo.from_xml(elem)
    return mo


class GenericUcsConfig(GenericConfig):
    # List of SDK objects to fetch that are common to UCS System, Central & IMC
    _COMMON_SDK_OBJECTS_TO_FETCH = ["aaaUser", "commNtpProvider", "topSystem"]

    def __init__(self, parent=None):
        GenericConfig.__init__(self, parent=parent)
        self.export_list = None
        self.handle = self.parent.parent.handle
        self.intersight_status = ""
        self.sdk_objects = defaultdict(list)

    def _fetch_sdk_objects(self, force=False):
        sdk_objects_to_fetch = self._COMMON_SDK_OBJECTS_TO_FETCH
        self.logger(level="debug", message="Fetching common UCS SDK objects for config")

        if self.device.task is not None:
            self.device.task.taskstep_manager.start_taskstep(name="FetchConfigUcsCommonSdkObjects",
                                                             description="Fetching common UCS SDK Config Objects")

        failed_to_fetch = []
        for sdk_object_name in sdk_objects_to_fetch:
            try:
                self.sdk_objects[sdk_object_name] = self.handle.query_classid(sdk_object_name)
                self.logger(level="debug", message="Fetched " + str(len(self.sdk_objects[sdk_object_name])) +
                                                   " objects of class " + sdk_object_name)
            except (UcsException, ImcException, UcscException) as err:
                if err.error_code in ["ERR-xml-parse-error", "0"] and \
                        "no class named " + sdk_object_name in err.error_descr:
                    self.logger(level="debug", message="No UCS class named " + sdk_object_name)
                elif err.error_code in ["2500"] and \
                        "MO is not supported on this UCS-C server platform." in err.error_descr:
                    self.logger(level="debug", message="No UCS class named " + sdk_object_name)
                else:
                    failed_to_fetch.append(sdk_object_name)
                    self.logger(level="error",
                                message="Error while trying to fetch " + self.device.metadata.device_type_long +
                                        " class " + sdk_object_name + ": " + str(err))
            except ConnectionRefusedError:
                failed_to_fetch.append(sdk_object_name)
                self.logger(level="error",
                            message="Error while communicating with " + self.device.metadata.device_type_long +
                                    " for class " + sdk_object_name + ": Connection refused")
            except urllib.error.URLError:
                failed_to_fetch.append(sdk_object_name)
                self.logger(level="error",
                            message="Timeout error while fetching " + self.device.metadata.device_type_long +
                                    " class " + sdk_object_name)
            except Exception as err:
                failed_to_fetch.append(sdk_object_name)
                self.logger(level="error", message="Error while fetching " + self.device.metadata.device_type_long +
                                                   " class " + sdk_object_name + ": " + str(err))

        # We retry all SDK objects that failed to fetch properly
        if failed_to_fetch:
            duplicate_failed_to_fetch = failed_to_fetch.copy()
            for sdk_object_name in duplicate_failed_to_fetch:
                self.logger(level="info", message="Retrying to fetch " + sdk_object_name)
                try:
                    self.sdk_objects[sdk_object_name] = self.handle.query_classid(sdk_object_name)
                    self.logger(level="debug", message="Fetched " + str(len(self.sdk_objects[sdk_object_name])) +
                                                       " objects of class " + sdk_object_name)
                    failed_to_fetch.remove(sdk_object_name)
                except (UcsException, ImcException, UcscException) as err:
                    self.logger(level="error",
                                message="Error while trying to fetch " + self.device.metadata.device_type_long +
                                        " class " + sdk_object_name + ": " + str(err))
                except ConnectionRefusedError:
                    self.logger(level="error",
                                message="Error while communicating with " + self.device.metadata.device_type_long +
                                        " for class " + sdk_object_name + ": Connection refused")
                except urllib.error.URLError:
                    self.logger(level="error",
                                message="Timeout error while fetching " + self.device.metadata.device_type_long +
                                        " class " + sdk_object_name)
                except Exception as err:
                    self.logger(level="error", message="Error while fetching " + self.device.metadata.device_type_long +
                                                       " class " + sdk_object_name + ": " + str(err))

        # In case we still have SDK objects that failed to fetch, we list them in a warning message
        if failed_to_fetch:
            for sdk_object_name in failed_to_fetch:
                self.logger(level="warning",
                            message="Impossible to fetch " + sdk_object_name + " after 2 attempts.")

        if self.device.task is not None:
            if not failed_to_fetch:
                self.device.task.taskstep_manager.stop_taskstep(
                    name="FetchConfigUcsCommonSdkObjects", status="successful",
                    status_message="Successfully fetched common UCS SDK Config Objects")
            elif force:
                self.device.task.taskstep_manager.stop_taskstep(
                    name="FetchConfigUcsCommonSdkObjects", status="successful",
                    status_message="Fetched common UCS SDK Config Objects with errors (forced)")
            else:
                self.device.task.taskstep_manager.stop_taskstep(
                    name="FetchConfigUcsCommonSdkObjects", status="failed",
                    status_message="Error while fetching common UCS SDK Config Objects")

                # If any of the mandatory tasksteps fails then return False
                if not self.device.task.taskstep_manager.is_taskstep_optional(name="FetchConfigUcsCommonSdkObjects"):
                    return False
        return True

    def get_config_objects_under_dn(self, dn=None, object_class=None, parent=None):
        if dn is not None and object_class is not None and parent is not None:
            if hasattr(object_class, "_UCS_SDK_OBJECT_NAME"):
                if object_class._UCS_SDK_OBJECT_NAME in self.sdk_objects.keys():
                    if self.sdk_objects[object_class._UCS_SDK_OBJECT_NAME] is not None:
                        # We filter out SDK objects that are not under this Dn
                        filtered_sdk_objects_list = []
                        for sdk_object in self.sdk_objects[object_class._UCS_SDK_OBJECT_NAME]:
                            if sdk_object.dn.startswith(dn + '/'):
                                if "/" not in sdk_object.dn[len(dn + "/"):]:
                                    # WWPN, WWNN and WWXN use the same object class.
                                    # We use the "purpose" parameter to differentiate them.
                                    if object_class.__name__ in ["UcsSystemWwpnPool", "UcsCentralWwpnPool"]:
                                        if sdk_object.purpose != "port-wwn-assignment":
                                            continue
                                    if object_class.__name__ in ["UcsSystemWwnnPool", "UcsCentralWwnnPool"]:
                                        if sdk_object.purpose != "node-wwn-assignment":
                                            continue
                                    if object_class.__name__ in ["UcsSystemWwxnPool", "UcsCentralWwxnPool"]:
                                        if sdk_object.purpose != "node-and-port-wwn-assignment":
                                            continue
                                    filtered_sdk_objects_list.append(sdk_object)

                                elif "/domaingroup-" not in sdk_object.dn[len(dn):]:
                                    # dn with / even after removing parent dn and do not have another domaingroup parent
                                    if object_class.__name__ in ["UcsCentralFlowControlPolicy"]:
                                        filtered_sdk_objects_list.append(sdk_object)

                                    if object_class.__name__ in ["UcsCentralVlan"]:
                                        # We filter out Appliance VLANs in case we are looking for VLANs in UCS Central
                                        if sdk_object.dn[len(dn + "/"):].startswith("fabric/eth-estc"):
                                            continue
                                        else:
                                            filtered_sdk_objects_list.append(sdk_object)

                                    if object_class.__name__ in ["UcsCentralApplianceVlan"]:
                                        # We filter out VLANs in case we are looking for Appliance VLANs in UCS Central
                                        if sdk_object.dn[len(dn + "/"):].startswith("fabric/lan"):
                                            continue
                                        else:
                                            filtered_sdk_objects_list.append(sdk_object)

                                    if object_class.__name__ in ["UcsCentralVlanGroup"]:
                                        if sdk_object.dn[len(dn + "/"):].startswith("fabric/lan/net-group"):
                                            filtered_sdk_objects_list.append(sdk_object)

                                    if object_class.__name__ in ["UcsCentralVsan"]:
                                        # We filter out Storage VSANs in case we are looking for VSANs in UCS Central
                                        if sdk_object.dn[len(dn + "/"):].startswith("fabric/fc-estc"):
                                            continue
                                        else:
                                            filtered_sdk_objects_list.append(sdk_object)

                                    if object_class.__name__ in ["UcsCentralStorageVsan"]:
                                        # We filter out VSANs in case we are looking for Storage VSANs in UCS Central
                                        if sdk_object.dn[len(dn + "/"):].startswith("fabric/san"):
                                            continue
                                        else:
                                            filtered_sdk_objects_list.append(sdk_object)

                            elif sdk_object.dn.startswith("fabric/lan/flowctrl/policy-"):
                                # Exception for Flow Control Policy
                                filtered_sdk_objects_list.append(sdk_object)

                        easyucs_objects_list = []
                        for sdk_object in sorted(filtered_sdk_objects_list,
                                                 key=lambda sdk_obj: [int(t) if t.isdigit() else t.lower()
                                                                      for t in re.split(r'(\d+)', sdk_obj.dn)]):
                            # We instantiate a Config Object for each corresponding SDK object
                            easyucs_objects_list.append(object_class(parent, None, sdk_object))
                        return easyucs_objects_list

            elif hasattr(object_class, "_UCS_SDK_OBJECTS_NAMES"):
                # Specific case for complex EasyUCS objects in UCS Central (e.g. Domain Group Remote Access)
                # that are made of multiple SDK objects
                filtered_sdk_objects_list = []
                for ucs_sdk_object_name in object_class._UCS_SDK_OBJECTS_NAMES:
                    if ucs_sdk_object_name in self.sdk_objects.keys():
                        if self.sdk_objects[ucs_sdk_object_name] is not None:
                            # We filter out SDK objects that are not under this Dn
                            for sdk_object in self.sdk_objects[ucs_sdk_object_name]:
                                if sdk_object.dn.startswith(dn + '/'):
                                    if "/" not in sdk_object.dn[len(dn + "/"):]:
                                        filtered_sdk_objects_list.append(sdk_object)

                if filtered_sdk_objects_list:
                    # We instantiate a single Config Object
                    return [object_class(parent, None, None)]
        return []

    def get_object(self, object_type=None, name="", org_path="", resolve_in_org_hierarchy=False,
                   resolve_to_default=True):
        """
        Gets a policy object from the config given its type, name and org path
        :param object_type: type of object to get (class)
        :param name: name of the object to get
        :param org_path: org path of the object to get
        :param resolve_in_org_hierarchy: whether to perform Policy Resolution up the org hierarchy to find the object
        :param resolve_to_default: whether to perform Policy Resolution for "default" if named object is not found
        :return: object if successful, None otherwise
        """
        if object_type is None:
            self.logger(level="error", message="Missing object type in get object request")
            return None

        if not name:
            self.logger(level="error", message="Invalid name in get object request")
            return None

        if not org_path:
            self.logger(level="error", message="Invalid org path in get object request")
            return None

        if not isinstance(resolve_in_org_hierarchy, bool):
            self.logger(level="error", message="Invalid resolve_in_org_hierarchy in get object request")
            return None

        # Determining the section name to look for in the config
        if not hasattr(object_type, "_CONFIG_SECTION_NAME"):
            self.logger(level="error", message="Invalid object type in get object request")
            return None
        section_name = object_type._CONFIG_SECTION_NAME

        # Identifying the org in which to look for in the config
        current_pointer = self
        for suborg in org_path.split("/"):
            if not current_pointer.orgs:
                self.logger(level="debug",
                            message="Could not find org " + str(suborg) + " of path " + str(org_path) + " in config")
                return None
            found_org = False
            for org in current_pointer.orgs:
                if org.name == suborg:
                    current_pointer = org
                    found_org = True
                    break
            if not found_org:
                self.logger(level="debug",
                            message="Could not find org " + str(suborg) + " of path " + str(org_path) + " in config")
                return None
        org = current_pointer

        if not resolve_in_org_hierarchy:
            # Checking in the section name of the found org if an object with the given name exists
            if not hasattr(org, section_name):
                self.logger(level="debug", message="No section named " + section_name + " in org " + str(org_path))
                return None
            if not getattr(org, section_name):
                self.logger(level="debug", message="No item in section " + section_name + " of org " + str(org_path))
                return None
            if not isinstance(getattr(org, section_name), list):
                self.logger(level="debug",
                            message="Section " + section_name + " in org " + str(org_path) + " is not a list")
                return None
            for obj in getattr(org, section_name):
                if hasattr(obj, "name"):
                    if obj.name == name and isinstance(obj, object_type):
                        return obj

            self.logger(level="debug", message="Could not find " + object_type._CONFIG_NAME +
                                               " with name '" + str(name) + "' in org " + str(org_path))
        else:
            from config.ucs.ucsm.admin import UcsSystemOrg
            from config.ucs.ucsc.orgs import UcsCentralOrg

            # We do a first look up the org hierarchy to find the named object
            current_org = org
            while any([isinstance(current_org, x) for x in [UcsSystemOrg, UcsCentralOrg]]):
                if getattr(current_org, section_name):
                    for obj in getattr(current_org, section_name):
                        if hasattr(obj, "name"):
                            if obj.name == name and isinstance(obj, object_type):
                                return obj
                current_org = current_org._parent

            self.logger(level="debug", message="Could not resolve " + object_type._CONFIG_NAME +
                                               " with name '" + str(name) + "' starting from org " + str(org_path))

            if resolve_to_default:
                # TODO: Properly define default object name based on the policy/pool type and handle 'global-default'
                default_object_name = "default"
                # If it is not found, we do a second look up the org hierarchy to find an object named "default"
                current_org = org
                while any([isinstance(current_org, x) for x in [UcsSystemOrg, UcsCentralOrg]]):
                    if getattr(current_org, section_name):
                        for obj in getattr(current_org, section_name):
                            if hasattr(obj, "name"):
                                if obj.name == default_object_name and isinstance(obj, object_type):
                                    return obj
                    current_org = current_org._parent

                self.logger(level="debug", message="Could not resolve " + object_type._CONFIG_NAME +
                                                   " with name '" + default_object_name +
                                                   "' starting from org " + str(org_path))
        return None

    def get_operational_policy_name_and_org_path(self, source_object=None, policy_type=""):
        """
        Gets the operational policy name and org path of a given type referenced by the source object
        :param source_object: A single EasyUCS object (Eg: UcsSystemServiceProfile) or a dictionary sub object
        (Eg: vnic)
        :param policy_type: type of the policy object to get (Eg: boot_policy)
        :return: (policy name, org path) if successful, (None, None) otherwise
        """
        if source_object is None:
            self.logger(level="error", message="Missing source object in get operational policy object request")
            return None, None
        if not policy_type:
            self.logger(level="error", message="Invalid policy type.")
            return None, None

        if isinstance(source_object, dict):
            # We are facing a sub-object (which is a dictionary)
            if not source_object.get("operational_state"):
                return None, None

            if not source_object["operational_state"].get(policy_type):
                return None, None

            if not source_object["operational_state"][policy_type].get("name"):
                return None, None

            # We add a warning in case the referenced policy name does not correspond to the operational policy name
            # This can happen in case a policy has been deleted, but profile still has the reference to it.
            # In that scenario, UCS will resolve the policy to use "default", so we will work with that one
            if source_object.get(policy_type, '') != source_object["operational_state"][policy_type]["name"]:
                self.device.logger(level="debug", message="Referenced policy " + policy_type + " with name " +
                                                          str(source_object.get(policy_type, "''")) + " has a " +
                                                          "different operational policy name: " +
                                                          str(source_object["operational_state"][policy_type]["name"]))

            if source_object["operational_state"][policy_type].get("org"):
                org_path = source_object["operational_state"][policy_type]["org"]
            else:
                return None, None

            referenced_policy_name = source_object["operational_state"][policy_type]["name"]

        else:
            # We are facing an EasyUCS object
            if not getattr(source_object, "operational_state", None):
                return None, None

            if not source_object.operational_state.get(policy_type):
                return None, None

            if not source_object.operational_state[policy_type].get("name"):
                return None, None

            # We add a warning in case the referenced policy name does not correspond to the operational policy name
            # This can happen in case a policy has been deleted, but profile still has the reference to it.
            # In that scenario, UCS will resolve the policy to use "default", so we will work with that one
            if getattr(source_object, policy_type) != source_object.operational_state[policy_type]["name"]:
                self.device.logger(
                    level="debug", message="Referenced policy " + policy_type + " with name '" +
                    str(getattr(source_object, policy_type)) + "' has a different" + " operational policy name: " +
                    str(source_object.operational_state[policy_type]["name"]))

            if source_object.operational_state[policy_type].get("org"):
                org_path = source_object.operational_state[policy_type]["org"]
            else:
                return None, None

            referenced_policy_name = source_object.operational_state[policy_type]["name"]

        return referenced_policy_name, org_path

    def refresh_config_handle(self):
        """
        Change all the references to a UCS Handle in a config in case of a change of handle attributes
        (IP address, username or password). For example: During a reset, or after an initial setup
        Check the first layer of the config and the second layer. No other _handle should be in another layer.

        :return: True if successful, False otherwise
        """
        self.handle = self.parent.parent.handle

        self._refresh_handle(current_object=self, handle=self.parent.parent.handle)

        self.logger(level="debug", message="Successfully refreshed config handle")
        return True

    def _refresh_handle(self, current_object=None, handle=None):
        """
        Recursively resets the reference to a UCS handle
        :param current_object: portion of the config file currently being looked at
        :return: nothing
        """
        if hasattr(current_object, "_handle"):
            current_object._handle = handle

        for attr in vars(current_object):
            if not attr.startswith('_') and not attr == "dn" and getattr(current_object, attr) is not None:
                obj = getattr(current_object, attr)
                if isinstance(obj, list):
                    for subobject in obj:
                        if not isinstance(subobject, (str, float, int, dict)):
                            self._refresh_handle(current_object=subobject, handle=handle)

    def resolve_operational_pool_name_and_org_path(self, source_objects=None, pool_type=""):
        """
        Resolves a pool object from the config given its type using the UCS source_object(s)
        :param source_objects: A list containing either a single EasyUCS object (Eg: UcsSystemServiceProfile) or a
         dict sub object (Eg: vnic) with its parent EasyUCS object (Eg: UcsSystemLanConnectivityPolicy) in that order
        :param pool_type: type of the pool object to get (Eg: ip_pool)
        :return: (pool name, org path) if successful, (None, None) otherwise
        """
        if not isinstance(source_objects, list):
            self.logger(level="error", message="No source objects provided when resolving the pool.")
            return None, None
        if 1 > len(source_objects) > 2:
            self.logger(level="error", message="Invalid number of source objects when resolving the pool.")
            return None, None
        if not pool_type:
            self.logger(level="error", message="Invalid pool type when resolving the pool.")
            return None, None

        source_object = source_objects[0]
        if len(source_objects) == 2:
            parent_object = source_objects[1]
            if not isinstance(parent_object, GenericUcsConfigObject):
                self.logger(level="error", message="Invalid parent object type when resolving the pool.")
                return None, None
            if getattr(parent_object, "_POLICY_MAPPING_TABLE", None):
                if not source_object.get("_object_type"):
                    self.logger(level="error", message="Missing attribute _object_type when resolving the pool.")
                    return None, None
                if source_object["_object_type"] not in parent_object._POLICY_MAPPING_TABLE:
                    self.logger(level="error",
                                message=f"Missing attribute {source_object['_object_type']} when resolving the pool.")
                    return None, None
                pool_object_type = parent_object._POLICY_MAPPING_TABLE[source_object["_object_type"]][0].get(pool_type)
                source_org = parent_object._parent
            else:
                self.logger(level="error", message="Missing policy mapping table when resolving the pool.")
                return None, None
        else:
            if not isinstance(source_object, GenericUcsConfigObject):
                self.logger(level="error", message="Invalid object type when resolving the pool.")
                return None, None
            if getattr(source_object, "_POLICY_MAPPING_TABLE", None):
                pool_object_type = source_object._POLICY_MAPPING_TABLE.get(pool_type)
                source_org = source_object._parent
            else:
                self.logger(level="error", message="Missing policy mapping table when resolving the pool.")
                return None, None

        if not pool_object_type:
            self.logger(level="error", message="Pool type not in policy mapping table.")
            return None, None
        from config.ucs.ucsm.admin import UcsSystemOrg
        from config.ucs.ucsc.orgs import UcsCentralOrg
        if not any([isinstance(source_org, x) for x in [UcsSystemOrg, UcsCentralOrg]]):
            self.logger(level="error", message="Could not find the parent org.")
            return None, None

        pool_name, pool_org_path = self.get_operational_policy_name_and_org_path(source_object=source_object,
                                                                                 policy_type=pool_type)
        if pool_name and pool_org_path:
            # We found the result from the operational state. We return the pool name and pool org path.
            return pool_name, pool_org_path
        else:
            # We did not find the result from the operational state. We will try to resolve it
            # We first need to get the name of the pool we are looking for
            if isinstance(source_object, dict):
                # We are facing a sub-object (which is a dictionary)
                if pool_type not in source_object:
                    return None, None
                if source_object[pool_type]:
                    pool_name = source_object[pool_type]
                else:
                    return None, None
            else:
                # We are facing an EasyUCS object
                if not getattr(source_object, pool_type):
                    return None, None
                if getattr(source_object, pool_type):
                    pool_name = getattr(source_object, pool_type)
                else:
                    return None, None

            # We now try to resolve the pool name over the UCS org hierarchy
            pool = self.get_object(object_type=pool_object_type, name=pool_name, org_path=source_org.get_org_path(),
                                   resolve_in_org_hierarchy=True, resolve_to_default=False)
            if pool:
                return pool_name, pool._parent.get_org_path()

            # We haven't been able to manually resolve the pool, so we only return its name
            return pool_name, None


class UcsSystemConfig(GenericUcsConfig):
    _BIOS_TOKENS_MIN_REQUIRED_VERSION = "3.2(1d)"
    _BIOS_MODERN_SDK_OBJECTS_TO_FETCH = ['biosTokenParam', 'biosTokenSettings']
    _BIOS_LEGACY_SDK_OBJECTS_TO_FETCH = [
        'biosVfASPMSupport', 'biosVfAllUSBDevices', 'biosVfAltitude',
        'biosVfAssertNMIOnPERR', 'biosVfBootOptionRetry',
        'biosVfCPUHardwarePowerManagement', 'biosVfCPUPerformance',
        'biosVfConsistentDeviceNameControl', 'biosVfConsoleRedirection',
        'biosVfCoreMultiProcessing', 'biosVfDDR3VoltageSelection',
        'biosVfDRAMClockThrottling', 'biosVfDirectCacheAccess',
        'biosVfDramRefreshRate', 'biosVfEnergyPerformanceTuning',
        'biosVfEnhancedIntelSpeedStepTech', 'biosVfExecuteDisableBit',
        'biosVfFRB2Timer', 'biosVfFrequencyFloorOverride', 'biosVfFrontPanelLockout',
        'biosVfIOEMezz1OptionROM', 'biosVfIOENVMe1OptionROM',
        'biosVfIOENVMe2OptionROM', 'biosVfIOESlot1OptionROM',
        'biosVfIOESlot2OptionROM', 'biosVfIntegratedGraphics',
        'biosVfIntegratedGraphicsApertureSize', 'biosVfIntelEntrySASRAIDModule',
        'biosVfIntelHyperThreadingTech', 'biosVfIntelTrustedExecutionTechnology',
        'biosVfIntelTurboBoostTech', 'biosVfIntelVTForDirectedIO',
        'biosVfIntelVirtualizationTechnology', 'biosVfInterleaveConfiguration',
        'biosVfLocalX2Apic', 'biosVfLvDIMMSupport', 'biosVfMaxVariableMTRRSetting',
        'biosVfMaximumMemoryBelow4GB', 'biosVfMemoryMappedIOAbove4GB',
        'biosVfMirroringMode', 'biosVfNUMAOptimized',
        'biosVfOSBootWatchdogTimerPolicy', 'biosVfOSBootWatchdogTimerTimeout',
        'biosVfOnboardGraphics', 'biosVfOnboardStorage', 'biosVfOutOfBandManagement',
        'biosVfPCILOMPortsConfiguration', 'biosVfPCIROMCLP', 'biosVfPCISlotLinkSpeed',
        'biosVfPCISlotOptionROMEnable', 'biosVfPOSTErrorPause',
        'biosVfPSTATECoordination', 'biosVfPackageCStateLimit', 'biosVfProcessorC1E',
        'biosVfProcessorC3Report', 'biosVfProcessorC6Report',
        'biosVfProcessorC7Report', 'biosVfProcessorCMCI', 'biosVfProcessorCState',
        'biosVfProcessorEnergyConfiguration', 'biosVfProcessorPrefetchConfig',
        'biosVfQPILinkFrequencySelect', 'biosVfQPISnoopMode', 'biosVfQuietBoot',
        'biosVfRedirectionAfterBIOSPOST', 'biosVfResumeOnACPowerLoss',
        'biosVfSBMezz1OptionROM', 'biosVfSBNVMe1OptionROM', 'biosVfSIOC1OptionROM',
        'biosVfSIOC2OptionROM', 'biosVfScrubPolicies',
        'biosVfSelectMemoryRASConfiguration', 'biosVfSerialPortAEnable',
        'biosVfTrustedPlatformModule', 'biosVfUSBBootConfig', 'biosVfUSBConfiguration',
        'biosVfUSBFrontPanelAccessLock', 'biosVfUSBPortConfiguration',
        'biosVfUSBSystemIdlePowerOptimizingSetting', 'biosVfVGAPriority',
        'biosVfWorkloadConfiguration',
    ]
    _UCSM_SPECIFIC_SDK_OBJECTS_TO_FETCH = [
        'aaaAuthRealm', 'aaaConsoleAuth', 'aaaDefaultAuth', 'aaaDomain', 'aaaDomainAuth', 'aaaEpAuthProfile',
        'aaaEpUser', 'aaaLdapEp', 'aaaLdapGroup', 'aaaLdapGroupRule', 'aaaLdapProvider', 'aaaLocale', 'aaaOrg',
        'aaaPreLoginBanner', 'aaaProviderGroup', 'aaaProviderRef', 'aaaPwdProfile', 'aaaRadiusEp',
        'aaaRadiusProvider', 'aaaRole', 'aaaSshAuth', 'aaaTacacsPlusEp', 'aaaTacacsPlusProvider', 'aaaUserEp',
        'aaaUserLocale', 'aaaUserRole', 'adaptorAzureQosProfile', 'adaptorCapQual', 'adaptorEthAdvFilterProfile',
        'adaptorEthArfsProfile', 'adaptorEthCompQueueProfile', 'adaptorEthFailoverProfile',
        'adaptorEthGENEVEProfile', 'adaptorEthInterruptProfile', 'adaptorEthInterruptScalingProfile',
        'adaptorEthNVGREProfile', 'adaptorEthOffloadProfile', 'adaptorEthRecvQueueProfile', 'adaptorEthRoCEProfile',
        'adaptorEthVxLANProfile', 'adaptorEthWorkQueueProfile', 'adaptorFcCdbWorkQueueProfile',
        'adaptorFcErrorRecoveryProfile', 'adaptorFcFnicProfile', 'adaptorFcInterruptProfile',
        'adaptorFcPortFLogiProfile', 'adaptorFcPortPLogiProfile', 'adaptorFcPortProfile',
        'adaptorFcRecvQueueProfile', 'adaptorFcVhbaTypeProfile', 'adaptorFcWorkQueueProfile',
        'adaptorHostEthIfProfile', 'adaptorHostFcIfProfile', 'adaptorHostIscsiIfProfile', 'adaptorProtocolProfile',
        'adaptorPTP', 'adaptorQual', 'adaptorRssProfile', 'biosVProfile', 'callhomeAnonymousReporting',
        'callhomeDest', 'callhomeEp', 'callhomePeriodicSystemInventory', 'callhomePolicy', 'callhomeProfile',
        'callhomeSmtp', 'callhomeSource', 'cimcvmediaConfigMountEntry', 'cimcvmediaMountConfigDef',
        'cimcvmediaMountConfigPolicy', 'commCimcWebService', 'commCimxml', 'commDateTime', 'commDns',
        'commDnsProvider', 'commFabricInterconnectAuditLogs', 'commHttp', 'commHttps','commMonitor', 'commShellSvcLimits',
        'commSnmp', 'commSnmpTrap', 'commSnmpUser', 'commSsh', 'commSyslog', 'commSyslogClient', 'commSyslogConsole',
        'commSyslogFile', 'commSyslogMonitor', 'commSyslogSource', 'commTelnet', 'commWebSvcLimits', 'computeBoard',
        'computeChassisDiscPolicy', 'computeChassisQual', 'computeFanPolicy', 'computeGraphicsCardPolicy',
        'computeHwChangeDiscPolicy', 'computeKvmMgmtPolicy', 'computeMemoryConfigPolicy',
        'computeModularChassisFanPolicy', 'computePhysicalQual', 'computePool', 'computePooledRackUnit',
        'computePooledSlot', 'computePoolingPolicy', 'computePortDiscPolicy', 'computePowerExtendedPolicy',
        'computePowerSavePolicy', 'computePowerSyncPolicy', 'computePsuPolicy', 'computeQual', 'computeRackQual',
        'computeScrubPolicy', 'computeServerDiscPolicy', 'computeServerMgmtPolicy', 'computeSlotQual',
        'cpmaintMaintPolicy', 'diagMemoryTest', 'diagRunPolicy', 'dpsecMac', 'epqosDefinition', 'epqosEgress',
        'equipmentBinding', 'equipmentChassisProfile', 'equipmentComputeConnPolicy', 'etherPIo', 'fabricBreakout',
        'fabricDceSwSrvEp', 'fabricDceSwSrvPcEp', 'fabricEthEstcEp', 'fabricEthEstcPc', 'fabricEthEstcPcEp',
        'fabricEthLanEp', 'fabricEthLanFlowMonitoring', 'fabricEthLanPc', 'fabricEthLanPcEp', 'fabricEthLinkProfile',
        'fabricEthMon', 'fabricEthMonDestEp', 'fabricEthMonSrcRef', 'fabricEthMonSrcEp', 'fabricEthTargetEp',
        'fabricEthVlanPc', 'fabricEthVlanPortEp', 'fabricFcEndpoint', 'fabricFcEstcEp', 'fabricFcMon',
        'fabricFcMonSrcEp', 'fabricFcMonSrcRef', 'fabricFcSan', 'fabricFcSanEp', 'fabricFcSanPc', 'fabricFcSanPcEp',
        'fabricFcUserZone', 'fabricFcVsanPc', 'fabricFcVsanPortEp', 'fabricFcZoneProfile', 'fabricFcoeEstcEp',
        'fabricFcoeSanEp', 'fabricFcoeSanPc', 'fabricFcoeSanPcEp', 'fabricFcoeVsanPortEp', 'fabricFlowMonDefinition',
        'fabricFlowMonExporterProfile', 'fabricLacpPolicy', 'fabricLanCloud', 'fabricLanCloudPolicy',
        'fabricLanPinGroup', 'fabricLanPinTarget', 'fabricLifeTime', 'fabricMacSec', 'fabricMacSecEapol',
        'fabricMacSecIfConfig', 'fabricMacSecKeyChain', 'fabricMacSecKey', 'fabricMacSecPolicy',
        'fabricMonOriginIP', 'fabricMonOriginSVI', 'fabricMulticastPolicy', 'fabricNetflowCollector',
        'fabricNetflowIPv4Addr', 'fabricNetflowMonitor', 'fabricNetflowMonitorRef', 'fabricNetflowMonExporter',
        'fabricNetflowMonExporterRef', 'fabricNetflowMonSession', 'fabricNetflowMonSrcRef',
        'fabricNetflowTimeoutPolicy', 'fabricNetGroup', 'fabricNetGroupRef', 'fabricOrgVlanPolicy',
        'fabricPooledVlan', 'fabricRemoteConfig', 'fabricReservedVlan', 'fabricSanCloud', 'fabricSanPinGroup',
        'fabricSanPinTarget', 'fabricUdldLinkPolicy', 'fabricUdldPolicy', 'fabricVCon', 'fabricVConProfile',
        'fabricVlan', 'fabricVlanGroupReq', 'fabricVlanReq', 'fabricVsan', 'faultPolicy', 'fcPIo', 'fcpoolBlock',
        'fcpoolInitiators', 'fcpoolOui', 'fcpoolOuis', 'firmwareAutoSyncPolicy', 'firmwareChassisPack',
        'firmwareComputeHostPack', 'firmwareExcludeChassisComponent', 'firmwareExcludeServerComponent',
        'firmwarePackItem', 'flowctrlItem', 'ipIpV4StaticTargetAddr', 'ippoolBlock', 'ippoolIpV6Block',
        'ippoolPool', 'iqnpoolBlock', 'iqnpoolPool', 'iscsiAuthProfile', 'lsBinding', 'lsPower', 'lsRequirement',
        'lsServer', 'lsServerExtension', 'lsVConAssign', 'lsbootBootSecurity', 'lsbootDef',
        'lsbootDefaultLocalImage', 'lsbootEFIShell', 'lsbootEmbeddedLocalDiskImage',
        'lsbootEmbeddedLocalDiskImagePath', 'lsbootEmbeddedLocalLunImage', 'lsbootIScsi', 'lsbootIScsiImagePath',
        'lsbootLan', 'lsbootLanImagePath', 'lsbootLocalDiskImage', 'lsbootLocalDiskImagePath',
        'lsbootLocalHddImage', 'lsbootLocalLunImagePath', 'lsbootNvme', 'lsbootPolicy', 'lsbootSan',
        'lsbootSanCatSanImage', 'lsbootSanCatSanImagePath', 'lsbootStorage', 'lsbootUEFIBootParam',
        'lsbootUsbExternalImage', 'lsbootUsbFlashStorageImage', 'lsbootUsbInternalImage', 'lsbootVirtualMedia',
        'lsmaintMaintPolicy', 'lstorageControllerDef', 'lstorageControllerModeConfig', 'lstorageControllerRef',
        'lstorageDasScsiLun', 'lstorageDiskGroupConfigPolicy', 'lstorageDiskGroupQualifier', 'lstorageDiskSlot',
        'lstorageDiskZoningPolicy', 'lstorageHybridDriveSlotConfig', 'lstorageLocal', 'lstorageLocalDiskConfigRef',
        'lstorageLogin', 'lstorageLunSetConfig', 'lstorageProfile', 'lstorageProfileBinding', 'lstorageProfileDef',
        'lstorageRemote', 'lstorageSasExpanderConfigPolicy', 'lstorageVirtualDriveDef', 'macpoolBlock', 'macpoolPool',
        'memoryPersistentMemoryGoal', 'memoryPersistentMemoryLocalSecurity',
        'memoryPersistentMemoryLogicalNamespace', 'memoryPersistentMemoryPolicy', 'memoryQual',
        'mgmtBackupExportExtPolicy', 'mgmtBackupPolicy', 'mgmtCfgExportPolicy', 'mgmtIPv6IfAddr',
        'mgmtInbandProfile', 'mgmtKmipCertPolicy', 'mgmtSpdmCertificate', 'mgmtSpdmCertificatePolicy', 'mgmtVnet',
        'networkElement', 'nwctrlDefinition', 'orgOrg', 'pfcWatchDog', 'policyCommunication', 'policyConfigBackup',
        'policyControlEp', 'policyDateTime', 'policyDns', 'policyEquipment', 'policyFault', 'policyInfraFirmware',
        'policyMEp', 'policyMonitoring', 'policyPortConfig', 'policyPowerMgmt', 'policyPsu', 'policySecurity',
        'powerChassisMember', 'powerFexMember', 'powerFIMember', 'powerGroup', 'powerGroupQual', 'powerMgmtPolicy',
        'powerPolicy', 'processorQual', 'powerRackUnitMember', 'qosclassEthBE', 'qosclassEthClassified',
        'qosclassFc', 'qosclassSlowDrain', 'solConfig', 'solPolicy', 'statsThr32Definition', 'statsThr32Value',
        'statsThr64Definition', 'statsThr64Value', 'statsThrFloatDefinition', 'statsThrFloatValue',
        'statsThresholdClass', 'statsThresholdPolicy', 'storageConnectionPolicy', 'storageFcTargetEp',
        'storageIniGroup', 'storageInitiator', 'storageLocalDiskConfigDef', 'storageLocalDiskConfigPolicy',
        'storageQual', 'storageScsiLunRef', 'storageVirtualDrive', 'storageVsanRef', 'sysdebugBackupBehavior',
        'sysdebugMEpLogPolicy', 'topInfoPolicy',
        'topInfoSyncPolicy', 'uuidpoolBlock', 'uuidpoolPool', 'uuidpoolPooled', 'vnicConnDef', 'vnicDynamicCon',
        'vnicDynamicConPolicy', 'vnicDynamicConPolicyRef', 'vnicEther', 'vnicEtherIf', 'vnicFc', 'vnicFcGroupDef',
        'vnicFcIf', 'vnicFcNode', 'vnicIPv4Dhcp', 'vnicIPv4If', 'vnicIPv4IscsiAddr', 'vnicIpV4PooledAddr',
        'vnicIPv4PooledIscsiAddr', 'vnicIpV4StaticAddr', 'vnicIPv6IscsiAddr', 'vnicIPv6PooledIscsiAddr',
        'vnicIpV6StaticAddr', 'vnicIScsi', 'vnicIScsiAutoTargetIf', 'vnicIScsiBootParams', 'vnicIScsiBootVnic',
        'vnicIScsiLCP', 'vnicIScsiNode', 'vnicIPv6IScsiStaticTargetIf', 'vnicIScsiStaticTargetIf',
        'vnicIpV4MgmtPooledAddr', 'vnicIpV6MgmtPooledAddr', 'vnicLanConnPolicy', 'vnicLanConnTempl', 'vnicLun',
        'vnicSanConnPolicy', 'vnicSanConnTempl', 'vnicSriovHpnConPolicy', 'vnicSriovHpnConPolicyRef',
        'vnicUsnicConPolicy', 'vnicUsnicConPolicyRef', 'vnicVhbaBehPolicy', 'vnicVlan', 'vnicVmqConPolicy',
        'vnicVmqConPolicyRef', 'vnicVnicBehPolicy',
    ]
    _CONFIG_SECTION_ATTRIBUTES_MAP = {
        "appliance_network_control_policies": "Appliance Network Control Policies",
        "appliance_port_channels": "Appliance Port-Channels",
        "appliance_ports": "Appliance Ports",
        "appliance_vlans": "Appliance VLANs",
        "authentication": "Authentication",
        "backup_export_policy": "Backup Export Policy",
        "breakout_ports": "Breakout Ports",
        "call_home": "Call Home",
        "communication_services": "Communication Services",
        "device_connector": "Device Connector",
        "dns": "DNS",
        "fabric_interconnect_audit_logs": "Fabric Interconnect Audit Logs",
        "fc_zone_profiles": "FC Zone Profiles",
        "fcoe_port_channels": "FCoE Port Channels",
        "fcoe_storage_ports": "FCoE Storage Ports",
        "fcoe_uplink_ports": "FCoE Uplink Ports",
        "global_fault_policy": "Global Fault Policy",
        "global_policies": "Global Policies",
        "kmip_client_cert_policy": "KMIP Certification Policies",
        "lan_pin_groups": "LAN Pin Groups",
        "lan_port_channels": "LAN Port-Channels",
        "lan_traffic_monitoring_sessions": "LAN Traffic Monitoring Sessions",
        "lan_uplink_ports": "LAN Uplink Ports",
        "ldap": "LDAP",
        "link_profiles": "Link Profiles",
        "local_users": "Local Users",
        "local_users_properties": "Local Users Properties",
        "locales": "Locales",
        "macsec": "MACsec",
        "management_interfaces": "Management Interfaces",
        "netflow_monitoring": "NetFlow Monitoring",
        "orgs": "Organizations",
        "oui_pools": "OUI Pools",
        "port_auto_discovery_policy": "Port Auto-Discovery Policy",
        "power_groups": "Power Groups",
        "pre_login_banner": "Pre-Login Banner",
        "qos_system_class": "QoS System Class",
        "radius": "RADIUS",
        "roles": "Roles",
        "scrub_policies": "Scrub Policies",
        "san_pin_groups": "SAN Pin Groups",
        "san_port_channels": "SAN Port-Channels",
        "san_storage_ports": "SAN Storage Ports",
        "san_traffic_monitoring_sessions": "SAN Traffic Monitoring Sessions",
        "san_unified_ports": "SAN Unified Ports",
        "san_uplink_ports": "SAN Uplink Ports",
        "sel_policy": "SEL Policy",
        "server_ports": "Server Ports",
        "slow_drain_timers": "Slow Drain Timers",
        "storage_vsans": "Storage VSANs",
        "switching_mode": "Switching Mode",
        "syslog": "Syslog",
        "system": "System",
        "tacacs": "TACACS",
        "timezone_mgmt": "Timezone Management",
        "traffic_monitoring_configuration": "Traffic Monitoring Configuration",
        "ucs_central": "UCS Central",
        "udld_link_policies": "UDLD Link Policies",
        "unified_storage_ports": "Unified Storage Ports",
        "unified_uplink_ports": "Unified Uplink Ports",
        "vlan_groups": "VLAN Groups",
        "vlans": "VLANs",
        "vsans": "VSANs",
        "watchdog_timers": "Watchdog Timers",
    }

    def __init__(self, parent=None):
        self.service_profile_plots = None
        self.orgs_plot = None

        self.appliance_network_control_policies = []
        self.appliance_port_channels = []
        self.appliance_ports = []
        self.appliance_vlans = []
        self.authentication = []
        self.backup_export_policy = []
        self.breakout_ports = []
        self.call_home = []
        self.communication_services = []
        self.device_connector = []
        self.dns = []
        self.global_fault_policy = []
        self.fabric_interconnect_audit_logs = []
        self.fc_zone_profiles = []
        self.fcoe_port_channels = []
        self.fcoe_storage_ports = []
        self.fcoe_uplink_ports = []
        self.global_policies = []
        self.kmip_client_cert_policy = []
        self.lan_pin_groups = []
        self.lan_port_channels = []
        self.lan_traffic_monitoring_sessions = []
        self.lan_uplink_ports = []
        self.ldap = []
        self.link_profiles = []
        self.local_users = []
        self.local_users_properties = []
        self.locales = []
        self.macsec = []
        self.management_interfaces = []
        self.netflow_monitoring = []
        self.orgs = []
        self.oui_pools = []
        self.port_auto_discovery_policy = []
        self.power_groups = []
        self.pre_login_banner = ""
        self.qos_system_class = []
        self.radius = []
        self.roles = []
        self.scrub_policies = []
        self.san_pin_groups = []
        self.san_port_channels = []
        self.san_storage_ports = []
        self.san_traffic_monitoring_sessions = []
        self.san_unified_ports = []
        self.san_uplink_ports = []
        self.sel_policy = []
        self.server_ports = []
        self.slow_drain_timers = []
        self.storage_vsans = []
        self.switching_mode = []
        self.syslog = []
        self.system = []
        self.tacacs = []
        self.timezone_mgmt = []
        self.traffic_monitoring_configuration = []
        self.ucs_central = []
        self.udld_link_policies = []
        self.unified_storage_ports = []
        self.unified_uplink_ports = []
        self.vlan_groups = []
        self.vlans = []
        self.vsans = []
        self.watchdog_timers = []
        GenericUcsConfig.__init__(self, parent=parent)

        # List of attributes to be exported in a config export
        self.export_list = self._CONFIG_SECTION_ATTRIBUTES_MAP.keys()

    def check_if_ports_config_requires_reboot(self):
        """
        Checks if the config will require a reboot when pushed because of port type changes (Unified Ports, Breakout)
        :return: True if config push will require a reboot because of port type changes, False otherwise
        """
        # FIXME: make sure we are connected to the live system
        # FIXME: IMPROVEMENT: determine the exact list of reboot reasons and return them as a dict

        # We first need to check for current ports types on the live system
        try:
            etherpio_list = self.device.query(mode="classid", target="etherPIo")
            fcpio_list = self.device.query(mode="classid", target="fcPIo")
        except ConnectionRefusedError:
            self.logger(level="error", message="Error while communicating with UCS System")
            return
        except UcsException:
            self.logger(level="error", message="Unable to fetch current ports types on UCS System")
            return
        except urllib.error.URLError:
            self.logger(level="error", message="Timeout error while fetching current ports types on UCS System")
            return

        # We create lists of ports of type Ethernet or FC from the configuration
        eth_port_config_list = [{"fabric": eth_port.fabric, "slot_id": eth_port.slot_id, "port_id": eth_port.port_id,
                                 "aggr_id": eth_port.aggr_id} for eth_port in (self.lan_uplink_ports +
                                                                               self.fcoe_storage_ports +
                                                                               self.fcoe_uplink_ports +
                                                                               self.appliance_ports +
                                                                               self.server_ports +
                                                                               self.unified_storage_ports +
                                                                               self.unified_uplink_ports)]

        fc_port_config_list = [{"fabric": fc_port.fabric, "slot_id": fc_port.slot_id, "port_id": fc_port.port_id} for
                               fc_port in (self.san_storage_ports + self.san_uplink_ports)]

        # We add the list of unified ports - since they are given as a range, we need to handle this differently
        for entry in self.san_unified_ports:
            start = int(entry.port_id_start)
            end = int(entry.port_id_end)
            for port in range(start, end + 1):
                fc_port_config_list.append({"fabric": entry.fabric, "slot_id": entry.slot_id, "port_id": str(port)})

        # We then deduplicate the list
        fc_port_config_list = [dict(t) for t in set([tuple(d.items()) for d in fc_port_config_list])]

        # We check if there are Ethernet ports that will need to be converted to FC ports
        for fc_port in fc_port_config_list:
            for eth_port in etherpio_list:
                if fc_port["fabric"] == eth_port.switch_id and fc_port["slot_id"] == eth_port.slot_id and\
                        fc_port["port_id"] == eth_port.port_id and eth_port.aggr_port_id == "0":
                    self.logger(level="debug", message="A reboot will be required because Ethernet ports will be " +
                                                       "converted to FC ports")
                    return True

        # We check if there are FC ports that will need to be converted to Ethernet ports
        for eth_port in eth_port_config_list:
            for fc_port in fcpio_list:
                if eth_port["fabric"] == fc_port.switch_id and eth_port["slot_id"] == fc_port.slot_id and\
                        eth_port["port_id"] == fc_port.port_id:
                    self.logger(level="debug", message="A reboot will be required because FC ports will be " +
                                                       "converted to Ethernet ports")
                    return True

        # We check if there are native Ethernet ports that will need to be converted to Breakout ports
        for breakout_port in self.breakout_ports:
            for eth_port in etherpio_list:
                if breakout_port.fabric == eth_port.switch_id and breakout_port.slot_id == eth_port.slot_id and\
                        breakout_port.port_id == eth_port.port_id and eth_port.aggr_port_id == "0":
                    self.logger(level="debug", message="A reboot will be required because Ethernet ports will be " +
                                                       "converted to Breakout ports")
                    return True

        # We check if there are Breakout ports that will need to be converted to native Ethernet ports
        for etherpio in etherpio_list:
            for eth_port in eth_port_config_list:
                if etherpio.switch_id == eth_port["fabric"] and etherpio.slot_id == eth_port["slot_id"] and\
                        etherpio.aggr_port_id == eth_port["port_id"] and eth_port["aggr_id"] is None:
                    self.logger(level="debug", message="A reboot will be required because Breakout ports will be " +
                                                       "converted to Ethernet ports")
                    return True

        return False

    def check_if_switching_mode_config_requires_reboot(self):
        """
        Checks if the config will require a reboot when pushed because of switching mode changes (Ethernet & FC)
        :return: True if config push will require a reboot because of switching mode changes, False otherwise
        """
        # FIXME: make sure we are connected to the live system
        # FIXME: IMPROVEMENT: determine the exact list of reboot reasons and return them as a dict

        # We first need to check for current Ethernet & FC switching modes on the live system
        try:
            fabric_lan_cloud_list = self.device.query(mode="classid", target="fabricLanCloud")
            fabric_san_cloud_list = self.device.query(mode="classid", target="fabricSanCloud")

            if fabric_lan_cloud_list:
                fabric_lan_cloud = fabric_lan_cloud_list[0]
            else:
                self.logger(level="error", message="Could not get currently running Ethernet switching mode")
                return None

            if fabric_san_cloud_list:
                fabric_san_cloud = fabric_san_cloud_list[0]
            else:
                self.logger(level="error", message="Could not get currently running FC switching mode")
                return None

            # We get the running Ethernet & FC switching mode
            eth_switching_mode = fabric_lan_cloud.mode
            fc_switching_mode = fabric_san_cloud.mode

            # We check if the Ethernet switching mode in the config is different from the running mode
            if self.switching_mode:
                if self.switching_mode[0].ethernet_mode != eth_switching_mode:
                    self.logger(level="debug",
                                message="A reboot will be required because Ethernet switching mode will be changed")
                    return True

            # We check if the FC switching mode in the config is different from the running mode
            if self.switching_mode:
                if self.switching_mode[0].fc_mode != fc_switching_mode:
                    self.logger(level="debug",
                                message="A reboot will be required because FC switching mode will be changed")
                    return True

            return False
        except Exception:
            self.logger(level="error", message="Error while trying to fetch switching mode info on the live system")
            return False

    def _fetch_sdk_objects(self, force=False):
        GenericUcsConfig._fetch_sdk_objects(self, force=force)

        # If any of the mandatory tasksteps fails then return False
        from api.api_server import easyucs
        if easyucs and self.device.task and \
                easyucs.task_manager.is_any_taskstep_failed(uuid=self.device.task.metadata.uuid):
            self.logger(level="error", message="Failed to fetch one or more common SDK objects. "
                                               "Stopping the config fetch.")
            return False

        version_min_required = UcsVersion(self._BIOS_TOKENS_MIN_REQUIRED_VERSION)

        # Depending on the UCSM version, we only fetch some SDK objects in order to gain time by making fewer queries
        if self.device.version.__ge__(version_min_required):
            self.logger(level="debug", message="Fetching BIOS Tokens for config")
            bios_sdk_objects_to_fetch = self._BIOS_MODERN_SDK_OBJECTS_TO_FETCH
        else:
            self.logger(level="debug", message="Fetching legacy BIOS objects for config")
            bios_sdk_objects_to_fetch = self._BIOS_LEGACY_SDK_OBJECTS_TO_FETCH

        # List of SDK objects to fetch that are only available in UCS System
        sdk_objects_to_fetch = self._UCSM_SPECIFIC_SDK_OBJECTS_TO_FETCH + bios_sdk_objects_to_fetch

        self.logger(level="debug",
                    message="Fetching " + self.device.metadata.device_type_long + " SDK objects for config")

        if self.device.task is not None:
            self.device.task.taskstep_manager.start_taskstep(
                name="FetchConfigUcsSystemSdkObjects",
                description="Fetching " + self.device.metadata.device_type_long + " SDK Config Objects")

        failed_to_fetch = []
        for sdk_object_name in sdk_objects_to_fetch:
            try:
                self.sdk_objects[sdk_object_name] = self.handle.query_classid(sdk_object_name,
                                                                              timeout=self.device.timeout)
                self.logger(level="debug", message="Fetched " + str(len(self.sdk_objects[sdk_object_name])) +
                                                   " objects of class " + sdk_object_name)
            except (UcsException, ImcException) as err:
                if err.error_code in ["ERR-xml-parse-error", "0"] and \
                        "no class named " + sdk_object_name in err.error_descr:
                    self.logger(level="debug", message="No UCS class named " + sdk_object_name)
                else:
                    self.logger(level="error",
                                message="Error while trying to fetch " + self.device.metadata.device_type_long +
                                        " class " + sdk_object_name + ": " + str(err))
                    failed_to_fetch.append(sdk_object_name)
            except ConnectionRefusedError:
                self.logger(level="error",
                            message="Error while communicating with " + self.device.metadata.device_type_long +
                                    " class " + sdk_object_name + ": Connection refused")
                failed_to_fetch.append(sdk_object_name)
            except urllib.error.URLError:
                self.logger(level="error", message="Timeout error while fetching " +
                                                   self.device.metadata.device_type_long + " class " + sdk_object_name)
                failed_to_fetch.append(sdk_object_name)
            except http.client.RemoteDisconnected:
                self.logger(level="error",
                            message="Connection closed while fetching " + self.device.metadata.device_type_long +
                                    " class " + sdk_object_name)
                failed_to_fetch.append(sdk_object_name)
            except Exception as err:
                self.logger(level="error", message="Error while fetching " + self.device.metadata.device_type_long +
                                                   " class " + sdk_object_name + ": " + str(err))
                failed_to_fetch.append(sdk_object_name)

        # We retry all SDK objects that failed to fetch properly
        if failed_to_fetch:
            duplicate_failed_to_fetch = failed_to_fetch.copy()
            for sdk_object_name in duplicate_failed_to_fetch:
                self.logger(level="info", message="Retrying to fetch " + sdk_object_name)
                try:
                    # While retying, we query for UCS sdk objects with twice the timeout value.
                    self.sdk_objects[sdk_object_name] = self.handle.query_classid(sdk_object_name,
                                                                                  timeout=self.device.timeout * 2)
                    self.logger(level="debug", message="Fetched " + str(len(self.sdk_objects[sdk_object_name])) +
                                                       " objects of class " + sdk_object_name)
                    failed_to_fetch.remove(sdk_object_name)
                except (UcsException, ImcException) as err:
                    self.logger(level="error",
                                message="Error while trying to fetch " + self.device.metadata.device_type_long +
                                        " class " + sdk_object_name + ": " + str(err))
                except ConnectionRefusedError:
                    self.logger(level="error",
                                message="Error while communicating with " + self.device.metadata.device_type_long +
                                        " for class " + sdk_object_name + ": Connection refused")
                except urllib.error.URLError:
                    self.logger(level="error",
                                message="Timeout error while fetching " + self.device.metadata.device_type_long +
                                        " class " + sdk_object_name)
                except http.client.RemoteDisconnected:
                    self.logger(level="error",
                                message="Connection closed while fetching " + self.device.metadata.device_type_long +
                                        " class " + sdk_object_name)
                except Exception as err:
                    self.logger(level="error", message="Error while fetching " + self.device.metadata.device_type_long +
                                                       " class " + sdk_object_name + ": " + str(err))

        # In case we still have SDK objects that failed to fetch, we list them in a warning message
        if failed_to_fetch:
            for sdk_object_name in failed_to_fetch:
                self.logger(level="warning", message="Impossible to fetch " + sdk_object_name + " after 2 attempts.")

        if self.device.task is not None:
            if not failed_to_fetch:
                self.device.task.taskstep_manager.stop_taskstep(
                    name="FetchConfigUcsSystemSdkObjects", status="successful",
                    status_message="Successfully fetched " + self.device.metadata.device_type_long +
                                   " SDK Config Objects")
            elif force:
                self.device.task.taskstep_manager.stop_taskstep(
                    name="FetchConfigUcsSystemSdkObjects", status="successful",
                    status_message="Fetched " + self.device.metadata.device_type_long +
                                   " SDK Config Objects with errors (forced)")
            else:
                self.device.task.taskstep_manager.stop_taskstep(
                    name="FetchConfigUcsSystemSdkObjects", status="failed",
                    status_message="Error while fetching " + self.device.metadata.device_type_long +
                                   " SDK Config Objects")

                # If any of the mandatory tasksteps fails then return False
                if not self.device.task.taskstep_manager.is_taskstep_optional(name="FetchConfigUcsSystemSdkObjects"):
                    return False

        # We sort all sdk objects by their DN in human-readable format
        for key, value in self.sdk_objects.items():
            value.sort(key=lambda obj: [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', obj.dn)])

        return True

    def _fetch_sdk_objects_from_xml(self, xml_file_path, force=False):
        """
        Alternative to _fetch_sdk_objects() that populates self.sdk_objects by
        parsing a UCSM MIT XML dump file (e.g. mit.xml from a tech-support bundle)
        instead of making live API calls via ucsmsdk.

        The MIT XML file is a flat document: a single <topRoot> element containing
        all Managed Objects as direct children, each represented as a self-closing
        tag whose name is the UCS class ID and whose XML attributes are the MO
        properties (in camelCase). A single pass with iterparse is sufficient.

        The resulting self.sdk_objects dict is identical in structure to what
        _fetch_sdk_objects() produces, so the rest of fetch_config() continues to
        work without any changes.

        :param xml_file_path: Path to the MIT XML file to parse.
        :param force: If True, tolerate parse errors and continue. If False, any
                      XML parse error causes the method to return False.
        :return: True if successful, False otherwise.
        """
        # Full set of class names to extract — the union of the common base list,
        # all UCSM-specific classes, and both modern and legacy BIOS token classes.
        # Including all BIOS variants is safe: the XML will only contain whichever
        # set was present on the system, and missing classes simply yield [].
        sdk_objects_to_fetch = set(
            self._COMMON_SDK_OBJECTS_TO_FETCH +
            self._UCSM_SPECIFIC_SDK_OBJECTS_TO_FETCH +
            self._BIOS_MODERN_SDK_OBJECTS_TO_FETCH +
            self._BIOS_LEGACY_SDK_OBJECTS_TO_FETCH
        )

        self.logger(level="debug",
                    message="Fetching " + self.device.metadata.device_type_long + " SDK objects from XML file: " +
                            str(xml_file_path))

        if self.device.task is not None:
            # The XML fetch reads all classes in a single pass, replacing both
            # the common and the UCSM-specific live-fetch steps.  Skip the common
            # step so the task-step sequence advances to the UCSM step below.
            self.device.task.taskstep_manager.skip_taskstep(
                name="FetchConfigUcsCommonSdkObjects",
                status_message="Skipped - all config SDK objects are fetched together from XML file")
            self.device.task.taskstep_manager.start_taskstep(
                name="FetchConfigUcsSystemSdkObjects",
                description="Fetching " + self.device.metadata.device_type_long +
                            " SDK Config Objects from XML file")

        # Pre-build the class cache: only load SDK classes that are in our target
        # set and are known to ucsmsdk.  Classes absent from the SDK are skipped
        # (same behaviour as when query_classid returns "no class named …").
        mo_class_cache = {}
        for class_id in sdk_objects_to_fetch:
            try:
                mo_class_cache[class_id] = ucscoreutils.load_class(class_id)
            except Exception:
                self.logger(level="debug", message="No ucsmsdk class for " + class_id + ", skipping")

        # Single-pass iterparse over the flat MIT XML structure.
        # <topRoot> contains ~180k child elements, each a self-closing MO tag.
        parse_error = False
        firmware_package_version = None
        try:
            for event, elem in ET.iterparse(xml_file_path, events=('end',)):
                if elem.tag == 'topRoot':
                    elem.clear()
                    continue
                # Opportunistically capture the system firmware version.
                # Primary source: firmwareRunning MO at dn="sys/mgmt/fw-system".
                # Fallback: versionApplication MO at dn="sys/version/application".
                if elem.tag == 'firmwareRunning' and elem.get('dn') == 'sys/mgmt/fw-system':
                    firmware_package_version = elem.get('version')
                elif (elem.tag == 'versionApplication' and elem.get('dn') == 'sys/version/application' and
                      not firmware_package_version):
                    firmware_package_version = elem.get('version')
                if elem.tag in mo_class_cache:
                    try:
                        mo = _load_mo_from_xml_element(mo_class_cache[elem.tag], elem)
                        self.sdk_objects.setdefault(elem.tag, []).append(mo)
                    except Exception as err:
                        self.logger(level="warning",
                                    message="Error instantiating " + elem.tag + " MO from XML: " + str(err))
                elem.clear()
        except ET.ParseError as err:
            parse_error = True
            self.logger(level="error",
                        message="XML parse error while reading " + str(xml_file_path) + ": " + str(err))

        # Classes absent from the XML are left out of sdk_objects entirely.
        # This mirrors live behaviour: classes that don't exist on the system
        # raise a "no class named X" exception and are never inserted, so
        # downstream "if 'className' in sdk_objects" guards correctly skip them.

        # Set device version from the firmwareRunning MO at sys/mgmt/fw-system or
        # versionApplication MO at sys/version/application so that version-gated
        # logic (e.g. BIOS token selection) works correctly without a live connection.
        # The version attribute is already a clean string like "4.1(3c)" with no suffix stripping needed.
        if firmware_package_version:
            try:
                self.device.version = UcsVersion(firmware_package_version)
                if hasattr(self.device.version, 'version'):
                    self.device.metadata.device_version = self.device.version.version
                self.logger(level="debug",
                            message="Set device version from XML: " + firmware_package_version)
            except Exception as err:
                self.logger(level="warning",
                            message="Could not parse firmware version '" + firmware_package_version + "': " + str(err))
        else:
            self.logger(level="warning",
                        message="Could not find firmwareRunning (sys/mgmt/fw-system) or versionApplication "
                                "(sys/version/application) MO in XML; device version will not be set")

        if parse_error and not force:
            if self.device.task is not None:
                self.device.task.taskstep_manager.stop_taskstep(
                    name="FetchConfigUcsSystemSdkObjects", status="failed",
                    status_message="XML parse error while fetching " +
                                   self.device.metadata.device_type_long + " SDK Config Objects")
                if not self.device.task.taskstep_manager.is_taskstep_optional(
                        name="FetchConfigUcsSystemSdkObjects"):
                    return False
            return False

        self.logger(level="debug",
                    message="Finished reading XML file. Loaded " +
                            str(sum(len(v) for v in self.sdk_objects.values())) +
                            " SDK objects across " +
                            str(sum(1 for v in self.sdk_objects.values() if v)) + " classes.")

        if self.device.task is not None:
            self.device.task.taskstep_manager.stop_taskstep(
                name="FetchConfigUcsSystemSdkObjects", status="successful",
                status_message="Successfully fetched " + self.device.metadata.device_type_long +
                               " SDK Config Objects from XML file")

        # Apply the same natural-sort-by-DN as the live fetch
        for value in self.sdk_objects.values():
            value.sort(key=lambda obj: [int(t) if t.isdigit() else t.lower()
                                        for t in re.split(r'(\d+)', obj.dn or '')])

        return True


class UcsImcConfig(GenericUcsConfig):
    _CONFIG_SECTION_ATTRIBUTES_MAP = {
        "adapter_cards": "Adapter Cards",
        "admin_networking": "Admin Networking",
        "bios_settings": "BIOS Settings",
        "boot_order_properties": "Boot Order Properties",
        "chassis_inventory": "Chassis Inventory",
        "communications_services": "Communications Services",
        "device_connector": "Device Connector",
        "dynamic_storage_zoning": "Dynamic Storage Zoning",
        "ip_blocking_properties": "IP Blocking Properties",
        "ip_filtering_properties": "IP Filtering Properties",
        "ldap_settings": "LDAP Settings",
        "local_users": "Local Users",
        "local_users_properties": "Local Users Properties",
        "logging_controls": "Logging Controls",
        "platform_event_filters": "Platform Event Filters",
        "power_cap_configuration": "Power Cap Configuration",
        "power_policies": "Power Policies",
        "secure_key_management": "Secure Key Management",
        "serial_over_lan_properties": "Serial Over LAN Properties",
        "server_properties": "Server Properties",
        "smtp_properties": "SMTP Properties",
        "snmp": "SNMP",
        "storage_controllers": "Storage Controllers",
        "storage_flex_flash_controllers": "Storage Flex Flash Controllers",
        "timezone_mgmt": "Timezone Management",
        "virtual_kvm_properties": "Virtual KVM Properties",
        "virtual_media": "Virtual Media"
    }

    _IMC_SPECIFIC_SDK_OBJECTS_TO_FETCH = [
        'aaaLdap', 'aaaLdapRoleGroup', 'aaaUserPasswordExpiration', 'aaaUserPolicy',
        'adaptorEthCompQueueProfile', 'adaptorEthGenProfile', 'adaptorEthInterruptProfile',
        'adaptorEthOffloadProfile', 'adaptorEthRecvQueueProfile', 'adaptorEthUSNICProfile',
        'adaptorEthWorkQueueProfile', 'adaptorExtIpV6RssHashProfile', 'adaptorFcBootTable',
        'adaptorFcCdbWorkQueueProfile', 'adaptorFcErrorRecoveryProfile', 'adaptorFcGenProfile',
        'adaptorFcInterruptProfile', 'adaptorFcPortFLogiProfile', 'adaptorFcPortPLogiProfile',
        'adaptorFcPortProfile', 'adaptorFcRecvQueueProfile', 'adaptorFcWorkQueueProfile',
        'adaptorGenProfile', 'adaptorHostEthIf', 'adaptorHostFcIf', 'adaptorIpV4RssHashProfile',
        'adaptorIpV6RssHashProfile', 'adaptorRssProfile', 'adaptorUnit', 'advancedPowerProfile',
        'biosVfAdjacentCacheLinePrefetch', 'biosVfAltitude', 'biosVfAutonumousCstateEnable',
        'biosVfBootPerformanceMode', 'biosVfCDNEnable', 'biosVfCPUEnergyPerformance',
        'biosVfCPUPerformance', 'biosVfCPUPowerManagement', 'biosVfCmciEnable',
        'biosVfConsoleRedirection', 'biosVfCoreMultiProcessing', 'biosVfDCUPrefetch',
        'biosVfDemandScrub', 'biosVfDirectCacheAccess', 'biosVfEnhancedIntelSpeedStepTech',
        'biosVfExecuteDisableBit', 'biosVfExtendedAPIC', 'biosVfFRB2Enable', 'biosVfHWPMEnable',
        'biosVfHardwarePrefetch', 'biosVfIntelHyperThreadingTech', 'biosVfIntelTurboBoostTech',
        'biosVfIntelVTForDirectedIO', 'biosVfIntelVirtualizationTechnology',
        'biosVfLOMPortOptionROM', 'biosVfLegacyUSBSupport', 'biosVfMemoryInterleave',
        'biosVfMemoryMappedIOAbove4GB', 'biosVfNUMAOptimized', 'biosVfOSBootWatchdogTimer',
        'biosVfOSBootWatchdogTimerPolicy', 'biosVfOSBootWatchdogTimerTimeout',
        'biosVfOSBootWatchdogTimerTimeout', 'biosVfOutOfBandMgmtPort', 'biosVfPCIOptionROMs',
        'biosVfPCISlotOptionROMEnable', 'biosVfPCIeSSDHotPlugSupport', 'biosVfPStateCoordType',
        'biosVfPackageCStateLimit', 'biosVfPatrolScrub', 'biosVfPchUsb30Mode',
        'biosVfPciRomClp', 'biosVfPowerOnPasswordSupport', 'biosVfProcessorC1E',
        'biosVfProcessorC3Report', 'biosVfProcessorC6Report', 'biosVfPwrPerfTuning',
        'biosVfQPIConfig', 'biosVfQpiSnoopMode', 'biosVfResumeOnACPowerLoss',
        'biosVfSataModeSelect', 'biosVfSelectMemoryRASConfiguration', 'biosVfSrIov',
        'biosVfTpmSupport', 'biosVfUSBEmulation', 'biosVfUSBPortsConfig',
        'biosVfUsbXhciSupport', 'biosVfVgaPriority', 'biosVfWorkLoadConfig', 'commHttp',
        'commHttps', 'commIpmiLan', 'commKvm', 'commMailAlert', 'commRedfish',
        'commSavedVMediaMap', 'commSnmp', 'commSnmpTrap', 'commSnmpUser', 'commSsh',
        'commSyslog', 'commSyslogClient', 'commVMedia', 'commVMediaMap', 'computeRackUnit',
        'computeServerRef', 'equipmentChassis', 'fanPolicy', 'ipBlocking', 'ipFiltering',
        'kmipServerLogin', 'ldapCACertificateManagement', 'lsbootDef', 'lsbootDevPrecision',
        'lsbootEfi', 'lsbootHdd', 'lsbootIscsi', 'lsbootLan', 'lsbootNVMe', 'lsbootPchStorage',
        'lsbootPxe', 'lsbootSan', 'lsbootSd', 'lsbootStorage', 'lsbootUefiShell', 'lsbootUsb',
        'lsbootVMedia', 'lsbootVirtualMedia', 'mailRecipient', 'memoryArray', 'mgmtIf',
        'oneTimePrecisionBootDevice', 'platformEventFilters', 'powerBudget',
        'selfEncryptStorageController', 'solIf', 'standardPowerProfile', 'storageController',
        'storageFlexFlashOperationalProfile', 'storageFlexFlashPhysicalDrive',
        'storageFlexFlashVirtualDrive', 'storageFlexFlashController', 'storageLocalDisk',
        'storageLocalDiskUsage', 'storageVirtualDrive'
    ]

    def __init__(self, parent=None):
        self.adapter_cards = []
        self.admin_networking = []
        self.bios_settings = []
        self.boot_order_properties = []
        self.chassis_inventory = []
        self.communications_services = []
        self.device_connector = []
        self.dynamic_storage_zoning = []
        self.ip_blocking_properties = []
        self.ip_filtering_properties = []
        self.ldap_settings = []
        self.local_users = []
        self.local_users_properties = []
        self.logging_controls = []
        self.platform_event_filters = []
        self.power_cap_configuration = []
        self.power_policies = []
        self.secure_key_management = []
        self.serial_over_lan_properties = []
        self.server_properties = []
        self.smtp_properties = []
        self.snmp = []
        self.storage_controllers = []
        self.storage_flex_flash_controllers = []
        self.timezone_mgmt = []
        self.virtual_kvm_properties = []
        self.virtual_media = []
        GenericUcsConfig.__init__(self, parent=parent)

        # List of attributes to be exported in a config export
        self.export_list = self._CONFIG_SECTION_ATTRIBUTES_MAP.keys()

    def _fetch_sdk_objects(self, force=False):
        GenericUcsConfig._fetch_sdk_objects(self, force=force)

        # If any of the mandatory tasksteps fails then return False
        from api.api_server import easyucs
        if easyucs and self.device.task and \
                easyucs.task_manager.is_any_taskstep_failed(uuid=self.device.task.metadata.uuid):
            self.logger(level="error", message="Failed to fetch one or more common SDK objects. "
                                               "Stopping the config fetch.")
            return False

        sdk_objects_to_fetch = self._IMC_SPECIFIC_SDK_OBJECTS_TO_FETCH

        self.logger(level="debug",
                    message="Fetching " + self.device.metadata.device_type_long + " SDK objects for config")

        if self.device.task is not None:
            self.device.task.taskstep_manager.start_taskstep(
                name="FetchConfigUcsImcSdkObjects",
                description="Fetching " + self.device.metadata.device_type_long + " SDK Config Objects")

        failed_to_fetch = []
        for sdk_object_name in sdk_objects_to_fetch:
            try:
                self.sdk_objects[sdk_object_name] = self.handle.query_classid(sdk_object_name)
                self.logger(level="debug", message="Fetched " + str(len(self.sdk_objects[sdk_object_name])) +
                                                   " objects of class " + sdk_object_name)
            except (UcsException, ImcException) as err:
                if err.error_code in ["ERR-xml-parse-error", "0"] and \
                        "no class named " + sdk_object_name in err.error_descr:
                    self.logger(level="debug", message="No " + self.device.metadata.device_type_long + " class named " +
                                                       sdk_object_name)
                elif err.error_code in ["2500"] and \
                        "MO is not supported on this UCS-C server platform." in err.error_descr:
                    self.logger(level="debug", message="No UCS class named " + sdk_object_name)
                else:
                    self.logger(level="error",
                                message="Error while trying to fetch " + self.device.metadata.device_type_long +
                                        " class " + sdk_object_name + ": " + str(err))
                    failed_to_fetch.append(sdk_object_name)
            except ConnectionRefusedError:
                self.logger(level="error",
                            message="Error while communicating with " + self.device.metadata.device_type_long +
                                    " class " + sdk_object_name + ": Connection refused")
                failed_to_fetch.append(sdk_object_name)
            except urllib.error.URLError:
                self.logger(level="error",
                            message="Timeout error while fetching " + self.device.metadata.device_type_long +
                                    " class " + sdk_object_name)
                failed_to_fetch.append(sdk_object_name)
            # Prevent rare exception due to Server Error return when fetching UCS IMC class
            except xml.etree.ElementTree.ParseError as err:
                self.logger(level="error",
                            message="Error while trying to fetch " + self.device.metadata.device_type_long +
                                    " class " + sdk_object_name + ": " + str(err))
                failed_to_fetch.append(sdk_object_name)
            except Exception as err:
                self.logger(level="error", message="Error while fetching " + self.device.metadata.device_type_long +
                                                   " class " + sdk_object_name + ": " + str(err))
                failed_to_fetch.append(sdk_object_name)

        # We retry all SDK objects that failed to fetch properly
        if failed_to_fetch:
            duplicate_failed_to_fetch = failed_to_fetch.copy()
            for sdk_object_name in duplicate_failed_to_fetch:
                self.logger(level="info", message="Retrying to fetch " + sdk_object_name)
                try:
                    self.sdk_objects[sdk_object_name] = self.handle.query_classid(sdk_object_name)
                    self.logger(level="debug", message="Fetched " + str(len(self.sdk_objects[sdk_object_name])) +
                                                       " objects of class " + sdk_object_name)
                    failed_to_fetch.remove(sdk_object_name)
                except (UcsException, ImcException) as err:
                    self.logger(level="error",
                                message="Error while trying to fetch " + self.device.metadata.device_type_long +
                                        " class " + sdk_object_name + ": " + str(err))
                except ConnectionRefusedError:
                    self.logger(level="error",
                                message="Error while communicating with " + self.device.metadata.device_type_long +
                                        " class " + sdk_object_name + ": Connection refused")
                except urllib.error.URLError:
                    self.logger(level="error",
                                message="Timeout error while fetching " + self.device.metadata.device_type_long +
                                        " class " + sdk_object_name)
                # Prevent rare exception due to Server Error return when fetching UCS IMC class
                except xml.etree.ElementTree.ParseError as err:
                    self.logger(level="error",
                                message="Error while trying to fetch " + self.device.metadata.device_type_long +
                                        " class " + sdk_object_name + ": " + str(err))
                except Exception as err:
                    self.logger(level="error", message="Error while fetching " + self.device.metadata.device_type_long +
                                                       " class " + sdk_object_name + ": " + str(err))

        # In case we still have SDK objects that failed to fetch, we list them in a warning message
        if failed_to_fetch:
            for sdk_object_name in failed_to_fetch:
                self.logger(level="warning", message="Impossible to fetch " + sdk_object_name + " after 2 attempts.")

        if self.device.task is not None:
            if not failed_to_fetch:
                self.device.task.taskstep_manager.stop_taskstep(
                    name="FetchConfigUcsImcSdkObjects", status="successful",
                    status_message="Successfully fetched " + self.device.metadata.device_type_long +
                                   " SDK Config Objects")
            elif force:
                self.device.task.taskstep_manager.stop_taskstep(
                    name="FetchConfigUcsImcSdkObjects", status="successful",
                    status_message="Fetched " + self.device.metadata.device_type_long +
                                   " SDK Config Objects with errors (forced)")
            else:
                self.device.task.taskstep_manager.stop_taskstep(
                    name="FetchConfigUcsImcSdkObjects", status="failed",
                    status_message="Error while fetching " + self.device.metadata.device_type_long +
                                   " SDK Config Objects")

                # If any of the mandatory tasksteps fails then return False
                if not self.device.task.taskstep_manager.is_taskstep_optional(name="FetchConfigUcsImcSdkObjects"):
                    return False

        return True

    def get_object(self, **kwargs):
        self.logger(level="error", message="Not available for device of type " + self.device.metadata.device_type_long)

    def get_operational_policy_name_and_org_path(self, **kwargs):
        self.logger(level="error", message="Not available for device of type " + self.device.metadata.device_type_long)

    def resolve_operational_pool_name_and_org_path(self, **kwargs):
        self.logger(level="error", message="Not available for device of type " + self.device.metadata.device_type_long)


class UcsCentralConfig(GenericUcsConfig):
    _CONFIG_SECTION_ATTRIBUTES_MAP = {
        "authentication": "Authentication",
        "date_time": "Date Time",
        "dns": "DNS",
        "domain_groups": "Domain Groups",
        "ldap": "LDAP",
        "local_users": "Local Users",
        "locales": "Locales",
        "management_interfaces": "Management Interfaces",
        "orgs": "Organizations",
        "password_profile": "Password Profile",
        "roles": "Roles",
        "snmp": "SNMP",
        "syslog": "Syslog",
        "system": "System"
    }

    _CENTRAL_SPECIFIC_SDK_OBJECTS_TO_FETCH = [
        'aaaAuthRealm', 'aaaConsoleAuth', 'aaaDefaultAuth', 'aaaDomain', 'aaaDomainAuth', 'aaaDomainGroup',
        'aaaLdapEp', 'aaaLdapGroup', 'aaaLdapGroupRule', 'aaaLdapProvider', 'aaaProviderGroup',
        'aaaProviderRef', 'aaaEpAuthProfile', 'aaaEpUser', 'aaaLocale', 'aaaOrg', 'aaaPwdProfile', 'aaaRole',
        'aaaSshAuth', 'aaaUser', 'aaaUserLocale', 'aaaUserRole', 'adaptorCapQual', 'adaptorEthAdvFilterProfile',
        'adaptorEthArfsProfile', 'adaptorEthCompQueueProfile', 'adaptorEthFailoverProfile',
        'adaptorEthGENEVEProfile', 'adaptorEthInterruptProfile', 'adaptorEthInterruptScalingProfile',
        'adaptorEthNVGREProfile', 'adaptorEthOffloadProfile', 'adaptorEthRecvQueueProfile', 'adaptorEthRoCEProfile',
        'adaptorEthVxLANProfile', 'adaptorEthWorkQueueProfile', 'adaptorFcCdbWorkQueueProfile',
        'adaptorFcErrorRecoveryProfile', 'adaptorFcFnicProfile', 'adaptorFcInterruptProfile',
        'adaptorFcPortFLogiProfile', 'adaptorFcPortPLogiProfile', 'adaptorFcPortProfile',
        'adaptorFcRecvQueueProfile', 'adaptorFcWorkQueueProfile', 'adaptorHostEthIfProfile',
        'adaptorHostFcIfProfile', 'adaptorHostIscsiIfProfile', 'adaptorQual', 'adaptorProtocolProfile',
        'adaptorRssProfile', 'biosTokenSettings', 'biosTokenParam', 'biosVProfile', 'cimcvmediaConfigMountEntry',
        'cimcvmediaMountConfigDef', 'cimcvmediaMountConfigPolicy', 'commCimxml', 'commDateTime', 'commDns',
        'commDnsProvider', 'commHttp', 'commNtpProvider', 'commShellSvcLimits', 'commSnmp', 'commSnmpTrap',
        'commSnmpUser', 'commSyslog', 'commSyslogClient', 'commSyslogConsole', 'commSyslogFile',
        'commSyslogMonitor', 'commSyslogSource', 'commTelnet', 'commWebSvcLimits', 'computeBoard',
        'computeChassisDiscPolicy', 'computeChassisQual', 'computeDomainGroupQual',
        'computeDomainHwChangeDiscPolicy', 'computeDomainNameQual', 'computeDomainPortDiscPolicy',
        'computeDomainQual', 'computeGraphicsCardPolicy', 'computeGroupMembership', 'computeModularChassisFanPolicy',
        'computePhysicalQual', 'computePool', 'computePoolingPolicy', 'computePooledRackUnit', 'computePooledSlot',
        'computeOwnerQual', 'computePowerExtendedPolicy', 'computePowerSavePolicy', 'computePowerSyncPolicy',
        'computeProductFamilyQual', 'computePsuPolicy', 'computeQual', 'computeRackQual', 'computeScrubPolicy',
        'computeServerDiscPolicy', 'computeServerMgmtPolicy', 'computeSiteQual', 'computeSlotQual', 'computeSystem',
        'computeSystemAddrQual', 'computeSystemQual', 'dpsecMac', 'epqosDefinition', 'epqosEgress',
        'equipmentBinding', 'equipmentChassisProfile', 'equipmentComputeConnPolicy', 'fabricEthLinkProfile',
        'fabricLacpPolicy', 'fabricLanCloudPolicy', 'fabricMulticastPolicy', 'fabricNetGroup', 'fabricNetGroupRef',
        'fabricNetGroupReq', 'fabricPooledVlan', 'fabricUdldLinkPolicy', 'fabricVCon', 'fabricVConProfile',
        'fabricVlan', 'fabricVlanReq', 'fabricVsan', 'fcpoolBlock', 'fcpoolInitiators', 'firmwareAutoSyncPolicy',
        'firmwareChassisPack', 'firmwareComputeHostPack', 'firmwareExcludeChassisComponent',
        'firmwareExcludeServerComponent', 'flowctrlItem', 'identpoolBlockQual', 'identpoolDomainGroupQual',
        'inbandPolicy', 'ippoolBlock', 'ippoolIpV6Block', 'ippoolPool', 'iqnpoolBlock', 'iqnpoolPool',
        'iscsiAuthProfile', 'lsBinding', 'lsbootBootSecurity', 'lsbootDef', 'lsbootDefaultLocalImage',
        'lsbootEFIShell', 'lsbootEmbeddedLocalDiskImage', 'lsbootEmbeddedLocalDiskImagePath',
        'lsbootEmbeddedLocalLunImage', 'lsbootIScsi', 'lsbootIScsiImagePath', 'lsbootLan', 'lsbootLanImagePath',
        'lsbootLocalDiskImage', 'lsbootLocalDiskImagePath', 'lsbootLocalHddImage', 'lsbootLocalLunImagePath',
        'lsbootNvme', 'lsbootPolicy', 'lsbootSan', 'lsbootSanCatSanImage', 'lsbootSanCatSanImagePath',
        'lsbootStorage', 'lsbootUEFIBootParam', 'lsbootUsbExternalImage', 'lsbootUsbFlashStorageImage',
        'lsbootUsbInternalImage', 'lsbootVirtualMedia', 'lsbootLocalStorage', 'lsmaintMaintPolicy', 'lsPower',
        'lsRequirement', 'lsServer', 'lsServerExtension', 'lstorageControllerDef', 'lstorageControllerModeConfig',
        'lstorageControllerRef', 'lstorageDasScsiLun', 'lstorageDiskGroupConfigPolicy', 'lstorageDiskGroupQualifier',
        'lstorageDiskSlot', 'lstorageDiskZoningPolicy', 'lstorageLocal', 'lstorageLocalDiskConfigRef', 'lstorageLogin',
        'lstorageProfile', 'lstorageProfileBinding', 'lstorageProfileDef', 'lstorageRemote',
        'lstorageVirtualDriveDef', 'lsVConAssign', 'macpoolBlock', 'macpoolPool', 'memoryQual', 'mgmtInterface',
        'mgmtIPv6IfAddr', 'mgmtNamedKmipCertPolicy', 'mgmtVnet', 'networkElement', 'nwctrlDefinition',
        'orgDomainGroup', 'orgDomainGroupPolicy', 'orgOrg', 'powerMgmtPolicy', 'powerPolicy', 'processorQual',
        'statsThr32Definition', 'statsThr32Value', 'statsThr64Definition', 'statsThr64Value',
        'statsThrFloatDefinition', 'statsThrFloatValue', 'statsThresholdClass', 'statsThresholdPolicy', 'solPolicy',
        'storageConnectionPolicy', 'storageFcTargetEp', 'storageIniGroup', 'storageInitiator',
        'storageLocalDiskConfigDef', 'storageLocalDiskConfigPolicy', 'storageQual', 'storageScsiLunRef',
        'storageVirtualDrive', 'storageVsanRef', "tagInstance",
        'topInfoSyncPolicy', 'uuidpoolBlock', 'uuidpoolPool', 'vnicConnDef', 'vnicDynamicCon',
        'vnicDynamicConPolicy', 'vnicDynamicConPolicyRef', 'vnicEther', 'vnicEtherIf', 'vnicFc', 'vnicFcGroupDef',
        'vnicFcIf', 'vnicFcNode', 'vnicIPv4Dhcp', 'VnicIPv4If', 'vnicIPv4IscsiAddr', 'vnicIpV4MgmtPooledAddr',
        'vnicIpV4PooledAddr', 'vnicIPv4PooledIscsiAddr', 'vnicIpV6MgmtPooledAddr', 'vnicIScsi',
        'vnicIScsiAutoTargetIf', 'vnicIScsiBootParams', 'vnicIScsiBootVnic', 'vnicIScsiLCP', 'vnicIScsiNode',
        'vnicIScsiStaticTargetIf', 'vnicIScsiTargetParams', 'vnicLanConnPolicy', 'vnicLanConnTempl', 'vnicLun',
        'vnicMgmtIf', 'vnicSanConnPolicy', 'vnicSanConnTempl', 'vnicSriovHpnConPolicy', 'vnicSriovHpnConPolicyRef',
        'vnicUsnicConPolicy', 'vnicUsnicConPolicyRef', 'vnicVlan', 'vnicVmqConPolicy', 'vnicVmqConPolicyRef'
    ]

    def __init__(self, parent=None):
        self.authentication = []
        self.date_time = []
        self.dns = []
        self.domain_groups = []
        self.ldap = []
        self.local_users = []
        self.locales = []
        self.management_interfaces = []
        self.orgs = []
        self.password_profile = []
        self.roles = []
        self.snmp = []
        self.syslog = []
        self.system = []

        GenericUcsConfig.__init__(self, parent=parent)

        # List of attributes to be exported in a config export
        self.export_list = self._CONFIG_SECTION_ATTRIBUTES_MAP.keys()

        # List of Appliance VLANs, VLANs, Storage VSANs & VSANs that are using aliasing in this config
        self.vxan_aliasing = {"fabric_a": {"appliance_vlans": {}, "storage_vsans": {}, "vlans": {}, "vsans": {}},
                              "fabric_b": {"appliance_vlans": {}, "storage_vsans": {}, "vlans": {}, "vsans": {}},
                              "vlan_groups": {}}
        self.vxan_aliasing_in_use = False

    def get_domain_group_from_path(self, domain_group_path=""):
        """
        Find a domain group by path and support hierarchy traversal.
        Handles paths like "root/DG_GV/DG_GV-ALPHA".
        :param domain_group_path: Full path like "root/DG_GV/DG_GV-ALPHA"
        :return: UcsCentralDomainGroup object if found, None otherwise
        """

        if not domain_group_path:
            self.logger(level="error", message="Domain Group path is empty.")
            return None

        path_parts = [part for part in domain_group_path.split("/") if part]

        if not path_parts:
            return None

        current_pointer = getattr(self, "domain_groups", []) or []

        current_match = None
        for domain_group_name in path_parts:
            current_match = next((dg for dg in current_pointer
                                    if getattr(dg, "name", None) == domain_group_name), None)

            if not current_match:
                return None

            current_pointer = getattr(
                current_match, "domain_groups", []) or []

        return current_match
    
    def _determine_vxan_aliasing(self, domain_group_list=None, vxans_list=None):
        """
        Recursive function to check if the config is using aliasing for VLANs, Appliance VLANs, VSANs, Storage VSANs
        :param domain_group_list: list of domain groups to analyze for aliased VxANs, used by recursion
        :param vxans_list: full list of VxANs encountered across domain groups, used by recursion to determine aliases
        :return: True if config uses aliasing, False otherwise
        """
        if not vxans_list:
            # Initializing the first run in the recursion
            vxans_list = {"fabric_a": {"appliance_vlans": {}, "storage_vsans": {}, "vlans": {}, "vsans": {}},
                          "fabric_b": {"appliance_vlans": {}, "storage_vsans": {}, "vlans": {}, "vsans": {}},
                          "vlan_groups": {}}
        if not domain_group_list:
            domain_group_list = self.domain_groups

        for domain_group in domain_group_list:
            for fabric in [key for key in vxans_list.keys() if key.startswith("fabric_")]:
                for vxan_type in vxans_list[fabric].keys():
                    if getattr(domain_group, vxan_type):
                        for vxan_object in getattr(domain_group, vxan_type):
                            if getattr(vxan_object, "fabric", None) in \
                                    [fabric.split("_")[1], fabric.split("_")[1].upper(), "dual", None]:
                                if vxan_object.name not in vxans_list[fabric][vxan_type]:
                                    vxans_list[fabric][vxan_type][vxan_object.name] = [
                                        {"id": vxan_object.id, "domain_group": domain_group.get_domain_group_path()}
                                    ]
                                else:
                                    # VxAN object name already exists in another Domain Group
                                    # We check if the VxAN ID is different - if not, this is not really an alias
                                    if vxan_object.id not in [x["id"]
                                                              for x in vxans_list[fabric][vxan_type]
                                                              [vxan_object.name]]:
                                        if vxan_object.name not in self.vxan_aliasing[fabric][vxan_type]:
                                            # We first copy the original VxAN that is aliased with the current one
                                            self.vxan_aliasing[fabric][vxan_type][vxan_object.name] = \
                                                vxans_list[fabric][vxan_type][vxan_object.name]
                                        self.vxan_aliasing[fabric][vxan_type][vxan_object.name].append(
                                            {"id": vxan_object.id, "domain_group": domain_group.get_domain_group_path()}
                                        )

            if getattr(domain_group, "vlan_groups"):
                for vlan_group in getattr(domain_group, "vlan_groups"):
                    if vlan_group.name not in vxans_list["vlan_groups"]:
                        vxans_list["vlan_groups"][vlan_group.name] = [
                            {"vlans": vlan_group.vlans, "domain_group": domain_group.get_domain_group_path()}
                        ]
                        # Resolving the IDs of the VLANs contained in this VLAN Group
                        vlan_ids = []
                        for vlan_name in vlan_group.vlans:
                            vlan = self.find_vxan(vxan_type="vlans", vxan_name=vlan_name,
                                                  domain_group_path=domain_group.get_domain_group_path())
                            if vlan:
                                vlan_ids.append(vlan.id)
                        vxans_list["vlan_groups"][vlan_group.name][0]["ids"] = vlan_ids
                    else:
                        if str(sorted(vlan_group.vlans)) not in [str(sorted(x["vlans"])) for x in
                                                                 vxans_list["vlan_groups"][vlan_group.name]]:
                            if vlan_group.name not in self.vxan_aliasing["vlan_groups"]:
                                self.vxan_aliasing["vlan_groups"][vlan_group.name] = \
                                    vxans_list["vlan_groups"][vlan_group.name]
                            # Resolving the IDs of the VLANs contained in this VLAN Group
                            vlan_ids = []
                            for vlan_name in vlan_group.vlans:
                                vlan = self.find_vxan(vxan_type="vlans", vxan_name=vlan_name,
                                                      domain_group_path=domain_group.get_domain_group_path())
                                if vlan:
                                    vlan_ids.append(vlan.id)
                            self.vxan_aliasing["vlan_groups"][vlan_group.name].append(
                                {"vlans": vlan_group.vlans, "domain_group": domain_group.get_domain_group_path(),
                                 "ids": vlan_ids}
                            )

            if getattr(domain_group, "domain_groups", []):
                self._determine_vxan_aliasing(domain_group_list=getattr(domain_group, "domain_groups"),
                                              vxans_list=vxans_list)
        if any(self.vxan_aliasing["fabric_a"].values()) or any(self.vxan_aliasing["fabric_b"].values()) or any(
                self.vxan_aliasing["vlan_groups"].values()):
            self.vxan_aliasing_in_use = True
            return True
        return False

    def _fetch_sdk_objects(self, force=False):
        GenericUcsConfig._fetch_sdk_objects(self, force=force)

        # If any of the mandatory tasksteps fails then return False
        from api.api_server import easyucs
        if easyucs and self.device.task and \
                easyucs.task_manager.is_any_taskstep_failed(uuid=self.device.task.metadata.uuid):
            self.logger(level="error", message="Failed to fetch one or more common SDK objects. Stopping the config fetch.")
            return False

        self.logger(level="debug", message="Fetching BIOS Tokens for config")

        sdk_objects_to_fetch = self._CENTRAL_SPECIFIC_SDK_OBJECTS_TO_FETCH

        self.logger(level="debug",
                    message="Fetching " + self.device.metadata.device_type_long + " SDK objects for config")

        if self.device.task is not None:
            self.device.task.taskstep_manager.start_taskstep(
                name="FetchConfigUcsCentralSdkObjects",
                description="Fetching " + self.device.metadata.device_type_long + " SDK Config Objects")

        failed_to_fetch = []
        for sdk_object_name in sdk_objects_to_fetch:
            try:
                self.sdk_objects[sdk_object_name] = self.handle.query_classid(sdk_object_name)
                self.logger(level="debug", message="Fetched " + str(len(self.sdk_objects[sdk_object_name])) +
                                                   " objects of class " + sdk_object_name)
            except UcscException as err:
                if err.error_code in ["ERR-xml-parse-error", "0"] and \
                        "no class named " + sdk_object_name in err.error_descr:
                    self.logger(level="debug", message="No " + self.device.metadata.device_type_long + " class named " +
                                                       sdk_object_name)
                else:
                    self.logger(level="error",
                                message="Error while trying to fetch " + self.device.metadata.device_type_long +
                                        " class " + sdk_object_name + ": " + str(err))
                    failed_to_fetch.append(sdk_object_name)
            except ConnectionRefusedError:
                self.logger(level="error",
                            message="Error while communicating with " + self.device.metadata.device_type_long +
                                    " class " + sdk_object_name + ": Connection refused")
                failed_to_fetch.append(sdk_object_name)
            except urllib.error.URLError:
                self.logger(level="error",
                            message="Timeout error while fetching " + self.device.metadata.device_type_long +
                                    " class " + sdk_object_name)
                failed_to_fetch.append(sdk_object_name)
            except Exception as err:
                self.logger(level="error", message="Error while fetching " + self.device.metadata.device_type_long +
                                                   " class " + sdk_object_name + ": " + str(err))
                failed_to_fetch.append(sdk_object_name)

        # We retry all SDK objects that failed to fetch properly
        if failed_to_fetch:
            duplicate_failed_to_fetch = failed_to_fetch.copy()
            for sdk_object_name in duplicate_failed_to_fetch:
                self.logger(level="info", message="Retrying to fetch " + sdk_object_name)
                try:
                    self.sdk_objects[sdk_object_name] = self.handle.query_classid(sdk_object_name)
                    self.logger(level="debug", message="Fetched " + str(len(self.sdk_objects[sdk_object_name])) +
                                                       " objects of class " + sdk_object_name)
                    failed_to_fetch.remove(sdk_object_name)
                except UcscException as err:
                    self.logger(level="error",
                                message="Error while trying to fetch " + self.device.metadata.device_type_long +
                                        " class " + sdk_object_name + ": " + str(err))
                except ConnectionRefusedError:
                    self.logger(level="error",
                                message="Error while communicating with " + self.device.metadata.device_type_long +
                                        " class " + sdk_object_name + ": Connection refused")
                except urllib.error.URLError:
                    self.logger(level="error",
                                message="Timeout error while fetching " + self.device.metadata.device_type_long +
                                        " class " + sdk_object_name)
                except Exception as err:
                    self.logger(level="error", message="Error while fetching " + self.device.metadata.device_type_long +
                                                       " class " + sdk_object_name + ": " + str(err))

        # In case we still have SDK objects that failed to fetch, we try to decompose the fetch operation to reduce the
        # number of objects per call
        if failed_to_fetch:
            for sdk_object_name in failed_to_fetch:
                if sdk_object_name == "tagInstance":
                    # We specifically ignore issues with tagInstance objects for UCS Central, since there is a known
                    # API issue with tagInstance objects using specific characters (EASYUCS-826)
                    self.logger(level="warning",
                                message="Ignoring " + sdk_object_name + " objects class due to " +
                                        self.device.metadata.device_type_long + " API issue")
                    failed_to_fetch.remove(sdk_object_name)
                    continue

                self.logger(level="info",
                            message="Retrying to fetch " + sdk_object_name + " using decomposition in smaller queries")
                failed_decomposed_fetch = False
                from string import ascii_lowercase, digits
                allowed_name_chars = ascii_lowercase + digits
                sdk_objects = {}
                for i in allowed_name_chars:
                    try:
                        sdk_objects[i] = self.handle.query_classid(
                            class_id=sdk_object_name, filter_str='(name, "^' + i + '.*", type="re", flag="I")')
                        self.logger(level="debug",
                                    message="Fetched " + str(len(sdk_objects[i])) + " objects of class " +
                                            sdk_object_name + " starting with character '" + i + "'")
                    except Exception as err:
                        self.logger(level="error",
                                    message="Error while fetching " + self.device.metadata.device_type_long +
                                            " class " + sdk_object_name + " starting with character '" + i + "': " +
                                            str(err))
                        failed_decomposed_fetch = True

                try:
                    sdk_objects["*"] = self.handle.query_classid(class_id=sdk_object_name,
                                                                 filter_str='(name, "^[\\-\\.:_].*", type="re")')
                    self.logger(level="debug",
                                message="Fetched " + str(len(sdk_objects["*"])) + " objects of class " +
                                        sdk_object_name + " starting with special characters '-.:_'")
                except Exception as err:
                    self.logger(level="error",
                                message="Error while fetching " + self.device.metadata.device_type_long +
                                        " class " + sdk_object_name + " starting with special characters '-.:_': " +
                                        str(err))
                    failed_decomposed_fetch = True

                if not failed_decomposed_fetch:
                    self.sdk_objects[sdk_object_name] = []
                    for i in allowed_name_chars + "*":
                        self.sdk_objects[sdk_object_name] += sdk_objects[i]
                    self.logger(level="debug", message="Fetched " + str(len(self.sdk_objects[sdk_object_name])) +
                                                       " objects of class " + sdk_object_name)
                    failed_to_fetch.remove(sdk_object_name)
                else:
                    # In case we still have SDK objects that failed to fetch, we list them in a warning message
                    self.logger(level="warning",
                                message="Impossible to fetch " + sdk_object_name + " after 2 attempts and decomposing.")

        if self.device.task is not None:
            if not failed_to_fetch:
                self.device.task.taskstep_manager.stop_taskstep(
                    name="FetchConfigUcsCentralSdkObjects", status="successful",
                    status_message="Successfully fetched " + self.device.metadata.device_type_long +
                                   " SDK Config Objects")
            elif force:
                self.device.task.taskstep_manager.stop_taskstep(
                    name="FetchConfigUcsCentralSdkObjects", status="successful",
                    status_message="Fetched " + self.device.metadata.device_type_long +
                                   " SDK Config Objects with errors (forced)")
            else:
                self.device.task.taskstep_manager.stop_taskstep(
                    name="FetchConfigUcsCentralSdkObjects", status="failed",
                    status_message="Error while fetching " + self.device.metadata.device_type_long +
                                   " SDK Config Objects")

                # If any of the mandatory tasksteps fails then return False
                if not self.device.task.taskstep_manager.is_taskstep_optional(name="FetchConfigUcsCentralSdkObjects"):
                    return False

        # Remove duplicate objects if they are getting displayed twice in central
        duplicate_sdk_objects = ["adaptorEthRoCEProfile", "vnicIScsiBootVnic"]
        for sdk_object_name in duplicate_sdk_objects:
            dn_list = []
            unique_dn_objects = []
            if sdk_object_name in self.sdk_objects:
                for obj in self.sdk_objects[sdk_object_name]:
                    # filtering the sdk object "vnicIScsiBootVnic" of LAN policy with object containing oper_state
                    if sdk_object_name == "vnicIScsiBootVnic":
                        if not obj.auth_profile_name:
                            if obj.dn not in dn_list:
                                dn_list.append(obj.dn)
                                unique_dn_objects.append(obj)
                        elif obj.oper_auth_profile_name:
                            if obj.dn not in dn_list:
                                dn_list.append(obj.dn)
                                unique_dn_objects.append(obj)

                    elif obj.dn not in dn_list:
                        dn_list.append(obj.dn)
                        unique_dn_objects.append(obj)

                self.sdk_objects[sdk_object_name] = unique_dn_objects

        return True

    def find_vxan(self, fabric="", vxan_type="", vxan_name="", domain_group_path=""):
        """
        Find a given VxAN in the config, given its type, name, fabric and optional Domain Group path
        :param fabric: The fabric ID (A / B / dual) to which the VxAN should be associated (will ignore if not set)
        :param vxan_type: The type of VxAN to find (appliance_vlans, vlan_groups, vlans, storage_vsans, vsans)
        :param vxan_name: The name of the VxAN to find
        :param domain_group_path: The path of the domain group in which to find the VxAN (will look in all if not set)
        :return: VxAN object if found, None otherwise
        """
        if not vxan_name:
            self.logger(level="error", message="Missing VxAN name in VxAN find")
            return None

        if vxan_type not in ["appliance_vlans", "storage_vsans", "vlan_groups", "vlans", "vsans"]:
            self.logger(level="error", message="Invalid VxAN type in VxAN alias check")
            return None

        dg = None
        if domain_group_path:
            # Identifying the domain group in which to start looking for the VxAN in the config
            current_pointer = self
            for subdg in domain_group_path.split("/"):
                if not current_pointer.domain_groups:
                    self.logger(level="debug",
                                message="Could not find domain group " + str(subdg) + " of path " + str(
                                    domain_group_path) + " in config")
                    return None
                found_dg = False
                for dg in current_pointer.domain_groups:
                    if dg.name == subdg:
                        current_pointer = dg
                        found_dg = True
                        break
                if not found_dg:
                    self.logger(level="debug",
                                message="Could not find domain group " + str(subdg) + " of path " + str(
                                    domain_group_path) + " in config")
                    return None
            dg = current_pointer

        if dg:
            current_pointer = dg
            while current_pointer._dn != "domaingroup-root":
                if hasattr(current_pointer, vxan_type):
                    if getattr(current_pointer, vxan_type):
                        for vxan in getattr(current_pointer, vxan_type):
                            if getattr(vxan, "name", None) == vxan_name:
                                return vxan
                current_pointer = current_pointer._parent

            if hasattr(current_pointer, vxan_type):
                if getattr(current_pointer, vxan_type):
                    for vxan in getattr(current_pointer, vxan_type):
                        if getattr(vxan, "name", None) == vxan_name:
                            return vxan

            self.logger(level="debug",
                        message="Could not resolve " + vxan_type + " with name " + vxan_name +
                                " starting from Domain Group " + str(domain_group_path))
            return None

        else:
            # Trying to find a VxAN of the given type, name and fabric in any of the Domain Groups
            vxans_list = []
            for domain_group in getattr(self, "domain_groups", []):
                self.parse_domain_group(domain_group=domain_group, element_list=vxans_list, element_to_parse=vxan_type)

            for vxan in vxans_list:
                if getattr(vxan, "name", None) == vxan_name:
                    if fabric:
                        # We check if the fabric ID corresponds
                        if getattr(vxan, "fabric", "").lower() == fabric.lower():
                            return vxan
                    else:
                        # We ignore the fabric value
                        return vxan

        message = f"Could not find VxAN of type {vxan_type} with name {vxan_name}"
        if domain_group_path:
            message += f" in domain group {domain_group_path}"
        self.logger(level="debug", message=message)
        return None

    def is_vxan_aliased(self, fabric="", vxan_type="", vxan_name=""):
        """
        Check if the config is using aliasing for the given VxAN type on the given fabric
        :param fabric: The fabric for which to check if VxAN is aliased (fabric_a or fabric_b)
        :param vxan_type: Type of VxAN to check for aliasing (appliance_vlans, vlan_groups, vlans, storage_vsans, vsans)
        :param vxan_name: The name of the VxAN to check for aliasing
        :return: True if VxAN uses aliasing, False if it does not use aliasing, None if check failed
        """
        if not vxan_name:
            self.logger(level="error", message="Missing VxAN name in VxAN alias check")
            return None

        if vxan_type in ["appliance_vlans", "storage_vsans", "vlans", "vsans"]:
            fabrics = [None]
            if fabric in ["a", "A", "b", "B"]:
                fabrics = ["fabric_" + fabric.lower()]
            if fabric in ["a-b", "A-B", "b-a", "B-A", "dual"]:
                fabrics = ["fabric_a", "fabric_b"]
            if fabric in ["fabric_a", "fabric_b"]:
                fabrics = [fabric]
            if any(x not in ["fabric_a", "fabric_b"] for x in fabrics):
                self.logger(level="error", message="Invalid fabric in VxAN alias check")
                return None

            for fabric in fabrics:
                if vxan_name in self.vxan_aliasing[fabric][vxan_type]:
                    return True
            return False
        elif vxan_type in ["vlan_groups"]:
            if fabric:
                self.logger(level="warning", message="Fabric is ignored for VLAN Group alias check")

            if vxan_name not in self.vxan_aliasing[vxan_type]:
                return False
            else:
                return True
        else:
            self.logger(level="error", message="Invalid VxAN type in VxAN alias check")
            return None

    def parse_domain_group(self, domain_group, element_list, element_to_parse):
        if eval("domain_group." + element_to_parse) is not None:
            for element in eval("domain_group." + element_to_parse):
                element_list.append(element)
        if hasattr(domain_group, "domain_groups"):
            if domain_group.domain_groups is not None:
                for subdomain_group in domain_group.domain_groups:
                    self.parse_domain_group(subdomain_group, element_list, element_to_parse)
