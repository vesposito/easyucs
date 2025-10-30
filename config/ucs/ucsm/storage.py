# coding: utf-8
# !/usr/bin/env python

""" storage.py: Easy UCS Deployment Tool """
from __init__ import __author__, __copyright__,  __version__, __status__

from ucsmsdk.mometa.lstorage.LstorageControllerDef import LstorageControllerDef
from ucsmsdk.mometa.lstorage.LstorageControllerModeConfig import LstorageControllerModeConfig
from ucsmsdk.mometa.lstorage.LstorageDasScsiLun import LstorageDasScsiLun
from ucsmsdk.mometa.lstorage.LstorageDiskGroupConfigPolicy import LstorageDiskGroupConfigPolicy
from ucsmsdk.mometa.lstorage.LstorageDiskGroupQualifier import LstorageDiskGroupQualifier
from ucsmsdk.mometa.lstorage.LstorageDriveSecurity import LstorageDriveSecurity
from ucsmsdk.mometa.lstorage.LstorageHybridDriveSlotConfig import LstorageHybridDriveSlotConfig
from ucsmsdk.mometa.lstorage.LstorageLocal import LstorageLocal
from ucsmsdk.mometa.lstorage.LstorageLocalDiskConfigRef import LstorageLocalDiskConfigRef
from ucsmsdk.mometa.lstorage.LstorageLogin import LstorageLogin
from ucsmsdk.mometa.lstorage.LstorageLunSetConfig import LstorageLunSetConfig
from ucsmsdk.mometa.lstorage.LstorageProfile import LstorageProfile
from ucsmsdk.mometa.lstorage.LstorageProfileDef import LstorageProfileDef
from ucsmsdk.mometa.lstorage.LstorageRemote import LstorageRemote
from ucsmsdk.mometa.lstorage.LstorageSecurity import LstorageSecurity
from ucsmsdk.mometa.lstorage.LstorageVirtualDriveDef import LstorageVirtualDriveDef

from config.ucs.object import UcsSystemConfigObject


