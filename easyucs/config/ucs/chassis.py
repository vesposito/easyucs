# coding: utf-8
# !/usr/bin/env python

""" chassis.py: Easy UCS Deployment Tool """
from easyucs import __author__, __copyright__,  __version__, __status__


from easyucs.config.object import GenericUcsConfigObject, UcsImcConfigObject, UcsSystemConfigObject

from ucsmsdk.mometa.cpmaint.CpmaintMaintPolicy import CpmaintMaintPolicy
from ucsmsdk.mometa.equipment.EquipmentBinding import EquipmentBinding
from ucsmsdk.mometa.equipment.EquipmentChassisProfile import EquipmentChassisProfile
from ucsmsdk.mometa.equipment.EquipmentComputeConnPolicy import EquipmentComputeConnPolicy
from ucsmsdk.mometa.firmware.FirmwareChassisPack import FirmwareChassisPack
from ucsmsdk.mometa.firmware.FirmwareExcludeChassisComponent import FirmwareExcludeChassisComponent
from ucsmsdk.mometa.lstorage.LstorageControllerRef import LstorageControllerRef
from ucsmsdk.mometa.lstorage.LstorageDiskSlot import LstorageDiskSlot
from ucsmsdk.mometa.lstorage.LstorageDiskZoningPolicy import LstorageDiskZoningPolicy
from ucsmsdk.mometa.lstorage.LstorageSasExpanderConfigPolicy import LstorageSasExpanderConfigPolicy
from ucsmsdk.ucsbasetype import DnSet, Dn
from ucsmsdk.ucsmethodfactory import equipment_instantiate_n_named_template, equipment_instantiate_template


