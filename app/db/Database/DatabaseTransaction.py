from typing import List, Optional

from sqlalchemy import select, update, desc
from sqlalchemy.dialects.postgresql import insert

from app.db.schema import UserBalance
from app.db.schema.Base import TransactionType
from app.db.schema.Entity.Transaction import Transaction


class DatabaseTransaction:
    def __init__(self, instance):
        self._instance = instance

    def get(self, user_id: str) -> List[Transaction]:
        stmt = select(Transaction).where(Transaction.user_id == user_id).order_by(desc(Transaction.created_at))
        return self._instance.GetAll(stmt)

    def get_admin(self) -> List[Transaction]:
        stmt = select(Transaction)
        return self._instance.GetAll(stmt)

    async def post(self, user_id: str, amount: int, description: str, transaction_type: TransactionType) -> Optional[int]:

        stmt = select(UserBalance).where(UserBalance.user_id == user_id)
        result = await self._instance.GetSingle(stmt)

        if transaction_type == TransactionType.CREDIT:
            if result.voice_seconds < amount:
                raise Exception("Недостаточно средств")

        stmt = insert(Transaction).values(user_id=user_id, amount=amount, description=description, transaction_type=transaction_type)
        result = await self._instance.ExecuteNonQuery(stmt)

        stmt_update_user_balance = update(UserBalance).where(UserBalance.user_id == user_id).values(
            voice_seconds=UserBalance.voice_seconds + amount if transaction_type == TransactionType.DEBIT else UserBalance.voice_seconds - amount
        )

        result = await self._instance.ExecuteNonQuery(stmt_update_user_balance)
        return result
