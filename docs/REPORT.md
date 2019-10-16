# Infrastructure & equipment report generation

EasyUCS can generate infrastructure & equipment report from a live device.


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
  {generate}  Report actions
    generate  Generate report of an UCS device
```

#### Arguments for report generation

List of arguments :

- **-h**, --help            | show this help message and exit
- **-i IP**, --ip IP        | UCS IP address
- **-u USERNAME**, --username USERNAME
                    | UCS Account Username
- **-p PASSWORD**, --password PASSWORD
                    | UCS Account Password
- **-t** {**ucsm**,**cimc**}, --ucstype {ucsm,cimc}
                    | UCS system type ("ucsm" or "cimc")
- **-s** {**a4**,**letter**}, --layoutsize {a4,letter}
                    | Report layout size ("a4" or "letter")
- **-v**, --verbose         | Print debug log
- **-l LOGFILE**, --logfile LOGFILE
                    | Print log in a file
- **-o OUTPUT_DIRECTORY**, --out OUTPUT_DIRECTORY
                    | Output report directory
- **-y**, --yes             | Answer yes to all questions
