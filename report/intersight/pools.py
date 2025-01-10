# coding: utf-8
# !/usr/bin/env python

""" pools.py: Easy UCS Deployment Tool """

from report.content import *
from report.ucs.section import UcsReportSection
from report.ucs.table import UcsReportTable
import ipaddress


class IntersightIpPoolsReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title="IP Pools"):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config

        ip_pools_list = []
        # Searching for all IP Pools
        for org in config.orgs:
            self.parse_org(org, ip_pools_list, element_to_parse="ip_pools")

        if ip_pools_list:
            for ip_pool in ip_pools_list:
                self.content_list.append(
                    IntersightIpPoolReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        ip_pool=ip_pool,
                        title=f"IP Pool {ip_pool.name}"
                    )
                )
        else:
            text = f"No IP Pools found."
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=text,
                    italicized=True,
                )
            )


class IntersightIpPoolReportSection(UcsReportSection):
    def __init__(self, order_id, parent, ip_pool, title):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightIpPoolReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                centered=True,
                ip_pool=ip_pool
            )
        )

        if hasattr(ip_pool, "ipv4_configuration") and ip_pool.ipv4_configuration:
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string="\nIPv4 Configuration Details: ",
                    bolded=True,
                )
            )

            self.content_list.append(
                IntersightIpPoolIpv4ConfigReportTable(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    centered=True,
                    ip_pool=ip_pool,
                )
            )

            if hasattr(ip_pool, "ipv4_blocks") and ip_pool.ipv4_blocks:
                self.content_list.append(
                    GenericReportText(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        string="\nIPv4 Block Details: ",
                        bolded=True,
                    )
                )

                self.content_list.append(
                    IntersightIpPoolIpv4BlocksReportTable(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        centered=True,
                        ipv4_blocks=ip_pool.ipv4_blocks
                    )
                )

        if hasattr(ip_pool, "ipv6_configuration") and ip_pool.ipv6_configuration:
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string="\nIPv6 Configuration Details: ",
                    bolded=True,
                )
            )

            self.content_list.append(
                IntersightIpPoolIpv6ConfigReportTable(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    centered=True,
                    ip_pool=ip_pool,
                )
            )

            if hasattr(ip_pool, "ipv6_blocks") and ip_pool.ipv6_blocks:
                self.content_list.append(
                    GenericReportText(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        string="\nIPv6 Block Details: ",
                        bolded=True,
                    )
                )

                self.content_list.append(
                    IntersightIpPoolIpv6BlocksReportTable(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        centered=True,
                        ipv6_blocks=ip_pool.ipv6_blocks
                    )
                )


