CREATE OR REPLACE VIEW users AS
SELECT
  id,
  CASE 
    WHEN raw_user_meta_data ? 'full_name' THEN raw_user_meta_data->>'full_name'
    ELSE SPLIT_PART(raw_user_meta_data->>'email', '@', 1)
  END AS display_name
FROM auth.users;