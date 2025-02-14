FROM python:3.11-slim-buster

WORKDIR /app

RUN mkdir /data  
COPY data /data

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "app.py"]