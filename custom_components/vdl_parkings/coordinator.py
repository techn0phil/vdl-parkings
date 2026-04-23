"""Data coordinator for VDL Parkings integration."""

from datetime import timedelta
import logging

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import VdlParkingApi
from .const import DOMAIN


_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = 60


class VdlParkingCoordinator(DataUpdateCoordinator):
    """Coordinator to manage fetching VDL Parkings data."""

    def __init__(self, hass):
        self.api = VdlParkingApi()

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL),
        )

    async def _async_update_data(self):
        try:
            data = await self.api.fetch()
        except ValueError as err:
            # Transient error: log it but allow coordinator to keep last-known-good data
            _LOGGER.warning("Ignoring failed API call: %s", err)
            raise

        parkings = {}

        for parking in data["parking"]:
            parking_id = str(parking["id"])
            total_capacity = parking["total"]
            available_spaces = parking["actuel"]
            occupied_spaces = max(total_capacity - available_spaces, 0)

            parkings[parking_id] = {
                "id": parking_id,
                "name": parking["title"],
                "open": bool(parking["ouvert"]),
                "full": bool(parking["complet"]),
                "out_of_service": bool(parking["panne"]),
                "total_capacity": total_capacity,
                "available_spaces": available_spaces,
                "occupied_spaces": occupied_spaces,
                "occupancy_rate": (
                    round(occupied_spaces / total_capacity * 100)
                    if total_capacity > 0
                    else 0
                ),
                "latitude": parking["coords"]["latitude"],
                "longitude": parking["coords"]["longitude"],
            }

        return parkings
