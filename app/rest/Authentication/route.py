import random
from typing import Annotated

from fastapi import HTTPException, Request
from fastapi.params import Depends
from fastapi.security import OAuth2PasswordRequestForm
from starlette import status
from user_agents import parse

from .entity import TokensResponse, RefreshTokenRequest, UserAuthenticationForm, WebTokenResponse, UserRegistrationForm, \
    TelegramLinkForm

from .handler import get_user, registration_user, post_session, set_telegram_id, create_confirm_code
from ..ConfrimEmail.route import ConfirmEmail
from ..CustomAPIRouter import APIRouter
from ..EmailService import EmailService
from ...db.DAO import DAO
from ...db.schema.Base import TokenType
from ...db.schema.Entity import User as UserBase
from ...jwt_auth.auth_jwt import get_refresh_token, AuthJWT, tg_validate_token, get_current_user
from ..User.entity import User as UserModel


class Authentication:

    def __init__(self):
        self.route = APIRouter(prefix="/user", tags=["Authentication"])
        self.route.add_api_route("/login", self.web_auth, methods=["POST"], response_model=WebTokenResponse,
                                 responses={
                                     401: {
                                         "description": "ErrorAuthentication",
                                         "content":
                                             {"application/json":
                                                 {
                                                     "example": {
                                                         "detail": "Incorrect username or password"
                                                     }
                                                 }
                                             }
                                     }
                                 })
        self.route.add_api_route("/token", self.rest_auth, methods=["POST"], response_model=TokensResponse,
                                 responses={
                                     401: {
                                         "description": "ErrorAuthentication",
                                         "content":
                                             {"application/json":
                                                 {
                                                     "example": {
                                                         "detail": "Incorrect username or password"
                                                     }
                                                 }
                                             }
                                     }
                                 })
        self.route.add_api_route("/registration", self.registration, methods=["POST"], response_model=TokensResponse,
                                 responses={
                                     409: {
                                         "description": "ErrorCreateUser",
                                         "content":
                                             {"application/json":
                                                 {
                                                     "example": {
                                                         "detail": "Already registered"
                                                     }
                                                 }
                                             }
                                     },
                                     500: {
                                         "description": "ErrorCreateUser",
                                         "content":
                                             {"application/json":
                                                 {
                                                     "example": {
                                                         "detail": "Error register User."
                                                     }
                                                 }
                                             }
                                     }
                                 })
        self.route.add_api_route("/refresh", self.refresh_access_token, methods=["POST"], response_model=TokensResponse)
        self.route.add_api_route('/tg_auth', self.tg_auth, methods=['POST'], response_model=TokensResponse)
        self.route.add_api_route('/registrationtg', self.registration_tg, methods=['POST'])
        self.route.add_api_route('/link_tg', self.link_tg, methods=['POST'])
        self.route.add_api_route('/send_link_tg_code', self.send_link_tg_code, methods=['POST'])

    @staticmethod
    async def refresh_access_token(refresh_token_request: RefreshTokenRequest,
                                   authorize: AuthJWT = Depends()):
        refresh_token_data = await get_refresh_token(refresh_token_request)
        user = await get_user(user_id=refresh_token_data.user_id)
        access_token = authorize.create_token(data={"sub": refresh_token_data.user_id,
                                                    "sid": refresh_token_data.session_key},
                                              token_type=TokenType.ACCESS_TOKEN)
        return TokensResponse(access_token=access_token, refresh_token=refresh_token_request.refresh_token,
                              email_verified=user.email_verified)

    @staticmethod
    async def authenticate(form_data: OAuth2PasswordRequestForm | UserAuthenticationForm | int,
                           request: Request,
                           authorize: AuthJWT = Depends()) -> TokensResponse:
        if isinstance(form_data, OAuth2PasswordRequestForm):
            user: UserBase = await authorize.authenticate_user(form_data.username, form_data.password)
        elif isinstance(form_data, int):
            user: UserBase = await get_user(telegram_id=form_data)
        else:
            user: UserBase = await authorize.authenticate_user(form_data.email, form_data.password)
        if not user.session_key:
            user.session_key = await authorize.set_session_key(user.id)
        response = authorize.create_tokens(data={"sub": user.id,
                                                 "sid": user.session_key})
        response.email_verified = user.email_verified
        if await post_session(user.session_key, str(parse(request.headers.getlist("user-agent")[0]))):
            pass
        return response

    async def web_auth(self, form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                       request: Request,
                       authorize: AuthJWT = Depends()) -> WebTokenResponse:
        tokens_response = await self.authenticate(form_data, request, authorize)
        return WebTokenResponse(access_token=tokens_response.access_token, token_type="bearer")

    async def rest_auth(self, form_data: UserAuthenticationForm, request: Request,
                        authorize: AuthJWT = Depends()
                        ) -> TokensResponse:
        return await self.authenticate(form_data, request, authorize)

    async def tg_auth(self, tg_id: Annotated[int, Depends(tg_validate_token)],
                      request: Request,
                      authorize: AuthJWT = Depends()
                      ):
        assert request.client.host == '127.0.0.1'
        try:
            user = await get_user(telegram_id=tg_id)
            if not user:
                raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return await self.authenticate(tg_id, request, authorize)

    @staticmethod
    async def registration(current_tg_id: Annotated[int, Depends(tg_validate_token)],
                           form_data: UserRegistrationForm, request: Request,
                           authorize: AuthJWT = Depends()) -> int:
        user = await get_user(form_data.email)
        if user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Already registered",
            )
        session_key = authorize.generate_session_key()
        user_id = await registration_user(email=form_data.email, password=authorize.hash_value(form_data.password),
                                          telegram_id=current_tg_id, name=form_data.name,
                                          session_key=session_key)
        if user_id:
            await ConfirmEmail.send_code(user_id, form_data.email)
            return 200
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error register User.",
        )

    async def registration_tg(self, current_tg_id: Annotated[int, Depends(tg_validate_token)],
                              form_data: UserRegistrationForm,
                              request: Request,
                              authorize: AuthJWT = Depends()):
        user_tg = await get_user(telegram_id=current_tg_id)
        user = await get_user(email=form_data.email)
        if not user:
            session_key = authorize.generate_session_key()
            user_id = await registration_user(email=form_data.email, password="",
                                              telegram_id=current_tg_id, name=form_data.name,
                                              session_key=session_key)
        else:
            if user_tg:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Already linked",
                )
            await self.send_link_code(user)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Already registered",
            )

        return 200

    @staticmethod
    async def send_link_code(user: UserModel):
        code_confirm = random.randint(1000, 9999)
        await create_confirm_code(user.id, AuthJWT.hash_value(str(code_confirm)),
                                  TokenType.LINK_TG)
        print(code_confirm)
        EmailService().send_link_tg_code(code_confirm, user.email)

    @staticmethod
    async def send_link_tg_code(self, current_user: Annotated[UserModel, Depends(get_current_user)],
                                authorize: AuthJWT = Depends()):
        await self.send_link_code(current_user)
        return 200

    @staticmethod
    async def link_tg(current_tg_id: Annotated[int, Depends(tg_validate_token)],
                      form_data: TelegramLinkForm,
                      request: Request,
                      authorize: AuthJWT = Depends()):
        user = await get_user(email=form_data.email)
        user_tg = await get_user(telegram_id=current_tg_id)

        if not (not user_tg and user.telegram_id != current_tg_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Already linked",
            )

        if ConfirmEmail.confirm_code(user, form_data.code, token_type=TokenType.LINK_TG):
            await set_telegram_id(user_id=user.id, telegram_id=current_tg_id)
            return 200

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Wrong code",
        )
