#!/usr/bin/env python3
# Copyright: 2016, Jens Carroll
#
# Check GPIO Pin 7 level (front door opening)
#
import RPi.GPIO as GPIO, time, os, signal, sys

GPIO.setmode(GPIO.BCM)
GPIO.setup(4, GPIO.IN) # Gpio 4, Pin 7

def signal_handler(signal, frame):
  # clean-up code goes here
  print("Exit program.")
  sys.exit(0)

i=0
# Ctrl-C and SIGTERM handler
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

while True:
  print("%d: Pin 7 level: %d (0 = relais opens door)" % (i, GPIO.input(4)))
  time.sleep(1)
  i += 1
