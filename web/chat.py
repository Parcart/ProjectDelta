import io
import os
from functools import wraps

from flask import Blueprint, render_template, request, jsonify, session, current_app, redirect, url_for, flash

import logging

import requests

from web.auth import Authentication

chat_bp = Blueprint('chat', __name__, url_prefix='/chat')
BACKEND_URL = os.environ.get('BACKEND_URL', 'http://localhost:8080')
CHATS_END_POINT = f"{BACKEND_URL}/message/get_dialogues"
MESSAGES_END_POINT = f"{BACKEND_URL}/message/get_messages"
CREATE_CHAT_END_POINT = f"{BACKEND_URL}/message/create_dialogue"
CREATE_MESSAGE_END_POINT = f"{BACKEND_URL}/message/create_message"


def authentication(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            auth_user: Authentication = Authentication.cookie_auth()
            kwargs['auth'] = auth_user
            return func(*args, **kwargs)
        except Exception as e:
            flash('Please log in', 'danger')
            return redirect(url_for('index'))

    return wrapper


@chat_bp.route('/', methods=['GET'])
@authentication
def chat(auth):
    return render_template('chat.html', title='Chat', **auth.user.layout_kwargs())


@chat_bp.route('/chats', methods=['GET'])
@authentication
def get_chats(auth):
    try:
        response = requests.get(CHATS_END_POINT, headers={
            'accept': 'application/json',
            "Authorization": f"Bearer {auth.get_access_token()}"
        })

        if response.ok:
            data = response.json()
            response_chats = []
            for dialogue in data:
                response_chats.append({
                    'id': dialogue['id'],
                    'name': dialogue['name']
                })
            return jsonify({'chats': response_chats})
    except Exception as e:
        logging.debug(f"Something went wrong: {str(e)}")
        return jsonify({'error': str(e)}), 500


@chat_bp.route('/create', methods=['POST'])
@authentication
def create_chat(auth):
    try:
        data = request.get_json()
        chat_name = data.get('name')
        response = requests.post(CREATE_CHAT_END_POINT, headers={
            'accept': 'application/json',
            'Content-Type': 'application/json',
            "Authorization": f"Bearer {auth.get_access_token()}"
        }, json={
            'name': chat_name
        })

        if response.ok:
            data = response.json()
            return jsonify({'chat_id': data["dialogue_id"]})
        flash('Something went wrong: ' + response.text, 'danger')
        raise response.text
    except Exception as e:
        logging.debug(f"Something went wrong: {str(e)}")
        return jsonify({'error': str(e)}), 500


@chat_bp.route('/messages/<chat_id>', methods=['GET'])
@authentication
def get_messages(auth, chat_id):
    try:
        response = requests.get(MESSAGES_END_POINT, headers={
            'accept': 'application/json',
            'Content-Type': 'application/json',
            "Authorization": f"Bearer {auth.get_access_token()}"
        }, json={
            'dialogue_id': chat_id
        })

        if response.ok:
            messages = response.json()
            response_messages = []
            for message in messages:
                response_messages.append({
                    "id": message['id'],
                    "user_id": 1 if message['sender'] == "USER" else 0,
                    "content": message['text'],

                })
            return jsonify({'messages': response_messages})
        raise response.text
    except Exception as e:
        logging.debug(f"Something went wrong: {str(e)}")
        return jsonify({'error': str(e)}), 500


@chat_bp.route('/messages/<chat_id>', methods=['POST'])
@authentication
def send_message(auth, chat_id):
    try:
        file = request.files['file']
        file_content = file.read()
        message_type = file.content_type
        message_name = file.filename

        file = io.BytesIO(file_content)
        if message_type == 'audio/mpeg':
            file.name = "Запись"
        else:
            file.name = message_name

        form_data = {
            'dialogue_id': str(chat_id)
        }

        files = {'file': (file.name, io.BytesIO(file_content), message_type)}

        response = requests.post(CREATE_MESSAGE_END_POINT, headers={
            'accept': 'application/json',
            'Authorization': f"Bearer {auth.get_access_token()}"
        }, files=files, data=form_data)

        if response.ok:
            response_json = response.json()
            if response_json.get('bot_message') is not None:
                return jsonify({'type': 'text', 'content': response_json['bot_message']})
            elif response_json.get('error') is not None:
                raise Exception(response_json['error'])
            else:
                raise response_json
        else:
            logging.error(
                f"Error during request to bot. Status code: {response.status_code}, Response: {response.text}")
            return jsonify({'error': 'Failed to send message to bot'}), response.status_code

    except Exception as e:
        logging.debug(f"Something went wrong: {str(e)}")
        return jsonify({'error': str(e)}), 500

