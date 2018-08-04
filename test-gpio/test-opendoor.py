#!/usr/bin/env python3
# Copyright: 2016, Jens Carroll
#
# Simulate ringing the doorbell
#
import RPi.GPIO as GPIO, time

GPIO_PIN = 17

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(GPIO_PIN, GPIO.OUT)

# inverse logic
GPIO.output(GPIO_PIN, GPIO.HIGH)

def opendoor(delay):
  GPIO.output(GPIO_PIN, GPIO.LOW)
  time.sleep(delay)
  GPIO.output(GPIO_PIN, GPIO.HIGH)
  time.sleep(1)

print("Open apartment door")
opendoor(1)
print("Stop and exit.")

