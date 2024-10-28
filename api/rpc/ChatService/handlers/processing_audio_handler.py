import asyncio
import enum
import io
import json
import os
import uuid
from dataclasses import dataclass


class AudioProcessing:

    def __init__(self):
        self.input_data = asyncio.Queue()
        self.processed_data = io.BytesIO()

    @staticmethod
    def __get_input_ffmpeg_processor(rate):
        """
        The ffmpeg processor for streaming conversion from pcm s16le to libopus ogg
        :param rate: int - rate of the input audio tts=24к user=16к
        :return: ffmpeg
        """

    @staticmethod
    def __get_output_ffmpeg_processor():
        """
        The ffmpeg processor for streaming conversion from libopus ogg to pcm s16le 24000
        :return:
        """

    def input_audio_process


class AudioConvertingError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code

    def __str__(self):
        return f"AudioConvertingError: code={self.code}, message={self.args[0]}"
