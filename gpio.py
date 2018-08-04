# -*- coding: utf-8 -*-
# Copyright: 2016-2018, Jens Carroll
# These sources are released under the terms of the MIT license: see LICENSE
import time, os, signal, random, math
from threading import Lock, Thread, Event
from logger import Logger
import RPi.GPIO as GPIO

OPEN_FRONT_DOOR_OUTPUT = 4      # Pin 5
OPEN_APARTMENT_DOOR_OUTPUT = 17 # Pin 11
RING_INPUT = 15                 # Pin 10

lock = Lock()

class BreakoutException(Exception):
  pass

class OpenFrontDoorThread(Thread):
  def __init__(self, logger, wait = False, test_mode = False):
    self._wait = wait
    self._logger = logger
    self._test_mode = test_mode
    super(OpenFrontDoorThread, self).__init__()

  def run(self):
    delay = random.randint(3, 6)
    if self._wait:
      time.sleep(delay) # wait 3-6 sec until we open the door

    if self._test_mode:
      self._logger.info("** Opendoor in test mode. Door will not be opened. **")

    if not self._test_mode:
      GPIO.output(OPEN_FRONT_DOOR_OUTPUT, GPIO.LOW) # Relais close

    self._logger.warn("Front door relais on (4 secs).")
    time.sleep(4) # Relais closed for for 4 secs.

    if not self._test_mode:
      GPIO.output(OPEN_FRONT_DOOR_OUTPUT, GPIO.HIGH) # Relais open
    self._logger.warn("Front door relais off.")

class OpenApartmentDoorThread(Thread):
  def __init__(self, logger, wait = 0, loops = 1, delay = 55, pipe = None, test_mode = False):
    super(OpenApartmentDoorThread, self).__init__()
    self._logger = logger
    self._wait = wait # secs before execution
    self._loops = loops # to prolong door opening
    self._loop_delay = delay # delay in secs for loops > 1
    self._pipe = pipe
    self._stop_event = Event()
    self._test_mode = test_mode

  def _send_to_app(self, msg):
    if self._pipe != None:
      self._pipe.send_to_app(msg)

  def _stopped(self):
    return self._stop_event.is_set() 

  def stop(self):
    self._stop_event.set()

  def run(self):
    if lock.acquire(False):
      try:
        self._logger.debug("Enter apartment door thread (wait=%d, loops=%d, delay=%d)." %
          (self._wait, self._loops, self._loop_delay))
        if self._wait > 0:
          time.sleep(self._wait) # wait ? secs before we close the relais
          self._logger.debug("Continue apartment door thread.")

        for i in range(0, self._loops):
          if self._test_mode:
            self._logger.info("** Opendoor in test mode. Door will not be opened. **")
          self._logger.warn("Apartment door relais on (loop: %d of %d)." % (i+1, self._loops))

          if not self._test_mode:
            GPIO.output(OPEN_APARTMENT_DOOR_OUTPUT, GPIO.LOW) # Relais close
          time.sleep(1) # Relais closed for 1 sec.

          if not self._test_mode:
            GPIO.output(OPEN_APARTMENT_DOOR_OUTPUT, GPIO.HIGH) # Relais open
          self._logger.warn("Apartment door relais off.")

          if self._loops > 1:
            for j in range(0, self._loop_delay):
              if self._stopped():
                raise BreakoutException
              counter = self._loops * self._loop_delay - i * self._loop_delay - j
              self._send_to_app("APARTMENT DOOR TIMER %d" % counter)
              time.sleep(1)
      except BreakoutException:
        self._logger.warn("Apartment door timer stopped.")
      finally:
        self._send_to_app("APARTMENT DOOR TIMER OFF")
        lock.release()

class Port(object):
  def __init__(self, logger, test_mode=False):
    self._logger = logger
    self._doorbell_rang = False
    self._test_mode = test_mode
    self._setup_gpio()
    self._add_event_detect()
    self._thread = None
    signal.signal(signal.SIGALRM, self._timeout_callback)
    self._logger.debug("Port initialized!")

  def _setup_gpio(self):
    """
      Setup GPIO ports
    """
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(RING_INPUT, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    # Relais open (inverse logic)
    GPIO.setup(OPEN_FRONT_DOOR_OUTPUT, GPIO.OUT)
    GPIO.output(OPEN_FRONT_DOOR_OUTPUT, GPIO.HIGH)

    # Relais open (inverse logic)
    GPIO.setup(OPEN_APARTMENT_DOOR_OUTPUT, GPIO.OUT)
    GPIO.output(OPEN_APARTMENT_DOOR_OUTPUT, GPIO.HIGH)

  def _add_event_detect(self):
    """
      Enable interrupts on doorbell
    """
    GPIO.add_event_detect(RING_INPUT, GPIO.FALLING, callback = self._ringing_callback, bouncetime = 300)

  def _remove_event_detect(self):
    """
      Disable interrupts on doorbell
    """
    GPIO.remove_event_detect(RING_INPUT)

  def _ringing_callback(self, channel):
    """
      Interrupt triggered (keep this callback as fast as possible)
    """
    self._remove_event_detect() # No interrupts after that
    signal.setitimer(signal.ITIMER_REAL, 14) # 14 sec timeout
    self._doorbell_rang = True

  def _timeout_callback(self, a, b):
    signal.setitimer(signal.ITIMER_REAL, 0) # Timeout timer off
    self._logger.debug("Timeout callback - Doorbell Interrupts enabled again.")
    self._add_event_detect()

  def open_front_door(self):
    """
      Keep the front door open for a few secs.
    """
    self._logger.debug("Disable Doorbell Interrupts.")
    self._remove_event_detect() # No interrupts after that
    signal.setitimer(signal.ITIMER_REAL, 12) # 12 sec timeout
    thread = OpenFrontDoorThread(self._logger, False)
    thread.start()

  def open_apartment_door(self, after=None):
    """
      Keep the apartment door open for a minute.
    """
    wait = 0
    if after == 1:
      wait = 60
    elif after == 2:
      wait = 90
    elif after == 3:
      wait = 120

    thread = OpenApartmentDoorThread(self._logger, wait)
    thread.start()

  def open_apartment_door_for(self, pipe, mins):
    """
      Keep the apartment door open for n minutes.
    """
    self._thread = OpenApartmentDoorThread(self._logger, loops=mins, delay=59, pipe=pipe)
    self._thread.start()

  def stop_open_apartment_door_for(self):
    self._thread.stop()
    self._thread.join()
    self._thread = None

  def delayed_open_front_door(self):
    """
      Keep the door open for a few secs, but wait a few secs
      before doing so.
    """
    thread = OpenFrontDoorThread(self._logger, True, self._test_mode)
    thread.start()

  def door_ring(self):
    """
      Check if someone rang the door bell at least once.
    """
    if self._doorbell_rang:
      self._logger.debug("Ringing detected (via Interrupt) - Disabled for 14 sec.")
    return self._doorbell_rang

  def door_ring_release(self):
    """
      Release ring_detected.
    """
    self._doorbell_rang = False
    self._logger.debug("Release auto open ringing.")

def main():
  # Be sure we have root privileges
  if os.geteuid() != 0:
    exit("You need to have root privileges. Exiting.")

  logger = Logger.get(verbose = True)
  gpio = Port(logger)

  i = 0
  while True:
    if gpio.door_ring():
      gpio.door_ring_release()

    # every 1 sec ... we should not miss any door bells
    print("running %d sec." % i)
    i += 1
    time.sleep(1)

if __name__ == "__main__":
  main()
