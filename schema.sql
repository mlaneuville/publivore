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
  timestamp DATE DEFAULT (date('now'))
);
