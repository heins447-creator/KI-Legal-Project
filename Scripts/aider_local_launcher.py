# -*- coding: utf-8 -*-
import os
import runpy
import sys

os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("NO_COLOR", "1")
os.environ.setdefault("RICH_NO_COLOR", "1")
os.environ.setdefault("PY_COLORS", "0")
os.environ.setdefault("CLICOLOR", "0")
os.environ.setdefault("TERM", "dumb")

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

try:
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

AIDER_SITE = r"I:\KI_Legal_Project\Tools\Aider\site"

if AIDER_SITE not in sys.path:
    sys.path.insert(0, AIDER_SITE)

sys.argv = ["aider"] + sys.argv[1:]
runpy.run_module("aider", run_name="__main__")