from typing import List

from sqlalchemy import Integer, Enum, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column

from db.schema.Base import AchievementType, Base
from db.schema.Entity.Text import Text


class Achievement(Base):
    __tablename__ = 'achievements'
    id = mapped_column(Integer, primary_key=True)
    name_id: Mapped[int] = mapped_column(Integer, ForeignKey("text.id"))
    description_id: Mapped[int] = mapped_column(Integer, ForeignKey("text.id"))
    type = mapped_column(Enum(AchievementType), nullable=False)
    goal = mapped_column(Integer, nullable=False)

    title: Mapped[List["Text"]] = relationship("Text", foreign_keys=[name_id], uselist=True)
    description: Mapped[List["Text"]] = relationship("Text", foreign_keys=[description_id], uselist=True)

