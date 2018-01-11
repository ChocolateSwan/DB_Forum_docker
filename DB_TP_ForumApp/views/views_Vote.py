from aiohttp.web import json_response, View

class VoteCreate (View):
    async def post(self):
        pool = self.request.app['pool']
        async with pool.acquire() as connection:
            async with connection.transaction():
                slug_or_id = self.request.match_info['slug_or_id']
                data = await  self.request.json()
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
                result_user = await connection.fetchrow('''
                                                        SELECT id
                                                        FROM "User"
                                                        WHERE nickname = $1::citext
                                                        ''', data.get('nickname'))
                if not result_user:
                    return json_response({'message': 'no user'},
                                         status=404)
                result_user = dict(result_user)
                user_id = result_user.get('id')
                result_vote = await connection.fetchrow('''
                                                        SELECT id, vote
                                                        FROM vote
                                                        WHERE user_id = $1 
                                                          AND thread_id = $2
                                                        ''', user_id, thread_id)
                if result_vote:
                    result_vote = dict(result_vote)
                    vote_id = result_vote.get('id')
                    vote = result_vote.get('vote')
                else:
                    vote_id = None
                    vote = None

                if vote_id and vote == data.get('voice'):
                    result_thread = await connection.fetchrow('''
                                                                SELECT author, created, forum, id, message, slug, title, votes
                                                                FROM thread
                                                                WHERE id = $1 
                                                                ''',thread_id)
                    result_thread = dict(result_thread)
                    result_thread['created'] = result_thread['created'].isoformat()
                    return json_response(result_thread, status=200)
                elif vote_id:
                    await connection.execute('''
                                            UPDATE vote
                                            SET vote = -vote
                                            WHERE id = $1 
                                            ''', vote_id)
                    result_thread = await connection.fetchrow('''
                                                            UPDATE thread 
                                                            SET votes = votes + $1
                                                            WHERE id = $2
                                                            RETURNING author, created, forum, id, message, slug, title, votes
                                                            ''', 2 if int(data.get('voice')) > 0 else -2, thread_id)
                    result_thread = dict(result_thread)
                    result_thread['created'] = result_thread['created'].isoformat()
                    return json_response(result_thread, status=200)

                await connection.execute('''
                                       INSERT INTO vote(user_id, thread_id, vote)
                                       VALUES ($1, $2, $3)
                                       ''', user_id, thread_id, 1 if int(data.get('voice')) > 0 else -1)
                result_thread = await connection.fetchrow('''
                                                       UPDATE thread 
                                                       SET votes = votes + $1
                                                       WHERE id = $2
                                                       RETURNING author, created, forum, id, message, slug, title, votes
                                                       ''', 1 if int(data.get('voice')) > 0 else -1, thread_id)
                result_thread = dict(result_thread)
                result_thread['created'] = result_thread['created'].isoformat()
                return json_response(result_thread, status=200)