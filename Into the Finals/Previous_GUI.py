from flask import Flask, jsonify, render_template_string, request

app = Flask(__name__)

# This flag tells the drone whether it should land.
yellow_requested = False

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
    <p>Status: {{ status }}</p>
</body>
</html>
"""

@app.route("/")
def index():
    status = "YELLOW request active" if yellow_requested else "Idle"
    return render_template_string(HTML_TEMPLATE, status=status)

@app.route("/yellow", methods=["POST"])
def trigger_yellow():
    global yellow_requested
    yellow_requested = True
    return render_template_string(HTML_TEMPLATE, status="YELLOW request active")

@app.route("/yellow_status")
def yellow_status():
    global yellow_requested
    if yellow_requested:
        return "YELLOW"
    else:
        return "IDLE"

@app.route("/reset_yellow", methods=["POST"])
def reset_yellow():
    global yellow_requested
    yellow_requested = False
    return "OK"

if __name__ == "__main__":
    app.run(port=8000, debug=False, host="0.0.0.0")
