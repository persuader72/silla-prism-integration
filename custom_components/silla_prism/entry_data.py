"""Runtime entry data for Silla Prism stored in hass.data."""

from dataclasses import dataclass


@dataclass(slots=True)
class RuntimeEntryData:
    """Store runtime data for esphome config entries."""

    topic: str
    vsensors: bool
