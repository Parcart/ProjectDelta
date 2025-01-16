import asyncio
import threading
import time
from queue import Queue
from threading import Lock

from telebot import BaseMiddleware, ContinueHandling, SkipHandler
from telebot.types import Message

from telegram_bot.User import User, StopProcessingError, Singleton


# You can use this classes for cancelling update or skipping handler:
# from telebot.handler_backends import CancelUpdate, SkipHandler


class Middleware(BaseMiddleware):
    active_tasks = []
    block_queue = False

    def __init__(self):
        super().__init__()
        self.update_types = ['message', 'callback_query']

    def pre_process(self, message, data):
        while True:
            if message.from_user.id in self.active_tasks or self.block_queue:
                continue
            try:
                self.active_tasks.append(message.from_user.id)
                if isinstance(message, Message) and message.content_type == "text":
                    if message.text.startswith('/start'):
                        Singleton.remove_instance(**message.from_user.to_dict())
                user = User(**message.from_user.to_dict())
                if isinstance(user.status, type(StopProcessingError)):
                    user.status = None
                    return SkipHandler()
                data["user"] = user
            finally:
                self.active_tasks.remove(message.from_user.id)
            break

    def post_process(self, message, data, exception=None):
        if exception:
            if not isinstance(exception, StopProcessingError):
                data["user"].error(message)
                print(exception)
