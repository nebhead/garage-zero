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
notify_on_close = False # Initialize the flag for notifying that the door has closed

def SndEmail(settings, notifyevent):
	# WriteLog("[DEBUG]: SndEmail Function. " + notifyevent)
	now = datetime.datetime.now()

	if notifyevent == "GarageEvent_Open_Alarm":
		notifymessage = "GarageZero wants you to know that your garage door has been open for " + str(settings['notification']['minutes']) + " minutes at " + str(now)
		subjectmessage = "GarageZero: Door Open for " + str(settings['notification']['minutes']) + " Minutes"
	elif notifyevent == "GarageEvent_Closed":
		notifymessage = "GarageZero wants you to know that your garage door was closed at " + str(now)
		subjectmessage = "GarageZero: Closed at " + str(now)
	else:
		notifymessage = "Whoops! GarageZero had the following unhandled notify event: " + notifyevent + " at " + str(now)
		subjectmessage = "GarageZero: Unknown Notification at " + str(now)

	try:
		fromaddr = settings['email']['FromEmail']
		toaddr = settings['email']['ToEmail']

		msg = MIMEMultipart()
		msg['From'] = fromaddr
		msg['To'] = toaddr
		msg['Subject'] = subjectmessage
		body = notifymessage
		msg.attach(MIMEText(body, 'plain'))

		server = smtplib.SMTP(settings['email']['SMTPServer'], settings['email']['SMTPPort'])
		server.starttls()
		server.login(fromaddr, settings['email']['Password'])
		text = msg.as_string()
		server.sendmail(fromaddr, toaddr, text)
		server.quit()
		event = subjectmessage + ". E-mail notification sent."
		WriteLog(event)
	except smtplib.SMTPException:
		event = "E-mail notification failed. SMTPLib general exception class(smptlib.SMTPException)."
		WriteLog(event)
	except:
		event = "E-mail notification failed, for some unknown reason."
		WriteLog(event)
	return()

def SendNotification(settings,notifyevent):
	# WriteLog("[DEBUG]: SendNotification Function. " + notifyevent)
	if notifyevent == "GarageEvent_Open_Alarm":
		if settings['email']['FromEmail'] != "":
			SndEmail(settings, notifyevent)
		if settings['ifttt']['APIKey'] != "0":
			key = settings['ifttt']['APIKey']
			url = 'https://maker.ifttt.com/trigger/' + notifyevent + '/with/key/' + key
			try:
				query_args = { "value1" : str(settings['notification']['minutes']) }
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

	if (notifyevent == "GarageEvent_Closed"):
		if settings['email']['FromEmail'] != "":
			SndEmail(settings, notifyevent)
		if settings['ifttt']['APIKey'] != "0":
			key = settings['ifttt']['APIKey']
			url = 'https://maker.ifttt.com/trigger/' + notifyevent + '/with/key/' + key
			try:
				request = urllib2.Request(url)
				response = urllib2.urlopen(request)
				WriteLog("IFTTT Notification Success: " + notifyevent)
			except urllib2.HTTPError:
				WriteLog("IFTTT Notification Failed: " + notifyevent)
			except urllib2.URLError:
				WriteLog("IFTTT Notification Failed: " + notifyevent)
			except:
				WriteLog("IFTTT Notification Failed: " + notifyevent)

	if (notifyevent == "GarageEvent_Notify_on_Open") and (settings['ifttt']['APIKey'] != "0"):
		key = settings['ifttt']['APIKey']
		url = 'https://maker.ifttt.com/trigger/' + notifyevent + '/with/key/' + key
		try:
			request = urllib2.Request(url)
			response = urllib2.urlopen(request)
			WriteLog("IFTTT Notification Success: " + notifyevent)
		except urllib2.HTTPError:
			WriteLog("IFTTT Notification Failed: " + notifyevent)
		except urllib2.URLError:
			WriteLog("IFTTT Notification Failed: " + notifyevent)
		except:
			WriteLog("IFTTT Notification Failed: " + notifyevent)

	return()

def ToggleRelay():
	# *****************************************
	# Function to Toggle Relay (and open/close the garage door)
	# *****************************************
	# Insert code to push button here
	GPIO.output(relay_pin, 1) 	#Turn on Relay
	time.sleep(0.5)			#Wait for 0.5s
	GPIO.output(relay_pin, 0)	#Turn off Relay

def ReadStates():
	# *****************************************
	# Read Switch States from File
	# *****************************************

	# Read all lines of states.json into an list(array)
	try:
		json_data_file = open("states.json", "r")
		json_data_string = json_data_file.read()
		states = json.loads(json_data_string)
		json_data_file.close()
	except(IOError, OSError):
		# Issue with reading states JSON, so create one/write new one
		states = {}

		states['inputs'] = {
			'switch': False # Magnetic Switch
		}

		states['outputs'] = {
			'button': False # Relay Button
		}
		WriteStates(states)

	return(states)

def WriteStates(states):
	# *****************************************
	# Write all control states to JSON file
	# *****************************************
	json_data_string = json.dumps(states)
	with open("states.json", 'w') as settings_file:
		settings_file.write(json_data_string)

def ReadSettings():
	# *****************************************
	# Read Settings from File
	# *****************************************

	# Read all lines of settings.json into an list(array)
	try:
		json_data_file = open("settings.json", "r")
		json_data_string = json_data_file.read()
		settings = json.loads(json_data_string)
		json_data_file.close()
	except(IOError, OSError):
		# Issue with reading settings JSON, so create one/write new one
		settings = {}

		settings['email'] = {
			'ToEmail': 'your_to_email', # E-mail address to send notification to
			'FromEmail': 'your_from_email', # E-mail address to log into system
			'Password' : 'your_password', # Password
			'SMTPServer' : 'smtp.gmail.com', # SMTP Server Name
			'SMTPPort' : 587 # SMTP Port
			}

		settings['notification'] = {
			'minutes': 0 # Minutes
		}

		settings['ifttt'] = {
			'APIKey': '0'
		}

		WriteSettings(settings)

	return(settings)

def WriteSettings(settings):
	# *****************************************
	# Write all settings to JSON file
	# *****************************************
	json_data_string = json.dumps(settings)
	with open("settings.json", 'w') as settings_file:
		settings_file.write(json_data_string)

def WriteLog(event):
	# *****************************************
	# Function: WriteLog
	# Input: str event
	# Description: Write event to event.log
	#  Event should be a string.
	# *****************************************
	now = str(datetime.datetime.now())
	now = now[0:19] # Truncate the microseconds

	logfile = open("events.log", "a")
	logfile.write(now + ' ' + event + '\n')
	logfile.close()

def CheckDoorState(states, settings):
	# *****************************************
	# Check switch state Open / Closed
	# Function run from Readstates()
	# *****************************************
	global timer_start

	if (GPIO.input(switch_pin) == True and states['inputs']['switch'] != True):
		states['inputs']['switch'] = True
		WriteStates(states)
		event = "Door Opened."
		WriteLog(event)
		if(settings['notification']['minutes'] > 0):
			timer_start = time.time() # Set start time for timer
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

	if (states['outputs']['button'] == True):

		event = "Button Pressed."
		WriteLog(event)

		ToggleRelay()

		states['outputs']['button'] = False
		WriteStates(states)

	time.sleep(0.25)

exit()
