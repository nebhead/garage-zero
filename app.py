from flask import Flask, request, render_template, make_response, redirect, abort, jsonify
import time
import datetime
import os
import secrets
from common import *

app = Flask(__name__)
settings = ReadSettings()

@app.route('/', methods=['POST','GET'])
def index():
	global settings
	if (request.method == 'POST'):
		response = request.form
		if('listorder' in response):
			if(response['listorder'] == 'topdown'):
				settings['misc']['listorder'] = 'topdown'
			else:
				settings['misc']['listorder'] = 'bottomup'
			WriteSettings(settings)
		if('24htime' in response): 
			if(response['24htime'] == 'true'):
				settings['misc']['24htime'] = True
			else:
				settings['misc']['24htime'] = False 
			WriteSettings(settings)

	return render_template('index.html', pagetheme=settings['misc']['theme'], settings=settings)

@app.route('/status')
def doorstatus():
	states = ReadStates()
	return render_template('doorstatus.html', state=states['inputs']['switch'])

@app.route('/shortlog')
def shortlog():
	global settings
	door_history, events = ReadLog(10, twentyfourhtime=settings['misc']['24htime'])
	return render_template('shortlog.html', door_history=door_history, events=events, settings=settings)

@app.route('/button')
def button():
	states = ReadStates()
	states['outputs']['button'] = True  		# Button pressed - Set state to 'on'
	WriteStates(states)		# Write button press to file
	ipaddress = request.remote_addr
	event = 'Button Press from WebUI [' + ipaddress + ']'
	WriteLog(event)
	return redirect('/')

@app.route('/history', methods=['POST','GET'])
def history():
	global settings

	if (request.method == 'POST'):
		response = request.form

		if('listorder' in response):
			if(response['listorder'] == 'topdown'):
				settings['misc']['listorder'] = 'topdown'
			else:
				settings['misc']['listorder'] = 'bottomup'
			WriteSettings(settings)
		if('24htime' in response): 
			if(response['24htime'] == 'true'):
				settings['misc']['24htime'] = True
			else:
				settings['misc']['24htime'] = False 
			WriteSettings(settings)

	door_history, events = ReadLog(twentyfourhtime=settings['misc']['24htime'])

	return render_template('history.html', door_history=door_history, events=events, pagetheme=settings['misc']['theme'], settings=settings)

@app.route('/admin/<action>', methods=['POST','GET'])
@app.route('/admin', methods=['POST','GET'])
def admin(action=None):
	states = ReadStates()
	global settings 
	settings = ReadSettings()

	if action == 'reboot':
		event = "Reboot Requested."
		WriteLog(event)
		os.system("sleep 3 && sudo reboot &")

		#Show Reboot Splash
		return render_template('shutdown.html', action=action, pagetheme=settings['misc']['theme'])

	if action == 'shutdown':
		event = "Shutdown Requested."
		WriteLog(event)
		os.system("sleep 3 && sudo shutdown -h now &")

		#Show Shutdown Splash
		return render_template('shutdown.html', action=action, pagetheme=settings['misc']['theme'])

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

		if('reminder' in response):
			if(response['reminder']!=''):
				print("Reminder: " + response['reminder'])
				settings['notification']['reminder'] = int(response['reminder'])

		if('iftttapi' in response):
			if(response['iftttapi']!=''):
				print("IFTTT API Key: " + response['iftttapi'])
				settings['ifttt']['APIKey'] = response['iftttapi']

		settings['notification']['notify_on_open'] = "off"  # Turn off notify_on_open if no response from POST

		if('notify_on_open' in response):
			if(response['notify_on_open']!=''):
				print("Notify on Open: " + response['notify_on_open'])
				settings['notification']['notify_on_open'] = response['notify_on_open']

		if('pushover_apikey' in response):
			if(response['pushover_apikey']!=settings['pushover']['APIKey']):
				print("Pushover API key: " + response['pushover_apikey'])
				settings['pushover']['APIKey'] = response['pushover_apikey']

		if('pushover_userkeys' in response):
			if(response['pushover_userkeys']!=settings['pushover']['UserKeys']):
				print("Pushover User keys: " + response['pushover_userkeys'])
				settings['pushover']['UserKeys'] = response['pushover_userkeys']

		if('theme' in response):
			print(response['theme'])
			settings['misc']['theme'] = response['theme']

		if('enable_api' in response):
			print(response['enable_api'])
			if response['enable_api'] == 'true':
				settings['api_config']['enable'] = True
				if settings['api_config']['apikey'] == '':
					settings['api_config']['apikey'] = gen_api_key(32)
			else:
				settings['api_config']['enable'] = False

		if('gen_api' in response):
			print(response['gen_api'])
			if response['gen_api'] == 'true':
				settings['api_config']['apikey'] = gen_api_key(32)

		WriteSettings(settings)
		event = "Settings Updated."
		WriteLog(event)

	uptime = os.popen('uptime').readline()

	cpuinfo = os.popen('cat /proc/cpuinfo').readlines()

	return render_template('admin.html', action=action, uptime=uptime, cpuinfo=cpuinfo, settings=settings, pagetheme=settings['misc']['theme'])

@app.route('/manifest')
def manifest():
    res = make_response(render_template('manifest.json'), 200)
    res.headers["Content-Type"] = "text/cache-manifest"
    return res

@app.route('/api/<action>', methods=['POST','GET'])
def api(action=None):
	global settings 

	apikey = settings['api_config']['apikey']
	doorname = settings['misc']['doorname']

	if (settings['api_config']['enable'] == True) and (apikey == action):
		if (request.method == 'POST'):
			if not request.json:
				event = 'Local API Call Failed - Local API interface not enabled.'
				WriteLog(event)
				abort(400)
			else:
				if('DoorButton' in request.json):
					states = ReadStates()
					states['outputs']['button'] = True  		# Button pressed - Set state to 'on'
					WriteStates(states)		# Write button press to file
					event = f'Local API Call Success. Door button [{doorname}] pressed.'
					WriteLog(event)
					return jsonify({'result': 'success'}), 201
			return jsonify({'result': 'failed'}), 201

		if (request.method == 'GET'):
			door_output = {}
			door_output = {
				doorname: {
					'id': settings['misc']['id'],
					'status': {
						'limitsensorclosed': ''
					}
				}
			}

			states = ReadStates()
			state=states['inputs']['switch']
			
			door_output[doorname]['status']['limitsensorclosed'] = 'open' if state == 1 else 'closed'
		
			event = 'Local API Call Success. [GET]'
			WriteLog(event)
			return jsonify(door_output), 201

	event = 'Local API Call Failed.'	
	WriteLog(event)

	abort(404)

@app.route('/haexample')
def haexample():
	global settings 

	doorname = "Garage Door"

	server_ip = request.environ['HTTP_HOST']
	#print(request.environ)

	site_url_api = f"http://{server_ip}/api/{settings['api_config']['apikey']}"
	value_template = "{{ value_json['" + doorname + "']['status']['limitsensorclosed'] }}"
	
	resp = make_response(render_template('ha_example.yaml', site_url_api=site_url_api, value_template=value_template, doorname=doorname))
	resp.mimetype = 'text/plain'
	return resp

"""
Supporting Functions
"""

# Attribution to Vladimir Ignatyev on Stack Overflow
# https://stackoverflow.com/questions/41969093/how-to-generate-passwords-in-python-2-and-python-3-securely
def gen_api_key(length, charset="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"):
    return "".join([secrets.choice(charset) for _ in range(0, length)])


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True) # use ,debug=True for debug mode
