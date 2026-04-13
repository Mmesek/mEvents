CREATE
OR REPLACE VIEW users AS
SELECT
  DISTINCT r.user_id AS id,
  CASE
    WHEN (u.raw_user_meta_data ? 'full_name' :: text) THEN (u.raw_user_meta_data ->> 'full_name' :: text)
    ELSE split_part(
      (u.raw_user_meta_data ->> 'email' :: text),
      '@' :: text,
      1
    )
  END AS display_name,
  r.event_id,
  max(r."timestamp") AS "timestamp"
FROM
  (
    "Response" r
    LEFT JOIN auth.users u ON ((u.id = r.user_id))
  )
GROUP BY
  r.user_id,
  r.event_id,
  CASE
    WHEN (u.raw_user_meta_data ? 'full_name' :: text) THEN (u.raw_user_meta_data ->> 'full_name' :: text)
    ELSE split_part(
      (u.raw_user_meta_data ->> 'email' :: text),
      '@' :: text,
      1
    )
  END;