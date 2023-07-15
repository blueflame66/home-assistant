from homeassistant.core import callback
import logging
from .common import MyCoordinator

from homeassistant.components.calendar import (
    ENTITY_ID_FORMAT,
    CalendarEntity,
    CalendarEvent,
)
from homeassistant.helpers.entity import generate_entity_id
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Config entry example."""
    # assuming API object stored here by __init__.py
    my_api = hass.data[DOMAIN][entry.entry_id]
    coordinator = MyCoordinator(hass, my_api)

    # Fetch initial data so we have data when entities subscribe
    #
    # If the refresh fails, async_config_entry_first_refresh will
    # raise ConfigEntryNotReady and setup will try again later
    #
    # If you do not want to retry setup on failure, use
    # coordinator.async_refresh() instead
    #
    await coordinator.async_config_entry_first_refresh()

    async_add_entities(
        MyOwnerRezCal(coordinator, idx) for idx, ent in enumerate(coordinator.data)
    )


class MyOwnerRezCal(CoordinatorEntity, CalendarEntity):
    """An entity using CoordinatorEntity.

    The CoordinatorEntity class provides:
      should_poll
      async_update
      async_added_to_hass
      available

    """

    def __init__(self, coordinator, idx):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator, context=idx)
        self.idx = idx
        caldata = coordinator.data[idx]
        self.entity_id = generate_entity_id(
            ENTITY_ID_FORMAT, DOMAIN + "_" + str(caldata.Id), hass=coordinator.hass
        )
        self._name = caldata.Pname
        self._prop_id = "OR" + str(caldata.Id)
        self._prop_tz = caldata.TimeZone
        self._event = None
        self.cal_events = []

    @property
    def event(self):
        """Return the next upcoming event."""
        return self._event

    @property
    def name(self):
        """Return the name of the entity."""
        return self._name

    @property
    def extra_state_attributes(self):
        """Return the device state attributes."""
        return {"FirstName": "Glenn", "LastName": "Moore"}

    @property
    def state(self):

        return True

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        # self._attr_is_on = self.coordinator.data[self.idx]["state"]

        self._attr_is_on = self.coordinator.data[self.idx].state
        self.async_write_ha_state()

    async def async_get_events(self, hass, start_date, end_date):
        """Get list of upcoming events."""
        _LOGGER.debug("Running OwnerRez async_get_events")
        events = []
        if len(self.coordinator.data[self.idx].calendar) > 0:
            for event in self.coordinator.data[self.idx].calendar:
                _LOGGER.debug(
                    "Checking if event %s has start %s and end %s within in the limit: %s and %s",
                    event["summary"],
                    event["start"],
                    event["end"],
                    start_date,
                    end_date,
                )
                if event["start"] < end_date and event["end"] > start_date:
                    _LOGGER.debug("... and it has")
                    # strongly type class fix
                    events.append(
                        CalendarEvent(event["start"], event["end"], event["summary"])
                    )
                    # events.append(event)
        return events

    async def async_turn_on(self, **kwargs):
        """Turn the light on.

        Example method how to request data updates.
        """
        # Do the turning on.
        # ...

        # Update the data
        await self.coordinator.async_request_refresh()
