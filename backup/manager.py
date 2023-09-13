# coding: utf-8
# !/usr/bin/env python

""" manager.py: Easy UCS Deployment Tool """


class GenericBackupManager:
    def __init__(self, parent=None):
        self.backup_class_name = None
        self.backup_list = []
        self.parent = parent

        self._parent_having_logger = self._find_logger()

    def clear_backup_list(self):
        """
        Removes all the backups from the backup list
        :return: True
        """
        self.backup_list.clear()
        return True

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
            print("WARNING: No logger found in Backup Manager")
            return None

    def get_latest_backup(self):
        """
        Returns the most recent backup from the inventory list
        :return: GenericBackup (or subclass), None if no backup is found
        """
        if len(self.backup_list) == 0:
            return None
        # return sorted(self.backup_list, key=lambda backup: backup.metadata.timestamp)[-1]
        return self.backup_list[-1]

    def find_backup_by_uuid(self, uuid=None):
        """
        Finds a backup from the backup list given a specific UUID
        :param uuid: UUID of the backup to find
        :return: backup if found, None otherwise
        """
        if uuid is None:
            self.logger(level="error", message="No backup UUID specified in find backup request.")
            return None

        backup_list = [backup for backup in self.backup_list if str(backup.uuid) == str(uuid)]
        if len(backup_list) != 1:
            self.logger(level="debug", message="Failed to locate backup with UUID " + str(uuid))
            return None
        else:
            return backup_list[0]

    def remove_backup(self, uuid=None):
        """
        Removes the specified backup from the backup list
        :param uuid: The UUID of the backup to be deleted
        :return: True if delete is successful, False otherwise
        """
        if uuid is None:
            self.logger(level="error", message="No backup UUID specified in remove backup request.")
            return False

        # Find the backup that needs to be removed
        backup = self.find_backup_by_uuid(uuid=uuid)
        if not backup:
            return False
        else:
            backup_to_remove = backup

        # Remove the backup from the list of backups
        self.backup_list.remove(backup_to_remove)

        return True
