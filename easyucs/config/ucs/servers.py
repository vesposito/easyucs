# coding: utf-8
# !/usr/bin/env python

""" servers.py: Easy UCS Deployment Tool """

from easyucs import __author__, __copyright__,  __version__, __status__


import json
import os
import urllib

from ucsmsdk.mometa.aaa.AaaEpAuthProfile import AaaEpAuthProfile
from ucsmsdk.mometa.aaa.AaaEpUser import AaaEpUser
from ucsmsdk.mometa.adaptor.AdaptorCapQual import AdaptorCapQual
from ucsmsdk.mometa.adaptor.AdaptorEthAdvFilterProfile import AdaptorEthAdvFilterProfile
from ucsmsdk.mometa.adaptor.AdaptorEthArfsProfile import AdaptorEthArfsProfile
from ucsmsdk.mometa.adaptor.AdaptorEthCompQueueProfile import AdaptorEthCompQueueProfile
from ucsmsdk.mometa.adaptor.AdaptorEthFailoverProfile import AdaptorEthFailoverProfile
from ucsmsdk.mometa.adaptor.AdaptorEthInterruptProfile import AdaptorEthInterruptProfile
from ucsmsdk.mometa.adaptor.AdaptorEthInterruptScalingProfile import AdaptorEthInterruptScalingProfile
from ucsmsdk.mometa.adaptor.AdaptorEthNVGREProfile import AdaptorEthNVGREProfile
from ucsmsdk.mometa.adaptor.AdaptorEthOffloadProfile import AdaptorEthOffloadProfile
from ucsmsdk.mometa.adaptor.AdaptorEthRecvQueueProfile import AdaptorEthRecvQueueProfile
from ucsmsdk.mometa.adaptor.AdaptorEthRoCEProfile import AdaptorEthRoCEProfile
from ucsmsdk.mometa.adaptor.AdaptorEthVxLANProfile import AdaptorEthVxLANProfile
from ucsmsdk.mometa.adaptor.AdaptorEthWorkQueueProfile import AdaptorEthWorkQueueProfile
from ucsmsdk.mometa.adaptor.AdaptorFcCdbWorkQueueProfile import AdaptorFcCdbWorkQueueProfile
from ucsmsdk.mometa.adaptor.AdaptorFcErrorRecoveryProfile import AdaptorFcErrorRecoveryProfile
from ucsmsdk.mometa.adaptor.AdaptorFcFnicProfile import AdaptorFcFnicProfile
from ucsmsdk.mometa.adaptor.AdaptorFcInterruptProfile import AdaptorFcInterruptProfile
from ucsmsdk.mometa.adaptor.AdaptorFcPortFLogiProfile import AdaptorFcPortFLogiProfile
from ucsmsdk.mometa.adaptor.AdaptorFcPortPLogiProfile import AdaptorFcPortPLogiProfile
from ucsmsdk.mometa.adaptor.AdaptorFcPortProfile import AdaptorFcPortProfile
from ucsmsdk.mometa.adaptor.AdaptorFcRecvQueueProfile import AdaptorFcRecvQueueProfile
from ucsmsdk.mometa.adaptor.AdaptorFcVhbaTypeProfile import AdaptorFcVhbaTypeProfile
from ucsmsdk.mometa.adaptor.AdaptorFcWorkQueueProfile import AdaptorFcWorkQueueProfile
from ucsmsdk.mometa.adaptor.AdaptorHostEthIfProfile import AdaptorHostEthIfProfile
from ucsmsdk.mometa.adaptor.AdaptorHostFcIfProfile import AdaptorHostFcIfProfile
from ucsmsdk.mometa.adaptor.AdaptorHostIscsiIfProfile import AdaptorHostIscsiIfProfile
from ucsmsdk.mometa.adaptor.AdaptorProtocolProfile import AdaptorProtocolProfile
from ucsmsdk.mometa.adaptor.AdaptorQual import AdaptorQual
from ucsmsdk.mometa.adaptor.AdaptorRssProfile import AdaptorRssProfile
from ucsmsdk.mometa.bios.BiosTokenParam import BiosTokenParam
from ucsmsdk.mometa.bios.BiosTokenSettings import BiosTokenSettings
from ucsmsdk.mometa.bios.BiosVProfile import BiosVProfile
from ucsmsdk.mometa.bios.BiosVfASPMSupport import BiosVfASPMSupport
from ucsmsdk.mometa.bios.BiosVfAllUSBDevices import BiosVfAllUSBDevices
from ucsmsdk.mometa.bios.BiosVfAltitude import BiosVfAltitude
from ucsmsdk.mometa.bios.BiosVfAssertNMIOnPERR import BiosVfAssertNMIOnPERR
from ucsmsdk.mometa.bios.BiosVfAssertNMIOnSERR import BiosVfAssertNMIOnSERR
from ucsmsdk.mometa.bios.BiosVfBootOptionRetry import BiosVfBootOptionRetry
from ucsmsdk.mometa.bios.BiosVfCPUHardwarePowerManagement import BiosVfCPUHardwarePowerManagement
from ucsmsdk.mometa.bios.BiosVfCPUPerformance import BiosVfCPUPerformance
from ucsmsdk.mometa.bios.BiosVfConsistentDeviceNameControl import BiosVfConsistentDeviceNameControl
from ucsmsdk.mometa.bios.BiosVfConsoleRedirection import BiosVfConsoleRedirection
from ucsmsdk.mometa.bios.BiosVfCoreMultiProcessing import BiosVfCoreMultiProcessing
from ucsmsdk.mometa.bios.BiosVfDDR3VoltageSelection import BiosVfDDR3VoltageSelection
from ucsmsdk.mometa.bios.BiosVfDRAMClockThrottling import BiosVfDRAMClockThrottling
from ucsmsdk.mometa.bios.BiosVfDirectCacheAccess import BiosVfDirectCacheAccess
from ucsmsdk.mometa.bios.BiosVfDramRefreshRate import BiosVfDramRefreshRate
from ucsmsdk.mometa.bios.BiosVfEnergyPerformanceTuning import BiosVfEnergyPerformanceTuning
from ucsmsdk.mometa.bios.BiosVfEnhancedIntelSpeedStepTech import BiosVfEnhancedIntelSpeedStepTech
from ucsmsdk.mometa.bios.BiosVfExecuteDisableBit import BiosVfExecuteDisableBit
from ucsmsdk.mometa.bios.BiosVfFRB2Timer import BiosVfFRB2Timer
from ucsmsdk.mometa.bios.BiosVfFrequencyFloorOverride import BiosVfFrequencyFloorOverride
from ucsmsdk.mometa.bios.BiosVfFrontPanelLockout import BiosVfFrontPanelLockout
from ucsmsdk.mometa.bios.BiosVfIOEMezz1OptionROM import BiosVfIOEMezz1OptionROM
from ucsmsdk.mometa.bios.BiosVfIOENVMe1OptionROM import BiosVfIOENVMe1OptionROM
from ucsmsdk.mometa.bios.BiosVfIOENVMe2OptionROM import BiosVfIOENVMe2OptionROM
from ucsmsdk.mometa.bios.BiosVfIOESlot1OptionROM import BiosVfIOESlot1OptionROM
from ucsmsdk.mometa.bios.BiosVfIOESlot2OptionROM import BiosVfIOESlot2OptionROM
from ucsmsdk.mometa.bios.BiosVfIntegratedGraphics import BiosVfIntegratedGraphics
from ucsmsdk.mometa.bios.BiosVfIntegratedGraphicsApertureSize import BiosVfIntegratedGraphicsApertureSize
from ucsmsdk.mometa.bios.BiosVfIntelEntrySASRAIDModule import BiosVfIntelEntrySASRAIDModule
from ucsmsdk.mometa.bios.BiosVfIntelHyperThreadingTech import BiosVfIntelHyperThreadingTech
from ucsmsdk.mometa.bios.BiosVfIntelTrustedExecutionTechnology import BiosVfIntelTrustedExecutionTechnology
from ucsmsdk.mometa.bios.BiosVfIntelTurboBoostTech import BiosVfIntelTurboBoostTech
from ucsmsdk.mometa.bios.BiosVfIntelVTForDirectedIO import BiosVfIntelVTForDirectedIO
from ucsmsdk.mometa.bios.BiosVfIntelVirtualizationTechnology import BiosVfIntelVirtualizationTechnology
from ucsmsdk.mometa.bios.BiosVfInterleaveConfiguration import BiosVfInterleaveConfiguration
from ucsmsdk.mometa.bios.BiosVfLocalX2Apic import BiosVfLocalX2Apic
from ucsmsdk.mometa.bios.BiosVfLvDIMMSupport import BiosVfLvDIMMSupport
from ucsmsdk.mometa.bios.BiosVfMaxVariableMTRRSetting import BiosVfMaxVariableMTRRSetting
from ucsmsdk.mometa.bios.BiosVfMaximumMemoryBelow4GB import BiosVfMaximumMemoryBelow4GB
from ucsmsdk.mometa.bios.BiosVfMemoryMappedIOAbove4GB import BiosVfMemoryMappedIOAbove4GB
from ucsmsdk.mometa.bios.BiosVfMirroringMode import BiosVfMirroringMode
from ucsmsdk.mometa.bios.BiosVfNUMAOptimized import BiosVfNUMAOptimized
from ucsmsdk.mometa.bios.BiosVfOSBootWatchdogTimer import BiosVfOSBootWatchdogTimer
from ucsmsdk.mometa.bios.BiosVfOSBootWatchdogTimerPolicy import BiosVfOSBootWatchdogTimerPolicy
from ucsmsdk.mometa.bios.BiosVfOSBootWatchdogTimerTimeout import BiosVfOSBootWatchdogTimerTimeout
from ucsmsdk.mometa.bios.BiosVfOnboardGraphics import BiosVfOnboardGraphics
from ucsmsdk.mometa.bios.BiosVfOnboardStorage import BiosVfOnboardStorage
from ucsmsdk.mometa.bios.BiosVfOutOfBandManagement import BiosVfOutOfBandManagement
from ucsmsdk.mometa.bios.BiosVfPCILOMPortsConfiguration import BiosVfPCILOMPortsConfiguration
from ucsmsdk.mometa.bios.BiosVfPCIROMCLP import BiosVfPCIROMCLP
from ucsmsdk.mometa.bios.BiosVfPCISlotLinkSpeed import BiosVfPCISlotLinkSpeed
from ucsmsdk.mometa.bios.BiosVfPCISlotOptionROMEnable import BiosVfPCISlotOptionROMEnable
from ucsmsdk.mometa.bios.BiosVfPOSTErrorPause import BiosVfPOSTErrorPause
from ucsmsdk.mometa.bios.BiosVfPSTATECoordination import BiosVfPSTATECoordination
from ucsmsdk.mometa.bios.BiosVfPackageCStateLimit import BiosVfPackageCStateLimit
from ucsmsdk.mometa.bios.BiosVfProcessorC1E import BiosVfProcessorC1E
from ucsmsdk.mometa.bios.BiosVfProcessorC3Report import BiosVfProcessorC3Report
from ucsmsdk.mometa.bios.BiosVfProcessorC6Report import BiosVfProcessorC6Report
from ucsmsdk.mometa.bios.BiosVfProcessorC7Report import BiosVfProcessorC7Report
from ucsmsdk.mometa.bios.BiosVfProcessorCMCI import BiosVfProcessorCMCI
from ucsmsdk.mometa.bios.BiosVfProcessorCState import BiosVfProcessorCState
from ucsmsdk.mometa.bios.BiosVfProcessorEnergyConfiguration import BiosVfProcessorEnergyConfiguration
from ucsmsdk.mometa.bios.BiosVfProcessorPrefetchConfig import BiosVfProcessorPrefetchConfig
from ucsmsdk.mometa.bios.BiosVfQPILinkFrequencySelect import BiosVfQPILinkFrequencySelect
from ucsmsdk.mometa.bios.BiosVfQPISnoopMode import BiosVfQPISnoopMode
from ucsmsdk.mometa.bios.BiosVfQuietBoot import BiosVfQuietBoot
from ucsmsdk.mometa.bios.BiosVfRedirectionAfterBIOSPOST import BiosVfRedirectionAfterBIOSPOST
from ucsmsdk.mometa.bios.BiosVfResumeOnACPowerLoss import BiosVfResumeOnACPowerLoss
from ucsmsdk.mometa.bios.BiosVfSBMezz1OptionROM import BiosVfSBMezz1OptionROM
from ucsmsdk.mometa.bios.BiosVfSBNVMe1OptionROM import BiosVfSBNVMe1OptionROM
from ucsmsdk.mometa.bios.BiosVfSIOC1OptionROM import BiosVfSIOC1OptionROM
from ucsmsdk.mometa.bios.BiosVfSIOC2OptionROM import BiosVfSIOC2OptionROM
from ucsmsdk.mometa.bios.BiosVfScrubPolicies import BiosVfScrubPolicies
from ucsmsdk.mometa.bios.BiosVfSelectMemoryRASConfiguration import BiosVfSelectMemoryRASConfiguration
from ucsmsdk.mometa.bios.BiosVfSerialPortAEnable import BiosVfSerialPortAEnable
from ucsmsdk.mometa.bios.BiosVfTrustedPlatformModule import BiosVfTrustedPlatformModule
from ucsmsdk.mometa.bios.BiosVfUSBBootConfig import BiosVfUSBBootConfig
from ucsmsdk.mometa.bios.BiosVfUSBConfiguration import BiosVfUSBConfiguration
from ucsmsdk.mometa.bios.BiosVfUSBFrontPanelAccessLock import BiosVfUSBFrontPanelAccessLock
from ucsmsdk.mometa.bios.BiosVfUSBPortConfiguration import BiosVfUSBPortConfiguration
from ucsmsdk.mometa.bios.BiosVfUSBSystemIdlePowerOptimizingSetting import BiosVfUSBSystemIdlePowerOptimizingSetting
from ucsmsdk.mometa.bios.BiosVfVGAPriority import BiosVfVGAPriority
from ucsmsdk.mometa.bios.BiosVfWorkloadConfiguration import BiosVfWorkloadConfiguration
from ucsmsdk.mometa.cimcvmedia.CimcvmediaConfigMountEntry import CimcvmediaConfigMountEntry
from ucsmsdk.mometa.cimcvmedia.CimcvmediaMountConfigPolicy import CimcvmediaMountConfigPolicy
from ucsmsdk.mometa.compute.ComputeChassisQual import ComputeChassisQual
from ucsmsdk.mometa.compute.ComputeGraphicsCardPolicy import ComputeGraphicsCardPolicy
from ucsmsdk.mometa.compute.ComputeKvmMgmtPolicy import ComputeKvmMgmtPolicy
from ucsmsdk.mometa.compute.ComputeMemoryConfigPolicy import ComputeMemoryConfigPolicy
from ucsmsdk.mometa.compute.ComputePhysicalQual import ComputePhysicalQual
from ucsmsdk.mometa.compute.ComputePool import ComputePool
from ucsmsdk.mometa.compute.ComputePooledRackUnit import ComputePooledRackUnit
from ucsmsdk.mometa.compute.ComputePooledSlot import ComputePooledSlot
from ucsmsdk.mometa.compute.ComputePoolingPolicy import ComputePoolingPolicy
from ucsmsdk.mometa.compute.ComputePowerSyncPolicy import ComputePowerSyncPolicy
from ucsmsdk.mometa.compute.ComputeQual import ComputeQual
from ucsmsdk.mometa.compute.ComputeRackQual import ComputeRackQual
from ucsmsdk.mometa.compute.ComputeScrubPolicy import ComputeScrubPolicy
from ucsmsdk.mometa.compute.ComputeSlotQual import ComputeSlotQual
from ucsmsdk.mometa.diag.DiagMemoryTest import DiagMemoryTest
from ucsmsdk.mometa.diag.DiagRunPolicy import DiagRunPolicy
from ucsmsdk.mometa.fabric.FabricNetGroupRef import FabricNetGroupRef
from ucsmsdk.mometa.fabric.FabricVCon import FabricVCon
from ucsmsdk.mometa.fabric.FabricVConProfile import FabricVConProfile
from ucsmsdk.mometa.firmware.FirmwareComputeHostPack import FirmwareComputeHostPack
from ucsmsdk.mometa.firmware.FirmwareExcludeServerComponent import FirmwareExcludeServerComponent
from ucsmsdk.mometa.firmware.FirmwarePackItem import FirmwarePackItem
from ucsmsdk.mometa.iscsi.IscsiAuthProfile import IscsiAuthProfile
from ucsmsdk.mometa.ls.LsBinding import LsBinding
from ucsmsdk.mometa.ls.LsPower import LsPower
from ucsmsdk.mometa.ls.LsRequirement import LsRequirement
from ucsmsdk.mometa.ls.LsServer import LsServer
from ucsmsdk.mometa.ls.LsServerExtension import LsServerExtension
from ucsmsdk.mometa.ls.LsVConAssign import LsVConAssign
from ucsmsdk.mometa.lsboot.LsbootBootSecurity import LsbootBootSecurity
from ucsmsdk.mometa.lsboot.LsbootDefaultLocalImage import LsbootDefaultLocalImage
from ucsmsdk.mometa.lsboot.LsbootEFIShell import LsbootEFIShell
from ucsmsdk.mometa.lsboot.LsbootEmbeddedLocalDiskImage import LsbootEmbeddedLocalDiskImage
from ucsmsdk.mometa.lsboot.LsbootEmbeddedLocalDiskImagePath import LsbootEmbeddedLocalDiskImagePath
from ucsmsdk.mometa.lsboot.LsbootEmbeddedLocalLunImage import LsbootEmbeddedLocalLunImage
from ucsmsdk.mometa.lsboot.LsbootIScsi import LsbootIScsi
from ucsmsdk.mometa.lsboot.LsbootIScsiImagePath import LsbootIScsiImagePath
from ucsmsdk.mometa.lsboot.LsbootLan import LsbootLan
from ucsmsdk.mometa.lsboot.LsbootLanImagePath import LsbootLanImagePath
from ucsmsdk.mometa.lsboot.LsbootLocalDiskImage import LsbootLocalDiskImage
from ucsmsdk.mometa.lsboot.LsbootLocalDiskImagePath import LsbootLocalDiskImagePath
from ucsmsdk.mometa.lsboot.LsbootLocalHddImage import LsbootLocalHddImage
from ucsmsdk.mometa.lsboot.LsbootLocalLunImagePath import LsbootLocalLunImagePath
from ucsmsdk.mometa.lsboot.LsbootLocalStorage import LsbootLocalStorage
from ucsmsdk.mometa.lsboot.LsbootNvme import LsbootNvme
from ucsmsdk.mometa.lsboot.LsbootPolicy import LsbootPolicy
from ucsmsdk.mometa.lsboot.LsbootSan import LsbootSan
from ucsmsdk.mometa.lsboot.LsbootSanCatSanImage import LsbootSanCatSanImage
from ucsmsdk.mometa.lsboot.LsbootSanCatSanImagePath import LsbootSanCatSanImagePath
from ucsmsdk.mometa.lsboot.LsbootStorage import LsbootStorage
from ucsmsdk.mometa.lsboot.LsbootUEFIBootParam import LsbootUEFIBootParam
from ucsmsdk.mometa.lsboot.LsbootUsbExternalImage import LsbootUsbExternalImage
from ucsmsdk.mometa.lsboot.LsbootUsbFlashStorageImage import LsbootUsbFlashStorageImage
from ucsmsdk.mometa.lsboot.LsbootUsbInternalImage import LsbootUsbInternalImage
from ucsmsdk.mometa.lsboot.LsbootVirtualMedia import LsbootVirtualMedia
from ucsmsdk.mometa.lsmaint.LsmaintMaintPolicy import LsmaintMaintPolicy
from ucsmsdk.mometa.lstorage.LstorageProfileBinding import LstorageProfileBinding
from ucsmsdk.mometa.memory.MemoryQual import MemoryQual
from ucsmsdk.mometa.mgmt.MgmtInterface import MgmtInterface
from ucsmsdk.mometa.mgmt.MgmtVnet import MgmtVnet
from ucsmsdk.mometa.power.PowerGroupQual import PowerGroupQual
from ucsmsdk.mometa.power.PowerPolicy import PowerPolicy
from ucsmsdk.mometa.processor.ProcessorQual import ProcessorQual
from ucsmsdk.mometa.sol.SolPolicy import SolPolicy
from ucsmsdk.mometa.stats.StatsThr32Definition import StatsThr32Definition
from ucsmsdk.mometa.stats.StatsThr32Value import StatsThr32Value
from ucsmsdk.mometa.stats.StatsThrFloatDefinition import StatsThrFloatDefinition
from ucsmsdk.mometa.stats.StatsThrFloatValue import StatsThrFloatValue
from ucsmsdk.mometa.stats.StatsThresholdClass import StatsThresholdClass
from ucsmsdk.mometa.stats.StatsThresholdPolicy import StatsThresholdPolicy
from ucsmsdk.mometa.storage.StorageIniGroup import StorageIniGroup
from ucsmsdk.mometa.storage.StorageInitiator import StorageInitiator
from ucsmsdk.mometa.storage.StorageLocalDiskConfigPolicy import StorageLocalDiskConfigPolicy
from ucsmsdk.mometa.storage.StorageQual import StorageQual
from ucsmsdk.mometa.uuidpool.UuidpoolBlock import UuidpoolBlock
from ucsmsdk.mometa.uuidpool.UuidpoolPool import UuidpoolPool
from ucsmsdk.mometa.vnic.VnicConnDef import VnicConnDef
from ucsmsdk.mometa.vnic.VnicDefBeh import VnicDefBeh
from ucsmsdk.mometa.vnic.VnicDynamicConPolicyRef import VnicDynamicConPolicyRef
from ucsmsdk.mometa.vnic.VnicEther import VnicEther
from ucsmsdk.mometa.vnic.VnicEtherIf import VnicEtherIf
from ucsmsdk.mometa.vnic.VnicFc import VnicFc
from ucsmsdk.mometa.vnic.VnicFcGroupDef import VnicFcGroupDef
from ucsmsdk.mometa.vnic.VnicFcIf import VnicFcIf
from ucsmsdk.mometa.vnic.VnicFcNode import VnicFcNode
from ucsmsdk.mometa.vnic.VnicIPv4Dhcp import VnicIPv4Dhcp
from ucsmsdk.mometa.vnic.VnicIPv4If import VnicIPv4If
from ucsmsdk.mometa.vnic.VnicIPv4PooledIscsiAddr import VnicIPv4PooledIscsiAddr
from ucsmsdk.mometa.vnic.VnicIScsi import VnicIScsi
from ucsmsdk.mometa.vnic.VnicIScsiAutoTargetIf import VnicIScsiAutoTargetIf
from ucsmsdk.mometa.vnic.VnicIScsiBootParams import VnicIScsiBootParams
from ucsmsdk.mometa.vnic.VnicIScsiBootVnic import VnicIScsiBootVnic
from ucsmsdk.mometa.vnic.VnicIScsiNode import VnicIScsiNode
from ucsmsdk.mometa.vnic.VnicIScsiStaticTargetIf import VnicIScsiStaticTargetIf
from ucsmsdk.mometa.vnic.VnicIpV4MgmtPooledAddr import VnicIpV4MgmtPooledAddr
from ucsmsdk.mometa.vnic.VnicIpV6MgmtPooledAddr import VnicIpV6MgmtPooledAddr
from ucsmsdk.mometa.vnic.VnicLun import VnicLun
from ucsmsdk.mometa.vnic.VnicUsnicConPolicyRef import VnicUsnicConPolicyRef
from ucsmsdk.mometa.vnic.VnicVlan import VnicVlan
from ucsmsdk.mometa.vnic.VnicVmqConPolicyRef import VnicVmqConPolicyRef
from ucsmsdk.ucsbasetype import DnSet, Dn
from ucsmsdk.ucscoremeta import UcsVersion
from ucsmsdk.ucsexception import UcsException
from ucsmsdk.ucsmethodfactory import ls_instantiate_n_named_template, ls_instantiate_template

