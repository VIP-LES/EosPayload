FROM thomasmholder/eos-base

WORKDIR /usr/src/app

RUN apt-get update

RUN apt-get install -y libgl1-mesa-glx git

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Docker compose mounts EosPayload into this directory
ENV PYTHONPATH /usr/src/app/EosPayload

CMD [ "python", "-m", "EosPayload", "-o", "eos_artifacts", "-c", "config.json"]
