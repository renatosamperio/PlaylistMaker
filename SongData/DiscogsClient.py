#!/usr/bin/python
import sys

import discogs_client
from difflib import get_close_matches

sys.path.append('../Utils')
from Utils.PlaylistLogger import BaseLogger, LogLevel

class DiscogsQuery:

  def __init__(self):
    '''Class constructor '''
    #TODO: Provide token and app name in a file
    personalToken = 'AdgFCqmDrSlqvvdsFVTyJqpyArvcqPywDvpfgPiI'
    self.client = discogs_client.Client('PlaylistMaker/0.1', user_token=personalToken)
    self.logging = BaseLogger()
    self.indent = '      '
  
  def SearchSongByRelease(self, videoName):
    '''Searches a song in Discogs database '''
    #TODO: video name should be divided by a dash inbetween spaces?
    #(artistName, songName) = videoName.split(' - ')
    spc = self.indent
    tSearchName = videoName.split(' - ')
    if len(tSearchName)>1:
      (artistName, songName) = tSearchName
    else:
      logMsg = spc+'- Incorrect name convention: '+videoName
      self.logging.log(LogLevel.CONSOLE, logMsg)
 
    logMsg = spc+'+ Searching for song: ['+videoName+']'
    self.logging.log(LogLevel.CONSOLE, logMsg)
    results = self.client.search(videoName, type='release')
    pages = results.pages
    
    taggedData = {}
    foundItems = len(results)
    logMsg = spc+'+ Found '+ str(foundItems)+' page results'
    self.logging.log(LogLevel.CONSOLE, logMsg)
    if foundItems>0:
      logMsg = spc+'+ Finding release for: '+songName
      self.logging.log(LogLevel.CONSOLE, logMsg)
      foundSongName, release = self.FindRelease(results, songName)
      if foundSongName == [] or release == []:
	logMsg = spc+'- No release found for: '+ songName
	self.logging.log(LogLevel.CONSOLE, logMsg)
      else:
	#TODO: Requires input mp3 metadata in real file
	logMsg = spc+'+ Getting song information for: '+foundSongName
	self.logging.log(LogLevel.CONSOLE, logMsg)
	taggedData = self.GetTagData(release, foundSongName)
    return taggedData
  
  def FindRelease(self, results, songName):
    ''' Searches a release in dicogs database'''
    spc = self.indent
    trackTitle = []
    for r in range(len(results)):
      data = results[r].data
      release = self.client.release(data["id"])
      for track in release.tracklist:
	lClosestMatches = get_close_matches(songName, [track.title, ''])
	if len(lClosestMatches)>0:
	  trackTitle = track.title
	  logMsg = spc+"+ Found: "+ track.title
	  self.logging.log(LogLevel.CONSOLE, logMsg)
	  return trackTitle, release
    return [], []

  def GetTagData(self, release, songName):
    '''Looks for MP3 metadata from a release '''
    # TODO: Give percentage of found items, how complete is the tag
    total = 13
    itemsFound = [0, total]
    
    # Preparing data encapsulation
    dData = {}
    data = release.data
    keys = data.keys()
    
    # 1-1) Song name
    itemsFound[0] +=1
    dData['SongName'] = songName
    #print "*** 1 SongName",";", songName," ==>",itemsFound[0]
    
    # 2-2) Release ID
    if "id" in keys:
      itemsFound[0] +=1
      dData['ReleaseID'] = data['id']
      #print "*** 2 ReleaseID",":",data['id']," ==>",itemsFound[0]
      
    # 3) Artist information
    if "artists" in keys:
      artistFound = [0,0]
      dData['Artist'] = {}
      for artist in data['artists']:
	artistsKeys = artist.keys()
	# 3-3.1) Artist Name
	if "name" in artistsKeys:
	  artistFound[0] = 1
	  dData['Artist']['Name'] = artist['name']
	  #print "*** 3 ArtistName",":",artist['name']," ==>",artistFound[0]
	# 4-Artist ID
	if "id" in artistsKeys: 
	  artistFound[1] = 1
	  dData['Artist']['ID'] = artist['id']
	  #print "*** 4 ArtistID",":",artist['id']," ==>",artistFound[0]
      itemsFound[0] += sum(artistFound)
      #print "***   Artist",": ==>",itemsFound[0]
    
    # 5-4) Country
    if "country" in keys:
      itemsFound[0] +=1
      dData['Country'] = data['country']
      #print "*** 5 Country",":",data['country'],": ==>",itemsFound[0]
      
    # 6-5) Genre
    if "genres" in keys:
      genresFound = [0]
      dData['Genres'] = []
      for genre in data['genres']:
	genresFound[0] = 1
	dData['Genres'].append(genre)
	#print "*** 6 Genres",":",genre,": ==>",genresFound[0]
      itemsFound[0] += sum(genresFound)
      #print "***   Genres",": ==>",itemsFound[0]

    # 6) Image information
    if "images" in keys:
      dData['Image'] = {}
      imagesFound = [0,0,0]
      for image in data['images']:
	imageKeys = image.keys()
	# 7-6.1) Height 
	if "height" in imageKeys:
	  imagesFound[0] = 1
	  dData['Image']['Height'] = image['height']
	  #print "*** 7 ImageHeight",":",image['height'],": ==>",imagesFound[0]
	# 8-6.2) Width 
	if "width" in imageKeys:
	  imagesFound[1] = 1
	  dData['Image']['Width'] = image['width']
	  #print "*** 8 ImageWidth",":",image['width'],": ==>",imagesFound[0]
	# 9-6.3) URI 
	if "uri" in imageKeys:
	  imagesFound[2] = 1
	  dData['Image']['URI'] = image['uri']
	  #print "*** 9 ImageURI",":",image['uri'],": ==>",imagesFound[0]
	break
      itemsFound[0] += sum(imagesFound)
      #print "***   Image",": ==>",itemsFound[0]
    
    # 10-7) Style
    if "styles" in keys:
      stylesFound = [0]
      dData['Styles'] = []
      for style in data['styles']:
	stylesFound[0] = 1
	dData['Styles'].append(style)
	#print "*** 10 Styles",":",style,": ==>",stylesFound[0]
      itemsFound[0] += sum(stylesFound)
      #print "***   Styles",": ==>",itemsFound[0]
    
    # 11-8) Title
    if "title" in keys:
      itemsFound[0] +=1
      dData['Album'] = data['title']
      #print "*** 11 Album",":",data['title'],": ==>",itemsFound[0]
    
    # 12-8) Year
    if "year" in keys:
      itemsFound[0] +=1
      dData['Year'] = data['year']
      #print "*** 12 Year",":",data['year'],": ==>",itemsFound[0]
    
    # 13-9) Label Name
    if "labels" in keys:
      labelsFound = [0]
      dData['Publisher'] = []
      for label in data['labels']:
	labelKeys = label.keys()
	if "name" in labelKeys:
	  labelsFound[0] = 1
	  dData['Publisher'].append(label['name'])
	  #print "*** 13 Publisher",":",label['name'],": ==>",labelsFound[0]
      itemsFound[0] += sum(labelsFound)
      #print "***   Publisher",": ==>",itemsFound[0]
      
    dData['Completeness'] = float((itemsFound[0])/float(itemsFound[1]))*100.0
    #if dData['Completeness']>0:
      #print data
    return dData


