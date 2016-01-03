#!/usr/bin/env python

import pygst
pygst.require("0.10")
import gst
import time
import sys, os
import json
import datetime
import threading
import logging
import pymongo

from Utils.PlaylistLogger import BaseLogger, LogLevel

from bson import ObjectId
from pymongo import MongoClient
from gst.extend import discoverer
from random import randint

# this is very important, without this, callbacks from gstreamer thread
# will messed our program up
import gobject
gobject.threads_init()
      
def state2json(state):
  new_state = state.copy()
  new_state['message_time'] = str(state['message_time'])
  #new_state['last_message'] = str(state['last_message'])
  return new_state

def stream_state():
  state = {}
  state.update({'percent': -1})
  state.update({'organization':''})
  state.update({'genre':''})
  state.update({'location':''})
  state.update({'audio-codec':''})
  state.update({'nominal-bitrate':''})
  state.update({'has-crc':''})
  state.update({'channel-mode':''})
  state.update({'audio-codec':''})
  state.update({'bitrate':-1})
  state.update({'minimum-bitrate':-1})
  state.update({'bitrate':-1})
  state.update({'maximum-bitrate':-1})
  state.update({'old_state':''})
  state.update({'new_state':''})
  state.update({'pending':''})
  state.update({'stream_status':''})
  state.update({'title':''})
  state.update({'message_time': None})
  #state.update({'last_message': None})
  #state.update({'':''})
  return state
      
