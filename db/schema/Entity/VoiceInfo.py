from sqlalchemy import FLOAT, TEXT, CHAR
from sqlalchemy.orm import Mapped, mapped_column

from db.schema.Base import Base


class VoiceInfo(Base):
    __tablename__ = "dialogue_voice_info"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    voice_data_id: Mapped[str] = mapped_column(CHAR(32))
    sound_wave: Mapped[str] = mapped_column(TEXT)
    duration: Mapped[float] = mapped_column(FLOAT)
