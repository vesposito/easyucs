# coding: utf-8
# !/usr/bin/env python

""" common.py: Easy UCS Deployment Tool """
import base64
import datetime
import hashlib
import ipaddress
import json
import jsonschema
import os
import re
import sys
import time
import tarfile
from collections import defaultdict
from cryptography.fernet import InvalidToken
from itertools import groupby, count

import natsort
import requests

from __init__ import EASYUCS_ROOT


def get_decoded_pem_certificate(certificate=None):
    """Method to decode the Base64 string
    :param certificate: base64 string
    :return: decoded base64 string if successful, None otherwise"""
    certificate_string = None
    if certificate is not None:
        base64_bytes = certificate.encode("ascii")
        certificate_string_bytes = base64.b64decode(base64_bytes)
        certificate_string = certificate_string_bytes.decode("ascii")
        return certificate_string


def get_encoded_pem_certificate(certificate=None):
    """Method to encode PEM format to Base64
    :param certificate: certificate in PEM format
    :return: encoded base64 string if successful, None otherwise"""
    base64_string = None
    if certificate is not None:
        certificate_string = certificate.encode("ascii")
        base64_bytes = base64.b64encode(certificate_string)
        base64_string = base64_bytes.decode("ascii")
        return base64_string


def calculate_checksum(file_path, algorithm="MD5"):
    """
    Calculates the MD5 Checksum of the file.
    :param file_path: File path for which MD5 Checksum is calculated
    :param algorithm: Algorithm which calculates the checksum
    :return: Checksum value if it's a file, None otherwise
    """
    if algorithm not in ["MD5", "SHA1", "SHA256"]:
        return None

    if os.path.isfile(file_path):
        if algorithm == "SHA1":
            checksum = hashlib.sha1()
        elif algorithm == "SHA256":
            checksum = hashlib.sha256()
        else:
            checksum = hashlib.md5()
        with open(file_path, "rb") as file:
            for chunk in iter(lambda: file.read(4096), b""):
                checksum.update(chunk)
        return checksum.hexdigest()
    else:
        return None


def check_web_page(device, url, str_match, timeout=20):
    """
    Checks Web page for presence of specific string
    :param device: device for which we need to check a web page (used for logger)
    :param url: URL to check
    :param str_match: string content to check for at the given URL
    :param timeout: time in seconds above which the check will be considered failed
    :return: True if check is successful, False if timeout exceeded
    """
    device.logger(level="debug", message="Checking status of " + url)

    # Disable requests warnings about HTTPS
    requests.packages.urllib3.disable_warnings()

    start = time.time()

    while (time.time() - start) < timeout:
        try:
            page = requests.get(url, verify=False, timeout=3)
            if page.text.find(str_match) != -1:
                device.logger(level="debug", message="Found '" + str_match + "' at " + url)
                return True
        except requests.exceptions.ConnectionError:
            pass
        except requests.exceptions.Timeout:
            pass
        device.logger(
            level="debug", message="Trying to reconnect to " + url + " ...")
        time.sleep(10)
    return False


def is_ip_address_valid(ip_address):
    """
    Validates that the given string is a valid IP address format
    :param ip_address: string containing IP address to validate
    :return: True if IP address is valid, False otherwise
    """
    try:
        ipaddress.ip_address(ip_address)
        return True
    except ValueError:
        return False


def is_ipv4_address_valid(ip_address):
    """
    Validates that the given string is a valid IPv4 address format
    :param ip_address: string containing IP address to validate
    :return: True if IP address is a valid IPv4 address, False otherwise
    """
    try:
        result = ipaddress.ip_address(ip_address)
        if isinstance(result, ipaddress.IPv4Address):
            return True
        return False
    except ValueError:
        return False


def is_ipv6_address_valid(ip_address):
    """
    Validates that the given string is a valid IPv6 address format
    :param ip_address: string containing IP address to validate
    :return: True if IP address is a valid IPv6 address, False otherwise
    """
    try:
        result = ipaddress.ip_address(ip_address)
        if isinstance(result, ipaddress.IPv6Address):
            return True
        return False
    except ValueError:
        return False


