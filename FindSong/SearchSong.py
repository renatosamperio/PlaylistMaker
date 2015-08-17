#!/usr/bin/python

from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.tools import argparser

import json
import time
import sys

sys.path.append('../Utils')
from Utils.PlaylistLogger import BaseLogger, LogLevel

DEVELOPER_KEY = "AIzaSyDwTQTUC9CGvqqJjTmPA1KX65EmALWGNRc"
#DEVELOPER_KEY = "AIzaSyDErrmDzBCLISIjj2Res-iLLkuTkw3hTK0"

YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
  
class PlaylistGenerator():

  logging = BaseLogger()
  
  def __init__(self, logger=[]):
    self.logging = logger
  
  def SearchInYouTube(self, options):
    return PlaylistGenerator.SearchInYouTube(Options)
    
  @staticmethod
  def SearchInYouTube(options):
    logMsg = "+ Searching query: ["+ options['query']+"]"
    PlaylistGenerator.logging.log(LogLevel.CONSOLE, logMsg)
    videos = []
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
      developerKey=DEVELOPER_KEY)

    # Call the search.list method to retrieve results matching the specified
    # query term.
    search_response = youtube.search().list(
      q=options['query'],
      part="id,snippet",
      maxResults=options['maxResults']
    ).execute()

    #print json.dumps(search_response, sort_keys=True, indent=4, separators=(',', ': '))
    # Filtering search results to only videos
    videosFound = {'video':[], 'playlist' : [], 'channel':[]}
    startTime = time.time()
    for search_result in search_response.get("items", []):
      if search_result["id"]["kind"] == "youtube#video":
	videosFound['videos'].append({'title':search_result["snippet"]["title"], \
				     'id': search_result["id"]["videoId"] })
      elif search_result["id"]["kind"] == "youtube#channel":
	videosFound['playlists'].append({'title':search_result["snippet"]["title"], \
				     'id': search_result["id"]["channelId"] })
      elif search_result["id"]["kind"] == "youtube#playlist":
	videosFound['channels'].append({'title':search_result["snippet"]["title"], \
				     'id': search_result["id"]["playlistId"] })
    ElapsedTime = time.time() - startTime
    
    size = len(videosFound['video']) + len(videosFound['playlist']) + len(videosFound['channel'])
    logMsg = '+ Found '+str(size)+' videos in '+str(ElapsedTime)+'s.'
    PlaylistGenerator.logging.log(LogLevel.CONSOLE, logMsg)
    #json.dumps(videosFound, sort_keys=True, indent=4, separators=(',', ': '))
    return videosFound

def SearchInYouTube(options):
  Options = {}
  Options['query'] = options.q
  Options['maxResults'] = options.max_results
  #plGen = PlaylistGenerator()
  return PlaylistGenerator.SearchInYouTube(Options)

if __name__ == "__main__":
  argparser.add_argument("--q", help="Search term", default="Google")
  argparser.add_argument("--max-results", help="Max results", default=50)
  args = argparser.parse_args()

  try:
    SearchYouTube(args)
  except HttpError, e:
    print "An HTTP error %d occurred:\n%s" % (e.resp.status, e.content)