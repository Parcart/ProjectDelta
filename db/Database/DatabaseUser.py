import uuid
from typing import Any, Coroutine, Optional

from sqlalchemy import CursorResult, select, delete, update

from db.schema import User, UserProfile, Referral
from db.schema.Entity import ConfirmationToken, ReferralCode


class DatabaseUser:
    def __init__(self, instance):
        self._instance = instance

    def get(self, email: str = None, user_id: str = None) -> Coroutine[Any, Optional[User], Any]:
        if email:
            stmt = select(User).where(User.email == email)
        elif user_id:
            stmt = select(User).where(User.id == user_id)
        else:
            return None
        return self._instance.GetSingle(stmt)

    async def post(self, email, password,
                   interface_language, referral_code: None | ReferralCode, session_key: str) -> str:
        user_id = uuid.uuid4().hex
        stmts = [User(id=user_id, email=email, password=password,
                      interface_language=interface_language, session_key=session_key),
                 UserProfile(user_id=user_id)]
        if referral_code:
            stmts.append(Referral(referral_id=user_id, referrer_id=referral_code.user_id,
                                  referral_code=referral_code.code))
        if await self._instance.ExecuteListNonQueryIgnoreObj(stmts):
            return user_id
        else:
            raise Exception("Error creating user")

    def delete(self, user_id: str) -> Coroutine[Any, CursorResult, Any]:
        stmt = delete(User).where(User.id == user_id)
        return self._instance.ExecuteNonQuery(stmt)

    async def update_confirm_email(self, user_id: str) -> Coroutine[Any, CursorResult, Any]:
        stmt_update = update(User).where(User.id == user_id).values(email_verified=True)
        await self._instance.ExecuteNonQuery(stmt_update)

    def update_password(self, user_id: str, password: str) -> Coroutine[Any, CursorResult, Any]:
        stmt = update(User).where(User.id == user_id).values(password=password)
        return self._instance.ExecuteNonQuery(stmt)

    def set_session_key(self, user_id: str, session_key: str) -> Coroutine[Any, CursorResult, Any]:
        stmt = update(User).where(User.id == user_id).values(session_key=session_key)
        return self._instance.ExecuteNonQuery(stmt)
