"""add content_text to proposals

Revision ID: 003_content_text
Revises: 002_contact_email
Create Date: 2026-06-16
"""
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "003_content_text"
down_revision: Union[str, None] = "002_contact_email"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("proposals", sa.Column("content_text", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("proposals", "content_text")
