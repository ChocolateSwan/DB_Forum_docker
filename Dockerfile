FROM ubuntu:16.04

MAINTAINER Surikova Olga

# Обвновление списка пакетов
RUN apt-get -y update

#
# Установка postgresql
#
ENV PGVER 9.5
RUN apt-get install -y postgresql-$PGVER

# Установка Python3
RUN apt-get install -y python3.5
RUN apt-get update
RUN apt-get install -y python3-pip 
RUN pip3 install --upgrade pip
RUN pip3 install aiohttp
RUN pip3 install asyncpg
RUN pip3 install python-dateutil
RUN pip3 install pytz
RUN pip3 install gunicorn


USER postgres

# Create a PostgreSQL role named ``postgresuser`` with ``postgres`` as the password and
# then create a database `dbapi` owned by the ``docker`` role.
RUN /etc/init.d/postgresql start &&\
    psql --command "CREATE USER postgresuser WITH SUPERUSER PASSWORD 'postgres';" &&\
    createdb -E UTF8 -T template0 -O postgresuser forumtp &&\
    /etc/init.d/postgresql stop

# Adjust PostgreSQL configuration so that remote connections to the
# database are possible.
RUN echo "host all  all    0.0.0.0/0  md5" >> /etc/postgresql/$PGVER/main/pg_hba.conf

RUN echo "listen_addresses='*'" >> /etc/postgresql/$PGVER/main/postgresql.conf
RUN echo "synchronous_commit=off" >> /etc/postgresql/$PGVER/main/postgresql.conf

# Expose the PostgreSQL port
EXPOSE 5432

# Add VOLUMEs to allow backup of config, logs and databases
VOLUME  ["/etc/postgresql", "/var/log/postgresql", "/var/lib/postgresql"]

# Back to the root user
USER root

# Копируем исходный код в Docker-контейнер
ENV WORK /opt/TP
ADD ./DB_TP_ForumApp/ $WORK/DB_TP_ForumApp/
#ADD dataBase.sql $WORK/dataBase.sql

# Объявлем порт сервера
EXPOSE 5001

#
# Запускаем PostgreSQL и сервер
#
ENV PGPASSWORD postgres
CMD service postgresql start &&\
	psql -h localhost -U postgresuser -d forumtp -f $WORK/DB_TP_ForumApp/SQL/settings.sql &&\
	psql -h localhost -U postgresuser -d forumtp -f $WORK/DB_TP_ForumApp/SQL/User_table.sql &&\
	psql -h localhost -U postgresuser -d forumtp -f $WORK/DB_TP_ForumApp/SQL/Forum_table.sql &&\
	psql -h localhost -U postgresuser -d forumtp -f $WORK/DB_TP_ForumApp/SQL/Users_per_forum_table.sql &&\
	psql -h localhost -U postgresuser -d forumtp -f $WORK/DB_TP_ForumApp/SQL/Thread_table.sql &&\
	psql -h localhost -U postgresuser -d forumtp -f $WORK/DB_TP_ForumApp/SQL/Post_table.sql &&\
	psql -h localhost -U postgresuser -d forumtp -f $WORK/DB_TP_ForumApp/SQL/Vote_table.sql &&\
	cd $WORK/DB_TP_ForumApp/ &&\
#	python manage.py runserver
# python3 ./app.py
gunicorn app:app --bind :5001 --worker-class aiohttp.worker.GunicornWebWorker --timeout 90
# gunicorn -b :5000 DB_TP_ForumApp.wsgi
