from fasthtml import common as fh
from monsterui.all import Theme

HEADERS = [
    *Theme.orange.headers(),
    fh.Style('.required:before {content:" *";color: orange;}'),
    fh.Link(rel="icon", href="/static/icons/favicon.svg"),
    fh.Link(rel="manifest", href="/manifest.json"),
    # Vercel Web Analytics
    fh.Script("window.va = window.va || function () { (window.vaq = window.vaq || []).push(arguments); };"),
    fh.Script(src="/_vercel/insights/script.js", defer=True),
    # Vercel Speed Insights
    fh.Script("window.si = window.si || function () { (window.siq = window.siq || []).push(arguments); };"),
    fh.Script(src="/_vercel/speed-insights/script.js", defer=True),
]
