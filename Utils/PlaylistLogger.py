#!/usr/bin/python

import logging

from enum import Enum

class LogLevel(Enum):
    CRITICAL		= 50
    ERROR		= 40
    WARNING		= 30
    FILE		= 21
    INFO		= 20  # => file
    CONSOLE		= 11
    DEBUG		= 10  # => console
    NOTSET		= 0
    
class Singleton(type):
    def __init__(cls, name, bases, dict):
        super(Singleton, cls).__init__(name, bases, dict)
        cls.instance = None 

    def __call__(cls,*args,**kw):
        if cls.instance is None:
            cls.instance = super(Singleton, cls).__call__(*args, **kw)
        return cls.instance
      
class BaseLogger(object):
  __metaclass__ = Singleton
    
  def __init__(self):
    """ Returns a logger with BarixTerminal logger 
    using barixTerminal.log files"""
    # create logger
    self.logger = logging.getLogger('PlaylistMaker')
    self.logger.setLevel(logging.DEBUG)
    
    # create file handler which logs even debug messages
    fh = logging.FileHandler('playlistMaker.log')
    fh.setLevel(LogLevel.INFO)

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(LogLevel.DEBUG)

    # create formatter
    formatterScreen = logging.Formatter('%(message)s')
    formatterFile   = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # add formatter to ch
    ch.setFormatter(formatterScreen)
    fh.setFormatter(formatterFile)

    # add ch to logger
    self.logger.addHandler(ch)
    self.logger.addHandler(fh)

  def log(self, level, msg):
    if self.logger is not []:
      if level == LogLevel.CRITICAL:
	self.logger.critical(msg)
      elif level == LogLevel.ERROR:
	self.logger.error(msg)
      elif level == LogLevel.WARNING:
	self.logger.warning(msg)
      elif level == LogLevel.INFO:
	self.logger.info(msg)
      elif level == LogLevel.DEBUG:
	self.logger.debug(msg)
      elif level == LogLevel.FILE:
	self.logger.info(msg)
      elif level == LogLevel.CONSOLE:
	print msg
    else:
      print "?("+str(level)+") :", msg