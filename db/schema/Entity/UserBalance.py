from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column


class UserBalance:
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("user.id"))
    tokens: Mapped[int] = mapped_column(default=1000)
    voice_seconds: Mapped[int] = mapped_column(default=0)
    photo_count: Mapped[int] = mapped_column(default=0)
