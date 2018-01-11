import traceback

import datetime

import dateutil
from aiohttp.web import json_response, View
from dateutil.tz import tzutc

from functions import update_users_per_forum


def dict_fix_created(record):
    tmp = dict(record)
    tmp['created'] = tmp['created'].replace(tzinfo=dateutil.tz.tzlocal()).isoformat()
    return tmp


def desc_to_string(desc):
    return 'DESC' if desc else ''


def desc_to_compare_operator(desc):
    return '<' if desc else '>'


class PostCreate (View):
    async def post(self):
        pool = self.request.app['pool']
        async with pool.acquire() as connection:
            slug_or_id = self.request.match_info['slug_or_id']
            data = await self.request.json()
            try:
                thread_id = int(slug_or_id)
                result_thread = await connection.fetchrow('''
                                                SELECT forum_id, forum
                                                FROM thread
                                                WHERE id = $1
                                                ''', thread_id)
                if not result_thread:
                    return json_response({'message': 'no thread'},
                                         status=404)
                result_thread = dict(result_thread)
                forum_id = result_thread.get('forum_id')
                forum_slug = result_thread.get('forum')
            except ValueError:
                result_thread = await connection.fetchrow('''
                                                                    SELECT id, forum_id, forum
                                                                    FROM thread
                                                                    WHERE slug = $1::citext
                                                                    ''', slug_or_id)
                if not result_thread:
                    return json_response({'message': 'no thread'},
                                         status=404)
                result_thread = dict(result_thread)
                thread_id = result_thread.get('id')
                forum_id = result_thread.get('forum_id')
                forum_slug = result_thread.get('forum')

            authors = list(map(lambda x: x.get("author"), data))
            parents = list(map(lambda x: x.get("parent", 0), data))
            messages = list(map(lambda x: x.get("message"), data))
            posts_count = len(authors)

            transact = connection.transaction()
            await transact.start()
            try:
                result = await connection.fetch('''
                    INSERT INTO "post" 
                      (author_id, author, forum_id, forum, created, message, root_parent, parent, path, thread_id)
                      (
                        SELECT 
                          u.id,
                          u.nickname,
                          $1,
                          $2::citext,
                          now(),
                          t.message,
                          case when t.parent_id = 0 then t.post_id else post_parent.path[1] end,
                          case when t.parent_id = 0 then 0 else post_parent.id end, 
                          array_append(coalesce(post_parent.path, ARRAY[]::int[]), t.post_id::int),
                          $3
                        FROM
                          UNNEST(ARRAY(select nextval('post_id_seq') from generate_series(0, $7)),
                                 $4::int[],
                                 $5::citext[],
                                 $6::citext[]) with ordinality t(post_id, parent_id, author, message)
                        INNER JOIN "User" u on u.nickname = t.author::citext
                        LEFT JOIN "post" post_parent on t.parent_id = post_parent.id AND post_parent.thread_id = $3
                        ORDER BY ordinality
                    )    
                    RETURNING id, author_id, author, message, parent, created, forum, thread_id as thread
                ''', forum_id, forum_slug, thread_id, parents, authors, messages, posts_count)
                result = list(map(dict, result))
                after_insert_count = 0
                authors = []
                for row in result:
                    after_insert_count += 1
                    if row.get('parent') is None:
                        await transact.rollback()
                        return json_response({'message': 'parent thread not found'}, status=409)
                    dt = row.get('created')
                    row['created'] = dt.replace(tzinfo=dateutil.tz.tzlocal()).isoformat()
                    authors.append(row['author_id'])
                    row.pop('author_id')

                if after_insert_count != posts_count:
                    await transact.rollback()
                    return json_response({'message': 'user not found'}, status=404)

                await update_users_per_forum(connection, forum_id, authors)

                await connection.execute('''
                    UPDATE "forum"
                    SET posts = posts + $1
                    WHERE id = $2''', posts_count, forum_id)

                await transact.commit()

                return json_response(result, status=201)
            except:
                traceback.print_exc()
                await transact.rollback()
                return json_response({'message': 'error'}, status=400)