class UcsSystemChassisMaintenancePolicy(UcsSystemConfigObject):
    _CONFIG_NAME = "Chassis Maintenance Policy"
    _UCS_SDK_OBJECT_NAME = "cpmaintMaintPolicy"

    def __init__(self, parent=None, json_content=None, cpmaint_maint_policy=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.name = None
        self.descr = None

        if self._config.load_from == "live":
            if cpmaint_maint_policy is not None:
                self.name = cpmaint_maint_policy.name
                self.descr = cpmaint_maint_policy.descr

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

        mo_cpmaint_maint_policy = CpmaintMaintPolicy(parent_mo_or_dn=parent_mo, name=self.name, descr=self.descr)

        self._handle.add_mo(mo=mo_cpmaint_maint_policy, modify_present=True)

        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True


class UcsSystemComputeConnectionPolicy(UcsSystemConfigObject):
    _CONFIG_NAME = "Compute Connection Policy"
    _UCS_SDK_OBJECT_NAME = "equipmentComputeConnPolicy"

    def __init__(self, parent=None, json_content=None, equipment_compute_conn_policy=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.name = None
        self.descr = None
        self.server_sioc_connectivity = None

        if self._config.load_from == "live":
            if equipment_compute_conn_policy is not None:
                self.name = equipment_compute_conn_policy.name
                self.descr = equipment_compute_conn_policy.descr
                self.server_sioc_connectivity = equipment_compute_conn_policy.server_sioc_connectivity

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

        mo_equipment_compute_conn_policy = \
            EquipmentComputeConnPolicy(parent_mo_or_dn=parent_mo,
                                       server_sioc_connectivity=self.server_sioc_connectivity,
                                       name=self.name,
                                       descr=self.descr)
        self._handle.add_mo(mo=mo_equipment_compute_conn_policy, modify_present=True)

        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True


class UcsSystemChassisFirmwarePackage(UcsSystemConfigObject):
    _CONFIG_NAME = "Chassis Firmware Package"
    _UCS_SDK_OBJECT_NAME = "firmwareChassisPack"

    def __init__(self, parent=None, json_content=None, firmware_chassis_pack=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.descr = None
        self.name = None
        self.chassis_package = None
        self.service_pack = None
        self.excluded_components = []

        if self._config.load_from == "live":
            if firmware_chassis_pack is not None:
                self.name = firmware_chassis_pack.name
                self.descr = firmware_chassis_pack.descr
                self.chassis_package = firmware_chassis_pack.chassis_bundle_version
                self.service_pack = firmware_chassis_pack.service_pack_bundle_version

                if "firmwareExcludeChassisComponent" in self._parent._config.sdk_objects:
                    for excluded in self._config.sdk_objects["firmwareExcludeChassisComponent"]:
                        if self._parent._dn:
                            if self._parent._dn + "/fw-chassis-pack-" + self.name + "/" in excluded.dn:
                                self.excluded_components.append(excluded.chassis_component)

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

        override_default_exclusion = "no"
        # TODO Check if still relevant
        # It is the only way to remove "local-disk" value in the excluded content (checked by default)
        # if 'local-disk' not in self.exclude:
        #     override_default_exclusion = "yes"
        # Same in UcsSystemHostFirmwarePackage

        mo_firmware_chassis_pack = FirmwareChassisPack(parent_mo_or_dn=parent_mo,
                                                       name=self.name,
                                                       descr=self.descr,
                                                       chassis_bundle_version=self.chassis_package,
                                                       override_default_exclusion=override_default_exclusion,
                                                       service_pack_bundle_version=self.service_pack)

        for excluded in self.excluded_components:
            element = excluded
            if element == "chassis-management-controller":
                element = "cmc"
            if element == "chassis-adaptor":
                element = "iocard"
            FirmwareExcludeChassisComponent(parent_mo_or_dn=mo_firmware_chassis_pack,
                                            chassis_component=element)

        self._handle.add_mo(mo=mo_firmware_chassis_pack, modify_present=True)

        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True


class UcsSystemDiskZoningPolicy(UcsSystemConfigObject):
    _CONFIG_NAME = "Disk Zoning Policy"
    _UCS_SDK_OBJECT_NAME = "lstorageDiskZoningPolicy"

    def __init__(self, parent=None, json_content=None, lstorage_disk_zoning_policy=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.descr = None
        self.name = None
        self.preserve_config = None
        self.disks_zoned = []

        if self._config.load_from == "live":
            if lstorage_disk_zoning_policy is not None:
                self.name = lstorage_disk_zoning_policy.name
                self.descr = lstorage_disk_zoning_policy.descr
                self.preserve_config = lstorage_disk_zoning_policy.preserve_config

                if "lstorageDiskSlot" in self._parent._config.sdk_objects:
                    for disk_slot in self._config.sdk_objects["lstorageDiskSlot"]:
                        if self._parent._dn:
                            if self._parent._dn + "/disk-zoning-policy-" + self.name + "/" in disk_slot.dn:
                                disk = {}
                                disk.update({"ownership": disk_slot.ownership})
                                disk.update({"drive_path": disk_slot.drive_path.lower()})
                                disk.update({"disk_slot": disk_slot.id})
                                # disk.update({"disk_slot_range_start": disk_slot.id.split("-")[0]})
                                # disk.update({"disk_slot_range_stop": disk_slot.id.split("-")[1]})
                                if "lstorageControllerRef" in self._parent._config.sdk_objects:
                                    for controller_ref in self._config.sdk_objects["lstorageControllerRef"]:
                                        if self._parent._dn + "/disk-zoning-policy-" + self.name + "/" \
                                                in controller_ref.dn:
                                            disk.update({"controller": controller_ref.controller_id})
                                            disk.update({"server": controller_ref.server_id})
                                self.disks_zoned.append(disk)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

                # We need to set all values that are not present in the config file to None
                for element in self.disks_zoned:
                    for value in ["server", "controller", "slot_range", "ownership", "disk_slot_range_start",
                                  "disk_slot_range_stop", "drive_path"]:
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

        mo_lstorage_disk_zoning_policy = LstorageDiskZoningPolicy(parent_mo_or_dn=parent_mo,
                                                                  preserve_config=self.preserve_config,
                                                                  name=self.name,
                                                                  descr=self.descr)
        for disk in self.disks_zoned:
            ownership = disk['ownership']
            if ownership == "chassis-global-hot-spare":
                ownership = "chassis-global-spare"
            drive_path = disk["drive_path"]
            if drive_path:
                drive_path = drive_path.upper()

            if disk["disk_slot_range_start"] and disk["disk_slot_range_stop"]:
                for slot_id in range(int(disk["disk_slot_range_start"]), int(disk["disk_slot_range_stop"])+1):
                    mo_lstorage_disk_slot = LstorageDiskSlot(parent_mo_or_dn=mo_lstorage_disk_zoning_policy,
                                                             id=str(slot_id), ownership=ownership,
                                                             drive_path=drive_path)
                    if ownership == "dedicated":
                        LstorageControllerRef(parent_mo_or_dn=mo_lstorage_disk_slot, controller_id=disk['controller'],
                                              server_id=disk['server'], controller_type="SAS")

            else:
                mo_lstorage_disk_slot = LstorageDiskSlot(parent_mo_or_dn=mo_lstorage_disk_zoning_policy,
                                                         id=disk['disk_slot'], ownership=ownership,
                                                         drive_path=drive_path)
                if ownership == "dedicated":
                    LstorageControllerRef(parent_mo_or_dn=mo_lstorage_disk_slot, controller_id=disk['controller'],
                                          server_id=disk['server'], controller_type="SAS")

        self._handle.add_mo(mo=mo_lstorage_disk_zoning_policy, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True


class UcsSystemChassisProfile(UcsSystemConfigObject):
    _CONFIG_NAME = "Chassis Profile"
    _UCS_SDK_OBJECT_NAME = "equipmentChassisProfile"

    def __init__(self, parent=None, json_content=None, equipment_chassis_profile=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.descr = None
        self.name = None
        self.type = None
        self.disk_zoning_policy = None
        self.chassis_firmware_policy = None
        self.compute_connection_policy = None
        self.chassis_maintenance_policy = None
        self.sas_expander_configuration_policy = None
        self.chassis_assignment_id = None
        self.restrict_migration = None

        self.chassis_profile_template = None
        self.suffix_start_number = None
        self.number_of_instances = None

        if self._config.load_from == "live":
            if equipment_chassis_profile is not None:
                self.name = equipment_chassis_profile.name
                self.descr = equipment_chassis_profile.descr
                self.type = equipment_chassis_profile.type
                self.chassis_profile_template = equipment_chassis_profile.src_templ_name

                parent_template_type = None
                if self.chassis_profile_template:
                    # We first try to get the CP Template object by using the operSrcTemplName attribute value
                    if equipment_chassis_profile.oper_src_templ_name:
                        mo_template_cp = self._device.query(mode="dn",
                                                            target=equipment_chassis_profile.oper_src_templ_name)
                        if mo_template_cp:
                            parent_template_type = mo_template_cp.type
                    else:
                        # If the operSrcTemplName attribute is not set (e.g. with UCS Central), we try to find the CP
                        # Template using a query for its name. In case it is the only object with this name, we use it
                        filter_str = '(name, "' + self.chassis_profile_template + '", type="eq")'
                        mo_template_cp = self._device.query(mode="classid", target="equipmentChassisProfile",
                                                            filter_str=filter_str)
                        if len(mo_template_cp) == 1:
                            parent_template_type = mo_template_cp[0].type

                if parent_template_type != "updating-template":
                    self.disk_zoning_policy = equipment_chassis_profile.disk_zoning_policy_name
                    self.chassis_firmware_policy = equipment_chassis_profile.chassis_fw_policy_name
                    self.compute_connection_policy = equipment_chassis_profile.compute_conn_policy_name
                    self.chassis_maintenance_policy = equipment_chassis_profile.maint_policy_name
                    self.sas_expander_configuration_policy = equipment_chassis_profile.sas_expander_config_policy_name
                if self.type == "instance":
                    if "equipmentBinding" in self._parent._config.sdk_objects:
                        for binding in self._config.sdk_objects["equipmentBinding"]:
                            if self._parent._dn:
                                if self._parent._dn + "/cp-" + self.name + "/" in binding.dn:
                                    if binding.chassis_dn:
                                        self.chassis_assignment_id = binding.chassis_dn.split("-")[1]
                                    self.restrict_migration = binding.restrict_migration

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

        mo_equipment_chassis_profile = EquipmentChassisProfile(parent_mo_or_dn=parent_mo,
                                                               disk_zoning_policy_name=self.disk_zoning_policy,
                                                               descr=self.descr, type=self.type, name=self.name,
                                                               chassis_fw_policy_name=self.chassis_firmware_policy,
                                                               compute_conn_policy_name=self.compute_connection_policy,
                                                               maint_policy_name=self.chassis_maintenance_policy,
                                                               sas_expander_config_policy_name=
                                                               self.sas_expander_configuration_policy)

        if self.type == "instance" and self.chassis_assignment_id:
            EquipmentBinding(parent_mo_or_dn=mo_equipment_chassis_profile,
                             chassis_dn="sys/chassis-" + self.chassis_assignment_id,
                             restrict_migration=self.restrict_migration)

        self._handle.add_mo(mo=mo_equipment_chassis_profile, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True

    def instantiate_profile(self):
        self.logger(message="Instantiating " + self._CONFIG_NAME + " configuration from " +
                            str(self.chassis_profile_template))

        if hasattr(self._parent, '_dn'):
            parent_mo = self._parent._dn
        else:
            self.logger(level="error",
                        message="Impossible to find the parent dn of " + self._CONFIG_NAME + " : " + str(self.name))
            return False

        if not hasattr(self, 'suffix_start_number'):
            self.suffix_start_number = "1"
        if not hasattr(self, 'number_of_instances'):
            self.number_of_instances = "1"

        if self.suffix_start_number and self.number_of_instances:
            dn_set = DnSet()
            for i in range(int(self.suffix_start_number),
                           int(self.number_of_instances) + int(self.suffix_start_number)):
                dn = Dn()
                dn.attr_set("value", str(self.name + str(i)))
                dn_set.child_add(dn)

            elem = equipment_instantiate_n_named_template(cookie=self._handle.cookie,
                                                          dn=parent_mo + "/cp-" + self.chassis_profile_template,
                                                          in_error_on_existing="false", in_name_set=dn_set,
                                                          in_target_org=parent_mo, in_hierarchical="false")

            for i in range(self._device.push_attempts):
                try:
                    if i:
                        self.logger(level="warning",
                                    message="Trying to push again the instantiated chassis profile(s) from " +
                                            str(self.chassis_profile_template))
                    self._handle.process_xml_elem(elem)
                    self.logger(level='debug',
                                message=self.number_of_instances + " " + self._CONFIG_NAME + " instantiated from " +
                                        str(self.chassis_profile_template) + " starting with " + str(self.name) +
                                        self.suffix_start_number)
                    return True
                except ConnectionRefusedError:
                    self.logger(level="error", message="Connection refused while trying to instantiate from " +
                                                       str(self.chassis_profile_template))
                except UcsException as err:
                    self.logger(level="error",
                                message="Error while trying to instantiate from " +
                                        str(self.chassis_profile_template) + " " + err.error_descr)
                except urllib.error.URLError:
                    self.logger(level="error",
                                message="Timeout while trying to instantiate from " + str(
                                    self.chassis_profile_template))

        else:
            elem = equipment_instantiate_template(cookie=self._handle.cookie,
                                                  dn=parent_mo + "/cp-" + self.chassis_profile_template,
                                                  in_error_on_existing="false",
                                                  in_chassis_profile_name=self.name,
                                                  in_target_org=parent_mo, in_hierarchical="false")

            for i in range(self._device.push_attempts):
                try:
                    if i:
                        self.logger(level="warning",
                                    message="Trying to push again the instantiated chassis profile(s) from " +
                                            str(self.chassis_profile_template))
                    self._handle.process_xml_elem(elem)
                    self.logger(level='debug',
                                message=self._CONFIG_NAME + " " + str(self.name) + " instantiated from " +
                                        str(self.chassis_profile_template))

                    # We now need to associate the instantiated Chassis Profile to the Chassis ID if provided
                    if self.type == "instance" and self.chassis_assignment_id:
                        mo_equipment_chassis_profile = EquipmentChassisProfile(parent_mo_or_dn=parent_mo,
                                                                               name=self.name)
                        EquipmentBinding(parent_mo_or_dn=mo_equipment_chassis_profile,
                                         chassis_dn="sys/chassis-" + self.chassis_assignment_id,
                                         restrict_migration=self.restrict_migration)

                    self._handle.add_mo(mo=mo_equipment_chassis_profile, modify_present=True)
                    if self.commit(detail=self.name) != True:
                        return False

                    return True

                except ConnectionRefusedError:
                    self.logger(level="error", message="Connection refused while trying to instantiate from " +
                                                       str(self.chassis_profile_template))
                except UcsException as err:
                    self.logger(level="error",
                                message="Error while trying to instantiate from " +
                                        str(self.chassis_profile_template) + " " + err.error_descr)
                except urllib.error.URLError:
                    self.logger(level="error",
                                message="Timeout while trying to instantiate from " + str(
                                    self.chassis_profile_template))


class UcsSystemSasExpanderConfigurationPolicy(UcsSystemConfigObject):
    _CONFIG_NAME = "SAS Expander Configuration Policy"
    _UCS_SDK_OBJECT_NAME = "lstorageSasExpanderConfigPolicy"

    def __init__(self, parent=None, json_content=None, ls_storage_sas_expander_config_policy=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.descr = None
        self.name = None
        self.mixed_mode = None

        if self._config.load_from == "live":
            if ls_storage_sas_expander_config_policy is not None:
                self.name = ls_storage_sas_expander_config_policy.name
                self.descr = ls_storage_sas_expander_config_policy.descr
                self.mixed_mode = ls_storage_sas_expander_config_policy.connection_management

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

        mixed_mode = self.mixed_mode
        if mixed_mode == "no-change":
            mixed_mode = "default"

        mo_ls_storage_sas_expander_config_policy = \
            LstorageSasExpanderConfigPolicy(parent_mo_or_dn=parent_mo,
                                            connection_management=mixed_mode,
                                            descr=self.descr,
                                            name=self.name)

        self._handle.add_mo(mo=mo_ls_storage_sas_expander_config_policy, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True
