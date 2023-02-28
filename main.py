import http
import json
import os
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from typing import Sequence, List

import click
import requests

from utils import *
from vk_api import VkAPI

vkapi = VkAPI(os.environ["VK_TOKEN"])

exclude_fields = [
    "track_code",
    "lists"
]

friends_get_fields = [
    "bdate",
    "can_post",
    "can_see_all_posts",
    "can_write_private_message",
    "city",
    "contacts",
    "country",
    "domain",
    "education",
    "has_mobile",
    "timezone",
    "last_seen",
    "nickname",
    "online",
    "photo_100",
    "photo_200_orig",
    "photo_50",
    "relation",
    "sex",
    "schools",
    "status",
    "universities"
]

friends_get_default_fields = [
    "bdate",
    "city",
    "contacts",
    "country",
    "domain",
    "education",
    "last_seen",
    "relation",
    "sex",
    "status",
    "schools",
    "universities"
]


def dict_exclude(d: dict, fields: Sequence[str]) -> dict:
    return {x: d[x] for x in d if x not in fields}


def list_dict_exclude(ds: Sequence[dict], fields: Sequence[str]) -> List[dict]:
    return list(dict_exclude(d, fields) for d in ds)


@click.group()
def cli():
    pass


@cli.command(name="friends")
@click.option('-I', '--id-only', help="Список только идентификаторов", is_flag=True, flag_value=True)
@click.option('-f', '--fields', help="Список параметров", default=",".join(friends_get_default_fields))
@click.option('-h', '--human', help="Человекочитаемый JSON", is_flag=True, flag_value=True)
@click.option('-j', '--join', help="Общий список друзей для все пользователей", is_flag=True, flag_value=True)
@click.option('-i', '--intersection',
              help="Список общих друзей для все пользователей (по дефолту для 2х и более пользаков)", is_flag=True,
              flag_value=True, default=True)
@click.option('-o', '--output', help="Выходной файл (по дефолту stdout)", default=None)
@click.option('-s', '--stat', help="Статистика по друзьям", default=None,
              type=click.Choice(["city", "c", "country", "co", "university", "u", "school", "s"]))
@click.argument('user-ids', nargs=-1, required=True)
def friends_handler(id_only, fields, human, user_ids, join, intersection, output, stat):
    if id_only:
        fields = ""

    class HashableDict(dict):
        def __hash__(self):
            return hash(frozenset(self.keys()))

    if len(user_ids) == 1:
        user_list = [user for user in vkapi.get_friends(user_ids[0], fields.split(","))]
        for user_info in user_list:
            clear_empty(user_info)
    else:
        if id_only:
            friends_list = [set(user_info for user_info in vkapi.get_friends(user_id, fields.split(",")))
                            for user_id in user_ids]
        else:
            friends_list = [set(HashableDict(user_info)
                                for user_info in vkapi.get_friends(user_id, fields.split(",")))
                            for user_id in user_ids]
            for users in friends_list:
                for user in users:
                    clear_empty(user)

        user_list = friends_list[0]
        if join:
            for i in range(1, len(friends_list)):
                user_list |= friends_list[i]
        elif intersection:
            for i in range(1, len(friends_list)):
                user_list &= friends_list[i]
        user_list = list(user_list)

    if stat:
        stat_dict = defaultdict(lambda: 0)
        if stat in ("city", "c"):
            for user in user_list:
                stat_dict[user.get("city", {}).get("title", "Неизвестно")] += 1

        if stat in ("university", "u"):
            for user in user_list:
                stat_dict[user.get("university_name", "Неизвестно")] += 1

        if stat in ("country", "co"):
            for user in user_list:
                stat_dict[user.get("country", {}).get("title", "Неизвестно")] += 1

        if stat in ("school", "s"):
            for user in user_list:
                for school in user.get("schools", []):
                    stat_dict[school.get("name", "Неизвестно")] += 1

        sorted_dict = {}
        for key in (key for key, _ in sorted(list(stat_dict.items()), key=lambda x: x[1], reverse=True)):
            sorted_dict[key] = stat_dict[key]

        result = json.dumps(sorted_dict, indent=3, ensure_ascii=False)
    else:
        if not id_only:
            user_list = list_dict_exclude(list(user_list), exclude_fields)

        if human:
            for user_info in user_list:
                human_readable_user(user_info)

        result = json.dumps(user_list, indent=3, ensure_ascii=False)

    if output:
        with open(output, "w") as f:
            f.write(result)
    else:
        click.echo(result)


def download(url: str, path: str) -> bool:
    response = requests.get(url, stream=True)
    with open(path, "wb") as f:
        for chunk in response.iter_content(chunk_size=64 * 2 ** 20):
            f.write(chunk)
    return response.status_code == http.HTTPStatus.OK


def save_pictures(user_id, path):
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


@cli.command(name="user")
@click.option('-f', '--fields', help="Список параметров", default=",".join(friends_get_default_fields))
@click.option('-h', '--human', help="Человекочитаемый JSON", is_flag=True, flag_value=True)
@click.option('-g', '--group-list', help="Информация о группах пользователя", is_flag=True, flag_value=True)
@click.option('-s', '--save-pics', help="Сохранить фотографии пользователя", is_flag=True, flag_value=True)
@click.option('-o', '--output', help="Выходной файл (по дефолту stdout)", default=None)
@click.option('-p', '--picture-path', help="Папка с фотографиями со страницы", default=None)
@click.argument('user-id')
def user_handler(user_id, fields, output, human, group_list, save_pics, picture_path):
    # if group_list:
    #     groups = vkapi.get_groups(user_id, fields.split(","))
    #     print(groups[0])
    # else:
    #     pass
    if save_pics:
        save_pictures(user_id, picture_path)

    user_info = vkapi.get_user(user_id, fields.split(","))
    clear_empty(user_info)

    if human:
        human_readable_user(user_info)

    result = json.dumps(user_info, indent=3, ensure_ascii=False)

    if output:
        with open(output, "x") as f:
            f.write(result)
    else:
        click.echo(result)


@cli.command(name="lastseen")
@click.argument("user-id")
def lastseen_handler(user_id):
    last_seen = vkapi.get_last_seen_time(user_id)
    click.echo(last_seen.strftime('%H:%M:%S %d.%m.%Y'))


if __name__ == '__main__':
    cli()