class UcsSystemDiskGroupPolicy(UcsSystemConfigObject):
    _CONFIG_NAME = "Disk Group Policy"
    _CONFIG_SECTION_NAME = "disk_group_policies"
    _UCS_SDK_OBJECT_NAME = "lstorageDiskGroupConfigPolicy"

    # TODO:  if a disk group configuration manual exists you can not change it to automatic and vice-versa
    # Object LstorageLocalDiskConfigRef and LstorageDiskGroupQualifier can not exist alongside each other
    # You need to remove one MO in order to create the other.

    def __init__(self, parent=None, json_content=None, lstorage_disk_group_config_policy=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=lstorage_disk_group_config_policy)
        self.name = None
        self.descr = None
        self.raid_level = None
        self.strip_size = None
        self.access_policy = None
        self.read_policy = None
        self.write_cache_policy = None
        self.io_policy = None
        self.drive_cache = None
        self.security = None
        self.manual_disk_group_configuration = []
        self.number_of_drives = None
        self.drive_type = None
        self.number_of_dedicated_hot_spares = None
        self.number_of_global_hot_spares = None
        self.min_drive_size = None
        self.use_remaining_disks = None
        self.use_jbod_disks = None

        if self._config.load_from == "live":
            if lstorage_disk_group_config_policy is not None:
                self.name = lstorage_disk_group_config_policy.name
                self.descr = lstorage_disk_group_config_policy.descr
                self.raid_level = lstorage_disk_group_config_policy.raid_level

                if "lstorageVirtualDriveDef" in self._parent._config.sdk_objects:
                    for lstorage_virtual_drive_def in self._config.sdk_objects["lstorageVirtualDriveDef"]:
                        if self._parent._dn:
                            if self._parent._dn + "/disk-group-config-" + self.name + "/" \
                                    in lstorage_virtual_drive_def.dn:
                                self.write_cache_policy = lstorage_virtual_drive_def.write_cache_policy
                                self.io_policy = getattr(lstorage_virtual_drive_def, "io_policy", None)
                                self.security = lstorage_virtual_drive_def.security
                                self.read_policy = lstorage_virtual_drive_def.read_policy
                                self.strip_size = lstorage_virtual_drive_def.strip_size
                                self.access_policy = lstorage_virtual_drive_def.access_policy
                                self.drive_cache = lstorage_virtual_drive_def.drive_cache
                                break

                if "lstorageDiskGroupQualifier" in self._parent._config.sdk_objects:
                    for lstorage_virtual_drive_def in self._config.sdk_objects["lstorageDiskGroupQualifier"]:
                        if self._parent._dn:
                            if self._parent._dn + "/disk-group-config-" + self.name + "/" in \
                                    lstorage_virtual_drive_def.dn:
                                self.drive_type = lstorage_virtual_drive_def.drive_type
                                self.number_of_global_hot_spares = lstorage_virtual_drive_def.num_glob_hot_spares
                                self.number_of_dedicated_hot_spares = lstorage_virtual_drive_def.num_ded_hot_spares
                                self.use_remaining_disks = lstorage_virtual_drive_def.use_remaining_disks
                                self.use_jbod_disks = lstorage_virtual_drive_def.use_jbod_disks
                                self.min_drive_size = lstorage_virtual_drive_def.min_drive_size
                                self.number_of_drives = lstorage_virtual_drive_def.num_drives
                                break

                if "lstorageLocalDiskConfigRef" in self._parent._config.sdk_objects:
                    for lstorage_virtual_drive_def in self._config.sdk_objects["lstorageLocalDiskConfigRef"]:
                        if self._parent._dn:
                            if self._parent._dn + "/disk-group-config-" + self.name + "/" \
                                    in lstorage_virtual_drive_def.dn:
                                drive = {}
                                drive.update({"slot_number": lstorage_virtual_drive_def.slot_num})
                                drive.update({"role": lstorage_virtual_drive_def.role})
                                drive.update({"span_id": lstorage_virtual_drive_def.span_id})
                                self.manual_disk_group_configuration.append(drive)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def clean_object(self):
        UcsSystemConfigObject.clean_object(self)

        # We need to set all values that are not present in the config file to None
        for element in self.manual_disk_group_configuration:
            for value in ["slot_number", "role", "span_id"]:
                if value not in element:
                    element[value] = None

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME +
                        " configuration: " + str(self.name))
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + str(self.name) +
                                ", waiting for a commit")

        if hasattr(self._parent, '_dn'):
            parent_mo = self._parent._dn
        else:
            self.logger(level="error", message="Impossible to find the parent dn of " + self._CONFIG_NAME + " : "
                                               + str(self.name))
            return False

        mo_lstorage_disk_group_config_policy = LstorageDiskGroupConfigPolicy(parent_mo_or_dn=parent_mo, name=self.name,
                                                                             raid_level=self.raid_level,
                                                                             descr=self.descr)
        if self.io_policy:
            LstorageVirtualDriveDef(parent_mo_or_dn=mo_lstorage_disk_group_config_policy,
                                    write_cache_policy=self.write_cache_policy, io_policy=self.io_policy,
                                    security=self.security, read_policy=self.read_policy, strip_size=self.strip_size,
                                    access_policy=self.access_policy, drive_cache=self.drive_cache)
        else:
            LstorageVirtualDriveDef(parent_mo_or_dn=mo_lstorage_disk_group_config_policy,
                                    write_cache_policy=self.write_cache_policy,
                                    security=self.security, read_policy=self.read_policy, strip_size=self.strip_size,
                                    access_policy=self.access_policy, drive_cache=self.drive_cache)

        if len(self.manual_disk_group_configuration):
            for disk in self.manual_disk_group_configuration:
                role = disk["role"]
                if role == "dedicated-hot-spare":
                    role = "ded-hot-spare"
                elif role == "global-hot-spare":
                    role = "glob-hot-spare"

                LstorageLocalDiskConfigRef(parent_mo_or_dn=mo_lstorage_disk_group_config_policy,
                                           slot_num=disk['slot_number'], role=role, span_id=disk['span_id'])
        else:
            LstorageDiskGroupQualifier(parent_mo_or_dn=mo_lstorage_disk_group_config_policy, drive_type=self.drive_type,
                                       num_glob_hot_spares=self.number_of_global_hot_spares,
                                       num_ded_hot_spares=self.number_of_dedicated_hot_spares,
                                       use_remaining_disks=self.use_remaining_disks, use_jbod_disks=self.use_jbod_disks,
                                       min_drive_size=self.min_drive_size, num_drives=self.number_of_drives)

        self._handle.add_mo(mo=mo_lstorage_disk_group_config_policy, modify_present=True)

        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True


