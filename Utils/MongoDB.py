#!/usr/bin/python

import sys, os
import time
import json
import pymongo

from pymongo import MongoClient	

track = {
	    'Track': '',
	    'State':'Input|Played|Downloaded|Tagged|NotFound|NotMatched',
	    'Properties' : {
	      'Path':'',
	      'Played':''
	    }
	  }

class MongoHandler:
  def __init__(self, database, collection, host='localhost', port=27017, logger=None ):
    try: 
      # Creating mongo client
      client = MongoClient(host, port)

      # Getting instance of database
      db = client[database]

      # Getting instance of collection
      self.collection = db[collection]
      
      if logger:
	self.logger = logger
    
    except Exception as inst:
      exc_type, exc_obj, exc_tb = sys.exc_info()
      exception_fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
      exception_line = str(exc_tb.tb_lineno) 
      exception_type = str(type(inst))
      exception_desc = str(inst)
      print "MongoHandler:Init: %s: %s in %s:%s"%(exception_type, 
					exception_desc, 
					exception_fname,
					exception_line )
      
  def SingleMatch(self, field, pattern):
    ''''''
    posts = self.collection.find( { field: { '$regex': pattern } } )
    return posts
  
  def InsertOne(self, document):
    try: 
      post_id = self.collection.insert(document)
      return post_id
    except Exception as inst:
      exc_type, exc_obj, exc_tb = sys.exc_info()
      exception_fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
      exception_line = str(exc_tb.tb_lineno) 
      exception_type = str(type(inst))
      exception_desc = str(inst)
      print "MongoHandler.InsertOne: %s: %s in %s:%s"%(exception_type, 
					exception_desc, 
					exception_fname,
					exception_line )
      sys.exit(0)
  
  def Exists(self, trackName):
    ''' '''
    # Checking if there is something in title state
    if len(trackName)<1:
      return False
    
    try: 
      pattern = trackName.replace(' ', '.*')
      #print "*** pattern:", pattern
      self.collection.create_index( [( 'Track', 'text')] )
      
      # Try fist time if song is in database
      posts = self.collection.find(
      { 'Track': { '$regex': pattern } } 
	)
      
      #print "***1",posts.count()
      #for post in posts:
	#print post['Track']
      if posts.count()>0:
	return posts.count()>0
      
      #Try with another query if song is not in database
      posts = self.collection.find(
	{ '$text': { '$search': pattern } },
	{ 'score': { '$meta': 'textScore' } }
      )
      #print "***2",posts.count()
      
      recount = 0
      scoreLimit = 3.0
      for post in posts:
	if post['score']>scoreLimit:
	  print '['+str(post['score'])+']= '+post['Track']
	  recount+=1
      print "Second try, Found ["+str(posts.count())+"] items, and ["+ \
	    str(recount)+"] with score over ["+str(scoreLimit)+"]:\n\t["+\
	    trackName+"]"
      return recount>0
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
      sys.exit(0)
  
  def Report(self, typeReport=''):
    ''' '''
    try: 
      if len(typeReport)<1:
	posts = self.collection.find()
	return posts
      elif typeReport=='Played':
	posts = self.collection.find({'State':typeReport})
	return posts
    
    except Exception as inst:
      exc_type, exc_obj, exc_tb = sys.exc_info()
      exception_fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
      exception_line = str(exc_tb.tb_lineno) 
      exception_type = str(type(inst))
      exception_desc = str(inst)
      print "MongoHandler.Report: %s: %s in %s:%s"%(exception_type, 
					exception_desc, 
					exception_fname,
					exception_line )
      
  def CleanRepeated(self):
    ''' Method that cleans repeated iterations'''
    try:
      
      # Removing entries with empty tracks
      print "Removing entries with empty tracks..."
      posts = self.collection.remove({'Track':''})
      print posts
      
      posts = self.collection.find()
      print "Found", posts.count(),"items"
      items = []
      for post in posts:
	#print "  Track:",post['Track']
	#print "  State:",post['State']
	#print "="*80
	if post['Track'] not in items:
	  items.append(post['Track'])
	else:
	  print "Already found, removing:", post
	  print self.collection.remove({"_id": {"$eq": post['_id']}})
	
      # Removing DI.fm adverts
      print "Removing not required tracks"
      print self.collection.remove({'Track':'DI.fm'})
    except Exception as inst:
      exc_type, exc_obj, exc_tb = sys.exc_info()
      exception_fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
      exception_line = str(exc_tb.tb_lineno) 
      exception_type = str(type(inst))
      exception_desc = str(inst)
      print "MongoHandler.CleanRepeated: %s: %s in %s:%s"%(exception_type, 
					exception_desc, 
					exception_fname,
					exception_line )
    
  def UpdateTrackState(self, trackName, state, path=''):
    ''' '''
    try:
      if state == 'Downloaded':
	result = self.collection.update(
	    {"Track": trackName},
	    {
		"$set": {
		    'State':state,
		    'Properties.Path':path
		},
		"$currentDate": {"lastModified": True}
	    }
	)
	return result['updatedExisting']
      elif state == 'NotFound' or state == 'NotMatched' :
	result = self.collection.update(
	    {"Track": trackName},
	    {
		"$set": {
		    'State':state,
		},
		"$currentDate": {"lastModified": True}
	    }
	)
	#print "result:", result
	return result['updatedExisting']
    except Exception as inst:
      exc_type, exc_obj, exc_tb = sys.exc_info()
      exception_fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
      exception_line = str(exc_tb.tb_lineno) 
      exception_type = str(type(inst))
      exception_desc = str(inst)
      print "MongoHandler.Report: %s: %s in %s:%s"%(exception_type, 
					exception_desc, 
					exception_fname,
					exception_line )
      

