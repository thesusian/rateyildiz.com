#!/bin/bash

# Environment setup
VENV_PATH=".venv"
PYTHON="$VENV_PATH/bin/python"
PIP="$VENV_PATH/bin/pip"
LOG_DIR="logs"
PIDFILE="gunicorn.pid"
WORKERS=3  # (2 x num_cores) + 1 is recommended

# Create logs directory if it doesn't exist
mkdir -p $LOG_DIR

# Ensure virtual environment is activated
source $VENV_PATH/bin/activate

# Install production dependencies if needed
$PIP install gunicorn

# Run database setup and migrations
echo "Setting up database and running migrations..."
$PYTHON << END
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from alembic.config import Config
from alembic import command
from app.database import SQLALCHEMY_DATABASE_URL

DATABASE_URL = SQLALCHEMY_DATABASE_URL

def create_database_if_not_exists(engine):
    with engine.connect() as connection:
        connection.execute("commit")
        connection.execute(f"CREATE DATABASE {engine.url.database}")

def run_migrations():
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", DATABASE_URL)
    command.upgrade(alembic_cfg, "head")

def main():
    engine = create_engine(DATABASE_URL)
    try:
        engine.connect()
        print("Database exists, proceeding with migrations.")
    except OperationalError:
        print("Database does not exist, creating now.")
        create_database_if_not_exists(engine)

    run_migrations()
    print("Migrations completed.")

if __name__ == "__main__":
    main()
END

# Compile translations
echo "Compiling translations..."
pybabel compile -d translations

# Kill any existing Gunicorn process
if [ -f $PIDFILE ]; then
    echo "Stopping existing Gunicorn process..."
    kill $(cat $PIDFILE) || true
    rm $PIDFILE
fi

# Start Gunicorn
echo "Starting Gunicorn server..."
gunicorn app.main:app \
    --bind 0.0.0.0:8001 \
    --workers $WORKERS \
    --worker-class uvicorn.workers.UvicornWorker \
    --pid $PIDFILE \
    --daemon \
    --access-logfile "$LOG_DIR/access.log" \
    --error-logfile "$LOG_DIR/error.log" \
    --capture-output \
    --log-level info \
    --timeout 120

# Check if Gunicorn started successfully
sleep 2
if [ -f $PIDFILE ] && kill -0 $(cat $PIDFILE) 2>/dev/null; then
    echo "Server started successfully! PID: $(cat $PIDFILE)"
    echo "Logs are available in the $LOG_DIR directory"
else
    echo "Failed to start server"
    exit 1
fi
