import time
import datetime
import os
import json

def DefaultSettings():
	settings = {}

	settings['misc'] = {
		'PublicURL': '',
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
		'minutes': 0 # Magnetic Switch
	}

	settings['ifttt'] = {
		'APIKey': "0", # API Key for WebMaker IFTTT App notification
		'notify_on_open': "off",
	}

	settings['pushover'] = {
		'APIKey': '', # API Key for Pushover notifications
		'UserKeys': '', # Comma-separated list of user keys
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

	# Read all lines of states.json into an list(array)
	try:
		json_data_file = open("settings.json", "r")
		json_data_string = json_data_file.read()
		user_settings = json.loads(json_data_string)
		json_data_file.close()

		# Merge each section of the user settings over the defaults
		for key in settings.keys():
			settings[key].update(user_settings.get(key, {}))

	except(IOError, OSError):
		# Issue with reading states JSON, so create one/write new one
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
		json_data_file = open("states.json", "r")
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
	with open("states.json", 'w') as settings_file:
		settings_file.write(json_data_string)

def ReadLog():
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

	# Get number of events
	num_events = len(event_lines)

	for x in range(num_events):
		event_list.append(event_lines[x].split(" ",2))

	# Error handling if number of events is less than 20, fill array with empty
	if (num_events < 10):
		for line in range((10-num_events)):
			event_list.append(["--------","--:--:--","---"])
		num_events = 10

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
