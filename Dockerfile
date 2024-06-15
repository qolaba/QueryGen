FROM python:3.11.9

RUN apt-get update && apt-get install ffmpeg libsm6 libxext6 supervisor -y

RUN apt install lsb-release curl gpg -y

RUN apt-get update

RUN mkdir /root/app

WORKDIR /root/app

ADD ./ /root/app

RUN pip install -r requirements.txt

ENTRYPOINT ["python", "main.py"]
