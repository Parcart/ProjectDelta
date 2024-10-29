from datetime import datetime

from sqlalchemy import TEXT, CHAR, ForeignKey, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column

from db.schema.Base import Base


class UserToken(Base):
    __tablename__ = "user_token"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(CHAR(32), ForeignKey("user.id", ondelete="CASCADE"))
    token: Mapped[str] = mapped_column(TEXT)
    device: Mapped[str] = mapped_column(TEXT)
    last_action: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.now())
