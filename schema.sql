drop table if exists users;
create table users (
  user_id integer primary key autoincrement,
  username text not null,
  pw_hash text not null,
  ncomms integer not null default 5,
  nclusters integer not null default 2,
  creation_time integer
);
drop table if exists library;
create table library (
  paper_id integer not null,
  user_id integer not null,
  timestamp DATE not null
);
drop table if exists world;
create table world (
  paper_id integer primary key,
  title text not null,
  journal text not null,
  volume integer not null,
  issue integer not null,
  timestamp date default (date('now'))
);
