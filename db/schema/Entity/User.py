from datetime import datetime

from sqlalchemy import CHAR, TEXT, TIMESTAMP, String, func, sql, Boolean, Enum
from sqlalchemy.orm import mapped_column, Mapped

from db.schema.Base import Base, LanguageCode, SubscriptionType


class User(Base):
    __tablename__ = 'user'
    id: Mapped[str] = mapped_column(CHAR(32), primary_key=True)
    email: Mapped[str] = mapped_column(TEXT)
    email_verified = mapped_column(Boolean, default=False, server_default=sql.expression.false(), nullable=False)
    password: Mapped[str] = mapped_column(String(256))
    interface_language: Mapped[LanguageCode] = mapped_column(Enum(LanguageCode), default=LanguageCode.ru)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.now())
    # Общий ключ для сброса всех сессий
    session_key: Mapped[str] = mapped_column(CHAR(32), nullable=True)
    subscription_type: Mapped[SubscriptionType] = mapped_column(Enum(SubscriptionType), default=SubscriptionType.FREE)
    disabled: Mapped[bool] = mapped_column(
        default=False, server_default=sql.expression.false())



