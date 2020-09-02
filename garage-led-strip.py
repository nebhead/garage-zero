# Base code thanks to https://www.freva.com/2019/06/12/light-sensor-on-raspberry-pi/

import RPi.GPIO as GPIO
import time
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
LIGHT_PIN = 17
GPIO.setup(LIGHT_PIN, GPIO.IN)
GPIO.setup(27, GPIO.OUT, initial=1)
lOld = not GPIO.input(LIGHT_PIN)

time.sleep(0.5)
while True:
  if GPIO.input(LIGHT_PIN) != lOld:
    if GPIO.input(LIGHT_PIN):
      GPIO.output(27, 0)
    else:
      GPIO.output(27, 1)
  lOld = GPIO.input(LIGHT_PIN)
  time.sleep(2.5) # Adjust time to allow for dimming light source
