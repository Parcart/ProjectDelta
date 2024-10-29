from enum import Enum as PyEnum

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

convention = {
    'all_column_names': lambda constraint, table: '_'.join([
        column.name for column in constraint.columns.values()
    ]),
    # Именование индексов
    'ix': 'ix__%(table_name)s__%(all_column_names)s',
    # Именование уникальных индексов
    'uq': 'uq__%(table_name)s__%(all_column_names)s',
    # Именование CHECK-constraint-ов
    'ck': 'ck__%(table_name)s__%(constraint_name)s',
    # Именование внешних ключей
    'fk': 'fk__%(table_name)s__%(all_column_names)s__%(referred_table_name)s',
    # Именование первичных ключей
    'pk': 'pk__%(table_name)s'
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=convention)


class MessageContentType(PyEnum):
    TEXT_MESSAGE = "TEXT_MESSAGE"
    VOICE_MESSAGE = "VOICE_MESSAGE"
    DIALOGUE_END = "DIALOGUE_END"


class DifficultDialogue(PyEnum):
    easy = "easy"
    hard = "hard"


class SenderType(PyEnum):
    USER = "USER"
    BOT = "BOT"


class LanguageCode(PyEnum):
    en = "en"
    ru = "ru"


class LanguageLevel(PyEnum):
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"

    def get_index_value(self):
        return list(LanguageLevel).index(self)

    def get_next_value_enum(self):
        finish = False
        for i in LanguageLevel:
            if finish:
                return i
            if i.name == self.name:
                finish = True
        return self


class TokenType(PyEnum):
    ACCESS_TOKEN = "ACCESS_TOKEN"
    EMAIL_CONFIRMATION = "EMAIL_CONFIRMATION"
    PASSWORD_RESET = "PASSWORD_RESET"
    CODE_CONFIRMATION = "CODE_CONFIRMATION"
    REFRESH_TOKEN = "REFRESH_TOKEN"


class AchievementType(PyEnum):
    instant = "instant"
    progressive = "progressive"


class SubscriptionType(PyEnum):
    FREE = "FREE",
    TRAFFIC = "TRAFFIC"
    STANDARD = "STANDARD"
    EXTENDED = "EXTENDED"
    UNLIMITED = "UNLIMITED"

