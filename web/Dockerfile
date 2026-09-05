FROM python:3.14-slim

WORKDIR /home/myapp

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY templates ./templates
COPY static ./static

EXPOSE 8080

CMD ["python", "app.py"]