class StreamPlayer(threading.Thread):
    ''' '''
    def __init__(self, uri='', verbose=True, logDB=False, logger=None):
      '''Class constructor '''
      threading.Thread.__init__(self)
      component		= self.__class__.__name__
      self.stop		= threading.Event()
      self.verbose	= verbose
      self.last_message	= None
      
      if logger:
	self.logger	= logger
	self.indent	= "    "

      self.LogDBOn	= logDB
      if self.LogDBOn:
	''' '''
	# Creating mongo client
	client = MongoClient('localhost', 27017)
	
	# Getting instance of database
	db = client.test_database

	# Getting instance of collection
	self.collection = db.streamer

      if len(uri)>0:
	self.state  = stream_state()
	self.uri    = uri
	self.bus    = None
	self.player = None
	
	# Starting thread
	self.start()
      else:
	m = self.indent+"URI not set, exiting"
	self.logger.debug(m)

    def setup(self):
	self.logger.debug(self.indent+"Setting up streamer")

	#creates a playbin (plays media form an uri) 
	self.player = gst.element_factory_make("playbin", "player")
	  
	#set the uri
	if self.uri and gst.uri_is_valid(self.uri):
	  self.player.set_property('uri', self.uri)
	else:
	  self.logger.debug(self.indent+"Invalid URI")

	#start playing
	self.player.set_state(gst.STATE_PLAYING)

	#listen for tags on the message bus; tag event might be called more than once
	self.bus    = self.player.get_bus()
	self.bus.enable_sync_message_emission()
	self.bus.add_signal_watch()

	#used to get messages that gstreamer emits
	self.bus.connect("message", self.on_message)
	
    def on_message(self, bus, message):
      ''' '''      
      if message is not None:
	if message.type == gst.MESSAGE_STATE_CHANGED:  
	  old_state, new_state, pending = message.parse_state_changed()
	  self.state['old_state'] = old_state.value_name
	  self.state['new_state'] = new_state.value_name
	  self.state['pending'] = pending.value_name
	  
	elif message.type == gst.MESSAGE_STREAM_STATUS:
	  st = message.parse_stream_status()
	  self.state['stream_status'] = st[0].value_name
	  
	elif message.type == gst.MESSAGE_BUFFERING:
	  percent = message.parse_buffering()
	  self.state['percent'] = percent
	  
	elif message.type == gst.MESSAGE_TAG:
	  taglist = message.parse_tag()
	  for key in taglist.keys():
	    self.state[key] = taglist[key]
	      
	elif message.type == gst.MESSAGE_EOS:
	  ''' '''
	  self.logger.debug(self.indent+"Error in transmission was found")
	  self.Stop()
	  self.Play()
	elif message.type == gst.MESSAGE_ERROR:
	  ''' '''
	  self.logger.debug(self.indent+"End of transmission was found")
	  self.Stop()
	  self.Play()
	elif message.type == gst.MESSAGE_ASYNC_DONE:
	  ''' '''
	elif message.type == gst.MESSAGE_NEW_CLOCK:
	    clock = message.parse_new_clock()
	else:
	  print '*** on_message[',message.type,']:', message
	  print "========================================================="

    def run(self):
      self.execute()
      
    def IsRunning(self):
      return not self.stop.isSet()
    
    def Pause(self):
      '''Pausiing streamer '''
      self.logger.debug(self.indent+"Pausing streamer")
      self.player.set_state(gst.STATE_PAUSED	)
      
    def Play(self):
      '''Playing streamer '''
      self.logger.debug(self.indent+"Playing streamer")
      self.player.set_state(gst.STATE_PLAYING)
      
    def Stop(self):
      '''Stopping streamer '''
      self.logger.debug(self.indent+"Stopping streamer")
      self.player.set_state(gst.STATE_NULL)
	
    def Volume(self):
      '''Stopping streamer '''
      volume = self.player.get_property('volume')
      self.logger.debug(self.indent+"Streamer volume: "+str(volume))
      return volume
    
    def VolumeUp(self, volume):
      '''Stopping streamer '''
      #new_volume = volume-0.05 if volume<=???? else 0.0
      self.logger.debug(self.indent+"Increasing volume to: "+str(volume))
      self.player.set_property('volume', volume+0.05)
	
    def VolumeDown(self, volume):
      '''Stopping streamer '''
      new_volume = volume-0.05 if volume>0.05 else 0.0
      self.logger.debug(self.indent+"Lowering volume to: "+str(new_volume))
      self.player.set_property('volume', new_volume)

    def SetURI(self, uri):
      ''' '''
      #set the uri
      if uri and gst.uri_is_valid(uri):
	self.logger.debug(self.indent+"Setting URI in streamer")
	self.player.set_property('uri', uri)
	self.Stop()
	self.Play()

    def GetState(self):
      return self.state, self.last_message

    def Replay(self):
      self.Stop()
      waiting_time = randint(0,5)
      time.sleep(waiting_time)
      self.Play()
      now = datetime.datetime.now()
      self.last_message = now - now 
      
    def Exit(self):
      ''' '''
      self.logger.debug(self.indent+"Stopping streamer loop")
      self.stop.set()
      
    def execute(self):
      '''wait and let the music play'''
      # Setting up GStremer
      self.setup()
	
      self.logger.debug(self.indent+"Starting streaming...")
      lastEntry = {}
      while not self.stop.isSet():
	''' '''
	#print "="*100
	try: 
	  message = self.bus.poll(gst.MESSAGE_ANY, 1)
	  ##debugLabel = ''
	  if message is not None:
	    ##debugLabel = "Getting message..."+str(self.last_message)
	    self.state['message_time'] = datetime.datetime.now()
	  else:
	    #self.state['last_message'] = datetime.datetime.now() - self.state['message_time']
	    self.last_message = datetime.datetime.now() - self.state['message_time']
	    #debugLabel = "Invalid message: "+str(self.state['last_message'])
	    ##debugLabel = "Invalid message: "+str(self.last_message)
	    
	  # Preparing JSON version of document
	  document = state2json(self.state)
	  
	  # Checking if consequtive entries are not similar
	  titleIsNotAdv = self.state["title"] != ""
	  if lastEntry != self.state:
	    
	    # Inserting document in database
	    if self.LogDBOn:
	      post_id = self.collection.insert_one(document)
	    
	    # Printing legible log message
	    #logMsg = "Record time [%s]"%document['message_time']
	    #if self.last_message != None:
	    #if self.state['last_message'] != None:
	      #logMsg += (", last message gotten at [%s]"%self.last_message)
	      #logMsg += (", last message gotten at [%s]"%self.state['last_message'])
	    #self.logger.debug(logMsg)
	    
	    #print "[",areEqual,"]:\nx=", lastEntry, "\ny=", self.state,"\nx!=y"
	    lastEntry = self.state.copy()
	  ##debugLabel+=("\n"+json.dumps( document, sort_keys=True, indent=4, separators=(',', ': ')))
	  #else:
	    #debugLabel += "  => Are equal"
	  ##print debugLabel
	     
	  time.sleep(0.1)
	  
	except Exception as inst:
	  exc_type, exc_obj, exc_tb = sys.exc_info()
	  exception_fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
	  exception_line = str(exc_tb.tb_lineno) 
	  exception_type = str(type(inst))
	  exception_desc = str(inst)
	  self.logger.debug( "  %s: %s in %s:%s"%(exception_type, 
					    exception_desc, 
					    exception_fname,
					    exception_line ))
      self.logger.debug(self.indent+"Finishing running stream")

    def get_state_change(self, old, new):
      table = {(gst.STATE_NULL, gst.STATE_READY):
             gst.STATE_CHANGE_NULL_TO_READY,
             (gst.STATE_READY, gst.STATE_PAUSED):
             gst.STATE_CHANGE_READY_TO_PAUSED,
             (gst.STATE_PAUSED, gst.STATE_PLAYING):
             gst.STATE_CHANGE_PAUSED_TO_PLAYING,
             (gst.STATE_PLAYING, gst.STATE_PAUSED):
             gst.STATE_CHANGE_PLAYING_TO_PAUSED,
             (gst.STATE_PAUSED, gst.STATE_READY):
             gst.STATE_CHANGE_PAUSED_TO_READY,
             (gst.STATE_READY, gst.STATE_NULL):
             gst.STATE_CHANGE_READY_TO_NULL}
      return table.get((old, new), 0)

