async def update_users_per_forum (connection, forum_id, users_id):
    if type(users_id) != type([]):
        users_id = [users_id]
    elif len(users_id) == 0:
        return
    
    for uid in set(users_id):
        await connection.execute('''
                           INSERT INTO users_per_forum (forum_id, user_id)
                           VALUES($1, $2)
                           ON CONFLICT DO NOTHING
                           ''', forum_id, uid)


