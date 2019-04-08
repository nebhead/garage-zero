from flask import Flask, request, render_template, make_response
import time
import datetime
import os
import json

app = Flask(__name__)

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
	# Read Switch States from File
	# *****************************************

	# Default settings
	settings = {}

	settings['misc'] = {
		'PublicURL': '',
	}

	settings['email'] = {
		'ToEmail': 'your_to_email', # E-mail address to send notification to
		'FromEmail': 'your_from_email', # E-mail address to log into system
		'Password' : 'your_password', # Password
		'SMTPServer' : 'smtp.gmail.com', # SMTP Server Name
		'SMTPPort' : 587 # SMTP Port
		}

	settings['notification'] = {
		'minutes': 0 # Magnetic Switch
	}

	settings['ifttt'] = {
		'APIKey': "0" # API Key for WebMaker IFTTT App notification
	}

	settings['pushover'] = {
		'APIKey': '', # API Key for Pushover notifications
		'UserKeys': '', # Comma-separated list of user keys
	}

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

@app.route('/')
def index():
	door_history, events = ReadLog()

	states = ReadStates()

	if(states['inputs']['switch'] == True):
		door_state = True
	else:
		door_state = False

	return render_template('index.html', state=door_state, events=events, door_history=door_history)

@app.route('/button')
def button():

	states = ReadStates()
	states['outputs']['button'] = True  		# Button pressed - Set state to 'on'
	WriteStates(states)		# Write button press to file

	return render_template('button.html')

@app.route('/history')
def history():

	door_history, events = ReadLog()

	return render_template('door-log.html', door_history=door_history, events=events)


@app.route('/admin/<action>', methods=['POST','GET'])
@app.route('/admin', methods=['POST','GET'])
def admin(action=None):
	states = ReadStates()
	settings = ReadSettings()

	if action == 'reboot':
		event = "Reboot Requested."
		WriteLog(event)
		os.system("sleep 3 && sudo reboot &")

		#Show Reboot Splash
		return render_template('shutdown.html', action=action)

	if action == 'shutdown':
		event = "Shutdown Requested."
		WriteLog(event)
		os.system("sleep 3 && sudo shutdown -h now &")

		#Show Shutdown Splash
		return render_template('shutdown.html', action=action)

	if (request.method == 'POST') and (action == 'settings'):
		response = request.form

		if('from_email' in response):
			if(response['from_email']!=''):
				print("from_email: " + response['from_email'])
				settings['email']['FromEmail'] = response['from_email']

		if('to_email' in response):
			if(response['to_email']!=''):
				print("to_email: " + response['to_email'])
				settings['email']['ToEmail'] = response['to_email']

		if('server' in response):
			if(response['server']!=''):
				print("Server: " + response['server'])
				settings['email']['SMTPServer'] = response['server']

		if('port' in response):
			if(response['port']!=''):
				print("Port: " + response['port'])
				settings['email']['SMTPPort'] = int(response['port'])

		if('password' in response):
			if(response['password']!=''):
				print("password: " + response['password'])
				settings['email']['Password'] = response['password']

		if('public_url' in response):
			if(response['public_url']!=''):
				print("public_url: " + response['public_url'])
				settings['misc']['PublicURL'] = response['public_url']

		if('timeout' in response):
			if(response['timeout']!=''):
				print("Timeout: " + response['timeout'])
				settings['notification']['minutes'] = int(response['timeout'])

		if('iftttapi' in response):
			if(response['iftttapi']!=''):
				print("IFTTT API Key: " + response['iftttapi'])
				settings['ifttt']['APIKey'] = response['iftttapi']

		settings['ifttt']['notify_on_open'] = "off"  # Turn off notify_on_open if no response from POST

		if('notify_on_open' in response):
			if(response['notify_on_open']!=''):
				print("Notify on Open: " + response['notify_on_open'])
				settings['ifttt']['notify_on_open'] = response['notify_on_open']

		if('pushover_apikey' in response):
			if(response['pushover_apikey']!=settings['pushover']['APIKey']):
				print("Pushover API key: " + response['pushover_apikey'])
				settings['pushover']['APIKey'] = response['pushover_apikey']

		if('pushover_userkeys' in response):
			if(response['pushover_userkeys']!=settings['pushover']['UserKeys']):
				print("Pushover User keys: " + response['pushover_userkeys'])
				settings['pushover']['UserKeys'] = response['pushover_userkeys']

		WriteSettings(settings)
		event = "Settings Updated."
		WriteLog(event)

	uptime = os.popen('uptime').readline()

	cpuinfo = os.popen('cat /proc/cpuinfo').readlines()

	return render_template('admin.html', action=action, uptime=uptime, cpuinfo=cpuinfo, settings=settings)

@app.route('/manifest')
def manifest():
    res = make_response(render_template('manifest.json'), 200)
    res.headers["Content-Type"] = "text/cache-manifest"
    return res

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True) # use ,debug=True for debug mode
