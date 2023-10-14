# coding: utf-8
# !/usr/bin/env python

""" policies.py: Easy UCS Central Policies objects """

import hashlib
import urllib

from ucscsdk.mometa.aaa.AaaEpAuthProfile import AaaEpAuthProfile
from ucscsdk.mometa.aaa.AaaEpUser import AaaEpUser
# from ucscsdk.mometa.adaptor.AdaptorAzureQosProfile import AdaptorAzureQosProfile
from ucscsdk.mometa.adaptor.AdaptorCapQual import AdaptorCapQual
from ucscsdk.mometa.adaptor.AdaptorEthAdvFilterProfile import AdaptorEthAdvFilterProfile
from ucscsdk.mometa.adaptor.AdaptorEthArfsProfile import AdaptorEthArfsProfile
from ucscsdk.mometa.adaptor.AdaptorEthCompQueueProfile import AdaptorEthCompQueueProfile
from ucscsdk.mometa.adaptor.AdaptorEthFailoverProfile import AdaptorEthFailoverProfile
from ucscsdk.mometa.adaptor.AdaptorEthGENEVEProfile import AdaptorEthGENEVEProfile
from ucscsdk.mometa.adaptor.AdaptorEthInterruptProfile import AdaptorEthInterruptProfile
from ucscsdk.mometa.adaptor.AdaptorEthInterruptScalingProfile import AdaptorEthInterruptScalingProfile
from ucscsdk.mometa.adaptor.AdaptorEthNVGREProfile import AdaptorEthNVGREProfile
from ucscsdk.mometa.adaptor.AdaptorEthOffloadProfile import AdaptorEthOffloadProfile
from ucscsdk.mometa.adaptor.AdaptorEthRecvQueueProfile import AdaptorEthRecvQueueProfile
from ucscsdk.mometa.adaptor.AdaptorEthRoCEProfile import AdaptorEthRoCEProfile
from ucscsdk.mometa.adaptor.AdaptorEthVxLANProfile import AdaptorEthVxLANProfile
from ucscsdk.mometa.adaptor.AdaptorEthWorkQueueProfile import AdaptorEthWorkQueueProfile
from ucscsdk.mometa.adaptor.AdaptorFcCdbWorkQueueProfile import AdaptorFcCdbWorkQueueProfile
from ucscsdk.mometa.adaptor.AdaptorFcErrorRecoveryProfile import AdaptorFcErrorRecoveryProfile
from ucscsdk.mometa.adaptor.AdaptorFcFnicProfile import AdaptorFcFnicProfile
from ucscsdk.mometa.adaptor.AdaptorFcInterruptProfile import AdaptorFcInterruptProfile
from ucscsdk.mometa.adaptor.AdaptorFcPortFLogiProfile import AdaptorFcPortFLogiProfile
from ucscsdk.mometa.adaptor.AdaptorFcPortPLogiProfile import AdaptorFcPortPLogiProfile
from ucscsdk.mometa.adaptor.AdaptorFcPortProfile import AdaptorFcPortProfile
from ucscsdk.mometa.adaptor.AdaptorFcRecvQueueProfile import AdaptorFcRecvQueueProfile
# from ucscsdk.mometa.adaptor.AdaptorFcVhbaTypeProfile import AdaptorFcVhbaTypeProfile
from ucscsdk.mometa.adaptor.AdaptorFcWorkQueueProfile import AdaptorFcWorkQueueProfile
from ucscsdk.mometa.adaptor.AdaptorHostEthIfProfile import AdaptorHostEthIfProfile
from ucscsdk.mometa.adaptor.AdaptorHostFcIfProfile import AdaptorHostFcIfProfile
from ucscsdk.mometa.adaptor.AdaptorHostIscsiIfProfile import AdaptorHostIscsiIfProfile
from ucscsdk.mometa.adaptor.AdaptorQual import AdaptorQual
from ucscsdk.mometa.adaptor.AdaptorProtocolProfile import AdaptorProtocolProfile
from ucscsdk.mometa.adaptor.AdaptorRssProfile import AdaptorRssProfile
from ucscsdk.mometa.bios.BiosTokenSettings import BiosTokenSettings
from ucscsdk.mometa.bios.BiosVProfile import BiosVProfile
from ucscsdk.mometa.cimcvmedia.CimcvmediaConfigMountEntry import CimcvmediaConfigMountEntry
from ucscsdk.mometa.cimcvmedia.CimcvmediaMountConfigDef import CimcvmediaMountConfigDef
from ucscsdk.mometa.cimcvmedia.CimcvmediaMountConfigPolicy import CimcvmediaMountConfigPolicy
from ucscsdk.mometa.compute.ComputeChassisQual import ComputeChassisQual
from ucscsdk.mometa.compute.ComputeDomainGroupQual import ComputeDomainGroupQual
from ucscsdk.mometa.compute.ComputeDomainHwChangeDiscPolicy import ComputeDomainHwChangeDiscPolicy
from ucscsdk.mometa.compute.ComputeDomainNameQual import ComputeDomainNameQual
from ucscsdk.mometa.compute.ComputeDomainPortDiscPolicy import ComputeDomainPortDiscPolicy
from ucscsdk.mometa.compute.ComputeDomainQual import ComputeDomainQual
from ucscsdk.mometa.compute.ComputeGraphicsCardPolicy import ComputeGraphicsCardPolicy
from ucscsdk.mometa.compute.ComputeOwnerQual import ComputeOwnerQual
from ucscsdk.mometa.compute.ComputePhysicalQual import ComputePhysicalQual
from ucscsdk.mometa.compute.ComputePowerSyncPolicy import ComputePowerSyncPolicy
from ucscsdk.mometa.compute.ComputeProductFamilyQual import ComputeProductFamilyQual
from ucscsdk.mometa.compute.ComputeQual import ComputeQual
from ucscsdk.mometa.compute.ComputeRackQual import ComputeRackQual
from ucscsdk.mometa.compute.ComputeScrubPolicy import ComputeScrubPolicy
from ucscsdk.mometa.compute.ComputeSiteQual import ComputeSiteQual
from ucscsdk.mometa.compute.ComputeSlotQual import ComputeSlotQual
from ucscsdk.mometa.compute.ComputeSystemAddrQual import ComputeSystemAddrQual
from ucscsdk.mometa.dpsec.DpsecMac import DpsecMac
from ucscsdk.mometa.epqos.EpqosDefinition import EpqosDefinition
from ucscsdk.mometa.epqos.EpqosEgress import EpqosEgress
from ucscsdk.mometa.equipment.EquipmentComputeConnPolicy import EquipmentComputeConnPolicy
from ucscsdk.mometa.fabric.FabricEthLinkProfile import FabricEthLinkProfile
from ucscsdk.mometa.fabric.FabricLacpPolicy import FabricLacpPolicy
from ucscsdk.mometa.fabric.FabricMulticastPolicy import FabricMulticastPolicy
from ucscsdk.mometa.fabric.FabricNetGroupRef import FabricNetGroupRef
from ucscsdk.mometa.fabric.FabricUdldLinkPolicy import FabricUdldLinkPolicy
from ucscsdk.mometa.fabric.FabricVCon import FabricVCon
from ucscsdk.mometa.fabric.FabricVConProfile import FabricVConProfile
from ucscsdk.mometa.firmware.FirmwareChassisPack import FirmwareChassisPack
from ucscsdk.mometa.firmware.FirmwareComputeHostPack import FirmwareComputeHostPack
from ucscsdk.mometa.firmware.FirmwareExcludeChassisComponent import FirmwareExcludeChassisComponent
from ucscsdk.mometa.firmware.FirmwareExcludeServerComponent import FirmwareExcludeServerComponent
from ucscsdk.mometa.flowctrl.FlowctrlItem import FlowctrlItem
from ucscsdk.mometa.identpool.IdentpoolBlockQual import IdentpoolBlockQual
from ucscsdk.mometa.identpool.IdentpoolDomainGroupQual import IdentpoolDomainGroupQual
from ucscsdk.mometa.inband.InbandPolicy import InbandPolicy
from ucscsdk.mometa.iscsi.IscsiAuthProfile import IscsiAuthProfile
from ucscsdk.mometa.lsboot.LsbootBootSecurity import LsbootBootSecurity
from ucscsdk.mometa.lsboot.LsbootDef import LsbootDef
from ucscsdk.mometa.lsboot.LsbootDefaultLocalImage import LsbootDefaultLocalImage
from ucscsdk.mometa.lsboot.LsbootEFIShell import LsbootEFIShell
from ucscsdk.mometa.lsboot.LsbootEmbeddedLocalDiskImage import LsbootEmbeddedLocalDiskImage
from ucscsdk.mometa.lsboot.LsbootEmbeddedLocalDiskImagePath import LsbootEmbeddedLocalDiskImagePath
from ucscsdk.mometa.lsboot.LsbootEmbeddedLocalLunImage import LsbootEmbeddedLocalLunImage
from ucscsdk.mometa.lsboot.LsbootIScsi import LsbootIScsi
from ucscsdk.mometa.lsboot.LsbootIScsiImagePath import LsbootIScsiImagePath
from ucscsdk.mometa.lsboot.LsbootLan import LsbootLan
from ucscsdk.mometa.lsboot.LsbootLanImagePath import LsbootLanImagePath
from ucscsdk.mometa.lsboot.LsbootLocalDiskImage import LsbootLocalDiskImage
from ucscsdk.mometa.lsboot.LsbootLocalDiskImagePath import LsbootLocalDiskImagePath
from ucscsdk.mometa.lsboot.LsbootLocalHddImage import LsbootLocalHddImage
from ucscsdk.mometa.lsboot.LsbootLocalLunImagePath import LsbootLocalLunImagePath
from ucscsdk.mometa.lsboot.LsbootLocalStorage import LsbootLocalStorage
from ucscsdk.mometa.lsboot.LsbootNvme import LsbootNvme
from ucscsdk.mometa.lsboot.LsbootPolicy import LsbootPolicy
from ucscsdk.mometa.lsboot.LsbootSan import LsbootSan
from ucscsdk.mometa.lsboot.LsbootSanCatSanImage import LsbootSanCatSanImage
from ucscsdk.mometa.lsboot.LsbootSanCatSanImagePath import LsbootSanCatSanImagePath
from ucscsdk.mometa.lsboot.LsbootStorage import LsbootStorage
from ucscsdk.mometa.lsboot.LsbootUEFIBootParam import LsbootUEFIBootParam
from ucscsdk.mometa.lsboot.LsbootUsbExternalImage import LsbootUsbExternalImage
from ucscsdk.mometa.lsboot.LsbootUsbFlashStorageImage import LsbootUsbFlashStorageImage
from ucscsdk.mometa.lsboot.LsbootUsbInternalImage import LsbootUsbInternalImage
from ucscsdk.mometa.lsboot.LsbootVirtualMedia import LsbootVirtualMedia
from ucscsdk.mometa.lsmaint.LsmaintMaintPolicy import LsmaintMaintPolicy
from ucscsdk.mometa.lstorage.LstorageControllerDef import LstorageControllerDef
from ucscsdk.mometa.lstorage.LstorageControllerModeConfig import LstorageControllerModeConfig
from ucscsdk.mometa.lstorage.LstorageControllerRef import LstorageControllerRef
from ucscsdk.mometa.lstorage.LstorageDasScsiLun import LstorageDasScsiLun
from ucscsdk.mometa.lstorage.LstorageDiskGroupConfigPolicy import LstorageDiskGroupConfigPolicy
from ucscsdk.mometa.lstorage.LstorageDiskGroupQualifier import LstorageDiskGroupQualifier
from ucscsdk.mometa.lstorage.LstorageDiskSlot import LstorageDiskSlot
from ucscsdk.mometa.lstorage.LstorageDiskZoningPolicy import LstorageDiskZoningPolicy
from ucscsdk.mometa.lstorage.LstorageDriveSecurity import LstorageDriveSecurity
from ucscsdk.mometa.lstorage.LstorageLocal import LstorageLocal
from ucscsdk.mometa.lstorage.LstorageLocalDiskConfigRef import LstorageLocalDiskConfigRef
from ucscsdk.mometa.lstorage.LstorageLogin import LstorageLogin
from ucscsdk.mometa.lstorage.LstorageProfile import LstorageProfile
from ucscsdk.mometa.lstorage.LstorageProfileDef import LstorageProfileDef
from ucscsdk.mometa.lstorage.LstorageRemote import LstorageRemote
from ucscsdk.mometa.lstorage.LstorageSecurity import LstorageSecurity
from ucscsdk.mometa.lstorage.LstorageVirtualDriveDef import LstorageVirtualDriveDef
from ucscsdk.mometa.memory.MemoryQual import MemoryQual
from ucscsdk.mometa.mgmt.MgmtNamedKmipCertPolicy import MgmtNamedKmipCertPolicy
from ucscsdk.mometa.power.PowerPolicy import PowerPolicy
from ucscsdk.mometa.processor.ProcessorQual import ProcessorQual
from ucscsdk.mometa.nwctrl.NwctrlDefinition import NwctrlDefinition
from ucscsdk.mometa.sol.SolPolicy import SolPolicy
from ucscsdk.mometa.stats.StatsThresholdClass import StatsThresholdClass
from ucscsdk.mometa.stats.StatsThresholdPolicy import StatsThresholdPolicy
from ucscsdk.mometa.stats.StatsThr32Definition import StatsThr32Definition
from ucscsdk.mometa.stats.StatsThr32Value import StatsThr32Value
from ucscsdk.mometa.stats.StatsThr64Definition import StatsThr64Definition
from ucscsdk.mometa.stats.StatsThr64Value import StatsThr64Value
from ucscsdk.mometa.stats.StatsThrFloatDefinition import StatsThrFloatDefinition
from ucscsdk.mometa.stats.StatsThrFloatValue import StatsThrFloatValue
from ucscsdk.mometa.storage.StorageConnectionPolicy import StorageConnectionPolicy
from ucscsdk.mometa.storage.StorageFcTargetEp import StorageFcTargetEp
from ucscsdk.mometa.storage.StorageIniGroup import StorageIniGroup
from ucscsdk.mometa.storage.StorageInitiator import StorageInitiator
from ucscsdk.mometa.storage.StorageLocalDiskConfigDef import StorageLocalDiskConfigDef
from ucscsdk.mometa.storage.StorageLocalDiskConfigPolicy import StorageLocalDiskConfigPolicy
from ucscsdk.mometa.storage.StorageQual import StorageQual
from ucscsdk.mometa.storage.StorageVsanRef import StorageVsanRef
from ucscsdk.mometa.vnic.VnicDynamicCon import VnicDynamicCon
from ucscsdk.mometa.vnic.VnicDynamicConPolicy import VnicDynamicConPolicy
from ucscsdk.mometa.vnic.VnicDynamicConPolicyRef import VnicDynamicConPolicyRef
from ucscsdk.mometa.vnic.VnicEther import VnicEther
from ucscsdk.mometa.vnic.VnicEtherIf import VnicEtherIf
from ucscsdk.mometa.vnic.VnicFc import VnicFc
from ucscsdk.mometa.vnic.VnicFcGroupDef import VnicFcGroupDef
from ucscsdk.mometa.vnic.VnicFcIf import VnicFcIf
from ucscsdk.mometa.vnic.VnicFcNode import VnicFcNode
from ucscsdk.mometa.vnic.VnicIScsiInitiatorParams import VnicIScsiInitiatorParams
from ucscsdk.mometa.vnic.VnicIPv4If import VnicIPv4If
from ucscsdk.mometa.vnic.VnicIPv4PooledIscsiAddr import VnicIPv4PooledIscsiAddr
from ucscsdk.mometa.vnic.VnicIScsiAutoTargetIf import VnicIScsiAutoTargetIf
from ucscsdk.mometa.vnic.VnicIScsiBootVnic import VnicIScsiBootVnic
from ucscsdk.mometa.vnic.VnicIScsiLCP import VnicIScsiLCP
from ucscsdk.mometa.vnic.VnicIScsiStaticTargetIf import VnicIScsiStaticTargetIf
from ucscsdk.mometa.vnic.VnicIScsiTargetParams import VnicIScsiTargetParams
from ucscsdk.mometa.vnic.VnicLanConnPolicy import VnicLanConnPolicy
from ucscsdk.mometa.vnic.VnicLun import VnicLun
from ucscsdk.mometa.vnic.VnicSanConnPolicy import VnicSanConnPolicy
from ucscsdk.mometa.vnic.VnicUsnicConPolicy import VnicUsnicConPolicy
from ucscsdk.mometa.vnic.VnicUsnicConPolicyRef import VnicUsnicConPolicyRef
from ucscsdk.mometa.vnic.VnicVlan import VnicVlan
from ucscsdk.mometa.vnic.VnicVmqConPolicy import VnicVmqConPolicy
from ucscsdk.mometa.vnic.VnicVmqConPolicyRef import VnicVmqConPolicyRef
from ucscsdk.ucscexception import UcscException

from config.ucs.object import UcsCentralConfigObject
from config.ucs.ucsc.templates import UcsCentralVhbaTemplate, UcsCentralVnicTemplate
from config.ucs.ucsc.pools import UcsCentralMacPool, UcsCentralWwnnPool, UcsCentralWwpnPool
from common import read_json_file


