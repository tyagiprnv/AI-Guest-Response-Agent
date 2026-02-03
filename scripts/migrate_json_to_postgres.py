"""
Migrate data from JSON files to PostgreSQL database.
"""
import asyncio
import json
from datetime import datetime
from pathlib import Path

from sqlalchemy import select

from src.config.settings import get_settings
from src.database.connection import AsyncSessionLocal
from src.database.models import Property, Reservation


async def migrate_properties():
    """Migrate properties from JSON to PostgreSQL."""
    base_dir = Path(__file__).parent.parent
    properties_file = base_dir / "data" / "properties" / "properties.json"

    if not properties_file.exists():
        print(f"Properties file not found: {properties_file}")
        return

    # Load JSON data
    with open(properties_file, "r") as f:
        properties_data = json.load(f)

    print(f"Found {len(properties_data)} properties in JSON file")

    # Insert into database
    async with AsyncSessionLocal() as session:
        # Check existing properties
        result = await session.execute(select(Property))
        existing_count = len(result.scalars().all())

        if existing_count > 0:
            print(f"Database already has {existing_count} properties. Skipping migration.")
            return

        # Insert properties
        for prop_data in properties_data:
            property_obj = Property(**prop_data)
            session.add(property_obj)

        await session.commit()
        print(f"Migrated {len(properties_data)} properties to PostgreSQL")


async def migrate_reservations():
    """Migrate reservations from JSON to PostgreSQL."""
    base_dir = Path(__file__).parent.parent
    reservations_file = base_dir / "data" / "reservations" / "reservations.json"

    if not reservations_file.exists():
        print(f"Reservations file not found: {reservations_file}")
        return

    # Load JSON data
    with open(reservations_file, "r") as f:
        reservations_data = json.load(f)

    print(f"Found {len(reservations_data)} reservations in JSON file")

    # Insert into database
    async with AsyncSessionLocal() as session:
        # Check existing reservations
        result = await session.execute(select(Reservation))
        existing_count = len(result.scalars().all())

        if existing_count > 0:
            print(f"Database already has {existing_count} reservations. Skipping migration.")
            return

        # Insert reservations
        for res_data in reservations_data:
            # Convert date strings to datetime objects
            res_data["check_in_date"] = datetime.fromisoformat(res_data["check_in_date"])
            res_data["check_out_date"] = datetime.fromisoformat(res_data["check_out_date"])
            res_data["booking_date"] = datetime.fromisoformat(res_data["booking_date"])

            reservation_obj = Reservation(**res_data)
            session.add(reservation_obj)

        await session.commit()
        print(f"Migrated {len(reservations_data)} reservations to PostgreSQL")


async def verify_migration():
    """Verify migration success."""
    async with AsyncSessionLocal() as session:
        # Count properties
        result = await session.execute(select(Property))
        properties_count = len(result.scalars().all())

        # Count reservations
        result = await session.execute(select(Reservation))
        reservations_count = len(result.scalars().all())

        print("\n=== Migration Verification ===")
        print(f"Properties in database: {properties_count}")
        print(f"Reservations in database: {reservations_count}")

        # Sample a property
        result = await session.execute(select(Property).limit(1))
        sample_property = result.scalar_one_or_none()
        if sample_property:
            print(f"\nSample property: {sample_property.name} ({sample_property.id})")

        # Sample a reservation
        result = await session.execute(select(Reservation).limit(1))
        sample_reservation = result.scalar_one_or_none()
        if sample_reservation:
            print(
                f"Sample reservation: {sample_reservation.guest_name} "
                f"({sample_reservation.id})"
            )


async def main():
    """Run migration."""
    settings = get_settings()
    print(f"Database URL: {settings.database_url}")
    print("Starting migration...\n")

    try:
        await migrate_properties()
        await migrate_reservations()
        await verify_migration()
        print("\n✅ Migration completed successfully!")
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
