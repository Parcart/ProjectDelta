from datetime import datetime

from pydantic import BaseModel

from app.db.schema.Base import TransactionType


class CreateTransactionRequest(BaseModel):
    amount: int
    description: str


class TransactionResponse(BaseModel):
    id: int
    user_id: str
    amount: int
    description: str
    created_at: datetime
    transaction_type: TransactionType


class TransactionsResponse(BaseModel):
    transactions: list[TransactionResponse]
