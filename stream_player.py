#!/usr/bin/env python

import sys
import logging
import logging.handlers

import Streamer

def main():

  if len(sys.argv) > 1:
      print "usage: streamplayer.py <...>"
      raise SystemExit
  Streamer.StreamTerminal.main()
  
if __name__ == '__main__':
  main()

  