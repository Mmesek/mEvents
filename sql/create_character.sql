CREATE
OR REPLACE FUNCTION create_character(user_id TEXT) RETURNS "Character" LANGUAGE plpgsql AS $ $ DECLARE v_secret_id INTEGER;

v_quest_id INTEGER;

v_challenge_id INTEGER;

v_background_id INTEGER;

v_cover_id INTEGER;

v_character "Character";

BEGIN
SELECT
    cs.id INTO v_secret_id
FROM
    Character_secret AS cs
WHERE
    (
        SELECT
            COUNT(*)
        FROM
            "Character" AS c
        WHERE
            c.secret_id = cs.id
    ) < cs.max_usage
ORDER BY
    random()
LIMIT
    1;

SELECT
    cq.id INTO v_quest_id
FROM
    Character_quest AS cq
WHERE
    (
        SELECT
            COUNT(*)
        FROM
            "Character" AS c
        WHERE
            c.quest_id = cq.id
    ) < cq.max_usage
ORDER BY
    random()
LIMIT
    1;

SELECT
    cc.id INTO v_challenge_id
FROM
    Character_challenge AS cc
WHERE
    (
        SELECT
            COUNT(*)
        FROM
            "Character" AS c
        WHERE
            c.challenge_id = cc.id
    ) < cc.max_usage
ORDER BY
    random()
LIMIT
    1;

SELECT
    cb.id INTO v_background_id
FROM
    Character_background AS cb
WHERE
    (
        SELECT
            COUNT(*)
        FROM
            "Character" AS c
        WHERE
            c.background_id = cb.id
    ) < cb.max_usage
ORDER BY
    random()
LIMIT
    1;

SELECT
    cv.id INTO v_cover_id
FROM
    Character_cover AS cv
WHERE
    (
        SELECT
            COUNT(*)
        FROM
            "Character" AS c
        WHERE
            c.cover_id = cv.id
    ) < cv.max_usage
ORDER BY
    random()
LIMIT
    1;

INSERT INTO
    "Character" (
        id,
        secret_id,
        quest_id,
        challenge_id,
        background_id,
        cover_id
    )
VALUES
    (
        user_id,
        v_secret_id,
        v_quest_id,
        v_challenge_id,
        v_background_id,
        v_cover_id
    ) RETURNING * INTO v_character;

RETURN v_character;

END;

$ $;