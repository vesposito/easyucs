# coding: utf-8
# !/usr/bin/env python

""" plot.py: Easy UCS Deployment Tool """
from easyucs import __author__, __copyright__,  __version__, __status__

import math
import networkx as nx
import matplotlib.pyplot as plt
from PIL import Image
import os
import json

from easyucs.config.ucs.servers import UcsSystemServiceProfile, UcsSystemBiosPolicy, UcsSystemBootPolicy, \
    UcsSystemMaintenancePolicy, UcsSystemLocalDiskConfPolicy, UcsSystemVnicVhbaPlacementPolicy, UcsSystemVmediaPolicy, \
    UcsSystemSerialOverLanPolicy, UcsSystemThresholdPolicy,UcsSystemPowerControlPolicy,UcsSystemScrubPolicy,\
    UcsSystemKvmManagementPolicy, UcsSystemGraphicsCardPolicy, UcsSystemPowerSyncPolicy, UcsSystemIpmiAccessProfile, \
    UcsSystemUuidPool, UcsSystemServerPool, UcsSystemHostFirmwarePackage
from easyucs.config.ucs.lan import UcsSystemLanConnectivityPolicy, UcsSystemDynamicVnicConnectionPolicy
from easyucs.config.ucs.san import UcsSystemSanConnectivityPolicy, UcsSystemWwnnPool
from easyucs.config.ucs.storage import UcsSystemStorageProfile

# All shapes : https://matplotlib.org/api/markers_api.html
# Color examples : https://matplotlib.org/examples/color/named_colors.html



class UcsSystemConfigPlot():
    def __init__(self, parent=None, config=None):
        # Parent is a config manager
        self.parent = parent
        self.config = config

        self.target = self.parent.parent.target


    def logger(self, level='info', message="No message"):
        self.parent.logger(level=level, message=message)

    def hierarchy_pos(self, G, root=None, width=1., vert_gap=0.2, vert_loc=0, xcenter=0.5):
        import networkx as nx
        import random
        '''
        From Joel's answer at https://stackoverflow.com/a/29597209/2966723.
        Licensed under Creative Commons Attribution-Share Alike

        If the graph is a tree this will return the positions to plot this in a
        hierarchical layout.

        G: the graph (must be a tree)

        root: the root node of current branch
        - if the tree is directed and this is not given,
          the root will be found and used
        - if the tree is directed and this is given, then
          the positions will be just for the descendants of this node.
        - if the tree is undirected and not given,
          then a random choice will be used.

        width: horizontal space allocated for this branch - avoids overlap with other branches

        vert_gap: gap between levels of hierarchy

        vert_loc: vertical location of root

        xcenter: horizontal location of root
        '''
        if not nx.is_tree(G):
            raise TypeError('cannot use hierarchy_pos on a graph that is not a tree')

        if root is None:
            if isinstance(G, nx.DiGraph):
                root = next(iter(nx.topological_sort(G)))  # allows back compatibility with nx version 1.11
            else:
                root = random.choice(list(G.nodes))

        def _hierarchy_pos(G, root, width=1., vert_gap=0.2, vert_loc=0, xcenter=0.5, pos=None, parent=None):
            '''
            see hierarchy_pos docstring for most arguments

            pos: a dict saying where all nodes go if they have been assigned
            parent: parent of this branch. - only affects it if non-directed

            '''

            if pos is None:
                pos = {root: (xcenter, vert_loc)}
            else:
                pos[root] = (xcenter, vert_loc)
            children = list(G.neighbors(root))
            if not isinstance(G, nx.DiGraph) and parent is not None:
                children.remove(parent)
            if len(children) != 0:
                dx = width / len(children)
                nextx = xcenter - width / 2 - dx / 2
                for child in children:
                    nextx += dx
                    pos = _hierarchy_pos(G, child, width=dx, vert_gap=vert_gap,
                                         vert_loc=vert_loc - vert_gap, xcenter=nextx,
                                         pos=pos, parent=root)
            return pos

        return _hierarchy_pos(G, root, width, vert_gap, vert_loc, xcenter)

    def export_plots(self, export_format="png", directory="."):
        pass


