import asyncio
import io
from typing import AsyncIterator

from api.rpc.ChatService.handlers.auth_handler import authorization
from api.rpc.protos import ChatService_pb2, ChatService_pb2_grpc


class UserSession:
    """
    The class is used to create a user connection session to the rpc messageStream.
    It is used to send new messages for the user.
    """

    def __init__(self, user_id: str):
        """
        Initialization of the session and placing it in the list of active sessions
        """
        self.user_id = user_id
        self.messages = asyncio.Queue()
        ChatService.active_users[user_id] = self

    @staticmethod
    async def queue_iterator(queue):
        """
        Creation an async iterator from the queue
        :param queue: asyncio.Queue[ChatService_pb2.Message] - queue with messages to be sent to the user
        :return: yield ChatService_pb2.Message - rpc Message
        """
        while True:
            value = await queue.get()
            yield value

    async def delete(self):
        """
        Deleting the session from the list of active sessions
        """
        ChatService.active_users.delete_session(self.user_id, self)

    async def send_message(self, message: ChatService_pb2.Message):
        """
        Adding message to queue
        :param message: RPC object with message that will be added for sending (ChatService_pb2.Message)
        :return:
        """
        message.user_id = self.user_id
        self.messages.put_nowait(message)

    async def listen_messages(self) -> AsyncIterator[ChatService_pb2.Message]:
        """
        Function returns the messages to be sent for the current connection
        :return: yield Message (AsyncIterator[ChatService_pb2.Message])
        """
        async for message in self.queue_iterator(self.messages):
            yield message
            self.messages.task_done()


class ActiveSessions(dict):
    """
    A dictionary that implements handling of all user sessions \n
    key: str - user identifier \n
    value: list(UserSession) - list of active sessions for a user

    Allows a user to use multiple devices and implements messaging for all user connections.
    Deletes the session when the user disconnects from message listening
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __setitem__(self, key: str, value: UserSession):
        """
        Add session to the session list
        :param key: user identifier (str)
        :param value: new user session (UserSession)
        :return:
        """
        self.setdefault(key, []).append(value)

    def delete_session(self, user_id, session: UserSession):
        """
        Remove session from the session list
        :param user_id: str - user identifier
        :param session: UserSession - the session to be removed
        :return:
        """
        sessions = self[user_id]
        sessions.remove(session)

    async def send_message(self, user_id: str, message: ChatService_pb2.Message):
        """
        Adding a message to be sent in all active sessions
        :param user_id:
        :param message:
        :return:
        """
        for session in self.get(user_id, []):
            await session.send_message(message)


class ChatService(ChatService_pb2_grpc.GigaChatServiceServicer):
    """
    RPC service
    """
    active_users = ActiveSessions()

    @authorization
    async def messageStream(self, request, context, current_user):
        """
        Method for receiving messages for current user session

        The function creates the current session and places it in the list of active sessions.
        Expects a message for the current session and sends it to the user
        :param current_user: User object that will return @authorization
        :param request:
        :param context:
        :return: yield ChatService_pb2.Message
        """

    @authorization
    async def uploadVoiceMessage(self, request_iterator, context, current_user):
        # docs in proto
        pass

    @authorization
    async def downloadVoiceMessage(self, request, context, current_user):
        # docs in proto
        pass

    @authorization
    async def createNewDialogue(self, request, context, current_user):
        # docs in proto
        pass

    @authorization
    async def sendEvent(self, request, context, current_user):
        # docs in proto
        pass
