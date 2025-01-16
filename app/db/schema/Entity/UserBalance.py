from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.db.schema.Base import Base


class UserBalance(Base):
    __tablename__ = 'user_balance'
    user_id: Mapped[str] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), primary_key=True)
    voice_seconds: Mapped[int] = mapped_column(default=0)

