from pydantic import BaseModel


class CreateDialogueRequest(BaseModel):
    name: str


class CreateMessageRequest(BaseModel):
    dialogue_id: str


class GetMessagesRequest(BaseModel):
    dialogue_id: str
