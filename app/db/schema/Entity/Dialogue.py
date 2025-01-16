from typing import List

from sqlalchemy import CHAR, ForeignKey, TEXT, UniqueConstraint
from sqlalchemy.orm import mapped_column, Mapped, relationship

from app.db.schema.Base import Base
from app.db.schema.Entity.DialogueMessage import DialogueMessage


class Dialogue(Base):
    __tablename__ = "dialogue"
    id: Mapped[str] = mapped_column(CHAR(32), primary_key=True)
    user_id: Mapped[str] = mapped_column(CHAR(32), ForeignKey("user.id", ondelete="CASCADE"))
    messages: Mapped[List["DialogueMessage"]] = relationship("DialogueMessage", backref="dialogue", uselist=True, order_by="asc(DialogueMessage.id)")
    name: Mapped[str] = mapped_column(TEXT)

    # last_message: Mapped["DialogueMessage"] = relationship(
    #     "DialogueMessage",
    #     order_by=DialogueMessage.timestamp.desc(),
    #     uselist=False,
    #     viewonly=True
    # )

    UniqueConstraint(
        'id', 'user_id', name='uq__dialogue_user'
    )
