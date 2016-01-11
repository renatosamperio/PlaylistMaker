#!/usr/bin/env python

import logging
import zmq
import threading
import sys, os
import time
import random
import ctypes
import json
import datetime 

from Utils.MongoDB import MongoHandler
from GStreamer import StreamPlayer

def jsonSerialisable(state):
  new_state = state.copy()
  new_state['message_time'] = str(state['message_time'])
  if 'last_message' in state.keys():
    new_state['last_message'] = str(state['last_message'])
  #for key in new_state .keys():
    #if isinstance(new_state [key], datetime.date):
      #new_state[key] = str(new_state[key])
  return new_state
  
class Inspector(threading.Thread):

    def __init__(self, streamer=None, logger=None, console=None, endpoint=''):
      ''' '''
      threading.Thread.__init__(self)
      component	    = self.__class__.__name__
      self.stop     = threading.Event()
      self.state    = None
      self.idle     = 0.0
      self.streamer = streamer
      self.indent   = "    "
      self.context  = None
      self.endpoint = endpoint
      self.socket   = None
      self.console  = console
      self.database = MongoHandler('test_database', 'tracks')
      
      if logger:
	self.logger = logger
	self.indent = "    "
      
      self.logger.debug(self.indent+"Starting stream inspection in [%s]"%self.endpoint)
      if streamer is not None:
	self.start()
      
    def SetZMQ(self):
      ''' Setting up ZMQ connection'''
      socket = []
      poller = None
      if len(self.endpoint) > 0:
        self.logger.debug(self.indent+"Creating ZMQ endpoint in %s"%(self.endpoint))
        self.context = zmq.Context()

        # Preparing type of socket communication from arguments
        if len(self.endpoint)>0	:
	  socket = self.context.socket(zmq.PUB)
	  socket.bind(self.endpoint)
	  time.sleep(1)
	  
      else:
        self.logger.debug(self.indent+"Endpoint not found")

      return socket
    
    def SetStreamer(self, streamer=None):
      ''' '''
      if streamer is None:
	self.logger.debug(self.indent+"Streamer was NOT set")
	return False
      
      self.logger.debug(self.indent+"Streamer was set")
      self.streamer = streamer
      return True
      
    def IsRunning(self):
      return not self.stop.isSet()
    
    def Exit(self):
      ''' '''
      self.logger.debug(self.indent+"Stopping inspector")
      self.stop.set()
      
      if self.context:
	self.logger.debug(self.indent+"Destroying ZMQ context")
	self.context.destroy()
	self.socket  = None
	self.context = None
	time.sleep(1)

    def GetDocument(self, state):
      ''' '''
      track = {
	    'Track' : state['title'],
	    'State' :'Played',
	    'Properties' : {
	      'Played':state['organization']
	    },
	    'lastModified' : datetime.datetime.now()
	  }
      return track

    def run(self):
      ''' '''
      # Setting up ZMQ publisher
      self.socket = self.SetZMQ()
      tid = ctypes.CDLL('libc.so.6').syscall(186)
      self.logger.debug(self.indent+'Starting thread [%d]'%(tid))
      
      deviatingStream = 0
      
      self.playingTrack = ''
      self.timeTaken = None
      self.timeLimit = 30
      while not self.stop.isSet():
	
	try: 
	  if self.streamer is not None:
	    # Getting streamer state
	    self.state, self.idle = self.streamer.GetState()
	    
	    # Checking if message of last time is valid
	    if self.idle is not None:
	      self.state.update({'last_message':self.idle  })
	      
	      # Temporal solution for resetting non-playing playback
	      if self.idle > datetime.timedelta(minutes=60):
		parsed = jsonSerialisable(self.state)
		print "==== state:", json.dumps( parsed, sort_keys=True, indent=4, separators=(',', ': '))
		self.logger.debug(self.indent+"Replaying streamer after [%s]"%(str(self.idle)))
		self.streamer.Replay()
	      
	    serialised = jsonSerialisable(self.state)
	    # Publishing data
	    if self.socket:
	      msg = json.dumps( serialised, sort_keys=True, indent=4, separators=(',', ': '))
	      self.socket.send(msg)
	    
	    steamingSong = self.state["title"]
	    steamLocation= self.state["location"] 
	    percent = self.state["percent"]
	    
	    # Checking if the annoying message in German is playing or if track is DI advert
	    banner = "http://message-stream.audioaddict.com/3rdparty_di_german"
	    bannerTrack = "listeners enjoying"
	    if steamLocation == banner or steamingSong == 'DI.fm':
	      #self.logger.debug(self.indent+'Deviating stream...')
	      self.console.do_stream('reset')
	      time.sleep(1)
	      continue
	    
	    if bannerTrack in steamingSong:
	      self.logger.debug(self.indent+'Invalid song title...')
	      time.sleep(1)
	      continue
	      
	    
	    # Checking if stream bufffer is not empty (less 5%) for 30s
	    if percent < 5:
	      if self.timeTaken is None:
		self.timeTaken = datetime.datetime.now()
	      else:
		timeDiff = datetime.datetime.now() - self.timeTaken
		if timeDiff.seconds > self.timeLimit:
		  self.logger.debug(self.indent+'Buffer level has been low for more than: '+str(self.timeLimit)+'s')
		  parsed = jsonSerialisable(self.state)
		  #print "==== state:", json.dumps( parsed, sort_keys=True, indent=4, separators=(',', ': '))
		  self.logger.debug(self.indent+"Replaying streamer after [%s]"%(str(timeDiff)))
		  self.streamer.Replay()
		  self.timeTaken = None
	      time.sleep(1)
	      continue
	    else:
	      self.timeTaken = None	
	      
	    # Checking if song title is empty
	    if len(steamingSong) < 1:
	      #self.logger.debug(self.indent+'Song title is empty')
	      time.sleep(1)
	      continue
	    
	    # Checking if it is playing a track is already seen
	    if len(self.playingTrack)>0 and self.playingTrack == steamingSong:
	      #self.logger.debug(self.indent+'Playing same track')
	      time.sleep(1)
	      continue
	      
	    # Checking if song exists 
	    if self.database.Exists(steamingSong):
	      #self.logger.debug(self.indent+'Song already exists')
	      time.sleep(1)
	      continue
	    
	    # Populating database
	    document = self.GetDocument(self.state)
	    post_id = self.database.InsertOne(document)
	    self.logger.debug(self.indent+'Inserted item: '+document['Track'])
	    self.playingTrack = document['Track']
	    
	  time.sleep(1)
	except Exception as inst:
	  exc_type, exc_obj, exc_tb = sys.exc_info()
	  exception_fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
	  exception_line = str(exc_tb.tb_lineno) 
	  exception_type = str(type(inst))
	  exception_desc = str(inst)
	  self.logger.debug( "Inspector.run: %s: %s in %s:%s"%(exception_type, 
					    exception_desc, 
					    exception_fname,
					    exception_line ))
	  
      self.logger.debug(self.indent+'Finishing running inspector [%d]'%(tid))