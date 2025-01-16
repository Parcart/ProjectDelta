import os
from typing import Annotated


from fastapi import HTTPException, status
from fastapi.params import Depends

from .entity import DialogueCreateResponse, DialoguesResponse, DialogueCreateRequest
from .handler import get_dialogues
from ..CustomAPIRouter import APIRouter
from ..User.entity import User as UserModel
from ..User.handler import get_user_profile
from ...jwt_auth.auth_jwt import get_current_active_user, get_token


class Dialogue:
    def __init__(self):
        self.route = APIRouter(prefix="/dialogue", tags=["Dialogue"])
        self.route.add_api_route("/", self.get_chats, methods=["GET"], response_model=DialoguesResponse)
        self.route.add_api_route("/create", self.post_dialogue, methods=["POST"],
                                 response_model=DialogueCreateResponse,
                                 responses={
                                     500: {
                                         "description": "ErrorDialogue",
                                         "content": {
                                             "RESTError": {
                                                 "example": {
                                                     "detail": "Failed to create dialogue"
                                                 }
                                             }
                                         }
                                     },
                                 })

    @staticmethod
    async def get_chats(current_user: Annotated[UserModel, Depends(get_current_active_user)]):
        result = await get_dialogues(current_user)
        return result

    @staticmethod
    async def post_dialogue(token: Annotated[str, Depends(get_token)],
                            current_user: Annotated[UserModel, Depends(get_current_active_user)],
                            dialogue_create: DialogueCreateRequest):
        pass

