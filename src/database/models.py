"""
SQLAlchemy ORM models for properties and reservations.
"""
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.connection import Base


class Property(Base):
    """Property model."""

    __tablename__ = "properties"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    check_in_time: Mapped[str] = mapped_column(String(20), nullable=False)
    check_out_time: Mapped[str] = mapped_column(String(20), nullable=False)
    parking: Mapped[str] = mapped_column(String(20), nullable=False)
    parking_details: Mapped[str | None] = mapped_column(String, nullable=True)
    amenities: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    policies: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    contact_info: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationship
    reservations: Mapped[list["Reservation"]] = relationship(
        "Reservation", back_populates="property", cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "check_in_time": self.check_in_time,
            "check_out_time": self.check_out_time,
            "parking": self.parking,
            "parking_details": self.parking_details,
            "amenities": self.amenities,
            "policies": self.policies,
            "contact_info": self.contact_info,
        }


class Reservation(Base):
    """Reservation model."""

    __tablename__ = "reservations"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    property_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("properties.id", ondelete="CASCADE"), nullable=False
    )
    guest_name: Mapped[str] = mapped_column(String(255), nullable=False)
    guest_email: Mapped[str] = mapped_column(String(255), nullable=False)
    check_in_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    check_out_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    room_type: Mapped[str] = mapped_column(String(50), nullable=False)
    guest_count: Mapped[int] = mapped_column(Integer, nullable=False)
    special_requests: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    booking_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationship
    property: Mapped["Property"] = relationship("Property", back_populates="reservations")

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "property_id": self.property_id,
            "guest_name": self.guest_name,
            "guest_email": self.guest_email,
            "check_in_date": self.check_in_date.isoformat(),
            "check_out_date": self.check_out_date.isoformat(),
            "room_type": self.room_type,
            "guest_count": self.guest_count,
            "special_requests": self.special_requests,
            "booking_date": self.booking_date.isoformat(),
        }