if __name__ == '__main__':
  ''''''
#client = MongoClient('localhost', 27017)
#db = client['test_database']
#collection = db ['tracks']
  
#print "Inserting new item"
#trackName = 'Markus Quittner - Sneaky Keys (Original Mix)'
#item = {
#'Track': trackName,
#'State':'Played',
#'Properties' : {
  #'Played':'House - DIGITALLY IMPORTED - silky sexy deep house music direct from New York city!'
#}}
#post_id = collection.insert_one(item)

#tic = time.clock()
#posts = collection.find()
#toc = time.clock()
#for post in posts:
  #print "  INSERTED:", post['Track']
#print "  Found:", collection.count(),"posts in ", str(toc - tic), "s"
  
#print ""
#print "Finding inserted item"
#trackName = 'Markus Quittner - Sneaky Keys (Original Mix)'
#collection.create_index( [( 'Track', pymongo.TEXT)] )
  
#pattern = 'Markus.*Quittner.*-.*Sneaky Keys.*(Original.*Mix)'
#tic = time.clock()
#posts = collection.find( 
  #{ 'Track': { '$regex': pattern } } 
#)
#toc = time.clock()
#print "  - Query 1 found", posts.count(), "posts in ", str(toc - tic), "s"
#for post in posts:
  #print "  FOUND:", post['Track']

#tic = time.clock()
#posts = collection.find(
  #{ '$text': { '$search': pattern } },
  #{ 'score': { '$meta': 'textScore' } }
#)
#toc = time.clock()
#print "  - Query 2 found", posts.count(), "posts in ", str(toc - tic), "s"
#for post in posts:
  #print "  FOUND:", post['Track']
  
#tic = time.clock()
#posts = collection.find(
  #{ '$text': { '$search': pattern } },
  #{ 'score': { '$meta': 'textScore' } }
#).sort( [('score', {'$meta': 'textScore'})])
#toc = time.clock()
#print "  - Query 3 found", posts.count(), "posts in ", str(toc - tic), "s"
#for post in posts:
  #print "  FOUND:", post['Track']
  
#tic = time.clock()
#posts = collection.find( 
  #{ 'Track': trackName } 
#)
#toc = time.clock()
#print "  - Query 4 found", posts.count(), "posts in ", str(toc - tic), "s"
#for post in posts:
  #print "  FOUND:", post['Track']

#tic = time.clock()
#posts = collection.find(
  #{ '$text': { '$search': pattern } }
#)
#toc = time.clock()
#print "  - Query 5 found", posts.count(), "posts in ", str(toc - tic), "s"
#for post in posts:
  #print "  FOUND:", post['Track']
    
  #print ""
  #print "Finding inserted item with handler"
  #database = MongoHandler('test_database', 'tracks')

  #trackName = "Kings Of Tomorrow feat. April - Fall For You (Sandy Rivera's C"
  #trackName = "Jay-J ft. Latrice Barnett - Keep On Rising (DJ Chus and David Penn Stereo Dub)"
  #if not database.Exists(trackName):
    #print "  Song does not exist!"
    
  #else:
    #print "  Song exists!"
    
  #print ""
  #print "Making report"
  #database.Report()
    
  #print ""
  #print "Clean repeated entries"
  #database.CleanRepeated()
  #collection.drop()

  
  #database = MongoHandler('test_database', 'tracks')
  #trackName = "Brancaccio & Aisher - It's Gonna Be (A Lovely Day) (Chris Lum & Jay-J Chumpchange Remix)"
  #path = '/home/samperio/topics/projects/PlaylistMaker/DownlaodedSongs/'+trackName+'-kqxr10qFuVM.mp3'
  #database.UpdateTrackState(trackName, 'Downloaded', path)
  
  ## Updating downloading state 
  #database = MongoHandler('test_database', 'temp')
  #posts = database.Report()
  #sizePosts= posts.count()
  #for i in range(sizePosts):
    #post = posts[i]
    
    #state = 'Downloaded'
    #if post["State"] == "Downloaded":
      #state = 'Played'

    #from random import randint
    #path = 'new/path'+str(randint(0,1000))
    #print "Updating document with path:",path
    #database.UpdateTrackState(post["Track"], state, path)
############################## MONGO SCRIPT ##############################
#var trackName = "Markus Quittner - Sneaky Keys (Original Mix)"
#db.tracks.insert({
  #'Track': trackName,
  #'State':'Played',
  #'Properties' : {
    #'Played':'House - DIGITALLY IMPORTED'
  #}
#})
#db.tracks.createIndex( { "Track": "text" } )

#var pattern = 'Markus.*Quittner.*-.*Sneaky Keys.*(Original.*Mix)'

#db.tracks.find({Track:pattern})
#db.tracks.find( { $text: { $search: "Markus" } } )
#// Search in any field
#db.tracks.createIndex( { "$**": "text" } )

#db.tracks.find( { 'Track': { $regex: pattern } } )
#db.tracks.findOne( { 'Track': { $regex: pattern } } )
#db.tracks.find(
    #{ $text: { $search: pattern } },
    #{ score: { $meta: 'textScore' } }
#)

#db.tracks.find(
    #{ $text: { $search: pattern } },
    #{ score: { $meta: 'textScore' } }
#).sort( { score: { $meta: 'textScore' } } )

#db.tracks.insert({
  #'Track': 'The Carry Nation - DJ Mix: The Carry Nation Vol. 2',
  #'State':'Played',
  #'Properties' : {
    #'Played':'House - DIGITALLY IMPORTED - silky sexy deep house music direct from New York city!'
  #}
#})

#db.tracks.find({'State':'Played'})
#db.tracks.find({'State':'Played'}).limit(3)

