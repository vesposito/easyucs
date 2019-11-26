#!/usr/bin/env python
# coding: utf-8

""" easyucs.py: Easy UCS Deployment Tool """
from easyucs import __author__, __copyright__,  __version__, __status__


import os
import sys
import argparse
import time

from easyucs import common
from easyucs.device.device import UcsImc, UcsSystem, BlindUcs, GenericUcsDevice, UcsCentral

from imcsdk.imchandle import ImcHandle
from ucsmsdk.ucshandle import UcsHandle
from pathlib import Path

# from hcl.hcl import UcsSystemHclCheck

OUTPUT_DIRECTORY = "temp"


def create_ucs_device(args):
    """
    Creates a UCS Device, depending on the arguments provided
    :param args: Command-line arguments provided (argparse format)
    :return: UCS device if creation is succesful, None otherwise
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

    if args.ip:
        target = args.ip
    if args.username:
        username = args.username
    if args.password:
        password = args.password

    device = None
    if args.ucstype:
        if args.ucstype == "ucsm":
            device = UcsSystem(target=target, user=username, password=password,
                               logger_handle_log_level=logger_handle_log_level, log_file_path=log_file_path)
            device.logger(level="debug", message="Created UcsSystem device with IP " + target)
        elif args.ucstype == "cimc":
            device = UcsImc(target=target, user=username, password=password,
                            logger_handle_log_level=logger_handle_log_level, log_file_path=log_file_path)
            device.logger(level="debug", message="Created UcsImc device with IP " + target)
        elif args.ucstype == "ucsc":
            device = UcsCentral(target=target, user=username, password=password,
                            logger_handle_log_level=logger_handle_log_level, log_file_path=log_file_path)
            device.logger(level="debug", message="Created UcsCentral device with IP " + target)
    else:
        device = BlindUcs(target=target, user=username, password=password,
                          logger_handle_log_level=logger_handle_log_level, log_file_path=log_file_path)
        if device.__class__.__name__ == "GenericUcsDevice":
            print("Error: Could not determine UCS Device type!")
            return None

    return device


def init_process(ucs_device, args, config_string):
    """
    Performs initial processing of EasyUCS, depending on the arguments provided
    :param ucs_device: UCS device to be used for processing
    :param args: Command-line arguments provided (argparse format)
    :param config_string: The config content
    :return: True if successful, False otherwise
    """

    bypass_version_checks = False
    if args.yes:
        bypass_version_checks = True

    ucs_device.set_task_progression(1)
    if args.scope == "config" and args.action == "push":
        # Adding configuration to the created UCS Device
        if config_string:
            if not ucs_device.config_manager.import_config(config=config_string):
                exit()
            config = ucs_device.config_manager.get_latest_config()

        # If we are doing a complete reset/setup cycle, we use the push_config method with the "reset" argument
        if args.setup and args.reset:
            if not args.yes:
                if not common.query_yes_no("Are you sure you want to erase all configuration on " + ucs_device.name + "?"):
                    # User declined configuration erase query
                    # FIXME: handle proper disconnection if required
                    exit()

            if ucs_device.__class__.__name__ == "UcsImc":
                ucs_device.config_manager.push_config(reset=True, imc_ip=args.setup[0],
                                                      bypass_version_checks=bypass_version_checks)
            elif ucs_device.__class__.__name__ == "UcsSystem":
                ucs_device.config_manager.push_config(reset=True, fi_ip_list=args.setup,
                                                      bypass_version_checks=bypass_version_checks)

        # If we are not doing a complete reset/setup cycle, we perform each action separately
        else:
            if args.reset:
                if not args.yes:
                    if not common.query_yes_no("Are you sure you want to erase all configuration on " + ucs_device.name +
                                               "?"):
                        # User declined configuration erase query
                        # FIXME: handle proper disconnection if required
                        exit()

                # Executing reset action
                if not ucs_device.reset(bypass_version_checks=bypass_version_checks):
                    ucs_device.logger(level="error", message="Error while performing UCS device reset")
                    exit()

            if args.setup:
                ucs_device.logger(level="debug", message="Performing initial setup with IP " + str(args.setup[0]))
                if ucs_device.__class__.__name__ == "UcsImc":
                    if not ucs_device.initial_setup(imc_ip=args.setup[0], config=config,
                                                    bypass_version_checks=bypass_version_checks):
                        ucs_device.logger(level="error", message="Error while performing initial setup on UCS IMC")
                        exit()

                    # We now need to get the new IP address and admin password from the configuration
                    imc_target_ip_address = ""
                    if config.admin_networking[0].management_ipv4_address:
                        imc_target_ip_address = config.admin_networking[0].management_ipv4_address
                    else:
                        ucs_device.logger(level="error",
                                          message="Could not find Management IP address of UCS IMC in the config")
                        exit()

                    if not config.local_users:
                        ucs_device.logger(level="error", message="Could not find local_users in the config")
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
                                    ucs_device.logger(level="error",
                                                      message="Could not find password for user id admin in the config")
                                    exit()

                    # We went through all users - Making sure we got the information we needed
                    if not target_admin_password:
                        ucs_device.logger(level="error", message="Could not find user id admin in the config")
                        exit()

                    # We need to refresh the UCS device handle so that it has the right attributes
                    ucs_device.handle = ImcHandle(ip=imc_target_ip_address, username="admin",
                                                  password=target_admin_password)

                    # Changing handle to the new one
                    config.refresh_config_handle()

                    ucs_device.logger(level="debug",
                                      message="Waiting for the IMC to come back with the IP " + imc_target_ip_address)
                    if not ucs_device.wait_for_reboot_after_reset(timeout=60, imc_ip=imc_target_ip_address):
                        exit()

                elif ucs_device.__class__.__name__ == "UcsSystem":
                    if len(args.setup) == 2:
                        ucs_device.sys_mode = "cluster"
                    elif len(args.setup) == 1:
                        ucs_device.sys_mode = "stand-alone"
                    if not ucs_device.initial_setup(fi_ip_list=args.setup, config=config):
                        ucs_device.logger(level="error", message="Error while performing initial setup on UCS System")
                        exit()

                    # We now need to wait to be able to configure the device using the configuration
                    if ucs_device.sys_mode == "cluster":
                        ucs_device.logger(message="Waiting up to 240 seconds for cluster election to complete")
                        time.sleep(80)
                        if config.system:
                            if config.system[0].virtual_ip:
                                ucs_device.target = config.system[0].virtual_ip
                            elif config.system[0].virtual_ipv6:
                                ucs_device.target = config.system[0].virtual_ipv6
                        if not ucs_device.target:
                            ucs_device.logger(level="error",
                                              message="Could not determine target IP of the device in the config")
                            exit()

                    elif ucs_device.sys_mode == "stand-alone":
                        ucs_device.logger(message="Waiting up to 180 seconds for initial configuration to complete")
                        time.sleep(20)

                        # TODO Handle Ipv6
                        if config.management_interfaces:
                            for management_interface in config.management_interfaces:
                                if management_interface.fabric.upper() == 'A':
                                    if management_interface.ip:
                                        ucs_device.target = management_interface.ip

                        if not ucs_device.target:
                            ucs_device.logger(level="error",
                                              message="Could not determine target IP of the device in the config")
                            exit()

                    if not config.local_users:
                        # Could not find local_users in config - Admin password is a mandatory parameter - Exiting
                        ucs_device.logger(level="error", message="Could not find local_users in the config")
                        exit()

                    # Going through all users to find admin
                    for user in config.local_users:
                        if user.id:
                            if user.id == "admin":
                                ucs_device.username = "admin"
                                if user.password:
                                    ucs_device.password = user.password
                                else:
                                    # Admin password is a mandatory input
                                    ucs_device.logger(level="error",
                                                      message="Could not find password for user id admin in the config")
                                    exit()

                    # We need to refresh the UCS device handle so that it has the right attributes
                    ucs_device.handle = UcsHandle(ip=ucs_device.target, username=ucs_device.username,
                                                  password=ucs_device.password)

                    # We also need to refresh the config handle
                    config.refresh_config_handle()

                    if not common.check_web_page(device=ucs_device, url="https://" + ucs_device.target, str_match="Cisco",
                                                 timeout=160):
                        ucs_device.logger(level="error", message="Impossible to reconnect to UCS system")
                        exit()

                    # Reconnecting and waiting for HA cluster to be ready (if in cluster mode)
                    if not ucs_device.connect(bypass_version_checks=bypass_version_checks, retries=3):
                        ucs_device.logger(level="error", message="Impossible to reconnect to UCS system")
                        exit()

                    # Bypass version checks for the rest of the procedure as potential warnings have already been made
                    bypass_version_checks = True

                    if ucs_device.sys_mode == "cluster":
                        ucs_device.logger(message="Waiting up to 300 seconds for UCS HA cluster to be ready...")
                        if not ucs_device.wait_for_ha_cluster_ready(timeout=300):
                            ucs_device.logger(
                                level="error",
                                message="Timeout exceeded while waiting for UCS HA cluster to be in ready state")
                            exit()
                    elif ucs_device.sys_mode == "stand-alone":
                        ucs_device.logger(message="Waiting up to 300 seconds for UCS stand-alone FI to be ready...")
                        if not ucs_device.wait_for_standalone_fi_ready(timeout=300):
                            ucs_device.logger(
                                level="error",
                                message="Timeout exceeded while waiting for UCS stand-alone FI to be ready")
                            exit()

            if config_string:
                ucs_device.config_manager.push_config(bypass_version_checks=bypass_version_checks)

    elif args.scope == "config" and args.action == "fetch":
        # Fetching config from live UCS Device
        if not ucs_device.connect(bypass_version_checks=bypass_version_checks):
            ucs_device.logger(level="error", message="Impossible to connect to UCS device")
            exit()
        ucs_device.config_manager.fetch_config()
        ucs_device.set_task_progression(50)

        # Exporting config to specified output config file
        directory = os.path.dirname(args.output_config)
        filename = os.path.basename(args.output_config)
        ucs_device.config_manager.export_config(directory=directory, filename=filename)

    elif args.scope == "inventory" and args.action == "fetch":
        # Fetching inventory from live UCS Device
        if not ucs_device.connect(bypass_version_checks=bypass_version_checks):
            ucs_device.logger(level="error", message="Impossible to connect to UCS device")
            exit()
        ucs_device.inventory_manager.fetch_inventory()
        ucs_device.set_task_progression(50)

        # Exporting inventory to specified output config file
        directory = os.path.dirname(args.output_inventory)
        filename = os.path.basename(args.output_inventory)
        ucs_device.inventory_manager.export_inventory(directory=directory, filename=filename)

    elif args.scope == "schemas" and args.action == "create":
        # Fetching inventory from live UCS Device and create schemas of it
        if not ucs_device.connect(bypass_version_checks=bypass_version_checks):
            ucs_device.logger(level="error", message="Impossible to connect to UCS device")
            exit()
        ucs_device.inventory_manager.fetch_inventory()
        ucs_device.set_task_progression(50)

        ucs_device.inventory_manager.draw_inventory()
        ucs_device.set_task_progression(75)

        directory = args.output_directory
        ucs_device.inventory_manager.export_draw(directory=directory, export_clear_pictures=args.clear_pictures)

    elif args.scope == "report" and args.action == "generate":
        # Fetching inventory from live UCS Device, create schemas and generate report of it
        if not ucs_device.connect(bypass_version_checks=bypass_version_checks):
            ucs_device.logger(level="error", message="Impossible to connect to UCS device")
            exit()

        ucs_device.config_manager.fetch_config()
        ucs_device.set_task_progression(25)

        ucs_device.inventory_manager.fetch_inventory()
        ucs_device.set_task_progression(50)

        # Exporting report to specified output directory
        directory = args.output_directory

        # Exporting inventory & config to JSON files
        ucs_device.inventory_manager.export_inventory(directory=directory,
                                                      filename="inventory_" + ucs_device.target + ".json")
        ucs_device.config_manager.export_config(directory=directory, filename="config_" + ucs_device.target + ".json")
        ucs_device.set_task_progression(60)

        ucs_device.inventory_manager.draw_inventory()
        ucs_device.set_task_progression(75)

        ucs_device.inventory_manager.export_draw(directory=directory, export_clear_pictures=True)
        ucs_device.set_task_progression(80)

        if ucs_device.device_type_short == "ucsm":
            ucs_device.config_manager.generate_config_plots()
            ucs_device.config_manager.export_config_plots(directory=directory)
            ucs_device.set_task_progression(90)

        ucs_device.generate_report(filename="report_" + ucs_device.target, directory=directory,
                                   page_layout=args.layout)

    ucs_device.set_task_progression(100)
    ucs_device.print_logger_summary()


def main():
    # Example texts for parser
    example_text = '''Examples:
      To see examples, please type: python easyucs.py {config, inventory, schemas, report} -h'''

    example_config_text = '''Examples:
      python easyucs.py config fetch -t ucsm -i 192.168.0.1 -u admin -p password -o configs/config_ucsm.json
            fetch config from UCS system and save it to configs/config_ucsm.json

      python easyucs.py config push -t ucsm -i 192.168.0.1 -u admin -p password -f configs/config_ucsm.json
            push config file config_ucsm.json to UCS system

      python easyucs.py config push -t cimc -i 192.168.0.2 -u admin -p password -f configs/config_cimc.json -r
            reset UCS IMC and push config file config_cimc.json

      python easyucs.py config push -t ucsm -f configs/config_ucsm.json -r -s 192.168.0.11 192.168.0.12
            reset UCS system, perform initial setup using DHCP IP addresses 192.168.0.11 & 192.168.0.12 and push config file config_ucsm.json'''

    example_config_fetch_text = '''Examples:
      python easyucs.py config fetch -t ucsm -i 192.168.0.1 -u admin -p password -o configs/config_ucsm.json
            fetch config from UCS system and save it to configs/config_ucsm.json

      python easyucs.py config fetch -t cimc -i 192.168.0.2 -u admin -p password -o configs/config_cimc.json
            fetch config from UCS IMC and save it to configs/config_cimc.json'''

    example_config_push_text = '''Examples:
      python easyucs.py config push -t ucsm -i 192.168.0.1 -u admin -p password -f configs/config_ucsm.json
            push config file config_ucsm.json to UCS system

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
              python easyucs.py report generate -t ucsm -i 192.168.0.1 -u admin -p password -o reports/report.docx
                    create schemas and report.docx from UCS system and save it to reports/

              python easyucs.py report generate -t cimc -i 192.168.0.2 -u admin -p password -o reports/report.docx
                    create schemas and report.docx from UCS IMC and save it to reports/'''

    # Create the main parser
    parser = argparse.ArgumentParser(prog='easyucs.py', description='EasyUCS Command-Line Interface',
                                     epilog=example_text,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers = parser.add_subparsers(dest='scope', title='Scope', description='Scope of action', help='EasyUCS scope')
    subparsers.required = True  # Not set directly in above line to avoid issue if running Python < 3.7

    # Create the parsers for the "config" & inventory scopes
    parser_config = subparsers.add_parser('config', help='config-related actions', epilog=example_config_text,
                                          formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers_config = parser_config.add_subparsers(dest='action', title='Action',
                                                     help='Config actions')
    subparsers_config.required = True  # Not set directly in above line to avoid issue if running Python < 3.7

    parser_inventory = subparsers.add_parser('inventory', help='inventory-related actions',
                                             epilog=example_inventory_fetch_text,
                                             formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers_inventory = parser_inventory.add_subparsers(dest='action', title='Action',
                                                           help='Inventory actions')
    subparsers_inventory.required = True  # Not set directly in above line to avoid issue if running Python < 3.7

    # Create the parsers for the "schemas" scopes
    parser_schemas = subparsers.add_parser('schemas', help='schemas-related actions',
                                           epilog=example_schemas_create_text,
                                           formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers_schemas = parser_schemas.add_subparsers(dest='action', title='Action',
                                                       help='Schemas actions')
    subparsers_schemas.required = True  # Not set directly in above line to avoid issue if running Python < 3.7

    # Create the parsers for the "report" scopes
    parser_report = subparsers.add_parser('report', help='report-related actions',
                                           epilog=example_report_generate_text,
                                           formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers_report = parser_report.add_subparsers(dest='action', title='Action',
                                                       help='Report actions')
    subparsers_report.required = True  # Not set directly in above line to avoid issue if running Python < 3.7

    # Create the parsers for the "fetch" & "push" actions of config
    parser_config_fetch = subparsers_config.add_parser('fetch', help='Fetch a config from a UCS device',
                                                       epilog=example_config_fetch_text,
                                                       formatter_class=argparse.RawDescriptionHelpFormatter)
    parser_config_fetch.add_argument('-i', '--ip', dest='ip', action='store', help='UCS IP address', required=True)
    parser_config_fetch.add_argument('-u', '--username', dest='username', action='store', help='UCS Account Username',
                                     required=True)
    parser_config_fetch.add_argument('-p', '--password', dest='password', action='store', help='UCS Account Password',
                                     required=True)
    parser_config_fetch.add_argument('-t', '--ucstype', dest='ucstype', action='store',
                                     choices=['ucsm', 'cimc', 'ucsc'], help='UCS device type')

    parser_config_fetch.add_argument('-v', '--verbose', dest='log', action='store_true', help='Print debug log')
    parser_config_fetch.add_argument('-l', '--logfile', dest='logfile', action='store', help='Print log in a file')

    parser_config_fetch.add_argument('-o', '--out', dest='output_config', action='store', help='Output config file',
                                     required=True)
    parser_config_fetch.add_argument('-y', '--yes', dest='yes', action='store_true', help='Answer yes to all questions')

    parser_config_push = subparsers_config.add_parser('push', help='Push a config to a UCS device',
                                                      epilog=example_config_push_text,
                                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser_config_push.add_argument('-i', '--ip', dest='ip', action='store', help='UCS IP address')
    parser_config_push.add_argument('-u', '--username', dest='username', action='store', help='UCS Account Username')
    parser_config_push.add_argument('-p', '--password', dest='password', action='store', help='UCS Account Password')
    parser_config_push.add_argument('-t', '--ucstype', dest='ucstype', action='store', choices=['ucsm', 'cimc', 'ucsc'],
                                    help='UCS device type')

    parser_config_push.add_argument('-v', '--verbose', dest='log', action='store_true', help='Print debug log')
    parser_config_push.add_argument('-l', '--logfile', dest='logfile', action='store', help='Print log in a file')

    parser_config_push.add_argument('-f', '--file', dest='file', action='store', help='UCS Configuration file')
    parser_config_push.add_argument('-r', '--reset', dest='reset', action='store_true', help='Erase Configuration')
    parser_config_push.add_argument('-s', '--setup', dest='setup', action='store', nargs='+',
                                    help='Perform Initial setup')
    parser_config_push.add_argument('-y', '--yes', dest='yes', action='store_true', help='Answer yes to all questions')

    # Create the parsers for the "fetch" action of inventory
    parser_inventory_fetch = subparsers_inventory.add_parser('fetch', help='Fetch an inventory from a UCS device',
                                                             epilog=example_inventory_fetch_text,
                                                             formatter_class=argparse.RawDescriptionHelpFormatter)
    parser_inventory_fetch.add_argument('-i', '--ip', dest='ip', action='store', help='UCS IP address', required=True)
    parser_inventory_fetch.add_argument('-u', '--username', dest='username', action='store',
                                        help='UCS Account Username',
                                        required=True)
    parser_inventory_fetch.add_argument('-p', '--password', dest='password', action='store',
                                        help='UCS Account Password',
                                        required=True)
    parser_inventory_fetch.add_argument('-t', '--ucstype', dest='ucstype', action='store', choices=['ucsm', 'cimc'],
                                        help='UCS system type ("ucsm" or "cimc")')

    parser_inventory_fetch.add_argument('-v', '--verbose', dest='log', action='store_true', help='Print debug log')
    parser_inventory_fetch.add_argument('-l', '--logfile', dest='logfile', action='store', help='Print log in a file')

    parser_inventory_fetch.add_argument('-o', '--out', dest='output_inventory', action='store',
                                        help='Output inventory file',
                                        required=True)
    parser_inventory_fetch.add_argument('-y', '--yes', dest='yes', action='store_true',
                                        help='Answer yes to all questions')

    # Create the parsers for the "create" action of schemas
    parser_schemas_create = subparsers_schemas.add_parser('create', help='Create schemas of an UCS device',
                                                          epilog=example_schemas_create_text,
                                                          formatter_class=argparse.RawDescriptionHelpFormatter)
    parser_schemas_create.add_argument('-i', '--ip', dest='ip', action='store', help='UCS IP address', required=True)
    parser_schemas_create.add_argument('-u', '--username', dest='username', action='store',
                                       help='UCS Account Username',
                                       required=True)
    parser_schemas_create.add_argument('-p', '--password', dest='password', action='store',
                                       help='UCS Account Password',
                                       required=True)
    parser_schemas_create.add_argument('-t', '--ucstype', dest='ucstype', action='store', choices=['ucsm', 'cimc'],
                                       help='UCS system type ("ucsm" or "cimc")')

    parser_schemas_create.add_argument('-v', '--verbose', dest='log', action='store_true', help='Print debug log')
    parser_schemas_create.add_argument('-l', '--logfile', dest='logfile', action='store', help='Print log in a file')

    parser_schemas_create.add_argument('-o', '--out', dest='output_directory', action='store',
                                       help='Output schemas directory',
                                       required=True)
    parser_schemas_create.add_argument('-c', '--clear', dest='clear_pictures', action='store_true',
                                       help='Export clear pictures (without colored ports)')
    parser_schemas_create.add_argument('-y', '--yes', dest='yes', action='store_true',
                                       help='Answer yes to all questions')

    # Create the parsers for the "create" action of schemas
    parser_report_generate = subparsers_report.add_parser('generate', help='Generate report of an UCS device',
                                                          epilog=example_report_generate_text,
                                                          formatter_class=argparse.RawDescriptionHelpFormatter)
    parser_report_generate.add_argument('-i', '--ip', dest='ip', action='store', help='UCS IP address', required=True)
    parser_report_generate.add_argument('-u', '--username', dest='username', action='store',
                                       help='UCS Account Username',
                                       required=True)
    parser_report_generate.add_argument('-p', '--password', dest='password', action='store',
                                       help='UCS Account Password',
                                       required=True)
    parser_report_generate.add_argument('-t', '--ucstype', dest='ucstype', action='store', choices=['ucsm', 'cimc'],
                                       help='UCS system type ("ucsm" or "cimc")')

    parser_report_generate.add_argument('-s', '--layoutsize', dest='layout', action='store', choices=['a4', 'letter'],
                                        help='Report layout size ("a4" or "letter")')

    parser_report_generate.add_argument('-v', '--verbose', dest='log', action='store_true', help='Print debug log')
    parser_report_generate.add_argument('-l', '--logfile', dest='logfile', action='store', help='Print log in a file')

    parser_report_generate.add_argument('-o', '--out', dest='output_directory', action='store',
                                       help='Output report directory',
                                       required=True)
    parser_report_generate.add_argument('-y', '--yes', dest='yes', action='store_true',
                                       help='Answer yes to all questions')

    args = parser.parse_args()

    json_string = ""
    # Checking arguments compliance for config push
    if args.scope == "config" and args.action == "push":
        if args.setup and args.file is None:
            print("--setup (-s) requires --file (-f) argument!")
            parser_config_push.print_help()
            exit()

        if args.setup and args.ucstype is None:
            print("--setup (-s) requires --ucstype (-t) argument!")
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
                print(
                    "--file (-f) without --setup (-s) requires --ip (-i), --username (-u) and --password (-p) arguments!")
                parser_config_push.print_help()
                exit()

        if args.setup and args.file and args.reset is False:
            if args.ip or args.username or args.password:
                print(
                    "--ip (-i), --username (-u) and --password (-p) arguments are not allowed with --setup (-s) with --file (-f)!")
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

    ucs_device = create_ucs_device(args)

    if ucs_device is not None:
        init_process(ucs_device, args, json_string)


if __name__ == '__main__':
    if sys.version_info <= (3, 0):
        print("ERROR: EasyUCS requires Python 3.x!")
        exit()
    main()
