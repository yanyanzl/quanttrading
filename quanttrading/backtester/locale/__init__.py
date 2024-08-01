from pathlib import Path
import gettext

localedir = Path(__file__).parent
translations = gettext.translation('backtester', localedir=localedir, fallback=True)

_ = translations.gettext
