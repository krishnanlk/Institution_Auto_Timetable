import os
import sys
from urllib.parse import parse_qs, urlencode

# Ensure root directory is in python module search path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import app as flask_app

class VercelWSGIWrapper:
    """WSGI Middleware that cleanly maps Vercel serverless paths and query params."""
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        query_string = environ.get('QUERY_STRING', '')
        qs = parse_qs(query_string, keep_blank_values=True)
        
        # Check if __path parameter was passed by vercel.json rewrite
        if '__path' in qs:
            path_val = qs.pop('__path')[0]
            environ['PATH_INFO'] = '/' + path_val.lstrip('/')
            # Reconstruct clean QUERY_STRING without the internal __path parameter
            environ['QUERY_STRING'] = urlencode(qs, doseq=True)
        else:
            # Fallback for direct invocations or headers
            matched_path = (
                environ.get('HTTP_X_MATCHED_PATH') or
                environ.get('HTTP_X_FORWARDED_URI') or
                environ.get('RAW_URI')
            )
            if matched_path:
                clean = matched_path.split('?')[0]
                if clean and not clean.startswith('/api/index'):
                    environ['PATH_INFO'] = clean
            else:
                path_info = environ.get('PATH_INFO', '')
                if path_info in ('/api/index', '/api/index/'):
                    environ['PATH_INFO'] = '/'
                elif path_info.startswith('/api/index/'):
                    environ['PATH_INFO'] = path_info[len('/api/index'):]

        return self.app(environ, start_response)

# Export app for Vercel Python runtime
app = VercelWSGIWrapper(flask_app)
