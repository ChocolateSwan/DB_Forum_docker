from views.views_Status import Clear, Status
from views.views_User import *
from views.views_Forum import *
from views.views_Thread import *
from views.views_Post import *
from views.views_Vote import *

# Первый элемент — http метод, далее расположен url,
# третьим в кортеже идёт объект handler,
# и напоследок — имя route, чтобы удобно было его вызывать в коде.
routes = [
    ('POST', '/api/service/clear', Clear, 'clear'),
    ('GET', '/api/service/status', Status, 'status'),
    ('POST', '/api/user/{nickname}/create', UserCreate, 'create_user'),
    ('*', '/api/user/{nickname}/profile', UserProfile, 'profile_user'),
    ('POST', '/api/forum/create', ForumCreate, 'create_forum'),
    ('GET', '/api/forum/{slug}/details', ForumDetails, 'details_forum'),
    ('POST', '/api/forum/{slug}/create', ThreadCreate, 'create_thread'),
    ('GET', '/api/forum/{slug}/threads', ForumThreads, 'threads_forum'),
    ('GET', '/api/forum/{slug}/users', ForumUsers, 'users_forum'),
    ('*', '/api/thread/{slug_or_id}/details', ThreadDetails, 'details_thread'),
    ('POST', '/api/thread/{slug_or_id}/create', PostCreate, 'create_post'),
    ('GET', '/api/thread/{slug_or_id}/posts', GetPosts, 'get_posts'),
    ('*', '/api/post/{id}/details', OnePost, 'one_post'),
    ('POST', '/api/thread/{slug_or_id}/vote', VoteCreate, 'create_vote'),


]