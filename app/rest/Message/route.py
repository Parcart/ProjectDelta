# import grpc
import asyncio
import datetime
import json
import math
import re
import uuid
from asyncio.subprocess import Process
from typing import Annotated, Optional

import aio_pika
import numpy as np

from fastapi import UploadFile
from fastapi.params import Depends
from starlette import status
from starlette.exceptions import HTTPException

from ..CustomAPIRouter import APIRouter
from app.db.schema import User as UserSchema
from ...jwt_auth.auth_jwt import get_current_active_user


class RabbitMQManager:
    def __init__(self, rabbitmq_host="localhost", rabbitmq_port=5672, rabbitmq_user="guest", rabbitmq_password="guest"):
        self.rabbitmq_host = rabbitmq_host
        self.rabbitmq_port = rabbitmq_port
        self.rabbitmq_user = rabbitmq_user
        self.rabbitmq_password = rabbitmq_password
        self.connection = None
        self.channel = None
        self.callback_queue = None
        self.futures = {}

    async def connect(self):
        self.connection = await aio_pika.connect_robust(
            host=self.rabbitmq_host,
            port=self.rabbitmq_port,
            login=self.rabbitmq_user,
            password=self.rabbitmq_password
        )

        self.channel = await self.connection.channel()
        # Создаем временную очередь для ответов
        result = await self.channel.declare_queue(name='', exclusive=True)
        self.callback_queue = result.name
        await result.consume(self.on_response)

    async def close(self):
        if self.channel:
            await self.channel.close()
        if self.connection:
            await self.connection.close()

    async def on_response(self, message: aio_pika.IncomingMessage):
        async with message.process():
            correlation_id = message.correlation_id
            if correlation_id and correlation_id in self.futures:
                future = self.futures.pop(correlation_id)
                data = json.loads(message.body)
                future.set_result(data)

    async def send_and_wait_for_response(self, audio_bytes: bytes, routing_key='audio_queue') -> Optional[dict]:
        try:
            future = asyncio.get_running_loop().create_future()
            correlation_id = str(uuid.uuid4())

            self.futures[correlation_id] = future

            await self.channel.default_exchange.publish(
                aio_pika.Message(
                    body=audio_bytes,
                    correlation_id=correlation_id,
                    reply_to=self.callback_queue,
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                ),
                routing_key=routing_key
            )

            print(f"Audio message sent with correlation_id: {correlation_id}, waiting for response...")
            return await future

        except Exception as e:
            print(f"Failed to send message or get a response from RabbitMQ: {e}")
            return None


class AudioProcessor:
    @staticmethod
    def process_file_to_pcm():
        return asyncio.create_subprocess_exec(
            'ffmpeg',
            '-i', 'pipe:0',
            '-acodec', 'pcm_s16le',
            '-ar', '16000',
            '-ac', '1',
            '-vn',
            '-y',
            '-f', 's16le',
            "-",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

    @staticmethod
    async def convert(content: bytes, process: Process) -> (bytes, float):
        stdout, stderr = await process.communicate(input=content)
        match = re.search(b"time=(\\d{2}:\\d{2}:\\d{2}.\\d{2})", stderr)
        time_str = match.group(1).decode()
        hours, minutes, seconds = map(float, time_str.split(':'))
        timedelta_obj = datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds)
        total_seconds = int(math.floor(timedelta_obj.total_seconds()))

        return stdout, total_seconds


class Message:
    rabbit_mq_manager: RabbitMQManager = None

    def __init__(self):
        self.route = APIRouter(prefix="/", tags=["transcribe"])
        self.route.add_api_route("/transcribe", self.transcribe, methods=["POST"])

    async def transcribe(self, current_user: Annotated[UserSchema, Depends(get_current_active_user)],
                         file: UploadFile):
        duration = None
        if not (file.filename == 'NOPROCESS'):
            file_data, duration = await AudioProcessor.convert(await file.read(),
                                                               await AudioProcessor.process_file_to_pcm())
        else:
            file_data = await file.read()

        raw_data = np.frombuffer(buffer=file_data, dtype=np.int16)
        audio_array = raw_data.astype(np.float32) / 32768.0
        audio_bytes = audio_array.tobytes()
        if duration is None:
            duration = audio_array.shape[0] / 16000

        if current_user.balance.voice_seconds < duration:
            return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Недостаточно средств")

        result = await self.rabbit_mq_manager.send_and_wait_for_response(audio_bytes)

        if result.get("result"):
            return result
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.get("error"))

#     @staticmethod
#     async def websocket_endpoint(websocket: WebSocket):
#         await websocket.accept()
#         try:
#             stream = StreamingSpeechRecognition()
#             current = None
#             while True:
#                 data = await websocket.receive_bytes()
#                 if data == b"finished":
#                     if current:
#                         print(current)
#                     await websocket.send_bytes(b"oke")
#                 current = await stream.add_data(data)
#                 print(data)
#         except WebSocketDisconnect:
#             pass
#         finally:
#             print("closing")
#
#
# class StreamingSpeechRecognition:
#     secret = "AQVN03o7YGCqC-Ye0mrk3m03rNRE_GNOmZ0Z8cji"
#
#     def __init__(self):
#         self.data: list[bytes] = []
#         self.result: str = ""
#         self.cred = grpc.ssl_channel_credentials()
#         self.channel = grpc.secure_channel('stt.api.cloud.yandex.net:443', self.cred)
#         self.stub = stt_service_pb2_grpc.RecognizerStub(self.channel)
#         response = self.send_settings()
#         print("Отправка настроек")
#         self.read_response(response)
#         print("---------------------------------------------")
#
#     async def add_data(self, data: bytes):
#         self.data.append(data)
#         response = self.send_data(data)
#         return self.read_response(response)
#
#     def send_settings(self):
#         return self.stub.RecognizeStreaming(stt_pb2.StreamingRequest(session_options=recognize_options), metadata=(
#             ('authorization', f'Api-Key {self.secret}'),
#         ))
#
#     def send_data(self, data: bytes):
#         # Отправьте данные для распознавания.
#         return self.stub.RecognizeStreaming(
#             stt_pb2.StreamingRequest(chunk=stt_pb2.AudioChunk(data=data)), metadata=(
#                 # Параметры для аутентификации с API-ключом от имени сервисного аккаунта
#                 ('authorization', f'Api-Key {self.secret}'),
#             ))
#
#     @staticmethod
#     def read_response(response):
#         try:
#             for r in response:
#                 event_type, alternatives = r.WhichOneof('Event'), None
#                 if event_type == 'partial' and len(r.partial.alternatives) > 0:
#                     alternatives = [a.text for a in r.partial.alternatives]
#                 if event_type == 'final':
#                     alternatives = [a.text for a in r.final.alternatives]
#                 if event_type == 'final_refinement':
#                     alternatives = [a.text for a in r.final_refinement.normalized_text.alternatives]
#                 print(f'type={event_type}, alternatives={alternatives}')
#                 return alternatives
#         except grpc._channel._Rendezvous as err:
#             print(f'Error code {err._state.code}, message: {err._state.details}')
