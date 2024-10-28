from google.protobuf import timestamp_pb2

from api.rpc.protos import ChatService_pb2
from db.schema import MessageButton


def assembly_message_response(dialogue_id: int,
                              message_id: int,
                              sender,
                              timestamp,
                              voice_data_id: int | None,
                              sound_wave: str,
                              duration: float,
                              text,
                              translate_text,
                              content_type,
                              buttons: list[MessageButton]) -> ChatService_pb2.Message:
    if content_type == ChatService_pb2.ContentType.VOICE_MESSAGE:
        voice_message_info = ChatService_pb2.VoiceMessageInfo(voice_data_id=voice_data_id,
                                                          sound_wave=sound_wave,
                                                          duration=duration)
    else:
        voice_message_info = None
    buttons_proto = []
    if any(button.is_tapped for button in buttons):
        is_disabled = True
    else:
        is_disabled = False
    for button in buttons:
        buttons_proto.append(ChatService_pb2.ReplyKeyboardButton(button_id=button.id,
                                                                 text=button.text,
                                                                 is_tapped=button.is_tapped,
                                                                 is_disabled=is_disabled))
    content_data = ChatService_pb2.ContentData(voice_info=voice_message_info,
                                               text=text,
                                               translate_text=translate_text,
                                               buttons=buttons_proto)
    content = ChatService_pb2.Content(content_type=content_type, content=content_data)
    timestamp_proto = timestamp_pb2.Timestamp()
    timestamp_proto.FromDatetime(timestamp)
    response_data = ChatService_pb2.Message(dialogue_id=dialogue_id,
                                            message_id=message_id,
                                            sender=sender,
                                            content=content,
                                            timestamp=timestamp_proto)
    return response_data


# def generate_default_answer(self, user_id, dialogue_id):
#     try:
#         cwd = os.getcwd()
#         voice_data_id = uuid.uuid4().hex
#         src = cwd + "\\voice_data\\default_voice_data\\default.ogg"
#         dst = cwd + f"\\voice_data\\{user_id}\\{dialogue_id}\\{voice_data_id}.ogg"
#         shutil.copy(src, dst)
#         # Работа с бд
#         result_VoiceInfo = DAO().DialogueVoice.post(voice_data_id, "89234598234759823457", 15.0)
#         if not result_VoiceInfo:
#             raise BackEndError(grpc.StatusCode.ABORTED, "DBerror: DialogueVoice POST failed")
#         text = "Омг. Я уже ем эти мягкие французские булоки, да выпью чаю!"
#         translate_text = "Omg. I'm already eating these soft French rolls, and I'll have some tea!"
#         message_dialogue = (
#             DAO().DialogueMessage.post(dialogue_id=dialogue_id, content_type=MessageContentType.VOICE_MESSAGE,
#                                        sender=SenderType.BOT,
#                                        voice_info_id=result_VoiceInfo.inserted_primary_key[0],
#                                        text=text,
#                                        translate_text=translate_text))
#         if not result_VoiceInfo:
#             raise BackEndError(grpc.StatusCode.ABORTED, "DBerror: DialogueMessage POST failed")
#         timestamp = timestamp_pb2.Timestamp()
#         timestamp.FromDatetime(datetime.now())
#         # Сборка ответа
#         message_id = message_dialogue.inserted_primary_key[0]
#         response_data = assembly_message_response(dialogue_id=dialogue_id,
#                                                   message_id=message_id,
#                                                   sender=ChatService_pb2.SenderType.BOT, timestamp=timestamp,
#                                                   voice_data_id=voice_data_id,
#                                                   sound_wave="123123123123123123", duration=15.0, text=text,
#                                                   translate_text=translate_text,
#                                                   content_type=ChatService_pb2.ContentType.VOICE_MESSAGE)
#         dialogue_id = int(dialogue_id)
#         find_user = self.new_messages.get(user_id)
#         if not find_user:
#             self.new_messages[user_id] = {dialogue_id: {message_id: response_data}}
#             return
#         find_dialog = find_user.get(dialogue_id)
#         if not find_user:
#             self.new_messages[user_id][dialogue_id] = {message_id: response_data}
#             return
#         self.new_messages[user_id][dialogue_id][message_id] = response_data
#         return
#     except Exception as e:
#         raise e
