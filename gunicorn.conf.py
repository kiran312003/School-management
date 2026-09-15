# gunicorn.conf.py — Production WSGI server configuration for Render

import os

# Bind to the port Render assigns via $PORT env var
bind = f"0.0.0.0:{os.environ.get('PORT', '5000')}"

# Workers: (2 × CPU cores) + 1  — Render free tier has 1 vCPU
workers = 2

# Worker class
worker_class = "sync"

# Timeout (seconds) — increase for slow DB cold starts
timeout = 120

# Logging
accesslog = "-"   # stdout
errorlog  = "-"   # stderr
loglevel  = "info"
