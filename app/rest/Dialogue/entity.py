from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, constr, model_validator

from ...db.schema.Base import DifficultDialogue, SenderType, MessageContentType


class VoiceInfoResponse(BaseModel):
    voice_data_id: str
    sound_wave: str
    duration: float


class InlineKeyBoardButton(BaseModel):
    id: int
    text: str
    is_tapped: bool = False
    is_disabled: bool = False


# class ReplyKeyboard(BaseModel):
#     buttons: list[InlineKeyBoardButton]
#     is_frozen: bool = False


class MessageResponse(BaseModel):
    id: int
    content_type: MessageContentType
    sender: SenderType
    voice_info: Optional[VoiceInfoResponse]
    text: Optional[str]
    translate_text: Optional[str]
    buttons: Optional[list[InlineKeyBoardButton]] = None
    timestamp: datetime


class DialogueMode(BaseModel):
    difficulty: DifficultDialogue = DifficultDialogue.easy
    mistakes: bool = False
    reference_id: Optional[int] = None



class DialogueInfo(DialogueMode):
    name: str


class DialogueResponse(BaseModel):
    id: int
    name: str
    mode: str
    is_finished: bool = False
    difficulty: DifficultDialogue
    messages: List[MessageResponse] = []


class DialoguesResponse(BaseModel):
    data: List[DialogueResponse]


class DialogueCreateRequest(BaseModel):
    name: constr(min_length=1)
    mode: DialogueMode


class DialogueCreateResponse(BaseModel):
    data: DialogueResponse

