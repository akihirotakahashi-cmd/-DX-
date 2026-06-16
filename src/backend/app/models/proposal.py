import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Proposal(Base):
    __tablename__ = "proposals"
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft','reviewing_tl','reviewing_mgr','approved','rejected','cancelled','superseded')",
            name="ck_proposals_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    # 自己参照 FK (DEC-015)
    parent_proposal_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("proposals.id"), nullable=True
    )
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    municipality_name: Mapped[str] = mapped_column(String(255), nullable=False)
    theme: Mapped[str] = mapped_column(String(200), nullable=False)
    # 外部ストレージ URL (DEC-018)
    content_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 編集可能な本文テキスト (DB直接保存)
    content_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 入力フィールド（再利用・履歴表示用）
    future_vision: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_state: Mapped[str | None] = mapped_column(Text, nullable=True)
    challenges: Mapped[str | None] = mapped_column(Text, nullable=True)
    root_causes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference_urls: Mapped[str | None] = mapped_column(Text, nullable=True)   # JSON array string
    attachment_names: Mapped[str | None] = mapped_column(Text, nullable=True) # JSON array string
    # 精緻化指示（このバージョンを生成した指示）
    refine_instruction: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    tenant = relationship("Tenant", back_populates="proposals")
    creator = relationship("User", back_populates="proposals")
    parent = relationship("Proposal", remote_side="Proposal.id", backref="revisions")
    approval_steps = relationship("ApprovalStep", back_populates="proposal")
    evidence = relationship("ProposalEvidence", back_populates="proposal")
    portal_urls = relationship("PortalUrl", back_populates="proposal")
