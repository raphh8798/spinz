import os
from datetime import date

from flask import Flask, g, redirect, jsonify, request, session, url_for
from dotenv import load_dotenv

from db import get_db_connection
import queries


load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")


@app.before_request
def require_login():
    if request.endpoint not in ("login", "static") and "user_id" not in session:
        return jsonify({"error": "login required"}), 401    # Unauthorized


def get_db():
    if "db" not in g:
        g.db = get_db_connection()

    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


@app.route("/api/login", methods=["POST"])
def login():
    db = get_db()
    login_name = request.form.get("name").strip()
    password = request.form.get("password")
    if login_name and password:
        user_id, is_new = queries.get_or_create_user(db.cursor(), login_name, password)
        if user_id is None:
            return jsonify({"error": "비밀번호가 틀렸습니다."}), 401    # Unauthorized
        db.commit()
        session["user_id"] = user_id
        session["user_name"] = login_name
        return jsonify({"user_id": user_id, "user_name": login_name, "is_new": is_new})

    return jsonify({"error": "이름과 비밀번호를 모두 입력해주세요."}), 400  # Bad Request
    

@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"ok": True})


@app.route("/api/me")
def me():
    return jsonify({"user_id": session["user_id"], "user_name": session["user_name"]})


def _parse_month():
    request_month = request.args.get("month")
    if request_month:
        year, month = map(int, request_month.split("-"))
    else:
        today = date.today()
        year, month = today.year, today.month
    return year, month


def _calendar_payload(db, year, month):
    performs = queries.get_calendar_performances(db.cursor(), session["user_id"], year, month)
    by_mt20id = {}

    for row in performs:
        existing = by_mt20id.get(row["mt20id"])
        if existing:
            if row["actor_name"]:
                existing["actor_name"].append(row["actor_name"])
        else:
            row["actor_name"] = [row["actor_name"]] if row["actor_name"] else []
            by_mt20id[row["mt20id"]] = row

    # datetime.date이기 때문에 문자열로 변환
    by_date = {}
    for row in by_mt20id.values():
        d = row["prfpdfrom"].isoformat()
        row["prfpdfrom"] = d
        row["prfpdto"] = row["prfpdto"].isoformat() if row["prfpdto"] else None
        by_date.setdefault(d, []).append(row)

    prev_month = f"{year}-{month-1:02d}" if month > 1 else f"{year-1}-12"
    next_month = f"{year}-{month+1:02d}" if month < 12 else f"{year+1}-01"

    return {"year": year, "month": month, "prev_month": prev_month, "next_month": next_month, "by_date": by_date}


def _actors_payload(db):
    watched_actors = queries.list_watched_actors(db.cursor(), session["user_id"])
    actor_names = [row["actor_name"] for row in watched_actors]
    performs = queries.get_performances_by_actors(db.cursor(), actor_names)
    
    for row in performs:    # datetime.date이기 때문에 문자열로 변환
        row["prfpdfrom"] = row["prfpdfrom"].isoformat() if row["prfpdfrom"] else None
        row["prfpdto"] = row["prfpdto"].isoformat() if row["prfpdto"] else None

    return {"watched_actors": watched_actors, "performs": performs}


@app.route("/api/calendar")
def calendar():
    year, month = _parse_month()
    return jsonify(_calendar_payload(get_db(), year, month))


@app.route("/api/favorite/<mt20id>", methods=["POST"])
def favorite(mt20id):
    db = get_db()
    queries.toggle_favorite(db.cursor(), session["user_id"], mt20id)
    db.commit()

    year, month = _parse_month()
    return jsonify(_calendar_payload(db, year, month))


@app.route("/api/actors", methods=["GET", "POST"])
def actors():
    db = get_db()
    if request.method == "POST":
        queries.add_watched_actor(db.cursor(), session["user_id"], request.form.get("actor_name"))
        db.commit()

    return jsonify(_actors_payload(db))


@app.route("/api/actors/<int:actor_id>/delete", methods=["POST"])
def delete_actor(actor_id):
    db = get_db()
    queries.delete_watched_actor(db.cursor(), session["user_id"], actor_id)
    db.commit()
    return jsonify(_actors_payload(db))



if __name__ == "__main__":
    app.run(debug=True)
