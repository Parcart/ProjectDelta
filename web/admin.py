import datetime
import os
from enum import Enum
from functools import wraps

import requests
from flask import Blueprint, render_template, request, redirect, url_for, flash
import logging
from werkzeug.exceptions import HTTPException

from web.auth import Authentication, User

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
logging.basicConfig(level=logging.DEBUG)

BACKEND_URL = os.environ.get('BACKEND_URL', 'http://localhost:8080')
ADMIN_GET_ALL_USERS_END_POINT = f"{BACKEND_URL}/admin/users"
ADMIN_USER_DETAIL_END_POINT = f"{BACKEND_URL}/admin/users/"
ADMIN_USER_ADD_TRANSACTION_END_POINT = f"{BACKEND_URL}/admin/add_transaction"
ADMIN_TRANSACTIONS_END_POINT = f"{BACKEND_URL}/admin/transactions"


class TransactionType(Enum):
    DEBIT = 'DEBIT'
    CREDIT = 'CREDIT'


def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            auth_user: Authentication = Authentication.cookie_auth()
            if auth_user.user.role != User.RoleType.ADMIN:
                raise HTTPException(403, 'Forbidden')
            kwargs['auth'] = auth_user
            return func(*args, **kwargs)
        except Exception as e:
            raise HTTPException(403, f'Forbidden: {str(e)}')

    return wrapper


@admin_bp.route('/dashboard', methods=['GET'])
@admin_required
def admin_dashboard(auth):
    return render_template('admin/dashboard.html', title='Dashboard', **auth.user.layout_kwargs())


@admin_bp.route('/users', methods=['GET'])
@admin_required
def admin_users(auth: Authentication):
    response = requests.get(ADMIN_GET_ALL_USERS_END_POINT, headers={
        'accept': 'application/json',
        "Authorization": f"Bearer {auth.get_access_token()}"})

    if response.ok:
        data = response.json()
        if 'users' in data:
            users = data['users']
            response_users = []
            for user in users:
                response_users.append({
                    'id': user['id'],
                    'email': user['email'],
                    'name': user['name']
                })
            return render_template('admin/users.html', users=users, title='Users', **auth.user.layout_kwargs())
    flash('Something went wrong', 'danger')
    return redirect(url_for('admin.admin_dashboard'))


@admin_bp.route('/users/<user_id>', methods=['GET'])
@admin_required
def admin_user_detail(auth, user_id):
    response = requests.get(ADMIN_USER_DETAIL_END_POINT + user_id, headers={
        'accept': 'application/json',
        "Authorization": f"Bearer {auth.get_access_token()}"})

    if response.ok:
        user = response.json()
        return render_template('admin/user_detail.html', user=user, title='User', **auth.user.layout_kwargs(), TransactionType=TransactionType)
    flash('Something went wrong', 'danger')
    return redirect(url_for('admin.admin_dashboard'))


@admin_bp.route('/add_transactions', methods=['GET', 'POST'])
@admin_required
def admin_add_transaction(auth):
    data = {
        'id': 0,
        'user_id': request.form.get("user_id"),
        'amount': int(request.form.get("amount")),
        'description': request.form.get("description"),
        'created_at': datetime.datetime.now().isoformat(),
        'transaction_type': request.form.get("transaction_type"),

    }
    try:

        response = requests.post(ADMIN_USER_ADD_TRANSACTION_END_POINT, json=data, headers={
            'accept': 'application/json',
            'Content-Type': 'application/json',
            "Authorization": f"Bearer {auth.get_access_token()}"

        })
    except Exception as e:
        flash('Something went wrong', 'danger')
        return redirect(url_for('admin.admin_dashboard'))

    if response.ok:
        return redirect(url_for('admin.admin_user_detail', user_id=data['user_id']))
    flash('Something went wrong', 'danger')
    return redirect(url_for('admin.admin_dashboard'))


@admin_bp.route('/transactions', methods=['GET'])
@admin_required
def admin_transactions(auth):
    response = requests.get(ADMIN_TRANSACTIONS_END_POINT, headers={
        'accept': 'application/json',
        "Authorization": f"Bearer {auth.get_access_token()}"})

    if response.ok:
        transactions = response.json()
        return render_template('admin/transactions.html', transactions=transactions, title='Transactions', **auth.user.layout_kwargs())
    flash('Something went wrong', 'danger')
    return redirect(url_for('admin.admin_dashboard'))