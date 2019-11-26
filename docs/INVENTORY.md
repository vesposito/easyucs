# Working with inventory files

Inventory files can be fetched from a UCS device. They are JSON-formatted files that are meant to be **human-readable** with each section corresponding to a UCS equipment.


## Fetch inventories

### Using the Command-Line Interface (CLI)

The **[easyucs module](../easyucs/easyucs.py)** is the main module that you will use.
You can have find help at each step by entering the **"-h"** argument.

It first needs the type of scope of action you want to use as an argument.
The scope of action:
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
  {fetch,push}  Inventory actions
    fetch       Fetch an inventory from a UCS device
```

#### Arguments for an inventory fetch

List of arguments :

- **-h**, --help            | show this help message and exit
- **-i IP**, --ip IP        | UCS IP address
- **-u USERNAME**, --username USERNAME
                    | UCS Account Username
- **-p PASSWORD**, --password PASSWORD
                    | UCS Account Password
- **-t** {**ucsm**,**cimc**}, --ucstype {ucsm,cimc}
                    | UCS system type ("ucsm" or "cimc")
- **-v**, --verbose         | Print debug log
- **-l LOGFILE**, --logfile LOGFILE
                    | Print log in a file
- **-o OUTPUT_CONFIG**, --out OUTPUT_CONFIG
                    | Output config file
- **-y**, --yes             | Answer yes to all questions
