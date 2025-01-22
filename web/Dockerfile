FROM python:3.13.1-bookworm

# install lib required for pyaudio
RUN apt update && apt-get clean && rm -rf /var/lib/apt/lists/*

# update pip to support for whl.metadata -> less downloading
RUN pip install --no-cache-dir -U "pip>=24"

RUN mkdir /web

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
RUN rm requirements.txt

COPY . /web

RUN rm web/main.py

COPY main.py .
WORKDIR /web


CMD python /main.py