class UcsSystemServiceProfileConfigPlot(UcsSystemConfigPlot):
    def __init__(self, parent=None, config=None):
        UcsSystemConfigPlot.__init__(self, parent=parent, config=config)

        self.service_profile_plots = {}

        self.draw_service_profile_dependencies()

    def draw_service_profile_dependencies(self):
        """
        Draws Service Profile dependencies using the specified config
        :return: True if draw is successful, False otherwise
        """

        def parse_org(org, service_profile_list):
            if org.service_profiles is not None:
                for service_profile in org.service_profiles:
                    if not service_profile.service_profile_template:
                        service_profile_list.append(service_profile)
            if hasattr(org, "orgs"):
                if org.orgs is not None:
                    for suborg in org.orgs:
                        parse_org(suborg, service_profile_list)

        if self.config is None:
            # We could not find any config
            self.logger(level="error",
                        message="Could not find any config to use for drawing service profile dependencies!")
            return False

        service_profile_list = []
        # Searching for all Service Profiles (template or not) that are not from a template in all orgs
        for org in self.config.orgs:
            parse_org(org, service_profile_list)

        # Parsing all service profiles and draw plot
        for service_profile in service_profile_list:
            G = nx.Graph()
            sp_options_dict = self.get_service_profile_plot_options()
            if not sp_options_dict:
                self.logger(level="error", message="Service Profile options for plot not imported.")
                continue
            # Save the Figure as fig for later use (save it and use it later)
            fig = plt.figure(figsize=(25, 10))
            plt.xlim(-0.25, 0.25)
            plt.ylim(-0.235, 0.235)

            # Create a dict to change the label's name and options (color, size) afterward
            # ex.     node: (new_label_name, node_options)
            labels_dict = {}

            # Get the config object through the "config_object_name" string info in the service_profile_plot_options
            config_object = eval(sp_options_dict["service_profile"]["config_object_name"])

            if "template" in service_profile.type:
                self.node_service_profile = config_object._CONFIG_NAME + " Template\n" + service_profile.name
            else:
                self.node_service_profile = config_object._CONFIG_NAME + "\n" + service_profile.name
            self.node_service_profile_options = sp_options_dict["service_profile"]
            self.node_service_profile_options["label"] = self.node_service_profile

            for sp_node, sp_node_options in sp_options_dict.items():
                if sp_node != "service_profile":
                    # if value of service_profile.*policy_name* != None
                    if eval('service_profile.' + sp_node):
                        # get the config object through the "config_object_name" string info in
                        # the service_profile_plot_options
                        config_object = eval(sp_node_options["config_object_name"])
                        # get the label name of a node (a specific policy). ex. "Boot Policy\ndefault"
                        node_label_name = config_object._CONFIG_NAME + "\n" + eval('service_profile.' + sp_node)

                        setattr(self, "node_" + sp_node, node_label_name)
                        sp_options_dict[sp_node]["label"] = getattr(self, "node_" + sp_node)
                        setattr(self, "node_" + sp_node + "_options", sp_options_dict[sp_node])
                        # Add a plot edge (link between two nodes)
                        G.add_edge(self.node_service_profile, sp_options_dict[sp_node]["label"])
                    else:
                        # Set the self.node_*policy* to None if the value is None in the Service Profile
                        setattr(self, "node_" + sp_node, None)

            # Get position for shattered view
            pos = self.hierarchy_pos(G, root=self.node_service_profile, width=2 * math.pi, xcenter=0)
            pos = {u: (r * math.cos(theta), r * math.sin(theta)) for u, (theta, r) in pos.items()}

            # Get position for top-down view (not used)
            # pos = self.hierarchy_pos(G, root=self.node_service_profile)

            # Setting options for each edge and node (a node is characterized only by a name (label))
            for node in ["node_" + i for i in sp_options_dict]:  # the list includes all of the policies supported
                node_label_name = getattr(self, node)
                if getattr(self, node) is None:
                    continue
                node_options = getattr(self, node + "_options")
                # Set options for a node
                nx.draw_networkx_nodes(G, pos,
                                       node_color=node_options["color"],
                                       nodelist=[node_label_name],
                                       node_size=node_options["size"],
                                       node_shape=node_options["shape"]
                                       )

                if node != "node_service_profile":
                    # Set options for an edge
                    nx.draw_networkx_edges(G, pos,
                                           edgelist=[
                                               (self.node_service_profile, node_label_name)])

                    edge_labels = {(self.node_service_profile, node_label_name): " ".join(
                        node_label_name.split("\n")[0:1])}

                    nx.draw_networkx_edge_labels(G,
                                                 pos,
                                                 rotate=True,
                                                 font_color='black',
                                                 font_size=11,
                                                 label_pos=0.5,
                                                 edge_labels=edge_labels
                                                 )

                    # Create a dict of label key associate with an alias to remove
                    # the unique identifier ("\n" and *policy name*)
                    # ex. 'Service Profile\nTest': 'Test'
                    labels_dict[node_label_name] = (node_label_name.split("\n")[1], node_options)
                else:
                    # Create a dict of label key associate with an alias to remove
                    # To fit into the square of the SP, it need to be split each 9 character
                    n = 9
                    line = node_label_name.split("\n")[1]
                    line = "\n".join([line[i:i + n] for i in range(0, len(line), n)])
                    labels_dict[node_label_name] = (line, node_options)

            # Raise text positions to be above the shape of the node
            for p in pos:
                for key, policy in sp_options_dict.items():
                    if "label" in policy:
                        if policy["label"] == p:
                            if key != "service_profile":
                                temp_pos = list(pos[p])
                                temp_pos[1] += 0.02
                                pos[p] = tuple(temp_pos)
                                del temp_pos
                                break  # the nearest loop

            # Add the labels alias using the dict created before
            for node, (label_node_name, label_node_option) in labels_dict.items():
                nx.draw_networkx_labels(G, pos,
                                        labels={node: label_node_name},
                                        font_color=label_node_option["node_font_color"],
                                        font_weight=label_node_option["node_font_weight"]
                                        )

            title = service_profile._parent._dn + "\n" + self.node_service_profile
            plt.title(title)

            self.service_profile_plots[service_profile] = fig

    def export_plots(self, export_format="png", directory="."):
        for service_profile, plot in self.service_profile_plots.items():
            if "template" in service_profile.type:
                file_name = directory + "/" + self.target + "_" + service_profile._parent._dn.replace("/", "_") + \
                       "_Service_Profile_Template_" + "_".join(
                    service_profile.name.split(" "))
            else:
                file_name = directory + "/" + self.target + "_" + service_profile._parent._dn.replace("/", "_") + \
                            "_Service_Profile_" + "_".join(
                    service_profile.name.split(" "))

            file = file_name + '_original.' + export_format
            # plot.show()
            plot.savefig(file)
            # Close the figure to save on memory
            plt.close(fig=plot)
            # Cropping the image to reduce white borders
            original = Image.open(file)
            left = 315
            top = 122
            right = 2248
            bottom = 888
            cropped = original.crop((left, top, right, bottom))
            cropped_file = file_name + '.' + export_format
            cropped.save(cropped_file)
            os.remove(file)

            self.logger(level="debug", message="Plot of service profile " +
                                               service_profile.name + " saved at: " + cropped_file)

    @staticmethod
    def get_service_profile_plot_options():
        filename = "./config/service_profile_plot_options.json"
        if os.path.isfile(filename):
            json_file = open(filename)
            service_profile_plot_options = json.loads(json_file.read())
            json_file.close()
            return service_profile_plot_options.copy()
        return None