def get_timestamp():
    """
    This function returns the time stamp as a formatted string
    """
    from datetime import datetime
    return (((datetime.now().strftime("%Y-%m-%d %H:%M:%S")).replace(" ", "_")).replace(":", "_")).replace("-", "_")


def query_yes_no(question, default="no"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}

    # Normal behavior
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        # Invalid default value
        prompt = " [y/n] "

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' (or 'y' or 'n').\n")


def read_json_file(file_path=None, logger=None):
    """
    Opens a JSON file and returns its parsed content as a dictionary
    :param file_path: The relative path to the file that needs to be opened
    :param logger: The associated object to get access to the logger
    :return: JSON parsed content as dict if successful, None otherwise
    """
    if not file_path:
        if logger:
            logger.logger(level="warning", message="No file path given")
        return None

    try:
        full_path = os.path.abspath(os.path.join(EASYUCS_ROOT, file_path))
        if os.path.isfile(full_path):
            json_file = open(full_path, "r")
            file_contents = json.load(fp=json_file)
            json_file.close()
            return file_contents

    except FileNotFoundError:
        if logger:
            logger.logger(level="warning", message="File " + str(file_path) + " not found")
        return None

    return None


def format_descr(descr_str):
    """
    Translates any special character in Description String of Policy/Profile
    :param descr_str: Description of a policy/profile in str format
    :return: Formatted Description String
    """
    if descr_str:
        return re.sub(r"^[^A-Za-z0-9]+", "", descr_str)
    else:
        return None


def _as_range(iterable):
    """
    Accepts the iterable and returns the output in the format '4-5' or '4'
    """
    l = list(iterable)
    if len(l) > 1:
        return '{0}-{1}'.format(l[0], l[-1])
    else:
        return '{0}'.format(l[0])


def convert_to_range(num_list, sep=",", logger=None):
    """
    Converts the List of Numbers or a String containing only numbers into
    a string of range of numbers

    Input #1: [1,2,3,4,11,15,16,17]     Output: "1-4,11,15-17" 
    Input #2: ["1","11",15,16,17]       Output: "1,11,15-17" 
    Input #3: "1,2,3,4,11,15,16,17"     Output: "1-4,11,15-17"
    Input #4: "1-2-3-4-11-15-16-17"     Output: "1-4,11,15-17" 

    Args:
        num_list (str, list): List of Numbers or a String containing only numbers
        sep (str, optional): Separator to split the string. Defaults to ",".
        logger (logger, optional): Logger to print/log the message. Defaults to None.
    """
    # Returns the input if the num_list is of type other than String and List
    if (not isinstance(num_list, list)) and (not isinstance(num_list, str)):
        if logger:
            logger.logger(level="warning", message=("Conversion to range is not "
                                                    + "possible since the input is neither a list nor a string"))
        return num_list

    # Handling the string which has comma separated numbers
    # e.g., "1,2,5,6,7,88"
    if isinstance(num_list, str):
        num_list = num_list.split(sep)

    # Returns the input if the list contains any non-digit item.
    if not all([str(x).isdigit() for x in num_list]):
        if logger:
            logger.logger(level="warning", message=(f"Conversion to range is not possible as the list contains "
                                                    f"non-digit items: {num_list}. Proceeding without the non digit "
                                                    f"values."))
        num_list = [num for num in num_list if str(num).isdigit()]

    # Converting all the elements of a list to integer type. Also removing duplicate entries
    num_list = list(set([int(num) for num in num_list]))
    return(','.join(_as_range(iterable) for _, iterable in groupby(
        sorted(num_list), key=lambda num, c=count(): num-next(c))))


