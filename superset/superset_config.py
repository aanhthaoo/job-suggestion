"""Superset runtime configuration (mounted into the container).

Sets a strong SECRET_KEY so the image stops refusing to start, and keeps the
metadata DB on the persistent superset_home volume.
"""
import os

# Strong key; override via SUPERSET_SECRET_KEY env in production.
SECRET_KEY = os.environ.get(
    "SUPERSET_SECRET_KEY",
    "EjlTdgHcmLxpsh7ZS7BGYPmRGXmq3/mBjsigYc/vLv2JAxiNRCN4xo4N",
)

# Metadata database (Superset's own state) on the persistent volume.
SQLALCHEMY_DATABASE_URI = os.environ.get(
    "SQLALCHEMY_DATABASE_URI",
    "sqlite:////app/superset_home/superset.db",
)

# Demo conveniences
WTF_CSRF_ENABLED = False
FEATURE_FLAGS = {"ENABLE_TEMPLATE_PROCESSING": True}