from easyucs.config.object import UcsSystemConfigObject


class UcsSystemUuidPool(UcsSystemConfigObject):
    _CONFIG_NAME = "UUID Pool"
    _UCS_SDK_OBJECT_NAME = "uuidpoolPool"

    def __init__(self, parent=None, json_content=None, uuidpool_pool=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.descr = None
        self.name = None
        self.order = None
        self.prefix = None
        self.uuid_blocks = []

        if self._config.load_from == "live":
            if uuidpool_pool is not None:
                self.name = uuidpool_pool.name
                self.descr = uuidpool_pool.descr
                self.prefix = uuidpool_pool.prefix
                self.order = uuidpool_pool.assignment_order

                if "uuidpoolBlock" in self._parent._config.sdk_objects:
                    for pool_block in self._config.sdk_objects["uuidpoolBlock"]:
                        if self._parent._dn:
                            if self._parent._dn + "/uuid-pool-" + self.name + "/block-" in pool_block.dn:
                                block = {}
                                block.update({"to": pool_block.to})
                                block.update({"from": pool_block.r_from})
                                block.update({"size": None})
                                self.uuid_blocks.append(block)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

                for element in self.uuid_blocks:
                    for value in ["to", "from", "size"]:
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
                                        assignment_order=self.order,
                                        name=self.name, prefix=prefix)
        self._handle.add_mo(mo=mo_uuidpool_pool, modify_present=True)

        if self.uuid_blocks:
            for block in self.uuid_blocks:
                if block["to"]:
                    UuidpoolBlock(parent_mo_or_dn=mo_uuidpool_pool, to=block["to"], r_from=block["from"])
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

                    UuidpoolBlock(parent_mo_or_dn=mo_uuidpool_pool, to=uuid_pool_to, r_from=block["from"])

        self._handle.add_mo(mo=mo_uuidpool_pool, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False


class UcsSystemServerPool(UcsSystemConfigObject):
    _CONFIG_NAME = "Server Pool"
    _UCS_SDK_OBJECT_NAME = "computePool"

    def __init__(self, parent=None, json_content=None, compute_pool=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.descr = None
        self.name = None
        self.servers = []

        if self._config.load_from == "live":
            if compute_pool is not None:
                self.name = compute_pool.name
                self.descr = compute_pool.descr

                if "computePooledSlot" in self._parent._config.sdk_objects:
                    for pool_block in self._config.sdk_objects["computePooledSlot"]:
                        if self._parent._dn:
                            # We avoid adding blade servers that are automatically added by a qualification policy
                            if pool_block.owner != "policy":
                                if self._parent._dn + "/compute-pool-" + self.name + "/" in pool_block.dn:
                                    block = {}
                                    block.update({"chassis_id": pool_block.chassis_id})
                                    block.update({"slot_id": pool_block.slot_id})
                                    self.servers.append(block)
                if "computePooledRackUnit" in self._parent._config.sdk_objects:
                    for pool_block in self._config.sdk_objects["computePooledRackUnit"]:
                        if self._parent._dn:
                            # We avoid adding rack servers that are automatically added by a qualification policy
                            if pool_block.owner != "policy":
                                if self._parent._dn + "/compute-pool-" + self.name + "/" in pool_block.dn:
                                    block = {}
                                    block.update({"rack_id": pool_block.id})
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
                    ComputePooledRackUnit(parent_mo_or_dn=mo_compute_pool, id=server['rack_id'])
                elif "chassis_id" in server and "slot_id" in server:
                    ComputePooledSlot(parent_mo_or_dn=mo_compute_pool, chassis_id=server['chassis_id'],
                                      slot_id=server['slot_id'])
        self._handle.add_mo(mo=mo_compute_pool, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False


class UcsSystemServerPoolPolicy(UcsSystemConfigObject):
    _CONFIG_NAME = "Server Pool Policy"
    _UCS_SDK_OBJECT_NAME = "computePoolingPolicy"

    def __init__(self, parent=None, json_content=None, compute_pooling_policy=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.descr = None
        self.name = None
        self.qualification = None
        self.target_pool = None

        if self._config.load_from == "live":
            if compute_pooling_policy is not None:
                self.name = compute_pooling_policy.name
                self.descr = compute_pooling_policy.descr
                self.qualification = compute_pooling_policy.qualifier
                self.target_pool = compute_pooling_policy.pool_dn.split('/')[-1].split('compute-pool-')[1] \
                    if compute_pooling_policy.pool_dn else None

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

        pool_dn = parent_mo + "/compute-pool-" + self.target_pool if self.target_pool else None
        mo_compute_pooling_policy = ComputePoolingPolicy(parent_mo_or_dn=parent_mo, name=self.name,
                                                         descr=self.descr,
                                                         pool_dn=pool_dn,
                                                         qualifier=self.qualification)
        self._handle.add_mo(mo=mo_compute_pooling_policy, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False


class UcsSystemPowerControlPolicy(UcsSystemConfigObject):
    _CONFIG_NAME = "Power Control Policy"
    _UCS_SDK_OBJECT_NAME = "powerPolicy"

    def __init__(self, parent=None, json_content=None, power_policy=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.name = None
        self.descr = None
        self.fan_speed_policy = None
        self.power_capping = None

        if self._config.load_from == "live":
            if power_policy is not None:
                self.name = power_policy.name
                self.descr = power_policy.descr
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
                                      fan_speed=self.fan_speed_policy,
                                      descr=self.descr)
        self._handle.add_mo(mo=mo_power_policy, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False


class UcsSystemMaintenancePolicy(UcsSystemConfigObject):
    _CONFIG_NAME = "Maintenance Policy"
    _UCS_SDK_OBJECT_NAME = "lsmaintMaintPolicy"

    def __init__(self, parent=None, json_content=None, lsmaint_maint_policy=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.name = None
        self.descr = None
        self.soft_shutdown_timer = None
        self.schedule = None
        self.on_next_boot = None
        self.reboot_policy = None

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
                                                     uptime_disr=self.reboot_policy, trigger_config=trigger)
        self._handle.add_mo(mo=mo_lsmaint_maint_policy, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
        
        
class UcsSystemGraphicsCardPolicy(UcsSystemConfigObject):
    _CONFIG_NAME = "Graphics Card Policy"
    _UCS_SDK_OBJECT_NAME = "computeGraphicsCardPolicy"

    def __init__(self, parent=None, json_content=None, compute_graphics_card_policy=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
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


class UcsSystemLocalDiskConfPolicy(UcsSystemConfigObject):
    _CONFIG_NAME = "Local Disk Configuration Policy"
    _UCS_SDK_OBJECT_NAME = "storageLocalDiskConfigPolicy"

    def __init__(self, parent=None, json_content=None, storage_local_disk_config_policy=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.name = None
        self.descr = None
        self.mode = None
        self.protect_configuration = None
        self.flexflash_state = None
        self.flexflash_raid_reporting_state = None

        if self._config.load_from == "live":
            if storage_local_disk_config_policy is not None:
                self.name = storage_local_disk_config_policy.name
                self.descr = storage_local_disk_config_policy.descr
                self.mode = storage_local_disk_config_policy.mode
                self.protect_configuration = storage_local_disk_config_policy.protect_config
                self.flexflash_state = storage_local_disk_config_policy.flex_flash_state
                self.flexflash_raid_reporting_state = storage_local_disk_config_policy.flex_flash_raid_reporting_state

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

        mo_storage_local_disk_config_policy = \
            StorageLocalDiskConfigPolicy(parent_mo_or_dn=parent_mo, name=self.name, mode=mode, descr=self.descr,
                                         protect_config=self.protect_configuration,
                                         flex_flash_raid_reporting_state=self.flexflash_raid_reporting_state,
                                         flex_flash_state=self.flexflash_state)

        self._handle.add_mo(mo=mo_storage_local_disk_config_policy, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True


class UcsSystemServerPoolPolicyQualifications(UcsSystemConfigObject):
    _CONFIG_NAME = "Server Pool Policy Qualification"
    _UCS_SDK_OBJECT_NAME = "computeQual"

    def __init__(self, parent=None, json_content=None, compute_qual=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.name = None
        self.qualifications = []
        self.descr = None

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

                if "computeRackQual" in self._parent._config.sdk_objects:
                    for qualif in self._config.sdk_objects["computeRackQual"]:
                        if self._parent._dn:
                            if self._parent._dn + "/blade-qualifier-" + self.name + "/" in qualif.dn:
                                qualification = {}
                                qualification.update({"type": "rack"})
                                qualification.update({"first_slot_id": qualif.min_id})
                                qualification.update({"last_slot_id": qualif.max_id})
                                self.qualifications.append(qualification)

                if "powerGroupQual" in self._parent._config.sdk_objects:
                    for qualif in self._config.sdk_objects["powerGroupQual"]:
                        if self._parent._dn:
                            if self._parent._dn + "/blade-qualifier-" + self.name + "/" in qualif.dn:
                                qualification = {}
                                qualification.update({"type": "power_group"})
                                qualification.update({"power_group": qualif.group_name})
                                self.qualifications.append(qualification)

                if "computeChassisQual" in self._parent._config.sdk_objects:
                    for qualif in self._config.sdk_objects["computeChassisQual"]:
                        if self._parent._dn:
                            if self._parent._dn + "/blade-qualifier-" + self.name + "/" in qualif.dn:
                                qualification = {}
                                qualification.update({"type": "chassis-server"})
                                qualification.update({"first_chassis_id": qualif.min_id})
                                qualification.update({"last_chassis_id": qualif.max_id})
                                qualification["server_qualifications"] = []
                                if "computeSlotQual" in self._parent._config.sdk_objects:
                                    for slot_qualif in self._config.sdk_objects["computeSlotQual"]:
                                        if self._parent._dn + "/blade-qualifier-" + self.name + "/chassis-from-" + \
                                                qualif.min_id + "-to-" + qualif.max_id + "/" in slot_qualif.dn:
                                            slot_qualification = {}
                                            slot_qualification.update({"first_slot_id": slot_qualif.min_id})
                                            slot_qualification.update({"last_slot_id": slot_qualif.max_id})
                                            qualification["server_qualifications"].append(slot_qualification)
                                self.qualifications.append(qualification)

                if "adaptorQual" in self._parent._config.sdk_objects:
                    for qualif in self._config.sdk_objects["adaptorQual"]:
                        if self._parent._dn:
                            if self._parent._dn + "/blade-qualifier-" + self.name + "/" in qualif.dn:
                                qualification = {}
                                qualification.update({"type": "adapter"})
                                if "adaptorCapQual" in self._parent._config.sdk_objects:
                                    for adapt_qualif in self._config.sdk_objects["adaptorCapQual"]:
                                        if self._parent._dn + "/blade-qualifier-" + self.name + "/adaptor/cap-" \
                                                in adapt_qualif.dn:
                                            qualification.update({"adapter_maximum_capacity": adapt_qualif.maximum})
                                            qualification.update({"adapter_type": adapt_qualif.type})
                                            qualification.update({"adapter_pid": adapt_qualif.model})
                                self.qualifications.append(qualification)

                if "processorQual" in self._parent._config.sdk_objects:
                    for qualif in self._config.sdk_objects["processorQual"]:
                        if self._parent._dn:
                            if self._parent._dn + "/blade-qualifier-" + self.name + "/" in qualif.dn:
                                qualification = {}
                                qualification.update({"type": "cpu-cores"})
                                qualification.update({"min_cores": qualif.min_cores})
                                qualification.update({"max_cores": qualif.max_cores})
                                qualification.update({"min_threads": qualif.min_threads})
                                qualification.update({"max_threads": qualif.max_threads})
                                qualification.update({"processor_architecture": qualif.arch})
                                qualification.update({"processor_pid": qualif.model})
                                qualification.update({"cpu_speed": qualif.speed})
                                qualification.update({"cpu_stepping": qualif.stepping})
                                self.qualifications.append(qualification)

                if "memoryQual" in self._parent._config.sdk_objects:
                    for qualif in self._config.sdk_objects["memoryQual"]:
                        if self._parent._dn:
                            if self._parent._dn + "/blade-qualifier-" + self.name + "/" in qualif.dn:
                                qualification = {}
                                qualification.update({"type": "memory"})
                                qualification.update({"min_cap": qualif.min_cap})
                                qualification.update({"max_cap": qualif.max_cap})
                                qualification.update({"clock": qualif.clock})
                                qualification.update({"latency": qualif.latency})
                                qualification.update({"width": qualif.width})
                                qualification.update({"units": qualif.units})
                                self.qualifications.append(qualification)

                if "storageQual" in self._parent._config.sdk_objects:
                    for qualif in self._config.sdk_objects["storageQual"]:
                        if self._parent._dn:
                            if self._parent._dn + "/blade-qualifier-" + self.name + "/" in qualif.dn:
                                qualification = {}
                                qualification.update({"type": "storage"})
                                qualification.update({"min_cap": qualif.min_cap})
                                qualification.update({"max_cap": qualif.max_cap})
                                qualification.update({"disk_type": qualif.disk_type})
                                qualification.update({"diskless": qualif.diskless})
                                qualification.update({"number_of_blocks": qualif.number_of_blocks})
                                qualification.update({"block_size": qualif.block_size})
                                qualification.update({"units": qualif.units})
                                qualification.update({"per_disk_cap": qualif.per_disk_cap})
                                qualification.update({"number_of_flexflash_cards": qualif.number_of_flex_flash_cards})
                                self.qualifications.append(qualification)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

                # We need to set all values that are not present in the config file to None
                for element in self.qualifications:
                    for value in ["type", "server_pid", "last_slot_id", "first_slot_id", "adapter_maximum_capacity",
                                  "adapter_type", "adapter_pid", "min_cores", "max_cores", "processor_architecture",
                                  "processor_pid", "min_cap", "max_cap", "per_disk_cap", "number_of_flexflash_cards",
                                  "units", "block_size", "number_of_blocks", "diskless", "disk_type", "min_threads",
                                  "max_threads", "cpu_speed", "cpu_stepping", "first_chassis_id", "last_chassis_id",
                                  "clock", "latency", "width", "power_group"]:
                        if value not in element:
                            element[value] = None

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

                if qualification["type"] == "rack":
                    last_slot_id = None
                    if "number_of_slots" in qualification:
                        last_slot_id = str(int(qualification['first_slot_id']) +
                                           int(qualification['number_of_slots']) - 1)
                    elif "last_slot_id" in qualification:
                        last_slot_id = qualification['last_slot_id']
                    ComputeRackQual(parent_mo_or_dn=mo_compute_qual, min_id=qualification['first_slot_id'],
                                    max_id=last_slot_id)

                if qualification["type"] == "power_group":
                    PowerGroupQual(parent_mo_or_dn=mo_compute_qual, group_name=qualification["power_group"])

                if qualification["type"] == "chassis-server":
                    last_chassis_id = None
                    if "number_of_chassis" in qualification:
                        last_chassis_id = str(int(qualification['first_chassis_id']) +
                                              int(qualification['number_of_chassis']) - 1)
                    elif "last_chassis_id" in qualification:
                        last_chassis_id = qualification['last_chassis_id']
                    mo_chassis_qual = ComputeChassisQual(parent_mo_or_dn=mo_compute_qual,
                                                         min_id=qualification['first_chassis_id'],
                                                         max_id=last_chassis_id)
                    if 'server_qualifications' in qualification:
                        for slot_id_range in qualification['server_qualifications']:
                            last_slot_id = None
                            if "number_of_slots" in slot_id_range:
                                last_slot_id = str(int(slot_id_range['first_slot_id']) +
                                                   int(slot_id_range['number_of_slots']) - 1)
                            elif "last_slot_id" in slot_id_range:
                                last_slot_id = slot_id_range['last_slot_id']
                            ComputeSlotQual(parent_mo_or_dn=mo_chassis_qual, max_id=last_slot_id,
                                            min_id=slot_id_range['first_slot_id'])

                if qualification["type"] == "adapter":
                    mo_adaptor_qual = AdaptorQual(parent_mo_or_dn=mo_compute_qual)
                    AdaptorCapQual(parent_mo_or_dn=mo_adaptor_qual, maximum=qualification['adapter_maximum_capacity'],
                                   type=qualification['adapter_type'], model=qualification['adapter_pid'])

                if qualification["type"] == "cpu-cores":
                    ProcessorQual(parent_mo_or_dn=mo_compute_qual, min_cores=qualification['min_cores'],
                                  max_cores=qualification['max_cores'], min_threads=qualification['min_threads'],
                                  max_threads=qualification['max_threads'], speed=qualification['cpu_speed'],
                                  arch=qualification['processor_architecture'], model=qualification['processor_pid'],
                                  stepping=qualification['cpu_stepping'])

                if qualification["type"] == "memory":
                    MemoryQual(parent_mo_or_dn=mo_compute_qual, min_cap=qualification['min_cap'],
                               max_cap=qualification['max_cap'], clock=qualification['clock'],
                               latency=qualification['latency'], width=qualification['width'],
                               units=qualification['units'])

                if qualification["type"] == "storage":
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


class UcsSystemPowerSyncPolicy(UcsSystemConfigObject):
    _CONFIG_NAME = "Power Sync Policy"
    _UCS_SDK_OBJECT_NAME = "computePowerSyncPolicy"

    def __init__(self, parent=None, json_content=None, compute_power_sync_policy=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
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

        mo_power_sync_policy = ComputePowerSyncPolicy(parent_mo_or_dn=parent_mo,
                                                      name=self.name,
                                                      sync_option=sync_option,
                                                      descr=self.descr)

        self._handle.add_mo(mo=mo_power_sync_policy, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True


class UcsSystemHostFirmwarePackage(UcsSystemConfigObject):
    _CONFIG_NAME = "Host Firmware Package"
    _UCS_SDK_OBJECT_NAME = "firmwareComputeHostPack"

    def __init__(self, parent=None, json_content=None, firmware_compute_host_pack=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.name = None
        self.descr = None
        self.blade_package = None
        self.rack_package = None
        self.service_pack = None
        self.excluded_components = []
        self.advanced_host_firmware_package = []

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

                # We only fetch Advanced Host Firmware Package info if blade_package and rack_package are not set
                if not self.blade_package and not self.rack_package:
                    self.blade_package = None
                    self.rack_package = None
                    self.service_pack = None
                    self.excluded_components = []

                    if "firmwarePackItem" in self._parent._config.sdk_objects:
                        for item in self._config.sdk_objects["firmwarePackItem"]:
                            if self._parent._dn:
                                if self._parent._dn + "/fw-host-pack-" + self.name + "/" in item.dn:
                                    pack_item = {}
                                    pack_item.update({"vendor": item.hw_vendor})
                                    pack_item.update({"model": item.hw_model})
                                    pack_item.update({"type": item.type})
                                    pack_item.update({"version": item.version})
                                    self.advanced_host_firmware_package.append(pack_item)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

                # We need to set all values that are not present in the config file to None
                for element in self.advanced_host_firmware_package:
                    for value in ["vendor", "model", "type", "version"]:
                        if value not in element:
                            element[value] = None

        self.clean_object()

        # We need an exception to clean_object() to help the JSON Schema to distinguish what schema to check
        if not self.blade_package and not self.rack_package and not self.advanced_host_firmware_package:
            self.blade_package = ""
            self.rack_package = ""

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

        # Checks if the Blade/Rack Package versions are already present on the UCS System
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

        for excluded in self.excluded_components:
            # Perform various renaming operations to conform to SDK expected input
            if excluded == "adapter":
                excluded = "adaptor"
            elif excluded == "bios":
                excluded = "blade-bios"
            elif excluded == "cimc":
                excluded = "blade-controller"
            elif excluded == "gpus":
                excluded = "graphics-card"
            elif excluded == "fc-adapters":
                excluded = "host-hba"
            elif excluded == "hba-optionrom":
                excluded = "host-hba-optionrom"
            elif excluded == "nvme-mswitch-fw":
                excluded = "nvme-mswitch"
            elif excluded == "sas-expander-regular-fw":
                excluded = "sas-exp-reg-fw"
            elif excluded == "storage-device-bridge":
                excluded = "storage-dev-bridge"
            FirmwareExcludeServerComponent(parent_mo_or_dn=mo_firmware_host_pack, server_component=excluded)

        for item in self.advanced_host_firmware_package:
            FirmwarePackItem(parent_mo_or_dn=mo_firmware_host_pack,
                             hw_vendor=item["vendor"], type=item["type"], version=item["version"],
                             hw_model=item["model"])

        self._handle.add_mo(mo=mo_firmware_host_pack, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True

    def _is_firmware_package_present(self):
        """
        Checks if the firmware package is present in the UCS System

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


class UcsSystemIpmiAccessProfile(UcsSystemConfigObject):
    _CONFIG_NAME = "IPMI Access Profile"
    _UCS_SDK_OBJECT_NAME = "aaaEpAuthProfile"

    def __init__(self, parent=None, json_content=None, aaa_ep_auth_profile=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
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


class UcsSystemKvmManagementPolicy(UcsSystemConfigObject):
    _CONFIG_NAME = "KVM Management Policy"
    _UCS_SDK_OBJECT_NAME = "computeKvmMgmtPolicy"

    def __init__(self, parent=None, json_content=None, compute_kvm_mgmt_policy=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.name = None
        self.descr = None
        self.vmedia_encryption = None

        if self._config.load_from == "live":
            if compute_kvm_mgmt_policy is not None:
                self.name = compute_kvm_mgmt_policy.name
                self.descr = compute_kvm_mgmt_policy.descr
                self.vmedia_encryption = compute_kvm_mgmt_policy.vmedia_encryption

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

        mo_compute_kvm_mgmt_policy = ComputeKvmMgmtPolicy(parent_mo_or_dn=parent_mo, name=self.name, descr=self.descr,
                                                          vmedia_encryption=self.vmedia_encryption)

        self._handle.add_mo(mo=mo_compute_kvm_mgmt_policy, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True


class UcsSystemScrubPolicy(UcsSystemConfigObject):
    _CONFIG_NAME = "Scrub Policy"
    _UCS_SDK_OBJECT_NAME = "computeScrubPolicy"

    def __init__(self, parent=None, json_content=None, compute_scrub_policy=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.name = None
        self.disk_scrub = None
        self.flexflash_scrub = None
        self.bios_settings_scrub = None
        self.descr = None

        if self._config.load_from == "live":
            if compute_scrub_policy is not None:
                self.name = compute_scrub_policy.name
                self.descr = compute_scrub_policy.descr
                self.disk_scrub = compute_scrub_policy.disk_scrub
                self.flexflash_scrub = compute_scrub_policy.flex_flash_scrub
                self.bios_settings_scrub = compute_scrub_policy.bios_settings_scrub

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
                                                     descr=self.descr)

        self._handle.add_mo(mo=mo_compute_scrub_policy, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True


class UcsSystemSerialOverLanPolicy(UcsSystemConfigObject):
    _CONFIG_NAME = "Serial Over LAN Policy"
    _UCS_SDK_OBJECT_NAME = "solPolicy"

    def __init__(self, parent=None, json_content=None, sol_policy=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
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

        mo_sol_policy = SolPolicy(parent_mo_or_dn=parent_mo,
                                  speed=self.speed,
                                  name=self.name,
                                  admin_state=self.serial_over_lan_state,
                                  descr=self.descr)

        self._handle.add_mo(mo=mo_sol_policy, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True


class UcsSystemBootPolicy(UcsSystemConfigObject):
    _CONFIG_NAME = "Boot Policy"
    _UCS_SDK_OBJECT_NAME = "lsbootPolicy"

    def __init__(self, parent=None, json_content=None, lsboot_policy=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
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

                if "lsbootBootSecurity" in self._parent._config.sdk_objects:
                    for boot_security in self._config.sdk_objects["lsbootBootSecurity"]:
                        if self._parent._dn:
                            if self._parent._dn + "/boot-policy-" + self.name + "/" in boot_security.dn:
                                self.boot_security = boot_security.secure_boot

                if "lsbootVirtualMedia" in self._parent._config.sdk_objects:
                    for boot_media in self._config.sdk_objects["lsbootVirtualMedia"]:
                        if self._parent._dn:
                            if self._parent._dn + "/boot-policy-" + self.name + "/" in boot_media.dn:
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
                        if self._parent._dn + "/boot-policy-" + self.name + "/storage/local-storage/" in boot_nvme.dn:
                            device = {}
                            device.update({"order": boot_nvme.order})
                            device.update({"device_type": "nvme"})
                            self.boot_order.append(device)
                if "lsbootLan" in self._parent._config.sdk_objects:
                    for boot_media in self._config.sdk_objects["lsbootLan"]:
                        if self._parent._dn:
                            if self._parent._dn + "/boot-policy-" + self.name + "/" in boot_media.dn:
                                device = {}
                                device.update({"device_type": "lan"})
                                device.update({"order": boot_media.order})
                                device.update({"vnics": None})
                                if "lsbootLanImagePath" in self._parent._config.sdk_objects:
                                    device["vnics"] = []
                                    for vnic in self._config.sdk_objects["lsbootLanImagePath"]:
                                        if self._parent._dn + "/boot-policy-" + self.name + "/" in vnic.dn:
                                            image = {}
                                            image.update({"type": vnic.type})
                                            image.update({"name": vnic.vnic_name})
                                            image.update({"ip_address_type": vnic.ip_addr_type})
                                            device["vnics"].append(image)
                                if device:
                                    self.boot_order.append(device)

                if "lsbootIScsi" in self._parent._config.sdk_objects:
                    for boot_iscsi in self._config.sdk_objects["lsbootIScsi"]:
                        if self._parent._dn + "/boot-policy-" + self.name + "/" in boot_iscsi.dn:
                            device = {}
                            device.update({"order": boot_iscsi.order})
                            device.update({"device_type": "iscsi"})
                            if "lsbootIScsiImagePath" in self._parent._config.sdk_objects:
                                device["iscsi_vnics"] = []
                                for boot_iscsi_img in self._config.sdk_objects["lsbootIScsiImagePath"]:
                                    if self._parent._dn + "/boot-policy-" + self.name + "/" in boot_iscsi_img.dn:
                                        image = {}
                                        image.update({"name": boot_iscsi_img.i_scsi_vnic_name})
                                        image.update({"type": boot_iscsi_img.type})
                                        if "lsbootUEFIBootParam" in self._parent._config.sdk_objects:
                                            for boot_iscsi_img_boot_param in \
                                                    self._config.sdk_objects["lsbootIScsiImagePath"]:
                                                if self._parent._dn + "/boot-policy-" + self.name + "/iscsi/path-" + \
                                                        boot_iscsi_img.type + "/" in boot_iscsi_img_boot_param.dn:
                                                    image.update({"boot_loader_name": boot_iscsi_img.boot_loader_name})
                                                    image.update({"boot_loader_path": boot_iscsi_img.boot_loader_path})
                                                    image.update(
                                                        {"boot_loader_description": boot_iscsi_img.boot_description})
                                        device["iscsi_vnics"].append(image)
                            self.boot_order.append(device)
                if "lsbootEFIShell" in self._parent._config.sdk_objects:
                    for boot_efi in self._config.sdk_objects["lsbootEFIShell"]:
                        if self._parent._dn + "/boot-policy-" + self.name + "/" in boot_efi.dn:
                            device = {}
                            device.update({"order": boot_efi.order})
                            device.update({"device_type": "efi_shell"})
                            self.boot_order.append(device)
                if "lsbootDefaultLocalImage" in self._parent._config.sdk_objects:
                    for image in self._config.sdk_objects["lsbootDefaultLocalImage"]:
                        if self._parent._dn + "/boot-policy-" + self.name + "/storage/local-storage/local-any" \
                                in image.dn:
                            device = {}
                            device.update({"order": image.order})
                            device.update({"device_type": "local_disk"})
                            self.boot_order.append(device)
                if "lsbootLocalHddImage" in self._parent._config.sdk_objects:
                    for image in self._config.sdk_objects["lsbootLocalHddImage"]:
                        if self._parent._dn + "/boot-policy-" + self.name + "/storage/local-storage/local-hdd" \
                                in image.dn:
                            device = {}
                            device.update({"order": image.order})
                            device.update({"device_type": "local_lun"})
                            device.update({"local_luns": None})
                            if "lsbootLocalLunImagePath" in self._parent._config.sdk_objects:
                                device["local_luns"] = []
                                for image_path in self._config.sdk_objects["lsbootLocalLunImagePath"]:
                                    if self._parent._dn + "/boot-policy-" + self.name + \
                                            "/storage/local-storage/local-hdd/lunimgpath-" in image_path.dn:
                                        lun = {}
                                        lun.update({"type": image_path.type})
                                        lun.update({"name": image_path.lun_name})
                                        if "lsbootUEFIBootParam" in self._parent._config.sdk_objects:
                                            for boot_disk_img_boot_param \
                                                    in self._config.sdk_objects["lsbootUEFIBootParam"]:
                                                if self._parent._dn + "/boot-policy-" + \
                                                        self.name + "/storage/local-storage/local-hdd/lunimgpath-" + \
                                                        image_path.type + "/" in boot_disk_img_boot_param.dn:
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
                        if self._parent._dn + "/boot-policy-" + self.name + "/storage/local-storage/local-jbod" \
                                in image.dn:
                            device = {}
                            device.update({"order": image.order})
                            device.update({"device_type": "local_jbod"})
                            device.update({"local_jbods": None})
                            if "lsbootLocalDiskImagePath" in self._parent._config.sdk_objects:
                                device["local_jbods"] = []
                                for image_path in self._config.sdk_objects["lsbootLocalDiskImagePath"]:
                                    if self._parent._dn + "/boot-policy-" + self.name + \
                                            "/storage/local-storage/local-jbod/diskimgpath-" in image_path.dn:
                                        jbod = {}
                                        jbod.update({"slot_number": image_path.slot_number})
                                        device["local_jbods"].append(jbod)
                            self.boot_order.append(device)
                if "lsbootUsbFlashStorageImage" in self._parent._config.sdk_objects:
                    for image in self._config.sdk_objects["lsbootUsbFlashStorageImage"]:
                        if self._parent._dn + "/boot-policy-" + self.name + "/storage/local-storage/sd" in image.dn:
                            device = {}
                            device.update({"order": image.order})
                            device.update({"device_type": "sd_card"})
                            self.boot_order.append(device)
                if "lsbootUsbInternalImage" in self._parent._config.sdk_objects:
                    for image in self._config.sdk_objects["lsbootUsbInternalImage"]:
                        if self._parent._dn + "/boot-policy-" + self.name + "/storage/local-storage/usb-intern" \
                                in image.dn:
                            device = {}
                            device.update({"order": image.order})
                            device.update({"device_type": "internal_usb"})
                            self.boot_order.append(device)
                if "lsbootUsbExternalImage" in self._parent._config.sdk_objects:
                    for image in self._config.sdk_objects["lsbootUsbExternalImage"]:
                        if self._parent._dn + "/boot-policy-" + self.name + "/storage/local-storage/usb-extern" \
                                in image.dn:
                            device = {}
                            device.update({"order": image.order})
                            device.update({"device_type": "external_usb"})
                            self.boot_order.append(device)
                if "lsbootEmbeddedLocalLunImage" in self._parent._config.sdk_objects:
                    for image in self._config.sdk_objects["lsbootEmbeddedLocalLunImage"]:
                        if self._parent._dn + "/boot-policy-" + self.name + \
                                "/storage/local-storage/embedded-local-lun" in image.dn:
                            device = {}
                            device.update({"order": image.order})
                            device.update({"device_type": "embedded_local_lun"})
                            device.update({"embedded_local_luns": None})
                            if "lsbootUEFIBootParam" in self._parent._config.sdk_objects:
                                device["embedded_local_luns"] = []
                                for boot_disk_img_boot_param in self._config.sdk_objects["lsbootUEFIBootParam"]:
                                    if self._parent._dn + "/boot-policy-" + self.name + \
                                            "/storage/local-storage/embedded-local-lun/" in boot_disk_img_boot_param.dn:
                                        lun = {}
                                        lun.update({"boot_loader_name": boot_disk_img_boot_param.boot_loader_name})
                                        lun.update({"boot_loader_path": boot_disk_img_boot_param.boot_loader_path})
                                        lun.update({"boot_loader_description":
                                                        boot_disk_img_boot_param.boot_description})
                                        device["embedded_local_luns"].append(lun)
                            self.boot_order.append(device)
                if "lsbootEmbeddedLocalDiskImage" in self._parent._config.sdk_objects:
                    for image in self._config.sdk_objects["lsbootEmbeddedLocalDiskImage"]:
                        if self._parent._dn + "/boot-policy-" + \
                                self.name + "/storage/local-storage/embedded-local-jbod" in image.dn:
                            device = {}
                            device.update({"order": image.order})
                            device.update({"device_type": "embedded_local_disk"})
                            device.update({"embedded_local_disks": None})
                            if "lsbootEmbeddedLocalDiskImagePath" in self._parent._config.sdk_objects:
                                device["embedded_local_disks"] = []
                                for image_path in self._config.sdk_objects["lsbootEmbeddedLocalDiskImagePath"]:
                                    if self._parent._dn + "/boot-policy-" + self.name + \
                                            "/storage/local-storage/embedded-local-jbod/diskimgpath-" in image_path.dn:
                                        disk = {}
                                        disk.update({"type": image_path.type})
                                        disk.update({"slot_number": image_path.slot_number})
                                        if "lsbootUEFIBootParam" in self._parent._config.sdk_objects:
                                            for boot_disk_img_boot_param \
                                                    in self._config.sdk_objects["lsbootUEFIBootParam"]:
                                                if self._parent._dn + "/boot-policy-" + self.name + \
                                                        "/storage/local-storage/embedded-local-jbod/diskimgpath-" + \
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
                        if self._parent._dn:
                            if self._parent._dn + "/boot-policy-" + self.name + "/san" in boot_media.dn:
                                device = {}
                                device.update({"device_type": "san"})
                                device.update({"order": boot_media.order})
                                device.update({"vhbas": None})
                                if "lsbootSanCatSanImage" in self._parent._config.sdk_objects:
                                    device["vhbas"] = []
                                    for vhba in self._config.sdk_objects["lsbootSanCatSanImage"]:
                                        if self._parent._dn + "/boot-policy-" + self.name + "/san/" in vhba.dn:
                                            image = {}
                                            image.update({"type": vhba.type})
                                            image.update({"name": vhba.vnic_name})
                                            if "lsbootSanCatSanImagePath" in self._parent._config.sdk_objects:
                                                image["targets"] = []
                                                for target in self._config.sdk_objects["lsbootSanCatSanImagePath"]:
                                                    if self._parent._dn + "/boot-policy-" + self.name + "/san/sanimg-" \
                                                            + vhba.type in target.dn:
                                                        image_path = {}
                                                        image_path.update({"type": target.type})
                                                        image_path.update({"lun": target.lun})
                                                        image_path.update({"wwpn": target.wwn})
                                                        image["targets"].append(image_path)
                                                        if "lsbootUEFIBootParam" in self._parent._config.sdk_objects:
                                                            for boot_san_img_boot_param in \
                                                                    self._config.sdk_objects["lsbootUEFIBootParam"]:
                                                                if self._parent._dn + "/boot-policy-" + self.name + \
                                                                        "/san/sanimg-" + vhba.type + "/sanimgpath-" + \
                                                                        target.type in boot_san_img_boot_param.dn:
                                                                    image_path.update({
                                                                        "boot_loader_name":
                                                                            boot_san_img_boot_param.boot_loader_name})
                                                                    image_path.update({
                                                                        "boot_loader_path":
                                                                            boot_san_img_boot_param.boot_loader_path})
                                                                    image_path.update({
                                                                        "boot_loader_description":
                                                                            boot_san_img_boot_param.boot_description})
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
                                             "boot_loader_description"]:
                                if subvalue not in vnic:
                                    vnic[subvalue] = None
                    if element["vnics"]:
                        for vnic in element["vnics"]:
                            for subvalue in ["name", "type", "ip_address_type"]:
                                if subvalue not in vnic:
                                    vnic[subvalue] = None

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

        mo_ls_boot_policy = LsbootPolicy(parent_mo_or_dn=parent_mo, descr=self.descr,
                                         reboot_on_update=self.reboot_on_boot_order_change, name=self.name,
                                         boot_mode=self.boot_mode, enforce_vnic_name=self.enforce_vnic_name)
        LsbootBootSecurity(parent_mo_or_dn=mo_ls_boot_policy, secure_boot=self.boot_security)
        self._handle.add_mo(mo=mo_ls_boot_policy, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False

        # Repeat of mo_ls_boot_policy - A bug occurred if the mo is committed and not repeated
        mo_ls_boot_policy = LsbootPolicy(parent_mo_or_dn=parent_mo, name=self.name)
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
            elif device['device_type'] == 'local_disk':
                mo_boot_storage = LsbootStorage(parent_mo_or_dn=mo_ls_boot_policy)
                mo_boot_local_storage = LsbootLocalStorage(parent_mo_or_dn=mo_boot_storage)
                LsbootDefaultLocalImage(parent_mo_or_dn=mo_boot_local_storage, order=device['order'])
            elif device['device_type'] == 'local_lun':
                mo_boot_storage = LsbootStorage(parent_mo_or_dn=mo_ls_boot_policy)
                mo_boot_local_storage = LsbootLocalStorage(parent_mo_or_dn=mo_boot_storage)
                mo_hdd_image = LsbootLocalHddImage(parent_mo_or_dn=mo_boot_local_storage, order=device['order'])
                if device["local_luns"]:
                    for lun in device["local_luns"]:
                        mo_local_lun = LsbootLocalLunImagePath(parent_mo_or_dn=mo_hdd_image, type=lun['type'],
                                                               lun_name=lun['name'])
                        LsbootUEFIBootParam(parent_mo_or_dn=mo_local_lun, boot_loader_path=lun["boot_loader_path"],
                                            boot_loader_name=lun["boot_loader_name"],
                                            boot_description=lun["boot_loader_description"])
            elif device['device_type'] == 'local_jbod':
                mo_boot_storage = LsbootStorage(parent_mo_or_dn=mo_ls_boot_policy)
                mo_boot_local_storage = LsbootLocalStorage(parent_mo_or_dn=mo_boot_storage)
                mo_disk_image = LsbootLocalDiskImage(parent_mo_or_dn=mo_boot_local_storage, order=device['order'])
                if device["local_jbods"]:
                    for jbod in device["local_jbods"]:
                        LsbootLocalDiskImagePath(parent_mo_or_dn=mo_disk_image, type="primary", 
                                                 slot_number=jbod['slot_number'])
            elif device['device_type'] == 'sd_card':
                mo_boot_storage = LsbootStorage(parent_mo_or_dn=mo_ls_boot_policy)
                mo_boot_local_storage = LsbootLocalStorage(parent_mo_or_dn=mo_boot_storage)
                LsbootUsbFlashStorageImage(parent_mo_or_dn=mo_boot_local_storage, order=device['order'])
            elif device['device_type'] == 'internal_usb':
                mo_boot_storage = LsbootStorage(parent_mo_or_dn=mo_ls_boot_policy)
                mo_boot_local_storage = LsbootLocalStorage(parent_mo_or_dn=mo_boot_storage)
                LsbootUsbInternalImage(parent_mo_or_dn=mo_boot_local_storage, order=device['order'])
            elif device['device_type'] == 'external_usb':
                mo_boot_storage = LsbootStorage(parent_mo_or_dn=mo_ls_boot_policy)
                mo_boot_local_storage = LsbootLocalStorage(parent_mo_or_dn=mo_boot_storage)
                LsbootUsbExternalImage(parent_mo_or_dn=mo_boot_local_storage, order=device['order'])
            elif device['device_type'] == 'embedded_local_lun':
                mo_boot_storage = LsbootStorage(parent_mo_or_dn=mo_ls_boot_policy)
                mo_boot_local_storage = LsbootLocalStorage(parent_mo_or_dn=mo_boot_storage)
                mo_embedded_local_lun = LsbootEmbeddedLocalLunImage(parent_mo_or_dn=mo_boot_local_storage,
                                                                    order=device['order'])
                if device["embedded_local_luns"]:
                    for lun in device["embedded_local_luns"]:
                        LsbootUEFIBootParam(parent_mo_or_dn=mo_embedded_local_lun,
                                            boot_loader_path=lun["boot_loader_path"],
                                            boot_loader_name=lun["boot_loader_name"],
                                            boot_description=lun["boot_loader_description"])
            elif device['device_type'] == 'embedded_local_disk':
                mo_boot_storage = LsbootStorage(parent_mo_or_dn=mo_ls_boot_policy)
                mo_boot_local_storage = LsbootLocalStorage(parent_mo_or_dn=mo_boot_storage)
                mo_embedded_local = LsbootEmbeddedLocalDiskImage(parent_mo_or_dn=mo_boot_local_storage,
                                                                 order=device['order'])
                if device["embedded_local_disks"]:
                    for disk in device["embedded_local_disks"]:
                        mo_emb_disk_img_path = LsbootEmbeddedLocalDiskImagePath(parent_mo_or_dn=mo_embedded_local,
                                                                                type=disk['type'],
                                                                                slot_number=disk['slot_number'])
                        LsbootUEFIBootParam(parent_mo_or_dn=mo_emb_disk_img_path,
                                            boot_loader_path=device["boot_loader_path"],
                                            boot_loader_name=device["boot_loader_name"],
                                            boot_description=device["boot_loader_description"])
            elif device['device_type'] == "nvme":
                mo_boot_storage = LsbootStorage(parent_mo_or_dn=mo_ls_boot_policy)
                mo_boot_local_storage = LsbootLocalStorage(parent_mo_or_dn=mo_boot_storage)
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
                LsbootVirtualMedia(parent_mo_or_dn=mo_ls_boot_policy, order=device['order'],
                                   access="read-only-remote-cimc")
            elif device['device_type'] == "cimc_mounted_hdd":
                LsbootVirtualMedia(parent_mo_or_dn=mo_ls_boot_policy, order=device['order'],
                                   access="read-write-remote-cimc")
            elif device['device_type'] == "iscsi":
                mo_boot_iscsi = LsbootIScsi(parent_mo_or_dn=mo_ls_boot_policy, order=device['order'])
                if device["iscsi_vnics"]:
                    for vnic in device["iscsi_vnics"]:
                        mo_boot_iscsi_image = LsbootIScsiImagePath(parent_mo_or_dn=mo_boot_iscsi,
                                                                   type=vnic["type"],
                                                                   i_scsi_vnic_name=vnic["name"])
                        LsbootUEFIBootParam(parent_mo_or_dn=mo_boot_iscsi_image,
                                            boot_loader_path=vnic["boot_loader_path"],
                                            boot_loader_name=vnic["boot_loader_name"],
                                            boot_description=vnic["boot_loader_description"])
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
            if self.commit(detail=self.name + ' devices') != True:
                return False
        return True


class UcsSystemVnicVhbaPlacementPolicy(UcsSystemConfigObject):
    _CONFIG_NAME = "vNIC/vHBA Placement Policy"
    _UCS_SDK_OBJECT_NAME = "fabricVConProfile"

    def __init__(self, parent=None, json_content=None, fabric_v_con_profile=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.name = None
        self.virtual_slot_mapping_scheme = None
        self.virtual_host_interfaces = []

        if self._config.load_from == "live":
            if fabric_v_con_profile is not None:
                self.name = fabric_v_con_profile.name
                self.virtual_slot_mapping_scheme = fabric_v_con_profile.mezz_mapping

                if "fabricVCon" in self._parent._config.sdk_objects:
                    for fabric_vcon in self._config.sdk_objects["fabricVCon"]:
                        if self._parent._dn + "/vcon-profile-" + self.name + "/vcon" in fabric_vcon.dn:
                            virtual_host_interface = {}
                            virtual_host_interface.update({"virtual_slot": fabric_vcon.id})
                            virtual_host_interface.update({"selection_preference": fabric_vcon.select})
                            virtual_host_interface.update({"transport": fabric_vcon.transport})
                            self.virtual_host_interfaces.append(virtual_host_interface)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

                # We need to set all values that are not present in the config file to None
                for element in self.virtual_host_interfaces:
                    for value in ["virtual_slot", "selection_preference", "transport"]:
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

        mo_fabric_vcon_profile = FabricVConProfile(parent_mo_or_dn=parent_mo,
                                                   mezz_mapping=self.virtual_slot_mapping_scheme,
                                                   name=self.name)

        for virtual_slot in self.virtual_host_interfaces:
            FabricVCon(parent_mo_or_dn=mo_fabric_vcon_profile,
                       id=virtual_slot["virtual_slot"],
                       select=virtual_slot["selection_preference"],
                       transport=virtual_slot["transport"])

        self._handle.add_mo(mo=mo_fabric_vcon_profile, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True


class UcsSystemBiosPolicy(UcsSystemConfigObject):
    _CONFIG_NAME = "BIOS Policy"
    _UCS_SDK_OBJECT_NAME = "biosVProfile"
    _BIOS_TOKENS_MIN_REQUIRED_VERSION = UcsVersion("3.2(1d)")

    def __init__(self, parent=None, json_content=None, bios_v_profile=None):
        UcsSystemConfigObject.__init__(self, parent=parent)

        bios_table = self.get_bios_table()
        if not bios_table:
            self.logger(level="error", message="BIOS Table not imported.")

        self.name = None
        self.descr = None
        self.reboot_on_bios_settings_change = None

        self._bios_token_method = False

        # Set all the bios options
        if bios_table:
            for attr in bios_table:
                setattr(self, attr, None)

        if self._config.load_from == "live":

            # We check what type of method is used to create the BIOS policy depending on the version of UCS Manager
            # The BIOS Token method is the newest method
            if self._device.version.__ge__(self._BIOS_TOKENS_MIN_REQUIRED_VERSION):
                self._bios_token_method = True

            if bios_v_profile is not None:
                self.name = bios_v_profile.name
                self.reboot_on_bios_settings_change = bios_v_profile.reboot_on_update
                self.descr = bios_v_profile.descr

                if self._bios_token_method and bios_table:
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
                                                                     if bios_token_param.dn in child.dn]
                                bios_token_value = None
                                for bios_token_settings_child in bios_token_settings_children_list:
                                    # We first try to determine the bios_token_name as defined in our BIOS Table
                                    bios_token_name = None
                                    for bios_table_key, bios_table_values in bios_table.items():
                                        if bios_table_values["target_name"] == bios_token_param.target_token_name:
                                            bios_token_name = bios_table_key
                                            # Since we have found the right BIOS Token name, we exit the for loop
                                            continue
                                    if bios_token_name:
                                        if bios_token_settings_child.is_assigned == "yes":
                                            bios_token_value = bios_token_settings_child.settings_mo_rn
                                            setattr(self, bios_token_name, bios_token_value)
                                            # Since we have found the right BIOS Token value, we exit the for loop
                                            continue
                                    else:
                                        self.logger(level="warning", message="BIOS Param name " +
                                                                             bios_token_param.param_name + " not found")
                                if bios_token_name and not bios_token_value:
                                    setattr(self, bios_token_name, "platform-default")

                else:
                    if "biosVfQuietBoot" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfQuietBoot"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.quiet_boot = policy.vp_quiet_boot

                    if "biosVfPOSTErrorPause" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfPOSTErrorPause"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.post_error_pause = policy.vp_post_error_pause

                    if "biosVfResumeOnACPowerLoss" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfResumeOnACPowerLoss"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.resume_on_ac_power_loss = policy.vp_resume_on_ac_power_loss

                    if "biosVfFrontPanelLockout" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfFrontPanelLockout"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.front_panel_lockout = policy.vp_front_panel_lockout

                    if "biosVfConsistentDeviceNameControl" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfConsistentDeviceNameControl"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.cdn_control = policy.vp_cdn_control

                    # Processor
                    if "biosVfIntelTurboBoostTech" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfIntelTurboBoostTech"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.intel_turbo_boost_tech = policy.vp_intel_turbo_boost_tech

                    if "biosVfEnhancedIntelSpeedStepTech" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfEnhancedIntelSpeedStepTech"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.enhanced_intel_speedstep_tech = policy.vp_enhanced_intel_speed_step_tech

                    if "biosVfIntelHyperThreadingTech" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfIntelHyperThreadingTech"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.intel_hyperthreading_tech = policy.vp_intel_hyper_threading_tech

                    if "biosVfCoreMultiProcessing" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfCoreMultiProcessing"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.core_multi_processing = policy.vp_core_multi_processing

                    if "biosVfExecuteDisableBit" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfExecuteDisableBit"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.execute_disable_bit = policy.vp_execute_disable_bit

                    if "biosVfIntelVirtualizationTechnology" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfIntelVirtualizationTechnology"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.intel_virtualization_technology = policy.vp_intel_virtualization_technology

                    if "biosVfProcessorPrefetchConfig" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfProcessorPrefetchConfig"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.hardware_prefetcher = policy.vp_hardware_prefetcher
                                self.adjacent_cache_line_prefetcher = policy.vp_adjacent_cache_line_prefetcher
                                self.dcu_streamer_prefetch = policy.vp_dcu_streamer_prefetch
                                self.dcu_ip_prefetcher = policy.vp_dcuip_prefetcher

                    if "biosVfDirectCacheAccess" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfDirectCacheAccess"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.direct_cache_access = policy.vp_direct_cache_access

                    if "biosVfProcessorCState" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfProcessorCState"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.processor_c_state = policy.vp_processor_c_state

                    if "biosVfProcessorC1E" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfProcessorC1E"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.processor_c1e = policy.vp_processor_c1_e

                    if "biosVfProcessorC3Report" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfProcessorC3Report"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.processor_c3_report = policy.vp_processor_c3_report

                    if "biosVfProcessorC6Report" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfProcessorC6Report"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.processor_c6_report = policy.vp_processor_c6_report

                    if "biosVfProcessorC7Report" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfProcessorC7Report"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.processor_c7_report = policy.vp_processor_c7_report

                    if "biosVfProcessorCMCI" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfProcessorCMCI"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.processor_cmci = policy.vp_processor_cmci

                    if "biosVfCPUPerformance" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfCPUPerformance"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.cpu_performance = policy.vp_cpu_performance

                    if "biosVfMaxVariableMTRRSetting" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfMaxVariableMTRRSetting"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.max_variable_mtrr_setting = policy.vp_processor_mtrr

                    if "biosVfLocalX2Apic" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfLocalX2Apic"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.local_x2_apic = policy.vp_local_x2_apic

                    if "biosVfProcessorEnergyConfiguration" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfProcessorEnergyConfiguration"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.power_technology = policy.vp_power_technology
                                self.energy_performance = policy.vp_energy_performance

                    if "biosVfFrequencyFloorOverride" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfFrequencyFloorOverride"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.frequency_floor_override = policy.vp_frequency_floor_override

                    if "biosVfPSTATECoordination" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfPSTATECoordination"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.p_state_coordination = policy.vp_pstate_coordination

                    if "biosVfDRAMClockThrottling" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfDRAMClockThrottling"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.dram_clock_throttling = policy.vp_dram_clock_throttling

                    if "biosVfInterleaveConfiguration" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfInterleaveConfiguration"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.channel_interleaving = policy.vp_channel_interleaving
                                self.rank_interleaving = policy.vp_rank_interleaving
                                self.memory_interleaving = policy.vp_memory_interleaving

                    if "biosVfScrubPolicies" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfScrubPolicies"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.patrol_scrub = policy.vp_patrol_scrub
                                self.demand_scrub = policy.vp_demand_scrub

                    if "biosVfAltitude" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfAltitude"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.altitude = policy.vp_altitude

                    if "biosVfPackageCStateLimit" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfPackageCStateLimit"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.package_c_state_limit = policy.vp_package_c_state_limit

                    if "biosVfCPUHardwarePowerManagement" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfCPUHardwarePowerManagement"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.cpu_hardware_power_management = policy.vp_cpu_hardware_power_management

                    if "biosVfEnergyPerformanceTuning" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfEnergyPerformanceTuning"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.energy_performance_tuning = policy.vp_pwr_perf_tuning

                    if "biosVfWorkloadConfiguration" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfWorkloadConfiguration"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.workload_configuration = policy.vp_workload_configuration

                    if "biosVfWorkloadConfiguration" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfWorkloadConfiguration"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.workload_configuration = policy.vp_workload_configuration

                    # Intel Directed IO
                    if "biosVfIntelVTForDirectedIO" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfIntelVTForDirectedIO"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.intel_vt_for_directed_io = policy.vp_intel_vt_for_directed_io
                                self.intel_vtd_interrupt_remapping = policy.vp_intel_vtd_interrupt_remapping
                                self.intel_vtd_coherency_support = policy.vp_intel_vtd_coherency_support
                                self.intel_vtd_ats_support = policy.vp_intel_vtdats_support
                                self.intel_vtd_pass_through_dma_support = policy.vp_intel_vtd_pass_through_dma_support

                    # RAS Memory
                    if "biosVfSelectMemoryRASConfiguration" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfSelectMemoryRASConfiguration"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.memory_ras_configuration = policy.vp_select_memory_ras_configuration

                    if "biosVfNUMAOptimized" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfNUMAOptimized"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.numa_optimized = policy.vp_numa_optimized

                    if "biosVfMirroringMode" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfMirroringMode"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.mirroring_mode = policy.vp_mirroring_mode

                    if "biosVfLvDIMMSupport" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfLvDIMMSupport"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.lv_ddr_mode = policy.vp_lv_ddr_mode

                    if "biosVfDramRefreshRate" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfDramRefreshRate"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.dram_refresh_rate = policy.vp_dram_refresh_rate

                    if "biosVfDDR3VoltageSelection" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfDDR3VoltageSelection"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.ddr3_voltage_selection = policy.vp_dd_r3_voltage_selection

                    # Serial Port
                    if "biosVfSerialPortAEnable" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfSerialPortAEnable"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.serial_port_a_enable = policy.vp_serial_port_a_enable

                    if "biosVfUSBBootConfig" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfUSBBootConfig"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.make_device_non_bootable = policy.vp_make_device_non_bootable
                                self.legacy_usb_support = policy.vp_legacy_usb_support

                    if "biosVfUSBSystemIdlePowerOptimizingSetting" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfUSBSystemIdlePowerOptimizingSetting"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.usb_idle_power_optimizing = policy.vp_usb_idle_power_optimizing

                    if "biosVfUSBFrontPanelAccessLock" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfUSBFrontPanelAccessLock"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.usb_front_panel_access_lock = policy.vp_usb_front_panel_lock

                    if "biosVfUSBPortConfiguration" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfUSBPortConfiguration"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.port_60_64_emulation = policy.vp_port6064_emulation
                                self.usb_port_front = policy.vp_usb_port_front
                                self.usb_port_internal = policy.vp_usb_port_internal
                                self.usb_port_kvm = policy.vp_usb_port_kvm
                                self.usb_port_rear = policy.vp_usb_port_rear
                                self.usb_port_sd_card = policy.vp_usb_port_sd_card
                                self.usb_port_vmedia = policy.vp_usb_port_v_media

                    if "biosVfAllUSBDevices" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfAllUSBDevices"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.all_usb_devices = policy.vp_all_usb_devices

                    if "biosVfUSBConfiguration" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfUSBConfiguration"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.xhci_mode = policy.vp_xhci_mode

                    # PCI
                    if "biosVfMaximumMemoryBelow4GB" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfMaximumMemoryBelow4GB"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.maximum_memory_below_4gb = policy.vp_maximum_memory_below4_gb

                    if "biosVfMemoryMappedIOAbove4GB" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfMemoryMappedIOAbove4GB"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.memory_mapped_io_above_4gb = policy.vp_memory_mapped_io_above4_gb

                    if "biosVfVGAPriority" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfVGAPriority"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.vga_priority = policy.vp_vga_priority

                    if "biosVfASPMSupport" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfASPMSupport"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.aspm_support = policy.vp_aspm_support

                    # QPI
                    if "biosVfQPILinkFrequencySelect" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfQPILinkFrequencySelect"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.qpi_link_frequency_select = policy.vp_qpi_link_frequency_select
                                # Transform "8000" to "8.0-GT-s" : change the old naming to the new naming of the values
                                if str.isdigit(self.qpi_link_frequency_select):
                                    self.qpi_link_frequency_select = self.qpi_link_frequency_select[0] + "." + \
                                                                     self.qpi_link_frequency_select[1] + "-GT-s"

                    if "biosVfQPISnoopMode" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfQPISnoopMode"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.qpi_snoop_mode = policy.vp_qpi_snoop_mode

                    # LOM and PCIe Slots
                    if "biosVfPCISlotLinkSpeed" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfPCISlotLinkSpeed"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.pcie_slot_1_link_speed = policy.vp_pc_ie_slot1_link_speed
                                self.pcie_slot_2_link_speed = policy.vp_pc_ie_slot2_link_speed
                                self.pcie_slot_3_link_speed = policy.vp_pc_ie_slot3_link_speed
                                self.pcie_slot_4_link_speed = policy.vp_pc_ie_slot4_link_speed
                                self.pcie_slot_5_link_speed = policy.vp_pc_ie_slot5_link_speed
                                self.pcie_slot_6_link_speed = policy.vp_pc_ie_slot6_link_speed
                                self.pcie_slot_7_link_speed = policy.vp_pc_ie_slot7_link_speed
                                self.pcie_slot_8_link_speed = policy.vp_pc_ie_slot8_link_speed
                                self.pcie_slot_9_link_speed = policy.vp_pc_ie_slot9_link_speed
                                self.pcie_slot_10_link_speed = policy.vp_pc_ie_slot10_link_speed

                    if "biosVfPCISlotOptionROMEnable" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfPCISlotOptionROMEnable"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.slot_1_state = policy.vp_slot1_state
                                self.slot_2_state = policy.vp_slot2_state
                                self.slot_3_state = policy.vp_slot3_state
                                self.slot_4_state = policy.vp_slot4_state
                                self.slot_5_state = policy.vp_slot5_state
                                self.slot_6_state = policy.vp_slot6_state
                                self.slot_7_state = policy.vp_slot7_state
                                self.slot_8_state = policy.vp_slot8_state
                                self.slot_9_state = policy.vp_slot9_state
                                self.slot_10_state = policy.vp_slot10_state
                                self.pcie_slot_hba_optionrom = policy.vp_pc_ie_slot_hba_option_rom
                                self.pcie_slot_n1_optionrom = policy.vp_pc_ie_slot_n1_option_rom
                                self.pcie_slot_n2_optionrom = policy.vp_pc_ie_slot_n2_option_rom
                                self.pcie_slot_sas_optionrom = policy.vp_pc_ie_slot_sas_option_rom
                                self.pcie_slot_mlom_optionrom = policy.vp_pc_ie_slot_mlom_option_rom

                    if "biosVfPCILOMPortsConfiguration" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfPCILOMPortsConfiguration"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.pcie_10g_lom_2_link = policy.vp_pc_ie10_glo_m2_link

                    if "biosVfPCIROMCLP" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfPCIROMCLP"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.pciromclp = policy.vp_pciromclp

                    if "biosVfSIOC1OptionROM" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfSIOC1OptionROM"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.sioc1_optionrom = policy.vp_sio_c1_option_rom

                    if "biosVfSIOC2OptionROM" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfSIOC2OptionROM"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.sioc2_optionrom = policy.vp_sio_c2_option_rom

                    if "biosVfSBMezz1OptionROM" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfSBMezz1OptionROM"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.sbmezz1_optionrom = policy.vp_sb_mezz1_option_rom

                    if "biosVfIOESlot1OptionROM" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfIOESlot1OptionROM"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.ioeslot1_optionrom = policy.vp_ioe_slot1_option_rom

                    if "biosVfIOEMezz1OptionROM" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfIOEMezz1OptionROM"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.ioemezz1_optionrom = policy.vp_ioe_mezz1_option_rom

                    if "biosVfIOESlot2OptionROM" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfIOESlot2OptionROM"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.ioeslot2_optionrom = policy.vp_ioe_slot2_option_rom

                    if "biosVfIOENVMe1OptionROM" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfIOENVMe1OptionROM"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.ioenvme1_optionrom = policy.vp_ioenv_me1_option_rom

                    if "biosVfIOENVMe2OptionROM" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfIOENVMe2OptionROM"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.ioenvme2_optionrom = policy.vp_ioenv_me2_option_rom

                    if "biosVfSBNVMe1OptionROM" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfSBNVMe1OptionROM"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.sbnvme1_optionrom = policy.vp_sbnv_me1_option_rom

                    # Trusted Platform
                    if "biosVfTrustedPlatformModule" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfTrustedPlatformModule"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.trusted_platform_module = policy.vp_trusted_platform_module_support

                    if "biosVfIntelTrustedExecutionTechnology" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfIntelTrustedExecutionTechnology"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.trusted_execution_technology = policy.vp_intel_trusted_execution_technology_support

                    # Graphics Configuration
                    if "biosVfIntegratedGraphics" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfIntegratedGraphics"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.integrated_graphics_control = policy.vp_integrated_graphics

                    if "biosVfIntegratedGraphicsApertureSize" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfIntegratedGraphicsApertureSize"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.integrated_graphics_aperture_size = policy.vp_integrated_graphics_aperture_size

                    if "biosVfOnboardGraphics" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfOnboardGraphics"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.onboard_graphics = policy.vp_onboard_graphics

                    if "biosVfBootOptionRetry" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfBootOptionRetry"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.boot_option_retry = policy.vp_boot_option_retry

                    if "biosVfIntelEntrySASRAIDModule" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfIntelEntrySASRAIDModule"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.sas_raid = policy.vp_sasraid
                                self.sas_raid_module = policy.vp_sasraid_module

                    if "biosVfOnboardStorage" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfOnboardStorage"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.onboard_scu_storage_support = policy.vp_onboard_scu_storage_support

                    # Server Management
                    if "biosVfAssertNMIOnSERR" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfAssertNMIOnSERR"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.assert_nmi_on_serr = policy.vp_assert_nmi_on_serr

                    if "biosVfAssertNMIOnPERR" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfAssertNMIOnPERR"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.assert_nmi_on_perr = policy.vp_assert_nmi_on_perr

                    if "biosVfOSBootWatchdogTimer" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfOSBootWatchdogTimer"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.os_boot_watchdog_timer = policy.vp_os_boot_watchdog_timer

                    if "biosVfOSBootWatchdogTimerPolicy" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfOSBootWatchdogTimerPolicy"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.os_boot_watchdog_timer_policy = policy.vp_os_boot_watchdog_timer_policy

                    if "biosVfOSBootWatchdogTimerTimeout" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfOSBootWatchdogTimerTimeout"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.os_boot_watchdog_timer_timeout = policy.vp_os_boot_watchdog_timer_timeout

                    if "biosVfFRB2Timer" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfFRB2Timer"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.frb_2_timer = policy.vp_fr_b2_timer

                    if "biosVfConsoleRedirection" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfConsoleRedirection"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.console_redirection = policy.vp_console_redirection
                                self.flow_control = policy.vp_flow_control
                                self.baud_rate = policy.vp_baud_rate
                                # Transform "115200" to "115.2k": change the old naming to the new naming of the values
                                if str.isdigit(self.baud_rate):
                                    self.baud_rate = self.baud_rate[:-3] + "." + self.baud_rate[-3] + "k"
                                self.terminal_type = policy.vp_terminal_type
                                self.legacy_os_redirection = policy.vp_legacy_os_redirection
                                self.putty_keypad = policy.vp_putty_key_pad

                    if "biosVfOutOfBandManagement" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfOutOfBandManagement"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.out_of_band_management = policy.vp_com_spcr_enable

                    if "biosVfRedirectionAfterBIOSPOST" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["biosVfRedirectionAfterBIOSPOST"]:
                            if self._parent._dn + "/bios-prof-" + self.name + "/" in policy.dn:
                                self.redirection_after_bios_post = policy.vp_redirection_after_post

                    # We transform all 'platform-recommended' values to "platform-default" because
                    # 'platform-recommended' does not exist in the GUI
                    for attr in self.__dict__.keys():
                        if not attr.startswith("_") and getattr(self, attr) is not None:
                            setting_value = str(getattr(self, attr))
                            if setting_value in ['platform-recommended']:
                                setting_value = "platform-default"
                            setattr(self, attr, setting_value)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

        self.clean_object()

    def push_object(self, commit=True):

        bios_table = self.get_bios_table()
        if not bios_table:
            self.logger(level="error", message="BIOS Table not imported.")

        if self._device.version.__ge__(self._BIOS_TOKENS_MIN_REQUIRED_VERSION):
            self._bios_token_method = True

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
        if self._bios_token_method and bios_table:
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
                    except (UcsException, ConnectionRefusedError, urllib.error.URLError) as err:
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
                        else:
                            self.logger(level="error", message="BIOS Value " + setting_value +
                                                               " for BIOS parameter " + option + " not expected")
                            continue

                mo_bios_token_settings = BiosTokenSettings(
                    parent_mo_or_dn=mo_bios_v_profile.dn + "/tokn-featr-" + bios_table[option]["feature_group"] +
                                    "/tokn-param-" + bios_table[option]["target_name"], settings_mo_rn=setting_value,
                    is_assigned="yes")
                self._handle.add_mo(mo=mo_bios_token_settings, modify_present=True)

        # Using the legacy method
        else:
            for attr in self.__dict__.keys():
                if not attr.startswith("_") and attr not in ["name"]:
                    setting_value = getattr(self, attr)
                    if setting_value in ['platform-default', "Platform Default"]:
                        setting_value = "platform-default"
                    elif setting_value in ["Enable", "enabled", "enable"]:
                        setting_value = "enabled"
                    elif setting_value in ["Disable", "disabled", "disable"]:
                        setting_value = "disabled"
                    elif setting_value:
                        setting_value = setting_value.lower()
                    setattr(self, attr, setting_value)
            try:
                # Main
                mo_bios_v_profile = BiosVProfile(parent_mo_or_dn=parent_mo, name=self.name,
                                                 reboot_on_update=self.reboot_on_bios_settings_change, descr=self.descr)

                BiosVfQuietBoot(parent_mo_or_dn=mo_bios_v_profile, vp_quiet_boot=self.quiet_boot)
                BiosVfPOSTErrorPause(parent_mo_or_dn=mo_bios_v_profile, vp_post_error_pause=self.post_error_pause)
                BiosVfResumeOnACPowerLoss(parent_mo_or_dn=mo_bios_v_profile,
                                          vp_resume_on_ac_power_loss=self.resume_on_ac_power_loss)
                BiosVfFrontPanelLockout(parent_mo_or_dn=mo_bios_v_profile,
                                        vp_front_panel_lockout=self.front_panel_lockout)
                BiosVfConsistentDeviceNameControl(parent_mo_or_dn=mo_bios_v_profile,
                                                  vp_cdn_control=self.cdn_control)

                # Processor
                BiosVfIntelTurboBoostTech(parent_mo_or_dn=mo_bios_v_profile,
                                          vp_intel_turbo_boost_tech=self.intel_turbo_boost_tech)
                BiosVfEnhancedIntelSpeedStepTech(parent_mo_or_dn=mo_bios_v_profile,
                                                 vp_enhanced_intel_speed_step_tech=self.enhanced_intel_speedstep_tech)
                BiosVfIntelHyperThreadingTech(parent_mo_or_dn=mo_bios_v_profile,
                                              vp_intel_hyper_threading_tech=self.intel_hyperthreading_tech)
                if self.core_multi_processing in ["1", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "2",
                                                  "20", "21", "22", "23", "24", "3", "4", "5", "6", "7", "8", "9",
                                                  "all", "platform-default", "platform-recommended"]:
                    BiosVfCoreMultiProcessing(parent_mo_or_dn=mo_bios_v_profile,
                                              vp_core_multi_processing=self.core_multi_processing)
                else:
                    self.logger(level="warning",
                                message="The value of core_multi_processing: " + str(self.core_multi_processing) +
                                        " in the BIOS Policy " + str(self.name) +
                                        " is not supported by this version of UCS Manager. " +
                                        "Thus, no configuration has been pushed for this BIOS parameter")

                BiosVfExecuteDisableBit(parent_mo_or_dn=mo_bios_v_profile,
                                        vp_execute_disable_bit=self.execute_disable_bit)
                BiosVfIntelVirtualizationTechnology(
                    parent_mo_or_dn=mo_bios_v_profile,
                    vp_intel_virtualization_technology=self.intel_virtualization_technology)

                BiosVfProcessorPrefetchConfig(parent_mo_or_dn=mo_bios_v_profile,
                                              vp_dcuip_prefetcher=self.dcu_ip_prefetcher,
                                              vp_hardware_prefetcher=self.hardware_prefetcher,
                                              vp_adjacent_cache_line_prefetcher=self.adjacent_cache_line_prefetcher,
                                              vp_dcu_streamer_prefetch=self.dcu_streamer_prefetch)
                BiosVfDirectCacheAccess(parent_mo_or_dn=mo_bios_v_profile,
                                        vp_direct_cache_access=self.direct_cache_access)
                BiosVfProcessorCState(parent_mo_or_dn=mo_bios_v_profile, vp_processor_c_state=self.processor_c_state)
                BiosVfProcessorC1E(parent_mo_or_dn=mo_bios_v_profile, vp_processor_c1_e=self.processor_c1e)
                BiosVfProcessorC3Report(parent_mo_or_dn=mo_bios_v_profile,
                                        vp_processor_c3_report=self.processor_c3_report)
                BiosVfProcessorC6Report(parent_mo_or_dn=mo_bios_v_profile,
                                        vp_processor_c6_report=self.processor_c6_report)
                BiosVfProcessorC7Report(parent_mo_or_dn=mo_bios_v_profile,
                                        vp_processor_c7_report=self.processor_c7_report)
                BiosVfProcessorCMCI(parent_mo_or_dn=mo_bios_v_profile, vp_processor_cmci=self.processor_cmci)
                BiosVfCPUPerformance(parent_mo_or_dn=mo_bios_v_profile, vp_cpu_performance=self.cpu_performance)
                BiosVfMaxVariableMTRRSetting(parent_mo_or_dn=mo_bios_v_profile,
                                             vp_processor_mtrr=self.max_variable_mtrr_setting)

                if self.local_x2_apic in ["auto", "platform-default", "platform-recommended", "x2apic", "xapic"]:
                    BiosVfLocalX2Apic(parent_mo_or_dn=mo_bios_v_profile, vp_local_x2_apic=self.local_x2_apic)
                else:
                    self.logger(level="warning",
                                message="The value of local_x2_apic: " + str(self.local_x2_apic) +
                                        " in the BIOS Policy " + str(self.name) +
                                        " is not supported by this version of UCS Manager. " +
                                        "Thus, no configuration has been pushed for this BIOS parameter")

                if self.energy_performance in ["balanced-energy", "balanced-performance", "energy-efficient",
                                               "performance", "platform-default", "platform-recommended"]:
                    BiosVfProcessorEnergyConfiguration(parent_mo_or_dn=mo_bios_v_profile,
                                                       vp_energy_performance=self.energy_performance,
                                                       vp_power_technology=self.power_technology)
                else:
                    BiosVfProcessorEnergyConfiguration(parent_mo_or_dn=mo_bios_v_profile,
                                                       vp_power_technology=self.power_technology)
                    self.logger(level="warning",
                                message="The value of energy_performance: " + str(self.energy_performance) +
                                        " in the BIOS Policy " + str(self.name) +
                                        " is not supported by this version of UCS Manager. " +
                                        "Thus, no configuration has been pushed for this BIOS parameter")

                BiosVfFrequencyFloorOverride(parent_mo_or_dn=mo_bios_v_profile,
                                             vp_frequency_floor_override=self.frequency_floor_override)
                BiosVfPSTATECoordination(parent_mo_or_dn=mo_bios_v_profile,
                                         vp_pstate_coordination=self.p_state_coordination)
                BiosVfDRAMClockThrottling(parent_mo_or_dn=mo_bios_v_profile,
                                          vp_dram_clock_throttling=self.dram_clock_throttling)

                BiosVfInterleaveConfiguration(parent_mo_or_dn=mo_bios_v_profile,
                                              vp_rank_interleaving=self.rank_interleaving,
                                              vp_channel_interleaving=self.channel_interleaving,
                                              vp_memory_interleaving=self.memory_interleaving)

                BiosVfScrubPolicies(parent_mo_or_dn=mo_bios_v_profile, vp_patrol_scrub=self.patrol_scrub,
                                    vp_demand_scrub=self.demand_scrub)

                BiosVfAltitude(parent_mo_or_dn=mo_bios_v_profile, vp_altitude=self.altitude)

                if self.package_c_state_limit in ["auto", "c0", "c1", "c2", "c3", "c6", "c7", "c7s", "no-limit",
                                                  "platform-default", "platform-recommended"]:
                    BiosVfPackageCStateLimit(parent_mo_or_dn=mo_bios_v_profile,
                                             vp_package_c_state_limit=self.package_c_state_limit)
                else:
                    self.logger(level="warning",
                                message="The value of package_c_state_limit: " + str(self.package_c_state_limit) +
                                        " in the BIOS Policy " + str(self.name) +
                                        " is not supported by this version of UCS Manager. " +
                                        "Thus, no configuration has been pushed for this BIOS parameter")

                if self.cpu_hardware_power_management in ["disabled", "hwpm-native-mode", "hwpm-oob-mode",
                                                          "platform-default", "platform-recommended"]:
                    BiosVfCPUHardwarePowerManagement(
                        parent_mo_or_dn=mo_bios_v_profile,
                        vp_cpu_hardware_power_management=self.cpu_hardware_power_management)
                else:
                    self.logger(level="warning",
                                message="The value of cpu_hardware_power_management: " +
                                        str(self.cpu_hardware_power_management) + " in the BIOS Policy "
                                        + str(self.name) + " is not supported by this version of UCS Manager. " +
                                        "Thus, no configuration has been pushed for this BIOS parameter")

                BiosVfEnergyPerformanceTuning(parent_mo_or_dn=mo_bios_v_profile,
                                              vp_pwr_perf_tuning=self.energy_performance_tuning)
                BiosVfWorkloadConfiguration(parent_mo_or_dn=mo_bios_v_profile,
                                            vp_workload_configuration=self.workload_configuration)

                # Intel Directed IO
                BiosVfIntelVTForDirectedIO(
                    parent_mo_or_dn=mo_bios_v_profile, vp_intel_vt_for_directed_io=self.intel_vt_for_directed_io,
                    vp_intel_vtd_interrupt_remapping=self.intel_vtd_interrupt_remapping,
                    vp_intel_vtd_coherency_support=self.intel_vtd_coherency_support,
                    vp_intel_vtdats_support=self.intel_vtd_ats_support,
                    vp_intel_vtd_pass_through_dma_support=self.intel_vtd_pass_through_dma_support)

                # RAS Memory
                if self.memory_ras_configuration in ["lockstep", "maximum-performance", "mirroring", "platform-default",
                                                     "platform-recommended", "sparing"]:
                    BiosVfSelectMemoryRASConfiguration(parent_mo_or_dn=mo_bios_v_profile,
                                                       vp_select_memory_ras_configuration=self.memory_ras_configuration)
                else:
                    self.logger(level="warning",
                                message="The value of memory_ras_configuration: " + str(self.memory_ras_configuration) +
                                        " in the BIOS Policy " + str(self.name) +
                                        " is not supported by this version of UCS Manager. " +
                                        "Thus, no configuration has been pushed for this BIOS parameter")

                BiosVfNUMAOptimized(parent_mo_or_dn=mo_bios_v_profile, vp_numa_optimized=self.numa_optimized)
                BiosVfMirroringMode(parent_mo_or_dn=mo_bios_v_profile, vp_mirroring_mode=self.mirroring_mode)
                BiosVfLvDIMMSupport(parent_mo_or_dn=mo_bios_v_profile, vp_lv_ddr_mode=self.lv_ddr_mode)
                BiosVfDramRefreshRate(parent_mo_or_dn=mo_bios_v_profile, vp_dram_refresh_rate=self.dram_refresh_rate)
                BiosVfDDR3VoltageSelection(parent_mo_or_dn=mo_bios_v_profile,
                                           vp_dd_r3_voltage_selection=self.ddr3_voltage_selection)
                # Serial Port
                BiosVfSerialPortAEnable(parent_mo_or_dn=mo_bios_v_profile,
                                        vp_serial_port_a_enable=self.serial_port_a_enable)

                # USB
                BiosVfUSBBootConfig(parent_mo_or_dn=mo_bios_v_profile,
                                    vp_make_device_non_bootable=self.make_device_non_bootable,
                                    vp_legacy_usb_support=self.legacy_usb_support)
                BiosVfUSBSystemIdlePowerOptimizingSetting(parent_mo_or_dn=mo_bios_v_profile,
                                                          vp_usb_idle_power_optimizing=self.usb_idle_power_optimizing)
                BiosVfUSBFrontPanelAccessLock(parent_mo_or_dn=mo_bios_v_profile,
                                              vp_usb_front_panel_lock=self.usb_front_panel_access_lock)

                BiosVfUSBPortConfiguration(parent_mo_or_dn=mo_bios_v_profile,
                                           vp_port6064_emulation=self.port_60_64_emulation,
                                           vp_usb_port_internal=self.usb_port_internal,
                                           vp_usb_port_v_media=self.usb_port_vmedia,
                                           vp_usb_port_kvm=self.usb_port_kvm, vp_usb_port_front=self.usb_port_front,
                                           vp_usb_port_sd_card=self.usb_port_sd_card,
                                           vp_usb_port_rear=self.usb_port_rear)
                BiosVfAllUSBDevices(parent_mo_or_dn=mo_bios_v_profile, vp_all_usb_devices=self.all_usb_devices)
                BiosVfUSBConfiguration(parent_mo_or_dn=mo_bios_v_profile, vp_xhci_mode=self.xhci_mode)

                # PCI
                BiosVfMaximumMemoryBelow4GB(parent_mo_or_dn=mo_bios_v_profile,
                                            vp_maximum_memory_below4_gb=self.maximum_memory_below_4gb)
                BiosVfMemoryMappedIOAbove4GB(parent_mo_or_dn=mo_bios_v_profile,
                                             vp_memory_mapped_io_above4_gb=self.memory_mapped_io_above_4gb)
                BiosVfVGAPriority(parent_mo_or_dn=mo_bios_v_profile, vp_vga_priority=self.vga_priority)
                BiosVfASPMSupport(parent_mo_or_dn=mo_bios_v_profile, vp_aspm_support=self.aspm_support)

                # QPI
                if self.qpi_link_frequency_select:
                    # Transform "8.0-GT-s" to "8000" : transform the new naming of the values to the old naming
                    link_frequency_value = self.qpi_link_frequency_select
                    if link_frequency_value.lower().endswith("-gt-s"):
                        link_frequency_value = link_frequency_value.lower().replace(".", "").replace("-gt-s", "00")
                    BiosVfQPILinkFrequencySelect(parent_mo_or_dn=mo_bios_v_profile,
                                                 vp_qpi_link_frequency_select=link_frequency_value)
                BiosVfQPISnoopMode(parent_mo_or_dn=mo_bios_v_profile, vp_qpi_snoop_mode=self.qpi_snoop_mode)

                # LOM and PCIe Slots
                BiosVfPCISlotLinkSpeed(parent_mo_or_dn=mo_bios_v_profile,
                                       vp_pc_ie_slot8_link_speed=self.pcie_slot_8_link_speed,
                                       vp_pc_ie_slot1_link_speed=self.pcie_slot_1_link_speed,
                                       vp_pc_ie_slot4_link_speed=self.pcie_slot_4_link_speed,
                                       vp_pc_ie_slot7_link_speed=self.pcie_slot_7_link_speed,
                                       vp_pc_ie_slot6_link_speed=self.pcie_slot_6_link_speed,
                                       vp_pc_ie_slot3_link_speed=self.pcie_slot_3_link_speed,
                                       vp_pc_ie_slot2_link_speed=self.pcie_slot_2_link_speed,
                                       vp_pc_ie_slot10_link_speed=self.pcie_slot_10_link_speed,
                                       vp_pc_ie_slot9_link_speed=self.pcie_slot_9_link_speed,
                                       vp_pc_ie_slot5_link_speed=self.pcie_slot_5_link_speed)

                BiosVfPCISlotOptionROMEnable(parent_mo_or_dn=mo_bios_v_profile,
                                             vp_pc_ie_slot_hba_option_rom=self.pcie_slot_hba_optionrom,
                                             vp_pc_ie_slot_n2_option_rom=self.pcie_slot_n2_optionrom,
                                             vp_pc_ie_slot_sas_option_rom=self.pcie_slot_sas_optionrom,
                                             vp_pc_ie_slot_mlom_option_rom=self.pcie_slot_mlom_optionrom,
                                             vp_pc_ie_slot_n1_option_rom=self.pcie_slot_n1_optionrom,
                                             vp_slot1_state=self.slot_1_state,
                                             vp_slot8_state=self.slot_8_state,
                                             vp_slot4_state=self.slot_4_state,
                                             vp_slot7_state=self.slot_7_state,
                                             vp_slot9_state=self.slot_9_state,
                                             vp_slot2_state=self.slot_2_state,
                                             vp_slot6_state=self.slot_6_state,
                                             vp_slot3_state=self.slot_3_state,
                                             vp_slot10_state=self.slot_10_state,
                                             vp_slot5_state=self.slot_5_state)

                BiosVfPCILOMPortsConfiguration(parent_mo_or_dn=mo_bios_v_profile,
                                               vp_pc_ie10_glo_m2_link=self.pcie_10g_lom_2_link)
                BiosVfPCIROMCLP(parent_mo_or_dn=mo_bios_v_profile, vp_pciromclp=self.pciromclp)
                BiosVfSIOC1OptionROM(parent_mo_or_dn=mo_bios_v_profile, vp_sio_c1_option_rom=self.sioc1_optionrom)
                BiosVfSIOC2OptionROM(parent_mo_or_dn=mo_bios_v_profile, vp_sio_c2_option_rom=self.sioc2_optionrom)
                BiosVfSBMezz1OptionROM(parent_mo_or_dn=mo_bios_v_profile,
                                       vp_sb_mezz1_option_rom=self.sbmezz1_optionrom)
                BiosVfIOESlot1OptionROM(parent_mo_or_dn=mo_bios_v_profile,
                                        vp_ioe_slot1_option_rom=self.ioeslot1_optionrom)
                BiosVfIOEMezz1OptionROM(parent_mo_or_dn=mo_bios_v_profile,
                                        vp_ioe_mezz1_option_rom=self.ioemezz1_optionrom)
                BiosVfIOESlot2OptionROM(parent_mo_or_dn=mo_bios_v_profile,
                                        vp_ioe_slot2_option_rom=self.ioeslot2_optionrom)
                BiosVfIOENVMe1OptionROM(parent_mo_or_dn=mo_bios_v_profile,
                                        vp_ioenv_me1_option_rom=self.ioenvme1_optionrom)
                BiosVfIOENVMe2OptionROM(parent_mo_or_dn=mo_bios_v_profile,
                                        vp_ioenv_me2_option_rom=self.ioenvme2_optionrom)
                BiosVfSBNVMe1OptionROM(parent_mo_or_dn=mo_bios_v_profile,
                                       vp_sbnv_me1_option_rom=self.sbnvme1_optionrom)

                # Trusted Platform
                BiosVfTrustedPlatformModule(parent_mo_or_dn=mo_bios_v_profile,
                                            vp_trusted_platform_module_support=self.trusted_platform_module)
                BiosVfIntelTrustedExecutionTechnology(
                    parent_mo_or_dn=mo_bios_v_profile,
                    vp_intel_trusted_execution_technology_support=self.trusted_execution_technology)

                # Graphics Configuration
                BiosVfIntegratedGraphics(parent_mo_or_dn=mo_bios_v_profile,
                                         vp_integrated_graphics=self.integrated_graphics_control)
                BiosVfIntegratedGraphicsApertureSize(
                    parent_mo_or_dn=mo_bios_v_profile,
                    vp_integrated_graphics_aperture_size=self.integrated_graphics_aperture_size)
                BiosVfOnboardGraphics(parent_mo_or_dn=mo_bios_v_profile, vp_onboard_graphics=self.onboard_graphics)

                # Boot options
                BiosVfBootOptionRetry(parent_mo_or_dn=mo_bios_v_profile, vp_boot_option_retry=self.boot_option_retry)
                sas_raid = self.sas_raid
                sas_raid_module = self.sas_raid_module
                BiosVfIntelEntrySASRAIDModule(parent_mo_or_dn=mo_bios_v_profile, vp_sasraid_module=sas_raid_module,
                                              vp_sasraid=sas_raid)
                BiosVfOnboardStorage(parent_mo_or_dn=mo_bios_v_profile,
                                     vp_onboard_scu_storage_support=self.onboard_scu_storage_support)

                # Server Management
                BiosVfAssertNMIOnSERR(parent_mo_or_dn=mo_bios_v_profile, vp_assert_nmi_on_serr=self.assert_nmi_on_serr)
                BiosVfAssertNMIOnPERR(parent_mo_or_dn=mo_bios_v_profile, vp_assert_nmi_on_perr=self.assert_nmi_on_perr)
                BiosVfOSBootWatchdogTimer(parent_mo_or_dn=mo_bios_v_profile,
                                          vp_os_boot_watchdog_timer=self.os_boot_watchdog_timer)
                BiosVfOSBootWatchdogTimerPolicy(parent_mo_or_dn=mo_bios_v_profile,
                                                vp_os_boot_watchdog_timer_policy=self.os_boot_watchdog_timer_policy)
                BiosVfOSBootWatchdogTimerTimeout(parent_mo_or_dn=mo_bios_v_profile,
                                                 vp_os_boot_watchdog_timer_timeout=self.os_boot_watchdog_timer_timeout)
                BiosVfFRB2Timer(parent_mo_or_dn=mo_bios_v_profile, vp_fr_b2_timer=self.frb_2_timer)

                baud_rate_value = self.baud_rate
                if baud_rate_value:
                    # Transform "115.2k" to "115200" : transform the new naming of the values to the old naming
                    if baud_rate_value.lower().endswith("k"):
                        baud_rate_value = baud_rate_value.replace("k", "00").replace(".", "")

                BiosVfConsoleRedirection(parent_mo_or_dn=mo_bios_v_profile, vp_baud_rate=baud_rate_value,
                                         vp_flow_control=self.flow_control,
                                         vp_putty_key_pad=self.putty_keypad,
                                         vp_console_redirection=self.console_redirection,
                                         vp_terminal_type=self.terminal_type,
                                         vp_legacy_os_redirection=self.legacy_os_redirection)
                BiosVfOutOfBandManagement(parent_mo_or_dn=mo_bios_v_profile,
                                          vp_com_spcr_enable=self.out_of_band_management)
                BiosVfRedirectionAfterBIOSPOST(parent_mo_or_dn=mo_bios_v_profile,
                                               vp_redirection_after_post=self.redirection_after_bios_post)
                self._handle.add_mo(mo=mo_bios_v_profile, modify_present=True)

            except Exception as e:
                self.logger(level="error",
                            message="BIOS Policy " + str(self.name) +
                                    " could not be committed. Please fix the issue and try again: " + str(e))
                return False

        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True

    @staticmethod
    def get_bios_table():
        filename = "./config/ucs/bios_table.json"
        if os.path.isfile(filename):
            json_file = open(filename)
            bios_table = json.loads(json_file.read())
            json_file.close()
            return bios_table
        return None


class UcsSystemIscsiAuthenticationProfile(UcsSystemConfigObject):
    _CONFIG_NAME = "iSCSI Authentication Profile"
    _UCS_SDK_OBJECT_NAME = "iscsiAuthProfile"

    def __init__(self, parent=None, json_content=None, iscsi_auth_profile=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
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
                            message="Fetch of password is not possible for user " + self.user_id + " of " +
                                    self._CONFIG_NAME + " " + str(self.name))

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


class UcsSystemVmediaPolicy(UcsSystemConfigObject):
    _CONFIG_NAME = "vMedia Policy"
    _UCS_SDK_OBJECT_NAME = "cimcvmediaMountConfigPolicy"

    def __init__(self, parent=None, json_content=None, cimcvmedia_mount_config_policy=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
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
                            if self._parent._dn + "/mnt-cfg-policy-" + self.name + "/" in cimcvmedia.dn:
                                user = {}
                                user.update({"device_type": cimcvmedia.device_type})
                                user.update({"protocol": cimcvmedia.mount_protocol})
                                user.update({"name": cimcvmedia.mapping_name})
                                user.update({"descr": cimcvmedia.description})
                                user.update({"username": cimcvmedia.user_id})
                                user.update({"password": cimcvmedia.password})
                                user.update({"image_name_variable": cimcvmedia.image_name_variable})
                                user.update({"remote_file": cimcvmedia.image_file_name})
                                user.update({"remote_path": cimcvmedia.image_path})
                                user.update({"hostname": cimcvmedia.remote_ip_address})
                                user.update({"authentication_protocol": cimcvmedia.auth_option})
                                user.update({"remap_on_eject": cimcvmedia.remap_on_eject})
                                self.vmedia_mounts.append(user)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

                # We need to set all values that are not present in the config file to None
                for element in self.vmedia_mounts:
                    for value in ["device_type", "password", "username", "descr", "protocol", "name", "remote_file",
                                  "remote_path", "hostname", "image_name_variable", "authentication_protocol",
                                  "remap_on_eject"]:
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

        mo_cimcvmedia_mount_config_policy = CimcvmediaMountConfigPolicy(parent_mo_or_dn=parent_mo, name=self.name,
                                                                        retry_on_mount_fail=self.retry_on_mount_fail,
                                                                        descr=self.descr)

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

            remap_on_eject = None
            if "remap_on_eject" in media:
                remap_on_eject = media['remap_on_eject']
            authentication_protocol = None
            if "authentication_protocol" in media:
                authentication_protocol = media['authentication_protocol']

            CimcvmediaConfigMountEntry(parent_mo_or_dn=mo_cimcvmedia_mount_config_policy, mapping_name=media_name,
                                       device_type=device_type, image_file_name=file_name, image_name_variable=inv,
                                       image_path=file_path, mount_protocol=protocol, user_id=username, password=pwd,
                                       remote_ip_address=hostname, description=descr, remap_on_eject=remap_on_eject,
                                       auth_option=authentication_protocol)

        self._handle.add_mo(mo=mo_cimcvmedia_mount_config_policy, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True


class UcsSystemEthernetAdapterPolicy(UcsSystemConfigObject):
    _CONFIG_NAME = "Ethernet Adapter Policy"
    _UCS_SDK_OBJECT_NAME = "adaptorHostEthIfProfile"

    def __init__(self, parent=None, json_content=None, adaptor_host_eth_if_profile=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
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

                if "adaptorEthRecvQueueProfile" in self._parent._config.sdk_objects:
                    for adapt in self._config.sdk_objects["adaptorEthRecvQueueProfile"]:
                        if self._parent._dn:
                            if self._parent._dn + "/eth-profile-" + self.name + "/" in adapt.dn:
                                self.receive_queues_ring_size = adapt.ring_size
                                self.receive_queues = adapt.count

                if "adaptorEthCompQueueProfile" in self._parent._config.sdk_objects:
                    for adapt in self._config.sdk_objects["adaptorEthCompQueueProfile"]:
                        if self._parent._dn:
                            if self._parent._dn + "/eth-profile-" + self.name + "/" in adapt.dn:
                                self.completion_queues = adapt.count

                if "adaptorEthOffloadProfile" in self._parent._config.sdk_objects:
                    for adapt in self._config.sdk_objects["adaptorEthOffloadProfile"]:
                        if self._parent._dn:
                            if self._parent._dn + "/eth-profile-" + self.name + "/" in adapt.dn:
                                self.transmit_checksum_offload = adapt.tcp_tx_checksum
                                self.receive_checksum_offload = adapt.tcp_rx_checksum
                                self.tcp_segmentation_offload = adapt.tcp_segment
                                self.tcp_large_receive_offload = adapt.large_receive
                
                if "adaptorRssProfile" in self._parent._config.sdk_objects:
                    for adapt in self._config.sdk_objects["adaptorRssProfile"]:
                        if self._parent._dn:
                            if self._parent._dn + "/eth-profile-" + self.name + "/" in adapt.dn:
                                self.receive_side_scaling = adapt.receive_side_scaling
                
                if "adaptorEthArfsProfile" in self._parent._config.sdk_objects:
                    for adapt in self._config.sdk_objects["adaptorEthArfsProfile"]:
                        if self._parent._dn:
                            if self._parent._dn + "/eth-profile-" + self.name + "/" in adapt.dn:
                                self.accelerated_receive_flow_steering = adapt.accelarated_rfs
                
                if "adaptorEthNVGREProfile" in self._parent._config.sdk_objects:
                    for adapt in self._config.sdk_objects["adaptorEthNVGREProfile"]:
                        if self._parent._dn:
                            if self._parent._dn + "/eth-profile-" + self.name + "/" in adapt.dn:
                                self.nvgre_offload = adapt.admin_state
                
                if "adaptorEthVxLANProfile" in self._parent._config.sdk_objects:
                    for adapt in self._config.sdk_objects["adaptorEthVxLANProfile"]:
                        if self._parent._dn:
                            if self._parent._dn + "/eth-profile-" + self.name + "/" in adapt.dn:
                                self.vxlan_offload = adapt.admin_state
                
                if "adaptorEthFailoverProfile" in self._parent._config.sdk_objects:
                    for adapt in self._config.sdk_objects["adaptorEthFailoverProfile"]:
                        if self._parent._dn:
                            if self._parent._dn + "/eth-profile-" + self.name + "/" in adapt.dn:
                                self.failback_timeout = adapt.timeout
                
                if "adaptorEthInterruptProfile" in self._parent._config.sdk_objects:
                    for adapt in self._config.sdk_objects["adaptorEthInterruptProfile"]:
                        if self._parent._dn:
                            if self._parent._dn + "/eth-profile-" + self.name + "/" in adapt.dn:
                                self.interrupt_coalescing_type = adapt.coalescing_type
                                self.interrupt_mode = adapt.mode
                                self.interrupt_timer = adapt.coalescing_time
                                self.interrupts = adapt.count
                
                if "adaptorEthRoCEProfile" in self._parent._config.sdk_objects:
                    for adapt in self._config.sdk_objects["adaptorEthRoCEProfile"]:
                        if self._parent._dn:
                            if self._parent._dn + "/eth-profile-" + self.name + "/" in adapt.dn:
                                self.roce = adapt.admin_state
                                roce_properties = {}
                                roce_properties.update({"version_1": adapt.v1})
                                roce_properties.update({"version_2": adapt.v2})
                                roce_properties.update({"queue_pairs": adapt.queue_pairs})
                                roce_properties.update({"memory_regions": adapt.memory_regions})
                                roce_properties.update({"resource_groups": adapt.resource_groups})
                                roce_properties.update({"priority": adapt.prio})
                                self.roce_properties.append(roce_properties)
                
                if "adaptorEthAdvFilterProfile" in self._parent._config.sdk_objects:
                    for adapt in self._config.sdk_objects["adaptorEthAdvFilterProfile"]:
                        if self._parent._dn:
                            if self._parent._dn + "/eth-profile-" + self.name + "/" in adapt.dn:
                                self.advance_filter = adapt.admin_state
                
                if "adaptorEthInterruptScalingProfile" in self._parent._config.sdk_objects:
                    for adapt in self._config.sdk_objects["adaptorEthInterruptScalingProfile"]:
                        if self._parent._dn:
                            if self._parent._dn + "/eth-profile-" + self.name + "/" in adapt.dn:
                                self.interrupt_scaling = adapt.admin_state

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


class UcsSystemFibreChannelAdapterPolicy(UcsSystemConfigObject):
    _CONFIG_NAME = "Fibre Channel Adapter Policy"
    _UCS_SDK_OBJECT_NAME = "adaptorHostFcIfProfile"

    def __init__(self, parent=None, json_content=None, adaptor_host_fc_if_profile=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
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

                if "adaptorFcRecvQueueProfile" in self._parent._config.sdk_objects:
                    for adapt in self._config.sdk_objects["adaptorFcRecvQueueProfile"]:
                        if self._parent._dn:
                            if self._parent._dn + "/fc-profile-" + self.name + "/" in adapt.dn:
                                self.receive_queues_ring_size = adapt.ring_size

                if "adaptorFcCdbWorkQueueProfile" in self._parent._config.sdk_objects:
                    for adapt in self._config.sdk_objects["adaptorFcCdbWorkQueueProfile"]:
                        if self._parent._dn:
                            if self._parent._dn + "/fc-profile-" + self.name + "/" in adapt.dn:
                                self.io_queues = adapt.count
                                self.io_queues_ring_size = adapt.ring_size

                if "adaptorFcPortFLogiProfile" in self._parent._config.sdk_objects:
                    for adapt in self._config.sdk_objects["adaptorFcPortFLogiProfile"]:
                        if self._parent._dn:
                            if self._parent._dn + "/fc-profile-" + self.name + "/" in adapt.dn:
                                self.flogi_retries = adapt.retries
                                self.flogi_timeout = adapt.timeout

                if "adaptorFcPortPLogiProfile" in self._parent._config.sdk_objects:
                    for adapt in self._config.sdk_objects["adaptorFcPortPLogiProfile"]:
                        if self._parent._dn:
                            if self._parent._dn + "/fc-profile-" + self.name + "/" in adapt.dn:
                                self.plogi_retries = adapt.retries
                                self.plogi_timeout = adapt.timeout

                if "adaptorFcErrorRecoveryProfile" in self._parent._config.sdk_objects:
                    for adapt in self._config.sdk_objects["adaptorFcErrorRecoveryProfile"]:
                        if self._parent._dn:
                            if self._parent._dn + "/fc-profile-" + self.name + "/" in adapt.dn:
                                self.fcp_error_recovery = adapt.fcp_error_recovery
                                self.port_down_timeout = adapt.port_down_timeout
                                self.port_down_io_retry = adapt.port_down_io_retry_count
                                self.link_down_timeout = adapt.link_down_timeout

                if "adaptorFcPortProfile" in self._parent._config.sdk_objects:
                    for adapt in self._config.sdk_objects["adaptorFcPortProfile"]:
                        if self._parent._dn:
                            if self._parent._dn + "/fc-profile-" + self.name + "/" in adapt.dn:
                                self.io_throttle_count = adapt.io_throttle_count
                                self.max_luns_per_target = adapt.luns_per_target

                if "adaptorFcFnicProfile" in self._parent._config.sdk_objects:
                    for adapt in self._config.sdk_objects["adaptorFcFnicProfile"]:
                        if self._parent._dn:
                            if self._parent._dn + "/fc-profile-" + self.name + "/" in adapt.dn:
                                self.io_retry_timeout = adapt.io_retry_timeout
                                self.lun_queue_depth = adapt.lun_queue_depth

                if "adaptorFcInterruptProfile" in self._parent._config.sdk_objects:
                    for adapt in self._config.sdk_objects["adaptorFcInterruptProfile"]:
                        if self._parent._dn:
                            if self._parent._dn + "/fc-profile-" + self.name + "/" in adapt.dn:
                                self.interrupt_mode = adapt.mode

                if "adaptorFcVhbaTypeProfile" in self._parent._config.sdk_objects:
                    for adapt in self._config.sdk_objects["adaptorFcVhbaTypeProfile"]:
                        if self._parent._dn:
                            if self._parent._dn + "/fc-profile-" + self.name + "/" in adapt.dn:
                                self.vhba_type = adapt.mode

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

        # Below is for handling an exception with UCS Central policy "global-default" using an invalid value of 16
        # for io_throttle_count
        io_throttle_count = self.io_throttle_count
        if self.name == "global-default":
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

        if self.vhba_type:
            AdaptorFcVhbaTypeProfile(parent_mo_or_dn=mo_adaptor_host_fc_if_profile, mode=self.vhba_type)

        self._handle.add_mo(mo=mo_adaptor_host_fc_if_profile, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True


class UcsSystemIscsiAdapterPolicy(UcsSystemConfigObject):
    _CONFIG_NAME = "iSCSI Adapter Policy"
    _UCS_SDK_OBJECT_NAME = "adaptorHostIscsiIfProfile"

    def __init__(self, parent=None, json_content=None, adaptor_host_iscsi_if_profile=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
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

        mo_adaptor_host_iscsi_if_profile = AdaptorHostIscsiIfProfile(parent_mo_or_dn=parent_mo, name=self.name)
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


class UcsSystemServiceProfile(UcsSystemConfigObject):
    _CONFIG_NAME = "Service Profile"
    _UCS_SDK_OBJECT_NAME = "lsServer"

    def __init__(self, parent=None, json_content=None, ls_server=None):
        UcsSystemConfigObject.__init__(self, parent=parent)

        self.service_profile_template = None
        self.suffix_start_number = None
        self.number_of_instances = None
        # Identify Service Profile
        self.descr = None
        self.name = None
        self.type = None
        self.user_label = None
        self.asset_tag = None
        self.uuid_pool = None
        self.uuid = None
        # Storage Provisioning
        self.storage_profile = None
        self.local_disk_configuration_policy = None
        # Networking
        self.dynamic_vnic_connection_policy = None
        self.lan_connectivity_policy = None
        self.vnics = []
        self.iscsi_vnics = []
        self.iscsi_initiator_name = None
        # SAN Connectivity
        self.san_connectivity_policy = None
        self.wwnn_pool = None
        self.wwnn = None
        self.vhbas = []
        # Zoning
        self.vhba_initiator_groups = []
        # vNIC/vHBA Placement
        self.placement_policy = None
        self.placement = []
        # vMedia Policy
        self.vmedia_policy = None
        # Server Boot Order
        self.boot_policy = None
        self.iscsi_boot_parameters = []
        # Maintenance Policy
        self.maintenance_policy = None
        # Server Assignment
        self.servers = []
        self.server_pool = None
        self.server_power_state = None
        self.server_pool_qualification = None
        self.restrict_migration = None
        self.host_firmware_package = None
        # Optional Policies
        self.bios_policy = None
        self.ipmi_access_profile = None
        self.serial_over_lan_policy = None
        self.outband_ipv4_pool = None
        self.inband_ipv6_pool = None
        self.inband_ipv4_pool = None
        self.threshold_policy = None
        self.power_control_policy = None
        self.scrub_policy = None
        self.kvm_management_policy = None
        self.graphics_card_policy = None
        self.power_sync_policy = None

        if self._config.load_from == "live":
            if ls_server is not None:
                self.name = ls_server.name
                self.descr = ls_server.descr
                self.type = ls_server.type
                self.user_label = ls_server.usr_lbl
                self.service_profile_template = ls_server.src_templ_name

                if "lsServerExtension" in self._parent._config.sdk_objects:
                    for ext in self._config.sdk_objects["lsServerExtension"]:
                        if self._parent._dn:
                            if self._parent._dn + "/ls-" + self.name + "/" in ext.dn:
                                self.asset_tag = ext.asset_tag

                parent_template_type = None
                if self.service_profile_template:
                    # We first try to get the SP Template object by using the operSrcTemplName attribute value
                    if ls_server.oper_src_templ_name:
                        mo_template_ls = self._device.query(mode="dn", target=ls_server.oper_src_templ_name)
                        if mo_template_ls:
                            parent_template_type = mo_template_ls.type
                    else:
                        # If the operSrcTemplName attribute is not set (e.g. with UCS Central), we try to find the SP
                        # Template using a query for its name. In case it is the only object with this name, we use it
                        filter_str = '(name, "' + self.service_profile_template + '", type="eq")'
                        mo_template_ls = self._device.query(mode="classid", target="lsServer", filter_str=filter_str)
                        if len(mo_template_ls) == 1:
                            parent_template_type = mo_template_ls[0].type

                if parent_template_type != "updating-template":
                    self.dynamic_vnic_connection_policy = ls_server.dynamic_con_policy_name
                    self.bios_policy = ls_server.bios_profile_name
                    self.host_firmware_package = ls_server.host_fw_policy_name
                    self.local_disk_configuration_policy = ls_server.local_disk_policy_name
                    self.maintenance_policy = ls_server.maint_policy_name
                    self.scrub_policy = ls_server.scrub_policy_name
                    self.uuid_pool = ls_server.ident_pool_name
                    self.uuid = ls_server.uuid
                    if not self.uuid_pool and self.uuid == "derived":
                        self.uuid = "hardware-default"

                    self.vmedia_policy = ls_server.vmedia_policy_name
                    self.boot_policy = ls_server.boot_policy_name
                    self.power_sync_policy = ls_server.power_sync_policy_name
                    self.power_control_policy = ls_server.power_policy_name
                    self.serial_over_lan_policy = ls_server.sol_policy_name
                    self.ipmi_access_profile = ls_server.mgmt_access_policy_name
                    self.placement_policy = ls_server.vcon_profile_name
                    self.threshold_policy = ls_server.stats_policy_name
                    self.kvm_management_policy = ls_server.kvm_mgmt_policy_name
                    self.graphics_card_policy = ls_server.graphics_card_policy_name
                    if ls_server.ext_ip_state == "pooled":
                        # We only fetch the Outband IPv4 Pool if it is configured explicitely. Other options ("none"
                        # or "static") correspond respectively to using the default ext-mgmt pool and using a statically
                        # assigned IP address to the CIMC
                        self.outband_ipv4_pool = ls_server.ext_ip_pool_name

                    if "vnicFcNode" in self._parent._config.sdk_objects:
                        for pool in self._config.sdk_objects["vnicFcNode"]:
                            if self._parent._dn:
                                if self._parent._dn + "/ls-" + self.name + "/" in pool.dn:
                                    self.wwnn_pool = pool.ident_pool_name
                                    if not self.wwnn_pool:
                                        self.wwnn = pool.addr

                    if "lsRequirement" in self._parent._config.sdk_objects:
                        for pool in self._config.sdk_objects["lsRequirement"]:
                            if self._parent._dn:
                                if self._parent._dn + "/ls-" + self.name + "/" in pool.dn:
                                    self.server_pool = pool.name
                                    self.server_pool_qualification = pool.qualifier
                                    self.restrict_migration = pool.restrict_migration

                    if "lstorageProfileBinding" in self._parent._config.sdk_objects:
                        for profile in self._config.sdk_objects["lstorageProfileBinding"]:
                            if self._parent._dn:
                                if self._parent._dn + "/ls-" + self.name + "/" in profile.dn:
                                    self.storage_profile = profile.storage_profile_name

                    if "vnicIpV4MgmtPooledAddr" in self._parent._config.sdk_objects:
                        for pool in self._config.sdk_objects["vnicIpV4MgmtPooledAddr"]:
                            if self._parent._dn:
                                if self._parent._dn + "/ls-" + self.name + "/" in pool.dn:
                                    self.inband_ipv4_pool = pool.name

                    if "vnicIpV6MgmtPooledAddr" in self._parent._config.sdk_objects:
                        for pool in self._config.sdk_objects["vnicIpV6MgmtPooledAddr"]:
                            if self._parent._dn:
                                if self._parent._dn + "/ls-" + self.name + "/" in pool.dn:
                                    self.inband_ipv6_pool = pool.name

                    if "vnicConnDef" in self._parent._config.sdk_objects:
                        for profile in self._config.sdk_objects["vnicConnDef"]:
                            if self._parent._dn:
                                if self._parent._dn + "/ls-" + self.name + "/" in profile.dn:
                                    self.san_connectivity_policy = profile.san_conn_policy_name
                                    self.lan_connectivity_policy = profile.lan_conn_policy_name

                    if "lsBinding" in self._parent._config.sdk_objects:
                        for ls_server in self._config.sdk_objects["lsBinding"]:
                            if self._parent._dn:
                                if self._parent._dn + "/ls-" + self.name + "/" in ls_server.dn:
                                    server = {}
                                    if "chassis" in ls_server.dn and "blade" in ls_server.dn:
                                        server.update({"chassis_id": ls_server.dn.split("/")[1].split("-")[1]})
                                        server.update({"blade": ls_server.dn.split("/")[2].split("-")[1]})
                                        self.servers.append(server)
                                    elif "rack_id" in ls_server.dn:
                                        server.update({"rack_id": ls_server.dn.split("/")[1].split("-")[2]})
                                        self.servers.append(server)

                    if "lsPower" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["lsPower"]:
                            if self._parent._dn:
                                if self._parent._dn + "/ls-" + self.name + "/" in policy.dn:
                                    self.server_power_state = policy.state

                    if "vnicIScsiNode" in self._parent._config.sdk_objects:
                        for policy in self._config.sdk_objects["vnicIScsiNode"]:
                            if self._parent._dn:
                                if self._parent._dn + "/ls-" + self.name + "/" in policy.dn:
                                    self.iscsi_initiator_name = policy.iqn_ident_pool_name

                    if self.type in ["initial-template", "updating-template"] and not self.lan_connectivity_policy \
                            or self.type in ["instance"]:
                    # We only fetch vNICs when LAN Connectivity Policy is not set for a Service Profile Template
                    # For a Service Profile Instance, we always fetch vNICs details to gather assigned identifiers
                        if "vnicEther" in self._parent._config.sdk_objects:
                            for vnic_ether in self._config.sdk_objects["vnicEther"]:
                                if self._parent._dn:
                                    if self._parent._dn + "/ls-" + self.name + "/" in vnic_ether.dn:
                                        vnic = {}
                                        vnic.update({"name": vnic_ether.name})
                                        if vnic_ether.addr != "derived":
                                            vnic.update({"mac_address": vnic_ether.addr})
                                        elif not vnic_ether.ident_pool_name and vnic_ether.addr == "derived":
                                            vnic.update({"mac_address": "hardware-default"})
                                        vnic.update({"mac_address_pool": vnic_ether.ident_pool_name})
                                        vnic.update({"order": vnic_ether.order})
                                        if vnic["order"] == "unspecified":
                                            vnic["order"] = None
                                        vnic.update({"fabric": vnic_ether.switch_id})
                                        vnic.update({"pin_group": vnic_ether.pin_to_group_name})
                                        vnic.update({"cdn_name": vnic_ether.admin_cdn_name})
                                        vnic.update({"adapter_policy": vnic_ether.adaptor_profile_name})
                                        vnic.update({"qos_policy": vnic_ether.qos_policy_name})
                                        vnic.update({"network_control_policy": vnic_ether.nw_ctrl_policy_name})
                                        vnic.update({"mtu": vnic_ether.mtu})
                                        vnic.update({"vnic_template": vnic_ether.nw_templ_name})
                                        vnic.update({"stats_threshold_policy": vnic_ether.stats_policy_name})

                                        if "vnicDynamicConPolicyRef" in self._parent._config.sdk_objects:
                                            for vnic_policy in self._config.sdk_objects["vnicDynamicConPolicyRef"]:
                                                if self._parent._dn + "/ls-" + self.name + "/" + "ether-" + \
                                                        vnic['name'] + "/" in vnic_policy.dn:
                                                    vnic.update({"dynamic_vnic": vnic_policy.con_policy_name})
                                        if "vnicUsnicConPolicyRef" in self._parent._config.sdk_objects:
                                            for vnic_policy in self._config.sdk_objects["vnicUsnicConPolicyRef"]:
                                                if self._parent._dn + "/ls-" + self.name + "/" + "ether-" + \
                                                        vnic['name'] + "/" in vnic_policy.dn:
                                                    vnic.update({"usnic": vnic_policy.con_policy_name})
                                        if "vnicVmqConPolicyRef" in self._parent._config.sdk_objects:
                                            for vnic_policy in self._config.sdk_objects["vnicVmqConPolicyRef"]:
                                                if self._parent._dn + "/ls-" + self.name + "/" + "ether-" + \
                                                        vnic['name'] + "/" in vnic_policy.dn:
                                                    vnic.update({"usnic": vnic_policy.con_policy_name})
                                        if "vnicEtherIf" in self._config.sdk_objects:
                                            vnic.update({"vlans": []})
                                            for vlan in self._config.sdk_objects["vnicEtherIf"]:
                                                if self._parent._dn + "/ls-" + self.name + "/" + "ether-" + \
                                                        vnic['name'] + "/" in vlan.dn:
                                                    if vlan.default_net in ["yes", "true"]:
                                                        vnic.update({"vlan_native": vlan.name})
                                                    else:
                                                        vnic['vlans'].append(vlan.name)

                                        if "fabricNetGroupRef" in self._parent._config.sdk_objects:
                                            vnic.update({"vlan_groups": []})
                                            for vlan_group in self._config.sdk_objects["fabricNetGroupRef"]:
                                                if self._parent._dn + "/ls-" + self.name + "/" + "ether-" + \
                                                        vnic['name'] + "/" in vlan_group.dn:
                                                    vnic['vlan_groups'].append(vlan_group.name)
                                        self.vnics.append(vnic)

                    if "vnicIScsi" in self._parent._config.sdk_objects:
                        for vnic_iscsi in self._config.sdk_objects["vnicIScsi"]:
                            if self._parent._dn:
                                if self._parent._dn + "/ls-" + self.name + "/" in vnic_iscsi.dn:
                                    vnic = {}
                                    vnic.update({"name": vnic_iscsi.name})
                                    vnic.update({"adapter_policy": vnic_iscsi.adaptor_profile_name})
                                    if vnic_iscsi.addr != "derived":
                                        vnic.update({"mac_address": vnic_iscsi.addr})
                                    elif not vnic_iscsi.ident_pool_name and vnic_iscsi.addr == "derived":
                                        vnic.update({"mac_address": "hardware-default"})
                                    vnic.update({"mac_address_pool": vnic_iscsi.ident_pool_name})
                                    if "vnicVlan" in self._parent._config.sdk_objects:
                                        for vlan in self._config.sdk_objects["vnicVlan"]:
                                            if vnic_iscsi.dn in vlan.dn:
                                                vnic.update({"vlan": vlan.vlan_name})
                                    self.iscsi_vnics.append(vnic)

                    if self.type in ["initial-template", "updating-template"] and not self.san_connectivity_policy \
                            or self.type in ["instance"]:
                    # We only fetch vHBAs when SAN Connectivity Policy is not set for a Service Profile Template
                    # For a Service Profile Instance, we fetch vHBAs details to gather assigned identifiers
                        if "vnicFc" in self._parent._config.sdk_objects:
                            for vnic_fc in self._config.sdk_objects["vnicFc"]:
                                if self._parent._dn:
                                    if self._parent._dn + "/ls-" + self.name + "/" in vnic_fc.dn:
                                        vhba = {}
                                        vhba.update({"name": vnic_fc.name})
                                        vhba.update({"wwpn_pool": vnic_fc.ident_pool_name})
                                        if vnic_fc.addr != "derived":
                                            vhba.update({"wwpn": vnic_fc.addr})
                                        elif not vnic_fc.ident_pool_name and vnic_fc.addr == "derived":
                                            vhba.update({"wwpn": "derived"})
                                        vhba.update({"order": vnic_fc.order})
                                        if vhba["order"] == "unspecified":
                                            vhba["order"] = None
                                        vhba.update({"fabric": vnic_fc.switch_id})
                                        vhba.update({"max_data_field_size": vnic_fc.max_data_field_size})
                                        vhba.update({"pin_group": vnic_fc.pin_to_group_name})
                                        vhba.update({"adapter_policy": vnic_fc.adaptor_profile_name})
                                        vhba.update({"qos_policy": vnic_fc.qos_policy_name})
                                        vhba.update({"vhba_template": vnic_fc.nw_templ_name})
                                        vhba.update({"stats_threshold_policy": vnic_fc.stats_policy_name})
                                        vhba.update({"persistent_binding": vnic_fc.pers_bind})
                                        if "vnicfcIf" in self._config.sdk_objects:
                                            for vsan in self._config.sdk_objects["vnicfcIf"]:
                                                if self._parent._dn + "/ls-" + self.name + "/" + "fc-" + \
                                                        vhba['name'] + "/" in vsan.dn:
                                                    vhba['vsan'].append(vsan.name)
                                        self.vhbas.append(vhba)

                    if "lsVConAssign" in self._parent._config.sdk_objects:
                        for vcon in self._config.sdk_objects["lsVConAssign"]:
                            if self._parent._dn:
                                if self._parent._dn + "/ls-" + self.name + "/" in vcon.dn:
                                    place = {}
                                    place.update({"vcon": vcon.admin_vcon})
                                    place.update({"order": vcon.order})
                                    if place["order"] == "unspecified":
                                        place["order"] = None
                                    if vcon.transport == "ethernet":
                                        place.update({"vnic": vcon.vnic_name})
                                    elif vcon.transport == "fc":
                                        place.update({"vhba": vcon.vnic_name})
                                    self.placement.append(place)

                    if "storageIniGroup" in self._parent._config.sdk_objects:
                        for initiator_group in self._config.sdk_objects["storageIniGroup"]:
                            if self._parent._dn:
                                if self._parent._dn + "/ls-" + self.name + "/" in initiator_group.dn:
                                    initiator = {}
                                    initiator.update({"name": initiator_group.name})
                                    initiator.update({"descr": initiator_group.descr})
                                    if "vnicFcGroupDef" in self._parent._config.sdk_objects:
                                        for fc_group in self._config.sdk_objects["vnicFcGroupDef"]:
                                            if initiator_group.dn in fc_group.dn:
                                                initiator.update(
                                                    {"storage_connection_policy": fc_group.storage_conn_policy_name})
                                    if "storageInitiator" in self._parent._config.sdk_objects:
                                        initiator.update({"initiators": []})
                                        for sto_init in self._config.sdk_objects["storageInitiator"]:
                                            if initiator_group.dn in sto_init.dn:
                                                initiator['initiators'].append(sto_init.name)
                                    self.vhba_initiator_groups.append(initiator)

                    if "vnicIScsiBootVnic" in self._parent._config.sdk_objects:
                        for mo in self._config.sdk_objects["vnicIScsiBootVnic"]:
                            if self._parent._dn:
                                if self._parent._dn + "/ls-" + self.name + "/" in mo.dn:
                                    boot_param = {}
                                    boot_param.update({"iscsi_vnic_name": mo.name})
                                    boot_param.update({"authentication_profile": mo.auth_profile_name})
                                    boot_param.update({"iqn_pool": mo.iqn_ident_pool_name})
                                    if mo.initiator_name != "derived":
                                        boot_param.update({"iqn": mo.initiator_name})
                                    boot_param.update({"iqn": mo.iqn_ident_pool_name})
                                    if "vnicIPv4PooledIscsiAddr" in self._parent._config.sdk_objects:
                                        for mo_ip_pool in self._config.sdk_objects["vnicIPv4PooledIscsiAddr"]:
                                            if mo.dn in mo_ip_pool.dn:
                                                boot_param.update({"initiator_ip_address_policy":
                                                                       mo_ip_pool.ident_pool_name})
                                    if "vnicIScsiAutoTargetIf" in self._parent._config.sdk_objects:
                                        for mo_if_auto in self._config.sdk_objects["vnicIScsiAutoTargetIf"]:
                                            if mo.dn in mo_if_auto.dn:
                                                boot_param.update({"dhcp_vendor_id": mo_if_auto.dhcp_vendor_id})
                                    boot_param.update({"iscsi_static_targets": []})
                                    if "vnicIScsiStaticTargetIf" in self._parent._config.sdk_objects:
                                        for mo_if in self._config.sdk_objects["vnicIScsiStaticTargetIf"]:
                                            if mo.dn in mo_if.dn:
                                                interface = {}
                                                interface.update({"name": mo_if.name})
                                                interface.update({"port": mo_if.port})
                                                interface.update({"authentication_profile": mo_if.auth_profile_name})
                                                interface.update({"ip_address": mo_if.ip_address})
                                                interface.update({"priority": mo_if.priority})
                                                if "vnicLun" in self._parent._config.sdk_objects:
                                                    for mo_lun in self._config.sdk_objects["vnicLun"]:
                                                        if mo_if.dn in mo_lun.dn:
                                                            interface.update({"lun_id": mo_lun.id})
                                                boot_param["iscsi_static_targets"].append(interface)
                                    self.iscsi_boot_parameters.append(boot_param)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)
                
                for element in self.vhbas:
                    for value in ["adapter_policy", "vhba_template", "fabric", "name", "order", "wwpn_pool",
                                  "pin_group", "max_data_field_size", "qos_policy", "vsan", "stats_threshold_policy",
                                  "persistent_binding", "wwpn"]:
                        if value not in element:
                            element[value] = None

                for element in self.vhba_initiator_groups:
                    for value in ["storage_connection_policy", "initiators", "name", "descr"]:
                        if value not in element:
                            element[value] = None

                for element in self.iscsi_vnics:
                    for value in ["name", "vlan", "mac_address_pool", "adapter_policy", "mac_address"]:
                        if value not in element:
                            element[value] = None
                
                for element in self.placement:
                    for value in ["vcon", "vnic", "vhba", "order"]:
                        if value not in element:
                            element[value] = None
                
                for element in self.vnics:
                    for value in ["vlans", "vnic_template", "adapter_policy", "name", "cdn_source", "cdn_name",
                                  "vlan_native", "order", "fabric", "mac_address_pool", "mtu", "qos_policy",
                                  "network_control_policy", "dynamic_vnic", "usnic", "vmq", "pin_group",
                                  "stats_threshold_policy", "mac_address", "vlan_groups"]:
                        if value not in element:
                            element[value] = None

                for element in self.iscsi_boot_parameters:
                    for value in ["iscsi_vnic_name", "authentication_profile", "iqn_pool",
                                  "initiator_ip_address_policy", "iscsi_static_targets", "dhcp_vendor_id",
                                  "priority", "iqn"]:
                        if value not in element:
                            element[value] = None
                    if element["iscsi_static_targets"]:
                        for subelement in element["iscsi_static_targets"]:
                            for subvalue in ["name", "port", "lun_id", "authentication_profile", "ip_address"]:
                                if subvalue not in subelement:
                                    subelement[subvalue] = None

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

        outband_ipv4_pool_state = None
        if self.outband_ipv4_pool:
            outband_ipv4_pool_state = "pooled"

        uuid_pool = self.uuid_pool
        uuid = self.uuid
        if self.uuid == "hardware-default":
            uuid = "derived"
            uuid_pool = None

        mo_ls_server = LsServer(parent_mo_or_dn=parent_mo,
                                name=self.name,
                                type=self.type,
                                bios_profile_name=self.bios_policy,
                                boot_policy_name=self.boot_policy,
                                descr=self.descr,
                                usr_lbl=self.user_label,
                                dynamic_con_policy_name=self.dynamic_vnic_connection_policy,
                                host_fw_policy_name=self.host_firmware_package,
                                local_disk_policy_name=self.local_disk_configuration_policy,
                                maint_policy_name=self.maintenance_policy,
                                scrub_policy_name=self.scrub_policy,
                                ident_pool_name=uuid_pool,
                                uuid=uuid,
                                vmedia_policy_name=self.vmedia_policy,
                                power_sync_policy_name=self.power_sync_policy,
                                power_policy_name=self.power_control_policy,
                                sol_policy_name=self.serial_over_lan_policy,
                                mgmt_access_policy_name=self.ipmi_access_profile,
                                vcon_profile_name=self.placement_policy,
                                stats_policy_name=self.threshold_policy,
                                kvm_mgmt_policy_name=self.kvm_management_policy,
                                graphics_card_policy_name=self.graphics_card_policy,
                                ext_ip_pool_name=self.outband_ipv4_pool,
                                ext_ip_state=outband_ipv4_pool_state)

        self._handle.add_mo(mo=mo_ls_server, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False

        # Add Asset Tag
        if self.asset_tag:
            LsServerExtension(parent_mo_or_dn=mo_ls_server, asset_tag=self.asset_tag)

        # Add WWNN Pool
        if self.wwnn_pool:
            VnicFcNode(parent_mo_or_dn=mo_ls_server, ident_pool_name=self.wwnn_pool, addr=self.wwnn)

        # Add Server Pool
        if self.server_pool:
            LsRequirement(parent_mo_or_dn=mo_ls_server, name=self.server_pool, qualifier=self.server_pool_qualification,
                          restrict_migration=self.restrict_migration)

        # Add a Storage Profile
        if self.storage_profile:
            LstorageProfileBinding(parent_mo_or_dn=mo_ls_server, storage_profile_name=self.storage_profile)

        # Add SAN and/or LAN Connectivity Policy
        if self.san_connectivity_policy or self.lan_connectivity_policy:
            VnicConnDef(parent_mo_or_dn=mo_ls_server, san_conn_policy_name=self.san_connectivity_policy,
                        lan_conn_policy_name=self.lan_connectivity_policy)

        # Add Inband Management IP Address
        if self.inband_ipv4_pool or self.inband_ipv6_pool:
            mo_mgmt_int = MgmtInterface(parent_mo_or_dn=mo_ls_server,
                                        ip_v4_state="pooled",
                                        ip_v6_state="pooled",
                                        mode="in-band")
            mo_vnet = MgmtVnet(parent_mo_or_dn=mo_mgmt_int, id="1")
            VnicIpV4MgmtPooledAddr(parent_mo_or_dn=mo_vnet, name=self.inband_ipv4_pool)
            VnicIpV6MgmtPooledAddr(parent_mo_or_dn=mo_vnet, name=self.inband_ipv6_pool)

        # Add the power state to be applied when a server pool is associated with the server
        # Status : only "admin-down", "admin-up", "down" or "up" - are used in a service profile
        # "soft-shut-down-only" can also be found as a state
        if self.server_power_state:
            LsPower(parent_mo_or_dn=mo_ls_server, state=self.server_power_state)

        # Add association to a server
        for server in self.servers:
            if ("chassis_id" and "blade") in server and "rack_id" not in server:
                server = "sys/chassis-" + server["chassis_id"] + "/blade-" + server["blade"]
            elif ("chassis_id" and "blade") not in server and "rack_id" in server:
                server = "sys/rack-unit-" + server["rack_id"]
            else:
                self.logger(level="error",
                            message="Wrong server details (chassis & blade /rack unit) for association "
                                    + "with service profile " + str(self.name))
                server = None
            LsBinding(parent_mo_or_dn=mo_ls_server, pn_dn=server)

        # Add all the elements above. The elements below have all their own commit
        self._handle.add_mo(mo=mo_ls_server, modify_present=True)
        if commit:
            if self.commit(detail="Service Profile policies of the service profile " + str(self.name)) != True:
                return False

        if self.iscsi_initiator_name or self.iscsi_vnics:
            VnicIScsiNode(parent_mo_or_dn=mo_ls_server, iqn_ident_pool_name=self.iscsi_initiator_name)
            for iscsi_vnic in self.iscsi_vnics:
                mac_address_pool = iscsi_vnic['mac_address_pool']
                mac_address = iscsi_vnic["mac_address"]

                mo_vnic_iscsi = VnicIScsi(parent_mo_or_dn=mo_ls_server,
                                          adaptor_profile_name=iscsi_vnic["adapter_policy"],
                                          ident_pool_name=mac_address_pool,
                                          addr=mac_address,
                                          name=iscsi_vnic['name'])
                VnicVlan(parent_mo_or_dn=mo_vnic_iscsi, vlan_name=iscsi_vnic["vlan"])

        for vnic in self.vnics:
            if vnic['fabric']:
                vnic['fabric'] = vnic['fabric'].upper()

            mac_address_pool = vnic['mac_address_pool']
            mac_address = vnic["mac_address"]
            if mac_address == "hardware-default":
                mac_address = "derived"
                mac_address_pool = None

            mo_vnic_ether = VnicEther(parent_mo_or_dn=mo_ls_server,
                                      name=vnic['name'],
                                      pin_to_group_name=vnic['pin_group'],
                                      order=vnic['order'],
                                      switch_id=vnic['fabric'],
                                      admin_cdn_name=vnic['cdn_name'],
                                      cdn_source=vnic['cdn_source'],
                                      nw_ctrl_policy_name=vnic['network_control_policy'],
                                      adaptor_profile_name=vnic['adapter_policy'],
                                      qos_policy_name=vnic['qos_policy'],
                                      ident_pool_name=mac_address_pool,
                                      mtu=vnic['mtu'],
                                      nw_templ_name=vnic['vnic_template'],
                                      stats_policy_name=vnic['stats_threshold_policy'],
                                      addr=mac_address)

            if vnic['dynamic_vnic']:
                VnicDynamicConPolicyRef(parent_mo_or_dn=mo_vnic_ether, con_policy_name=vnic['dynamic_vnic'])
            elif vnic['usnic']:
                VnicUsnicConPolicyRef(parent_mo_or_dn=mo_vnic_ether, con_policy_name=vnic['usnic'])
            elif vnic['vmq']:
                VnicVmqConPolicyRef(parent_mo_or_dn=mo_vnic_ether, con_policy_name=vnic['vmq'])

            if vnic['vlan_native']:
                VnicEtherIf(parent_mo_or_dn=mo_vnic_ether, name=vnic['vlan_native'], default_net="yes")
            if vnic['vlans']:
                for vlan in vnic['vlans']:
                    VnicEtherIf(parent_mo_or_dn=mo_vnic_ether, name=vlan, default_net="no")
            if vnic['vlan_groups']:
                for vlan_group in vnic['vlan_groups']:
                    FabricNetGroupRef(parent_mo_or_dn=mo_vnic_ether, name=vlan_group)
                
            self._handle.add_mo(mo=mo_vnic_ether, modify_present=True)
            if commit:
                if self.commit(detail=vnic['name']) != True:
                    return False
        
        for vhba in self.vhbas:
            if vhba['fabric']:
                vhba['fabric'] = vhba['fabric'].upper()
            mo_vnic_fc = VnicFc(parent_mo_or_dn=mo_ls_server,
                                name=vhba['name'],
                                max_data_field_size=vhba['max_data_field_size'],
                                order=vhba['order'],
                                switch_id=vhba['fabric'],
                                pin_to_group_name=vhba['pin_group'],
                                ident_pool_name=vhba['wwpn_pool'],
                                adaptor_profile_name=vhba['adapter_policy'],
                                qos_policy_name=vhba['qos_policy'],
                                nw_templ_name=vhba['vhba_template'],
                                stats_policy_name=vhba['stats_threshold_policy'],
                                pers_bind=vhba['persistent_binding'],
                                addr=vhba["wwpn"])
            if vhba['vsan']:
                VnicFcIf(parent_mo_or_dn=mo_vnic_fc, name=vhba['vsan'])
            self._handle.add_mo(mo=mo_vnic_fc, modify_present=True)
            if commit:
                if self.commit(detail=vhba['name']) != True:
                    return False

        for place in self.placement:
            if ("vhba" in place) or ("vnic" in place):
                transport = ""
                name = ""
                if 'vnic' in place:
                    if place['vnic']:
                        transport = 'ethernet'
                        name = place['vnic']
                if 'vhba' in place:
                    if place['vhba']:
                        transport = 'fc'
                        name = place['vhba']
                mo_vcon_assign = LsVConAssign(parent_mo_or_dn=mo_ls_server, admin_vcon=place['vcon'],
                                              order=place['order'], transport=transport, vnic_name=name)
                self._handle.add_mo(mo=mo_vcon_assign, modify_present=True)
                if commit:
                    if self.commit(detail=name) != True:
                        return False

        for initiator in self.vhba_initiator_groups:
            mo_ini_group = StorageIniGroup(parent_mo_or_dn=mo_ls_server, name=initiator['name'],
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

        for iscsi_boot_parameter in self.iscsi_boot_parameters:
            mo_iscsi_boot_params = VnicIScsiBootParams(parent_mo_or_dn=mo_ls_server)

            if iscsi_boot_parameter["dhcp_vendor_id"]:
                mo_iscsi_boot_vnic = VnicIScsiBootVnic(parent_mo_or_dn=mo_iscsi_boot_params,
                                                       name=iscsi_boot_parameter["iscsi_vnic_name"]
                                                       )
                # mo_ipv4_if = VnicIPv4If(parent_mo_or_dn=mo_iscsi_boot_vnic)
                # mo_ipv4_dhcp = VnicIPv4Dhcp(parent_mo_or_dn=mo_ipv4_if)
                VnicIScsiAutoTargetIf(parent_mo_or_dn=mo_iscsi_boot_vnic,
                                      dhcp_vendor_id=iscsi_boot_parameter["dhcp_vendor_id"])
            else:
                mo_iscsi_boot_vnic = VnicIScsiBootVnic(parent_mo_or_dn=mo_iscsi_boot_params,
                                                       auth_profile_name=iscsi_boot_parameter["authentication_profile"],
                                                       iqn_ident_pool_name=iscsi_boot_parameter["iqn_pool"],
                                                       initiator_name=iscsi_boot_parameter["iqn"],
                                                       name=iscsi_boot_parameter["iscsi_vnic_name"])
                mo_ipv4_if = VnicIPv4If(parent_mo_or_dn=mo_iscsi_boot_vnic)
                VnicIPv4PooledIscsiAddr(parent_mo_or_dn=mo_ipv4_if,
                                        ident_pool_name=iscsi_boot_parameter["initiator_ip_address_policy"])

                for target in iscsi_boot_parameter["iscsi_static_targets"]:
                    mo_static_target_if = VnicIScsiStaticTargetIf(parent_mo_or_dn=mo_iscsi_boot_vnic,
                                                                  ip_address=target["ip_address"],
                                                                  name=target["name"],
                                                                  port=target["port"],
                                                                  auth_profile_name=target["authentication_profile"],
                                                                  priority=target["priority"])
                    VnicLun(parent_mo_or_dn=mo_static_target_if,
                            id=target["lun_id"])

            self._handle.add_mo(mo=mo_iscsi_boot_params, modify_present=True)
            if commit:
                if self.commit(detail=iscsi_boot_parameter["iscsi_vnic_name"]) != True:
                    return False

        return True

    def instantiate_profile(self):
        self.logger(message="Instantiating " + self._CONFIG_NAME +
                            " configuration from " + str(self.service_profile_template))

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

            elem = ls_instantiate_n_named_template(cookie=self._handle.cookie,
                                                   dn=parent_mo + "/ls-" + self.service_profile_template,
                                                   in_error_on_existing="false", in_name_set=dn_set,
                                                   in_target_org=parent_mo, in_hierarchical="false")

            for i in range(self._device.push_attempts):
                try:
                    if i:
                        self.logger(level="warning",
                                    message="Trying to push again the instantiated service profile(s) from " +
                                            str(self.service_profile_template))
                    self._handle.process_xml_elem(elem)
                    self.logger(level='debug',
                                message=self.number_of_instances + " " + self._CONFIG_NAME + " instantiated from " +
                                        str(self.service_profile_template) + " starting with " + str(self.name) +
                                        self.suffix_start_number)
                    return True
                except ConnectionRefusedError:
                    self.logger(level="error", message="Connection refused while trying to instantiate from " +
                                                       str(self.service_profile_template))
                except UcsException as err:
                    self.logger(level="error",
                                message="Error while trying to instantiate from " +
                                        str(self.service_profile_template) + " " + err.error_descr)
                except urllib.error.URLError:
                    self.logger(level="error",
                                message="Timeout while trying to instantiate from " + str(
                                    self.service_profile_template))

        else:
            elem = ls_instantiate_template(cookie=self._handle.cookie,
                                           dn=parent_mo + "/ls-" + self.service_profile_template,
                                           in_error_on_existing="false",
                                           in_server_name=self.name,
                                           in_target_org=parent_mo, in_hierarchical="false")

            for i in range(self._device.push_attempts):
                try:
                    if i:
                        self.logger(level="warning",
                                    message="Trying to push again the instantiated service profile(s) from " +
                                            str(self.service_profile_template))
                    self._handle.process_xml_elem(elem)
                    self.logger(level='debug',
                                message=self._CONFIG_NAME + " " + str(self.name) + " instantiated from " +
                                        str(self.service_profile_template))
                    return True
                except ConnectionRefusedError:
                    self.logger(level="error", message="Connection refused while trying to instantiate from " +
                                                       str(self.service_profile_template))
                except UcsException as err:
                    self.logger(level="error",
                                message="Error while trying to instantiate from " +
                                        str(self.service_profile_template) + " " + err.error_descr)
                except urllib.error.URLError:
                    self.logger(level="error",
                                message="Timeout while trying to instantiate from " + str(
                                    self.service_profile_template))


class UcsSystemMemoryPolicy(UcsSystemConfigObject):
    _CONFIG_NAME = "Memory Policy"
    _UCS_SDK_OBJECT_NAME = "computeMemoryConfigPolicy"

    def __init__(self, parent=None, json_content=None, compute_memory_config_policy=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.blacklisting = None

        if self._config.load_from == "live":
            if compute_memory_config_policy is not None:
                self.blacklisting = compute_memory_config_policy.black_listing

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

        if hasattr(self._parent, '_dn'):
            parent_mo = self._parent._dn
        else:
            self.logger(level="error", message="Impossible to find the parent dn of " + self._CONFIG_NAME)
            return False

        mo_compute_memory_config_policy = ComputeMemoryConfigPolicy(parent_mo_or_dn=parent_mo,
                                                                    black_listing=self.blacklisting,
                                                                    name="default")
        self._handle.add_mo(mo=mo_compute_memory_config_policy, modify_present=True)
        if commit:
            if self.commit() != True:
                return False
        return True


class UcsSystemThresholdPolicy(UcsSystemConfigObject):
    _CONFIG_NAME = "Threshold Policy"
    _UCS_SDK_OBJECT_NAME = "statsThresholdPolicy"

    def __init__(self, parent=None, json_content=None, stats_threshold_policy=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.name = None
        self.descr = None
        self.threshold_classes = []

        # Open JSON configuration file
        try:
            json_file = open("./config/ucs/threshold_policies_table.json")
            self._model_table = json.load(json_file)
            json_file.close()
        except FileNotFoundError:
            self.logger(level="error", message="Unable to find threshold_policies_table.json file")
            self._model_table = {}

        if self._config.load_from == "live":
            if stats_threshold_policy is not None:

                self.name = stats_threshold_policy.name
                self.descr = stats_threshold_policy.descr

                if "statsThresholdClass" in self._parent._config.sdk_objects:
                    for thr_class in self._config.sdk_objects["statsThresholdClass"]:
                        if self._parent._dn:
                            if self._parent._dn + "/thr-policy-" + self.name + "/" in thr_class.dn:
                                stat_thr_class = {}

                                # Find group and stat class
                                group = ""
                                stat_class = ""
                                for model_group in self._model_table:
                                    for model_stat_class, model_stat_class_values in\
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

                                if "statsThrFloatDefinition" in self._parent._config.sdk_objects:
                                    for thr_def in self._config.sdk_objects["statsThrFloatDefinition"]:
                                        if self._parent._dn:
                                            if self._parent._dn + "/thr-policy-" + self.name + "/" + \
                                                    thr_class.stats_class_id in thr_def.dn:
                                                thr_32 = {}

                                                # Find property type
                                                property_type = ""
                                                for model_property_type, model_property_type_sdk in \
                                                        self._model_table[group][stat_class]["values"].items():
                                                    if model_property_type_sdk == thr_def.prop_id:
                                                        property_type = model_property_type
                                                        break

                                                thr_32.update({"property_type": property_type})
                                                thr_32.update({"normal_value": thr_def.normal_value.split('.')[0]})
                                                thr_32.update({"alarm_triggers_above": []})
                                                thr_32.update({"alarm_triggers_below": []})
                                                if "statsThrFloatValue" in self._parent._config.sdk_objects:
                                                    for thr_val in self._config.sdk_objects["statsThrFloatValue"]:
                                                        if self._parent._dn:
                                                            if self._parent._dn + "/thr-policy-" + self.name + "/" \
                                                                    + thr_class.stats_class_id + "/" + \
                                                                    thr_def.prop_id in thr_val.dn:
                                                                val_32 = {}
                                                                val_32.update({"severity": thr_val.severity})
                                                                val_32.update({"down":
                                                                                   thr_val.deescalating.split('.')[0]})
                                                                val_32.update({"up":
                                                                                   thr_val.escalating.split('.')[0]})
                                                                if thr_val.direction == "aboveNormal":
                                                                    thr_32["alarm_triggers_above"].append(val_32)
                                                                elif thr_val.direction == "belowNormal":
                                                                    thr_32["alarm_triggers_below"].append(val_32)
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
            self.logger(message="Pushing " + self._CONFIG_NAME + " configuration")
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

            stats_class_id = self._model_table[thr_class["group"]][thr_class["stat_class"]]["name"]

            mo_stats_threshold_class = StatsThresholdClass(parent_mo_or_dn=mo_stats_threshold_policy,
                                                           stats_class_id=stats_class_id)
            if thr_class["threshold_definitions"]:
                for definition in thr_class["threshold_definitions"]:
                    prop_id = self._model_table[thr_class["group"]][thr_class["stat_class"]]["values"][definition["property_type"]]
                    mo_stats_thr_32_def = StatsThrFloatDefinition(parent_mo_or_dn=mo_stats_threshold_class,
                                                                  normal_value=definition["normal_value"],
                                                                  prop_id=prop_id)
                    if definition["alarm_triggers_above"]:
                        for alarm in definition["alarm_triggers_above"]:
                            StatsThrFloatValue(parent_mo_or_dn=mo_stats_thr_32_def,
                                               deescalating=alarm["down"],
                                               escalating=alarm["up"],
                                               severity=alarm["severity"],
                                               direction="aboveNormal")
                    if definition["alarm_triggers_below"]:
                        for alarm in definition["alarm_triggers_below"]:
                            StatsThrFloatValue(parent_mo_or_dn=mo_stats_thr_32_def,
                                               deescalating=alarm["down"],
                                               escalating=alarm["up"],
                                               severity=alarm["severity"],
                                               direction="belowNormal")
        self._handle.add_mo(mo=mo_stats_threshold_policy, modify_present=True)
        if commit:
            if self.commit() != True:
                return False
        return True


class UcsSystemDiagnosticsPolicy(UcsSystemConfigObject):
    _CONFIG_NAME = "Diagnostics Policy"
    _UCS_SDK_OBJECT_NAME = "diagRunPolicy"

    def __init__(self, parent=None, json_content=None, diag_run_policy=None):
        UcsSystemConfigObject.__init__(self, parent=parent)
        self.name = None
        self.descr = None
        self.memory_tests = []

        if self._config.load_from == "live":
            if diag_run_policy is not None:
                self.name = diag_run_policy.name
                self.descr = diag_run_policy.descr

                if "diagMemoryTest" in self._parent._config.sdk_objects:
                    for diag in self._config.sdk_objects["diagMemoryTest"]:
                        if self._parent._dn:
                            if self._parent._dn + "/diag-policy-" + self.name + "/" in diag.dn:
                                test = {}
                                test.update({"order": diag.order})
                                test.update({"cpu_filter": diag.cpu_filter})
                                test.update({"loop_count": diag.loop_count})
                                test.update({"memory_chunk_size": diag.mem_chunk_size})
                                test.update({"memory_size": diag.mem_size})
                                test.update({"pattern": diag.pattern})
                                self.memory_tests.append(test)

        elif self._config.load_from == "file":
            if json_content is not None:
                if not self.get_attributes_from_json(json_content=json_content):
                    self.logger(level="error",
                                message="Unable to get attributes from JSON content for " + self._CONFIG_NAME)

                for element in self.memory_tests:
                    for value in ["order", "cpu_filter", "loop_count", "memory_chunk_size", "memory_size", "pattern"]:
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

        mo_diag_run_policy = DiagRunPolicy(parent_mo_or_dn=parent_mo, name=self.name, descr=self.descr)
        for test in self.memory_tests:
            DiagMemoryTest(parent_mo_or_dn=mo_diag_run_policy,
                           cpu_filter=test["cpu_filter"],
                           loop_count=test["loop_count"],
                           mem_chunk_size=test["memory_chunk_size"],
                           mem_size=test["memory_size"],
                           order=test["order"],
                           pattern=test["pattern"])

        self._handle.add_mo(mo=mo_diag_run_policy, modify_present=True)
        if commit:
            if self.commit(detail=self.name) != True:
                return False
        return True

