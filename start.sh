#!/bin/bash

# Run migrations
echo "Running database migrations..."
flask db upgrade

# Start Gunicorn with your config
echo "Starting Gunicorn..."
gunicorn -c gunicorn_config.py wsgi:app