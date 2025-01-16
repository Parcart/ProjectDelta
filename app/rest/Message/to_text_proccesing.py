# from yandex.cloud.ai.stt.v3 import stt_pb2
#
# recognize_options = stt_pb2.StreamingOptions(
#         recognition_model=stt_pb2.RecognitionModelOptions(
#             audio_format=stt_pb2.AudioFormatOptions(
#                 raw_audio=stt_pb2.RawAudio(
#                     audio_encoding=stt_pb2.RawAudio.LINEAR16_PCM,
#                     sample_rate_hertz=8000,
#                     audio_channel_count=1
#                 )
#             ),
#             text_normalization=stt_pb2.TextNormalizationOptions(
#                 text_normalization=stt_pb2.TextNormalizationOptions.TEXT_NORMALIZATION_ENABLED,
#                 profanity_filter=True,
#                 literature_text=False
#             ),
#             language_restriction=stt_pb2.LanguageRestrictionOptions(
#                 restriction_type=stt_pb2.LanguageRestrictionOptions.WHITELIST,
#                 language_code=['ru-RU']
#             ),
#             audio_processing_type=stt_pb2.RecognitionModelOptions.REAL_TIME
#         )
#     )