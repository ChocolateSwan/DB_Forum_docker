CREATE TABLE thread
(
  id SERIAL PRIMARY KEY NOT NULL,
	author_id INT NOT NULL,
	author CITEXT COLLATE pg_catalog.ucs_basic NOT NULL,
  created TIMESTAMP WITH TIME ZONE DEFAULT now(),
  forum_id INT NOT NULL,
  forum CITEXT COLLATE pg_catalog.ucs_basic NOT NULL,
	message TEXT NOT NULL,
	slug CITEXT COLLATE pg_catalog.ucs_basic ,
  title VARCHAR(200) NOT NULL,
  votes INT DEFAULT 0,

  CONSTRAINT thread_forum_id_fk FOREIGN KEY (forum_id)
  REFERENCES public.forum (id) MATCH SIMPLE
  ON UPDATE NO ACTION ON DELETE NO ACTION,
  CONSTRAINT thread_user_id_fk FOREIGN KEY (author_id)
  REFERENCES public."User" (id) MATCH SIMPLE
  ON UPDATE NO ACTION ON DELETE NO ACTION
);

CREATE UNIQUE INDEX thread_slug_unique ON public.thread (slug);
CREATE INDEX "thread_author_index" on public.thread(author_id);
CREATE INDEX "thread_forum_created_index" on public.thread(forum_id, created);
