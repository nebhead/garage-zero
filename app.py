from flask import Flask, request, render_template, make_response
import time
import datetime
import os
from common import *

app = Flask(__name__)

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

		if('username' in response):
			if(response['username']!=''):
				print("username: " + response['username'])
				settings['email']['Username'] = response['username']

		if('password' in response):
			if(response['password']!=''):
				print("password: " + response['password'])
				settings['email']['Password'] = response['password']

		use_tls = 'use_tls' in response
		if(use_tls!=settings['email']['UseTLS']):
			print("useTLS: %s" % use_tls)
			settings['email']['UseTLS'] = use_tls

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
