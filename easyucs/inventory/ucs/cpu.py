# coding: utf-8
# !/usr/bin/env python

""" adaptor.py: Easy UCS Deployment Tool """
from easyucs import __author__, __copyright__,  __version__, __status__


import re
from easyucs.inventory.object import GenericUcsInventoryObject, UcsImcInventoryObject, UcsSystemInventoryObject


class UcsCpu(GenericUcsInventoryObject):
    _UCS_SDK_OBJECT_NAME = "processorUnit"

    def __init__(self, parent=None, processor_unit=None):
        GenericUcsInventoryObject.__init__(self, parent=parent, ucs_sdk_object=processor_unit)

        self.arch = self.get_attribute(ucs_sdk_object=processor_unit, attribute_name="arch")
        self.cores = self.get_attribute(ucs_sdk_object=processor_unit, attribute_name="cores", attribute_type="int")
        self.cores_enabled = self.get_attribute(ucs_sdk_object=processor_unit, attribute_name="cores_enabled",
                                                attribute_type="int")
        self.id = self.get_attribute(ucs_sdk_object=processor_unit, attribute_name="id")
        self.model = self.get_attribute(ucs_sdk_object=processor_unit, attribute_name="model")
        self.speed = self.get_attribute(ucs_sdk_object=processor_unit, attribute_name="speed")
        self.threads = self.get_attribute(ucs_sdk_object=processor_unit, attribute_name="threads", attribute_type="int")
        self.vendor = self.get_attribute(ucs_sdk_object=processor_unit, attribute_name="vendor")

        self.model_short_name = None
        if self.model is not None:
            if "AMD EPYC" in self.model:
                # We have an AMD processor. Getting its model short name
                regex_amd = r"EPYC (\d*)"
                res_amd = re.search(regex_amd, self.model)
                if res_amd is not None:
                    self.model_short_name = res_amd.group(1)
                self.family_name = "AMD EPYC E7 Series processors"

            else:
                # We have an Intel processor. Getting its model short name
                regex = r"CPU *([EX].*\d) *@"
                res = re.search(regex, self.model)
                if res is not None:
                    self.model_short_name = res.group(1)
                    # Remove trailing 0 for E5-2XXX processors models
                    if self.model_short_name.endswith(" 0"):
                        self.model_short_name = self.model_short_name[:-2]
                    # Fix catalog issue for E7-8867L processor model
                    if self.model_short_name == "E7-L8867":
                        self.model_short_name = "E7-8867L"
                    # Remove extra space for E7-XXXX processors models
                    if "- " in self.model_short_name:
                        self.model_short_name = self.model_short_name.replace("- ", "-")
                        if self.model_short_name[:5] == "E7-28":
                            self.family_name = "Intel Xeon E7-2800 Series processors"
                        elif self.model_short_name[:5] == "E7-48":
                            self.family_name = "Intel Xeon E7-4800 Series processors"
                        elif self.model_short_name[:5] == "E7-88":
                            self.family_name = "Intel Xeon E7-8800 Series processors"
                else:
                    # We might have an M5 Intel CPU
                    regex2 = r"Xeon\(R\) .* (\d*\w?) CPU"
                    res2 = re.search(regex2, self.model)
                    if res2 is not None:
                        self.model_short_name = res2.group(1)
                        if self.model_short_name[1:2] == "1":
                            self.family_name = "Intel Xeon Processor Scalable Family"
                        elif self.model_short_name[1:2] == "2":
                            self.family_name = "2nd Gen Intel Xeon Processor Scalable Family"

                if self.model_short_name is not None:
                    if self.model_short_name[:5] == "E5-24":
                        if self.model_short_name[-2:] == "v2":
                            self.family_name = "Intel Xeon E5-2400 v2 Series processors"
                        else:
                            self.family_name = "Intel Xeon E5-2400 Series processors"
                    elif self.model_short_name[:5] == "E5-26":
                        if self.model_short_name[-2:] == "v2":
                            self.family_name = "Intel Xeon E5-2600 v2 Series processors"
                        elif self.model_short_name[-2:] == "v3":
                            self.family_name = "Intel Xeon E5-2600 v3 Series processors"
                        elif self.model_short_name[-2:] == "v4":
                            self.family_name = "Intel Xeon E5-2600 v4 Series processors"
                        else:
                            self.family_name = "Intel Xeon E5-2600 Series processors"
                    elif self.model_short_name[:5] == "E5-46":
                        if self.model_short_name[-2:] == "v2":
                            self.family_name = "Intel Xeon E5-4600 v2 Series processors"
                        elif self.model_short_name[-2:] == "v3":
                            self.family_name = "Intel Xeon E5-4600 v3 Series processors"
                        elif self.model_short_name[-2:] == "v4":
                            self.family_name = "Intel Xeon E5-4600 v4 Series processors"
                        else:
                            self.family_name = "Intel Xeon E5-4600 Series processors"
                    elif self.model_short_name[:5] == "E7-28":
                        if self.model_short_name[-2:] == "v2":
                            self.family_name = "Intel Xeon E7-2800 v2 Series processors"
                        else:
                            self.family_name = "Intel Xeon E7-2800 Series processors"
                    elif self.model_short_name[:5] == "E7-48":
                        if self.model_short_name[-2:] == "v2":
                            self.family_name = "Intel Xeon E7-4800 v2 Series processors"
                        elif self.model_short_name[-2:] == "v3":
                            self.family_name = "Intel Xeon E7-4800 v3 Series processors"
                        elif self.model_short_name[-2:] == "v4":
                            self.family_name = "Intel Xeon E7-4800 v4 Series processors"
                        else:
                            self.family_name = "Intel Xeon E7-4800 Series processors"
                    elif self.model_short_name[:5] == "E7-88":
                        if self.model_short_name[-2:] == "v2":
                            self.family_name = "Intel Xeon E7-8800 v2 Series processors"
                        elif self.model_short_name[-2:] == "v3":
                            self.family_name = "Intel Xeon E7-8800 v3 Series processors"
                        elif self.model_short_name[-2:] == "v4":
                            self.family_name = "Intel Xeon E7-8800 v4 Series processors"
                        else:
                            self.family_name = "Intel Xeon E7-8800 Series processors"
                    elif len(self.model_short_name) == 5:
                        if self.model_short_name[1:3] == "55":
                            self.family_name = "Intel Xeon 5500 Series processors"
                        elif self.model_short_name[1:3] == "56":
                            self.family_name = "Intel Xeon 5600 Series processors"
                        elif self.model_short_name[1:3] == "65":
                            self.family_name = "Intel Xeon 6500 Series processors"
                        elif self.model_short_name[1:3] == "75":
                            self.family_name = "Intel Xeon 7500 Series processors"


