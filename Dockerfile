FROM python:3.10-slim

WORKDIR /usr/src/app

RUN apt update

RUN apt install -y git

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH /usr/src/app/EosPayload

CMD [ "python", "-m", "EosPayload", "-o", "eos_artifacts"]
