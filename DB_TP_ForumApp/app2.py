#! /usr/bin/env python

import asyncio
import asyncpg
from aiohttp import web
from routes import routes

async def init(app2):
    for route in routes:
        app2.router.add_route(route[0], route[1], route[2], name=route[3])

    app2['pool'] = await asyncpg.create_pool(user='postgresuser', password='postgres',
                                            database='forumtp', host='127.0.0.1', min_size=1, max_size=10)

app2 = web.Application()
asyncio.get_event_loop().run_until_complete(init(app2))