class IntersightIpPoolReportTable(UcsReportTable):
    def __init__(self, order_id, parent, ip_pool, centered=False):

        rows = [
            ["Description", "Value"],
            ["Name", ip_pool.name],
            ["Description", ip_pool.descr],
            ["Organization", ip_pool._parent.name],
            ["Configure Subnet at Block Level", ip_pool.configure_subnet_at_block_level]
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightIpPoolIpv4ConfigReportTable(UcsReportTable):
    def __init__(self, order_id, parent, ip_pool, centered=False):

        rows = [
            ["Description", "Value"],
            ["Gateway", ip_pool.ipv4_configuration["gateway"]],
            ["Netmask", ip_pool.ipv4_configuration["netmask"]],
        ]

        if "primary_dns" in ip_pool.ipv4_configuration.keys() and ip_pool.ipv4_configuration["primary_dns"]:
            rows.append(["Primary DNS", ip_pool.ipv4_configuration["primary_dns"]])
        if "secondary_dns" in ip_pool.ipv4_configuration.keys() and ip_pool.ipv4_configuration["secondary_dns"]:
            rows.append(["Secondary DNS", ip_pool.ipv4_configuration["secondary_dns"]])

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightIpPoolIpv4BlocksReportTable(UcsReportTable):
    def __init__(self, order_id, parent, ipv4_blocks, centered=False):

        rows = [["ID", "From", "To", "Size"]]

        for block_num, block in enumerate(ipv4_blocks):
            size = (int(ipaddress.IPv4Address(block["to"])) - int(ipaddress.IPv4Address(block["from"])) + 1)
            rows.append([block_num + 1, block["from"], block["to"], size])

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightIpPoolIpv6ConfigReportTable(UcsReportTable):
    def __init__(self, order_id, parent, ip_pool, centered=False):

        rows = [
            ["Description", "Value"],
            ["Gateway", ip_pool.ipv6_configuration["gateway"]],
            ["Prefix", str(ip_pool.ipv6_configuration["prefix"])],
        ]

        if "primary_dns" in ip_pool.ipv6_configuration.keys() and ip_pool.ipv6_configuration["primary_dns"]:
            rows.append(["Primary DNS", ip_pool.ipv6_configuration["primary_dns"]])
        if "secondary_dns" in ip_pool.ipv6_configuration.keys() and ip_pool.ipv6_configuration["secondary_dns"]:
            rows.append(["Secondary DNS", ip_pool.ipv6_configuration["secondary_dns"]])

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightIpPoolIpv6BlocksReportTable(UcsReportTable):
    def __init__(self, order_id, parent, ipv6_blocks, centered=False):

        rows = [["ID", "From", "To", "Size"]]

        for block_num, block in enumerate(ipv6_blocks):
            size = (int(ipaddress.IPv6Address(block["to"])) - int(ipaddress.IPv6Address(block["from"])) + 1)
            rows.append([block_num + 1, block["from"], block["to"], size])

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightIqnPoolsReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title="IQN Pools"):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config

        iqn_pools_list = []
        # Searching for all IQN Pools
        for org in config.orgs:
            self.parse_org(org, iqn_pools_list, element_to_parse="iqn_pools")

        if iqn_pools_list:
            for iqn_pool in iqn_pools_list:
                self.content_list.append(
                    IntersightIqnPoolReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        iqn_pool=iqn_pool,
                        title=f"IQN Pool {iqn_pool.name}"
                    )
                )
        else:
            text = f"No IQN Pools found."
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=text,
                    italicized=True,
                )
            )


class IntersightIqnPoolReportSection(UcsReportSection):
    def __init__(self, order_id, parent, iqn_pool, title):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightIqnPoolReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                centered=True,
                iqn_pool=iqn_pool
            )
        )

        if hasattr(iqn_pool, "iqn_blocks") and iqn_pool.iqn_blocks:
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string="\nIQN Block Details: ",
                    bolded=True,
                )
            )

            self.content_list.append(
                IntersightIqnPoolIqnBlocksReportTable(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    centered=True,
                    iqn_blocks=iqn_pool.iqn_blocks
                )
            )


class IntersightIqnPoolReportTable(UcsReportTable):
    def __init__(self, order_id, parent, iqn_pool, centered=False):

        rows = [
            ["Description", "Value"],
            ["Name", iqn_pool.name],
            ["Description", iqn_pool.descr],
            ["Organization", iqn_pool._parent.name],
            ["Prefix", iqn_pool.prefix]
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightIqnPoolIqnBlocksReportTable(UcsReportTable):
    def __init__(self, order_id, parent, iqn_blocks, centered=False):

        rows = [["ID", "Suffix", "From", "To", "Size"]]

        for block_num, block in enumerate(iqn_blocks):
            size = int(str(block["to"])) - int(str(block["from"])) + 1
            rows.append([block_num + 1, block["suffix"], block["from"], block["to"], size])

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightMacPoolsReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title="MAC Pools"):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config

        mac_pools_list = []
        # Searching for all MAC Pools
        for org in config.orgs:
            self.parse_org(org, mac_pools_list, element_to_parse="mac_pools")

        if mac_pools_list:
            for mac_pool in mac_pools_list:
                self.content_list.append(
                    IntersightMacPoolReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        mac_pool=mac_pool,
                        title=f"MAC Pool {mac_pool.name}"
                    )
                )
        else:
            text = f"No MAC Pools found."
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=text,
                    italicized=True,
                )
            )


class IntersightMacPoolReportSection(UcsReportSection):
    def __init__(self, order_id, parent, mac_pool, title):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightMacPoolReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                centered=True,
                mac_pool=mac_pool
            )
        )

        if hasattr(mac_pool, "mac_blocks") and mac_pool.mac_blocks:
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string="\nMAC Block Details: ",
                    bolded=True,
                )
            )

            self.content_list.append(
                IntersightMacPoolMacBlocksReportTable(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    centered=True,
                    mac_blocks=mac_pool.mac_blocks
                )
            )