class UcsCentralBiosPolicy(UcsCentralConfigObject):
    _CONFIG_NAME = "BIOS Policy"
    _CONFIG_SECTION_NAME = "bios_policies"
    _UCS_SDK_OBJECT_NAME = "biosVProfile"

    def __init__(self, parent=None, json_content=None, bios_v_profile=None):
        UcsCentralConfigObject.__init__(self, parent=parent, ucs_sdk_object=bios_v_profile)

        bios_table = read_json_file(file_path="config/ucs/ucsc/bios_table.json", logger=self)
        if not bios_table:
            self.logger(level="error", message="BIOS Table not imported.")

        self.name = None
        self.descr = None
        self.reboot_on_bios_settings_change = None

        # Set all the bios options
        if bios_table:
            for attr in bios_table:
                setattr(self, attr, None)

        if self._config.load_from == "live":

            if bios_v_profile is not None:
                self.name = bios_v_profile.name
                self.reboot_on_bios_settings_change = bios_v_profile.reboot_on_update
                self.descr = bios_v_profile.descr

                if "biosTokenParam" in self._parent._config.sdk_objects and "biosTokenSettings" in \
                        self._parent._config.sdk_objects:

                    bios_token_param_list = [bios_token_param for bios_token_param in
                                             self._config.sdk_objects["biosTokenParam"]
                                             if self._parent._dn + "/bios-prof-" + self.name + "/"
                                             in bios_token_param.dn]
                    bios_token_settings_list = [bios_token_setting for bios_token_setting in
                                                self._config.sdk_objects["biosTokenSettings"]
                                                if self._parent._dn + "/bios-prof-" + self.name + "/"
                                                in bios_token_setting.dn]

                    for bios_token_param in bios_token_param_list:
                        if self._parent._dn + "/bios-prof-" + self.name + "/" in bios_token_param.dn:
                            bios_token_settings_children_list = [child for child in bios_token_settings_list
                                                                 if bios_token_param.dn + "/" in child.dn]
                            bios_token_value = None
                            bios_token_name = None
                            # We first try to determine the bios_token_name as defined in our BIOS Table
                            for bios_table_key, bios_table_values in bios_table.items():
                                if bios_table_values["target_name"] == bios_token_param.target_token_name:
                                    bios_token_name = bios_table_key
                                    # Since we have found the right BIOS Token name, we exit the for loop
                                    break
                            if bios_token_name:
                                for bios_token_settings_child in bios_token_settings_children_list:
                                    if bios_token_settings_child.is_assigned == "yes":
                                        bios_token_value = bios_token_settings_child.settings_mo_rn
                                        if bios_token_value in ["Integer", "Float", "Hex"]:
                                            # Handle new BIOS Token values introduced in UCSM 4.1
                                            bios_token_value = bios_token_settings_child.bios_ret_setting_name
                                        setattr(self, bios_token_name, bios_token_value)
                                        # Since we have found the right BIOS Token value, we exit the for loop
                                        break
                            else:
                                self.logger(level="warning",
                                            message=f"BIOS Param name '{bios_token_param.param_name}' not found"
                                                    f" in BIOS Table for {self._CONFIG_NAME} '{self.name}'")
                            if bios_token_name and not bios_token_value:
                                setattr(self, bios_token_name, "platform-default")

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):

        bios_table = read_json_file(file_path="config/ucs/ucsc/bios_table.json", logger=self)
        if not bios_table:
            self.logger(level="error", message="BIOS Table not imported.")

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

        # Using the token method
        mo_bios_v_profile = BiosVProfile(parent_mo_or_dn=parent_mo, name=self.name,
                                         reboot_on_update=self.reboot_on_bios_settings_change, descr=self.descr)

        # We need to commit the BIOS Profile beforehand because some BIOS Parameters can't be set if the
        # BIOS Profile doesn't exist yet, even if the commit also contains the BIOS Profile creation
        self._handle.add_mo(mo=mo_bios_v_profile, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False

        self.logger(message="Pushing BIOS Policy " + self.name + " tokens - It may take a while.")
        for option in bios_table:
            setting_value = str(getattr(self, option))
            if setting_value in ['platform-default', "Platform Default"]:
                try:
                    children = self._handle.query_children(in_dn=mo_bios_v_profile.dn + "/tokn-featr-" +
                                                           bios_table[option]["feature_group"] +
                                                           "/tokn-param-" + bios_table[option]["target_name"])
                except (UcscException, ConnectionRefusedError, urllib.error.URLError) as err:
                    self.logger(level="error",
                                message="Error while trying to fetch info for BIOS parameter " + option +
                                        " in BIOS Profile " + str(self.name) + ": " + str(err))
                    continue

                for mo_bios_token_settings in children:
                    mo_bios_token_settings.is_assigned = "no"
                    self._handle.add_mo(mo=mo_bios_token_settings, modify_present=True)
                # Go to the next option
                continue
            elif setting_value in ["Enabled", "Enable", "enabled", "enable"]:
                setting_value = "Enabled"
            elif setting_value in ["Disabled", "Disable", "disabled", "disable"]:
                setting_value = "Disabled"
            elif setting_value in [None, "None"]:
                continue
            else:
                lower_case_values = bios_table[option]["legacy_values"]
                value_type = bios_table[option]["type"]
                values = bios_table[option]["values"]

                if setting_value not in values:
                    if setting_value in lower_case_values:
                        # This means that the setting value is written with the old SDK setting values type
                        # We need to find the value used in the new SDK, one in the list named "values"
                        found = False
                        for value in values:
                            for lower_case_value in lower_case_values:
                                if setting_value == lower_case_value and not found:
                                    if value.lower().replace("-", "").replace("  ", "").replace(" ", "") == \
                                            lower_case_value.replace("-", "").replace("  ", "").replace(" ", ""):
                                        setting_value = value
                                        found = True
                        if not found:
                            self.logger(level="error", message="BIOS Value " + setting_value +
                                        " for BIOS parameter " + option + " not expected")
                            continue
                    elif value_type in ["float", "hex", "integer"]:
                        mo_bios_token_settings = BiosTokenSettings(
                            parent_mo_or_dn=mo_bios_v_profile.dn + "/tokn-featr-" + bios_table[option][
                                "feature_group"] + "/tokn-param-" + bios_table[option]["target_name"],
                            settings_mo_rn=value_type.title(), bios_ret_setting_name=setting_value,
                            is_assigned="yes")
                        self._handle.add_mo(mo=mo_bios_token_settings, modify_present=True)
                        continue
                    else:
                        self.logger(level="error", message="BIOS Value " + setting_value +
                                    " for BIOS parameter " + option + " not expected")
                        continue

            mo_bios_token_settings = BiosTokenSettings(
                parent_mo_or_dn=mo_bios_v_profile.dn + "/tokn-featr-" + bios_table[option]["feature_group"] +
                "/tokn-param-" + bios_table[option]["target_name"], settings_mo_rn=setting_value, is_assigned="yes")
            self._handle.add_mo(mo=mo_bios_token_settings, modify_present=True)

        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True


class UcsCentralBootPolicy(UcsCentralConfigObject):
    _CONFIG_NAME = "Boot Policy"
    _CONFIG_SECTION_NAME = "boot_policies"
    _UCS_SDK_OBJECT_NAME = "lsbootPolicy"
    _UCS_SDK_SPECIFIC_OBJECT_NAME = "lsbootDef"

    def __init__(self, parent=None, json_content=None, lsboot_policy=None):
        UcsCentralConfigObject.__init__(self, parent=parent, ucs_sdk_object=lsboot_policy)
        self.descr = None
        self.name = None
        self.reboot_on_boot_order_change = None
        self.boot_mode = None
        self.boot_security = None
        self.enforce_vnic_name = None
        self.boot_order = []

        # Below is a list of all the device types :
        # cd-dvd, remote_cd-dvd, local_cd-dvd, floppy, local_floppy, remote_floppy, remote_virtual_drive,
        # cimc_mounted_cd-dvd, cimc_mounted_hdd, lan, local_disk, local_lun, local_jbod, sd_card, internal_usb,
        # external_usb, embedded_local_lun, embedded_local_disk, san, efi_shell, iscsi, nvme

        if self._config.load_from == "live":
            if lsboot_policy is not None:
                self.name = lsboot_policy.name
                self.reboot_on_boot_order_change = lsboot_policy.reboot_on_update
                self.descr = lsboot_policy.descr
                self.boot_mode = lsboot_policy.boot_mode
                self.enforce_vnic_name = lsboot_policy.enforce_vnic_name

                # Ignoring invalid boot mode values (e.g. "0") for some old UCS Central boot policies instances
                if self.boot_mode not in ["legacy", "uefi"]:
                    self.boot_mode = None

                if self._parent._dn:
                    if self._parent.__class__.__name__ == "UcsCentralServiceProfile":
                        # We are in presence of a Specific Boot Policy under a Service Profile object
                        boot_policy_dn = self._parent._dn + "/boot-policy/"
                        self.name = None
                    else:
                        # We are in presence of a regular Boot Policy under an Org object
                        boot_policy_dn = self._parent._dn + "/boot-policy-" + self.name + "/"

                    if "lsbootBootSecurity" in self._parent._config.sdk_objects:
                        for boot_security in self._config.sdk_objects["lsbootBootSecurity"]:
                            if boot_policy_dn in boot_security.dn:
                                self.boot_security = boot_security.secure_boot
                                break

                    if "lsbootVirtualMedia" in self._parent._config.sdk_objects:
                        for boot_media in self._config.sdk_objects["lsbootVirtualMedia"]:
                            if boot_policy_dn in boot_media.dn:
                                device = {}
                                device.update({"order": boot_media.order})
                                if boot_media.access == "read-only":
                                    device.update({"device_type": "cd-dvd"})
                                if boot_media.access == "read-only-remote":
                                    device.update({"device_type": "remote_cd-dvd"})
                                if boot_media.access == "read-only-local":
                                    device.update({"device_type": "local_cd-dvd"})
                                if boot_media.access == "read-write":
                                    device.update({"device_type": "floppy"})
                                if boot_media.access == "read-write-local":
                                    device.update({"device_type": "local_floppy"})
                                if boot_media.access == "read-write-remote":
                                    device.update({"device_type": "remote_floppy"})
                                if boot_media.access == "read-write-drive":
                                    device.update({"device_type": "remote_virtual_drive"})
                                if boot_media.access == "read-only-remote-cimc":
                                    device.update({"device_type": "cimc_mounted_cd-dvd"})
                                if boot_media.access == "read-write-remote-cimc":
                                    device.update({"device_type": "cimc_mounted_hdd"})

                                if device:
                                    self.boot_order.append(device)

                    if "lsbootNvme" in self._parent._config.sdk_objects:
                        for boot_nvme in self._config.sdk_objects["lsbootNvme"]:
                            if boot_policy_dn + "storage/local-storage/" in boot_nvme.dn:
                                device = {}
                                device.update({"order": boot_nvme.order})
                                device.update({"device_type": "nvme"})
                                self.boot_order.append(device)

                    if "lsbootLan" in self._parent._config.sdk_objects:
                        for boot_media in self._config.sdk_objects["lsbootLan"]:
                            if boot_policy_dn in boot_media.dn:
                                device = {}
                                device.update({"device_type": "lan"})
                                device.update({"order": boot_media.order})
                                device.update({"vnics": None})
                                if "lsbootLanImagePath" in self._parent._config.sdk_objects:
                                    device["vnics"] = []
                                    for vnic in self._config.sdk_objects["lsbootLanImagePath"]:
                                        if boot_policy_dn in vnic.dn:
                                            image = {}
                                            image.update({"type": vnic.type})
                                            image.update({"name": vnic.vnic_name})
                                            image.update({"ip_address_type": vnic.ip_addr_type})

                                            device["vnics"].append(image)
                                if device:
                                    self.boot_order.append(device)

                    if "lsbootIScsi" in self._parent._config.sdk_objects:
                        for boot_iscsi in self._config.sdk_objects["lsbootIScsi"]:
                            if boot_policy_dn in boot_iscsi.dn:
                                device = {}
                                device.update({"order": boot_iscsi.order})
                                device.update({"device_type": "iscsi"})
                                if "lsbootIScsiImagePath" in self._parent._config.sdk_objects:
                                    device["iscsi_vnics"] = []
                                    for boot_iscsi_img in self._config.sdk_objects["lsbootIScsiImagePath"]:
                                        if boot_policy_dn in boot_iscsi_img.dn:
                                            image = {}
                                            image.update({"name": boot_iscsi_img.i_scsi_vnic_name})
                                            image.update({"type": boot_iscsi_img.type})
                                            image.update({"boot_loader_name": None})
                                            image.update({"boot_loader_path": None})
                                            image.update({"boot_loader_description": None})
                                            if "lsbootUEFIBootParam" in self._parent._config.sdk_objects:
                                                for boot_iscsi_img_boot_param in \
                                                        self._config.sdk_objects["lsbootUEFIBootParam"]:
                                                    if boot_policy_dn + "iscsi/path-" + boot_iscsi_img.type + "/" \
                                                            in boot_iscsi_img_boot_param.dn:
                                                        image.update({"boot_loader_name":
                                                                      boot_iscsi_img_boot_param.boot_loader_name})
                                                        image.update({"boot_loader_path":
                                                                      boot_iscsi_img_boot_param.boot_loader_path})
                                                        image.update({"boot_loader_description":
                                                                      boot_iscsi_img_boot_param.boot_description})
                                            if "vnicIScsiTargetParams" in self._parent._config.sdk_objects:
                                                for boot_iscsi_img_target_param in \
                                                        self._config.sdk_objects["vnicIScsiTargetParams"]:
                                                    if boot_policy_dn + "iscsi/path-" + boot_iscsi_img.type + "/" \
                                                            in boot_iscsi_img_target_param.dn:
                                                        iscsi_target_params = []
                                                        if "vnicIScsiAutoTargetIf" in self._parent._config.sdk_objects:
                                                            for mo_if_auto in self._config.sdk_objects["vnicIScsiAutoTargetIf"]:
                                                                if boot_iscsi_img_target_param.dn in mo_if_auto.dn:
                                                                    target_param = {}
                                                                    target_param["iscsi_target_interface"] = "Auto"
                                                                    target_param.update(
                                                                        {"dhcp_vendor_id": mo_if_auto.dhcp_vendor_id})
                                                                    iscsi_target_params.append(target_param)
                                                        if "vnicIScsiStaticTargetIf" in self._parent._config.sdk_objects:
                                                            target_param = {}
                                                            target_param["iscsi_target_interface"] = "Static"
                                                            iscsi_targets = []
                                                            for mo_if in self._config.sdk_objects["vnicIScsiStaticTargetIf"]:
                                                                if boot_iscsi_img_target_param.dn in mo_if.dn:
                                                                    iscsi_static_targets = {}
                                                                    iscsi_static_targets.update({"name": mo_if.name})
                                                                    iscsi_static_targets.update({"port": mo_if.port})
                                                                    iscsi_static_targets.update(
                                                                        {"authentication_profile": mo_if.auth_profile_name})
                                                                    iscsi_static_targets.update(
                                                                        {"ip_address": mo_if.ip_address})
                                                                    iscsi_static_targets.update(
                                                                        {"priority": mo_if.priority})
                                                                    if "vnicLun" in self._parent._config.sdk_objects:
                                                                        for mo_lun in self._config.sdk_objects["vnicLun"]:
                                                                            if mo_if.dn in mo_lun.dn:
                                                                                iscsi_static_targets.update(
                                                                                    {"lun_id": mo_lun.id})
                                                                    # Fetching the operational state of the referenced policies
                                                                    operational_state = {}
                                                                    operational_state.update(
                                                                        self.get_operational_state(
                                                                            policy_dn=mo_if.oper_auth_profile_name,
                                                                            separator="/iscsi-auth-profile-",
                                                                            policy_name="authentication_profile"
                                                                        )
                                                                    )
                                                                    iscsi_static_targets.update({"operational_state":
                                                                                                 operational_state})
                                                                    iscsi_targets.append(iscsi_static_targets)
                                                            if len(iscsi_targets) > 0:
                                                                target_param.update(
                                                                    {"iscsi_static_targets": iscsi_targets})
                                                                iscsi_target_params.append(target_param)
                                                        if len(iscsi_target_params) > 0:
                                                            image.update(
                                                                {"iscsi_target_parameters": iscsi_target_params})
                                            device["iscsi_vnics"].append(image)
                                self.boot_order.append(device)

                    if "lsbootEFIShell" in self._parent._config.sdk_objects:
                        for boot_efi in self._config.sdk_objects["lsbootEFIShell"]:
                            if boot_policy_dn in boot_efi.dn:
                                device = {}
                                device.update({"order": boot_efi.order})
                                device.update({"device_type": "efi_shell"})
                                self.boot_order.append(device)

                    if "lsbootDefaultLocalImage" in self._parent._config.sdk_objects:
                        for image in self._config.sdk_objects["lsbootDefaultLocalImage"]:
                            if boot_policy_dn + "storage/local-storage/local-any" in image.dn:
                                device = {}
                                device.update({"order": image.order})
                                device.update({"device_type": "local_disk"})
                                self.boot_order.append(device)

                    if "lsbootLocalHddImage" in self._parent._config.sdk_objects:
                        for image in self._config.sdk_objects["lsbootLocalHddImage"]:
                            if boot_policy_dn + "storage/local-storage/local-hdd" in image.dn:
                                device = {}
                                device.update({"order": image.order})
                                device.update({"device_type": "local_lun"})
                                device.update({"local_luns": None})
                                if "lsbootLocalLunImagePath" in self._parent._config.sdk_objects:
                                    device["local_luns"] = []
                                    for image_path in self._config.sdk_objects["lsbootLocalLunImagePath"]:
                                        if boot_policy_dn + "storage/local-storage/local-hdd/lunimgpath-" in \
                                                image_path.dn:
                                            lun = {}
                                            lun.update({"type": image_path.type})
                                            lun.update({"name": image_path.lun_name})
                                            lun.update({"boot_loader_name": None})
                                            lun.update({"boot_loader_path": None})
                                            lun.update({"boot_loader_description": None})
                                            if "lsbootUEFIBootParam" in self._parent._config.sdk_objects:
                                                for boot_disk_img_boot_param \
                                                        in self._config.sdk_objects["lsbootUEFIBootParam"]:
                                                    if boot_policy_dn + "storage/local-storage/local-hdd/lunimgpath-" \
                                                            + image_path.type + "/" in boot_disk_img_boot_param.dn:
                                                        lun.update({"boot_loader_name":
                                                                    boot_disk_img_boot_param.boot_loader_name})
                                                        lun.update({"boot_loader_path":
                                                                    boot_disk_img_boot_param.boot_loader_path})
                                                        lun.update({"boot_loader_description":
                                                                    boot_disk_img_boot_param.boot_description})
                                            device["local_luns"].append(lun)
                                self.boot_order.append(device)

                    if "lsbootLocalDiskImage" in self._parent._config.sdk_objects:
                        for image in self._config.sdk_objects["lsbootLocalDiskImage"]:
                            if boot_policy_dn + "storage/local-storage/local-jbod" in image.dn:
                                device = {}
                                device.update({"order": image.order})
                                device.update({"device_type": "local_jbod"})
                                device.update({"local_jbods": None})
                                if "lsbootLocalDiskImagePath" in self._parent._config.sdk_objects:
                                    device["local_jbods"] = []
                                    for image_path in self._config.sdk_objects["lsbootLocalDiskImagePath"]:
                                        if boot_policy_dn + "storage/local-storage/local-jbod/diskimgpath-" \
                                                in image_path.dn:
                                            jbod = {}
                                            jbod.update({"slot_number": image_path.slot_number})
                                            device["local_jbods"].append(jbod)
                                self.boot_order.append(device)

                    if "lsbootUsbFlashStorageImage" in self._parent._config.sdk_objects:
                        for image in self._config.sdk_objects["lsbootUsbFlashStorageImage"]:
                            if boot_policy_dn + "storage/local-storage/sd" in image.dn:
                                device = {}
                                device.update({"order": image.order})
                                device.update({"device_type": "sd_card"})
                                self.boot_order.append(device)

                    if "lsbootUsbInternalImage" in self._parent._config.sdk_objects:
                        for image in self._config.sdk_objects["lsbootUsbInternalImage"]:
                            if boot_policy_dn + "storage/local-storage/usb-intern" in image.dn:
                                device = {}
                                device.update({"order": image.order})
                                device.update({"device_type": "internal_usb"})
                                self.boot_order.append(device)

                    if "lsbootUsbExternalImage" in self._parent._config.sdk_objects:
                        for image in self._config.sdk_objects["lsbootUsbExternalImage"]:
                            if boot_policy_dn + "storage/local-storage/usb-extern" in image.dn:
                                device = {}
                                device.update({"order": image.order})
                                device.update({"device_type": "external_usb"})
                                self.boot_order.append(device)

                    if "lsbootEmbeddedLocalLunImage" in self._parent._config.sdk_objects:
                        for image in self._config.sdk_objects["lsbootEmbeddedLocalLunImage"]:
                            if boot_policy_dn + "storage/local-storage/embedded-local-lun" in image.dn:
                                device = {}
                                device.update({"order": image.order})
                                device.update({"device_type": "embedded_local_lun"})
                                device.update({"embedded_local_luns": None})
                                if "lsbootUEFIBootParam" in self._parent._config.sdk_objects:
                                    device["embedded_local_luns"] = []
                                    for boot_disk_img_boot_param in self._config.sdk_objects["lsbootUEFIBootParam"]:
                                        if boot_policy_dn + "storage/local-storage/embedded-local-lun/" \
                                                in boot_disk_img_boot_param.dn:
                                            lun = {}
                                            lun.update({"boot_loader_name": boot_disk_img_boot_param.boot_loader_name})
                                            lun.update({"boot_loader_path": boot_disk_img_boot_param.boot_loader_path})
                                            lun.update({"boot_loader_description":
                                                        boot_disk_img_boot_param.boot_description})
                                            device["embedded_local_luns"].append(lun)
                                self.boot_order.append(device)

                    if "lsbootEmbeddedLocalDiskImage" in self._parent._config.sdk_objects:
                        for image in self._config.sdk_objects["lsbootEmbeddedLocalDiskImage"]:
                            if boot_policy_dn + "storage/local-storage/embedded-local-jbod" in image.dn:
                                device = {}
                                device.update({"order": image.order})
                                device.update({"device_type": "embedded_local_disk"})
                                device.update({"embedded_local_disks": None})
                                if "lsbootEmbeddedLocalDiskImagePath" in self._parent._config.sdk_objects:
                                    device["embedded_local_disks"] = []
                                    for image_path in self._config.sdk_objects["lsbootEmbeddedLocalDiskImagePath"]:
                                        if boot_policy_dn + "storage/local-storage/embedded-local-jbod/diskimgpath-" \
                                                in image_path.dn:
                                            disk = {}
                                            disk.update({"type": image_path.type})
                                            disk.update({"slot_number": image_path.slot_number})
                                            disk.update({"boot_loader_name": None})
                                            disk.update({"boot_loader_path": None})
                                            disk.update({"boot_loader_description": None})
                                            if "lsbootUEFIBootParam" in self._parent._config.sdk_objects:
                                                for boot_disk_img_boot_param \
                                                        in self._config.sdk_objects["lsbootUEFIBootParam"]:
                                                    if boot_policy_dn + \
                                                            "storage/local-storage/embedded-local-jbod/diskimgpath-" + \
                                                            image_path.type + "/" in boot_disk_img_boot_param.dn:
                                                        disk.update({"boot_loader_name":
                                                                     boot_disk_img_boot_param.boot_loader_name})
                                                        disk.update({"boot_loader_path":
                                                                     boot_disk_img_boot_param.boot_loader_path})
                                                        disk.update({"boot_loader_description":
                                                                     boot_disk_img_boot_param.boot_description})
                                            device["embedded_local_disks"].append(disk)
                                self.boot_order.append(device)

                    if "lsbootSan" in self._parent._config.sdk_objects:
                        for boot_media in self._config.sdk_objects["lsbootSan"]:
                            if boot_policy_dn + "san" in boot_media.dn:
                                device = {}
                                device.update({"device_type": "san"})
                                device.update({"order": boot_media.order})
                                device.update({"vhbas": None})
                                if "lsbootSanCatSanImage" in self._parent._config.sdk_objects:
                                    device["vhbas"] = []
                                    for vhba in self._config.sdk_objects["lsbootSanCatSanImage"]:
                                        if boot_policy_dn + "san/" in vhba.dn:
                                            image = {}
                                            image.update({"type": vhba.type})
                                            image.update({"name": vhba.vnic_name})
                                            if "lsbootSanCatSanImagePath" in self._parent._config.sdk_objects:
                                                image["targets"] = []
                                                for target in self._config.sdk_objects["lsbootSanCatSanImagePath"]:
                                                    if boot_policy_dn + "san/sanimg-" + vhba.type in target.dn:
                                                        image_path = {}
                                                        image_path.update({"type": target.type})
                                                        image_path.update({"lun": target.lun})
                                                        image_path.update({"wwpn": target.wwn})
                                                        image_path.update({"boot_loader_name": None})
                                                        image_path.update({"boot_loader_path": None})
                                                        image_path.update({"boot_loader_description": None})
                                                        if "lsbootUEFIBootParam" in self._parent._config.sdk_objects:
                                                            for boot_san_img_boot_param in \
                                                                    self._config.sdk_objects["lsbootUEFIBootParam"]:
                                                                if boot_policy_dn + "san/sanimg-" + vhba.type + \
                                                                        "/sanimgpath-" + target.type in \
                                                                        boot_san_img_boot_param.dn:
                                                                    image_path.update({
                                                                        "boot_loader_name":
                                                                            boot_san_img_boot_param.boot_loader_name})
                                                                    image_path.update({
                                                                        "boot_loader_path":
                                                                            boot_san_img_boot_param.boot_loader_path})
                                                                    image_path.update({
                                                                        "boot_loader_description":
                                                                            boot_san_img_boot_param.boot_description})
                                                        image["targets"].append(image_path)
                                            device["vhbas"].append(image)
                                if device:
                                    self.boot_order.append(device)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

                # We need to set all values that are not present in the config file to None
                for element in self.boot_order:
                    for value in ['device_type', 'embedded_local_disks', 'iscsi_vnics', 'local_luns', 'name', 'order',
                                  'vhbas', 'vnics', 'local_jbods', 'embedded_local_luns']:
                        if value not in element:
                            element[value] = None

                    if element["vhbas"]:
                        for vhba in element["vhbas"]:
                            for subvalue in ["name", "targets", "type"]:
                                if subvalue not in vhba:
                                    vhba[subvalue] = None
                            if vhba["targets"]:
                                for target in vhba["targets"]:
                                    for subsubvalue in ["lun", "wwpn", "type", "boot_loader_name", "boot_loader_path",
                                                        "boot_loader_description"]:
                                        if subsubvalue not in target:
                                            target[subsubvalue] = None
                    if element["embedded_local_disks"]:
                        for disk in element["embedded_local_disks"]:
                            for subvalue in ["slot_number", "type", "boot_loader_name", "boot_loader_path",
                                             "boot_loader_description"]:
                                if subvalue not in disk:
                                    disk[subvalue] = None
                    if element["local_luns"]:
                        for lun in element["local_luns"]:
                            for subvalue in ["name", "type", "boot_loader_name", "boot_loader_path",
                                             "boot_loader_description"]:
                                if subvalue not in lun:
                                    lun[subvalue] = None
                    if element["iscsi_vnics"]:
                        for vnic in element["iscsi_vnics"]:
                            for subvalue in ["name", "type", "boot_loader_name", "boot_loader_path",
                                             "boot_loader_description", "iscsi_target_parameters"]:
                                if subvalue not in vnic:
                                    vnic[subvalue] = None
                            if vnic["iscsi_target_parameters"]:
                                for static_target_parameter in vnic["iscsi_target_parameters"]:
                                    for subvalue in [
                                            "dhcp_vendor_id", "iscsi_target_interface", "iscsi_static_targets"]:
                                        if subvalue not in static_target_parameter:
                                            static_target_parameter[subvalue] = None
                                    if static_target_parameter["iscsi_static_targets"]:
                                        for iscsi_static_targets in static_target_parameter["iscsi_static_targets"]:
                                            for subvalue in [
                                                "authentication_profile", "ip_address", "lun_id", "name", "port",
                                                    "priority"]:
                                                if subvalue not in iscsi_static_targets:
                                                    iscsi_static_targets[subvalue] = None

                    if element["vnics"]:
                        for vnic in element["vnics"]:
                            for subvalue in ["name", "type", "ip_address_type"]:
                                if subvalue not in vnic:
                                    vnic[subvalue] = None

        self.clean_object()

    def push_object(self, commit=True):
        detail = str(self.name)
        if self._parent.__class__.__name__ == "UcsCentralServiceProfile":
            # We are in presence of a Specific Boot Policy under a Service Profile object
            detail = "Service Profile " + str(self._parent.name)
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + detail)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + detail +
                                ", waiting for a commit")

        if hasattr(self._parent, '_dn'):
            parent_mo = self._parent._dn
        else:
            self.logger(level="error",
                        message="Impossible to find the parent dn of " + self._CONFIG_NAME + " : " + str(self.name))
            return False

        if self._parent.__class__.__name__ == "UcsCentralServiceProfile":
            # We are in presence of a Specific Boot Policy under a Service Profile object
            mo_ls_boot_policy = LsbootDef(parent_mo_or_dn=parent_mo, descr=self.descr,
                                          reboot_on_update=self.reboot_on_boot_order_change,
                                          boot_mode=self.boot_mode, enforce_vnic_name=self.enforce_vnic_name)
        else:
            # We are in presence of a regular Boot Policy under an Org object
            mo_ls_boot_policy = LsbootPolicy(parent_mo_or_dn=parent_mo, descr=self.descr,
                                             reboot_on_update=self.reboot_on_boot_order_change, name=self.name,
                                             boot_mode=self.boot_mode, enforce_vnic_name=self.enforce_vnic_name)
        LsbootBootSecurity(parent_mo_or_dn=mo_ls_boot_policy, secure_boot=self.boot_security)
        self._handle.add_mo(mo=mo_ls_boot_policy, modify_present=True)
        if commit:
            detail = self.name
            if self._parent.__class__.__name__ == "UcsCentralServiceProfile":
                # We are in presence of a Specific Boot Policy under a Service Profile object
                detail = "Service Profile " + self._parent.name
            if self.commit(detail=detail) != True:
                return False

        # Repeat of mo_ls_boot_policy - A bug occurred if the mo is committed and not repeated
        if self._parent.__class__.__name__ == "UcsCentralServiceProfile":
            # We are in presence of a Specific Boot Policy under a Service Profile object
            mo_ls_boot_policy = LsbootDef(parent_mo_or_dn=parent_mo)
        else:
            # We are in presence of a regular Boot Policy under an Org object
            mo_ls_boot_policy = LsbootPolicy(parent_mo_or_dn=parent_mo, name=self.name)
        mo_boot_local_storage = None
        for device in self.boot_order:
            if device['device_type'] == "cd-dvd":
                LsbootVirtualMedia(parent_mo_or_dn=mo_ls_boot_policy, access="read-only", order=device['order'])
            elif device['device_type'] == "remote_cd-dvd":
                LsbootVirtualMedia(parent_mo_or_dn=mo_ls_boot_policy, access="read-only-remote", order=device['order'])
            elif device['device_type'] == "local_cd-dvd":
                LsbootVirtualMedia(parent_mo_or_dn=mo_ls_boot_policy, access="read-only-local", order=device['order'])
            elif device['device_type'] == "lan":
                mo_boot_lan = LsbootLan(parent_mo_or_dn=mo_ls_boot_policy, prot="pxe", order=device['order'])
                if device["vnics"]:
                    for vnic in device["vnics"]:
                        LsbootLanImagePath(parent_mo_or_dn=mo_boot_lan, type=vnic["type"], vnic_name=vnic["name"],
                                           ip_addr_type=vnic["ip_address_type"])
            elif device['device_type'] in ['local_disk', 'local_lun', 'local_jbod', 'sd_card', 'internal_usb',
                                           'external_usb', 'embedded_local_lun', 'embedded_local_disk', "nvme"]:
                # Check if mo_boot_storage and mo_boot_local_storage objects are already present
                if not mo_boot_local_storage:
                    mo_boot_storage = LsbootStorage(parent_mo_or_dn=mo_ls_boot_policy)
                    mo_boot_local_storage = LsbootLocalStorage(parent_mo_or_dn=mo_boot_storage)
                if device['device_type'] == 'local_disk':
                    LsbootDefaultLocalImage(parent_mo_or_dn=mo_boot_local_storage, order=device['order'])
                elif device['device_type'] == 'local_lun':
                    mo_hdd_image = LsbootLocalHddImage(parent_mo_or_dn=mo_boot_local_storage, order=device['order'])
                    if device["local_luns"]:
                        for lun in device["local_luns"]:
                            mo_local_lun = LsbootLocalLunImagePath(parent_mo_or_dn=mo_hdd_image, type=lun['type'],
                                                                   lun_name=lun['name'])
                            LsbootUEFIBootParam(parent_mo_or_dn=mo_local_lun,
                                                boot_loader_path=lun["boot_loader_path"],
                                                boot_loader_name=lun["boot_loader_name"],
                                                boot_description=lun["boot_loader_description"])
                elif device['device_type'] == 'local_jbod':
                    mo_disk_image = LsbootLocalDiskImage(
                        parent_mo_or_dn=mo_boot_local_storage, order=device['order'])
                    if device["local_jbods"]:
                        for jbod in device["local_jbods"]:
                            LsbootLocalDiskImagePath(parent_mo_or_dn=mo_disk_image, type="primary",
                                                     slot_number=jbod['slot_number'])
                elif device['device_type'] == 'sd_card':
                    LsbootUsbFlashStorageImage(parent_mo_or_dn=mo_boot_local_storage, order=device['order'])
                elif device['device_type'] == 'internal_usb':
                    LsbootUsbInternalImage(parent_mo_or_dn=mo_boot_local_storage, order=device['order'])
                elif device['device_type'] == 'external_usb':
                    LsbootUsbExternalImage(parent_mo_or_dn=mo_boot_local_storage, order=device['order'])
                elif device['device_type'] == 'embedded_local_lun':
                    mo_embedded_local_lun = LsbootEmbeddedLocalLunImage(parent_mo_or_dn=mo_boot_local_storage,
                                                                        order=device['order'])
                    if device["embedded_local_luns"]:
                        for lun in device["embedded_local_luns"]:
                            LsbootUEFIBootParam(parent_mo_or_dn=mo_embedded_local_lun,
                                                boot_loader_path=lun["boot_loader_path"],
                                                boot_loader_name=lun["boot_loader_name"],
                                                boot_description=lun["boot_loader_description"])
                elif device['device_type'] == 'embedded_local_disk':
                    mo_embedded_local = LsbootEmbeddedLocalDiskImage(parent_mo_or_dn=mo_boot_local_storage,
                                                                     order=device['order'])
                    if device["embedded_local_disks"]:
                        for disk in device["embedded_local_disks"]:
                            mo_emb_disk_img_path = LsbootEmbeddedLocalDiskImagePath(
                                parent_mo_or_dn=mo_embedded_local, type=disk['type'],
                                slot_number=disk['slot_number'])
                            LsbootUEFIBootParam(parent_mo_or_dn=mo_emb_disk_img_path,
                                                boot_loader_path=disk["boot_loader_path"],
                                                boot_loader_name=disk["boot_loader_name"],
                                                boot_description=disk["boot_loader_description"])
                elif device['device_type'] == "nvme":
                    LsbootNvme(parent_mo_or_dn=mo_boot_local_storage, order=device['order'])

            elif device['device_type'] == 'floppy':
                LsbootVirtualMedia(parent_mo_or_dn=mo_ls_boot_policy, access="read-write", order=device['order'])
            elif device['device_type'] == 'local_floppy':
                LsbootVirtualMedia(parent_mo_or_dn=mo_ls_boot_policy, access="read-write-local", order=device['order'])
            elif device['device_type'] == 'remote_floppy':
                LsbootVirtualMedia(parent_mo_or_dn=mo_ls_boot_policy, access="read-write-remote", order=device['order'])
            elif device['device_type'] == 'remote_virtual_drive':
                LsbootVirtualMedia(parent_mo_or_dn=mo_ls_boot_policy, access="read-write-drive", order=device['order'])
            elif device['device_type'] == "cimc_mounted_cd-dvd":
                LsbootVirtualMedia(
                    parent_mo_or_dn=mo_ls_boot_policy, order=device['order'],
                    access="read-only-remote-cimc")
            elif device['device_type'] == "cimc_mounted_hdd":
                LsbootVirtualMedia(
                    parent_mo_or_dn=mo_ls_boot_policy, order=device['order'],
                    access="read-write-remote-cimc")
            elif device['device_type'] == "iscsi":
                mo_boot_iscsi = LsbootIScsi(parent_mo_or_dn=mo_ls_boot_policy, order=device['order'])
                if device["iscsi_vnics"]:
                    for vnic in device["iscsi_vnics"]:
                        mo_boot_iscsi_image = LsbootIScsiImagePath(parent_mo_or_dn=mo_boot_iscsi,
                                                                   type=vnic["type"],
                                                                   i_scsi_vnic_name=vnic["name"])
                        if vnic["boot_loader_path"] or vnic["boot_loader_name"] or vnic["boot_loader_description"]:
                            LsbootUEFIBootParam(parent_mo_or_dn=mo_boot_iscsi_image,
                                                boot_loader_path=vnic["boot_loader_path"],
                                                boot_loader_name=vnic["boot_loader_name"],
                                                boot_description=vnic["boot_loader_description"])
                        if vnic["iscsi_target_parameters"]:
                            mo_vnic_iscsi_target_params = VnicIScsiTargetParams(parent_mo_or_dn=mo_boot_iscsi_image)
                            for static_target_parameter in vnic["iscsi_target_parameters"]:
                                if static_target_parameter["iscsi_target_interface"] == "Static":
                                    if static_target_parameter.get("iscsi_static_targets"):
                                        for iscsi_static_targets in static_target_parameter["iscsi_static_targets"]:
                                            mo_static_target_if = VnicIScsiStaticTargetIf(
                                                parent_mo_or_dn=mo_vnic_iscsi_target_params,
                                                ip_address=iscsi_static_targets["ip_address"],
                                                name=iscsi_static_targets["name"],
                                                port=iscsi_static_targets["port"],
                                                auth_profile_name=iscsi_static_targets["authentication_profile"],
                                                priority=iscsi_static_targets["priority"])
                                            VnicLun(parent_mo_or_dn=mo_static_target_if,
                                                    id=iscsi_static_targets["lun_id"])
                                elif static_target_parameter["iscsi_target_interface"] == "Auto":
                                    VnicIScsiAutoTargetIf(parent_mo_or_dn=mo_vnic_iscsi_target_params,
                                                          dhcp_vendor_id=static_target_parameter["dhcp_vendor_id"])

            elif device['device_type'] == "efi_shell":
                LsbootEFIShell(parent_mo_or_dn=mo_ls_boot_policy, order=device['order'])
            elif device['device_type'] == "san":
                mo_boot_san = LsbootSan(parent_mo_or_dn=mo_ls_boot_policy, order=device['order'])
                for vhba in device['vhbas']:
                    mo_cat_san_image = LsbootSanCatSanImage(parent_mo_or_dn=mo_boot_san, type=vhba['type'],
                                                            vnic_name=vhba['name'])
                    if vhba['targets']:
                        for target in vhba['targets']:
                            mo_boot_san_path = LsbootSanCatSanImagePath(parent_mo_or_dn=mo_cat_san_image,
                                                                        type=target['type'], lun=target['lun'],
                                                                        wwn=target['wwpn'])
                            if target['boot_loader_path'] or target['boot_loader_name'] or \
                                    target['boot_loader_description']:
                                LsbootUEFIBootParam(parent_mo_or_dn=mo_boot_san_path,
                                                    boot_loader_path=target["boot_loader_path"],
                                                    boot_loader_name=target["boot_loader_name"],
                                                    boot_description=target["boot_loader_description"])

            self._handle.add_mo(mo=mo_ls_boot_policy, modify_present=True)
        if commit:
            detail = str(self.name) + ' devices'
            if self._parent.__class__.__name__ == "UcsCentralServiceProfile":
                # We are in presence of a Specific Boot Policy under a Service Profile object
                detail = "Service Profile " + str(self._parent.name) + ' - devices'
            if self.commit(detail=detail) != True:
                return False
        return True


