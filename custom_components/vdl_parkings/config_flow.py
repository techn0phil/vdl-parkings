"""Config flow for VDL Parkings integration."""

import logging

from homeassistant import config_entries
from homeassistant.helpers import config_validation as cv

import voluptuous as vol

from .api import VdlParkingApi
from .const import DOMAIN, CONF_PARKINGS


_LOGGER = logging.getLogger(__name__)


class VdlParkingConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for VDL Parkings."""

    def is_matching(self, _) -> bool:
        """Check if this flow matches another flow."""

        return False  # No unique matching needed for generic multi-parking setup


    async def async_step_user(self, user_input=None):
        api = VdlParkingApi()
        data = await api.fetch()

        parkings = data["parking"]

        # mapping title -> id
        id_map = {
            p["title"]: str(p["id"])
            for p in parkings
        }

        # sorted mapping title -> title
        parking_map = {
            p["title"]: p["title"]
            for p in sorted(parkings, key=lambda p: p["title"].casefold())
        }

        if user_input is not None:
            selected_ids = [id_map[name] for name in user_input[CONF_PARKINGS]]
            _LOGGER.info(
                "Selected %s parkings: %s (ids: %s)",
                len(selected_ids),
                user_input[CONF_PARKINGS],
                selected_ids
            )

            return self.async_create_entry(
                title="Parkings",
                data={CONF_PARKINGS: selected_ids},
            )

        schema = vol.Schema({
            vol.Required(CONF_PARKINGS): cv.multi_select(parking_map)
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
        )
