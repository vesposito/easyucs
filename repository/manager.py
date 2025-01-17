# coding: utf-8
# !/usr/bin/env python

""" manager.py: Easy UCS Deployment Tool """

import contextlib
import copy
import datetime
import inspect
import json
import os
import shutil
import threading
import uuid as python_uuid
from sqlite3 import IntegrityError

import sqlalchemy.exc
from cryptography.fernet import Fernet
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from __init__ import EASYUCS_ROOT, __version__
from backup.backup import GenericBackup
from common import read_json_file, validate_json
from config.config import GenericConfig
from cache.cache import GenericCache
from device.device import GenericDevice
from inventory.inventory import GenericInventory
from report.report import GenericReport
from repository import metadata
from repository.db import models
from repository.metadata import GenericMetadata, BackupMetadata, ConfigMetadata, DeviceMetadata, InventoryMetadata, \
    ReportMetadata, GenericTaskMetadata, TaskMetadata, TaskStepMetadata, RepoFileMetadata, RepoSyncToDeviceMetadata
from repository.repo import Repo


def hasattr_table_record(cls):
    """
    Function which checks whether a class has the attribute TABLE_RECORD
    :param cls: Class where we look for the attribute TABLE_RECORD
    :return: True if cls have attribute TABLE_RECORD, False otherwise
    """
    if hasattr(cls, "TABLE_RECORD"):
        return True
    return False