class UcsCentralChassisFirmwarePackage(UcsCentralConfigObject):
    _CONFIG_NAME = "Chassis Firmware Package"
    _CONFIG_SECTION_NAME = "chassis_firmware_packages"
    _UCS_SDK_OBJECT_NAME = "firmwareChassisPack"

    def __init__(self, parent=None, json_content=None, firmware_chassis_pack=None):
        UcsCentralConfigObject.__init__(self, parent=parent, ucs_sdk_object=firmware_chassis_pack)
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
        # It is the only way to remove "local-disk" value in the excluded content (checked by default)
        if 'local-disk' not in self.excluded_components:
            override_default_exclusion = "yes"
        # Same in UcsCentralHostFirmwarePackage

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


class UcsCentralComputeConnectionPolicy(UcsCentralConfigObject):
    _CONFIG_NAME = "Compute Connection Policy"
    _CONFIG_SECTION_NAME = "compute_connection_policies"
    _UCS_SDK_OBJECT_NAME = "equipmentComputeConnPolicy"

    def __init__(self, parent=None, json_content=None, equipment_compute_conn_policy=None):
        UcsCentralConfigObject.__init__(self, parent=parent, ucs_sdk_object=equipment_compute_conn_policy)
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


class UcsCentralDiskGroupPolicy(UcsCentralConfigObject):
    _CONFIG_NAME = "Disk Group Policy"
    _CONFIG_SECTION_NAME = "disk_group_policies"
    _UCS_SDK_OBJECT_NAME = "lstorageDiskGroupConfigPolicy"

    def __init__(self, parent=None, json_content=None, lstorage_disk_group_config_policy=None):
        UcsCentralConfigObject.__init__(self, parent=parent, ucs_sdk_object=lstorage_disk_group_config_policy)
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
        self.number_of_drives = None
        self.drive_type = None
        self.manual_disk_group_configuration = []
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
                                self.io_policy = lstorage_virtual_drive_def.io_policy
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

                # We need to set all values that are not present in the config file to None
                for element in self.manual_disk_group_configuration:
                    for value in ["slot_number", "role", "span_id"]:
                        if value not in element:
                            element[value] = None

        self.clean_object()

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


class UcsCentralDiskZoningPolicy(UcsCentralConfigObject):
    _CONFIG_NAME = "Disk Zoning Policy"
    _CONFIG_SECTION_NAME = "disk_zoning_policies"
    _UCS_SDK_OBJECT_NAME = "lstorageDiskZoningPolicy"

    def __init__(self, parent=None, json_content=None, lstorage_disk_zoning_policy=None):
        UcsCentralConfigObject.__init__(self, parent=parent, ucs_sdk_object=lstorage_disk_zoning_policy)
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
                                disk.update(
                                    {"drive_path": disk_slot.drive_path.lower() if disk_slot.drive_path else None})
                                disk.update({"disk_slot": disk_slot.id})
                                # disk.update({"disk_slot_range_start": disk_slot.id.split("-")[0]})
                                # disk.update({"disk_slot_range_stop": disk_slot.id.split("-")[1]})
                                if "lstorageControllerRef" in self._parent._config.sdk_objects:
                                    for controller_ref in self._config.sdk_objects["lstorageControllerRef"]:
                                        if self._parent._dn + "/disk-zoning-policy-" + self.name + "/disk-slot-" + \
                                                disk_slot.id + "/" in controller_ref.dn:
                                            disk.update({"controller": controller_ref.controller_id})
                                            disk.update({"server": controller_ref.server_id})
                                            break
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


class UcsCentralDynamicVnicConnectionPolicy(UcsCentralConfigObject):
    _CONFIG_NAME = "Dynamic vNIC Connection Policy"
    _CONFIG_SECTION_NAME = "dynamic_vnic_connection_policies"
    _UCS_SDK_OBJECT_NAME = "vnicDynamicConPolicy"
    _UCS_SDK_SPECIFIC_OBJECT_NAME = "vnicDynamicCon"

    def __init__(self, parent=None, json_content=None, vnic_dynamic_con_policy=None):
        UcsCentralConfigObject.__init__(self, parent=parent, ucs_sdk_object=vnic_dynamic_con_policy)
        self.name = None
        self.descr = None
        self.number_dynamic_vnics = None
        self.adapter_policy = None
        self.protection = None

        if self._config.load_from == "live":
            if vnic_dynamic_con_policy is not None:
                self.name = vnic_dynamic_con_policy.name
                self.descr = vnic_dynamic_con_policy.descr
                self.number_dynamic_vnics = vnic_dynamic_con_policy.dynamic_eth
                self.adapter_policy = vnic_dynamic_con_policy.adaptor_profile_name
                self.protection = vnic_dynamic_con_policy.protection

                if self._parent._dn:
                    if self._parent.__class__.__name__ == "UcsCentralServiceProfile":
                        # We are in presence of a Specific Dynamic vNIC Connection Policy under a Service Profile object
                        self.name = None

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        detail = str(self.name)
        if self._parent.__class__.__name__ == "UcsCentralServiceProfile":
            # We are in presence of a Specific Dynamic vNIC Connection Policy under a Service Profile object
            detail = "Service Profile " + str(self._parent.name)
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + detail)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + detail +
                                ", waiting for a commit")

        if hasattr(self._parent, '_dn'):
            parent_mo = self._parent._dn
        else:
            self.logger(level="error",
                        message="Impossible to find the parent dn of " + self._CONFIG_NAME + " : " + self.name)
            return False

        if self._parent.__class__.__name__ == "UcsCentralServiceProfile":
            # We are in presence of a Specific Dynamic vNIC Connection Policy under a Service Profile object
            mo_vnic_dynamic_con_policy = VnicDynamicCon(
                parent_mo_or_dn=parent_mo, descr=self.descr, dynamic_eth=self.number_dynamic_vnics,
                adaptor_profile_name=self.adapter_policy, protection=self.protection
            )
        else:
            # We are in presence of a regular Dynamic vNIC Connection Policy under an Org object
            mo_vnic_dynamic_con_policy = VnicDynamicConPolicy(
                parent_mo_or_dn=parent_mo, descr=self.descr, name=self.name, dynamic_eth=self.number_dynamic_vnics,
                adaptor_profile_name=self.adapter_policy, protection=self.protection
            )

        self._handle.add_mo(mo=mo_vnic_dynamic_con_policy, modify_present=True)
        if commit:
            detail = str(self.name)
            if self._parent.__class__.__name__ == "UcsCentralServiceProfile":
                # We are in presence of a Specific Dynamic vNIC Connection Policy under a Service Profile object
                detail = "Service Profile " + str(self._parent.name)
            if self.commit(detail=detail) != True:
                return False
        return True


