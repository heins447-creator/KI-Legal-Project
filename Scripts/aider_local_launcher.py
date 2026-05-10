# -*- coding: utf-8 -*-
import runpy
import sys

AIDER_SITE = r"I:\KI_Legal_Project\Tools\Aider\site"

if AIDER_SITE not in sys.path:
    sys.path.insert(0, AIDER_SITE)

sys.argv = ["aider"] + sys.argv[1:]
runpy.run_module("aider", run_name="__main__")
