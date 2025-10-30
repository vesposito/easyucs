# coding: utf-8
# !/usr/bin/env python

""" pools.py: Easy UCS Deployment Tool """

import copy
import ipaddress
import re
import uuid

from config.intersight.object import IntersightConfigObject
from common import format_descr


def _find_overlapping_reservations(existing_reservations=None, to_be_pushed_reservations=None, used_identities=None):
    """
    Function to find the overlapping, non overlapping and used reservations between the live device and the config file
    :param existing_reservations: Object of type [fcpool.Reservation, iqnpool.Reservation...]
    :param to_be_pushed_reservations: List of reservations from the config file
    :param used_identities: List of identities which are already used by some profile
    :return: overlapping_reservations, non overlapping_reservations and used_reservations lists (sorted by Identity)
    """
    # If there are no 'existing_reservations' then there are no overlapping reservations and all are non
    # overlapping reservations. And if there are no 'to_be_pushed_reservations' then also there are no
    # overlapping reservations.
    if not existing_reservations or not to_be_pushed_reservations:
        return [], to_be_pushed_reservations, []

    overlapping_reservations = []
    non_overlapping_reservations = []
    used_reservations = []

    existing_identities = dict([(getattr(reservation, "identity", None),
                                 getattr(reservation.organization, "name", None))
                                for reservation in existing_reservations])
    for reservation in to_be_pushed_reservations:
        if reservation["identity"] in existing_identities:
            reservation["organization"] = existing_identities[reservation["identity"]]
            overlapping_reservations.append(reservation)
        elif reservation["identity"] in used_identities:
            used_reservations.append(reservation)
        else:
            non_overlapping_reservations.append(reservation)

    overlapping_reservations.sort(key=lambda reservation: reservation["identity"])
    non_overlapping_reservations.sort(key=lambda reservation: reservation["identity"])
    used_reservations.sort(key=lambda reservation: reservation["identity"])

    return overlapping_reservations, non_overlapping_reservations, used_reservations


class IntersightIpPool(IntersightConfigObject):
    _CONFIG_NAME = "IP Pool"
    _CONFIG_SECTION_NAME = "ip_pools"
    _INTERSIGHT_SDK_OBJECT_NAME = "ippool.Pool"

    def __init__(self, parent=None, ippool_pool=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=ippool_pool)

        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.ipv4_blocks = []
        self.ipv6_blocks = []
        self.ipv4_configuration = None
        self.ipv6_configuration = None
        self.name = self.get_attribute(attribute_name="name")
        self.reservations = []
        self.configure_subnet_at_block_level = self.get_attribute(attribute_name="enable_block_level_subnet_config",
                                                                  attribute_secondary_name="configure_subnet_at_block_"
                                                                                           "level")
        if self._config.load_from == "live":
            # Fetches the common IPv4 configuration parameters of the IP Pool (netmask, gateway and DNS servers)
            if hasattr(self._object, "ip_v4_config"):
                self.ipv4_configuration = {}
                ipv4_config = self._object.ip_v4_config

                if ipv4_config.netmask:
                    self.ipv4_configuration["netmask"] = ipv4_config.netmask
                if ipv4_config.gateway:
                    self.ipv4_configuration["gateway"] = ipv4_config.gateway
                if ipv4_config.primary_dns:
                    self.ipv4_configuration["primary_dns"] = ipv4_config.primary_dns
                if ipv4_config.secondary_dns:
                    self.ipv4_configuration["secondary_dns"] = ipv4_config.secondary_dns

                # Makes sure that the IPv4 configuration is not empty
                if not self.ipv4_configuration:
                    self.ipv4_configuration = None

            # Fetches the common IPv6 configuration parameters of the IP Pool (prefix, gateway and DNS servers)
            if hasattr(self._object, "ip_v6_config"):
                self.ipv6_configuration = {}
                ipv6_config = self._object.ip_v6_config

                if ipv6_config.prefix:
                    self.ipv6_configuration["prefix"] = ipv6_config.prefix
                if ipv6_config.gateway:
                    self.ipv6_configuration["gateway"] = ipv6_config.gateway
                if ipv6_config.primary_dns:
                    self.ipv6_configuration["primary_dns"] = ipv6_config.primary_dns
                if ipv6_config.secondary_dns:
                    self.ipv6_configuration["secondary_dns"] = ipv6_config.secondary_dns

            # Makes sure that the IPv6 configuration is not empty
            if not self.ipv6_configuration:
                self.ipv6_configuration = None

            # Fetches the IPv4 Blocks configurations
            if hasattr(self._object, "ip_v4_blocks"):
                for ipv4_block in self._object.ip_v4_blocks:
                    if self.configure_subnet_at_block_level:
                        # Add ipv4_configuration to ipv4_block if block level subnet configuration is enabled
                        if ipv4_block.ip_v4_config:
                            ipv4_configuration = {
                                "gateway": ipv4_block.ip_v4_config.gateway,
                                "netmask": ipv4_block.ip_v4_config.netmask,
                                "primary_dns": ipv4_block.ip_v4_config.primary_dns,
                                "secondary_dns": ipv4_block.ip_v4_config.secondary_dns
                            }
                            self.ipv4_blocks.append({"from": ipv4_block._from, "ipv4_configuration": ipv4_configuration,
                                                     "to": ipv4_block.to})

                    else:
                        self.ipv4_blocks.append({"from": ipv4_block._from, "to": ipv4_block.to})

            # Fetches the IPv6 Blocks configurations
            if hasattr(self._object, "ip_v6_blocks"):
                for ipv6_block in self._object.ip_v6_blocks:
                    if self.configure_subnet_at_block_level:
                        # Add ipv6_configuration to ipv6_block if block level subnet configuration is enabled
                        if ipv6_block.ip_v6_config:
                            ipv6_configuration = {
                                "gateway": ipv6_block.ip_v6_config.gateway,
                                "prefix": ipv6_block.ip_v6_config.prefix,
                                "primary_dns": ipv6_block.ip_v6_config.primary_dns,
                                "secondary_dns": ipv6_block.ip_v6_config.secondary_dns
                            }
                            self.ipv6_blocks.append({"from": ipv6_block._from, "ipv6_configuration": ipv6_configuration,
                                                     "to": ipv6_block.to})
                    else:
                        self.ipv6_blocks.append({"from": ipv6_block._from, "to": ipv6_block.to})

            # Fetches the IP reservations
            self.reservations = self._get_reservations()

        elif self._config.load_from == "file":
            for attribute in ["ipv4_blocks", "ipv4_configuration", "ipv6_blocks", "ipv6_configuration", "reservations"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

        self.clean_object()

    def clean_object(self):
        # We use this to make sure all options of the IPv4 configuration are set to None if they are not present
        for attribute in ["gateway", "netmask", "primary_dns", "secondary_dns"]:
            if self.ipv4_configuration:
                if attribute not in self.ipv4_configuration:
                    self.ipv4_configuration[attribute] = None

        # We use this to make sure all options of the IPv6 configuration are set to None if they are not present
        for attribute in ["gateway", "prefix", "primary_dns", "secondary_dns"]:
            if self.ipv6_configuration:
                if attribute not in self.ipv6_configuration:
                    self.ipv6_configuration[attribute] = None

        # We use this to make sure all options of a reservations are set to None if they are not present
        if self.reservations:
            for reservation in self.reservations:
                for attribute in ["identity", "ip_type"]:
                    if attribute not in reservation:
                        reservation[attribute] = None

    def _find_overlapping_reservations(self, existing_reservations=None, to_be_pushed_reservations=None):
        ip_used = self._device.query(object_type="ippool.PoolMember", filter="Assigned eq true")

        ip_used_identities = []
        for pool_member in ip_used:
            if pool_member.ip_v4_address:
                ip_used_identities.append(pool_member.ip_v4_address)
            elif pool_member.ip_v6_address:
                ip_used_identities.append(pool_member.ip_v6_address)

        return _find_overlapping_reservations(existing_reservations=existing_reservations,
                                              to_be_pushed_reservations=to_be_pushed_reservations,
                                              used_identities=ip_used_identities)

    def _get_reservations(self):
        # Fetches the Reservations of an IP Pool
        if "ippool_reservation" in self._config.sdk_objects:
            reservations = []
            for reservation in self._config.sdk_objects["ippool_reservation"]:
                if hasattr(reservation, "pool"):
                    if reservation.pool.moid == self._moid:
                        reservations.append({"identity": reservation.identity, "ip_type": reservation.ip_type})

            return reservations

        return None

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.ippool_pool import IppoolPool

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        ipv4_config = None
        # get pool-level ipv4_configuration
        if self.ipv4_configuration:
            from intersight.model.ippool_ip_v4_config import IppoolIpV4Config
            kwargs = {
                "object_type": "ippool.IpV4Config",
                "class_id": "ippool.IpV4Config",
            }
            if self.ipv4_configuration.get("gateway") is not None:
                kwargs["gateway"] = self.ipv4_configuration["gateway"]
            if self.ipv4_configuration.get("netmask") is not None:
                kwargs["netmask"] = self.ipv4_configuration["netmask"]
            if self.ipv4_configuration.get("primary_dns") is not None:
                kwargs["primary_dns"] = self.ipv4_configuration["primary_dns"]
            if self.ipv4_configuration.get("secondary_dns") is not None:
                kwargs["secondary_dns"] = self.ipv4_configuration["secondary_dns"]
            ipv4_config = IppoolIpV4Config(**kwargs)

        ipv6_config = None
        # get pool-level ipv6_configuration
        if self.ipv6_configuration:
            from intersight.model.ippool_ip_v6_config import IppoolIpV6Config
            kwargs = {
                "object_type": "ippool.IpV6Config",
                "class_id": "ippool.IpV6Config",
            }
            if self.ipv6_configuration.get("gateway") is not None:
                kwargs["gateway"] = self.ipv6_configuration["gateway"]
            if self.ipv6_configuration.get("prefix") is not None:
                kwargs["prefix"] = self.ipv6_configuration["prefix"]
            if self.ipv6_configuration.get("primary_dns") is not None:
                kwargs["primary_dns"] = self.ipv6_configuration["primary_dns"]
            if self.ipv6_configuration.get("secondary_dns") is not None:
                kwargs["secondary_dns"] = self.ipv6_configuration["secondary_dns"]
            ipv6_config = IppoolIpV6Config(**kwargs)

        ipv4_blocks = []
        if self.ipv4_blocks:
            from intersight.model.ippool_ip_v4_block import IppoolIpV4Block
            for ipv4_block in self.ipv4_blocks:
                kwargs = {
                    "object_type": "ippool.IpV4Block",
                    "class_id": "ippool.IpV4Block",
                    "_from": ipv4_block["from"]
                }
                if ipv4_block.get("to"):
                    kwargs["to"] = ipv4_block["to"]
                elif ipv4_block.get("size"):
                    kwargs["size"] = ipv4_block["size"]
                # Add ipv4_configuration to ipv4_block if block level subnet is defined
                if self.configure_subnet_at_block_level:
                    kwargs["ip_v4_config"] = ipv4_block["ipv4_configuration"]

                ipv4_blocks.append(IppoolIpV4Block(**kwargs))

        ipv6_blocks = []
        if self.ipv6_blocks:
            from intersight.model.ippool_ip_v6_block import IppoolIpV6Block
            for ipv6_block in self.ipv6_blocks:
                kwargs = {
                    "object_type": "ippool.IpV6Block",
                    "class_id": "ippool.IpV6Block",
                    "_from": ipv6_block["from"]
                }
                if ipv6_block.get("to"):
                    # Intersight doesn't have the support to generate IPv6 address using "To" option.
                    # Hence, "Size" of IPv6 range is being calculated for IPv6 generation
                    kwargs["size"] = int(ipaddress.IPv6Address(ipv6_block["to"])) - int(
                        ipaddress.IPv6Address(kwargs["_from"])) + 1
                elif ipv6_block.get("size"):
                    kwargs["size"] = ipv6_block["size"]
                # Add ipv6_configuration to ipv6_block if block level subnet is defined
                if self.configure_subnet_at_block_level:
                    kwargs["ip_v6_config"] = ipv6_block["ipv6_configuration"]

                ipv6_blocks.append(IppoolIpV6Block(**kwargs))

        org = self.get_parent_org_relationship()
        org_name = self._parent.name

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": org,
            "ip_v4_blocks": ipv4_blocks,
            "ip_v6_blocks": ipv6_blocks
        }
        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()
        if ipv4_config is not None:
            kwargs["ip_v4_config"] = ipv4_config
        if ipv6_config is not None:
            kwargs["ip_v6_config"] = ipv6_config
        if self.configure_subnet_at_block_level is not None:
            kwargs["enable_block_level_subnet_config"] = self.configure_subnet_at_block_level

        ippool_pool = IppoolPool(**kwargs)

        ippool = self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=ippool_pool, detail=self.name,
                             return_relationship=True)
        if not ippool:
            return False

        if not self.reservations:
            return True

        # Get all the IP Pool reservations
        ip_reservations = self._device.query(object_type="ippool.Reservation", expand="Organization")

        # Find overlapping, non overlapping and used reservations between ip_reservations and self.reservations
        overlapping_reservations, non_overlapping_reservations, used_reservations = self._find_overlapping_reservations(
            existing_reservations=ip_reservations,
            to_be_pushed_reservations=self.reservations
        )

        # Reservations which need to be newly created (Non Overlapping Reservations) are bulk pushed.
        if non_overlapping_reservations:
            # We now need to bulk push the ippool.Reservation object for each Reservation in the list
            from intersight.model.bulk_request import BulkRequest
            from intersight.model.bulk_sub_request import BulkSubRequest
            from intersight.model.mo_base_mo import MoBaseMo

            bulk_request_kwargs = {
                "uri": "/v1/ippool/Reservations",
                "verb": "POST",
                "requests": []
            }
            requests = []

            for reservation in non_overlapping_reservations:
                body_kwargs = {
                    "object_type": "ippool.Reservation",
                    "class_id": "ippool.Reservation",
                    "identity": reservation["identity"],
                    "ip_type": reservation["ip_type"],
                    "organization": org,
                    "pool": ippool
                }
                if self.tags is not None:
                    kwargs["tags"] = self.create_tags()

                body = MoBaseMo(**body_kwargs)

                sub_request_kwargs = {
                    "object_type": "bulk.RestSubRequest",
                    "class_id": "bulk.RestSubRequest",
                    "body": body
                }

                sub_request = BulkSubRequest(**sub_request_kwargs)

                requests.append(sub_request)

            # Bulk API can send maximum 100 requests per call. So we send the requests in groups of 100.
            start = 0
            end = 100
            while start < len(requests):
                start_identity = non_overlapping_reservations[start]["identity"]
                if end - 1 < len(non_overlapping_reservations):
                    end_identity = non_overlapping_reservations[end - 1]["identity"]
                else:
                    end_identity = non_overlapping_reservations[-1]["identity"]
                bulk_request_kwargs["requests"] = requests[start:end]
                bulk_request = BulkRequest(**bulk_request_kwargs)

                detail = f"{self.name} - {len(bulk_request_kwargs['requests'])} Reservations between identities " \
                         f"({start_identity}, {end_identity})"
                self.commit(object_type="bulk.Request", payload=bulk_request, detail=detail, key_attributes=[])
                start = end
                end += 100

        # These reservations already exist, so we skip them.
        if overlapping_reservations:
            for reservation in overlapping_reservations:
                if reservation["organization"] != org_name:
                    err_message = f"Failed to push object-type ippool.Reservation with identity "\
                                  f"{reservation['identity']} as it already exists in an org "\
                                  f"'{reservation['organization']}' different than the {self._CONFIG_NAME} org "\
                                  f"'{org_name}'."
                    push_status = "failed"
                    self.logger(level="error", message=err_message)
                else:
                    err_message = f"Skipping push of object-type ippool.Reservation with identity "\
                                  f"{reservation['identity']} as it already exists."
                    push_status = "skipped"
                    self.logger(level="warning", message=err_message)
                self._config.push_summary_manager.add_object_status(
                    obj=self, obj_detail=f"Reservation {reservation['identity']}", obj_type="ippool.Reservation",
                    status=push_status, message=err_message
                )

        # These reservations already in-use by some profile, so we skip them.
        if used_reservations:
            for reservation in used_reservations:
                err_message = f"Skipping push of object-type ippool.Reservation with identity "\
                              f"{reservation['identity']} as it's already in use."
                self.logger(level="warning", message=err_message)
                self._config.push_summary_manager.add_object_status(
                    obj=self, obj_detail=f"Reservation {reservation['identity']}", obj_type="ippool.Reservation",
                    status="skipped", message=err_message
                )

        return True


