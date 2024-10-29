from typing import List

from sqlalchemy import CHAR, Enum, ForeignKey, TEXT, Boolean, Integer
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import mapped_column, Mapped, relationship

from db.schema.Base import Base, DifficultDialogue
from db.schema.Entity.DialogueMessage import DialogueMessage


class Dialogue(Base):
    __tablename__ = "dialogue"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(CHAR(32), ForeignKey("user.id", ondelete="CASCADE"))
    messages: Mapped[List["DialogueMessage"]] = relationship("DialogueMessage", backref="dialogue", uselist=True, order_by="asc(DialogueMessage.id)")
    name: Mapped[str] = mapped_column(TEXT)

    last_message: Mapped["DialogueMessage"] = relationship(
        "DialogueMessage",
        order_by=DialogueMessage.timestamp.desc(),
        uselist=False,
        viewonly=True
    )
