"""Support for VDL Parkings zones."""

import logging

from homeassistant.components.zone import ZoneStorageCollection
from homeassistant.helpers.collection import ItemNotFound

from .const import CONF_PARKINGS, CONF_ZONES_MAPPING


_LOGGER = logging.getLogger(__name__)


async def create_parking_zones(hass, coordinator, entry):
    """Create zones for selected parkings.
    
    Prevents duplicate zones by tracking them in entry.data, deduplicating by coordinates,
    and deleting zones when parkings are no longer in the config.
    """

    zone_collection: ZoneStorageCollection = hass.data["zone"]
    selected = entry.data[CONF_PARKINGS]
    zones_mapping = entry.data.get(CONF_ZONES_MAPPING, {})
    new_mapping = {}

    # Get all existing zones for coordinate deduplication
    all_zones = zone_collection.async_items()

    for parking_id in selected:
        parking = coordinator.data[parking_id]

        if not parking:
            continue

        latitude = parking["latitude"]
        longitude = parking["longitude"]

        if latitude is None or longitude is None:
            continue

        # Check if we already have a zone for this parking
        zone_id = zones_mapping.get(parking_id)
        zone_exists = False

        if zone_id:
            # Verify the zone still exists in zone collection and coordinates match
            for zone in all_zones:
                if zone["id"] == zone_id:
                    if (zone.get("latitude") == latitude and
                        zone.get("longitude") == longitude):
                        zone_exists = True
                        new_mapping[parking_id] = zone_id
                        _LOGGER.debug(
                            "Zone '%s' already exists for parking '%s' " \
                            "with matching coordinates", zone_id, parking_id
                        )
                    else:
                        # Coordinates changed, delete old zone
                        await zone_collection.async_delete_item(zone_id)
                        _LOGGER.info(
                            "Coordinates changed for parking '%s', " \
                            "deleted old zone '%s'", parking_id, zone_id
                        )
                    break

        # If zone doesn't exist, check for duplicate by coordinates
        if not zone_exists:
            zone_id = None
            for zone in all_zones:
                if (zone.get("latitude") == latitude and
                    zone.get("longitude") == longitude and
                    zone.get("icon") == "mdi:parking" and
                    "Parking" in zone.get("name", "")):
                    # Found existing zone with same coordinates
                    zone_id = zone["id"]
                    _LOGGER.debug(
                        "Found existing zone '%s' with matching coordinates for parking '%s', " \
                        "reusing it", zone_id, parking_id
                    )
                    break

            # Create new zone only if one doesn't exist with same coordinates
            if not zone_id:
                zone = await zone_collection.async_create_item({
                    "name": f"Parking {parking['name']}",
                    "latitude": latitude,
                    "longitude": longitude,
                    "radius": 100,
                    "icon": "mdi:parking",
                })
                zone_id = zone["id"]
                _LOGGER.info(
                    "Created new zone '%s' for parking '%s' and for entry %s",
                    zone_id, parking_id, entry.entry_id
                )

            new_mapping[parking_id] = zone_id

    # Delete zones for parkings no longer in the config
    for parking_id, zone_id in zones_mapping.items():
        if parking_id not in selected:
            await zone_collection.async_delete_item(zone_id)
            _LOGGER.info("Deleted zone '%s' for parking '%s'", zone_id, parking_id)

    # Persist the updated mapping to entry.data
    if new_mapping != zones_mapping:
        hass.config_entries.async_update_entry(
            entry, data={**entry.data, CONF_ZONES_MAPPING: new_mapping}
        )

    _LOGGER.debug(
        "Updated %d zones mapping for entry %s: %s",
        len(new_mapping), entry.entry_id, new_mapping
    )


async def remove_parking_zones(hass, entry):
    """Remove zones for the entry when it is unloaded."""

    zone_collection: ZoneStorageCollection = hass.data["zone"]

    # Load zone mapping from entry.data
    zones_mapping = entry.data.get(CONF_ZONES_MAPPING, {})

    # Delete all tracked zones
    for zone_id in zones_mapping.values():
        try:
            await zone_collection.async_delete_item(zone_id)
            _LOGGER.info("Deleted zone '%s' from entry %s", zone_id, entry.entry_id)
        except ItemNotFound:
            pass

    _LOGGER.debug(
        "Removed %d zones from entry %s: %s",
        len(zones_mapping), entry.entry_id, list(zones_mapping.values())
    )