class RepositoryManager:
    REPOSITORY_BACKUPS_FOLDER_NAME: str = "backups"
    REPOSITORY_CA_CERTS_FILE_NAME: str = "ca_cert.pem"
    REPOSITORY_CA_CERTS_FOLDER_NAME: str = "ca_certs"
    REPOSITORY_DB_BACKUP_NAME = "db_backup.json"
    REPOSITORY_DB_FILE_NAME: str = "easyucs.db"
    REPOSITORY_DB_FOLDER_NAME: str = "db"
    REPOSITORY_DEVICES_CACHE_FOLDER_NAME: str = "cache"
    REPOSITORY_DEVICES_FOLDER_NAME: str = "devices"
    REPOSITORY_DEVICES_OS_FIRMWARE_FILE_NAME: str = "os_firmware.json"
    REPOSITORY_FILES_FOLDER_NAME: str = "files"
    REPOSITORY_FOLDER_NAME: str = "data"
    REPOSITORY_IMAGES_FOLDER_NAME: str = "images"
    REPOSITORY_KEYS_FOLDER_NAME: str = "keys"
    REPOSITORY_KEY_FILE_NAME: str = "easyucs.key"
    REPOSITORY_TMP_FOLDER_NAME: str = "tmp"
    SAMPLES_FOLDER_NAME: str = "samples"
    SETTINGS_FILE_NAME: str = "settings.json"
    PROXY_SETTINGS_FILE_NAME: str = "proxy_settings.json"
    SOFTWARE_REPOSITORY_FOLDER_NAME: str = "repo"
    TABLE_TO_METADATA_MAPPING = {}  # It's a mapping from table name to its "(Metadata, DB record)"
    for table in inspect.getmembers(metadata, hasattr_table_record):
        TABLE_TO_METADATA_MAPPING[table[1].TABLE_RECORD.__tablename__] = (table[1], table[1].TABLE_RECORD)

    def __init__(self, parent=None):
        self.cipher_suite = None
        self.settings = None
        self.db = None
        self.engine = None
        self.thread_safe_session_factory = None
        self.parent = parent

        self._parent_having_logger = self._find_logger()
        self.repo = Repo(parent=self)

        self._init_tmp()
        self._init_key()
        self._init_db()
        self._init_settings()
        self._init_proxy_settings()
        self._init_config_catalog()
        self._init_repo()

    def _delete_device(self, metadata=None, delete_keys=True):
        """
        Deletes an EasyUCS device and its associated objects from the repository (all files + all DB entries)
        :param metadata: DeviceMetadata of the device to be deleted
        :param delete_keys: Also deletes associated private key file in case it exists, if set to True.
        :return: True if delete operation is successful, False otherwise
        """
        if metadata is None:
            self.logger(level="error", message="No metadata provided!")
            return False

        if not isinstance(metadata, DeviceMetadata):
            self.logger(level="error", message="Not a valid metadata!")
            return False

        # We first need to delete the entire folder structure of the device
        device_uuid = str(metadata.uuid)
        full_path = os.path.abspath(
            os.path.join(EASYUCS_ROOT, self.REPOSITORY_FOLDER_NAME, self.REPOSITORY_FILES_FOLDER_NAME,
                         self.REPOSITORY_DEVICES_FOLDER_NAME, device_uuid))
        result = True
        try:
            shutil.rmtree(full_path)
            self.logger(message="Successfully deleted device folder: " + full_path)

        except FileNotFoundError:
            self.logger(level="info", message="Device folder not found: " + full_path)
        except OSError as err:
            self.logger(level="error", message="Unable to delete device folder: " + full_path + ": " + str(err))
            result = False

        # We then delete the private keys stored in the repository for this device
        if delete_keys and metadata.private_key_path is not None:
            private_key_full_path = os.path.abspath(
                os.path.join(EASYUCS_ROOT, self.REPOSITORY_FOLDER_NAME, self.REPOSITORY_KEYS_FOLDER_NAME,
                             self.REPOSITORY_DEVICES_FOLDER_NAME, str(device_uuid) + ".pem"))
            try:
                os.remove(private_key_full_path)
                self.logger(message="Successfully deleted private key file: " + private_key_full_path)

            except OSError:
                self.logger(level="debug", message="Unable to delete private key file: " + private_key_full_path)

        # We now need to delete every single backup/config/inventory/report attached to this device from the Database
        for object_type in ["backup", "config", "inventory", "report"]:
            object_metadata_list = self.get_metadata(object_type=object_type, device_uuid=metadata.device_uuid)
            for object_metadata in object_metadata_list:
                if not self._delete_metadata(metadata=object_metadata):
                    result = False

        # We now delete all the sub-devices of this device
        if metadata.sub_device_uuids:
            for sub_device_uuid in metadata.sub_device_uuids:
                sub_device_metadata_list = self.get_metadata(object_type="device", uuid=sub_device_uuid)
                for sub_device_metadata in sub_device_metadata_list:
                    self.delete_from_repository(metadata=sub_device_metadata)

        return result

    def _delete_file(self, metadata=None):
        """
        Deletes an EasyUCS object (file) from the repository
        :param metadata: GenericMetadata of file to be deleted from the repository (backup/config/inventory/report)
        :return: True if delete operation is successful, False otherwise
        """
        if metadata is None:
            self.logger(level="error", message="No metadata provided!")
            return False

        if not any(isinstance(metadata, x) for x in [BackupMetadata, ConfigMetadata, InventoryMetadata,
                                                     ReportMetadata]):
            self.logger(level="error", message="Not a valid metadata!")
            return False

        if metadata.file_path is None:
            self.logger(level="error", message="No file path in metadata!")
            return False

        full_path = os.path.abspath(os.path.join(EASYUCS_ROOT, metadata.file_path))
        try:
            os.remove(full_path)

        except OSError:
            self.logger(level="error", message="Unable to delete file: " + full_path)
            return False

        self.logger(message="Successfully deleted file: " + full_path)
        return True

    def _delete_metadata(self, metadata=None):
        """
        Deletes GenericMetadata object from DB
        :param metadata: GenericMetadata of object to be deleted from the DB (backup/config/device/inventory/report)
        :return: True if delete operation is successful, False otherwise
        """
        if metadata is None:
            self.logger(level="error", message="No metadata provided!")
            return False

        if isinstance(metadata, BackupMetadata):
            db_table_name = models.BackupRecord
        elif isinstance(metadata, ConfigMetadata):
            db_table_name = models.ConfigRecord
        elif isinstance(metadata, DeviceMetadata):
            db_table_name = models.DeviceRecord
        elif isinstance(metadata, InventoryMetadata):
            db_table_name = models.InventoryRecord
        elif isinstance(metadata, ReportMetadata):
            db_table_name = models.ReportRecord
        elif isinstance(metadata, RepoFileMetadata):
            db_table_name = models.RepoFileRecord
        elif isinstance(metadata, RepoSyncToDeviceMetadata):
            db_table_name = models.RepoSyncToDeviceRecord
        else:
            self.logger(level="error", message="Not a valid metadata!")
            return False

        if db_table_name:
            try:
                with self.ManagedSession() as session:
                    # We delete the entry in the DB using a filter based on the UUID value
                    session.query(db_table_name).filter(getattr(db_table_name, "uuid") == str(metadata.uuid)).delete()

            except Exception as err:
                if metadata.file_type is not None:
                    self.logger(level="error",
                                message=f"Unable to delete {metadata.file_type} metadata with UUID "
                                        f"{str(metadata.uuid)} from DB: {str(err)}")
                return False
        if metadata.file_type is not None:
            self.logger(message=f"Successfully deleted {metadata.file_type} with UUID {str(metadata.uuid)} from DB")
        return True

    class WatchdogEventHandler(FileSystemEventHandler):
        def __init__(self, parent, observed_path):
            self.parent = parent
            self.observed_path = observed_path
            # If observed_path is symlink, then we determine the real path.
            self.real_observed_path = os.path.realpath(observed_path)

        def get_relative_path(self, path, start=EASYUCS_ROOT):
            """
            Function to get the path relative to the start (EASYUCS_ROOT). This also handles situation where
            self.observed_path is a symlink to another path (self.real_observed_path).
            """
            return os.path.relpath(
                os.path.join(self.observed_path,
                             os.path.relpath(path, start=self.real_observed_path)),
                start=start)

        def on_any_event(self, event):
            try:
                if event.is_directory:
                    return
                elif event.event_type == 'created':
                    self.parent.logger(level="debug",
                                       message=f"Watchdog received 'created' event - "
                                               f"{self.get_relative_path(event.src_path)}.")
                    file_metadata = self.parent.repo.create_repofile_metadata(
                        file_path=self.get_relative_path(event.src_path, start=EASYUCS_ROOT))
                    self.parent.save_metadata(metadata=file_metadata)
                elif event.event_type == 'modified':
                    self.parent.logger(level="debug",
                                       message=f"Watchdog received 'modified' event - "
                                               f"{self.get_relative_path(event.src_path)}.")
                    repo_file_list = self.parent.get_metadata(object_type="repofile",
                                                              repo_file_path=self.get_relative_path(event.src_path,
                                                                                                    start=EASYUCS_ROOT))
                    if len(repo_file_list) < 1:
                        # If there is no record for the file in DB, then we create one.
                        repo_file_list.append(self.parent.repo.create_repofile_metadata(
                            file_path=self.get_relative_path(event.src_path, start=EASYUCS_ROOT)))
                        self.parent.save_metadata(metadata=repo_file_list[0])

                    # We reset the values of checksums to None in case of a modified event
                    if repo_file_list[0].md5 is not None or repo_file_list[0].sha1 is not None or \
                            repo_file_list[0].sha256 is not None:
                        repo_file_list[0].md5 = None
                        repo_file_list[0].sha1 = None
                        repo_file_list[0].sha256 = None
                        self.parent.save_metadata(metadata=repo_file_list[0])
                elif event.event_type == 'deleted':
                    self.parent.logger(level="debug",
                                       message=f"Watchdog received 'deleted' event - "
                                               f"{self.get_relative_path(event.src_path)}.")
                    repo_file_list = self.parent.get_metadata(object_type="repofile",
                                                              repo_file_path=self.get_relative_path(event.src_path,
                                                                                                    start=EASYUCS_ROOT))
                    if len(repo_file_list) < 1:
                        self.parent.logger(level="debug", message=f"Could not find the entry of the file: "
                                                                  f"{self.get_relative_path(str(event.src_path))}")
                        return

                    # Delete all the sync to device records related to this file
                    synctodevice_metadata = self.parent.get_metadata(object_type="reposynctodevice",
                                                                     filter=("file_uuid", "==",
                                                                             str(repo_file_list[0].uuid)))
                    for sync_metadata in synctodevice_metadata:
                        self.parent._delete_metadata(metadata=sync_metadata)

                    self.parent._delete_metadata(metadata=repo_file_list[0])
                elif event.event_type == 'moved':
                    self.parent.logger(level="debug",
                                       message=f"Watchdog received 'moved' event - "
                                               f"{self.get_relative_path(event.src_path)}.")
                    repo_file_list = self.parent.get_metadata(object_type="repofile",
                                                              repo_file_path=self.get_relative_path(event.src_path,
                                                                                                    start=EASYUCS_ROOT))
                    if len(repo_file_list) < 1:
                        # If there is no record for the file in DB, then we create one.
                        repo_file_list.append(self.parent.repo.create_repofile_metadata(
                            file_path=self.get_relative_path(event.src_path, start=EASYUCS_ROOT)))

                    # Because the file is moved/renamed delete all the sync to device records related to this file
                    synctodevice_metadata = self.parent.get_metadata(object_type="reposynctodevice",
                                                                     filter=("file_uuid", "==",
                                                                             str(repo_file_list[0].uuid)))
                    for sync_metadata in synctodevice_metadata:
                        self.parent._delete_metadata(metadata=sync_metadata)

                    repo_file_list[0].file_path = self.get_relative_path(event.dest_path, start=EASYUCS_ROOT)
                    self.parent.save_metadata(metadata=repo_file_list[0])
            except Exception as err:
                if isinstance(err, sqlalchemy.exc.IntegrityError) and isinstance(err.orig, IntegrityError):
                    self.parent.logger(level="warning",
                                       message=f"While handling Watchdog event '{str(event.event_type)}' "
                                               f"encountered the 'UniqueViolation' error for file '{event.src_path}'")
                else:
                    self.parent.logger(level="error",
                                       message=f"While handling Watchdog event '{str(event.event_type)}' "
                                               f"encountered the error: {str(err)}")

    def _repo_watchdog(self, path):
        """
        Function which starts the watchdog monitoring
        :param path: Absolute path which needs to be monitored
        """
        event_handler = self.WatchdogEventHandler(parent=self, observed_path=path)
        observer = Observer()
        self.logger(message=f"Monitoring file hosting path {path}")
        observer.schedule(event_handler, os.path.realpath(path), recursive=True)
        observer.start()
        try:
            while observer.is_alive():
                observer.join(1)
        finally:
            observer.stop()
            observer.join()

    def _find_logger(self):
        # Method to find the object having a logger - it can be high up in the hierarchy of objects
        current_object = self
        while hasattr(current_object, 'parent') and not hasattr(current_object, '_logger_handle'):
            current_object = current_object.parent

        if hasattr(current_object, '_logger_handle'):
            return current_object
        else:
            print("WARNING: No logger found in Repository Manager")
            return None

    def _init_repo(self):
        """
        Initializes repo directory, also starts a watchdog on the repo path
        :return: True if repo directory exists (or created) and watchdog started
        """

        repo_path = os.path.abspath(os.path.join(EASYUCS_ROOT, self.REPOSITORY_FOLDER_NAME,
                                                 self.SOFTWARE_REPOSITORY_FOLDER_NAME))
        if not os.path.exists(repo_path):
            self.logger(message="Creating Software Repository directory " + repo_path)
            os.makedirs(repo_path)

        self.watchdog_thread = threading.Thread(target=self._repo_watchdog, name="repo_watchdog",
                                                args=(repo_path,))

        self.watchdog_thread.start()

        # Delete the 'repofile' records which does not exist in repo folder.
        repofiles_metadata = self.get_metadata(object_type="repofile")
        for repofile_metadata in repofiles_metadata:
            if not os.path.exists(os.path.join(EASYUCS_ROOT, repofile_metadata.file_path)):
                self._delete_metadata(metadata=repofile_metadata)

        return True

    def _init_settings(self, file_update=False):
        """
        Initializes Settings
        :param file_update: Update the settings file with the initialized settings
        :return: True if settings init is successful, False otherwise
        """
        file_contents = read_json_file(file_path=self.SETTINGS_FILE_NAME)
        # Validating settings.json
        if not validate_json(json_data=file_contents, schema_path="schema/settings/settings.json", logger=self):
            self.logger(level="error", message="settings.json file is not valid")
            raise ValueError("Failed to validate settings.json file")

        self.settings = copy.deepcopy(file_contents)

        if file_update:
            with open(os.path.abspath(os.path.join(EASYUCS_ROOT, self.SETTINGS_FILE_NAME)), "w") as settings_file:
                for content in ['default_password', 'default_password_mutual_chap_authentication']:
                    if content in file_contents["convert_settings"]:
                        del file_contents["convert_settings"][content]
                json.dump(file_contents, settings_file, indent=3)
        return True

    def _init_proxy_settings(self, file_update=False):
        """
        Initializes Proxy Settings
        :param file_update: Update the proxy settings file with the initialized proxy settings
        :return: True if proxy settings init is successful, False otherwise
        """
        file_contents = read_json_file(file_path=self.PROXY_SETTINGS_FILE_NAME)
        # Validating settings.json
        if not validate_json(json_data=file_contents, schema_path="schema/proxy_settings/proxy_settings.json",
                             logger=self):
            self.logger(level="error", message="proxy_settings.json file is not valid")
            raise ValueError("Failed to validate proxy_settings.json file")

        # There are 3 scenarios:
        # 1. If password fields are not present and encrypted password fields are present. In this case we just decrypt
        # the encrypted password fields.
        # 2. If password fields are not present and encrypted password fields are also not present. In this case we
        # set encrypted password as empty.
        # 3. If password fields are present, then we add the encrypted password fields to the settings.
        for content in ['proxy_password']:
            if not file_contents.get(content) and file_contents.get(
                    'encrypted_' + content):
                # If password fields are not present and encrypted password fields are present
                try:
                    file_contents[content] = self.cipher_suite.decrypt(bytes(
                        file_contents['encrypted_' + content], 'utf-8')).decode('utf-8')
                except Exception as err:
                    self.logger(level="error", message=f"Could not decrypt the password: {str(err)}")
                    file_contents['encrypted_' + content] = ""
                    file_update = True

            elif not file_contents.get(content) and not file_contents.\
                    get('encrypted_'+content):
                # If password fields are not present and encrypted password fields are also not present
                self.logger(level="info",
                            message="No password provided. Setting the password fields with empty string")
                file_contents['encrypted_' + content] = ""
                file_update = True

            else:
                # If password fields are present
                file_contents['encrypted_' + content] = self.cipher_suite.encrypt(bytes(
                    file_contents[content], encoding='utf8')).decode('utf-8')
                file_update = True

        if file_update:
            with open(os.path.abspath(os.path.join(EASYUCS_ROOT, self.PROXY_SETTINGS_FILE_NAME)), "w") as proxy_settings_file:
                for content in ['proxy_password']:
                    if content in file_contents:
                        del file_contents[content]
                json.dump(file_contents, proxy_settings_file, indent=3)
        return True

    def _init_config_catalog(self):
        """
        Initializes the config catalog
        :return: True if config catalog init is successful, False otherwise
        """
        config_samples_full_path = os.path.abspath(os.path.join(EASYUCS_ROOT, self.SAMPLES_FOLDER_NAME, "configs"))
        if not os.path.exists(config_samples_full_path):
            self.logger(level="warning", message="Unable to find the config samples directory")
            return False

        # Determining the types of devices that have samples
        self.logger(message="Initializing config catalog...")
        device_list = self.get_metadata(object_type="device")
        for device_folder_name in ["cimc", "imm_domain", "intersight", "ucsc", "ucsm"]:
            # We first need to check if we already have a system device of usage "catalog" for this device type
            already_present = False
            for device_metadata in device_list:
                if getattr(device_metadata, "device_type", None) == device_folder_name and \
                        getattr(device_metadata, "is_system", None) and \
                        getattr(device_metadata, "system_usage", None) == "catalog":
                    already_present = True
                    self.logger(level="debug",
                                message="Using existing system device with UUID " + str(device_metadata.uuid) +
                                        " for config catalog of type '" + str(device_folder_name) + "'")

                    # We load the corresponding device if it is not already loaded
                    device = self.parent.device_manager.find_device_by_uuid(uuid=device_metadata.uuid)
                    if not device:
                        self.parent.device_manager.add_device(metadata=device_metadata)
                        device = self.parent.device_manager.find_device_by_uuid(uuid=device_metadata.uuid)
                    break

            if not already_present:
                # We create a new (hidden) system device of usage "catalog" for this device type
                self.parent.device_manager.add_device(device_type=device_folder_name,
                                                      target=device_folder_name + "_catalog.easyucs",
                                                      is_hidden=True, is_system=True, system_usage="catalog")
                device = self.parent.device_manager.get_latest_device()
                self.logger(message="Created system device with UUID " + str(device.uuid) +
                                    " for config catalog of type '" + str(device_folder_name) + "'")
                self.save_to_repository(object=device)

            # We now parse the entire folder to find config files to import in the config catalog
            config_files_list = []
            for root, dirs, files in os.walk(os.path.join(config_samples_full_path, device_folder_name)):
                for file in files:
                    if file.endswith(".json"):
                        config_files_list.append(os.path.join(root, file))

            if config_files_list:
                self.logger(
                    level="debug",
                    message=str(len(config_files_list)) + " config file(s) to parse for config catalog of type '" +
                            str(device_folder_name) + "'"
                )
                config_list = self.get_metadata(object_type="config", device_uuid=device.uuid)
                for config_file in config_files_list:
                    self._parse_catalog_config_file(config_file_path=config_file, catalog_device=device,
                                                    config_list=config_list)

        return True

    def _init_db(self):
        """
        Initializes Database
        :return: True if DB init is successful, False otherwise
        """
        db_folder_full_path = os.path.abspath(os.path.join(
            EASYUCS_ROOT, self.REPOSITORY_FOLDER_NAME, self.REPOSITORY_DB_FOLDER_NAME))
        if not os.path.exists(db_folder_full_path):
            self.logger(message="Creating DB directory " + db_folder_full_path)
            os.makedirs(db_folder_full_path)

        SQLALCHEMY_DATABASE_URL = "sqlite:///" + \
                                  os.path.abspath(os.path.join(db_folder_full_path, self.REPOSITORY_DB_FILE_NAME))

        self._init_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}, echo=False, future=True)
        self._init_session_factory()

        return True

    def _init_engine(self, uri, **kwargs):
        """Initialize the engine.
        Args:
            uri (str): The string database URI. Examples:
                - sqlite:///database.db
                - postgresql+psycopg2://username:password@0.0.0.0:5432/database
        """
        if self.engine is None:
            self.engine = create_engine(uri, **kwargs, pool_size=50, max_overflow=100, pool_recycle=3600)
            # Create all tables in DB
            models.Base.metadata.create_all(bind=self.engine)
        return self.engine

    def _init_session_factory(self):
        """Initialize the thread_safe_session_factory."""
        if self.engine is None:
            raise ValueError("Initialize engine by calling init_engine before calling init_session_factory!")
        if self.thread_safe_session_factory is None:
            self.thread_safe_session_factory = scoped_session(sessionmaker(bind=self.engine, expire_on_commit=False))
        return self.thread_safe_session_factory

    @contextlib.contextmanager
    def ManagedSession(self):
        if self.thread_safe_session_factory is None:
            raise ValueError("Call init_session_factory before using ManagedSession!")

        session = self.thread_safe_session_factory()

        try:
            yield session
            session.commit()
            session.flush()
        except Exception:
            session.rollback()
            # When an exception occurs, handle session cleaning,
            # but raise the Exception afterwards so that user can handle it.
            raise
        finally:
            self.thread_safe_session_factory.remove()

    def _init_key(self):
        """
        Initializes key for encrypting device passwords
        :return: True if key init is successful, False otherwise
        """
        key = None

        key_folder_full_path = os.path.abspath(os.path.join(
            EASYUCS_ROOT, self.REPOSITORY_FOLDER_NAME, self.REPOSITORY_KEYS_FOLDER_NAME))
        if not os.path.exists(key_folder_full_path):
            self.logger(message="Creating Keys directory " + key_folder_full_path)
            os.makedirs(key_folder_full_path)

        key_file_full_path = os.path.abspath(os.path.join(
            EASYUCS_ROOT, self.REPOSITORY_FOLDER_NAME, self.REPOSITORY_KEYS_FOLDER_NAME, self.REPOSITORY_KEY_FILE_NAME))
        if not os.path.exists(key_file_full_path):
            key = Fernet.generate_key()
            self.logger(level="debug", message="Generating new key to file " + key_file_full_path)
            with open(key_file_full_path, 'wb') as key_file:
                key_file.write(key)
        else:
            self.logger(level="debug", message="Retrieving key from file " + key_file_full_path)
            with open(key_file_full_path, 'rb') as key_file:
                for line in key_file:
                    key = line

        if key is not None:
            self.cipher_suite = Fernet(key)
            return True
        else:
            return False

    def _init_tmp(self):
        """
        Initializes tmp directory for storing temporary files
        :return: True if tmp init is successful, False otherwise
        """
        tmp_folder_full_path = os.path.abspath(os.path.join(
            EASYUCS_ROOT, self.REPOSITORY_FOLDER_NAME, self.REPOSITORY_TMP_FOLDER_NAME))
        # In IMM Transition Tool, 'tmp' directory is a symlink to a folder in disk2. For that reason we don't
        # delete the 'tmp' folder directly. Rather we delete the content of the 'tmp' folder.
        if os.path.exists(tmp_folder_full_path):
            # Remove all its content
            for file_name in os.listdir(tmp_folder_full_path):
                file_path = os.path.join(tmp_folder_full_path, file_name)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                else:
                    shutil.rmtree(file_path)
        else:
            self.logger(message="Creating Temp directory " + tmp_folder_full_path)
            os.makedirs(tmp_folder_full_path)

        return True

    def _parse_catalog_config_file(self, config_file_path=None, catalog_device=None, config_list=None):
        """
        Parses a config file to add it to the config catalog of a given device type
        :param config_file_path: the path to the config file to parse
        :param catalog_device: the device for which to add the config file in the catalog
        :param config_list: the list of configs of the device (to avoid fetching it every time we call this method)
        :return: True if parse operation is successful, False otherwise
        """
        if not config_file_path:
            self.logger(level="error", message="Missing config file path")
            return False

        if not catalog_device:
            self.logger(level="error", message="Missing device")
            return False

        if config_list is None:
            self.logger(level="error", message="Missing config list")
            return False

        json_dict = read_json_file(file_path=config_file_path, logger=self)

        if not json_dict:
            self.logger(level="error", message="Not a JSON file")
            return False

        if not catalog_device.config_manager._validate_config_from_json(config_json=json_dict):
            return False

        self.logger(level="debug", message="Parsing catalog config file: " + config_file_path)

        # We first check if we have already loaded this config file during a previous run
        # To determine this, we compare the category, subcategory and name fields. If those fields are not populated,
        # we simply ignore the file
        category = json_dict["easyucs"]["metadata"][0].get("category", None)
        subcategory = json_dict["easyucs"]["metadata"][0].get("subcategory", None)
        name = json_dict["easyucs"]["metadata"][0].get("name", None)
        revision = json_dict["easyucs"]["metadata"][0].get("revision", None)

        if not category or not subcategory or not name:
            return False

        # We check if a config with the same category, subcategory and name already exists
        for config in config_list:
            if config.category == category and config.subcategory == subcategory and config.name == name:
                # If revision is lower or equal, we don't need to import the config file
                # If existing catalog config file has a revision but not the new one, we skip it
                # If new config file has a revision but not the existing catalog file, we replace it
                if revision and config.revision:
                    if revision <= config.revision:
                        return True
                elif config.revision:
                    return True
                elif not revision and not config.revision:
                    return True

                # Revision is lower, so we need to remove the old config before importing the new one
                self.logger(
                    level="debug",
                    message="Catalog config file " + config_file_path + " has a newer revision: " + str(revision)
                )
                self.delete_from_repository(metadata=config)
                break

        # We need to import the new config
        imported_config = catalog_device.config_manager.import_config(import_format="json", directory="samples",
                                                                      config=json_dict)
        if imported_config:
            self.save_to_repository(object=imported_config)
            # We now remove the config from the config list to save memory
            catalog_device.config_manager.remove_config(uuid=imported_config.uuid)
            return True

        return False

    def _save_file(self, object=None):
        """
        Saves an EasyUCS object to the file repository
        :param object: object to be saved to the repository (config/inventory/report)
        :return: complete file path if save operation is successful, False otherwise
        """
        if object is None:
            self.logger(level="error", message="No object given for save file operation!")
            return False

        if not any(isinstance(object, x) for x in [GenericCache, GenericConfig, GenericInventory, GenericReport]):
            self.logger(level="error", message="Object type not supported!")
            return False

        device_uuid = str(object.device.uuid)

        directory = ""
        if isinstance(object, GenericConfig):
            directory = "configs"
        elif isinstance(object, GenericInventory):
            directory = "inventories"
        elif isinstance(object, GenericReport):
            directory = "reports"
        elif isinstance(object, GenericCache):
            directory = "cache"

        directory_full_path = os.path.abspath(
            os.path.join(EASYUCS_ROOT, self.REPOSITORY_FOLDER_NAME, self.REPOSITORY_FILES_FOLDER_NAME,
                         self.REPOSITORY_DEVICES_FOLDER_NAME, device_uuid, directory))
        directory_relative_path = os.path.join(self.REPOSITORY_FOLDER_NAME, self.REPOSITORY_FILES_FOLDER_NAME,
                                               self.REPOSITORY_DEVICES_FOLDER_NAME, device_uuid, directory)

        # Creating folder in case it does not exist yet
        if not os.path.exists(directory_full_path):
            self.logger(level="debug", message="Creating folder: " + directory_full_path)
            os.makedirs(directory_full_path)

        filename = ""
        if isinstance(object, GenericCache):
            filename = "cache.json"
            if not object.device.cache_manager.export_cache(
                    export_format="json", directory=directory_full_path, filename=filename):
                return False
        elif isinstance(object, GenericConfig):
            filename = "config-" + str(object.uuid) + ".json"
            if not object.device.config_manager.export_config(uuid=object.uuid, export_format="json",
                                                              directory=directory_full_path, filename=filename):
                return False
        elif isinstance(object, GenericInventory):
            filename = "inventory-" + str(object.uuid) + ".json"
            if not object.device.inventory_manager.export_inventory(uuid=object.uuid, export_format="json",
                                                                    directory=directory_full_path, filename=filename):
                return False
        elif isinstance(object, GenericReport):
            if object.metadata.output_format in ["docx", "json", "pdf"]:
                filename = "report_" + str(object.metadata.report_type) + "-" + str(object.uuid) + "." + \
                           object.metadata.output_format
                if not object.device.report_manager.export_report(uuid=object.uuid, directory=directory_full_path,
                                                                  export_format=object.metadata.output_format,
                                                                  filename=filename):
                    return False

        file_path = os.path.join(directory_relative_path, filename)
        return file_path

    def clear_db(self):
        """
        Function to delete all the DB records from the DB
        :return: True is successful, False otherwise
        """
        # Deleting the existing data from the DB
        for table in self.TABLE_TO_METADATA_MAPPING:
            try:
                with self.ManagedSession() as session:
                    # We delete the entry in the DB using a filter based on the UUID value
                    session.query(self.TABLE_TO_METADATA_MAPPING[table][1]).delete()
            except Exception as err:
                self.logger(level="error", message=f"Unable to delete {table} table records from DB: {str(err)}")
                return False
        return True

    def clear_files(self):
        """
        Function to delete all the files
        :return: True is successful, False otherwise
        """
        # We first need to delete the entire folder structure of the files and ./keys/devices
        for folder in [self.REPOSITORY_FILES_FOLDER_NAME, os.path.join(self.REPOSITORY_KEYS_FOLDER_NAME,
                                                                       self.REPOSITORY_DEVICES_FOLDER_NAME)]:
            full_path = os.path.join(EASYUCS_ROOT, self.REPOSITORY_FOLDER_NAME, folder)
            try:
                shutil.rmtree(full_path)
                self.logger(message="Successfully deleted folder: " + full_path)
            except FileNotFoundError:
                self.logger(level="info", message=f"Folder {folder} not found: {full_path}")
            except OSError as err:
                self.logger(level="error", message=f"Unable to delete {folder} folder {str(err)}")
        return True

    def _update_backup_record(self, record=None, table=None, backup_version=None):
        """
        Function which updates the DB record to make it compatible with current version. This function will handle the
        field name changes across multiple releases
        :param record: JSON Record which needs to be upgraded
        :param table: The table to which the record belongs to
        :param backup_version: The version of the backup
        :return: True if successful, False otherwise
        """
        if not record:
            self.logger(level="error", message="No record given to update")
            return False
        if not table:
            self.logger(level="error", message="Table not specified for the update")
            return False
        if not backup_version:
            self.logger(level="error", message="No Backup Version mentioned for the update")
            return False

        # Dictionary to store the fields to be added into the 'record'
        fields_to_be_added = {}

        for field in record:
            if record[field]:
                if "uuid" in field:
                    if "uuids" in field and isinstance(record[field], list):
                        record[field] = [python_uuid.UUID(item) for item in record[field]]
                    else:
                        record[field] = python_uuid.UUID(record[field])
                elif "timestamp" in field:
                    record[field] = datetime.datetime.fromisoformat(record[field])
                elif "cached_orgs" in field:
                    for org_name in record[field]:
                        if isinstance(record[field][org_name], str):
                            record[field][org_name] = {
                                "description": record[field][org_name],
                                "is_shared": False,
                                "resource_groups": [],
                                "shared_with_orgs": []
                            }
                elif field == "origin" and table in ["configs", "inventories"] and "is_custom" not in record:
                    # When restoring a backup (from an older version), if 'is_custom' field is not present then we set
                    # it to 'True' if it's an uploaded config (i.e. origin == file). Otherwise is_custom=False, which is
                    # the default value set in the metadata object creation.
                    if record[field] == "file":
                        fields_to_be_added["is_custom"] = True
        if fields_to_be_added:
            record.update(fields_to_be_added)

        # Remove the fields which were removed in latest version.
        fields_to_remove = ["cached_orgs", "cache_path"]
        for field in fields_to_remove:
            if field in record:
                del record[field]

        return True

    def create_backups_folder(self, device=None):
        """
        Create the backups folder in the repository if it does not exist already
        :param device: Device for which to create the backups folder
        """
        if device is None:
            self.logger(level="error", message="No device given for create backups folder operation!")
            return False
        else:
            if not isinstance(device, GenericDevice):
                self.logger(level="error", message="Not a valid device provided!")
                return False
            device_uuid = str(device.uuid)

        directory_full_path = os.path.abspath(
            os.path.join(EASYUCS_ROOT, self.REPOSITORY_FOLDER_NAME, self.REPOSITORY_FILES_FOLDER_NAME,
                         self.REPOSITORY_DEVICES_FOLDER_NAME, device_uuid, self.REPOSITORY_BACKUPS_FOLDER_NAME))
        directory_relative_path = os.path.join(self.REPOSITORY_FOLDER_NAME, self.REPOSITORY_FILES_FOLDER_NAME,
                                               self.REPOSITORY_DEVICES_FOLDER_NAME, device_uuid,
                                               self.REPOSITORY_BACKUPS_FOLDER_NAME)

        # Creating folder in case it does not exist yet
        if not os.path.exists(directory_full_path):
            self.logger(level="debug", message="Creating folder: " + directory_full_path)
            os.makedirs(directory_full_path)

        # Saving backups folder path to device metadata
        device.metadata.backups_path = directory_relative_path
        if not self.save_metadata(metadata=device.metadata):
            self.logger(level="error", message="Unable to save backups folder path to device metadata")
            return False

        return True

    def create_images_folder(self, device=None):
        """
        Create the images folder in the repository if it does not exist already
        :param device: Device for which to create the images folder
        """
        if device is None:
            self.logger(level="error", message="No device given for create images folder operation!")
            return False
        else:
            if not isinstance(device, GenericDevice):
                self.logger(level="error", message="Not a valid device provided!")
                return False
            device_uuid = str(device.uuid)

        directory_full_path = os.path.abspath(
            os.path.join(EASYUCS_ROOT, self.REPOSITORY_FOLDER_NAME, self.REPOSITORY_FILES_FOLDER_NAME,
                         self.REPOSITORY_DEVICES_FOLDER_NAME, device_uuid, self.REPOSITORY_IMAGES_FOLDER_NAME))
        directory_relative_path = os.path.join(self.REPOSITORY_FOLDER_NAME, self.REPOSITORY_FILES_FOLDER_NAME,
                                               self.REPOSITORY_DEVICES_FOLDER_NAME, device_uuid,
                                               self.REPOSITORY_IMAGES_FOLDER_NAME)

        # Creating folder in case it does not exist yet
        if not os.path.exists(directory_full_path):
            self.logger(level="debug", message="Creating folder: " + directory_full_path)
            os.makedirs(directory_full_path)

        # Saving images folder path to device metadata
        device.metadata.images_path = directory_relative_path
        if not self.save_metadata(metadata=device.metadata):
            self.logger(level="error", message="Unable to save images folder path to device metadata")
            return False

        return True

    def create_db_backup(self, decrypt_passwords=False):
        """
        Function to create a json backup of the DB
        :param decrypt_passwords: Whether to decrypt the passwords or not
        :return: File path to the DB backup file
        """
        backup_json = {
            "metadata": {
                "easyucs_version": __version__,
                "timestamp": str(datetime.datetime.now())
            },
            "db": {}
        }
        for table in self.TABLE_TO_METADATA_MAPPING.keys():
            metadata_list = self.get_metadata(object_type=self.TABLE_TO_METADATA_MAPPING[table][0].OBJECT_TYPE)
            if metadata_list:
                backup_json["db"][table] = []
                for metadata in metadata_list:
                    record = vars(metadata.db_record).copy()
                    for key, val in vars(metadata.db_record).items():
                        if key not in metadata.db_record.__table__.columns.keys():
                            del record[key]
                        elif isinstance(val, datetime.datetime):
                            record[key] = str(record[key])
                        elif "password" in key and record[key]:
                            if decrypt_passwords:
                                try:
                                    record[key] = self.cipher_suite.decrypt(record[key]).decode('utf-8')
                                except Exception as err:
                                    print(err)
                                    self.logger(level="error", message="Unable to decrypt password for " + table +
                                                                       " with UUID " + str(record["uuid"]))
                                    record[key] = ""
                            else:
                                record[key] = ""
                    backup_json["db"][table].append(record)

        file_path = os.path.join(EASYUCS_ROOT, self.REPOSITORY_FOLDER_NAME, self.REPOSITORY_DB_FOLDER_NAME,
                                 self.REPOSITORY_DB_BACKUP_NAME)
        with open(file_path, "w") as f:
            json.dump(backup_json, f, indent=3)
        return file_path

    def restore_db_backup(self, db_backup_file="", db_backup_data=None, restore_repo=False):
        """
        Function to restore DB from a json backup
        :param db_backup_file: JSON file path which contains the DB backup
        :param db_backup_data: Backed up DB data in JSON format
        :param restore_repo: Whether to restore the repofiles and reposynctodevice tables (default: false)
        :return: True if successful, False otherwise
        """
        if not db_backup_data and not db_backup_file:
            self.logger(level="error", message="Missing db_backup_file or db_backup_data argument")
            return False

        if db_backup_file:
            try:
                with open(db_backup_file) as f:
                    db_backup_data = json.load(f)
            except FileNotFoundError:
                self.logger(level="error", message=f"Failed to find the DB Backup File {db_backup_file}")
                return False
            except Exception as err:
                self.logger(level="error", message=f"Unexpected error while reading the DB Backup File "
                                                   f"{db_backup_file}: {str(err)}")
                return False

        backup_easyucs_version = db_backup_data["metadata"]["easyucs_version"]

        # Adding the records from the backed up DB
        for table, records in db_backup_data["db"].items():
            if not restore_repo and table in ["repofiles", "reposynctodevice"]:
                # If "restore_repo" is false then we don't restore the "repofiles" and "reposynctodevice" tables.
                continue
            for record in records:
                self._update_backup_record(record=record, table=table, backup_version=backup_easyucs_version)
                metadata = self.TABLE_TO_METADATA_MAPPING[table][0](**record)
                self.save_metadata(metadata)

        # Initializing the config catalog at the end to avoid duplicate catalog records
        self._init_config_catalog()

        return True

    def restore_key_and_settings_backup(self):
        """
        Function to restore the key and settings from the replaced file
        :return: True if successful, False otherwise
        """
        # Reloading the key
        if not self._init_key():
            return False

        # Restoring the settings from the replaced settings file.
        # If the backed-up setting have some missing attributes then add them here before calling _init_settings().
        file_contents = read_json_file(file_path=self.SETTINGS_FILE_NAME)
        file_changed = False
        # A mapping of field to their default values
        fields_to_value_mapping = {
            "delete_existing_resource_group_memberships_for_intersight_shared_orgs": False
        }
        for field in fields_to_value_mapping:
            if field not in file_contents:
                file_contents[field] = fields_to_value_mapping[field]
                file_changed = True

        if file_changed:
            full_path = os.path.abspath(os.path.join(EASYUCS_ROOT, self.SETTINGS_FILE_NAME))
            with open(full_path, 'w') as file:
                json.dump(file_contents, file, indent=3)

        if not self._init_settings():
            return False

        return True

    def delete_from_repository(self, metadata=None, delete_keys=True):
        """
        Deletes an EasyUCS object from the repository (file + metadata)
        Also removes the object from the config/device/inventory/report list if it is loaded
        :param metadata: GenericMetadata of the object to delete from repository
        :param delete_keys: Also deletes associated private key file in case it exists, if set to True
        :return: True if successful, False otherwise
        """
        if metadata is None:
            self.logger(level="error", message="No metadata provided!")
            return False

        # We need to check if the object is currently loaded in memory
        if isinstance(metadata, BackupMetadata):
            if metadata.parent is not None:
                self.logger(level="debug", message="Removing backup " + str(metadata.uuid) +
                                                   " from the list of backups of device " + str(metadata.device_uuid))
                metadata.parent.parent.remove_backup(uuid=metadata.uuid)
        elif isinstance(metadata, ConfigMetadata):
            if metadata.parent is not None:
                self.logger(level="debug", message="Removing config " + str(metadata.uuid) +
                                                   " from the list of configs of device " + str(metadata.device_uuid))
                metadata.parent.parent.remove_config(uuid=metadata.uuid)
        elif isinstance(metadata, DeviceMetadata):
            if metadata.parent is not None:
                self.logger(level="debug",
                            message="Removing device " + str(metadata.uuid) + " from the list of devices")
                metadata.parent.parent.remove_device(uuid=metadata.uuid)
        elif isinstance(metadata, InventoryMetadata):
            if metadata.parent is not None:
                self.logger(level="debug", message="Removing inventory " + str(metadata.uuid) +
                                                   " from the list of inventories of device " +
                                                   str(metadata.device_uuid))
                metadata.parent.parent.remove_inventory(uuid=metadata.uuid)
        elif isinstance(metadata, ReportMetadata):
            if metadata.parent is not None:
                self.logger(level="debug", message="Removing report " + str(metadata.uuid) +
                                                   " from the list of reports of device " + str(metadata.device_uuid))
                metadata.parent.parent.remove_report(uuid=metadata.uuid)
        else:
            self.logger(level="error", message="Not a valid metadata!")
            return False

        result = True
        if not isinstance(metadata, DeviceMetadata):
            if not self._delete_file(metadata=metadata):
                result = False
        else:
            if not self._delete_device(metadata=metadata, delete_keys=delete_keys):
                result = False

        if not self._delete_metadata(metadata=metadata):
            result = False

        return result

    def delete_bulk_from_repository(self, metadata_list=None, delete_keys=True):
        """
        Deletes a list of EasyUCS objects from the repository (file + metadata)
        Also removes the object from the config/device/inventory/report list if it is loaded
        :param metadata_list: List of GenericMetadata of the objects to delete from repository
        :param delete_keys: Also deletes associated private key file in case it exists, if set to True
        :return: True if successful, False otherwise
        """
        if metadata_list is None:
            self.logger(level="error", message="No metadata list provided!")
            return False

        result = True
        for metadata in metadata_list:
            try:
                result = self.delete_from_repository(metadata=metadata, delete_keys=delete_keys)
            except:
                self.logger(level="error", message="Impossible to delete " + metadata + " from " + metadata_list + "!")
                return False
        return result

    def get_metadata(self, object_type=None, uuid=None, device_uuid=None, task_uuid=None, filter=None,
                     repo_file_path=None, order_by=("timestamp", "desc"), limit=None, page=0):
        """
        Gets all GenericMetadata objects from reading Database
        :param object_type: Type of object to get metadata of (config/device/inventory/report)
        :param uuid: Only get metadata that matches the specified UUID
        :param device_uuid: Filter results to only include entries for a given device UUID
        :param task_uuid: Filter results to only include entries for a given task UUID
        :param filter: Optional tuple of attributes to filter in the get operation
        :param repo_file_path: Path to the file in repo
        :param order_by: Order of returned objects (Tuple with object attribute and order [desc, asc])
        :param limit: Number of returned objects
        :param page: Page number of returned objects
        :return: List of GenericMetadata objects if successful, Empty list otherwise
        """
        if object_type is None:
            self.logger(level="error", message="No object type given for get metadata operation!")
            return []

        if uuid and device_uuid:
            self.logger(level="error", message="uuid and device_uuid attributes should not be set at the same time!")
            return []

        if uuid and task_uuid:
            self.logger(level="error", message="uuid and task_uuid attributes should not be set at the same time!")
            return []

        if device_uuid and task_uuid:
            self.logger(level="error",
                        message="device_uuid and task_uuid attributes should not be set at the same time!")
            return []

        if not isinstance(order_by, tuple):
            self.logger(level="error", message="order_by attribute not set properly!")
            return []

        if len(order_by) != 2:
            self.logger(level="error", message="order_by attribute not set properly!")
            return []

        if order_by[1] not in ["asc", "desc"]:
            self.logger(level="error", message="order_by attribute should be in 'asc' or 'desc' order")
            return []

        if filter is not None:
            if not isinstance(filter, tuple):
                self.logger(level="error", message="filter attribute not set properly!")
                return []

            if len(filter) != 3:
                self.logger(level="error", message="filter attribute not set properly!")
                return []

            if filter[1] not in ["==", "!=", ">", ">=", "<", "<="]:
                self.logger(level="error",
                            message="filter attribute should contain one of '==', '!=', '>', '>=', '<', '<='")
                return []

        if object_type == "backup":
            db_table_name = models.BackupRecord
            metadata_object_type = BackupMetadata
        elif object_type == "config":
            db_table_name = models.ConfigRecord
            metadata_object_type = ConfigMetadata
        elif object_type == "device":
            db_table_name = models.DeviceRecord
            metadata_object_type = DeviceMetadata
        elif object_type == "inventory":
            db_table_name = models.InventoryRecord
            metadata_object_type = InventoryMetadata
        elif object_type == "report":
            db_table_name = models.ReportRecord
            metadata_object_type = ReportMetadata
        elif object_type == "task":
            db_table_name = models.TaskRecord
            metadata_object_type = TaskMetadata
            if order_by[0] == "timestamp":
                order_by = ("timestamp_start", order_by[1])
        elif object_type == "taskstep":
            db_table_name = models.TaskStepRecord
            metadata_object_type = TaskStepMetadata
            if order_by[0] == "timestamp":
                order_by = ("timestamp_start", order_by[1])
        elif object_type == "repofile":
            db_table_name = models.RepoFileRecord
            metadata_object_type = RepoFileMetadata
        elif object_type == "reposynctodevice":
            db_table_name = models.RepoSyncToDeviceRecord
            metadata_object_type = RepoSyncToDeviceMetadata
        else:
            self.logger(level="error", message="Not a valid object type")
            return []

        if not hasattr(db_table_name, order_by[0]):
            self.logger(level="error", message="order_by attribute " + str(order_by[0]) + " is not valid")
            return []

        if db_table_name:
            try:
                with self.ManagedSession() as session:
                    filter_string = ""
                    filter_logger_string = ""
                    if filter is not None:
                        filter_string = "getattr(db_table_name, '" + str(filter[0]) + "') " + str(filter[1]) + " "
                        if isinstance(filter[2], bool):
                            filter_string += str(filter[2])
                        else:
                            filter_string += "'" + str(filter[2]) + "'"
                        filter_logger_string = " using filter " + str(filter_string)
                    if limit is not None:
                        filter_logger_string += " limit " + str(limit)
                    offset = 0
                    if page not in [0, "0", None]:
                        if limit is not None:
                            offset = int(page) * int(limit)
                        filter_logger_string += " offset " + str(offset)
                    if not device_uuid and not task_uuid and not repo_file_path:
                        if not uuid:
                            self.logger(level="debug",
                                        message="Querying " + object_type + " metadata from DB" + filter_logger_string)
                            if filter is not None:
                                # We query the DB with order_by (attribute_name & asc/desc order: e.g. timestamp.desc())
                                db_records = session.query(db_table_name).filter(eval(filter_string)).order_by(
                                    getattr(getattr(db_table_name, order_by[0]), order_by[1])()).offset(offset).limit(
                                    limit)
                            else:
                                db_records = session.query(db_table_name).order_by(
                                    getattr(getattr(db_table_name, order_by[0]), order_by[1])()).offset(offset).limit(
                                    limit)
                        else:
                            self.logger(level="debug", message="Querying " + object_type + " metadata with UUID " +
                                                               str(uuid) + " from DB" + filter_logger_string)
                            # We query the DB using UUID as filter and order_by (attribute_name & asc/desc order)
                            if filter is not None:
                                db_records = session.query(db_table_name).filter(eval(filter_string)).filter(
                                    getattr(db_table_name, "uuid") == str(uuid)).order_by(
                                    getattr(getattr(db_table_name, order_by[0]), order_by[1])()).offset(offset).limit(
                                    limit)
                            else:
                                db_records = session.query(db_table_name).filter(
                                    getattr(db_table_name, "uuid") == str(uuid)).order_by(
                                    getattr(getattr(db_table_name, order_by[0]), order_by[1])()).offset(offset).limit(
                                    limit)

                    elif device_uuid:
                        self.logger(level="debug", message="Querying " + object_type + " metadata for device " +
                                                           str(device_uuid) + " from DB" + filter_logger_string)
                        # We query the DB using device UUID as filter and order_by (attribute_name & asc/desc order)
                        if filter is not None:
                            db_records = session.query(db_table_name).filter(eval(filter_string)).filter(
                                getattr(db_table_name, "device_uuid") == str(device_uuid)).order_by(
                                getattr(getattr(db_table_name, order_by[0]), order_by[1])()).offset(offset).limit(limit)
                        else:
                            db_records = session.query(db_table_name).filter(
                                getattr(db_table_name, "device_uuid") == str(device_uuid)).order_by(
                                getattr(getattr(db_table_name, order_by[0]), order_by[1])()).offset(offset).limit(limit)
                    elif task_uuid:
                        self.logger(level="debug", message="Querying " + object_type + " metadata for task " +
                                                           str(task_uuid) + " from DB" + filter_logger_string)
                        # We query the DB using taskID as filter and order_by (attribute_name & asc/desc order)
                        if filter is not None:
                            db_records = session.query(db_table_name).filter(eval(filter_string)).filter(
                                getattr(db_table_name, "task_uuid") == str(task_uuid)).order_by(
                                getattr(getattr(db_table_name, order_by[0]), order_by[1])()).offset(offset).limit(limit)
                        else:
                            db_records = session.query(db_table_name).filter(
                                getattr(db_table_name, "task_uuid") == str(task_uuid)).order_by(
                                getattr(getattr(db_table_name, order_by[0]), order_by[1])()).offset(offset).limit(limit)
                    elif repo_file_path:
                        self.logger(level="debug", message="Querying " + object_type + " metadata for repo file " +
                                                           str(repo_file_path) + " from DB" + filter_logger_string)
                        # We query the DB using file_path as filter and order_by (attribute_name & asc/desc order)
                        if filter is not None:
                            db_records = session.query(db_table_name).filter(eval(filter_string)).filter(
                                getattr(db_table_name, "file_path") == str(repo_file_path)).order_by(
                                getattr(getattr(db_table_name, order_by[0]), order_by[1])()).offset(offset).limit(limit)
                        else:
                            db_records = session.query(db_table_name).filter(
                                getattr(db_table_name, "file_path") == str(repo_file_path)).order_by(
                                getattr(getattr(db_table_name, order_by[0]), order_by[1])()).offset(offset).limit(limit)

                metadata_list = []
                for db_record in db_records:
                    metadata = metadata_object_type()
                    if metadata.db_record is None:
                        metadata.db_record = db_record
                    for attribute in vars(db_record):
                        if "uuid" in attribute:
                            if getattr(db_record, attribute) is None:
                                setattr(metadata, attribute, None)
                            elif "uuids" in attribute and isinstance(getattr(db_record, attribute), list):
                                setattr(metadata, attribute, getattr(db_record, attribute))
                            else:
                                setattr(metadata, attribute, python_uuid.UUID(getattr(db_record, attribute)))
                        elif attribute in ["password"]:
                            if getattr(db_record, attribute, None):
                                try:
                                    setattr(metadata, attribute,
                                            self.cipher_suite.decrypt(getattr(db_record, attribute)).decode('utf-8'))
                                except Exception:
                                    self.logger(level="error", message="Unable to decrypt password for " + object_type +
                                                                       " with UUID " + str(db_record.uuid))
                        else:
                            setattr(metadata, attribute, getattr(db_record, attribute))
                    metadata_list.append(metadata)
                return metadata_list

            except Exception as err:
                self.logger(level="error", message="Unable to query " + object_type + " metadata from DB: " + str(err))
                return []

        return []

    def logger(self, level='info', message="No message"):
        if not self._parent_having_logger:
            self._parent_having_logger = self._find_logger()

        if self._parent_having_logger:
            self._parent_having_logger.logger(level=level, message=message)

    def save_images_to_repository(self, config=None, inventory=None):
        """
        Saves draw images generated from config or inventory to the repository
        :param config: config object handling generated images (service_profile_plots & orgs_plot)
        :param inventory: inventory object handling generated images (draw_inventory)
        :return: True if successful, False otherwise
        """
        if config and inventory:
            self.logger(level="error",
                        message="Config OR inventory must be given for save images to repository operation!")
            return False

        if inventory is not None:
            if not isinstance(inventory, GenericInventory):
                self.logger(level="error", message="Not a valid inventory provided!")
                return False
            device = inventory.device
        elif config is not None:
            if not isinstance(config, GenericConfig):
                self.logger(level="error", message="Not a valid config provided!")
                return False
            device = config.device
        else:
            self.logger(level="error", message="No config or inventory given for save images to repository operation!")
            return False

        # Creating folder in case it does not exist yet
        if self.create_images_folder(device=device):
            images_folder_full_path = os.path.abspath(os.path.join(EASYUCS_ROOT, device.metadata.images_path))
        else:
            images_folder_full_path = os.path.abspath(os.path.join(EASYUCS_ROOT, "."))

        if inventory:
            if not inventory.parent.export_draw(uuid=inventory.uuid, export_format="png",
                                                directory=images_folder_full_path, export_clear_pictures=True):
                return False

            return True
        elif config:
            if not config.parent.export_config_plots(config=config, export_format="png",
                                                     directory=images_folder_full_path):
                return False

            return True

        return False

    def save_key_to_repository(self, private_key=None, device_uuid=None):
        """
        Saves private key to the repository
        :param private_key: string containing private key to be saved
        :param device_uuid: UUID of the device to which the private key belongs
        :return: private key file path if save operation is successful, False otherwise
        """
        if private_key is None:
            self.logger(level="error", message="No private_key given for save key to repository operation!")
            return False

        if device_uuid is None:
            self.logger(level="error", message="No device_uuid given for save key to repository operation!")
            return False

        directory_keys = os.path.abspath(
            os.path.join(EASYUCS_ROOT, self.REPOSITORY_FOLDER_NAME, self.REPOSITORY_KEYS_FOLDER_NAME,
                         self.REPOSITORY_DEVICES_FOLDER_NAME)
        )
        private_key_full_path = os.path.abspath(
            os.path.join(EASYUCS_ROOT, self.REPOSITORY_FOLDER_NAME, self.REPOSITORY_KEYS_FOLDER_NAME,
                         self.REPOSITORY_DEVICES_FOLDER_NAME, str(device_uuid) + ".pem"))
        directory_relative_path = os.path.join(self.REPOSITORY_FOLDER_NAME, self.REPOSITORY_KEYS_FOLDER_NAME,
                                               self.REPOSITORY_DEVICES_FOLDER_NAME, str(device_uuid) + ".pem")

        # Creating keys folder in case it does not exist yet
        if not os.path.exists(directory_keys):
            self.logger(level="debug", message="Creating folder: " + directory_keys)
            os.makedirs(directory_keys)

        with open(private_key_full_path, 'w') as private_key_file:
            private_key_file.write(private_key)
        private_key_file.close()

        return directory_relative_path

    def save_metadata(self, metadata=None):
        """
        Saves GenericMetadata object to Database
        :param metadata: GenericMetadata object to be saved
        :return: True if successful, False otherwise
        """
        if metadata is None:
            self.logger(level="error", message="No metadata to save!")
            return False

        if not any(isinstance(metadata, x) for x in [GenericMetadata, GenericTaskMetadata]):
            self.logger(level="error", message="Not a valid metadata!")
            return False

        with self.ManagedSession() as session:
            if isinstance(metadata, BackupMetadata):
                if metadata.db_record is None:
                    metadata.db_record = models.BackupRecord()
            elif isinstance(metadata, ConfigMetadata):
                if metadata.db_record is None:
                    metadata.db_record = models.ConfigRecord()
            elif isinstance(metadata, DeviceMetadata):
                if metadata.db_record is None:
                    metadata.db_record = models.DeviceRecord()
            elif isinstance(metadata, InventoryMetadata):
                if metadata.db_record is None:
                    metadata.db_record = models.InventoryRecord()
            elif isinstance(metadata, ReportMetadata):
                if metadata.db_record is None:
                    metadata.db_record = models.ReportRecord()
            elif isinstance(metadata, TaskMetadata):
                if metadata.db_record is None:
                    metadata.db_record = models.TaskRecord()
            elif isinstance(metadata, TaskStepMetadata):
                if metadata.db_record is None:
                    metadata.db_record = models.TaskStepRecord()
            elif isinstance(metadata, RepoFileMetadata):
                if metadata.db_record is None:
                    metadata.db_record = models.RepoFileRecord()
            elif isinstance(metadata, RepoSyncToDeviceMetadata):
                if metadata.db_record is None:
                    metadata.db_record = models.RepoSyncToDeviceRecord()
            if metadata.db_record:
                for attribute in vars(metadata):
                    if "uuid" in attribute:
                        if getattr(metadata, attribute) is None:
                            setattr(metadata.db_record, attribute, None)
                        elif "uuids" in attribute and isinstance(getattr(metadata, attribute), list):
                            setattr(metadata.db_record, attribute, [str(item) for item in getattr(metadata, attribute)])
                        else:
                            setattr(metadata.db_record, attribute, str(getattr(metadata, attribute)))
                    elif attribute in ["password"]:
                        if getattr(metadata, attribute, None):
                            setattr(metadata.db_record, attribute,
                                    self.cipher_suite.encrypt(bytes(getattr(metadata, attribute), encoding='utf8')))
                    else:
                        setattr(metadata.db_record, attribute, getattr(metadata, attribute))

            try:
                if hasattr(metadata, "file_type") and metadata.file_type is not None:
                    self.logger(level="debug", message="Saving " + metadata.file_type + " metadata with UUID " +
                                                       str(metadata.uuid) + " to DB")
                elif hasattr(metadata, "name") and metadata.name is not None:
                    self.logger(level="debug", message="Saving " + metadata.name + " metadata with UUID " +
                                                       str(metadata.uuid) + " to DB")

                # Since this metadata object may be linked to a previous db session, we merge it to the current session
                # to be able to add it to the db
                local_db_record = session.merge(metadata.db_record)
                session.add(local_db_record)

            except Exception as err:
                self.logger(level="error", message="Unable to save metadata to DB: " + str(err))
                return False

        return True

    def save_to_repository(self, object=None):
        """
        Saves an EasyUCS object to the repository (file + metadata)
        :param object: object to be saved to the repository (config/device/inventory/report)
        :return: True if successful, False otherwise
        """
        if object is None:
            self.logger(level="error", message="No object given for save to repository operation!")
            return False

        if not any(isinstance(object, x) for x in [GenericBackup, GenericConfig, GenericDevice, GenericInventory,
                                                   GenericReport]):
            self.logger(level="error", message="Object type not supported!")
            return False

        # We save the corresponding file to the repository, unless it's a device (no file to save),
        # or a backup (file already saved during backup fetch operation)
        if not any(isinstance(object, x) for x in [GenericBackup, GenericDevice]):
            file_path = self._save_file(object=object)
            if not file_path:
                return False

            # We now save the file path to the object's metadata
            object.metadata.file_path = file_path

        # We also save the sub devices to the repository
        if getattr(object, "sub_devices", None):
            for sub_device in object.sub_devices:
                if not self.save_to_repository(object=sub_device):
                    return False

        if not self.save_metadata(metadata=object.metadata):
            return False

        return True
