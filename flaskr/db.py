import pymongo
import config

client = pymongo.MongoClient(config.get_setting("mongodb-connection-string"), ssl=True, ssl_cert_reqs="CERT_NONE")
db = client.testing
coll_products = db.test
coll_benchmarks = db.bench
coll_transports = db.trans
