
from aiohttp.web import json_response, View


class Clear (View):
    async def post(self):
        pool = self.request.app['pool']
        async with pool.acquire() as connection:
            await connection.execute('truncate table "User" cascade')
            return json_response({}, status=200)


class Status (View):
    async def get(self):
        pool = self.request.app['pool']
        async with pool.acquire() as connection:
            result = await connection.fetchrow('''
                SELECT
                    (SELECT count(1) FROM "User") as "user",
                    (SELECT count(1) FROM "forum") as forum,
                    (SELECT count(1) FROM "thread") as thread,
                    (SELECT count(1) FROM "post") as post
            ''')
            return json_response(dict(result), status=200)