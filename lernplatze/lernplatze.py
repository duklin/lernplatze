import json
import itertools
from urllib.parse import urljoin
from datetime import date, timedelta

from requests import Session
from bs4 import BeautifulSoup

BASE_URL = "https://merry.ulb.uni-bonn.de/mrbs_studyplaces"
AUTH_DATA = {
    "returl": "https://merry.ulb.uni-bonn.de/mrbs_studyplaces/day.php?&returl=https%3A%2F%2Fmerry.ulb.uni-bonn.de%2Fmrbs_studyplaces%2Fday.php&returl=https%3A%2F%2Fmerry.ulb.uni-bonn.de%2Fmrbs_studyplaces%2Fday.php%3F%26returl%3Dhttps%253A%252F%252Fmerry.ulb.uni-bonn.de%252Fmrbs_studyplaces%252Fday.php",
    "TargetURL": "day.php?&returl=https%3A%2F%2Fmerry.ulb.uni-bonn.de%2Fmrbs_studyplaces%2Fday.php&returl=https%3A%2F%2Fmerry.ulb.uni-bonn.de%2Fmrbs_studyplaces%2Fday.php%3F%26returl%3Dhttps%253A%252F%252Fmerry.ulb.uni-bonn.de%252Fmrbs_studyplaces%252Fday.php",
    "Action": "SetName",
}


def collapse_hours(hours: list[int], min_timespan: int) -> list[str]:
    range_list = []
    for _, group in itertools.groupby(enumerate(hours), lambda part: part[1] - part[0]):
        group = list(group)
        low, high = group[0][1], group[-1][1]
        if high - low >= min_timespan:
            range_list.append(f"{low}-{high}")
    return range_list


def auth(username: str, password: str) -> Session:
    AUTH_DATA["NewUserName"] = username
    AUTH_DATA["NewUserPassword"] = password
    sess = Session()
    res = sess.post(urljoin(BASE_URL, "mrbs_studyplaces/admin.php"), data=AUTH_DATA)
    if not res.ok:
        raise Exception(res.text)
    return sess


def get_appointment(sess: Session, html: BeautifulSoup, student_name: str) -> dict:
    me = html.findAll("a", string=student_name, limit=1)
    if me:
        termin_url = urljoin(BASE_URL, f"mrbs_studyplaces/{me[0]['href']}")
        termin_res = sess.get(termin_url)
        if termin_res.ok:
            termin = BeautifulSoup(termin_res.text, "html.parser")
            table = termin.find_all(id="entry", limit=1)[0]
            tds = table.find_all("td")
            place = tds[1].string.split()
            start = tds[3].string
            end = tds[7].string
            return {
                "Place": f"{place[0]} {place[-1]}",
                "Period": f"{start[:2]} - {end[:2]}",
                "Link": termin_url,
            }
    return {}


def get_appointment_for_day(sess: Session, day: date, student_name: str) -> dict:
    params = {"year": day.year, "month": day.month, "day": day.day, "area": 2}
    mnl_res = sess.get(urljoin(BASE_URL, f"mrbs_studyplaces/day.php"), params=params)

    if mnl_res.ok:
        mnl_html = BeautifulSoup(mnl_res.text, "html.parser")
        mnl_app = get_appointment(sess, mnl_html, student_name)
        if mnl_app:
            return mnl_app

    # params = {"year": day.year, "month": day.month, "day": day.day, "area": 1}
    # hb_res = sess.get(urljoin(BASE_URL, f"mrbs_studyplaces/day.php"), params=params)

    # if hb_res.ok:
    #     hb_html = BeautifulSoup(hb_res.text, "html.parser")
    #     hb_app = get_appointment(sess, hb_html, student_name)
    #     if hb_app:
    #         return hb_app

    return {}


def get_slots(html: BeautifulSoup) -> dict:
    until = 21
    min_timespan = 4

    slots = {}

    table = html.find_all(id="day_main", limit=1)[0]
    data = table.contents[2]
    for row in data.contents:
        place = row.find_next("td")
        counter = 10
        free_slots_per_row = {}
        for td in place.find_next_siblings("td"):
            if "I" in td["class"]:
                counter += int(td["colspan"])
            else:
                link = td.find(class_="new_booking")
                free_slots_per_row[counter] = urljoin(
                    BASE_URL, f'mrbs_studyplaces/{link["href"]}'
                )
                counter += 1
            if counter > until:
                break
        if free_slots_per_row:
            collapsed_hours = collapse_hours(
                sorted(free_slots_per_row.keys()), min_timespan
            )
            for r in collapsed_hours:
                begin = r.split("-")[0]
                if r not in slots:
                    slots[r] = [
                        {"Place": place.string, "Link": free_slots_per_row[int(begin)]}
                    ]
                else:
                    slots[r].append(
                        {"Place": place.string, "Link": free_slots_per_row[int(begin)]}
                    )

    return slots


def get_slots_for_day(sess: Session, day: date) -> dict:
    slots = {}

    params = {"year": day.year, "month": day.month, "day": day.day, "area": 2}
    mnl_res = sess.get(urljoin(BASE_URL, f"mrbs_studyplaces/day.php"), params=params)

    if mnl_res.ok:
        mnl_html = BeautifulSoup(mnl_res.text, "html.parser")
        slots["MNL"] = get_slots(mnl_html)

    # params = {"year": day.year, "month": day.month, "day": day.day, "area": 1}
    # hb_res = sess.get(urljoin(BASE_URL, f"mrbs_studyplaces/day.php"), params=params)

    # if hb_res.ok:
    #     hb_html = BeautifulSoup(hb_res.text, "html.parser")
    #     slots["HB"] = get_slots(hb_html)

    return slots
