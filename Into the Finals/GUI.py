from flask import Flask, jsonify, render_template_string, request

app = Flask(__name__)

# These flags control the drone
yellow_requested = False
land_requested = False

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Drone Control Panel</title>
</head>
<body>
    <h1>Drone Control Panel</h1>
    <form action="/yellow" method="post">
        <button type="submit">YELLOW</button>
    </form>
    <form action="/land" method="post">
        <button type="submit">LAND</button>
    </form>
    <p>Status:</p>
    <ul>
        <li>Yellow: {{ yellow_status }}</li>
        <li>Land: {{ land_status }}</li>
    </ul>
</body>
</html>
"""

@app.route("/")
def index():
    yellow_status = "YELLOW request active" if yellow_requested else "Idle"
    land_status = "LAND request active" if land_requested else "Idle"
    return render_template_string(HTML_TEMPLATE, yellow_status=yellow_status, land_status=land_status)

@app.route("/yellow", methods=["POST"])
def trigger_yellow():
    global yellow_requested
    yellow_requested = True
    return render_template_string(HTML_TEMPLATE, yellow_status="YELLOW request active", land_status="Idle")

@app.route("/land", methods=["POST"])
def trigger_land():
    global land_requested
    land_requested = True
    return render_template_string(HTML_TEMPLATE, yellow_status="Idle", land_status="LAND request active")

@app.route("/yellow_status")
def yellow_status():
    global yellow_requested
    return "YELLOW" if yellow_requested else "IDLE"

@app.route("/land_status")
def land_status():
    global land_requested
    return "LAND" if land_requested else "IDLE"

@app.route("/reset_yellow", methods=["POST"])
def reset_yellow():
    global yellow_requested
    yellow_requested = False
    return "OK"

@app.route("/reset_land", methods=["POST"])
def reset_land():
    global land_requested
    land_requested = False
    return "OK"

if __name__ == "__main__":
    app.run(port=8000, debug=False, host="0.0.0.0")
