# Working with inventory files

Inventory files can be fetched from a device. They are JSON-formatted files that are meant to be **human-readable** with each section corresponding to a UCS equipment.


## Fetch inventories

### Using the Command-Line Interface (CLI)

The file **[easyucs.py](../easyucs.py)** is the main file that you will use. 
You can have find help at each step by entering the **"-h"** argument.

It first needs the type of scope of action you want to use as an argument. 
The scope of action:
```
Scope:
  Scope of action

  {config,inventory,schemas,report,device}
                        EasyUCS scope
    config              config-related actions
    inventory           inventory-related actions
    schemas             schemas-related actions
    report              report-related actions
    device              device-related actions
```

The second argument is the type of action:
```
Action:
  {fetch}     Inventory actions
    fetch     Fetch an inventory from a device
```

#### Arguments for an inventory fetch

List of arguments :

- **-h**, --help            | show this help message and exit
- **-i IP**, --ip IP        | Device IP address
- **-u USERNAME**, --username USERNAME
                      | Device Account Username
- **-p PASSWORD**, --password PASSWORD
                      | Device Account Password
- **-a API_KEY**, --api_key API_KEY
                     | Device Account API Key
- **-k SECRET_KEY_PATH**, --secret_key_path SECRET_KEY_PATH
                     | Device Account Secret Key (path to file)
- **-t** {**ucsm**,**cimc**, **ucsc**, **intersight**}, --device_type {ucsm,cimc,ucsc,intersight}
                      | Device type ("ucsm", "cimc", "ucsc" or "intersight")
- **-v**, --verbose         | Print debug log
- **-l LOGFILE**, --logfile LOGFILE
                    | Print log in a file
- **-o OUTPUT_CONFIG**, --out OUTPUT_CONFIG
                    | Output config file
- **-y**, --yes             | Answer yes to all questions
