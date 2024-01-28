# coding: utf-8
# !/usr/bin/env python

""" manager.py: Easy UCS Deployment Tool """

import datetime
import os
import time

from __init__ import __version__
from backup.manager import GenericBackupManager
from backup.ucs.backup import UcsCentralBackup, UcsImcBackup, UcsSystemBackup


class GenericUcsBackupManager(GenericBackupManager):
    def __init__(self, parent=None):
        GenericBackupManager.__init__(self, parent=parent)

    def fetch_backup(self, backup_type="full-state", preserve_identities=True, use_repository=False, directory=None,
                     filename=None, timeout=600):
        """
        Performs a backup of the UCS device and stores it in the specified filename in the specified directory
        :param backup_type: Type of backup to be performed (valid types are available under GenericUcsBackup object)
        :param preserve_identities: Preserve identities in backup file (for config-logical or config-all only)
        :param use_repository: Use repository to store backup files. If enabled, directory & filename are ignored
        :param directory: The directory in which to store the backup file
        :param filename: The name of the backup file to be saved
        :param timeout: The maximum allowed duration of the backup operation before timing out (in seconds)
        :return: Backup UUID if successful, False otherwise
        """
        backup = self.backup_class_name(parent=self, backup_type=backup_type)
        backup.metadata.easyucs_version = __version__
        backup.metadata.origin = "live"

        if use_repository:
            if self.parent.parent:
                self.parent.parent.parent.repository_manager.create_backups_folder(device=self.parent)
                directory = self.parent.metadata.backups_path
                filename = "backup-" + backup_type + "-" + str(backup.uuid) + backup.metadata.backup_file_extension
                backup.metadata.file_path = os.path.join(directory, filename)
            else:
                self.logger(level="error", message="Impossible to use repository for backup operation")
                return False
        else:
            if not directory or not filename:
                self.logger(level="error", message="Missing directory or file name for backup operation")
                return False

            if not filename.endswith(backup.metadata.backup_file_extension):
                filename += backup.metadata.backup_file_extension
            if not os.path.exists(directory):
                self.logger(message="Creating directory " + directory)
                os.makedirs(directory)

        if backup_type not in backup.valid_backup_types:
            self.logger(level="error", message="Invalid backup type: " + str(backup_type))
            return False

        host_name = "easyucs-" + datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        file_path = "/" + host_name + "_" + backup_type + "_backup" + backup.metadata.backup_file_extension

        if self.parent.task is not None:
            task_name = ""
            if self.parent.metadata.device_type == "ucsc":
                task_name = "FetchBackupUcsCentralDevice"
            elif self.parent.metadata.device_type == "ucsm":
                task_name = "FetchBackupUcsSystemDevice"
            self.parent.task.taskstep_manager.start_taskstep(
                name=task_name,
                description="Fetching " + self.parent.metadata.device_type_long + " Backup")

        self.logger(message="Performing backup of type '" + backup_type + "' for " +
                            self.parent.metadata.device_type_long + " " + self.parent.name)

        # create MgmtBackup
        if backup_type in ["full-state", "config-system"]:
            preserve_identities = False

        mgmt_backup = backup.backup_mo(parent_mo_or_dn="sys", hostname=host_name, admin_state="enabled", proto="http",
                                       type=backup_type, remote_file=file_path)

        if preserve_identities:
            mgmt_backup.preserve_pooled_values = "yes"
        else:
            mgmt_backup.preserve_pooled_values = "no"

        try:
            self.parent.handle.add_mo(mgmt_backup)
            self.parent.handle.commit()
        except Exception as err:
            if self.parent.task is not None:
                status_message = f"Error while fetching {self.parent.metadata.device_type_long} Backup. "
                if "password encryption key" in str(err).lower():
                    # Maximum characters allowed in status_message column is 256
                    if len(status_message + str(err)) < 256:
                        status_message += str(err)
                    else:
                        status_message = str(err)
                task_name = ""
                if self.parent.metadata.device_type == "ucsc":
                    task_name = "FetchBackupUcsCentralDevice"
                elif self.parent.metadata.device_type == "ucsm":
                    task_name = "FetchBackupUcsSystemDevice"
                self.parent.task.taskstep_manager.stop_taskstep(
                    name=task_name, status="failed",
                    status_message=status_message)
            self.logger(
                level="error",
                message="Failed to perform backup of type '" + backup_type + "' for " +
                        self.parent.metadata.device_type_long + " " + self.parent.name + ": " + str(err)
            )
            return False

        # Checking for the backup to complete.
        duration = timeout
        poll_interval = 10
        failed_backup = False

        while True:
            self.logger(level="debug",
                        message="Waiting up to " + str(duration) + " seconds for the backup operation to finish...")
            mgmt_backup = self.parent.handle.query_dn(dn=mgmt_backup.dn)
            admin_state_temp = mgmt_backup.admin_state

            # Break condition:- if state is disabled then break
            if admin_state_temp == "disabled":
                break

            time.sleep(min(duration, poll_interval))
            duration = max(0, (duration - poll_interval))
            if duration == 0:
                self.parent.handle.remove_mo(mgmt_backup)
                self.parent.handle.commit()
                self.logger(level="error", message="Timeout during backup operation")
                failed_backup = True

        # download backup
        file_source = "backupfile/" + file_path
        try:
            self.parent.handle.file_download(url_suffix=file_source, file_dir=directory, file_name=filename)
        except Exception as err:
            self.logger(level="error",
                        message="Error while backing up " + self.parent.metadata.device_type_long + " " +
                                self.parent.name + ": " + str(err))
            failed_backup = True

        # remove backup from UCS device
        try:
            self.parent.handle.remove_mo(mgmt_backup)
            self.parent.handle.commit()
            self.logger(level="debug",
                        message="Successfully removed backup of type '" + backup_type + "' from " +
                                self.parent.metadata.device_type_long + " " + self.parent.name)
        except Exception as err:
            self.logger(level="error",
                        message="Failed to remove backup of type '" + backup_type + "' from " +
                                self.parent.metadata.device_type_long + " " + self.parent.name + ": " + str(err))

        if failed_backup:
            if self.parent.task is not None:
                task_name = ""
                if self.parent.metadata.device_type == "ucsc":
                    task_name = "FetchBackupUcsCentralDevice"
                elif self.parent.metadata.device_type == "ucsm":
                    task_name = "FetchBackupUcsSystemDevice"
                self.parent.task.taskstep_manager.stop_taskstep(
                    name=task_name, status="failed",
                    status_message="Error while fetching " + self.parent.metadata.device_type_long + " Backup")

            self.logger(message="Backup of type '" + backup_type + "' failed")
            return False

        self.logger(message="Backup of type '" + backup_type + "' successfully saved to " +
                            directory + "/" + filename)

        self.backup_list.append(backup)

        if self.parent.task is not None:
            task_name = ""
            if self.parent.metadata.device_type == "ucsc":
                task_name = "FetchBackupUcsCentralDevice"
            elif self.parent.metadata.device_type == "ucsm":
                task_name = "FetchBackupUcsSystemDevice"
            self.parent.task.taskstep_manager.stop_taskstep(
                name=task_name, status="successful",
                status_message="Successfully fetched " + self.parent.metadata.device_type_long + " Backup")

        self.logger(message="Finished taking backup with UUID " + str(backup.uuid) + " from live device")
        return backup.uuid


