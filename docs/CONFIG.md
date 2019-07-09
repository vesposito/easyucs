# Working with configuration files

Configuration files can be pushed or fetched to/from a UCS device. They are JSON-formatted files that are meant to be **human-readable** with each section corresponding to a UCS feature.

You can find configuration samples in the **samples** directory. 
This directory contains:
* **best practices** configurations (for BIOS Policies)
* **CVD** configurations for quick deployment of FlashStack/FlexPod/VersaStack
* **sample** configurations grouped by topic. See [below](./CONFIG.md#Samples-for-UCS-System) for more info

[Fetching a live configuration](CONFIG.md#fetch-configurations) from a UCS device is also a good solution to get started.

## Deploy configurations

### Using the Command-Line Interface (CLI)

The file **[easyucs.py](../easyucs.py)** is the main file that you will use. 
You can find help at each step by entering the **"-h"** argument.

The tool first needs the scope of action you want to use as argument:
```
Scope:
  Scope of action

  {config,inventory,schemas,report}
                        EasyUCS scope
    config              config-related actions
    inventory           inventory-related actions
    schemas             schemas-related actions
    report              report-related actions
```

The second argument is the type of action:
```
Action:
  {fetch,push}  Config actions
    fetch       Fetch a config from a UCS device
    push        Push a config to a UCS device
```

##### Arguments for a config push 

List of arguments :
  
  - **-h**, --help            | show this help message and exit
  - **-i IP**, --ip IP        | UCS IP address
  - **-u USERNAME**, --username USERNAME
                        | UCS Account Username
  - **-p PASSWORD**, --password PASSWORD
                        | UCS Account Password
  - **-t** {**ucsm**,**cimc**, **ucsc**}, --ucstype {ucsm,cimc,ucsc}
                        | UCS system type ("ucsm", "cimc" or "ucsc")
  - **-v**, --verbose         | Print debug log
  - **-l LOGFILE**, --logfile LOGFILE
                        | Print log in a file
  - **-f FILE**, --file FILE  | UCS Configuration file
  - **-r**, --reset           | Erase Configuration
  - **-s SETUP** [SETUP ...], --setup SETUP [SETUP ...]
                        | Perform Initial setup
  - **-y**, --yes             | Answer yes to all questions


###Using the Web Graphical User Interface (GUI)

The Web GUI is hosted by your machine, in order to launch it you need to use the file **[easyucs_gui.py](./easyucs_gui.py)**.

```
python easyucs_gui.py
```


The result of this command will be something like:

```
 * Serving Flask app "easyucs_gui" (lazy loading)
 * Environment: production
   WARNING: Do not use the development server in a production environment.
   Use a production WSGI server instead.
 * Debug mode: off
 * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
```

It means that the GUI is available on your local machine at the URL http://127.0.0.1:5000/

The GUI can be used to deploy configurations on all types of UCS devices.

Open a web browser and enter the given URL. Select the UCS device type you want to use (UCS System, UCS IMC or UCS Central).

Enter the credentials of your UCS device. You also have the option to perform a "reset" and/or an initial "setup" for it.

If the "setup" box is selected you **must** enter the DHCP IP Address(es) that are given to your UCS device.

![GUI 1](img/GUI1_850.png)

Next you have to choose the configuration to push on your UCS Device. 
You can either select a file on your computer or use a "remote" file from the **samples** directory. 
Those remote files are JSON transcriptions of some CVDs and Best Practices.

![GUI 2](img/GUI2_850.png)

The last part of the GUI is the "Run Script" button, the progress bar and the log console.
In the log console you can choose what level of logs you want. Level "info" is selected by default.
The auto scrolling of this console is also an option.

![GUI 3](img/GUI3_850.png)

## Fetch configurations

*Warning: It is impossible to fetch any kind of password from a live system configuration.*

### Using the Command-Line Interface (CLI)

The file **[easyucs.py](../easyucs.py)** is the main file that you will use. 
You can find help at each step by entering the **"-h"** argument.

It first needs the type of scope of action you want to use as an argument. 
The scope of action:
```
Scope:
  Scope of action

  {config,inventory,schemas}  
                      EasyUCS scope
    config            config-related actions
    inventory         inventory-related actions
    schemas           schemas-related actions
```

The second argument is the type of action:
```
Action:
  {fetch,push}  Config actions
    fetch       Fetch a config from a UCS device
    push        Push a config to a UCS device
```

#### Arguments for a config fetch

List of arguments :

- **-h**, --help            | show this help message and exit
- **-i IP**, --ip IP        | UCS IP address
- **-u USERNAME**, --username USERNAME
                    | UCS Account Username
- **-p PASSWORD**, --password PASSWORD
                    | UCS Account Password
- **-t** {**ucsm**,**cimc**,**ucsc**}, --ucstype {ucsm,cimc,ucsc}
                    | UCS system type ("ucsm", "cimc" or "ucsc")
- **-v**, --verbose         | Print debug log
- **-l LOGFILE**, --logfile LOGFILE
                    | Print log in a file
- **-o OUTPUT_CONFIG**, --out OUTPUT_CONFIG
                    | Output config file
- **-y**, --yes             | Answer yes to all questions


## Structure of a configuration file

Each JSON file is structured with two sections : "easyucs" and "config"
```json5
{
   "easyucs":{
      
   },
   "config":{
      
   }
}
```
### "easyucs" section

An "easyucs" section is a composed of a "metadata" and a potential "options" sections. 

#### Metadata

The main section is "metadata", this section is an array of dict composed of items associated.

The required items are : ***"device_type", "file_type", "easyucs_version"***

The others are : *"category", "device_name", "device_uuid", "device_version", "hash", "name", "origin", "revision", "subcategory", "timestamp", "url", "uuid"*

Some of these other items are not meant to be written by the user. 

Example metadata header:
```json5
{
   "easyucs":{
      "metadata":[
         {
            "file_type": "config",
            "device_type": "ucsm",
            "easyucs_version":"0.9.0",
            "category":"cvd",
            "subcategory":"FlexPod",
            "name":"FlexPod Datacenter with VMware vSphere 6.5, NetApp AFF A-Series and Fibre Channel (6248UP)",
            "url":"https://www.cisco.com/c/en/us/td/docs/unified_computing/ucs/UCS_CVDs/flexpod_esxi65_n9fc.html",
            "revision": "1.0"
         }
      ]
   },
   "config":{
   }
}
```

#### Options

The optional section of the "easyucs" section is "options". This section lets you set some specific options or actions on the device.

The possible items are : *"discover_server_ports_in_order", "erase_all_virtual_drives_before_reset", "erase_all_flexflash_before_reset", "clear_all_sel_logs_before_reset", "set_drives_to_status"*

Example options section:
```json5
{
   "easyucs":{
      "metadata":[
         {
            "file_type": "config",
            "device_type": "cimc",
            "easyucs_version":"0.9.0",
            "category":"custom",
            "subcategory":"samples"
         }
      ],
      "options":[
         {
            "erase_all_flexflash_before_reset": "yes",
            "clear_all_sel_logs_before_reset": "yes",
            "set_drives_to_status": "jbod"
         }
      ]
   },
   "config":{
   }
}
```

### "config" section

This section is composed of all the features of a UCS Device configuration.

Each configuration feature is formatted the same way: a list of dictionaries featuring all of the items constituent of this feature.

Example config section:
```json5
{
   "easyucs":{
      "metadata":[...]
   },
   "config":{
      "system":[
         {
            "name":"bb04-6248",
            "virtual_ip":"192.168.156.12",
            "virtual_ipv6":"::",
            "domain_name":"vikings.cisco.com",
            "owner":"",
            "site":"",
            "descr":""
         }
      ],
      "switching_mode":[
         {
            "ethernet_mode":"end-host",
            "fc_mode":"end-host"
         }
      ]
   }
}
```

Some features are placed under an org to respect the hierarchy of the features (in UCS Manager or UCS Central). 

Note: An org can be placed under an org and so on. The first org must be named "root".

Example orgs section:
```json5
{
   "easyucs":{
      "metadata":[...]
   },
   "config":{
      "system":[
         {
            "name":"bb04-6248",
            "virtual_ip":"192.168.156.12",
            "virtual_ipv6":"::",
            "domain_name":"vikings.cisco.com",
            "owner":"",
            "site":"",
            "descr":""
         }
      ],
      "orgs":[
         {
            "name":"root",
            "ip_pools":[
               {
                  "name":"ext-mgmt",
                  "order":"sequential",
                  "ip_blocks":[
                     {
                        "from":"192.168.156.101",
                        "to":"192.168.156.112",
                        "gateway":"192.168.156.1",
                        "primary_dns":"0.0.0.0",
                        "secondary_dns":"0.0.0.0",
                        "netmask":"255.255.255.0"
                     }
                  ]
               }
            ]
         }
      ]
   }
}
```

For an IMC Device, all the features are on the same level.

You can find the list of all the features and where to find them on the sample config files below. 
To find the list of all the required items and all possible values for each features, please refer to the JSON Schema files
(not available for UCS IMC yet).

## Samples for UCS System

### Features outside of an organization

**config-ucsm-policies.json**

- appliance_network_control_policies

- link_profiles

- udld_link_policies

**config-ucsm-interfaces.json**

- appliance_port_channels

- appliance_ports

- breakout_ports

- fcoe_port_channels

- fcoe_storage_ports

- fcoe_uplink_ports

- lan_pin_groups

- lan_port_channels

- lan_uplink_ports

- qos_system_class

- san_pin_groups

- san_port_channels

- san_storage_ports

- san_unified_ports

- san_uplink_ports

- server_ports

- unified_storage_ports

- unified_uplink_ports

**config-ucsm-vlan-vsan.json**

- appliance_vlans

- storage_vsans

- vlan_groups

- vlans

- vsans

**config-ucsm-admin.json**

- backup_export_policy

- call_home

- dns

- global_policies

- ldap

- local_users

- local_users_properties

- locales

- management_interfaces

- orgs

- pre_login_banner

- radius

- roles

- sel_policy

- system

- tacacs

- timezone_mgmt

- ucs_central

- communication_services

- port_auto_discovery_policy

- slow_drain_timers

- switching_mode

### Features inside of an organization

**config-ucsm-org-pools.json**

- orgs

- ip_pools

- uuid_pools

- wwnn_pools

- wwpn_pools

- wwxn_pools

- iqn_suffix_pools

**config-ucsm-org-srv-pools.json**

- server_pools

- server_pool_policies

- server_pool_policy_qualifications

**config-ucsm-interfaces.json**

- vnic_templates

- vhba_templates

- default_vnic_behavior

- default_vhba_behavior

**config-ucsm-policies.json**

- power_control_policies

- qos_policies

- power_sync_policies

- ipmi_access_profiles

- kvm_management_policies

- serial_over_lan_policies

- vnic_vhba_placement_policies

- network_control_policies

- flow_control_policies

- lacp_policies

- iscsi_authentication_profiles

- vmedia_policies

- multicast_policies

- link_protocol_policy

- ethernet_adapter_policies

- fibre_channel_adapter_policies

- iscsi_adapter_policies

- memory_policy

- graphics_card_policies

- threshold_policies

- diagnostics_policies

- sas_expander_configuration_policies

**config-ucsm-serviceprofile.json**

- maintenance_policies

- local_disk_config_policies

- host_firmware_packages

- scrub_policies

- boot_policies

- bios_policies

- lan_connectivity_policies

- san_conn_policy

- storage_connection_policies

- fc_zone_profiles

- service_profiles

**config-ucsm-storage.json**

- disk_group_policies

- storage_profiles

**config-ucsm-chassis.json**

- chassis_maintenance_policies

- compute_connection_policies

- chassis_firmware_packages

- disk_zoning_policies

- chassis_profile

## Samples for UCS Central

### Features inside of a domain group

**config-ucsc-domain_group-vlan-vsan.json**

- domain_groups

- vlans

- appliance_vlans

- vlan_groups

### Features inside of an organization

**config-ucsc-org-pools.json**

- orgs

- ip_pools

- uuid_pools

- wwnn_pools

- wwpn_pools

## Samples for UCS IMC

Coming Soon