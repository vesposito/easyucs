# coding: utf-8
# !/usr/bin/env python

""" common.py: Easy UCS Deployment Tool """
from easyucs import __author__, __copyright__,  __version__, __status__


import ipaddress
import requests
import time
import sys
import urllib


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
        device.logger(level="debug", message="Trying to reconnect to " + url + " ...")
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
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")
