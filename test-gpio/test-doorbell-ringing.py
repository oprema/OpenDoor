#!/usr/bin/env python3
# Copyright: 2016, Jens Carroll
#
# Simulate ringing the doorbell
#
import RPi.GPIO as GPIO, time

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(15, GPIO.OUT)

def ring(delay):
  GPIO.output(15, GPIO.HIGH)
  time.sleep(delay)
  GPIO.output(15, GPIO.LOW)
  time.sleep(1)

print("Ringing the doorbell for 3 secs.")
ring(3)
print("Ringing the doorbell twice for 1 sec.")
ring(1)
ring(1)
print("Stop ringing and exit.")
