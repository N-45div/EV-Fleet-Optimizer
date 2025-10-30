import os
import requests
from flask import Flask, request, jsonify, render_template

AGENT_URL = os.getenv("AGENT_URL", "http://127.0.0.1:8000")

app = Flask(__name__, template_folder="templates", static_folder="static")


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/status")
def api_status():
    try:
        r = requests.get(f"{AGENT_URL}/status", timeout=15)
        return jsonify(r.json()), r.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.post("/api/optimize")
def api_optimize():
    try:
        payload = request.get_json(force=True) or {}
        r = requests.post(f"{AGENT_URL}/optimize", json=payload, timeout=60)
        return jsonify(r.json()), r.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.post("/api/compare")
def api_compare():
    try:
        payload = request.get_json(force=True) or {}
        r = requests.post(f"{AGENT_URL}/compare", json=payload, timeout=60)
        return jsonify(r.json()), r.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.post("/api/whatif/site_peak")
def api_site_peak():
    try:
        payload = request.get_json(force=True) or {}
        r = requests.post(f"{AGENT_URL}/whatif/site_peak", json=payload, timeout=30)
        return jsonify(r.json()), r.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.post("/api/whatif/blackout")
def api_blackout():
    try:
        payload = request.get_json(force=True) or {}
        r = requests.post(f"{AGENT_URL}/whatif/blackout", json=payload, timeout=30)
        return jsonify(r.json()), r.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.getenv("FRONTEND_PORT", "5000"))
    app.run(host="127.0.0.1", port=port, debug=True)
