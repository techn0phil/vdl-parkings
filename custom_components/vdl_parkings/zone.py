"""Support for VDL Parkings zones."""

import logging

from homeassistant.components.zone import ZoneStorageCollection

from .const import CONF_PARKINGS, DOMAIN


_LOGGER = logging.getLogger(__name__)


async def create_parking_zones(hass, coordinator, entry):
    """Create zones for selected parkings."""

    zone_collection: ZoneStorageCollection = hass.data["zone"]
    zones = []

    selected = entry.data[CONF_PARKINGS]

    for parking_id in selected:
        parking = coordinator.data[parking_id]

        if not parking:
            continue

        latitude = parking["latitude"]
        longitude = parking["longitude"]

        if latitude is None or longitude is None:
            continue

        zone = await zone_collection.async_create_item({
            "name": f"Parking {parking['name']}",
            "latitude": latitude,
            "longitude": longitude,
            "radius": 100,
            "icon": "mdi:parking",
        })

        zones.append(zone["id"])

    _LOGGER.debug("Created %d zones for entry %s: %s", len(zones), entry.entry_id, zones)

    hass.data[DOMAIN].setdefault("zones", {})
    hass.data[DOMAIN]["zones"][entry.entry_id] = zones


async def remove_parking_zones(hass, entry):
    """Remove zones for the entry."""

    zone_collection: ZoneStorageCollection = hass.data["zone"]
    zones = hass.data[DOMAIN].get("zones", {}).pop(entry.entry_id, [])

    for entity_id in zones:
        await zone_collection.async_delete_item(entity_id)

    _LOGGER.debug("Removed %d zones for entry %s: %s", len(zones), entry.entry_id, zones)
