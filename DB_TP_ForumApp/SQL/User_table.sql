CREATE TABLE "User"
(
  id SERIAL PRIMARY KEY NOT NULL,
  about TEXT,
  email CITEXT COLLATE pg_catalog.ucs_basic NOT NULL,
  fullname VARCHAR(100) NOT NULL,
  nickname CITEXT COLLATE pg_catalog.ucs_basic NOT NULL
);

CREATE UNIQUE INDEX user_nickname_unique ON "User" (nickname);
CREATE UNIQUE INDEX user_email_unique ON "User" (email);
