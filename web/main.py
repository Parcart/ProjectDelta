import os
from datetime import datetime
from functools import wraps

from flask import Flask, request, render_template, redirect, url_for, flash, Response
import requests

from web.auth import auth_bp, Authentication, send_confirmation_email
from web.forms import LoginForm, RegistrationForm, EmailConfirmationForm
from web.admin import admin_bp
from web.chat import chat_bp


template_folder = 'templates'
static_folder = 'static'
if os.environ.get('AM_IN_DOCKER', None):
    template_folder = '/web/templates'
    static_folder = '/web/static'

app = Flask(__name__,
            template_folder=template_folder,
            root_path=os.path.dirname(__file__),
            static_folder=static_folder,
            static_url_path=None)

app.config['SECRET_KEY'] = "Don't Panic! 42!"
BACKEND_URL = os.environ.get('BACKEND_URL', 'http://localhost:8080')
print(BACKEND_URL)
PROFILE_END_POINT = f"{BACKEND_URL}/user/web_me"


def format_datetime(value):
    if value:
        date_obj = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return date_obj.strftime('%H:%M:%S %d.%m.%Y')
    return ''


admin_bp.add_app_template_filter(format_datetime, 'format_datetime')

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(chat_bp, url_prefix='/chat')


@app.after_request
def after_request_func(response: Response):
    if hasattr(request, 'auth'):
        request.auth.set_auth_cookie(response)
    return response


def main_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            auth_user: Authentication = Authentication.cookie_auth()
            kwargs['auth'] = auth_user
            return func(*args, **kwargs)
        except Exception as e:
            kwargs['auth'] = e
            return func(*args, **kwargs)

    return wrapper


@app.route("/")
@main_required
def index(auth):
    if isinstance(auth, Authentication.ErrorEmailVerification):
        send_confirmation_email(auth, auth.user.email)
        return render_template("confirm_email.html", form=EmailConfirmationForm(), email=auth.user.email)
    if isinstance(auth, Exception):
        return render_template("about.html", title="About")

    return render_template("chat.html", title="Chat", **auth.user.layout_kwargs())


@app.route('/profile', methods=['GET'])
@main_required
def page_profile(auth):
    if isinstance(auth, Exception):
        return redirect(url_for('index'))

    response = requests.get(PROFILE_END_POINT, headers={
        'accept': 'application/json',
        "Authorization": f"Bearer {auth.get_access_token()}"})

    if response.ok:
        user = response.json()
        return render_template('user_profile.html', user=user, title='Profile', **auth.user.layout_kwargs())
    flash('Something went wrong', 'danger')
    return redirect(url_for('index'))


@app.route('/login', methods=['GET'])
@main_required
def login_page(auth):
    if isinstance(auth, Authentication):
        return redirect(url_for('index'))
    login_form = LoginForm()
    return render_template("login.html", login_form=login_form, title="Login")


@app.route('/about')
@main_required
def about(auth):
    if isinstance(auth, Exception):
        return render_template("about.html", title="About")
    return render_template("about.html", title="About", **auth.user.layout_kwargs())


@app.route('/registration', methods=['GET'])
@main_required
def registration_page(auth):
    if isinstance(auth, Authentication):
        return redirect(url_for('index'))
    registration_form = RegistrationForm()
    return render_template("registration.html", title="Registration", registration_form=registration_form)


@app.route('/logout', methods=['GET'])
def page_logout():
    return redirect(url_for('auth.logout'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
