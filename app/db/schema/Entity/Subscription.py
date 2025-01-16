from datetime import datetime

from sqlalchemy import Column, String, ForeignKey, Enum, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column

from app.db.schema.Base import SubscriptionType, Base


class Subscription(Base):
    __tablename__ = "subscriptions"
    user_id: Mapped[str] = mapped_column(ForeignKey("user.id"), primary_key=True)
    subscription_type: Mapped[SubscriptionType] = mapped_column(Enum(SubscriptionType), default=SubscriptionType.FREE)
    subscription_starts: Mapped[datetime] = mapped_column(TIMESTAMP)
    subscription_expires: Mapped[datetime] = mapped_column(TIMESTAMP)