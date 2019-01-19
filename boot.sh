#!/bin/sh
cd /home/pi/garage-zero
# Run via Gunicorn / nginx
sudo gunicorn app:app &
# Run via Python
sudo python control.py &
