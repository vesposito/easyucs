# coding: utf-8
# !/usr/bin/env python

""" easyucs.py: Easy UCS Deployment Tool """
import argparse
import os
import sys
import time

from imcsdk.imchandle import ImcHandle
from ucsmsdk.ucshandle import UcsHandle

import common
from __init__ import __author__, __copyright__, __version__
from device.intersight.device import IntersightDevice
from device.ucs.device import UcsImc, UcsSystem, UcsCentral

OUTPUT_DIRECTORY = "temp"


def instantiate_device(args):
    """
    Instantiates a Device, depending on the arguments provided
    :param args: Command-line arguments provided (argparse format)
    :return: Device if creation is successful, None otherwise
    """

    # Set logger values
    logger_handle_log_level = "info"
    log_file_path = None
    if args.log:
        logger_handle_log_level = "debug"
    if args.logfile:
        log_file_path = args.logfile

    target = ""
    username = ""
    password = ""
    api_key = ""
    secret_key_path = ""

    if args.ip:
        target = args.ip
    if args.username:
        username = args.username
    if args.password:
        password = args.password
    if args.api_key:
        api_key = args.api_key
    if args.secret_key_path:
        secret_key_path = args.secret_key_path

    device = None
    if args.device_type:
        if args.device_type == "ucsm":
            device = UcsSystem(target=target, user=username, password=password,
                               logger_handle_log_level=logger_handle_log_level, log_file_path=log_file_path)
            device.logger(level="debug", message="Created UcsSystem device with target: " + target)
        elif args.device_type == "cimc":
            device = UcsImc(target=target, user=username, password=password,
                            logger_handle_log_level=logger_handle_log_level, log_file_path=log_file_path)
            device.logger(level="debug", message="Created UcsImc device with target: " + target)
        elif args.device_type == "ucsc":
            device = UcsCentral(target=target, user=username, password=password,
                                logger_handle_log_level=logger_handle_log_level, log_file_path=log_file_path)
            device.logger(level="debug", message="Created UcsCentral device with target: " + target)
        elif args.device_type == "intersight":
            device = IntersightDevice(target=target, key_id=api_key, private_key_path=secret_key_path,
                                      logger_handle_log_level=logger_handle_log_level, log_file_path=log_file_path)
            device.logger(level="debug", message="Created Intersight device with target: " + target)
    else:
        print("Error: Could not determine device type!")
        return None

    return device


