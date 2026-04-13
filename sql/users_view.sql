CREATE
OR REPLACE VIEW forms.users AS
SELECT
  DISTINCT u.id AS id,
  COALESCE(
    u.raw_user_meta_data ->> 'full_name',
    split_part(u.raw_user_meta_data ->> 'email', '@', 1)
  ) AS display_name,
  r.event_id,
  MAX(r."timestamp") AS "timestamp"
FROM
  auth.users u
  INNER JOIN forms."Response" r ON u.id = r.user_id
GROUP BY
  u.id,
  r.event_id,
  u.raw_user_meta_data;