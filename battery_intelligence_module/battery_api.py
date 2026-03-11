from flask import Flask, jsonify, Response
import random
import json
import time
from battery_report import get_battery_report

app = Flask(__name__)


# -------------------------------
# Endpoint 1: Single Battery Status
# -------------------------------
@app.route("/battery_status", methods=["GET"])
def battery_status():

    soc = random.randint(20, 100)

    drain_rate = random.choice([
        "slow",
        "moderate",
        "fast"
    ])

    drop_percent = random.choice([
        0,
        2,
        4,
        6,
        10
    ])

    repeated = random.choice([
        True,
        False
    ])

    report = get_battery_report(
        soc,
        drain_rate,
        drop_percent,
        repeated
    )

    return jsonify(report)


# -------------------------------
# Endpoint 2: Real-Time Battery Stream
# -------------------------------
@app.route("/battery_stream")
def battery_stream():

    def generate_stream():
        while True:

            soc = random.randint(20, 100)

            drain_rate = random.choice([
                "slow",
                "moderate",
                "fast"
            ])

            drop_percent = random.choice([
                0,
                2,
                4,
                6,
                10
            ])

            repeated = random.choice([
                True,
                False
            ])

            report = get_battery_report(
                soc,
                drain_rate,
                drop_percent,
                repeated
            )

            yield f"data:{json.dumps(report)}\n\n"

            time.sleep(3)

    return Response(generate_stream(), mimetype="text/event-stream")


# -------------------------------
# Run Flask Server
# -------------------------------
if __name__ == "__main__":
    app.run(debug=True)