def main(argv):
  query = DiscogsQuery()
  
  for videoName in argv:
    if " - " in videoName:
      print 'Looking for data of video:',videoName
      query.SearchSongData(videoName)
    
  #videoName = "Noel Nanton - Your Love (Ian Pooley's 'Summertime' Mix)"
  #print 'Looking for data of vide:',videoName
  #query.SearchSongData(videoName)
  
  #videoName = "Dj Cam - Summer In Paris (Montilla's Got The Dub Mix)"
  #print 'Looking for data of vide:',videoName
  #query.SearchSongData(videoName)
  
  #videoName = "Gus Gus - David (King Britt Mix)"
  #print 'Looking for data of vide:',videoName
  #query.SearchSongData(videoName)
  
  #videoName = "Jetlag feat Esther - Walk with me (original mix)"
  #print 'Looking for data of vide:',videoName
  #query.SearchSongData(videoName)
  
  #videoName = "Ministry of Da Funk - L'amour toujours (Original Mix)"
  #print 'Looking for data of vide:',videoName
  #query.SearchSongData(videoName)
  
  #videoName = "The Shapeshifters - Treadstone"
  #print 'Looking for data of vide:',videoName
  #query.SearchSongData(videoName)
  
  #videoName = "Pearl Jam - Jeremy"
  #print 'Looking for data of vide:',videoName
  #query.SearchSongData(videoName)
  
if __name__ == "__main__":
   main(sys.argv[1:])