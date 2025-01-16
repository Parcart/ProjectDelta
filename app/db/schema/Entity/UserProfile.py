from datetime import datetime

from sqlalchemy import CHAR, ForeignKey, TEXT, Enum, DECIMAL, TIMESTAMP
from sqlalchemy.orm import mapped_column, Mapped, relationship

from app.db.schema.Base import Base, LanguageLevel


class UserProfile(Base):
    __tablename__ = "user_profile"
    user_id: Mapped[str] = mapped_column(CHAR(32), ForeignKey("user.id", ondelete="CASCADE"), primary_key=True)
    name: Mapped[str] = mapped_column(TEXT, nullable=True)
