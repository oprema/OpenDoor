# Copyright: 2016, Jens Carroll
# These sources are released under the terms of the MIT license: see LICENSE
import logging

class Logger:
  @classmethod
  def get(cls, path=None, verbose=False):
    # create logger
    logger = logging.getLogger('opendoor')
    if verbose:
      logger.setLevel(logging.DEBUG)
    else:
      logger.setLevel(logging.INFO)

    # create console handler and set level to debug
    if path is None:
      handler = logging.StreamHandler()
    else:
      handler = logging.FileHandler(path)

    # create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s',
      '%Y-%m-%d %H:%M:%S')

    # add formatter to handler
    handler.setFormatter(formatter)

    # add handler to logger
    logger.addHandler(handler)
    return logger

if __name__ == "__main__":
  #log = Logger.get("bla.log")
  log = Logger.get(verbose=False)
  log.debug('debug message')
  log.info('info message')
  log.warn('warn message')
  log.error('error message')
  log.critical('critical message')