class UcsSystemBackupManager(GenericUcsBackupManager):
    def __init__(self, parent=None):
        GenericUcsBackupManager.__init__(self, parent=parent)
        self.backup_class_name = UcsSystemBackup


class UcsImcBackupManager(GenericUcsBackupManager):
    def __init__(self, parent=None):
        GenericUcsBackupManager.__init__(self, parent=parent)
        self.backup_class_name = UcsImcBackup

    def fetch_backup(self, backup_type="bmc", preserve_identities=False, use_repository=False, directory=None,
                     filename=None, timeout=600):
        """
        Performs a backup of the UCS IMC and stores it in the specified filename in the specified directory
        :param backup_type: Entity to back up (BMC/VIC or CMC/CIMC1/CIMC2 for S3260)
        :param preserve_identities: Unused for CIMC backup
        :param use_repository: Use repository to store backup files. If enabled, directory & filename are ignored
        :param directory: The directory in which to store the backup file
        :param filename: The name of the backup file to be saved
        :param timeout: The maximum allowed duration of the backup operation before timing out (in seconds)
        :return: Backup UUID if successful, False otherwise
        """
        backup = self.backup_class_name(parent=self, backup_type=backup_type)
        backup.metadata.easyucs_version = __version__
        backup.metadata.origin = "live"

        if use_repository:
            if self.parent.parent:
                self.parent.parent.parent.repository_manager.create_backups_folder(device=self.parent)
                directory = self.parent.metadata.backups_path
                filename = "backup-" + str(backup.uuid) + backup.metadata.backup_file_extension
                backup.metadata.file_path = os.path.join(directory, filename)
            else:
                self.logger(level="error", message="Impossible to use repository for backup operation")
                return False
        else:
            if not directory or not filename:
                self.logger(level="error", message="Missing directory or file name for backup operation")
                return False

            if not filename.endswith(backup.metadata.backup_file_extension):
                filename += backup.metadata.backup_file_extension
            if not os.path.exists(directory):
                self.logger(message="Creating directory " + directory)
                os.makedirs(directory)

        if backup_type not in backup.valid_backup_types:
            self.logger(level="error", message="Invalid backup type: " + str(backup_type))
            return False

        host_name = "easyucs-" + datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        file_path = "/" + host_name + "_" + backup_type + "_backup" + backup.metadata.backup_file_extension

        if self.parent.task is not None:
            self.parent.task.taskstep_manager.start_taskstep(
                name="FetchBackupUcsImcDevice",
                description="Fetching " + self.parent.metadata.device_type_long + " Backup")

        self.logger(message="Performing backup of entity '" + backup_type + "' for " +
                            self.parent.metadata.device_type_long + " " + self.parent.name)

        # create MgmtBackup
        mgmt_backup = backup.backup_mo(parent_mo_or_dn="sys", hostname=host_name, admin_state="enabled", proto="http",
                                       passphrase="easyucs", remote_file=file_path)

        try:
            self.parent.handle.add_mo(mgmt_backup)
        except Exception as err:
            if self.parent.task is not None:
                self.parent.task.taskstep_manager.stop_taskstep(
                    name="FetchBackupUcsImcDevice", status="failed",
                    status_message=f"Error while fetching {self.parent.metadata.device_type_long} Backup.")
            self.logger(
                level="error",
                message="Failed to perform backup of type '" + backup_type + "' for " +
                        self.parent.metadata.device_type_long + " " + self.parent.name + ": " + str(err)
            )
            return False

        # Checking for the backup to complete.
        duration = timeout
        poll_interval = 10
        download_status = False
        failed_backup = False

        while True:
            self.logger(level="debug",
                        message="Waiting up to " + str(duration) + " seconds for the backup operation to finish...")
            mgmt_backup = self.parent.handle.query_dn(dn=mgmt_backup.dn)
            admin_state_temp = mgmt_backup.admin_state

            # Break condition:- if state is disabled then break
            if admin_state_temp == "disabled":
                if mgmt_backup.fsm_stage_descr == "Completed successfully":
                    download_status = True
                    break
                elif mgmt_backup.fsm_stage_descr == "Error":
                    failed_backup = True
                    break

            time.sleep(min(duration, poll_interval))
            duration = max(0, (duration - poll_interval))
            if duration == 0:
                self.parent.handle.remove_mo(mgmt_backup)
                self.logger(level="error", message="Timeout during backup operation")
                failed_backup = True

        # download backup
        if download_status:
            file_source = "backupfile/" + file_path
            try:
                self.parent.handle.file_download(url_suffix=file_source, file_dir=directory, file_name=filename)
            except Exception as err:
                self.logger(level="error",
                            message="Error while backing up " + self.parent.metadata.device_type_long + " " +
                                    self.parent.name + ": " + str(err))
                failed_backup = True
        else:
            self.logger(level="error",
                        message="Error while backing up " + self.parent.metadata.device_type_long + " " +
                                self.parent.name + " - Code: " + mgmt_backup.fsm_rmt_inv_err_code +
                                " - Descr: " + mgmt_backup.fsm_rmt_inv_err_descr)

        if failed_backup:
            if self.parent.task is not None:
                self.parent.task.taskstep_manager.stop_taskstep(
                    name="FetchBackupUcsImcDevice", status="failed",
                    status_message="Error while fetching " + self.parent.metadata.device_type_long + " Backup")

            self.logger(message="Backup of entity '" + backup_type + "' failed")
            return False

        self.logger(message="Backup of entity '" + backup_type + "' successfully saved to " +
                            directory + "/" + filename)

        self.backup_list.append(backup)

        if self.parent.task is not None:
            self.parent.task.taskstep_manager.stop_taskstep(
                name="FetchBackupUcsImcDevice", status="successful",
                status_message="Successfully fetched " + self.parent.metadata.device_type_long + " Backup")

        self.logger(message="Finished taking backup with UUID " + str(backup.uuid) + " from live device")
        return backup.uuid


class UcsCentralBackupManager(GenericUcsBackupManager):
    def __init__(self, parent=None):
        GenericUcsBackupManager.__init__(self, parent=parent)
        self.backup_class_name = UcsCentralBackup
