import os
import sys

if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
    templates_path = os.path.join(BASE_DIR, "templates")
    static_path = os.path.join(BASE_DIR, "static")
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    templates_path = os.path.join(BASE_DIR, "..", "templates")
    static_path = os.path.join(BASE_DIR, "..", "static") 