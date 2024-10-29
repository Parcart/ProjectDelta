from sqlalchemy import Enum
from sqlalchemy.dialects.mysql import TEXT
from sqlalchemy.orm import Mapped, mapped_column

from db.schema import Base
from db.schema.Base import LanguageCode


class Text(Base):
    __tablename__ = "text"
    id: Mapped[int] = mapped_column(primary_key=True)
    language_code: Mapped[LanguageCode] = mapped_column(Enum(LanguageCode), primary_key=True)
    text: Mapped[str] = mapped_column(TEXT)
    __table_args__ = {
        'mariadb_charset': 'utf8mb4_general_ci'
    }