# coding: utf-8
# !/usr/bin/env python

""" backup.py: Easy UCS Deployment Tool """

import uuid

from repository.metadata import BackupMetadata


class GenericBackup:
    def __init__(self, parent=None, backup_type=None):
        self.backup_file_extension = ""
        self.device = parent.parent
        self.parent = parent
        self.uuid = uuid.uuid4()

        # Needs to be created after UUID
        self.metadata = BackupMetadata(parent=self, backup_type=backup_type)

        self._parent_having_logger = self._find_logger()

    def logger(self, level='info', message="No message"):
        if not self._parent_having_logger:
            self._parent_having_logger = self._find_logger()

        if self._parent_having_logger:
            self._parent_having_logger.logger(level=level, message=message)

    def _find_logger(self):
        # Method to find the object having a logger - it can be high up in the hierarchy of objects
        current_object = self
        while hasattr(current_object, 'parent') and not hasattr(current_object, '_logger_handle'):
            current_object = current_object.parent

        if hasattr(current_object, '_logger_handle'):
            return current_object
        else:
            print("WARNING: No logger found in backup")
            return None

    def __str__(self):
        return str(vars(self))
