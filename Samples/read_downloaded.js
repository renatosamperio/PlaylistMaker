use test_database
var items = db.tracks.find({State:'Downloaded'})
print (" - Found "+items.size().toString()+" items")


var report = db.tracks.find({State:'Downloaded'}).sort({_id:-1}).limit(10)

var reportArray = report.toArray()

print (" - Last songs");
for (i = 0; i < reportArray.length; i++) {
    print( "     "+reportArray[i]["Track"] );
}

