import os
from calendar import timegm
from datetime import datetime, timezone
from enum import Enum

from flask import Blueprint, request, make_response, redirect, url_for, render_template, Response, jsonify
import requests
from web.forms import LoginForm, RegistrationForm, EmailConfirmationForm
from jose import jwt



class User:
    class RoleType(Enum):
        USER = "USER"
        ADMIN = "ADMIN"

    def __init__(self, access_token: str):
        user_data = self.__get_user(access_token)
        self.id: str = user_data["id"]
        self.email: str = user_data["email"]
        self.created_at: datetime = datetime.fromisoformat(user_data["created_at"])
        self.name: str = user_data["name"]
        self.balance: int = user_data["balance"]
        self.role: User.RoleType = User.RoleType(user_data["role"])

    @staticmethod
    def __get_user(access_token: str) -> dict:
        response = requests.get(USER_ME_END_POINT, headers={
            'accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        })

        if response.ok:
            return response.json()
        else:
            raise Authentication.ErrorAuthentication(response.status_code, response.text)

    def refresh(self, access_token: str) -> 'User':
        for k, v in self.__get_user(access_token).items():
            self.__setattr__(k, v)
        return self

    def layout_kwargs(self):
        return {
            "username": self.name,
            "balance": self.balance,
            "role": self.role.value
        }


class Authentication:
    class ErrorAuthentication(Exception):
        def __init__(self, code, message):
            self.code = code
            self.message = message

        def __str__(self):
            return f"{self.code}: {self.message}"

    class ErrorEmailVerification(Exception):

        def __init__(self, auth):
            self.auth: Authentication = auth

    class ErrorTokenExpired(Exception):
        pass

    def __init__(self, access_token, refresh_token, email_verified):
        self.access_token: str = access_token
        self.refresh_token: str = refresh_token
        self.email_verified: bool = email_verified

        self.get_access_token()

        if not self.email_verified:
            raise self.ErrorEmailVerification(self)

        self.user: User = User(self.access_token)

    @classmethod
    def web_auth(cls, email: str, password: str) -> 'Authentication':
        data = {
            'grant_type': 'password',
            'username': email,
            'password': password,
            'scope': '',
            'client_id': '',
            'client_secret': ''
        }
        response = requests.post(TOKEN_END_POINT, data=data, headers={
            'accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded',
        })
        if response.ok:
            token_data = response.json()
            return cls(token_data['access_token'], token_data['refresh_token'], token_data['email_verified'])
        else:
            if response.status_code == 401:
                raise cls.ErrorAuthentication(401, 'Invalid password')
            raise cls.ErrorAuthentication(response.status_code, response.text)

    @classmethod
    def cookie_auth(cls) -> 'Authentication':
        if (not request.cookies.get('access_token') and
                not request.cookies.get('refresh_token') and
                request.cookies.get('email_verified') is None):
            raise cls.ErrorTokenExpired
        self = Authentication(
            request.cookies.get('access_token'),
            request.cookies.get('refresh_token'),
            request.cookies.get('email_verified')
        )
        return self

    @staticmethod
    def __validate_token(token: str):
        try:
            payload = jwt.decode(token, "SECRET", algorithms=["HS256"],
                                 options={"verify_exp": False, 'verify_signature': False})

            exp = int(payload.get("exp"))
            if exp < timegm(datetime.now(timezone.utc).utctimetuple()):
                return False
            return True
        except Exception as e:
            raise e

    @classmethod
    def __refresh_token(cls, refresh_token: str):
        response = requests.post(REFRESH_TOKEN_END_POINT, headers={
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }, json={'refresh_token': refresh_token})
        if response.ok:
            token_data = response.json()
            return token_data
        else:
            if response.status_code == 401:
                raise cls.ErrorTokenExpired
            raise cls.ErrorAuthentication(response.status_code, response.text)

    def refresh_tokens(self):
        token_data = self.__refresh_token(self.refresh_token)
        self.access_token = token_data['access_token']
        self.refresh_token = token_data['refresh_token']
        self.email_verified = token_data['email_verified']
        return self

    def get_access_token(self):
        if not self.__validate_token(self.access_token):
            token_data = self.__refresh_token(self.refresh_token)
            self.access_token = token_data['access_token']
            self.refresh_token = token_data['refresh_token']
            self.email_verified = token_data['email_verified']
            return self.access_token

        return self.access_token

    def set_auth_cookie(self, response: Response) -> Response:
        response.set_cookie('access_token', self.get_access_token(), httponly=True)
        response.set_cookie('refresh_token', self.refresh_token, httponly=True)
        response.set_cookie('email_verified', str(self.email_verified), httponly=True)
        return response

    @staticmethod
    def logout(response: Response) -> Response:
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        response.delete_cookie('email_verified')
        return response


auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
BACKEND_URL = os.environ.get('BACKEND_URL', 'http://localhost:8080')
TOKEN_END_POINT = f"{BACKEND_URL}/user/login"
REFRESH_TOKEN_END_POINT = f"{BACKEND_URL}/user/refresh"
REGISTRATION_END_POINT = f"{BACKEND_URL}/user/registration"
SEND_VERIFICATION_CODE_END_POINT = f"{BACKEND_URL}/user/send_confirm_code_email"
CONFIRM_EMAIL_END_POINT = f"{BACKEND_URL}/user/confirm_email"
USER_ME_END_POINT = f"{BACKEND_URL}/user"


def send_confirmation_email(auth: Authentication, email):
    response = requests.post(SEND_VERIFICATION_CODE_END_POINT, json={
        "email": email
    }, headers={'accept': 'application/json', 'Content-Type': 'application/json',
                "Authorization": f"Bearer {auth.get_access_token()}"})

    if response.ok:
        return True
    else:
        return False


@auth_bp.route('/login', methods=['POST'])
def login():
    login_form = LoginForm(request.form)
    if login_form.validate_on_submit():
        email = login_form.email.data
        password = login_form.password.data

        try:
            auth = Authentication.web_auth(email, password)
        except Authentication.ErrorEmailVerification as e:
            send_confirmation_email(e.auth, email)
            return e.auth.set_auth_cookie(make_response(render_template(
                'confirm_email.html',
                form=EmailConfirmationForm(),
                email=email
            )))
        except Authentication.ErrorAuthentication as e:
            return render_template('login.html', login_form=login_form, error=str(e), title="Login")
        except Exception as e:
            print(e)
            return render_template('login.html', login_form=login_form, error='Something went wrong', title="Login")

        return auth.set_auth_cookie(make_response(redirect(url_for("index"))))
    else:
        errors = []
        for field, error_list in login_form.errors.items():
            for error in error_list:
                errors.append(f'{field}: {error}')
        return render_template('login.html', login_form=login_form, errors=errors, title="Login")


@auth_bp.route('/registration', methods=['POST'])
def register():
    registration_form = RegistrationForm(request.form)
    email_confirmation_form = EmailConfirmationForm()
    if registration_form.validate_on_submit():
        response = requests.post(REGISTRATION_END_POINT, json={
            "email": registration_form.email.data,
            "password": registration_form.password.data,
            "name": registration_form.name.data
        })
        if response.ok:
            try:
                auth = Authentication.web_auth(registration_form.email.data, registration_form.password.data)
            except Authentication.ErrorEmailVerification as e:
                res = e.auth.set_auth_cookie(make_response(render_template(
                    'confirm_email.html',
                    form=email_confirmation_form,
                    email=registration_form.email.data
                )))
                return res

            return auth.set_auth_cookie(make_response(redirect(url_for("index"))))
        else:
            return render_template('registration.html', registration_form=registration_form, error=response.text,
                                   title="Registration")
    else:
        # Получаем все ошибки из формы
        errors = []
        for field, error_list in registration_form.errors.items():
            for error in error_list:
                errors.append(f'{field}: {error}')
        return render_template('registration.html', registration_form=registration_form, errors=errors)


@auth_bp.route('/confirm_email', methods=['POST'])
def confirm_email():
    auth: Authentication = Authentication.cookie_auth()
    form = EmailConfirmationForm(request.form)
    email = request.args.get('email')
    if form.validate_on_submit():
        code = form.code.data
        response = requests.post(CONFIRM_EMAIL_END_POINT,
                                 json={
                                     'code': code
                                 },
                                 headers={
                                     'accept': 'application/json',
                                     'Content-Type': 'application/json',
                                     "Authorization": f"Bearer {auth.get_access_token()}"
                                 }
                                 )

        if response.ok:
            try:
                auth.refresh_tokens()
            except Authentication.ErrorTokenExpired:
                return redirect(url_for("auth.login"))
            except Authentication.ErrorAuthentication as e:
                return render_template('confirm_email.html', form=form, email=email, error=str(e),
                                       title="Confirm Email")

            return auth.set_auth_cookie(make_response(redirect(url_for("index"))))
        if response.status_code == 400:
            return render_template('confirm_email.html', form=form, email=email, error=response.text,
                                   title="Confirm Email")
        return render_template('confirm_email.html', form=form, email=email, error=response.text, title="Confirm Email")

    else:
        errors = []
        for field, error_list in form.errors.items():
            for error in error_list:
                errors.append(f'{field}: {error}')
        return render_template('confirm_email.html', login_form=form, errors=errors, email=auth.user.email,
                               title="Confirm Email")


@auth_bp.route('/resend_code', methods=['POST'])
def resend_code():
    auth: Authentication = Authentication.cookie_auth()
    email = request.args.get('email')
    if send_confirmation_email(auth, email):
        return jsonify({'message': 'Code resent!'})
    return jsonify({'error': 'Something went wrong'}), 500


@auth_bp.route('/logout')
def logout():
    auth: Authentication = Authentication.cookie_auth()
    return auth.logout(make_response(redirect(url_for("index"))))
