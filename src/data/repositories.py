"""
Data repositories for properties and reservations.
"""
import json
from functools import lru_cache
from pathlib import Path
from typing import Dict

from src.config.settings import get_settings
from src.data.models import Property, Reservation

BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data"


class PropertyRepository:
    """Repository for property data."""

    def __init__(self):
        self._properties: Dict[str, Property] = {}
        self._load_properties()

    def _load_properties(self):
        """Load properties from JSON file."""
        properties_file = DATA_DIR / "properties" / "properties.json"
        if properties_file.exists():
            with open(properties_file, "r") as f:
                data = json.load(f)
                for prop_data in data:
                    prop = Property(**prop_data)
                    self._properties[prop.id] = prop

    async def get_by_id(self, property_id: str) -> Property | None:
        """Get property by ID."""
        return self._properties.get(property_id)

    def get_all(self) -> list[Property]:
        """Get all properties."""
        return list(self._properties.values())


class ReservationRepository:
    """Repository for reservation data."""

    def __init__(self):
        self._reservations: Dict[str, Reservation] = {}
        self._load_reservations()

    def _load_reservations(self):
        """Load reservations from JSON file."""
        reservations_file = DATA_DIR / "reservations" / "reservations.json"
        if reservations_file.exists():
            with open(reservations_file, "r") as f:
                data = json.load(f)
                for res_data in data:
                    res = Reservation(**res_data)
                    self._reservations[res.id] = res

    async def get_by_id(self, reservation_id: str) -> Reservation | None:
        """Get reservation by ID."""
        return self._reservations.get(reservation_id)

    def get_by_property(self, property_id: str) -> list[Reservation]:
        """Get all reservations for a property."""
        return [
            res for res in self._reservations.values()
            if res.property_id == property_id
        ]

    def get_all(self) -> list[Reservation]:
        """Get all reservations."""
        return list(self._reservations.values())


@lru_cache(maxsize=1)
def get_property_repository():
    """Get cached property repository (JSON or PostgreSQL based on config)."""
    settings = get_settings()
    if settings.data_backend == "postgres":
        from src.database.repositories import PostgresPropertyRepository

        return PostgresPropertyRepository()
    return PropertyRepository()


@lru_cache(maxsize=1)
def get_reservation_repository():
    """Get cached reservation repository (JSON or PostgreSQL based on config)."""
    settings = get_settings()
    if settings.data_backend == "postgres":
        from src.database.repositories import PostgresReservationRepository

        return PostgresReservationRepository()
    return ReservationRepository()
