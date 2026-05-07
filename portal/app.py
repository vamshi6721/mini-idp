from flask import Flask, request, Response
import os
import subprocess
import socket

app = Flask(__name__)

BASE_PORT = 5010


def get_free_port():

    port = BASE_PORT

    while True:

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        result = s.connect_ex(("localhost", port))

        s.close()

        if result != 0:
            return port

        port += 1


@app.route("/")
def home():

    return """
    <h1>Mini Internal Developer Platform</h1>

    <h3>Select Service</h3>

    <form action="/provision" method="post">

        <select name="service">

            <option>payment-service</option>
            <option>user-service</option>
            <option>inventory-service</option>
            <option>auth-service</option>
            <option>notification-service</option>

        </select>

        <br><br>

        <button type="submit">
            Provision Service
        </button>

    </form>
    """


@app.route("/provision", methods=["POST"])
def provision():

    service = request.form["service"]

    host = request.host.split(":")[0]

    subprocess.run(
        ["docker", "rm", "-f", service],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    port = get_free_port()

    service_path = f"services/{service}"

    os.makedirs(service_path, exist_ok=True)

    app_code = f"""
from flask import Flask, Response
import time

app = Flask(__name__)

requests_count = 0

start_time = time.time()


@app.route("/")
def home():

    global requests_count

    requests_count += 1

    return "{service} running"


@app.route("/health")
def health():

    return "UP"


@app.route("/metrics")
def metrics():

    uptime = int(time.time() - start_time)

    data = f'''
# HELP requests_total Total requests
# TYPE requests_total counter
requests_total {{requests_count}}

# HELP uptime_seconds Service uptime
# TYPE uptime_seconds gauge
uptime_seconds {{uptime}}

# HELP service_health Service health
# TYPE service_health gauge
service_health 1
'''

    return Response(data, mimetype="text/plain")


app.run(host="0.0.0.0", port={port})
"""

    with open(f"{service_path}/app.py", "w") as f:
        f.write(app_code)

    with open(f"{service_path}/requirements.txt", "w") as f:
        f.write("flask")

    dockerfile = """
FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

CMD ["python", "app.py"]
"""

    with open(f"{service_path}/Dockerfile", "w") as f:
        f.write(dockerfile)

    github_dir = f"{service_path}/.github/workflows"

    os.makedirs(github_dir, exist_ok=True)

    github_actions = f"""
name: Deploy {service}

on:
  push:
    branches:
      - main

jobs:

  build-and-deploy:

    runs-on: ubuntu-latest

    steps:

      - name: Checkout Repository
        uses: actions/checkout@v4

      - name: Build Docker Image
        run: docker build -t {service} .

      - name: Verify Docker Images
        run: docker images
"""

    with open(f"{github_dir}/deploy.yml", "w") as f:

        f.write(github_actions)


    subprocess.run(

        ["docker", "build", "-t", service, service_path]

    )


    subprocess.run(
        [

            "docker",
            "run",

            "-d",
            "--name",

            service,
            "-p",

            f"{port}:{port}",
            service

        ]
    )


    nginx_route = f"""


location /services/{service} {{


    proxy_pass http://172.17.0.1:{port};

}}


"""


    with open("gateway/dynamic.conf", "a") as f:
        f.write(nginx_route)


    prometheus_job = f"""


  - job_name: "{service}"


    static_configs:

      - targets: ["172.17.0.1:{port}"]

"""

    with open("monitoring/prometheus.yml", "a") as f:
        f.write(prometheus_job)

    return f"""
    <h1>SERVICE CREATED SUCCESSFULLY</h1>

    <p>Service: {service}</p>

    <p>Port: {port}</p>

    <p>
    <a href="http://{host}/services/{service}">
    Open Service
    </a>
    </p>

    <p>
    <a href="http://{host}:{port}/metrics">
    Metrics
    </a>
    </p>

    <p>
    <a href="http://{host}:{port}/health">

    Health
    </a>

    </p>


    <h3>CI/CD Pipeline Generated</h3>


    <p>
    .github/workflows/deploy.yml

    </p>


    <pre>

docker exec mini-idp-nginx-1 nginx -s reload


docker restart mini-idp-prometheus-1

    </pre>
    """



app.run(host="0.0.0.0", port=5000)
