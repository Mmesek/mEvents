import supabase, os
import dotenv

dotenv.load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

s = supabase.create_client(SUPABASE_URL, SUPABASE_KEY).schema("forms")
