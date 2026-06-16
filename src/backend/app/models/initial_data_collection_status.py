import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class InitialDataCollectionStatus(Base):
    __tablename__ = "initial_data_collection_statuses"
    __table_args__ = (
        CheckConstraint(
            "status IN ('collecting','completed','failed')",
            name="ck_idcs_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # 1テナント1件 (UNIQUE)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, unique=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="collecting")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # 完了時に F-01 アンロック通知送信 (DEC-013)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
