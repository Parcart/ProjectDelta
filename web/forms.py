from enum import Enum

from flask_wtf import FlaskForm
from wtforms.fields.choices import SelectField
from wtforms.fields.numeric import IntegerField
from wtforms.fields.simple import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length


class TransactionType(Enum):
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class RegistrationForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(min=1, max=50)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password",
                             validators=[DataRequired(), EqualTo('password2', message='Passwords must match'), Length(min=5, max=50)])
    password2 = PasswordField('Confirm Password',
                              validators=[DataRequired(), EqualTo('password', message='Passwords must match'), Length(min=5, max=50)])
    submit = SubmitField("Register")


class EmailConfirmationForm(FlaskForm):
    code = IntegerField('Confirmation Code', validators=[DataRequired()])
    submit = SubmitField('Confirm Email')


class OAuth2PasswordRequestForm(FlaskForm):
    grant_type = StringField('grant_type', default="password", validators=[DataRequired()])
    username = StringField('username', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired(), Length(min=4, max=20)])
    scope = StringField('scope')
    submit = SubmitField('Get Token')


class TransactionForm(FlaskForm):
    user_id = SelectField('User', validators=[DataRequired()], coerce=str)
    amount = IntegerField('Amount', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    transaction_type = SelectField('Transaction Type', choices=[(type.value, type.name) for type in TransactionType], validators=[DataRequired()])
    submit = SubmitField('Create Transaction')
