
from cache.cache import GenericCache
import datetime


class UcsSystemCache(GenericCache):
    def __init__(self, parent=None):
        GenericCache.__init__(self, parent=parent)

        self.server_details = []

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

    def get_server_details(self):
        """
        Function to server details from the device
        :return: A list containing information about the servers.
        """

        return self.server_details
