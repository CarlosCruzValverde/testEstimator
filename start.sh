#!/bin/bash

# Initialize if needed
if [ ! -d "migrations" ]; then
    flask db init
fi

# Create fresh migration (safely)
if [ ! -f "migrations/versions/*_initial_tables.py" ]; then
    flask db migrate -m "initial tables"
fi

# Apply migrations
flask db upgrade

# Fallback: Create tables directly if migrations failed
flask init-db

# Run the database seeder
python scripts/database_seeder.py

# Start app
gunicorn -c gunicorn_config.py wsgi:app