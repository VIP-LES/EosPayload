FROM thomasmholder/eos-base

WORKDIR /usr/src/app

RUN apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get update --allow-releaseinfo-change \
    && apt-get install -y --fix-missing libgl1-mesa-glx git build-essential

RUN pip install --no-cache-dir --upgrade pip setuptools wheel

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Docker compose mounts EosPayload into this directory
ENV PYTHONPATH /usr/src/app/EosPayload

CMD [ "python", "-m", "EosPayload", "-o", "eos_artifacts", "-c", "config.json"]
