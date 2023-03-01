import json
from collections import defaultdict

import click

from fields import *
from utils import *
from vk_api import VkAPI

vkapi = VkAPI(os.environ["VK_TOKEN"])


def friends_handler(*, id_only, fields, human, user_ids, join, intersection, output, stat):
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
                    dict_exclude(user, exclude_fields)

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
            for user in user_list:
                dict_exclude(user, exclude_fields)

        if human:
            for user in user_list:
                human_readable_user(user)

        result = json.dumps(user_list, indent=3, ensure_ascii=False)

    if output:
        with open(output, "w") as f:
            f.write(result)
    else:
        click.echo(result)


def subscriptions_handler(*, fields, user_ids, join, intersection, output, human):
    if len(user_ids) == 1:
        _, _, subs = vkapi.get_subscriptions(user_ids[0], fields.split(","))
        for sub in subs:
            clear_empty(sub)
    else:
        subs_list = []
        for user_id in user_ids:
            _, _, subs = vkapi.get_subscriptions(user_id, fields.split(","))
            subs_list.append(set(HashableDict(sub) for sub in subs))

        for subs in subs_list:
            for sub in subs:
                clear_empty(sub)

        subs = subs_list[0]
        if join:
            for i in range(1, len(subs_list)):
                subs |= subs_list[i]
        elif intersection:
            for i in range(1, len(subs_list)):
                subs &= subs_list[i]

        subs = list(subs)
        for sub in subs:
            dict_exclude(sub, exclude_fields)

    if human:
        for sub in subs:
            human_readable_sub(sub)

    result = json.dumps(subs, indent=3, ensure_ascii=False)

    if output:
        with open(output, "w") as f:
            f.write(result)
    else:
        click.echo(result)


def groups_handler(*, fields, human, user_ids, join, intersection, output):
    if len(user_ids) == 1:
        groups = vkapi.get_groups(user_ids[0], fields.split(","))
        for group in groups:
            clear_empty(group)
    else:
        groups_list = [set(HashableDict(group)
                           for group in vkapi.get_groups(user_id, fields.split(",")))
                       for user_id in user_ids]
        for groups in groups_list:
            for group in groups:
                clear_empty(group)

        groups = groups_list[0]
        if join:
            for i in range(1, len(groups_list)):
                groups |= groups_list[i]
        elif intersection:
            for i in range(1, len(groups_list)):
                groups &= groups_list[i]

        for group in groups:
            dict_exclude(group, exclude_fields)

        if human:
            for group in groups:
                human_readable_group(group)
        groups = tuple(groups)

    result = json.dumps(groups, indent=3, ensure_ascii=False)

    if output:
        with open(output, "w") as f:
            f.write(result)
    else:
        click.echo(result)


def user_handler(*, user_id, fields, output, human, group_list, save_pics, picture_path):
    # if group_list:
    #     groups = vkapi.get_groups(user_id, fields.split(","))
    #     print(groups[0])
    # else:
    #     pass
    if save_pics:
        save_pictures(vkapi, user_id, picture_path)

    user_info = vkapi.get_user(user_id, fields.split(","))
    clear_empty(user_info)

    if human:
        human_readable_user(user_info)

    result = json.dumps(user_info, indent=3, ensure_ascii=False)

    if output:
        with open(output, "w") as f:
            f.write(result)
    else:
        click.echo(result)


def lastseen_handler(user_id):
    last_seen = vkapi.get_last_seen_time(user_id)
    click.echo(last_seen.strftime('%H:%M:%S %d.%m.%Y'))


def full_handler(**kwargs):
    friends_handler(**kwargs)
    user_handler(**kwargs)
    groups_handler(**kwargs)
    subscriptions_handler(**kwargs)
