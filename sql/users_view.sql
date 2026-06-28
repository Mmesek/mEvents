CREATE
OR REPLACE VIEW forms.users AS
SELECT
  DISTINCT u.id AS id,
  COALESCE(
    p.display_name,
    COALESCE(
      u.raw_user_meta_data ->> 'full_name',
      split_part(u.raw_user_meta_data ->> 'email', '@', 1)
    )
  ) AS display_name,
  r.event_id,
  COALESCE(p.email, u.email) AS email,
  MAX(r."timestamp") AS "timestamp"
FROM
  auth.users u
  INNER JOIN forms."Response" r ON u.id = r.user_id FULL
  OUTER JOIN forms."Profile" p ON u.id = p.user_id
GROUP BY
  u.id,
  r.event_id,
  p.display_name,
  p.email,
  u.raw_user_meta_data;