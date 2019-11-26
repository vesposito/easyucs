# coding: utf-8
# !/usr/bin/env python

""" export.py: Easy UCS Deployment Tool """
from easyucs import __author__, __copyright__,  __version__, __status__


import hashlib


def export_attributes_json(current_object, output_json):
    """
    Exports attributes of the given Object in JSON format in recursive fashion
    :return: nothing
    """
    try:
        if isinstance(current_object, dict):
            # We have a plain dictionary that is not an EasyUCS object
            for attribute in sorted(current_object.keys()):
                if not attribute.startswith('_') and not attribute == "dn" \
                        and current_object[attribute] is not None:
                    if not isinstance(current_object[attribute], list):
                        output_json[attribute] = current_object[attribute]
                    else:
                        if len(current_object[attribute]) == 0:
                            continue
                        output_json[attribute] = []
                        element_count = 0
                        for element in current_object[attribute]:
                            if not isinstance(element, (str, float, int)):
                                output_json[attribute].append({})
                                export_attributes_json(element, output_json[attribute][element_count])
                            else:
                                output_json[attribute].append(element)
                            element_count += 1
        else:
            # We have an EasyUCS object
            for attribute in sorted(vars(current_object)):
                if not attribute.startswith('_') and not attribute == "dn" \
                        and getattr(current_object, attribute) is not None:
                    if not isinstance(getattr(current_object, attribute), list):
                        output_json[attribute] = getattr(current_object, attribute)
                    else:
                        if len(getattr(current_object, attribute)) == 0:
                            continue
                        output_json[attribute] = []
                        element_count = 0
                        for element in getattr(current_object, attribute):
                            if not isinstance(element, (str, float, int)):
                                output_json[attribute].append({})
                                export_attributes_json(element, output_json[attribute][element_count])
                            else:
                                output_json[attribute].append(element)
                            element_count += 1

    except TypeError as err:
        print("Error while trying to export " + str(current_object) + ": " + str(err))


def generate_json_metadata_header(file_type=None, inventory=None, config=None, device=None, name=None, category=None,
                                  subcategory=None, url=None, revision=None):
    """
    Generates an easyucs metadata JSON header for an export file
    :param file_type: Export file type (e.g. "inventory", "config", "device")
    :param inventory: If the export file type is "inventory", this must contain the inventory to be exported
    :param config: If the export file type is "config", this must contain the config to be exported
    :param device: If the export file type is "device", this must contain the device to be exported
    :param name: Name of the export file
    :param category: Category of the export file (used to categorize config files)
    :param subcategory: Subcategory of the export file (used to categorize config files)
    :param url: Associated URL if applicable
    :param revision: Revision of the file if applicable
    :return: The metadata JSON header if successful, None otherwise
    """
    if file_type is None:
        return None
    if inventory is None and config is None and device is None:
        return None
    if file_type is "inventory" and inventory is None:
        return None
    if file_type is "config" and config is None:
        return None
    if file_type is "device" and device is None:
        return None

    json_metadata_header = {}
    json_metadata_header["file_type"] = file_type
    json_metadata_header["easyucs_version"] = __version__
    if name is not None:
        json_metadata_header["name"] = name
    if category is not None:
        json_metadata_header["category"] = category
    if subcategory is not None:
        json_metadata_header["subcategory"] = subcategory
    if url is not None:
        json_metadata_header["url"] = url
    if revision is not None:
        json_metadata_header["revision"] = revision

    if file_type is "inventory":
        json_metadata_header["uuid"] = str(inventory.uuid)
        json_metadata_header["timestamp"] = inventory.timestamp
        json_metadata_header["origin"] = inventory.origin
        json_metadata_header["device_uuid"] = str(inventory.parent.parent.uuid)
        json_metadata_header["device_type"] = inventory.parent.parent.device_type_short
        json_metadata_header["device_name"] = inventory.parent.parent.name
        if hasattr(inventory.parent.parent.version, "version"):
            json_metadata_header["device_version"] = inventory.parent.parent.version.version
        json_metadata_header["intersight_status"] = inventory.parent.parent.intersight_status
    elif file_type is "config":
        json_metadata_header["uuid"] = str(config.uuid)
        json_metadata_header["timestamp"] = config.timestamp
        json_metadata_header["origin"] = config.origin
        json_metadata_header["device_uuid"] = str(config.parent.parent.uuid)
        json_metadata_header["device_type"] = config.parent.parent.device_type_short
        json_metadata_header["device_name"] = config.parent.parent.name
        if hasattr(config.parent.parent.version, "version"):
            json_metadata_header["device_version"] = config.parent.parent.version.version
        json_metadata_header["intersight_status"] = config.parent.parent.intersight_status
    elif file_type is "device":
        json_metadata_header["device_uuid"] = str(device.uuid)
        json_metadata_header["device_type"] = device.device_type_short
        json_metadata_header["device_name"] = device.name
        if hasattr(device.version, "version"):
            json_metadata_header["device_version"] = device.version.version
        json_metadata_header["intersight_status"] = device.intersight_status

    return json_metadata_header


def insert_json_metadata_hash(json_content=None):
    """
    Inserts a SHA-256 hash of the supplied JSON file in the metadata header
    :param json_content: JSON file to be hashed
    :return: JSON content with inserted SHA-256 hash if successful, None otherwise
    """
    if json_content is None:
        return None

    if "easyucs" not in json_content:
        return None

    if "metadata" not in json_content["easyucs"]:
        return None

    json_content["easyucs"]["metadata"][0]["hash"] = hashlib.sha256(str(json_content).encode()).hexdigest()
    return json_content


def verify_json_metadata_hash(json_content=None):
    """
    Verifies the SHA-256 hash in the metadata header of the supplied JSON file
    :param json_content: JSON file containing the hash header
    :return: True if hash is verified, False otherwise
    """
    if json_content is None:
        return False

    if "easyucs" not in json_content:
        return False

    if "metadata" not in json_content["easyucs"]:
        return False

    if "hash" not in json_content["easyucs"]["metadata"][0]:
        return False

    file_hash = json_content["easyucs"]["metadata"][0]["hash"]
    json_content["easyucs"]["metadata"][0].pop("hash")

    calculated_hash = hashlib.sha256(str(json_content).encode()).hexdigest()

    if file_hash == calculated_hash:
        return True
    return False
