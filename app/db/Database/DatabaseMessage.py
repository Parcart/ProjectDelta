import uuid

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import selectinload

from app.db.schema import Dialogue, DialogueMessage


class DatabaseMessage:
    def __init__(self, instance):
        self._instance = instance

    async def create_dialogue(self, user_id, name):
        stmt = insert(Dialogue).values(id=uuid.uuid4().hex,user_id=user_id, name=name)
        return await self._instance.ExecuteNonQuery(stmt)

    async def get_dialogue(self, user_id, dialogue_id):
        stmt = select(Dialogue).where(Dialogue.user_id == user_id, Dialogue.id == dialogue_id)
        return await self._instance.GetSingle(stmt)

    async def get_dialogues(self, user_id):
        stmt = select(Dialogue).where(Dialogue.user_id == user_id)
        return await self._instance.GetAll(stmt)

    async def get_messages(self, dialogue_id):
        stmt = select(DialogueMessage).where(DialogueMessage.dialogue_id == dialogue_id)
        return await self._instance.GetAll(stmt)

    async def get_dialogues_with_messages(self, user_id):
        stmt = select(Dialogue).where(Dialogue.user_id == user_id).options(selectinload(Dialogue.messages))
        return await self._instance.GetAll(stmt)

    async def create_message(self, dialogue_id, content_type, sender, text):
        stmt = insert(DialogueMessage).values(dialogue_id=dialogue_id, content_type=content_type, sender=sender, text=text)
        return await self._instance.ExecuteNonQuery(stmt)
