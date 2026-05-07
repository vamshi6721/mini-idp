
from flask import Flask, Response
import time

app = Flask(__name__)

requests_count = 0

start_time = time.time()


@app.route("/")
def home():

    global requests_count

    requests_count += 1

    return "payment-service running"


@app.route("/health")
def health():

    return "UP"


@app.route("/metrics")
def metrics():

    uptime = int(time.time() - start_time)

    data = f'''
# HELP requests_total Total requests
# TYPE requests_total counter
requests_total {requests_count}

# HELP uptime_seconds Service uptime
# TYPE uptime_seconds gauge
uptime_seconds {uptime}

# HELP service_health Service health
# TYPE service_health gauge
service_health 1
'''

    return Response(data, mimetype="text/plain")


app.run(host="0.0.0.0", port=5014)
