from typing import List

from sqlalchemy import select, desc

from app.db.schema.Entity.User import User
from app.db.schema.Entity.Transaction import Transaction


class DatabaseAdmin:
    voice_path = None

    def __init__(self, instance):
        self._instance = instance

    async def get_all_users(self):
        stmt = select(User)
        return await self._instance.GetAll(stmt)

    async def get_transactions(self) -> List[Transaction]:
        stmt = select(Transaction).order_by(desc(Transaction.created_at))
        return await self._instance.GetAll(stmt)

