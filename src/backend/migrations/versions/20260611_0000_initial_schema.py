"""initial schema — all 13 tables

Revision ID: 001_initial
Revises:
Create Date: 2026-06-11
"""
from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # tenants
    # ------------------------------------------------------------------
    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("municipality_name", sa.String(255), nullable=False),
        sa.Column("tenant_code", sa.String(50), nullable=False, unique=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="onboarding"),
        sa.Column("contract_start", sa.Date, nullable=False),
        sa.Column("contract_end", sa.Date, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint(
            "status IN ('onboarding','active','suspended','cancelled')",
            name="ck_tenants_status",
        ),
    )

    # ------------------------------------------------------------------
    # contracts
    # ------------------------------------------------------------------
    op.create_table(
        "contracts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("initial_fee", sa.Numeric(15, 2), nullable=False),
        sa.Column("monthly_fee", sa.Numeric(15, 2), nullable=False),
        sa.Column("contract_start", sa.Date, nullable=False),
        sa.Column("contract_end", sa.Date, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('active','expired','cancelled')", name="ck_contracts_status"),
    )

    # ------------------------------------------------------------------
    # users
    # ------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("role IN ('consultant','tl','manager','system_admin')", name="ck_users_role"),
        sa.CheckConstraint(
            "role != 'consultant' OR tenant_id IS NOT NULL",
            name="consultant_requires_tenant",
        ),
    )

    # ------------------------------------------------------------------
    # proposals
    # ------------------------------------------------------------------
    op.create_table(
        "proposals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("parent_proposal_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("proposals.id"), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("municipality_name", sa.String(255), nullable=False),
        sa.Column("theme", sa.String(200), nullable=False),
        sa.Column("content_url", sa.Text, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint(
            "status IN ('draft','reviewing_tl','reviewing_mgr','approved','rejected','cancelled','superseded')",
            name="ck_proposals_status",
        ),
    )
    op.create_index("ix_proposals_tenant_status", "proposals", ["tenant_id", "status"])

    # ------------------------------------------------------------------
    # approval_steps
    # ------------------------------------------------------------------
    op.create_table(
        "approval_steps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("proposal_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("proposals.id"), nullable=False),
        sa.Column("step_number", sa.Integer, nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("action", sa.String(20), nullable=False),
        sa.Column("comment", sa.Text, nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("step_number IN (1, 2)", name="ck_approval_steps_step_number"),
        sa.CheckConstraint(
            "action IN ('submitted','approved','returned','rejected')",
            name="ck_approval_steps_action",
        ),
    )

    # ------------------------------------------------------------------
    # proposal_evidence
    # ------------------------------------------------------------------
    op.create_table(
        "proposal_evidence",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("proposal_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("proposals.id"), nullable=False),
        sa.Column("source_name", sa.String(255), nullable=False),
        sa.Column("source_url", sa.Text, nullable=True),
        sa.Column("excerpt", sa.Text, nullable=True),
        sa.Column("classification", sa.String(20), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint(
            "classification IN ('fact','inference','analysis')",
            name="ck_proposal_evidence_classification",
        ),
    )

    # ------------------------------------------------------------------
    # portal_urls
    # ------------------------------------------------------------------
    op.create_table(
        "portal_urls",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("proposal_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("proposals.id"), nullable=False),
        sa.Column("token", sa.String(64), nullable=False, unique=True),
        sa.Column("issued_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("downloaded_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ------------------------------------------------------------------
    # kpi_metrics
    # ------------------------------------------------------------------
    op.create_table(
        "kpi_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("unit", sa.String(50), nullable=False),
        sa.Column("alert_threshold_pct", sa.Integer, nullable=True),
        sa.Column("is_required", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ------------------------------------------------------------------
    # csv_upload_records
    # ------------------------------------------------------------------
    op.create_table(
        "csv_upload_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("target_year", sa.Integer, nullable=False),
        sa.Column("target_quarter", sa.Integer, nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("validation_errors", postgresql.JSONB, nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("target_quarter BETWEEN 1 AND 4", name="ck_csv_upload_quarter"),
        sa.CheckConstraint(
            "status IN ('pending','validating','success','failed')",
            name="ck_csv_upload_status",
        ),
    )

    # ------------------------------------------------------------------
    # kpi_data_points
    # ------------------------------------------------------------------
    op.create_table(
        "kpi_data_points",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("kpi_metric_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("kpi_metrics.id"), nullable=False),
        sa.Column(
            "upload_record_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("csv_upload_records.id"),
            nullable=False,
        ),
        sa.Column("target_year", sa.Integer, nullable=False),
        sa.Column("target_quarter", sa.Integer, nullable=False),
        sa.Column("value", sa.Numeric(20, 4), nullable=False),
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("target_quarter BETWEEN 1 AND 4", name="ck_kpi_dp_quarter"),
    )
    # 部分 UNIQUE インデックス (DEC-017): active=true の行のみ重複を禁止
    op.execute(
        """
        CREATE UNIQUE INDEX uq_kpi_dp_active
        ON kpi_data_points (kpi_metric_id, target_year, target_quarter)
        WHERE active = true
        """
    )

    # ------------------------------------------------------------------
    # onboarding_records
    # ------------------------------------------------------------------
    op.create_table(
        "onboarding_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("consultant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ------------------------------------------------------------------
    # initial_data_collection_statuses
    # ------------------------------------------------------------------
    op.create_table(
        "initial_data_collection_statuses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("status", sa.String(20), nullable=False, server_default="collecting"),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('collecting','completed','failed')", name="ck_idcs_status"),
    )

    # ------------------------------------------------------------------
    # notifications (DEC-026)
    # ------------------------------------------------------------------
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("link_url", sa.Text, nullable=True),
        sa.Column("read", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_notifications_user_read", "notifications", ["user_id", "read"])


def downgrade() -> None:
    op.drop_table("notifications")
    op.drop_table("initial_data_collection_statuses")
    op.drop_table("onboarding_records")
    op.execute("DROP INDEX IF EXISTS uq_kpi_dp_active")
    op.drop_table("kpi_data_points")
    op.drop_table("csv_upload_records")
    op.drop_table("kpi_metrics")
    op.drop_table("portal_urls")
    op.drop_table("proposal_evidence")
    op.drop_table("approval_steps")
    op.drop_index("ix_proposals_tenant_status", "proposals")
    op.drop_table("proposals")
    op.drop_table("users")
    op.drop_table("contracts")
    op.drop_table("tenants")
