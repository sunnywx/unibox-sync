CREATE TABLE IF NOT EXISTS [movie_en_us](
    [movie_id] Integer NOT NULL,
    [movie_name] text NOT NULL,
    [director] text DEFAULT '',
    [actor] text DEFAULT '',
    [genre] text DEFAULT '',
    [running_time] text DEFAULT '',
    [nation] text DEFAULT '',
    [release_time] DATETIME DEFAULT 0,
    [play_time] DATETIME DEFAULT 0,
    [dub_language] text DEFAULT '',
    [subtitling] text DEFAULT '',
    [audio_format] text DEFAULT '',
    [content_class] text DEFAULT '',
    [color] text DEFAULT '',
    [per_number] Integer DEFAULT 0,
    [medium] text DEFAULT '',
    [bar_code] text DEFAULT '',
    [isrc_code] text DEFAULT '',
    [area_code] text DEFAULT '',
    [import_code] text DEFAULT '',
    [fn_name] text DEFAULT '',
    [box_office] text DEFAULT '',
    [bullet_films] text DEFAULT '',
    [issuing_company] text DEFAULT '',
    [copyright] text DEFAULT '',
    [synopsis] text DEFAULT '',
    [movie_desc] text DEFAULT '',
    [movie_img] text DEFAULT '',
    [movie_img_url] TEXT,
    [movie_thumb] text DEFAULT '',
    [movie_thumb_url] TEXT,
    [version_num] BIGINT(10),
    [movie_name_pinyin] text DEFAULT '',
    [movie_name_fpinyin] text DEFAULT '',
    [is_delete] Integer DEFAULT 0
    );

CREATE UNIQUE INDEX IF NOT EXISTS [movie_en_us_idx1]
ON [movie_en_us](
    [movie_id]);

CREATE TRIGGER IF NOT EXISTS [trg_movie_en_us_delete] AFTER DELETE ON [movie_en_us]
BEGIN
    REPLACE INTO [tabledirty]
        ([tablename],
        [lastupdatetime])
        VALUES ('movie_en_us', STRFTIME ('%s', DATETIME ('now', 'localtime')));
END;

CREATE TRIGGER IF NOT EXISTS [trg_movie_en_us_insert] AFTER INSERT ON [movie_en_us]
BEGIN
    REPLACE INTO [tabledirty]
        ([tablename],
        [lastupdatetime])
        VALUES ('movie_en_us', STRFTIME ('%s', DATETIME ('now', 'localtime')));
END;

CREATE TRIGGER IF NOT EXISTS [trg_movie_en_us_update] AFTER UPDATE ON [movie_en_us]
BEGIN
    REPLACE INTO [tabledirty]
        ([tablename],
        [lastupdatetime])
        VALUES ('movie_en_us', STRFTIME ('%s', DATETIME ('now', 'localtime')));
END;
