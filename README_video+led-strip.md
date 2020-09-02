VIDEO SETUP

Open index.html and add camera ip address.

sudo nano garage-zero/templates/index.html

1. Uncomment (remove <!-- and --> from beginning and end) of the following line.

<!--<center><img name="main" id="main" border="0" width="400" height="300" src="http://[camera ip]:[port]/video"></center> -->

2. Enter the cameras ip and port number.


GARAGE LED STRIP LIGHTS

1.COPY TO garage-zero folder.

garage-led-strip.py
garage-led-strip.service
garage-led-strip.sh

2.Copy the garage-led-strip.sh to /usr/bin and make it executable:

sudo cp garage-led-strip.sh /usr/bin/garage-led-strip.sh
sudo chmod +x /usr/bin/garage-led-strip.sh


3.Copy garage-led-strip.service to /etc/systemd/system and give it permissions:


sudo cp garage-led-strip.service /etc/systemd/system/garage-led-strip.service
sudo chmod 644 /etc/systemd/system/garage-led-strip.service


4. Test

sudo systemctl start garage-led-strip.service   # May get a warning to reload daemon

5. Check status

sudo systemctl status garage-led-strip.service


6. Stop and restart service

sudo systemctl stop garage-led-strip.service
sudo systemctl restart garage-led-strip.service

7. Enable the service 

sudo systemctl enable garage-led-strip.service

8. Reboot the linode manager

sudo systemctl status garage-led-strip.service

9. Test on reboot of pi.

10. Adjust time.sleep in garage-led-strip.py

sudo nano garage-zero/garage-led-strip.py

This adjustment makes allowance for a dimming light source (original garage opener lights) that the photdiode is detecting. A dimming light source can trigger the GPIO pin to read high/low/high repeatly which will switch the relay on and off until the light source eventually goes out.

-if your light source does not dim before going out, time.sleep at the end of the script can be set between 0.2 and 2.5. [e.g time.sleep(0.2)]
-if you light source gradually dims, play around with the sleep time to prevent the relay triggering as light source dims. [default is time.sleep(2.5)]