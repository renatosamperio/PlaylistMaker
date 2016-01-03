use test_database
var items = db.tracks.find({State:'Played'})
print (" - Found "+items.size().toString()+" items")

var item = db.tracks.find({State:'Played'}).sort({_id:-1}).limit(1)
item.forEach(printjson);


