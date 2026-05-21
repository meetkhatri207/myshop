#!/usr/bin/env bash
# exit on error
set -o errexit

# 1. Install dependencies using requirements.txt
pip install -r requirements.txt

# 2. Collect Static Files (Crucial for production Django)
python manage.py collectstatic --no-input

# 3. Run database migrations
python manage.py migrate