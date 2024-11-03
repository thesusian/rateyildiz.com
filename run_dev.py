#!.venv/bin/python

from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from alembic.config import Config
from alembic import command
from app.database import SQLALCHEMY_DATABASE_URL
import subprocess

DATABASE_URL = SQLALCHEMY_DATABASE_URL

def create_database_if_not_exists(engine):
    """Create the database if it does not exist."""
    with engine.connect() as connection:
        connection.execute("commit")  # Ensure no transaction is active
        connection.execute(f"CREATE DATABASE {engine.url.database}")

def run_migrations():
    """Run Alembic migrations."""
    alembic_cfg = Config("alembic.ini")  # Path to your alembic.ini file
    alembic_cfg.set_main_option("sqlalchemy.url", DATABASE_URL)

    command.upgrade(alembic_cfg, "head")

def main():
    # Create an engine instance
    engine = create_engine(DATABASE_URL)

    # Check if the database exists and create it if not
    try:
        engine.connect()
        print("Database exists, proceeding with migrations.")
    except OperationalError:
        print("Database does not exist, creating now.")
        create_database_if_not_exists(engine)

    # Run migrations
    run_migrations()
    print("Migrations completed.")

    # I think you can replace these with normal python
    subprocess.run(["pybabel", "compile", "-d", "translations"])
    subprocess.run(["uvicorn", "app.main:app", "--reload", "--host", "localhost", "--port", "8000"])

if __name__ == "__main__":
    main()
