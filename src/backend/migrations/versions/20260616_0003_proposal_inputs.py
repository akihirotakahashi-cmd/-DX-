"""add proposal input fields and refine_instruction

Revision ID: 004_proposal_inputs
Revises: 003_content_text
Create Date: 2026-06-16
"""
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "004_proposal_inputs"
down_revision: Union[str, None] = "003_content_text"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("proposals", sa.Column("future_vision", sa.Text(), nullable=True))
    op.add_column("proposals", sa.Column("current_state", sa.Text(), nullable=True))
    op.add_column("proposals", sa.Column("challenges", sa.Text(), nullable=True))
    op.add_column("proposals", sa.Column("root_causes", sa.Text(), nullable=True))
    op.add_column("proposals", sa.Column("reference_urls", sa.Text(), nullable=True))
    op.add_column("proposals", sa.Column("attachment_names", sa.Text(), nullable=True))
    op.add_column("proposals", sa.Column("refine_instruction", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("proposals", "refine_instruction")
    op.drop_column("proposals", "attachment_names")
    op.drop_column("proposals", "reference_urls")
    op.drop_column("proposals", "root_causes")
    op.drop_column("proposals", "challenges")
    op.drop_column("proposals", "current_state")
    op.drop_column("proposals", "future_vision")
