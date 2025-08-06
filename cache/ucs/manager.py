from cache.manager import GenericCacheManager
from cache.ucs.cache import UcsCentralCache, UcsSystemCache


class GenericUcsCacheManager(GenericCacheManager):
    def __init__(self, parent=None):
        GenericCacheManager.__init__(self, parent=parent)

    def fetch_cache(self):
        """
        Fetches server details, organizations, and OS firmware data for UCS devices and stores them in cache.
        Returns:
            UcsSystemCache: The updated cache object containing the fetched cache, or None if fetching failed.
        """
        self.logger(level="info", message="Fetching cache from device")

        # Fetch server details from the connected UCS device
        server_details_status = self.cache.fetch_server_details()
        if server_details_status:
            self.logger(level="debug", message="Successfully updated " + self.parent.metadata.device_type_long +
                                               " cache with server details")

        # Fetch orgs from the connected UCS device
        orgs_status = self.cache.fetch_orgs()
        if orgs_status:
            self.logger(level="debug", message="Successfully updated " + self.parent.metadata.device_type_long +
                                               " cache with orgs")

        return self.cache


class UcsSystemCacheManager(GenericUcsCacheManager):
    def __init__(self, parent=None):
        GenericUcsCacheManager.__init__(self, parent=parent)
        self.cache = UcsSystemCache(parent=self)
        self._fill_cache_from_json()


class UcsCentralCacheManager(GenericUcsCacheManager):
    def __init__(self, parent=None):
        GenericUcsCacheManager.__init__(self, parent=parent)
        self.cache = UcsCentralCache(parent=self)
        self._fill_cache_from_json()
