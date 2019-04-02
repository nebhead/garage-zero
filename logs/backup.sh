#!/bin/sh

NOW=$(date +"%Y-%m-%d")
LOGFILE="/home/pi/garage-zero/logs/backuplog-$NOW.log"

mv /home/pi/garage-zero/events.log $LOGFILE
touch /home/pi/garage-zero/events.log