class IntersightIqnPool(IntersightConfigObject):
    _CONFIG_NAME = "IQN Pool"
    _CONFIG_SECTION_NAME = "iqn_pools"
    _INTERSIGHT_SDK_OBJECT_NAME = "iqnpool.Pool"

    def __init__(self, parent=None, iqnpool_pool=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=iqnpool_pool)

        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.iqn_blocks = []
        self.name = self.get_attribute(attribute_name="name")
        self.prefix = self.get_attribute(attribute_name="prefix")
        self.reservations = []

        if self._config.load_from == "live":
            # Fetches the IQN Blocks configurations
            if hasattr(self._object, "iqn_suffix_blocks"):
                for iqn_block in self._object.iqn_suffix_blocks:
                    self.iqn_blocks.append({"from": iqn_block._from, "suffix": iqn_block.suffix, "to": iqn_block.to})
            # Fetches the IQN reservations
            self.reservations = self._get_reservations()

        elif self._config.load_from == "file":
            for attribute in ["iqn_blocks", "reservations"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))
        self.clean_object()

    def clean_object(self):
        # We use this to make sure all options of an IQN Block are set to None if they are not present
        if self.iqn_blocks:
            for iqn_block in self.iqn_blocks:
                for attribute in ["from", "size", "suffix", "to"]:
                    if attribute not in iqn_block:
                        iqn_block[attribute] = None

        # We use this to make sure all options of a reservations are set to None if they are not present
        if self.reservations:
            for reservation in self.reservations:
                for attribute in ["identity"]:
                    if attribute not in reservation:
                        reservation[attribute] = None

    def _find_overlapping_reservations(self, existing_reservations=None, to_be_pushed_reservations=None):
        iqn_used = self._device.query(object_type="iqnpool.PoolMember", filter="Assigned eq true")

        iqn_used_identities = [pool_member.iqn_address for pool_member in iqn_used]

        return _find_overlapping_reservations(existing_reservations=existing_reservations,
                                              to_be_pushed_reservations=to_be_pushed_reservations,
                                              used_identities=iqn_used_identities)

    def _get_reservations(self):
        # Fetches the Reservations of a IQN Pool
        if "iqnpool_reservation" in self._config.sdk_objects:
            reservations = []
            for reservation in self._config.sdk_objects["iqnpool_reservation"]:
                if hasattr(reservation, "pool"):
                    if reservation.pool.moid == self._moid:
                        reservations.append({"identity": reservation.identity})
            return reservations

        return None

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.iqnpool_pool import IqnpoolPool

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        iqn_blocks = []
        if self.iqn_blocks:
            from intersight.model.iqnpool_iqn_suffix_block import IqnpoolIqnSuffixBlock
            for iqn_block in self.iqn_blocks:
                kwargs = {
                    "object_type": "iqnpool.IqnSuffixBlock",
                    "class_id": "iqnpool.IqnSuffixBlock",
                    "_from": iqn_block["from"]
                }
                if iqn_block.get("to"):
                    # kwargs["to"] = iqn_block["to"]
                    # Intersight doesn't have the support to generate IQN Pool block using "To" option.
                    # Hence, "Size" of IQN Pool range is being calculated for IQN Block generation
                    kwargs["size"] = int(iqn_block["to"]) - int(kwargs["_from"]) + 1

                elif iqn_block.get("size"):
                    kwargs["size"] = iqn_block["size"]
                if iqn_block.get("suffix"):
                    kwargs["suffix"] = iqn_block["suffix"]
                iqn_blocks.append(IqnpoolIqnSuffixBlock(**kwargs))

        org = self.get_parent_org_relationship()
        org_name = self._parent.name

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": org,
            "iqn_suffix_blocks": iqn_blocks
        }
        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()
        if self.prefix is not None:
            kwargs["prefix"] = self.prefix

        iqnpool_pool = IqnpoolPool(**kwargs)

        iqnpool = self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME,
                              payload=iqnpool_pool, detail=self.name, return_relationship=True)
        if not iqnpool:
            return False

        if not self.reservations:
            return True

        # Get the all the IQN Pool reservations
        iqn_reservations = self._device.query(object_type="iqnpool.Reservation", expand="Organization")

        # Find overlapping, non overlapping and used reservations between iqn_reservations and self.reservations
        overlapping_reservations, non_overlapping_reservations, used_reservations = self._find_overlapping_reservations(
            existing_reservations=iqn_reservations,
            to_be_pushed_reservations=self.reservations
        )

        # Reservations which need to be newly created (Non Overlapping Reservations) are individually pushed.
        successful_reservations_push = True
        if non_overlapping_reservations:
            from intersight.model.iqnpool_reservation import IqnpoolReservation
            for reservation in non_overlapping_reservations:
                kwargs = {
                    "object_type": "iqnpool.Reservation",
                    "class_id": "iqnpool.Reservation",
                    "identity": reservation["identity"],
                    "organization": org,
                    "pool": iqnpool
                }
                if self.tags is not None:
                    kwargs["tags"] = self.create_tags()
                iqnpool_reservation = IqnpoolReservation(**kwargs)

                if not self.commit(object_type="iqnpool.Reservation", payload=iqnpool_reservation,
                                   detail="Reservation " + reservation["identity"],
                                   key_attributes=["identity", "pool"]):
                    successful_reservations_push = False

        # TODO: Replace the above code with the below commented code once IQN Reservation Bulk Push issue is resolved
        # Reservations which need to be newly created (Non Overlapping Reservations) are bulk pushed.
        # if non_overlapping_reservations:
        #     # We now need to bulk push the iqnpool.Reservation object for each Reservation in the list
        #     from intersight.model.bulk_request import BulkRequest
        #     from intersight.model.bulk_sub_request import BulkSubRequest
        #     from intersight.model.mo_base_mo import MoBaseMo
        #
        #     bulk_request_kwargs = {
        #         "uri": "/v1/iqnpool/Reservations",
        #         "verb": "POST",
        #         "requests": []
        #     }
        #     requests = []
        #     from intersight.model.iqnpool_reservation import IqnpoolReservation
        #
        #     for reservation in non_overlapping_reservations:
        #         body_kwargs = {
        #             "object_type": "iqnpool.Reservation",
        #             "class_id": "iqnpool.Reservation",
        #             "identity": reservation["identity"],
        #             "organization": org,
        #             "pool": iqnpool
        #         }
        #         if self.tags is not None:
        #             kwargs["tags"] = self.create_tags()
        #
        #         body = MoBaseMo(**body_kwargs)
        #
        #         sub_request_kwargs = {
        #             "object_type": "bulk.RestSubRequest",
        #             "class_id": "bulk.RestSubRequest",
        #             "body": body
        #         }
        #
        #         sub_request = BulkSubRequest(**sub_request_kwargs)
        #
        #         requests.append(sub_request)
        #
        #     # Bulk API can send maximum 100 requests per call. So we send the requests in groups of 100.
        #     start = 0
        #     end = 100
        #     while start < len(requests):
        #         start_identity = non_overlapping_reservations[start]["identity"]
        #         if end - 1 < len(non_overlapping_reservations):
        #             end_identity = non_overlapping_reservations[end - 1]["identity"]
        #         else:
        #             end_identity = non_overlapping_reservations[-1]["identity"]
        #         bulk_request_kwargs["requests"] = requests[start:end]
        #         bulk_request = BulkRequest(**bulk_request_kwargs)
        #
        #         detail = f"{self.name} - {len(bulk_request_kwargs['requests'])} Reservations between identities " \
        #                  f"({start_identity}, {end_identity})"
        #         self.commit(object_type="bulk.Request", payload=bulk_request, detail=detail, key_attributes=[])
        #         start = end
        #         end += 100

        # These reservations already exist, so we skip them.
        if overlapping_reservations:
            for reservation in overlapping_reservations:
                if reservation["organization"] != org_name:
                    err_message = f"Failed to push object-type iqnpool.Reservation with identity "\
                                  f"{reservation['identity']} as it already exists in an org "\
                                  f"'{reservation['organization']}' different than the {self._CONFIG_NAME} org "\
                                  f"'{org_name}'."
                    push_status = "failed"
                    self.logger(level="error", message=err_message)
                else:
                    err_message = f"Skipping push of object-type iqnpool.Reservation with identity "\
                                  f"{reservation['identity']} as it already exists."
                    push_status = "skipped"
                    self.logger(level="warning", message=err_message)
                self._config.push_summary_manager.add_object_status(
                    obj=self, obj_detail=f"Reservation {reservation['identity']}", obj_type="iqnpool.Reservation",
                    status=push_status, message=err_message
                )

        # These reservations already in-use by some profile, so we skip them.
        if used_reservations:
            for reservation in used_reservations:
                err_message = f"Skipping push of object-type iqnpool.Reservation with identity "\
                              f"{reservation['identity']} as it's already in use."
                self.logger(level="warning", message=err_message)
                self._config.push_summary_manager.add_object_status(
                    obj=self, obj_detail=f"Reservation {reservation['identity']}", obj_type="iqnpool.Reservation",
                    status="skipped", message=err_message
                )

        return successful_reservations_push


