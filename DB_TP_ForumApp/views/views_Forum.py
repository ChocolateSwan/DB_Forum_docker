from aiohttp.web import json_response, View


def desc_to_string(desc):
    return 'DESC' if desc else ''


def desc_to_compare_operator(desc):
    return '<' if desc else '>'


class ForumCreate (View):
    async def post(self):
        pool = self.request.app['pool']
        async with pool.acquire() as connection:
            async with connection.transaction():
                data = await  self.request.json()
                result_user = await connection.fetchrow(
                    ''' select id, nickname from "User" where nickname = $1''',
                    data.get('user',' ')
                )
                if result_user is None:
                    return json_response({'message': 'Cant find user' },
                                         status=404)
                result_user = dict(result_user)
                result_forum = await connection.fetchrow(
                    '''INSERT INTO forum (slug, title, "user", user_id) VALUES
                ($1, $2, $3, $4)
                ON CONFLICT DO NOTHING
                RETURNING posts, slug, threads, title, "user"''',
                    data.get('slug',' '),
                    data.get('title', ' '),
                    result_user.get('nickname', ' '),
                    result_user.get('id', 0)
                )
                if result_forum is not None:
                    return json_response(dict(result_forum),
                                         status=201)
                result_forum = await connection.fetchrow(
                    ''' select posts, slug, threads, title, "user" from forum where slug = $1''',
                    data.get('slug',' ')
                )
                return json_response(dict(result_forum),
                                     status=409)


class ForumDetails (View):
    async def get(self):
        pool = self.request.app['pool']
        async with pool.acquire() as connection:
            async with connection.transaction():
                result = await connection.fetchrow(
                    '''select posts, slug, threads, title, "user" from forum where slug = $1''',
                                                   self.request.match_info['slug'])
                status = 404 if result is None else 200
                return json_response({'message': 'cant find forum'} if status == 404 else dict(result),
                                     status=status)


class ForumThreads (View):
    async def get(self):
        pool = self.request.app['pool']
        async with pool.acquire() as connection:
            async with connection.transaction():
                result_forum = await connection.fetchrow(
                    ''' select id, slug from forum where slug = $1''',
                    self.request.match_info['slug']
                )
                if result_forum is None:
                    return json_response({'message': 'Cant find forum'},
                                         status=404)
                query_str = '''SELECT author, created, forum, id, message, slug, title, votes
                            FROM thread 
                            WHERE forum = '{}' {} ORDER BY created {} {} ;'''\
                    .format(
                    self.request.match_info['slug'],
                    " AND created" +
                    (' <= ' if self.request.GET.get('desc') == 'true' else ' >= ') +
                    " '{}' ".format(self.request.GET['since']) if self.request.GET.get('since') else '',
                    'DESC' if self.request.GET.get('desc') == 'true' else 'ASC',
                    " LIMIT {} ".format(int(self.request.GET.get('limit'))) if self.request.GET.get('limit') else ' '
                )
                result = await connection.fetch(query_str)
                result = list(map(lambda x: dict(x), result))
                for thread in result:
                    thread['created'] = thread['created'].isoformat()
                return json_response(result,
                                     status=200)


class ForumUsers (View):
    async def get(self):
        slug = self.request.match_info['slug']
        limit = int(self.request.GET.get('limit', -1))
        since = self.request.GET.get('since', None)
        desc = bool(True if self.request.GET.get('desc', 'false') == 'true' else False)

        pool = self.request.app['pool']
        async with pool.acquire() as connection:
            forum_id_result = await connection.fetchrow('''
                SELECT
                    id
                FROM "forum"
                WHERE slug = $1::citext''', slug)
            if forum_id_result is None:
                return json_response({'message': 'no forum'}, status=404)

            query_list = ['''
                SELECT
                    u.nickname,
                    u.fullname,
                    u.about,
                    u.email
                FROM "users_per_forum" upf
                INNER JOIN "User" u on u.id = upf.user_id
                WHERE upf.forum_id = $1
            ''']
            params = [dict(forum_id_result).get('id')]
            param_counter = 2
            if since is not None:
                query_list.append('AND u.nickname ')
                query_list.append(desc_to_compare_operator(desc))
                query_list.append('$')
                query_list.append(str(param_counter))
                query_list.append('\n')
                params.append(since)
                param_counter += 1
            query_list.append('ORDER BY u.nickname ')
            query_list.append(desc_to_string(desc))
            query_list.append('\n')
            if limit != -1:
                params.append(limit)
                query_list.append('LIMIT $')
                query_list.append(str(param_counter))
                query_list.append('\n')
                param_counter += 1

            query = ''.join(query_list)
            users = await connection.fetch(query, *params)

            return json_response(list(map(dict, users)), status=200)

