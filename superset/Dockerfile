FROM apache/superset:latest

USER root
# The stock image ships without a PostgreSQL driver, and Superset runs from a
# uv-managed virtualenv at /app/.venv that has no pip. Install psycopg2 into
# that venv with uv so the running app can import it.
RUN uv pip install --python /app/.venv/bin/python --no-cache psycopg2-binary
USER superset
