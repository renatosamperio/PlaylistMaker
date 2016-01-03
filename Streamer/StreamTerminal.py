#!/usr/bin/python
# -*- coding: utf-8 -*-

import cmd
import sys, os
import json
import time

import youtube_dl
import eyed3
import logging
import re

from stat import *
from apiclient.errors import HttpError
from difflib import get_close_matches, SequenceMatcher

from Utils.MongoDB import MongoHandler
from Utils.PlaylistLogger import BaseLogger, LogLevel
from Utils import ParseXml2Dict
from FindSong.SearchSong import PlaylistGenerator
from StreamInspector import Inspector
from GStreamer import StreamPlayer

LOG_NAME	= 'StreamConsole'


class StreamConsole(cmd.Cmd):
    """Simple command processor example."""

    prompt = 'StreamPlayer> '
    intro = "Welcome to stream player, v.0.1"

    doc_header = 'Help commands'
    misc_header = 'misc_header'
    undoc_header = 'No help description'
    
    def __init__(self):
      cmd.Cmd.__init__(self)
      component		= self.__class__.__name__
      self.items 	= []
      self.chosenItem	= []
      self.streamer	= None
      self.inspect	= None
      self.streamURI	= ''
      
      # Creating logger
      self.logger = BaseLogger(terminal=self)
      
      # Parsing data file
      rootName = 'Streamer'
      filename = "Conf/Streamer.xml"
      self.streamConf = ParseXml2Dict(filename, rootName)
      #print "==== streamConf:", json.dumps(self.streamConf, sort_keys=True, indent=4, separators=(',', ': '))
      
    def cmdloop(self, intro=None):
	'''Command loop '''
	
        #print 'cmdloop(%s)' % intro
        #return cmd.Cmd.cmdloop(self, intro)
        try:
            return cmd.Cmd.cmdloop(self)
        except KeyboardInterrupt as e:
            self.do_exit('')
            time.sleep(0.5)
    
    def preloop(self):
      '''print 'preloop() '''
    
    def postloop(self):
      '''print 'postloop() '''
        
    def parseline(self, line):
      ret = cmd.Cmd.parseline(self, line)
      return ret
    
    def emptyline(self):
      '''Method called for empty line '''
      #return cmd.Cmd.emptyline(self)
      return
    
    def default(self, line):
        print 'default(%s)' % line
        return cmd.Cmd.default(self, line)
    
    def precmd(self, line):
      ''' Method called for preprocessing command'''
      #print 'precmd(%s)' % line
      return cmd.Cmd.precmd(self, line)
    
    def postcmd(self, stop, line):
      ''' Method called for post processing command'''
      #print 'postcmd(%s, %s)' % (stop, line)
      return cmd.Cmd.postcmd(self, stop, line)
    
    def do_EOF(self, line):
        "Exit"
        print ""
        if self.streamer is not None:
	  self.streamer.Stop()
        if self.inspect is not None:
	  self.inspect.Exit()
        return True

    def do_exit(self, line):
        print ""
        if self.streamer is not None:
	  self.streamer.Stop()
	  self.streamer.Exit()
	  
        if self.inspect is not None:
	  self.inspect.Exit()
        return True
      
    # Stream commands
    def do_stream(self, line):
      '''Provide actions to play/stop/pause and volume up/down in a stream''' 
      #print "====", line
      try: 
	operations = self.streamConf['StreamOps']['Operations']
	if not self.ValidateOps(operations, line):
	  return
	
	tasks = line.split()
	
	if tasks[0] == "show":
	  streams = self.streamConf["Streams"]["Stream"]
	  for i in range(len(streams)):
	    stream = streams[i]
	    desc = stream['StreamDescription']
	    uri = stream['Uri']
	    self.logger.debug("   ["+str(i+1)+"] "+desc+":\n"+"    "+uri)
	elif tasks[0] == 'set_uri':
	  if len(tasks)<2:
	    self.logger.debug('  Warning: No index given')
	    return 
	    
	  index = int(tasks[1])
	  streams = self.streamConf["Streams"]["Stream"]
	  if index >= len(streams) or index < 0:
	    self.logger.debug("  Index ["+tasks[1]+"] is out of range")
	    return 

	  # Setting up stream value from configuration file
	  self.logger.debug("  Setting URI: "+streams[index]['StreamDescription'])
	  self.streamURI = streams[index]['Uri']
	  
	  # Setting up URI in player
	  if self.streamer is not None and self.streamer.IsRunning():
	    self.logger.debug('  Passing stream URI...')
	    self.streamer.SetURI(self.streamURI)
	    return 
	elif tasks[0] == "play":
	  if len(self.streamURI)<1:
	    self.logger.debug("  No URI has been defined")
	    return
	  
	  if self.streamer == None:
	    self.streamer = StreamPlayer(uri=self.streamURI, 
					 logger=self.logger)
	    self.emptyline()
	  elif self.streamer.IsRunning():
	    self.streamer.Play()
	    
	elif tasks[0] == "pause":
	  if self.streamer is not None:
	    self.streamer.Pause()
	elif tasks[0] == "stop":
	  if self.streamer is not None:
	    self.streamer.Stop()
	elif tasks[0].startswith("volume"):
	  volume = self.streamer.Volume()
	  if tasks[0] == "volume_up":
	    print "Volume: ", self.streamer.VolumeUp(volume)
	  elif tasks[0] == "volume_down":
	    print "Volume: ", self.streamer.VolumeDown(volume)
	elif tasks[0] == "inspect":
	  if self.streamer is None:
	    self.logger.debug("  Streamer not started yet")
	    
	  elif self.inspect is None:
	    if len(tasks)>1 and '://' in tasks[1]:
		self.inspect = Inspector(streamer=self.streamer, 
					logger=self.logger,
					console=self,
					endpoint=tasks[1])
	    else:
	      self.inspect = Inspector(streamer=self.streamer, 
				       console=self,
				       logger=self.logger)
	  
	  elif self.inspect.IsRunning():
	    if len(tasks)>1:
	      if tasks[1] == 'stop':
		self.logger.debug("  Stream inspection stopped")
		self.inspect.Exit()
	    else:
	      self.logger.debug("  Stream inspection already running")
	    
	  elif not self.inspect.IsRunning():
	    self.inspect.Exit()
	    if len(tasks)>1 and '://' in tasks[1]:
		self.inspect = Inspector(streamer=self.streamer, 
					logger=self.logger, 
					console=self,
					endpoint=tasks[1])
	    else:
	      self.logger.debug("  Restarting stream inspection")
	      self.inspect = Inspector(streamer=self.streamer, 
				       console=self,
				       logger=self.logger)
	
	elif tasks[0] == 'reset':
	  self.logger.debug("  Resetting streamer...")
	  self.streamer.Stop()
	  self.streamer.Exit()
	  self.streamer = None
	  time.sleep(1)
	  self.do_stream('play')
	  self.logger.debug("  Setting new streamer for inspecting")
	  self.inspect.SetStreamer(streamer=self.streamer)
	  #self.inspect.clone(self.inspect.streamer)      
	  
      except ValueError:
	self.logger.debug("  Incorrect index value: "+line.split()[1])
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

    def complete_stream(self, text, line, begidx, endidx):
      keys = self.streamConf['StreamOps']['Operations']
      if not text:
	  completions = keys
      else:
	  completions = [ f
			  for f in keys
			  if f.startswith(text) ]
      return completions
      
    def help_stream(self):
        print '\n'.join([ 'stream [play]',
                           '\tPlays a stream',
                           'stream [pauses]',
                           '\tPauses a stream',
                           'stream [stop]',
                           '\tVolume up/down',
                           'stream [volume] [up down]',
                           '\tSets volume up or down',
                           'stream [show]',
			   '\tShows available URI',
			   'stream [set_uri] [INDEX]',
			   '\tSets a new URI by using index',
                           ])
      
    def ValidateOps(self, operations, line):
      '''Generic validation'''
      keys = operations
      if len(line) < 1:
	self.logger.debug('  Warning: No option given')
	return False
      
      tasks = line.split()
      if tasks[0] not in operations:
	self.logger.debug('  Warning: Invalid option: '+line)
	return False
      
      return True
      
    # Report commands
    def do_tracks(self, line):
      '''Provide actions to play/stop/pause and volume up/down in a stream'''  
      tasks = line.split()
      try: 
	
	  operations = self.streamConf['StreamReport']['Operations']
	  if not self.ValidateOps(operations, line):
	    return
	  
	  #print '====', tasks
	  database = MongoHandler('test_database', 'tracks')
	  
	  if tasks[0] == "all":
	    self.logger.debug("  Getting tracks from database")
	    posts = database.Report()
	    myFormat = '%5s|%8s|%85s|'
	    sizePosts = posts.count()
	    for i in range(sizePosts):
	      post = posts[i]
	      print myFormat%(str(i),post['State'], post['Track'])
	  elif tasks[0] == "clean":
	    self.logger.debug("  Removing repeated tracks")
	    posts = database.CleanRepeated()
	  elif tasks[0] == "played":
	    self.logger.debug("  Getting all played tracks from database")
	    posts = database.Report('Played')
	    myFormat = '%5s|%8s|%85s|'
	    sizePosts = posts.count()
	    for i in range(sizePosts):
	      post = posts[i]
	      print myFormat%(str(i),post['State'], post['Track'])      
	  elif tasks[0] == "download":
	    ''' '''
	    # Choosing how many tracks should be downloaded in one go
	    totalTracks = 1
	    if len(tasks)>1:
	      totalTracks = int(tasks[1])
	    posts = database.Report('Played')
	    sizePosts= posts.count()
	    self.logger.debug("  Getting %d of %d played track(s) from database"%
		       (totalTracks, sizePosts))
	    
	    # Updating the tracks
	    for i in range(totalTracks):
	      post = posts[i]
	      
	      # Searching current track
	      trackName = post['Track']	   
	      self.logger.debug(" %d/%d Searching: [%s] ..."%
			 (i+1, totalTracks, trackName))
	      bestMatch, findings = self.SearchSong(trackName)
	      
	      if findings<1:
		self.logger.debug('  No results from online query')
		state = 'NotFound'
		updated = database.UpdateTrackState(trackName, state)
		updatedLog = 'updated' if updated else 'NOT updated'
		self.logger.debug("  State in played record was %s with [%s]"%(updatedLog, state))
		continue
	      
	      if len(bestMatch)<1:
		self.logger.debug("  Best match for track was not found")
		state = 'NotMatched'
		updated = database.UpdateTrackState(trackName, state)
		updatedLog = 'updated' if updated else 'NOT updated'
		self.logger.debug("  State in played record was %s with [%s]"%(updatedLog, state))
		continue

	      # Downloading track
	      path = self.DownloadTrack(bestMatch)
	      if len(path)>0:
		updated = database.UpdateTrackState(trackName, 'Downloaded', path=path)
		updatedLog = 'updated' if updated else 'NOT updated'
		self.logger.debug("  State in played record was %s with [%s]"%(updatedLog, 'Downloaded'))
	    
      except ValueError as inst:
	if tasks[0] == "download":
	  self.logger.debug("  Required download files is not a NUMBER")
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
    
    def complete_tracks(self, text, line, begidx, endidx):
      keys = self.streamConf['StreamReport']['Operations']
      if not text:
	  completions = keys
      else:
	  completions = [ f
			  for f in keys
			  if f.startswith(text) ]
      return completions
    
    def help_tracks(self):
        print '\n'.join([ 'tracks [all]',
                           '\tDisplay all songs',
                           'tracks [clean]',
                           '\tRemoves repeated entries'
                           'tracks [played]',
                           '\tDisplay only played tracks',
                           'tracks [download] [NUMBER]',
                           '\tDownloads [NUMBER] played tracks, default is 1 track'
                           ])
      
    def SearchSong(self, trackName):
      ''' '''
      try:
	# Getting configuration options
	maxResults = int(self.streamConf['SearchOptions']['maxResults'])
	maxRatio   = float(self.streamConf['SearchOptions']['maxRatio'])
	maxValue   = 0.0
	bestMatch  = ()
	
	# Preparing Youtube query
	options = {'query':trackName, 'maxResults':maxResults}
	songFinder = PlaylistGenerator()
	items = songFinder.SearchInYouTube(options)
	
	#print "==== items:", len(items['videos'])
	videosFound = len(items['videos'])
	if len(items['videos'])<1:
	  return bestMatch, videosFound
	
	for item in items['videos']:
	  match = get_close_matches(item['title'], [trackName, ''])
	  if len(match)>0:
	    #print "  =>", item['title']
	    s = SequenceMatcher(None, item['title'], trackName)
	    ratio = s.ratio()
	    #print ratio,"==>", item['title'], ":", maxValue >= ratio
	    if ratio >= maxValue:
	      maxValue  = ratio
	      bestMatch = (ratio, item['id'], item['title'])
	  #else:
	    #print "    ", item['title']
	      
	#print "==== BestMatch:", bestMatch
	if len(bestMatch)<1:
	  return bestMatch, videosFound
	
	bestMatchRatio = bestMatch[0]
	if bestMatchRatio < maxRatio:
	  self.logger.debug('    Ratio is lower than maximum allowed of %s'%str(maxRatio))
	  isGoodTitle = self.WordByWord(bestMatch[2], trackName, bestMatchRatio)
	  if not isGoodTitle:
	    self.logger.debug('    Does not matches the entry...')
	    bestMatch = ()
	return bestMatch, videosFound
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

    def DownloadTrack(self, bestMatch):
      ''' '''
      downloaded = ''
      try:
	itemId = bestMatch[1]
	itemTitle = bestMatch[2]
	url = 'https://www.youtube.com/watch?v='+itemId
	ydl_opts = {
	  u'keepvideo': False, 
	  u'format': u'bestaudio/best', 
	  u'postprocessors': [{u'preferredcodec': u'mp3',
	  u'preferredquality': u'0',
	  u'key': u'FFmpegExtractAudio'}]
	}
	with youtube_dl.YoutubeDL(ydl_opts) as ydl:
	  success = ydl.download([url])
	  #print "====", success
	  
	  # Get a nice file name, otherwise it screws the unix file system
	  
	  # Stating new downloaded file
	  fileName = itemTitle+"-"+itemId+'.mp3'
	  if success == 0:
	    #fileName = re.sub(re.escape(''.join('"')) , '\"', fileName)
	    fileName = self.ChangeSpecialChars(fileName)
	    self.logger.debug('  + Stating file: '+fileName)
	    mode = os.stat(fileName).st_mode
	    if S_ISREG(mode):
	      self.logger.debug('  + Successfully downloaded file: '+fileName)
	    
	    # Creating store path if not exist
	    destinationPath = os.path.abspath('DownlaodedSongs')
	    if not os.path.exists(destinationPath):
	      self.logger.debug('  + Creating directoy '+destinationPath)
	      os.makedirs(destinationPath)
	    else:
	      self.logger.debug('  + Directory '+destinationPath+' exists')
	      
	    # Moving files to storing directory
	    source = os.path.abspath('')+'/'+fileName
	    dest = destinationPath+'/'+fileName
	    os.rename(source, dest)
	    self.logger.debug('  + Storing '+fileName)
	    downloaded = dest
	    
      except Exception as inst:
	exc_type, exc_obj, exc_tb = sys.exc_info()
	exception_fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
	exception_line = str(exc_tb.tb_lineno) 
	exception_type = str(type(inst))
	exception_desc = str(inst)
	print "MongoHandler.Exists: %s: %s in %s:%s"%(exception_type, 
					  exception_desc, 
					  exception_fname,
					  exception_line )
	
      finally:
	return downloaded
      
    def ChangeSpecialChars(self, str1):
      specialChars = '"'
      newStr = ''
      for c in str1:
	if c == '"':
	  newStr += "\'"
	elif c == "'":
	  newStr += "\'"
	else:
	  newStr += c
      return newStr
      
    def TextCleanup(self, text):
      new = ""
      for i in text:
	  if i not in '.,|[!@#$%^&*?_~-+/()]':
	      new += i
      return new
  
    def WordByWord(self, str1, str2, bestRatio):
      ''''''
      try:
	# Getting best score word-by-word
	word1 = str1.split()
	word2 = str2.split()
	
	listing = []
	for w in word1:
	  if len(w)>1:
	    w = self.TextCleanup(w)
	    highest = 0.0
	    curr_word = [w, '', highest]
	    for v in word2:
	      if len(v)>1:
		v = self.TextCleanup(v)
		s = SequenceMatcher(None, w, v)
		ratio = s.ratio()
		#print "   - comparing: [",w,"/", v, "]:", ratio
		if ratio >= highest:
		  highest = ratio
		  curr_word[1] = v
		  curr_word[2] = ratio
	    if curr_word[2]>0.0:
	      #print "   ",curr_word
	      listing.append(curr_word)
	    #print "="*20
	
	# Checking average of matches
	sumed = 0.0
	hits = 0.0
	length = len(listing)
	for word in listing:
	  sumed += word[2]
	  if word[2]>=0.8:
	    hits+=1
	average = (sumed/length)
	hitsPercentage = (hits/length)
	#print "Length:", length
	#print "Avg:", average
	#print "Hits:", hitsPercentage
	
	msg = "  Best match is:\n\t ratio:\t\t"+str(bestRatio)+ 	\
			       "\n\t best:\t\t"+str1+		\
			       "\n\t original:\t"+str2+		\
			       "\n\t average:\t"+str(average)+		\
			       "\n\t hits:\t\t"+str(hitsPercentage)
	self.logger.debug(msg)
	isGoodTitle = average >= ratio or hitsPercentage >= 0.7
	return isGoodTitle
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
      
def main():
  if len(sys.argv) > 1:
    StreamConsole().onecmd(' '.join(sys.argv[1:]))
  else:
    #StreamConsole().cmdloop('Starting terminal for stream player...')
    StreamConsole().cmdloop()

    
if __name__ == '__main__': 
  main()