def format_network_ports(network_ports=[], logger=None):
    """
    Formats the list of network ports to range

    Input: [{'slot_id': 1, 'port_id': 7, 'aggr_id': 1}, {'slot_id': 1, 'port_id': 7, 'aggr_id': 2}, 
            {'slot_id': 1, 'port_id': 7, 'aggr_id': 5}, {'slot_id': 1, 'port_id': 7, 'aggr_id': 6}, 
            {'slot_id': 1, 'port_id': 11, 'aggr_id': None}, {'slot_id': 1, 'port_id': 12, 'aggr_id': None}, 
            {'slot_id': 1, 'port_id': 13, 'aggr_id': None}, {'slot_id': 1, 'port_id': 14, 'aggr_id': None}, 
            {'slot_id': 1, 'port_id': 17, 'aggr_id': None}, {'slot_id': 1, 'port_id': 18, 'aggr_id': None}, 
            {'slot_id': 1, 'port_id': 19, 'aggr_id': None}, {'slot_id': 1, 'port_id': 20, 'aggr_id': None}]

    Output: ['1/7/1-2', '1/7/5-6', '1/11-14', '1/17-20']

    Args:
        network_ports (list): List of dictionaries, where the keys of each dictionary 
        will be slot_id, port_id and aggr_id
        logger (logger, optional): Logger to print/log the message. Defaults to None.
    """
    if not network_ports:
        return []

    interfaces_list = []
    for port_dict in network_ports:
        slot_id = port_dict["slot_id"]
        port_id = port_dict["port_id"]
        aggr_id = port_dict.get("aggr_id", None)
        interfaces_list.append((slot_id, port_id, aggr_id))

    # https://stackoverflow.com/questions/35007794/creating-a-nested-dictionary-from-a-list-of-tuples
    # Creating a nested dictionary from a list of tuples
    # Input - [(1,7,1), (1,7,2), (1,7,5), (1,7,6), (1,11,None), (1,12,None), (1,13,None),
    #          (1,14,None), (1,11,None), (1,17,None), (1,18,None), (1,19,None), (1,20,None)]
    # Output - {1: {7: [1,2,5,6]}, {11:[]}, {12:[]}, {13:[]}, {14:[]}, {17:[]}, {18:[]}, {19:[]}, {20:[]}}
    interfaces_dict = defaultdict(dict)
    for slot_id, port_id, aggr_id in interfaces_list:
        if port_id not in interfaces_dict[slot_id]:
            interfaces_dict[slot_id][port_id] = [aggr_id]
        else:
            interfaces_dict[slot_id][port_id].append(aggr_id)

    formatted_network_ports = []
    for slot_id, port_aggr_dict in interfaces_dict.items():
        ports_list = []
        for port_id, aggr_id in port_aggr_dict.items():
            if all([x is None for x in aggr_id]):
                # For ports like 1/2, 3/5
                ports_list.append(port_id)
            elif len(aggr_id) == 1:
                # For ports like 1/2/1, 1/3/2
                formatted_network_ports.append(str(slot_id) + "/" + str(port_id) + "/" + str(aggr_id[0]))
            elif len(aggr_id) > 1:
                # For ports like 1/7/1-2, 1/7/5-6
                nested_merged_ports = convert_to_range(aggr_id, logger=logger)
                for nested_port in nested_merged_ports.split(","):
                    formatted_network_ports.append(str(slot_id) + "/" + str(port_id) + "/" + str(nested_port))

        merged_ports = convert_to_range(ports_list)
        for port in merged_ports.split(","):
            formatted_network_ports.append(str(slot_id) + "/" + port)

    return natsort.natsorted(formatted_network_ports)


def find_by_key(data, key_to_find):
    """
    This function will return all the values of a specific key by scanning through the entire dictionary

    Args:
        data (dict): Dictionary
        key_to_find (str): Key of a dictionary whose value has to be returned
    Yields:
        [str/list]: Yields the value of key in String or List format
    """
    for key, value in data.items():
        if key == key_to_find:
            if isinstance(value, dict):
                yield value.keys()
            else:
                yield value
        elif isinstance(value, dict):
            yield from find_by_key(value, key_to_find)


