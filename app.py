import os
from flask import Flask, render_template
from lernplatze import auth, get_appointment_for_day, get_slots_for_day
from datetime import date, timedelta
import pickle
from requests.exceptions import ConnectionError

app = Flask(__name__)

USERNAME = os.getenv("LERNPLATZE_USERNAME")
PASSWORD = os.getenv("LERNPLATZE_PASSWORD")
STUDENT_NAME = os.getenv("LERNPLATZE_STUDENT_NAME")


@app.route("/")
def get_weekly_appointments():
    try:
        sess = auth(USERNAME, PASSWORD)
    except ConnectionError:
        with open("days.pkl", "rb") as fin:
            days = pickle.load(fin)
            cached = True
    else:
        days = {}
        for day in [date.today() + timedelta(i) for i in range(8)]:
            days[day] = get_appointment_for_day(sess, day, STUDENT_NAME)
        with open("days.pkl", "wb") as fout:
            pickle.dump(days, fout)
        cached = False
    return render_template("index.jinja", days=days, cached=cached)


@app.route("/day/<day>")
def get_daily_slots(day: str):
    sess = auth(USERNAME, PASSWORD)
    day = date.fromisoformat(day)
    slots = get_slots_for_day(sess, day)
    return render_template("day.jinja", slots=slots, day=day)
