from sqlalchemy import CHAR, INT, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.schema import Base


class Referral(Base):
    __tablename__ = 'referrals'
    id: Mapped[int] = mapped_column(INT, primary_key=True)
    referral_id: Mapped[str] = mapped_column(CHAR(32), ForeignKey('user.id'))
    referrer_id: Mapped[str] = mapped_column(CHAR(32), ForeignKey('user.id'))
    referral_code: Mapped[str] = mapped_column(CHAR(12), ForeignKey('referral_code.code'))
    referrer = relationship("User", foreign_keys=referrer_id, backref="referrals")
    referral = relationship("User", foreign_keys=referral_id, backref="referrer")
