# Infrastructure & equipment schemas creation

EasyUCS can generate infrastructure & equipment schemas from a live device.

The following schemas are generated:
* Front & rear view of chassis including i/o modules and blades
* Front & rear view of rack servers including adapters
* Front & rear view of fabric interconnects & fabric extenders
* Infrastructure view of each chassis & rack server with its physical connectivity to the fabric interconnects
* Infrastructure view of LAN neighbors connected to the fabric interconnects
* Infrastructure view of SAN neighbors connected to the fabric interconnects
* Service Profile deployment view


## Schemas creation

### Using the Command-Line Interface (CLI)

The file **[easyucs.py](../easyucs.py)** is the main file that you will use. 
You can find help at each step by entering the **"-h"** argument.

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
  {create}    Schemas actions
    create    Create schemas of an UCS device
```

#### Arguments for schemas creation

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
- **-o OUTPUT_DIRECTORY**, --out OUTPUT_DIRECTORY
                    | Output schemas directory
- **-c CLEAR_PICTURES**, --clear CLEAR_PICTURES
                    | Export clear pictures (without colored ports)
- **-y**, --yes             | Answer yes to all questions