def validate_json(json_data=None, schema_path=None, logger=None):
    """
    Validates JSON data using the JSON schema definition
    :param json_data: JSON content to be validated
    :param schema_path: Schema path of the JSON data
    :param logger: Logger to print/log the message. Defaults to None
    :return: True if json_data is valid, False otherwise
    """
    if not schema_path:
        if logger:
            logger.logger(level="error", message="Missing schema path!")
        return False

    if not json_data:
        if logger:
            logger.logger(level="error", message="Missing JSON content to validate!")
        return False

    # Open JSON master schema
    json_schema = read_json_file(file_path=schema_path, logger=logger)

    master_schema_path = os.path.abspath(os.path.join(EASYUCS_ROOT, schema_path))
    full_schema_path = 'file:///{0}/'.format(os.path.dirname(master_schema_path).replace("\\", "/"))

    resolver = jsonschema.RefResolver(full_schema_path, json_schema)
    format_checker = jsonschema.FormatChecker()

    try:
        jsonschema.validate(json_data, json_schema, resolver=resolver, format_checker=format_checker)
        return True

    except jsonschema.ValidationError as err:
        absolute_path = []
        for full_schema_path in err.absolute_path:
            absolute_path.append(full_schema_path)
        if logger:
            logger.logger(level="error", message="Failed to validate JSON data at " + str(absolute_path))
            logger.logger(level="error",
                          message="Failed to validate JSON data due to schema error: " + str(err.message))
        return False

    except jsonschema.SchemaError as err:
        if logger:
            logger.logger(level="error", message="Failed to validate JSON data due to schema error: " + str(err))
        return False

    except Exception as err:
        if logger:
            logger.logger(level="error", message="Error in validating JSON data: " + str(err))
        return False


def password_generator(
        password_length, min_uppercase=1, min_lowercase=1, min_digits=1, min_special_chars=1, logger=None):
    """
    Generates Random password
    :param password_length: The length of the password
    :param min_uppercase: Minimum number of uppercase characters in the password, Defaults to 1
    :param min_lowercase: Minimum number of lowercase characters in the password, Defaults to 1
    :param min_digits: Minimum number of digits in the password, Defaults to 1
    :param min_special_chars: Minimum number of special characters in the password, Defaults to 1
    :param logger (logger, optional): Logger to print/log the message. Defaults to None
    :return: Randomly generated password with specified parameters
    """
    import string
    import secrets
    import random

    if password_length - min_digits - min_uppercase - min_lowercase - min_special_chars < 0:
        logger.logger(level="error", message="Minimum number of specific characters is greater than the overall "
                                             "password length")
        return False

    # A string of allowed punctuations
    allowed_punctuation = r"""!@#$%^&\*+-_="""

    random_source = string.ascii_letters + string.digits + allowed_punctuation
    password = ''.join((secrets.choice(string.ascii_lowercase)) for i in range(min_lowercase))
    password += ''.join((secrets.choice(string.ascii_uppercase)) for i in range(min_uppercase))
    password += ''.join((secrets.choice(string.digits)) for i in range(min_digits))
    password += ''.join((secrets.choice(allowed_punctuation)) for i in range(min_special_chars))

    for i in range(password_length-min_digits-min_uppercase-min_lowercase-min_special_chars):
        password += secrets.choice(random_source)

    password_list = list(password)
    # shuffle all characters
    random.SystemRandom().shuffle(password_list)
    password = ''.join(password_list)
    return password


def generate_self_signed_cert():
    """
    Generates a self-signed certificate
    return: private_key, certificate
    """
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes

    # Generate our key
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096,
    )

    # Various details about who we are. For a self-signed certificate the
    # subject and issuer are always the same.
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, u"US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"California"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, u"San Francisco"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"My Company"),
        x509.NameAttribute(NameOID.COMMON_NAME, u"mysite.com"),
    ])
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.utcnow()
    ).not_valid_after(
        # Our certificate will be valid for 10 days
        datetime.datetime.utcnow() + datetime.timedelta(days=10)
    )
    # Sign the CSR with our private key.
    cert = cert.sign(key, hashes.SHA512())

    private_key = key.private_bytes(encoding=serialization.Encoding.PEM, format=serialization.PrivateFormat.PKCS8,
                                    encryption_algorithm=serialization.NoEncryption()).decode('utf-8')
    certificate = cert.public_bytes(serialization.Encoding.PEM).decode('utf-8')

    return private_key, certificate