class IntersightMacPool(IntersightConfigObject):
    _CONFIG_NAME = "MAC Pool"
    _CONFIG_SECTION_NAME = "mac_pools"
    _INTERSIGHT_SDK_OBJECT_NAME = "macpool.Pool"

    def __init__(self, parent=None, macpool_pool=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=macpool_pool)

        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.mac_blocks = []
        self.name = self.get_attribute(attribute_name="name")
        self.reservations = []

        if self._config.load_from == "live":
            # Fetches the MAC Blocks configurations
            if hasattr(self._object, "mac_blocks"):
                for mac_block in self._object.mac_blocks:
                    self.mac_blocks.append({"from": mac_block._from, "to": mac_block.to})
            # Fetches the MAC reservations
            self.reservations = self._get_reservations()

        elif self._config.load_from == "file":
            for attribute in ["mac_blocks", "reservations"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

        self.clean_object()

    def clean_object(self):
        # We use this to make sure all options of a MAC Block are set to None if they are not present
        if self.mac_blocks:
            for mac_block in self.mac_blocks:
                for attribute in ["from", "size", "to"]:
                    if attribute not in mac_block:
                        mac_block[attribute] = None

        # We use this to make sure all options of a reservations are set to None if they are not present
        if self.reservations:
            for reservation in self.reservations:
                for attribute in ["identity"]:
                    if attribute not in reservation:
                        reservation[attribute] = None

    def _find_overlapping_reservations(self, existing_reservations=None, to_be_pushed_reservations=None):
        mac_used = self._device.query(object_type="macpool.PoolMember", filter="Assigned eq true")

        mac_used_identities = [pool_member.mac_address for pool_member in mac_used]

        return _find_overlapping_reservations(existing_reservations=existing_reservations,
                                              to_be_pushed_reservations=to_be_pushed_reservations,
                                              used_identities=mac_used_identities)

    def _get_reservations(self):
        # Fetches the Reservations of a MAC Pool
        if "macpool_reservation" in self._config.sdk_objects:
            reservations = []
            for reservation in self._config.sdk_objects["macpool_reservation"]:
                if hasattr(reservation, "pool"):
                    if reservation.pool.moid == self._moid:
                        reservations.append({"identity": reservation.identity})
            return reservations

        return None

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.macpool_pool import MacpoolPool

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        mac_blocks = []
        if self.mac_blocks:
            from intersight.model.macpool_block import MacpoolBlock
            for mac_block in self.mac_blocks:
                kwargs = {
                    "object_type": "macpool.Block",
                    "class_id": "macpool.Block",
                    "_from": mac_block["from"]
                }
                if mac_block.get("to"):
                    kwargs["to"] = mac_block["to"]
                elif mac_block.get("size"):
                    kwargs["size"] = mac_block["size"]
                mac_blocks.append(MacpoolBlock(**kwargs))

        org = self.get_parent_org_relationship()
        org_name = self._parent.name

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": org,
            "mac_blocks": mac_blocks
        }
        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()

        macpool_pool = MacpoolPool(**kwargs)

        macpool = self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=macpool_pool, detail=self.name,
                              return_relationship=True)
        if not macpool:
            return False

        if not self.reservations:
            return True

        # Get the all the MAC Pool reservations
        mac_reservations = self._device.query(object_type="macpool.Reservation", expand="Organization")

        # Find overlapping, non overlapping and used reservations between mac_reservations and self.reservations
        overlapping_reservations, non_overlapping_reservations, used_reservations = self._find_overlapping_reservations(
            existing_reservations=mac_reservations,
            to_be_pushed_reservations=self.reservations
        )

        # Reservations which need to be newly created (Non Overlapping Reservations) are bulk pushed.
        if non_overlapping_reservations:
            # We now need to bulk push the macpool.Reservation object for each Reservation in the list
            from intersight.model.bulk_request import BulkRequest
            from intersight.model.bulk_sub_request import BulkSubRequest
            from intersight.model.mo_base_mo import MoBaseMo

            bulk_request_kwargs = {
                "uri": "/v1/macpool/Reservations",
                "verb": "POST",
                "requests": []
            }
            requests = []

            for reservation in non_overlapping_reservations:
                body_kwargs = {
                    "object_type": "macpool.Reservation",
                    "class_id": "macpool.Reservation",
                    "identity": reservation["identity"],
                    "organization": org,
                    "pool": macpool
                }
                if self.tags is not None:
                    kwargs["tags"] = self.create_tags()

                body = MoBaseMo(**body_kwargs)

                sub_request_kwargs = {
                    "object_type": "bulk.RestSubRequest",
                    "class_id": "bulk.RestSubRequest",
                    "body": body
                }

                sub_request = BulkSubRequest(**sub_request_kwargs)

                requests.append(sub_request)

            # Bulk API can send maximum 100 requests per call. So we send the requests in groups of 100.
            start = 0
            end = 100
            while start < len(requests):
                start_identity = non_overlapping_reservations[start]["identity"]
                if end - 1 < len(non_overlapping_reservations):
                    end_identity = non_overlapping_reservations[end - 1]["identity"]
                else:
                    end_identity = non_overlapping_reservations[-1]["identity"]
                bulk_request_kwargs["requests"] = requests[start:end]
                bulk_request = BulkRequest(**bulk_request_kwargs)

                detail = f"{self.name} - {len(bulk_request_kwargs['requests'])} Reservations between identities " \
                         f"({start_identity}, {end_identity})"
                self.commit(object_type="bulk.Request", payload=bulk_request, detail=detail, key_attributes=[])
                start = end
                end += 100

        # These reservations already exist, so we skip them.
        if overlapping_reservations:
            for reservation in overlapping_reservations:
                if reservation["organization"] != org_name:
                    err_message = f"Failed to push object-type macpool.Reservation with identity "\
                                  f"{reservation['identity']} as it already exists in an org "\
                                  f"'{reservation['organization']}' different than the {self._CONFIG_NAME} org "\
                                  f"'{org_name}'."
                    push_status = "failed"
                    self.logger(level="error", message=err_message)
                else:
                    err_message = f"Skipping push of object-type macpool.Reservation with identity "\
                                  f"{reservation['identity']} as it already exists."
                    push_status = "skipped"
                    self.logger(level="warning", message=err_message)
                self._config.push_summary_manager.add_object_status(
                    obj=self, obj_detail=f"Reservation {reservation['identity']}", obj_type="macpool.Reservation",
                    status=push_status, message=err_message
                )

        # These reservations already in-use by some profile, so we skip them.
        if used_reservations:
            for reservation in used_reservations:
                err_message = f"Skipping push of object-type macpool.Reservation with identity "\
                              f"{reservation['identity']} as it's already in use."
                self.logger(level="warning", message=err_message)
                self._config.push_summary_manager.add_object_status(
                    obj=self, obj_detail=f"Reservation {reservation['identity']}", obj_type="macpool.Reservation",
                    status="skipped", message=err_message
                )

        return True


