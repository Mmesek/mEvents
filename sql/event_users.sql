CREATE
OR REPLACE VIEW forms.event_users AS
SELECT
    DISTINCT p.display_name,
    p.user_id,
    u.email,
    r.event_id
FROM
    (
        (
            "Response" r
            JOIN "Profile" p ON ((p.user_id = r.user_id))
        )
        JOIN users_emails u ON ((u.id = r.user_id))
    );