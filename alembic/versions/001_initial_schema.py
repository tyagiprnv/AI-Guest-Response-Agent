"""Initial schema for properties and reservations

Revision ID: 001
Revises:
Create Date: 2026-02-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create properties table
    op.create_table(
        'properties',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('check_in_time', sa.String(length=20), nullable=False),
        sa.Column('check_out_time', sa.String(length=20), nullable=False),
        sa.Column('parking', sa.String(length=20), nullable=False),
        sa.Column('parking_details', sa.String(), nullable=True),
        sa.Column('amenities', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('policies', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('contact_info', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create reservations table
    op.create_table(
        'reservations',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('property_id', sa.String(length=50), nullable=False),
        sa.Column('guest_name', sa.String(length=255), nullable=False),
        sa.Column('guest_email', sa.String(length=255), nullable=False),
        sa.Column('check_in_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('check_out_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('room_type', sa.String(length=50), nullable=False),
        sa.Column('guest_count', sa.Integer(), nullable=False),
        sa.Column('special_requests', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('booking_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create index on property_id for faster lookups
    op.create_index('idx_reservations_property_id', 'reservations', ['property_id'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_reservations_property_id', table_name='reservations')
    op.drop_table('reservations')
    op.drop_table('properties')
