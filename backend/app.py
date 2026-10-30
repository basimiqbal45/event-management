import os, time, pymysql
from flask import Flask, request, jsonify

app = Flask(__name__)

def db():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "event-db"),
        user=os.getenv("DB_USER", "eventuser"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "eventsdb"),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )

def init_db():
    for _ in range(40):
        try:
            c = db()
            c.cursor().execute(
                "CREATE TABLE IF NOT EXISTS events ("
                "id INT AUTO_INCREMENT PRIMARY KEY,"
                "title VARCHAR(120) NOT NULL,"
                "event_date DATE NOT NULL,"
                "location VARCHAR(120),"
                "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
            c.close()
            return
        except Exception as e:
            print("waiting for database:", e, flush=True)
            time.sleep(5)

init_db()

@app.get("/api/health")
def health():
    try:
        c = db(); c.cursor().execute("SELECT 1"); c.close()
        return jsonify(status="ok", database="up")
    except Exception as e:
        return jsonify(status="error", database=str(e)), 500

@app.get("/api/events")
def list_events():
    c = db(); cur = c.cursor()
    cur.execute("SELECT id, title, DATE_FORMAT(event_date,'%Y-%m-%d') AS event_date, location FROM events ORDER BY event_date")
    rows = cur.fetchall(); c.close()
    return jsonify(rows)

@app.post("/api/events")
def add_event():
    d = request.get_json(force=True)
    if not d.get("title") or not d.get("event_date"):
        return jsonify(error="title and event_date required"), 400
    c = db()
    c.cursor().execute("INSERT INTO events (title, event_date, location) VALUES (%s,%s,%s)",
                       (d["title"], d["event_date"], d.get("location", "")))
    c.close()
    return jsonify(message="created"), 201

@app.delete("/api/events/<int:eid>")
def delete_event(eid):
    c = db(); c.cursor().execute("DELETE FROM events WHERE id=%s", (eid,)); c.close()
    return jsonify(message="deleted")
