# coding: utf-8
# !/usr/bin/env python

""" manager.py: Easy UCS Deployment Tool """

import json
import os

from packaging import version as packaging_version

from __init__ import __version__
from common import read_json_file, validate_json
import export


class GenericConfigManager:
    def __init__(self, parent=None):
        self.config_class_name = None
        self.config_list = []
        self.parent = parent

        self._parent_having_logger = self._find_logger()

    def clear_config_list(self):
        """
        Removes all the configs from the config list
        :return: True
        """
        self.config_list.clear()
        return True

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

    def fetch_config(self, force=False):
        return None

    def export_config(self, uuid=None, export_format="json", directory=None, filename=None):
        """
        Exports the specified config in the specified export format to the specified filename
        :param uuid: The UUID of the config to be exported. If not specified, the most recent config will be used
        :param export_format: The export format (e.g. "json")
        :param directory: The directory containing the export file
        :param filename: The name of the file containing the exported content
        :return: True if export is successful, False otherwise
        """
        if export_format not in ["json"]:
            self.logger(level="error", message="Requested config export format not supported!")
            return False
        if filename is None:
            self.logger(level="error", message="Missing filename in config export request!")
            return False
        if not directory:
            self.logger(level="debug",
                        message="No directory specified in config export request. Using local folder.")
            directory = "."

        if uuid is None:
            self.logger(level="debug", message="No config UUID specified in config export request. Using latest.")
            config = self.get_latest_config()
        else:
            # Find the config that needs to be exported
            config_list = [config for config in self.config_list if config.uuid == uuid]
            if len(config_list) != 1:
                self.logger(level="error", message="Failed to locate config with UUID " + str(uuid) + " for export")
                return False
            else:
                config = config_list[0]

        if config is None:
            # We could not find any config
            self.logger(level="error", message="Could not find any config to export!")
            return False
        if config.export_list is None or len(config.export_list) == 0:
            # Nothing to export
            self.logger(level="error", message="Nothing to export on the selected config!")
            return False

        self.logger(level="debug", message="Using config " + str(config.uuid) + " for export")

        if export_format == "json":
            self.logger(level="debug", message="Requested config export format is JSON")
            header_json = {"metadata": [export.generate_json_metadata_header(file_type="config", config=config)]}
            config_json = {"easyucs": header_json, "config": {}}
            for export_attribute in config.export_list:
                # We check if the attribute to be exported is an empty list, in which case, we don't export it
                if isinstance(getattr(config, export_attribute), list):
                    if len(getattr(config, export_attribute)) == 0:
                        continue
                config_json["config"][export_attribute] = []
                if isinstance(getattr(config, export_attribute), list):
                    count = 0
                    for config_object in getattr(config, export_attribute):
                        if isinstance(config_object, str):
                            config_json["config"][export_attribute].append(config_object)
                        elif isinstance(config_object, list):
                            config_json["config"][export_attribute].extend(config_object)
                        else:
                            config_json["config"][export_attribute].append({})
                            export.export_attributes_json(config_object,
                                                          config_json["config"][export_attribute][count])
                        count += 1
                elif isinstance(getattr(config, export_attribute), str):
                    config_json["config"][export_attribute] = getattr(config, export_attribute)
                else:
                    config_object = getattr(config, export_attribute)
                    config_json["config"][export_attribute].append({})
                    export.export_attributes_json(config_object, config_json["config"][export_attribute][0])

            # Calculate md5 hash of entire JSON file and adding it to header before exporting
            config_json = export.insert_json_metadata_hash(json_content=config_json)
            if not config_json:
                self.logger(level="error", message="Unable to calculate MD5 hash of config file!")
                return False

            # Saving md5 hash to the ConfigMetadata object
            config.metadata.hash = config_json["easyucs"]["metadata"][0]["hash"]

            self.logger(message="Exporting config " + str(config.uuid) + " to file: " + directory + "/" + filename)
            if not os.path.exists(directory):
                self.logger(message="Creating directory " + directory)
                os.makedirs(directory)
            with open(directory + '/' + filename, 'w') as config_json_file:
                json.dump(config_json, config_json_file, indent=3)
            config_json_file.close()
            return True

    def import_config(self, import_format="json", directory=None, filename=None, config=None, metadata=None):
        """
        Imports the specified config in the specified import format from the specified filename to config_list
        :param import_format: The import format (e.g. "json")
        :param directory: The directory containing the import file
        :param filename: The name of the file containing the content to be imported
        :param config: The config content to be imported (if no directory/filename provided)
        :param metadata: The metadata object of to the config to be imported (if no config or dir/file provided)
        :return: Config object if import is successful, False otherwise
        """
        if import_format not in ["json"]:
            self.logger(level="error", message="Requested config import format not supported!")
            return False

        # If no config content is provided, we need to open the file using directory and filename arguments
        if config is None:
            if metadata is None:
                if filename is None:
                    self.logger(level="error", message="Missing filename in config import request!")
                    return False
                if directory is None:
                    self.logger(level="debug",
                                message="No directory specified in config import request. Using local folder.")
                    directory = "."
            else:
                if metadata.file_path is None:
                    self.logger(level="error", message="Missing metadata file path in config import request!")
                    return False
                else:
                    directory = os.path.dirname(metadata.file_path)
                    filename = os.path.basename(metadata.file_path)

            # Making sure config file exists
            if not os.path.exists(directory + '/' + filename):
                self.logger(level="error",
                            message="Requested config file: " + directory + "/" + filename + " does not exist!")
                return False

            if import_format == "json":
                self.logger(level="debug", message="Requested config import format is JSON")
                with open(directory + '/' + filename, 'r') as config_json_file:
                    try:
                        complete_json = json.load(config_json_file)
                    except json.decoder.JSONDecodeError as err:
                        self.logger(level="error",
                                    message="Invalid config JSON file " + directory + "/" + filename + ": " + str(err))
                        return False
                config_json_file.close()

        else:
            if import_format == "json":
                self.logger(level="debug", message="Requested config import format is JSON")
                if isinstance(config, str):
                    try:
                        complete_json = json.loads(config)
                    except json.decoder.JSONDecodeError as err:
                        self.logger(level="error", message="Error while importing config: " + str(err))
                        return False
                elif isinstance(config, dict):
                    complete_json = config
                else:
                    self.logger(level="error", message="Unable to import config")
                    return False

        if import_format in ["json"]:
            # We verify that the JSON content is valid
            if not self._validate_config_from_json(config_json=complete_json):
                self.logger(level="error", message="Can't import invalid config JSON file", set_api_error_message=False)
                return False
            else:
                self.logger(message="Successfully validated config JSON file")

            # We verify the hash of the file to check if it has been modified
            custom = False
            if not export.verify_json_metadata_hash(json_content=complete_json):
                self.logger(message="Hash of the imported file does not verify. Config will be marked as custom")
                custom = True

            # We calculate md5 hash of entire imported JSON file and add it to header
            complete_json = export.insert_json_metadata_hash(json_content=complete_json)
            if not complete_json:
                self.logger(level="debug", message="Unable to calculate MD5 hash of imported config file!")
                return False

            # We now compare the hash of the file to the hash of the metadata object if we have it
            if not custom and metadata is not None:
                if "metadata" in complete_json["easyucs"]:
                    if "hash" in complete_json["easyucs"]["metadata"][0]:
                        if metadata.hash is not None:
                            if metadata.hash != complete_json["easyucs"]["metadata"][0]["hash"]:
                                self.logger(level="debug", message="Hash of the imported file does not match " +
                                                                   "metadata hash. Config will be marked as custom")
                                custom = True

            # We make sure there is a "config" section in the file
            if "config" in complete_json:
                config_json = complete_json["config"]
            else:
                self.logger(level="error", message="No config section in JSON file. Could not import config")
                return False
            from api.api_server import easyucs
            if easyucs:
                settings = easyucs.repository_manager.settings
            else:
                settings = read_json_file(file_path="settings.json", logger=self)
            # We create a new config object
            if self.config_class_name.__name__ == "IntersightConfig" and settings:
                config = self.config_class_name(parent=self, settings=settings)
            else:
                config = self.config_class_name(parent=self)

            # We use the provided metadata for the new config object if the hash of the file is valid
            if not custom and metadata is not None:
                self.logger(level="debug", message="Using provided metadata for config import")
                config.metadata = metadata
                config.metadata.parent = config
                config.uuid = metadata.uuid

            config.load_from = "file"
            config.metadata.easyucs_version = __version__

            # If device is system catalog device, and import is not from /samples directory, we mark config as Custom
            if self.parent.metadata.is_system and self.parent.metadata.system_usage == "catalog" \
                    and directory != "samples":
                config.metadata.category = "custom"

            # We save md5 hash to the ConfigMetadata object
            config.metadata.hash = complete_json["easyucs"]["metadata"][0]["hash"]

            # We set the origin of the config as "file"
            config.metadata.origin = "file"

            # We set the custom flag of the config
            if custom:
                config.custom = True

            # We fetch all options set in "easyucs" section of the file
            if "easyucs" in complete_json:
                if "options" in complete_json["easyucs"]:
                    self.logger(level="debug", message="Importing options from config file")
                    for option in complete_json["easyucs"]["options"]:
                        config.options.update(option)
                if (custom or metadata is None) and "metadata" in complete_json["easyucs"]:
                    # We use some values from the file (but not all - e.g. we do not trust UUID)
                    if "intersight_status" in complete_json["easyucs"]["metadata"][0]:
                        config.intersight_status = complete_json["easyucs"]["metadata"][0]["intersight_status"]

                    if "category" in complete_json["easyucs"]["metadata"][0]:
                        config.metadata.category = complete_json["easyucs"]["metadata"][0]["category"]
                    if "device_name" in complete_json["easyucs"]["metadata"][0]:
                        config.metadata.device_name = complete_json["easyucs"]["metadata"][0]["device_name"]
                    if "device_version" in complete_json["easyucs"]["metadata"][0]:
                        config.metadata.device_version = complete_json["easyucs"]["metadata"][0]["device_version"]
                    if "name" in complete_json["easyucs"]["metadata"][0]:
                        config.metadata.name = complete_json["easyucs"]["metadata"][0]["name"]
                    if "revision" in complete_json["easyucs"]["metadata"][0]:
                        config.metadata.revision = complete_json["easyucs"]["metadata"][0]["revision"]
                    if "subcategory" in complete_json["easyucs"]["metadata"][0]:
                        config.metadata.subcategory = complete_json["easyucs"]["metadata"][0]["subcategory"]
                    if "url" in complete_json["easyucs"]["metadata"][0]:
                        config.metadata.url = complete_json["easyucs"]["metadata"][0]["url"]

            # We start filling up the config
            self.logger(message="Importing config from " + import_format)
            result = self._fill_config_from_json(config=config, config_json=config_json)
            if result:
                self.logger(message="Config import successful. Appending config " + str(config.uuid) +
                                    " to the list of configs for device " + str(self.parent.uuid))
                # We add the config to the list of configs
                self.config_list.append(config)
                return config
            else:
                self.logger(level="error", message="Config import failed!")
                return False

    def _validate_config_from_json(self, config_json=None):
        """
        Validates a config using the JSON schema definition
        :param config_json: JSON content containing config to be validated
        :return: True if config is valid, False otherwise
        """

        # Open JSON master schema for the corresponding config
        if self.parent.metadata.device_type in ["cimc", "ucsc", "ucsm"]:
            master_file_path = "schema/ucs/" + self.parent.metadata.device_type + "/master.json"
        else:
            master_file_path = "schema/" + self.parent.metadata.device_type + "/master.json"

        if not validate_json(json_data=config_json, schema_path=master_file_path, logger=self):
            self.logger(level="error", message="Failed to validate config from json file", set_api_error_message=False)
            return False

        # We now validate that the easyucs_version of the file is not greater than the running version of EasyUCS
        easyucs_version_from_file = config_json["easyucs"]["metadata"][0]["easyucs_version"]
        if packaging_version.parse(easyucs_version_from_file) > packaging_version.parse(__version__):
            self.logger(level="error",
                        message="Failed to validate config JSON file because it has been created using a more " +
                                "recent version of EasyUCS (" + easyucs_version_from_file + " > " + __version__ + ")")
            return False

        return True

    def push_config(self, uuid=None):
        """
        Push the specified config on the live system
        :param uuid: The UUID of the config to be exported. If not specified, the most recent config will be used
        :return: True if config push was successful, False otherwise
        """
        return False

    def _fill_config_from_json(self, config=None, config_json=None):
        """
        Fills config using parsed JSON config file
        :param config: config to be filled
        :param config_json: parsed JSON content containing config
        :return: True if successful, False otherwise
        """
        return False

    def get_latest_config(self):
        """
        Returns the most recent config from the config list
        :return: GenericConfig (or subclass), None if no config is found
        """
        if len(self.config_list) == 0:
            return None
        # return sorted(self.config_list, key=lambda config: config.metadata.timestamp)[-1]
        return self.config_list[-1]

    def find_config_by_uuid(self, uuid=None):
        """
        Finds a config from the config list given a specific UUID
        :param uuid: UUID of the config to find
        :return: config if found, None otherwise
        """
        if uuid is None:
            self.logger(level="error", message="No config UUID specified in find config request.")
            return None

        config_list = [config for config in self.config_list if str(config.uuid) == str(uuid)]
        if len(config_list) != 1:
            self.logger(level="debug", message="Failed to locate config with UUID " + str(uuid))
            return None
        else:
            return config_list[0]

    def remove_config(self, uuid=None):
        """
        Removes the specified config from the config list
        :param uuid: The UUID of the config to be deleted
        :return: True if delete is successful, False otherwise
        """
        if uuid is None:
            self.logger(level="error", message="No config UUID specified in remove config request.")
            return False

        # Find the config that needs to be removed
        config = self.find_config_by_uuid(uuid=uuid)
        if not config:
            return False
        else:
            config_to_remove = config

        # Remove the config from the list of configs
        self.config_list.remove(config_to_remove)

        # Delete the config in the repository
        # directory = "repository/" + str(self.parent.uuid) + "/configs/config-" + str(uuid) + ".json"
        #
        # if os.path.exists(directory):
        #     os.remove(directory)
        # else:
        #     self.logger(level="error", message="Config not found in repository. Nothing to delete.")
        #     return False

        return True
