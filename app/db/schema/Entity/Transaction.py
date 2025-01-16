from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import TEXT, Integer, ForeignKey, TIMESTAMP, func, Enum
from datetime import datetime
from app.db.schema.Base import Base, TransactionType


class Transaction(Base):
    __tablename__ = "transactions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.now(), nullable=False)
    description: Mapped[str] = mapped_column(TEXT, nullable=True)
    transaction_type: Mapped[TransactionType] = mapped_column(Enum(TransactionType), nullable=False)