def encrypt(data=None, fernet=None, logger=None):
    """
    Function to encrypt the data
    :param data: Bytes data to be encrypted
    :param fernet: A Fernet key which encrypts the data
    :param logger: Logger object to log error message
    :return: Encrypted data if successful, None otherwise
    """
    if not data:
        if logger:
            logger.logger(level="error", message="Data argument missing")
        return None
    if not fernet:
        if logger:
            logger.logger(level="error", message="Fernet argument missing")
        return None
    try:
        # Encrypt the data using Fernet
        encrypted_data = fernet.encrypt(data)
    except InvalidToken:
        if logger:
            logger.logger(level="error", message="Invalid key for decrypting the tar file")
        return None
    return encrypted_data


def decrypt(data=None, fernet=None, logger=None):
    """
    Function to decrypt the data
    :param data: Bytes data to be decrypted
    :param fernet: A Fernet key which decrypts the data
    :param logger: Logger object to log error message
    :return: Decrypted data if successful, None otherwise
    """
    if not data:
        if logger:
            logger.logger(level="error", message="Data argument missing")
        return None
    if not fernet:
        if logger:
            logger.logger(level="error", message="Fernet argument missing")
        return None
    try:
        # Decrypt the data using Fernet
        decrypted_data = fernet.decrypt(data)
    except InvalidToken:
        if logger:
            logger.logger(level="error", message="Invalid key for decrypting the tar file")
        return None
    return decrypted_data


def extract(tar_file=None, file_name=None, destination_path=EASYUCS_ROOT, logger=None):
    """
    Function to extract all or single file from the tarfile
    :param tar_file: Path to the tar file which needs to be extracted
    :param file_name: Name of the file to be extracted
    :param destination_path: Path where the files are extracted. EASYUCS_ROOT by default
    :param logger: Logger object to log error message
    :return: True if successful, False otherwise
    """
    if not tar_file:
        if logger:
            logger.logger(level="error", message="Tar file argument missing")
        return False

    # Extract and decrypt members in the current directory
    with tarfile.open(name=tar_file, mode='r:gz') as tar:
        # If the file name is specified then we extract only the file name, otherwise we extract everything.
        if file_name:
            for member in tar.getmembers():
                if member.name.endswith(file_name):
                    tar.extract(member=member, path=destination_path)
                    if logger:
                        logger.logger(level="debug",
                                      message=f"File {file_name} extracted successfully from the {tar_file}")
        else:
            tar.extractall(path=destination_path)
            if logger:
                logger.logger(level="debug", message=f"All contents of {tar_file} extracted successfully")
    return True


def identity_in_range(identity_type=None, start=None, end=None, identity=None):
    """
    Function to check whether an identity is a part of a range
    :param identity_type: Type of the identity
    :param start: Start of the range of identities
    :param end: End of the range of identities
    :param identity: Identity whose presence needs to be checked in the range
    :return: True if identity in range, False otherwise
    """
    if identity_type == "iqn":
        return start <= identity <= end
    elif identity_type == "ip":
        if not ipaddress.ip_address(identity).__class__.__name__ == ipaddress.ip_address(start).__class__.__name__ \
                == ipaddress.ip_address(end).__class__.__name__:
            return False
        if isinstance(ipaddress.ip_address(identity), ipaddress.IPv4Address):
            return ipaddress.IPv4Address(start) <= ipaddress.IPv4Address(identity) <= ipaddress.IPv4Address(end)
        elif isinstance(ipaddress.ip_address(identity), ipaddress.IPv6Address):
            return ipaddress.IPv6Address(start) <= ipaddress.IPv6Address(identity) <= ipaddress.IPv6Address(end)
    elif identity_type in ["mac", "uuid", "wwnn", "wwpn", "wwxn"]:
        return start.upper() <= identity.upper() <= end.upper()
    return False
