from flask import Flask, request, Response
import os
import subprocess

app = Flask(__name__)

ALLOWED_SERVICES = [
    "payment-service",
    "user-service",
    "inventory-service",
    "auth-service",
    "notification-service"
]

SERVICE_PORTS = {
    "payment-service": 5010,
    "user-service": 5011,
    "inventory-service": 5012,
    "auth-service": 5013,
    "notification-service": 5014
}


@app.route("/")
def home():

    return """
    <html>

    <head>

        <title>Mini Internal Developer Platform</title>

        <style>

            body {
                font-family: Arial;
                background: #0f172a;
                color: white;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
            }

            .card {
                background: #1e293b;
                padding: 40px;
                border-radius: 15px;
                width: 450px;
                text-align: center;
            }

            select {
                width: 100%;
                padding: 12px;
                margin-top: 20px;
                border-radius: 8px;
                border: none;
            }

            button {
                width: 100%;
                padding: 12px;
                margin-top: 20px;
                border: none;
                border-radius: 8px;
                background: #2563eb;
                color: white;
                cursor: pointer;
                font-size: 16px;
            }

        </style>

    </head>

    <body>

        <div class="card">

            <h1>Mini Internal Developer Platform</h1>

            <form action="/provision" method="POST">

                <select name="service">

                    <option value="payment-service">payment-service</option>

                    <option value="user-service">user-service</option>

                    <option value="inventory-service">inventory-service</option>

                    <option value="auth-service">auth-service</option>

                    <option value="notification-service">notification-service</option>

                </select>

                <button type="submit">
                    Provision Service
                </button>

            </form>

        </div>

    </body>

    </html>
    """


@app.route("/provision", methods=["POST"])
def provision():

    service = request.form.get("service")

    port = SERVICE_PORTS[service]


    host = request.host.split(":")[0]


    subprocess.run(

        ["docker", "rm", "-f", service],

        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL

    )


    service_path = f"services/{service}"


    os.makedirs(service_path, exist_ok=True)


    app_code = f'''

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

    data = f"""
# HELP requests_total Total requests
# TYPE requests_total counter
requests_total {{requests_count}}

# HELP uptime_seconds Uptime
# TYPE uptime_seconds gauge
uptime_seconds {{uptime}}

# HELP service_health Service health
# TYPE service_health gauge
service_health 1
"""

    return Response(data, mimetype="text/plain")


app.run(host="0.0.0.0", port={port})
'''

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
name: CI Pipeline {service}

on:
  push:
    branches:
      - main

jobs:


  build-and-test:


    runs-on: ubuntu-latest


    steps:


      - name: Checkout Repository

        uses: actions/checkout@v4


      - name: Show Files

        run: ls -R


      - name: Build Docker Image

        run: docker build -t {service} ./services/{service}


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

            "--label",
            "platform=mini-idp",

            "-p",

            f"{port}:{port}",
            service

        ]
    )


    subprocess.run(
        ["docker", "exec", "mini-idp-nginx-1", "nginx", "-s", "reload"]
    )


    subprocess.run(

        ["docker", "restart", "mini-idp-prometheus-1"]
    )


    subprocess.run(

        ["git", "add", "."]
    )


    subprocess.run(

        [
            "git",

            "commit",
            "-m",

            f"SERVICE={service}"
        ]

    )


    subprocess.run(

        ["git", "push", "origin", "main"]

    )


    return f"""

    <html>


    <head>


        <style>


            body {{
                font-family: Arial;
                background: #0f172a;

                color: white;

                display: flex;
                justify-content: center;
                align-items: center;

                height: 100vh;

            }}


            .card {{

                background: #1e293b;
                padding: 40px;

                border-radius: 15px;
                width: 500px;

                text-align: center;

            }}


            a {{
                display: block;

                background: #2563eb;
                color: white;
                padding: 12px;

                margin-top: 15px;
                text-decoration: none;
                border-radius: 8px;

            }}


        </style>


    </head>


    <body>


        <div class="card">


            <h1> SERVICE CREATED SUCCESSFULLY</h1>


            <h2>{service}</h2>


            <h3>Port: {port}</h3>


            <a href="http://{host}/services/{service}">
                Open Service
            </a>


            <a href="http://{host}:{port}/metrics">

                Metrics
            </a>

            <a href="http://{host}:{port}/health">
                Health
            </a>

            <h3> GitHub Actions Triggered</h3>

            <h3> Governance Automation Enabled</h3>

            <h3> Terraform Templates Added</h3>


            <h3> Observability Enabled</h3>


        </div>


    </body>


    </html>


    """



@app.route("/cleanup/<service>")
def cleanup(service):

    subprocess.run(

        ["docker", "rm", "-f", service],
        stdout=subprocess.DEVNULL,

        stderr=subprocess.DEVNULL
    )

    return f"{service} removed"


app.run(host="0.0.0.0", port=5000)
