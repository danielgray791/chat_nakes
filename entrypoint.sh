#!/bin/sh
# entrypoint.sh
gunicorn --bind :3000 --workers 2 app:monitor &
python3 app.py
