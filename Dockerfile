FROM python:3.10-slim

WORKDIR /usr/src/app

RUN apt update
# Dependency for opencv-python (cv2). `import cv2` raises ImportError: libGL.so.1: cannot open shared object file: No such file or directory
# Solution from https://askubuntu.com/a/1015744
RUN apt install -y libgl1-mesa-glx

RUN apt install -y git

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH /usr/src/app/EosPayload

COPY EosPayload ./EosPayload

CMD [ "python", "-m", "EosPayload" ]
