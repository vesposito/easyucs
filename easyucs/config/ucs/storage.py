# coding: utf-8
# !/usr/bin/env python

""" storage.py: Easy UCS Deployment Tool """
from easyucs import __author__, __copyright__,  __version__, __status__

from ucsmsdk.mometa.lstorage.LstorageControllerDef import LstorageControllerDef
from ucsmsdk.mometa.lstorage.LstorageControllerModeConfig import LstorageControllerModeConfig
from ucsmsdk.mometa.lstorage.LstorageDasScsiLun import LstorageDasScsiLun
from ucsmsdk.mometa.lstorage.LstorageDiskGroupConfigPolicy import LstorageDiskGroupConfigPolicy
from ucsmsdk.mometa.lstorage.LstorageDiskGroupQualifier import LstorageDiskGroupQualifier
from ucsmsdk.mometa.lstorage.LstorageDriveSecurity import LstorageDriveSecurity
from ucsmsdk.mometa.lstorage.LstorageLocal import LstorageLocal
from ucsmsdk.mometa.lstorage.LstorageLocalDiskConfigRef import LstorageLocalDiskConfigRef
from ucsmsdk.mometa.lstorage.LstorageLogin import LstorageLogin
from ucsmsdk.mometa.lstorage.LstorageLunSetConfig import LstorageLunSetConfig
from ucsmsdk.mometa.lstorage.LstorageProfile import LstorageProfile
from ucsmsdk.mometa.lstorage.LstorageRemote import LstorageRemote
from ucsmsdk.mometa.lstorage.LstorageSecurity import LstorageSecurity
from ucsmsdk.mometa.lstorage.LstorageVirtualDriveDef import LstorageVirtualDriveDef

from easyucs.config.object import UcsSystemConfigObject


