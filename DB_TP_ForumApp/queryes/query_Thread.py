select_user_id_for_thread = '''
select id, nickname
from "User" 
where nickname = $1
'''

select_forum_id_for_thread = '''
select id, slug from "forum" where slug = $1
'''


create_thread = '''
with try_insert as 
(
INSERT INTO thread (author_id,author, forum_id, forum, message, slug, title, created) 
VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
ON CONFLICT DO NOTHING
RETURNING author, created, forum, id, message, slug, title, votes, true
)
 select * 
from try_insert

union all

select author, created, forum, id, message, slug, title, votes, false 
from thread 
where slug = $6
'''


select_threads = '''
select (author_id,author, forum_id, forum, message, slug, title, created)
from thread
where created >= $
order by creadted $
limit 
'''