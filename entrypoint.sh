#!/bin/sh
# entrypoint.sh
gunicorn --bind :3000 --workers 2 nakeschat_bot:monitor &
python3 nakeschat_bot.py
