from cache.manager import GenericCacheManager
from cache.intersight.cache import IntersightCache


class IntersightCacheManager(GenericCacheManager):
    def __init__(self, parent=None):
        GenericCacheManager.__init__(self, parent=parent)
        self.cache = IntersightCache(parent=self)
        self._fill_cache_from_json()

    def fetch_cache(self):
        """
        Fetches server details, organizations, and OS firmware data for Intersight devices and stores them in cache.
        Returns:
            IntersightCache: The updated cache object containing the fetched cache, or None if fetching failed.
        """
        self.logger(level="info", message="Fetching cache from device")

        # Fetch os_firmware and orgs data from the connected Intersight device
        os_firmware_status = self.cache.fetch_os_firmware_data()
        orgs = self.cache.fetch_orgs()

        if os_firmware_status and orgs:
            self.logger(level="debug", message="Successfully updated cache with os_firmware_data and orgs.")

        # TODO: Fetch additional data such as Server Details in future steps.

        return self.cache
