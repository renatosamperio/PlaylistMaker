#!/usr/bin/env python

import pymongo

main():
  # Creating mongo client
  client = MongoClient('localhost', 27017)

  # Getting instance of database
  db = client.test_database

  # Getting instance of collection
  self.collection = db.streamer

  post_id = self.collection.insert_one(document)
  
if __name__ == '__main__':
  main()