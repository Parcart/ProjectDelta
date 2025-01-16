import json

from app.rest.Dialogue.entity import DialoguesResponse, DialogueMode, \
    DialogueCreateResponse
from app.rest.User.entity import User


def get_mode(mode) -> str:
    mode = json.loads(mode)
    if mode["mode"] == "onboarding":
        return "Знакомство"
    elif mode["mode"] == "train_rule":
        return "Изучение правила"
    elif mode["mode"] == "train_mistake":
        return "Отработка ошибки"
    elif mode["mode"] == "free_communication":
        if mode["mistakes"]:
            return "Обучение"
        else:
            return "Свободное общение"
    return ""


async def get_dialogues(current_user: User) -> DialoguesResponse:
    pass


async def dialogue_create_handler(user_id: str, name: str, mode: DialogueMode) -> DialogueCreateResponse | bool:
    pass