class UcsCentralEthernetAdapterPolicy(UcsCentralConfigObject):
    _CONFIG_NAME = "Ethernet Adapter Policy"
    _CONFIG_SECTION_NAME = "ethernet_adapter_policies"
    _UCS_SDK_OBJECT_NAME = "adaptorHostEthIfProfile"

    def __init__(self, parent=None, json_content=None, adaptor_host_eth_if_profile=None):
        UcsCentralConfigObject.__init__(self, parent=parent, ucs_sdk_object=adaptor_host_eth_if_profile)
        self.descr = None
        self.name = None
        self.pooled = None
        self.transmit_queues = None
        self.transmit_queues_ring_size = None
        self.receive_queues = None
        self.receive_queues_ring_size = None
        self.completion_queues = None
        self.interrupts = None
        self.transmit_checksum_offload = None
        self.receive_checksum_offload = None
        self.tcp_segmentation_offload = None
        self.tcp_large_receive_offload = None
        self.receive_side_scaling = None
        self.accelerated_receive_flow_steering = None
        self.nvgre_offload = None
        self.vxlan_offload = None
        self.geneve_offload = None
        # self.azurestack_host_qos = None
        self.failback_timeout = None
        self.interrupt_mode = None
        self.interrupt_coalescing_type = None
        self.interrupt_timer = None
        self.roce = None
        self.roce_properties = []
        self.advance_filter = None
        self.interrupt_scaling = None
        if self._config.load_from == "live":
            if adaptor_host_eth_if_profile is not None:
                self.name = adaptor_host_eth_if_profile.name
                self.descr = adaptor_host_eth_if_profile.descr
                self.pooled = adaptor_host_eth_if_profile.pooled_resources

                if "adaptorEthWorkQueueProfile" in self._parent._config.sdk_objects:
                    for adapt in self._config.sdk_objects["adaptorEthWorkQueueProfile"]:
                        if self._parent._dn:
                            if self._parent._dn + "/eth-profile-" + self.name + "/" in adapt.dn:
                                self.transmit_queues_ring_size = adapt.ring_size
                                self.transmit_queues = adapt.count
                                break

                if "adaptorEthRecvQueueProfile" in self._parent._config.sdk_objects:
                    for adapt in self._config.sdk_objects["adaptorEthRecvQueueProfile"]:
                        if self._parent._dn:
                            if self._parent._dn + "/eth-profile-" + self.name + "/" in adapt.dn:
                                self.receive_queues_ring_size = adapt.ring_size
                                self.receive_queues = adapt.count
                                break

                if "adaptorEthCompQueueProfile" in self._parent._config.sdk_objects:
                    for adapt in self._config.sdk_objects["adaptorEthCompQueueProfile"]:
                        if self._parent._dn:
                            if self._parent._dn + "/eth-profile-" + self.name + "/" in adapt.dn:
                                self.completion_queues = adapt.count
                                break

                if "adaptorEthOffloadProfile" in self._parent._config.sdk_objects:
                    for adapt in self._config.sdk_objects["adaptorEthOffloadProfile"]:
                        if self._parent._dn:
                            if self._parent._dn + "/eth-profile-" + self.name + "/" in adapt.dn:
                                self.transmit_checksum_offload = adapt.tcp_tx_checksum
                                self.receive_checksum_offload = adapt.tcp_rx_checksum
                                self.tcp_segmentation_offload = adapt.tcp_segment
                                self.tcp_large_receive_offload = adapt.large_receive
                                break

                if "adaptorRssProfile" in self._parent._config.sdk_objects:
                    for adapt in self._config.sdk_objects["adaptorRssProfile"]:
                        if self._parent._dn:
                            if self._parent._dn + "/eth-profile-" + self.name + "/" in adapt.dn:
                                self.receive_side_scaling = adapt.receive_side_scaling
                                break

                if "adaptorEthArfsProfile" in self._parent._config.sdk_objects:
                    for adapt in self._config.sdk_objects["adaptorEthArfsProfile"]:
                        if self._parent._dn:
                            if self._parent._dn + "/eth-profile-" + self.name + "/" in adapt.dn:
                                self.accelerated_receive_flow_steering = adapt.accelarated_rfs
                                break

                if "adaptorEthNVGREProfile" in self._parent._config.sdk_objects:
                    for adapt in self._config.sdk_objects["adaptorEthNVGREProfile"]:
                        if self._parent._dn:
                            if self._parent._dn + "/eth-profile-" + self.name + "/" in adapt.dn:
                                self.nvgre_offload = adapt.admin_state
                                break

                if "adaptorEthVxLANProfile" in self._parent._config.sdk_objects:
                    for adapt in self._config.sdk_objects["adaptorEthVxLANProfile"]:
                        if self._parent._dn:
                            if self._parent._dn + "/eth-profile-" + self.name + "/" in adapt.dn:
                                self.vxlan_offload = adapt.admin_state
                                break

                if "adaptorEthGENEVEProfile" in self._parent._config.sdk_objects:
                    for adapt in self._config.sdk_objects["adaptorEthGENEVEProfile"]:
                        if self._parent._dn:
                            if self._parent._dn + "/eth-profile-" + self.name + "/" in adapt.dn:
                                self.geneve_offload = adapt.offload
                                break

                # if "adaptorAzureQosProfile" in self._parent._config.sdk_objects:
                #     for adapt in self._config.sdk_objects["adaptorAzureQosProfile"]:
                #         if self._parent._dn:
                #             if self._parent._dn + "/eth-profile-" + self.name + "/" in adapt.dn:
                #                 self.azurestack_host_qos = adapt.adp_azure_qos
                #                 break

                if "adaptorEthFailoverProfile" in self._parent._config.sdk_objects:
                    for adapt in self._config.sdk_objects["adaptorEthFailoverProfile"]:
                        if self._parent._dn:
                            if self._parent._dn + "/eth-profile-" + self.name + "/" in adapt.dn:
                                self.failback_timeout = adapt.timeout
                                break

                if "adaptorEthInterruptProfile" in self._parent._config.sdk_objects:
                    for adapt in self._config.sdk_objects["adaptorEthInterruptProfile"]:
                        if self._parent._dn:
                            if self._parent._dn + "/eth-profile-" + self.name + "/" in adapt.dn:
                                self.interrupt_coalescing_type = adapt.coalescing_type
                                self.interrupt_mode = adapt.mode
                                self.interrupt_timer = adapt.coalescing_time
                                self.interrupts = adapt.count
                                break

                if "adaptorEthRoCEProfile" in self._parent._config.sdk_objects:
                    for adapt in self._config.sdk_objects["adaptorEthRoCEProfile"]:
                        if self._parent._dn:
                            if self._parent._dn + "/eth-profile-" + self.name + "/" in adapt.dn:
                                self.roce = adapt.admin_state
                                if self.roce in ["enabled"]:
                                    roce_properties = {}
                                    roce_properties.update({"version_1": adapt.v1})
                                    roce_properties.update({"version_2": adapt.v2})
                                    roce_properties.update({"queue_pairs": adapt.queue_pairs})
                                    roce_properties.update({"memory_regions": adapt.memory_regions})
                                    roce_properties.update({"resource_groups": adapt.resource_groups})
                                    roce_properties.update({"priority": adapt.prio})
                                    self.roce_properties.append(roce_properties)
                                    break

                if "adaptorEthAdvFilterProfile" in self._parent._config.sdk_objects:
                    for adapt in self._config.sdk_objects["adaptorEthAdvFilterProfile"]:
                        if self._parent._dn:
                            if self._parent._dn + "/eth-profile-" + self.name + "/" in adapt.dn:
                                self.advance_filter = adapt.admin_state
                                break

                if "adaptorEthInterruptScalingProfile" in self._parent._config.sdk_objects:
                    for adapt in self._config.sdk_objects["adaptorEthInterruptScalingProfile"]:
                        if self._parent._dn:
                            if self._parent._dn + "/eth-profile-" + self.name + "/" in adapt.dn:
                                self.interrupt_scaling = adapt.admin_state
                                break

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)
                # We need to set all values that are not present in the config file to None
                for element in self.roce_properties:
                    for value in ["version_1", "version_2", "queue_pairs", "memory_regions", "resource_groups",
                                  "priority"]:
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

        mo_adaptor_host_eth_if_profile = AdaptorHostEthIfProfile(parent_mo_or_dn=parent_mo,
                                                                 descr=self.descr,
                                                                 name=self.name,
                                                                 pooled_resources=self.pooled)
        AdaptorEthWorkQueueProfile(parent_mo_or_dn=mo_adaptor_host_eth_if_profile,
                                   ring_size=self.transmit_queues_ring_size, count=self.transmit_queues)
        AdaptorEthRecvQueueProfile(parent_mo_or_dn=mo_adaptor_host_eth_if_profile,
                                   ring_size=self.receive_queues_ring_size, count=self.receive_queues)
        AdaptorEthCompQueueProfile(parent_mo_or_dn=mo_adaptor_host_eth_if_profile, count=self.completion_queues)
        AdaptorEthOffloadProfile(parent_mo_or_dn=mo_adaptor_host_eth_if_profile,
                                 tcp_tx_checksum=self.transmit_checksum_offload,
                                 tcp_rx_checksum=self.receive_checksum_offload,
                                 tcp_segment=self.tcp_segmentation_offload,
                                 large_receive=self.tcp_large_receive_offload)
        AdaptorRssProfile(parent_mo_or_dn=mo_adaptor_host_eth_if_profile,
                          receive_side_scaling=self.receive_side_scaling)
        AdaptorEthArfsProfile(parent_mo_or_dn=mo_adaptor_host_eth_if_profile,
                              accelarated_rfs=self.accelerated_receive_flow_steering)
        AdaptorEthNVGREProfile(parent_mo_or_dn=mo_adaptor_host_eth_if_profile, admin_state=self.nvgre_offload)
        AdaptorEthVxLANProfile(parent_mo_or_dn=mo_adaptor_host_eth_if_profile, admin_state=self.vxlan_offload)
        AdaptorEthGENEVEProfile(parent_mo_or_dn=mo_adaptor_host_eth_if_profile, offload=self.geneve_offload)
        # AdaptorAzureQosProfile(parent_mo_or_dn=mo_adaptor_host_eth_if_profile, adp_azure_qos=self.azurestack_host_qos)
        AdaptorEthFailoverProfile(parent_mo_or_dn=mo_adaptor_host_eth_if_profile, timeout=self.failback_timeout)
        AdaptorEthInterruptProfile(parent_mo_or_dn=mo_adaptor_host_eth_if_profile,
                                   coalescing_type=self.interrupt_coalescing_type,
                                   mode=self.interrupt_mode,
                                   coalescing_time=self.interrupt_timer,
                                   count=self.interrupts)
        if self.roce_properties:
            for roce_properties in self.roce_properties:
                AdaptorEthRoCEProfile(parent_mo_or_dn=mo_adaptor_host_eth_if_profile, admin_state=self.roce,
                                      queue_pairs=roce_properties["queue_pairs"],
                                      memory_regions=roce_properties["memory_regions"],
                                      resource_groups=roce_properties["resource_groups"],
                                      v1=roce_properties["version_1"],
                                      v2=roce_properties["version_2"],
                                      prio=roce_properties["priority"]
                                      )
        else:
            AdaptorEthRoCEProfile(parent_mo_or_dn=mo_adaptor_host_eth_if_profile, admin_state=self.roce)
        AdaptorEthAdvFilterProfile(parent_mo_or_dn=mo_adaptor_host_eth_if_profile, admin_state=self.advance_filter)
        AdaptorEthInterruptScalingProfile(parent_mo_or_dn=mo_adaptor_host_eth_if_profile,
                                          admin_state=self.interrupt_scaling)

        self._handle.add_mo(mo=mo_adaptor_host_eth_if_profile, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True


class UcsCentralFibreChannelAdapterPolicy(UcsCentralConfigObject):
    _CONFIG_NAME = "Fibre Channel Adapter Policy"
    _CONFIG_SECTION_NAME = "fibre_channel_adapter_policies"
    _UCS_SDK_OBJECT_NAME = "adaptorHostFcIfProfile"

    def __init__(self, parent=None, json_content=None, adaptor_host_fc_if_profile=None):
        UcsCentralConfigObject.__init__(self, parent=parent, ucs_sdk_object=adaptor_host_fc_if_profile)
        self.descr = None
        self.name = None
        self.receive_queues_ring_size = None
        self.transmit_queues_ring_size = None
        self.io_queues = None
        self.io_queues_ring_size = None
        self.fcp_error_recovery = None
        self.flogi_retries = None
        self.flogi_timeout = None
        self.plogi_retries = None
        self.plogi_timeout = None
        self.port_down_timeout = None
        self.io_retry_timeout = None
        self.port_down_io_retry = None
        self.link_down_timeout = None
        self.io_throttle_count = None
        self.max_luns_per_target = None
        self.lun_queue_depth = None
        self.interrupt_mode = None
        self.vhba_type = None

        if self._config.load_from == "live":
            if adaptor_host_fc_if_profile is not None:
                self.name = adaptor_host_fc_if_profile.name
                self.descr = adaptor_host_fc_if_profile.descr

                if "adaptorFcWorkQueueProfile" in self._parent._config.sdk_objects:
                    for adapt in self._config.sdk_objects["adaptorFcWorkQueueProfile"]:
                        if self._parent._dn:
                            if self._parent._dn + "/fc-profile-" + self.name + "/" in adapt.dn:
                                self.transmit_queues_ring_size = adapt.ring_size
                                break

                if "adaptorFcRecvQueueProfile" in self._parent._config.sdk_objects:
                    for adapt in self._config.sdk_objects["adaptorFcRecvQueueProfile"]:
                        if self._parent._dn:
                            if self._parent._dn + "/fc-profile-" + self.name + "/" in adapt.dn:
                                self.receive_queues_ring_size = adapt.ring_size
                                break

                if "adaptorFcCdbWorkQueueProfile" in self._parent._config.sdk_objects:
                    for adapt in self._config.sdk_objects["adaptorFcCdbWorkQueueProfile"]:
                        if self._parent._dn:
                            if self._parent._dn + "/fc-profile-" + self.name + "/" in adapt.dn:
                                self.io_queues = adapt.count
                                self.io_queues_ring_size = adapt.ring_size
                                break

                if "adaptorFcPortFLogiProfile" in self._parent._config.sdk_objects:
                    for adapt in self._config.sdk_objects["adaptorFcPortFLogiProfile"]:
                        if self._parent._dn:
                            if self._parent._dn + "/fc-profile-" + self.name + "/" in adapt.dn:
                                self.flogi_retries = adapt.retries
                                self.flogi_timeout = adapt.timeout
                                break

                if "adaptorFcPortPLogiProfile" in self._parent._config.sdk_objects:
                    for adapt in self._config.sdk_objects["adaptorFcPortPLogiProfile"]:
                        if self._parent._dn:
                            if self._parent._dn + "/fc-profile-" + self.name + "/" in adapt.dn:
                                self.plogi_retries = adapt.retries
                                self.plogi_timeout = adapt.timeout
                                break

                if "adaptorFcErrorRecoveryProfile" in self._parent._config.sdk_objects:
                    for adapt in self._config.sdk_objects["adaptorFcErrorRecoveryProfile"]:
                        if self._parent._dn:
                            if self._parent._dn + "/fc-profile-" + self.name + "/" in adapt.dn:
                                self.fcp_error_recovery = adapt.fcp_error_recovery
                                self.port_down_timeout = adapt.port_down_timeout
                                self.port_down_io_retry = adapt.port_down_io_retry_count
                                self.link_down_timeout = adapt.link_down_timeout
                                break

                if "adaptorFcPortProfile" in self._parent._config.sdk_objects:
                    for adapt in self._config.sdk_objects["adaptorFcPortProfile"]:
                        if self._parent._dn:
                            if self._parent._dn + "/fc-profile-" + self.name + "/" in adapt.dn:
                                self.io_throttle_count = adapt.io_throttle_count
                                self.max_luns_per_target = adapt.luns_per_target
                                break

                if "adaptorFcFnicProfile" in self._parent._config.sdk_objects:
                    for adapt in self._config.sdk_objects["adaptorFcFnicProfile"]:
                        if self._parent._dn:
                            if self._parent._dn + "/fc-profile-" + self.name + "/" in adapt.dn:
                                self.io_retry_timeout = adapt.io_retry_timeout
                                self.lun_queue_depth = adapt.lun_queue_depth
                                break

                if "adaptorFcInterruptProfile" in self._parent._config.sdk_objects:
                    for adapt in self._config.sdk_objects["adaptorFcInterruptProfile"]:
                        if self._parent._dn:
                            if self._parent._dn + "/fc-profile-" + self.name + "/" in adapt.dn:
                                self.interrupt_mode = adapt.mode
                                break

                # Commented below lines as vHBA type is not supported in central:CDET:CSCwa19838
                # if "adaptorFcVhbaTypeProfile" in self._parent._config.sdk_objects:
                #    for adapt in self._config.sdk_objects["adaptorFcVhbaTypeProfile"]:
                #        if self._parent._dn:
                #            if self._parent._dn + "/fc-profile-" + self.name + "/" in adapt.dn:
                #                self.vhba_type = adapt.mode
                #                break

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

        # Below is for handling an exception with UCS Central default global policies using an invalid value of 16
        # for io_throttle_count
        io_throttle_count = self.io_throttle_count
        if self.name in ["global-default", "global-Linux", "global-Solaris"]:
            if self.io_throttle_count == "16":
                io_throttle_count = None

        mo_adaptor_host_fc_if_profile = AdaptorHostFcIfProfile(parent_mo_or_dn=parent_mo, descr=self.descr,
                                                               name=self.name)
        AdaptorFcWorkQueueProfile(parent_mo_or_dn=mo_adaptor_host_fc_if_profile,
                                  ring_size=self.transmit_queues_ring_size)
        AdaptorFcRecvQueueProfile(parent_mo_or_dn=mo_adaptor_host_fc_if_profile,
                                  ring_size=self.receive_queues_ring_size)
        AdaptorFcCdbWorkQueueProfile(parent_mo_or_dn=mo_adaptor_host_fc_if_profile, count=self.io_queues,
                                     ring_size=self.io_queues_ring_size)
        AdaptorFcPortFLogiProfile(parent_mo_or_dn=mo_adaptor_host_fc_if_profile, retries=self.flogi_retries,
                                  timeout=self.flogi_timeout)
        AdaptorFcPortPLogiProfile(parent_mo_or_dn=mo_adaptor_host_fc_if_profile, retries=self.plogi_retries,
                                  timeout=self.plogi_timeout)
        AdaptorFcErrorRecoveryProfile(parent_mo_or_dn=mo_adaptor_host_fc_if_profile,
                                      fcp_error_recovery=self.fcp_error_recovery,
                                      port_down_timeout=self.port_down_timeout,
                                      port_down_io_retry_count=self.port_down_io_retry,
                                      link_down_timeout=self.link_down_timeout)
        AdaptorFcPortProfile(parent_mo_or_dn=mo_adaptor_host_fc_if_profile, io_throttle_count=io_throttle_count,
                             luns_per_target=self.max_luns_per_target)
        AdaptorFcFnicProfile(parent_mo_or_dn=mo_adaptor_host_fc_if_profile, io_retry_timeout=self.io_retry_timeout,
                             lun_queue_depth=self.lun_queue_depth)
        AdaptorFcInterruptProfile(parent_mo_or_dn=mo_adaptor_host_fc_if_profile, mode=self.interrupt_mode)

        # Commented below lines as vHBA type is not supported in central:CDET:CSCwa19838
        # if self.vhba_type:
        #    AdaptorFcVhbaTypeProfile(parent_mo_or_dn=mo_adaptor_host_fc_if_profile, mode=self.vhba_type)

        self._handle.add_mo(mo=mo_adaptor_host_fc_if_profile, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True


class UcsCentralFlowControlPolicy(UcsCentralConfigObject):
    _CONFIG_NAME = "Flow Control Policy"
    _CONFIG_SECTION_NAME = "flow_control_policies"
    _UCS_SDK_OBJECT_NAME = "flowctrlItem"

    def __init__(self, parent=None, json_content=None, flowctrl_item=None):
        UcsCentralConfigObject.__init__(self, parent=parent, ucs_sdk_object=flowctrl_item)
        self.name = None
        self.priority = None
        self.receive = None
        self.send = None
        if self._config.load_from == "live":
            if flowctrl_item is not None:
                self.name = flowctrl_item.name
                self.priority = flowctrl_item.prio
                self.receive = flowctrl_item.rcv
                self.send = flowctrl_item.snd

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

        parent_mo = "domaingroup-root/flowctrl"
        mo_flowctrl_item = FlowctrlItem(parent_mo_or_dn=parent_mo, name=self.name, snd=self.send,
                                        rcv=self.receive, prio=self.priority)

        self._handle.add_mo(mo=mo_flowctrl_item, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True


class UcsCentralGraphicsCardPolicy(UcsCentralConfigObject):
    _CONFIG_NAME = "Graphics Card Policy"
    _CONFIG_SECTION_NAME = "graphics_card_policies"
    _UCS_SDK_OBJECT_NAME = "computeGraphicsCardPolicy"

    def __init__(self, parent=None, json_content=None, compute_graphics_card_policy=None):
        UcsCentralConfigObject.__init__(self, parent=parent, ucs_sdk_object=compute_graphics_card_policy)
        self.name = None
        self.descr = None
        self.graphics_card_mode = None

        if self._config.load_from == "live":
            if compute_graphics_card_policy is not None:
                self.name = compute_graphics_card_policy.name
                self.descr = compute_graphics_card_policy.descr
                self.graphics_card_mode = compute_graphics_card_policy.graphics_card_mode

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

        mo_compute_graphics_card_policy = ComputeGraphicsCardPolicy(parent_mo_or_dn=parent_mo,
                                                                    name=self.name,
                                                                    descr=self.descr,
                                                                    graphics_card_mode=self.graphics_card_mode)
        self._handle.add_mo(mo=mo_compute_graphics_card_policy, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True


class UcsCentralHardwareChangeDiscoveryPolicy(UcsCentralConfigObject):
    _CONFIG_NAME = "Hardware Change Discovery Policy"
    _CONFIG_SECTION_NAME = "hardware_change_discovery_policies"
    _UCS_SDK_OBJECT_NAME = "computeDomainHwChangeDiscPolicy"

    def __init__(self, parent=None, json_content=None, compute_domain_hw_change_disc_policy=None):
        UcsCentralConfigObject.__init__(self, parent=parent, ucs_sdk_object=compute_domain_hw_change_disc_policy)
        self.name = None
        self.descr = None
        self.action = None

        if self._config.load_from == "live":
            if compute_domain_hw_change_disc_policy is not None:
                self.name = compute_domain_hw_change_disc_policy.name
                self.descr = compute_domain_hw_change_disc_policy.descr
                self.action = compute_domain_hw_change_disc_policy.action

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

        parent_mo = self._parent._dn
        mo_compute_domain_hw_change_disc_policy = ComputeDomainHwChangeDiscPolicy(
            parent_mo_or_dn=parent_mo, name=self.name, descr=self.descr, action=self.action)
        self._handle.add_mo(mo=mo_compute_domain_hw_change_disc_policy, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True


class UcsCentralHostFirmwarePackage(UcsCentralConfigObject):
    _CONFIG_NAME = "Host Firmware Package"
    _CONFIG_SECTION_NAME = "host_firmware_packages"
    _UCS_SDK_OBJECT_NAME = "firmwareComputeHostPack"

    def __init__(self, parent=None, json_content=None, firmware_compute_host_pack=None):
        UcsCentralConfigObject.__init__(self, parent=parent, ucs_sdk_object=firmware_compute_host_pack)
        self.name = None
        self.descr = None
        self.blade_package = None
        self.rack_package = None
        self.service_pack = None
        self.excluded_components = []

        if self._config.load_from == "live":
            if firmware_compute_host_pack is not None:
                self.name = firmware_compute_host_pack.name
                self.descr = firmware_compute_host_pack.descr
                self.rack_package = firmware_compute_host_pack.rack_bundle_version
                self.blade_package = firmware_compute_host_pack.blade_bundle_version
                self.service_pack = firmware_compute_host_pack.service_pack_bundle_version
                if "firmwareExcludeServerComponent" in self._parent._config.sdk_objects:
                    for excluded in self._config.sdk_objects["firmwareExcludeServerComponent"]:
                        if self._parent._dn:
                            if self._parent._dn + "/fw-host-pack-" + self.name + "/" in excluded.dn:
                                self.excluded_components.append(excluded.server_component)

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

        # Checks if the Blade/Rack Package versions are already present on the UCS Central
        # Avoids throwing an SDK error if the packages are not there
        if not self._is_firmware_package_present():
            return False

        override_default_exclusion = "no"
        # If "local-disk" is not explicitly excluded, we do not exclude it (excluded by default)
        if 'local-disk' not in self.excluded_components:
            override_default_exclusion = "yes"

        mo_firmware_host_pack = FirmwareComputeHostPack(parent_mo_or_dn=parent_mo, name=self.name, descr=self.descr,
                                                        blade_bundle_version=self.blade_package,
                                                        rack_bundle_version=self.rack_package,
                                                        override_default_exclusion=override_default_exclusion,
                                                        service_pack_bundle_version=self.service_pack)
        # Creating excluded list to identify user defined duplicate entry.
        excluded_list = []
        for excluded in self.excluded_components:
            excluded = self._rename_component_type(component_type=excluded)
            # Check if excluded element is duplicate entry or not.
            if excluded not in excluded_list:
                excluded_list.append(excluded)
                FirmwareExcludeServerComponent(parent_mo_or_dn=mo_firmware_host_pack, server_component=excluded)
            else:
                self.logger(level="debug",
                            message="Ignoring duplicate excluded component " + excluded +
                            " for " + self._CONFIG_NAME + ": " + str(self.name))
                continue

        self._handle.add_mo(mo=mo_firmware_host_pack, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True

    def _is_firmware_package_present(self):
        """
        Checks if the firmware package is present in the UCS Central

        :return: True if the firmware package is present, False otherwise
        """
        return_value = True
        if self.blade_package:
            found = self._handle.query_classid("firmwareDistributable",
                                               filter_str="(version,'" + self.blade_package + "',type='eq')")
            if not found:
                self.logger(level="warning",
                            message="Blade Package version " + self.blade_package +
                                    " is not present, the Host Firmware Package will not be created")
                return_value = False
        if self.rack_package:
            found = self._handle.query_classid("firmwareDistributable",
                                               filter_str="(version,'" + self.rack_package + "',type='eq')")
            if not found:
                self.logger(level="warning",
                            message="Rack Package version " + self.rack_package +
                                    " is not present, the Host Firmware Package will not be created")
                return_value = False

        return return_value

    def _rename_component_type(self, component_type=None):
        # Perform various renaming operations to conform to SDK expected input
        component_type_dict = {
            "adapter": "adaptor",
            "bios": "blade-bios", "server-bios": "blade-bios",
            "cimc": "blade-controller",
            "gpus": "graphics-card",
            "fc-adapters": "host-hba",
            "hba-optionrom": "host-hba-optionrom",
            "nvme-mswitch-fw": "nvme-mswitch",
            "pci-switch-fw": "plx-switch",
            "sas-expander-regular-fw": "sas-exp-reg-fw",
            "storage-device-bridge": "storage-dev-bridge", "storage-bridge-device": "storage-dev-bridge"
        }
        if component_type in component_type_dict.keys():
            return component_type_dict[component_type]
        else:
            return component_type


class UcsCentralHostInterfacePlacementPolicy(UcsCentralConfigObject):
    _CONFIG_NAME = "Host Interface Placement Policy"
    _CONFIG_SECTION_NAME = "host_interface_placement_policies"
    _UCS_SDK_OBJECT_NAME = "fabricVConProfile"

    def __init__(self, parent=None, json_content=None, fabric_vcon_profile=None):
        UcsCentralConfigObject.__init__(self, parent=parent, ucs_sdk_object=fabric_vcon_profile)
        self.name = None
        self.descr = None
        self.virtual_slot_mapping_scheme = None
        self.selection_preference = []

        if self._config.load_from == "live":
            if fabric_vcon_profile is not None:
                self.name = fabric_vcon_profile.name
                self.descr = fabric_vcon_profile.descr
                self.virtual_slot_mapping_scheme = fabric_vcon_profile.mezz_mapping

                if "fabricVCon" in self._parent._config.sdk_objects:
                    for slot_preference in self._config.sdk_objects["fabricVCon"]:
                        if self._parent._dn:
                            if self._parent._dn + "/vcon-profile-" + self.name + "/" in slot_preference.dn:
                                self.selection_preference.append(
                                    {
                                        "slot_id": slot_preference.id,
                                        "slot_selection_preference": slot_preference.select
                                    }
                                )

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

        parent_mo = self._parent._dn
        mo_fabric_vcon_profile = FabricVConProfile(
            parent_mo_or_dn=parent_mo, name=self.name, descr=self.descr, mezz_mapping=self.virtual_slot_mapping_scheme)
        for preferance in self.selection_preference:
            FabricVCon(parent_mo_or_dn=mo_fabric_vcon_profile, id=preferance["slot_id"],
                       select=preferance["slot_selection_preference"])

        self._handle.add_mo(mo=mo_fabric_vcon_profile, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True


class UcsCentralIdRangeAccessControlPolicy(UcsCentralConfigObject):
    _CONFIG_NAME = "ID Range Access Control Policy"
    _CONFIG_SECTION_NAME = "id_range_access_control_policies"
    _UCS_SDK_OBJECT_NAME = "identpoolBlockQual"

    def __init__(self, parent=None, json_content=None, ident_pool_block_qual=None):
        UcsCentralConfigObject.__init__(self, parent=parent, ucs_sdk_object=ident_pool_block_qual)
        self.name = None
        self.descr = None
        self.domain_groups = []

        if self._config.load_from == "live":
            if ident_pool_block_qual is not None:
                self.name = ident_pool_block_qual.name
                self.descr = ident_pool_block_qual.descr

            # Filtering Domain Group(s) associated with the ID Range Access Control Policy.
            if "identpoolDomainGroupQual" in self._parent._config.sdk_objects:
                for identpoolDomainGroupQual in self._config.sdk_objects["identpoolDomainGroupQual"]:
                    if self._parent._dn + "/block-qualifier-" + self.name + "/" in identpoolDomainGroupQual.dn:
                        # Converting Domain Group name to user readable name.
                        # Eg:  domaingroup-root/domaingroup-EU-root-1 is changed to root/EU-root-1
                        self.domain_groups.append('/'.join([domaingrp.replace('domaingroup-', '', 1) for domaingrp
                                                            in identpoolDomainGroupQual.group_dn.split('/')]))

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

        mo_id_range_access_control_policy = \
            IdentpoolBlockQual(parent_mo_or_dn=parent_mo,
                               name=self.name,
                               descr=self.descr)

        # Add Permitted Domain Group(s) to ID Range Access Control Policy
        for domain_group in self.domain_groups:
            # Converting user readable Domain Group name to sdk acceptable Domain Group Dn
            # Eg: root/EU-root-1 is changed to domaingroup-root/domaingroup-EU-root-1
            # Name of IdentpoolDomainGroupQual is provided as hexadecimal encoding of domain group name
            group_dn = '/'.join(["domaingroup-" + dngrp for dngrp in domain_group.split('/')])
            IdentpoolDomainGroupQual(parent_mo_or_dn=mo_id_range_access_control_policy,
                                     name="easyucs-" + hashlib.md5(domain_group.encode()).hexdigest()[:8],
                                     group_dn=group_dn)

        self._handle.add_mo(mo=mo_id_range_access_control_policy, modify_present=True)

        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True


class UcsCentralInbandPolicy(UcsCentralConfigObject):
    _CONFIG_NAME = "Inband Policy"
    _CONFIG_SECTION_NAME = "inband_policies"
    _UCS_SDK_OBJECT_NAME = "inbandPolicy"

    def __init__(self, parent=None, json_content=None, inband_policy=None):
        UcsCentralConfigObject.__init__(self, parent, ucs_sdk_object=inband_policy)
        self.name = None
        self.descr = None
        self.vlan_groups = []
        self.management_ip_pool = None

        if self._config.load_from == "live":
            if inband_policy is not None:
                self.name = inband_policy.name
                self.descr = inband_policy.descr
                vlan_group = {}
                vlan_group.update({"default_management_vlan": inband_policy.default_network,
                                   "vlan_group": inband_policy.netgroup_name})
                self.vlan_groups.append(vlan_group)
                self.management_ip_pool = inband_policy.pool_name

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error", message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + str(self.name))
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + str(self.name) +
                        ", waiting for a commit")

        parent_mo = self._parent._dn
        for vlan_group in self.vlan_groups:
            mo_inband_policy = InbandPolicy(
                parent_mo_or_dn=parent_mo, name=self.name, descr=self.descr,
                default_network=vlan_group["default_management_vlan"],
                netgroup_name=vlan_group["vlan_group"], pool_name=self.management_ip_pool)

        self._handle.add_mo(mo=mo_inband_policy, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True


class UcsCentralIpmiAccessProfile(UcsCentralConfigObject):
    _CONFIG_NAME = "IPMI Access Profile"
    _CONFIG_SECTION_NAME = "ipmi_access_profiles"
    _UCS_SDK_OBJECT_NAME = "aaaEpAuthProfile"

    def __init__(self, parent=None, json_content=None, aaa_ep_auth_profile=None):
        UcsCentralConfigObject.__init__(self, parent=parent, ucs_sdk_object=aaa_ep_auth_profile)
        self.descr = None
        self.name = None
        self.ipmi_over_lan = None
        self.users = []

        if self._config.load_from == "live":
            if aaa_ep_auth_profile is not None:
                self.name = aaa_ep_auth_profile.name
                self.ipmi_over_lan = aaa_ep_auth_profile.ipmi_over_lan
                self.descr = aaa_ep_auth_profile.descr

                if "aaaEpUser" in self._parent._config.sdk_objects:
                    for ep_user in self._config.sdk_objects["aaaEpUser"]:
                        if self._parent._dn:
                            if self._parent._dn + "/auth-profile-" + self.name + "/" in ep_user.dn:
                                user = {}
                                user.update({"name": ep_user.name})
                                user.update({"password": ep_user.pwd})
                                user.update({"role": ep_user.priv})
                                user.update({"descr": ep_user.descr})
                                self.users.append(user)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

                # We need to set all values that are not present in the config file to None
                for element in self.users:
                    for value in ["name", "password", "role", "descr"]:
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

        mo_ep_auth_profile = AaaEpAuthProfile(parent_mo_or_dn=parent_mo, descr=self.descr, name=self.name,
                                              ipmi_over_lan=self.ipmi_over_lan)

        for user in self.users:
            role = user['role']
            if role in ["read_only", "read-only", "read only"]:
                role = "readonly"
            AaaEpUser(parent_mo_or_dn=mo_ep_auth_profile, priv=role, descr=user['descr'],
                      name=user['name'], pwd=user['password'])

        self._handle.add_mo(mo=mo_ep_auth_profile, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True


class UcsCentralIscsiAdapterPolicy(UcsCentralConfigObject):
    _CONFIG_NAME = "iSCSI Adapter Policy"
    _CONFIG_SECTION_NAME = "iscsi_adapter_policies"
    _UCS_SDK_OBJECT_NAME = "adaptorHostIscsiIfProfile"

    def __init__(self, parent=None, json_content=None, adaptor_host_iscsi_if_profile=None):
        UcsCentralConfigObject.__init__(self, parent=parent, ucs_sdk_object=adaptor_host_iscsi_if_profile)
        self.descr = None
        self.name = None
        self.connection_timeout = None
        self.lun_busy_retry_count = None
        self.dhcp_timeout = None
        self.enable_tcp_timestamp = None
        self.hba_mode = None
        self.boot_to_target = None

        if self._config.load_from == "live":
            if adaptor_host_iscsi_if_profile is not None:
                self.name = adaptor_host_iscsi_if_profile.name
                self.descr = adaptor_host_iscsi_if_profile.descr

                if "adaptorProtocolProfile" in self._parent._config.sdk_objects:
                    for adapt in self._config.sdk_objects["adaptorProtocolProfile"]:
                        if self._parent._dn:
                            if self._parent._dn + "/iscsi-profile-" + self.name + "/" in adapt.dn:
                                self.connection_timeout = adapt.connection_time_out
                                self.lun_busy_retry_count = adapt.lun_busy_retry_count
                                self.dhcp_timeout = adapt.dhcp_time_out
                                self.enable_tcp_timestamp = adapt.tcp_time_stamp
                                self.hba_mode = adapt.hba_mode
                                self.boot_to_target = adapt.boot_to_target
                                break

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

        mo_adaptor_host_iscsi_if_profile = AdaptorHostIscsiIfProfile(
            parent_mo_or_dn=parent_mo, name=self.name, descr=self.descr)
        AdaptorProtocolProfile(parent_mo_or_dn=mo_adaptor_host_iscsi_if_profile,
                               connection_time_out=self.connection_timeout,
                               lun_busy_retry_count=self.lun_busy_retry_count, dhcp_time_out=self.dhcp_timeout,
                               tcp_time_stamp=self.enable_tcp_timestamp, hba_mode=self.hba_mode,
                               boot_to_target=self.boot_to_target)

        self._handle.add_mo(mo=mo_adaptor_host_iscsi_if_profile, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True


class UcsCentralIscsiAuthenticationProfile(UcsCentralConfigObject):
    _CONFIG_NAME = "iSCSI Authentication Profile"
    _CONFIG_SECTION_NAME = "iscsi_authentication_profiles"
    _UCS_SDK_OBJECT_NAME = "iscsiAuthProfile"

    def __init__(self, parent=None, json_content=None, iscsi_auth_profile=None):
        UcsCentralConfigObject.__init__(self, parent=parent, ucs_sdk_object=iscsi_auth_profile)
        self.name = None
        self.user_id = None
        self.password = None
        self.descr = None

        if self._config.load_from == "live":
            if iscsi_auth_profile is not None:
                self.name = iscsi_auth_profile.name
                self.descr = iscsi_auth_profile.descr
                self.name = iscsi_auth_profile.name
                self.user_id = iscsi_auth_profile.user_id

                self.logger(level="warning",
                            message="Password of user " + self.user_id + " of " + self._CONFIG_NAME + " " +
                                    str(self.name) + " can't be exported")

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

        mo_iscsi_auth_profile = IscsiAuthProfile(parent_mo_or_dn=parent_mo,
                                                 name=self.name,
                                                 descr=self.descr,
                                                 user_id=self.user_id,
                                                 password=self.password)

        self._handle.add_mo(mo=mo_iscsi_auth_profile, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True


class UcsCentralKmipCertificationPolicy(UcsCentralConfigObject):
    _CONFIG_NAME = "KMIP Certification Policy"
    _CONFIG_SECTION_NAME = "kmip_certification_policies"
    _UCS_SDK_OBJECT_NAME = "mgmtNamedKmipCertPolicy"

    def __init__(self, parent=None, json_content=None, mgmt_named_kmip_cert_policy=None):
        UcsCentralConfigObject.__init__(self, parent=parent, ucs_sdk_object=mgmt_named_kmip_cert_policy)
        self.name = None
        self.country_code = None
        self.descr = None
        self.email_addr = None
        self.locality = None
        self.org_name = None
        self.org_unit_name = None
        self.state = None
        self.validity = None

        if self._config.load_from == "live":
            if mgmt_named_kmip_cert_policy is not None:
                self.name = mgmt_named_kmip_cert_policy.name
                self.country_code = mgmt_named_kmip_cert_policy.country_code
                self.descr = mgmt_named_kmip_cert_policy.descr
                self.email_addr = mgmt_named_kmip_cert_policy.email_addr
                self.locality = mgmt_named_kmip_cert_policy.locality
                self.org_name = mgmt_named_kmip_cert_policy.org_name
                self.org_unit_name = mgmt_named_kmip_cert_policy.org_unit_name
                self.state = mgmt_named_kmip_cert_policy.state
                self.validity = mgmt_named_kmip_cert_policy.validity

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

        mo_kmip_certification_policy = MgmtNamedKmipCertPolicy(parent_mo_or_dn=parent_mo,
                                                               name=self.name,
                                                               descr=self.descr,
                                                               country_code=self.country_code,
                                                               email_addr=self.email_addr,
                                                               locality=self.locality,
                                                               org_name=self.org_name,
                                                               org_unit_name=self.org_unit_name,
                                                               state=self.state,
                                                               validity=self.validity)
        self._handle.add_mo(mo=mo_kmip_certification_policy, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True


class UcsCentralLacpPolicy(UcsCentralConfigObject):
    _CONFIG_NAME = "LACP Policy"
    _CONFIG_SECTION_NAME = "lacp_policies"
    _UCS_SDK_OBJECT_NAME = "fabricLacpPolicy"

    def __init__(self, parent=None, json_content=None, fabric_lacp_policy=None):
        UcsCentralConfigObject.__init__(self, parent=parent, ucs_sdk_object=fabric_lacp_policy)
        self.name = None
        self.suspend_individual = None
        self.lacp_rate = None

        if self._config.load_from == "live":
            if fabric_lacp_policy is not None:
                self.name = fabric_lacp_policy.name
                self.suspend_individual = fabric_lacp_policy.suspend_individual
                self.lacp_rate = fabric_lacp_policy.fast_timer

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

        mo_fabric_lacp_policy = FabricLacpPolicy(parent_mo_or_dn=parent_mo, suspend_individual=self.suspend_individual,
                                                 fast_timer=self.lacp_rate, name=self.name)
        self._handle.add_mo(mo=mo_fabric_lacp_policy, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True


class UcsCentralLinkProfile(UcsCentralConfigObject):
    _CONFIG_NAME = "Link Profile"
    _CONFIG_SECTION_NAME = "link_profiles"
    _UCS_SDK_OBJECT_NAME = "fabricEthLinkProfile"

    def __init__(self, parent=None, json_content=None, fabric_eth_link_profile=None):
        UcsCentralConfigObject.__init__(self, parent=parent, ucs_sdk_object=fabric_eth_link_profile)
        self.name = None
        self.descr = None
        self.udld_link_policy = None

        if self._config.load_from == "live":
            if fabric_eth_link_profile is not None:
                self.name = fabric_eth_link_profile.name
                self.descr = fabric_eth_link_profile.descr
                self.udld_link_policy = fabric_eth_link_profile.udld_link_policy_name

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

        parent_mo = self._parent._dn
        mo_fabric_eth_link_profile = FabricEthLinkProfile(parent_mo_or_dn=parent_mo,
                                                          udld_link_policy_name=self.udld_link_policy,
                                                          name=self.name, descr=self.descr)

        self._handle.add_mo(mo=mo_fabric_eth_link_profile, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True


class UcsCentralLocalDiskConfPolicy(UcsCentralConfigObject):
    _CONFIG_NAME = "Local Disk Configuration Policy"
    _CONFIG_SECTION_NAME = "local_disk_config_policies"
    _UCS_SDK_OBJECT_NAME = "storageLocalDiskConfigPolicy"
    _UCS_SDK_SPECIFIC_OBJECT_NAME = "storageLocalDiskConfigDef"

    def __init__(self, parent=None, json_content=None, storage_local_disk_config_policy=None):
        UcsCentralConfigObject.__init__(self, parent=parent, ucs_sdk_object=storage_local_disk_config_policy)
        self.name = None
        self.descr = None
        self.mode = None
        self.protect_configuration = None
        self.flexflash_state = None
        self.flexflash_raid_reporting_state = None
        # self.flexflash_removable_state = None

        if self._config.load_from == "live":
            if storage_local_disk_config_policy is not None:
                self.name = storage_local_disk_config_policy.name
                self.descr = storage_local_disk_config_policy.descr
                self.mode = storage_local_disk_config_policy.mode
                self.protect_configuration = storage_local_disk_config_policy.protect_config
                self.flexflash_state = storage_local_disk_config_policy.flex_flash_state
                self.flexflash_raid_reporting_state = storage_local_disk_config_policy.flex_flash_raid_reporting_state
                # self.flexflash_removable_state = storage_local_disk_config_policy.flex_flash_removable_state

                if self._parent._dn:
                    if self._parent.__class__.__name__ == "UcsCentralServiceProfile":
                        # We are in presence of a Specific Local Disk Config Policy under a Service Profile object
                        self.name = None

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        detail = str(self.name)
        if self._parent.__class__.__name__ == "UcsCentralServiceProfile":
            # We are in presence of a Specific Local Disk Config Policy under a Service Profile object
            detail = "Service Profile " + str(self._parent.name)
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + detail)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + detail +
                                ", waiting for a commit")

        if hasattr(self._parent, '_dn'):
            parent_mo = self._parent._dn
        else:
            self.logger(level="error",
                        message="Impossible to find the parent dn of " + self._CONFIG_NAME + " : " + str(self.name))
            return False

        # Handle all types of writing for all modes
        mode = self.mode
        if mode == "none" or mode == "no-local-storage" or mode == "no":
            mode = "no-local-storage"
        elif mode == "default" or mode == "any-configuration" or mode == "any":
            mode = "any-configuration"
        elif mode == "NoRaid" or mode == "no-raid" or mode == "no raid":
            mode = "no-raid"
        elif mode == "RAID0" or mode == "raid0" or mode == "raid-striped":
            mode = "raid-striped"
        elif mode == "RAID1" or mode == "raid1" or mode == "raid-mirrored":
            mode = "raid-mirrored"
        elif mode == "RAID5" or mode == "raid5" or mode == "raid-striped-parity":
            mode = "raid-striped-parity"
        elif mode == "RAID6" or mode == "raid6" or mode == "raid-striped-dual-parity":
            mode = "raid-striped-dual-parity"
        elif mode == "RAID10" or mode == "raid10" or mode == "raid-mirrored-striped":
            mode = "raid-mirrored-striped"
        elif mode == "RAID50" or mode == "raid50" or mode == "raid-striped-parity-striped":
            mode = "raid-striped-parity-striped"
        elif mode == "RAID60" or mode == "raid60" or mode == "raid-striped-dual-parity-striped":
            mode = "raid-striped-dual-parity-striped"

        if self._parent.__class__.__name__ == "UcsCentralServiceProfile":
            # We are in presence of a Specific Local Disk Config Policy under a Service Profile object
            # Removed param "flex_flash_removable_state=self.flexflash_removable_state" from below func
            mo_storage_local_disk_config_policy = StorageLocalDiskConfigDef(
                parent_mo_or_dn=parent_mo, mode=mode, descr=self.descr, protect_config=self.protect_configuration,
                flex_flash_raid_reporting_state=self.flexflash_raid_reporting_state,
                flex_flash_state=self.flexflash_state
            )
        else:
            # We are in presence of a regular Local Disk Config Policy under an Org object
            # Removed param "flex_flash_removable_state=self.flexflash_removable_state" from below func
            mo_storage_local_disk_config_policy = StorageLocalDiskConfigPolicy(
                parent_mo_or_dn=parent_mo, name=self.name, mode=mode, descr=self.descr,
                protect_config=self.protect_configuration,
                flex_flash_raid_reporting_state=self.flexflash_raid_reporting_state,
                flex_flash_state=self.flexflash_state
            )

        self._handle.add_mo(mo=mo_storage_local_disk_config_policy, modify_present=True)
        if commit:
            detail = str(self.name)
            if self._parent.__class__.__name__ == "UcsCentralServiceProfile":
                # We are in presence of a Specific Local Disk Config Policy under a Service Profile object
                detail = "Service Profile " + str(self._parent.name)
            if self.commit(detail=detail) != True:
                return False
        return True


class UcsCentralMulticastPolicy(UcsCentralConfigObject):
    _CONFIG_NAME = "Multicast Policy"
    _CONFIG_SECTION_NAME = "multicast_policies"
    _UCS_SDK_OBJECT_NAME = "fabricMulticastPolicy"

    def __init__(self, parent=None, json_content=None, fabric_multicast_policy=None):
        UcsCentralConfigObject.__init__(self, parent=parent, ucs_sdk_object=fabric_multicast_policy)
        self.name = None
        self.descr = None
        self.igmp_snooping_state = None
        self.igmp_snooping_querier_state = None
        self.fi_a_querier_ip_address = None
        self.fi_b_querier_ip_address = None

        if self._config.load_from == "live":
            if fabric_multicast_policy is not None:
                self.name = fabric_multicast_policy.name
                self.descr = fabric_multicast_policy.descr
                self.igmp_snooping_state = fabric_multicast_policy.snooping_state
                self.igmp_snooping_querier_state = fabric_multicast_policy.querier_state

                if self.igmp_snooping_querier_state == "enabled":
                    self.fi_a_querier_ip_address = fabric_multicast_policy.querier_ip_addr
                    self.fi_b_querier_ip_address = fabric_multicast_policy.querier_ip_addr_peer

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

        mo_fabric_multicast_policy = FabricMulticastPolicy(parent_mo_or_dn=parent_mo, name=self.name, descr=self.descr,
                                                           querier_state=self.igmp_snooping_querier_state,
                                                           snooping_state=self.igmp_snooping_state,
                                                           querier_ip_addr_peer=self.fi_b_querier_ip_address,
                                                           querier_ip_addr=self.fi_a_querier_ip_address)

        self._handle.add_mo(mo=mo_fabric_multicast_policy, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True


class UcsCentralMaintenancePolicy(UcsCentralConfigObject):
    _CONFIG_NAME = "Maintenance Policy"
    _CONFIG_SECTION_NAME = "maintenance_policies"
    _UCS_SDK_OBJECT_NAME = "lsmaintMaintPolicy"

    def __init__(self, parent=None, json_content=None, lsmaint_maint_policy=None):
        UcsCentralConfigObject.__init__(self, parent=parent, ucs_sdk_object=lsmaint_maint_policy)
        self.name = None
        self.descr = None
        self.soft_shutdown_timer = None
        self.schedule = None
        self.on_next_boot = None
        self.reboot_policy = None
        self.storage_config_deployment_policy = None

        if self._config.load_from == "live":
            if lsmaint_maint_policy is not None:
                self.name = lsmaint_maint_policy.name
                self.descr = lsmaint_maint_policy.descr
                self.soft_shutdown_timer = lsmaint_maint_policy.soft_shutdown_timer
                if self.soft_shutdown_timer:
                    if "-secs" in self.soft_shutdown_timer:
                        self.soft_shutdown_timer = self.soft_shutdown_timer.split('-secs')[0]
                self.schedule = lsmaint_maint_policy.sched_name
                if lsmaint_maint_policy.trigger_config == "on-next-boot":
                    self.on_next_boot = "on"
                self.reboot_policy = lsmaint_maint_policy.uptime_disr
                self.storage_config_deployment_policy = lsmaint_maint_policy.data_disr

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

        timer = self.soft_shutdown_timer
        if timer and timer != "never":
            timer = timer + "-secs"

        trigger = None
        if self.on_next_boot in ["on", "true", "yes"]:
            trigger = "on-next-boot"

        mo_lsmaint_maint_policy = LsmaintMaintPolicy(parent_mo_or_dn=parent_mo, name=self.name, descr=self.descr,
                                                     soft_shutdown_timer=timer, sched_name=self.schedule,
                                                     uptime_disr=self.reboot_policy, trigger_config=trigger,
                                                     data_disr=self.storage_config_deployment_policy)
        self._handle.add_mo(mo=mo_lsmaint_maint_policy, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False


class UcsCentralGenericNetworkControlPolicy(UcsCentralConfigObject):
    _UCS_SDK_OBJECT_NAME = "nwctrlDefinition"

    def __init__(self, parent=None, json_content=None, nwctrl_definition=None):
        UcsCentralConfigObject.__init__(self, parent=parent, ucs_sdk_object=nwctrl_definition)
        self.name = None
        self.cdp_admin_state = None
        self.action_on_uplink_fail = None
        self.mac_register_mode = None
        self.descr = None
        self.lldp_receive = None
        self.lldp_transmit = None
        self.mac_security_forge = None

        if self._config.load_from == "live":
            if nwctrl_definition is not None:
                self.name = nwctrl_definition.name
                self.cdp_admin_state = nwctrl_definition.cdp
                self.action_on_uplink_fail = nwctrl_definition.uplink_fail_action
                self.mac_register_mode = nwctrl_definition.mac_register_mode
                self.descr = nwctrl_definition.descr
                self.lldp_receive = nwctrl_definition.lldp_receive
                self.lldp_transmit = nwctrl_definition.lldp_transmit

                if "dpsecMac" in self._parent._config.sdk_objects:
                    for dpsec_mac in self._config.sdk_objects["dpsecMac"]:
                        if self._parent._dn + "/nwctrl-" + self.name + "/" in dpsec_mac.dn:
                            self.mac_security_forge = dpsec_mac.forge
                            break

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

        mo_nwctrl_definition = NwctrlDefinition(parent_mo_or_dn=parent_mo, cdp=self.cdp_admin_state,
                                                lldp_receive=self.lldp_receive, name=self.name,
                                                uplink_fail_action=self.action_on_uplink_fail,
                                                lldp_transmit=self.lldp_transmit, descr=self.descr,
                                                mac_register_mode=self.mac_register_mode)
        DpsecMac(parent_mo_or_dn=mo_nwctrl_definition, descr=self.descr, name="", forge=self.mac_security_forge)

        self._handle.add_mo(mo=mo_nwctrl_definition, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True


class UcsCentralNetworkControlPolicy(UcsCentralGenericNetworkControlPolicy):
    _CONFIG_NAME = "Network Control Policy"
    _CONFIG_SECTION_NAME = "network_control_policies"


class UcsCentralApplianceNetworkControlPolicy(UcsCentralGenericNetworkControlPolicy):
    _CONFIG_NAME = "Appliance Network Control Policy"
    _CONFIG_SECTION_NAME = "appliance_network_control_policies"


class UcsCentralPortAutoDiscoveryPolicy(UcsCentralConfigObject):
    _CONFIG_NAME = "Port Auto Discovery Policy"
    _CONFIG_SECTION_NAME = "port_auto_discovery_policies"
    _UCS_SDK_OBJECT_NAME = "computeDomainPortDiscPolicy"

    def __init__(self, parent=None, json_content=None, compute_domain_port_disc_policy=None):
        UcsCentralConfigObject.__init__(self, parent=parent, ucs_sdk_object=compute_domain_port_disc_policy)

        self.name = None
        self.descr = None
        self.auto_configure_server_ports = None

        if self._config.load_from == "live":
            self.name = compute_domain_port_disc_policy.name
            self.descr = compute_domain_port_disc_policy.descr
            self.auto_configure_server_ports = compute_domain_port_disc_policy.eth_svr_auto_discovery

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration" +
                                ", waiting for a commit")

        if hasattr(self._parent, '_dn'):
            parent_mo = self._parent._dn
        else:
            self.logger(level="error",
                        message="Impossible to find the parent dn of " + self._CONFIG_NAME + " : " + str(self.name))
            return False

        mo_compute_domain_port_disc_policy = ComputeDomainPortDiscPolicy(
            parent_mo_or_dn=parent_mo, name=self.name, descr=self.descr,
            eth_svr_auto_discovery=self.auto_configure_server_ports)

        self._handle.add_mo(mo=mo_compute_domain_port_disc_policy, modify_present=True)
        if commit:
            if self.commit() != True:
                return False
        return True


class UcsCentralPowerControlPolicy(UcsCentralConfigObject):
    _CONFIG_NAME = "Power Control Policy"
    _CONFIG_SECTION_NAME = "power_control_policies"
    _UCS_SDK_OBJECT_NAME = "powerPolicy"

    def __init__(self, parent=None, json_content=None, power_policy=None):
        UcsCentralConfigObject.__init__(self, parent=parent, ucs_sdk_object=power_policy)
        self.name = None
        self.descr = None
        # self.aggressive_cooling = None
        self.fan_speed_policy = None
        self.power_capping = None

        if self._config.load_from == "live":
            if power_policy is not None:
                self.name = power_policy.name
                self.descr = power_policy.descr
                # self.aggressive_cooling = power_policy.aggressive_cooling
                self.fan_speed_policy = power_policy.fan_speed
                self.power_capping = power_policy.prio

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

        mo_power_policy = PowerPolicy(parent_mo_or_dn=parent_mo,
                                      prio=self.power_capping,
                                      name=self.name,
                                      # aggressive_cooling=self.aggressive_cooling,
                                      fan_speed=self.fan_speed_policy,
                                      descr=self.descr)
        self._handle.add_mo(mo=mo_power_policy, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False


class UcsCentralPowerSyncPolicy(UcsCentralConfigObject):
    _CONFIG_NAME = "Power Sync Policy"
    _CONFIG_SECTION_NAME = "power_sync_policies"
    _UCS_SDK_OBJECT_NAME = "computePowerSyncPolicy"

    def __init__(self, parent=None, json_content=None, compute_power_sync_policy=None):
        UcsCentralConfigObject.__init__(self, parent=parent, ucs_sdk_object=compute_power_sync_policy)
        self.name = None
        self.descr = None
        self.sync_option = None

        if self._config.load_from == "live":
            if compute_power_sync_policy is not None:
                self.name = compute_power_sync_policy.name
                self.descr = compute_power_sync_policy.descr
                self.sync_option = compute_power_sync_policy.sync_option

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

        sync_option = self.sync_option
        if sync_option == "initial":
            sync_option = "initial-only-sync"
        if sync_option == "always":
            sync_option = "always-sync"
        if sync_option == "default-sync":
            sync_option = "default"

        mo_power_sync_policy = ComputePowerSyncPolicy(parent_mo_or_dn=parent_mo,
                                                      name=self.name,
                                                      sync_option=sync_option,
                                                      descr=self.descr)

        self._handle.add_mo(mo=mo_power_sync_policy, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True


class UcsCentralQosPolicy(UcsCentralConfigObject):
    _CONFIG_NAME = "QoS Policy"
    _CONFIG_SECTION_NAME = "qos_policies"
    _UCS_SDK_OBJECT_NAME = "epqosDefinition"

    def __init__(self, parent=None, json_content=None, epqos_definition=None):
        UcsCentralConfigObject.__init__(self, parent=parent, ucs_sdk_object=epqos_definition)
        self.name = None
        self.descr = None
        self.rate = None
        self.priority = None
        self.burst = None
        self.host_control = None

        if self._config.load_from == "live":
            if epqos_definition is not None:
                self.name = epqos_definition.name
                self.descr = epqos_definition.descr
                if "epqosEgress" in self._config.sdk_objects:
                    if self._parent._dn:
                        epqos_egress = [egress for egress in self._config.sdk_objects["epqosEgress"]
                                        if self._parent._dn + "/ep-qos-" + self.name + "/" in egress.dn]
                        if len(epqos_egress) == 1:
                            self.rate = epqos_egress[0].rate
                            self.priority = epqos_egress[0].prio
                            self.burst = epqos_egress[0].burst
                            self.host_control = epqos_egress[0].host_control

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
                        message="Impossible to find the parent dn of " + self._CONFIG_NAME + " : " + self.policy_name)
            return False

        mo_epqos_definition = EpqosDefinition(parent_mo_or_dn=parent_mo, descr=self.descr, name=self.name)
        EpqosEgress(parent_mo_or_dn=mo_epqos_definition, rate=self.rate, prio=self.priority, burst=self.burst, name="",
                    host_control=self.host_control)

        self._handle.add_mo(mo=mo_epqos_definition, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False


class UcsCentralScrubPolicy(UcsCentralConfigObject):
    _CONFIG_NAME = "Scrub Policy"
    _CONFIG_SECTION_NAME = "scrub_policies"
    _UCS_SDK_OBJECT_NAME = "computeScrubPolicy"

    def __init__(self, parent=None, json_content=None, compute_scrub_policy=None):
        UcsCentralConfigObject.__init__(self, parent=parent, ucs_sdk_object=compute_scrub_policy)
        self.name = None
        self.disk_scrub = None
        self.flexflash_scrub = None
        self.bios_settings_scrub = None
        # uncomment the below line when the persistent memory scrub attribute is added in UCSC SDK and UI
        # self.persistent_memory_scrub = None
        self.descr = None

        if self._config.load_from == "live":
            if compute_scrub_policy is not None:
                self.name = compute_scrub_policy.name
                self.descr = compute_scrub_policy.descr
                self.disk_scrub = compute_scrub_policy.disk_scrub
                self.flexflash_scrub = compute_scrub_policy.flex_flash_scrub
                self.bios_settings_scrub = compute_scrub_policy.bios_settings_scrub
                # uncomment the below line when the persistent memory scrub attribute is added in UCSC SDK and UI
                # self.persistent_memory_scrub = compute_scrub_policy.persistent_memory_scrub

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

        mo_compute_scrub_policy = ComputeScrubPolicy(parent_mo_or_dn=parent_mo, name=self.name,
                                                     disk_scrub=self.disk_scrub,
                                                     bios_settings_scrub=self.bios_settings_scrub,
                                                     flex_flash_scrub=self.flexflash_scrub,
                                                     # uncomment the below line when the persistent memory scrub attribute is added in UCSC SDK and UI
                                                     #  persistent_memory_scrub=self.persistent_memory_scrub,
                                                     descr=self.descr)

        self._handle.add_mo(mo=mo_compute_scrub_policy, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True


class UcsCentralSerialOverLanPolicy(UcsCentralConfigObject):
    _CONFIG_NAME = "Serial Over LAN Policy"
    _CONFIG_SECTION_NAME = "serial_over_lan_policies"
    _UCS_SDK_OBJECT_NAME = "solPolicy"

    def __init__(self, parent=None, json_content=None, sol_policy=None):
        UcsCentralConfigObject.__init__(self, parent=parent, ucs_sdk_object=sol_policy)
        self.name = None
        self.descr = None
        self.speed = None
        self.serial_over_lan_state = None

        if self._config.load_from == "live":
            if sol_policy is not None:
                self.name = sol_policy.name
                self.descr = sol_policy.descr
                self.speed = sol_policy.speed
                self.serial_over_lan_state = sol_policy.admin_state

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):
        detail = str(self.name)
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + detail)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + detail +
                                ", waiting for a commit")

        if hasattr(self._parent, '_dn'):
            parent_mo = self._parent._dn
        else:
            self.logger(level="error",
                        message="Impossible to find the parent dn of " + self._CONFIG_NAME + " : " + str(self.name))
            return False

        mo_sol_policy = SolPolicy(
            parent_mo_or_dn=parent_mo, speed=self.speed, name=self.name, admin_state=self.serial_over_lan_state,
            descr=self.descr
        )

        self._handle.add_mo(mo=mo_sol_policy, modify_present=True)
        if commit:
            detail = str(self.name)
            if self.commit(detail=detail) != True:
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

                # We need to set all values that are not present in the config file to None
                for element in self.qualifications:
                    for value in [
                        "adapter_maximum_capacity", "adapter_pid", "adapter_qualifications", "adapter_type",
                        "block_size", "clock", "cpu_speed", "cpu_stepping", "data_rate", "diskless", "disk_type",
                        "domain_qualifications", "domain_qual_name", "latency", "max_cap", "min_cap", "max_cores",
                        "min_cores", "min_procs", "max_procs", "max_threads", "min_threads", "number_of_blocks",
                        "number_of_flexflash_cards", "per_disk_cap", "processor_architecture", "processor_pid",
                            "server_pid", "type", "units", "width"]:
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


class UcsCentralStorageConnectionPolicy(UcsCentralConfigObject):
    _CONFIG_NAME = "Storage Connection Policy"
    _CONFIG_SECTION_NAME = "storage_connection_policies"
    _UCS_SDK_OBJECT_NAME = "storageConnectionPolicy"

    def __init__(self, parent=None, json_content=None, storage_connection_policy=None):
        UcsCentralConfigObject.__init__(self, parent=parent, ucs_sdk_object=storage_connection_policy)
        self.name = None
        self.descr = None
        self.zoning_type = None
        self.fc_target_endpoints = []

        if self._config.load_from == "live":
            if storage_connection_policy is not None:
                self.name = storage_connection_policy.name
                self.descr = storage_connection_policy.descr
                self.zoning_type = storage_connection_policy.zoning_type
                if self.zoning_type == "simt":
                    self.zoning_type = "single_initiator_multiple_targets"
                elif self.zoning_type == "sist":
                    self.zoning_type = "single_initiator_single_target"

                if "storageFcTargetEp" in self._parent._config.sdk_objects:
                    for fc_target in self._config.sdk_objects["storageFcTargetEp"]:
                        if self._parent._dn:
                            if self._parent._dn + "/storage-connpolicy-" + self.name + '/' in fc_target.dn:
                                target = {}
                                target.update({"wwpn": fc_target.targetwwpn})
                                target.update({"descr": fc_target.descr})
                                target.update({"path": fc_target.path})

                                if "storageVsanRef" in self._parent._config.sdk_objects:
                                    for vsan in self._config.sdk_objects["storageVsanRef"]:
                                        if self._parent._dn + "/storage-connpolicy-" + self.name + '/fc-target-ep-' + \
                                                target["wwpn"] + '/' in vsan.dn:
                                            target.update({"vsan": vsan.name})
                                            break
                                self.fc_target_endpoints.append(target)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

                for element in self.fc_target_endpoints:
                    for value in ["wwpn", "descr", "path", "vsan"]:
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

        zoning_type = self.zoning_type
        if zoning_type == "single_initiator_multiple_targets":
            zoning_type = "simt"
        if zoning_type == "single_initiator_single_target":
            zoning_type = "sist"

        mo_storage_connection_policy = StorageConnectionPolicy(parent_mo_or_dn=parent_mo, name=self.name,
                                                               descr=self.descr, zoning_type=zoning_type)
        self._handle.add_mo(mo=mo_storage_connection_policy, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False

        if self.fc_target_endpoints:
            for target in self.fc_target_endpoints:
                mo_storage_fc_target_ep = StorageFcTargetEp(parent_mo_or_dn=mo_storage_connection_policy,
                                                            targetwwpn=target["wwpn"], descr=target["descr"],
                                                            path=target["path"])
                # Adding the VSAN
                if 'vsan' in target:
                    StorageVsanRef(parent_mo_or_dn=mo_storage_fc_target_ep, name=target['vsan'])

                self._handle.add_mo(mo=mo_storage_connection_policy, modify_present=True)
                if commit:
                    if self.commit(detail=target['wwpn']) != True:
                        continue

        return True


class UcsCentralStorageProfile(UcsCentralConfigObject):
    _CONFIG_NAME = "Storage Profile"
    _CONFIG_SECTION_NAME = "storage_profiles"
    _UCS_SDK_OBJECT_NAME = "lstorageProfile"
    _UCS_SDK_SPECIFIC_OBJECT_NAME = "lstorageProfileDef"
    _POLICY_MAPPING_TABLE = {
        "local_luns": [
            {
                "disk_group_policy": UcsCentralDiskGroupPolicy
            }
        ]
    }

    def __init__(self, parent=None, json_content=None, lstorage_profile=None):
        UcsCentralConfigObject.__init__(self, parent=parent, ucs_sdk_object=lstorage_profile)
        self.name = None
        self.descr = None
        # auto_config_mode and lun_sets are not available in UCS Central UI and ucsc SDK same have commented the code,
        # Wherever the attributes are present
        # self.auto_config_mode = None
        self.security_policy = []
        self.local_luns = []
        # self.lun_sets = []
        self.controller_definitions = []

        if self._config.load_from == "live":
            if lstorage_profile is not None:
                self.name = lstorage_profile.name
                self.descr = lstorage_profile.descr
                # self.auto_config_mode = lstorage_profile.auto_config_mode

                if self._parent._dn:
                    if self._parent.__class__.__name__ == "UcsCentralServiceProfile":
                        # We are in presence of a Specific Storage Policy under a Service Profile object
                        self.name = None
                        storage_policy_dn = self._parent._dn + "/profile-def" + "/"
                    else:
                        storage_policy_dn = self._parent._dn + "/profile-" + self.name + "/"

                # Need to test security policy of type "remote" having the valid kmip_server_public_certificate.
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
                                # deployed_key not present in UCS Central UI but ucsc sdk is present
                                policy.update({"deployed_key": remote_policy.deployed_security_key})
                                policy.update({"timeout": remote_policy.timeout})
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

                # if "lstorageLunSetConfig" in self._parent._config.sdk_objects:
                #     for lun_set_config in self._config.sdk_objects["lstorageLunSetConfig"]:
                #         if self._parent._dn:
                #             if storage_policy_dn in lun_set_config.dn:
                #                 lun_set = {}
                #                 lun_set.update({"name": lun_set_config.name})
                #                 lun_set.update({"raid_level": lun_set_config.raid_level})
                #                 lun_set.update({"disk_slot_range": lun_set_config.disk_slot_range})
                #                 if "lstorageVirtualDriveDef" in self._parent._config.sdk_objects:
                #                     for lsstorage in self._config.sdk_objects["lstorageVirtualDriveDef"]:
                #                         if lun_set_config.dn in lsstorage.dn:
                #                             lun_set.update({"strip_size": lsstorage.strip_size})
                #                             lun_set.update({"access_policy": lsstorage.access_policy})
                #                             lun_set.update({"read_policy": lsstorage.read_policy})
                #                             lun_set.update({"write_cache_policy": lsstorage.write_cache_policy})
                #                             lun_set.update({"io_policy": lsstorage.io_policy})
                #                             lun_set.update({"drive_cache": lsstorage.drive_cache})
                #                             lun_set.update({"security": lsstorage.security})
                #                             break
                #                 self.lun_sets.append(lun_set)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

                # We need to set all values that are not present in the config file to None
                for element in self.security_policy:
                    for value in ["primary_ip_address", "secondary_ip_address", "port", "timeout",
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
                            else:
                                for value in ["name", "org"]:
                                    if value not in element["operational_state"][policy]:
                                        element["operational_state"][policy][value] = None
                for element in self.controller_definitions:
                    for value in ["name", "protected_configuration", "raid_level"]:
                        if value not in element:
                            element[value] = None
                # for element in self.lun_sets:
                #     for value in ["name", "disk_slot_range", "raid_level", "strip_size", "access_policy", "read_policy",
                #                   "write_cache_policy", "io_policy", "drive_cache", "security"]:
                #         if value not in element:
                #             element[value] = None

        self.clean_object()

    def push_object(self, commit=True):
        detail = str(self.name)
        if self._parent.__class__.__name__ == "UcsCentralServiceProfile":
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

        if self._parent.__class__.__name__ == "UcsCentralServiceProfile":
            pass
            # We are in presence of a Specific Storage Policy under a Service Profile object
            mo_lstorage_profile = LstorageProfileDef(
                # parent_mo_or_dn=parent_mo, descr=self.descr, auto_config_mode=self.auto_config_mode)
                parent_mo_or_dn=parent_mo, descr=self.descr)
        else:
            # We are in presence of a regular Storage Policy under an Org object
            mo_lstorage_profile = LstorageProfile(
                # parent_mo_or_dn=parent_mo, name=self.name, descr=self.descr, auto_config_mode=self.auto_config_mode)
                parent_mo_or_dn=parent_mo, name=self.name, descr=self.descr)

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
                                               deployed_security_key=policy['deployed_key'],
                                               timeout=policy["timeout"])
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

        # if self.lun_sets:
        #     for lun_set in self.lun_sets:
        #         mo_ls_storage_lun_set_config = LstorageLunSetConfig(parent_mo_or_dn=mo_lstorage_profile,
        #                                                             disk_slot_range=lun_set['disk_slot_range'],
        #                                                             name=lun_set['name'])
        #         LstorageVirtualDriveDef(parent_mo_or_dn=mo_ls_storage_lun_set_config,
        #                                 access_policy=lun_set['access_policy'],
        #                                 drive_cache=lun_set['drive_cache'],
        #                                 io_policy=lun_set['io_policy'],
        #                                 read_policy=lun_set['read_policy'],
        #                                 security=lun_set['security'],
        #                                 strip_size=lun_set['strip_size'],
        #                                 write_cache_policy=lun_set['write_cache_policy'])

        self._handle.add_mo(mo=mo_lstorage_profile, modify_present=True)

        if commit:
            detail = str(self.name)
            if self._parent.__class__.__name__ == "UcsCentralServiceProfile":
                # We are in presence of a Specific Storage Policy under a Service Profile object
                detail = "Service Profile " + str(self._parent.name)
            if self.commit(detail=detail) != True:
                return False
        return True


class UcsCentralThresholdPolicy(UcsCentralConfigObject):
    _CONFIG_NAME = "Threshold Policy"
    _CONFIG_SECTION_NAME = "threshold_policies"
    _UCS_SDK_OBJECT_NAME = "statsThresholdPolicy"

    def __init__(self, parent=None, json_content=None, stats_threshold_policy=None):
        UcsCentralConfigObject.__init__(self, parent=parent, ucs_sdk_object=stats_threshold_policy)
        self.name = None
        self.descr = None
        self.threshold_classes = []

        # Open JSON configuration file
        self._model_table = read_json_file(file_path="config/ucs/ucsc/threshold_policies_table.json", logger=self)
        if not self._model_table:
            self.logger(level="error", message="Unable to load threshold_policies_table.json file")
            self._model_table = {}

        if self._config.load_from == "live":
            if stats_threshold_policy is not None:

                self.name = stats_threshold_policy.name
                self.descr = stats_threshold_policy.descr
                # Dictionary for mapping definition type and vlaue
                definition_value_dict = {
                    "statsThr32Definition": "statsThr32Value",
                    "statsThr64Definition": "statsThr64Value",
                    "statsThrFloatDefinition": "statsThrFloatValue"
                }
                if "statsThresholdClass" in self._parent._config.sdk_objects:
                    for thr_class in self._config.sdk_objects["statsThresholdClass"]:
                        if self._parent._dn:
                            if self._parent._dn + "/thr-policy-" + self.name + "/" in thr_class.dn:
                                stat_thr_class = {}

                                # Find group and Model statistic class
                                # Eg: group is adaptor Class and Model class is (adaptor)EthPortBySizeLargeStats.
                                group = ""
                                stat_class = ""
                                for model_group in self._model_table:
                                    for model_stat_class, model_stat_class_values in \
                                            self._model_table[model_group].items():
                                        if model_stat_class_values["name"] == thr_class.stats_class_id:
                                            group = model_group
                                            stat_class = model_stat_class
                                            break
                                    if stat_class:
                                        break

                                stat_thr_class.update({"group": group})
                                stat_thr_class.update({"stat_class": stat_class})
                                stat_thr_class.update({"threshold_definitions": []})

                                for model_property_type, model_property_type_sdk in \
                                        self._model_table[group][stat_class]["values"].items():
                                    model_property_definition = self._model_table[group][stat_class]["types"][
                                        model_property_type + "_type"]
                                    if model_property_definition in self._parent._config.sdk_objects:
                                        for thr_def in self._config.sdk_objects[model_property_definition]:
                                            if self._parent._dn:
                                                if self._parent._dn + "/thr-policy-" + self.name + "/" + \
                                                        thr_class.stats_class_id + "/" in thr_def.dn:
                                                    thr_32 = {}
                                                    # Finding properties_type from each model class
                                                    # Eg: less_than2048_delta is property_type of (adaptor)EthPortBySizeLargeStats.
                                                    property_type = ""
                                                    if model_property_type_sdk == thr_def.prop_id:
                                                        property_type = model_property_type
                                                        thr_32.update({"property_type": property_type})
                                                        thr_32.update(
                                                            {"normal_value": thr_def.normal_value.split('.')[0]})
                                                        thr_32.update({"alarm_triggers_above": []})
                                                        thr_32.update({"alarm_triggers_below": []})

                                                        # Checking if property_type has any definition specified.
                                                        # Eg: property_type less_than2048_delta can have definiton set for alarm (above or below normal value).
                                                        if definition_value_dict[model_property_definition] in self._parent._config.sdk_objects:
                                                            for thr_val in self._config.sdk_objects[definition_value_dict[model_property_definition]]:
                                                                if self._parent._dn:
                                                                    if self._parent._dn + "/thr-policy-" + self.name + "/" \
                                                                            + thr_class.stats_class_id + "/" + \
                                                                            thr_def.prop_id + "/" in thr_val.dn:
                                                                        val_32 = {}
                                                                        val_32.update({"severity": thr_val.severity})
                                                                        val_32.update(
                                                                            {"down": thr_val.deescalating.split('.')[0]})
                                                                        val_32.update(
                                                                            {"up": thr_val.escalating.split('.')[0]})
                                                                        if thr_val.direction == "aboveNormal":
                                                                            thr_32["alarm_triggers_above"].append(
                                                                                val_32)
                                                                        elif thr_val.direction == "belowNormal":
                                                                            thr_32["alarm_triggers_below"].append(
                                                                                val_32)
                                                        stat_thr_class["threshold_definitions"].append(thr_32)
                                self.threshold_classes.append(stat_thr_class)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

                for element in self.threshold_classes:
                    for value in ["stat_class", "threshold_definitions", "group"]:
                        if value not in element:
                            element[value] = None
                    if element["threshold_definitions"]:
                        for subelement in element["threshold_definitions"]:
                            for subvalue in ["property_type", "normal_value",
                                             "alarm_triggers_above", "alarm_triggers_below"]:
                                if subvalue not in subelement:
                                    subelement[subvalue] = None
                            if subelement["alarm_triggers_above"]:
                                for subsubelement in subelement["alarm_triggers_above"]:
                                    for subsubvalue in ["severity", "up", "down"]:
                                        if subsubvalue not in subsubelement:
                                            subsubelement[subsubvalue] = None
                            if subelement["alarm_triggers_below"]:
                                for subsubelement in subelement["alarm_triggers_below"]:
                                    for subsubvalue in ["severity", "up", "down"]:
                                        if subsubvalue not in subsubelement:
                                            subsubelement[subsubvalue] = None

        self.clean_object()

    def push_object(self, commit=True):
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + str(self.name))
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration" +
                                ", waiting for a commit")

        if hasattr(self._parent, '_dn'):
            parent_mo = self._parent._dn
        else:
            self.logger(level="error", message="Impossible to find the parent dn of " + self._CONFIG_NAME)
            return False

        mo_stats_threshold_policy = StatsThresholdPolicy(parent_mo_or_dn=parent_mo, descr=self.descr,
                                                         name=self.name)
        for thr_class in self.threshold_classes:

            stats_class_id = self._model_table[thr_class["group"]
                                               ][thr_class["stat_class"]]["name"]

            mo_stats_threshold_class = StatsThresholdClass(parent_mo_or_dn=mo_stats_threshold_policy,
                                                           stats_class_id=stats_class_id)

            if thr_class["threshold_definitions"]:
                for definition in thr_class["threshold_definitions"]:
                    prop_id = self._model_table[thr_class["group"]][thr_class["stat_class"]]["values"][
                        definition["property_type"]]
                    prop_definition_type = self._model_table[thr_class["group"]][thr_class["stat_class"]]["types"][
                        definition["property_type"] + "_type"]

                    # Mapping Definition type and Value type for each property.
                    StatsDefinition = ""
                    StatsValue = ""
                    if prop_definition_type == "statsThrFloatDefinition":
                        StatsDefinition = StatsThrFloatDefinition
                        StatsValue = StatsThrFloatValue
                    elif prop_definition_type == "statsThr64Definition":
                        StatsDefinition = StatsThr64Definition
                        StatsValue = StatsThr64Value
                    elif prop_definition_type == "statsThr32Definition":
                        StatsDefinition = StatsThr32Definition
                        StatsValue = StatsThr32Value

                    if StatsDefinition:
                        mo_stats_thr_32_def = StatsDefinition(parent_mo_or_dn=mo_stats_threshold_class,
                                                              normal_value=definition["normal_value"],
                                                              prop_id=prop_id)
                    if StatsValue:
                        for alarm_trigger_type in ["alarm_triggers_above", "alarm_triggers_below"]:
                            alarm_direction = alarm_trigger_type.split('_')[2] + "Normal"
                            if definition[alarm_trigger_type]:
                                severity_added = []
                                for alarm in definition[alarm_trigger_type]:
                                    if alarm["severity"] not in severity_added:
                                        StatsValue(parent_mo_or_dn=mo_stats_thr_32_def,
                                                   deescalating=alarm["down"],
                                                   escalating=alarm["up"],
                                                   severity=alarm["severity"],
                                                   direction=alarm_direction)
                                        severity_added.append(alarm["severity"])
                                    else:
                                        # Ignore duplicate entry for Definition type severity.
                                        self.logger(message="Ignoring duplicate entry in {0} for {1} {2} component {3}".format(
                                            alarm_trigger_type, self._CONFIG_NAME, str(self.name), definition["property_type"]))

        self._handle.add_mo(mo=mo_stats_threshold_policy, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True


class UcsCentralUdldLinkPolicy(UcsCentralConfigObject):
    _CONFIG_NAME = "UDLD Link Policy"
    _CONFIG_SECTION_NAME = "udld_link_policies"
    _UCS_SDK_OBJECT_NAME = "fabricUdldLinkPolicy"

    def __init__(self, parent=None, json_content=None, fabric_udld_link_policy=None):
        UcsCentralConfigObject.__init__(self, parent=parent, ucs_sdk_object=fabric_udld_link_policy)
        self.name = None
        self.descr = None
        self.mode = None
        self.admin_state = None

        if self._config.load_from == "live":
            if fabric_udld_link_policy is not None:
                self.name = fabric_udld_link_policy.name
                self.descr = fabric_udld_link_policy.descr
                self.mode = fabric_udld_link_policy.mode
                self.admin_state = fabric_udld_link_policy.admin_state

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

        parent_mo = self._parent._dn
        mo_fabric_udld_link_policy = FabricUdldLinkPolicy(
            parent_mo_or_dn=parent_mo, mode=self.mode, admin_state=self.admin_state, name=self.name, descr=self.descr)

        self._handle.add_mo(mo=mo_fabric_udld_link_policy, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True


class UcsCentralUsnicConnectionPolicy(UcsCentralConfigObject):
    _CONFIG_NAME = "usNIC Connection Policy"
    _CONFIG_SECTION_NAME = "usnic_connection_policies"
    _UCS_SDK_OBJECT_NAME = "vnicUsnicConPolicy"

    def __init__(self, parent=None, json_content=None, vnic_usnic_con_policy=None):
        UcsCentralConfigObject.__init__(self, parent=parent, ucs_sdk_object=vnic_usnic_con_policy)
        self.name = None
        self.descr = None
        self.number_of_usnics = None
        self.adapter_policy = None

        if self._config.load_from == "live":
            if vnic_usnic_con_policy is not None:
                self.name = vnic_usnic_con_policy.name
                self.descr = vnic_usnic_con_policy.descr
                self.number_of_usnics = vnic_usnic_con_policy.usnic_count
                self.adapter_policy = vnic_usnic_con_policy.adaptor_profile_name

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
                        message="Impossible to find the parent dn of " + self._CONFIG_NAME + " : " + self.name)
            return False

        mo_vnic_usnic_con_policy = VnicUsnicConPolicy(parent_mo_or_dn=parent_mo, descr=self.descr, name=self.name,
                                                      usnic_count=self.number_of_usnics,
                                                      adaptor_profile_name=self.adapter_policy)

        self._handle.add_mo(mo=mo_vnic_usnic_con_policy, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False


class UcsCentralVmediaPolicy(UcsCentralConfigObject):
    _CONFIG_NAME = "vMedia Policy"
    _CONFIG_SECTION_NAME = "vmedia_policies"
    _UCS_SDK_OBJECT_NAME = "cimcvmediaMountConfigPolicy"
    _UCS_SDK_SPECIFIC_OBJECT_NAME = "cimcvmediaMountConfigDef"

    def __init__(self, parent=None, json_content=None, cimcvmedia_mount_config_policy=None):
        UcsCentralConfigObject.__init__(self, parent=parent, ucs_sdk_object=cimcvmedia_mount_config_policy)
        self.descr = None
        self.name = None
        self.retry_on_mount_fail = None
        self.vmedia_mounts = []

        if self._config.load_from == "live":
            if cimcvmedia_mount_config_policy is not None:
                self.name = cimcvmedia_mount_config_policy.name
                self.descr = cimcvmedia_mount_config_policy.descr
                self.retry_on_mount_fail = cimcvmedia_mount_config_policy.retry_on_mount_fail

                if "cimcvmediaConfigMountEntry" in self._parent._config.sdk_objects:
                    for cimcvmedia in self._config.sdk_objects["cimcvmediaConfigMountEntry"]:
                        if self._parent._dn:
                            if self._parent.__class__.__name__ == "UcsCentralServiceProfile":
                                # We are in presence of a Specific Boot Policy under a Service Profile object
                                vmedia_policy_dn = self._parent._dn + "/mnt-cfg-def/"
                                self.name = None
                            else:
                                # We are in presence of a regular Boot Policy under an Org object
                                vmedia_policy_dn = self._parent._dn + "/mnt-cfg-policy-" + self.name + "/"
                            if vmedia_policy_dn in cimcvmedia.dn:
                                user = {}
                                user.update({"device_type": cimcvmedia.device_type})
                                user.update({"protocol": cimcvmedia.mount_protocol})
                                user.update({"name": cimcvmedia.mapping_name})
                                # description option is not available in Central UI same is available in ucsc sdk
                                # user.update({"descr": cimcvmedia.description})
                                user.update({"username": cimcvmedia.user_id})
                                user.update({"password": cimcvmedia.password})
                                user.update({"image_name_variable": cimcvmedia.image_name_variable})
                                user.update({"remote_file": cimcvmedia.image_file_name})
                                user.update({"remote_path": cimcvmedia.image_path})
                                user.update({"hostname": cimcvmedia.remote_ip_address})
                                user.update({"authentication_protocol": cimcvmedia.auth_option})
                                # remap_on_eject and writable options are not available in UI and ucsc sdk
                                # user.update({"remap_on_eject": cimcvmedia.remap_on_eject})
                                # user.update({"writable": cimcvmedia.writable})
                                self.vmedia_mounts.append(user)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

                # We need to set all values that are not present in the config file to None
                for element in self.vmedia_mounts:
                    for value in ["device_type", "password", "username", "descr", "protocol", "name", "remote_file",
                                  "remote_path", "hostname", "image_name_variable", "authentication_protocol"
                                  ]:
                        if value not in element:
                            element[value] = None

        self.clean_object()

    def push_object(self, commit=True):
        detail = str(self.name)
        if self._parent.__class__.__name__ == "UcsCentralServiceProfile":
            # We are in presence of a Specific vMedia Policy under a Service Profile object
            detail = "Service Profile " + str(self._parent.name)
        if commit:
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration: " + detail)
        else:
            self.logger(message="Adding to the handle " + self._CONFIG_NAME + " configuration: " + detail +
                                ", waiting for a commit")

        if hasattr(self._parent, '_dn'):
            parent_mo = self._parent._dn
        else:
            self.logger(level="error",
                        message="Impossible to find the parent dn of " + self._CONFIG_NAME + " : " + str(self.name))
            return False

        if self._parent.__class__.__name__ == "UcsCentralServiceProfile":
            # We are in presence of a Specific vMedia Policy under a Service Profile object
            mo_cimcvmedia_mount_config_policy = CimcvmediaMountConfigDef(
                parent_mo_or_dn=parent_mo, retry_on_mount_fail=self.retry_on_mount_fail, descr=self.descr
            )
        else:
            # We are in presence of a regular vMedia Policy under an Org object
            mo_cimcvmedia_mount_config_policy = CimcvmediaMountConfigPolicy(
                parent_mo_or_dn=parent_mo, name=self.name, retry_on_mount_fail=self.retry_on_mount_fail,
                descr=self.descr
            )

        for media in self.vmedia_mounts:
            # We first fetch the mandatory attributes
            media_name = media['name']
            hostname = media['hostname']
            file_path = media['remote_path']

            descr = None
            if 'descr' in media:
                descr = media['descr']
            device_type = None
            if "device_type" in media:
                device_type = media['device_type']
            protocol = None
            if "protocol" in media:
                protocol = media['protocol']

            username = ""
            pwd = ""
            if protocol not in ["nfs"]:
                if "username" in media:
                    username = media['username']
                if "password" in media:
                    pwd = media['password']

            file_name = ""
            if "remote_file" in media:
                file_name = media['remote_file']

            inv = None
            if "image_name_variable" in media:
                inv = media['image_name_variable']
            if inv not in ["none", None]:
                file_name = ""

            # remap_on_eject = None
            # if "remap_on_eject" in media:
            #     remap_on_eject = media['remap_on_eject']

            authentication_protocol = None
            if "authentication_protocol" in media:
                authentication_protocol = media['authentication_protocol']

            # writable = None
            # if protocol in ["cifs", "nfs"] and device_type in ["hdd"]:
            #     if 'writable' in media:
            #         writable = media['writable']

            CimcvmediaConfigMountEntry(parent_mo_or_dn=mo_cimcvmedia_mount_config_policy, mapping_name=media_name,
                                       device_type=device_type, image_file_name=file_name, image_name_variable=inv,
                                       image_path=file_path, mount_protocol=protocol, user_id=username, password=pwd,
                                       remote_ip_address=hostname, description=descr,
                                       # remap_on_eject=remap_on_eject,
                                       auth_option=authentication_protocol)
            # writable=writable)

        self._handle.add_mo(mo=mo_cimcvmedia_mount_config_policy, modify_present=True)
        if commit:
            detail = str(self.name)
            if self._parent.__class__.__name__ == "UcsCentralServiceProfile":
                # We are in presence of a Specific vMedia Policy under a Service Profile object
                detail = "Service Profile " + str(self._parent.name)
            if self.commit(detail=detail) != True:
                return False
        return True


class UcsCentralVmqConnectionPolicy(UcsCentralConfigObject):
    _CONFIG_NAME = "VMQ Connection Policy"
    _CONFIG_SECTION_NAME = "vmq_connection_policies"
    _UCS_SDK_OBJECT_NAME = "vnicVmqConPolicy"

    def __init__(self, parent=None, json_content=None, vnic_vmq_con_policy=None):
        UcsCentralConfigObject.__init__(self, parent=parent, ucs_sdk_object=vnic_vmq_con_policy)
        self.name = None
        self.descr = None
        self.multi_queue = None
        self.number_of_sub_vnics = None
        self.number_of_vmqs = None
        self.number_of_interrupts = None
        self.adapter_policy = None

        if self._config.load_from == "live":
            if vnic_vmq_con_policy is not None:
                self.name = vnic_vmq_con_policy.name
                self.descr = vnic_vmq_con_policy.descr
                self.multi_queue = vnic_vmq_con_policy.multi_queue
                if self.multi_queue in ["disabled"]:
                    self.number_of_vmqs = vnic_vmq_con_policy.vmq_count
                    self.number_of_interrupts = vnic_vmq_con_policy.intr_count
                elif self.multi_queue in ["enabled"]:
                    self.adapter_policy = vnic_vmq_con_policy.adaptor_profile_name
                    self.number_of_sub_vnics = vnic_vmq_con_policy.vmmq_sub_vnics

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
                        message="Impossible to find the parent dn of " + self._CONFIG_NAME + " : " + self.name)
            return False

        mo_vnic_vmq_con_policy = VnicVmqConPolicy(parent_mo_or_dn=parent_mo, descr=self.descr, name=self.name,
                                                  multi_queue=self.multi_queue,
                                                  adaptor_profile_name=self.adapter_policy,
                                                  intr_count=self.number_of_interrupts,
                                                  vmmq_sub_vnics=self.number_of_sub_vnics,
                                                  vmq_count=self.number_of_vmqs)

        self._handle.add_mo(mo=mo_vnic_vmq_con_policy, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False


class UcsCentralLanConnectivityPolicy(UcsCentralConfigObject):
    _CONFIG_NAME = "LAN Connectivity Policy"
    _CONFIG_SECTION_NAME = "lan_connectivity_policies"
    _UCS_SDK_OBJECT_NAME = "vnicLanConnPolicy"
    _POLICY_MAPPING_TABLE = {
        "vnics": [
            {
                "adapter_policy": UcsCentralEthernetAdapterPolicy,
                "mac_address_pool": UcsCentralMacPool,
                "network_control_policy": UcsCentralNetworkControlPolicy,
                "pin_group": None,
                "qos_policy": UcsCentralQosPolicy,
                "stats_threshold_policy": UcsCentralThresholdPolicy,
                "vnic_template": UcsCentralVnicTemplate
            }
        ]
    }

    def __init__(self, parent=None, json_content=None, vnic_lan_conn_policy=None):
        UcsCentralConfigObject.__init__(self, parent=parent, ucs_sdk_object=vnic_lan_conn_policy)
        self.name = None
        self.descr = None
        self.vnics = []
        self.iscsi_vnics = []

        if self._config.load_from == "live":
            if vnic_lan_conn_policy is not None:
                self.name = vnic_lan_conn_policy.name
                self.descr = vnic_lan_conn_policy.descr

                if "vnicEther" in self._parent._config.sdk_objects:
                    for vnic_ether in self._config.sdk_objects["vnicEther"]:
                        if self._parent._dn:
                            if self._parent._dn + "/lan-conn-pol-" + self.name + "/" in vnic_ether.dn:
                                oper_state = {}
                                vnic = {"_object_type": "vnics"}
                                vnic.update({"name": vnic_ether.name})
                                vnic.update({"adapter_policy": vnic_ether.adaptor_profile_name})
                                vnic.update({"order": vnic_ether.order})

                                if vnic_ether.nw_templ_name:
                                    vnic.update({"vnic_template": vnic_ether.nw_templ_name})
                                    vnic.update({"redundancy_pair": vnic_ether.redundancy_pair_type})
                                else:
                                    vnic.update({"fabric": vnic_ether.switch_id})
                                    vnic.update({"mac_address_pool": vnic_ether.ident_pool_name})
                                    if not vnic_ether.ident_pool_name and vnic_ether.addr == "derived":
                                        vnic.update({"mac_address": "hardware-default"})
                                    vnic.update({"mtu": vnic_ether.mtu})
                                    vnic.update({"qos_policy": vnic_ether.qos_policy_name})
                                    vnic.update({"network_control_policy": vnic_ether.nw_ctrl_policy_name})
                                    vnic.update({"cdn_source": vnic_ether.cdn_source})
                                    vnic.update({"cdn_name": vnic_ether.admin_cdn_name})
                                    vnic.update({"stats_threshold_policy": vnic_ether.stats_policy_name})
                                    vnic.update({"dynamic_vnic_connection_policy": None})
                                    vnic.update({"usnic_connection_policy": None})
                                    vnic.update({"vmq_connection_policy": None})
                                    if "vnicDynamicConPolicyRef" in self._parent._config.sdk_objects:
                                        for conn_policy in self._config.sdk_objects["vnicDynamicConPolicyRef"]:

                                            if self._parent._dn + "/lan-conn-pol-" + self.name + '/ether-' + \
                                                    vnic['name'] + '/' in conn_policy.dn:
                                                vnic.update(
                                                    {"dynamic_vnic_connection_policy": conn_policy.con_policy_name})
                                                # Added the operational state of connection policy for manual type
                                                oper_state.update(
                                                    self.get_operational_state(
                                                        policy_dn=conn_policy.oper_con_policy_name,
                                                        separator="/dynamic-con-",
                                                        policy_name="dynamic_vnic_connection_policy"
                                                    )
                                                )
                                                break
                                    if "vnicUsnicConPolicyRef" in self._parent._config.sdk_objects \
                                            and not vnic['usnic_connection_policy']:
                                        for conn_policy in self._config.sdk_objects["vnicUsnicConPolicyRef"]:
                                            if self._parent._dn + "/lan-conn-pol-" + self.name + '/ether-' + \
                                                    vnic['name'] + '/' in conn_policy.dn:
                                                vnic.update({"usnic_connection_policy": conn_policy.con_policy_name})
                                                # Added the operational state of connection policy for manual type
                                                oper_state.update(
                                                    self.get_operational_state(
                                                        policy_dn=conn_policy.oper_con_policy_name,
                                                        separator="/usnic-con-",
                                                        policy_name="usnic_connection_policy"
                                                    )
                                                )
                                                break
                                    if "vnicVmqConPolicyRef" in self._parent._config.sdk_objects \
                                            and not vnic['vmq_connection_policy']:
                                        for conn_policy in self._config.sdk_objects["vnicVmqConPolicyRef"]:
                                            if self._parent._dn + "/lan-conn-pol-" + self.name + '/ether-' + \
                                                    vnic['name'] + '/' in conn_policy.dn:
                                                vnic.update({"vmq_connection_policy": conn_policy.con_policy_name})
                                                # Added the operational state of connection policy for manual type
                                                oper_state.update(
                                                    self.get_operational_state(
                                                        policy_dn=conn_policy.oper_con_policy_name,
                                                        separator="/vmq-con-",
                                                        policy_name="vmq_connection_policy"
                                                    )
                                                )
                                                break

                                    if "vnicEtherIf" in self._parent._config.sdk_objects:
                                        vnic.update({"vlans": []})
                                        for vnic_ether_if in self._config.sdk_objects["vnicEtherIf"]:
                                            if self._parent._dn + "/lan-conn-pol-" + self.name + '/ether-' + \
                                                    vnic['name'] + '/' in vnic_ether_if.dn:
                                                if vnic_ether_if.default_net == "yes":
                                                    vnic.update({"vlan_native": vnic_ether_if.name})
                                                else:
                                                    vnic['vlans'].append(vnic_ether_if.name)

                                    if "fabricNetGroupRef" in self._parent._config.sdk_objects:
                                        vnic.update({"vlan_groups": []})
                                        for fabric_net_group_ref in self._config.sdk_objects["fabricNetGroupRef"]:
                                            if self._parent._dn + "/lan-conn-pol-" + self.name + '/ether-' + \
                                                    vnic['name'] + '/' in fabric_net_group_ref.dn:
                                                vnic['vlan_groups'].append(fabric_net_group_ref.name)

                                # Fetching the operational state of the referenced policies
                                oper_state.update(
                                    self.get_operational_state(
                                        policy_dn=vnic_ether.oper_adaptor_profile_name,
                                        separator="/eth-profile-",
                                        policy_name="adapter_policy"
                                    )
                                )
                                oper_state.update(
                                    self.get_operational_state(
                                        policy_dn=vnic_ether.oper_nw_ctrl_policy_name,
                                        separator="/nwctrl-",
                                        policy_name="network_control_policy"
                                    )
                                )
                                oper_state.update(
                                    self.get_operational_state(
                                        policy_dn=vnic_ether.oper_qos_policy_name,
                                        separator="/ep-qos-",
                                        policy_name="qos_policy"
                                    )
                                )
                                oper_state.update(
                                    self.get_operational_state(
                                        policy_dn=vnic_ether.oper_stats_policy_name,
                                        separator="/thr-policy-",
                                        policy_name="stats_threshold_policy"
                                    )
                                )
                                oper_state.update(
                                    self.get_operational_state(
                                        policy_dn=vnic_ether.oper_nw_templ_name,
                                        separator="/lan-conn-templ-",
                                        policy_name="vnic_template"
                                    )
                                )

                                vnic['operational_state'] = oper_state

                                self.vnics.append(vnic)

                if "vnicIScsiLCP" in self._parent._config.sdk_objects:
                    for vnic_iscsi_lcp in self._config.sdk_objects["vnicIScsiLCP"]:
                        if self._parent._dn:
                            if self._parent._dn + "/lan-conn-pol-" + self.name + "/" in vnic_iscsi_lcp.dn:
                                oper_state = {}
                                vnic = {"_object_type": "iscsi_vnics"}
                                # Additional pools/policies in iscsi vnic compared to UCSM
                                # ip pool
                                # iqn pool
                                # authentication profile policy

                                # missing fetching of fabric in UCSM
                                # vnic.update({"fabric": vnic_iscsi_lcp.switch_id})  # ["A", "B", "NONE", "mgmt"]
                                vnic.update({"name": vnic_iscsi_lcp.name})
                                vnic.update({"overlay_vnic": vnic_iscsi_lcp.vnic_name})
                                vnic.update({"iscsi_adapter_policy": vnic_iscsi_lcp.adaptor_profile_name})
                                vnic.update({"mac_address_pool": vnic_iscsi_lcp.ident_pool_name})

                                if "vnicVlan" in self._parent._config.sdk_objects:
                                    for vnicvlan in self._config.sdk_objects["vnicVlan"]:
                                        if self._parent._dn + "/lan-conn-pol-" + self.name + '/iscsi-' + \
                                                vnic['name'] + '/' in vnicvlan.dn:
                                            vnic.update({"vlan": vnicvlan.vlan_name})
                                            break

                                # Added the fetch code for ip_pool ,iqn_pool and authentication_profile
                                if "vnicIPv4PooledIscsiAddr" in self._parent._config.sdk_objects:
                                    for vnicippool in self._config.sdk_objects["vnicIPv4PooledIscsiAddr"]:
                                        if self._parent._dn + "/lan-conn-pol-" + self.name + '/iscsi-' + \
                                                vnic['name'] + '/' in vnicippool.dn:
                                            vnic.update({"ip_pool": vnicippool.ident_pool_name})
                                            break
                                if "vnicIScsiBootVnic" in self._parent._config.sdk_objects:
                                    for vnic_iscsi_boot_vnic in self._config.sdk_objects["vnicIScsiBootVnic"]:
                                        if self._parent._dn + "/lan-conn-pol-" + self.name + '/iscsi-' + \
                                                vnic['name'] + '/' in vnic_iscsi_boot_vnic.dn:
                                            vnic.update({"iqn_pool": vnic_iscsi_boot_vnic.iqn_ident_pool_name})
                                            vnic.update(
                                                {"authentication_profile": vnic_iscsi_boot_vnic.auth_profile_name})
                                            oper_state.update(
                                                self.get_operational_state(
                                                    policy_dn=vnic_iscsi_boot_vnic.oper_auth_profile_name,
                                                    separator="/iscsi-auth-profile-",
                                                    policy_name="authentication_profile"
                                                )
                                            )
                                            break

                                oper_state.update(
                                    self.get_operational_state(
                                        policy_dn=vnic_iscsi_lcp.oper_adaptor_profile_name,
                                        separator="/iscsi-profile-",
                                        policy_name="iscsi_adapter_policy"
                                    )
                                )
                                vnic['operational_state'] = oper_state

                                self.iscsi_vnics.append(vnic)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

                for element in self.vnics:
                    for value in ["adapter_policy", "cdn_name", "cdn_source", "dynamic_vnic_connection_policy",
                                  "fabric", "mac_address", "mac_address_pool", "mtu", "name", "network_control_policy",
                                  "order", "operational_state", "pin_group", "qos_policy", "redundancy_pair",
                                  "stats_threshold_policy", "usnic_connection_policy", "vlans", "vlan_groups",
                                  "vlan_native", "vmq_connection_policy", "vnic_template"]:
                        if value not in element:
                            element[value] = None

                    for policy in ["adapter_policy", "mac_address_pool", "network_control_policy",
                                   "qos_policy", "stats_threshold_policy", "vnic_template"]:
                        if element["operational_state"]:
                            if policy not in element["operational_state"]:
                                element["operational_state"][policy] = None
                            else:
                                for value in ["name", "org"]:
                                    if value not in element["operational_state"][policy]:
                                        element["operational_state"][policy][value] = None

                    # Flagging this as a vNIC
                    element["_object_type"] = "vnics"

                for element in self.iscsi_vnics:
                    # Added  ip_pool, iqn_pool and authentication_profile into the list
                    for value in ["vlan", "mac_address_pool", "ip_pool", "iqn_pool", "overlay_vnic", "name",
                                  "iscsi_adapter_policy", "authentication_profile", "operational_state"]:
                        if value not in element:
                            element[value] = None

                    for policy in ["iscsi_adapter_policy", "authentication_profile"]:
                        if element["operational_state"]:
                            if policy not in element["operational_state"]:
                                element["operational_state"][policy] = None
                            else:
                                for value in ["name", "org"]:
                                    if value not in element["operational_state"][policy]:
                                        element["operational_state"][policy][value] = None
                    # Flagging this as a iSCSI_vNIC
                    element["_object_type"] = "iscsi_vnics"

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

        mo_vnic_lan_conn_policy = VnicLanConnPolicy(parent_mo_or_dn=parent_mo, name=self.name, descr=self.descr)
        self._handle.add_mo(mo=mo_vnic_lan_conn_policy, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False

        if self.vnics:
            for vnic in self.vnics:
                if vnic['vnic_template']:
                    mo_vnic_ether = VnicEther(parent_mo_or_dn=mo_vnic_lan_conn_policy,
                                              adaptor_profile_name=vnic['adapter_policy'],
                                              nw_templ_name=vnic['vnic_template'],
                                              # redundancy_pair_type=vnic['redundancy_pair'],
                                              name=vnic['name'],
                                              order=vnic['order'])
                    self._handle.add_mo(mo=mo_vnic_ether, modify_present=True)
                    # We need to commit the interface first and then add the vlan and connection policy to it
                    if commit:
                        if self.commit(detail=vnic['name'] + " on " + str(self.name)) != True:
                            # We can use continue because the commit buffer is discard if it's an SDK error exception
                            continue
                else:
                    if vnic['fabric']:
                        vnic['fabric'] = vnic['fabric'].upper()
                    mac_address_pool = vnic["mac_address_pool"]
                    mac_address = vnic["mac_address"]
                    if mac_address == "hardware-default":
                        mac_address_pool = ""
                        mac_address = "derived"
                    mo_vnic_ether = VnicEther(parent_mo_or_dn=mo_vnic_lan_conn_policy,
                                              name=vnic['name'], mtu=vnic['mtu'],
                                              adaptor_profile_name=vnic['adapter_policy'],
                                              order=vnic['order'], switch_id=vnic['fabric'],
                                              ident_pool_name=mac_address_pool,
                                              addr=mac_address,
                                              qos_policy_name=vnic['qos_policy'],
                                              nw_ctrl_policy_name=vnic['network_control_policy'],
                                              cdn_source=vnic['cdn_source'],
                                              admin_cdn_name=vnic['cdn_name'],
                                              stats_policy_name=vnic["stats_threshold_policy"])
                    self._handle.add_mo(mo=mo_vnic_ether, modify_present=True)
                    # We need to commit the interface first and then add the vlan and connection policy to it
                    if commit:
                        if self.commit(detail=vnic['name'] + " on " + str(self.name)) != True:
                            # We can use continue because the commit buffer is discard if it's an SDK error exception
                            continue

                    # Creating connection_policy
                    if vnic["dynamic_vnic_connection_policy"]:
                        # connection_policy = "SRIOV-VMFEX"
                        VnicDynamicConPolicyRef(parent_mo_or_dn=mo_vnic_ether,
                                                con_policy_name=vnic["dynamic_vnic_connection_policy"])
                    elif vnic["usnic_connection_policy"]:
                        # connection_policy = "SRIOV-USNIC"
                        VnicUsnicConPolicyRef(parent_mo_or_dn=mo_vnic_ether,
                                              con_policy_name=vnic["usnic_connection_policy"])
                    elif vnic["vmq_connection_policy"]:
                        # connection_policy = "VMQ"
                        VnicVmqConPolicyRef(parent_mo_or_dn=mo_vnic_ether,
                                            con_policy_name=vnic["vmq_connection_policy"])

                    # Adding the vlans
                    if vnic['vlan_native']:
                        mo_vnic_ether_if = VnicEtherIf(parent_mo_or_dn=mo_vnic_ether,
                                                       name=vnic['vlan_native'],
                                                       default_net="yes")
                        self._handle.add_mo(mo_vnic_ether_if, modify_present=True)
                    if vnic['vlans']:
                        for vlan in vnic['vlans']:
                            mo_vnic_ether_if = VnicEtherIf(parent_mo_or_dn=mo_vnic_ether,
                                                           name=vlan,
                                                           default_net="no")
                            self._handle.add_mo(mo_vnic_ether_if, modify_present=True)

                    # Adding the vlan groups
                    if vnic['vlan_groups']:
                        for vlan_group in vnic['vlan_groups']:
                            mo_fabric_net_group_ref = FabricNetGroupRef(parent_mo_or_dn=mo_vnic_ether,
                                                                        name=vlan_group)
                            self._handle.add_mo(mo_fabric_net_group_ref, modify_present=True)

                self._handle.add_mo(mo=mo_vnic_ether, modify_present=True)

            for iscsi_vnic in self.iscsi_vnics:
                mo_vnic_iscsi_lcp = VnicIScsiLCP(parent_mo_or_dn=mo_vnic_lan_conn_policy,
                                                 adaptor_profile_name=iscsi_vnic["iscsi_adapter_policy"],
                                                 ident_pool_name=iscsi_vnic["mac_address_pool"],
                                                 name=iscsi_vnic["name"],
                                                 #  switch_id=iscsi_vnic['fabric'],
                                                 vnic_name=iscsi_vnic["overlay_vnic"])
                VnicVlan(parent_mo_or_dn=mo_vnic_iscsi_lcp, name="", vlan_name=iscsi_vnic["vlan"])

                mo_vnic_iscsi_initiator_params = VnicIScsiInitiatorParams(parent_mo_or_dn=mo_vnic_iscsi_lcp)

                # Added additional pools/policies present in UCS Central when compared to UCSM
                mo_vnic_iscsi_boot_vnic = VnicIScsiBootVnic(
                    parent_mo_or_dn=mo_vnic_iscsi_initiator_params, name=iscsi_vnic["name"],
                    auth_profile_name=iscsi_vnic["authentication_profile"],
                    iqn_ident_pool_name=iscsi_vnic["iqn_pool"])

                mo_vnicipv4if = VnicIPv4If(parent_mo_or_dn=mo_vnic_iscsi_boot_vnic)
                VnicIPv4PooledIscsiAddr(parent_mo_or_dn=mo_vnicipv4if,
                                        ident_pool_name=iscsi_vnic["ip_pool"])

                self._handle.add_mo(mo=mo_vnic_iscsi_lcp, modify_present=True)

        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True


class UcsCentralSanConnectivityPolicy(UcsCentralConfigObject):
    _CONFIG_NAME = "SAN Connectivity Policy"
    _CONFIG_SECTION_NAME = "san_connectivity_policies"
    _UCS_SDK_OBJECT_NAME = "vnicSanConnPolicy"
    _POLICY_MAPPING_TABLE = {
        "wwnn_pool": UcsCentralWwnnPool,
        "vhbas": [
            {
                "adapter_policy": UcsCentralFibreChannelAdapterPolicy,
                "pin_group": None,
                "qos_policy": UcsCentralQosPolicy,
                "stats_threshold_policy": UcsCentralThresholdPolicy,
                "vhba_template": UcsCentralVhbaTemplate,
                "wwpn_pool": UcsCentralWwpnPool
            }
        ]
    }

    def __init__(self, parent=None, json_content=None, vnic_san_conn_policy=None):
        UcsCentralConfigObject.__init__(self, parent=parent, ucs_sdk_object=vnic_san_conn_policy)
        self.name = None
        self.descr = None
        self.wwnn_pool = None
        self.vhbas = []
        self.vhba_initiator_groups = []

        if self._config.load_from == "live":
            if vnic_san_conn_policy is not None:
                self.name = vnic_san_conn_policy.name
                self.descr = vnic_san_conn_policy.descr

                if "vnicFcNode" in self._parent._config.sdk_objects:
                    for vnic_fc in self._config.sdk_objects["vnicFcNode"]:
                        if self._parent._dn:
                            if self._parent._dn + "/san-conn-pol-" + self.name + '/' in vnic_fc.dn:
                                self.wwnn_pool = vnic_fc.ident_pool_name
                                break

                if "vnicFc" in self._parent._config.sdk_objects:
                    for vnic_fc in self._config.sdk_objects["vnicFc"]:
                        if self._parent._dn:
                            if self._parent._dn + "/san-conn-pol-" + self.name + '/' in vnic_fc.dn:
                                vhba = {"_object_type": "vhbas"}
                                vhba.update({"name": vnic_fc.name})
                                vhba.update({"adapter_policy": vnic_fc.adaptor_profile_name})
                                vhba.update({"order": vnic_fc.order})
                                if vnic_fc.nw_templ_name:
                                    vhba.update({"vhba_template": vnic_fc.nw_templ_name})
                                else:
                                    vhba.update({"fabric": vnic_fc.switch_id})
                                    vhba.update({"wwpn_pool": vnic_fc.ident_pool_name})
                                    vhba.update({"persistent_binding": vnic_fc.pers_bind})
                                    vhba.update({"max_data_field_size": vnic_fc.max_data_field_size})
                                    vhba.update({"qos_policy": vnic_fc.qos_policy_name})
                                    vhba.update({"stats_threshold_policy": vnic_fc.stats_policy_name})

                                    if vhba["persistent_binding"] == "1":
                                        vhba["persistent_binding"] = "enabled"

                                    if "vnicFcIf" in self._parent._config.sdk_objects:
                                        for conn_policy in self._config.sdk_objects["vnicFcIf"]:
                                            if self._parent._dn + "/san-conn-pol-" + self.name + '/fc-' + vhba['name'] \
                                                    + '/' in conn_policy.dn:
                                                vhba.update({"vsan": conn_policy.name})
                                                break

                                # Fetching the operational state of the referenced policies
                                oper_state = {}
                                oper_state.update(
                                    self.get_operational_state(
                                        policy_dn=vnic_fc.oper_adaptor_profile_name,
                                        separator="/fc-profile-",
                                        policy_name="adapter_policy"
                                    )
                                )
                                oper_state.update(
                                    self.get_operational_state(
                                        policy_dn=vnic_fc.oper_qos_policy_name,
                                        separator="/ep-qos-",
                                        policy_name="qos_policy"
                                    )
                                )
                                oper_state.update(
                                    self.get_operational_state(
                                        policy_dn=vnic_fc.oper_stats_policy_name,
                                        separator="/thr-policy-",
                                        policy_name="stats_threshold_policy"
                                    )
                                )
                                oper_state.update(
                                    self.get_operational_state(
                                        policy_dn=vnic_fc.oper_nw_templ_name,
                                        separator="/san-conn-templ-",
                                        policy_name="vhba_template"
                                    )
                                )

                                vhba['operational_state'] = oper_state

                                self.vhbas.append(vhba)

                if "storageIniGroup" in self._parent._config.sdk_objects:
                    for ini_group in self._config.sdk_objects["storageIniGroup"]:
                        if self._parent._dn:
                            if self._parent._dn + "/san-conn-pol-" + self.name + '/' in ini_group.dn:
                                group = {}
                                group.update({"name": ini_group.name})
                                group.update({"descr": ini_group.descr})
                                if "vnicFcGroupDef" in self._parent._config.sdk_objects:
                                    for fc_group in self._config.sdk_objects["vnicFcGroupDef"]:
                                        if self._parent._dn + "/san-conn-pol-" + self.name + '/grp-' + group['name'] + \
                                                '/fc' in fc_group.dn:
                                            group.update(
                                                {"storage_connection_policy": fc_group.storage_conn_policy_name})
                                            break
                                if "storageInitiator" in self._parent._config.sdk_objects:
                                    group.update({"initiators": []})
                                    for init in self._config.sdk_objects["storageInitiator"]:
                                        if self._parent._dn + "/san-conn-pol-" + self.name + '/grp-' + group['name'] + \
                                                '/' in init.dn:
                                            group['initiators'].append(init.name)

                                self.vhba_initiator_groups.append(group)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

                for element in self.vhbas:
                    for value in ["adapter_policy", "vhba_template", "fabric", "name", "order", "wwpn_pool",
                                  "persistent_binding", "max_data_field_size", "qos_policy", "vsan", "pin_group",
                                  "stats_threshold_policy", "operational_state"]:
                        if value not in element:
                            element[value] = None
                    for policy in ["adapter_policy", "qos_policy", "stats_threshold_policy", "vhba_template",
                                   "wwpn_pool"]:
                        if element["operational_state"]:
                            if policy not in element["operational_state"]:
                                element["operational_state"][policy] = None
                            else:
                                for value in ["name", "org"]:
                                    if value not in element["operational_state"][policy]:
                                        element["operational_state"][policy][value] = None

                    # Flagging this as a vHBA
                    element["_object_type"] = "vhbas"

                for element in self.vhba_initiator_groups:
                    for value in ["storage_connection_policy", "initiators", "name", "descr"]:
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

        mo_vnic_san_conn_policy = VnicSanConnPolicy(parent_mo_or_dn=parent_mo, name=self.name, descr=self.descr)
        if self.wwnn_pool:
            VnicFcNode(parent_mo_or_dn=mo_vnic_san_conn_policy, ident_pool_name=self.wwnn_pool)
        self._handle.add_mo(mo=mo_vnic_san_conn_policy, modify_present=True)
        if self.commit(detail=self.name) != True:
            return False

        if self.vhbas:
            for vhba in self.vhbas:
                if vhba['vhba_template']:
                    mo_vnic_fc = VnicFc(parent_mo_or_dn=mo_vnic_san_conn_policy,
                                        adaptor_profile_name=vhba['adapter_policy'],
                                        nw_templ_name=vhba['vhba_template'], name=vhba['name'],
                                        order=vhba['order'])

                    self._handle.add_mo(mo=mo_vnic_fc, modify_present=True)
                    if commit:
                        if self.commit(detail=vhba['name']) != True:
                            continue
                else:
                    if vhba['fabric']:
                        vhba['fabric'] = vhba['fabric'].upper()
                    if vhba['persistent_binding'] == "enabled":
                        vhba['persistent_binding'] = "1"
                    mo_vnic_fc = VnicFc(parent_mo_or_dn=mo_vnic_san_conn_policy, name=vhba['name'], order=vhba['order'],
                                        switch_id=vhba['fabric'],
                                        ident_pool_name=vhba['wwpn_pool'], pers_bind=vhba['persistent_binding'],
                                        max_data_field_size=vhba['max_data_field_size'],
                                        adaptor_profile_name=vhba['adapter_policy'], qos_policy_name=vhba['qos_policy'],
                                        stats_policy_name=vhba["stats_threshold_policy"])

                    # Adding the vsan
                    if 'vsan' in vhba:
                        mo_vnic_ether_if = VnicFcIf(parent_mo_or_dn=mo_vnic_fc, name=vhba['vsan'])
                        self._handle.add_mo(mo_vnic_ether_if, modify_present=True)

                    self._handle.add_mo(mo=mo_vnic_fc, modify_present=True)
                    if commit:
                        if self.commit(detail=vhba['name']) != True:
                            continue

        if self.vhba_initiator_groups:
            for initiator in self.vhba_initiator_groups:
                mo_ini_group = StorageIniGroup(parent_mo_or_dn=mo_vnic_san_conn_policy,
                                               name=initiator['name'],
                                               descr=initiator['descr'])
                if initiator['storage_connection_policy']:
                    VnicFcGroupDef(parent_mo_or_dn=mo_ini_group,
                                   storage_conn_policy_name=initiator['storage_connection_policy'])
                if initiator['initiators']:
                    for sto_initiator in initiator['initiators']:
                        StorageInitiator(parent_mo_or_dn=mo_ini_group, name=sto_initiator)

                self._handle.add_mo(mo=mo_ini_group, modify_present=True)
                if commit:
                    if self.commit(detail=initiator['name']) != True:
                        return False

        # if commit:
        #   if self.commit(detail=self.name):
        #      return False
        return True
