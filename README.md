# EasyUCS

EasyUCS is a toolbox to help deploy and manage Cisco UCS devices.

It can :

* [deploy a configuration](docs/CONFIG.md) on a running UCS device:
    - UCS system (UCS Manager)
    - UCS IMC (Integrated Management Controller) for standalone servers
    - UCS Central
* perform the initial setup of an "out of the box" UCS device (UCSM or CIMC)
* reset the configuration of an UCS device before configuring it
* fetch a configuration and export it in JSON format
* [fetch an inventory](docs/INVENTORY.md) and export it in JSON format
* create pictures of equipment and infrastructure [schemas](docs/SCHEMAS.md)
* create Technical Architecture Documentation (TAD) in Word format

## Getting Started

These instructions will get you a copy of the project up and running on your local machine.

### Prerequisites

Minimum versions of UCS devices :

* UCS Manager: ***3.2(1d)*** or above
* UCS IMC: ***3.0(1c)*** or above
* UCS Central: ***2.0(1a)*** or above

This tool requires ***Python 3.x*** to work. *Python 2.x* is not supported.

Python can be used on Windows, Linux/Unix, Mac OS X and more.

You can download the latest version of *Python 3* on the [official website](https://www.python.org/downloads/).

### Installing
EasyUCS can be installed using any of ways below:

#### From GitHub
Click *"Clone or Download"* and *"Download ZIP"* on the GitHub website to download the whole project. 

Uncompress the zip and put the folder on your system. 

#### From Git command line

You need to have Git on your system (not necessarily installed by default on all types of system).

Navigate to your desired path where you want EasyUCS to be placed on and clone it through your command-line console,

```
git clone https://github.com/vesposito/easyucs.git
```

## Requirements

EasyUCS requires some Python modules dependencies. The file **[requirements.txt](./requirements.txt)** contains all of these requirements.

Use Python Pip to install all of them.

- for Max OS X, Unix, Linux:
```
pip install -r requirements.txt
```

- for Windows:
```
python -m pip install -r requirements.txt
```

## Running EasyUCS

EasyUCS can be used with command line interface or via a Web GUI.


### Using the Command-Line Interface (CLI)

Push config file config_ucsm.json to UCS system
```
python easyucs.py config push -t ucsm -i 192.168.0.1 -u admin -p password -f configs/config_ucsm.json
```

Reset UCS IMC and push config file config_cimc.json
```
python easyucs.py config push -t cimc -i 192.168.0.2 -u admin -p password -f configs/config_cimc.json -r
```

Reset UCS system, perform initial setup using DHCP IP addresses 192.168.0.11 & 192.168.0.12 and push config file config_ucsm.json
```
python easyucs.py config push -t ucsm -f configs/config_ucsm.json -r -s 192.168.0.11 192.168.0.12
```

Fetch config from UCS system and save it to configs/config_ucsm.json
```
python easyucs.py config fetch -t ucsm -i 192.168.0.1 -u admin -p password -o configs/config_ucsm.json
```


Fetch inventory from UCS IMC and save it to inventories/inventory_cimc.json
```
python easyucs.py inventory fetch -t cimc -i 192.168.0.2 -u admin -p password -o inventories/inventory_cimc.json
```

Create schemas from UCS system and save them to schemas folder
```
python easyucs.py schemas create -t ucsm -i 192.168.0.1 -u admin -p password -o schemas
```

Create report from UCS system and save it to reports/report.docx
```
python easyucs.py report generate -t ucsm -i 192.168.0.1 -u admin -p password -o reports/report.docx
```

#### Using the Web Graphical User Interface (GUI)

The Web GUI is hosted by your machine, in order to launch it you need to use the file **[easyucs_gui.py](./easyucs_gui.py)**.

```
python easyucs_gui.py
```


## Built With

* [ucsmsdk](https://github.com/CiscoUcs/ucsmsdk) - The UCS Manager Python SDK
* [imcsdk](https://github.com/CiscoUcs/imcsdk) - The UCS IMC Python SDK
* [ucscsdk](https://github.com/CiscoUcs/ucscsdk) - The UCS Central Python SDK


## Versioning

#### 0.9.1

* Add automatic Technical Architecture Documentation creation (containing detailed inventory and architecture schemas)
* Add support for LAN & SAN Global Policies in UCS Manager (VLAN Port Count Optimization, VLAN Org Permissions, Inband Profile)
* Rework of NVMe drives support in inventory (now displayed in its own nvme_drives section instead of being in storage_controllers)
* Add support for IOM 2408, HXAF220C All NVMe, C480 M5 ML
* Various bug fixes and improvements

#### 0.9.0

Initial release

## Authors

* **Marc Abu El Ghait** - *Initial work*
* **Franck Bonneau** - *Initial work* - [github account link](https://github.com/Franck-Bonneau)
* **Vincent Esposito** - *Initial work* - [github account link](https://github.com/vesposito)

See also the list of [contributors](https://github.com/vesposito/easyucs/contributors) who participated in this project.

## License

This project is licensed under the GPLv2 License - see the [LICENSE](LICENSE) file for details
