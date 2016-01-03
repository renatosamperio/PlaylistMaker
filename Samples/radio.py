import pygst
pygst.require("0.10")
import gst

#def on_tag(bus, msg):
    #taglist = msg.parse_tag()
    #print 'on_tag:'
    #for key in taglist.keys():
        #print '\t%s = %s' % (key, taglist[key])

def on_message(self, bus, message):
  if message.type == gst.MESSAGE_TAG:
    taglist = message.parse_tag()
    for key in taglist.keys():
        print '\t%s = %s' % (key, taglist[key])
  else:
    print '*** on_message[',message.type,']:', message
    print "========================================================="
  
#our stream to play
music_stream_uri = 'http://mp3channels.webradio.antenne.de/chillout'
music_stream_uri = 'http://pub6.di.fm:80/di_house?98a17136cec3b063de6e3d34'

#creates a playbin (plays media form an uri) 
player = gst.element_factory_make("playbin", "player")

#set the uri
player.set_property('uri', music_stream_uri)

#start playing
player.set_state(gst.STATE_PLAYING)

#listen for tags on the message bus; tag event might be called more than once
bus = player.get_bus()
bus.enable_sync_message_emission()
bus.add_signal_watch()
#bus.connect('message::tag', on_tag)
bus.connect("message", on_message)

#wait and let the music play
raw_input('Press enter to stop playing...')
