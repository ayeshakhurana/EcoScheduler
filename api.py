# api.py
from flask import Flask, jsonify
import sqlite3

app = Flask(__name__)

def fetch(q, args=()):
    conn = sqlite3.connect("ecoscheduler.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(q, args)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

@app.route("/api/logs")
def logs():
    return jsonify(fetch("SELECT * FROM logs ORDER BY id DESC LIMIT 200"))

if __name__ == "__main__":
    app.run(port=5000, debug=True)