def init_process(device, args, config_string):
    """
    Performs initial processing of EasyUCS, depending on the arguments provided
    :param device: Device to be used for processing
    :param args: Command-line arguments provided (argparse format)
    :param config_string: The config content
    :return: True if successful, False otherwise
    """

    bypass_version_checks = False
    if args.yes:
        bypass_version_checks = True

    device.set_task_progression(1)
    if args.scope == "config" and args.action == "push":
        # Adding configuration to the created Device
        if config_string:
            if not device.config_manager.import_config(config=config_string):
                exit()
            config = device.config_manager.get_latest_config()

        # If we are doing a complete reset/setup cycle, we use the push_config method with the "reset" argument
        if args.setup and args.reset:
            if not args.yes:
                if not common.query_yes_no("Are you sure you want to erase all configuration on " + device.name +
                                           "?"):
                    # User declined configuration erase query
                    # FIXME: handle proper disconnection if required
                    exit()

            if device.__class__.__name__ == "UcsImc":
                device.config_manager.push_config(reset=True, imc_ip=args.setup[0],
                                                  bypass_version_checks=bypass_version_checks)
            elif device.__class__.__name__ == "UcsSystem":
                device.config_manager.push_config(reset=True, fi_ip_list=args.setup,
                                                  bypass_version_checks=bypass_version_checks)

        # If we are not doing a complete reset/setup cycle, we perform each action separately
        else:
            if args.reset:
                if not args.yes:
                    if not common.query_yes_no("Are you sure you want to erase all configuration on " +
                                               device.name + "?"):
                        # User declined configuration erase query
                        # FIXME: handle proper disconnection if required
                        exit()

                # Executing reset action
                if not device.reset(bypass_version_checks=bypass_version_checks):
                    device.logger(level="error", message="Error while performing device reset")
                    exit()

            if args.setup:
                device.logger(level="debug", message="Performing initial setup with IP " + str(args.setup[0]))
                if device.__class__.__name__ == "UcsImc":
                    if not device.initial_setup(imc_ip=args.setup[0], config=config,
                                                bypass_version_checks=bypass_version_checks):
                        device.logger(level="error", message="Error while performing initial setup on UCS IMC")
                        exit()

                    # We now need to get the new IP address and admin password from the configuration
                    imc_target_ip_address = ""
                    if config.admin_networking[0].management_ipv4_address:
                        imc_target_ip_address = config.admin_networking[0].management_ipv4_address
                    else:
                        device.logger(level="error",
                                      message="Could not find Management IP address of UCS IMC in the config")
                        exit()

                    if not config.local_users:
                        device.logger(level="error", message="Could not find local_users in the config")
                        exit()

                    # Going through all users to find admin
                    target_admin_password = ""
                    for user in config.local_users:
                        if user.username:
                            if user.username == "admin":
                                if user.password:
                                    target_admin_password = user.password
                                else:
                                    # Admin password is a mandatory input - Exiting
                                    device.logger(level="error",
                                                  message="Could not find password for user id admin in the config")
                                    exit()

                    # We went through all users - Making sure we got the information we needed
                    if not target_admin_password:
                        device.logger(level="error", message="Could not find user id admin in the config")
                        exit()

                    # We need to refresh the device handle so that it has the right attributes
                    device.handle = ImcHandle(ip=imc_target_ip_address, username="admin",
                                              password=target_admin_password)

                    # Changing handle to the new one
                    config.refresh_config_handle()

                    device.logger(level="debug",
                                  message="Waiting for the IMC to come back with the IP " + imc_target_ip_address)
                    if not device.wait_for_reboot_after_reset(timeout=60, imc_ip=imc_target_ip_address):
                        exit()

                elif device.__class__.__name__ == "UcsSystem":
                    if len(args.setup) == 2:
                        device.sys_mode = "cluster"
                    elif len(args.setup) == 1:
                        device.sys_mode = "stand-alone"
                    if not device.initial_setup(fi_ip_list=args.setup, config=config):
                        device.logger(level="error", message="Error while performing initial setup on UCS System")
                        exit()

                    # We now need to wait to be able to configure the device using the configuration
                    if device.sys_mode == "cluster":
                        device.logger(message="Waiting up to 240 seconds for cluster election to complete")
                        time.sleep(80)
                        if config.system:
                            if config.system[0].virtual_ip:
                                device.target = config.system[0].virtual_ip
                            elif config.system[0].virtual_ipv6:
                                device.target = config.system[0].virtual_ipv6
                        if not device.target:
                            device.logger(level="error",
                                          message="Could not determine target IP of the device in the config")
                            exit()

                    elif device.sys_mode == "stand-alone":
                        device.logger(message="Waiting up to 180 seconds for initial configuration to complete")
                        time.sleep(20)

                        # TODO Handle Ipv6
                        if config.management_interfaces:
                            for management_interface in config.management_interfaces:
                                if management_interface.fabric.upper() == 'A':
                                    if management_interface.ip:
                                        device.target = management_interface.ip

                        if not device.target:
                            device.logger(level="error",
                                          message="Could not determine target IP of the device in the config")
                            exit()

                    if not config.local_users:
                        # Could not find local_users in config - Admin password is a mandatory parameter - Exiting
                        device.logger(level="error", message="Could not find local_users in the config")
                        exit()

                    # Going through all users to find admin
                    for user in config.local_users:
                        if user.id:
                            if user.id == "admin":
                                device.username = "admin"
                                if user.password:
                                    device.password = user.password
                                else:
                                    # Admin password is a mandatory input
                                    device.logger(level="error",
                                                  message="Could not find password for user id admin in the config")
                                    exit()

                    # We need to refresh the device handle so that it has the right attributes
                    device.handle = UcsHandle(ip=device.target, username=device.username,
                                              password=device.password)

                    # We also need to refresh the config handle
                    config.refresh_config_handle()

                    if not common.check_web_page(device=device, url="https://" + device.target,
                                                 str_match="Cisco", timeout=160):
                        device.logger(level="error", message="Impossible to reconnect to UCS system")
                        exit()

                    # Reconnecting and waiting for HA cluster to be ready (if in cluster mode)
                    if not device.connect(bypass_version_checks=bypass_version_checks, retries=3):
                        device.logger(level="error", message="Impossible to reconnect to UCS system")
                        exit()

                    # Bypass version checks for the rest of the procedure as potential warnings have already been made
                    bypass_version_checks = True

                    if device.sys_mode == "cluster":
                        device.logger(message="Waiting up to 300 seconds for UCS HA cluster to be ready...")
                        if not device.wait_for_ha_cluster_ready(timeout=300):
                            device.logger(
                                level="error",
                                message="Timeout exceeded while waiting for UCS HA cluster to be in ready state")
                            exit()
                    elif device.sys_mode == "stand-alone":
                        device.logger(message="Waiting up to 300 seconds for UCS stand-alone FI to be ready...")
                        if not device.wait_for_standalone_fi_ready(timeout=300):
                            device.logger(
                                level="error",
                                message="Timeout exceeded while waiting for UCS stand-alone FI to be ready")
                            exit()

            if config_string:
                device.config_manager.push_config(bypass_version_checks=bypass_version_checks)

    elif args.scope == "config" and args.action == "fetch":
        # Fetching config from live Device
        if not device.connect(bypass_version_checks=bypass_version_checks):
            device.logger(level="error", message="Failed to connect to device")
            exit()
        device.config_manager.fetch_config()
        device.set_task_progression(50)

        # Exporting config to specified output config file
        directory = os.path.dirname(args.output_config)
        filename = os.path.basename(args.output_config)
        device.config_manager.export_config(directory=directory, filename=filename)

    elif args.scope == "inventory" and args.action == "fetch":
        # Fetching inventory from live Device
        if not device.connect(bypass_version_checks=bypass_version_checks):
            device.logger(level="error", message="Failed to connect to device")
            exit()
        device.inventory_manager.fetch_inventory()
        device.set_task_progression(50)

        # Exporting inventory to specified output config file
        directory = os.path.dirname(args.output_inventory)
        filename = os.path.basename(args.output_inventory)
        device.inventory_manager.export_inventory(directory=directory, filename=filename)

    elif args.scope == "schemas" and args.action == "create":
        # Fetching inventory from live Device and create schemas of it
        if not device.connect(bypass_version_checks=bypass_version_checks):
            device.logger(level="error", message="Failed to connect to device")
            exit()
        device.inventory_manager.fetch_inventory()
        device.set_task_progression(50)

        device.inventory_manager.draw_inventory()
        device.set_task_progression(75)

        directory = args.output_directory
        device.inventory_manager.export_draw(directory=directory, export_clear_pictures=args.clear_pictures)

    elif args.scope == "report" and args.action == "generate":
        # Fetching inventory from live Device, create schemas and generate report of it
        if not device.connect(bypass_version_checks=bypass_version_checks):
            device.logger(level="error", message="Failed to connect to device")
            exit()

        device.config_manager.fetch_config()
        device.set_task_progression(25)

        device.inventory_manager.fetch_inventory()
        device.set_task_progression(50)

        # Exporting report to specified output directory
        directory = args.output_directory

        # Exporting inventory & config to JSON files
        device.inventory_manager.export_inventory(directory=directory, filename="inventory_" + device.target + ".json")
        device.config_manager.export_config(directory=directory, filename="config_" + device.target + ".json")
        device.set_task_progression(60)

        device.inventory_manager.draw_inventory()
        device.set_task_progression(75)

        device.inventory_manager.export_draw(directory=directory, export_clear_pictures=True)
        device.set_task_progression(80)

        if device.metadata.device_type == "ucsm":
            device.config_manager.generate_config_plots()
            device.config_manager.export_config_plots(directory=directory)
            device.set_task_progression(90)

        if args.layout:
            device.report_manager.generate_report(directory=directory, page_layout=args.layout)
        else:
            device.report_manager.generate_report(directory=directory)
        device.report_manager.export_report(filename="report_" + device.target, directory=directory)

    elif args.scope == "device" and args.action == "regenerate_certificate":
        # Regenerating self-signed certificate of Device if expired
        if not device.connect(bypass_version_checks=bypass_version_checks):
            device.logger(level="error", message="Failed to connect to device")
            exit()

        device.set_task_progression(10)
        if device.is_default_keyring_certificate_expired():
            device.set_task_progression(25)
            device.regenerate_default_keyring_certificate()
        else:
            if not args.yes:
                if not common.query_yes_no("Default keyring certificate is still valid. " +
                                           "Are you sure you want to regenerate it on " + device.name + "?"):
                    # User declined regenerate certificate query
                    device.logger(level="warning", message="The default keyring certificate is still valid. " +
                                                           "Skipping regenerate operation.")
                    exit()

            device.regenerate_default_keyring_certificate()

    elif args.scope == "device" and args.action == "clear_sel_logs":
        # Clears SEL Logs of all discovered servers of UCS Device
        if not device.connect(bypass_version_checks=bypass_version_checks):
            device.logger(level="error", message="Failed to connect to device")
            exit()

        device.set_task_progression(10)
        device.clear_sel_logs()

    elif args.scope == "device" and args.action == "clear_user_sessions":
        # Clears all user sessions of Device
        device.set_task_progression(10)
        device.clear_user_sessions()

    elif args.scope == "device" and args.action == "clear_intersight_claim_status":
        # Clears Intersight Claim Status of Device
        device.set_task_progression(10)
        device.clear_intersight_claim_status()

    elif args.scope == "device" and args.action == "get_device_connector_status":
        # Get Intersight info of Device
        from tabulate import tabulate

        device.set_task_progression(10)
        if not device.connect(bypass_version_checks=bypass_version_checks):
            device.logger(level="error", message="Failed to connect to device")
            exit()
        device.disconnect()
        print("Intersight Device Connector Status")
        print(tabulate(device._device_connector_info.items(), tablefmt="fancy_grid"))

    device.set_task_progression(100)
    device.print_logger_summary()


