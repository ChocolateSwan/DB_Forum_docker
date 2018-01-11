CREATE TABLE users_per_forum
(
    id SERIAL PRIMARY KEY NOT NULL,
    forum_id INT NOT NULL,
    user_id INT NOT NULL
    --CONSTRAINT forum_users_forum_id_fk FOREIGN KEY (forum_ID) REFERENCES forum (id),
    --CONSTRAINT forum_users_user_id_fk FOREIGN KEY (user_ID) REFERENCES "User" (id)
);
CREATE UNIQUE INDEX "users_per_forum_forum_id_user_id_index" ON users_per_forum (forum_id, user_id)
