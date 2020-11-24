import pymongo
import config

client = pymongo.MongoClient(config.get_setting("mongodb-connection-string"),ssl=True,ssl_cert_reqs="CERT_NONE")
db = client.testing
collection = db.test

