import random
from typing import Annotated

from fastapi import HTTPException
from fastapi.params import Depends
from starlette import status

from app.db.DAO import DAO
from app.db.schema.Base import TokenType
from app.jwt_auth import AuthJWT
from app.jwt_auth.auth_jwt import validate_token, get_current_active_user
from app.rest.Authentication.entity import TokenResponse, EmailRequest, TokenData, ConfirmCodeRequest, \
    ResetPasswordRequest
from app.rest.Authentication.handler import get_user, create_confirm_code, get_confirm_code, confirm_code, \
    change_password
from app.rest.CustomAPIRouter import APIRouter
from app.rest.EmailService import EmailService


class ResetPassword:

    def __init__(self):
        self.route = APIRouter(prefix="/user", tags=["ResetPassword"])
        self.route.add_api_route("/reset_password_send_code/", self.reset_password_send_code, methods=["POST"],
                                 response_model=TokenResponse,
                                 responses={
                                     404: {
                                         "description": "ErrorUserNotFound",
                                         "content":
                                             {"application/json":
                                                 {
                                                     "example": {
                                                         "detail": "User not found"
                                                     }
                                                 }
                                             }
                                     }
                                 })
        self.route.add_api_route("/reset_password_confirm_code/", self.reset_password_confirm_code, methods=["POST"],
                                 response_model=TokenResponse,
                                 responses={
                                     404: {
                                         "description": "ErrorUserNotFound",
                                         "content":
                                             {"application/json":
                                                 {
                                                     "example": {
                                                         "detail": "User not found"
                                                     }
                                                 }
                                             }
                                     }
                                 })
        self.route.add_api_route("/reset_password/", self.reset_password, methods=["POST"],
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
                                     404: {
                                         "description": "ErrorUserNotFound",
                                         "content":
                                             {"application/json":
                                                 {
                                                     "example": {
                                                         "detail": "User not found"
                                                     }
                                                 }
                                             }
                                     },
                                     400: {
                                         "description": "ErrorWrongTokenType",
                                         "content":
                                             {"application/json":
                                                 {
                                                     "example": {
                                                         "detail": "Wrong token type"
                                                     }
                                                 }
                                             }
                                     },
                                     500: {
                                         "description": "ErrorChangePassword",
                                         "content":
                                             {"application/json":
                                                 {
                                                     "example": {
                                                         "detail": "Password not changed"
                                                     }
                                                 }
                                             }
                                     }
                                 })

    @staticmethod
    async def reset_password_send_code(request: EmailRequest,
                                       authorize: AuthJWT = Depends()):
        user = await get_user(request.email)
        if user:
            code_confirm = random.randint(100000, 999999)
            print(code_confirm)
            await create_confirm_code(user.id, authorize.hash_value(str(code_confirm)), TokenType.PASSWORD_RESET)
            EmailService().send_reset_password_code(code_confirm, user.email)
            confirm_code_token = authorize.create_token(data={"sub": user.id},
                                                        token_type=TokenType.CODE_CONFIRMATION)
            return TokenResponse(token=confirm_code_token, type=TokenType.CODE_CONFIRMATION.value)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found",
        )

    @staticmethod
    async def reset_password_confirm_code(token: Annotated[TokenData, Depends(validate_token)],
                                          request: ConfirmCodeRequest,
                                          authorize: AuthJWT = Depends()):
        if token.token_type == TokenType.CODE_CONFIRMATION:
            confirmation_code = await get_confirm_code(TokenType.PASSWORD_RESET, user_id=token.user_id)
            await get_current_active_user(await DAO().User.get(user_id=token.user_id))
            if confirmation_code and authorize.verify_value(str(request.code), confirmation_code.code):
                await confirm_code(token.user_id)
                reset_password_token = authorize.create_token(
                    data={"sub": confirmation_code.user_id,
                          "jti": authorize.generate_session_key()},
                    token_type=TokenType.PASSWORD_RESET
                )
                return TokenResponse(token=reset_password_token, type=TokenType.PASSWORD_RESET.value)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Wrong code",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Wrong token type",
            )

    @staticmethod
    async def reset_password(token: Annotated[TokenData, Depends(validate_token)],
                             request: ResetPasswordRequest,
                             authorize: AuthJWT = Depends()):
        if token.token_type == TokenType.PASSWORD_RESET or token.token_type == TokenType.ACCESS_TOKEN:
            user = await get_user(user_id=token.user_id)
            if user:
                await get_current_active_user(user)
                if await change_password(user.id, authorize.hash_value(request.password)):
                    return 200
                else:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Password not changed",
                    )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not found",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Wrong token type",
            )
