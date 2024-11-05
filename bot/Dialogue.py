import asyncio
import uuid

from enum import Enum as PyEnum
from functools import wraps
from typing import Callable, Optional


class DialogueTaskDBType(PyEnum):
    CREATE_DIALOGUE = "CREATE_DIALOGUE"
    ADD_MESSAGE = "ADD_MESSAGE"
    UPDATE_MESSAGE = "UPDATE_MESSAGE"


class MessageRole(PyEnum):
    SYSTEM = "SYSTEM"
    USER = "USER"
    BOT = "BOT"


class MessageRoleGPT4FREE(PyEnum):
    USER = "user"


async def some_task(type_task: DialogueTaskDBType):
    print("task run", type_task.value)
    await asyncio.sleep(3)


class DialogueTasksDB(set):

    def __init__(self, db_created=False):
        super().__init__()
        self.db_created = db_created

    @staticmethod
    def with_dialog_created(func: Callable):
        async def wait_add(self, element):
            while self.db_created is False:
                print("wait creation db")
                await asyncio.sleep(0.3)
            return await func(self, element)

        @wraps(func)
        async def wrapper(*args, **kwargs):
            self, element = args[0], args[1]
            if element[0] == DialogueTaskDBType.CREATE_DIALOGUE:
                return await func(*args, **kwargs)
            else:
                if self.db_created:
                    return await func(*args, **kwargs)
                else:
                    task = asyncio.create_task(wait_add(*args, **kwargs))
                    return

        return wrapper

    def __done_callback(self, task):
        if not self.db_created:
            if task.get_name() == DialogueTaskDBType.CREATE_DIALOGUE.value:
                self.db_created = True
        self.remove(task)
        print("done task", task.get_name())

    @with_dialog_created
    async def add(self, __element: (DialogueTaskDBType, Callable)):
        task = asyncio.create_task(__element[1], name=__element[0].value)
        task.add_done_callback(self.__done_callback)
        super().add(task)


class DialogueBase:
    __instance = dict()

    def __init__(self, name, user_id):
        self._messages = []
        self.name: Optional[str] = name
        self.id = None
        self.user_id = user_id
        self.db_tasks = DialogueTasksDB()
        self.db_created = False
        self.__next_message_id = 0

    @property
    def next_message_id(self):
        self.__next_message_id += 1
        return self.__next_message_id

    @property
    def messages(self):
        return self._messages

    @classmethod
    async def create(cls, name, user_id):
        self = cls(name, user_id)
        self.id = uuid.uuid4().hex
        await self.db_tasks.add((DialogueTaskDBType.CREATE_DIALOGUE, some_task(DialogueTaskDBType.CREATE_DIALOGUE)))
        self.__instance[self.id] = self
        return self

    @classmethod
    async def from_id(cls, user_id, dialogue_id):
        dialogue = cls.__instance.get(dialogue_id)
        if dialogue:
            return dialogue
        return cls.create(name=None, user_id=user_id)

    async def __call__(self, role: MessageRole, text=None, audio_request_iterator=None):
        assert sum(
            source is not None for source in [text, audio_request_iterator]
        ) <= 1, 'You must provide only one selected source'

        message_id = self.next_message_id

        await self.db_tasks.add((DialogueTaskDBType.ADD_MESSAGE, some_task(DialogueTaskDBType.ADD_MESSAGE)))

        if text is not None:
            return MessageBase(
                message_id=message_id,
                role=role,
                content=text
            )
        if audio_request_iterator is not None:
            # Обработочку сделать звука
            return MessageBase(
                message_id=self.next_message_id,
                role=role,
                content=audio_request_iterator
            )


class DialogueGPT4FREE(DialogueBase):

    def __init__(self, name, user_id):
        super().__init__(name, user_id)

    async def __call__(self, role: MessageRole, text=None, audio_request_iterator=None):
        message_base: MessageBase = await super().__call__(role, text, audio_request_iterator)
        self.messages.append(MessageGPT4FREE(message_base))

    @property
    def messages(self) -> list:
        return [message() for message in self._messages]


class MessageBase:

    def __init__(self, message_id: int, role: MessageRole, content):
        self.id = message_id
        self.role = role
        self.content = content


class MessageGPT4FREE(MessageBase):

    def __init__(self, message: MessageBase):
        super().__init__(message_id=message.id, role=message.role, content=message.content)
        self.role = MessageRoleGPT4FREE(message.role.name)

    def __call__(self) -> dict:
        return dict(role=self.role, content=self.content)


async def main():
    dialog = await DialogueGPT4FREE.create(name=None, user_id="parket")

    await dialog(MessageRole.USER, "Hello, how are you?")

    while True:
        await asyncio.sleep(0.1)

    # await asyncio.gather(*dialog.db_tasks)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
