# -*- coding: utf-8 -*-
# Copyright: 2016, Jens Carroll
# These sources are released under the terms of the MIT license: see LICENSE
import sqlite3, sys, binascii, time, os.path, pytz, random, string
from datetime import datetime, timedelta, date

class Sqlite(object):
  """ Utilizing a SQLite database for persistent settings and logging """
  def __init__(self, db_path, log):
    self.db_path = db_path
    self._log = log

  def _connect(self):
    self.db = sqlite3.connect(self.db_path, detect_types = sqlite3.PARSE_DECLTYPES)
    return self.db

  def _sql(self):
    with self._connect():
      try:
        self.db.row_factory = sqlite3.Row
        yield self.db.cursor()
      # Catch exception
      except sqlite3.Error as e:
        print("SQLite Error: %s" % e.args[0])

  def exist(self):
    return os.path.isfile(self.db_path)

  def drop_tables(self):
    for cursor in self._sql():
      cursor.execute("DROP TABLE IF EXISTS settings")
      cursor.execute("DROP TABLE IF EXISTS auth_codes")
      cursor.execute("DROP TABLE IF EXISTS open_door_logs")
      self._log.debug("Droping database")

  def create_tables(self):
    for cursor in self._sql():
      cursor.execute("""CREATE TABLE IF NOT EXISTS
        open_times(id INTEGER PRIMARY KEY,
          disabled INTEGER NOT NULL DEFAULT 0,
          title TEXT NOT NULL,
          open_dow INTEGER NOT NULL DEFAULT 0,
          open_begin timestamp DATE NOT NULL,
          open_end timestamp DATE NOT NULL,
          open_after INTEGER NOT NULL DEFAULT 0,
          created_at timestamp DATE DEFAULT (datetime('now', 'localtime')),
          updated_at timestamp DATE DEFAULT (datetime('now', 'localtime'))
        )""")
      # Authorization codes for json access
      cursor.execute("""CREATE TABLE IF NOT EXISTS
        auth_codes(id INTEGER PRIMARY KEY,
          user_name TEXT NOT NULL UNIQUE,
          auth_code TEXT NOT NULL UNIQUE,
          disabled INTEGER NOT NULL DEFAULT 0,
          created_at timestamp DATE DEFAULT (datetime('now', 'localtime'))
        )""")
      # 'RING' or 'OPEN'
      cursor.execute("""CREATE TABLE IF NOT EXISTS
        open_door_logs(id INTEGER PRIMARY KEY,
          log_text TEXT NOT NULL,
          created_at timestamp DATE DEFAULT (datetime('now', 'localtime'))
        )""")

  def reset_tables(self):
    self.drop_tables()
    self.create_tables()

  def auto_open(self):
    """
    Check if we are supposed to open the door.
    """
    dow = datetime.today().weekday() # todays dow
    for cursor in self._sql():
      cursor.execute("""SELECT * FROM open_times WHERE open_dow = ? AND disabled = 0""", (dow, ))
      open_times = cursor.fetchall()

    # TODO get timezone name instead of a hard set CET
    cet = pytz.timezone('CET')
    now = datetime.now()
    offset = cet.utcoffset(now)

    for open_time in open_times:
      open_begin = now.replace(hour=open_time['open_begin'].hour,
        minute=open_time['open_begin'].minute) + offset
      open_end = now.replace(hour=open_time['open_end'].hour,
        minute=open_time['open_end'].minute) + offset

      # Return True if now falls in time frame
      if ((now >= open_begin) and (now < open_end)):
        return [True, open_time['open_after']]

    return [False, False]

  def add_log(self, logstr):
    """
    Log each RING and OPEN of the door.
    """
    for cursor in self._sql():
      created_at = str(datetime.now()).split('.')[0]
      cursor.execute("""INSERT INTO open_door_logs(
        log_text, created_at)
        VALUES
        (?, ?)""", (logstr, created_at))

  def list_log(self, page, count=10):
    """
    List logged entries one page (10 entries) per call
    """
    for cursor in self._sql():
      cursor.execute("""SELECT * FROM open_door_logs
        ORDER BY created_at DESC LIMIT ?, ?""", (page*count, count))
      r = self.to_json(cursor)
    return r

  def clear_log(self):
    """
    Clear all logged entries
    """
    for cursor in self._sql():
      cursor.execute("DELETE FROM open_door_logs WHERE 1")
    return True

  def to_json(self, cursor, one=False):
    """
    Add column descr to fetchall
    """
    r = [dict((cursor.description[i][0], value) \
      for i, value in enumerate(row)) for row in cursor.fetchall()]
    return (r[0] if r else None) if one else r

  # --- for testing purpose only ---
  def count_table_entries(self, tablename):
    for cursor in self._sql():
      cursor.execute("SELECT COUNT(*) FROM %s" % tablename)
      count = cursor.fetchone()[0]
      print("Found %d table (%s) entries" % (count, tablename))

def main():
  from logger import Logger
  log = Logger.get(verbose=True)

  db = Sqlite("test.db", log)
  db.create_tables()
  print("Tables created!")

#  db.create_open_time('First entry', 0, '18:00', '19:00')
#  print "Added first open time entry."

  print("Open door? " + db.auto_open())

if __name__ == "__main__":
  main()
