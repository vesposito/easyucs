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
* create [Technical Architecture Documentation (TAD)](docs/REPORT.md) in Word format

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
EasyUCS can either be installed locally to a directory or using a Python
package management tool like `pip`. Outside of testing and development, `pip`
is the preferred method.

#### Using Pip
Pip can be install the current version directly from a link to the GitHub repository, like
- with Linux or Mac OSX
```
pip install https://github.com/vesposito/easyucs.git
```
- with Windows
```
python -m pip install https://github.com/vesposito/easyucs.git
```

It can also be used to install from a locally downloaded copy of the package. Instructions for downloading manually are in the next section.
- with Linux or Mac OSX
```
pip install path/to/local/copy
```

- with Windows
```
python -m pip install path/to/local/copy
```

#### Downloading Manually

##### From GitHub
Click *"Clone or Download"* and *"Download ZIP"* on the GitHub website to download the whole project.

Uncompress the zip and put the folder on your system. Commands under *Running
EasyUCS* below can be run from the root of the uncompressed folder.

##### From Git command line
You need to have Git on your system (not necessarily installed by default on all types of system).

Navigate to your desired path where you want EasyUCS to be placed on and clone it through your command-line console,

```
git clone https://github.com/vesposito/easyucs.git
```

Again, commands below can be run from the root of the downloaded repository.

## Requirements

EasyUCS requires some Python modules dependencies. The file **[setup.py](./setup.py)** contains these requirements.

**If you installed EasyUCS using Pip, this step is already complete.** Otherwise, you will need to install the dependencies either by hand, using Pip manually, or with your operating system package manager.

## Running EasyUCS

EasyUCS can be used with command line interface or via a Web GUI.


### Using the Command-Line Interface (CLI)

Push config file `config_ucsm.json` to UCS system
```
python -m easyucs.easyucs config push -t ucsm -i 192.168.0.1 -u admin -p password -f configs/config_ucsm.json
```

Reset UCS IMC and push config file `config_cimc.json`
```
python -m easyucs.easyucs config push -t cimc -i 192.168.0.2 -u admin -p password -f configs/config_cimc.json -r
```

Reset UCS system, perform initial setup using DHCP IP addresses `192.168.0.11` & `192.168.0.12` and push config file `config_ucsm.json`
```
python -m easyucs.easyucs config push -t ucsm -f configs/config_ucsm.json -r -s 192.168.0.11 192.168.0.12
```

Fetch config from UCS system and save it to `output/configs/config_ucsm.json`
```
python -m easyucs.easyucs config fetch -t ucsm -i 192.168.0.1 -u admin -p password -o output/configs/config_ucsm.json
```


Fetch inventory from UCS IMC and save it to `output/inventories/inventory_cimc.json`
```
python -m easyucs.easyucs inventory fetch -t cimc -i 192.168.0.2 -u admin -p password -o output/inventories/inventory_cimc.json
```

Create schemas from UCS system and save them to `output/schemas` folder
```
python -m easyucs.easyucs schemas create -t ucsm -i 192.168.0.1 -u admin -p password -o output/schemas
```

Create report from UCS system and save it to `output/reports` folder
```
python -m easyucs.easyucs report generate -t ucsm -i 192.168.0.1 -u admin -p password -o output/reports
```

#### Using the Web Graphical User Interface (GUI)

The Web GUI is hosted by your machine, in order to launch it you need to use the **[easyucs_gui module](./easyucs/easyucs_gui.py)**.

```
python -m easyucs.easyucs_gui
```


## Built With

* [ucsmsdk](https://github.com/CiscoUcs/ucsmsdk) - The UCS Manager Python SDK
* [imcsdk](https://github.com/CiscoUcs/imcsdk) - The UCS IMC Python SDK
* [ucscsdk](https://github.com/CiscoUcs/ucscsdk) - The UCS Central Python SDK


## Versioning

#### 0.9.4

* Add support for "comment" field in all sections of a configuration file for easily add comments to specific items of a configuration
* Add support for Fabric Interconnect port licenses in inventory and report
* Add support for 1st Gen Fabric Interconnects 6120XP/6140XP
* Add support for UCS Central inventory fetch (will fetch inventories of all registered domains)
* Support up to 32 Service Profile Templates when generating schemas
* Bump up requirements packages versions
* Miscellaneous bug fixes and improvements


#### 0.9.3

* Include Storage Enclosures & drives of S3260 in report
* Add support for UEFI Boot Parameters in SAN Boot (Boot Policies)
* Remove admin password from report (for security reasons)
* Change "generate report" command argument to specify directory instead of report file name. All required files will be written in that directory
* Automatically export config & inventory to JSON files when generating report
* Lots of bug fixes and improvements


#### 0.9.2

* Include portions of Logical Configuration in Technical Architecture Documentation, including Networking, Organizations, Identities and Service Profiles
* Add support for Dynamic vNIC Connection Policies in UCS Manager
* Add preliminary support for S3260 in IMC for config fetch/push - works for single server node only for now
* Add support for C4200 and C125 server node
* Various bug fixes and improvements

#### 0.9.1

* Add automatic Technical Architecture Documentation creation (containing detailed inventory and architecture schemas)
* Add support for LAN & SAN Global Policies in UCS Manager (VLAN Port Count Optimization, VLAN Org Permissions, Inband Profile)
* Rework of NVMe drives support in inventory (now displayed in its own nvme_drives section instead of being in storage_controllers)
* Add support for IOM 2408, HXAF220C All NVMe, C480 M5 ML
* Various bug fixes and improvements

#### 0.9.0

Initial release

## Authors

* **Marc Abu El Ghait** - *Initial work* - [github account link](https://github.com/marc-aeg)
* **Franck Bonneau** - *Initial work* - [github account link](https://github.com/Franck-Bonneau)
* **Vincent Esposito** - *Initial work* - [github account link](https://github.com/vesposito)

See also the list of [contributors](https://github.com/vesposito/easyucs/contributors) who participated in this project.

## License

This project is licensed under the GPLv2 License - see the [LICENSE](LICENSE) file for details
