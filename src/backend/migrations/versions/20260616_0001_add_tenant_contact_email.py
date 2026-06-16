"""add contact_email to tenants

Revision ID: 002_contact_email
Revises: 001_initial
Create Date: 2026-06-16
"""
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "002_contact_email"
down_revision: Union[str, None] = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("contact_email", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("tenants", "contact_email")
