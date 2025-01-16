from datetime import datetime

from sqlalchemy import TIMESTAMP, ForeignKey, CHAR, Enum, String, func
from sqlalchemy.orm import mapped_column, Mapped

from app.db.schema import Base
from app.db.schema.Base import TokenType


class ConfirmationToken(Base):
    __tablename__ = 'confirmation_tokens'
    user_id: Mapped[str] = mapped_column(CHAR(32), ForeignKey('user.id', ondelete='CASCADE'), primary_key=True)
    code: Mapped[str] = mapped_column(String(256))
    type_code: Mapped[TokenType] = mapped_column(Enum(TokenType))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.now())
    expires_at: Mapped[datetime] = mapped_column(TIMESTAMP)
