# coding: utf-8
# !/usr/bin/env python

""" tpm.py: Easy UCS Deployment Tool """
from easyucs import __author__, __copyright__,  __version__, __status__


import re
from easyucs.inventory.object import GenericUcsInventoryObject, UcsImcInventoryObject, UcsSystemInventoryObject


class UcsTpm(GenericUcsInventoryObject):
    _UCS_SDK_OBJECT_NAME = "equipmentTpm"

    def __init__(self, parent=None, equipment_tpm=None):
        GenericUcsInventoryObject.__init__(self, parent=parent, ucs_sdk_object=equipment_tpm)

        self.active_status = self.get_attribute(ucs_sdk_object=equipment_tpm, attribute_name="active_status")
        self.enabled_status = self.get_attribute(ucs_sdk_object=equipment_tpm, attribute_name="enabled_status")
        self.model = self.get_attribute(ucs_sdk_object=equipment_tpm, attribute_name="model")
        self.ownership = self.get_attribute(ucs_sdk_object=equipment_tpm, attribute_name="ownership")
        self.serial = self.get_attribute(ucs_sdk_object=equipment_tpm, attribute_name="serial")
        self.tpm_revision = self.get_attribute(ucs_sdk_object=equipment_tpm, attribute_name="tpm_revision")
        self.vendor = self.get_attribute(ucs_sdk_object=equipment_tpm, attribute_name="vendor")


class UcsSystemTpm(UcsTpm, UcsSystemInventoryObject):
    def __init__(self, parent=None, equipment_tpm=None):
        UcsTpm.__init__(self, parent=parent, equipment_tpm=equipment_tpm)

        self.id = self.get_attribute(ucs_sdk_object=equipment_tpm, attribute_name="id")
        self.password_state = self.get_attribute(ucs_sdk_object=equipment_tpm, attribute_name="password_state")
        self.revision = self.get_attribute(ucs_sdk_object=equipment_tpm, attribute_name="revision")
        self.type = self.get_attribute(ucs_sdk_object=equipment_tpm, attribute_name="type")

        UcsSystemInventoryObject.__init__(self, parent=parent, ucs_sdk_object=equipment_tpm)


class UcsImcTpm(UcsTpm, UcsImcInventoryObject):
    def __init__(self, parent=None, equipment_tpm=None):
        UcsTpm.__init__(self, parent=parent, equipment_tpm=equipment_tpm)

        self.version = self.get_attribute(ucs_sdk_object=equipment_tpm, attribute_name="version")

        UcsImcInventoryObject.__init__(self, parent=parent, ucs_sdk_object=equipment_tpm)
