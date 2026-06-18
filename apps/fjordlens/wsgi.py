from app import app as application

# Startup: intentionally do not touch filesystem or DB; initialization is lazy during use.

# Gunicorn expects a module-level 'application' or a named app; we expose 'application'.
