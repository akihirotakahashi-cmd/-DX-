import uuid
from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Tenant(Base):
    __tablename__ = "tenants"
    __table_args__ = (
        CheckConstraint(
            "status IN ('onboarding','active','suspended','cancelled')",
            name="ck_tenants_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    municipality_name: Mapped[str] = mapped_column(String(255), nullable=False)
    tenant_code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="onboarding")
    contract_start: Mapped[date] = mapped_column(Date, nullable=False)
    contract_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    contracts = relationship("Contract", back_populates="tenant")
    users = relationship("User", back_populates="tenant")
    proposals = relationship("Proposal", back_populates="tenant")
    kpi_metrics = relationship("KpiMetric", back_populates="tenant")
