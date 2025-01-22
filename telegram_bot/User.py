import json
import os
import urllib.request
import uuid
from calendar import timegm
from datetime import timedelta, datetime, timezone
from enum import Enum
from functools import lru_cache
from io import BytesIO
from typing import Optional, Callable, List
from urllib.error import URLError

from pydantic import BaseModel, StrictStr, StrictInt, StrictBool, ConfigDict
from telebot.types import User as TelebotUser, Message, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, \
    ReplyKeyboardRemove, CallbackQuery

from passlib.context import CryptContext
from jose import jwt, JWTError

from telegram_bot.Text import text


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        key = (args, frozenset(kwargs.items()))
        if key not in cls._instances:
            cls._instances[key] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[key]

    @classmethod
    def remove_instance(cls, *args, **kwargs):
        key = (args, frozenset(kwargs.items()))
        if key in cls._instances:
            del cls._instances[key]


class StopProcessingError(Exception):
    pass


class TokensResponse(BaseModel):
    access_token: str
    refresh_token: str
    email_verified: Optional[bool] = None


class AuthConfig:
    _tg_secret_key = None
    _pwd_context: CryptContext = CryptContext(schemes=["bcrypt"], deprecated="auto")
    _algorithm = "HS256"
    _access_token_expires = None
    _reset_token_expires = None

    # _refresh_token_expires = None

    class LoadConfig(BaseModel):
        authjwt_secret_key: StrictStr | None = None
        tg_authjwt_secret_key: StrictStr | None = None
        authjwt_algorithm: StrictStr | None = "HS256"
        authjwt_access_token_expires: StrictBool | StrictInt | timedelta | None = timedelta(minutes=1)
        model_config = ConfigDict(str_min_length=1, str_strip_whitespace=True)

    @classmethod
    def load_config(cls, settings: [..., Callable]):
        try:
            config = cls.LoadConfig(**settings())

            cls._algorithm = config.authjwt_algorithm
            cls._access_token_expires = config.authjwt_access_token_expires
            cls._tg_secret_key = config.tg_authjwt_secret_key
        except Exception as e:
            print("Error loading config: ", e)
            raise e


class Authentication(AuthConfig):
    def __init__(self, tg_id):
        self.access_token: str
        self.refresh_token: str
        self.email_verified: bool

        self.access_token, self.refresh_token, self.email_verified = self.authenticate(tg_id)

    def authenticate(self, tg_id: int):
        request = urllib.request.Request(
            os.environ['REST'] + "/user/tg_auth",
            data=json.dumps({
                "telegram_id": tg_id
            }).encode('utf-8'),
            headers={'accept': 'application/json', 'Content-Type': 'application/json',
                     "Authorization": f"Bearer {self.create_auth_token(tg_id)}"}
        )
        try:
            with urllib.request.urlopen(request) as response:
                assert response.getcode() == 200
                response_data = json.loads(response.read().decode('utf-8'))
                return response_data["access_token"], response_data["refresh_token"], response_data["email_verified"]
        except urllib.error.HTTPError as e:
            if e.getcode() == 404:
                raise Authentication.NotRegisteredUser
            raise e
        except Exception as e:
            raise e

    class NotRegisteredUser(Exception):
        pass

    class EmailNotVerified(Exception):
        pass

    @classmethod
    def create_auth_token(cls, tg_id: int):
        data = {
            "tg_id": tg_id,
            "exp": datetime.now(timezone.utc) + cls._access_token_expires
        }
        return jwt.encode(data, cls._tg_secret_key, algorithm=cls._algorithm)

    def get_access_token(self):
        def refresh_token():
            request = urllib.request.Request(
                os.environ['REST'] + "/user/refresh/",
                headers={'accept': 'application/json', 'Content-Type': 'application/json',
                         "Authorization": f"Bearer {self.refresh_token}"},
                method='POST')

            try:
                with urllib.request.urlopen(request) as response:
                    if response.getcode() == 200:
                        response_data = json.loads(response.read().decode('utf-8'))
                        self.access_token = response_data["access_token"]
                        self.refresh_token = response_data["refresh_token"]
                        self.email_verified = response_data["email_verified"]
                    else:
                        print("Error:", response.getcode())
                        print("Message:", response.read().decode('utf-8'))
                        return False
            except urllib.error.HTTPError as e:
                self.access_token, self.refresh_token, self.email_verified = self.authenticate(payload.get("tg_id"))
            except urllib.error.URLError as e:
                raise e
            except Exception as e:
                raise e

        payload = jwt.decode(self.access_token, self._tg_secret_key, algorithms=self._algorithm,
                             options={"verify_exp": False, 'verify_signature': False})

        exp = int(payload.get("exp"))
        if exp < timegm(datetime.now(timezone.utc).utctimetuple()):
            refresh_token()

        return self.access_token


@Authentication.load_config
def get_config():
    return {
        "authjwt_algorithm": "HS256",
        "tg_authjwt_secret_key": "SECRET_KEY_TG"
    }


