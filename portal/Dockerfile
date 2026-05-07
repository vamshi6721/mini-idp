FROM docker:latest

WORKDIR /app

RUN apk add --no-cache python3 py3-pip py3-flask

COPY . .

CMD ["python3", "app.py"]