class IntersightServerPoolQualificationPolicy(IntersightConfigObject):
    _CONFIG_NAME = "Server Pool Qualification Policy"
    _CONFIG_SECTION_NAME = "server_pool_qualification_policies"
    _INTERSIGHT_SDK_OBJECT_NAME = "resourcepool.QualificationPolicy"

    def __init__(self, parent=None, server_pool_qualification_policy=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=server_pool_qualification_policy)

        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.name = self.get_attribute(attribute_name="name")
        self.domain_qualifiers = None
        self.server_qualifiers = None
        self.tag_qualifiers = None
        self.hardware_qualifiers = None

        if self._config.load_from == "live":
            if hasattr(self._object, "qualifiers"):
                for qualifiers in getattr(self._object, "qualifiers"):
                    obj_type = qualifiers.object_type

                    if obj_type == "resource.DomainQualifier":
                        domain_qualifier = {
                            "domain_names": qualifiers.domain_names,
                            "fabric_interconnect_pids": qualifiers.fabric_inter_connect_pids
                        }
                        self.domain_qualifiers = domain_qualifier

                    elif obj_type == "resource.RackServerQualifier":
                        self.server_qualifiers = self.server_qualifiers or {}
                        rack_server = {
                            "asset_tags": qualifiers.asset_tags,
                            "rack_pids": qualifiers.pids,
                            "user_labels": qualifiers.user_labels,
                            "rack_ids": self._get_rack_server_id_range(getattr(qualifiers, "rack_id_range", []))
                        }
                        self.server_qualifiers.update({"rack_server_qualifier": rack_server})

                    elif obj_type == "resource.BladeQualifier":
                        self.server_qualifiers = self.server_qualifiers or {}
                        blade_server = {
                            "asset_tags": qualifiers.asset_tags,
                            "blade_pids": qualifiers.pids,
                            "chassis_pids": qualifiers.chassis_pids,
                            "user_labels": qualifiers.user_labels,
                            "chassis_slot_ids":
                                self._get_chassis_and_slot_id_range(getattr(qualifiers, "chassis_and_slot_id_range", []))
                        }
                        self.server_qualifiers.update({"blade_server_qualifier": blade_server})

                    elif obj_type == "resource.TagQualifier":
                        tag_qualifier = {
                            "chassis_tags": self._get_qualifier_tags(getattr(qualifiers, "chassis_tags", [])),
                            "domain_profile_tags":
                                self._get_qualifier_tags(getattr(qualifiers, "domain_profile_tags", [])),
                            "server_tags": self._get_qualifier_tags(getattr(qualifiers, "server_tags", []))
                        }
                        self.tag_qualifiers = tag_qualifier

                    elif obj_type == "resource.MemoryQualifier":
                        self.hardware_qualifiers = self.hardware_qualifiers or {}
                        memory_qualifier = {
                            "capacity_minimum": self._get_hardware_qualifier_min_range(
                                getattr(qualifiers, "memory_capacity_range", {})),
                            "capacity_maximum": self._get_hardware_qualifier_max_range(
                                getattr(qualifiers, "memory_capacity_range", {})),
                            "number_of_units_minimum": self._get_hardware_qualifier_min_range(
                                getattr(qualifiers, "memory_units_range", {})),
                            "number_of_units_maximum": self._get_hardware_qualifier_max_range(
                                getattr(qualifiers, "memory_units_range", {}))
                        }
                        self.hardware_qualifiers.update({"memory_qualifier": memory_qualifier})

                    elif obj_type == "resource.GpuQualifier":
                        self.hardware_qualifiers = self.hardware_qualifiers or {}
                        gpu_qualifier = {
                            "gpu_pids": qualifiers.pids,
                            "number_of_gpus_minimum": self._get_hardware_qualifier_min_range(
                                getattr(qualifiers, "gpu_controllers_range", {})),
                            "number_of_gpus_maximum": self._get_hardware_qualifier_max_range(
                                getattr(qualifiers, "gpu_controllers_range", {})),
                            "gpu_evaluation_type": qualifiers.gpu_evaluation_type,
                            "vendor": qualifiers.vendor
                        }
                        self.hardware_qualifiers.update({"gpu_qualifier": gpu_qualifier})

                    elif obj_type == "resource.ProcessorQualifier":
                        self.hardware_qualifiers = self.hardware_qualifiers or {}
                        cpu_qualifier = {
                            "number_of_cores_minimum": self._get_hardware_qualifier_min_range(
                                getattr(qualifiers, "cpu_cores_range", {})),
                            "number_of_cores_maximum": self._get_hardware_qualifier_max_range(
                                getattr(qualifiers, "cpu_cores_range", {})),
                            "speed_minimum": self._get_hardware_qualifier_min_range(
                                getattr(qualifiers, "speed_range", {})),
                            "speed_maximum": self._get_hardware_qualifier_max_range(
                                getattr(qualifiers, "speed_range", {})),
                            "cpu_pids": qualifiers.pids,
                            "vendor": qualifiers.vendor
                        }
                        self.hardware_qualifiers.update({"cpu_qualifier": cpu_qualifier})

                    elif obj_type == "resource.NetworkAdaptorQualifier":
                        self.hardware_qualifiers = self.hardware_qualifiers or {}
                        adpater_qualifier = {
                            "number_of_network_adapters_minimum": self._get_hardware_qualifier_min_range(
                                getattr(qualifiers, "adaptors_range", {})),
                            "number_of_network_adapters_maximum": self._get_hardware_qualifier_max_range(
                                getattr(qualifiers, "adaptors_range", {}))
                        }
                        self.hardware_qualifiers.update({"network_adapter_qualifier": adpater_qualifier})

        elif self._config.load_from == "file":
            for attribute in ["domain_qualifiers", "server_qualifiers", "tag_qualifiers", "hardware_qualifiers"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

        self.clean_object()

    def clean_object(self):
        if self.domain_qualifiers:
            for attribute in ["domain_names", "fabric_interconnect_pids"]:
                if attribute not in self.domain_qualifiers:
                    self.domain_qualifiers[attribute] = None

        if self.hardware_qualifiers:
            for qualifier in ["cpu_qualifier", "gpu_qualifier", "memory_qualifier", "network_adapter_qualifier"]:
                if qualifier not in self.hardware_qualifiers:
                    self.hardware_qualifiers[qualifier] = None
                elif self.hardware_qualifiers[qualifier]:
                    if qualifier == "cpu_qualifier":
                        for attribute in ["number_of_cores_maximum", "number_of_cores_minimum", "speed_maximum",
                                          "speed_minimum", "cpu_pids", "vendor"]:
                            if attribute not in self.hardware_qualifiers[qualifier]:
                                self.hardware_qualifiers[qualifier][attribute] = None

                    elif qualifier == "gpu_qualifier":
                        for attribute in ["number_of_gpus_maximum", "number_of_gpus_minimum", "gpu_evaluation_type",
                                          "gpu_pids", "vendor"]:
                            if attribute not in self.hardware_qualifiers[qualifier]:
                                self.hardware_qualifiers[qualifier][attribute] = None

                    elif qualifier == "memory_qualifier":
                        for attribute in ["capacity_maximum", "capacity_minimum", "number_of_units_minimum",
                                          "number_of_units_maximum"]:
                            if attribute not in self.hardware_qualifiers[qualifier]:
                                self.hardware_qualifiers[qualifier][attribute] = None

                    elif qualifier == "network_adapter_qualifier":
                        for attribute in ["number_of_network_adapters_maximum", "number_of_network_adapters_minimum"]:
                            if attribute not in self.hardware_qualifiers[qualifier]:
                                self.hardware_qualifiers[qualifier][attribute] = None
        if self.server_qualifiers:
            if "blade_server_qualifier" not in self.server_qualifiers:
                self.server_qualifiers["blade_server_qualifier"] = None
            elif self.server_qualifiers["blade_server_qualifier"]:
                for attribute in ["asset_tags", "blade_pids", "chassis_pids", "chassis_slot_ids", "user_labels"]:
                    if attribute not in self.server_qualifiers["blade_server_qualifier"]:
                        self.server_qualifiers["blade_server_qualifier"][attribute] = None
                    if attribute == "chassis_slot_ids" and self.server_qualifiers["blade_server_qualifier"][attribute]:
                        for slot in self.server_qualifiers["blade_server_qualifier"]["chassis_slot_ids"]:
                            if "chassis_ids" not in slot:
                                slot["chassis_ids"] = None
                            else:
                                for sub_attr in ["chassis_id_from", "chassis_id_to"]:
                                    if sub_attr not in slot["chassis_ids"]:
                                        slot["chassis_ids"][sub_attr] = None
                            if "slot_ids" not in slot:
                                slot["slot_ids"] = None
                            elif slot["slot_ids"]:
                                for slot_range in slot["slot_ids"]:
                                    for sub_attr in ["slot_id_from", "slot_id_to"]:
                                        if sub_attr not in slot_range:
                                            slot_range[sub_attr] = None
            if "rack_server_qualifier" not in self.server_qualifiers:
                self.server_qualifiers["rack_server_qualifier"] = None
            elif self.server_qualifiers["rack_server_qualifier"]:
                for attribute in ["asset_tags", "rack_ids", "rack_pids", "user_labels"]:
                    if attribute not in self.server_qualifiers["rack_server_qualifier"]:
                        self.server_qualifiers["rack_server_qualifier"][attribute] = None
                    if attribute == "rack_ids" and self.server_qualifiers["rack_server_qualifier"][attribute]:
                        for rack in self.server_qualifiers["rack_server_qualifier"]["rack_ids"]:
                            for sub_attr in ["rack_id_from", "rack_id_to"]:
                                if sub_attr not in rack:
                                    rack[sub_attr] = None

        if self.tag_qualifiers:
            for attribute in ["chassis_tags", "domain_profile_tags", "server_tags"]:
                if attribute not in self.tag_qualifiers:
                    self.tag_qualifiers[attribute] = None

    def _get_qualifier_tags(self, qualifier_tags):
        if qualifier_tags:
            tags = []
            for tag in qualifier_tags:
                tags.append({
                    "key": tag.key,
                    "value": tag.value
                })

            return tags

        return None

    def _get_rack_server_id_range(self, server_id_range):
        if server_id_range:
            id_range = []
            for range in server_id_range:
                id_range.append({
                    "rack_id_from": range.min_value,
                    "rack_id_to": range.max_value
                })
            return id_range
        return None

    def _get_chassis_and_slot_id_range(self, chassis_and_slot_id_range):
        if chassis_and_slot_id_range:
            chassis_and_slot_range = []
            for id_range in chassis_and_slot_id_range:
                slot_ranges = []
                if getattr(id_range, "chassis_id_range", {}):
                    chassis_range = {
                        "chassis_id_from": id_range.chassis_id_range.get("min_value", 0),
                        "chassis_id_to": id_range.chassis_id_range.get("max_value", 0)
                    }

                    for slot_range in getattr(id_range, "slot_id_ranges", []):
                        slot_id = {
                            "slot_id_from": slot_range.get("min_value", 0),
                            "slot_id_to": slot_range.get("max_value", 0)
                        }
                        slot_ranges.append(slot_id)

                    chassis_and_slot_range.append({
                        "chassis_ids": chassis_range,
                        "slot_ids": slot_ranges
                    })

            return chassis_and_slot_range

        return None

    def _get_hardware_qualifier_min_range(self, hardware_qualifier_range):
        if hardware_qualifier_range:
            return hardware_qualifier_range.min_value
        return None

    def _get_hardware_qualifier_max_range(self, hardware_qualifier_range):
        if hardware_qualifier_range:
            return hardware_qualifier_range.max_value
        return None

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.resourcepool_qualification_policy import ResourcepoolQualificationPolicy

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": self.get_parent_org_relationship()
        }
        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()

        resource_qualifiers = []

        if self.domain_qualifiers is not None:
            from intersight.model.resource_domain_qualifier import ResourceDomainQualifier
            domain_qualifiers_kwargs = {
                "object_type": "resource.DomainQualifier",
                "class_id": "resource.DomainQualifier",
            }
            if self.domain_qualifiers.get("domain_names", []):
                domain_qualifiers_kwargs["domain_names"] = self.domain_qualifiers["domain_names"]
            if self.domain_qualifiers.get("fabric_interconnect_pids", []):
                domain_qualifiers_kwargs["fabric_inter_connect_pids"] = (
                    self.domain_qualifiers)["fabric_interconnect_pids"]

            resource_qualifiers.append(ResourceDomainQualifier(**domain_qualifiers_kwargs))

        if self.server_qualifiers is not None:
            from intersight.model.resource_chassis_and_slot_qualification import ResourceChassisAndSlotQualification
            from intersight.model.resource_blade_qualifier import ResourceBladeQualifier
            from intersight.model.resource_slot_id_range_filter import ResourceSlotIdRangeFilter
            from intersight.model.resource_chassis_id_range_filter import ResourceChassisIdRangeFilter
            from intersight.model.resource_rack_server_qualifier import ResourceRackServerQualifier
            from intersight.model.resource_rack_id_range_filter import ResourceRackIdRangeFilter

            if self.server_qualifiers.get("blade_server_qualifier", {}):
                blade_qualifiers_kwargs = {
                    "object_type": "resource.BladeQualifier",
                    "class_id": "resource.BladeQualifier",
                }
                if self.server_qualifiers["blade_server_qualifier"].get("asset_tags", []):
                    blade_qualifiers_kwargs["asset_tags"] = (
                        self.server_qualifiers)["blade_server_qualifier"]["asset_tags"]
                if self.server_qualifiers["blade_server_qualifier"].get("blade_pids", []):
                    blade_qualifiers_kwargs["pids"] = (
                        self.server_qualifiers)["blade_server_qualifier"]["blade_pids"]
                if self.server_qualifiers["blade_server_qualifier"].get("chassis_pids", []):
                    blade_qualifiers_kwargs["chassis_pids"] = (
                        self.server_qualifiers)["blade_server_qualifier"]["chassis_pids"]
                if self.server_qualifiers["blade_server_qualifier"].get("user_labels", []):
                    blade_qualifiers_kwargs["user_labels"] = (
                        self.server_qualifiers)["blade_server_qualifier"]["user_labels"]
                if self.server_qualifiers["blade_server_qualifier"].get("chassis_slot_ids", []):
                    chassis_slot_ids = []
                    for chassis_slot_id in self.server_qualifiers["blade_server_qualifier"]["chassis_slot_ids"]:
                        slot_ids = []
                        chassis_slot_kwargs = {
                            "object_type": "resource.ChassisAndSlotQualification",
                            "class_id": "resource.ChassisAndSlotQualification",
                        }
                        if chassis_slot_id.get("slot_ids", []):
                            for slot_id in chassis_slot_id["slot_ids"]:
                                slot_kwargs = {
                                    "object_type": "resource.SlotIdRangeFilter",
                                    "class_id": "resource.SlotIdRangeFilter"
                                }
                                if slot_id.get("slot_id_from"):
                                    slot_kwargs["min_value"] = slot_id["slot_id_from"]
                                if slot_id.get("slot_id_to"):
                                    slot_kwargs["max_value"] = slot_id["slot_id_to"]

                                slot_ids.append(ResourceSlotIdRangeFilter(**slot_kwargs))
                        chassis_ids_kwargs = {
                            "object_type": "resource.ChassisIdRangeFilter",
                            "class_id": "resource.ChassisIdRangeFilter",
                        }
                        if chassis_slot_id.get("chassis_ids", {}):
                            if chassis_slot_id["chassis_ids"].get("chassis_id_from"):
                                chassis_ids_kwargs["min_value"] = chassis_slot_id["chassis_ids"]["chassis_id_from"]
                            if chassis_slot_id["chassis_ids"].get("chassis_id_to"):
                                chassis_ids_kwargs["max_value"] = chassis_slot_id["chassis_ids"]["chassis_id_to"]

                        chassis_slot_kwargs["chassis_id_range"] = ResourceChassisIdRangeFilter(**chassis_ids_kwargs)
                        chassis_slot_kwargs["slot_id_ranges"] = slot_ids

                        chassis_slot_ids.append(ResourceChassisAndSlotQualification(**chassis_slot_kwargs))

                    blade_qualifiers_kwargs["chassis_and_slot_id_range"] = chassis_slot_ids

                resource_qualifiers.append(ResourceBladeQualifier(**blade_qualifiers_kwargs))

            if self.server_qualifiers.get("rack_server_qualifier", {}):

                rack_server_qualifiers_kwargs = {
                    "object_type": "resource.RackServerQualifier",
                    "class_id": "resource.RackServerQualifier",
                }
                if self.server_qualifiers["rack_server_qualifier"].get("asset_tags", []):
                    rack_server_qualifiers_kwargs["asset_tags"] = (
                        self.server_qualifiers)["rack_server_qualifier"]["asset_tags"]
                if self.server_qualifiers["rack_server_qualifier"].get("rack_pids", []):
                    rack_server_qualifiers_kwargs["pids"] = (
                        self.server_qualifiers)["rack_server_qualifier"]["rack_pids"]
                if self.server_qualifiers["rack_server_qualifier"].get("user_labels", []):
                    rack_server_qualifiers_kwargs["user_labels"] = (
                        self.server_qualifiers)["rack_server_qualifier"]["user_labels"]
                if self.server_qualifiers["rack_server_qualifier"].get("rack_ids", []):
                    rack_ids = []
                    for rack_id in self.server_qualifiers["rack_server_qualifier"]["rack_ids"]:
                        rack_id_kwargs = {
                            "object_type": "resource.RackIdRangeFilter",
                            "class_id": "resource.RackIdRangeFilter"
                        }
                        if rack_id.get("rack_id_from"):
                            rack_id_kwargs["min_value"] = rack_id["rack_id_from"]
                        if rack_id.get("rack_id_to"):
                            rack_id_kwargs["max_value"] = rack_id["rack_id_to"]

                        rack_ids.append(ResourceRackIdRangeFilter(**rack_id_kwargs))

                    rack_server_qualifiers_kwargs["rack_id_range"] = rack_ids
                resource_qualifiers.append(ResourceRackServerQualifier(**rack_server_qualifiers_kwargs))

        if self.tag_qualifiers is not None:
            from intersight.model.resource_tag_qualifier import ResourceTagQualifier
            from intersight.model.resource_tag import ResourceTag
            tag_qualifiers_kwargs = {
                "object_type": "resource.TagQualifier",
                "class_id": "resource.TagQualifier",
            }
            if self.tag_qualifiers.get("chassis_tags", []):
                chassis_tags = []
                for tag in self.tag_qualifiers["chassis_tags"]:
                    tag_kwargs = {
                        "object_type": "resource.Tag",
                        "class_id": "resource.Tag",
                        "key": tag["key"],
                        "value": tag["value"]
                    }
                    chassis_tags.append(ResourceTag(**tag_kwargs))
                tag_qualifiers_kwargs["chassis_tags"] = chassis_tags

            if self.tag_qualifiers.get("domain_profile_tags", []):
                domain_profile_tags = []
                for tag in self.tag_qualifiers["domain_profile_tags"]:
                    tag_kwargs = {
                        "object_type": "resource.Tag",
                        "class_id": "resource.Tag",
                        "key": tag["key"],
                        "value": tag["value"]
                    }
                    domain_profile_tags.append(ResourceTag(**tag_kwargs))
                tag_qualifiers_kwargs["domain_profile_tags"] = domain_profile_tags

            if self.tag_qualifiers.get("server_tags", []):
                server_tags = []
                for tag in self.tag_qualifiers["server_tags"]:
                    tag_kwargs = {
                        "object_type": "resource.Tag",
                        "class_id": "resource.Tag",
                        "key": tag["key"],
                        "value": tag["value"]
                    }
                    server_tags.append(ResourceTag(**tag_kwargs))
                tag_qualifiers_kwargs["server_tags"] = server_tags

            resource_qualifiers.append(ResourceTagQualifier(**tag_qualifiers_kwargs))

        if self.hardware_qualifiers is not None:
            if self.hardware_qualifiers.get("memory_qualifier", {}):
                from intersight.model.resource_memory_qualifier import ResourceMemoryQualifier
                from intersight.model.resource_memory_capacity_range_filter import ResourceMemoryCapacityRangeFilter
                from intersight.model.resource_memory_units_range_filter import ResourceMemoryUnitsRangeFilter

                memory_qualifier_kwargs = {
                    "object_type": "resource.MemoryQualifier",
                    "class_id": "resource.MemoryQualifier",
                }

                memory_capacity_range_kwargs = {
                    "object_type": "resource.MemoryCapacityRangeFilter",
                    "class_id": "resource.MemoryCapacityRangeFilter"
                }
                if self.hardware_qualifiers["memory_qualifier"].get("capacity_minimum"):
                    memory_capacity_range_kwargs["min_value"] = (
                        self.hardware_qualifiers)["memory_qualifier"]["capacity_minimum"]
                if self.hardware_qualifiers["memory_qualifier"].get("capacity_maximum"):
                    memory_capacity_range_kwargs["max_value"] = (
                        self.hardware_qualifiers)["memory_qualifier"]["capacity_maximum"]

                memory_qualifier_kwargs["memory_capacity_range"] = (
                    ResourceMemoryCapacityRangeFilter(**memory_capacity_range_kwargs))

                memory_units_range_kwargs = {
                    "object_type": "resource.MemoryUnitsRangeFilter",
                    "class_id": "resource.MemoryUnitsRangeFilter"
                }
                if self.hardware_qualifiers["memory_qualifier"].get("number_of_units_minimum"):
                    memory_units_range_kwargs["min_value"] = (
                        self.hardware_qualifiers)["memory_qualifier"]["number_of_units_minimum"]
                if self.hardware_qualifiers["memory_qualifier"].get("number_of_units_maximum"):
                    memory_units_range_kwargs["max_value"] = (
                        self.hardware_qualifiers)["memory_qualifier"]["number_of_units_maximum"]
                memory_qualifier_kwargs["memory_units_range"] = (
                    ResourceMemoryUnitsRangeFilter(**memory_units_range_kwargs))

                resource_qualifiers.append(ResourceMemoryQualifier(**memory_qualifier_kwargs))

            if self.hardware_qualifiers.get("cpu_qualifier", {}):
                from intersight.model.resource_processor_qualifier import ResourceProcessorQualifier
                from intersight.model.resource_cpu_core_range_filter import ResourceCpuCoreRangeFilter
                from intersight.model.resource_cpu_speed_range_filter import ResourceCpuSpeedRangeFilter
                cpu_qualifier_kwargs = {
                    "object_type": "resource.ProcessorQualifier",
                    "class_id": "resource.ProcessorQualifier",
                }

                cpu_cores_range_kwargs = {
                    "object_type": "resource.CpuCoreRangeFilter",
                    "class_id": "resource.CpuCoreRangeFilter"
                }
                if self.hardware_qualifiers["cpu_qualifier"].get("number_of_cores_minimum"):
                    cpu_cores_range_kwargs["min_value"] = (
                        self.hardware_qualifiers)["cpu_qualifier"]["number_of_cores_minimum"]
                if self.hardware_qualifiers["cpu_qualifier"].get("number_of_cores_maximum"):
                    cpu_cores_range_kwargs["max_value"] = (
                        self.hardware_qualifiers)["cpu_qualifier"]["number_of_cores_maximum"]

                cpu_qualifier_kwargs["cpu_cores_range"] = (
                    ResourceCpuCoreRangeFilter(**cpu_cores_range_kwargs))
                if self.hardware_qualifiers["cpu_qualifier"].get("cpu_pids", []):
                    cpu_qualifier_kwargs["pids"] = self.hardware_qualifiers["cpu_qualifier"]["cpu_pids"]

                cpu_speed_range_kwargs = {
                    "object_type": "resource.CpuSpeedRangeFilter",
                    "class_id": "resource.CpuSpeedRangeFilter"
                }
                if self.hardware_qualifiers["cpu_qualifier"].get("speed_minimum"):
                    cpu_speed_range_kwargs["min_value"] = (
                        self.hardware_qualifiers)["cpu_qualifier"]["speed_minimum"]
                if self.hardware_qualifiers["cpu_qualifier"].get("speed_maximum"):
                    cpu_speed_range_kwargs["max_value"] = (
                        self.hardware_qualifiers)["cpu_qualifier"]["speed_maximum"]

                cpu_qualifier_kwargs["speed_range"] = (
                    ResourceCpuSpeedRangeFilter(**cpu_speed_range_kwargs))

                if self.hardware_qualifiers["cpu_qualifier"].get("vendor", ""):
                    cpu_qualifier_kwargs["vendor"] = self.hardware_qualifiers["cpu_qualifier"]["vendor"]

                resource_qualifiers.append(ResourceProcessorQualifier(**cpu_qualifier_kwargs))

            if self.hardware_qualifiers.get("gpu_qualifier", {}):
                from intersight.model.resource_gpu_qualifier import ResourceGpuQualifier
                from intersight.model.resource_gpu_controllers_range_filter import ResourceGpuControllersRangeFilter
                from intersight.model.resource_cpu_speed_range_filter import ResourceCpuSpeedRangeFilter
                gpu_qualifier_kwargs = {
                    "object_type": "resource.GpuQualifier",
                    "class_id": "resource.GpuQualifier",
                }
                gpu_controllers_range_kwargs = {
                    "object_type": "resource.GpuControllersRangeFilter",
                    "class_id": "resource.GpuControllersRangeFilter"
                }
                if self.hardware_qualifiers["gpu_qualifier"].get("number_of_gpus_minimum"):
                    gpu_controllers_range_kwargs["min_value"] = (
                        self.hardware_qualifiers)["gpu_qualifier"]["number_of_gpus_minimum"]
                if self.hardware_qualifiers["gpu_qualifier"].get("number_of_gpus_maximum"):
                    gpu_controllers_range_kwargs["max_value"] = (
                        self.hardware_qualifiers)["gpu_qualifier"]["number_of_gpus_maximum"]

                gpu_qualifier_kwargs["gpu_controllers_range"] = (
                    ResourceGpuControllersRangeFilter(**gpu_controllers_range_kwargs))

                if self.hardware_qualifiers["gpu_qualifier"].get("gpu_pids", []):
                    gpu_qualifier_kwargs["pids"] = self.hardware_qualifiers["gpu_qualifier"]["gpu_pids"]
                if self.hardware_qualifiers["gpu_qualifier"].get("vendor", ""):
                    gpu_qualifier_kwargs["vendor"] = self.hardware_qualifiers["gpu_qualifier"]["vendor"]

                gpu_qualifier_kwargs["gpu_evaluation_type"] = (
                    self.hardware_qualifiers["gpu_qualifier"].get("gpu_evaluation_type"))

                resource_qualifiers.append(ResourceGpuQualifier(**gpu_qualifier_kwargs))

            if self.hardware_qualifiers.get("network_adapter_qualifier", {}):
                from intersight.model.resource_network_adaptor_qualifier import ResourceNetworkAdaptorQualifier
                from intersight.model.resource_adaptors_range_filter import ResourceAdaptorsRangeFilter
                network_adapter_qualifier_kwargs = {
                    "object_type": "resource.NetworkAdaptorQualifier",
                    "class_id": "resource.NetworkAdaptorQualifier",
                }
                adaptors_range_kwargs = {
                    "object_type": "resource.AdaptorsRangeFilter",
                    "class_id": "resource.AdaptorsRangeFilter"
                }
                if self.hardware_qualifiers["network_adapter_qualifier"].get("number_of_network_adapters_minimum"):
                    adaptors_range_kwargs["min_value"] = (
                        self.hardware_qualifiers)["network_adapter_qualifier"]["number_of_network_adapters_minimum"]
                if self.hardware_qualifiers["network_adapter_qualifier"].get("number_of_network_adapters_maximum"):
                    adaptors_range_kwargs["max_value"] = (
                        self.hardware_qualifiers)["network_adapter_qualifier"]["number_of_network_adapters_maximum"]

                network_adapter_qualifier_kwargs["adaptors_range"] = (
                    ResourceAdaptorsRangeFilter(**adaptors_range_kwargs))

                resource_qualifiers.append(ResourceNetworkAdaptorQualifier(**network_adapter_qualifier_kwargs))

        kwargs["qualifiers"] = resource_qualifiers

        server_pool_qualification_policy = ResourcepoolQualificationPolicy(**kwargs)

        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=server_pool_qualification_policy,
                           detail=self.name):
            return False

        return True


