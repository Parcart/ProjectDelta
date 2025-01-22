FROM python:3.13.1-bookworm

RUN apt-get update && apt-get install -y ffmpeg

# install lib required for pyaudio
RUN apt update && apt-get clean && rm -rf /var/lib/apt/lists/*

# update pip to support for whl.metadata -> less downloading
RUN pip install --no-cache-dir -U "pip>=24"

RUN mkdir /telegram_bot

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
RUN rm requirements.txt

COPY .env .

COPY . /telegram_bot

RUN rm telegram_bot/main.py

COPY main.py .
WORKDIR /telegram_bot


CMD python /main.py



