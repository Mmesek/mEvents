import supabase, os
import dotenv

dotenv.load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supa = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)
s = supa.schema("forms")