class IntersightResourcePool(IntersightConfigObject):
    _CONFIG_NAME = "Resource Pool"
    _CONFIG_SECTION_NAME = "resource_pools"
    _INTERSIGHT_SDK_OBJECT_NAME = "resourcepool.Pool"

    _POLICY_MAPPING_TABLE = {
        "server_pool_qualification_policies": [IntersightServerPoolQualificationPolicy]
    }

    UCS_TO_INTERSIGHT_POLICY_MAPPING_TABLE = {
        "server_pool_qualification": "server_pool_qualification_policies"
    }

    def __init__(self, parent=None, resourcepool_pool=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=resourcepool_pool)

        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.name = self.get_attribute(attribute_name="name")
        self.resources = None
        self.server_pool_qualification_policies = None
        self.target_platform = None

        if self._config.load_from == "live":
            self.target_platform = self._get_target_platform()
            self.resources = self._get_member_resources()
            if getattr(self._object, "qualification_policies", None):
                server_pool_qualification_policies = []
                for qualification_policy in self._object.qualification_policies:
                    server_pool_qualification_policies.append(self._get_policy_name(policy=qualification_policy))

                self.server_pool_qualification_policies = server_pool_qualification_policies

        elif self._config.load_from == "file":
            for attribute in ["resources", "server_pool_qualification_policies", "target_platform"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

        self.clean_object()

    def clean_object(self):
        # We use this to make sure all options of a Resource are set to None if they are not present
        if self.resources:
            for resource in self.resources:
                for attribute in ["moid", "name", "serial", "type"]:
                    if attribute not in resource:
                        resource[attribute] = None

    def _get_member_resources(self):
        # Get the list of resources member of this pool
        selectors = self._object.selectors

        resource_list = []
        for selector in selectors:
            if selector["object_type"] == "resource.Selector":
                # Selectors can either use MOIDs (older method) or Serials to identify resources
                if "Moid in" in selector["selector"]:
                    # We use a regex to get the MOIDs of resources member of the pool
                    regex_device_moid = r"([a-f0-9]{24})"
                    res_resources = re.findall(regex_device_moid, selector["selector"])
                    res_identify_by = "moid"

                else:
                    # We use a regex to get the Serial numbers of resources member of the pool
                    regex_device_serial = r"([A-Z0-9]{11})"
                    res_resources = re.findall(regex_device_serial, selector["selector"])
                    res_identify_by = "serial"

                if res_resources:
                    for resource in res_resources:
                        if res_identify_by == "moid":
                            device_list = self._device.query(object_type="compute.PhysicalSummary",
                                                             filter="Moid eq '%s'" % resource)
                        else:
                            device_list = self._device.query(object_type="compute.PhysicalSummary",
                                                             filter="Serial eq '%s'" % resource)

                        if device_list:
                            if len(device_list) != 1:
                                self.logger(level="warning",
                                            message=f"Could not find unique device '{resource}' to assign to "
                                                    f"{self._CONFIG_NAME} {self.name}")
                            else:
                                if hasattr(device_list[0], "name"):
                                    resource_type = None
                                    if device_list[0].source_object_type == "compute.Blade":
                                        resource_type = "blade"
                                    elif device_list[0].source_object_type == "compute.RackUnit":
                                        resource_type = "rack"
                                    resource_list.append({"name": device_list[0].name, "type": resource_type,
                                                          "serial": device_list[0].serial})
                                else:
                                    self.logger(level="warning",
                                                message=f"Could not find name for device '{resource}' to assign "
                                                        f"to {self._CONFIG_NAME} {self.name}")
                        else:
                            self.logger(level="warning", message=f"Could not find device '{resource}' to assign "
                                                                 f"to {self._CONFIG_NAME} {self.name}")
        if resource_list:
            return resource_list

        return None

    def _get_target_platform(self):
        # Determine the target platform for this Resource Pool
        if self._object.resource_pool_parameters:
            if self._object.resource_pool_parameters.get("management_mode") == "Intersight":
                return "FI-Attached"
            elif self._object.resource_pool_parameters.get("management_mode") == "IntersightStandalone":
                return "Standalone"

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.resourcepool_pool import ResourcepoolPool

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        # Determining if we have a list of resources
        serial_list_blades = []
        serial_list_racks = []
        if self.resources:
            for resource in self.resources:
                if resource.get("serial"):
                    if resource.get("type") == "blade":
                        serial_list_blades.append(resource["serial"])
                    elif resource.get("type") == "rack":
                        serial_list_racks.append(resource["serial"])
                elif resource.get("name"):
                    # We need to retrieve the resource MOID
                    device_list = self._device.query(object_type="compute.PhysicalSummary",
                                                     filter="Name eq '%s'" % resource["name"])

                    if device_list:
                        if len(device_list) != 1:
                            self.logger(level="warning",
                                        message="Could not find unique device '" + resource["name"] +
                                                "' to assign to " + self._CONFIG_NAME + " " + self.name)
                        else:
                            if hasattr(device_list[0], "serial"):
                                if resource.get("type") == "blade":
                                    serial_list_blades.append(device_list[0].serial)
                                elif resource.get("type") == "rack":
                                    serial_list_racks.append(device_list[0].serial)
                                else:
                                    self.logger(level="warning",
                                                message="Could not find resource type for device '" + resource["name"] +
                                                        "' to assign to " + self._CONFIG_NAME + " " + self.name)
                            else:
                                self.logger(level="warning",
                                            message="Could not find moid for device '" + resource["name"] +
                                                    "' to assign to " + self._CONFIG_NAME + " " + self.name)
                    else:
                        self.logger(level="warning", message="Could not find device '" + resource["name"] +
                                                             "' to assign to " + self._CONFIG_NAME + " " + self.name)

        from intersight.model.resource_selector import ResourceSelector

        management_mode = "IntersightStandalone"
        if self.target_platform == "FI-Attached":
            management_mode = "Intersight"

        selector_list = []
        if serial_list_blades:
            selector = "/api/v1/compute/Blades"
            selector += "?$filter=(Serial in ('"
            selector += "','".join(serial_list_blades)
            selector += "'))"  # and (ManagementMode eq '" + management_mode + "')"
            selector_list.append(selector)
        if serial_list_racks:
            selector = "/api/v1/compute/RackUnits"
            selector += "?$filter=(Serial in ('"
            selector += "','".join(serial_list_racks)
            selector += "'))"  # and (ManagementMode eq '" + management_mode + "')"
            selector_list.append(selector)

        resource_selector_list = []
        for selector in selector_list:
            resource_selector_list.append(ResourceSelector(
                object_type="resource.Selector",
                class_id="resource.Selector",
                selector=selector
            ))

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": self.get_parent_org_relationship()
        }
        if resource_selector_list:
            kwargs["selectors"] = resource_selector_list
        if self.target_platform is not None:
            from intersight.model.resourcepool_server_pool_parameters import ResourcepoolServerPoolParameters

            resource_pool_parameters_kwargs = {
                "object_type": "resourcepool.ServerPoolParameters",
                "class_id": "resourcepool.ServerPoolParameters"
            }
            if self.target_platform == "Standalone":
                resource_pool_parameters_kwargs["management_mode"] = "IntersightStandalone"
            elif self.target_platform == "FI-Attached":
                resource_pool_parameters_kwargs["management_mode"] = "Intersight"

            resource_pool_parameters = ResourcepoolServerPoolParameters(**resource_pool_parameters_kwargs)
            if resource_pool_parameters:
                kwargs["resource_pool_parameters"] = resource_pool_parameters

        # For now Resource Pools are only of type "Server"
        kwargs["resource_type"] = "Server"

        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()
        if self.server_pool_qualification_policies is not None:
            server_pool_qualification_policies_list = []
            for qualification_policy in self.server_pool_qualification_policies:
                # We need to identify the Server Pool Qualification Policy object reference
                server_pool_qualification_policy = self.get_live_object(
                    object_name=qualification_policy,
                    object_type="resourcepool.QualificationPolicy"
                )
                if server_pool_qualification_policy:
                    server_pool_qualification_policies_list.append(server_pool_qualification_policy)
                else:
                    self._config.push_summary_manager.add_object_status(
                        obj=self, obj_detail=f"Attaching Server Pool Qualification Policy '{qualification_policy}'",
                        obj_type=self._INTERSIGHT_SDK_OBJECT_NAME, status="failed",
                        message=f"Failed to find Server Pool Qualification Policy '{qualification_policy}'"
                    )
            kwargs["qualification_policies"] = server_pool_qualification_policies_list

        resourcepool_pool = ResourcepoolPool(**kwargs)

        if not self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=resourcepool_pool, detail=self.name):
            return False

        return True


