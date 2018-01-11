async def update_users_per_forum (connection, forum_id, users_id):
    if type(users_id) is not 'list':
        users_id = [users_id]
    await connection.execute('''
                           INSERT INTO users_per_forum (forum_id, user_id)
                           SELECT $1, t.user_id
                           FROM unnest($2::int[]) t(user_id)
                           ON CONFLICT DO NOTHING
                           ''', forum_id, users_id)

