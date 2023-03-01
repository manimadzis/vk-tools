import click

from fields import *
from handlers import friends_handler, subscriptions_handler, groups_handler, lastseen_handler, user_handler


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
def handler(*args, **kwargs):
    friends_handler(*args, **kwargs)


@cli.command(name="subs")
@click.option('-f', '--fields', help="Список параметров", default=",".join(friends_get_default_fields))
@click.option('-j', '--join', help="Общий список групп для все пользователей", is_flag=True, flag_value=True)
@click.option('-i', '--intersection',
              help="Список общих групп для все пользователей (по дефолту для 2х и более пользаков)", is_flag=True,
              flag_value=True, default=True)
@click.option('-h', '--human', help="Человекочитаемый JSON", is_flag=True, flag_value=True)
@click.option('-o', '--output', help="Выходной файл (по дефолту stdout)", default=None)
@click.argument('user-ids', nargs=-1, required=True)
def handler(*args, **kwargs):
    subscriptions_handler(*args, **kwargs)


@cli.command(name="groups")
@click.option('-f', '--fields', help="Список параметров", default=",".join(friends_get_default_fields))
@click.option('-j', '--join', help="Общий список групп для все пользователей", is_flag=True, flag_value=True)
@click.option('-i', '--intersection',
              help="Список общих групп для все пользователей (по дефолту для 2х и более пользаков)", is_flag=True,
              flag_value=True, default=True)
@click.option('-h', '--human', help="Человекочитаемый JSON", is_flag=True, flag_value=True)
@click.option('-o', '--output', help="Выходной файл (по дефолту stdout)", default=None)
@click.argument('user-ids', nargs=-1, required=True)
def handler(*args, **kwargs):
    groups_handler(*args, **kwargs)


@cli.command(name="user")
@click.option('-f', '--fields', help="Список параметров", default=",".join(friends_get_default_fields))
@click.option('-h', '--human', help="Человекочитаемый JSON", is_flag=True, flag_value=True)
@click.option('-g', '--group-list', help="Информация о группах пользователя", is_flag=True, flag_value=True)
@click.option('-s', '--save-pics', help="Сохранить фотографии пользователя", is_flag=True, flag_value=True)
@click.option('-o', '--output', help="Выходной файл (по дефолту stdout)", default=None)
@click.option('-p', '--picture-path', help="Папка с фотографиями со страницы", default=None)
@click.argument('user-id')
def handler(*args, **kwargs):
    user_handler(*args, **kwargs)


@cli.command(name="lastseen")
@click.argument("user-id")
def handler(*args, **kwargs):
    lastseen_handler(*args, **kwargs)