class IntersightUuidPool(IntersightConfigObject):
    _CONFIG_NAME = "UUID Pool"
    _CONFIG_SECTION_NAME = "uuid_pools"
    _INTERSIGHT_SDK_OBJECT_NAME = "uuidpool.Pool"

    def __init__(self, parent=None, uuidpool_pool=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=uuidpool_pool)
        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.uuid_blocks = []
        self.name = self.get_attribute(attribute_name="name")
        self.prefix = self.get_attribute(attribute_name="prefix")
        self.reservations = []

        if self._config.load_from == "live":
            # Fetches the UUID Blocks configurations
            if hasattr(self._object, "uuid_suffix_blocks"):
                for uuid_block in self._object.uuid_suffix_blocks:
                    self.uuid_blocks.append({"from": uuid_block._from, "to": uuid_block.to})
            # Fetches the UUID reservations
            self.reservations = self._get_reservations()

        elif self._config.load_from == "file":
            for attribute in ["uuid_blocks", "reservations"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))
        self.clean_object()

    def clean_object(self):
        # We use this to make sure all options of a UUID Block are set to None if they are not present
        if self.uuid_blocks:
            for uuid_block in self.uuid_blocks:
                for attribute in ["from", "size", "to"]:
                    if attribute not in uuid_block:
                        uuid_block[attribute] = None

        if self.reservations:
            for reservation in self.reservations:
                for attribute in ["identity"]:
                    if attribute not in reservation:
                        reservation[attribute] = None

    def _find_overlapping_reservations(self, existing_reservations=None, to_be_pushed_reservations=None):
        uuid_used = self._device.query(object_type="uuidpool.PoolMember", filter="Assigned eq true")

        uuid_used_identities = [pool_member.uuid for pool_member in uuid_used]

        return _find_overlapping_reservations(existing_reservations=existing_reservations,
                                              to_be_pushed_reservations=to_be_pushed_reservations,
                                              used_identities=uuid_used_identities)

    def _get_reservations(self):
        # Fetches the Reservations of a UUID Pool
        if "uuidpool_reservation" in self._config.sdk_objects:
            reservations = []
            for reservation in self._config.sdk_objects["uuidpool_reservation"]:
                if hasattr(reservation, "pool"):
                    if reservation.pool.moid == self._moid:
                        reservations.append({"identity": reservation.identity})
            return reservations

        return None

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.uuidpool_pool import UuidpoolPool
        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        uuid_blocks = []
        if self.uuid_blocks:
            from intersight.model.uuidpool_uuid_block import UuidpoolUuidBlock
            for uuid_block in self.uuid_blocks:
                kwargs = {
                    "object_type": "uuidpool.UuidBlock",
                    "class_id": "uuidpool.UuidBlock",
                    "_from": uuid_block["from"]
                }
                if uuid_block.get("to"):
                    # kwargs["to"] = uuid_block["to"]
                    # Intersight doesn't have the support to generate UUID Pool block using "To" option.
                    # Hence, "Size" of UUID Pool range is being calculated for UUID Block generation by
                    # replacing the "-" with "" and typecasting the string to int type
                    # ex: "to": "0000-000000000000"
                    kwargs["size"] = int(uuid_block["to"].replace("-", ""), 16) - \
                        int(kwargs["_from"].replace("-", ""), 16) + 1

                elif uuid_block.get("size"):
                    kwargs["size"] = uuid_block["size"]
                uuid_blocks.append(UuidpoolUuidBlock(**kwargs))

        org = self.get_parent_org_relationship()
        org_name = self._parent.name

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": org,
            "uuid_suffix_blocks": uuid_blocks
        }
        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()
        if self.prefix is not None:
            kwargs["prefix"] = self.prefix

        uuidpool_pool = UuidpoolPool(**kwargs)

        uuidpool = self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME,
                               payload=uuidpool_pool, detail=self.name, return_relationship=True)
        if not uuidpool:
            return False

        if not self.reservations:
            return True

        # Get the all the UUID Pool reservations
        uuid_reservations = self._device.query(object_type="uuidpool.Reservation", expand="Organization")

        # Find overlapping, non overlapping and used reservations between uuid_reservations and self.reservations
        overlapping_reservations, non_overlapping_reservations, used_reservations = self._find_overlapping_reservations(
            existing_reservations=uuid_reservations,
            to_be_pushed_reservations=self.reservations
        )

        # Reservations which need to be newly created (Non Overlapping Reservations) are bulk pushed.
        if non_overlapping_reservations:
            # We now need to bulk push the macpool.Reservation object for each Reservation in the list
            from intersight.model.bulk_request import BulkRequest
            from intersight.model.bulk_sub_request import BulkSubRequest
            from intersight.model.mo_base_mo import MoBaseMo

            bulk_request_kwargs = {
                "uri": "/v1/uuidpool/Reservations",
                "verb": "POST",
                "requests": []
            }
            requests = []

            for reservation in non_overlapping_reservations:
                body_kwargs = {
                    "object_type": "uuidpool.Reservation",
                    "class_id": "uuidpool.Reservation",
                    "identity": reservation["identity"],
                    "organization": org,
                    "pool": uuidpool
                }
                if self.tags is not None:
                    kwargs["tags"] = self.create_tags()

                body = MoBaseMo(**body_kwargs)

                sub_request_kwargs = {
                    "object_type": "bulk.RestSubRequest",
                    "class_id": "bulk.RestSubRequest",
                    "body": body
                }

                sub_request = BulkSubRequest(**sub_request_kwargs)

                requests.append(sub_request)

            # Bulk API can send maximum 100 requests per call. So we send the requests in groups of 100.
            start = 0
            end = 100
            while start < len(requests):
                start_identity = non_overlapping_reservations[start]["identity"]
                if end - 1 < len(non_overlapping_reservations):
                    end_identity = non_overlapping_reservations[end - 1]["identity"]
                else:
                    end_identity = non_overlapping_reservations[-1]["identity"]
                bulk_request_kwargs["requests"] = requests[start:end]
                bulk_request = BulkRequest(**bulk_request_kwargs)

                detail = f"{self.name} - {len(bulk_request_kwargs['requests'])} Reservations between identities " \
                         f"({start_identity}, {end_identity})"
                self.commit(object_type="bulk.Request", payload=bulk_request, detail=detail, key_attributes=[])
                start = end
                end += 100

        # These reservations already exist, so we skip them.
        if overlapping_reservations:
            for reservation in overlapping_reservations:
                if reservation["organization"] != org_name:
                    err_message = f"Failed to push object-type uuidpool.Reservation with identity "\
                                  f"{reservation['identity']} as it already exists in an org "\
                                  f"'{reservation['organization']}' different than the {self._CONFIG_NAME} org "\
                                  f"'{org_name}'."
                    push_status = "failed"
                    self.logger(level="error", message=err_message)
                else:
                    err_message = f"Skipping push of object-type uuidpool.Reservation with identity "\
                                  f"{reservation['identity']} as it already exists."
                    push_status = "skipped"
                    self.logger(level="warning", message=err_message)
                self._config.push_summary_manager.add_object_status(
                    obj=self, obj_detail=f"Reservation {reservation['identity']}", obj_type="uuidpool.Reservation",
                    status=push_status, message=err_message
                )

        # These reservations already in-use by some profile, so we skip them.
        if used_reservations:
            for reservation in used_reservations:
                err_message = f"Skipping push of object-type uuidpool.Reservation with identity "\
                              f"{reservation['identity']} as it's already in use."
                self.logger(level="warning", message=err_message)
                self._config.push_summary_manager.add_object_status(
                    obj=self, obj_detail=f"Reservation {reservation['identity']}", obj_type="uuidpool.Reservation",
                    status="skipped", message=err_message
                )

        return True


