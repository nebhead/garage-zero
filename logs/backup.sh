#!/bin/sh

NOW=$(date +"%Y-%m-%d")
LOGFILE="/home/pi/garage-zero/logs/backuplog-$NOW.log"

mv /home/pi/garage-zero/events.log $LOGFILE
cp /home/pi/garage-zero/events.log.template /home/pi/garage-zero/events.log
