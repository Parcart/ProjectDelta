from datetime import datetime, timedelta
from typing import Any, Coroutine, Optional

import sqlalchemy
from sqlalchemy import CursorResult, func, select, delete, text
from sqlalchemy.dialects.postgresql import insert

from app.db.schema import ConfirmationToken
from app.db.schema.Base import TokenType


class DatabaseConfirm:
    voice_path = None

    def __init__(self, instance):
        self._instance = instance

    async def post(self, user_id: str, code: int, type_code: TokenType) -> Coroutine[Any,CursorResult,Any]:
        try:
            stmt = insert(ConfirmationToken).values(
                user_id=user_id,
                code=code,
                type_code=type_code.value,
                expires_at=datetime.now() + timedelta(minutes=5)
            )
            return await self._instance.ExecuteNonQuery(stmt)
        except sqlalchemy.exc.IntegrityError as e:
            stmt = delete(ConfirmationToken).where(ConfirmationToken.user_id == user_id)
            await self._instance.ExecuteNonQuery(stmt)
            return await self.post(user_id, code, type_code)

    def get(self, token_type: TokenType, user_id: str) -> Coroutine[Any,Optional[ConfirmationToken],Any]:
        conditions = [ConfirmationToken.expires_at > func.now(),
                      ConfirmationToken.type_code == token_type,
                      ConfirmationToken.user_id == user_id]
        stmt = select(ConfirmationToken).where(*conditions)
        return self._instance.GetSingle(stmt)