class UcsSystemCpu(UcsCpu, UcsSystemInventoryObject):
    _UCS_SDK_CATALOG_OBJECT_NAME = "equipmentProcessorUnitCapProvider"

    def __init__(self, parent=None, processor_unit=None):
        UcsCpu.__init__(self, parent=parent, processor_unit=processor_unit)

        self.revision = self.get_attribute(ucs_sdk_object=processor_unit, attribute_name="revision")

        if self._inventory.load_from == "live":
            # We convert the speed from GHz to MHz and change it to integer in order to have a consistent value with IMC
            if self.speed != 'unspecified':
                self.speed = int(float(self.speed) * 1000)

        UcsSystemInventoryObject.__init__(self, parent=parent, ucs_sdk_object=processor_unit)


class UcsImcCpu(UcsCpu, UcsImcInventoryObject):
    _UCS_SDK_CATALOG_OBJECT_NAME = "pidCatalogCpu"
    _UCS_SDK_CATALOG_IDENTIFY_ATTRIBUTE = "id"
    _UCS_SDK_OBJECT_IDENTIFY_ATTRIBUTE = "id"

    def __init__(self, parent=None, processor_unit=None):
        UcsCpu.__init__(self, parent=parent, processor_unit=processor_unit)

        if self._inventory.load_from == "live":
            # We convert the speed string to integer
            if self.speed != 'unspecified':
                self.speed = int(self.speed)

        UcsImcInventoryObject.__init__(self, parent=parent, ucs_sdk_object=processor_unit)
