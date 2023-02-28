from datetime import datetime


def clear_empty(d: dict) -> None:
    for key in tuple(d.keys()):
        if d[key] in ("", [], {}, None, 0) and d[key] is not False:
            del d[key]


def human_readable_user(d: dict) -> None:
    clear_empty(d)

    if d.get("country"):
        d["country"] = d["country"]["title"]

    if d.get("city"):
        d["city"] = d["city"]["title"]

    if d.get("last_seen"):
        d["last_seen"] = datetime.fromtimestamp(d["last_seen"]["time"]).isoformat()

    if d.get("sex"):
        d["sex"] = "муж" if d["sex"] == 2 else "жен"

    if d.get("schools"):
        schools = d["schools"]
        d["schools"] = []
        for school in schools:
            d["schools"].append({
                "name": school["name"],
                "year_from": school["year_from"],
                "year_to": school["year_to"],
            })

    if d.get("universities"):
        universities = d["universities"]
        d["universities"] = []
        for university in universities:
            d["university"].append({
                "name": university["name"],
                "graduation": university["graduation"]
            })
            if university.get("faculty_name"):
                d["university"][-1]["faculty_name"] = university["faculty_name"]


