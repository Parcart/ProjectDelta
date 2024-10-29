from datetime import datetime

from sqlalchemy import CHAR, TIMESTAMP, func, UniqueConstraint, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column

from db.schema.Base import Base


class UserSession(Base):
    __tablename__ = "user_session"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_key: Mapped[str] = mapped_column(CHAR(32), index=True)
    user_agent: Mapped[str] = mapped_column(VARCHAR(255))
    create_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.now())

    __table_args__ = (
        UniqueConstraint("session_key", "user_agent", name="unique_session_user_agent"),
    )