def main():
    # Example texts for parser
    example_text = '''Examples:
      To see examples, please type: python easyucs.py {config, inventory, schemas, report, device} -h'''

    example_config_text = '''Examples:
      python easyucs.py config fetch -t ucsm -i 192.168.0.1 -u admin -p password -o configs/config_ucsm.json
            fetch config from UCS system and save it to configs/config_ucsm.json

      python easyucs.py config fetch -t intersight -a "211e44297564712d361b8426/211e44297565612d331b842a/211e44a97565612d32a8cea3" -k ./SecretKey.txt -o configs/config_intersight.json
            fetch config from Intersight and save it to configs/config_intersight.json

      python easyucs.py config push -t ucsm -i 192.168.0.1 -u admin -p password -f configs/config_ucsm.json
            push config file config_ucsm.json to UCS system

      python easyucs.py config push -t cimc -i 192.168.0.2 -u admin -p password -f configs/config_cimc.json -r
            reset UCS IMC and push config file config_cimc.json

      python easyucs.py config push -t ucsm -f configs/config_ucsm.json -r -s 192.168.0.11 192.168.0.12
            reset UCS system, perform initial setup using DHCP IP addresses 192.168.0.11 & 192.168.0.12 and push config file config_ucsm.json'''

    example_config_fetch_text = '''Examples:
      python easyucs.py config fetch -t ucsm -i 192.168.0.1 -u admin -p password -o configs/config_ucsm.json
            fetch config from UCS system and save it to configs/config_ucsm.json

      python easyucs.py config fetch -t intersight -a "211e44297564712d361b8426/211e44297565612d331b842a/211e44a97565612d32a8cea3" -k ./SecretKey.txt -o configs/config_intersight.json
            fetch config from Intersight and save it to configs/config_intersight.json

      python easyucs.py config fetch -t cimc -i 192.168.0.2 -u admin -p password -o configs/config_cimc.json
            fetch config from UCS IMC and save it to configs/config_cimc.json'''

    example_config_push_text = '''Examples:
      python easyucs.py config push -t ucsm -i 192.168.0.1 -u admin -p password -f configs/config_ucsm.json
            push config file config_ucsm.json to UCS system

      python easyucs.py config push -t intersight -a "211e44297564712d361b8426/211e44297565612d331b842a/211e44a97565612d32a8cea3" -k ./SecretKey.txt -f configs/config_intersight.json
            push config file config_intersight.json to Intersight

      python easyucs.py config push -t cimc -i 192.168.0.2 -u admin -p password -f configs/config_cimc.json -r
            reset UCS IMC and push config file config_cimc.json

      python easyucs.py config push -t ucsm -f configs/config_ucsm.json -r -s 192.168.0.11 192.168.0.12
            reset UCS system, perform initial setup using DHCP IP addresses 192.168.0.11 & 192.168.0.12 and push config file config_ucsm.json'''

    example_inventory_fetch_text = '''Examples:
      python easyucs.py inventory fetch -t ucsm -i 192.168.0.1 -u admin -p password -o inventories/inventory_ucsm.json
            fetch inventory from UCS system and save it to inventories/inventory_ucsm.json

      python easyucs.py inventory fetch -t cimc -i 192.168.0.2 -u admin -p password -o inventories/inventory_cimc.json
            fetch inventory from UCS IMC and save it to inventories/inventory_cimc.json'''

    example_schemas_create_text = '''Examples:
      python easyucs.py schemas create -t ucsm -i 192.168.0.1 -u admin -p password -o schemas
            create schemas from UCS system and save them to schemas folder

      python easyucs.py schemas create -t cimc -i 192.168.0.2 -u admin -p password -o schemas
            create schemas from UCS IMC and save them to schemas folder'''

    example_report_generate_text = '''Examples:
      python easyucs.py report generate -t ucsm -i 192.168.0.1 -u admin -p password -o reports
            create schemas and report.docx from UCS system and save it to reports/

      python easyucs.py report generate -t cimc -i 192.168.0.2 -u admin -p password -o reports
            create schemas and report.docx from UCS IMC and save it to reports/'''

    example_device_text = '''Examples:
      python easyucs.py device regenerate_certificate -t ucsm -i 192.168.0.1 -u admin -p password
            regenerate self-signed certificate of UCS system

      python easyucs.py device clear_sel_logs -t ucsm -i 192.168.0.1 -u admin -p password
            clear SEL Logs of all discovered servers of UCS system'''

    example_device_regenerate_certificate_text = '''Examples:
      python easyucs.py device regenerate_certificate -t ucsm -i 192.168.0.1 -u admin -p password
            regenerate self-signed certificate of UCS system if it has expired'''

    example_device_clear_sel_logs_text = '''Examples:
      python easyucs.py device clear_sel_logs -t ucsm -i 192.168.0.1 -u admin -p password
            clear SEL Logs of all discovered servers of UCS system

      python easyucs.py device clear_sel_logs -t cimc -i 192.168.0.2 -u admin -p password
            clear SEL Log of UCS IMC device'''

    example_device_clear_user_sessions_text = '''Examples:
      python easyucs.py device clear_user_sessions -t ucsm -i 192.168.0.1 -u admin -p password
            clear all user sessions of UCS System

      python easyucs.py device clear_user_sessions -t cimc -i 192.168.0.2 -u admin -p password
            clear all user sessions of UCS IMC

      python easyucs.py device clear_user_sessions -t ucsc -i 192.168.0.3 -u admin -p password
            clear all user sessions of UCS Central'''

    example_device_clear_intersight_claim_status_text = '''Examples:
          python easyucs.py device clear_intersight_claim_status -t ucsm -i 192.168.0.1 -u admin -p password
                clear intersight claim status of UCS System
          python easyucs.py device clear_intersight_claim_status -t cimc -i 192.168.0.2 -u admin -p password
                clear intersight claim status of IMC System
          '''

    example_device_get_device_connector_status_text = '''Examples:
              python easyucs.py device get_device_connector_status -t ucsm -i 192.168.0.1 -u admin -p password
                    clear intersight claim status of UCS System
              python easyucs.py device get_device_connector_status -t cimc -i 192.168.0.2 -u admin -p password
                    clear intersight claim status of IMC System
              '''

    # Introduction message
    print("\n" + "EasyUCS " + __version__ + " created by " + __author__ + ", " + __copyright__ + "\n")
    # Create the main parser
    parser = argparse.ArgumentParser(prog='easyucs.py', description='EasyUCS Command-Line Interface',
                                     epilog=example_text,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers = parser.add_subparsers(dest='scope', title='Scope', description='Scope of action', help='EasyUCS scope')
    subparsers.required = True  # Not set directly in above line to avoid issue if running Python < 3.7

    # Create the parsers for the "config" & inventory scopes
    parser_config = subparsers.add_parser('config', help='config-related actions', epilog=example_config_text,
                                          formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers_config = parser_config.add_subparsers(dest='action', title='Action', help='Config actions')
    subparsers_config.required = True  # Not set directly in above line to avoid issue if running Python < 3.7

    parser_inventory = subparsers.add_parser('inventory', help='inventory-related actions',
                                             epilog=example_inventory_fetch_text,
                                             formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers_inventory = parser_inventory.add_subparsers(dest='action', title='Action', help='Inventory actions')
    subparsers_inventory.required = True  # Not set directly in above line to avoid issue if running Python < 3.7

    # Create the parsers for the "schemas" scope
    parser_schemas = subparsers.add_parser('schemas', help='schemas-related actions',
                                           epilog=example_schemas_create_text,
                                           formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers_schemas = parser_schemas.add_subparsers(dest='action', title='Action',
                                                       help='Schemas actions')
    subparsers_schemas.required = True  # Not set directly in above line to avoid issue if running Python < 3.7

    # Create the parsers for the "report" scope
    parser_report = subparsers.add_parser('report', help='report-related actions',
                                          epilog=example_report_generate_text,
                                          formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers_report = parser_report.add_subparsers(dest='action', title='Action', help='Report actions')
    subparsers_report.required = True  # Not set directly in above line to avoid issue if running Python < 3.7

    # Create the parsers for the "device" scope
    parser_device = subparsers.add_parser('device', help='device-related actions',
                                          epilog=example_device_text,
                                          formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers_device = parser_device.add_subparsers(dest='action', title='Action', help='Device actions')
    subparsers_device.required = True  # Not set directly in above line to avoid issue if running Python < 3.7

    # Create the parsers for the "fetch" & "push" actions of config
    parser_config_fetch = subparsers_config.add_parser('fetch', help='Fetch a config from a device',
                                                       epilog=example_config_fetch_text,
                                                       formatter_class=argparse.RawDescriptionHelpFormatter)
    parser_config_fetch.add_argument('-i', '--ip', dest='ip', action='store', help='Device IP address/Hostname',
                                     required=True)
    parser_config_fetch.add_argument('-u', '--username', dest='username', action='store',
                                     help='Device Account Username')
    parser_config_fetch.add_argument('-p', '--password', dest='password', action='store',
                                     help='Device Account Password')
    parser_config_fetch.add_argument('-a', '--api_key', dest='api_key', action='store', help='Device Account API Key')
    parser_config_fetch.add_argument('-k', '--secret_key_path', dest='secret_key_path', action='store',
                                     help='Device Account Secret Key (path to file)')
    parser_config_fetch.add_argument('-t', '--device_type', dest='device_type', action='store',
                                     choices=['ucsm', 'cimc', 'ucsc', 'intersight'], required=True, help='Device type')

    parser_config_fetch.add_argument('-v', '--verbose', dest='log', action='store_true', help='Print debug log')
    parser_config_fetch.add_argument('-l', '--logfile', dest='logfile', action='store', help='Print log in a file')

    parser_config_fetch.add_argument('-o', '--out', dest='output_config', action='store', help='Output config file',
                                     required=True)
    parser_config_fetch.add_argument('-y', '--yes', dest='yes', action='store_true', help='Answer yes to all questions')

    parser_config_push = subparsers_config.add_parser('push', help='Push a config to a device',
                                                      epilog=example_config_push_text,
                                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser_config_push.add_argument('-i', '--ip', dest='ip', action='store', help='Device IP address/Hostname')
    parser_config_push.add_argument('-u', '--username', dest='username', action='store', help='Device Account Username')
    parser_config_push.add_argument('-p', '--password', dest='password', action='store', help='Device Account Password')
    parser_config_push.add_argument('-a', '--api_key', dest='api_key', action='store', help='Device Account API Key')
    parser_config_push.add_argument('-k', '--secret_key_path', dest='secret_key_path', action='store',
                                    help='Device Account Secret Key (path to file)')
    parser_config_push.add_argument('-t', '--device_type', dest='device_type', action='store',
                                    choices=['ucsm', 'cimc', 'ucsc', 'intersight'], required=True, help='Device type')

    parser_config_push.add_argument('-v', '--verbose', dest='log', action='store_true', help='Print debug log')
    parser_config_push.add_argument('-l', '--logfile', dest='logfile', action='store', help='Print log in a file')

    parser_config_push.add_argument('-f', '--file', dest='file', action='store', help='Configuration file')
    parser_config_push.add_argument('-r', '--reset', dest='reset', action='store_true', help='Erase Configuration')
    parser_config_push.add_argument('-s', '--setup', dest='setup', action='store', nargs='+',
                                    help='Perform Initial setup')
    parser_config_push.add_argument('-y', '--yes', dest='yes', action='store_true', help='Answer yes to all questions')

    # Create the parsers for the "fetch" action of inventory
    parser_inventory_fetch = subparsers_inventory.add_parser('fetch', help='Fetch an inventory from a device',
                                                             epilog=example_inventory_fetch_text,
                                                             formatter_class=argparse.RawDescriptionHelpFormatter)
    parser_inventory_fetch.add_argument('-i', '--ip', dest='ip', action='store', help='Device IP address/Hostname',
                                        required=True)
    parser_inventory_fetch.add_argument('-u', '--username', dest='username', action='store',
                                        help='Device Account Username')
    parser_inventory_fetch.add_argument('-p', '--password', dest='password', action='store',
                                        help='Device Account Password')
    parser_inventory_fetch.add_argument('-a', '--api_key', dest='api_key', action='store',
                                        help='Device Account API Key')
    parser_inventory_fetch.add_argument('-k', '--secret_key_path', dest='secret_key_path', action='store',
                                        help='Device Account Secret Key (path to file)')
    parser_inventory_fetch.add_argument('-t', '--device_type', dest='device_type', action='store',
                                        choices=['ucsm', 'cimc', 'ucsc', 'intersight'], required=True,
                                        help='Device type')

    parser_inventory_fetch.add_argument('-v', '--verbose', dest='log', action='store_true', help='Print debug log')
    parser_inventory_fetch.add_argument('-l', '--logfile', dest='logfile', action='store', help='Print log in a file')

    parser_inventory_fetch.add_argument('-o', '--out', dest='output_inventory', action='store',
                                        help='Output inventory file', required=True)
    parser_inventory_fetch.add_argument('-y', '--yes', dest='yes', action='store_true',
                                        help='Answer yes to all questions')

    # Create the parsers for the "create" action of schemas
    parser_schemas_create = subparsers_schemas.add_parser('create', help='Create schemas of a device',
                                                          epilog=example_schemas_create_text,
                                                          formatter_class=argparse.RawDescriptionHelpFormatter)
    parser_schemas_create.add_argument('-i', '--ip', dest='ip', action='store', help='Device IP address/Hostname',
                                       required=True)
    parser_schemas_create.add_argument('-u', '--username', dest='username', action='store',
                                       help='Device Account Username', required=True)
    parser_schemas_create.add_argument('-p', '--password', dest='password', action='store',
                                       help='Device Account Password', required=True)
    parser_schemas_create.add_argument('-t', '--device_type', dest='device_type', action='store',
                                       choices=['ucsm', 'cimc'], required=True, help='Device type')

    parser_schemas_create.add_argument('-v', '--verbose', dest='log', action='store_true', help='Print debug log')
    parser_schemas_create.add_argument('-l', '--logfile', dest='logfile', action='store', help='Print log in a file')

    parser_schemas_create.add_argument('-o', '--out', dest='output_directory', action='store',
                                       help='Output schemas directory', required=True)
    parser_schemas_create.add_argument('-c', '--clear', dest='clear_pictures', action='store_true',
                                       help='Export clear pictures (without colored ports)')
    parser_schemas_create.add_argument('-y', '--yes', dest='yes', action='store_true',
                                       help='Answer yes to all questions')

    # Create the parsers for the "generate" action of report
    parser_report_generate = subparsers_report.add_parser('generate', help='Generate report of a device',
                                                          epilog=example_report_generate_text,
                                                          formatter_class=argparse.RawDescriptionHelpFormatter)
    parser_report_generate.add_argument('-i', '--ip', dest='ip', action='store', help='Device IP address/Hostname',
                                        required=True)
    parser_report_generate.add_argument('-u', '--username', dest='username', action='store',
                                        help='Device Account Username', required=True)
    parser_report_generate.add_argument('-p', '--password', dest='password', action='store',
                                        help='Device Account Password', required=True)
    parser_report_generate.add_argument('-t', '--device_type', dest='device_type', action='store',
                                        choices=['ucsm', 'cimc'], required=True, help='Device type')

    parser_report_generate.add_argument('-s', '--layout_size', dest='layout', action='store', choices=['a4', 'letter'],
                                        help='Report layout size ("a4" or "letter")')

    parser_report_generate.add_argument('-v', '--verbose', dest='log', action='store_true', help='Print debug log')
    parser_report_generate.add_argument('-l', '--logfile', dest='logfile', action='store', help='Print log in a file')

    parser_report_generate.add_argument('-o', '--out', dest='output_directory', action='store',
                                        help='Output report directory', required=True)
    parser_report_generate.add_argument('-y', '--yes', dest='yes', action='store_true',
                                        help='Answer yes to all questions')

    # Create the parsers for the "regenerate_certificate" action of device
    parser_device_regen_cert = subparsers_device.add_parser('regenerate_certificate',
                                                            help='Regenerate self-signed certificate of an UCS system',
                                                            epilog=example_device_regenerate_certificate_text,
                                                            formatter_class=argparse.RawDescriptionHelpFormatter)
    parser_device_regen_cert.add_argument('-i', '--ip', dest='ip', action='store', help='Device IP address/Hostname',
                                          required=True)
    parser_device_regen_cert.add_argument('-u', '--username', dest='username', action='store',
                                          help='Device Account Username', required=True)
    parser_device_regen_cert.add_argument('-p', '--password', dest='password', action='store',
                                          help='Device Account Password', required=True)
    parser_device_regen_cert.add_argument('-t', '--device_type', dest='device_type', action='store',
                                          choices=['ucsm'], required=True, help='Device type')

    parser_device_regen_cert.add_argument('-v', '--verbose', dest='log', action='store_true', help='Print debug log')
    parser_device_regen_cert.add_argument('-l', '--logfile', dest='logfile', action='store', help='Print log in a file')

    parser_device_regen_cert.add_argument('-y', '--yes', dest='yes', action='store_true',
                                          help='Answer yes to all questions')

    # Create the parsers for the "clear_sel_logs" action of device
    parser_device_clear_sel_logs = subparsers_device.add_parser('clear_sel_logs',
                                                                help='Clears all SEL logs of a device',
                                                                epilog=example_device_clear_sel_logs_text,
                                                                formatter_class=argparse.RawDescriptionHelpFormatter)
    parser_device_clear_sel_logs.add_argument('-i', '--ip', dest='ip', action='store',
                                              help='Device IP address/Hostname', required=True)
    parser_device_clear_sel_logs.add_argument('-u', '--username', dest='username', action='store',
                                              help='Device Account Username', required=True)
    parser_device_clear_sel_logs.add_argument('-p', '--password', dest='password', action='store',
                                              help='Device Account Password', required=True)
    parser_device_clear_sel_logs.add_argument('-t', '--device_type', dest='device_type', action='store',
                                              choices=['ucsm', 'cimc'], required=True, help='Device type')

    parser_device_clear_sel_logs.add_argument('-v', '--verbose', dest='log', action='store_true',
                                              help='Print debug log')
    parser_device_clear_sel_logs.add_argument('-l', '--logfile', dest='logfile', action='store',
                                              help='Print log in a file')

    parser_device_clear_sel_logs.add_argument('-y', '--yes', dest='yes', action='store_true',
                                              help='Answer yes to all questions')

    # Create the parsers for the "clear_user_sessions" action of device
    parser_device_clear_user_sessions = \
        subparsers_device.add_parser('clear_user_sessions',
                                     help='Clears all user sessions of a device',
                                     epilog=example_device_clear_user_sessions_text,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser_device_clear_user_sessions.add_argument('-i', '--ip', dest='ip', action='store',
                                                   help='Device IP address/Hostname', required=True)
    parser_device_clear_user_sessions.add_argument('-u', '--username', dest='username', action='store',
                                                   help='Device Account Username', required=True)
    parser_device_clear_user_sessions.add_argument('-p', '--password', dest='password', action='store',
                                                   help='Device Account Password', required=True)
    parser_device_clear_user_sessions.add_argument('-t', '--device_type', dest='device_type', action='store',
                                                   choices=['ucsm', 'cimc', 'ucsc'], required=True, help='Device type')

    parser_device_clear_user_sessions.add_argument('-v', '--verbose', dest='log', action='store_true',
                                                   help='Print debug log')
    parser_device_clear_user_sessions.add_argument('-l', '--logfile', dest='logfile', action='store',
                                                   help='Print log in a file')

    parser_device_clear_user_sessions.add_argument('-y', '--yes', dest='yes', action='store_true',
                                                   help='Answer yes to all questions')

    # Create the parsers for the "clear_intersight_claim_status" action of device
    parser_device_clear_intersight_claim_status = \
        subparsers_device.add_parser('clear_intersight_claim_status',
                                     help='Clears Intersight claim status of a device',
                                     epilog=example_device_clear_intersight_claim_status_text,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser_device_clear_intersight_claim_status.add_argument('-i', '--ip', dest='ip', action='store',
                                                             help='Device IP address/Hostname', required=True)
    parser_device_clear_intersight_claim_status.add_argument('-u', '--username', dest='username', action='store',
                                                             help='Device Account Username', required=True)
    parser_device_clear_intersight_claim_status.add_argument('-p', '--password', dest='password', action='store',
                                                             help='Device Account Password', required=True)
    parser_device_clear_intersight_claim_status.add_argument('-t', '--device_type', dest='device_type', action='store',
                                                             choices=['ucsm', 'cimc', 'ucsc'], required=True,
                                                             help='Device type')

    parser_device_clear_intersight_claim_status.add_argument('-v', '--verbose', dest='log', action='store_true',
                                                             help='Print debug log')
    parser_device_clear_intersight_claim_status.add_argument('-l', '--logfile', dest='logfile', action='store',
                                                             help='Print log in a file')

    parser_device_clear_intersight_claim_status.add_argument('-y', '--yes', dest='yes', action='store_true',
                                                             help='Answer yes to all questions')

    # Create the parsers for the "get_device_connector_status" action of device
    parser_device_get_device_connector_status = \
        subparsers_device.add_parser('get_device_connector_status',
                                     help='Clears Intersight claim status of a device',
                                     epilog=example_device_get_device_connector_status_text,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser_device_get_device_connector_status.add_argument('-i', '--ip', dest='ip', action='store',
                                                           help='Device IP address/Hostname', required=True)
    parser_device_get_device_connector_status.add_argument('-u', '--username', dest='username', action='store',
                                                           help='Device Account Username', required=True)
    parser_device_get_device_connector_status.add_argument('-p', '--password', dest='password', action='store',
                                                           help='Device Account Password', required=True)
    parser_device_get_device_connector_status.add_argument('-t', '--device_type', dest='device_type', action='store',
                                                           choices=['ucsm', 'cimc', 'ucsc'], required=True,
                                                           help='Device type')

    parser_device_get_device_connector_status.add_argument('-v', '--verbose', dest='log', action='store_true',
                                                           help='Print debug log')
    parser_device_get_device_connector_status.add_argument('-l', '--logfile', dest='logfile', action='store',
                                                           help='Print log in a file')

    parser_device_get_device_connector_status.add_argument('-y', '--yes', dest='yes', action='store_true',
                                                           help='Answer yes to all questions')

    args = parser.parse_args()

    json_string = ""
    # Checking arguments compliance for config/inventory (Intersight vs UCS devices)
    if args.scope in ["config", "inventory"]:
        if args.device_type == "intersight":
            if args.api_key is None or args.secret_key_path is None:
                print("Intersight device type requires --api_key (-a) and --secret_key_path (-k) arguments!")
                parser_config_push.print_help()
                exit()
        else:
            if args.username is None or args.password is None:
                print("UCS device type requires --username (-u) and --password (-p) arguments!")
                parser_config_push.print_help()
                exit()

    # Checking arguments compliance for config push
    if args.scope == "config" and args.action == "push":
        if args.setup and args.file is None:
            print("--setup (-s) requires --file (-f) argument!")
            parser_config_push.print_help()
            exit()

        if args.setup and args.device_type is None:
            print("--setup (-s) requires --device_type (-t) argument!")
            parser_config_push.print_help()
            exit()

        if args.reset and args.file and args.setup is None:
            print("--reset (-r) with --file (-f) requires --setup (-s) argument!")
            parser_config_push.print_help()
            exit()

        if args.reset:
            if args.ip is None or args.username is None or args.password is None:
                print("--reset (-r) requires --ip (-i), --username (-u) and --password (-p) arguments!")
                parser_config_push.print_help()
                exit()

        if args.file and args.setup is None:
            if args.ip is None or args.username is None or args.password is None:
                print("--file (-f) without --setup (-s) requires --ip (-i), --username (-u) " +
                      "and --password (-p) arguments!")
                parser_config_push.print_help()
                exit()

        if args.setup and args.file and args.reset is False:
            if args.ip or args.username or args.password:
                print("--ip (-i), --username (-u) and --password (-p) arguments are not allowed with " +
                      "--setup (-s) with --file (-f)!")
                parser_config_push.print_help()
                exit()

        if args.reset is False and args.file is None and args.setup is None:
            print("At least one action argument is required!")
            parser_config_push.print_help()
            exit()

        if args.setup:
            # Verify input is valid IP address(es)
            if len(args.setup) == 1:
                # We are running in standalone mode or IMC
                if not common.is_ip_address_valid(args.setup[0]):
                    print("Invalid IP address for setup action: " + args.setup[0])
                    exit()
            elif len(args.setup) == 2:
                # We are running in cluster mode
                if not common.is_ip_address_valid(args.setup[0]):
                    print("Invalid IP address for setup action: " + args.setup[0])
                    exit()
                elif not common.is_ip_address_valid(args.setup[1]):
                    print("Invalid IP address for setup action: " + args.setup[1])
                    exit()
            else:
                # We have too many IP addresses as input
                print("Too many arguments given for --setup!")
                exit()

        if args.file:
            # Open JSON configuration file
            json_file = open(args.file)
            json_string = json_file.read()
            json_file.close()

    device = instantiate_device(args)

    if device is not None:
        init_process(device, args, json_string)


if __name__ == '__main__':
    if sys.version_info <= (3, 0):
        print("ERROR: EasyUCS requires Python 3.x!")
        exit()
    main()
