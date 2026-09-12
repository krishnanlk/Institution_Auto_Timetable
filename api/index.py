import os
import sys

# Ensure root directory is in python module search path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Import the Flask app
from app import app

# Vercel serverless function entrypoint
# app is the WSGI callable
