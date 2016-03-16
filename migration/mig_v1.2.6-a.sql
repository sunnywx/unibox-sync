alter table movie add column movie_name_pinyin text default '';
alter table movie add column movie_name_fpinyin text default '';

alter table title add column contents_type integer default 0;
alter table title add column screen_def integer default 0;
alter table title add column screen_dim integer default 0;