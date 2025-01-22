FROM python:3.13.1-bookworm

# install lib required for pyaudio
RUN apt update && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y ffmpeg

# update pip to support for whl.metadata -> less downloading
RUN pip install --no-cache-dir -U "pip>=24"

RUN mkdir /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
RUN rm requirements.txt

COPY . /app

RUN rm app/main.py

COPY main.py .
WORKDIR /app


CMD python /main.py



