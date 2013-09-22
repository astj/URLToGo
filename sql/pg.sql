CREATE TABLE bookmarks (
    id serial PRIMARY KEY,
    url text NOT NULL,
    title text,
    owner_user_id integer NOT NULL,
    visited_time timestamp without time zone,
    entry_time timestamp without time zone NOT NULL,
    comment text
);

CREATE TABLE users (
    id serial PRIMARY KEY,
    username text NOT NULL,
    password text NOT NULL,
    email text NOT NULL
);
