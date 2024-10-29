from sqlalchemy import Integer, ForeignKey, Boolean, TIMESTAMP, CHAR
from sqlalchemy import func
from sqlalchemy.orm import relationship, mapped_column, Mapped

from db.schema import Base


class UserAchievement(Base):
    __tablename__ = 'user_achievements'
    achievement_id = mapped_column(Integer, ForeignKey('achievements.id'), primary_key=True)
    user_id: Mapped[int] = mapped_column(CHAR(32), ForeignKey("user.id", ondelete="CASCADE"), primary_key=True)
    progress = mapped_column(Integer, default=0)
    is_completed = mapped_column(Boolean, default=False)
    timestamp = mapped_column(TIMESTAMP, default=func.now())

    achievement = relationship("Achievement", backref="user_achievements")
