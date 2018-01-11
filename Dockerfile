FROM ubuntu:16.04

MAINTAINER Surikova Olga

# Обвновление списка пакетов
RUN apt-get -y update

#
# Установка postgresql
#
ENV PGVER 9.5
ENV PGPASSWORD postgres
RUN apt-get update
RUN apt-get install -y postgresql-$PGVER

# Установка Python3
RUN apt-get install -y python3.5

RUN apt-get install -y python3-pip 
RUN pip3 install --upgrade pip
RUN pip3 install aiohttp
RUN pip3 install asyncpg
RUN pip3 install python-dateutil
RUN pip3 install pytz
RUN pip3 install gunicorn

# Копируем исходный код в Docker-контейнер
ENV WORK /opt/TP
ADD ./DB_TP_ForumApp/ $WORK/
EXPOSE 5000

USER postgres

RUN /etc/init.d/postgresql start &&\
    psql --command "CREATE USER postgresuser WITH SUPERUSER PASSWORD 'postgres';" &&\
    createdb -E UTF8 -T template0 -O postgresuser forumtp &&\
	psql -h localhost -U postgresuser -d forumtp -f $WORK/SQL/settings.sql &&\
	psql -h localhost -U postgresuser -d forumtp -f $WORK/SQL/User_table.sql &&\
	psql -h localhost -U postgresuser -d forumtp -f $WORK/SQL/Forum_table.sql &&\
	psql -h localhost -U postgresuser -d forumtp -f $WORK/SQL/Users_per_forum_table.sql &&\
	psql -h localhost -U postgresuser -d forumtp -f $WORK/SQL/Thread_table.sql &&\
	psql -h localhost -U postgresuser -d forumtp -f $WORK/SQL/Post_table.sql &&\
	psql -h localhost -U postgresuser -d forumtp -f $WORK/SQL/Vote_table.sql &&\
    /etc/init.d/postgresql stop

RUN echo "host all  all    0.0.0.0/0  md5" >> /etc/postgresql/$PGVER/main/pg_hba.conf
RUN echo "listen_addresses='*'" >> /etc/postgresql/$PGVER/main/postgresql.conf
RUN echo "synchronous_commit=off" >> /etc/postgresql/$PGVER/main/postgresql.conf
EXPOSE 5432
VOLUME  ["/etc/postgresql", "/var/log/postgresql", "/var/lib/postgresql"]

USER root

WORKDIR $WORK
CMD service postgresql start &&\
	gunicorn app2:app2 --bind :5000 --worker-class aiohttp.worker.GunicornWebWorker --timeout 90