class IntersightWwnnPool(IntersightConfigObject):
    _CONFIG_NAME = "WWNN Pool"
    _CONFIG_SECTION_NAME = "wwnn_pools"
    _INTERSIGHT_SDK_OBJECT_NAME = "fcpool.Pool"

    def __init__(self, parent=None, fcpool_pool=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=fcpool_pool)

        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.name = self.get_attribute(attribute_name="name")
        self.wwnn_blocks = []
        self.reservations = []

        if self._config.load_from == "live":
            # Fetches the WWNN Blocks configurations
            if hasattr(self._object, "id_blocks"):
                for id_block in self._object.id_blocks:
                    self.wwnn_blocks.append({"from": id_block._from, "to": id_block.to})
            # Fetches the WWNN reservations
            self.reservations = self._get_reservations()

        elif self._config.load_from == "file":
            for attribute in ["wwnn_blocks", "reservations"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

        self.clean_object()

    def clean_object(self):
        # We use this to make sure all options of a WWNN Block are set to None if they are not present
        if self.wwnn_blocks:
            for uuid_block in self.wwnn_blocks:
                for attribute in ["from", "size", "to"]:
                    if attribute not in uuid_block:
                        uuid_block[attribute] = None
        # We use this to make sure all options of a reservations are set to None if they are not present
        if self.reservations:
            for reservation in self.reservations:
                for attribute in ["identity"]:
                    if attribute not in reservation:
                        reservation[attribute] = None

    def _find_overlapping_reservations(self, existing_reservations=None, to_be_pushed_reservations=None):
        fc_used = self._device.query(object_type="fcpool.PoolMember", filter="Assigned eq true")

        fc_used_identities = [pool_member.wwn_id for pool_member in fc_used]

        return _find_overlapping_reservations(existing_reservations=existing_reservations,
                                              to_be_pushed_reservations=to_be_pushed_reservations,
                                              used_identities=fc_used_identities)

    def _get_reservations(self):
        # Fetches the Reservations of a WWNN Pool
        if "fcpool_reservation" in self._config.sdk_objects:
            reservations = []
            for reservation in self._config.sdk_objects["fcpool_reservation"]:
                if hasattr(reservation, "pool"):
                    if reservation.pool.moid == self._moid:
                        reservations.append({"identity": reservation.identity})
            return reservations

        return None

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.fcpool_pool import FcpoolPool

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        id_blocks = []
        if self.wwnn_blocks:
            from intersight.model.fcpool_block import FcpoolBlock
            for id_block in self.wwnn_blocks:
                kwargs = {
                    "object_type": "fcpool.Block",
                    "class_id": "fcpool.Block",
                    "_from": id_block["from"]
                }
                if id_block.get("to"):
                    kwargs["to"] = id_block["to"]
                elif id_block.get("size"):
                    kwargs["size"] = id_block["size"]
                id_blocks.append(FcpoolBlock(**kwargs))

        org = self.get_parent_org_relationship()
        org_name = self._parent.name

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": org,
            "id_blocks": id_blocks,
            "pool_purpose": "WWNN"
        }
        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()

        fcpool_pool = FcpoolPool(**kwargs)

        fcpool = self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=fcpool_pool, detail=self.name,
                             return_relationship=True, key_attributes=["name", "pool_purpose"])
        if not fcpool:
            return False

        if not self.reservations:
            return True

        # Get the all the WWNN Pool reservations
        wwnn_reservations = self._device.query(object_type="fcpool.Reservation", expand="Organization")

        # Find overlapping, non overlapping and used reservations between wwnn_reservations and self.reservations
        overlapping_reservations, non_overlapping_reservations, used_reservations = self._find_overlapping_reservations(
            existing_reservations=wwnn_reservations,
            to_be_pushed_reservations=self.reservations
        )

        # Reservations which need to be newly created (Non Overlapping Reservations) are bulk pushed.
        if non_overlapping_reservations:
            # We now need to bulk push the fcpool.Reservation object for each Reservation in the list
            from intersight.model.bulk_request import BulkRequest
            from intersight.model.bulk_sub_request import BulkSubRequest
            from intersight.model.mo_base_mo import MoBaseMo

            bulk_request_kwargs = {
                "uri": "/v1/fcpool/Reservations",
                "verb": "POST",
                "requests": []
            }
            requests = []

            for reservation in non_overlapping_reservations:
                body_kwargs = {
                    "object_type": "fcpool.Reservation",
                    "class_id": "fcpool.Reservation",
                    "identity": reservation["identity"],
                    "id_purpose": "WWNN",
                    "organization": org,
                    "pool": fcpool
                }
                if self.tags is not None:
                    kwargs["tags"] = self.create_tags()

                body = MoBaseMo(**body_kwargs)

                sub_request_kwargs = {
                    "object_type": "bulk.RestSubRequest",
                    "class_id": "bulk.RestSubRequest",
                    "body": body
                }

                sub_request = BulkSubRequest(**sub_request_kwargs)

                requests.append(sub_request)

            # Bulk API can send maximum 100 requests per call. So we send the requests in groups of 100.
            start = 0
            end = 100
            while start < len(requests):
                start_identity = non_overlapping_reservations[start]["identity"]
                if end - 1 < len(non_overlapping_reservations):
                    end_identity = non_overlapping_reservations[end - 1]["identity"]
                else:
                    end_identity = non_overlapping_reservations[-1]["identity"]
                bulk_request_kwargs["requests"] = requests[start:end]
                bulk_request = BulkRequest(**bulk_request_kwargs)

                detail = f"{self.name} - {len(bulk_request_kwargs['requests'])} Reservations between identities " \
                         f"({start_identity}, {end_identity})"
                self.commit(object_type="bulk.Request", payload=bulk_request, detail=detail, key_attributes=[])
                start = end
                end += 100

        # These reservations already exist, so we skip them.
        if overlapping_reservations:
            for reservation in overlapping_reservations:
                if reservation["organization"] != org_name:
                    err_message = f"Failed to push object-type fcpool.Reservation with identity "\
                                  f"{reservation['identity']} as it already exists in an org "\
                                  f"'{reservation['organization']}' different than the {self._CONFIG_NAME} org "\
                                  f"'{org_name}'."
                    push_status = "failed"
                    self.logger(level="error", message=err_message)
                else:
                    err_message = f"Skipping push of object-type fcpool.Reservation with identity "\
                                  f"{reservation['identity']} as it already exists."
                    push_status = "skipped"
                    self.logger(level="warning", message=err_message)
                self._config.push_summary_manager.add_object_status(
                    obj=self, obj_detail=f"Reservation {reservation['identity']}", obj_type="fcpool.Reservation",
                    status=push_status, message=err_message
                )

        # These reservations already in-use by some profile, so we skip them.
        if used_reservations:
            for reservation in used_reservations:
                err_message = f"Skipping push of object-type fcpool.Reservation with identity "\
                              f"{reservation['identity']} as it's already in use."
                self.logger(level="warning", message=err_message)
                self._config.push_summary_manager.add_object_status(
                    obj=self, obj_detail=f"Reservation {reservation['identity']}", obj_type="fcpool.Reservation",
                    status="failed", message=err_message
                )

        return True


