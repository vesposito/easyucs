# coding: utf-8
# !/usr/bin/env python

""" cpu.py: Easy UCS Deployment Tool """
import re

from inventory.object import GenericInventoryObject


class GenericCpu(GenericInventoryObject):
    def __init__(self, parent=None):
        GenericInventoryObject.__init__(self, parent=parent)

        self.family_name = None
        self.model_short_name = None
        self.sku = None

    def _get_model_short_name(self):
        """
        Returns CPU short name from Model
        """
        if hasattr(self, "model"):
            if self.model is not None:
                if "AMD EPYC" in self.model:
                    # We have an AMD processor. Getting its model short name
                    regex_amd = r"EPYC (\d*)"
                    res_amd = re.search(regex_amd, self.model)
                    if res_amd is not None:
                        self.model_short_name = res_amd.group(1)
                    if self.model_short_name[-1] == "1":
                        self.family_name = "AMD EPYC 7001 Series Processors"
                    elif self.model_short_name[-1] == "2":
                        self.family_name = "2nd Gen AMD EPYC 7002 Series Processors"
                    elif self.model_short_name[-1] == "3":
                        self.family_name = "3rd Gen AMD EPYC 7003 Series Processors"
                    elif self.model_short_name[-1] == "4":
                        self.family_name = "4th Gen AMD EPYC 9004 Series Processors"
                    elif self.model_short_name[-1] == "5":
                        self.family_name = "5th Gen AMD EPYC 9005 Series Processors"

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
                    else:
                        # We might have an M5/M6 Intel CPU
                        regex2 = r"Xeon\(R\) .* (\d*\w?) CPU"
                        res2 = re.search(regex2, self.model)
                        if res2 is not None:
                            self.model_short_name = res2.group(1)
                            if self.model_short_name[1:2] == "1":
                                self.family_name = "Intel Xeon Processor Scalable Family"
                            elif self.model_short_name[1:2] == "2":
                                self.family_name = "2nd Gen Intel Xeon Processor Scalable Family"
                            elif self.model_short_name[1:2] == "3":
                                self.family_name = "3rd Gen Intel Xeon Processor Scalable Family"

                        else:
                            # We might have an M7 4th Gen Intel CPU
                            regex2 = r"Xeon\(R\) .* (\d*\w?\+?)"
                            res2 = re.search(regex2, self.model)
                            if res2 is not None:
                                self.model_short_name = res2.group(1)
                                if self.model_short_name[1:2] == "4":
                                    self.family_name = "4th Gen Intel Xeon Processor Scalable Family"

                            else:
                                # We might have an M7 5th Gen Intel CPU
                                regex3 = r"INTEL\(R\) XEON\(R\) .* (\d*\w?\+?)"
                                res3 = re.search(regex3, self.model)
                                if res3 is not None:
                                    self.model_short_name = res3.group(1)
                                    if self.model_short_name[1:2] == "5":
                                        self.family_name = "5th Gen Intel Xeon Processor Scalable Family"

                                else:
                                    # We might have an M8 Intel Xeon 6 CPU
                                    regex4 = r"Intel\(R\) Xeon\(R\) (\d*[EP])"
                                    res4 = re.search(regex4, self.model)
                                    if res4 is not None:
                                        self.model_short_name = res4.group(1)
                                        if self.model_short_name[-1] == "P":
                                            self.family_name = "Intel Xeon 6"
