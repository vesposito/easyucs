import json
import common
import os
from __init__ import EASYUCS_ROOT
from repository.manager import RepositoryManager
from device.device import GenericDevice


class GenericCacheManager:
    REPOSITORY_DEVICES_CACHE_FOLDER_NAME: str = "cache"

    def __init__(self, parent=None):
        self.parent = parent
        self._parent_having_logger = self._find_logger()
        self.cache = None

    def logger(self, level='info', message="No message", set_api_error_message=True):
        if not self._parent_having_logger:
            self._parent_having_logger = self._find_logger()

        if self._parent_having_logger:
            self._parent_having_logger.logger(level=level, message=message, set_api_error_message=set_api_error_message)

    def _find_logger(self):
        # Method to find the object having a logger - it can be high up in the hierarchy of objects
        current_object = self
        while hasattr(current_object, 'parent') and not hasattr(current_object, '_logger_handle'):
            current_object = current_object.parent

        if hasattr(current_object, '_logger_handle'):
            return current_object
        else:
            print("WARNING: No logger found in Config Manager")
            return None

    def _fill_cache_from_json(self):
        """
        Fills the cache with data from a JSON cache file.

        Returns:
            bool: True if the cache was successfully populated, False otherwise.
        """
        if not isinstance(self.parent, GenericDevice):
            self.logger(level="error", message="Invalid device provided to fill the cache")
            return False

        # System catalog devices don't have a cache as they are not real devices. Ignoring them
        if self.parent.metadata.is_system and self.parent.metadata.is_hidden and \
                self.parent.metadata.system_usage == "catalog":
            return False

        cache_json = common.read_json_file(
            file_path=os.path.join("data", "files", "devices", str(self.parent.uuid), "cache", "cache.json"),
            logger=self
        )
        if not cache_json:
            self.logger(level="info", message="Cache JSON file is not available in the repository for this device")
            return False

        # Fill cache from JSON data
        if cache_json.get("servers", None):
            self.cache.server_details = cache_json["servers"]
        if cache_json.get("orgs", None):
            self.cache.orgs = cache_json["orgs"]
        if cache_json.get("os_firmware", None):
            self.cache.os_firmware_data = cache_json["os_firmware"]
        return True

    def create_cache_folder(self):
        """
        Creates a cache folder for the specified device.

        Validates the provided device object and constructs a cache folder path
        based on the device's UUID. If the folder does not already exist, it is created.

        :return: The absolute path to the cache folder if successful, None if the device is invalid.
        """

        if not isinstance(self.parent, GenericDevice):
            self.logger(level="error", message="Invalid device provided for cache folder creation!")
            return None

        # Construct the cache folder path
        device_uuid = str(self.parent.uuid)
        directory_full_path = os.path.abspath(
            os.path.join(
                EASYUCS_ROOT,
                RepositoryManager.REPOSITORY_FOLDER_NAME,
                RepositoryManager.REPOSITORY_FILES_FOLDER_NAME,
                RepositoryManager.REPOSITORY_DEVICES_FOLDER_NAME,
                device_uuid,
                self.REPOSITORY_DEVICES_CACHE_FOLDER_NAME
            )
        )

        # Create the folder if it doesn't exist
        if not os.path.exists(directory_full_path):
            self.logger(level="debug", message=f"Creating folder: {directory_full_path}")
            os.makedirs(directory_full_path)

        return directory_full_path

    def save_to_cache(self, cache_key):
        """
        Saves specific data (e.g., server details, organizations, firmware data) to the cache for a device.

        :param cache_key: Key identifying the type of data to save in the cache
        (e.g., "os_firmware_data", "orgs", "server_details")
        :return: bool: True if data was saved successfully, False otherwise
        """

        if not cache_key:
            self.logger(level="error", message="No cache key specified for saving data!")
            return False

        # Create cache folder and check for errors
        cache_folder_path = self.create_cache_folder()
        if not cache_folder_path:
            return False

        # Construct the path for the cache JSON file
        cache_path = os.path.join(cache_folder_path, "cache.json")

        # Read the existing data if the file exists, otherwise initialize with an empty structure
        try:
            if os.path.exists(cache_path):
                with open(cache_path, "r") as file:
                    cached_data = json.load(file)
            else:
                cached_data = {}
        except (IOError, json.JSONDecodeError) as e:
            self.logger(level="error", message=f"Failed to read existing cache file: {e}")
            return False

        if cache_key == "os_firmware":
            cached_data["os_firmware"] = self.cache.os_firmware_data
        elif cache_key == "orgs":
            cached_data["orgs"] = self.cache.orgs
        elif cache_key == "server_details":
            cached_data["servers"] = self.cache.server_details

        # Write the updated data back to the cache JSON file
        try:
            with open(cache_path, "w") as file:
                json.dump(cached_data, file, indent=3)
            self.logger(level="debug", message=f"Successfully saved {cache_key} data to {cache_path}")
        except IOError as e:
            self.logger(level="error", message=f"Failed to write {cache_key} data to file: {e}.")
            return False

        return True

    def fetch_cache(self):
        return None

    def export_cache(self, export_format="json", directory=None, filename=None):
        """
        Exports the specified cache in the specified export format to the specified filename
        :param export_format: The export format (e.g. "json")
        :param directory: The directory containing the export file
        :param filename: The name of the file containing the exported content
        :return: True if export is successful, False otherwise
        """
        if export_format not in ["json"]:
            self.logger(level="error", message="Requested inventory export format not supported!")
            return False
        if filename is None:
            self.logger(level="error", message="Missing filename in inventory export request!")
            return False
        if not directory:
            self.logger(level="debug",
                        message="No directory specified in inventory export request. Using local folder.")
            directory = "."

        cache = self.cache
        if cache is None:
            self.logger(level="error", message="Could not find any cache to export!")
            return False
        self.logger(level="debug", message="Using cache for export")

        cache_json = {}

        if export_format == "json":
            self.logger(level="debug", message="Requested cache export format is JSON")
            self.logger(message="Exporting cache to file: " + directory + "/" + filename)
            if getattr(cache, "server_details", None):
                cache_json["servers"] = cache.server_details
            if getattr(cache, "os_firmware_data", None):
                cache_json["os_firmware"] = cache.os_firmware_data
            if getattr(cache, "orgs", None):
                cache_json["orgs"] = cache.orgs
            if not os.path.exists(directory):
                self.logger(message="Creating directory " + directory)
                os.makedirs(directory)
            with open(directory + '/' + filename, 'w') as cache_json_file:
                json.dump(cache_json, cache_json_file, indent=3)
            cache_json_file.close()
        return True