class IntersightWwpnPool(IntersightConfigObject):
    _CONFIG_NAME = "WWPN Pool"
    _CONFIG_SECTION_NAME = "wwpn_pools"
    _INTERSIGHT_SDK_OBJECT_NAME = "fcpool.Pool"

    def __init__(self, parent=None, fcpool_pool=None):
        IntersightConfigObject.__init__(self, parent=parent, sdk_object=fcpool_pool)

        self.descr = self.get_attribute(attribute_name="description", attribute_secondary_name="descr")
        self.name = self.get_attribute(attribute_name="name")
        self.wwpn_blocks = []
        self.reservations = []

        if self._config.load_from == "live":
            # Fetches the WWPN Blocks configurations
            if hasattr(self._object, "id_blocks"):
                for id_block in self._object.id_blocks:
                    self.wwpn_blocks.append({"from": id_block._from, "to": id_block.to})
                # Fetches the WWPN reservations
                self.reservations = self._get_reservations()

        elif self._config.load_from == "file":
            for attribute in ["wwpn_blocks", "reservations"]:
                setattr(self, attribute, None)
                if attribute in self._object:
                    setattr(self, attribute, self.get_attribute(attribute_name=attribute))

        self.clean_object()

    def clean_object(self):
        # We use this to make sure all options of a WWPN Block are set to None if they are not present
        if self.wwpn_blocks:
            for uuid_block in self.wwpn_blocks:
                for attribute in ["from", "size", "to"]:
                    if attribute not in uuid_block:
                        uuid_block[attribute] = None

        # We use this to make sure all options of a reservations are set to None if they are not present
        if self.reservations:
            for reservation in self.reservations:
                for attribute in ["identity"]:
                    if attribute not in reservation:
                        reservation[attribute] = None

    def _find_overlapping_reservations(self, existing_reservations=None, to_be_pushed_reservations=None):
        fc_used = self._device.query(object_type="fcpool.PoolMember", filter="Assigned eq true")

        fc_used_identities = [pool_member.wwn_id for pool_member in fc_used]

        return _find_overlapping_reservations(existing_reservations=existing_reservations,
                                              to_be_pushed_reservations=to_be_pushed_reservations,
                                              used_identities=fc_used_identities)

    def _get_reservations(self):
        # Fetches the Reservations of a WWPN Pool
        if "fcpool_reservation" in self._config.sdk_objects:
            reservations = []
            for reservation in self._config.sdk_objects["fcpool_reservation"]:
                if hasattr(reservation, "pool"):
                    if reservation.pool.moid == self._moid:
                        reservations.append({"identity": reservation.identity})
            return reservations

        return None

    @IntersightConfigObject.update_taskstep_description()
    def push_object(self):
        from intersight.model.fcpool_pool import FcpoolPool

        self.logger(message=f"Pushing {self._CONFIG_NAME} configuration: {self.name}")

        id_blocks = []
        if self.wwpn_blocks:
            from intersight.model.fcpool_block import FcpoolBlock
            for id_block in self.wwpn_blocks:
                kwargs = {
                    "object_type": "fcpool.Block",
                    "class_id": "fcpool.Block",
                    "_from": id_block["from"]
                }
                if id_block.get("to"):
                    kwargs["to"] = id_block["to"]
                elif id_block.get("size"):
                    kwargs["size"] = id_block["size"]
                id_blocks.append(FcpoolBlock(**kwargs))

        org = self.get_parent_org_relationship()
        org_name = self._parent.name

        kwargs = {
            "object_type": self._INTERSIGHT_SDK_OBJECT_NAME,
            "class_id": self._INTERSIGHT_SDK_OBJECT_NAME,
            "organization": self.get_parent_org_relationship(),
            "id_blocks": id_blocks,
            "pool_purpose": "WWPN"
        }
        if self.name is not None:
            kwargs["name"] = self.name
        if self.descr is not None:
            kwargs["description"] = self.descr
        if self.tags is not None:
            kwargs["tags"] = self.create_tags()

        fcpool_pool = FcpoolPool(**kwargs)

        fcpool = self.commit(object_type=self._INTERSIGHT_SDK_OBJECT_NAME, payload=fcpool_pool, detail=self.name,
                             return_relationship=True, key_attributes=["name", "pool_purpose"])
        if not fcpool:
            return False

        if not self.reservations:
            return True

        # Get the all the WWPN Pool reservations
        wwpn_reservations = self._device.query(object_type="fcpool.Reservation", expand="Organization")

        # Find overlapping, non overlapping and used reservations between wwpn_reservations and self.reservations
        overlapping_reservations, non_overlapping_reservations, used_reservations = self._find_overlapping_reservations(
            existing_reservations=wwpn_reservations,
            to_be_pushed_reservations=self.reservations
        )

        # Reservations which need to be newly created (Non Overlapping Reservations) are bulk pushed.
        if non_overlapping_reservations:
            # We now need to bulk push the fcpool.Reservation object for each Reservation in the list
            from intersight.model.bulk_request import BulkRequest
            from intersight.model.bulk_sub_request import BulkSubRequest
            from intersight.model.mo_base_mo import MoBaseMo

            bulk_request_kwargs = {
                "uri": "/v1/fcpool/Reservations",
                "verb": "POST",
                "requests": []
            }
            requests = []

            for reservation in non_overlapping_reservations:
                body_kwargs = {
                    "object_type": "fcpool.Reservation",
                    "class_id": "fcpool.Reservation",
                    "identity": reservation["identity"],
                    "id_purpose": "WWPN",
                    "organization": org,
                    "pool": fcpool
                }
                if self.tags is not None:
                    kwargs["tags"] = self.create_tags()

                body = MoBaseMo(**body_kwargs)

                sub_request_kwargs = {
                    "object_type": "bulk.RestSubRequest",
                    "class_id": "bulk.RestSubRequest",
                    "body": body
                }

                sub_request = BulkSubRequest(**sub_request_kwargs)

                requests.append(sub_request)

            # Bulk API can send maximum 100 requests per call. So we send the requests in groups of 100.
            start = 0
            end = 100
            while start < len(requests):
                start_identity = non_overlapping_reservations[start]["identity"]
                if end - 1 < len(non_overlapping_reservations):
                    end_identity = non_overlapping_reservations[end - 1]["identity"]
                else:
                    end_identity = non_overlapping_reservations[-1]["identity"]
                bulk_request_kwargs["requests"] = requests[start:end]
                bulk_request = BulkRequest(**bulk_request_kwargs)

                detail = f"{self.name} - {len(bulk_request_kwargs['requests'])} Reservations between identities " \
                         f"({start_identity}, {end_identity})"
                self.commit(object_type="bulk.Request", payload=bulk_request, detail=detail, key_attributes=[])
                start = end
                end += 100

        # These reservations already exist, so we skip them.
        if overlapping_reservations:
            for reservation in overlapping_reservations:
                if reservation["organization"] != org_name:
                    err_message = f"Failed to push object-type fcpool.Reservation with identity "\
                                  f"{reservation['identity']} as it already exists in an org "\
                                  f"'{reservation['organization']}' different than the {self._CONFIG_NAME} org "\
                                  f"'{org_name}'."
                    push_status = "failed"
                    self.logger(level="error", message=err_message)
                else:
                    err_message = f"Skipping push of object-type fcpool.Reservation with identity "\
                                  f"{reservation['identity']} as it already exists."
                    push_status = "skipped"
                    self.logger(level="warning", message=err_message)
                self._config.push_summary_manager.add_object_status(
                    obj=self, obj_detail=f"Reservation {reservation['identity']}", obj_type="fcpool.Reservation",
                    status=push_status, message=err_message
                )

        # These reservations already in-use by some profile, so we skip them.
        if used_reservations:
            for reservation in used_reservations:
                err_message = f"Skipping push of object-type fcpool.Reservation with identity "\
                              f"{reservation['identity']} as it's already in use."
                self.logger(level="warning", message=err_message)
                self._config.push_summary_manager.add_object_status(
                    obj=self, obj_detail=f"Reservation {reservation['identity']}", obj_type="fcpool.Reservation",
                    status="skipped", message=err_message
                )

        return True
