FROM ubuntu:latest

WORKDIR /app

RUN mkdir /data
COPY data /data

RUN mkdir /app/scripts
COPY --chmod=755 scripts /app/scripts
RUN chmod +x /app/scripts/*.sh

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-setuptools \
    python3-wheel \
    python3-venv \
    nodejs \
    npm \
    jq

RUN npx -v

WORKDIR /app

COPY requirements.txt requirements.txt
RUN python3 -m venv venv && \
    . venv/bin/activate && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["venv/bin/python", "app.py"]