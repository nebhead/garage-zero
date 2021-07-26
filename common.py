import time
from datetime import datetime
import os
import json

# Storage for Door States. 
# On Raspberry Pi /var/tmp is ram storage
states_file = "/tmp/states.json"

def DefaultSettings():
	settings = {}

	settings['misc'] = {
		'PublicURL': '',
		'theme': 'default',
		'listorder': 'topdown', # default list order 'topdown' or 'bottomup'
		'24htime': True, # default to 24hr time (commonly known as military time in the USA)
	}

	settings['email'] = {
		'ToEmail': 'your_to_email', # E-mail address to send notification to
		'FromEmail': 'your_from_email', # E-mail address to log into system
		'Username': 'your_username', # Username
		'Password' : 'your_password', # Password
		'SMTPServer' : 'smtp.gmail.com', # SMTP Server Name
		'SMTPPort' : 587, # SMTP Port
		'UseTLS': True,
	}

	settings['notification'] = {
		'minutes': 0, # Once-off notification that the door is open
		'reminder': 0, # Repeated notification that the door is still open
		'notify_on_open': "off",
	}

	settings['ifttt'] = {
		'APIKey': "0", # API Key for WebMaker IFTTT App notification
		'notify_on_open': "off",
	}

	settings['pushover'] = {
		'APIKey': '', # API Key for Pushover notifications
		'UserKeys': '', # Comma-separated list of user keys
		'notify_on_open': "off",
	}

	return settings

def DefaultStates():
	states = {}

	states['inputs'] = {
		'switch': False # Magnetic Switch
	}

	states['outputs'] = {
		'button': False # Relay Button
	}

	return states

def ReadSettings():
	# *****************************************
	# Read Switch States from File
	# *****************************************

	# Default settings
	settings = DefaultSettings()

	# Read all lines of settings.json into an list(array)
	try:
		json_data_file = open("settings.json", "r")
		json_data_string = json_data_file.read()
		user_settings = json.loads(json_data_string)
		json_data_file.close()

		# Merge each section of the user settings over the defaults
		for key in settings.keys():
			settings[key].update(user_settings.get(key, {}))

	except(IOError, OSError):
		# Issue with reading settings JSON, so create one/write new one
		WriteSettings(settings)

	return(settings)

def WriteSettings(settings):
	# *****************************************
	# Write all control states to JSON file
	# *****************************************
	json_data_string = json.dumps(settings)
	with open("settings.json", 'w') as settings_file:
	    settings_file.write(json_data_string)

def ReadStates():
	# *****************************************
	# Read Switch States from File
	# *****************************************

	# Read all lines of states.json into an list(array)
	try:
		json_data_file = open(states_file, "r")
		json_data_string = json_data_file.read()
		states = json.loads(json_data_string)
		json_data_file.close()
	except(IOError, OSError):
		# Issue with reading states JSON, so create one/write new one
		states = DefaultStates()
		WriteStates(states)

	return(states)

def WriteStates(states):
	# *****************************************
	# Write all control states to JSON file
	# *****************************************
	json_data_string = json.dumps(states)
	with open(states_file, 'w') as json_data_file:
		json_data_file.write(json_data_string)
		
	# Set world writable so both root and pi user can modify	
	try:
		os.chmod(states_file, 0o666)
	except(IOError, OSError):
		pass # Can not change chmod if not root or owner


def ReadLog(num_events=0, twentyfourhtime=True):
	# *****************************************
	# Function: ReadLog
	# Input: none
	# Output: event_list, num_events
	# Description: Read event.log and populate
	#  an array of events.
	# *****************************************

	# Read all lines of events.log into an list(array)
	try:
		with open('events.log') as event_file:
			event_lines = event_file.readlines()
			event_file.close()
	# If file not found error, then create events.log file
	except(IOError, OSError):
		event_file = open('events.log', "w")
		event_file.close()
		event_lines = []

	# Initialize event_list list
	event_list = []
	event_line_length = len(event_lines)

	# Check if there are no events in the list
	if (event_line_length == 0):
		num_events = 0
	else: 
		if ((num_events == 0) or (num_events > event_line_length)):
			# Get all events in file
			for x in range(event_line_length):
				event_list.append(event_lines[x].split(" ",2))
			num_events = event_line_length
		elif (num_events < event_line_length): 
			# Get just the last num_events in list
			for x in range(event_line_length-num_events, event_line_length):
				event_list.append(event_lines[x].split(" ",2))

		if (twentyfourhtime == False): 
			for x in range(num_events):
				convertedtime = datetime.strptime(event_list[x][1], "%H:%M:%S")  # Get 24 hour time from log
				event_list[x][1] = convertedtime.strftime("%I:%M:%S %p") # Convert to 12 hour time for display

	return(event_list, num_events)

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