class UcsSystemStorageProfile(UcsSystemConfigObject):
    _CONFIG_NAME = "Storage Profile"
    _CONFIG_SECTION_NAME = "storage_profiles"
    _UCS_SDK_OBJECT_NAME = "lstorageProfile"
    _UCS_SDK_SPECIFIC_OBJECT_NAME = "lstorageProfileDef"
    _POLICY_MAPPING_TABLE = {
        "local_luns": [
            {
                "disk_group_policy": UcsSystemDiskGroupPolicy
            }
        ]
    }

    def __init__(self, parent=None, json_content=None, lstorage_profile=None):
        UcsSystemConfigObject.__init__(self, parent=parent, ucs_sdk_object=lstorage_profile)
        self.name = None
        self.descr = None
        self.auto_config_mode = None
        self.security_policy = []
        self.local_luns = []
        self.lun_sets = []
        self.controller_definitions = []
        self.hybrid_slot_configuration = []

        if self._config.load_from == "live":
            if lstorage_profile is not None:
                self.name = lstorage_profile.name
                self.descr = lstorage_profile.descr
                self.auto_config_mode = lstorage_profile.auto_config_mode

                if self._parent._dn:
                    if self._parent.__class__.__name__ == "UcsSystemServiceProfile":
                        # We are in presence of a Specific Storage Policy under a Service Profile object
                        self.name = None
                        storage_policy_dn = self._parent._dn + "/profile-def" + "/"
                    else:
                        storage_policy_dn = self._parent._dn + "/profile-" + self.name + "/"

                if "lstorageRemote" in self._parent._config.sdk_objects:
                    for remote_policy in self._config.sdk_objects["lstorageRemote"]:
                        if self._parent._dn:
                            if storage_policy_dn in remote_policy.dn:
                                policy = {}
                                policy.update({"type": "remote_policy"})
                                policy.update({"primary_ip_address": remote_policy.primary_server})
                                policy.update({"secondary_ip_address": remote_policy.secondary_server})
                                policy.update({"port": remote_policy.port})
                                policy.update({"kmip_server_public_certificate": remote_policy.server_cert})
                                policy.update({"deployed_key": remote_policy.deployed_security_key})
                                if "lstorageLogin" in self._parent._config.sdk_objects:
                                    for login in self._config.sdk_objects["lstorageLogin"]:
                                        if storage_policy_dn in login.dn:
                                            policy.update({"username": login.user_name})
                                            policy.update({"password": login.password})
                                            break
                                self.security_policy.append(policy)
                                break

                if "lstorageLocal" in self._parent._config.sdk_objects and not self.security_policy:
                    for local_policy in self._config.sdk_objects["lstorageLocal"]:
                        if self._parent._dn:
                            if storage_policy_dn in local_policy.dn:
                                policy = {}
                                policy.update({"type": "local_policy"})
                                policy.update({"key": local_policy.security_key})
                                # policy.update({"deployed_key": local_policy.deployed_security_key})
                                self.security_policy.append(policy)
                                break

                if "lstorageDasScsiLun" in self._parent._config.sdk_objects:
                    for lstorage_das_scsi_lun in self._config.sdk_objects["lstorageDasScsiLun"]:
                        if self._parent._dn:
                            if storage_policy_dn in lstorage_das_scsi_lun.dn:
                                lun = {"_object_type": "local_luns"}
                                # No difference between "name" in "Create Local LUN" and "Prepare Claim Local LUN"
                                lun.update({"name": lstorage_das_scsi_lun.name})
                                lun.update({"size": lstorage_das_scsi_lun.size})
                                lun.update({"fractional_size": lstorage_das_scsi_lun.fractional_size})
                                lun.update({"auto_deploy": lstorage_das_scsi_lun.auto_deploy})
                                lun.update({"expand_to_available": lstorage_das_scsi_lun.expand_to_avail})
                                lun.update({"disk_group_policy": lstorage_das_scsi_lun.local_disk_policy_name})

                                # Fetching the operational state of the referenced policies
                                oper_state = {}
                                oper_state.update(
                                    self.get_operational_state(
                                        policy_dn=lstorage_das_scsi_lun.oper_local_disk_policy_name,
                                        separator="/disk-group-config-",
                                        policy_name="disk_group_policy"
                                    )
                                )
                                lun['operational_state'] = oper_state

                                self.local_luns.append(lun)

                if "lstorageControllerDef" in self._parent._config.sdk_objects:
                    for lstorage_controller_def in self._config.sdk_objects["lstorageControllerDef"]:
                        if self._parent._dn:
                            if storage_policy_dn in lstorage_controller_def.dn:
                                controller_def = {}
                                controller_def.update({"name": lstorage_controller_def.name})
                                if "lstorageControllerModeConfig" in self._parent._config.sdk_objects:
                                    for lsstorage in self._config.sdk_objects["lstorageControllerModeConfig"]:
                                        if storage_policy_dn in lsstorage.dn:
                                            controller_def.update({"protected_configuration": lsstorage.protect_config})
                                            controller_def.update({"raid_level": lsstorage.raid_mode})
                                            break
                                self.controller_definitions.append(controller_def)

                if "lstorageLunSetConfig" in self._parent._config.sdk_objects:
                    for lun_set_config in self._config.sdk_objects["lstorageLunSetConfig"]:
                        if self._parent._dn:
                            if storage_policy_dn in lun_set_config.dn:
                                lun_set = {}
                                lun_set.update({"name": lun_set_config.name})
                                lun_set.update({"raid_level": lun_set_config.raid_level})
                                lun_set.update({"disk_slot_range": lun_set_config.disk_slot_range})
                                if "lstorageVirtualDriveDef" in self._parent._config.sdk_objects:
                                    for lsstorage in self._config.sdk_objects["lstorageVirtualDriveDef"]:
                                        if lun_set_config.dn in lsstorage.dn:
                                            lun_set.update({"strip_size": lsstorage.strip_size})
                                            lun_set.update({"access_policy": lsstorage.access_policy})
                                            lun_set.update({"read_policy": lsstorage.read_policy})
                                            lun_set.update({"write_cache_policy": lsstorage.write_cache_policy})
                                            lun_set.update({"io_policy": getattr(lsstorage, "io_policy", None)})
                                            lun_set.update({"drive_cache": lsstorage.drive_cache})
                                            lun_set.update({"security": lsstorage.security})
                                            break
                                self.lun_sets.append(lun_set)

                if "lstorageHybridDriveSlotConfig" in self._parent._config.sdk_objects:
                    for hybrid_drive_policy in self._config.sdk_objects["lstorageHybridDriveSlotConfig"]:
                        if self._parent._dn:
                            if storage_policy_dn in hybrid_drive_policy.dn:
                                policy = {}
                                policy.update({"direct_attached_slots": hybrid_drive_policy.direct_attached_slots})
                                policy.update({"raid_attached_slots": hybrid_drive_policy.raid_attached_slots})
                                self.hybrid_slot_configuration.append(policy)
                                break

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def clean_object(self):
        UcsSystemConfigObject.clean_object(self)

        # We need to set all values that are not present in the config file to None
        for element in self.security_policy:
            for value in ["primary_ip_address", "secondary_ip_address", "port",
                          "kmip_server_public_certificate", "username", "password", "deployed_key", "type",
                          "key"]:
                if value not in element:
                    element[value] = None
        for element in self.local_luns:
            element["_object_type"] = "local_luns"
            for value in ["name", "size", "fractional_size", "auto_deploy", "expand_to_available",
                          "disk_group_policy", "operational_state"]:
                if value not in element:
                    element[value] = None
            if element["operational_state"]:
                for policy in ["disk_group_policy"]:
                    if policy not in element["operational_state"]:
                        element["operational_state"][policy] = None
                    elif element["operational_state"][policy]:
                        for value in ["name", "org"]:
                            if value not in element["operational_state"][policy]:
                                element["operational_state"][policy][value] = None
        for element in self.controller_definitions:
            for value in ["name", "protected_configuration", "raid_level"]:
                if value not in element:
                    element[value] = None
        for element in self.lun_sets:
            for value in ["name", "disk_slot_range", "raid_level", "strip_size", "access_policy", "read_policy",
                          "write_cache_policy", "io_policy", "drive_cache", "security"]:
                if value not in element:
                    element[value] = None
        for element in self.hybrid_slot_configuration:
            for value in ["direct_attached_slots", "raid_attached_slots"]:
                if value not in element:
                    element[value] = None

    def push_object(self, commit=True):
        detail = str(self.name)
        if self._parent.__class__.__name__ == "UcsSystemServiceProfile":
            # We are in presence of a Specific Storage Policy under a Service Profile object
            detail = "Service Profile " + str(self._parent.name)

        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME +
                        " configuration: " + detail)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + detail +
                                ", waiting for a commit")

        if hasattr(self._parent, '_dn'):
            parent_mo = self._parent._dn
        else:
            self.logger(level="error", message="Impossible to find the parent dn of " + self._CONFIG_NAME + " : " +
                                               detail)
            return False

        if self._parent.__class__.__name__ == "UcsSystemServiceProfile":
            # We are in presence of a Specific Storage Policy under a Service Profile object
            mo_lstorage_profile = LstorageProfileDef(
                parent_mo_or_dn=parent_mo, descr=self.descr, auto_config_mode=self.auto_config_mode)
        else:
            # We are in presence of a regular Storage Policy under an Org object
            mo_lstorage_profile = LstorageProfile(
                parent_mo_or_dn=parent_mo, name=self.name, descr=self.descr, auto_config_mode=self.auto_config_mode)

        if self.security_policy:
            mo_security = LstorageSecurity(parent_mo_or_dn=mo_lstorage_profile)
            mo_drive_security = LstorageDriveSecurity(parent_mo_or_dn=mo_security)
            for policy in self.security_policy:
                if policy["type"] == "remote_policy":
                    mo_remote = LstorageRemote(parent_mo_or_dn=mo_drive_security,
                                               primary_server=policy['primary_ip_address'],
                                               port=policy['port'],
                                               secondary_server=policy['secondary_ip_address'],
                                               server_cert=policy['kmip_server_public_certificate'],
                                               deployed_security_key=policy['deployed_key'])
                    LstorageLogin(parent_mo_or_dn=mo_remote,
                                  user_name=policy['username'],
                                  password=policy['password'])
                elif policy["type"] == "local_policy":
                    LstorageLocal(parent_mo_or_dn=mo_drive_security,
                                  security_key=policy["key"])
                    # deployed_security_key=policy['deployed_key']
        if self.local_luns:
            for local_lun in self.local_luns:
                LstorageDasScsiLun(parent_mo_or_dn=mo_lstorage_profile, fractional_size=local_lun['fractional_size'],
                                   expand_to_avail=local_lun['expand_to_available'],
                                   local_disk_policy_name=local_lun['disk_group_policy'], size=local_lun['size'],
                                   name=local_lun['name'],
                                   auto_deploy=local_lun['auto_deploy'])
        if self.controller_definitions:
            for controller_definition in self.controller_definitions:
                mo_controller_def = LstorageControllerDef(parent_mo_or_dn=mo_lstorage_profile,
                                                          name=controller_definition['name'])
                LstorageControllerModeConfig(parent_mo_or_dn=mo_controller_def,
                                             protect_config=controller_definition['protected_configuration'],
                                             raid_mode=controller_definition['raid_level'])

        if self.lun_sets:
            for lun_set in self.lun_sets:
                mo_ls_storage_lun_set_config = LstorageLunSetConfig(parent_mo_or_dn=mo_lstorage_profile,
                                                                    disk_slot_range=lun_set['disk_slot_range'],
                                                                    name=lun_set['name'])
                if lun_set.get("io_policy", None):
                    LstorageVirtualDriveDef(parent_mo_or_dn=mo_ls_storage_lun_set_config,
                                            access_policy=lun_set['access_policy'],
                                            drive_cache=lun_set['drive_cache'],
                                            io_policy=lun_set['io_policy'],
                                            read_policy=lun_set['read_policy'],
                                            security=lun_set['security'],
                                            strip_size=lun_set['strip_size'],
                                            write_cache_policy=lun_set['write_cache_policy'])
                else:
                    LstorageVirtualDriveDef(parent_mo_or_dn=mo_ls_storage_lun_set_config,
                                            access_policy=lun_set['access_policy'],
                                            drive_cache=lun_set['drive_cache'],
                                            read_policy=lun_set['read_policy'],
                                            security=lun_set['security'],
                                            strip_size=lun_set['strip_size'],
                                            write_cache_policy=lun_set['write_cache_policy'])

        if self.hybrid_slot_configuration:
            for policy in self.hybrid_slot_configuration:
                LstorageHybridDriveSlotConfig(parent_mo_or_dn=mo_lstorage_profile,
                                              direct_attached_slots=policy['direct_attached_slots'],
                                              raid_attached_slots=policy['raid_attached_slots'])

        self._handle.add_mo(mo=mo_lstorage_profile, modify_present=True)

        if commit:
            detail = str(self.name)
            if self._parent.__class__.__name__ == "UcsSystemServiceProfile":
                # We are in presence of a Specific Storage Policy under a Service Profile object
                detail = "Service Profile " + str(self._parent.name)
            if self.commit(detail=detail) != True:
                return False
        return True
