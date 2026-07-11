import os
import sys

# Ensure src is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.interfaces.web import create_app

app = create_app()
