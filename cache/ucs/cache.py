import datetime

from cache.cache import GenericCache


class GenericUcsCache(GenericCache):
    def __init__(self, parent=None):
        GenericCache.__init__(self, parent=parent)
        self.orgs = {"orgs": {"root": {"description": ""}}}
        self.server_details = []

    def fetch_orgs(self):
        """
        Fetches the UCS Organizations
        :return: List of Orgs if successful, None otherwise
        """
        task_step_name = "FetchOrgs"
        # Start the "FetchOrgs" task step only if it exists in the current task's taskstep list.
        # If the device has no task or "FetchOrgs" is not part of the task steps, skip starting the task step.
        if self.device.task is not None and task_step_name in self.device.task.taskstep_manager.taskstep_list:
            self.device.task.taskstep_manager.start_taskstep(
                name=task_step_name,
                description=f"Fetching {self.device.metadata.device_type_long} Organizations"
            )
        try:
            orgs = self.device.handle.query_classid("OrgOrg")
            org_tree = {
                "orgs": {
                    "root": {
                        "description": ""
                    }
                }
            }

            for org in orgs:
                dn = org.dn
                if dn == "org-root":
                    org_tree["orgs"]["root"]["description"] = getattr(org, "descr", "")
                    continue

                parts = dn.split("/")[1:]
                current = org_tree["orgs"]["root"]
                for i, part in enumerate(parts):
                    org_key = part.replace("org-", "")
                    if "orgs" not in current:
                        current["orgs"] = {}
                    if org_key not in current["orgs"]:
                        current["orgs"][org_key] = {
                            "description": getattr(org, "descr", "") if i == len(parts) - 1 else ""
                        }
                    current = current["orgs"][org_key]

            orgs_info = {
                "timestamp": datetime.datetime.now().isoformat()[:-3] + 'Z',
                "orgs": org_tree["orgs"]
            }

            self.orgs = orgs_info

            if self.device.task is not None and task_step_name in self.device.task.taskstep_manager.taskstep_list:
                self.device.task.taskstep_manager.stop_taskstep(
                    name=task_step_name,
                    status="successful",
                    status_message=f"Successfully fetched {self.device.metadata.device_type_long} Organizations"
                )

            return orgs_info

        except Exception as err:
            message_str = f"Failed to fetch {self.device.metadata.device_type_long} Organizations: {err}"
            self.logger(level="error", message=message_str)
            if self.device.task is not None and task_step_name in self.device.task.taskstep_manager.taskstep_list:
                self.device.task.taskstep_manager.stop_taskstep(
                    name=task_step_name,
                    status="failed",
                    status_message=message_str[:255]
                )
            return None

    def fetch_server_details(self):
        """
        Fetches server details from the connected device and updates the `server_details` attribute.

        This method verifies the device connection, queries for both blade and rack servers, and extracts
        relevant details like serial number, model, profile name, organization, operational state, and power status.
        The collected data is then saved to the `server_details` attribute and also stored in the cache.

        Returns: A List containing server details, None otherwise
        """
        if self.device.task is not None:
            self.device.task.taskstep_manager.start_taskstep(name="FetchServerDetails",
                                                             description=f"Fetching connected device servers details")

        # Ensure the device is connected. Attempt reconnection if not connected.
        if not self.device.is_connected():
            self.device.connect()

        try:
            # Query the device for blade servers and rack servers
            blade_servers = self.device.handle.query_classid(class_id="ComputeBlade")
            rack_servers = self.device.handle.query_classid(class_id="ComputeRackUnit")

            # Combine the results from blade and rack servers
            all_servers = blade_servers + rack_servers

            servers_list = []

            for server in all_servers:
                server_info = {
                    "serial": server.serial,
                    "model": server.model,
                    "dn": server.assigned_to_dn,
                    "oper_state": server.oper_state,
                    "oper_power": server.oper_power
                }
                servers_list.append(server_info)

            if self.device.task is not None:
                self.device.task.taskstep_manager.stop_taskstep(
                    name="FetchServerDetails",
                    status="successful",
                    status_message="Server details fetched successfully"
                )

        except Exception as e:
            message = f"Error while fetching servers info: {str(e)}"
            self.logger(level="error", message=message)
            self.device.task.taskstep_manager.stop_taskstep(
                name="FetchServerDetails",
                status="failed",
                status_message=message[:255]
            )
            return None

        servers_info = {
            "timestamp": datetime.datetime.now().isoformat()[:-3] + 'Z',
            "servers": servers_list
        }

        self.server_details = servers_info
        return servers_info

    def get_orgs(self):
        """
        Returns the cached orgs dictionary.
        """
        return self.orgs

    def get_server_details(self):
        """
        Function to server details from the device
        :return: A list containing information about the servers.
        """
        return self.server_details


class UcsSystemCache(GenericUcsCache):
    def __init__(self, parent=None):
        GenericUcsCache.__init__(self, parent=parent)


class UcsCentralCache(GenericUcsCache):
    def __init__(self, parent=None):
        GenericUcsCache.__init__(self, parent=parent)
