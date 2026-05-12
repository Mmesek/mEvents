import os
from src.db import Base

with open("static/service-worker.js", encoding="utf-8") as file:
    SERVICE_WORKER = file.read()

with open("static/app.js", encoding="utf-8") as file:
    PWA_SCRIPT = (
        file.read()
        .replace("{VAPID_PUBLIC_KEY}", os.getenv("VAPID_PUBLIC_KEY"))
        .replace("{BASE_URL}", os.getenv("BASE_URL", "http://localhost:5001"))
    )

MANIFEST = {
    "name": os.getenv("APP_NAME"),
    "short_name": os.getenv("SHORT_NAME"),
    "start_url": "/events/",
    "display": "standalone",
    "background_color": "#0C0A09",
    "theme_color": "#F6AF62",
    "icons": [
        {"src": os.getenv("ICON_192", "/icon.png"), "sizes": "192x192", "type": "image/png"},
        {"src": os.getenv("ICON_512", "/icon.png"), "sizes": "512x512", "type": "image/png"},
    ],
}


class Notification(Base):
    user_id: str
    subscription: str
    scope: str


SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect width="100" height="100" rx="18" fill="#f97316"/>
  <!-- Ciało kalendarza -->
  <rect x="14" y="28" width="72" height="58" rx="8" fill="white"/>
  <!-- Nagłówek -->
  <rect x="14" y="28" width="72" height="22" rx="8" fill="#ea580c"/>
  <rect x="14" y="42" width="72" height="8" fill="#ea580c"/>
  <!-- Uchwyty -->
  <rect x="30" y="18" width="10" height="16" rx="5" fill="white"/>
  <rect x="60" y="18" width="10" height="16" rx="5" fill="white"/>
  <!-- Siatka dni -->
  <rect x="22" y="58" width="10" height="10" rx="3" fill="#fed7aa"/>
  <rect x="37" y="58" width="10" height="10" rx="3" fill="#fed7aa"/>
  <rect x="52" y="58" width="10" height="10" rx="3" fill="#f97316"/>
  <rect x="67" y="58" width="10" height="10" rx="3" fill="#fed7aa"/>
  <rect x="22" y="73" width="10" height="10" rx="3" fill="#fed7aa"/>
  <rect x="37" y="73" width="10" height="10" rx="3" fill="#fed7aa"/>
  <rect x="52" y="73" width="10" height="10" rx="3" fill="#fed7aa"/>
</svg>
"""
