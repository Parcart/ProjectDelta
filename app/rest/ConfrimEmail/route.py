import random
from typing import Annotated

from fastapi import HTTPException
from fastapi.params import Depends
from starlette import status

from ..Authentication.entity import ConfirmCodeRequest
from ..Authentication.handler import create_confirm_code, get_confirm_code, confirm_code
from ..CustomAPIRouter import APIRouter
from ..EmailService import EmailService
from ..User.entity import User as UserModel
from ...db.schema.Base import TokenType
from ...jwt_auth import AuthJWT
from ...jwt_auth.auth_jwt import get_current_user


class ConfirmEmail:

    def __init__(self):
        self.route = APIRouter(prefix="/user", tags=["ConfirmEmail"])
        self.route.add_api_route("/send_confirm_code_email/", self.send_confirm_code_email, methods=["POST"],
                                 responses={
                                     200: {
                                         "description": "OK",
                                         "content":
                                             {"application/json":
                                                 {
                                                     "example": {
                                                         "detail": 200
                                                     }
                                                 }
                                             }
                                     },
                                     400: {
                                         "description": "ErrorEmailAlreadyVerified",
                                         "content":
                                             {"application/json":
                                                 {
                                                     "example": {
                                                         "detail": "Email already verified"
                                                     }
                                                 }
                                             }
                                     }
                                 })
        self.route.add_api_route("/confirm_email/", self.confirm_email, methods=["POST"],
                                 responses={
                                     200: {
                                         "description": "OK",
                                         "content":
                                             {"application/json":
                                                 {
                                                     "example": {
                                                         "detail": 200
                                                     }
                                                 }
                                             }
                                     },
                                     400: {
                                         "description": "ErrorEmailAlreadyVerified",
                                         "content":
                                             {"EmailAlreadyVerified":
                                                 {
                                                     "example": {
                                                         "detail": "Email already verified"
                                                     }
                                                 },
                                                 "WrongCode":
                                                     {
                                                         "example": {
                                                             "detail": "Wrong code"
                                                         }
                                                     }
                                             }
                                     }
                                 })

    @classmethod
    async def send_code(cls, user_id, email, token_type: TokenType = TokenType.EMAIL_CONFIRMATION):
        code_confirm = random.randint(1000, 9999)
        await create_confirm_code(user_id, AuthJWT.hash_value(str(code_confirm)),
                                  TokenType.EMAIL_CONFIRMATION)
        print(code_confirm)
        EmailService().send_verification_email_code(code_confirm, email)

    async def send_confirm_code_email(self, current_user: Annotated[UserModel, Depends(get_current_user)],
                                      authorize: AuthJWT = Depends()):
        if not current_user.email_verified:
            await self.send_code(current_user.id, current_user.email)
            return 200
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="EmailAlreadyVerified",
        )

    @staticmethod
    async def confirm_code(current_user: UserModel, code: int, authorize: AuthJWT = Depends(), token_type: TokenType = TokenType.EMAIL_CONFIRMATION):
        confirmation_token = await get_confirm_code(user_id=current_user.id, token_type=token_type)
        if confirmation_token:
            if AuthJWT.verify_value(str(code), confirmation_token.code):
                return True
        return False

    async def confirm_email(self, current_user: Annotated[UserModel, Depends(get_current_user)],
                            request: ConfirmCodeRequest,
                            authorize: AuthJWT = Depends()):
        if current_user.email_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="EmailAlreadyVerified",
            )
        if await self.confirm_code(current_user, request.code):
            await confirm_code(current_user.id)
            return 200
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Wrong code",
        )

    async def confirm_email_tg(self, current_user: Annotated[UserModel, Depends(get_current_user)],
                               request: ConfirmCodeRequest,
                               authorize: AuthJWT = Depends()):
        await self.confirm_email(current_user, request)




