# coding: utf-8
# !/usr/bin/env python

""" backup.py: Easy UCS Deployment Tool """

from imcsdk.mometa.mgmt.MgmtBackup import MgmtBackup as imcsdk_MgmtBackup
from ucscsdk.mometa.mgmt.MgmtBackup import MgmtBackup as ucscsdk_MgmtBackup
from ucsmsdk.mometa.mgmt.MgmtBackup import MgmtBackup as ucsmsdk_MgmtBackup

from backup.backup import GenericBackup


class GenericUcsBackup(GenericBackup):
    def __init__(self, parent=None, backup_type=None):
        GenericBackup.__init__(self, parent=parent, backup_type=backup_type)
        self.valid_backup_types = []


class UcsSystemBackup(GenericUcsBackup):
    def __init__(self, parent=None, backup_type=None):
        GenericUcsBackup.__init__(self, parent=parent, backup_type=backup_type)
        self.metadata.backup_file_extension = ".tgz"
        self.backup_mo = ucsmsdk_MgmtBackup
        self.valid_backup_types = ["full-state", "config-logical", "config-system", "config-all"]

        # Config exports are using XML file extension
        if self.metadata.backup_type in ["config-logical", "config-system", "config-all"]:
            self.metadata.backup_file_extension = ".xml"


class UcsImcBackup(GenericUcsBackup):
    def __init__(self, parent=None, backup_type=None):
        GenericUcsBackup.__init__(self, parent=parent, backup_type=backup_type)
        self.metadata.backup_file_extension = ".xml"
        self.backup_mo = imcsdk_MgmtBackup
        self.valid_backup_types = ["bmc", "cmc", "cimc1", "cimc2", "vic"]


class UcsCentralBackup(GenericUcsBackup):
    def __init__(self, parent=None, backup_type=None):
        self.domains = []
        GenericUcsBackup.__init__(self, parent=parent, backup_type=backup_type)
        self.metadata.backup_file_extension = ".tgz"
        self.backup_mo = ucscsdk_MgmtBackup
        self.valid_backup_types = ["full-state"]