class UcsSystemDiskGroupPolicy(UcsSystemConfigObject):
    _CONFIG_NAME = "Disk Group Policy"
    _UCS_SDK_OBJECT_NAME = "lstorageDiskGroupConfigPolicy"

    # TODO:  if a disk group configuration manual exists you can not change it to automatic and vice-versa
    # Object LstorageLocalDiskConfigRef and LstorageDiskGroupQualifier can not exist alongside each other
    # You need to remove one MO in order to create the other.

    def __init__(self, parent=None, json_content=None, lstorage_disk_group_config_policy=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
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
                            if self._parent._dn + "/disk-group-config-" + self.name \
                                    in lstorage_disk_group_config_policy.dn:
                                self.write_cache_policy = lstorage_virtual_drive_def.write_cache_policy
                                self.io_policy = lstorage_virtual_drive_def.io_policy
                                self.security = lstorage_virtual_drive_def.security
                                self.read_policy = lstorage_virtual_drive_def.read_policy
                                self.strip_size = lstorage_virtual_drive_def.strip_size
                                self.access_policy = lstorage_virtual_drive_def.access_policy
                                self.drive_cache = lstorage_virtual_drive_def.drive_cache

                if "lstorageLocalDiskConfigRef" in self._parent._config.sdk_objects:
                    for lstorage_virtual_drive_def in self._config.sdk_objects["lstorageLocalDiskConfigRef"]:
                        if self._parent._dn:
                            if self._parent._dn + "/disk-group-config-" + self.name in lstorage_virtual_drive_def.dn:
                                drive = {}
                                drive.update({"slot_number": lstorage_virtual_drive_def.slot_num})
                                drive.update({"role": lstorage_virtual_drive_def.role})
                                drive.update({"span_id": lstorage_virtual_drive_def.span_id})
                                self.manual_disk_group_configuration.append(drive)

                if "lstorageDiskGroupQualifier" in self._parent._config.sdk_objects:
                    for lstorage_virtual_drive_def in self._config.sdk_objects["lstorageDiskGroupQualifier"]:
                        if self._parent._dn:
                            if self._parent._dn + "/disk-group-config-" + self.name in lstorage_virtual_drive_def.dn:
                                self.drive_type = lstorage_virtual_drive_def.drive_type
                                self.number_of_global_hot_spares = lstorage_virtual_drive_def.num_glob_hot_spares
                                self.number_of_dedicated_hot_spares = lstorage_virtual_drive_def.num_ded_hot_spares
                                self.use_remaining_disks = lstorage_virtual_drive_def.use_remaining_disks
                                self.use_jbod_disks = lstorage_virtual_drive_def.use_jbod_disks
                                self.min_drive_size = lstorage_virtual_drive_def.min_drive_size
                                self.number_of_drives = lstorage_virtual_drive_def.num_drives

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

                # We need to set all values that are not present in the config file to None
                for element in self.manual_disk_group_configuration:
                    for value in ["slot_number", "role", "span_id"]:
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
            self.logger(level="error", message="Impossible to find the parent dn of " + self._CONFIG_NAME + " : "
                                               + str(self.name))
            return False

        mo_lstorage_disk_group_config_policy = LstorageDiskGroupConfigPolicy(parent_mo_or_dn=parent_mo, name=self.name,
                                                                             raid_level=self.raid_level,
                                                                             descr=self.descr)
        LstorageVirtualDriveDef(parent_mo_or_dn=mo_lstorage_disk_group_config_policy,
                                write_cache_policy=self.write_cache_policy, io_policy=self.io_policy,
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
    _UCS_SDK_OBJECT_NAME = "lstorageProfile"

    def __init__(self, parent=None, json_content=None, lstorage_profile=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.name = None
        self.descr = None
        self.security_policy = []
        self.local_luns = []
        self.lun_sets = []
        self.controller_definitions = []

        if self._config.load_from == "live":
            if lstorage_profile is not None:
                self.name = lstorage_profile.name
                self.descr = lstorage_profile.descr

                if "lstorageRemote" in self._parent._config.sdk_objects:
                    for remote_policy in self._config.sdk_objects["lstorageRemote"]:
                        if self._parent._dn:
                            if self._parent._dn + "/profile-" + self.name + "/" in remote_policy.dn:
                                policy = {}
                                policy.update({"type": "remote_policy"})
                                policy.update({"primary_ip_address": remote_policy.primary_server})
                                policy.update({"secondary_ip_address": remote_policy.secondary_server})
                                policy.update({"port": remote_policy.port})
                                policy.update({"kmip_server_public_certificate": remote_policy.server_cert})
                                policy.update({"deployed_key": remote_policy.deployed_security_key})
                                if "lstorageLogin" in self._parent._config.sdk_objects:
                                    for login in self._config.sdk_objects["lstorageLogin"]:
                                        if self._parent._dn + "/profile-" + self.name + "/" in login.dn:
                                            policy.update({"username": login.user_name})
                                            policy.update({"password": login.password})
                                self.security_policy.append(policy)
                if "lstorageLocal" in self._parent._config.sdk_objects and not self.security_policy:
                    for remote_policy in self._config.sdk_objects["lstorageLocal"]:
                        if self._parent._dn:
                            if self._parent._dn + "/profile-" + self.name + "/" in remote_policy.dn:
                                policy = {}
                                policy.update({"type": "local_policy"})
                                policy.update({"key": remote_policy.security_key})
                                # policy.update({"deployed_key": remote_policy.deployed_security_key})
                                self.security_policy.append(policy)

                if "lstorageDasScsiLun" in self._parent._config.sdk_objects:
                    for lstorage_das_scsi_lun in self._config.sdk_objects["lstorageDasScsiLun"]:
                        if self._parent._dn:
                            if self._parent._dn + "/profile-" + self.name + "/" in lstorage_das_scsi_lun.dn:
                                lun = {}
                                # No difference between "name" in "Create Local LUN" and "Prepare Claim Local LUN"
                                lun.update({"name": lstorage_das_scsi_lun.name})
                                lun.update({"size": lstorage_das_scsi_lun.size})
                                lun.update({"fractional_size": lstorage_das_scsi_lun.fractional_size})
                                lun.update({"auto_deploy": lstorage_das_scsi_lun.auto_deploy})
                                lun.update({"expand_to_available": lstorage_das_scsi_lun.expand_to_avail})
                                lun.update({"disk_group_policy": lstorage_das_scsi_lun.local_disk_policy_name})
                                self.local_luns.append(lun)

                if "lstorageControllerDef" in self._parent._config.sdk_objects:
                    for lstorage_controller_def in self._config.sdk_objects["lstorageControllerDef"]:
                        if self._parent._dn:
                            if self._parent._dn + "/profile-" + self.name + "/" in lstorage_controller_def.dn:
                                controller_def = {}
                                controller_def.update({"name": lstorage_controller_def.name})
                                if "lstorageControllerModeConfig" in self._parent._config.sdk_objects:
                                    for lsstorage in self._config.sdk_objects["lstorageControllerModeConfig"]:
                                        if self._parent._dn + "/profile-" + self.name + "/" in lsstorage.dn:
                                            controller_def.update({"protected_configuration": lsstorage.protect_config})
                                            controller_def.update({"raid_level": lsstorage.raid_mode})
                                self.controller_definitions.append(controller_def)

                if "lstorageLunSetConfig" in self._parent._config.sdk_objects:
                    for lun_set_config in self._config.sdk_objects["lstorageLunSetConfig"]:
                        if self._parent._dn:
                            if self._parent._dn + "/profile-" + self.name + "/" in lun_set_config.dn:
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
                                            lun_set.update({"io_policy": lsstorage.io_policy})
                                            lun_set.update({"drive_cache": lsstorage.drive_cache})
                                            lun_set.update({"security": lsstorage.security})
                                self.lun_sets.append(lun_set)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

                # We need to set all values that are not present in the config file to None
                for element in self.security_policy:
                    for value in ["primary_ip_address", "secondary_ip_address", "port",
                                  "kmip_server_public_certificate", "username", "password", "deployed_key", "type",
                                  "key"]:
                        if value not in element:
                            element[value] = None
                for element in self.local_luns:
                    for value in ["name", "size", "fractional_size", "auto_deploy", "expand_to_available",
                                  "disk_group_policy"]:
                        if value not in element:
                            element[value] = None
                for element in self.controller_definitions:
                    for value in ["name", "protected_configuration", "raid_level"]:
                        if value not in element:
                            element[value] = None
                for element in self.controller_definitions:
                    for value in ["name", "disk_slot_range", "raid_level", "strip_size", "access_policy", "read_policy",
                                  "write_cache_policy", "io_policy", "drive_cache", "security"]:
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
            self.logger(level="error", message="Impossible to find the parent dn of " + self._CONFIG_NAME + " : " +
                                               str(self.name))
            return False

        mo_lstorage_profile = LstorageProfile(parent_mo_or_dn=parent_mo, name=self.name, descr=self.descr)
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
                LstorageVirtualDriveDef(parent_mo_or_dn=mo_ls_storage_lun_set_config,
                                        access_policy=lun_set['access_policy'],
                                        drive_cache=lun_set['drive_cache'],
                                        io_policy=lun_set['io_policy'],
                                        read_policy=lun_set['read_policy'],
                                        security=lun_set['security'],
                                        strip_size=lun_set['strip_size'],
                                        write_cache_policy=lun_set['write_cache_policy'])

        self._handle.add_mo(mo=mo_lstorage_profile, modify_present=True)

        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True
