import pymongo

client = pymongo.MongoClient("paste connection string here",ssl=True,ssl_cert_reqs="CERT_NONE")
db = client.databaseNameHere
collection = db.collectionNameHere