class IntersightMacPoolReportTable(UcsReportTable):
    def __init__(self, order_id, parent, mac_pool, centered=False):

        rows = [
            ["Description", "Value"],
            ["Name", mac_pool.name],
            ["Description", mac_pool.descr],
            ["Organization", mac_pool._parent.name],
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightMacPoolMacBlocksReportTable(UcsReportTable):
    def __init__(self, order_id, parent, mac_blocks, centered=False):

        rows = [["ID", "From", "To", "Size"]]
        for block_num, block in enumerate(mac_blocks):
            size = (
                int(str(block["to"]).replace("-", "").replace(":", ""), 16)
                - int(str(block["from"]).replace("-", "").replace(":", ""), 16)
                + 1
            )
            rows.append([block_num + 1, block["from"], block["to"], size])

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightResourcePoolsReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title="Resource Pools"):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config

        resource_pools_list = []
        # Searching for all Resource Pools
        for org in config.orgs:
            self.parse_org(org, resource_pools_list, element_to_parse="resource_pools")

        if resource_pools_list:
            for resource_pool in resource_pools_list:
                self.content_list.append(
                    IntersightResourcePoolReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        resource_pool=resource_pool,
                        title=f"Resource Pool {resource_pool.name}"
                    )
                )
        else:
            text = f"No Resource Pools found."
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=text,
                    italicized=True,
                )
            )


class IntersightResourcePoolReportSection(UcsReportSection):
    def __init__(self, order_id, parent, resource_pool, title):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightResourcePoolReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                centered=True,
                resource_pool=resource_pool
            )
        )


class IntersightResourcePoolReportTable(UcsReportTable):
    def __init__(self, order_id, parent, resource_pool, centered=False):

        rows = [
            ["Description", "Value"],
            ["Name", resource_pool.name],
            ["Description", resource_pool.descr],
            ["Organization", resource_pool._parent.name],
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightUuidPoolsReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title="UUID Pools"):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config

        uuid_pools_list = []
        # Searching for all UUID Pools
        for org in config.orgs:
            self.parse_org(org, uuid_pools_list, element_to_parse="uuid_pools")

        if uuid_pools_list:
            for uuid_pool in uuid_pools_list:
                self.content_list.append(
                    IntersightUuidPoolReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        uuid_pool=uuid_pool,
                        title=f"UUID Pool {uuid_pool.name}"
                    )
                )
        else:
            text = f"No UUID Pools found."
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=text,
                    italicized=True,
                )
            )


class IntersightUuidPoolReportSection(UcsReportSection):
    def __init__(self, order_id, parent, uuid_pool, title):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightUuidPoolReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                centered=True,
                uuid_pool=uuid_pool
            )
        )

        if hasattr(uuid_pool, "uuid_blocks") and uuid_pool.uuid_blocks:
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string="\nUUID Block Details: ",
                    bolded=True,
                )
            )

            self.content_list.append(
                IntersightUuidPoolUuidBlocksReportTable(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    centered=True,
                    uuid_blocks=uuid_pool.uuid_blocks,
                )
            )


class IntersightUuidPoolReportTable(UcsReportTable):
    def __init__(self, order_id, parent, uuid_pool, centered=False):

        rows = [
            ["Description", "Value"],
            ["Name", uuid_pool.name],
            ["Description", uuid_pool.descr],
            ["Organization", uuid_pool._parent.name],
            ["Prefix", uuid_pool.prefix]
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightUuidPoolUuidBlocksReportTable(UcsReportTable):
    def __init__(self, order_id, parent, uuid_blocks, centered=False):

        rows = [["ID", "From", "To", "Size"]]

        for block_num, block in enumerate(uuid_blocks):
            size = (
                int(str(block["to"]).replace("-", ""), 16)
                - int(str(block["from"]).replace("-", ""), 16)
                + 1
            )
            rows.append([block_num + 1, block["from"], block["to"], size])

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightWwnnPoolsReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title="WWNN Pools"):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config

        wwnn_pools_list = []
        # Searching for all WWNN Pools
        for org in config.orgs:
            self.parse_org(org, wwnn_pools_list, element_to_parse="wwnn_pools")

        if wwnn_pools_list:
            for wwnn_pool in wwnn_pools_list:
                self.content_list.append(
                    IntersightWwnnPoolReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        wwnn_pool=wwnn_pool,
                        title=f"WWNN Pool {wwnn_pool.name}"
                    )
                )
        else:
            text = f"No WWNN Pools found."
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=text,
                    italicized=True,
                )
            )


