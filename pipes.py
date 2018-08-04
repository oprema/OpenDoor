# -*- coding: utf-8 -*-
# Copyright: 2016-2018, Jens Carroll
# These sources are released under the terms of the MIT license: see LICENSE

import time, threading, os, signal, re
from gpio import Port
from logger import Logger
from fileutil import FileUtil
from sqlite import Sqlite
from timer import FrontDoorTimer

WRITE_FIFO = "/tmp/opendoor_fifo"
READ_FIFO = "/tmp/app_fifo"

class ReadPipeThread(threading.Thread):
  def __init__(self, logger, port, db, pipe):
    self._logger = logger
    self._port = port
    self._db = db
    self._pipe = pipe
    super(ReadPipeThread, self).__init__()

  def _getInt(self, line):
    return [int(s) for s in line.split() if s.isdigit()][0]

  def run(self):
    self._logger.debug("Waiting to open read fifo (in a own thread).")
    pipein = open(READ_FIFO, 'r')
    self._logger.debug("Read fifo opened.")

    while True:
      time.sleep(1)
      line = pipein.readline()[:-1]
      if line == "":
        continue

      match = re.search(r"\((\w+)\)", line)
      user = "Web" if match == None else match.groups(1)

      if "OPEN FRONT DOOR TIMED" in line:
        duration = self._getInt(line)
        self._db.add_log("Open front door active for %d mins.\n" % duration)
        self._logger.debug("Received an OPEN FRONT DOOR TIMED (%d min) from the app." % duration)
        self._pipe.send_to_app("OPEN FRONT DOOR TIMED")
        FrontDoorTimer().mins = duration
      elif "OPEN FRONT DOOR" in line:
        self._db.add_log("User opens front door (%s).\n" % user)
        self._pipe.send_to_app("FRONT DOOR OPENED")
        self._logger.debug("Received an OPEN FRONT DOOR from user (%s)." % user)
        self._port.open_front_door()
        time.sleep(3)
        self._port.door_ring_release()
      elif "OPEN APARTMENT DOOR" in line:
        self._db.add_log("User opens door to the apartment (%s).\n" % user)
        self._pipe.send_to_app("APARTMENT DOOR OPENED")
        self._logger.debug("Received an OPEN APARTMENT DOOR from user (%s)." % user)
        self._port.open_apartment_door()
      elif "KEEP APARTMENT DOOR OPEN" in line:
        duration = self._getInt(line)
        self._db.add_log("Keep aparment door open for %d mins (%s).\n" % (duration, user))
        self._pipe.send_to_app("KEEP APARTMENT DOOR OPEN")
        self._logger.debug("Received a KEEP APARTMENT DOOR OPEN (%d mins) from user (%s)." % (duration, user))
        self._port.open_apartment_door_for(self._pipe, duration)
      elif "CLOSE APARTMENT DOOR" in line:
        self._logger.debug("Received a CLOSE APARTMENT DOOR from user (%s)." % user)
        self._port.stop_open_apartment_door_for()
      else:
        self._logger.debug("Unknown command in pipes: %s." % line)

class Pipes(object):
  def __init__(self, logger, port, db):
    self._logger = logger
    self._pipeout = None

    # create fifos if they do not exist
    os.umask(0)
    if not os.path.exists(WRITE_FIFO):
      os.mkfifo(WRITE_FIFO, 0o666)
      self._logger.debug("Create write fifo.")
    if not os.path.exists(READ_FIFO):
      os.mkfifo(READ_FIFO, 0o666)
      self._logger.debug("Create read fifo.")

    self._thread = ReadPipeThread(self._logger, port, db, self)
    self._thread.setDaemon(True)
    self._thread.start()
    self._logger.debug("Waiting to open write fifo ...")
    self._pipeout = os.open(WRITE_FIFO, os.O_WRONLY)
    self._logger.debug("Write fifo opened.")

  def send_to_app(self, msg, count=None):
    try:
      if self._pipeout != None:
        os.write(self._pipeout, (msg + "\n").encode())
      else:
        self._logger.warn("Write fifo does not exist.")
    except OSError as e:
      self._logger.debug("Close and waiting to reopen write fifo ...")
      self._pipeout = os.open(WRITE_FIFO, os.O_WRONLY)
      self._logger.debug("Write fifo opened.")

def main():
  # Create directory if it doesn't exist
  futil = FileUtil(".opendoord")

  # Get access to the database handler
  logger = Logger.get(verbose = True)
  db = Sqlite(futil.path + "/opendoor.db", logger)
  port = Port(logger)
  pipes = Pipes(logger, port, db)

  i = 0
  logger.debug("Send commands via pipe with 10 sec delay")
  while i<100:
    i += 1
    pipes.send_to_app("OPEN DOOR\n", i)
    logger.debug("OPEN DOOR")
    time.sleep(10)
    i += 1
    pipes.send_to_app("DOORBELL PRESSED\n", i)
    logger.debug("DOORBELL PRESSED")
    time.sleep(10)
    i += 1
    pipes.send_to_app("DOW RING WITH AUTO OPEN\n", i)
    logger.debug("DOW RING WITH AUTO OPEN")
    time.sleep(10)

if __name__ == "__main__":
  main()
