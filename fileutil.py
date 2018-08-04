# Copyright: 2016, Jens Carroll
# These sources are released under the terms of the MIT license: see LICENSE
import os, errno

class FileUtil:
  def __init__(self, path):
    self.path = os.path.join(os.getcwd(), path)
    try:
      os.makedirs(self.path, 0o750)
    except OSError as exc:
      if exc.errno == errno.EEXIST and os.path.isdir(self.path):
        pass
      else:
        raise

  def path(self):
    return self.path

if __name__ == "__main__":
  fu = FileUtil(".progdir")
  print("Path is: %s" % fu.path)
