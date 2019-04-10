# *****************************************
# Garage Door Control Python script
# *****************************************
#
# Description: This script will read the states.txt file and set relays/LEDs
# upon any changes to that file.  This script also accepts input from the IR
# sensor and will write the states.txt file and set the relays appropriately.
#
# This script runs as a separate process from the Flask / Gunicorn
# implementation which handles the web interface.
#
# *****************************************

# Imports
import time
import datetime
import os
import json
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
import urllib2
import urllib
import RPi.GPIO as GPIO
from common import *

# GPIO Definitions
relay_pin = 14			# GPIO 14, Pin 08 (RasPi Header)
relay_gate_pin = 15		# GPIO 15, Pin 10 (RasPi Header)
switch_pin = 18			# GPIO 18, Pin 12 (RasPi Header)

# Init GPIO's to default values / behavior
GPIO.setmode(GPIO.BCM)

GPIO.setup(relay_pin, GPIO.OUT, initial=0) # Setup Relay IN1 on GPIO
GPIO.setup(relay_gate_pin, GPIO.OUT, initial=0) # Setup Relay IN2 on GPIO

GPIO.setup(switch_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # Setup Magnetic Switch on GPIO18 (set pull down)

timer_start = 0 # Initialize timer_start variable, set to 0
reminder_timer_start = 0 # Initialize reminder_timer_start, set to 0
notify_on_close = False # Initialize the flag for notifying that the door has closed
opened_at = 0 # Time the door was opened

def SendEmail(settings, notifyevent):
	# WriteLog("[DEBUG]: SndEmail Function. " + notifyevent)
	now = datetime.datetime.now()

	if notifyevent == "GarageEvent_Open_Alarm" or notifyevent == "GarageEvent_StillOpen_Alarm":
		open_minutes = int((time.time() - opened_at) / 60)
		notifymessage = "GarageZero wants you to know that your garage door has been open for %d minutes at %s" % (open_minutes, now)
		subjectmessage = "GarageZero: Door Open for %d Minutes" % open_minutes
	elif notifyevent == "GarageEvent_Closed":
		notifymessage = "GarageZero wants you to know that your garage door was closed at " + str(now)
		subjectmessage = "GarageZero: Closed at " + str(now)
	elif notifyevent == "GarageEvent_Notify_on_Open":
		return # don't send emails for these
	else:
		notifymessage = "Whoops! GarageZero had the following unhandled notify event: " + notifyevent + " at " + str(now)
		subjectmessage = "GarageZero: Unknown Notification at " + str(now)

	try:
		fromaddr = settings['email']['FromEmail']
		toaddr = settings['email']['ToEmail']
		toaddrlist = [addr.strip() for addr in toaddr.split(',')] # split on commas and strip out any spaces

		msg = MIMEMultipart()
		msg['From'] = fromaddr
		msg['To'] = ', '.join(toaddrlist)
		msg['Subject'] = subjectmessage
		body = notifymessage
		msg.attach(MIMEText(body, 'plain'))

		server = smtplib.SMTP(settings['email']['SMTPServer'], settings['email']['SMTPPort'])
		if settings['email']['UseTLS']:
			server.starttls()
		if settings['email']['Username']:
			server.login(settings['email']['Username'], settings['email']['Password'])
		text = msg.as_string()
		server.sendmail(fromaddr, toaddrlist, text)
		server.quit()

		for addr in toaddrlist:
			event = subjectmessage + ". E-mail notification sent to: " + addr
			WriteLog(event)

	except smtplib.SMTPException as e:
		event = "E-mail notification failed. SMTPLib general exception: %s" % e
		WriteLog(event)
	except Exception as e:
		event = "E-mail notification failed, with exception: %s" % e
		WriteLog(event)
	return()


def SendPushoverNotification(settings,notifyevent):
	now = datetime.datetime.now()

	if notifyevent == "GarageEvent_Open_Alarm" or notifyevent == "GarageEvent_StillOpen_Alarm":
		open_minutes = int((time.time() - opened_at) / 60)
		notifymessage = "GarageZero wants you to know that your garage door has been open for %d minutes at %s" % (open_minutes, now)
		subjectmessage = "GarageZero: Door Open for %d Minutes" % open_minutes
	elif notifyevent == "GarageEvent_Closed":
		notifymessage = "GarageZero wants you to know that your garage door was closed at " + str(now)
		subjectmessage = "GarageZero: Closed at " + str(now)
	elif notifyevent == "GarageEvent_Notify_on_Open":
		return # don't send Pushover notifications for these
	else:
		notifymessage = "Whoops! GarageZero had the following unhandled notify event: " + notifyevent + " at " + str(now)
		subjectmessage = "GarageZero: Unknown Notification at " + str(now)

	for user in settings['pushover']['UserKeys'].split(','):
		data = {
			"token": settings['pushover']['APIKey'],
			"user": user.strip(),
			"message": notifymessage,
			"title": subjectmessage,
			"url": settings['misc']['PublicURL'],
		}

		url = 'https://api.pushover.net/1/messages.json'
		try:
			request = urllib2.Request(url, json.dumps(data), {'Content-Type': 'application/json'})
			response = urllib2.urlopen(request)
			WriteLog("Pushover Notification to %s Succeeded: %s" % (user, notifyevent))
		except urllib2.HTTPError as e:
			WriteLog("Pushover Notification to %s Failed: %s" % (user, e))
		except urllib2.URLError as e:
			WriteLog("Pushover Notification to %s Failed: %s" % (user, e))
		except Exception as e:
			WriteLog("Pushover Notification to %s Failed: %s" % (user, e))


def SendIFTTTNotification(settings,notifyevent):
	# WriteLog("[DEBUG]: SendIFTTTNotification Function. " + notifyevent)

	key = settings['ifttt']['APIKey']
	url = 'https://maker.ifttt.com/trigger/' + notifyevent + '/with/key/' + key

	if notifyevent == "GarageEvent_Open_Alarm":
		query_args = { "value1" : str(settings['notification']['minutes']) }
	elif notifyevent == "GarageEvent_StillOpen_Alarm":
		open_minutes = int((time.time() - opened_at) / 60)
		query_args = { "value1" : open_minutes }
	else:
		query_args = {}

	try:
		postdata = urllib.urlencode(query_args)

		request = urllib2.Request(url,postdata)
		response = urllib2.urlopen(request)
		WriteLog("IFTTT Notification Success: " + notifyevent)
	except urllib2.HTTPError:
		WriteLog("IFTTT Notification Failed: " + notifyevent)
	except urllib2.URLError:
		WriteLog("IFTTT Notification Failed: " + notifyevent)
	except:
		WriteLog("IFTTT Notification Failed: " + notifyevent)


def SendNotification(settings,notifyevent):
	if settings['email']['FromEmail'] != "":
		SendEmail(settings, notifyevent)
	if settings['pushover']['APIKey']:
		SendPushoverNotification(settings, notifyevent)
	if settings['ifttt']['APIKey'] != "0":
		SendIFTTTNotification(settings, notifyevent)


def ToggleRelay():
	# *****************************************
	# Function to Toggle Relay (and open/close the garage door)
	# *****************************************
	# Insert code to push button here
	GPIO.output(relay_pin, 1) 	#Turn on Relay
	time.sleep(0.5)			#Wait for 0.5s
	GPIO.output(relay_pin, 0)	#Turn off Relay


def CheckDoorState(states, settings):
	# *****************************************
	# Check switch state Open / Closed
	# Function run from Readstates()
	# *****************************************
	global timer_start
        global reminder_timer_start
        global opened_at

	if (GPIO.input(switch_pin) == True and states['inputs']['switch'] != True):
		states['inputs']['switch'] = True
		WriteStates(states)
		event = "Door Opened."
		WriteLog(event)
		if(settings['notification']['minutes'] > 0):
			timer_start = time.time() # Set start time for timer
			opened_at = timer_start # Note time the door was actually opened
		if(settings['ifttt']['notify_on_open'] == "on"):
			notifyevent = "GarageEvent_Notify_on_Open"
			SendNotification(settings,notifyevent)
		time.sleep(1)
	if (GPIO.input(switch_pin) == False and states['inputs']['switch'] != False):
		states['inputs']['switch'] = False
		WriteStates(states)
		event = "Door Closed."
		WriteLog(event)
		timer_start = 0
		reminder_timer_start = 0
		time.sleep(1)
	return(states)

# *****************************************
# Main Program Loop
# *****************************************

# First Init List Switch States

while True:
	settings = ReadSettings()
	states = CheckDoorState(ReadStates(),settings)

	if (states['inputs']['switch'] == False) and (notify_on_close == True):
		# WriteLog("[DEBUG]: Garage Door Closed. Calling SendNotification Function")
		notify_on_close = False
		notifyevent = "GarageEvent_Closed"
		SendNotification(settings,notifyevent)

	if (timer_start > 0):
		if(time.time() > (timer_start + (settings['notification']['minutes']*60))):
			# WriteLog("[DEBUG]: Garage open for 10 mins. Calling SendNotification Function")
			notifyevent = "GarageEvent_Open_Alarm"
			SendNotification(settings,notifyevent)
			timer_start = 0 # Stop the timer, stop from sending another notification
			notify_on_close = True

			if (settings['notification']['reminder'] > 0):
				reminder_timer_start = time.time()

	if (reminder_timer_start > 0):
		if(time.time() > (reminder_timer_start + (settings['notification']['reminder']*60))):
			# WriteLog("[DEBUG]: Garage still open for 10 mins. Calling SendNotification Function")
			notifyevent = "GarageEvent_StillOpen_Alarm"
			SendNotification(settings,notifyevent)
			reminder_timer_start = time.time() # Restart the timer

	if (states['outputs']['button'] == True):

		event = "Button Pressed."
		WriteLog(event)

		ToggleRelay()

		states['outputs']['button'] = False
		WriteStates(states)

	time.sleep(0.25)

exit()
