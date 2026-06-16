import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Text, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ApprovalStep(Base):
    __tablename__ = "approval_steps"
    __table_args__ = (
        CheckConstraint("step_number IN (1, 2)", name="ck_approval_steps_step_number"),
        CheckConstraint(
            "action IN ('submitted','approved','returned','rejected')",
            name="ck_approval_steps_action",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proposal_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("proposals.id"), nullable=False)
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)  # 1=TL / 2=Mgr
    actor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    proposal = relationship("Proposal", back_populates="approval_steps")
    actor = relationship("User", back_populates="approval_steps")
