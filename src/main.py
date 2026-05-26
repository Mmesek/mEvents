from fasthtml import common as fh

import src.modules.login
import src.modules.events
import src.modules.responses
import src.modules.contributions
import src.modules.tickets
import src.modules.forms
import src.modules.new_form
import src.modules.new_event
import src.modules.profile
import src.modules.clues
from src.root import app
import src.modules.pwa
import src.modules.discord
import src.components.translations

import sentry_sdk
import dotenv
import os

dotenv.load_dotenv()
if os.getenv("SENTRY_URL"):
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_URL"),
        # Add data like request headers and IP for users,
        # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
        send_default_pii=True,
        # Enable sending logs to Sentry
        enable_logs=True,
    )

if __name__ == "__main__":
    fh.serve()
