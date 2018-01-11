from aiohttp.web import json_response, View
import json
from dateutil.tz import tzutc
from datetime import datetime
from pytz import timezone
from functions import update_users_per_forum

from queryes.query_Thread import create_thread, select_threads

UTC = tzutc()


def serialize_date(dt):
    if dt.tzinfo:
        dt = dt.astimezone(UTC).replace(tzinfo=None)
    return dt.isoformat() + 'Z'


class ThreadCreate (View):
    async def post(self):
        pool = self.request.app['pool']
        async with pool.acquire() as connection:
            async with connection.transaction():
                data = await  self.request.json()
                # TODO добавить default в гет чтоб исключение не бросало
                result_user = await connection.fetchrow(
                    ''' select id, nickname from "User" where nickname = $1''',
                    data.get('author',' ')
                )
                if result_user is None:
                    return json_response({'message': 'Cant find user' },
                                         status=404)
                result_forum = await connection.fetchrow(
                    ''' select id, slug from forum where slug = $1''',
                    self.request.match_info['slug']
                )
                if result_forum is None:
                    return json_response({'message': 'Cant find forum' },
                                         status=404)

                result_user = dict(result_user)
                result_forum = dict(result_forum)
                created = data.get('created')
                if created:
                    t = datetime.strptime(''.join(created.rsplit(':', 1)), '%Y-%m-%dT%H:%M:%S.%f%z')
                    t.astimezone(UTC)
                else:
                    t = datetime.now(UTC)

                result_thread = await connection.fetchrow(create_thread,
                    result_user.get('id', 0),
                    result_user.get('nickname', ' '),
                    result_forum.get('id', 0),
                    result_forum.get('slug', ' '),
                    data.get('message', ' '),
                    data.get('slug', None),
                    data.get('title', ' '),
                    t,
                )

                await update_users_per_forum(connection,result_forum.get('id', 0), result_user.get('id', 0))
                await connection.execute('''
                                   UPDATE "forum"
                                   SET threads = threads + 1
                                   WHERE id = $1''', result_forum.get('id', 0))

                result_thread = dict(result_thread)
                result_thread['created'] = result_thread['created'].isoformat()

                status = 201 if result_thread['bool'] else 409
                result_thread.pop('bool', False)
                return json_response(result_thread,
                                     status=status)


class ThreadDetails(View):
    async def get(self):
        pool = self.request.app['pool']
        async with pool.acquire() as connection:
            async with connection.transaction():
                slug_or_id = self.request.match_info['slug_or_id']
                sql_query = ''' SELECT author, created, forum, id, message, slug, title, votes
                    FROM thread
                    WHERE {} '''\
                    .format(
                    'id = {}'.format(slug_or_id) if slug_or_id.isdigit()
                    else "slug = '{}'".format(slug_or_id)
                )
                result_thread = await connection.fetchrow(sql_query)
                status = 404
                if result_thread:
                    status = 200
                    result_thread = dict(result_thread)
                    result_thread['created'] = result_thread['created'].isoformat()
                return json_response(result_thread if status == 200 else {'message': 'thread not found'},
                                     status=status)

    async def post(self):
        pool = self.request.app['pool']
        async with pool.acquire() as connection:
            async with connection.transaction():
                slug_or_id = self.request.match_info['slug_or_id']
                data = await  self.request.json()
                print(data)
                sql_str = '''
                UPDATE thread SET message = {}, title = {} WHERE {}
                RETURNING author, created, forum, id, message, slug, title, votes;
                '''.format(
                    "'" + data.get('message') + "'" if data.get('message') else 'message',
                    "'" + data.get('title') + "'" if data.get('title') else 'title',
                    'id = {}'.format(slug_or_id) if slug_or_id.isdigit()
                    else "slug = '{}'".format(slug_or_id)
                )
                print(sql_str)
                result_thread = await connection.fetchrow(sql_str)
                status = 404
                if result_thread:
                    status = 200
                    result_thread = dict(result_thread)
                    result_thread['created'] = result_thread['created'].isoformat()
                return json_response(result_thread if status == 200 else {'message': 'thread not found'},
                                     status=status)


