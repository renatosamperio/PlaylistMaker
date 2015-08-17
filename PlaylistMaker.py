#!/usr/bin/python

import cmd
import logging
import sys
import json

from apiclient.errors import HttpError

from FindSong.SearchSong import PlaylistGenerator
from Utils.PlaylistLogger import BaseLogger, LogLevel

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
      # Creating logger
      self.logger = BaseLogger()
      self.plMaker = PlaylistGenerator()
    
    def cmdloop(self, intro=None):
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
    
    # Utility functions
    
    # Without help
    def do_greet(self, line):
	#line2 = raw_input('Enter a sentence:')
        #print 'hello,', line, ':', str(line2)
        print 'hello,', line


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
	  jsonMsg = json.dumps(self.items, sort_keys=True, indent=4, separators=(',', ': '))
	  print jsonMsg
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
	keys = self.items.keys()
	try:
	  if line not in keys:
	    if line == 'all':
	      items = self.items
	      index = 1
	      for key in keys:
		for item in items[key]:
		  #print item['title'].strip()
		  msg = '  ['+str(index)+']: '+key+': '+item['title'].strip()
		  self.logger.log(LogLevel.CONSOLE, msg)
		  index += 1
	    else:
	      self.logger.log(LogLevel.CONSOLE, 'Warning: Input argument ['+str(line)+'] not in stored items')
	    return
	  else:
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
      if not text:
	  completions = keys
      else:
	  completions = [ f
			  for f in keys
			  if f.startswith(text)
			  ]
      return completions

    def do_choose(self, line):
	""" List existing items"""
	# Check if argument line exists in item keys
	keys = self.items.keys()
	cmds = line.split(' ')
	try:
	  if len(cmds) > 1:
	    itemType = cmds[0]+'s'
	    index = int(cmds[1])-1
	    if itemType in keys:
	      if index in range(len(self.items[itemType])):
		msg = 'Chose item: ['+str(self.items[itemType][index]['title'])+']'
		self.logger.log(LogLevel.CONSOLE, msg)
	      else:
		msg = 'Warning: item index ['+str(index)+'] out of range'
		self.logger.log(LogLevel.CONSOLE, msg)
	    else:
	      msg = 'Warning: item type ['+itemType+'] not found in items list'
	      self.logger.log(LogLevel.CONSOLE, msg)
	  else:
	    itemType = cmds[0]+'s'
	    #line = line+'s'
	    if itemType not in keys:
	      self.logger.log(LogLevel.CONSOLE, 'Warning: item type ['+itemType+'] not found in items list')
	      return
	    else:
	      items = self.items[itemType]
	      if len(items) > 0:
		index = 1
		self.logger.log(LogLevel.CONSOLE, 'Choose an item to download')
		for item in items:
		  msg = '  ['+str(index)+']: '+item['title'].strip()
		  self.logger.log(LogLevel.CONSOLE, msg)
		  index += 1
	      else:
		self.logger.log(LogLevel.CONSOLE, 'Warning: No items found')
		return
	except IOError as e:
	  print "I/O error({0}): {1}".format(e.errno, e.strerror)
	  
    def complete_choose(self, text, line, begidx, endidx):
      keys = self.items.keys()
      if not text:
	  completions = keys
      else:
	  completions = [ f[:-1]
			  for f in keys
			  if f.startswith(text)
			  ]
      return completions
	  
if __name__ == '__main__': 
    import sys
    if len(sys.argv) > 1:
        PlaylistTerm().onecmd(' '.join(sys.argv[1:]))
    else:
        PlaylistTerm().cmdloop('Starting terminal for playlist maker...')
