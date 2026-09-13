import os
import sys

# Ensure root directory is in python module search path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import app as flask_app

class VercelWSGIWrapper:
    """WSGI Middleware that fixes Vercel path routing and environment."""
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        path_info_raw = environ.get('PATH_INFO', '')
        if 'debug-env' in path_info_raw or 'debug-env' in str(environ.get('HTTP_X_MATCHED_PATH', '')) or 'debug-env' in str(environ.get('RAW_URI', '')):
            import json
            headers = {k: str(v) for k, v in environ.items() if isinstance(v, (str, int, float, bool))}
            start_response('200 OK', [('Content-Type', 'application/json')])
            return [json.dumps(headers, indent=2).encode('utf-8')]

        # If Vercel passed original matched URL in headers (e.g. /login, /timetable)
        matched_path = (
            environ.get('HTTP_X_MATCHED_PATH') or
            environ.get('HTTP_X_FORWARDED_URI') or
            environ.get('RAW_URI')
        )
        if matched_path:
            clean = matched_path.split('?')[0]
            if clean and not clean.startswith('/api/index'):
                environ['PATH_INFO'] = clean
            if '?' in matched_path and not environ.get('QUERY_STRING'):
                environ['QUERY_STRING'] = matched_path.split('?', 1)[1]
        
        # Strip /api/index prefix if Vercel routed to the function directly
        path_info = environ.get('PATH_INFO', '')
        if path_info in ('/api/index', '/api/index/'):
            environ['PATH_INFO'] = '/'
        elif path_info.startswith('/api/index/'):
            environ['PATH_INFO'] = path_info[len('/api/index'):]

        return self.app(environ, start_response)

# Export app for Vercel Python runtime
app = VercelWSGIWrapper(flask_app)
