from datetime import datetime

from sqlalchemy import CHAR, ForeignKey, TEXT, Enum, DECIMAL, TIMESTAMP
from sqlalchemy.orm import mapped_column, Mapped, relationship

from db.schema.Base import Base, LanguageLevel


class UserProfile(Base):
    __tablename__ = "user_profile"
    user_id: Mapped[str] = mapped_column(CHAR(32), ForeignKey("user.id", ondelete="CASCADE"), primary_key=True)
    name: Mapped[str] = mapped_column(TEXT, nullable=True)
    target: Mapped[str] = mapped_column(TEXT, nullable=True)
    interests: Mapped[str] = mapped_column(TEXT, nullable=True)
    language_level: Mapped[LanguageLevel] = mapped_column(Enum(LanguageLevel), default=LanguageLevel.A1)
    progress: Mapped[float] = mapped_column(DECIMAL, nullable=False, default=0)
    subscription_until: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=True)

    referral_code = relationship(
        "ReferralCode",
        primaryjoin="UserProfile.user_id == foreign(ReferralCode.user_id)",
        uselist=False,
        lazy="joined",
        overlaps="referral_codes,user"
    )
