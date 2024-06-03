"""Manager for Prism wallbox."""

from .domain_data import DomainData
from homeassistant.core import HomeAssistant

from .entry_data import RuntimeEntryData


class PrismManager:
    """Class to manage a Prism mqtt connection."""

    def __init__(
        self, hass: HomeAssistant, domain_data: DomainData, entry_data: RuntimeEntryData
    ) -> None:
        """Initialize the Prism wallbox manager."""

    async def async_start(self) -> None:
        """Start the Prism wallbox connection manager."""
