import os

# PostgreSQL
PG_HOST = os.getenv("PGHOST", "distracted_wing")
PG_PORT = int(os.getenv("PGPORT", "5432"))
PG_DB   = os.getenv("PGDATABASE", "postgres")
PG_USER = os.getenv("PGUSER", "postgres")
PG_PASS = os.getenv("PGPASSWORD", "password")