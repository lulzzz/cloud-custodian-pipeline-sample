FROM python:3.6-slim

WORKDIR /install
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY src/setup/ ./

CMD ["python", "-u", "main.py"]
