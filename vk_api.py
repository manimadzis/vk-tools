import http
from datetime import datetime, timezone, timedelta
from typing import Union, Optional, Sequence, Tuple

import requests
from bs4 import BeautifulSoup as bs


class VkAPIException(Exception):
    pass


class RequestFailed(VkAPIException):
    pass


class NoSuchUser(VkAPIException):
    pass


class VkAPI():
    def __init__(self, token):
        self.token = token

    def _make_request(self, method, params) -> Optional[Union[dict, list]]:
        """
        Совершает запрос к заданному методу VK API с переданными параметрами 
        
        method - название метода VK API [str] (подробнее на сайте https://vk.com/dev/methods)
        params - данные, передаваемые в запросе [dict]

        В случаем неудачного запроса поднимает RequestFailed
        """

        params['access_token'] = self.token

        try:
            _ = params['v']
        except:
            params['v'] = '5.122'
        try:
            _ = params['lang']
        except:
            params['lang'] = 'ru'

        url = 'https://api.vk.com/method/{}'.format(method)
        response = requests.get(url, params=params)

        if response.status_code == http.HTTPStatus.OK:
            content = response.json()
            if 'response' in content.keys():
                content = content['response']
            else:
                error_code = content['error']['error_code']
                error_msg = content['error']['error_msg']
                raise RequestFailed(
                        f'VK API: method: {method} | params: {params} | code: {error_code} | msg: {error_msg}')
        else:
            raise RequestFailed('Код ответа: {}'.format(response.status_code))

        return content

    def _is_user_id(self, domain: str) -> bool:
        """
        Проверяет, ялвяется ли переданная строка - id пользователя (числом)
        
        domain - часть url страницы после vk.com/ 
        """

        return domain.startswith("id") and domain[:2].isdigit()

    def _get_user_id(self, domain) -> int:
        """
        Возвращает id пользователя по domain

        domain - часть url страницы после vk.com/ 
        """

        if self._is_user_id(domain):
            return domain[2:]
        else:
            params = {
                'user_ids': domain
            }
            method = 'users.get'
            response = self._make_request(method, params)
            if not response:
                raise NoSuchUser(f"User name {domain} doesn't exist")

            return response[0]['id']

    def _get_group_id(self, domain) -> int:
        """
        Возвращает id группы по domain

        """

        try:
            group_id = int(domain)
        except ValueError:
            params = {
                'group_id': domain
            }
            response = self._make_request('groups.getById', params)
            group_id = response[0]['id']

        return group_id

    def _get_posts_count(self, domain):
        params = {
            'domain': domain,
            'extended': 0,
            'count': 1,
            'offset': 0
        }
        method = 'wall.get'
        response = self._make_request(method, params)
        posts_count = response.get('count', 0)
        return posts_count

    def _get_post_ids(self, posts):

        post_ids = [post['id'] for post in posts]

        return post_ids

    def get_user_name(self, domain) -> str:

        """
        Возвращает имя (фамилия имя) пользователя по domain

        domain - часть url страницы после vk.com/ 
        """

        params = {
            'user_ids': domain
        }
        method = 'users.get'
        response = self._make_request(method, params)

        user_name = '{last_name} {first_name}'.format(**response[0])

        return user_name

    def get_group_name(self, domain) -> str:
        """
        Возвращает название группы её по domain

        domain - часть url страницы после vk.com/ 
        """

        params = {
            'group_ids': domain
        }
        method = 'groups.getById'
        response = self._make_request(method, params)

        name = response[0]['name']

        return name

    # СПИСКИ ПОЛЬЗОВАТЕЛЕЙ
    def get_friends(self, domain: str, fields: Sequence[str]) -> list:
        """
        Возвращет список друзей по id
        
        fields - строка, содержащая список лополнительных полей
        для каждого пользователя

        Подробнее:
        https://vk.com/dev/friends.get
        """

        params = {
            'user_id': self._get_user_id(domain),
            'count': 5000,
            'offset': 0,
            'fields': ",".join(fields)
        }  # order не использовать, тк по дефолту стоит сортировка по возрастанию id
        method = 'friends.get'

        friends = []
        while True:
            response = self._make_request(method, params)
            friends.extend(response.get('items', []))
            friend_count = response.get('count', 0)

            params['offset'] += params['count']
            if params['offset'] >= friend_count:
                break

        return friends

    def get_followers(self, domain, fields=''):
        """
        Возвращет список подписчиков по id

        fields - строка, содержащая список лополнительных полей
        для каждого пользователя

        Подробнее:
        https://vk.com/dev/users.getFollowers

        """

        params = {
            'user_id': self._get_user_id(domain),
            'count': 1000,
            'offset': 0,
            'fields': fields
        }
        method = 'users.getFollowers'

        followers = []
        while True:
            response = self._make_request(method, params)
            followers.extend(response.get('items', []))
            follower_count = response.get('count', 0)

            params['offset'] += params['count']
            if params['offset'] >= follower_count:
                break

        return followers

    def get_subscriptions(self, domain: str, fields: Sequence[str]) -> Tuple[
        Sequence[dict], Sequence[dict], Sequence[dict]]:

        """
        Возвращет список подписок пользователя
        """

        params = {
            'user_id': self._get_user_id(domain),
            'count': 200,
            'extended': 1,
            'offset': 0,
            'fields': ",".join(fields)
        }

        subscriptions = []
        while True:
            response = self._make_request('users.getSubscriptions', params)
            subscriptions.extend(response.get('items', []))
            subscription_count = response.get('count', 0)

            params['offset'] += params['count']
            if params['offset'] >= subscription_count:
                break

        pages, users = [], []
        for subscription in subscriptions:
            if subscription.get('type') == 'profile':
                users.append(subscription)
            else:
                pages.append(subscription)

        return tuple(users), tuple(pages), tuple(subscriptions)

    def get_groups(self, domain: str, fields: Sequence[str] = tuple()):
        params = {
            'user_id': self._get_user_id(domain),
            'extended': 1,
            'fields': ','.join(fields),
            'count': 1000,
            'offset': 0
        }
        response = self._make_request('groups.get', params)
        groups = response.get('items', [])

        return groups

    # ФОТОГРАФИИ
    def get_albums(self, domain):
        """
        Возвращает список id альбомов пользователя или группы
        """

        params = {
            'owner_id': self._get_user_id(domain),
            'need_system': 1
        }
        method = 'photos.getAlbums'
        response = self._make_request(method, params)

        albums = []

        items = response.get('items', [])

        for album in items:
            albums.append(album['id'])

        return albums

    def get_urls_from_album(self, domain, album_id):
        params = {
            'owner_id': self._get_user_id(domain),
            'album_id': album_id,
            'count': 1000,
            'offset': 0
        }
        method = 'photos.get'

        urls = []
        received_count = 0
        all_photos_count = 1
        while received_count < all_photos_count:
            response = self._make_request(method, params)

            items = response.get('items', [])
            for photo in items:
                url = photo['sizes'][-1]['url']
                urls.append(url)

            all_photos_count = response.get('count', 0)

            received_count += params['count']
            params['offset'] += params['count']
        return urls

    def get_urls_of_all_photos(self, domain):
        albums = [album for album in self.get_albums(domain) if album != -9000]

        all_urls = []
        for album_id in albums:
            album_urls = self.get_urls_from_album(domain, album_id)
            all_urls.extend(album_urls)

        return all_urls

    def get_photo_urls_from_comments(self, posts, timestamp=False):

        post_ids = self._get_post_ids(posts)
        group_id = posts[0]['from_id']

        params = {
            'owner_id': group_id,
            'post_id': '',
            'count': 100,
            'offset': 0
        }
        method = 'wall.getComments'

        urls = []

        for post_id in post_ids:
            params['post_id'] = post_id

            while True:
                response = self._make_request(method, params)
                items = response.get('items', [])
                comments_count = response.get('count', 0)

                for comment in items:
                    attachments = comment.get('attachments', [])

                    for attachment in attachments:
                        if attachment['type'] == 'photo':
                            url = attachment['photo']['sizes'][-1]['url']

                            if timestamp:
                                urls.append((url, attachment['date']))
                            else:
                                urls.append(url)

                params['offset'] += params['count']
                if params['offset'] >= comments_count:
                    break

        return urls

    def get_photo_urls_from_posts(self, posts, timestamp=False):
        urls = []
        for post in posts:
            attachments = post.get('attachments', [])
            for attachment in attachments:
                if attachment['type'] == 'photo':
                    url = attachment['photo']['sizes'][-1]['url']

                    if timestamp:
                        urls.append((url, attachment['date']))
                    else:
                        urls.append(url)

        return urls

    # ВРЕМЯ
    def get_last_seen_time(self, domain) -> datetime:
        """
        Возвращает время последнего посещения пользователя
        """
        last_seen = None

        params = {
            'user_ids': self._get_user_id(domain),
            'fields': 'last_seen'
        }
        method = 'users.get'
        response = self._make_request(method, params)

        timestamp = response[0].get('last_seen', {}).get('time', 0)  # int
        tz = timezone(timedelta(hours=3))
        last_seen = datetime.fromtimestamp(timestamp, tz=tz)

        return last_seen

    def get_registration_time(self, domain):
        user_id = self._get_user_id(domain)
        url = 'https://vk.com/foaf.php?id={}'.format(user_id)

        content = requests.get(url).content
        soup = bs(content, 'lxml')
        time = soup.find('ya:created')['dc:date'].replace('T', ' ')

        return time

    def get_user(self, domain: str, fields: Sequence[str]):
        params = {
            'user_ids': domain,
            'fields': ",".join(fields)
        }
        response = self._make_request('users.get', params)
        return response[0]

    def get_extended_info(self, domain, fields=''):

        params = {
            'user_ids': domain,
            'fields': fields
        }
        method = 'users.get'
        response = self._make_request(method, params)

        return response[0]

    def get_gifts(self, domain):

        params = {
            'user_id': self._get_user_id(domain),
            'count': 100000
        }
        method = 'gifts.get'

        response = self._make_request(method, params)

        gifts = response['items']

        return gifts

    def get_dogs(self, domains):
        """
        Возвращает список удаленных пользователей

        Собака - удаленный пользователь
        В качестве аргумента принимается спискок domain-ов для проверки
        """
        _max_count = 1000  # максимальное кол-во domain-ов в одном запросе

        # Проходимся по списку domains и разрезаем его на куски длиной _max_count
        start, end, step = 0, len(domains), _max_count

        dogs = []
        while start < end:
            # Делаем срез
            _slice = domains[start:start + step]
            start = start + step

            _slice = map(str, _slice)
            # Выполняем запрос к API
            params = {
                'user_ids': ','.join(_slice)
            }
            method = 'users.get'
            response = self._make_request(method, params)

            # Записываем в dogs список собак
            for user in response:
                if user.get('deactivated', None) is not None:
                    dogs.append(user['id'])
        return dogs

    def get_posts(self, domain, count=None, offset=0, start=None, end=None) -> list:
        """
        Возвращает генератор списков постов (не более 100 за раз)

        Выбор временного промежутка [start; end]:
        start, end - timestamp-ы (int)

        count - кол-во возвращаемых постов (None - вернуть все посты)
        offset - смещение

        Если переданы оба параметра start, end, то вначале получается список всех
        пос

        """
        _max_count = 100  # максимально кол-во постов за 1 запрос

        params = {
            'domain': domain,
            'extended': 1,
            # 'filter': 'owner',
            'offset': offset
        }

        if count is None:
            params['count'] = _max_count
        else:
            params['count'] = _max_count if (count > _max_count or count == 0) else count

        method = 'wall.get'

        # задается количество и смещение
        if start == end == None:
            while True:
                response = self._make_request(method, params)
                posts = response['items']
                params['offset'] += len(posts)

                if count is not None:
                    if len(posts) >= count:
                        yield posts[:count]
                        break
                    else:
                        yield posts
                        count -= len(posts)
                elif len(posts) != 0:
                    yield posts
                else:
                    break

                    # посты с таймстампом больше чем start
        elif start is not None and end is None:
            while True:
                response = self._make_request(method, params)
                posts = response['items']
                params['offset'] += len(posts)
                start_index = None

                for i, post in enumerate(posts):
                    if post['date'] >= start:
                        start_index = i

                if start_index is None:
                    break
                else:
                    if count is None:
                        if posts == []:
                            break
                        yield posts[:start_index + 1]
                    else:
                        if count < start_index + 1:
                            print(start_index)
                            yield posts[start_index + 1 - count:start_index + 1]
                            break
                        else:
                            yield posts
                            count -= start_index + 1
        # посты с таймстампом меньше чем end
        elif start is None and end is not None:
            while True:
                response = self._make_request(method, params)
                posts = response['items']
                params['offset'] += len(posts)

                end_index = None

                for i, post in enumerate(posts):
                    if post['date'] <= end:
                        end_index = i
                        break

                if end_index is not None:
                    if count is None:
                        yield posts[end_index:]
                    else:
                        if count < len(posts) - end_index:
                            yield posts[end_index:end_index + count]
                            break
                        else:
                            yield posts[end_index:]
                            count -= len(posts) - end_index
        # посты с таймстампом внутри отрезка [start, end]
        else:
            start_index = end_index = None
            while True:
                response = self._make_request(method, params)
                posts = response['items']
                params['offset'] += len(posts)

                for i, post in enumerate(posts):
                    if post['date'] <= end and end_index is None:
                        end_index = i

                    if post['date'] < start and start_index is None:
                        start_index = i - 1

                if end_index is not None:
                    if end_index == -1:
                        if start_index is not None:
                            yield posts[:start_index + 1]
                            break
                        else:
                            yield posts
                    else:
                        if start_index is not None:
                            yield posts[end_index:start_index + 1]
                            break
                        else:
                            yield posts[end_index:]

                    end_index = -1

    def get_common_friends(self, domain_1, domain_2, mode=0):

        """
        Возвращает список общих друзей двух пользователей

        mode:
        0: список id
        1: словарь с информацие о каждом друге
        """

        fields = ''
        if mode == 1:
            fields = 'city, country, education, universities'

        # Получаем список друзей каждого из пользователей
        friends_1 = self.get_friends(domain_1, fields)
        friends_2 = self.get_friends(domain_2)

        # Ищем общие элементы
        common = []
        if mode == 0:
            for person in friends_1:
                if person in friends_2:
                    common.append(person)
        elif mode == 1:
            for person in friends_1:
                if person['id'] in friends_2:
                    common.append(person)
            people = []
            for person in common:
                name = '{} {}'.format(person['last_name'], person['first_name'])
                city = person.get('city', {}).get('title', '')
                country = person.get('country', {}).get('title', '')
                university = person.get('university_name', '')

                info = {'name': name, 'city': city, 'country': country, 'university': university}
                people.append(info)
            common = people

            return common

    def process_people(self, people, sort_by='name', filter_by={}, filter_reverse=False) -> list:
        """
        Обрабатывает список people

        filter_by:
        задается словарем
        {'param': 'value1,value2'}
        param - параметр person
        value1,value2,... значения для фильтрации(одно из значений, которое принимает/непринимает параметр person)
        (записывать строго через запятую, без пробелов и т.д.)

        filter_reverse:
        False только persons с переданные значения будут возвращены
        True будут возвращены все persons, кроме имеющих переданные значения

        sort_by:
        заадется строкой, которая является параметром person
        """

        people_keys = people[0].keys()  # Список параметров person

        # for person in people:
        #     for key in people_keys:

        # Выполняем сортировку по укзанному в sort_by параметру
        if sort_by in people_keys:
            people.sort(key=lambda x: x[sort_by])
        else:
            print('Неизвестный ключ сортировки')

        # Выполняем фильтрацию данных по указанным в filter_by параметрам и их значениям
        if filter_by != {}:  # Если filter_by не пустой
            filter_by_keys = filter_by.keys()  # списко параметров filter_by
            _people = []  # список людей отвечающих критериям
            for person in people:  # проходимся по списку people
                _bool = True  # проверяет одновременность выполнения всех условий
                for _filter in filter_by_keys:  # проходимся по всем параметрам filter_by
                    values = filter_by[_filter].split(',')  # разбиваем строку значений на список возможных значений
                    __bool = False  # проверяет выполнение хотя бы одного условия из списка значений
                    for value in values:
                        __bool = __bool or (filter_reverse ^ (person[_filter] == value))
                    _bool = _bool and __bool
                if _bool:  # если все условия выполнятся, то добавляем в список отвечающих критериям
                    _people.append(person)
            people = _people  # переприсваеваем people

        return people

    def get_likes(self, owner_id, item_id):
        params = {
            'owner_id': owner_id,
            'item_id': item_id,
            'type': 'post',
            'count': 1000,
            'offset': 0
        }
        method = 'likes.getList'
        likes = []
        while True:
            response = self._make_request(method, params)
            items = response.get('items', [])
            likes.extend(items)
            likes_count = response.get('count', 0)

            params['offset'] += params['count']
            if params['offset'] >= likes_count:
                break

        return likes
