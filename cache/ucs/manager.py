from cache.manager import GenericCacheManager
from cache.ucs.cache import UcsSystemCache


class UcsSystemCacheManager(GenericCacheManager):
    def __init__(self, parent=None):
        GenericCacheManager.__init__(self, parent=parent)
        self.cache = UcsSystemCache(parent=self)
        self._fill_cache_from_json()

    def fetch_cache(self):
        """
        Fetches server details, organizations, and OS firmware data for UCS devices and stores them in cache.
        Returns:
            UcsSystemCache: The updated cache object containing the fetched cache, or None if fetching failed.
        """
        self.logger(level="info", message="Fetching cache from device")

        # Fetch server details from the connected UCS device
        server_details_status = self.cache.fetch_server_details()

        # If fetching server details fails, return None.
        if server_details_status:
            self.logger(level="debug", message="Successfully updated cache with server details")

        # TODO: Fetch additional data such as Organizations and OS Firmware Data in future steps.

        return self.cache
