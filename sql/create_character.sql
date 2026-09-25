CREATE
OR REPLACE FUNCTION create_character(
    user_id TEXT,
    challenge_count INTEGER DEFAULT 3
) RETURNS "Character" LANGUAGE plpgsql AS $ $ DECLARE v_secret_id INTEGER;

v_quest_id INTEGER;

v_challenge_ids INTEGER [];

v_background_id INTEGER;

v_cover_id INTEGER;

v_character "Character";

BEGIN
SELECT
    cs.id INTO v_secret_id
FROM
    "Character_Secret" AS cs
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
    "Character_Quest" AS cq
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
    ARRAY(
        SELECT
            cc.id
        FROM
            "Character_Challenge" AS cc
        WHERE
            (
                SELECT
                    COUNT(*)
                FROM
                    "Character_Challenges" AS ccm
                WHERE
                    ccm.challenge_id = cc.id
            ) < cc.max_usage
        ORDER BY
            random()
        LIMIT
            challenge_count
    ) INTO v_challenge_ids;

SELECT
    cb.id INTO v_background_id
FROM
    "Character_Background" AS cb
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
    "Character_Cover" AS cv
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
        background_id,
        cover_id
    )
VALUES
    (
        user_id,
        v_secret_id,
        v_quest_id,
        v_background_id,
        v_cover_id
    ) RETURNING * INTO v_character;

INSERT INTO
    "Character_Challenges" (character_id, challenge_id)
SELECT
    v_character.id,
    challenge_id
FROM
    unnest(
        COALESCE(v_challenge_ids, ARRAY [] :: INTEGER [])
    ) AS challenge_id;

RETURN v_character;

END;

$ $;