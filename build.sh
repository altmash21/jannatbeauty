#!/bin/bash
# Build script for Django project

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Start server
python manage.py runserver
