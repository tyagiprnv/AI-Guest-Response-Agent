"""
PostgreSQL-backed repository implementations.
"""
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_session_context
from src.database.models import Property, Reservation


class PostgresPropertyRepository:
    """PostgreSQL-backed property repository."""

    async def get(self, property_id: str) -> dict[str, Any] | None:
        """Get property by ID."""
        async with get_session_context() as session:
            result = await session.execute(select(Property).where(Property.id == property_id))
            property_obj = result.scalar_one_or_none()
            return property_obj.to_dict() if property_obj else None

    async def get_all(self) -> list[dict[str, Any]]:
        """Get all properties."""
        async with get_session_context() as session:
            result = await session.execute(select(Property))
            properties = result.scalars().all()
            return [prop.to_dict() for prop in properties]

    async def create(self, property_data: dict[str, Any]) -> dict[str, Any]:
        """Create a new property."""
        async with get_session_context() as session:
            property_obj = Property(**property_data)
            session.add(property_obj)
            await session.flush()
            return property_obj.to_dict()

    async def update(self, property_id: str, property_data: dict[str, Any]) -> dict[str, Any] | None:
        """Update a property."""
        async with get_session_context() as session:
            result = await session.execute(select(Property).where(Property.id == property_id))
            property_obj = result.scalar_one_or_none()
            if not property_obj:
                return None

            for key, value in property_data.items():
                if hasattr(property_obj, key):
                    setattr(property_obj, key, value)

            await session.flush()
            return property_obj.to_dict()

    async def delete(self, property_id: str) -> bool:
        """Delete a property."""
        async with get_session_context() as session:
            result = await session.execute(select(Property).where(Property.id == property_id))
            property_obj = result.scalar_one_or_none()
            if not property_obj:
                return False

            await session.delete(property_obj)
            return True


class PostgresReservationRepository:
    """PostgreSQL-backed reservation repository."""

    async def get(self, reservation_id: str) -> dict[str, Any] | None:
        """Get reservation by ID."""
        async with get_session_context() as session:
            result = await session.execute(
                select(Reservation).where(Reservation.id == reservation_id)
            )
            reservation_obj = result.scalar_one_or_none()
            return reservation_obj.to_dict() if reservation_obj else None

    async def get_all(self) -> list[dict[str, Any]]:
        """Get all reservations."""
        async with get_session_context() as session:
            result = await session.execute(select(Reservation))
            reservations = result.scalars().all()
            return [res.to_dict() for res in reservations]

    async def get_by_property(self, property_id: str) -> list[dict[str, Any]]:
        """Get all reservations for a property."""
        async with get_session_context() as session:
            result = await session.execute(
                select(Reservation).where(Reservation.property_id == property_id)
            )
            reservations = result.scalars().all()
            return [res.to_dict() for res in reservations]

    async def create(self, reservation_data: dict[str, Any]) -> dict[str, Any]:
        """Create a new reservation."""
        async with get_session_context() as session:
            # Convert date strings to datetime objects if needed
            if isinstance(reservation_data.get("check_in_date"), str):
                reservation_data["check_in_date"] = datetime.fromisoformat(
                    reservation_data["check_in_date"]
                )
            if isinstance(reservation_data.get("check_out_date"), str):
                reservation_data["check_out_date"] = datetime.fromisoformat(
                    reservation_data["check_out_date"]
                )
            if isinstance(reservation_data.get("booking_date"), str):
                reservation_data["booking_date"] = datetime.fromisoformat(
                    reservation_data["booking_date"]
                )

            reservation_obj = Reservation(**reservation_data)
            session.add(reservation_obj)
            await session.flush()
            return reservation_obj.to_dict()

    async def update(
        self, reservation_id: str, reservation_data: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Update a reservation."""
        async with get_session_context() as session:
            result = await session.execute(
                select(Reservation).where(Reservation.id == reservation_id)
            )
            reservation_obj = result.scalar_one_or_none()
            if not reservation_obj:
                return None

            # Convert date strings to datetime objects if needed
            for date_field in ["check_in_date", "check_out_date", "booking_date"]:
                if date_field in reservation_data and isinstance(
                    reservation_data[date_field], str
                ):
                    reservation_data[date_field] = datetime.fromisoformat(
                        reservation_data[date_field]
                    )

            for key, value in reservation_data.items():
                if hasattr(reservation_obj, key):
                    setattr(reservation_obj, key, value)

            await session.flush()
            return reservation_obj.to_dict()

    async def delete(self, reservation_id: str) -> bool:
        """Delete a reservation."""
        async with get_session_context() as session:
            result = await session.execute(
                select(Reservation).where(Reservation.id == reservation_id)
            )
            reservation_obj = result.scalar_one_or_none()
            if not reservation_obj:
                return False

            await session.delete(reservation_obj)
            return True