if __name__ == '__main__':
  myFormat = '%(asctime)s|%(name)15s|%(message)s'
  logging.basicConfig(format=myFormat, level=logging.DEBUG)
  
  uri = 'http://pub6.di.fm:80/di_house?98a17136cec3b063de6e3d34'
  streamer = StreamPlayer(uri=uri)
  streamer.execute()
  
  
	#elif message.type == gst.MESSAGE_ERROR:
	    #print '    type: MESSAGE_ERROR'
	    #self.player.set_state(gst.STATE_NULL)
	    #(err, debug) = message.parse_error()
	    #print "*** Error: %s" % err, debug    
	#elif message.type == gst.MESSAGE_EOS:
	    #print '    type: MESSAGE_EOS'
	    #duration = self.player.query_duration(gst.FORMAT_TIME)
	    #print '*** Duration', duration
	#elif message.type == gst.MESSAGE_ELEMENT:
	    #print '    type: MESSAGE_ELEMENT'
	    #print '    members: ',message.__class__.__dict__
	#elif message.type == gst.MESSAGE_INFO:
	    #print '    type: MESSAGE_INFO'
	    #print '    members: ',message.__class__.__dict__
	#elif message.type == gst.MESSAGE_STATE_DIRTY:
	    #print '    type: MESSAGE_STATE_DIRTY'
	#elif message.type == gst.MESSAGE_STEP_DONE:
	    #print '    type: MESSAGE_STEP_DONE'
	#elif message.type == gst.MESSAGE_CLOCK_PROVIDE:
	    #print '    type: MESSAGE_CLOCK_PROVIDE'
	#elif message.type == gst.MESSAGE_CLOCK_LOST:
	    #print '    type: MESSAGE_CLOCK_LOST'
	#elif message.type == gst.MESSAGE_STRUCTURE_CHANGE:
	    #print '    type: MESSAGE_STRUCTURE_CHANGE'
	#elif message.type == gst.MESSAGE_APPLICATION:
	    #print '    type: MESSAGE_APPLICATION'
	    #print '    members: ',message.__class__.__dict__
	#elif message.type == gst.MESSAGE_SEGMENT_START:
	    #print '    type: MESSAGE_SEGMENT_START'
	#elif message.type == gst.MESSAGE_SEGMENT_DONE:
	    #print '    type: MESSAGE_SEGMENT_DONE'
	#elif message.type == gst.MESSAGE_LATENCY:
	    #print '    type: MESSAGE_LATENCY'
	#elif message.type == gst.MESSAGE_ASYNC_START:
	    #print '    type: MESSAGE_ASYNC_START'
	#elif message.type == gst.MESSAGE_REQUEST_STATE:
	    #print '    type: MESSAGE_REQUEST_STATE'
	#elif message.type == gst.MESSAGE_STEP_START:
	    #print '    type: MESSAGE_STEP_START'
	#elif message.type == gst.MESSAGE_QOS:
	    #print '    type: MESSAGE_QOS'
	    #print '    members: ',message.__class__.__dict__s	    
	#elif message.type == gst.MESSAGE_PROGRESS:
	    #print '    type: MESSAGE_PROGRESS'
	    #print '    members: ',message.__class__.__dict__
	#elif message.type == gst.MESSAGE_TOC:
	    #print '    type: MESSAGE_TOC'
	#elif message.type == gst.MESSAGE_RESET_TIME:
	    #print '    type: MESSAGE_RESET_TIME'
	#elif message.type == gst.MESSAGE_STREAM_START:
	    #print '    type: MESSAGE_STREAM_START'
	    #print '    members: ',message.__class__.__dict__
	#elif message.type == gst.MESSAGE_NEED_CONTEXT:
	    #print '    type: MESSAGE_NEED_CONTEXT'
	#elif message.type == gst.MESSAGE_HAVE_CONTEXT:
	    #print '    type: MESSAGE_HAVE_CONTEXT'
	#elif message.type == gst.MESSAGE_EXTENDED:
	    #print '    type: MESSAGE_EXTENDED'
	#elif message.type == gst.MESSAGE_DEVICE_ADDED:
	    #print '    type: MESSAGE_DEVICE_ADDED'
	#elif message.type == gst.MESSAGE_DEVICE_REMOVED:
	    #print '    type: MESSAGE_DEVICE_REMOVED'
	
	
	#if no_print:
	  #print '    message.structure', message.structure.get_name()  
	  #print '*** on_message[',message.type,']:', message
	  #print "========================================================="