class GetPosts (View):
    async def get(self):
        slug_or_id = self.request.match_info['slug_or_id']
        limit = int(self.request.GET.get('limit', -1))
        since = int(self.request.GET.get('since', -1))
        sortType = self.request.GET.get('sort', 'flat')
        desc = bool(True if self.request.GET.get('desc', 'false') == 'true' else False)

        pool = self.request.app['pool']
        async with pool.acquire() as connection:
            try:
                thread_id = int(slug_or_id)
                result_thread = await connection.fetchrow('''
                                                SELECT 1
                                                FROM thread
                                                WHERE id = $1
                                                ''', thread_id)
                if not result_thread:
                    return json_response({'message': 'no thread'},
                                         status=404)
            except ValueError:
                result_thread = await connection.fetchrow('''
                                                                    SELECT id
                                                                    FROM thread
                                                                    WHERE slug = $1::citext
                                                                    ''', slug_or_id)
                if not result_thread:
                    return json_response({'message': 'no thread'},
                                         status=404)
                result_thread = dict(result_thread)
                thread_id = result_thread.get('id')

            query_list = ['''
                SELECT
                    p.id,
                    author,
                    created,
                    forum,
                    isedited,
                    message,
                    parent,
                    thread_id as thread
                    ''']
            params = []
            param_counter = 1

            if sortType == 'flat':
                query_list.append('''
                FROM "post" p
                WHERE thread_id = $1 
                ''')
                params.append(thread_id)
                param_counter += 1
                if since != -1:
                    params.append(since)
                    query_list.append(' AND id ')
                    query_list.append(desc_to_compare_operator(desc))
                    query_list.append('$')
                    query_list.append(str(param_counter))
                    query_list.append('\n')
                    param_counter += 1
                query_list.append('ORDER BY created ')
                query_list.append(desc_to_string(desc))
                query_list.append(', id ')
                query_list.append(desc_to_string(desc))
                query_list.append('\n')
                if limit != -1:
                    params.append(limit)
                    query_list.append('LIMIT $')
                    query_list.append(str(param_counter))
                    query_list.append('\n')
                    param_counter += 1
            elif sortType == 'tree':
                query_list.append('''
                                FROM "post" p
                                WHERE thread_id = $1 
                                ''')
                params.append(thread_id)
                param_counter += 1
                if since != -1:
                    params.append(since)
                    query_list.append(' AND path ')
                    query_list.append(desc_to_compare_operator(desc))
                    query_list.append('(SELECT path FROM "post" WHERE id = $')
                    query_list.append(str(param_counter))
                    query_list.append(')\n')
                    param_counter += 1
                query_list.append('ORDER BY path ')
                query_list.append(desc_to_string(desc))
                query_list.append(', id ')
                query_list.append(desc_to_string(desc))
                query_list.append('\n')
                if limit != -1:
                    params.append(limit)
                    query_list.append('LIMIT $')
                    query_list.append(str(param_counter))
                    query_list.append('\n')
                    param_counter += 1
            elif sortType == 'parent_tree':
                query_list.append('''
                    FROM
                    (
                        SELECT
                            id,
                            dense_rank() OVER ( ORDER BY root_parent ''')
                query_list.append(desc_to_string(desc))
                query_list.append(''') as parent_root_rank
                    FROM "post"
                    WHERE thread_id = $''')
                query_list.append(str(param_counter))
                query_list.append('\n')
                params.append(thread_id)
                param_counter += 1
                if since != -1:
                    params.append(since)
                    query_list.append(' AND path ')
                    query_list.append(desc_to_compare_operator(desc))
                    query_list.append('(SELECT path FROM "post" WHERE id = $')
                    query_list.append(str(param_counter))
                    query_list.append(')\n')
                    param_counter += 1
                query_list.append(''') t
                JOIN "post" p ON (p.id = t.id)
                ''')
                if limit != -1:
                    params.append(limit)
                    query_list.append('WHERE t.parent_root_rank <= $')
                    query_list.append(str(param_counter))
                    query_list.append('\n')
                    param_counter += 1
                query_list.append('ORDER BY p.path ')
                query_list.append(desc_to_string(desc))
                query_list.append(', p.id ')
                query_list.append(desc_to_string(desc))
                query_list.append('\n')

            query = ''.join(query_list)
            posts = await connection.fetch(query, *params)

            return json_response(list(map(dict_fix_created, posts)), status=200)


