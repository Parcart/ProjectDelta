from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, Enum, INT, TEXT, Boolean, func, CHAR
from sqlalchemy.dialects.mysql import TIMESTAMP
from sqlalchemy.orm import mapped_column, Mapped, relationship

from app.db.schema.Base import Base, SenderType, MessageContentType


class DialogueMessage(Base):
    __tablename__ = "dialogue_message"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    dialogue_id: Mapped[str] = mapped_column(CHAR(32), ForeignKey("dialogue.id", ondelete="CASCADE"))
    content_type: Mapped[MessageContentType] = mapped_column(Enum(MessageContentType))
    sender: Mapped[SenderType] = mapped_column(Enum(SenderType))
    voice_info_id: Mapped[int] = mapped_column(INT, ForeignKey("dialogue_voice_info.id", ondelete="CASCADE"), nullable=True)
    voice_info: Mapped["VoiceInfo"] = relationship("VoiceInfo", backref="dialog_message", lazy="joined", uselist=False)
    text: Mapped[Optional[str]] = mapped_column(TEXT, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.now())