class UcsSystemOrgConfigPlot(UcsSystemConfigPlot):
    def __init__(self, parent=None, config=None):
        UcsSystemConfigPlot.__init__(self, parent=parent, config=config)

        self.org_plot = None

        self.draw_org_dependencies()

    def draw_org_dependencies(self):
        """
        Draws Orgs dependencies using the specified config
        :param uuid: The UUID of the config to be used. If not specified, the most recent config will be used
        :return: True if draw is successful, False otherwise
        """

        def parse_org(org, current_list, G):
            if hasattr(org, "orgs"):
                if org.orgs is not None:
                    for suborg in org.orgs:
                        current_list.append({suborg.name: []})
                        parse_org(suborg, current_list[-1][suborg.name], G)
                        G.add_edge(org._dn, suborg._dn)

        if self.config is None:
            # We could not find any config
            self.logger(level="error",
                        message="Could not find any config to use for drawing service profile dependencies!")
            return False

        # Draw plot
        G = nx.Graph()
        # Save the Figure as fig for later use (save it and use it later)
        fig = plt.figure(figsize=(25, 10))

        # Starting dict of orgs
        orgs_dict = {"root": []}
        G.add_node("org-root")
        # Searching for all orgs
        for org in self.config.orgs:
            parse_org(org, orgs_dict["root"], G)

        # Get position for shattered view (not used)
        # pos = self.hierarchy_pos(G, root="org-root", width=2 * math.pi, xcenter=0)
        # pos = {u: (r * math.cos(theta), r * math.sin(theta)) for u, (theta, r) in pos.items()}

        # Get position for top-down view (if less than 10 org (excluding root) are present)
        if len(G._node) < 11:
            pos = self.hierarchy_pos(G, root="org-root")
            mode_pos = "hierarchy_pos"
        # Get position for kamada_kawai_layout view
        else:
            pos = nx.kamada_kawai_layout(G)
            mode_pos = "kamada_kawai_layout"

        # Draw nodes, edges and labels
        nx.draw_networkx_nodes(G, pos, node_shape="v", node_size=1000)
        # Put a red color for the root Org
        nx.draw_networkx_nodes(G, pos,
                               node_color="red",
                               node_shape="v",
                               node_size=1000,
                               nodelist=["org-root"]
                               )
        nx.draw_networkx_edges(G, pos)

        labels_dict = {}

        # Raise text positions to be above the shape of the node
        for p in pos:
            temp_pos = list(pos[p])
            if mode_pos == "hierarchy_pos":
                temp_pos[1] += 0.02
            elif mode_pos == "kamada_kawai_layout":
                temp_pos[1] += 0.08
            pos[p] = tuple(temp_pos)
            del temp_pos

            labels_dict[p] = p.replace("org-", "").split("/")[-1]

        nx.draw_networkx_labels(G, pos,
                                labels=labels_dict)

        title = "Orgs"
        plt.title(title)

        self.org_plot = fig

    def export_plots(self, export_format="png", directory="."):

        if self.org_plot:
            file_name = directory + "/" + self.target + "_" + "orgs"
            file = file_name + '_original.' + export_format
            # plot.show()
            self.org_plot.savefig(file)

            # Cropping the image to reduce white borders
            original = Image.open(file)
            left = 315
            top = 122
            right = 2248
            bottom = 888
            cropped = original.crop((left, top, right, bottom))
            cropped_file = file_name + '.' + export_format
            cropped.save(cropped_file)
            os.remove(file)

            self.logger(level="debug", message="Plot of orgs saved at: " + file)
