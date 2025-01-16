from typing import Any, Coroutine

from sqlalchemy import CursorResult, func
from sqlalchemy.dialects.postgresql import insert

from app.db.schema import UserSession


class DatabaseUserSession:
    def __init__(self, instance):
        self._instance = instance

    def post(self, session_key: str, user_agent: str) -> Coroutine[Any, CursorResult, Any]:
        stmt = insert(UserSession).values(
            session_key=session_key,
            user_agent=user_agent
        ).on_conflict_do_update(
            index_elements=[UserSession.session_key, UserSession.user_agent],
            set_={
                "user_agent": insert(UserSession).excluded.user_agent,
                "create_at": func.now()
            }
        )
        return self._instance.ExecuteNonQuery(stmt)
