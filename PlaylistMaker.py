#!/usr/bin/python

import os
import cmd
import logging
import sys
import json

import youtube_dl
import eyed3

from stat import *
from apiclient.errors import HttpError

from FindSong.SearchSong import PlaylistGenerator
from Utils.PlaylistLogger import BaseLogger, LogLevel
from SongData.DiscogsClient import DiscogsQuery

class PlaylistTerm(cmd.Cmd):
    """Simple command processor example."""

    prompt = 'PlaylistMaker> '
    intro = "Welcome to playlist maker, v.0.1"

    doc_header = 'Help commands'
    misc_header = 'misc_header'
    undoc_header = 'No help description'
    
    def __init__(self):
      cmd.Cmd.__init__(self)
      self.items = []
      self.chosenItem = []
      
      # Creating logger
      self.logger = BaseLogger()
      self.plMaker = PlaylistGenerator()
      self.query = DiscogsQuery()
    
    def cmdloop(self, intro=None):
	'''Command loop '''
        #print 'cmdloop(%s)' % intro
        return cmd.Cmd.cmdloop(self, intro)
    
    def preloop(self):
        0;#print 'preloop()'
    
    def postloop(self):
	0;#print 'postloop()'
        
    def parseline(self, line):
        ret = cmd.Cmd.parseline(self, line)
        #print '*** parseline(%s) =>' % line
        #print "*** ret:",ret
        return ret
    
    #def onecmd(self, s):
      #''' Method called for one command execution'''
      #print 'onecmd(%s)' % s
      #return cmd.Cmd.onecmd(self, s)

    def emptyline(self):
      '''Method called for empty line '''
      #print 'emptyline()'
      return cmd.Cmd.emptyline(self)
    
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
        return True
    
    # Playlist maker commands
    def do_search(self, line):
	"""Search in Youtube engine for a song"""
        #print 'search:', line
	options = {}
	options['query'] = line
	options['maxResults'] = 50 
	#self.items = self.plMaker.SearchInYouTube(options)
        #self.items = PlaylistGenerator.SearchInYouTube(options)
        try:
	  self.items = self.plMaker.SearchInYouTube(options)
	  #jsonMsg = json.dumps(self.items, sort_keys=True, indent=4, separators=(',', ': '))
	  #print jsonMsg
	except HttpError, e:
	  print "An HTTP error %d occurred:\n%s" % (e.resp.status, e.content)
    
    def do_open_file(self, line):
      try:
	fileName = 'tmp/sample.json'
	logMsg = 'Opening file: '+fileName
	self.logger.log(LogLevel.CONSOLE, logMsg)
	with open (fileName, "r") as myfile:
	  data = myfile.read().replace('\n', '')
	  self.items = json.loads(data)
      except IOError as e:
	print "I/O error({0}): {1}".format(e.errno, e.strerror)
      
    def do_list(self, line):
	""" List existing items"""
	# Check if argument line exists in item keys
	if self.items == []:
	  self.logger.log(LogLevel.CONSOLE, '  Warning: items are empty')
	  return
		   
	keys = self.items.keys()
	options = self.items.keys()
	options.append('all')
	options.append('pickups')
	if len(keys) < 1:
	  self.logger.log(LogLevel.CONSOLE, '  Warning: No items types were found')
	  return
	
	if len(line)>0 and line not in options:
	  self.logger.log(LogLevel.CONSOLE, '  Warning: Invalid option: '+line)
	  return
	  
	try:
	  if line =='' or line == 'all':
	    items = self.items
	    index = 1
	    for key in keys:
	      for item in items[key]:
		#print item['title'].strip()
		msg = '  ['+str(index)+']: '+key+': '+item['title'].strip()
		self.logger.log(LogLevel.CONSOLE, msg)
		index += 1
	    return
	  elif line == 'pickups':
	    if self.chosenItem == []:
	      self.logger.log(LogLevel.CONSOLE, '  Choose a video to download')
	    else:
	      index = 0
	      for item in self.chosenItem:
		msg = '  ['+str(index)+']: '+item['title']+"]"
		self.logger.log(LogLevel.CONSOLE, msg)
		index += 1
	    return
	  else:
	    #print '*** line', line
	    items = self.items[line]
	    if len(items) > 0:
	      index = 1
	      self.logger.log(LogLevel.CONSOLE, 'Listing items:')
	      for item in items:
		msg = '  ['+str(index)+']: '+item['title'].strip()
		self.logger.log(LogLevel.CONSOLE, msg)
		index += 1
	    else:
	      self.logger.log(LogLevel.CONSOLE, 'Warning: No items found')
	      return
	except IOError as e:
	  print "I/O error({0}): {1}".format(e.errno, e.strerror)

    def complete_list(self, text, line, begidx, endidx):
      keys = self.items.keys()
      keys.append('all')
      keys.append('pickups')
      if not text:
	  completions = keys
      else:
	  completions = [ f
			  for f in keys
			  if f.startswith(text)
			  ]
      return completions

    def do_pickup(self, line):
	""" List existing items"""
	# Check if argument line exists in item keys
	keys = self.items.keys()
	cmds = line.split(' ')
	try:
	  if len(cmds) > 1:
	    
	    # Checking if last character is an 's'
	    itemType = cmds[0]
	    if itemType[-1:] != 's':
	      itemType = itemType+'s'
	    
	    # Looking for position of item in list
	    index = int(cmds[1])-1
	    if itemType in keys:
	      if index in range(len(self.items[itemType])):
		# Checking if youtube name is valid
		try:
		  youtubeTitle = self.items[itemType][index]['title']
		  title = str(youtubeTitle)
		except UnicodeEncodeError as err:
		  title = youtubeTitle
		msg = '  Chosen item: ['+title+']'
		self.chosenItem.append(self.items[itemType][index])
		self.logger.log(LogLevel.CONSOLE, msg)
	      else:
		msg = '  Warning: item index ['+str(index)+'] out of range'
		self.logger.log(LogLevel.CONSOLE, msg)
	    else:
	      msg = '  Warning: item type ['+itemType+'] not found in items list'
	      self.logger.log(LogLevel.CONSOLE, msg)
	  else:
	    itemType = cmds[0]+'s'
	    #line = line+'s'
	    if itemType not in keys:
	      self.logger.log(LogLevel.CONSOLE, '  Warning: item type ['+itemType+'] not found in items list')
	      return
	    else:
	      items = self.items[itemType]
	      if len(items) > 0:
		index = 1
		self.logger.log(LogLevel.CONSOLE, '  Choose an item to download')
		for item in items:
		  msg = '  ['+str(index)+']: '+item['title'].strip()
		  self.logger.log(LogLevel.CONSOLE, msg)
		  index += 1
	      else:
		self.logger.log(LogLevel.CONSOLE, '  Warning: No items found')
		return
	except IOError as e:
	  print "I/O error({0}): {1}".format(e.errno, e.strerror)
	except UnicodeEncodeError as err:
	  print "Unicode encoding error in", err.object
	  
    def complete_pickup(self, text, line, begidx, endidx):
      keys = self.items.keys()
      if not text:
	  completions = keys
      else:
	  completions = [ f[:-1]
			  for f in keys
			  if f.startswith(text)
			  ]
      return completions

    def do_download(self, line):
      args = line.split(' ')
      # Destination:
      if 'video' in args:
	self.do_pickup(line)
      if 'pickup' in args:
	msg = "  + There are "+str(len(self.chosenItem))+" collected videos to download"
	self.logger.log(LogLevel.CONSOLE, msg)
      else:
	self.logger.log(LogLevel.CONSOLE, "Error in downloading, invalid arguments: ("+line+")")
	return
      	
      keys = self.items.keys()
      head = 0
      total = len(self.chosenItem)
      itemID=0
      for i in range(len(self.chosenItem)):
	success = False
	try:
	  item = self.chosenItem[head]
	  itemKeys = item.keys()
	  itemID += 1
	  self.logger.log(LogLevel.CONSOLE, "  + Downloading "+str(itemID)+"/"+str(total)+": ["+item['title']+"] ...")
	  
	  url = 'https://www.youtube.com/watch?v='+item['id']
	  ydl_opts = {
	    u'keepvideo': False, 
	    u'format': u'bestaudio/best', 
	    u'postprocessors': [{u'preferredcodec': u'mp3',
	    u'preferredquality': u'0',
	    u'key': u'FFmpegExtractAudio'}]
	  }
	  with youtube_dl.YoutubeDL(ydl_opts) as ydl:
	    success = ydl.download([url])
	    # Get a nice file name, otherwise it screws the unix file system
	    
	    # Stating new downloaded file
	    fileName = item['title']+"-"+item['id']+'.mp3'
	    if success == 0:
	      self.logger.log(LogLevel.CONSOLE, '  + Stating file: '+fileName)
	      mode = os.stat(fileName).st_mode
	      if S_ISREG(mode):
		self.logger.log(LogLevel.CONSOLE, '  + Successfully downloaded file'+fileName)
	      
	      # Creating store path if not exist
	      destinationPath = os.path.abspath('DownlaodedSongs')
	      if not os.path.exists(destinationPath):
		self.logger.log(LogLevel.CONSOLE, '  + Creating directoy '+destinationPath)
		os.makedirs(destinationPath)
	      else:
		self.logger.log(LogLevel.CONSOLE, '  + Directory '+destinationPath+' exists')
	      
	      # Searching for tag if it is empty
	      if 'tag' not in itemKeys:
		msg = "  + Looking for online song meta-data"
		self.logger.log(LogLevel.CONSOLE, msg)
		self.do_tag(line)
		itemKeys = item.keys()
	
	      # Applying tags to MP3 file only if tag was found
	      if 'tag' in itemKeys and len(item['tag'])>0:
		itemTag = item['tag']
		audiofile = eyed3.load(fileName)
		audiofile.tag.artist 	= itemTag['Artist']['Name']
		audiofile.tag.album 	= itemTag['Album']
		audiofile.tag.title 	= itemTag['SongName']
		msg = '  + Applied tags to MP3 file'
		self.logger.log(LogLevel.CONSOLE, msg)
		
		# Checking if artist and song name exist
		if len(itemTag['Artist']['Name'])>0 and len(itemTag['SongName'])>0:
		  
		  artistName = audiofile.tag.artist.encode('utf-8').strip()
		  songName   = audiofile.tag.title.encode('utf-8').strip()
		  new_filename = "{0}-{1}.mp3".format(artistName, songName)
		  os.rename(fileName, new_filename)
		  fileName = new_filename
		  msg = '  + Renaming MP3 file: '+fileName
		  self.logger.log(LogLevel.CONSOLE, msg)
	      
	      # Moving files to storing directory
	      source = os.path.abspath('')+'/'+fileName
	      dest = destinationPath+'/'+fileName
	      os.rename(source, dest)
	      self.logger.log(LogLevel.CONSOLE, '  + Storing '+fileName)
	      
	    # Removing items from chosen list if they were successfully downloaded
	    del self.chosenItem[0]
	except IOError as e:
	  #print "*** 2Success:", success
	  print "I/O error({0}): {1}".format(e.errno, e.strerror)
	except OSError as e:
	  #print "*** 2Success:", success
	  if not success:
	    print "The file should be there, try to move it anyway..."
	    continue
	  print "O/S error({0}): {1}".format(e.errno, e.strerror)
   
    def complete_download(self, text, line, begidx, endidx):
      keys = self.items.keys()
      
      keys.append('pickups')
      if not text:
	  completions = keys
      else:
	  completions = [ f[:-1]
			  for f in keys
			  if f.startswith(text)
			  ]
      return completions
    
    def do_remove(self, line):
      args = line.split(' ')
      # Check if argument line exists in item keys
      if self.items == []:
	self.logger.log(LogLevel.CONSOLE, '  Warning: items are empty')
	return
      if len(args) < 1:
	self.logger.log(LogLevel.CONSOLE, '  Warning: no arguments given')
	return
      
      keys = self.items.keys()
      options = self.items.keys()
      options.append('all')
      options.append('pickups')
      if len(keys) < 1:
	self.logger.log(LogLevel.CONSOLE, '  Warning: No items types were found')
	return
      
      if len(args[0])>0 and args[0] not in options:
	self.logger.log(LogLevel.CONSOLE, '  Warning: Invalid option: '+args[0])
	return
      if self.chosenItem == []:
	self.logger.log(LogLevel.CONSOLE, '  Warning: No items have been picked up')
	return
      
      try:
	if args[0] == 'all':
	  index = 0
	  while len(self.chosenItem) > 0:
	    item = self.chosenItem.pop(index)
	    msg = "  Removing item: "+ item['title']
	    self.logger.log(LogLevel.CONSOLE, msg)
	elif args[0] == 'pickups':
	  index = int(args[1])
	  if index in range(len(self.chosenItem)):
	    item = self.chosenItem.pop(index)
	    msg = "  Removing item in "+str(index)+": " + item['title']
	    self.logger.log(LogLevel.CONSOLE, msg)
	  else:
	    self.logger.log(LogLevel.CONSOLE, '  Warning: Index not found')

      except IndexError as e:
	msg = "Index out of range: "+str(args[1])
      except ValueError as e:
	msg = "Invalid value: "+str(args[1])
	self.logger.log(LogLevel.CONSOLE, msg)
      except IOError as e:
	msg = "I/O error({0}): {1}".format(e.errno, e.strerror)
	self.logger.log(LogLevel.CONSOLE, msg)
      except Exception as e:
	msg =  str(type(e))+":"+str(e.args)
	self.logger.log(LogLevel.CONSOLE, msg)
      
    def complete_remove(self, text, line, begidx, endidx):
      keys = self.items.keys()
      keys.append('pickups')
      keys.append('all')
      if not text:
	  completions = keys
      else:
	  completions = [ f
			  for f in keys
			  if f.startswith(text)
			  ]
      return completions

    def do_tag(self, line):
      cmds = line.split(' ')
      if len(cmds) > 0:
	itemType = cmds[0]
	
	if itemType == 'pickups':
	  if len(self.chosenItem) < 1:
	    self.logger.log(LogLevel.CONSOLE, '  No videos had been picked up')
	  else:
	    index = 0
	    for i in range(len(self.chosenItem)):
	    #for item in self.chosenItem:
	      item = self.chosenItem[i]
	      itemTitle = item['title']
	      msg = '  ['+str(index)+']: Getting tag information for: '+itemTitle+'...'
	      self.logger.log(LogLevel.CONSOLE, msg)
	      tags = self.query.SearchSongByRelease(itemTitle)
	      msg = '  ['+str(index)+']: Retrieved '+str(len(tags))+' tags'
	      self.logger.log(LogLevel.CONSOLE, msg)
	      if len(tags)>0:
		item['tag'] = tags
		msg = '  ['+str(index)+']: '+str(len(tags))+' tags assigned'
		self.logger.log(LogLevel.CONSOLE, msg)
		
		#msg = json.dumps(item, sort_keys=True, indent=4, separators=(',', ': '))
		#self.logger.log(LogLevel.CONSOLE, msg)
	      index += 1
	  return
	else:
	  self.logger.log(LogLevel.CONSOLE, '  Warning: item type ['+itemType+'] not found in items list')
      else:
	self.logger.log(LogLevel.CONSOLE, '  Warning: no input commands')
      
    def complete_tag(self, text, line, begidx, endidx):
      tagLine = ['pickups']
      if not text:
	  completions = tagLine
      else:
	  completions = [ f
			  for f in tagLine
			  if f.startswith(text)
			  ]
      return completions

    
if __name__ == '__main__': 
    import sys
    if len(sys.argv) > 1:
        PlaylistTerm().onecmd(' '.join(sys.argv[1:]))
    else:
        PlaylistTerm().cmdloop('Starting terminal for playlist maker...')
#search Bunny shower
#choose video 1
#list chosen
#download chosen
