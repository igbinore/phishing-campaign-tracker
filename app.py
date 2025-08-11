from flask import Flask, render_template, request, redirect, url_for, jsonify
import json
from pathlib import Path
from uuid import uuid4
from datetime import datetime

app = Flask(__name__)

DATA_PATH = Path(__file__).parent / "data" / "phishing_samples.json"

def load_data():
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_data(data):
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

@app.route("/", methods=["GET"])
def index():
    data = load_data()

    # Filters
    status = request.args.get("status", "").strip()
    q = request.args.get("q", "").strip().lower()
    sort = request.args.get("sort", "").strip()

    if status:
        data = [d for d in data if (d.get("status") or "").lower() == status.lower()]

    if q:
        def matches(item):
            for k in ("sender", "subject", "url", "notes"):
                v = (item.get(k) or "").lower()
                if q in v:
                    return True
            return False
        data = [d for d in data if matches(d)]

    if sort in {"sender", "subject", "status"}:
        data = sorted(data, key=lambda x: (x.get(sort) or "").lower())

    return render_template("index.html", data=data, status=status, q=q, sort=sort)

@app.route("/add", methods=["POST"])
def add_record():
    # Minimal validation
    sender = (request.form.get("sender") or "").strip()
    subject = (request.form.get("subject") or "").strip()
    url = (request.form.get("url") or "").strip()
    status = (request.form.get("status") or "").strip()
    notes = (request.form.get("notes") or "").strip()

    if not (sender and subject and url and status):
        # If anything important is missing, just go back to home
        return redirect(url_for("index"))

    data = load_data()
    data.append({
        "id": str(uuid4()),
        "sender": sender,
        "subject": subject,
        "url": url,
        "status": status,
        "notes": notes,
        "created_at": datetime.utcnow().isoformat() + "Z"
    })
    save_data(data)
    return redirect(url_for("index"))

@app.route("/delete/<item_id>", methods=["POST"])
def delete_record(item_id):
    data = load_data()
    data = [d for d in data if d.get("id") != item_id]
    save_data(data)
    return redirect(url_for("index"))

@app.route("/api/data", methods=["GET"])
def api_data():
    return jsonify(load_data())

if __name__ == "__main__":
    app.run(debug=True)
