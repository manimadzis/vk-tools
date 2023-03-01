import http
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Sequence

import requests


class HashableDict(dict):
    def __hash__(self):
        return hash(frozenset(self.keys()))


def clear_empty(d: dict) -> None:
    for key in tuple(d.keys()):
        if d[key] in ("", [], {}, None, 0) and d[key] is not False:
            del d[key]


def dict_exclude(d: dict, fields: Sequence[str]) -> None:
    for key in [key for key in d if key in fields]:
        del d[key]


def human_readable_group(d: dict) -> None:
    if d.get("photo_50"):
        del d["photo_50"]
    if d.get("photo_100"):
        del d["photo_100"]
    if d.get("photo_200"):
        del d["photo_200"]
    if d.get("country"):
        d["country"] = d["country"]["title"]

    if d.get("city"):
        d["city"] = d["city"]["title"]


def human_readable_sub(d: dict) -> None:
    if d.get("photo_50"):
        del d["photo_50"]
    if d.get("photo_100"):
        del d["photo_100"]
    if d.get("photo_200"):
        del d["photo_200"]

    if d.get("country"):
        d["country"] = d["country"]["title"]

    if d.get("city"):
        d["city"] = d["city"]["title"]


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
                "name": school.get("name"),
                "year_from": school.get("year_from"),
                "year_to": school.get("year_to"),
            })

    if d.get("universities"):
        universities = d["universities"]
        d["universities"] = []
        for university in universities:
            d["universities"].append({
                "name": university.get("name"),
                "graduation": university.get("graduation")
            })
            if university.get("faculty_name"):
                d["universities"][-1]["faculty_name"] = university["faculty_name"]


def download(url: str, path: str) -> bool:
    response = requests.get(url, stream=True)
    with open(path, "wb") as f:
        for chunk in response.iter_content(chunk_size=64 * 2 ** 20):
            f.write(chunk)
    return response.status_code == http.HTTPStatus.OK


def save_pictures(vkapi, user_id, path):
    def save_pic(url):
        name = url.split("/")[-1].split("?")[0] + ".jpg"
        result = download(url, name)
        if result:
            print(f"Скачал: {url}")
        else:
            print(f"Загрузка провалилась: {url}")
        return result

    if path is None:
        path = user_id

    urls = vkapi.get_urls_of_all_photos(user_id)
    if not os.path.exists(path):
        os.makedirs(path)
    os.chdir(path)
    with ThreadPoolExecutor(max_workers=4) as ex:
        results = ex.map(save_pic, urls)
    os.chdir("../")

    if not all(results):
        print("Скачаны не все файлы. Смотреть в логах сверху")
    print("Все скачано")