class OnePost (View):
    async def get(self):
        pool = self.request.app['pool']
        async with pool.acquire() as connection:
            post_id = self.request.match_info['id']
            related = self.request.GET.get('related', [])
            select_fields = []
            joins = []
            if 'user' in related:
                select_fields.append('''
                    u.email,
                    u.about,
                    u.nickname,
                    u.fullname,
                ''')
                joins.append('INNER JOIN "User" u ON u.ID = p.author_id\n')
            if 'forum' in related:
                select_fields.append('''
                    f.posts AS forum_posts,
                    f.threads AS forum_threads,
                    f.slug AS forum_slug,
                    f.title AS forum_title,
                    f.user AS forum_user,
                ''')
                joins.append('INNER JOIN "forum" f ON f.ID = p.forum_id\n')
            if 'thread' in related:
                select_fields.append('''
                    t.author AS thread_author, 
                    t.created AS thread_created,
                    t.forum AS thread_forum, 
                    t.id AS thread_id, 
                    t.message AS thread_message, 
                    t.slug AS thread_slug, 
                    t.title AS thread_title, 
                    t.votes AS thread_votes,
                ''')
                joins.append('INNER JOIN "thread" t ON t.ID = p.thread_id\n')

            query = '''
                SELECT
                    {0}
                    p.author as post_author, 
                    p.created AS post_created,
                    p.forum AS post_forum, 
                    p.id AS post_id, 
                    p.message AS post_message, 
                    p.isedited AS post_isedited, 
                    p.parent AS post_parent, 
                    p.thread_id AS post_thread
                FROM "post" p
                {1}
                WHERE p.id = $1
            '''.format(''.join(select_fields), ''.join(joins))
            result = await connection.fetchrow(query, int(post_id))
            if result is None:
                return json_response({'message': 'post not found'}, status=404)

            result = dict(result)
            response = {
                "post": {
                    "author": result['post_author'],
                    "created": result['post_created'].replace(tzinfo=dateutil.tz.tzlocal()).isoformat(),
                    "forum": result['post_forum'],
                    "id": result['post_id'],
                    "isEdited": result['post_isedited'],
                    "message": result['post_message'],
                    "parent": result['post_parent'],
                    "thread": result['post_thread']
                }
            }
            if 'user' in related:
                response["author"] = {
                    "about": result['about'],
                    "email": result['email'],
                    "fullname": result['fullname'],
                    "nickname": result['nickname']
                }
            if 'forum' in related:
                response["forum"] = {
                    "posts": result['forum_posts'],
                    "slug": result['forum_slug'],
                    "threads": result['forum_threads'],
                    "title": result['forum_title'],
                    "user": result['forum_user']
                }
            if 'thread' in related:
                response["thread"] = {
                    "author": result['thread_author'],
                    "created": result['thread_created'].isoformat(),
                    "forum": result['thread_forum'],
                    "id": result['thread_id'],
                    "message": result['thread_message'],
                    "slug": result['thread_slug'],
                    "title": result['thread_title'],
                    "votes": result['thread_votes']
                }
            return json_response(response, status=200)

    async def post(self):
        pool = self.request.app['pool']
        async with pool.acquire() as connection:
            async with connection.transaction():
                post_id = self.request.match_info['id']
                data = await self.request.json()

                if data.get('message') is not None:
                    result = await connection.fetchrow(
                        '''
                        UPDATE "post"
                        SET message = $1,
                            isedited = CASE WHEN message <> $1 THEN TRUE ELSE isedited END
                        WHERE id = $2
                        RETURNING id, author, message, parent, isedited as "isEdited", created, forum, thread_id AS thread
                        ''', data.get('message'), int(post_id))
                else:
                    result = await connection.fetchrow(
                        '''
                          SELECT
                            id, 
                            author,
                            message,
                            parent, 
                            isedited as "isEdited", 
                            created, 
                            forum, 
                            thread_id AS thread
                        FROM "post"
                        WHERE id = $1
                        ''', int(post_id))

                if result is None:
                    return json_response({'message': 'post not found'}, status=404)
                result = dict(result)
                result['created'] = result['created'].replace(tzinfo=dateutil.tz.tzlocal()).isoformat()
                return json_response(result, status=200)
