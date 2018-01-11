create_user = '''
with try_insert as 
(
    INSERT INTO "User" (about, email, fullname, nickname) 
    VALUES ($1, $2, $3, $4)
    ON CONFLICT DO NOTHING
    RETURNING about, email, fullname, nickname, true
)
                
                select * 
                from try_insert
                
                union all
                
                select about, email, fullname, nickname, false 
                from "User" 
                where nickname = $4 or email = $2'''

get_user = '''
select about, email, fullname, nickname 
from "User" 
where nickname = $1'''

has_email = '''
select 1
from "User"
where email = $1
;'''

update_user = '''update "User"
set 
  about = case when $1::citext is not null
     then $1
     else about
  end,
  fullname = case when $2::citext is not null
    then $2
    else fullname
  end,
  email = case when $3::citext is not null
     then $3
     else email
  end
where nickname = $4
returning nickname, fullname, about, email
; '''



