#! /usr/bin/env python

import asyncio
import asyncpg
from aiohttp import web
from routes import routes

# from settings import *


async def shutdown(server, app, app_handler):
    server.close()
    await server.wait_closed()
    pool = app['pool']
    await  pool.close() #????????????????????????????
    await app.shutdown()
    # await app_handler.finish_connections(10.0) #Что с этим делать?
    await app.cleanup()


async def init(app, app_loop):
    # app = web.Application(loop=app_loop)
    # route part
    for route in routes:
        app.router.add_route(route[0], route[1], route[2], name=route[3])


    # app.router.add_static('/static', 'static', name='static')
    # end route part

    handler = app.make_handler()

    app['pool'] = await asyncpg.create_pool(user='postgresuser', password='postgres',
                                            database='forumtp', host='127.0.0.1', min_size=1, max_size=10)
    print("Connection pool created")
    # conn = await asyncpg.connect(user='olyasur', password='Arielariel111',
    #                              database='ForumTP', host='127.0.0.1')
    # values = await conn.fetch('''SELECT * FROM "User" where nickname = $1 ''',"silva.mtdeemjJx10Pj1" )
    # await conn.close()
    # print(values[0])
    # end db connect
    serv_generator = app_loop.create_server(handler, '127.0.0.1', 5000) #8080
    return serv_generator, handler, app

loop = asyncio.get_event_loop()
app = web.Application(loop=loop)
serv_generator, handler, app = loop.run_until_complete(init(app, loop))
serv = loop.run_until_complete(serv_generator)
print('start server')
try:
    loop.run_forever()
except KeyboardInterrupt:
    print('Stop server keyboardInterrupt')
finally:
    loop.run_until_complete(shutdown(serv, app, handler))
    loop.close()
print('Stop server')
