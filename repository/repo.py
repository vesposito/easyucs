# coding: utf-8
# !/usr/bin/env python

""" repo.py: Easy UCS Deployment Tool """
import datetime
import os
import requests
import shutil
import sqlalchemy.exc
import time
import uuid
from queue import Queue
from sqlite3 import IntegrityError

from repository.metadata import RepoFileMetadata, RepoSyncToDeviceMetadata
from repository.db.models import RepoFileRecord, RepoSyncToDeviceRecord
from common import calculate_checksum
from __init__ import EASYUCS_ROOT


class Repo:
    def __init__(self, parent=None):
        self.parent = parent
        # Tasks queued to be executed for the repo (excluding the already executing ones in the task manager).
        # This queue will only get populated when a repo already have a task under execution and some other tasks
        # are queued to be executed. So the queued tasks will be part of this queue.
        self.queued_tasks = Queue(maxsize=10)
        self.task = None

    def calculate_checksums(self, file_path=None, algorithms=None):
        """
        Calculate multiple checksum algorithms for a file path.
        :param file_path: Path of the file.
        :param algorithms: A list of checksums to apply.
        :return: True if checksums calculation is successful, False otherwise
        """
        if not file_path:
            self.parent.logger(level="error", message="No file path provided")
            return False
        if not algorithms:
            self.parent.logger(level="error", message="No algorithms provided")
            return False

        file_metadata = self.parent.get_metadata(object_type="repofile",
                                                 repo_file_path=os.path.relpath(file_path, start=EASYUCS_ROOT))
        if len(file_metadata) == 1:
            file_metadata = file_metadata[0]
        else:
            self.parent.logger(level="error", message=f"No db record found for file path {file_path}")
            return False

        if self.task is not None:
            self.task.taskstep_manager.start_taskstep(
                name="CalculateChecksums",
                description=f"Calculating the checksums of the file {file_metadata.file_path}")

        for algorithm in algorithms:
            checksum = calculate_checksum(file_path=file_path, algorithm=algorithm)
            if checksum:
                setattr(file_metadata, algorithm.lower(), checksum)
            else:
                self.parent.logger(level="error",
                               message=f"Failed to calculate {algorithm} checksum for file {file_path}")

                if self.task is not None:
                    self.task.taskstep_manager.stop_taskstep(
                        name="CalculateChecksums", status="failed",
                        status_message=f"Failed to calculate {algorithm} checksum for file {file_path}")

                self.parent.save_metadata(file_metadata)

                return False

        self.parent.save_metadata(file_metadata)

        if self.task is not None:
            self.task.taskstep_manager.stop_taskstep(
                name="CalculateChecksums", status="successful",
                status_message=f"Successfully calculated {', '.join(algorithms)} checksums")

        return True

    @staticmethod
    def create_repofile_download_link(file_path=None, host_url=None):
        """
        Function to return the repofile download link
        :param file_path: Relative file path to the file
        :param host_url: Host url where the backend server runs
        :return: Download link to the file
        """
        file_path = file_path.replace('\\', '/')
        return f"{host_url}/repo/{file_path}"

    @staticmethod
    def create_repofile_metadata(file_path=None, md5=None, sha1=None, sha256=None):
        """
        Function to create a repofile metadata object
        :param file_path: Path to the repo file
        :param md5: MD5 checksum of the file
        :param sha1: SHA1 checksum of the file
        :param sha256: SHA256 checksum of the file
        :return: Repofile metadata object if successful, None otherwise
        """
        if not file_path:
            return None
        file_metadata = RepoFileMetadata()
        file_metadata.file_path = file_path
        file_metadata.md5 = md5
        file_metadata.sha1 = sha1
        file_metadata.sha256 = sha256
        file_metadata.uuid = uuid.uuid4()

        return file_metadata

    def create_reposynctodevice_metadata(self, description=None, device=None, file_download_link=None, file_path=None,
                                         file_uuid=None, firmware_image_type=None, image_type=None, name=None,
                                         org_name=None, supported_models=None, tags=None, vendor=None, version=None):
        """
        Function to create a repofile metadata object.
        :param description: Description
        :param device: EasyUCS device object
        :param file_download_link: Link from where file can be downloaded
        :param file_path: Path to the download file
        :param file_uuid: UUID of file which is synced to the device
        :param firmware_image_type: Image type of the firmware
        :param image_type: Type of image (os/firmware/scu)
        :param name: Name of the software repository link
        :param org_name: Organization name
        :param supported_models: Models that are supported
        :param tags: Tags
        :param vendor: Vendor of the OS
        :param version: Version of image type
        :return: RepoSyncToDeviceMetadata metadata object if successful, None otherwise
        """
        if not file_uuid and file_path:
            # We try to get the file_uuid using the file_path attribute
            repo_file_list = self.parent.get_metadata(object_type="repofile", repo_file_path=file_path)
            if len(repo_file_list) != 1:
                self.parent.logger(level="error",
                                   message=f"RepoFile record with path '{file_path}' not found in DB")
                return None
            file_uuid = getattr(repo_file_list[0], "uuid")

        repo_sync_to_device_metadata = RepoSyncToDeviceMetadata()
        repo_sync_to_device_metadata.description = description
        repo_sync_to_device_metadata.device_name = device.metadata.device_name
        repo_sync_to_device_metadata.device_type = device.metadata.device_type
        repo_sync_to_device_metadata.device_uuid = device.metadata.uuid
        repo_sync_to_device_metadata.file_download_link = file_download_link
        repo_sync_to_device_metadata.file_uuid = file_uuid
        repo_sync_to_device_metadata.firmware_image_type = firmware_image_type
        repo_sync_to_device_metadata.image_type = image_type
        repo_sync_to_device_metadata.name = name
        repo_sync_to_device_metadata.org_name = org_name
        repo_sync_to_device_metadata.supported_models = supported_models
        repo_sync_to_device_metadata.tags = tags
        repo_sync_to_device_metadata.uuid = uuid.uuid4()
        repo_sync_to_device_metadata.vendor = vendor
        repo_sync_to_device_metadata.version = version

        return repo_sync_to_device_metadata

    def download_file(self, url=None, path=None, file_name=None, verify_ssl=True):
        """
        Function to download a file to the download path
        :param url: URL to download the file
        :param path: Download path of the file
        :param file_name: Download file name
        :param verify_ssl: If True, we verify the server's TLS certificate otherwise we don't
        :return: True if successful, False otherwise
        """
        if not url:
            self.parent.logger(level="error", message=f"Download URL is not provided")
            return False
        if not path:
            self.parent.logger(level="error", message=f"Download Path is not provided")
            return False
        if not file_name:
            # This assumes that the filename is the last segment in the URL
            file_name = url.split('/')[-1]

        if self.task is not None:
            self.task.taskstep_manager.start_taskstep(
                name="DownloadFile",
                description=f"Downloading the file '{file_name}' to the repo")
        try:
            # Generate a unique filename to avoid overwriting using 8 chars of uuid before filename.
            tmp_file_name = f"{str(uuid.uuid4())[:8]}_{file_name}"
            tmp_path = os.path.abspath(os.path.join(EASYUCS_ROOT, self.parent.REPOSITORY_FOLDER_NAME,
                                                    self.parent.REPOSITORY_TMP_FOLDER_NAME))
            tmp_file_path = os.path.join(tmp_path, tmp_file_name)

            dest_file_path = os.path.join(path, file_name)

            # Calling the download url
            res = requests.get(url, stream=True, verify=verify_ssl)
            # Checking the HTTP response status code
            if res.status_code != 200:
                err_msg = (f"Failed to download the file '{file_name}', "
                           f"Status code: {res.status_code}, Reason: {res.reason}")
                self.parent.logger(level="error", message=err_msg)
                if self.task is not None:
                    self.task.taskstep_manager.stop_taskstep(
                        name="DownloadFile", status="failed", status_message=err_msg)
                return False

            total_length = res.headers.get('content-length')

            # If content-length header is missing then we write all the content to the file. Otherwise, we write the
            # file in chunks.
            if total_length is None:  # no content length header
                with open(tmp_file_path, 'wb') as f:
                    f.write(res.content)
            else:
                total_length = int(total_length)
                downloaded = 0

                last_time = time.time()
                chunk_size = 10**6  # 1 MB
                with open(tmp_file_path, 'wb') as f:
                    for data in res.iter_content(chunk_size=chunk_size):
                        downloaded += len(data)
                        f.write(data)

                        current_time = time.time()
                        if (current_time - last_time) >= 10:
                            last_time = current_time
                            self.parent.logger(level="debug",
                                               message=f"Downloaded {downloaded} of {total_length} bytes "
                                                       f"({(downloaded / total_length) * 100:.2f}%)")
                            if self.task:
                                self.task.parent.set_task_progression(uuid=self.task.metadata.uuid,
                                                                      progress=int((downloaded / total_length) * 100))

            # During the download if someone creates a file with same name in the destination path, then we mark this
            # task as failed and delete the downloaded file from 'tmp' directory.
            if os.path.exists(dest_file_path):
                self.parent.logger(level="error", message=f"File with name '{file_name}' already exists")
                if self.task is not None:
                    self.task.taskstep_manager.stop_taskstep(
                        name="DownloadFile", status="failed",
                        status_message=f"File with name '{file_name}' already exists")

                # Removing the downloaded file
                os.remove(tmp_file_path)

                return False

            # After all the chunks are saved to tmp folder, we move the file to its designated position.
            shutil.move(tmp_file_path, dest_file_path)

            if self.task is not None:
                self.task.taskstep_manager.stop_taskstep(
                    name="DownloadFile", status="successful",
                    status_message=f"Successfully downloaded the file '{file_name}'")

            return True

        except requests.exceptions.RequestException as e:
            error_message = f"Error downloading file: {e}"
            self.parent.logger(level="error", message=error_message)

        except Exception as e:
            error_message = f"Unexpected error downloading file: {e}"
            self.parent.logger(level="error", message=error_message)

        if self.task is not None:
            self.task.taskstep_manager.stop_taskstep(
                name="DownloadFile", status="failed",
                status_message=error_message[:255]
            )
        return False

    @staticmethod
    def get_size(file_path):
        """
        Function which returns the size of the file as most appropriate string. Assumes file already exists
        :param file_path: Path to the file
        :return: Size of the file as string
        """
        total_size = 0
        if os.path.isdir(file_path):
            for dir_path, _, filenames in os.walk(file_path):
                for filename in filenames:
                    sub_file_path = os.path.join(dir_path, filename)
                    total_size += os.path.getsize(sub_file_path)
        else:
            total_size = os.path.getsize(file_path)

        return total_size

    def get_repofile(self, absolute_file_path=None, file_uuid=None, synced_data=False):
        """
        Function to get the repofile record with some additional information.
        :param absolute_file_path: Relative path to the file
        :param file_uuid: UUID of the repofile record
        :param synced_data: Whether to return synced data with the repofile record
        :return: repofile data with some additional information if found, otherwise {}
        """
        if not absolute_file_path and not file_uuid:
            self.parent.logger("File path or file uuid not provided")
            return {}

        rel_file_path = os.path.relpath(absolute_file_path, start=EASYUCS_ROOT)

        repofile_record = {}
        # EASYUCS-980: If 2 APIs, Get files and rename are called in a very short duration, then there is a chance
        # we may encounter a race condition that can occur when creating a record in 'repofile', which will result in
        # a UniqueViolation error. To handle this scenario we catch the UniqueViolation error and retry the
        # get_metadata() to get the already existing record.
        for _ in range(2):
            if absolute_file_path:
                repofile_metadata = self.parent.get_metadata(object_type="repofile", repo_file_path=rel_file_path)
            else:
                repofile_metadata = self.parent.get_metadata(object_type="repofile", uuid=file_uuid)

            # If there is no record for the file in DB, then we create one.
            if not repofile_metadata:
                repofile_metadata = self.create_repofile_metadata(file_path=os.path.relpath(absolute_file_path,
                                                                                            start=EASYUCS_ROOT))
                try:
                    self.parent.save_metadata(metadata=repofile_metadata)
                except sqlalchemy.exc.IntegrityError as err:
                    if isinstance(err.orig, IntegrityError):
                        continue
                    else:
                        raise
            else:
                repofile_metadata = repofile_metadata[0]
            break

        for field in [column.key for column in RepoFileRecord.__table__.columns]:
            if getattr(repofile_metadata, field) not in [None, ""]:
                if "uuid" in field:
                    repofile_record[field] = str(getattr(repofile_metadata, field))
                elif "timestamp" in field:
                    repofile_record[field] = getattr(repofile_metadata, field).isoformat()[:-3] + 'Z'
                else:
                    repofile_record[field] = getattr(repofile_metadata, field)

        synctodevice_metadata = self.parent.get_metadata(object_type="reposynctodevice",
                                                         filter=("file_uuid", "==",
                                                                 str(repofile_metadata.uuid)))
        if synctodevice_metadata:
            repofile_record["is_synced"] = True
            if synced_data:
                repofile_record["synced_data"] = []
                for sync_metadata in synctodevice_metadata:
                    sync_record = {}
                    for field in [column.key for column in RepoSyncToDeviceRecord.__table__.columns]:
                        if getattr(sync_metadata, field) not in [None, ""]:
                            if "uuid" in field:
                                sync_record[field] = str(getattr(sync_metadata, field))
                            elif "timestamp" in field:
                                sync_record[field] = getattr(sync_metadata, field).isoformat()[:-3] + 'Z'
                            else:
                                sync_record[field] = getattr(sync_metadata, field)
                    repofile_record["synced_data"].append(sync_record)
        else:
            repofile_record["is_synced"] = False

        repofile_record["name"] = os.path.basename(absolute_file_path)
        repofile_record["is_directory"] = False
        repofile_record["size"] = self.get_size(file_path=absolute_file_path)
        repofile_record["timestamp_last_modified"] = datetime.datetime.fromtimestamp(os.path.getmtime(
            absolute_file_path)).isoformat()[:-3] + 'Z'

        return repofile_record
