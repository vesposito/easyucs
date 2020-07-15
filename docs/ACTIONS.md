# Maintenance actions on devices

EasyUCS can perform maintenance actions on a live device, like:
* Regenerate expired self-signed certificate on a UCS system
* Clear SEL Logs of a UCS IMC / of all discovered servers on a UCS system
* Clear all user sessions of a UCS IMC / UCS system / UCS central


## Device actions

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
  {regenerate_certificate,clear_sel_logs,clear_user_sessions}
                        Device actions

    regenerate_certificate  Regenerate self-signed certificate of an UCS system
    clear_sel_logs          Clears all SEL logs of an UCS device
    clear_user_sessions     Clears all user sessions of an UCS device
```

#### Arguments for a device action

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
- **-y**, --yes             | Answer yes to all questions
