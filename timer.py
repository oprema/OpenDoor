import math

class Timer(object):
  _secs = -1

  def get_secs(self):
    return type(self)._secs

  def set_secs(self, value):
    type(self)._secs = value

  secs = property(get_secs, set_secs)

  def decr_sec(self):
    if type(self)._secs >= 0:
      type(self)._secs -= 1

  def get_mins(self):
    secs = type(self)._secs
    if secs < 0:
      return -1
    else:
      return math.ceil(secs/60.0)

  def set_mins(self, value):
    type(self)._secs = value * 60

  mins = property(get_mins, set_mins)

class FrontDoorTimer(Timer):
  _secs = -1

def main():
  timer1 = FrontDoorTimer()
  timer1.mins = 3
  FrontDoorTimer().decr_sec()
  print("Duration: %d" % timer1.secs)

if __name__ == "__main__":
  main()

