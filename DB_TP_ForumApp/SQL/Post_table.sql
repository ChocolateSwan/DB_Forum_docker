CREATE TABLE post
(
    id SERIAL PRIMARY KEY NOT NULL,
    author_id INT NOT NULL,
    author citext COLLATE pg_catalog.ucs_basic NOT NULL,
    created TIMESTAMP with time zone DEFAULT now() NOT NULL,
    forum_id INT NOT NULL,
    forum citext COLLATE pg_catalog.ucs_basic NOT NULL,
    isEdited BOOLEAN DEFAULT FALSE NOT NULL,
    message TEXT NOT NULL,
    root_parent INT DEFAULT 0,
    parent INT DEFAULT 0,
    path integer[] DEFAULT '{}'::integer[],
    thread_id INT NOT NULL,

  CONSTRAINT Post_forum_id_fk FOREIGN KEY (forum_id)
      REFERENCES Forum (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION,
  CONSTRAINT Post_thread_id_fk FOREIGN KEY (thread_id)
      REFERENCES public.thread (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION,
  CONSTRAINT Post_user_id_fk FOREIGN KEY (author_id)
      REFERENCES public."User" (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION
);
CREATE INDEX "post_author_id_index" on public.post(author_id);
CREATE INDEX "post_forum_id_index" on public.post(forum_id);
CREATE INDEX "post_thread_id_parent_index" on public.post(thread_id, parent);
CREATE INDEX "post_root_parent_index" on public.post(root_parent);
CREATE INDEX "post_parent_path_index" ON public.post USING GIN ("path");
