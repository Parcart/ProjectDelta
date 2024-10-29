from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.mysql import CHAR, TIMESTAMP
from sqlalchemy.orm import mapped_column, relationship, Mapped

from db.schema import Base


class ReferralCode(Base):
    __tablename__ = 'referral_code'
    code: Mapped[str] = mapped_column(CHAR(12), primary_key=True)
    view: Mapped[str] = mapped_column(CHAR(12))
    user_id: Mapped[str] = mapped_column(CHAR(32), ForeignKey('user.id'))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.now())
    user = relationship("User", backref="referral_codes")
