from flask import Flask, jsonify, render_template_string, request

app = Flask(__name__)

# This flag tells the drone whether it should land.
land_requested = False

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Drone Control Panel</title>
</head>
<body>
    <h1>Drone Control Panel</h1>
    <form action="/land" method="post">
        <button type="submit">Land</button>
    </form>
    <p>Status: {{ status }}</p>
</body>
</html>
"""

@app.route("/")
def index():
    status = "LAND request active" if land_requested else "Idle"
    return render_template_string(HTML_TEMPLATE, status=status)

@app.route("/land", methods=["POST"])
def trigger_land():
    global land_requested
    land_requested = True
    return render_template_string(HTML_TEMPLATE, status="LAND request active")

@app.route("/land_status")
def land_status():
    global land_requested
    if land_requested:
        return "LAND"
    else:
        return "IDLE"

@app.route("/reset_land", methods=["POST"])
def reset_land():
    global land_requested
    land_requested = False
    return "OK"

if __name__ == "__main__":
    app.run(port=8000, debug=False, host="0.0.0.0")