class IntersightWwnnPoolReportSection(UcsReportSection):
    def __init__(self, order_id, parent, wwnn_pool, title):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightWwnnPoolReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                centered=True,
                wwnn_pool=wwnn_pool
            )
        )

        if hasattr(wwnn_pool, "wwnn_blocks") and wwnn_pool.wwnn_blocks:
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string="\nWWNN Block Details: ",
                    bolded=True,
                )
            )

            self.content_list.append(
                IntersightWwnnPoolWwnnBlocksReportTable(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    centered=True,
                    wwnn_blocks=wwnn_pool.wwnn_blocks,
                )
            )


class IntersightWwnnPoolReportTable(UcsReportTable):
    def __init__(self, order_id, parent, wwnn_pool, centered=False):

        rows = [
            ["Description", "Value"],
            ["Name", wwnn_pool.name],
            ["Description", wwnn_pool.descr],
            ["Organization", wwnn_pool._parent.name],
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightWwnnPoolWwnnBlocksReportTable(UcsReportTable):
    def __init__(self, order_id, parent, wwnn_blocks, centered=False):

        rows = [["ID", "From", "To", "Size"]]

        for block_num, block in enumerate(wwnn_blocks):
            size = (
                int(str(block["to"]).replace("-", "").replace(":", ""), 16)
                - int(str(block["from"]).replace("-", "").replace(":", ""), 16)
                + 1
            )
            rows.append([block_num + 1, block["from"], block["to"], size])

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightWwpnPoolsReportSection(UcsReportSection):
    def __init__(self, order_id, parent, title="WWPN Pools"):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)
        config = self.report.config

        wwpn_pools_list = []
        # Searching for all WWPN Pools
        for org in config.orgs:
            self.parse_org(org, wwpn_pools_list, element_to_parse="wwpn_pools")

        if wwpn_pools_list:
            for wwpn_pool in wwpn_pools_list:
                self.content_list.append(
                    IntersightWwpnPoolReportSection(
                        order_id=self.report.get_current_order_id(),
                        parent=self,
                        wwpn_pool=wwpn_pool,
                        title=f"WWPN Pool {wwpn_pool.name}"
                    )
                )
        else:
            text = f"No WWPN Pools found."
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string=text,
                    italicized=True,
                )
            )


class IntersightWwpnPoolReportSection(UcsReportSection):
    def __init__(self, order_id, parent, wwpn_pool, title):
        UcsReportSection.__init__(self, order_id=order_id, parent=parent, title=title)

        self.content_list.append(
            IntersightWwpnPoolReportTable(
                order_id=self.report.get_current_order_id(),
                parent=self,
                centered=True,
                wwpn_pool=wwpn_pool
            )
        )

        if hasattr(wwpn_pool, "wwpn_blocks") and wwpn_pool.wwpn_blocks:
            self.content_list.append(
                GenericReportText(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    string="\nWWPN Block Details: ",
                    bolded=True,
                )
            )

            self.content_list.append(
                IntersightWwpnPoolWwpnBlocksReportTable(
                    order_id=self.report.get_current_order_id(),
                    parent=self,
                    centered=True,
                    wwpn_blocks=wwpn_pool.wwpn_blocks,
                )
            )


class IntersightWwpnPoolReportTable(UcsReportTable):
    def __init__(self, order_id, parent, wwpn_pool, centered=False):

        rows = [
            ["Description", "Value"],
            ["Name", wwpn_pool.name],
            ["Description", wwpn_pool.descr],
            ["Organization", wwpn_pool._parent.name],
        ]

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )


class IntersightWwpnPoolWwpnBlocksReportTable(UcsReportTable):
    def __init__(self, order_id, parent, wwpn_blocks, centered=False):

        rows = [["ID", "From", "To", "Size"]]

        for block_num, block in enumerate(wwpn_blocks):
            size = (
                int(str(block["to"]).replace("-", "").replace(":", ""), 16)
                - int(str(block["from"]).replace("-", "").replace(":", ""), 16)
                + 1
            )
            rows.append([block_num + 1, block["from"], block["to"], size])

        UcsReportTable.__init__(
            self,
            order_id=order_id,
            parent=parent,
            row_number=len(rows),
            column_number=len(rows[1]),
            centered=centered,
            cells_list=rows,
        )
