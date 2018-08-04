#!/usr/bin/env python3
# Copyright: 2016, Jens Carroll
# These sources are released under the terms of the MIT license: see LICENSE
"""
Description:
Opendoor - Open the door on the base floor to access the Carroll nest

Usage: opendoor.py [-vcrth]

You must have root privileges to start opendoord.py

Options:
  -v, --verbose         Verbose output.
  -c, --console         Output to stdout (verbose).
  -r, --resetdb         Reset sqlite database.
  -t, --test            Do not open the door, just logging
  -h, --help            This screen.
  --version             Program version.
"""
# Docopt is a library for parsing command line arguments
import setproctitle, signal, sys, os, re, docopt, datetime
from logger import Logger
from time import sleep
from fileutil import FileUtil
from sqlite import Sqlite
from gpio import Port
from pipes import Pipes
from timer import FrontDoorTimer

log, pipes, port, db = None, None, None, None
test_mode = False

def signal_handler(signal, frame):
  # clean-up code goes here
  global log
  log.debug("Pid was %s" % os.getpid())
  sleep(2)
  sys.exit(0)

def pipes_and_log(action, param=None):
  global pipes, db

  if action == 'open_front_door':
    pipes.send_to_app("AUTO OPEN FRONT DOOR")
    db.add_log("Doorbell pressed with auto open.")
  elif action == 'doorbell':
    pipes.send_to_app("DOORBELL PRESSED")
    db.add_log("Doorbell pressed without auto open.")

def opendoor_endless_loop():
  global log, port

  # Change title
  setproctitle.setproctitle("opendoord")

  # Timer that controls the automatic opening times for the front door.
  timer = FrontDoorTimer()

  i, timer_off = 0, False
  while True:
    # let's sleep
    sleep(1)

    # should we auto open the door the front door?
    open_front_door, open_apartment_door = db.auto_open()

    if port.door_ring():
      if open_front_door or timer.secs > 0:
        pipes_and_log('open_front_door')

        port.delayed_open_front_door() # 4-7 secs delay + 5 secs open
        if open_apartment_door:
          port.open_apartment_door(open_apartment_door)
      else:
        pipes_and_log('doorbell')
        sleep(5) # timeout for port actions

      # release lock
      port.door_ring_release()

    # decrement front door timer by a sec
    timer.decr_sec()

    # add some logging
    if not i % 300:
      log.debug("Endless work (%06d min), Autoopen: %s" % (i/60, ("yes" if open_front_door else "no")))

    if timer.secs >= 0 or timer.mins >= 0:
      timer_off = False
      pipes.send_to_app("FRONT DOOR TIMER %d" % timer.mins)
    elif open_front_door:
      pipes.send_to_app("FRONT DOOR TIMER 0") # 0 is a dummy in that case
    elif not timer_off:
      pipes.send_to_app("FRONT DOOR TIMER OFF")
      timer_off = True

    i += 1

def main():
  global log, port, pipes, db, test_mode

  # Be sure we have root privileges
  if os.geteuid() != 0:
    exit("You need to have root privileges. Exiting.")

  # Ctrl-C and SIGTERM handler
  signal.signal(signal.SIGINT, signal_handler)
  signal.signal(signal.SIGTERM, signal_handler)

  # Parse arguments, use file docstring as a parameter definition
  args = docopt.docopt(__doc__, version='0.1a')

  # Create directory if it doesn't exist
  futil = FileUtil(".opendoord")

  print("Path: %s, args: %s" % (futil.path, args))
  # Create a logger
  if args["--console"]:
    log = Logger.get(verbose = True)
  else:
    log = Logger.get(futil.path + "/opendoor.log", verbose = args["--verbose"])
  log.info("*** Start OpenDoor ***")

  # Get access to the database handler
  db = Sqlite(futil.path + "/opendoor.db", log)
  if not db.exist():
    log.info("No database found. Will create one.")
    db.create_tables() # if not already created
    db.reset_tables()  # and initialize

  if args["--test"]:
    test_mode = True

  # Let's initialize the gpio's
  port = Port(log, test_mode)

  # Open the pipes
  pipes = Pipes(log, port, db)

  if args["--resetdb"]:
    db.reset_tables()
    log.info("Database has been reset.")
  else:
    log.info("Watch door events in an endless loop.")
    opendoor_endless_loop()

if __name__ == '__main__':
  main()
