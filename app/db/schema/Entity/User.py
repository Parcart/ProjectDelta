from datetime import datetime

from sqlalchemy import CHAR, TEXT, TIMESTAMP, String, func, sql, Boolean, Enum, BIGINT
from sqlalchemy.orm import mapped_column, Mapped, relationship

from app.db.schema.Base import Base, LanguageCode, SubscriptionType, Role


class User(Base):
    __tablename__ = 'user'
    id: Mapped[str] = mapped_column(CHAR(32), primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BIGINT, nullable=True)
    email: Mapped[str] = mapped_column(TEXT)
    email_verified = mapped_column(Boolean, default=False, server_default=sql.expression.false(), nullable=False)
    password: Mapped[str] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.now())
    # Общий ключ для сброса всех сессий
    session_key: Mapped[str] = mapped_column(CHAR(32), nullable=True)
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.USER)
    disabled: Mapped[bool] = mapped_column(
        default=False, server_default=sql.expression.false())

    profile: Mapped['UserProfile'] = relationship("UserProfile", uselist=False, lazy="joined")
    balance: Mapped['UserBalance'] = relationship("UserBalance", uselist=False, lazy="joined")
    transactions: Mapped[list["Transaction"]] = relationship("Transaction", backref="user", uselist=True)