class TransactionType(Enum):
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"


class User(TelebotUser, metaclass=Singleton):
    class UserRegistrationFrom:
        def __init__(self):
            self.username = None
            self.email = None

    class UserProfile(BaseModel):
        id: str
        email: str
        created_at: datetime
        name: str
        balance: int

    class Transaction(BaseModel):
        id: int
        user_id: str
        amount: int
        description: str
        created_at: datetime
        transaction_type: TransactionType

    _bot = None

    def __init__(self, id, is_bot, first_name, last_name=None, username=None, language_code=None,
                 can_join_groups=None, can_read_all_group_messages=None, supports_inline_queries=None,
                 is_premium=None, added_to_attachment_menu=None, can_connect_to_business=None,
                 has_main_web_app=None, **kwargs):
        super().__init__(id, is_bot, first_name, last_name, username, language_code,
                         can_join_groups, can_read_all_group_messages, supports_inline_queries,
                         is_premium, added_to_attachment_menu, can_connect_to_business,
                         has_main_web_app, **kwargs)

        self.user_id: Optional[str]
        self.auth: Optional[Authentication] = None

        self.status = None

        try:
            self.authenticate()
        except Authentication.NotRegisteredUser:
            self.__ask_registration()
            self.status = StopProcessingError
            return
        except urllib.error.HTTPError as e:
            print(e)
            self.send(text['service_unavailable'], keyboard=ReplyKeyboardRemove())
            self.status = StopProcessingError
            return
        except urllib.error.URLError as e:
            print(e)
            self.send(text['service_unavailable'], keyboard=ReplyKeyboardRemove())
            self.status = StopProcessingError
            return
        except Exception as e:
            print(e)
            self.send(text['service_unavailable'], keyboard=ReplyKeyboardRemove())
            self.status = StopProcessingError
            return

        if not self.auth.email_verified:
            self.__ask_verification_email_code()
            self.status = StopProcessingError

    def authenticate(self):
        self.auth = Authentication(self.id)

    def check_completed_registration(self):
        if self.auth:
            if self.auth.email_verified:
                return True
        return False

    def __load_user(self):
        pass

    def send(self, text: str, keyboard=None, parse_mode=None, disable_web_page_preview=True) -> Message:

        message = text
        try:
            send: Message = self._bot.send_message(self.id,
                                                   message,
                                                   parse_mode=parse_mode,
                                                   reply_markup=keyboard,
                                                   disable_web_page_preview=disable_web_page_preview)
            return send
        except Exception as e:
            print(e)

    def __ask_registration(self):
        self.send("Привет ;>", keyboard=ReplyKeyboardRemove())
        markup_main = InlineKeyboardMarkup()
        markup_main.add(InlineKeyboardButton(text["button_registration"], callback_data="registration"))
        self.send(text["text_registration"],
                  keyboard=markup_main)

    def __ask_verification_email_code(self):
        self.send_verification_email_code()
        markup_main = InlineKeyboardMarkup()
        markup_main.add(InlineKeyboardButton(text['button_send_code'], callback_data="verification_code"))
        self.send(text['start_send_code'],
                  keyboard=markup_main)

    def registration(self, user_form: UserRegistrationFrom):
        request = urllib.request.Request(
            os.environ['REST'] + "/user/registrationtg/",
            data=json.dumps({
                "email": user_form.email,
                'password': "NULL",
                "name": user_form.username
            }).encode('utf-8'),
            headers={'accept': 'application/json', 'Content-Type': 'application/json',
                     "Authorization": f"Bearer {Authentication.create_auth_token(self.id)}"},
            method='POST'
        )
        try:
            with urllib.request.urlopen(request) as response:
                if response.getcode() == 200:
                    self.authenticate()
                    return 200
                else:
                    print("Error:", response.getcode())
                    print("Message:", response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            return e.getcode()

    def send_verification_email_code(self):
        request = urllib.request.Request(
            os.environ['REST'] + "/user/send_confirm_code_email/",
            headers={'accept': 'application/json', 'Content-Type': 'application/json',
                     "Authorization": f"Bearer {self.auth.get_access_token()}"},
            method='POST')

        try:
            with urllib.request.urlopen(request) as response:
                if response.getcode() == 200:
                    return True
                else:
                    print("Error:", response.getcode())
                    print("Message:", response.read().decode('utf-8'))
                    return False
        except urllib.error.HTTPError as e:
            return False

    def confirm_verification_code(self, code: str):
        request = urllib.request.Request(
            os.environ['REST'] + "/user/confirm_email/",
            data=json.dumps({
                "code": code
            }).encode('utf-8'),
            headers={'accept': 'application/json', 'Content-Type': 'application/json',
                     "Authorization": f"Bearer {self.auth.get_access_token()}"}
        )
        try:
            with urllib.request.urlopen(request) as response:
                if response.getcode() == 200:
                    return 200
                else:
                    return response.getcode()
        except urllib.error.HTTPError as e:
            return e.detail

    def link_telegram(self, email: str, code: int):
        request = urllib.request.Request(
            os.environ['REST'] + "/user/link_telegram/",
            data=json.dumps({
                "email": email,
                "code": code
            }).encode('utf-8'),
            headers={'accept': 'application/json', 'Content-Type': 'application/json',
                     "Authorization": f"Bearer {self.auth.get_access_token()}"}
        )
        try:
            with urllib.request.urlopen(request) as response:
                if response.getcode() == 200:
                    return 200
                else:
                    return response.getcode()
        except urllib.error.HTTPError as e:
            return e.getcode()

    def send_link_telegram_code(self):
        request = urllib.request.Request(
            os.environ['REST'] + "/user/send_link_telegram_code/",
            headers={'accept': 'application/json', 'Content-Type': 'application/json',
                     "Authorization": f"Bearer {self.auth.get_access_token()}"})

        try:
            with urllib.request.urlopen(request) as response:
                if response.getcode() == 200:
                    return True
                else:
                    print("Error:", response.getcode())
                    print("Message:", response.read().decode('utf-8'))
                    return False
        except urllib.error.HTTPError as e:
            return False

    def service_unavailable(self):
        self.send(text['service_unavailable'])

    def profile(self) -> UserProfile:
        request = urllib.request.Request(
            os.environ['REST'] + "/user",
            headers={'accept': 'application/json', 'Content-Type': 'application/json',
                     "Authorization": f"Bearer {self.auth.get_access_token()}"})

        try:
            with urllib.request.urlopen(request) as response:
                if response.getcode() == 200:
                    data = response.read().decode("utf-8")
                    json_data = json.loads(data)
                    return self.UserProfile(**json_data)
                else:
                    print("Error:", response.getcode())
                    print("Message:", response.read().decode('utf-8'))
                    raise
        except urllib.error.HTTPError as e:
            raise e

    def read_transactions(self) -> List[Transaction]:
        request = urllib.request.Request(
            os.environ['REST'] + "/user/transactions",
            headers={'accept': 'application/json', 'Content-Type': 'application/json',
                     "Authorization": f"Bearer {self.auth.get_access_token()}"})

        try:
            with urllib.request.urlopen(request) as response:
                if response.getcode() == 200:
                    data = response.read().decode("utf-8")
                    json_data = json.loads(data)
                    if len(json_data["transactions"]):
                        return [self.Transaction(**transaction) for transaction in json_data["transactions"]]
                    return []
                else:
                    print("Error:", response.getcode())
                    print("Message:", response.read().decode('utf-8'))
                    raise
        except urllib.error.HTTPError as e:
            raise e

    def add_balance(self, amount: int):
        request = urllib.request.Request(
            os.environ['REST'] + "/user/add_transaction",
            data=json.dumps({
                "amount": amount,
                "description": "Пополнение баланса"
            }).encode('utf-8'),
            headers={'accept': 'application/json', 'Content-Type': 'application/json',
                     "Authorization": f"Bearer {self.auth.get_access_token()}"}
        )
        try:
            with urllib.request.urlopen(request) as response:
                if response.getcode() == 200:
                    return True
                else:
                    raise
        except urllib.error.HTTPError as e:
            raise e

    def transcribe(self, audio_bytes, filename="NOPROCESS"):
        boundary = uuid.uuid4().hex
        content_type = f'multipart/form-data; boundary={boundary}'
        body = BytesIO()

        # Добавляем файл (исправили имя и структуру)
        body.write(("--" + boundary + "\r\n").encode())
        body.write(f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode()) #исправленное имя файла
        body.write('Content-Type: application/octet-stream\r\n'.encode())
        body.write(b"\r\n")
        body.write(audio_bytes)
        body.write(b"\r\n")


        # Завершающая граница
        body.write(("--" + boundary + "--\r\n").encode())

        body_bytes = body.getvalue()
        request = urllib.request.Request(
            os.environ['REST'] + "/message/transcribe",
            data=body_bytes,
            headers={'accept': 'application/json',
                     'Content-Type': content_type,
                     'Content-Length': str(len(body_bytes)), # правильное вычисление длины
                     "Authorization": f"Bearer {self.auth.get_access_token()}"}
        )
        try:
            with urllib.request.urlopen(request) as response:
                if response.getcode() == 200:
                    data = response.read().decode("utf-8")
                    json_data = json.loads(data)
                    return json_data
                else:
                    print("Error:", response.getcode())
                    print("Message:", response.read().decode('utf-8'))
                    raise
        except urllib.error.HTTPError as e:
            print(f"HTTP Error: {e.code} - {e.reason}")
            print(e.read().decode('utf-8')) #вывод текста ошибки сервера
            raise
        except Exception as e:
            print(f"Другая ошибка: {e}")
            raise

    def error(self, message=None):
        if message and not isinstance(message, CallbackQuery):
            self._bot.reply_to(message, text['error'])
        else:
            self.send(text['error'])
