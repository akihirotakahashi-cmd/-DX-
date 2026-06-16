import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, Numeric, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class KpiDataPoint(Base):
    __tablename__ = "kpi_data_points"
    __table_args__ = (
        CheckConstraint("target_quarter BETWEEN 1 AND 4", name="ck_kpi_dp_quarter"),
        # 部分 UNIQUE インデックスは Alembic マイグレーションで定義 (DEC-017)
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kpi_metric_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("kpi_metrics.id"), nullable=False)
    upload_record_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("csv_upload_records.id"), nullable=False
    )
    target_year: Mapped[int] = mapped_column(Integer, nullable=False)
    target_quarter: Mapped[int] = mapped_column(Integer, nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)  # DEC-017
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    metric = relationship("KpiMetric", back_populates="data_points")
    upload_record = relationship("CsvUploadRecord", back_populates="data_points")
