"""Support for Prism wallbox domain data."""

from dataclasses import dataclass, field
from typing import Self, cast

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .entry_data import RuntimeEntryData


@dataclass(slots=True)
class DomainData:
    """Define a class that stores global prism wallbox data in hass.data[DOMAIN]."""

    _entry_datas: dict[str, RuntimeEntryData] = field(default_factory=dict)

    def get_entry_data(self, entry: ConfigEntry) -> RuntimeEntryData:
        """Return the runtime entry data associated with this config entry."""
        return self._entry_datas[entry.entry_id]

    def set_entry_data(self, entry: ConfigEntry, entry_data: RuntimeEntryData) -> None:
        """Set the runtime entry data associated with this config entry."""
        assert entry.entry_id not in self._entry_datas, "Entry data already set!"
        self._entry_datas[entry.entry_id] = entry_data

    @classmethod
    def get(cls, hass: HomeAssistant) -> Self:
        """Get the global DomainData instance stored in hass.data."""
        # Don't use setdefault - this is a hot code path
        if DOMAIN in hass.data:
            return cast(Self, hass.data[DOMAIN])
        ret = hass.data[DOMAIN] = cls()
        return ret
